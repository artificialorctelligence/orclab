import subprocess
import types

import pytest

from orc_test import detect


def _mod(key, markers):
    return types.SimpleNamespace(KEY=key, MARKERS=markers)


PY = _mod("python", ["pyproject.toml", "setup.py"])
JS = _mod("javascript", ["package.json"])
CS = _mod("csharp", ["*.csproj", "*.sln"])


def test_project_root_requires_git(tmp_path):
    with pytest.raises(detect.NotAProject):
        detect.project_root(tmp_path)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    assert detect.project_root(tmp_path) == tmp_path.resolve()


def test_languages_by_marker_depth_two_and_skips_node_modules(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "App.csproj").write_text("")
    (tmp_path / "node_modules" / "x").mkdir(parents=True)
    (tmp_path / "node_modules" / "x" / "package.json").write_text("{}")
    found = detect.languages(tmp_path, [PY, JS, CS])
    assert [m.KEY for m in found] == ["python", "csharp"]


def test_declared_test_cmd_precedence(tmp_path):
    (tmp_path / "package.json").write_text('{"scripts": {"test": "vitest run"}}')
    (tmp_path / "Makefile").write_text("test:\n\tpytest\n")
    cfg = {"languages": {"python": {"test": "make check"}}}
    assert detect.declared_test_cmd(tmp_path, "python", cfg) == ["make", "check"]
    assert detect.declared_test_cmd(tmp_path, "javascript", {"languages": {}}) == ["npm", "test"]
    assert detect.declared_test_cmd(tmp_path, "dart", {"languages": {}}) == ["make", "test"]
    (tmp_path / "Makefile").unlink()
    assert detect.declared_test_cmd(tmp_path, "dart", {"languages": {}}) is None
