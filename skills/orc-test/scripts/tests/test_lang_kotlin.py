from orc_test import detect, langs
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
    assert [m.KEY for m in detect.languages(repo, [java, kotlin])] == ["kotlin"]


def test_coverage_is_kover(tmp_path):
    repo = _gradle_kotlin(tmp_path)
    assert kotlin.coverage_cmd(repo, None, tmp_path)[-2:] == ["test", "koverXmlReport"]


def test_arcmutate_only_with_open_source_licence(tmp_path):
    repo = _gradle_kotlin(tmp_path)
    (repo / "build.gradle.kts").write_text("plugins { id(\"info.solidsoft.pitest\") }\n")
    assert kotlin.mutation_unavailable(repo) is None
    assert "approximate" in kotlin.CAVEATS_FOR(repo)[0]
    (repo / "LICENSE").write_text("MIT License")
    assert "Arcmutate" in kotlin.CAVEATS_FOR(repo)[0] and "approximate" not in kotlin.CAVEATS_FOR(repo)[0]


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
