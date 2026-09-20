"""Tool checks happen where the tools run: the host, or the container when one is active
(spec 2026-09-20-orclab-v23-containers-design.md §2)."""

import subprocess

from orc_test import container, probe, runner


def test_host_checks_when_no_container(monkeypatch):
    runner.use(None)
    monkeypatch.setattr(probe.shutil, "which", lambda n: "/usr/bin/x" if n == "x" else None)
    assert probe.which("x") and not probe.which("y")
    assert probe.python_module("json") and not probe.python_module("no_such_module_anywhere")


def test_container_checks_go_through_run(monkeypatch, tmp_path):
    seen = []
    runner.use(container.Container(root=tmp_path, runner="docker"))
    monkeypatch.setattr(probe.runner, "run", lambda cmd, cwd: seen.append(cmd) or _cp(0 if "pytest" in cmd[-1] else 1))
    try:
        assert probe.python_module("pytest") and not probe.python_module("nope")
        assert probe.which("pytest") and not probe.which("nope")
    finally:
        runner.use(None)
    assert seen[0] == ["python3", "-c", "import pytest"]
    assert seen[2] == ["sh", "-c", "command -v pytest"]


def _cp(code):
    return subprocess.CompletedProcess([], code, stdout="", stderr="")
