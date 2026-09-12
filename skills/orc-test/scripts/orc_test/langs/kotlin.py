"""Kotlin: Gradle + JUnit 5, Kover (JaCoCo-format XML), Pitest with or without Arcmutate."""

import pathlib
import shutil

from .. import jacoco, licence, pitest
from ..detect import SKIP_DIRS
from ..model import Coverage, Finding, Mutation
from ..runner import run
from .java import _find_build_gradle

KEY = "kotlin"
LABEL = "Kotlin"
SOURCE_EXT = ".kt"
MARKERS = ["build.gradle", "build.gradle.kts"]
TOOLS = {"java": "install a JDK (https://adoptium.net)"}
CAVEATS = []          # computed per project — see CAVEATS_FOR


def claims(root):
    root = pathlib.Path(root)
    dirs = [root] + list(root.glob("*")) + list(root.glob("*/*"))
    for d in dirs:
        if any(part in SKIP_DIRS for part in d.relative_to(root).parts):
            continue
        src = d / "src"
        if src.is_dir() and any(True for _ in src.rglob("*.kt")):
            return True
    return False


def CAVEATS_FOR(root):
    label = licence.open_source(root)
    if label:
        return [f"TCE via Pitest + Arcmutate's Kotlin plugin (free for open source; this project "
                f"declares {label}). Arcmutate filters the junk mutants plain Pitest "
                "produces on Kotlin bytecode."]
    return ["TCE is approximate: plain Pitest on Kotlin bytecode reports junk mutants from compiler-"
            "generated code. Arcmutate's Kotlin plugin fixes that but needs an open-source licence, "
            "and this project does not declare one."]


def _gradle(root):
    return ["./gradlew"] if (pathlib.Path(root) / "gradlew").exists() else ["gradle"]


def missing(root):
    return [t for t in TOOLS if shutil.which(t) is None]


def test_cmd(root, target):
    return _gradle(root) + ["test"]


def coverage_cmd(root, target, out):
    return _gradle(root) + ["test", "koverXmlReport"]


def coverage_parse(root, out):
    p = jacoco.find(root)
    return jacoco.parse(p) if p else Coverage(0, 0)


def mutation_unavailable(root):
    build_file = _find_build_gradle(root)
    if build_file is None:
        return "no build.gradle found at or below the project root"
    build = build_file.read_text()
    return None if "pitest" in build else "Gradle project does not apply the pitest plugin (info.solidsoft.pitest)"


def mutation_cmd(root, target, out):
    return _gradle(root) + ["pitest"]


def mutation_parse(root, out):
    p = pitest.find(root)
    return pitest.parse(p) if p else Mutation(0, 0)


def lint(root, target, out):
    if shutil.which("detekt") is None:
        return "detekt not installed — https://detekt.dev/docs/gettingstarted/cli"
    tests = pathlib.Path(root) / (target or "src/test")
    report = pathlib.Path(out) / "detekt.xml"
    run(["detekt", "--input", str(tests), "--report", f"xml:{report}"], cwd=root)
    import xml.etree.ElementTree as ET
    if not report.exists():
        return "detekt wrote no report"
    return [Finding(str(pathlib.Path(f.get("name")).relative_to(root)), int(e.get("line")), e.get("message"))
            for f in ET.parse(report).getroot().iter("file") for e in f.iter("error")]
