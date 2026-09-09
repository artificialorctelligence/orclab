import json
import subprocess
import sys
import pathlib

GUARD = str(pathlib.Path(__file__).resolve().parent.parent / "backlog_guard.py")


def make_repo(tmp_path, dirty):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "BACKLOG.md").write_text("# Backlog\n\n## #7: committed one\n\nprose\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "BACKLOG.md"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "init"], check=True)
    if dirty:
        with open(tmp_path / "BACKLOG.md", "a") as f:
            f.write("\n## #8: an uncommitted finding\n\nreal prose\n")
    return tmp_path


def guard(command, repo):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    out = subprocess.run([sys.executable, GUARD], input=payload, capture_output=True,
                         text=True, cwd=str(repo))
    assert out.returncode == 0, "a hook must never wedge the shell"
    return json.loads(out.stdout) if out.stdout.strip() else None


def test_it_fires_on_a_discarding_command_when_entries_are_at_risk(tmp_path):
    repo = make_repo(tmp_path, dirty=True)
    decision = guard("git reset --hard HEAD", repo)
    assert decision is not None
    reason = decision["hookSpecificOutput"]["permissionDecisionReason"]
    assert "#8" in reason and "an uncommitted finding" in reason


def test_it_is_silent_on_a_discarding_command_when_nothing_is_at_risk(tmp_path):
    """A guard that fires on every checkout is noise, and noise gets waved through."""
    assert guard("git reset --hard HEAD", make_repo(tmp_path, dirty=False)) is None


def test_it_is_silent_on_a_harmless_command_even_with_entries_at_risk(tmp_path):
    assert guard("git status", make_repo(tmp_path, dirty=True)) is None
    assert guard("ls -la", make_repo(tmp_path, dirty=True)) is None


def test_it_covers_every_form_that_really_discards(tmp_path):
    repo = make_repo(tmp_path, dirty=True)
    for cmd in ["git checkout -- BACKLOG.md", "git checkout BACKLOG.md", "git checkout .",
                "git restore BACKLOG.md", "git reset --hard", "git reset --hard HEAD~1",
                "git stash", "git stash push -u"]:
        assert guard(cmd, repo) is not None, cmd


def test_it_stays_silent_on_commands_that_only_look_dangerous(tmp_path):
    """Verified empirically 2026-09-09: git clean touches only untracked files, and a branch
    switch carries the edit over rather than discarding it. git checkout <branch> is the most
    common git command there is - firing on it would make this guard noise within a day."""
    repo = make_repo(tmp_path, dirty=True)
    for cmd in ["git clean -fdx", "git clean -fd", "git checkout main", "git switch main",
                "git restore --staged BACKLOG.md", "git stash list", "git stash pop"]:
        assert guard(cmd, repo) is None, cmd


def test_the_escape_marker_lets_a_deliberate_discard_through(tmp_path):
    """Same convention secret_guard.py already uses for orclab:allow-secret, so the codebase
    has one escape idiom rather than two."""
    repo = make_repo(tmp_path, dirty=True)
    assert guard("git reset --hard  # orclab:discard-entries", repo) is None


def test_the_decision_is_deny_since_ask_is_not_a_documented_value(tmp_path):
    repo = make_repo(tmp_path, dirty=True)
    decision = guard("git reset --hard", repo)
    assert decision["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_a_non_bash_tool_is_ignored(tmp_path):
    repo = make_repo(tmp_path, dirty=True)
    payload = json.dumps({"tool_name": "Read", "tool_input": {"file_path": "x"}})
    out = subprocess.run([sys.executable, GUARD], input=payload, capture_output=True,
                         text=True, cwd=str(repo))
    assert out.returncode == 0 and not out.stdout.strip()


def test_outside_a_git_repo_it_fails_open(tmp_path):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git reset --hard"}})
    out = subprocess.run([sys.executable, GUARD], input=payload, capture_output=True,
                         text=True, cwd=str(tmp_path))
    assert out.returncode == 0 and not out.stdout.strip()


def test_garbage_on_stdin_fails_open(tmp_path):
    out = subprocess.run([sys.executable, GUARD], input="{not json",
                         capture_output=True, text=True, cwd=str(tmp_path))
    assert out.returncode == 0 and not out.stdout.strip()
