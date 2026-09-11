"""/orc-publish CLI: resolve a selection, execute it, and report results.

This module never prompts for confirmation itself - --dry-run resolves, prints, and stops
without running any leaf command, normal mode resolves, prints, and executes immediately.

--dry-run is not entirely subprocess-free: to say what preflight will do it shell-expands each
leaf's `artifact:` expression, command substitution included, on the same trust boundary as
`action:` (the project's own config). That is still not a `prepare:`-style side effect - a path
expression is a read, a build is not - and a dry run deliberately never runs `prepare:`.

The conversational safety gate
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

from .inspect import UnsupportedArchive, format_findings, inspect_archive, unknown_rules
from .selection import SelectionError, resolve_selection, resolve_token
from .tree import load_tree


NOT_ACTIONABLE = "known channel, not yet actionable"
NO_METRICS = "known channel, no metrics source"
NO_CONFIRM = "synchronous channel - its publish settles when the action exits"

# Every leaf command key. "action" publishes (writes, needs the SKILL.md confirmation gate);
# "metrics" reads back numbers a channel already publishes about itself (safe, no gate). They
# share the whole execution path - selection, timeout, process-group kill, output capture -
# because the only thing that differs is which key holds the command. BACKLOG #18 shipped as
# `confirm:` and is deliberately NOT this shape - it is a mapping of two optional sub-fields,
# not a bare command, and it reports four statuses of its own. It has its own small path
# (confirm_plan) rather than a fourth entry here.
NOT_SET = {"action": NOT_ACTIONABLE, "metrics": NO_METRICS}

# `prepare:` and `preflight:` gate the *action* path only. A metrics query publishes nothing,
# so there is no irreversible step to gate - and running a project's build just to answer a
# read-only download-count question would be wrong on its own terms.
GATED_COMMAND_KEY = "action"

# A "something is wrong" ceiling, not a performance budget. A genuinely slow-but-healthy
# upload sets its own `timeout:` on its leaf rather than raising this. See BACKLOG #11.
DEFAULT_TIMEOUT_SECONDS = 600

# Heuristics over a shell string, so this warns and never refuses - unlike the content rules,
# which are deterministic checks of real bytes.
PUBLISH_VERBS = (
    "dput", "snapcraft upload", "twine upload", "npm publish",
    "gh release create", "cargo publish",
)
BUILD_VERBS = (
    "dpkg-buildpackage", "debuild", "python -m build", "flatpak-builder", "cargo build",
)


def build_plan(channel_root, tokens):
    """Resolve CLI selection tokens against the channel tree to a list of leaf Nodes."""
    return resolve_selection(channel_root, tokens)


def action_shape_warning(leaf):
    """Warn when one action both builds and irreversibly publishes, so no gate can run between."""
    action = leaf.action or ""
    for publish in PUBLISH_VERBS:
        # rfind, not find: an action can publish, build, then publish again. Comparing the
        # *last* publish against the *first* build tests every pair at once - if any publish
        # follows any build, the last one follows the first one too. See BACKLOG #23.
        at = action.rfind(publish)
        if at == -1:
            continue
        for build in BUILD_VERBS:
            built = action.find(build)
            if built != -1 and built < at:
                return (
                    "action builds and irreversibly publishes in one command - no gate can run "
                    "between them. Split the build into prepare: to enable preflight."
                )
    return None


def _preflight_plan_result(leaf, default_timeout):
    """What the dry-run plan promises preflight will do for one leaf declaring `preflight:`.

    The plan is what an operator consents to, so it reports the real refusal wherever the real
    run's answer is already knowable without the artifact existing - an unknown rule name, or a
    `preflight:` with no `artifact:` at all - by asking `preflight_refusal` itself rather than
    keeping a second copy of those checks. Only a leaf that actually has a `prepare:` step can
    honestly defer: without one, nothing will build the artifact between now and the action, so
    a missing file is reported as the `artifact not found:` refusal it will really be.
    """
    if unknown_rules(leaf.preflight) or not leaf.artifact:
        return preflight_refusal(leaf, default_timeout)
    resolved = _expand_artifact(leaf, effective_timeout(leaf, default_timeout))
    path, error = resolved
    if not error and not (path and pathlib.Path(path).is_file()) and leaf.prepare:
        return "artifact not built yet - will be inspected after prepare, at execution time"
    return preflight_refusal(leaf, default_timeout, resolved=resolved) or "clean"


def _preflight_plan_lines(leaf, default_timeout):
    """The dry-run plan's preflight and action-shape lines for one actionable leaf.

    Action path only - `format_plan` calls this only for GATED_COMMAND_KEY, so a `--metrics`
    plan never inspects an artifact.
    """
    lines = []
    if leaf.preflight:
        lines.append(f"  preflight: {', '.join(leaf.preflight)}")
        lines.append(f"  preflight result: {_preflight_plan_result(leaf, default_timeout)}")
    warning = action_shape_warning(leaf)
    if warning:
        lines.append(f"  warning: {warning}")
    if leaf.confirm:
        lines.append("  asynchronous: declares confirm - check separately with --confirm")
    return lines


def format_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS, command_key="action"):
    if not leaves:
        return "(no leaves selected)"
    lines = []
    for leaf in leaves:
        command = leaf.command(command_key)
        if command:
            lines.append(f"{leaf.dotted_path}: {command}")
            lines.append(f"  timeout: {effective_timeout(leaf, default_timeout)}s")
            if command_key == GATED_COMMAND_KEY:
                lines.extend(_preflight_plan_lines(leaf, default_timeout))
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


def command_error(leaves):
    """The first `action:`, `metrics:` or `prepare:` that isn't a command string - or None.

    `action: true` is valid YAML and a Python bool. It used to escape as a traceback from two
    places - `action_shape_warning` on the dry-run plan, `subprocess.Popen` on the real run -
    with no summary printed and a healthy sibling never attempted. Same treatment as a bad
    `timeout:` or `confirm:`, for the same reason: it is a declaration that cannot do what it
    claims, and a publish is irreversible, so stopping before anything runs beats publishing
    the siblings and re-publishing them after the typo is fixed. See BACKLOG #29.
    """
    for leaf in leaves:
        for key in ("action", "metrics", "prepare"):
            value = leaf.command(key)
            if value is not None and not isinstance(value, str):
                return f"{leaf.dotted_path}: {key} must be a command string, got {value!r}"
    return None


def confirm_error(leaves):
    """The first unusable `confirm:` block, as a message - or None.

    Same treatment as a bad `timeout:`, and for the same reason: the value is a declaration
    the operator made, it cannot do what it claims, and guessing a default would be inventing
    an answer to "did this land" that nobody supplied.
    """
    for leaf in leaves:
        value = leaf.confirm
        if value is None:
            continue
        if not isinstance(value, dict):
            return (
                f"{leaf.dotted_path}: confirm must be a mapping with `command` and/or `url`, "
                f"got {value!r}"
            )
        if not leaf.confirm_command and not leaf.confirm_url:
            return f"{leaf.dotted_path}: confirm must declare `command`, `url`, or both"
        for key in ("command", "url"):
            sub = value.get(key)
            if sub is not None and not isinstance(sub, str):
                return f"{leaf.dotted_path}: confirm.{key} must be a string, got {sub!r}"
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


def _run(command, limit):
    """Run one command to completion under `limit` seconds.

    Returns (returncode, stdout, stderr). Raises subprocess.TimeoutExpired, which the caller
    turns into whatever it means in that context. The process starts in its own session and its
    whole group is killed on any exception - a compound shell command forks, so killing only the
    shell orphans the grandchild that is doing the real work. Interrupts take that path too, not
    just timeouts: start_new_session means a Ctrl-C no longer reaches the child by itself.

    Every path that spawns a subprocess routes through here - a leaf's `prepare:`, an
    `artifact:` path expansion, a leaf's `action:` and a leaf's `metrics:` alike - so the
    process-group handling below exists exactly once.
    """
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
        return proc.returncode, stdout, stderr


def expand_path(expr, timeout):
    """Shell-expand an artifact path the same way an action is shell-expanded.

    Double-quoted so command substitution still runs but word splitting does not - a path
    with a space stays one path. Same trust boundary as `action`: it is the project's own
    config, not untrusted input. Routed through `_run` rather than a bare `subprocess.run`
    so this, too, runs in its own killable process group - an expansion like
    `$(sleep 20; echo x)` forks just like a compound action does, and a bare `subprocess.run`
    timeout only kills the /bin/sh -c process, orphaning whatever it forked. Raises
    subprocess.TimeoutExpired, same as `_run` - the caller decides what a hung expansion means.
    """
    _returncode, stdout, _stderr = _run(f'printf %s "{expr}"', timeout)
    return stdout.strip()


def _expand_artifact(leaf, timeout):
    """Expand `leaf.artifact` once, turning a hang into a message instead of a crash.

    Returns (path, error): on success `error` is None; on a timed-out expansion `path` is
    None and `error` is the message to show, whether that ends up on a dry-run plan line or
    in a real preflight refusal. The one guarded call site both `format_plan` and
    `preflight_refusal` route through, so a hanging `artifact:` expression can never reach a
    caller that forgot to catch `subprocess.TimeoutExpired` itself - and a caller that
    already has a `(path, error)` from here can hand it to `preflight_refusal` via
    `resolved=` instead of expanding the same expression a second time.
    """
    try:
        return expand_path(leaf.artifact, timeout), None
    except subprocess.TimeoutExpired:
        return None, f"artifact path expansion timed out after {timeout}s"


def preflight_refusal(leaf, default_timeout=DEFAULT_TIMEOUT_SECONDS, resolved=None):
    """Why this leaf must not publish, or None if it may.

    Returns None when the leaf declares no preflight - the check is opt-in, and a leaf that
    asks for nothing is not silently held to anything. `resolved` is an optional
    already-computed `(path, error)` pair from `_expand_artifact`, for a caller (the dry-run
    plan) that expanded `leaf.artifact` itself and would otherwise cause a second shell-out
    for the same expression; omit it and this expands it itself, exactly as before.
    """
    if not leaf.preflight:
        return None
    bad = unknown_rules(leaf.preflight)
    if bad:
        return f"unknown preflight rule(s): {', '.join(bad)}"
    if not leaf.artifact:
        return "preflight is declared but no artifact: is set - nothing to inspect"
    if resolved is None:
        resolved = _expand_artifact(leaf, effective_timeout(leaf, default_timeout))
    path, error = resolved
    if error:
        return error
    if not path or not pathlib.Path(path).is_file():
        return f"artifact not found: {path or leaf.artifact}"
    try:
        findings = inspect_archive(path, leaf.preflight)
    except UnsupportedArchive:
        return f"unsupported archive format, cannot inspect: {path}"
    if findings:
        return format_findings(findings)
    return None


def _accepted_detail(leaf, output):
    """The `accepted` line's detail: what happened, what has not, and how to find out.

    The action's own output goes last, not first. A real publish's capture is a wall of log,
    and the sentence that tells an operator this is not finished has to survive being read
    above it - see BACKLOG #15, where a correct message was unreadable in exactly this way.
    """
    how = "run --confirm" if leaf.confirm_command else "no confirm command declared"
    if leaf.confirm_url:
        how += f", or see {leaf.confirm_url}"
    parts = [f"upload accepted; not yet confirmed - {how}"]
    if output:
        parts.append(output)
    return "\n".join(parts)


def execute_plan(
    leaves,
    default_timeout=DEFAULT_TIMEOUT_SECONDS,
    command_key="action",
    allow_preflight_failure=False,
):
    """Run each leaf's command under `command_key`. One failure doesn't stop the others.

    Returns a list of (leaf, status, detail) - status is "success", "accepted", "failed",
    "timed out", "refused", or "not attempted". A leaf that declares `confirm` reports
    "accepted" rather than "success" on a zero-exit action: the upload genuinely succeeded
    and nothing went wrong, so the exit code stays 0, but it has not landed yet. detail is
    the command's real stdout on success, the real error text on failure, and the per-key
    "not set" wording when not attempted - never silently empty on success, since this is
    the only evidence an operator gets that a real publish actually happened.

    On the *action* path the order is **prepare -> inspect -> act**, and a tripped preflight
    rule reports "refused" without the action ever running. `--metrics` skips both gates
    entirely: it publishes nothing, so there is no irreversible step to gate, and running a
    project's build to answer a read-only download-count query would be wrong.
    """
    results = []
    for leaf in leaves:
        command = leaf.command(command_key)
        if not command:
            results.append((leaf, "not attempted", NOT_SET[command_key]))
            continue

        if command_key == GATED_COMMAND_KEY:
            if leaf.prepare:
                prepare_limit = effective_timeout(leaf, default_timeout)
                try:
                    rc, _out, err = _run(leaf.prepare, prepare_limit)
                except subprocess.TimeoutExpired:
                    results.append(
                        (leaf, "timed out", f"prepare timed out after {prepare_limit}s")
                    )
                    continue
                if rc != 0:
                    results.append(
                        (leaf, "failed", (err or "").strip() or f"prepare exited {rc}")
                    )
                    continue

            refusal = preflight_refusal(leaf, default_timeout)
            if refusal and not allow_preflight_failure:
                results.append((leaf, "refused", refusal))
                continue
            if refusal:
                print(f"warning: {leaf.dotted_path}: {refusal}", flush=True)

        limit = effective_timeout(leaf, default_timeout)
        try:
            returncode, stdout, stderr = _run(command, limit)
            if returncode != 0:
                raise subprocess.CalledProcessError(
                    returncode, command, output=stdout, stderr=stderr
                )
            detail = (stdout or "").strip()
            if command_key == GATED_COMMAND_KEY and leaf.confirm:
                results.append((leaf, "accepted", _accepted_detail(leaf, detail)))
            else:
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


def format_confirm_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS):
    """What `--confirm` will check, printed before it runs.

    Deliberately not `format_plan` with a third command key: `--confirm` publishes nothing, so
    there is no preflight or action-shape line to print, and half of what it reports is a URL
    rather than a command.
    """
    if not leaves:
        return "(no leaves selected)"
    lines = []
    for leaf in leaves:
        if leaf.confirm_command:
            lines.append(f"{leaf.dotted_path}: {leaf.confirm_command}")
            lines.append(f"  timeout: {effective_timeout(leaf, default_timeout)}s")
        elif leaf.confirm_url:
            lines.append(f"{leaf.dotted_path}: (needs a human) {leaf.confirm_url}")
        else:
            lines.append(f"{leaf.dotted_path}: ({NO_CONFIRM})")
    return "\n".join(lines)


def confirm_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS):
    """Check whether each selected leaf's accepted publish has actually landed.

    Publishes nothing. Returns (leaf, status, detail) with status "confirmed",
    "not confirmed", "needs a human", or "no confirm declared".

    Exit 0 from the command means confirmed and anything else means not confirmed - two
    states, not three. A three-state protocol distinguishing "not yet" from "the check itself
    broke" would have to be honoured by every project implementing `confirm`, and for gating
    purposes both answers mean do not advance. Which one it was belongs in the command's own
    output, which a human reads.

    A timeout is "not confirmed" for the same reason: it is not a positive answer, and this
    never waits on a remote publish by design.
    """
    results = []
    for leaf in leaves:
        command = leaf.confirm_command
        if not command:
            if leaf.confirm_url:
                results.append((leaf, "needs a human", leaf.confirm_url))
            else:
                results.append((leaf, "no confirm declared", NO_CONFIRM))
            continue

        # Built once and applied on every path below, timeout included - a hung check is
        # exactly when a human needs the declared page to look at, and this used to only
        # reach the success/non-zero paths.
        see_url = f"see {leaf.confirm_url}" if leaf.confirm_url else None

        limit = effective_timeout(leaf, default_timeout)
        try:
            returncode, stdout, stderr = _run(command, limit)
        except subprocess.TimeoutExpired as e:
            captured = "\n".join(filter(None, [_decode(e.stdout), _decode(e.stderr)]))
            detail = f"confirm timed out after {limit}s"
            if captured:
                detail += f"\n{captured}"
            detail = "\n".join(filter(None, [detail, see_url]))
            results.append((leaf, "not confirmed", detail))
            continue

        detail = "\n".join(filter(None, [(stdout or "").strip(), (stderr or "").strip()]))
        detail = "\n".join(filter(None, [detail, see_url]))
        results.append((leaf, "confirmed" if returncode == 0 else "not confirmed", detail))
    return results


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
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="check whether each selected leaf's already-accepted publish has actually "
        "landed, by running its `confirm.command` - publishes nothing",
    )
    parser.add_argument("--channels", default=".orclab/publish/channels.yaml")
    parser.add_argument("--distro", default=".orclab/publish/distro.yaml")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--allow-preflight-failure", action="store_true")
    args = parser.parse_args(argv)

    if is_bad_timeout(args.timeout):
        print(
            "error: --timeout must be a positive whole number of seconds, "
            f"got {args.timeout!r}",
            file=sys.stderr,
            flush=True,
        )
        return 1

    if args.confirm and (args.dry_run or args.metrics):
        other = "--dry-run" if args.dry_run else "--metrics"
        print(
            f"error: --confirm cannot be combined with {other} - --confirm is its own mode "
            "and publishes nothing. Run them separately.",
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

    bad_confirm = confirm_error(leaves)
    if bad_confirm:
        print(f"error: {bad_confirm}", file=sys.stderr, flush=True)
        return 1

    bad_command = command_error(leaves)
    if bad_command:
        print(f"error: {bad_command}", file=sys.stderr, flush=True)
        return 1

    if args.confirm:
        print(format_confirm_plan(leaves, default_timeout=args.timeout), flush=True)
        results = confirm_plan(leaves, default_timeout=args.timeout)
        print(format_summary(results), flush=True)
        return 0 if all(status != "not confirmed" for _, status, _ in results) else 1

    command_key = "metrics" if args.metrics else "action"
    print(format_plan(leaves, default_timeout=args.timeout, command_key=command_key), flush=True)

    if args.dry_run:
        return 0

    results = execute_plan(
        leaves,
        default_timeout=args.timeout,
        command_key=command_key,
        allow_preflight_failure=args.allow_preflight_failure,
    )
    print(format_summary(results), flush=True)
    return 0 if all(
        status not in ("failed", "timed out", "refused") for _, status, _ in results
    ) else 1


if __name__ == "__main__":
    sys.exit(main())
