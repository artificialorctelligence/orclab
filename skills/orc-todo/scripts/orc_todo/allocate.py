"""Allocate a number and write the entry, in one lock hold.

The allocator owns the write rather than handing out a number and trusting the caller, because
there is then nothing to bypass: an agent cannot take a number and forget to use it, or write
without taking one.

It stops short of committing. Correctness does not need it - every agent reads the same
canonical file, so an entry is visible the instant it is written - and committing would mean
running git in a checkout the agent does not own, sweeping whatever uncommitted work is in that
file into a commit that claims to be a backlog entry. The durability that buys is paid for
instead by hooks/scripts/backlog_guard.py, which asks before anything discards an uncommitted
entry.
"""

from . import state
from .resources import RESOURCES, insert, render, scan_max


class ResourceMissing(Exception):
    """The project has no such file. Never create one - a project without a BACKLOG.md has
    not opted into having one."""


def canonical_file(resource, cwd=None):
    """The one real file every agent reaches, in the main checkout - not the caller's copy."""
    return state.canonical_root(cwd) / resource.filename


def target_file(resource, cwd=None):
    """Where the text lands. The number is always canonical; the text is only for a backlog
    entry. A verification scenario written during feature work describes behaviour that exists
    only on that branch, so it goes into the checkout the command ran in (BACKLOG #30). In the
    main checkout the two are the same file."""
    if resource.canonical_text:
        return canonical_file(resource, cwd)
    return state.invoking_root(cwd) / resource.filename


def next_number(resource, cwd=None):
    """max(stored counter, file scans) + 1. Call only inside a held lock.

    Both sources are consulted because each covers the other's failure. A lost counter (fresh
    clone, cleaned .git) would reissue numbers the file already has; a file whose highest entry
    was deleted would reissue a number the counter remembers, and backlog numbers are permanent
    and never reused.

    Both the canonical file and the target are scanned. They differ only for a scenario written
    on a branch, and there the counter is what keeps the number unique across branches; the
    scan of the target is the lost-counter fallback for the one file the canonical scan cannot
    see.
    """
    target = target_file(resource, cwd)
    if not target.exists():
        raise ResourceMissing(f"{resource.filename} not found at {target}")
    paths = {canonical_file(resource, cwd), target}
    stored = state.read_counters(cwd).get(resource.key, 0)
    scanned = max(scan_max(p.read_text(), resource) for p in paths if p.exists())
    return max(stored, scanned) + 1


def allocate(resource_key, title, body, cwd=None, timeout=10.0):
    """Allocate the next number, write the entry into the target file, return the number."""
    resource = RESOURCES[resource_key]
    path = target_file(resource, cwd)
    if not path.exists():
        raise ResourceMissing(f"{resource.filename} not found at {path}")
    with state.held(f"allocating a {resource.key} number", cwd=cwd, timeout=timeout):
        number = next_number(resource, cwd)
        state.atomic_write(path, insert(path.read_text(), resource, render(resource, number, title, body)))
        counters = state.read_counters(cwd)
        counters[resource.key] = number
        state.write_counters(counters, cwd)
    return number
