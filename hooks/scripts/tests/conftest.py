"""One fixture for the hook tests: drive a hook's main() in this process.

The hooks are separate processes when Claude Code runs them - JSON on stdin, a decision on
stdout, exit 0 - and until 2026-09-15 their tests ran them that way too. Coverage and mutation
testing both see only this process, so those tests measured nothing (languages/python.md,
Caveats). Each test file now calls main() with stdin, stdout, cwd and environment pinned here,
and keeps one real subprocess test for the exit-0 contract."""

import io
import json

import pytest


@pytest.fixture
def run_hook(monkeypatch, capsys):
    """run_hook(main, payload, cwd=None) -> (exit_code, stdout, stderr). `payload` is the hook's
    stdin: a dict to be JSON-encoded, or a str sent as-is (for the garbage-input tests)."""
    def run(main, payload, cwd=None):
        if cwd is not None:
            monkeypatch.chdir(cwd)
        text = payload if isinstance(payload, str) else json.dumps(payload)
        monkeypatch.setattr("sys.stdin", io.StringIO(text))
        capsys.readouterr()
        code = main()
        out = capsys.readouterr()
        return code, out.out, out.err
    return run
