import pathlib

from orc_test import stryker

FIX = pathlib.Path(__file__).parent / "fixtures" / "stryker.json"


def test_parse_scores_like_stryker_and_lists_survivors():
    m = stryker.parse(FIX, root=".")
    assert (m.killed, m.total) == (1, 3)              # Ignored is not counted
    assert [(s.file, s.line, s.description) for s in m.survivors] == [
        ("src/clamp.js", 2, "EqualityOperator → x <= lo"),
        ("src/clamp.js", 4, "BlockStatement → {} (no test reaches it)")]


def test_find_newest_report(tmp_path):
    (tmp_path / "old.json").write_text('{"files": {}}')
    new = tmp_path / "sub"
    new.mkdir()
    (new / "mutation.json").write_text('{"files": {}}')
    (tmp_path / "other.json").write_text('{"not": "a report"}')
    assert stryker.find(tmp_path) == new / "mutation.json"
