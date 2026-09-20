"""JavaScript/TypeScript: vitest or jest, lcov via their coverage reporters, StrykerJS."""

import json
import pathlib
import shutil

from .. import lcov, stryker
from ..model import Finding, Mutation
from ..runner import run

KEY = "javascript"
LABEL = "JS/TS"
SOURCE_EXT = ".js"    # TypeScript projects are counted by .js only for the "mutating N files"
                      # announcement — informational, not a gate.
MARKERS = ["package.json"]
TOOLS = {"npx": "install Node.js (https://nodejs.org) — npx ships with npm"}
CAVEATS = [("Stryker's incremental file is reports/stryker-incremental.json; commit it or add it "
           "to .gitignore, either is fine, but do not delete it between runs.")]
SANDBOX = {"reports", ".stryker-tmp"}   # legitimate even when committed, per the caveat above

AUDIT_TOOL = ("npm", "install Node.js (https://nodejs.org) — npm ships with it")
_UNREADABLE = ["audit output not understood — see above"]


def audit_unavailable(root):
    return None if shutil.which("npm") else "npm not installed"


def audit_cmd(root):
    # Reads package-lock.json ("npm requires a package-lock or shrinkwrap in order to run the
    # audit"); without one npm prints an ENOLOCK error JSON, which lands on the sentinel.
    return ["npm", "audit", "--json"]


def _fix(v):
    fix = v.get("fixAvailable")
    if isinstance(fix, dict):
        return f"{fix['name']} {fix['version']}"
    return "npm audit fix" if fix else "none published"


def audit_findings(stdout, returncode):
    # npm keys `vulnerabilities` by package and gives the vulnerable `range`, not the installed
    # version (languages/javascript.md). A `via` entry is an advisory dict, or a bare package name
    # when the vulnerability is inherited from a dependency; both are named. Exit code is not
    # consulted: npm's is tunable by --audit-level, the output is not.
    try:
        # runner.run merges stderr, and an .npmrc can make npm print a warning line there ahead
        # of the JSON (e.g. "npm warn config shrinkwrap ...", seen live 2026-09-19) — read from
        # the first `{`, the way python.py and csharp.py do.
        data, _ = json.JSONDecoder().raw_decode(stdout, stdout.index("{"))
        vulns = data["vulnerabilities"]
        out = []
        for name, v in vulns.items():
            ids = [x["url"].rpartition("/")[2] if isinstance(x, dict) else f"via {x}" for x in v["via"]]
            out.append(f"{name} {v['range']}: {', '.join(dict.fromkeys(ids))} — fix {_fix(v)}")
        return out
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError, ValueError):
        return _UNREADABLE


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


def mutation_unavailable(root, target=None):
    deps = _deps(root)
    if "@stryker-mutator/core" not in deps or f"@stryker-mutator/{_runner(root)}-runner" not in deps:
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
    p = stryker.find(out)
    return stryker.parse(p, root) if p else Mutation(0, 0)


def lint(root, target, out):
    deps = _deps(root)
    candidates = ("@vitest/eslint-plugin", "eslint-plugin-jest") if _runner(root) == "vitest" \
        else ("eslint-plugin-jest", "@vitest/eslint-plugin")
    plugin = next((p for p in candidates if p in deps), None)
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
