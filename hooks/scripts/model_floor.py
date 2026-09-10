#!/usr/bin/env python3
"""PreToolUse guard: raise a subagent dispatched below the model floor, before it runs.

On 2026-09-09 a session executing the v13 plan dispatched haiku implementers for two tasks,
following `superpowers:subagent-driven-development`'s Model Selection section, which says to use
the cheapest tier when the plan already contains the complete code. It cost two fix rounds and,
on one task, an implementer silently deleted the assertions from an unrelated pre-existing test -
leaving it passing unconditionally, which a green suite never surfaces. The saving was not real.

This is a hook rather than prose for the reason `CLAUDE.md` already gives about where a rule can
live: the guidance being followed was itself prose, and prose lost. The rule that should have
covered it belongs to a third-party plugin, so widening its trigger was not available - which is
the one case that section allows a mechanism beside it rather than a wider trigger.

**Allowlist, not denylist.** An unrecognised model name is raised too, so a cheap tier released
after this file was written does not slip under the floor by not being on a list.

**A dispatch naming no model is left alone.** That is how an agent definition's own pinned model
and the session's inherited model reach the subagent; overriding those would be a different rule
than the one this file implements.

Contract: read the hook payload as JSON on stdin, print `hookSpecificOutput.updatedInput` with
the corrected input, exit 0. Verified live 2026-09-09 against a real dispatch, not only against
the settings schema: an Agent call made with `model: "haiku"` ran and reported itself as Sonnet.
Every unexpected failure here lets the dispatch through unchanged - a guard that wedges every
subagent is worse than the model it corrects.
"""

import json
import os
import re
import sys

FLOOR = "sonnet"
OFF = "ORCLAB_MODEL_FLOOR_OFF"

# Families at or above the floor. Matches a bare alias ("opus") and a full id
# ("claude-sonnet-5"), since a dispatch may legitimately use either form.
AT_OR_ABOVE = re.compile(r"^(sonnet|opus|fable|claude-(sonnet|opus|fable)-)", re.I)


def corrected(tool_input):
    """The tool input with a sub-floor model raised, or None when nothing needs changing."""
    requested = (tool_input or {}).get("model")
    if not requested or AT_OR_ABOVE.match(str(requested)):
        return None
    return dict(tool_input, model=FLOOR)


def main():
    try:
        # An explicit off-switch, because this hook spends someone else's money differently
        # than they asked. A plugin may hold an opinion about which model writes code; it must
        # not be the only opinion available on a machine it does not own.
        if os.environ.get(OFF):
            return 0
        payload = json.load(sys.stdin)
        if payload.get("tool_name") not in ("Agent", "Task"):
            return 0
        tool_input = payload.get("tool_input", {})
        patched = corrected(tool_input)
        if patched is None:
            return 0
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "updatedInput": patched,
                },
                "systemMessage": (
                    f'orclab: subagent model "{tool_input.get("model")}" raised to {FLOOR} - '
                    f"nothing below it writes code. Set {OFF}=1 to disable."
                ),
            },
            sys.stdout,
        )
    except Exception:
        # Fail open, always - same reasoning as secret_guard.
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
