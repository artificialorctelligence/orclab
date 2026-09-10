import json
import subprocess
import sys
import pathlib

GUARD = str(pathlib.Path(__file__).resolve().parent.parent / "backlog_guard.py")


def make_repo(tmp_path, dirty):
    tmp_path.mkdir(parents=True, exist_ok=True)
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
    # One repo, both commands. make_repo commits, so calling it twice on the same tmp_path
    # leaves the second commit with nothing to commit and fails inside the helper.
    repo = make_repo(tmp_path, dirty=True)
    assert guard("git status", repo) is None
    assert guard("ls -la", repo) is None


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


def test_a_forced_switch_or_checkout_fires(tmp_path):
    """git refuses an unforced branch switch rather than overwriting, which is why the guard
    ignores it - and exactly why someone reaches for -f next. Verified 2026-09-09: the forced
    forms really do destroy the edit."""
    repo = make_repo(tmp_path, dirty=True)
    for cmd in ["git checkout -f other", "git switch --discard-changes main",
                "git switch -f main", "git checkout --force other"]:
        assert guard(cmd, repo) is not None, cmd


def test_restore_staged_worktree_fires_but_staged_alone_does_not(tmp_path):
    """--staged alone only unstages; --staged --worktree discards the working copy too."""
    repo = make_repo(tmp_path, dirty=True)
    assert guard("git restore --staged BACKLOG.md", repo) is None
    assert guard("git restore --staged --worktree BACKLOG.md", repo) is not None


def test_a_path_scoped_discard_naming_an_unrelated_file_is_silent(tmp_path):
    """Denying `git restore README.md` is the same noise as denying `git checkout main` - the
    command cannot reach BACKLOG.md, so there is nothing to warn about."""
    repo = make_repo(tmp_path, dirty=True)
    (repo / "README.md").write_text("unrelated\n")
    for cmd in ["git restore README.md", "git checkout -- README.md",
                "git checkout README.md", "git restore src/thing.py"]:
        assert guard(cmd, repo) is None, cmd


def test_a_path_scoped_discard_that_sweeps_the_tree_still_fires(tmp_path):
    repo = make_repo(tmp_path, dirty=True)
    for cmd in ["git restore .", "git checkout -- .", "git checkout ."]:
        assert guard(cmd, repo) is not None, cmd


def test_a_staged_entry_is_still_uncommitted_and_still_guarded(tmp_path):
    """git diff compares against the index, so an entry that was `git add`ed reads as no change
    at all - and reset --hard then destroys it with nothing said."""
    repo = make_repo(tmp_path, dirty=True)
    subprocess.run(["git", "-C", str(repo), "add", "BACKLOG.md"], check=True)
    decision = guard("git reset --hard", repo)
    assert decision is not None, "a staged entry is uncommitted work too"
    assert "#8" in decision["hookSpecificOutput"]["permissionDecisionReason"]


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


def test_a_worktree_is_not_denied_for_the_main_checkouts_uncommitted_entry(tmp_path):
    """A discard reaches only the tree it runs in. Denying a worktree's reset because the main
    checkout has an uncommitted entry tells the user to commit something their tree does not
    contain - and an allocated entry is meant to sit uncommitted, so that would deny every
    whole-tree discard in every worktree for as long as it sits there."""
    repo = make_repo(tmp_path / "main", dirty=True)
    wt = tmp_path / "wt"
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", str(wt), "-b", "b"],
                   check=True)
    assert guard("git reset --hard", wt) is None
    assert guard("git reset --hard", repo) is not None, "the canonical tree is still guarded"


def test_outside_a_git_repo_it_fails_open(tmp_path):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git reset --hard"}})
    out = subprocess.run([sys.executable, GUARD], input=payload, capture_output=True,
                         text=True, cwd=str(tmp_path))
    assert out.returncode == 0 and not out.stdout.strip()


def test_garbage_on_stdin_fails_open(tmp_path):
    out = subprocess.run([sys.executable, GUARD], input="{not json",
                         capture_output=True, text=True, cwd=str(tmp_path))
    assert out.returncode == 0 and not out.stdout.strip()
