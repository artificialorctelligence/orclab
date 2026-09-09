import subprocess

from orc_todo import lanes, state
from orc_todo.cli import main

BACKLOG = """# Backlog

## #7: an open one

prose about it

## #12: a closed one (RESOLVED 2026-09-07)

prose

## #22: another open one

more prose
"""


def make_repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "BACKLOG.md").write_text(BACKLOG)
    d = tmp_path / "docs" / "superpowers" / "specs"
    d.mkdir(parents=True)
    (d / "2026-09-08-orclab-v13-x-design.md").write_text("# s\n")
    (d / "2026-09-08-orclab-v14-y-design.md").write_text("# s\n")
    return tmp_path


def run(args, repo, capsys, stdin=None, monkeypatch=None):
    if monkeypatch is not None and stdin is not None:
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(stdin))
    # --cwd is a top-level option, so it MUST precede the subcommand. argparse assigns
    # options after a subcommand to that subparser, and this one is not defined there.
    code = main(["--cwd", str(repo), *args])
    captured = capsys.readouterr()
    # Both streams. main() prints errors to stderr, which is correct and stays that way; what
    # these assertions care about is what the operator actually sees, and in a terminal that is
    # the two interleaved.
    return code, captured.out + captured.err


def test_list_shows_open_entries_one_line_each_and_marks_resolved_ones_absent(tmp_path, capsys):
    repo = make_repo(tmp_path)
    code, out = run(["list"], repo, capsys)
    assert code == 0
    assert "#7: an open one" in out
    assert "#22: another open one" in out
    assert "#12" not in out, "resolved entries are not open work"
    assert "prose about it" not in out, "list is one line per entry, not the file"


def test_list_marks_a_partially_addressed_entry(tmp_path, capsys):
    """Partially-addressed entries are still open work, but knowing half of one is already
    done changes whether you pick it up."""
    repo = make_repo(tmp_path)
    (repo / "BACKLOG.md").write_text(
        BACKLOG + "\n## #30: half done (PARTIALLY ADDRESSED 2026-09-08 - rest still open)\n\nprose\n")
    code, out = run(["list"], repo, capsys)
    assert code == 0
    assert "#30" in out and "[partial]" in out


def test_show_prints_one_entry_in_full(tmp_path, capsys):
    repo = make_repo(tmp_path)
    code, out = run(["show", "7"], repo, capsys)
    assert code == 0
    assert "prose about it" in out
    assert "another open one" not in out


def test_show_on_a_missing_entry_is_an_error_not_an_empty_success(tmp_path, capsys):
    repo = make_repo(tmp_path)
    code, _ = run(["show", "999"], repo, capsys)
    assert code == 1


def test_add_allocates_and_writes_the_entry(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    code, out = run(["add", "backlog", "a real finding"], repo, capsys,
                    stdin="A genuine paragraph of context.\n", monkeypatch=monkeypatch)
    assert code == 0
    assert "23" in out
    assert "## #23: a real finding" in (repo / "BACKLOG.md").read_text()


def test_add_refuses_an_empty_body(tmp_path, capsys, monkeypatch):
    """backlog-discipline requires a real paragraph, never a stub. The command is a front door
    to that rule, not a way around it."""
    repo = make_repo(tmp_path)
    code, _ = run(["add", "backlog", "t"], repo, capsys, stdin="   \n", monkeypatch=monkeypatch)
    assert code == 1
    assert "## #23" not in (repo / "BACKLOG.md").read_text()


def test_remove_deletes_the_section_and_renumbers_nothing(tmp_path, capsys):
    repo = make_repo(tmp_path)
    code, _ = run(["remove", "7"], repo, capsys)
    assert code == 0
    text = (repo / "BACKLOG.md").read_text()
    assert "## #7:" not in text
    assert "## #12:" in text and "## #22:" in text, "no other entry may be renumbered"


def test_lane_create_and_list(tmp_path, capsys):
    repo = make_repo(tmp_path)
    assert run(["lane", "create", "B", "v13,v14"], repo, capsys)[0] == 0
    code, out = run(["lane", "list"], repo, capsys)
    assert code == 0 and "B" in out and "v13" in out


def test_lane_create_with_an_unspecced_item_fails_and_says_which(tmp_path, capsys):
    repo = make_repo(tmp_path)
    code, out = run(["lane", "create", "A", "v13,v99"], repo, capsys)
    assert code == 1
    assert "v99" in out


def test_list_shows_lanes_when_they_exist_and_omits_the_section_when_they_do_not(tmp_path, capsys):
    repo = make_repo(tmp_path)
    assert "lane" not in run(["list"], repo, capsys)[1].lower()
    run(["lane", "create", "B", "v13"], repo, capsys)
    assert "B" in run(["list"], repo, capsys)[1]


def test_lock_status_reports_free_and_held(tmp_path, capsys):
    repo = make_repo(tmp_path)
    assert "not held" in run(["lock", "status"], repo, capsys)[1].lower()
    with state.held("a real holder", cwd=repo):
        assert "a real holder" in run(["lock", "status"], repo, capsys)[1]


def test_lock_clear_removes_a_lock_and_says_so_when_there_was_none(tmp_path, capsys):
    repo = make_repo(tmp_path)
    assert run(["lock", "clear"], repo, capsys)[0] == 0
    state.shared_dir(repo)
    state.lock_path(repo).write_text("{}")
    assert run(["lock", "clear"], repo, capsys)[0] == 0
    assert not state.lock_path(repo).exists()


def test_outside_a_git_repo_it_reports_unavailable_rather_than_crashing(tmp_path, capsys):
    code, out = run(["list"], tmp_path, capsys)
    assert code == 1
    assert "git" in out.lower()


def test_a_project_with_no_backlog_is_told_so_and_none_is_created(tmp_path, capsys):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    code, out = run(["list"], tmp_path, capsys)
    assert code == 1
    assert "BACKLOG.md" in out
    assert not (tmp_path / "BACKLOG.md").exists()
