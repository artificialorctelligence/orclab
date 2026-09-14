import pytest
from orc_test import langs
from tests.helpers import fake, make_repo, run

pytest.importorskip("pytest_cov")


def _src(repo, body):
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "calc.py").write_text(body)
    (repo / "tests" / "test_calc.py").write_text(
        "import sys; sys.path.insert(0, 'src')\nfrom calc import clamp\n"
        "def test_mid():\n    assert clamp(5, 0, 10) == 5\n")


def test_coverage_under_threshold_lists_files_worst_first_and_fails(tmp_path, capsys):
    repo = make_repo(tmp_path)
    _src(repo, "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n"
               "    if x > hi:\n        return hi\n    return x\n")
    code, out = run(["coverage", "src"], repo, capsys)
    assert code == 1
    assert "Python" in out and "66.7%" in out and "✗" in out
    assert "src/calc.py" in out
    assert (repo / ".orclab" / "test" / "python" / "coverage.lcov").exists()
    assert "html report:" in out


def test_coverage_threshold_from_config(tmp_path, capsys):
    repo = make_repo(tmp_path)
    _src(repo, "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n"
               "    if x > hi:\n        return hi\n    return x\n")
    (repo / ".orclab").mkdir()
    (repo / ".orclab" / "test.yaml").write_text("coverage: 60\n")
    code, out = run(["coverage", "src"], repo, capsys)
    assert code == 0 and "✓" in out


def test_coverage_with_red_tests_stops_that_language(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "tests" / "test_bad.py").write_text("def test_bad():\n    assert 0\n")
    code, out = run(["coverage"], repo, capsys)
    assert code == 1 and "tests failed; coverage not measured" in out


def test_coverage_denominator_excludes_the_tests_themselves(tmp_path, capsys):
    repo = make_repo(tmp_path)
    _src(repo, "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n"
               "    if x > hi:\n        return hi\n    return x\n")
    _code, out = run(["coverage"], repo, capsys)        # --cov=. would count tests/ too
    assert "(4/6 lines)" in out and "tests/" not in out


def test_coverage_empty_suite_still_fails_the_gate(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "tests" / "test_ok.py").unlink()
    (repo / "src").mkdir()
    (repo / "src" / "calc.py").write_text("x = 1\n")
    code, out = run(["coverage", "src"], repo, capsys)
    assert code == 1 and "tests failed; coverage not measured" in out


def test_coverage_unavailable_is_words_not_a_failure(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(coverage_unavailable="nano-coverage addon not installed")])
    code, out = run(["coverage"], make_repo(tmp_path), capsys)
    assert code == 0
    assert out.count("coverage not measurable — nano-coverage addon not installed") == 1
    assert "nothing measured" not in out


def test_coverage_unavailable_never_calls_coverage_cmd_or_parse(tmp_path, capsys, monkeypatch):
    m = fake(coverage_unavailable="no tool")
    m.coverage_cmd = lambda root, t, out: (_ for _ in ()).throw(AssertionError("should not run"))
    m.coverage_parse = lambda root, out: (_ for _ in ()).throw(AssertionError("should not run"))
    monkeypatch.setattr(langs, "ALL", [m])
    code, _out = run(["coverage"], make_repo(tmp_path), capsys)
    assert code == 0


def test_coverage_denominator_includes_a_file_nothing_imports_under_an_init_less_src(tmp_path, capsys):
    repo = make_repo(tmp_path)
    _src(repo, "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n"
               "    if x > hi:\n        return hi\n    return x\n")
    (repo / "src" / "window.py").write_text("def show():\n    return 1\n")   # a GTK window: no test imports it
    _code, out = run(["coverage"], repo, capsys)
    assert "(4/8 lines)" in out and "src/window.py" in out               # BACKLOG #42: was 4/6
