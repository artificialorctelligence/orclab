"""Dart/Flutter: dart test or flutter test, lcov via package:coverage, mutation_test (junit)."""

import pathlib
import re
import shlex
import shutil
import xml.etree.ElementTree as ET

from .. import lcov
from ..model import Coverage, Mutation, Survivor

KEY = "dart"
LABEL = "Dart"
SOURCE_EXT = ".dart"
MARKERS = ["pubspec.yaml"]
TOOLS = {
    "dart": "install the Dart SDK (https://dart.dev/get-dart) or Flutter",
    "flutter": "install Flutter (https://docs.flutter.dev/get-started/install)",
}
CAVEATS = ["mutation_test is young (pub.dev 1.8.0, 2026-02); its report is read from junit XML. "
           "dart_mutant (Rust, Stryker JSON) is the alternative if this proves unreliable.",
           "No test-specific lint exists for Dart; `dart analyze` runs, but it cannot see an "
           "assertion-free test."]
SANDBOX = {"coverage", ".dart_tool"}   # package:coverage/mutation_test/pub output

_CASE = re.compile(r"^(?P<file>[^:]+):(?P<line>\d+):\d+ (?P<what>.*)$")


def _flutter(root):
    return "sdk: flutter" in (pathlib.Path(root) / "pubspec.yaml").read_text()


def _tool(root):
    return "flutter" if _flutter(root) else "dart"


def missing(root):
    tool = _tool(root)
    return [] if shutil.which(tool) else [tool]


def test_cmd(root, target):
    return [_tool(root), "test"] + ([target] if target else [])


def coverage_cmd(root, target, out):
    # both write coverage/lcov.info at the project root; --coverage on dart test needs
    # package:coverage's format step, which `dart test --coverage=DIR` does not run itself.
    if _flutter(root):
        return ["flutter", "test", "--coverage"] + ([target] if target else [])
    quoted = shlex.quote(target) if target else ""
    return ["bash", "-c", "dart test --coverage=coverage " + quoted +
            " && dart run coverage:format_coverage --lcov --in=coverage --out=coverage/lcov.info --packages=.dart_tool/package_config.json --report-on=lib"]


def coverage_parse(root, out):
    report = pathlib.Path(root) / "coverage" / "lcov.info"
    return lcov.parse(report) if report.exists() else Coverage(0, 0)


def mutation_unavailable(root, target=None):
    if "mutation_test" not in (pathlib.Path(root) / "pubspec.yaml").read_text():
        return "mutation_test not installed — dart pub add --dev mutation_test"
    return None


def mutation_cmd(root, target, out):
    return ["dart", "run", "mutation_test", "-f", "junit", "-o", str(out)] + ([target] if target else [])


def mutation_parse(root, out):
    reports = list(pathlib.Path(out).rglob("*.xml"))
    if not reports:
        return Mutation(0, 0)
    return _parse_junit(max(reports, key=lambda p: p.stat().st_mtime))


def _parse_junit(path):
    killed, total, survivors = 0, 0, []
    for case in ET.parse(path).getroot().iter("testcase"):
        total += 1
        if case.find("failure") is None:
            killed += 1
            continue
        m = _CASE.match(case.get("name", ""))
        if m:
            survivors.append(Survivor(m["file"], int(m["line"]), m["what"]))
        else:
            survivors.append(Survivor(case.get("classname", "?"), 0, case.get("name", "")))
    return Mutation(killed, total, survivors)


def lint(root, target, out):
    return "no test-specific lint exists for Dart (dart analyze has no assertion-free rule)"
