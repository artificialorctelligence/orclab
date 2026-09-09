import json
import os
import subprocess

import pytest

from orc_todo import state


def make_repo(tmp_path):
    """A real git repo — these functions shell out to git, so a fake would prove nothing."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def test_shared_dir_is_inside_the_git_common_dir(tmp_path):
    repo = make_repo(tmp_path)
    assert state.shared_dir(repo) == (repo / ".git" / "orclab")
    assert state.shared_dir(repo).is_dir()


def test_a_worktree_resolves_to_the_same_shared_dir_as_its_main_checkout(tmp_path):
    """The whole design rests on this. Two checkouts, one shared directory - otherwise a lock
    locks two different files and protects nothing, which is what happened on 2026-09-08."""
    repo = make_repo(tmp_path)
    (repo / "f.txt").write_text("x")
    subprocess.run(["git", "-C", str(repo), "add", "f.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-qm", "init"], check=True)
    wt = tmp_path / "wt"
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", str(wt), "-b", "b"], check=True)
    assert state.shared_dir(wt) == state.shared_dir(repo)
    assert state.canonical_root(wt) == state.canonical_root(repo) == repo


def test_outside_a_git_repo_raises_rather_than_guessing(tmp_path):
    with pytest.raises(state.NotAGitRepo):
        state.git_common_dir(tmp_path)


def test_the_lock_is_acquired_and_released(tmp_path):
    repo = make_repo(tmp_path)
    with state.held("allocating #26", cwd=repo):
        assert state.lock_path(repo).exists()
        assert state.lock_info(repo)["description"] == "allocating #26"
    assert not state.lock_path(repo).exists()


def test_a_second_holder_times_out_and_names_the_first(tmp_path):
    repo = make_repo(tmp_path)
    with state.held("first holder", cwd=repo):
        with pytest.raises(state.LockUnavailable) as e:
            with state.held("second", cwd=repo, timeout=0.5, poll=0.1):
                pass
    assert e.value.info["description"] == "first holder"
    assert e.value.info["pid"] == os.getpid()


def test_acquisition_is_atomic_not_check_then_set(tmp_path):
    """O_CREAT|O_EXCL must be what fails, not a prior existence check - two processes can both
    pass a check and both proceed."""
    repo = make_repo(tmp_path)
    with state.held("holder", cwd=repo):
        with pytest.raises(FileExistsError):
            os.open(state.lock_path(repo), os.O_CREAT | os.O_EXCL | os.O_WRONLY)


def test_the_lock_is_released_even_when_the_body_raises(tmp_path):
    repo = make_repo(tmp_path)
    with pytest.raises(ValueError):
        with state.held("boom", cwd=repo):
            raise ValueError("boom")
    assert not state.lock_path(repo).exists()


def test_a_dead_holder_is_reported_as_not_alive_but_never_removed(tmp_path):
    """direflail's operational note: a lock found when none is expected is worth investigating,
    not clearing reflexively. Nothing auto-clears."""
    repo = make_repo(tmp_path)
    state.shared_dir(repo)
    state.lock_path(repo).write_text(json.dumps(
        {"pid": 999999, "started": "2026-09-08T00:00:00+00:00", "description": "ghost"}))
    info = state.lock_info(repo)
    assert info["alive"] is False
    assert info["description"] == "ghost"
    with pytest.raises(state.LockUnavailable):
        with state.held("mine", cwd=repo, timeout=0.3, poll=0.1):
            pass
    assert state.lock_path(repo).exists(), "a stale lock must never be auto-cleared"


def test_clear_lock_removes_it_and_reports_whether_there_was_one(tmp_path):
    repo = make_repo(tmp_path)
    state.shared_dir(repo)
    assert state.clear_lock(repo) is False
    state.lock_path(repo).write_text("{}")
    assert state.clear_lock(repo) is True
    assert not state.lock_path(repo).exists()


def test_a_corrupt_lock_file_still_reports_and_still_blocks(tmp_path):
    """A half-written lock must not read as 'no lock'."""
    repo = make_repo(tmp_path)
    state.shared_dir(repo)
    state.lock_path(repo).write_text("{not json")
    info = state.lock_info(repo)
    assert info is not None and info["pid"] is None and info["alive"] is True


def test_counters_round_trip_and_default_to_empty(tmp_path):
    repo = make_repo(tmp_path)
    assert state.read_counters(repo) == {}
    state.write_counters({"BACKLOG.md": 25}, repo)
    assert state.read_counters(repo) == {"BACKLOG.md": 25}
