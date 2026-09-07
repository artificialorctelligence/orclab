"""The release position cursor.

This records WHERE a release is, never WHAT its steps are - RELEASING.md is the single
definition of the steps, and nothing here duplicates it, so there is nothing to drift.

The stored doc_hash is load-bearing: release-checklist explicitly renumbers steps when one is
inserted mid-document, so a document edited mid-release can make a recorded "step 7" mean a
different step than the one that was actually run.
"""

import datetime
import json
import os

STATE_PATH = ".orclab/release/state.json"


def _path(root):
    return os.path.join(root, STATE_PATH)


def _now():
    return datetime.datetime.now().astimezone().isoformat()


def start_release(root, version, previous_version, doc_path, doc_hash):
    """Create and persist fresh release state. previous_version is what rollback restores."""
    state = {
        "version": version,
        "previous_version": previous_version,
        "doc_path": doc_path,
        "doc_hash": doc_hash,
        "completed": [],
        "skipped": [],
        "started_at": _now(),
        "updated_at": _now(),
    }
    save_state(root, state)
    return state


def load_state(root):
    """Return the in-progress release state, or None if there isn't one."""
    try:
        with open(_path(root)) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def save_state(root, state):
    state["updated_at"] = _now()
    path = _path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def is_in_progress(root):
    return load_state(root) is not None


def mark_complete(state, number, title, irreversible=False):
    """Record a step as done. Idempotent - re-running a step does not duplicate the entry."""
    if number not in completed_numbers(state):
        state["completed"].append(
            {"number": number, "title": title, "irreversible": bool(irreversible)}
        )
    return state


def mark_skipped(state, number, title, reason):
    """Record a step as deliberately skipped. A reason is required, never optional."""
    if not reason or not reason.strip():
        raise ValueError("a skip requires a real reason")
    state["skipped"].append(
        {"number": number, "title": title, "reason": reason.strip()}
    )
    return state


def completed_numbers(state):
    """Step numbers that are finished - completed or deliberately skipped."""
    done = [c["number"] for c in state.get("completed", [])]
    done += [s["number"] for s in state.get("skipped", [])]
    return sorted(set(done))


def next_step_number(state, all_numbers):
    """The first step number not yet finished, or None if the release is complete."""
    done = set(completed_numbers(state))
    for n in sorted(all_numbers):
        if n not in done:
            return n
    return None


def irreversible_completed(state):
    """Completed steps the document marked irreversible - what abort cannot undo."""
    return [c for c in state.get("completed", []) if c.get("irreversible")]


def clear_state(root):
    try:
        os.remove(_path(root))
    except FileNotFoundError:
        pass
