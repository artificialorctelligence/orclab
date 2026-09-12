import json
import pathlib

from orc_test import langs
from orc_test.model import Mutation, Survivor
from tests.helpers import fake, make_repo, run


def test_analyze_lint_not_run_is_a_reason_not_a_count(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(9, 10, []), lint="eslint not configured")])
    code, out = run(["analyze"], make_repo(tmp_path), capsys)
    assert "lint: not run — eslint not configured" in out


def test_analyze_all_gates_and_result_file(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(6, 10, [Survivor("src/a.py", 2, "x <= 1")]))])
    code, out = run(["analyze"], repo, capsys)
    assert code == 1
    assert "coverage 90.0%" in out and "TCE 60.0% ✗ (min 70)" in out and "lint: 1 finding" in out
    assert "src/a.py:2  x <= 1" in out and "a caveat" in out
    assert "gates failed: tce — run `/orc-test generate` to repair" in out
    data = json.loads((repo / ".orclab" / "test" / "analyze.json").read_text())
    assert data["languages"]["fake"]["tce"]["survivors"] == [["src/a.py", 2, "x <= 1"]]


def test_analyze_unavailable_mutation_is_words_not_a_number(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(unavailable="no mutation tool exists for Fake")])
    code, out = run(["analyze"], make_repo(tmp_path), capsys)
    assert "TCE not measurable — no mutation tool exists for Fake" in out
    assert "TCE 0" not in out


def test_analyze_no_mutation_flag(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(9, 10, []))])
    code, out = run(["analyze", "--no-mutation"], make_repo(tmp_path), capsys)
    assert "TCE skipped" in out and "$ true" in out


def test_analyze_announces_size_on_whole_repo(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    for i in range(3):
        (repo / f"m{i}.py").write_text("x = 1\n")
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(9, 10, []))])
    code, out = run(["analyze"], repo, capsys)
    assert "mutating 4 files" in out    # 3 modules + tests/test_ok.py; first run, no cache yet


def test_analyze_no_mutants_is_words_not_a_fabricated_zero(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(0, 0, []))])
    code, out = run(["analyze"], make_repo(tmp_path), capsys)
    assert "TCE not measurable — mutation tool produced no mutants" in out
    assert "TCE 0" not in out


def test_analyze_writes_result_file_even_when_every_language_fails_tests(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    monkeypatch.setattr(langs, "ALL", [fake(test_cmd=["false"])])
    code, out = run(["analyze"], repo, capsys)
    data = json.loads((repo / ".orclab" / "test" / "analyze.json").read_text())
    assert data["languages"] == {}


def test_analyze_coverage_unavailable_is_words_not_a_failed_gate(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(9, 10, []), coverage_unavailable="no coverage tool for Fake")])
    code, out = run(["analyze"], repo, capsys)
    assert code == 0
    assert out.count("coverage not measurable — no coverage tool for Fake") == 1
    data = json.loads((repo / ".orclab" / "test" / "analyze.json").read_text())
    assert data["languages"]["fake"]["coverage"] == {"unavailable": "no coverage tool for Fake"}


def test_analyze_rebases_survivors_from_a_sub_project_to_the_root(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    m = fake(Mutation(9, 10, [Survivor("pkg/a.py", 2, "x <= 1")]))
    (repo / "skills" / "x" / "scripts").mkdir(parents=True)
    m.mutation_cwd = lambda root, target: pathlib.Path(root) / "skills" / "x" / "scripts"
    monkeypatch.setattr(langs, "ALL", [m])
    code, out = run(["analyze"], repo, capsys)
    assert "skills/x/scripts/pkg/a.py:2  x <= 1" in out
