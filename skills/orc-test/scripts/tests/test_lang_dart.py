import pathlib
import shutil

from orc_test.langs import dart
from orc_test.model import Coverage, Mutation

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_source_ext():
    assert dart.SOURCE_EXT == ".dart"


def test_flutter_vs_dart(tmp_path):
    (tmp_path / "pubspec.yaml").write_text("name: x\ndependencies:\n  flutter:\n    sdk: flutter\n")
    assert dart.test_cmd(tmp_path, None) == ["flutter", "test"]
    assert dart.coverage_cmd(tmp_path, None, tmp_path / "out")[:3] == ["flutter", "test", "--coverage"]
    (tmp_path / "pubspec.yaml").write_text("name: x\n")
    assert dart.test_cmd(tmp_path, "test/a_test.dart") == ["dart", "test", "test/a_test.dart"]


def test_coverage_parse_reads_lcov_the_tool_wrote(tmp_path):
    (tmp_path / "coverage").mkdir()
    (tmp_path / "coverage" / "lcov.info").write_text("SF:lib/a.dart\nDA:1,1\nDA:2,0\nend_of_record\n")
    assert dart.coverage_parse(tmp_path, tmp_path / "out").files == {"lib/a.dart": (1, 2)}


def test_coverage_parse_no_report(tmp_path):
    assert dart.coverage_parse(tmp_path, tmp_path / "out") == Coverage(0, 0)


def test_mutation_junit_parse():
    m = dart._parse_junit(FIX / "mutation_test_junit.xml")
    assert (m.killed, m.total) == (2, 3)
    assert (m.survivors[0].file, m.survivors[0].line) == ("lib/clamp.dart", 5)
    assert ">= " in m.survivors[0].description or "replaced" in m.survivors[0].description


def test_mutation_parse_no_report(tmp_path):
    assert dart.mutation_parse(tmp_path, tmp_path / "out") == Mutation(0, 0)


def test_mutation_needs_dev_dependency(tmp_path):
    (tmp_path / "pubspec.yaml").write_text("name: x\n")
    assert "dart pub add --dev mutation_test" in dart.mutation_unavailable(tmp_path)
    (tmp_path / "pubspec.yaml").write_text("name: x\ndev_dependencies:\n  mutation_test: ^1.8.0\n")
    assert dart.mutation_unavailable(tmp_path) is None


def test_missing_reports_dart(tmp_path, monkeypatch):
    (tmp_path / "pubspec.yaml").write_text("name: x\n")
    monkeypatch.setattr(dart.shutil, "which", lambda name: None)
    assert dart.missing(tmp_path) == ["dart"]
    monkeypatch.setattr(dart.shutil, "which", lambda name: "/usr/bin/dart")
    assert dart.missing(tmp_path) == []


def test_missing_reports_flutter(tmp_path, monkeypatch):
    (tmp_path / "pubspec.yaml").write_text("name: x\ndependencies:\n  flutter:\n    sdk: flutter\n")
    monkeypatch.setattr(dart.shutil, "which", lambda name: None)
    assert dart.missing(tmp_path) == ["flutter"]
    monkeypatch.setattr(dart.shutil, "which", lambda name: "/usr/bin/flutter")
    assert dart.missing(tmp_path) == []


def test_tools_covers_both_keys():
    assert set(dart.TOOLS) == {"dart", "flutter"}


def test_coverage_cmd_quotes_target(tmp_path):
    (tmp_path / "pubspec.yaml").write_text("name: x\n")
    cmd = dart.coverage_cmd(tmp_path, "test/a b_test.dart", tmp_path / "out")
    assert "'test/a b_test.dart'" in cmd[-1]
