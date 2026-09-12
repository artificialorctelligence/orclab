"""Java: JUnit 5 through Maven or Gradle, JaCoCo, Pitest, PMD's unit-test rules."""

import json
import pathlib
import shutil

from .. import jacoco, pitest
from ..model import Coverage, Finding, Mutation
from ..runner import run

KEY = "java"
LABEL = "Java"
SOURCE_EXT = ".java"
MARKERS = ["pom.xml", "build.gradle", "build.gradle.kts"]
TOOLS = {
    "java": "install a JDK (https://adoptium.net)",
    "mvn": "install Maven (https://maven.apache.org)",
    "gradle": "install Gradle (https://gradle.org), or commit the wrapper (./gradlew)",
}
CAVEATS = ["Gradle projects must apply the `jacoco` plugin (and `pitest` for TCE) themselves; "
           "Maven needs nothing in the pom for coverage, only the pitest-junit5-plugin dependency for TCE."]
SANDBOX = {"target", "build", ".gradle"}   # Maven/Gradle/Pitest/JaCoCo build output

_JACOCO = "org.jacoco:jacoco-maven-plugin"


def _maven(root):
    return (pathlib.Path(root) / "pom.xml").exists()


def _gradle_cmd(root):
    return ["./gradlew"] if (pathlib.Path(root) / "gradlew").exists() else ["gradle"]


def missing(root):
    needed = dict(TOOLS)
    if _maven(root):
        del needed["gradle"]
    else:
        del needed["mvn"]
        if (pathlib.Path(root) / "gradlew").exists():
            del needed["gradle"]
    return [t for t in needed if shutil.which(t) is None]


def _pkg_filter(target):
    # src/main/java/com/x → com.x.* ; anything else: no narrowing
    parts = pathlib.Path(target).parts
    if "java" in parts:
        return ".".join(parts[parts.index("java") + 1:]) + ".*"
    return None


def test_cmd(root, target):
    if _maven(root):
        f = _pkg_filter(target) if target else None
        return ["mvn", "-q", "test"] + ([f"-Dtest={f}"] if f else [])
    return _gradle_cmd(root) + ["test"]


def coverage_cmd(root, target, out):
    if _maven(root):
        return ["mvn", "-q", f"{_JACOCO}:prepare-agent", "test", f"{_JACOCO}:report"]
    return _gradle_cmd(root) + ["test", "jacocoTestReport"]


def coverage_parse(root, out):
    p = jacoco.find(root)
    return jacoco.parse(p) if p else Coverage(0, 0)


def _find_build_gradle(root):
    root = pathlib.Path(root)
    for pattern in ("build.gradle*", "*/build.gradle*", "*/*/build.gradle*"):
        hit = next(iter(sorted(root.glob(pattern))), None)
        if hit is not None:
            return hit
    return None


def mutation_unavailable(root, target=None):
    if _maven(root):
        if "pitest-junit5-plugin" not in (pathlib.Path(root) / "pom.xml").read_text():
            return ("Pitest needs the org.pitest:pitest-junit5-plugin dependency in the pom "
                    "(plus JUnit 5) — see languages/java.md")
        return None
    build_file = _find_build_gradle(root)
    if build_file is None:
        return "no build.gradle found at or below the project root"
    build = build_file.read_text()
    return None if "pitest" in build else "Gradle project does not apply the pitest plugin (info.solidsoft.pitest)"


def mutation_cmd(root, target, out):
    if _maven(root):
        cmd = ["mvn", "-q", "org.pitest:pitest-maven:mutationCoverage", "-DoutputFormats=XML,HTML",
               "-DwithHistory", "-DtimestampedReports=false"]
        f = _pkg_filter(target) if target else None
        return cmd + ([f"-DtargetClasses={f}"] if f else [])
    return _gradle_cmd(root) + ["pitest"]


def mutation_parse(root, out):
    p = pitest.find(root)
    return pitest.parse(p) if p else Mutation(0, 0)


def _test_dir(target):
    # src/main/java/<pkg-path> → src/test/java/<pkg-path>; anything else is used as given.
    if not target:
        return "src/test"
    parts = pathlib.Path(target).parts
    if parts[:3] == ("src", "main", "java"):
        return str(pathlib.Path("src", "test", "java", *parts[3:]))
    return target


def lint(root, target, out):
    if shutil.which("pmd") is None:
        return "PMD not installed — https://pmd.github.io (`pmd check` with the unit-test rules)"
    tests = pathlib.Path(root) / _test_dir(target)
    cp = run(["pmd", "check", "-d", str(tests), "-f", "json", "--no-progress", "-R",
              "category/java/bestpractices.xml/UnitTestShouldIncludeAssert,"
              "category/java/bestpractices.xml/UnitTestContainsTooManyAsserts"], cwd=root)
    try:
        data = json.loads(cp.stdout[cp.stdout.index("{"):])
    except ValueError:
        return f"PMD produced no JSON (exit {cp.returncode})"
    return [Finding(str(pathlib.Path(f["filename"]).relative_to(root)), v["beginline"], v["description"])
            for f in data.get("files", []) for v in f.get("violations", [])]
