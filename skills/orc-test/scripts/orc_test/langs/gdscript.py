"""GDScript (Godot 4): gdUnit4's CLI runner; nano-coverage (alpha) for lcov; gdmutant (Stryker JSON)."""

import os
import pathlib
import re
import shutil

from .. import lcov, stryker
from ..model import Coverage, Finding, Mutation
from ..runner import run

KEY = "gdscript"
LABEL = "GDScript"
SOURCE_EXT = ".gd"
MARKERS = ["project.godot"]
TOOLS = {"gdUnit4": "install the gdUnit4 addon (Godot Asset Library) — it ships addons/gdUnit4/runtest.sh",
         "GODOT_BIN": "export GODOT_BIN=/path/to/godot (the 4.x binary gdUnit4 should run)"}
CAVEATS = ["A fresh checkout needs one `$GODOT_BIN --headless --import` first, or gdUnit4's own scripts fail to parse.",
           "gdUnit4 exits 100 on test failures and 101 on warnings.",
           "nano-coverage is alpha and built from source; its lcov lands at the project root.",
           "gdmutant is 0.1.x from one maintainer; pin the minor (pip install 'gdmutant==0.1.*')."]
SKIP_DIRS = {"addons"}             # gdmutant never mutates addons/; do not count them either
SANDBOX = {".orclab", "reports"}   # gdmutant reruns gdUnit4/GUT, which write their JUnit XML under reports/
_GDLINT = re.compile(r"^(?P<file>[^:]+):(?P<line>\d+): (?P<msg>.*)$", re.M)


def _runner(root):
    return pathlib.Path(root) / "addons" / "gdUnit4" / "runtest.sh"


def missing(root):
    if not _runner(root).exists():
        return ["gdUnit4"]
    return [] if os.environ.get("GODOT_BIN") else ["GODOT_BIN"]


def test_cmd(root, target):
    return ["./addons/gdUnit4/runtest.sh", "-a", target or "test"]


def coverage_unavailable(root):
    if not (pathlib.Path(root) / "addons" / "nano_coverage").exists():
        return "nano-coverage addon not installed (github.com/IgorBayerl/nano-coverage-godot, alpha, build from source)"
    return None


def coverage_cmd(root, target, out):
    # nano-coverage hooks gdUnit4's session and writes lcov.info at the project root
    return test_cmd(root, target)


def coverage_parse(root, out):
    report = pathlib.Path(root) / "lcov.info"
    if not report.exists():
        return Coverage(0, 0)
    return lcov.parse(report)


def mutation_unavailable(root, target=None):
    if shutil.which("gdmutant") is None:
        return "gdmutant not installed — pip install 'gdmutant==0.1.*'"
    return None


def mutation_cmd(root, target, out):
    # A directory mutates every .gd under it (addons/ and dot-dirs excluded); test/ is excluded
    # here because mutating the suite itself measures nothing. gdUnit4's layout matches gdmutant's
    # default --tests res://test; GUT keeps suites in test/unit and needs it spelled out.
    cmd = ["gdmutant", "run", target or ".", "--project", str(root), "--exclude", "test/*",
           "--json", str(pathlib.Path(out) / "mutation-report.json"), "--progress", "plain"]
    cmd += ["--runner", "gdunit4"] if _runner(root).exists() else ["--runner", "gut", "--tests", "res://test/unit"]
    if os.environ.get("GODOT_BIN"):
        cmd += ["--godot", os.environ["GODOT_BIN"]]
    return cmd


def mutation_parse(root, out):
    p = stryker.find(out) if pathlib.Path(out).is_dir() else None
    return stryker.parse(p, root) if p else Mutation(0, 0)


def lint(root, target, out):
    if shutil.which("gdlint") is None:
        return "gdlint not installed — pip install gdtoolkit"
    cp = run(["gdlint", target or "test"], cwd=root)
    return [Finding(m["file"], int(m["line"]), m["msg"]) for m in _GDLINT.finditer(cp.stdout)]
