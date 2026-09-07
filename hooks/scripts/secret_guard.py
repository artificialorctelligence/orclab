#!/usr/bin/env python3
"""PreToolUse guard: refuse Bash commands whose own output would be a secret.

Enforcement half of `skills/secret-hygiene/SKILL.md`. That skill is prose Claude reads; this
runs whether or not it was read. Scope is deliberately narrow: only commands whose *entire
purpose* is to emit a credential to stdout, never a general "looks security-ish" heuristic.

Contract (verified against the current Claude Code hooks docs, 2026-09-07): read the hook
payload as JSON on stdin, print a `hookSpecificOutput` decision on stdout, exit 0. An exit
status other than 0 or 2 is a non-blocking error, so every unexpected failure here lets the
command through rather than wedging the user's shell.
"""

import json
import re
import sys

ALLOW_MARKER = "orclab:allow-secret"

DOC = (
    "See secret-hygiene. If this is genuinely required, re-run with a trailing "
    "`# orclab:allow-secret`."
)

# Pipelines that discard the values and keep only the variable names — the form secret-hygiene
# actively recommends, so the bare-`env` rule must not fire on it.
KEYS_ONLY = re.compile(
    r"sed\b[^;&|]*=\.\*|cut\b[^;&|]*-d\s*['\"]?=|awk\b[^;&|]*-F\s*['\"]?="
)

# Template files are committed precisely because they hold no real values.
TEMPLATE_SUFFIX = re.compile(r"\.(example|sample|template|dist|tpl)\b")

# (pattern, reason, exemption). Each reason names the safe alternative, because a denial should
# redirect Claude to the right command rather than dead-end the task it was doing.
RULES = [
    (
        re.compile(r"\bgh\s+auth\s+token\b"),
        "`gh auth token` prints the token itself. Use `gh auth status` (self-masks) to check "
        "auth, or capture it: TOK=$(gh auth token).",
        None,
    ),
    (
        re.compile(
            r"\b(op\s+read|vault\s+(kv\s+get|read)|pass\s+show|keyring\s+get"
            r"|secret-tool\s+lookup)\b"
        ),
        "This reads a secret manager and prints the secret. Capture it instead: "
        "SECRET=$(<the same command>), then use $SECRET without echoing it.",
        None,
    ),
    (
        re.compile(r"\bsecurity\s+find-(generic|internet)-password\b[^;&|]*\s-w\b"),
        "`-w` prints the password to stdout. Capture it instead: PW=$(<the same command>).",
        None,
    ),
    (
        re.compile(r"(^|[;&|]\s*)(env|printenv)\s*($|[|;&>])"),
        "A bare `env`/`printenv` dumps every variable, including any credentials. For a "
        "comparison use keys only: env | sed -E 's/=.*//'. For one variable, test presence: "
        '[ -n "$VAR" ] && echo set.',
        KEYS_ONLY,
    ),
    (
        re.compile(
            r"\b(cat|bat|less|more|head|tail|xxd|od|strings|nl)\b[^;&|]*?"
            r"(\.env\b|\.npmrc\b|\.pypirc\b|\.netrc\b|\bcredentials\b|\bhosts\.yml\b"
            r"|\bid_rsa\b|\bid_ecdsa\b|\bid_ed25519\b|\.pem\b|\.p12\b|\.pfx\b"
            r"|service[-_]account[^\s;&|]*\.json)"
        ),
        "This file commonly holds live credentials. Redact on read instead: "
        "sed -E 's/((token|secret|password|api[_-]?key)[[:space:]]*[:=][[:space:]]*).*/"
        "\\1<redacted>/I' <file>",
        None,
    ),
    (
        re.compile(
            r"\b(echo|printf)\b[^;&|]*\$\{?\w*"
            r"(TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|PRIVATE_KEY|CREDENTIAL|ACCESS_KEY)\w*\}?"
        ),
        "Echoing a credential variable puts it in the transcript permanently. To confirm it is "
        'set without revealing it: [ -n "$VAR" ] && echo set.',
        None,
    ),
    (
        re.compile(r"\bkubectl\s+get\s+secrets?\b[^;&|]*-o[= ]\s*(yaml|json)\b"),
        "This prints secret material (base64 is not redaction). Read the one key you need and "
        "capture it, rather than dumping the object.",
        None,
    ),
    (
        re.compile(r"\baws\s+configure\s+get\b[^;&|]*(secret|session_token)"),
        "This prints the AWS secret to stdout. Capture it instead: KEY=$(<the same command>).",
        None,
    ),
]


def _is_captured(command, match):
    """True when the match's stdout is captured rather than shown.

    `TOK=$(gh auth token)` and `gh auth token > f` never reach the transcript, and
    secret-hygiene recommends both, so they must not be blocked.
    """
    # ponytail: prefix/suffix inspection, not real shell parsing. Misses exotic forms
    # (process substitution, nested eval); upgrade to an AST parser only if that shows up.
    before = command[: match.start()].rstrip()
    if before.endswith("$(") or before.endswith("`"):
        return True
    # Must be a *stdout* redirect to a file. `2>&1` and `2>/dev/null` leave stdout on screen,
    # so the fd digit and the `>&` form are both excluded — the real 2026-09-07 leak ended in
    # `2>&1` and a looser check waved it straight through.
    return bool(re.match(r"^[^;&|]*?(?<![0-9>&])>>?\s*(?!&)\S", command[match.end() :]))


def evaluate(command):
    """Return a denial reason for `command`, or None to let it through."""
    if not command or ALLOW_MARKER in command:
        return None
    for pattern, reason, exemption in RULES:
        match = pattern.search(command)
        if not match:
            continue
        if exemption is not None and exemption.search(command):
            continue
        # The suffix sits past the match, since the pattern stops at the bare filename.
        if TEMPLATE_SUFFIX.match(command[match.end() :]):
            continue
        if _is_captured(command, match):
            continue
        return "{} {}".format(reason, DOC)
    return None


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
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                },
                sys.stdout,
            )
    except Exception:
        # Fail open, always. A guard that wedges every Bash call is worse than the leak it
        # prevents, and exit 0 with no output leaves the normal permission flow untouched.
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
