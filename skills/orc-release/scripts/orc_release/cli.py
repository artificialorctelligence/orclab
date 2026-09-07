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
from .steps import doc_hash, parse_steps

DOC_NAME = "RELEASING.md"


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
    return text, parse_steps(text)


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
    state = st.load_state(root)
    if state is None:
        print("No release in progress.")
        return 0
    text, steps = _load_doc(root)
    if text is None:
        return 1
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


def cmd_complete(root, args):
    state = _require_state(root)
    if state is None:
        return 1
    text, steps = _load_doc(root)
    if text is None:
        return 1
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


def cmd_abort(root, _args):
    state = _require_state(root)
    if state is None:
        return 1
    text, steps = _load_doc(root)
    marked = {s.number for s in (steps or []) if s.is_irreversible}
    completed = state.get("completed", [])

    if state.get("previous_version"):
        for rel in vf.detect(root):
            if rel == vf.DEBIAN_CHANGELOG:
                continue  # a prepended entry is removed by hand; never rewrite history blindly
            try:
                vf.write_version(root, rel, state["previous_version"])
            except ValueError:
                pass
        print(f"Rolled version files back to {state['previous_version']}.")

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
    if vf.DEBIAN_CHANGELOG in vf.detect(root):
        print(
            f"Note: {vf.DEBIAN_CHANGELOG}'s new entry was left in place - remove it by hand if "
            f"you want it gone."
        )
    st.clear_state(root)
    print("Release aborted; state cleared.")
    return 0


def cmd_version_set(root, args):
    detected = vf.detect(root)
    if not detected:
        print("error: no known version-holding file in this project", file=sys.stderr)
        return 1
    for rel in detected:
        kwargs = {}
        if rel == vf.DEBIAN_CHANGELOG:
            if not args.changelog_body:
                print(
                    f"error: {rel} needs --changelog-body (its entry is prose, not a field)",
                    file=sys.stderr,
                )
                return 1
            kwargs["body"] = args.changelog_body
        vf.write_version(root, rel, args.version, **kwargs)
        print(f"Set {rel} to {args.version}.")
    return 0


def cmd_version_verify(root, _args):
    ok, versions = vf.verify_consistency(root)
    if ok:
        print(f"Version files are consistent: {versions or 'none found'}")
        return 0
    print(f"error: version files disagree: {versions}", file=sys.stderr)
    return 1


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
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("steps")
    sub.add_parser("status")
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
        "abort": cmd_abort,
        "version-set": cmd_version_set,
        "version-verify": cmd_version_verify,
        "version-rollback": cmd_version_rollback,
    }
    return handlers[args.cmd](args.root, args)


if __name__ == "__main__":
    sys.exit(main())
