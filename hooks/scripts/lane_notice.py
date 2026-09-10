#!/usr/bin/env python3
"""SessionStart: tell a new session what is already going on.

On 2026-09-08 two sessions built the same feature for two hours because nothing recorded that
the first had started. Nobody forgot to check - there was nothing to check. This is what makes
the lane record consulted without anyone remembering to.

Silent unless there is something to say. A hook that speaks every session gets tuned out.
"""

import json
import pathlib
import sys

from orclab_shared import shared_dir, uncommitted_entries


def _load(path):
    """The file's contents, or None when it exists but cannot be read.

    Missing and unreadable are different answers and the caller needs both. Silence is this
    hook's way of saying "nothing in progress", so a corrupt lane record must not produce it -
    that would fail into precisely the state the lane record exists to prevent.
    """
    path = pathlib.Path(path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def notice():
    d = shared_dir()
    if d is None:
        return ""
    lines = []
    lanes = _load(d / "lanes.json")
    if lanes is None:
        return ("Orclab shared state:\n  lanes.json is unreadable - what is in progress cannot "
                "be determined. Inspect it before starting work: /orc-todo lane list")
    for name, lane in sorted(lanes.items()):
        if lane.get("current"):
            since = f" since {lane['started']}" if lane.get("started") else ""
            lines.append(f"  lane {name}: {lane['current']} in progress{since}")
    if (d / "lock").exists():
        lock = _load(d / "lock") or {}
        lines.append(f"  lock held: {lock.get('description', 'unknown')} (pid {lock.get('pid')})")
    for filename, heading in uncommitted_entries():
        lines.append(f"  uncommitted in {filename}: {heading}")
    if not lines:
        return ""
    return "Orclab shared state:\n" + "\n".join(lines)


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    try:
        text = notice()
    except Exception:
        return 0  # fail open
    if text:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
