"""Kotlin: Gradle + JUnit 5, Kover (JaCoCo-format XML), Pitest with or without Arcmutate."""

import pathlib

from .. import jacoco, licence, pitest, probe
from ..detect import SKIP_DIRS
from ..model import Coverage, Finding, Mutation
from ..runner import run
from .java import (  # noqa: F401 — audit_findings is this module's too
    _DC_GRADLE,
    _find_build_gradle,
    _gradle_audit_cmd,
    _gradle_audit_unavailable,
    audit_findings,
    test_summary,
)

KEY = "kotlin"
LABEL = "Kotlin"
SOURCE_EXT = ".kt"
MARKERS = ["build.gradle", "build.gradle.kts"]
TOOLS = {"java": "install a JDK (https://adoptium.net)",
         "gradle": "install Gradle (https://gradle.org), or commit the wrapper (./gradlew)"}
CAVEATS = []          # computed per project — see CAVEATS_FOR
SANDBOX = {"build", ".gradle"}   # Gradle/Kover/Pitest build output

AUDIT_TOOL = ("dependency-check", f"declare {_DC_GRADLE}")   # the Gradle half of java.py's audit
audit_unavailable = _gradle_audit_unavailable
audit_cmd = _gradle_audit_cmd


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
    build = _find_build_gradle(root)
    arcmutate = build is not None and "arcmutate" in build.read_text()
    if label and arcmutate:
        return [(f"TCE via Pitest + Arcmutate's Kotlin plugin (free for open source; this project "
                f"declares {label}). Arcmutate filters the junk mutants plain Pitest "
                "produces on Kotlin bytecode.")]
    if label:
        return [(f"TCE is approximate (plain Pitest); this project declares {label}, so Arcmutate's "
                "Kotlin plugin is free — add com.arcmutate:pitest-kotlin-plugin to the build to "
                "filter the junk mutants plain Pitest produces on Kotlin bytecode.")]
    return [("TCE is approximate: plain Pitest on Kotlin bytecode reports junk mutants from compiler-"
            "generated code. Arcmutate's Kotlin plugin fixes that but needs an open-source licence, "
            "and this project does not declare one.")]


def _gradle(root):
    return ["./gradlew"] if (pathlib.Path(root) / "gradlew").exists() else ["gradle"]


def missing(root):
    needed = dict(TOOLS)
    if (pathlib.Path(root) / "gradlew").exists():
        del needed["gradle"]
    return [t for t in needed if not probe.which(t)]


def test_cmd(root, target):
    return _gradle(root) + ["test"]


def coverage_cmd(root, target, out):
    return _gradle(root) + ["test", "koverXmlReport"]


def coverage_parse(root, out):
    p = jacoco.find(root)
    return jacoco.parse(p) if p else Coverage(0, 0)


def mutation_unavailable(root, target=None):
    """Whether a `pitest` task exists to run — decided by *any* of the project's build files.

    Not just the first one `_find_build_gradle` returns, which in a Gradle project is the root's and
    names no module's tooling: orcweather's pitest is declared in `app/build.gradle.kts`, the only
    place it can be, and TCE read "does not apply the pitest plugin" beside a working `gradlew
    :app:pitest` (2026-09-27; BACKLOG #88).

    "pitest" rather than the plugin id, because on Android there is no plugin to apply — neither
    `info.solidsoft.pitest` nor the four-year-stale Android fork works on AGP, and a hand-written
    `JavaExec` task named `pitest` is how a project gets there. `languages/kotlin.md` has the task.
    """
    builds = [f for pattern in ("build.gradle*", "*/build.gradle*", "*/*/build.gradle*")
              for f in sorted(pathlib.Path(root).glob(pattern))
              if not any(part in SKIP_DIRS for part in f.relative_to(root).parts)]
    if not builds:
        return "no build.gradle found at or below the project root"
    if any("pitest" in f.read_text() for f in builds):
        return None
    return "no `pitest` task in any build.gradle — see languages/kotlin.md (no Gradle plugin works on Android)"


def mutation_cmd(root, target, out):
    return _gradle(root) + ["pitest"]


def mutation_parse(root, out):
    p = pitest.find(root)
    return pitest.parse(p) if p else Mutation(0, 0)


def _test_dirs(root, target):
    """Every directory holding test sources, for a linter's input.

    `src/test` is the single-module layout. A Gradle project can have any number of modules, and an
    Android app's tests live in `app/src/test` — pointed at the language root's `src/test` there,
    detekt is handed a path that does not exist, writes no report, and `analyze` says `lint: not
    run` on a project whose tests are right there (orcweather, 2026-09-27; BACKLOG #87).
    """
    root = pathlib.Path(root)
    if target:
        return [root / target]
    found = [d for d in sorted(root.glob("**/src/test"))
             if d.is_dir() and not any(part in SKIP_DIRS for part in d.relative_to(root).parts)]
    return found or [root / "src/test"]


def lint(root, target, out):
    if not probe.which("detekt"):
        return "detekt not installed — https://detekt.dev/docs/gettingstarted/cli"
    tests = ",".join(str(d) for d in _test_dirs(root, target))
    report = pathlib.Path(out) / "detekt.xml"
    run(["detekt", "--input", tests, "--report", f"xml:{report}"], cwd=root)
    import xml.etree.ElementTree as ET
    if not report.exists():
        return "detekt wrote no report"
    return [Finding(str(pathlib.Path(f.get("name")).relative_to(root)), int(e.get("line")), e.get("message"))
            for f in ET.parse(report).getroot().iter("file") for e in f.iter("error")]
