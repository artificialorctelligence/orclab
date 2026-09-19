import pathlib
from types import SimpleNamespace

from orc_test.langs import java


def test_source_ext():
    assert java.SOURCE_EXT == ".java"


def test_maven_vs_gradle(tmp_path):
    (tmp_path / "pom.xml").write_text("<project/>")
    assert java.test_cmd(tmp_path, None) == ["mvn", "-q", "test"]
    assert java.test_cmd(tmp_path, "src/main/java/com/x") == ["mvn", "-q", "test", "-Dtest=com.x.*"]
    (tmp_path / "pom.xml").unlink()
    (tmp_path / "build.gradle.kts").write_text("")
    (tmp_path / "gradlew").write_text("")   # the wrapper _gradle_cmd checks for
    assert java.test_cmd(tmp_path, None) == ["./gradlew", "test"]


def test_coverage_cmd_maven_fully_qualified(tmp_path):
    (tmp_path / "pom.xml").write_text("<project/>")
    cmd = java.coverage_cmd(tmp_path, None, tmp_path)
    assert cmd == ["mvn", "-q", "org.jacoco:jacoco-maven-plugin:prepare-agent", "test",
                   "org.jacoco:jacoco-maven-plugin:report"]


def test_mutation_needs_junit5_plugin_declared(tmp_path):
    (tmp_path / "pom.xml").write_text("<project><dependencies></dependencies></project>")
    assert "pitest-junit5-plugin" in java.mutation_unavailable(tmp_path)
    (tmp_path / "pom.xml").write_text("<project><artifactId>pitest-junit5-plugin</artifactId></project>")
    assert java.mutation_unavailable(tmp_path) is None


def test_coverage_parse_absent_report_is_zero(tmp_path):
    cov = java.coverage_parse(tmp_path, tmp_path)
    assert (cov.covered, cov.total) == (0, 0)


def test_mutation_parse_absent_report_is_zero(tmp_path):
    m = java.mutation_parse(tmp_path, tmp_path)
    assert (m.killed, m.total) == (0, 0)


def test_lint_maps_main_target_to_test_dir(tmp_path, monkeypatch):
    captured = {}

    def fake_run(cmd, cwd):
        captured["cmd"] = cmd
        return SimpleNamespace(stdout='{"files": []}', returncode=0)

    monkeypatch.setattr(java, "run", fake_run)
    monkeypatch.setattr(java.shutil, "which", lambda tool: "/usr/bin/pmd")

    java.lint(tmp_path, "src/main/java/com/x", tmp_path)

    d = captured["cmd"][captured["cmd"].index("-d") + 1]
    assert d.endswith("src/test/java/com/x")


def test_lint_other_target_used_as_given(tmp_path, monkeypatch):
    captured = {}

    def fake_run(cmd, cwd):
        captured["cmd"] = cmd
        return SimpleNamespace(stdout='{"files": []}', returncode=0)

    monkeypatch.setattr(java, "run", fake_run)
    monkeypatch.setattr(java.shutil, "which", lambda tool: "/usr/bin/pmd")

    java.lint(tmp_path, "src/test/java/com/x", tmp_path)

    d = captured["cmd"][captured["cmd"].index("-d") + 1]
    assert d.endswith("src/test/java/com/x")


def test_mutation_unavailable_nested_gradle_build_file(tmp_path):
    nested = tmp_path / "backend"
    nested.mkdir()
    (nested / "build.gradle.kts").write_text('plugins { id("info.solidsoft.pitest") }')
    assert java.mutation_unavailable(tmp_path) is None


def test_mutation_unavailable_no_build_file_at_all(tmp_path):
    assert java.mutation_unavailable(tmp_path) == "no build.gradle found at or below the project root"


def test_missing_maven_reports_only_mvn_no_duplication(tmp_path, monkeypatch):
    (tmp_path / "pom.xml").write_text("<project/>")
    monkeypatch.setattr(java.shutil, "which", lambda tool: None if tool == "mvn" else "/usr/bin/" + tool)
    assert java.missing(tmp_path) == ["mvn"]
    assert java.missing(tmp_path) == ["mvn"]


def test_missing_gradle_with_wrapper_never_reports_gradle(tmp_path, monkeypatch):
    (tmp_path / "build.gradle.kts").write_text("")
    (tmp_path / "gradlew").write_text("")
    monkeypatch.setattr(java.shutil, "which", lambda tool: None)
    assert "gradle" not in java.missing(tmp_path)


# --- audit: OWASP dependency-check (fixtures/dependency_check_report.json, hand-built) ---

_FIX = pathlib.Path(__file__).parent / "fixtures"
_UNREADABLE = ["audit output not understood — see above"]


def test_audit_unavailable_reads_the_build_file(tmp_path):
    assert java.AUDIT_TOOL[0] == "dependency-check"
    (tmp_path / "pom.xml").write_text("<project/>")
    assert "dependency-check" in java.audit_unavailable(tmp_path)
    (tmp_path / "pom.xml").write_text("<artifactId>dependency-check-maven</artifactId>")
    assert java.audit_unavailable(tmp_path) is None
    (tmp_path / "pom.xml").unlink()
    (tmp_path / "build.gradle.kts").write_text('plugins { id("org.owasp.dependencycheck") version "13.0.0" }\n')
    assert "not applied" in java.audit_unavailable(tmp_path)      # plugin, but no JSON report asked for
    (tmp_path / "build.gradle.kts").write_text('plugins { id("org.owasp.dependencycheck") version "13.0.0" }\n'
                                               'dependencyCheck { formats = listOf("JSON") }\n')
    assert java.audit_unavailable(tmp_path) is None


def test_audit_cmd_runs_the_build_then_prints_the_report(tmp_path):
    (tmp_path / "pom.xml").write_text("")
    cmd = java.audit_cmd(tmp_path)
    assert cmd[:2] == ["sh", "-c"]
    # A build that fails before writing today's report must not leave last week's to be read
    assert cmd[2].startswith("rm -f target/dependency-check-report.json; ")
    assert "mvn -q org.owasp:dependency-check-maven:check -Dformat=JSON >target/dependency-check.log 2>&1" in cmd[2]
    assert cmd[2].endswith("cat target/dependency-check-report.json 2>/dev/null || cat target/dependency-check.log")
    (tmp_path / "pom.xml").unlink()
    (tmp_path / "build.gradle").write_text("")
    assert "gradle dependencyCheckAnalyze >build/reports/dependency-check.log" in java.audit_cmd(tmp_path)[2]
    (tmp_path / "gradlew").write_text("")
    assert "./gradlew dependencyCheckAnalyze" in java.audit_cmd(tmp_path)[2]


def test_audit_findings_from_report():
    lines = java.audit_findings((_FIX / "dependency_check_report.json").read_text(), 0)
    # commons-io's one CVE comes from two sources (NVD, OSSINDEX) — one line, not two
    assert lines == [
        "commons-io-2.6.jar: CVE-2021-29425 (MEDIUM) — fix not reported by dependency-check",
        "snakeyaml-1.30.jar: CVE-2022-1471 (HIGH) — fix not reported by dependency-check",
        "snakeyaml-1.30.jar: CVE-2022-25857 (HIGH) — fix not reported by dependency-check",
    ]


def test_audit_clean_and_unreadable():
    assert java.audit_findings('{"reportSchema": "1.1", "dependencies": [{"fileName": "a.jar"}]}', 0) == []
    assert java.audit_findings("[ERROR] Failed to execute goal", 1) == _UNREADABLE   # the log stood in
    assert java.audit_findings("cat: target/x: No such file", 1) == _UNREADABLE
    assert java.audit_findings('{"dependencies": [{"vulnerabilities": [{}]}]}', 0) == _UNREADABLE
    assert java.audit_findings("42", 0) == _UNREADABLE
