"""One fixture, for `/orc-test analyze`. Two tests in test_cli.py prove that a timed-out or
interrupted action's *whole process group* is killed, using a real grandchild `sleep`; the code
puts the action in its own group (`start_new_session=True`). A mutant that drops that flag
leaves the action in *this* process's group, and `_kill_group` then SIGKILLs pytest and mutmut
with it - the whole `analyze` run died with exit 137 the first time (2026-09-15). Refusing to
kill our own group turns that mutant into an ordinary test failure.

It lives here, not in ../conftest.py: mutmut runs pytest from its mutants/ copy, which holds
tests/ (also_copy) and nothing above it, so a conftest beside the package is never loaded there."""

import os

import pytest


@pytest.fixture(autouse=True)
def _never_kill_our_own_process_group(monkeypatch):
    real_killpg = os.killpg
    own = os.getpgid(0)

    def guarded(pgid, sig):
        assert pgid != own, "refusing to kill the test process's own group"
        real_killpg(pgid, sig)

    monkeypatch.setattr(os, "killpg", guarded)
