"""/orc-publish CLI: resolve a selection, execute it, and report results.

This module never prompts for confirmation itself - --dry-run resolves and prints only,
normal mode resolves, prints, and executes immediately. The conversational safety gate
("always dry-run first, get an explicit yes, then run for real") lives in SKILL.md, which
calls this script twice: once with --dry-run, once without, once the user has confirmed.
"""

import argparse
import os
import signal
import subprocess
import sys

import yaml

from .selection import SelectionError, resolve_selection, resolve_token
from .tree import load_tree


NOT_ACTIONABLE = "known channel, not yet actionable"

# A "something is wrong" ceiling, not a performance budget. A genuinely slow-but-healthy
# upload sets its own `timeout:` on its leaf rather than raising this. See BACKLOG #11.
DEFAULT_TIMEOUT_SECONDS = 600


def render_filename(template, version):
    """Render a leaf's filename_template for a given version string, or None if unset."""
    return template.replace("<version>", version) if template else None


def build_plan(channel_root, tokens):
    """Resolve CLI selection tokens against the channel tree to a list of leaf Nodes."""
    return resolve_selection(channel_root, tokens)


def format_plan(leaves):
    if not leaves:
        return "(no leaves selected)"
    lines = []
    for leaf in leaves:
        action = leaf.action or f"({NOT_ACTIONABLE})"
        lines.append(f"{leaf.dotted_path}: {action}")
        for req in leaf.requirements:
            lines.append(f"  requirement: {req}")
        for issue in leaf.issues:
            lines.append(f"  issue: {issue}")
    return "\n".join(lines)


def run_for(distro_root, distro_path):
    """--for: report which channel path a distro leaf points at, or that none is set."""
    node = resolve_token(distro_root, distro_path)
    if not node.is_leaf:
        raise SelectionError(f"'{distro_path}' is not a single distro target - select a leaf")
    channel = node.channel
    if channel:
        return f"{node.dotted_path} -> {channel}"
    return f"{node.dotted_path}: no channel set (known target, not yet actionable)"


def effective_timeout(leaf, default_timeout=DEFAULT_TIMEOUT_SECONDS):
    """The timeout a leaf really runs under: its own if set, otherwise the default."""
    return leaf.timeout if leaf.timeout is not None else default_timeout


def execute_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS):
    """Run each leaf's action. An independent failure doesn't stop the remaining leaves.

    Returns a list of (leaf, status, detail) - status is "success", "failed", "timed out",
    or "not attempted". detail is the action's real stdout on success, the real error text on
    failure, and "known channel, not yet actionable" when not attempted - never silently
    empty on success, since this is the only evidence an operator gets that a real publish
    actually happened.
    """
    results = []
    for leaf in leaves:
        if not leaf.action:
            results.append((leaf, "not attempted", NOT_ACTIONABLE))
            continue
        limit = effective_timeout(leaf, default_timeout)
        try:
            # start_new_session=True puts the shell in its own process group so a compound
            # action (pipes, &&, subshells) can be killed as a whole on timeout - subprocess.run
            # only kills the /bin/sh -c process itself, orphaning whatever it forked. See
            # BACKLOG #11 follow-up: a timed-out debsign/dput kept running past the report.
            with subprocess.Popen(
                leaf.action,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            ) as proc:
                try:
                    stdout, stderr = proc.communicate(timeout=limit)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    proc.wait()
                    raise
                if proc.returncode != 0:
                    raise subprocess.CalledProcessError(
                        proc.returncode, leaf.action, output=stdout, stderr=stderr
                    )
            detail = (stdout or "").strip()
            results.append((leaf, "success", detail))
        except subprocess.TimeoutExpired:
            # stdout/stderr are unavailable here (capture never completed) - say so, or the
            # operator has no reason to suspect stdin at all.
            results.append(
                (
                    leaf,
                    "timed out",
                    f"timed out after {limit}s - no output captured, "
                    "the action may be waiting on stdin",
                )
            )
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


def main(argv=None):
    parser = argparse.ArgumentParser(prog="orc-publish")
    parser.add_argument("selection", nargs="*")
    parser.add_argument("--for", dest="for_distro")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--channels", default=".orclab/publish/channels.yaml")
    parser.add_argument("--distro", default=".orclab/publish/distro.yaml")
    args = parser.parse_args(argv)

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

    print(format_plan(leaves), flush=True)

    if args.dry_run:
        return 0

    results = execute_plan(leaves)
    print(format_summary(results), flush=True)
    return 0 if all(status not in ("failed", "timed out") for _, status, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
