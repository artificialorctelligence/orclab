import json
import pathlib
import subprocess
import sys

import pytest
from lane_notice import main

# The real script, for the one test that runs it as a process: under /orc-test analyze this
# file runs from mutmut's mutants/ copy, whose scripts are rewritten and not runnable alone.
_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent
NOTICE = str((_SCRIPTS.parent if _SCRIPTS.name == "mutants" else _SCRIPTS) / "lane_notice.py")


@pytest.fixture
def notice(run_hook):
    """notice(repo) -> what the hook prints at the start of a session in `repo`."""
    def start(repo):
        code, out, _ = run_hook(main, {"hook_event_name": "SessionStart"}, cwd=repo)
        assert code == 0
        return out
    return start


def make_repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "BACKLOG.md").write_text("# Backlog\n")
    return tmp_path


def test_it_says_nothing_when_nothing_is_running(tmp_path, notice):
    """Silence is the common case. A hook that speaks every session gets tuned out."""
    assert notice(make_repo(tmp_path)).strip() == ""


def test_it_reports_a_lane_in_progress(tmp_path, notice):
    repo = make_repo(tmp_path)
    shared = repo / ".git" / "orclab"
    shared.mkdir(parents=True)
    (shared / "lanes.json").write_text(json.dumps(
        {"A": {"items": ["v13"], "current": "v13", "started": "2026-09-08T14:20:00+00:00"}}))
    assert notice(repo) == "Orclab shared state:\n  lane A: v13 in progress since 2026-09-08T14:20:00+00:00\n"


def test_it_reports_a_held_lock(tmp_path, notice):
    repo = make_repo(tmp_path)
    shared = repo / ".git" / "orclab"
    shared.mkdir(parents=True)
    (shared / "lock").write_text(json.dumps(
        {"pid": 999999, "started": "2026-09-08T14:20:00+00:00", "description": "allocating"}))
    assert "  lock held: allocating (pid 999999)" in notice(repo)


def test_a_lock_without_a_description_still_reports(tmp_path, notice):
    repo = make_repo(tmp_path)
    shared = repo / ".git" / "orclab"
    shared.mkdir(parents=True)
    (shared / "lock").write_text(json.dumps({"pid": 4}))
    assert "  lock held: unknown (pid 4)" in notice(repo)


def test_a_lane_with_no_start_time_has_no_since(tmp_path, notice):
    repo = make_repo(tmp_path)
    shared = repo / ".git" / "orclab"
    shared.mkdir(parents=True)
    (shared / "lanes.json").write_text(json.dumps({"B": {"items": ["v2"], "current": "v2"}}))
    assert notice(repo) == "Orclab shared state:\n  lane B: v2 in progress\n"


def test_if_the_notice_itself_raises_the_session_still_starts(tmp_path, run_hook, monkeypatch):
    import lane_notice
    monkeypatch.setattr(lane_notice, "notice", lambda: 1 / 0)
    code, out, _ = run_hook(main, {"hook_event_name": "SessionStart"}, cwd=make_repo(tmp_path))
    assert code == 0 and out == ""


def test_it_reports_uncommitted_entries(tmp_path, notice):
    repo = make_repo(tmp_path)
    subprocess.run(["git", "-C", str(repo), "add", "BACKLOG.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "init"], check=True)
    (repo / "BACKLOG.md").write_text("# Backlog\n\n## #8: unsaved finding\n\nprose\n")
    out = notice(repo)
    assert "#8" in out


def test_a_corrupt_lane_file_speaks_up_rather_than_going_silent(tmp_path, notice):
    """Silence is this hook's "nothing in progress" signal, so an unreadable lane record must
    not produce it - that fails into exactly the state the lane record exists to prevent."""
    repo = make_repo(tmp_path)
    shared = repo / ".git" / "orclab"
    shared.mkdir(parents=True)
    (shared / "lanes.json").write_text("{not json")
    assert "unreadable" in notice(repo)


def test_outside_a_git_repo_it_says_nothing_and_exits_clean(tmp_path, run_hook):
    code, out, _ = run_hook(main, "{}", cwd=tmp_path)
    assert code == 0 and out.strip() == ""


def test_garbage_on_stdin_is_drained_not_fatal(tmp_path, run_hook):
    repo = make_repo(tmp_path)
    shared = repo / ".git" / "orclab"
    shared.mkdir(parents=True)
    (shared / "lock").write_text(json.dumps({"pid": 1, "description": "allocating"}))
    code, out, _ = run_hook(main, "{not json", cwd=repo)
    assert code == 0 and "lock held: allocating (pid 1)" in out


def test_as_a_process_it_exits_0_with_the_notice_on_stdout(tmp_path):
    """The contract Claude Code sees; the one test here that runs the script for real."""
    repo = make_repo(tmp_path)
    shared = repo / ".git" / "orclab"
    shared.mkdir(parents=True)
    (shared / "lanes.json").write_text(json.dumps({"A": {"items": ["v13"], "current": "v13"}}))
    out = subprocess.run([sys.executable, NOTICE], check=False, input=json.dumps({"hook_event_name": "SessionStart"}),
                         capture_output=True, text=True, cwd=str(repo))
    assert out.returncode == 0 and "lane A: v13 in progress" in out.stdout
