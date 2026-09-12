import pytest

from orc_test import cli
from tests.test_cli import make_repo, run

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
