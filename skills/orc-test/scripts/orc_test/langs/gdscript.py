"""GDScript (Godot 4): gdUnit4's CLI runner; nano-coverage (alpha) for lcov; no mutation tool."""

import os
import pathlib
import re
import shutil

from .. import lcov
from ..model import Coverage, Finding
from ..runner import run

KEY = "gdscript"
LABEL = "GDScript"
SOURCE_EXT = ".gd"
MARKERS = ["project.godot"]
TOOLS = {"gdUnit4": "install the gdUnit4 addon (Godot Asset Library) — it ships addons/gdUnit4/runtest.sh",
         "GODOT_BIN": "export GODOT_BIN=/path/to/godot (the 4.x binary gdUnit4 should run)"}
CAVEATS = ["gdUnit4 exits 100 on test failures and 101 on warnings.",
           "nano-coverage is alpha and built from source; its lcov lands at the project root."]
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


def mutation_unavailable(root):
    return "no mutation tool exists for GDScript (checked 2026-09-11)"


def mutation_cmd(root, target, out):
    raise NotImplementedError


def mutation_parse(root, out):
    raise NotImplementedError


def lint(root, target, out):
    if shutil.which("gdlint") is None:
        return "gdlint not installed — pip install gdtoolkit"
    cp = run(["gdlint", target or "test"], cwd=root)
    return [Finding(m["file"], int(m["line"]), m["msg"]) for m in _GDLINT.finditer(cp.stdout)]
