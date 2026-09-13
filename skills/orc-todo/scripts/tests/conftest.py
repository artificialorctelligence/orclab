"""Every test isolates itself by passing a throwaway repo as `cwd`. That holds only while the code
honours the argument: under mutation testing a `cwd → None` mutant falls back to the process cwd,
which was the real Orclab checkout — and the suite wrote its fixtures into the real BACKLOG.md
(BACKLOG #34). So the ambient cwd is pinned to a sandbox too; a dropped argument now lands here,
where the assertion sees it and the mutant dies."""

import subprocess

import pytest


@pytest.fixture(autouse=True)
def _ambient_cwd_is_a_sandbox(tmp_path_factory, monkeypatch):
    sandbox = tmp_path_factory.mktemp("ambient")
    subprocess.run(["git", "init", "-q", str(sandbox)], check=True)
    (sandbox / "BACKLOG.md").write_text("# Backlog\n")
    monkeypatch.chdir(sandbox)
