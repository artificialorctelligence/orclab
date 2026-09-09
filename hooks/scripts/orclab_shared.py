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


def uncommitted_entries(cwd=None):
    """Entry headings added but not committed, as [(filename, heading)].

    Read from the diff rather than by parsing the file, because only the diff distinguishes an
    entry that was just added from the hundreds already committed.
    """
    root = canonical_root(cwd)
    if root is None:
        return []
    found = []
    for name in TRACKED:
        if not (root / name).exists():
            continue
        diff = git(["-C", str(root), "diff", "--", name], cwd)
        if not diff:
            continue
        found.extend((name, m.group(1)) for m in ENTRY_RE.finditer(diff))
    return found
