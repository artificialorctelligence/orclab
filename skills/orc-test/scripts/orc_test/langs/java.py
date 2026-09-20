"""Java: JUnit 5 through Maven or Gradle, JaCoCo, Pitest, PMD's unit-test rules."""

import json
import pathlib
import shutil

from .. import jacoco, pitest, probe
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
CAVEATS = [("Gradle projects must apply the `jacoco` plugin (and `pitest` for TCE) themselves; "
           "Maven needs nothing in the pom for coverage, only the pitest-junit5-plugin dependency for TCE.")]
SANDBOX = {"target", "build", ".gradle"}   # Maven/Gradle/Pitest/JaCoCo build output

_JACOCO = "org.jacoco:jacoco-maven-plugin"

# OWASP dependency-check 13.0.0, a build plugin: "installed" when the build file names it.
_DC_GRADLE = ('plugins { id("org.owasp.dependencycheck") version "13.0.0" } and '
              'dependencyCheck { formats = listOf("JSON") } in build.gradle(.kts)')
AUDIT_TOOL = ("dependency-check",
              ("declare org.owasp:dependency-check-maven 13.0.0 under <plugins> in "
               f"pom.xml, or {_DC_GRADLE}"))
_UNREADABLE = ["audit output not understood — see above"]


def _maven(root):
    return (pathlib.Path(root) / "pom.xml").exists()


def _gradle_cmd(root):
    return ["./gradlew"] if (pathlib.Path(root) / "gradlew").exists() else ["gradle"]


def _gradle_audit_unavailable(root):
    build = _find_build_gradle(root)
    text = build.read_text() if build else ""
    # formats is build-file config only (no -P for it), so a JSON report has to be asked for there.
    return None if "org.owasp.dependencycheck" in text and "JSON" in text else "dependency-check plugin not applied"


def audit_unavailable(root):
    if _maven(root):
        return None if "dependency-check-maven" in (pathlib.Path(root) / "pom.xml").read_text() else "dependency-check plugin not declared"
    return _gradle_audit_unavailable(root)


def _report_cmd(build, report):
    """The build, then the report on stdout — audit_findings sees stdout only. The build's own
    output goes to a log beside the report and stands in for it when no report was written, so
    an audit that never ran lands on the sentinel with the reason printed. The old report goes
    first: a build that fails before writing (NVD update, plugin resolution) must not leave last
    run's clean report to be read as today's."""
    d = report.rpartition("/")[0]
    log = f"{d}/dependency-check.log"
    return ["sh", "-c", f"rm -f {report}; mkdir -p {d}; {build} >{log} 2>&1; cat {report} 2>/dev/null || cat {log}"]


def _gradle_audit_cmd(root):
    return _report_cmd(" ".join(_gradle_cmd(root) + ["dependencyCheckAnalyze"]), "build/reports/dependency-check-report.json")


def audit_cmd(root):
    if _maven(root):
        return _report_cmd("mvn -q org.owasp:dependency-check-maven:check -Dformat=JSON", "target/dependency-check-report.json")
    return _gradle_audit_cmd(root)


def _vulns_of(dep, seen):
    for v in dep.get("vulnerabilities", []):
        key = (dep["fileName"], v["name"])
        if key in seen:
            continue
        seen.add(key)
        yield f"{dep['fileName']}: {v['name']} ({v.get('severity', 'unscored')}) — fix not reported by dependency-check"


def audit_findings(stdout, returncode):
    # The report decides, not the exit code: failBuildOnCVSS defaults to 11 (never fails) and the
    # report is written before that check either way. dependency-check names no fixed version —
    # it matches CPEs against the NVD — so the line ends at the advisory. seen: a shaded or
    # multi-CPE jar can list one CVE more than once.
    try:
        seen = set()
        return [line for dep in json.loads(stdout)["dependencies"] for line in _vulns_of(dep, seen)]
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        return _UNREADABLE


def missing(root):
    needed = dict(TOOLS)
    if _maven(root):
        del needed["gradle"]
    else:
        del needed["mvn"]
        if (pathlib.Path(root) / "gradlew").exists():
            del needed["gradle"]
    return [t for t in needed if not probe.which(t)]


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
              ("category/java/bestpractices.xml/UnitTestShouldIncludeAssert,"
              "category/java/bestpractices.xml/UnitTestContainsTooManyAsserts")], cwd=root)
    try:
        data = json.loads(cp.stdout[cp.stdout.index("{"):])
    except ValueError:
        return f"PMD produced no JSON (exit {cp.returncode})"
    return [Finding(str(pathlib.Path(f["filename"]).relative_to(root)), v["beginline"], v["description"])
            for f in data.get("files", []) for v in f.get("violations", [])]
