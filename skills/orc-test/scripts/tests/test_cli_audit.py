"""`/orc-test audit` (spec 2026-09-19-orclab-v22-security-discipline-design.md §3): one line per
language, ✓/✗ on vulnerable dependencies, never installs, 'not available' where no free tool exists."""

from orc_test import langs
from tests.helpers import fake, make_repo, run


def _with(monkeypatch, m):
    monkeypatch.setattr(langs, "ALL", [m])


def test_clean_audit_is_a_tick_and_exit_zero(tmp_path, capsys, monkeypatch):
    _with(monkeypatch, fake())
    code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert code == 0 and "Fake       audit ✓ 0 vulnerable" in out


def test_findings_are_a_cross_listed_and_exit_one(tmp_path, capsys, monkeypatch):
    _with(monkeypatch, fake(audit_findings=["requests 2.19.0: CVE-2018-18074 — fix 2.20.0",
                                             "urllib3 1.24: CVE-2019-11324 — fix 1.24.2"]))
    code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert code == 1 and "Fake       audit ✗ 2 vulnerable" in out
    assert "    requests 2.19.0: CVE-2018-18074 — fix 2.20.0" in out


def test_missing_tool_is_named_with_its_install_line_and_skipped(tmp_path, capsys, monkeypatch):
    _with(monkeypatch, fake(audit_unavailable="faketool not installed"))
    code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert code == 0 and "Fake: missing faketool — install faketool — skipped" in out
    assert "✓" not in out and "✗" not in out


def test_language_with_no_free_tool_says_so_and_is_not_a_failure(tmp_path, capsys, monkeypatch):
    _with(monkeypatch, fake(audit_tool=None))
    code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert code == 0 and "Fake       audit not available — no free audit tool for Fake" in out


def test_no_language_prints_nothing_audited(tmp_path, capsys, monkeypatch):
    m = fake()
    m.MARKERS = ["no-such-marker.xyz"]
    _with(monkeypatch, m)
    code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert code == 0 and "nothing audited" in out


def test_audit_prints_the_command_it_ran(tmp_path, capsys, monkeypatch):
    _with(monkeypatch, fake())
    _code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert "$ true" in out


def test_nothing_declared_is_not_available_and_never_asks_for_the_tool(tmp_path, capsys, monkeypatch):
    # BACKLOG #54: a project that declares nothing to audit is "not available", not red — and the
    # check runs before the tool check, so a tool-only repo is never told to install a tool that
    # will then refuse it.
    def never(root):
        raise AssertionError("audit_unavailable consulted although nothing is declared")
    m = fake()
    m.audit_nothing = lambda root: "nothing declared: pyproject.toml has no [project] table"
    m.audit_unavailable = never
    _with(monkeypatch, m)
    code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert code == 0
    assert "Fake       audit not available — nothing declared: pyproject.toml has no [project] table" in out
    assert "$ true" not in out and "vulnerable" not in out


def test_unreadable_audit_output_fails_the_gate_without_a_bogus_count(tmp_path, capsys, monkeypatch):
    _with(monkeypatch, fake(audit_findings=["audit output not understood — see above"]))
    code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert code == 1 and "Fake: audit output not understood — see above" in out
    assert "vulnerable" not in out
