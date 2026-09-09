"""/orc-todo: look at and manipulate the backlog, and see the lanes.

Everything the lock and the allocator do is invisible from here on purpose. This is the only
part of v16 with a user in front of it.
"""

import argparse
import pathlib
import re
import sys

from . import lanes as lanemod
from . import state
from .allocate import ResourceMissing, allocate
from .resources import RESOURCES

RESOLVED = re.compile(r"\(RESOLVED\b")
PARTIAL = re.compile(r"\(PARTIALLY ADDRESSED\b")
_HEADING = re.compile(r"^## #(\d+): ", re.MULTILINE)
_NEXT_SECTION = re.compile(r"^## ", re.MULTILINE)


def _backlog_path(cwd):
    return state.canonical_root(cwd) / "BACKLOG.md"


def _sections(text):
    """(number, title, body) for every backlog entry, in file order."""
    parts = re.split(r"^(## #(\d+): .*)$", text, flags=re.MULTILINE)
    out = []
    for i in range(1, len(parts), 3):
        heading, number, body = parts[i], int(parts[i + 1]), parts[i + 2]
        out.append((number, heading[len(f"## #{number}: "):].strip(), body))
    return out


def _read_backlog(cwd):
    path = _backlog_path(cwd)
    if not path.exists():
        raise ResourceMissing(f"no BACKLOG.md in this project (looked in {path.parent})")
    return path.read_text()


def cmd_list(args):
    text = _read_backlog(args.cwd)
    open_entries = [(n, t) for n, t, _ in _sections(text) if not RESOLVED.search(t)]
    if not open_entries:
        print("no open entries")
    for n, title in sorted(open_entries):
        mark = " [partial]" if PARTIAL.search(title) else ""
        print(f"  #{n}: {title}{mark}")
    running = {r["lane"]: r for r in lanemod.in_progress(args.cwd)}
    all_lanes = lanemod.read_lanes(args.cwd)
    if all_lanes:
        print("\nlanes:")
        for name, lane in sorted(all_lanes.items()):
            mark = f" (in progress: {running[name]['item']})" if name in running else ""
            print(f"  {name}: {', '.join(lane['items']) or '(empty)'}{mark}")
    return 0


def cmd_show(args):
    for n, title, body in _sections(_read_backlog(args.cwd)):
        if n == args.number:
            print(f"## #{n}: {title}")
            print(body.rstrip("\n"))
            return 0
    print(f"error: no entry #{args.number}", file=sys.stderr)
    return 1


def cmd_add(args):
    body = sys.stdin.read()
    if not body.strip():
        print(
            "error: an entry needs a real paragraph of context, not a stub - that is what "
            "makes it worth keeping. Pipe the body in on stdin.",
            file=sys.stderr,
        )
        return 1
    number = allocate(args.resource, args.title, body, cwd=args.cwd)
    print(f"allocated #{number} in {RESOURCES[args.resource].filename} (uncommitted)")
    return 0


def cmd_remove(args):
    """Delete an entry. Numbers are permanent: nothing is renumbered and the number is never
    reissued, which the counter guarantees by never going backwards.

    The entry is cut out of the real text rather than the file being rebuilt from parsed
    pieces. Rebuilding loses whatever the parser did not model - a header whose own prose
    happens to contain "## #", a note sitting between two entries, a closing section after the
    last one - and it loses it silently, with a zero exit. This is the file the whole mechanism
    exists to protect; it does not get to be lossy.

    An entry ends at the next "## " heading of any kind, not the next "## #N:". That is what
    lets a trailing section such as VERIFICATION.md's "## Recording the result" survive the
    removal of the entry above it.
    """
    path = _backlog_path(args.cwd)
    text = _read_backlog(args.cwd)
    starts = [(int(m.group(1)), m.start()) for m in _HEADING.finditer(text)]
    for i, (number, start) in enumerate(starts):
        if number != args.number:
            continue
        after = _NEXT_SECTION.search(text, start + 1)
        end = after.start() if after else len(text)
        state.atomic_write(path, (text[:start].rstrip("\n") + "\n\n" + text[end:]).rstrip("\n") + "\n")
        print(f"removed #{args.number}; nothing renumbered, and #{args.number} is never reissued")
        return 0
    print(f"error: no entry #{args.number}", file=sys.stderr)
    return 1


def cmd_lane(args):
    items = [i.strip() for i in args.items.split(",") if i.strip()] if getattr(args, "items", None) else []
    if args.lane_command == "list":
        all_lanes = lanemod.read_lanes(args.cwd)
        if not all_lanes:
            print("no lanes")
        for name, lane in sorted(all_lanes.items()):
            current = f" (in progress: {lane['current']})" if lane.get("current") else ""
            print(f"  {name}: {', '.join(lane['items']) or '(empty)'}{current}")
    elif args.lane_command == "create":
        print(f"  {args.name}: {', '.join(lanemod.create_lane(args.name, items, args.cwd)['items'])}")
    elif args.lane_command == "modify":
        print(f"  {args.name}: {', '.join(lanemod.modify_lane(args.name, items, args.cwd)['items'])}")
    elif args.lane_command == "delete":
        lanemod.delete_lane(args.name, args.cwd)
        print(f"deleted lane {args.name}")
    elif args.lane_command == "current":
        item = None if args.item == "-" else args.item
        lanemod.set_current(args.name, item, args.cwd)
        print(f"  {args.name}: {'in progress on ' + item if item else 'idle'}")
    return 0


def cmd_lock(args):
    if args.lock_command == "status":
        info = state.lock_info(args.cwd)
        if not info:
            print("lock is not held")
            return 0
        age = f"{int(info['age_seconds'])}s" if info["age_seconds"] is not None else "unknown age"
        alive = "running" if info["alive"] else "NOT running - apparently stale"
        print(f"lock held by pid {info['pid']} ({alive}), {age}: {info['description']}")
        if not info["alive"]:
            print("A lock found when none is expected is worth investigating before clearing.")
        return 0
    print("cleared the lock" if state.clear_lock(args.cwd) else "no lock was held")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="orc-todo")
    p.add_argument("--cwd", default=None, help="operate on this project (default: current dir)")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list")
    show = sub.add_parser("show")
    show.add_argument("number", type=int)

    add = sub.add_parser("add")
    add.add_argument("resource", choices=sorted(RESOURCES))
    add.add_argument("title")

    rm = sub.add_parser("remove")
    rm.add_argument("number", type=int)

    lane = sub.add_parser("lane")
    lanesub = lane.add_subparsers(dest="lane_command", required=True)
    lanesub.add_parser("list")
    for name in ("create", "modify"):
        q = lanesub.add_parser(name)
        q.add_argument("name")
        q.add_argument("items")
    lanesub.add_parser("delete").add_argument("name")
    cur = lanesub.add_parser("current")
    cur.add_argument("name")
    cur.add_argument("item")

    lock = sub.add_parser("lock")
    locksub = lock.add_subparsers(dest="lock_command", required=True)
    locksub.add_parser("status")
    locksub.add_parser("clear")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.cwd = pathlib.Path(args.cwd) if args.cwd else pathlib.Path.cwd()
    handlers = {
        "list": cmd_list, "show": cmd_show, "add": cmd_add,
        "remove": cmd_remove, "lane": cmd_lane, "lock": cmd_lock,
    }
    try:
        return handlers[args.command](args)
    except state.NotAGitRepo as e:
        print(f"error: {e} - /orc-todo needs a git repository", file=sys.stderr)
        return 1
    except (ResourceMissing, lanemod.UnspeccedItem, lanemod.LaneMissing, lanemod.LaneStateCorrupt) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except state.LockUnavailable as e:
        print(f"error: {e}. See /orc-todo lock status", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
