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
