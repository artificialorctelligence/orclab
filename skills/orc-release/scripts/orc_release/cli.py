"""/orc-release CLI: the deterministic half of driving a release.

This script never decides whether a step passed - that is Claude's judgment, made against the
document's own "what done looks like". What lives here is what must be exactly right every time:
parsing the document, tracking position, and writing version files.

There is no confirmation prompt anywhere in this module. The gates are conversational and live
in SKILL.md, the same division /orc-publish uses.
"""

import argparse
import dataclasses
import json
import os
import sys

from . import state as st
from . import versionfiles as vf
from .steps import doc_hash, numbering_warning, parse_steps, unclosed_fence_warning

DOC_NAME = "RELEASING.md"


def find_project_root(start="."):
    """Walk up from `start` to the git root, falling back to `start` itself.

    Defaulting to the process's cwd made every subcommand report "no RELEASING.md in this
    project" from any subdirectory - a false negative on the one message that must never be
    wrong, told to a user who does have one. --root still overrides this explicitly.
    """
    start = os.path.abspath(start)
    d = start
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return start
        d = parent


def _load_doc(root):
    """Return (text, steps) or (None, None) after reporting a missing document."""
    path = os.path.join(root, DOC_NAME)
    try:
        with open(path) as f:
            text = f.read()
    except FileNotFoundError:
        print(
            f"error: no {DOC_NAME} in this project - nothing to drive. "
            f"Use the release-checklist skill to create one; never invent a release process.",
            file=sys.stderr,
        )
        return None, None
    steps = parse_steps(text)
    for warning in (unclosed_fence_warning(text), numbering_warning(steps)):
        if warning:
            print(warning, file=sys.stderr)
    return text, steps


def _require_state(root):
    state = st.load_state(root)
    if state is None:
        print("error: no release in progress", file=sys.stderr)
    return state


def cmd_steps(root, _args):
    text, steps = _load_doc(root)
    if text is None:
        return 1
    print(json.dumps([dataclasses.asdict(s) for s in steps], indent=2))
    return 0


def cmd_status(root, _args):
    # The document is loaded first so its own problems (missing, oddly numbered) are reported
    # even when no release has started - that is exactly when they are cheapest to fix.
    text, steps = _load_doc(root)
    if text is None:
        return 1
    state = st.load_state(root)
    if state is None:
        print("No release in progress.")
        return 0
    print(f"Release {state['version']} in progress (was {state['previous_version']}).")
    if doc_hash(text) != state["doc_hash"]:
        print(
            f"WARNING: {DOC_NAME} has CHANGED since this release started. Step numbers may "
            f"have shifted - re-read it before continuing."
        )
    done = st.completed_numbers(state)
    print(f"Completed: {done or 'none'}")
    for s in state.get("skipped", []):
        print(f"  skipped {s['number']} ({s['title']}): {s['reason']}")
    nxt = st.next_step_number(state, [s.number for s in steps])
    print(f"Next: step {nxt}" if nxt else "All steps finished.")
    return 0


def cmd_start(root, args):
    if st.is_in_progress(root):
        print(
            "error: a release is already in progress - resume it or abort it first",
            file=sys.stderr,
        )
        return 1
    text, _ = _load_doc(root)
    if text is None:
        return 1
    detected = vf.detect(root)
    previous = vf.read_version(root, detected[0]) if detected else None
    st.start_release(root, args.version, previous, DOC_NAME, doc_hash(text))
    print(f"Started release {args.version} (previous: {previous}).")
    return 0


def _step_by_number(steps, number):
    for s in steps:
        if s.number == number:
            return s
    return None


def _warn_if_doc_changed(text, state):
    """Print (never block on) a stderr warning when the document has moved since release start.

    complete/skip resolve step numbers against whatever the document says right now - if it was
    edited mid-release, "step 3" may no longer mean what it meant when the release started. This
    can never be silent, but it also can never refuse: refusing would strand a user mid-release
    with abort as their only way out, including when the edit was deliberate.
    """
    if doc_hash(text) != state.get("doc_hash"):
        print(
            f"warning: {DOC_NAME} has changed since this release started - step numbers may "
            f"have shifted.",
            file=sys.stderr,
        )


def cmd_complete(root, args):
    state = _require_state(root)
    if state is None:
        return 1
    text, steps = _load_doc(root)
    if text is None:
        return 1
    _warn_if_doc_changed(text, state)
    step = _step_by_number(steps, args.number)
    if step is None:
        print(f"error: no step {args.number} in {DOC_NAME}", file=sys.stderr)
        return 1
    try:
        st.mark_complete(state, step.number, step.title, irreversible=step.is_irreversible)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    st.save_state(root, state)
    print(f"Step {step.number} ({step.title}) complete.")
    return 0


def cmd_skip(root, args):
    state = _require_state(root)
    if state is None:
        return 1
    text, steps = _load_doc(root)
    if text is None:
        return 1
    _warn_if_doc_changed(text, state)
    step = _step_by_number(steps, args.number)
    if step is None:
        print(f"error: no step {args.number} in {DOC_NAME}", file=sys.stderr)
        return 1
    try:
        st.mark_skipped(state, step.number, step.title, args.reason)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    st.save_state(root, state)
    print(f"Step {step.number} ({step.title}) skipped: {args.reason.strip()}")
    return 0


def cmd_finish(root, _args):
    """Close a release that actually shipped. Clears state; rolls back NOTHING.

    Without this, a finished release had no exit at all: state was permanent, the next start was
    refused forever, and the only documented way out was abort - which rolls the version files
    back to their pre-release values on a repo whose release commit and tag already exist, and
    reports that as success.
    """
    state = _require_state(root)
    if state is None:
        return 1
    text, steps = _load_doc(root)
    if text is None:
        return 1
    _warn_if_doc_changed(text, state)
    nxt = st.next_step_number(state, [s.number for s in steps])
    if nxt is not None:
        step = _step_by_number(steps, nxt)
        print(
            f"error: step {nxt} ({step.title}) is not finished - complete or skip it before "
            f"finishing the release",
            file=sys.stderr,
        )
        return 1

    print(f"Release {state['version']} finished (previous version: {state['previous_version']}).")
    for c in state.get("completed", []):
        print(f"  completed {c['number']} ({c['title']})")
    for s in state.get("skipped", []):
        print(f"  skipped {s['number']} ({s['title']}): {s['reason']}")
    for c in st.irreversible_completed(state):
        print(f"  irreversible and now permanent: step {c['number']} ({c['title']})")
    st.clear_state(root)
    print("State cleared. Nothing was rolled back; the release stands as shipped.")
    return 0


def cmd_abort(root, _args):
    state = _require_state(root)
    if state is None:
        return 1
    text, steps = _load_doc(root)
    marked = {s.number for s in (steps or []) if s.is_irreversible}
    completed = state.get("completed", [])

    if state.get("previous_version"):
        rolled_back = []
        failed = []
        for rel in vf.detect(root):
            if rel == vf.DEBIAN_CHANGELOG:
                continue  # a prepended entry is removed by hand; never rewrite history blindly
            try:
                vf.write_version(root, rel, state["previous_version"])
                rolled_back.append(rel)
            except (ValueError, OSError) as e:
                failed.append((rel, str(e)))
        # Never claim a rollback that did not happen - report exactly what succeeded and what
        # didn't, with the real error, rather than one blanket success line covering both.
        if rolled_back:
            print(
                f"Rolled back to {state['previous_version']}: " + ", ".join(rolled_back)
            )
        for rel, err in failed:
            print(f"NOT rolled back - {rel}: {err}")
        if not rolled_back and not failed:
            print("No version files needed rolling back.")

    if completed and not marked:
        print(
            "Completed steps: "
            + ", ".join(f"{c['number']} ({c['title']})" for c in completed)
        )
        print(
            "This document marks no steps irreversible, so I CANNOT DETERMINE which of these "
            "had effects outside this repo. Check them yourself before assuming anything was "
            "undone."
        )
    else:
        for c in st.irreversible_completed(state):
            print(
                f"Step {c['number']} ({c['title']}) is irreversible and completed - "
                f"it STANDS and was not undone."
            )
    leftovers = []
    if state.get("changelog_written") and vf.DEBIAN_CHANGELOG in vf.detect(root):
        leftovers.append(
            f"{vf.DEBIAN_CHANGELOG}'s new entry was left in place - remove it by hand if you "
            f"want it gone."
        )
    if os.path.exists(os.path.join(root, "CHANGELOG.md")):
        leftovers.append(
            "CHANGELOG.md is not touched by abort - if /orc-version drafted an entry for this "
            "release, remove it by hand."
        )
    # Abort's rollback is deliberately partial (a prepended changelog entry is never rewritten
    # blindly), so it can leave the project's own version-verify reporting a broken state. Saying
    # "rolled back" and stopping there hides that; name the disagreement and the real versions.
    try:
        ok, versions = vf.verify_consistency(root)
    except (OSError, ValueError) as e:
        print(f"Could not check whether the version files agree ({e}) - check them by hand.")
    else:
        if not ok:
            print("The project's version files now DISAGREE - clean this up by hand:")
            for rel, v in sorted(versions.items()):
                print(f"  {rel}: {v}")
    for note in leftovers:
        print(f"Note: {note}")
    st.clear_state(root)
    print("Release aborted; state cleared.")
    return 0


def cmd_version_set(root, args):
    detected = vf.detect(root)
    if not detected:
        print("error: no known version-holding file in this project", file=sys.stderr)
        return 1
    # Validate every detected file's required input before writing any of them - writing some
    # files, then erroring on a later one, leaves a real project in a state its own
    # verify_consistency reports as broken.
    if vf.DEBIAN_CHANGELOG in detected and not args.changelog_body:
        print(
            f"error: {vf.DEBIAN_CHANGELOG} needs --changelog-body (its entry is prose, not a "
            f"field) - nothing was written",
            file=sys.stderr,
        )
        return 1
    # ...and read every detected file before writing any of them. Pre-validating only the
    # changelog body left the same hole it was meant to close: a corrupt plugin.json wrote
    # pyproject.toml first, then died with a raw JSONDecodeError traceback, leaving exactly the
    # half-written state this check exists to prevent.
    unreadable = []
    for rel in detected:
        try:
            vf.read_version(root, rel)
        except (OSError, ValueError) as e:
            unreadable.append((rel, e))
    if unreadable:
        for rel, e in unreadable:
            print(f"error: cannot read {rel}: {e}", file=sys.stderr)
        print("error: nothing was written", file=sys.stderr)
        return 1
    for rel in detected:
        kwargs = {"body": args.changelog_body} if rel == vf.DEBIAN_CHANGELOG else {}
        vf.write_version(root, rel, args.version, **kwargs)
        print(f"Set {rel} to {args.version}.")
    if vf.DEBIAN_CHANGELOG in detected:
        state = st.load_state(root)
        if state is not None:
            state["changelog_written"] = True
            st.save_state(root, state)
    return 0


def cmd_version_verify(root, _args):
    ok, versions = vf.verify_consistency(root)
    if not ok:
        print(f"error: version files disagree: {versions}", file=sys.stderr)
        return 1
    # Agreeing with each other is not the same as agreeing with the release. A bad merge that
    # moves every file to one consistent but wrong version passes the check above; the state
    # cursor knows the target, which is the whole reason it records it.
    state = st.load_state(root)
    if state is not None and versions:
        found = sorted(set(versions.values()))[0]
        if found != state["version"]:
            print(
                f"error: version files agree on {found}, but this release targets "
                f"{state['version']}: {versions}",
                file=sys.stderr,
            )
            return 1
    print(f"Version files are consistent: {versions or 'none found'}")
    return 0


def cmd_version_rollback(root, _args):
    state = _require_state(root)
    if state is None:
        return 1
    previous = state.get("previous_version")
    if not previous:
        print("error: no previous version recorded to roll back to", file=sys.stderr)
        return 1
    for rel in vf.detect(root):
        if rel == vf.DEBIAN_CHANGELOG:
            continue
        vf.write_version(root, rel, previous)
        print(f"Rolled {rel} back to {previous}.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="orc-release")
    parser.add_argument("--root", default=None, help="project root (default: the git root)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("steps")
    sub.add_parser("status")
    sub.add_parser("finish")
    sub.add_parser("abort")
    sub.add_parser("version-verify")
    sub.add_parser("version-rollback")

    p_start = sub.add_parser("start")
    p_start.add_argument("version")

    p_complete = sub.add_parser("complete")
    p_complete.add_argument("number", type=int)

    p_skip = sub.add_parser("skip")
    p_skip.add_argument("number", type=int)
    p_skip.add_argument("--reason", required=True)

    p_vset = sub.add_parser("version-set")
    p_vset.add_argument("version")
    p_vset.add_argument("--changelog-body")

    args = parser.parse_args(argv)
    handlers = {
        "steps": cmd_steps,
        "status": cmd_status,
        "start": cmd_start,
        "complete": cmd_complete,
        "skip": cmd_skip,
        "finish": cmd_finish,
        "abort": cmd_abort,
        "version-set": cmd_version_set,
        "version-verify": cmd_version_verify,
        "version-rollback": cmd_version_rollback,
    }
    root = args.root if args.root is not None else find_project_root()
    return handlers[args.cmd](root, args)


if __name__ == "__main__":
    sys.exit(main())
