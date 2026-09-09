"""/orc-publish CLI: resolve a selection, execute it, and report results.

This module never prompts for confirmation itself - --dry-run resolves and prints only,
normal mode resolves, prints, and executes immediately. The conversational safety gate
("always dry-run first, get an explicit yes, then run for real") lives in SKILL.md, which
calls this script twice: once with --dry-run, once without, once the user has confirmed.
"""

import argparse
import contextlib
import os
import pathlib
import signal
import subprocess
import sys

import yaml

from .selection import SelectionError, resolve_selection, resolve_token
from .tree import load_tree


NOT_ACTIONABLE = "known channel, not yet actionable"
NO_METRICS = "known channel, no metrics source"

# Every leaf command key. "action" publishes (writes, needs the SKILL.md confirmation gate);
# "metrics" reads back numbers a channel already publishes about itself (safe, no gate). They
# share the whole execution path - selection, timeout, process-group kill, output capture -
# because the only thing that differs is which key holds the command. BACKLOG #18's proposed
# `status:` is the same shape again: add it to tree.LEAF_KEYS and to NOT_SET below.
NOT_SET = {"action": NOT_ACTIONABLE, "metrics": NO_METRICS}

# A "something is wrong" ceiling, not a performance budget. A genuinely slow-but-healthy
# upload sets its own `timeout:` on its leaf rather than raising this. See BACKLOG #11.
DEFAULT_TIMEOUT_SECONDS = 600


def render_filename(template, version):
    """Render a leaf's filename_template for a given version string, or None if unset."""
    return template.replace("<version>", version) if template else None


def build_plan(channel_root, tokens):
    """Resolve CLI selection tokens against the channel tree to a list of leaf Nodes."""
    return resolve_selection(channel_root, tokens)


def format_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS, command_key="action"):
    if not leaves:
        return "(no leaves selected)"
    lines = []
    for leaf in leaves:
        command = leaf.command(command_key)
        if command:
            lines.append(f"{leaf.dotted_path}: {command}")
            lines.append(f"  timeout: {effective_timeout(leaf, default_timeout)}s")
        else:
            lines.append(f"{leaf.dotted_path}: ({NOT_SET[command_key]})")
        for req in leaf.requirements:
            lines.append(f"  requirement: {req}")
        for issue in leaf.issues:
            lines.append(f"  issue: {issue}")
    return "\n".join(lines)


def is_bad_timeout(value):
    """True when a timeout value isn't a usable positive whole number of seconds.

    YAML turns `timeout: true` into a bool, and bool is a subclass of int, so it has to be
    rejected explicitly rather than passing the isinstance check. Shared by the leaf-level
    `timeout:` check and `--timeout`, so the same setting can't mean two different things.
    """
    return isinstance(value, bool) or not isinstance(value, int) or value <= 0


def timeout_error(leaves):
    """The first leaf-level `timeout:` that isn't usable, as a message - or None."""
    for leaf in leaves:
        value = leaf.timeout
        if value is None:
            continue
        if is_bad_timeout(value):
            return (
                f"{leaf.dotted_path}: timeout must be a positive whole number of seconds, "
                f"got {value!r}"
            )
    return None


def run_for(distro_root, distro_path):
    """--for: report which channel path a distro leaf points at, or that none is set."""
    node = resolve_token(distro_root, distro_path)
    if not node.is_leaf:
        raise SelectionError(f"'{distro_path}' is not a single distro target - select a leaf")
    channel = node.channel
    if channel:
        return f"{node.dotted_path} -> {channel}"
    return f"{node.dotted_path}: no channel set (known target, not yet actionable)"


def _decode(stream):
    """Text from a captured stdout/stderr stream, whatever shape it comes in.

    TimeoutExpired hands back raw bytes (not the text=True str the success/failed branches
    get) or None when nothing was captured - decode defensively rather than betting the tool
    on a subprocess implementation detail. See BACKLOG #15.
    """
    if stream is None:
        return ""
    if isinstance(stream, bytes):
        stream = stream.decode(errors="replace")
    return stream.strip()


def effective_timeout(leaf, default_timeout=DEFAULT_TIMEOUT_SECONDS):
    """The timeout a leaf really runs under: its own if set, otherwise the default."""
    return leaf.timeout if leaf.timeout is not None else default_timeout


def execute_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS, command_key="action"):
    """Run each leaf's action. An independent failure doesn't stop the remaining leaves.

    Returns a list of (leaf, status, detail) - status is "success", "failed", "timed out",
    or "not attempted". detail is the action's real stdout on success, the real error text on
    failure, and "known channel, not yet actionable" when not attempted - never silently
    empty on success, since this is the only evidence an operator gets that a real publish
    actually happened.
    """
    results = []
    for leaf in leaves:
        command = leaf.command(command_key)
        if not command:
            results.append((leaf, "not attempted", NOT_SET[command_key]))
            continue
        limit = effective_timeout(leaf, default_timeout)
        try:
            # start_new_session=True puts the shell in its own process group so a compound
            # action (pipes, &&, subshells) can be killed as a whole - subprocess.run's own
            # timeout only kills the /bin/sh -c process itself, orphaning whatever it forked,
            # so a timed-out dput would keep uploading past the report. See BACKLOG #11.
            with subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            ) as proc:
                try:
                    stdout, stderr = proc.communicate(timeout=limit)
                except BaseException:
                    # Unconditional, not just on timeout: the same start_new_session that lets
                    # the group be killed also means a Ctrl-C on this process no longer reaches
                    # the action, so an interrupt would orphan exactly what the group kill
                    # exists to catch. TimeoutExpired is a BaseException and is still re-raised
                    # below, so the timeout path is unchanged. wait(), not communicate(): an
                    # escaped grandchild can still hold the pipes open.
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    proc.wait()
                    raise
                if proc.returncode != 0:
                    raise subprocess.CalledProcessError(
                        proc.returncode, command, output=stdout, stderr=stderr
                    )
            detail = (stdout or "").strip()
            results.append((leaf, "success", detail))
        except subprocess.TimeoutExpired as e:
            # TimeoutExpired does carry whatever was captured before the timeout - but as
            # undecoded bytes despite text=True, because the exception is built from the raw
            # buffers before the text wrapper ever sees them. A stream that produced nothing
            # comes back as None, not b"". See BACKLOG #15. The stdin clause stays either way:
            # without it an operator has no reason to suspect stdin at all.
            captured = "\n".join(filter(None, [_decode(e.stdout), _decode(e.stderr)]))
            if captured:
                # Actionable sentence first, captured output last. A real action's capture is a
                # wall of build log, and a stdin hint stranded under its final line reads as
                # part of that output rather than as the tool talking.
                detail = (
                    f"timed out after {limit}s - the action may be waiting on stdin. "
                    f"Output captured before it hung:\n{captured}"
                )
            else:
                detail = (
                    f"timed out after {limit}s - no output captured, "
                    "the action may be waiting on stdin"
                )
            results.append((leaf, "timed out", detail))
        except subprocess.CalledProcessError as e:
            detail = (e.stderr or "").strip() or str(e)
            results.append((leaf, "failed", detail))
    return results


def format_summary(results):
    lines = []
    for leaf, status, detail in results:
        line = f"{leaf.dotted_path}: {status}"
        if detail:
            line += f" ({detail})"
        lines.append(line)
    return "\n".join(lines)


def scripts_dir():
    """This script bundle's own directory, as an absolute path.

    Exported to every leaf command as $ORC_PUBLISH_SCRIPTS so a project's channels.yaml can
    invoke Orclab's own bundled helpers (metrics/launchpad_ppa.py) by a stable name. Derived
    from __file__ rather than from $CLAUDE_SKILL_DIR, which is not set in every context a
    skill's Bash calls actually run in - confirmed unset live, 2026-09-08.
    """
    return str(pathlib.Path(__file__).resolve().parent.parent)


def main(argv=None):
    os.environ["ORC_PUBLISH_SCRIPTS"] = scripts_dir()
    parser = argparse.ArgumentParser(prog="orc-publish")
    parser.add_argument("selection", nargs="*")
    parser.add_argument("--for", dest="for_distro")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="run each selected leaf's `metrics:` command instead of its `action:` - a "
        "read-only report of the numbers that channel already publishes about itself",
    )
    parser.add_argument("--channels", default=".orclab/publish/channels.yaml")
    parser.add_argument("--distro", default=".orclab/publish/distro.yaml")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)

    if is_bad_timeout(args.timeout):
        print(
            "error: --timeout must be a positive whole number of seconds, "
            f"got {args.timeout!r}",
            file=sys.stderr,
            flush=True,
        )
        return 1

    if args.for_distro:
        if args.selection:
            print(
                "note: selection tokens are ignored when --for is used",
                file=sys.stderr,
                flush=True,
            )
        try:
            distro_root = load_tree(args.distro)
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"error: could not load {args.distro}: {e}", file=sys.stderr, flush=True)
            return 1
        try:
            print(run_for(distro_root, args.for_distro), flush=True)
        except SelectionError as e:
            print(f"error: {e}", file=sys.stderr, flush=True)
            return 1
        return 0

    try:
        channel_root = load_tree(args.channels)
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"error: could not load {args.channels}: {e}", file=sys.stderr, flush=True)
        return 1

    try:
        leaves = build_plan(channel_root, args.selection)
    except SelectionError as e:
        print(f"error: {e}", file=sys.stderr, flush=True)
        return 1

    bad_timeout = timeout_error(leaves)
    if bad_timeout:
        print(f"error: {bad_timeout}", file=sys.stderr, flush=True)
        return 1

    command_key = "metrics" if args.metrics else "action"
    print(format_plan(leaves, default_timeout=args.timeout, command_key=command_key), flush=True)

    if args.dry_run:
        return 0

    results = execute_plan(leaves, default_timeout=args.timeout, command_key=command_key)
    print(format_summary(results), flush=True)
    return 0 if all(status not in ("failed", "timed out") for _, status, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
