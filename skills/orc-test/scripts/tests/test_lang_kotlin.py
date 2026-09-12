from orc_test import detect
from orc_test.langs import java, kotlin


def _gradle_kotlin(tmp_path):
    (tmp_path / "build.gradle.kts").write_text("plugins { kotlin(\"jvm\") }\n")
    (tmp_path / "src" / "main" / "kotlin").mkdir(parents=True)
    (tmp_path / "src" / "main" / "kotlin" / "A.kt").write_text("class A\n")
    return tmp_path


def test_source_ext():
    assert kotlin.SOURCE_EXT == ".kt"


def test_kotlin_claims_gradle_project_and_java_steps_aside(tmp_path):
    repo = _gradle_kotlin(tmp_path)
    assert kotlin.claims(repo)
    assert [m.KEY for m, _ in detect.languages(repo, [java, kotlin])] == ["kotlin"]


def test_kotlin_claims_multi_module_gradle_project(tmp_path):
    app = tmp_path / "app"
    (app / "src" / "main" / "kotlin").mkdir(parents=True)
    (app / "build.gradle.kts").write_text("plugins { kotlin(\"jvm\") }\n")
    (app / "src" / "main" / "kotlin" / "A.kt").write_text("class A\n")
    assert kotlin.claims(tmp_path)
    assert [(m.KEY, d) for m, d in detect.languages(tmp_path, [java, kotlin])] == [("kotlin", app)]


def test_coverage_is_kover(tmp_path):
    repo = _gradle_kotlin(tmp_path)
    assert kotlin.coverage_cmd(repo, None, tmp_path)[-2:] == ["test", "koverXmlReport"]


def test_arcmutate_caveat_needs_both_licence_and_plugin(tmp_path):
    repo = _gradle_kotlin(tmp_path)
    (repo / "build.gradle.kts").write_text("plugins { id(\"info.solidsoft.pitest\") }\n")
    assert kotlin.mutation_unavailable(repo) is None
    assert "approximate" in kotlin.CAVEATS_FOR(repo)[0] and "does not declare one" in kotlin.CAVEATS_FOR(repo)[0]
    (repo / "LICENSE").write_text("MIT License")
    caveat = kotlin.CAVEATS_FOR(repo)[0]     # licence but no plugin: approximate, and says how to fix it
    assert "approximate" in caveat and "MIT" in caveat and "add com.arcmutate:pitest-kotlin-plugin" in caveat
    (repo / "build.gradle.kts").write_text(
        "plugins { id(\"info.solidsoft.pitest\") }\n"
        "dependencies { pitest(\"com.arcmutate:pitest-kotlin-plugin:1.4.0\") }\n")
    caveat = kotlin.CAVEATS_FOR(repo)[0]
    assert "TCE via Pitest + Arcmutate" in caveat and "approximate" not in caveat


def test_missing_reports_gradle_only_without_the_wrapper(tmp_path, monkeypatch):
    repo = _gradle_kotlin(tmp_path)
    monkeypatch.setattr(kotlin.shutil, "which", lambda name: "/usr/bin/java" if name == "java" else None)
    assert kotlin.missing(repo) == ["gradle"]
    (repo / "gradlew").write_text("#!/bin/sh\n")
    assert kotlin.missing(repo) == []


def test_coverage_parse_absent_report_is_zero(tmp_path):
    cov = kotlin.coverage_parse(tmp_path, tmp_path)
    assert (cov.covered, cov.total) == (0, 0)


def test_mutation_parse_absent_report_is_zero(tmp_path):
    m = kotlin.mutation_parse(tmp_path, tmp_path)
    assert (m.killed, m.total) == (0, 0)


def test_mutation_unavailable_no_build_file_does_not_crash(tmp_path):
    assert kotlin.mutation_unavailable(tmp_path) == "no build.gradle found at or below the project root"


def test_mutation_unavailable_finds_nested_build_file(tmp_path):
    nested = tmp_path / "app"
    nested.mkdir()
    (nested / "build.gradle.kts").write_text("plugins { id(\"info.solidsoft.pitest\") }\n")
    assert kotlin.mutation_unavailable(tmp_path) is None
