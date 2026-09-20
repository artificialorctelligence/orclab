import json
import pathlib
from unittest.mock import patch

from orc_test import probe
from orc_test.langs import javascript as js
from orc_test.model import Finding, Mutation


def _pkg(tmp_path, dev):
    (tmp_path / "package.json").write_text(json.dumps({"devDependencies": dev}))


def test_source_ext():
    assert js.SOURCE_EXT == ".js"


def test_vitest_when_present_else_jest(tmp_path):
    _pkg(tmp_path, {"vitest": "^5"})
    assert js.test_cmd(tmp_path, None) == ["npx", "vitest", "run"]
    assert js.test_cmd(tmp_path, "src/x") == ["npx", "vitest", "run", "src/x"]
    _pkg(tmp_path, {"jest": "^30"})
    assert js.test_cmd(tmp_path, None) == ["npx", "jest"]


def test_coverage_cmd_writes_lcov_into_out(tmp_path):
    _pkg(tmp_path, {"vitest": "^5"})
    out = tmp_path / "out"
    cmd = js.coverage_cmd(tmp_path, None, out)
    assert cmd[:4] == ["npx", "vitest", "run", "--coverage"]
    assert f"--coverage.reportsDirectory={out}" in cmd and "--coverage.reporter=lcov" in cmd


def test_mutation_unavailable_without_stryker(tmp_path):
    _pkg(tmp_path, {"vitest": "^5"})
    assert "npm i -D @stryker-mutator/core" in js.mutation_unavailable(tmp_path)
    _pkg(tmp_path, {"vitest": "^5", "@stryker-mutator/core": "^10",
                    "@stryker-mutator/vitest-runner": "^10"})
    assert js.mutation_unavailable(tmp_path) is None


def test_mutation_unavailable_without_runner_package(tmp_path):
    # core present, but the vitest-runner companion package is missing
    _pkg(tmp_path, {"vitest": "^5", "@stryker-mutator/core": "^10"})
    assert "npm i -D @stryker-mutator/core" in js.mutation_unavailable(tmp_path)
    _pkg(tmp_path, {"vitest": "^5", "@stryker-mutator/core": "^10",
                    "@stryker-mutator/vitest-runner": "^10"})
    assert js.mutation_unavailable(tmp_path) is None


def test_mutation_parse_on_empty_out_dir(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    assert js.mutation_parse(tmp_path, out) == Mutation(0, 0, [])


def test_lint_needs_eslint_plugin(tmp_path):
    _pkg(tmp_path, {"vitest": "^5"})
    assert js.lint(tmp_path, None, tmp_path).startswith("eslint not configured")


def test_lint_parses_json_and_filters_by_plugin_prefix(tmp_path):
    _pkg(tmp_path, {"vitest": "^5", "eslint": "^9", "@vitest/eslint-plugin": "^1"})
    eslint_json = json.dumps([
        {"filePath": str(tmp_path / "src" / "a.test.js"), "messages": [
            {"ruleId": "vitest/expect-expect", "line": 3, "message": "Add an expect"},
            {"ruleId": "no-unused-vars", "line": 5, "message": "unused"},
            {"ruleId": None, "line": 7, "message": "parse error"}]}])
    fake_stdout = "npx: chatter before the real output\n" + eslint_json

    class FakeResult:
        stdout = fake_stdout
        returncode = 1

    with patch.object(js, "run", return_value=FakeResult()):
        findings = js.lint(tmp_path, None, tmp_path)

    assert findings == [Finding("src/a.test.js", 3, "Add an expect")]


# --- audit: npm audit --json (fixtures/npm_audit.json, captured) ---

_FIX = pathlib.Path(__file__).parent / "fixtures"
_UNREADABLE = ["audit output not understood — see above"]


def test_audit_tool_and_command():
    assert js.AUDIT_TOOL[0] == "npm"
    assert js.audit_cmd("/x") == ["npm", "audit", "--json"]


def test_audit_findings_from_captured_json():
    lines = js.audit_findings((_FIX / "npm_audit.json").read_text(), 1)
    assert len(lines) == 2   # metadata.vulnerabilities.total in the capture
    assert lines[0].startswith("lodash <=4.17.23: GHSA-35jh-r3h4-6jhm, GHSA-p6mc-m468-83gw, ")
    assert lines[0].endswith(" — fix lodash 4.18.1")
    assert lines[1] == "minimist 1.0.0 - 1.2.5: GHSA-vh95-rmgr-6w4m, GHSA-xvch-5gv4-984h — fix minimist 1.2.8"


def test_audit_findings_via_string_and_boolean_fix():
    # A package vulnerable only through a dependency has bare names in `via`; fixAvailable is
    # true (npm audit fix does it) or false (nothing published).
    data = json.dumps({"vulnerabilities": {
        "a": {"via": ["b", "b"], "range": "*", "fixAvailable": True},
        "b": {"via": [{"url": "https://github.com/advisories/GHSA-1"}], "range": "<2", "fixAvailable": False}}})
    assert js.audit_findings(data, 1) == ["a *: via b — fix npm audit fix", "b <2: GHSA-1 — fix none published"]


def test_audit_clean_and_unreadable():
    assert js.audit_findings('{"vulnerabilities": {}, "metadata": {}}', 0) == []
    assert js.audit_findings('{"error": {"code": "ENOLOCK"}}', 1) == _UNREADABLE   # no package-lock
    assert js.audit_findings("npm ERR! network", 1) == _UNREADABLE
    assert js.audit_findings('{"vulnerabilities": {"a": {"via": [{}]}}}', 1) == _UNREADABLE
    assert js.audit_findings("42", 1) == _UNREADABLE


def test_audit_findings_skips_stderr_prefix():
    # runner.run merges stderr into stdout, and an .npmrc with shrinkwrap=false makes npm print
    # a warning line on stderr ahead of the JSON (found live 2026-09-19) — read from the first
    # `{`, the way python.py and csharp.py do, instead of crashing json.loads on the prefix.
    prefixed = ("npm warn config shrinkwrap Use the --package-lock setting instead.\n"
                + (_FIX / "npm_audit.json").read_text())
    assert js.audit_findings(prefixed, 1) == js.audit_findings((_FIX / "npm_audit.json").read_text(), 1)


def test_audit_unavailable_names_npm(monkeypatch):
    monkeypatch.setattr(probe, "which", lambda tool: False)
    assert "npm" in js.audit_unavailable("/x")
    monkeypatch.setattr(probe, "which", lambda tool: True)
    assert js.audit_unavailable("/x") is None
