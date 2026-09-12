import json
import pathlib

from orc_test import detect
from orc_test.langs import swift
from orc_test.model import Coverage, Mutation

FIX = pathlib.Path(__file__).parent / "fixtures"


def _make_xcodeproj(root, *parts):
    """Create root/<parts.../>Name.xcodeproj/project.pbxproj and return the bundle dir."""
    proj = pathlib.Path(root).joinpath(*parts)
    proj.mkdir(parents=True)
    (proj / "project.pbxproj").write_text("")
    return proj


def test_source_ext():
    assert swift.SOURCE_EXT == ".swift"


def test_spm_vs_xcodeproj(tmp_path):
    (tmp_path / "Package.swift").write_text("")
    assert swift.test_cmd(tmp_path, None) == ["swift", "test"]
    assert swift.coverage_cmd(tmp_path, None, tmp_path)[:3] == ["swift", "test", "--enable-code-coverage"]
    (tmp_path / "Package.swift").unlink()
    _make_xcodeproj(tmp_path, "App.xcodeproj")
    cmd = swift.test_cmd(tmp_path, None)
    assert cmd[:2] == ["xcodebuild", "test"] and "-scheme" in cmd and "App" in cmd


def test_xccov_parse_relativises_paths(tmp_path):
    (tmp_path / "xccov.json").write_text((FIX / "xccov.json").read_text())
    cov = swift._parse_xccov(tmp_path / "xccov.json", root="/Users/x/App")
    assert cov.files == {"Sources/App/Clamp.swift": (4, 6), "Sources/App/Other.swift": (3, 4)}
    assert (cov.covered, cov.total) == (7, 10)


def test_llvmcov_parse_relativises_paths(tmp_path):
    (tmp_path / "llvmcov.json").write_text((FIX / "llvmcov.json").read_text())
    cov = swift._parse_xccov(tmp_path / "llvmcov.json", root="/Users/x/App")
    assert cov.files == {"Sources/App/Clamp.swift": (4, 6), "Sources/App/Other.swift": (3, 4)}
    assert (cov.covered, cov.total) == (7, 10)


def test_coverage_parse_no_report(tmp_path):
    assert swift.coverage_parse(tmp_path, tmp_path / "out") == Coverage(0, 0)


def test_muter_parse_uses_file_level_numbers():
    m = swift._parse_muter(FIX / "muter.json")
    assert (m.killed, m.total) == (5, 8)
    assert [(s.file, s.line) for s in m.survivors] == [("Clamp.swift", 0), ("Other.swift", 0)]
    assert "50%" in m.survivors[0].description


def test_mutation_parse_no_report(tmp_path):
    assert swift.mutation_parse(tmp_path, tmp_path / "out") == Mutation(0, 0)


def test_needs_mac(tmp_path, monkeypatch):
    monkeypatch.setattr(swift.platform, "system", lambda: "Linux")
    _make_xcodeproj(tmp_path, "App.xcodeproj")
    assert swift.missing(tmp_path) == ["xcodebuild"]
    assert swift.TOOLS["xcodebuild"]  # KeyError here is the bug cli.py hits


def test_xcodeproj_marker_matches_nested_bundle(tmp_path):
    """*.xcodeproj is a directory; detect._candidates only yields files — the marker must be
    the file inside the bundle, and it must be found through nesting too."""
    _make_xcodeproj(tmp_path, "App", "App.xcodeproj")
    found = detect.languages(tmp_path, [swift])
    assert found == [swift]
    cmd = swift.test_cmd(tmp_path, None)
    assert cmd[cmd.index("-project") + 1] == "App/App.xcodeproj"


def test_lint_filters_by_path_component(tmp_path, monkeypatch):
    monkeypatch.setattr(swift.shutil, "which", lambda name: "/usr/bin/swiftlint")
    findings = [
        {"file": "/x/Tests/AppTests.swift", "line": 5, "rule_id": "force_cast", "reason": "avoid force casts"},
        {"file": "/x/Sources/App/Clamp.swift", "line": 10, "rule_id": "force_cast", "reason": "avoid force casts"},
        {"file": "/x/Sources/App/UITestHelper.swift", "line": 1, "rule_id": "line_length", "reason": "too long"},
    ]
    monkeypatch.setattr(swift, "run", lambda cmd, cwd: type("R", (), {"stdout": json.dumps(findings), "returncode": 0})())
    result = swift.lint("/x", None, tmp_path)
    assert [f.file for f in result] == ["Tests/AppTests.swift"]
