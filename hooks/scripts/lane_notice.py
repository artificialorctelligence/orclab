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
    try:
        return json.loads(pathlib.Path(path).read_text())
    except (OSError, ValueError):
        return {}


def notice():
    d = shared_dir()
    if d is None:
        return ""
    lines = []
    for name, lane in sorted(_load(d / "lanes.json").items()):
        if lane.get("current"):
            since = f" since {lane['started']}" if lane.get("started") else ""
            lines.append(f"  lane {name}: {lane['current']} in progress{since}")
    lock = _load(d / "lock")
    if (d / "lock").exists():
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
