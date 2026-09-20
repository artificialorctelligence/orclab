import pathlib

from orc_test import probe
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
    monkeypatch.setattr(probe, "which", lambda name: False)
    assert dart.missing(tmp_path) == ["dart"]
    monkeypatch.setattr(probe, "which", lambda name: True)
    assert dart.missing(tmp_path) == []


def test_missing_reports_flutter(tmp_path, monkeypatch):
    (tmp_path / "pubspec.yaml").write_text("name: x\ndependencies:\n  flutter:\n    sdk: flutter\n")
    monkeypatch.setattr(probe, "which", lambda name: False)
    assert dart.missing(tmp_path) == ["flutter"]
    monkeypatch.setattr(probe, "which", lambda name: True)
    assert dart.missing(tmp_path) == []


def test_tools_covers_both_keys():
    assert set(dart.TOOLS) == {"dart", "flutter"}


def test_coverage_cmd_quotes_target(tmp_path):
    (tmp_path / "pubspec.yaml").write_text("name: x\n")
    cmd = dart.coverage_cmd(tmp_path, "test/a b_test.dart", tmp_path / "out")
    assert "'test/a b_test.dart'" in cmd[-1]


# --- audit: dart pub outdated --json (fixtures/pub_outdated.json, captured) ---

_UNREADABLE = ["audit output not understood — see above"]


def test_audit_tool_and_command(tmp_path, monkeypatch):
    assert dart.AUDIT_TOOL[0] == "dart pub outdated"
    (tmp_path / "pubspec.yaml").write_text("name: x\n")
    assert dart.audit_cmd(tmp_path) == ["dart", "pub", "outdated", "--json"]
    (tmp_path / "pubspec.yaml").write_text("name: x\ndependencies:\n  flutter:\n    sdk: flutter\n")
    assert dart.audit_cmd(tmp_path) == ["flutter", "pub", "outdated", "--json"]
    monkeypatch.setattr(probe, "which", lambda tool: False)
    assert "flutter" in dart.audit_unavailable(tmp_path)
    monkeypatch.setattr(probe, "which", lambda tool: True)
    assert dart.audit_unavailable(tmp_path) is None


def test_audit_findings_from_captured_json():
    # pub exited 0 with the advisory; only http is flagged, the two transitive rows have
    # current: null and must not trip the parser.
    lines = dart.audit_findings((FIX / "pub_outdated.json").read_text(), 0)
    assert lines == ["http 0.13.0: security advisory (dart pub get prints the URL) — fix not reported by pub (latest 1.6.0)"]


def test_audit_findings_skips_stderr_prefix():
    # runner.run merges stderr into stdout; a one-line prefix ahead of the JSON must not crash
    # json.loads — read from the first `{`, the way python.py and csharp.py do.
    prefixed = "Resolving dependencies...\n" + (FIX / "pub_outdated.json").read_text()
    assert dart.audit_findings(prefixed, 0) == dart.audit_findings((FIX / "pub_outdated.json").read_text(), 0)


def test_audit_clean_and_unreadable():
    assert dart.audit_findings('{"packages": []}', 0) == []
    assert dart.audit_findings('{"packages": [{"package": "a", "isCurrentAffectedByAdvisory": true, "current": null, "latest": null}]}', 0) == [
        "a ?: security advisory (dart pub get prints the URL) — fix not reported by pub (latest unknown)"]
    assert dart.audit_findings("Resolving dependencies...\nBecause x depends on y", 1) == _UNREADABLE
    assert dart.audit_findings('{"packages": [{}]}', 0) == _UNREADABLE
    assert dart.audit_findings("42", 0) == _UNREADABLE
