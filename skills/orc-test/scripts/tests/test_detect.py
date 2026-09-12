import os
import pathlib
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


def test_declared_test_cmd_ignores_malformed_package_json(tmp_path):
    (tmp_path / "package.json").write_text("{not valid json")
    assert detect.declared_test_cmd(tmp_path, "javascript", {"languages": {}}) is None


def test_languages_marker_at_depth_three_not_found(tmp_path):
    (tmp_path / "a" / "b" / "c").mkdir(parents=True)
    (tmp_path / "a" / "b" / "c" / "pyproject.toml").write_text("")
    found = detect.languages(tmp_path, [PY])
    assert found == []


def test_languages_marker_two_directories_down_found(tmp_path):
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "pyproject.toml").write_text("")
    found = detect.languages(tmp_path, [PY])
    assert [m.KEY for m in found] == ["python"]


def test_candidates_never_walks_into_skipped_dirs(tmp_path, monkeypatch):
    (tmp_path / "node_modules" / "x" / "y" / "z").mkdir(parents=True)
    (tmp_path / "node_modules" / "x" / "y" / "z" / "deep.json").write_text("{}")

    real_walk = os.walk
    visited = []

    def spying_walk(top, *a, **kw):
        for dirpath, dirnames, filenames in real_walk(top, *a, **kw):
            visited.append(dirpath)
            yield dirpath, dirnames, filenames

    monkeypatch.setattr(detect.os, "walk", spying_walk)
    list(detect._candidates(tmp_path))
    # node_modules gets pruned from the root's dirnames before os.walk ever descends,
    # so no visited dirpath should even be (or be under) node_modules.
    assert not any("node_modules" in pathlib.Path(v).parts for v in visited)
