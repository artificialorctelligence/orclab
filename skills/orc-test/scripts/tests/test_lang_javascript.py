import json
from unittest.mock import patch

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
