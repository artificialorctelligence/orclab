import json
import subprocess
import sys
import pathlib

NOTICE = str(pathlib.Path(__file__).resolve().parent.parent / "lane_notice.py")


def notice(repo):
    out = subprocess.run([sys.executable, NOTICE], input=json.dumps({"hook_event_name": "SessionStart"}),
                         capture_output=True, text=True, cwd=str(repo))
    assert out.returncode == 0
    return out.stdout


def make_repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "BACKLOG.md").write_text("# Backlog\n")
    return tmp_path


def test_it_says_nothing_when_nothing_is_running(tmp_path):
    """Silence is the common case. A hook that speaks every session gets tuned out."""
    assert notice(make_repo(tmp_path)).strip() == ""


def test_it_reports_a_lane_in_progress(tmp_path):
    repo = make_repo(tmp_path)
    shared = repo / ".git" / "orclab"
    shared.mkdir(parents=True)
    (shared / "lanes.json").write_text(json.dumps(
        {"A": {"items": ["v13"], "current": "v13", "started": "2026-09-08T14:20:00+00:00"}}))
    out = notice(repo)
    assert "A" in out and "v13" in out


def test_it_reports_a_held_lock(tmp_path):
    repo = make_repo(tmp_path)
    shared = repo / ".git" / "orclab"
    shared.mkdir(parents=True)
    (shared / "lock").write_text(json.dumps(
        {"pid": 999999, "started": "2026-09-08T14:20:00+00:00", "description": "allocating"}))
    assert "lock" in notice(repo).lower()


def test_it_reports_uncommitted_entries(tmp_path):
    repo = make_repo(tmp_path)
    subprocess.run(["git", "-C", str(repo), "add", "BACKLOG.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "init"], check=True)
    (repo / "BACKLOG.md").write_text("# Backlog\n\n## #8: unsaved finding\n\nprose\n")
    out = notice(repo)
    assert "#8" in out


def test_outside_a_git_repo_it_says_nothing_and_exits_clean(tmp_path):
    out = subprocess.run([sys.executable, NOTICE], input="{}", capture_output=True,
                         text=True, cwd=str(tmp_path))
    assert out.returncode == 0 and out.stdout.strip() == ""
