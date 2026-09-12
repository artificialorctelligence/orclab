"""JavaScript/TypeScript: vitest or jest, lcov via their coverage reporters, StrykerJS."""

import json
import pathlib
import shutil

from .. import lcov, stryker
from ..model import Finding
from ..runner import run

KEY = "javascript"
LABEL = "JS/TS"
SOURCE_EXT = ".js"    # TypeScript projects are counted by .js only for the "mutating N files"
                      # announcement — informational, not a gate.
MARKERS = ["package.json"]
TOOLS = {"npx": "install Node.js (https://nodejs.org) — npx ships with npm"}
CAVEATS = ["Stryker's incremental file is reports/stryker-incremental.json; commit it or add it "
           "to .gitignore, either is fine, but do not delete it between runs."]


def _deps(root):
    pkg = pathlib.Path(root) / "package.json"
    data = json.loads(pkg.read_text()) if pkg.exists() else {}
    return {**data.get("dependencies", {}), **data.get("devDependencies", {})}


def _runner(root):
    return "vitest" if "vitest" in _deps(root) else "jest"


def missing(root):
    return [t for t in TOOLS if shutil.which(t) is None]


def test_cmd(root, target):
    base = ["npx", "vitest", "run"] if _runner(root) == "vitest" else ["npx", "jest"]
    return base + ([target] if target else [])


def coverage_cmd(root, target, out):
    if _runner(root) == "vitest":
        return ["npx", "vitest", "run", "--coverage", "--coverage.reporter=lcov",
                "--coverage.reporter=html", f"--coverage.reportsDirectory={out}"] + ([target] if target else [])
    return ["npx", "jest", "--coverage", "--coverageReporters=lcov", "--coverageReporters=html",
            f"--coverageDirectory={out}"] + ([target] if target else [])


def coverage_parse(root, out):
    return lcov.parse(pathlib.Path(out) / "lcov.info")


def mutation_unavailable(root):
    if "@stryker-mutator/core" not in _deps(root):
        return ("StrykerJS not installed — npm i -D @stryker-mutator/core "
                f"@stryker-mutator/{_runner(root)}-runner, then npx stryker init")
    return None


def mutation_cmd(root, target, out):
    cmd = ["npx", "stryker", "run", "--incremental", "--reporters", "json,progress",
           f"--jsonReporter.fileName={pathlib.Path(out) / 'mutation.json'}"]
    if target:
        cmd += ["--mutate", f"{target}/**/*"]
    return cmd


def mutation_parse(root, out):
    return stryker.parse(stryker.find(out), root)


def lint(root, target, out):
    deps = _deps(root)
    plugin = next((p for p in ("@vitest/eslint-plugin", "eslint-plugin-jest") if p in deps), None)
    if not plugin or "eslint" not in deps:
        return "eslint not configured with @vitest/eslint-plugin or eslint-plugin-jest"
    cp = run(["npx", "eslint", "--format", "json", "--no-error-on-unmatched-pattern", target or "."], cwd=root)
    try:
        results = json.loads(cp.stdout[cp.stdout.index("["):])
    except ValueError:
        return f"eslint produced no JSON (exit {cp.returncode})"
    prefix = "vitest/" if plugin.startswith("@vitest") else "jest/"
    return [Finding(str(pathlib.Path(r["filePath"]).relative_to(root)), m["line"], m["message"])
            for r in results for m in r["messages"] if (m.get("ruleId") or "").startswith(prefix)]
