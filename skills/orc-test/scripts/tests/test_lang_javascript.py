import json

from orc_test.langs import javascript as js


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
    _pkg(tmp_path, {"vitest": "^5", "@stryker-mutator/core": "^10"})
    assert js.mutation_unavailable(tmp_path) is None


def test_lint_needs_eslint_plugin(tmp_path):
    _pkg(tmp_path, {"vitest": "^5"})
    assert js.lint(tmp_path, None, tmp_path).startswith("eslint not configured")
