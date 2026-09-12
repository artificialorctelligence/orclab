"""Shared helpers for the cli tests. Not a test module: under --import-mode=importlib test
modules cannot import each other (pytest's rule), and `tests` is a namespace package spanning every
scripts/tests dir on pythonpath, so this file's basename must stay unique across the project."""

import subprocess
import types

from orc_test import cli
from orc_test.model import Coverage, Finding


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


def fake(mutation=None, unavailable=None, cov=(9, 10), lint=None, test_cmd=None, coverage_unavailable=None):
    m = types.SimpleNamespace(
        KEY="fake", LABEL="Fake", SOURCE_EXT=".py", MARKERS=["pyproject.toml"], TOOLS={}, CAVEATS=["a caveat"],
        mutation_unavailable=lambda root: unavailable, missing=lambda root: [],
        test_cmd=lambda root, t: test_cmd if test_cmd is not None else ["true"],
        coverage_unavailable=lambda root: coverage_unavailable,
        coverage_cmd=lambda root, t, out: ["true"],
        coverage_parse=lambda root, out: Coverage(*cov, {"src/a.py": cov}),
        mutation_cmd=lambda root, t, out: ["true"],
        mutation_parse=lambda root, out: mutation,
        lint=lambda root, t, out: lint if lint is not None else [
            Finding("tests/test_a.py", 3, "no assertion in test_x")])
    return m
