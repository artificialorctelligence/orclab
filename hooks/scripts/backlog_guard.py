#!/usr/bin/env python3
"""PreToolUse guard: consent before a command discards an uncommitted backlog entry.

The allocator writes entries without committing them - see orc_todo/allocate.py for why - so
real findings sit in the canonical working tree until someone commits. Several ordinary git
commands throw exactly that away.

Two conditions, both required, and the second is what keeps this usable: the command must
really discard a tracked modification, AND there must actually be an uncommitted entry to lose.
A guard that fires on every `git checkout` is noise, and noise gets waved through - which is the
failure it exists to prevent.

Which commands qualify was settled empirically, not by intuition (2026-09-09): `git clean` only
removes untracked files, and `git checkout <branch>` carries a modification over rather than
discarding it. Neither belongs here, and both were in the first draft.

`permissionDecision` has no "ask" - only "allow" and "deny", per the live hooks docs checked
2026-09-09. So this denies, with a `# orclab:discard-entries` escape marker mirroring
secret_guard.py's `# orclab:allow-secret`.

Contract: read the hook payload as JSON on stdin, print a `hookSpecificOutput` decision on
stdout, exit 0. Any other exit status is a non-blocking error, so every unexpected failure here
lets the command through rather than wedging the shell.
"""

import json
import re
import sys

from orclab_shared import in_canonical_checkout, uncommitted_entries

ALLOW_MARKER = "orclab:discard-entries"

# Only forms that really discard a TRACKED modification - verified empirically 2026-09-09.
# `git clean` touches only untracked files, and `git checkout <branch>` carries the edit over
# (git refuses rather than overwriting), so neither belongs here. A guard that fires on
# `git checkout main` is noise, and noise gets waved through.
#
# Two shapes, because they need different tests. A whole-tree discard takes no pathspec and
# always reaches every tracked file. A path-scoped one reaches only what it names, so naming
# something else is not a risk - and denying `git restore README.md` is the same noise as
# denying `git checkout main`, just rarer and therefore more annoying when it lands.
# The forced forms belong with the whole-tree ones. The docstring above is right that git
# REFUSES an unforced branch switch rather than overwriting - which is exactly why someone
# reaches for -f next, and that one really does destroy the edit. Verified 2026-09-09.
WHOLE_TREE = re.compile(
    r"\bgit\s+(?:"
    r"reset\s+(?:--hard|--merge|--keep)\b"
    r"|stash\b(?!\s+(?:list|show|apply|pop))"
    r"|(?:checkout|switch)\s+(?:\S+\s+)*(?:-f\b|--force\b|--discard-changes\b)"
    r")"
)
# --staged alone only unstages, so it is excluded; --staged --worktree discards both and is not.
PATH_SCOPED = re.compile(
    r"\bgit\s+(?:restore\b(?!\s+--staged\b(?!\s+--worktree\b))|checkout\s+)")
# A pathspec that could contain a tracked file: one of them by name, or a whole-tree sweep.
REACHES_TRACKED = re.compile(r"(?:BACKLOG|VERIFICATION)\.md\b|(?<![\w./-])[.*](?:\s|$)")


def _discards(command):
    """Whether this command can really destroy an uncommitted entry.

    A whole-tree discard always can. A path-scoped one can only reach what its pathspec names,
    so it counts only when that pathspec is a tracked file or a whole-tree sweep. Firing on
    `git restore README.md` would be the same noise as firing on `git checkout main`, and the
    brief settled that one empirically: noise gets waved through, which is the failure this
    guard exists to prevent.
    """
    if WHOLE_TREE.search(command):
        return True
    return bool(PATH_SCOPED.search(command) and REACHES_TRACKED.search(command))


def evaluate(command):
    """The refusal reason, or None when this command is not a risk right now."""
    if ALLOW_MARKER in command:
        return None
    if not _discards(command):
        return None
    if not in_canonical_checkout():
        return None  # this tree cannot reach the canonical file; nothing here is at risk
    at_risk = uncommitted_entries()
    if not at_risk:
        return None
    listed = "\n".join(f"  {name}: {heading}" for name, heading in at_risk)
    return (
        "This command discards uncommitted work, and these entries are not committed yet:\n"
        f"{listed}\n"
        "They were written by the allocator, which never commits. Commit them first, or "
        f"re-run with a trailing `# {ALLOW_MARKER}` to discard them deliberately."
    )


def main():
    try:
        payload = json.load(sys.stdin)
        if payload.get("tool_name") != "Bash":
            return 0
        reason = evaluate(payload.get("tool_input", {}).get("command", ""))
        if reason:
            json.dump(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        # "ask" is not a documented value - only allow and deny. Checked
                        # against the live hooks docs 2026-09-09. The escape marker above is
                        # what stands in for consent.
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                },
                sys.stdout,
            )
    except Exception:
        return 0  # fail open, always
    return 0


if __name__ == "__main__":
    sys.exit(main())
