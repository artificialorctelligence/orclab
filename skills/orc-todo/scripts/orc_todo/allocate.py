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

import os

from . import state
from .resources import RESOURCES, insert, render, scan_max


class ResourceMissing(Exception):
    """The project has no such file. Never create one - a project without a BACKLOG.md has
    not opted into having one."""


def canonical_file(resource, cwd=None):
    """The one real file every agent reaches, in the main checkout - not the caller's copy."""
    return state.canonical_root(cwd) / resource.filename


def _atomic_write(path, text):
    """Replace the file's contents in one step, never leaving it half-written.

    path.write_text() truncates and then writes, so a crash in that window leaves the file
    empty - and this is the file the allocator deliberately never commits, so there is no
    committed copy to recover from. os.replace() is atomic on POSIX: a reader sees the old file
    or the new one, never a torn one.

    The temp file sits in the same directory on purpose. os.replace is only atomic within one
    filesystem, and /tmp is routinely a different one.
    """
    tmp = path.with_name(f".{path.name}.tmp{os.getpid()}")
    tmp.write_text(text)
    os.replace(tmp, path)


def next_number(resource, cwd=None):
    """max(stored counter, file scan) + 1. Call only inside a held lock.

    Both sources are consulted because each covers the other's failure. A lost counter (fresh
    clone, cleaned .git) would reissue numbers the file already has; a file whose highest entry
    was deleted would reissue a number the counter remembers, and backlog numbers are permanent
    and never reused.
    """
    path = canonical_file(resource, cwd)
    if not path.exists():
        raise ResourceMissing(f"{resource.filename} not found at {path}")
    stored = state.read_counters(cwd).get(resource.key, 0)
    return max(stored, scan_max(path.read_text(), resource)) + 1


def allocate(resource_key, title, body, cwd=None, timeout=10.0):
    """Allocate the next number, write the entry into the canonical file, return the number."""
    resource = RESOURCES[resource_key]
    path = canonical_file(resource, cwd)
    if not path.exists():
        raise ResourceMissing(f"{resource.filename} not found at {path}")
    with state.held(f"allocating a {resource.key} number", cwd=cwd, timeout=timeout):
        number = next_number(resource, cwd)
        _atomic_write(path, insert(path.read_text(), resource, render(resource, number, title, body)))
        counters = state.read_counters(cwd)
        counters[resource.key] = number
        state.write_counters(counters, cwd)
    return number
