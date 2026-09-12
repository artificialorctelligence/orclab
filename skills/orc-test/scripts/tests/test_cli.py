import types

import pytest

from orc_test import langs
from tests.helpers import make_repo, run


def test_outside_git_says_so(tmp_path, capsys):
    code, out = run(["detect"], tmp_path, capsys)
    assert code == 1 and "not inside a git repository" in out


def test_detect_lists_languages(tmp_path, capsys):
    code, out = run(["detect"], make_repo(tmp_path), capsys)
    assert code == 0 and "detected: Python" in out


def test_run_green_suite_exits_zero_and_prints_command(tmp_path, capsys):
    code, out = run(["run"], make_repo(tmp_path), capsys)
    assert code == 0
    assert "$ python3 -m pytest -q '--ignore-glob=*/mutants/*'" in out
    assert "Python" in out and "passed" in out


def test_run_red_suite_exits_nonzero(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "tests" / "test_bad.py").write_text("def test_bad():\n    assert 0\n")
    code, out = run(["run"], repo, capsys)
    assert code == 1 and "failed" in out


def test_empty_suite_reports_zero_tests_not_failed(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "tests" / "test_ok.py").unlink()
    code, out = run(["run"], repo, capsys)
    assert code == 1
    assert "0 tests" in out and "✗" in out


def test_missing_tool_skips_language_with_install_line(tmp_path, capsys, monkeypatch):
    fake = types.SimpleNamespace(KEY="fake", LABEL="Fake", MARKERS=["pyproject.toml"],
                                 TOOLS={"faketool": "brew install faketool"},
                                 missing=lambda root: ["faketool"])
    monkeypatch.setattr(langs, "ALL", [fake])
    code, out = run(["run"], make_repo(tmp_path), capsys)
    assert "Fake: missing faketool — brew install faketool — skipped" in out
    assert code == 0


def test_declared_command_wins(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "Makefile").write_text("test:\n\t@echo make-ran\n")
    code, out = run(["run"], repo, capsys)
    assert "$ make test" in out and "make-ran" in out


def test_bad_config_reports_error(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / ".orclab").mkdir()
    (repo / ".orclab" / "test.yaml").write_text("coverage: [unterminated\n")
    code, out = run(["detect"], repo, capsys)
    assert code == 1 and "invalid YAML" in out
