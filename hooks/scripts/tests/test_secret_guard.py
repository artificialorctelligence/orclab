import io
import json

import pytest

from secret_guard import ALLOW_MARKER, evaluate, main


def run_hook(monkeypatch, capsys, payload):
    """Drive main() end to end and return (exit_code, parsed_stdout_or_None)."""
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    code = main()
    out = capsys.readouterr().out
    return code, json.loads(out) if out.strip() else None


def bash(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}}


# --- The incident this hook exists for (2026-09-07) ------------------------------------------

def test_denies_the_real_leak_command():
    """The exact command that printed a live gho_ token into a transcript."""
    leak = "env -i HOME=$HOME PATH=/usr/bin:/bin gh auth token --hostname github.com 2>&1"
    reason = evaluate(leak)
    assert reason is not None
    assert "gh auth status" in reason


@pytest.mark.parametrize(
    "command",
    [
        # Every other command from that same investigation handled the token correctly and
        # must keep working — the guard is worthless if it blocks the safe forms too.
        "gh auth status",
        "TOK=$(gh auth token); echo ${TOK:0:4}",
        "gh auth token > /tmp/ghtok.txt",
        "curl -s -o /dev/null -w 'http=%{http_code}' -H \"Authorization: token $TOK\" https://api.github.com/user",
        "sed -E 's/(oauth_token):.*/\\1: <redacted>/' ~/.config/gh/hosts.yml",
    ],
)
def test_allows_the_safe_forms(command):
    assert evaluate(command) is None


# --- Rule coverage ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "command",
    [
        "gh auth token",
        "op read op://vault/item/password",
        "vault kv get secret/prod",
        "pass show github/token",
        "secret-tool lookup service github",
        "security find-generic-password -s github -w",
        "env",
        "printenv",
        "cd /tmp && env",
        "cat .env",
        "cat ~/.aws/credentials",
        "head -5 ~/.ssh/id_rsa",
        "cat server.pem",
        "cat service_account.json",
        "echo $GITHUB_TOKEN",
        "printf '%s' $AWS_SECRET_ACCESS_KEY",
        "kubectl get secret db -o yaml",
        "aws configure get aws_secret_access_key",
    ],
)
def test_denied(command):
    assert evaluate(command) is not None


@pytest.mark.parametrize(
    "command",
    [
        "env | sed -E 's/=.*//'",          # keys-only: the form secret-hygiene recommends
        "env | cut -d= -f1",
        "env -i HOME=/root PATH=/bin ls",  # env as a prefix, not a dump
        "cat .env.example",                # templates hold no real values
        "cat config.env.sample",
        'echo "prefix: ${TOK:0:4}"',       # a fingerprint, not the secret
        '[ -n "$API_KEY" ] && echo set',
        "kubectl get secret db",           # no -o yaml/json: names only
        "aws configure get region",
        "git status",
        "pytest tests/ -v",
    ],
)
def test_allowed(command):
    assert evaluate(command) is None


def test_allow_marker_is_an_escape_hatch():
    assert evaluate("gh auth token") is not None
    assert evaluate("gh auth token  # " + ALLOW_MARKER) is None


# --- Hook protocol ---------------------------------------------------------------------------

def test_deny_emits_the_documented_schema(monkeypatch, capsys):
    code, out = run_hook(monkeypatch, capsys, bash("gh auth token"))
    assert code == 0, "must exit 0; the decision travels in stdout, not the exit status"
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert out["hookSpecificOutput"]["permissionDecisionReason"]


def test_safe_command_emits_nothing(monkeypatch, capsys):
    code, out = run_hook(monkeypatch, capsys, bash("git status"))
    assert (code, out) == (0, None)


def test_ignores_other_tools(monkeypatch, capsys):
    payload = {"tool_name": "Read", "tool_input": {"file_path": "/etc/passwd"}}
    code, out = run_hook(monkeypatch, capsys, payload)
    assert (code, out) == (0, None)


@pytest.mark.parametrize(
    "stdin_text", ["", "not json at all", "[]", '{"tool_name": "Bash"}'],
)
def test_fails_open_on_bad_input(monkeypatch, capsys, stdin_text):
    """A guard that wedges every Bash call is worse than the leak it prevents."""
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    assert main() == 0
    assert capsys.readouterr().out.strip() == ""


@pytest.mark.parametrize(
    "command",
    [
        "gh auth token 2>&1",          # stderr merged into stdout: still shown
        "gh auth token 2>/dev/null",   # stderr silenced; stdout still shown
    ],
)
def test_stderr_redirects_are_not_a_capture(command):
    assert evaluate(command) is not None


@pytest.mark.parametrize(
    "command", ["gh auth token > f", "gh auth token >> log", "gh auth token >/tmp/t 2>&1"],
)
def test_stdout_redirects_are_a_capture(command):
    assert evaluate(command) is None
