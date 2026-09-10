"""Lanes: N ordered lists of work that run concurrently. A record, never a runner.

Nothing here launches a session, supervises a process, or handles a crash. Ordering and mutual
exclusion are deliberately separate mechanisms - a lane needs no lock to be ordered, and the
lock needs no lane to be correct (BACKLOG #22).

A lane item is a design spec or an implementation plan, named vNN. Not a backlog number: #12 is
a resolved entry about publish pipeline gaps while v12 is the preflight work, and the real
mapping is many-to-many - v14 and v15 both derive primarily from #17.
"""

import datetime
import json
import re

from . import state

SPEC_DIRS = ("docs/superpowers/specs", "docs/superpowers/plans")


class UnspeccedItem(Exception):
    """No spec or plan exists for this item, so it cannot join a lane yet."""

    def __init__(self, message, item):
        super().__init__(message)
        self.item = item


class LaneMissing(Exception):
    """No such lane, or no such item within it."""


class LaneExists(Exception):
    """A lane by that name is already there. Recreating it would erase what it was doing."""


class LaneStateCorrupt(Exception):
    """lanes.json exists but cannot be parsed."""


def _lanes_path(cwd=None):
    return state.shared_dir(cwd) / "lanes.json"


def spec_files(item, cwd=None):
    """Every spec or plan file naming this item, e.g. v13 -> .../...-orclab-v13-...md."""
    root = state.canonical_root(cwd)
    pattern = re.compile(rf"(^|[-_]){re.escape(item)}([-_.]|$)")
    found = []
    for d in SPEC_DIRS:
        directory = root / d
        if directory.is_dir():
            found.extend(p for p in sorted(directory.glob("*.md")) if pattern.search(p.stem))
    return found


def _require_specced(items, cwd=None):
    for item in items:
        if not spec_files(item, cwd):
            raise UnspeccedItem(
                f"'{item}' has no spec or plan under {' or '.join(SPEC_DIRS)}. "
                "Spec it first - an unspecced item is genuinely ambiguous.",
                item,
            )


def read_lanes(cwd=None):
    """Every lane. Empty when the file has never been written; raises when it is unreadable.

    Those two cases must not collapse into one. Reading a corrupt file as "no lanes" would let
    the very next create/modify/delete write a single lane back over every other one, losing
    them all with nothing reported. Absent is normal; unreadable is a fault.
    """
    path = _lanes_path(cwd)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError) as e:
        raise LaneStateCorrupt(
            f"{path} exists but cannot be read: {e}. Nothing has been changed. "
            "Inspect it before any lane command writes over it."
        ) from e


def _write_lanes(data, cwd=None):
    state.atomic_write(_lanes_path(cwd), json.dumps(data, indent=2, sort_keys=True) + "\n")


def create_lane(name, items, cwd=None):
    """Create a lane. Refuses to overwrite one that already exists.

    Recreating a lane resets `current` to None, and that marker is the single record stopping a
    second agent from rebuilding what a first is already building. A create where modify was
    meant is an ordinary typo; erasing the in-progress marker on it, silently and with a zero
    exit, is the 2026-09-08 failure handed back.
    """
    _require_specced(items, cwd)   # validate before taking the lock, and before any write
    with state.held(f"creating lane {name}", cwd=cwd):
        data = read_lanes(cwd)
        if name in data:
            raise LaneExists(
                f"lane '{name}' already exists (items: {', '.join(data[name]['items']) or 'none'}). "
                "Use `lane modify` to change its items - creating it again would clear what it "
                "is working on."
            )
        data[name] = {"items": list(items), "current": None, "started": None}
        _write_lanes(data, cwd)
    return data[name]


def modify_lane(name, items, cwd=None):
    """Replace the item list. Covers reorder, add and drop in one operation.

    A current item that survives the change stays current; one that was dropped is cleared,
    because a lane cannot be in progress on something it no longer contains.
    """
    _require_specced(items, cwd)
    with state.held(f"modifying lane {name}", cwd=cwd):
        data = read_lanes(cwd)
        if name not in data:
            raise LaneMissing(f"no lane named '{name}'")
        lane = data[name]
        lane["items"] = list(items)
        if lane.get("current") not in items:
            lane["current"] = None
            lane["started"] = None
        _write_lanes(data, cwd)
    return data[name]


def delete_lane(name, cwd=None):
    with state.held(f"deleting lane {name}", cwd=cwd):
        data = read_lanes(cwd)
        if name not in data:
            raise LaneMissing(f"no lane named '{name}'")
        del data[name]
        _write_lanes(data, cwd)


def set_current(name, item, cwd=None):
    """Mark which item a lane is working on. item=None clears it."""
    with state.held(f"advancing lane {name}", cwd=cwd):
        data = read_lanes(cwd)
        if name not in data:
            raise LaneMissing(f"no lane named '{name}'")
        lane = data[name]
        if item is not None and item not in lane["items"]:
            raise LaneMissing(f"lane '{name}' does not contain '{item}'")
        lane["current"] = item
        lane["started"] = datetime.datetime.now().astimezone().isoformat() if item else None
        _write_lanes(data, cwd)
    return data[name]


def in_progress(cwd=None):
    """Every lane currently working on something. This is what stops a duplicate build."""
    return [
        {"lane": name, "item": lane["current"], "started": lane.get("started")}
        for name, lane in sorted(read_lanes(cwd).items())
        if lane.get("current")
    ]
