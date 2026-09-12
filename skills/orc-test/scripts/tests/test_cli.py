import subprocess
import types

import pytest

from orc_test import cli, langs


def make_repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok():\n    assert 1\n")
    return tmp_path


def run(args, repo, capsys):
    code = cli.main(["--cwd", str(repo), *args])
    out = capsys.readouterr()
    return code, out.out + out.err


def test_outside_git_says_so(tmp_path, capsys):
    code, out = run(["detect"], tmp_path, capsys)
    assert code == 1 and "not inside a git repository" in out


def test_detect_lists_languages(tmp_path, capsys):
    code, out = run(["detect"], make_repo(tmp_path), capsys)
    assert code == 0 and "detected: Python" in out


def test_run_green_suite_exits_zero_and_prints_command(tmp_path, capsys):
    code, out = run(["run"], make_repo(tmp_path), capsys)
    assert code == 0
    assert "$ python3 -m pytest -q --ignore=mutants" in out
    assert "Python" in out and "passed" in out


def test_run_red_suite_exits_nonzero(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "tests" / "test_bad.py").write_text("def test_bad():\n    assert 0\n")
    code, out = run(["run"], repo, capsys)
    assert code == 1 and "failed" in out


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
