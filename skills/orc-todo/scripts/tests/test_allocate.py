import multiprocessing
import subprocess

import pytest

from orc_todo import allocate as alloc
from orc_todo import state


def make_repo(tmp_path, backlog="# Backlog\n\n## #22: last one\n\nprose\n"):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "BACKLOG.md").write_text(backlog)
    return tmp_path


def test_allocate_returns_the_next_number_and_writes_the_entry(tmp_path):
    repo = make_repo(tmp_path)
    n = alloc.allocate("backlog", "a new finding", "real prose here", cwd=repo)
    assert n == 23
    text = (repo / "BACKLOG.md").read_text()
    assert "## #23: a new finding" in text
    assert "real prose here" in text
    assert "## #22: last one" in text, "existing entries must be untouched"


def test_allocate_never_commits(tmp_path):
    """Committing means running git in a checkout the agent does not own, sweeping up whatever
    uncommitted work is in that file."""
    repo = make_repo(tmp_path)
    alloc.allocate("backlog", "t", "b", cwd=repo)
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "BACKLOG.md"],
        capture_output=True, text=True, check=True).stdout
    assert status.strip(), "the entry must be left uncommitted"


def test_allocate_appends_even_when_the_file_is_dirty(tmp_path):
    """The earlier design refused here, which blocks an agent from recording a finding until a
    human intervenes. It appends instead; the guard protects the entry."""
    repo = make_repo(tmp_path)
    (repo / "BACKLOG.md").write_text("# Backlog\n\n## #22: last one\n\nEDITED BY HAND\n")
    alloc.allocate("backlog", "t", "b", cwd=repo)
    text = (repo / "BACKLOG.md").read_text()
    assert "EDITED BY HAND" in text, "the human's uncommitted edit must survive"
    assert "## #23: t" in text


def test_the_counter_is_updated_so_the_next_call_does_not_rescan_from_zero(tmp_path):
    repo = make_repo(tmp_path)
    alloc.allocate("backlog", "one", "b", cwd=repo)
    assert state.read_counters(repo)["backlog"] == 23


def test_a_lost_counter_self_heals_from_the_file(tmp_path):
    """A fresh clone or a cleaned .git loses the counter. The file is still there, so a lost
    counter must never reissue a number."""
    repo = make_repo(tmp_path)
    alloc.allocate("backlog", "one", "b", cwd=repo)
    state.write_counters({}, repo)
    assert alloc.allocate("backlog", "two", "b", cwd=repo) == 24


def test_a_counter_ahead_of_the_file_wins(tmp_path):
    """The reverse case: an entry was deleted, so the file's maximum went backwards. The
    counter must hold the line - backlog numbers are never reused."""
    repo = make_repo(tmp_path)
    state.write_counters({"backlog": 40}, repo)
    assert alloc.allocate("backlog", "t", "b", cwd=repo) == 41


def test_a_missing_resource_file_raises_rather_than_creating_one(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    with pytest.raises(alloc.ResourceMissing):
        alloc.allocate("backlog", "t", "b", cwd=tmp_path)


def test_allocation_fails_cleanly_when_the_lock_is_held(tmp_path):
    repo = make_repo(tmp_path)
    with state.held("someone else", cwd=repo):
        with pytest.raises(state.LockUnavailable):
            alloc.allocate("backlog", "t", "b", cwd=repo, timeout=0.4)


def _child(repo, title, out):
    try:
        out.put(alloc.allocate("backlog", title, "body", cwd=repo, timeout=30.0))
    except Exception as e:  # surface it rather than hanging the parent on an empty queue
        out.put(f"ERROR {e!r}")


def test_two_real_concurrent_processes_get_different_numbers(tmp_path):
    """The actual race, with two real processes - not two sequential calls. This is the test
    that would have failed on 2026-09-08, when both sessions took #23 and #24.
    """
    repo = make_repo(tmp_path)
    q = multiprocessing.Queue()
    procs = [multiprocessing.Process(target=_child, args=(repo, f"entry {i}", q))
             for i in range(2)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=60)
    results = sorted(q.get() for _ in procs)
    assert results == [23, 24], f"got {results}"
    text = (repo / "BACKLOG.md").read_text()
    assert "## #23:" in text and "## #24:" in text, "both entries must land"


def test_a_completed_allocation_leaves_no_temp_file_behind(tmp_path):
    repo = make_repo(tmp_path)
    alloc.allocate("backlog", "t", "b", cwd=repo)
    assert not list(repo.glob(".BACKLOG.md.tmp*")), "the temp file must be renamed, not left"


def test_a_failed_write_leaves_the_original_file_intact(tmp_path, monkeypatch):
    """The reason this is atomic at all: write_text() truncates first, so a crash mid-write
    destroys the one file the allocator deliberately never commits - there is no committed copy
    to recover from."""
    repo = make_repo(tmp_path)
    before = (repo / "BACKLOG.md").read_text()

    def boom(src, dst):
        raise OSError("simulated failure at the replace step")

    monkeypatch.setattr(alloc.os, "replace", boom)
    with pytest.raises(OSError):
        alloc.allocate("backlog", "t", "b", cwd=repo)
    assert (repo / "BACKLOG.md").read_text() == before, "the original must survive intact"
