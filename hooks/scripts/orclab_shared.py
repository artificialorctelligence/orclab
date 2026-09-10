"""Shared-dir resolution and uncommitted-entry detection, for the hooks.

A deliberate second copy of what skills/orc-todo/scripts/orc_todo/state.py already does. Hooks
run as standalone processes with their own working directory; a skill's scripts/ directory is
not on their path, and a sys.path insertion pointing into one would break the moment that skill
moved. Fifteen duplicated lines beat a hook that fails silently.

Everything here fails open: a hook that raises is worse than a hook that says nothing.
"""

import pathlib
import re
import subprocess

TRACKED = ("BACKLOG.md", "VERIFICATION.md")
ENTRY_RE = re.compile(r"^\+(## (?:#(\d+)|Scenario (\d+)): .*)$", re.MULTILINE)


def git(args, cwd=None):
    """Run git, returning stdout, or None if git failed for any reason at all."""
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def shared_dir(cwd=None):
    """<git-common-dir>/orclab, or None outside a repo. Never created here."""
    out = git(["rev-parse", "--git-common-dir"], cwd)
    if not out or not out.strip():
        return None
    base = pathlib.Path(cwd) if cwd else pathlib.Path.cwd()
    return (base / out.strip()).resolve() / "orclab"


def canonical_root(cwd=None):
    d = shared_dir(cwd)
    return d.parent.parent if d else None


def in_canonical_checkout(cwd=None):
    """Whether the caller's own working tree IS the canonical checkout.

    A discard command reaches only the tree it runs in. The allocator writes canonically, so an
    uncommitted entry normally lives there - and denying a worktree's `git reset --hard` because
    the main checkout has one tells the user to commit something their tree does not contain.
    Since an allocated entry is meant to sit uncommitted until someone deliberately commits it,
    that would deny every whole-tree discard in every worktree for as long as it sits there, in
    a project whose own workflow is worktree-based.
    """
    top = git(["rev-parse", "--show-toplevel"], cwd)
    root = canonical_root(cwd)
    if not top or root is None:
        return False
    return pathlib.Path(top.strip()).resolve() == root.resolve()


def uncommitted_entries(cwd=None):
    """Entry headings added but not committed, as [(filename, heading)].

    Read from the diff rather than by parsing the file, because only the diff distinguishes an
    entry that was just added from the hundreds already committed.

    Diffed against HEAD, not against the index. A bare `git diff` compares the working tree to
    what is staged, so an entry that has been `git add`ed reads as no change at all - and then
    `git reset --hard` destroys it with nothing said. Staged is still uncommitted, which is the
    only thing this function is being asked.
    """
    root = canonical_root(cwd)
    if root is None:
        return []
    found = []
    for name in TRACKED:
        if not (root / name).exists():
            continue
        diff = git(["-C", str(root), "diff", "HEAD", "--", name], cwd)
        if not diff:
            continue
        found.extend((name, m.group(1)) for m in ENTRY_RE.finditer(diff))
    return found
