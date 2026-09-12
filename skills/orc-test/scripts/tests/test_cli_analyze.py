import json
import types

from orc_test import cli, langs
from orc_test.model import Coverage, Finding, Mutation, Survivor
from tests.test_cli import make_repo, run


def fake(mutation=None, unavailable=None, cov=(9, 10), lint=None):
    m = types.SimpleNamespace(
        KEY="fake", LABEL="Fake", MARKERS=["pyproject.toml"], TOOLS={}, CAVEATS=["a caveat"],
        mutation_unavailable=lambda root: unavailable, missing=lambda root: [],
        test_cmd=lambda root, t: ["true"],
        coverage_cmd=lambda root, t, out: ["true"],
        coverage_parse=lambda root, out: Coverage(*cov, {"src/a.py": cov}),
        mutation_cmd=lambda root, t, out: ["true"],
        mutation_parse=lambda root, out: mutation,
        lint=lambda root, t, out: lint if lint is not None else [
            Finding("tests/test_a.py", 3, "no assertion in test_x")])
    return m


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
