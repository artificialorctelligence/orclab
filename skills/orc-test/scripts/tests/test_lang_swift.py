import pathlib

from orc_test.langs import swift
from orc_test.model import Coverage, Mutation

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_source_ext():
    assert swift.SOURCE_EXT == ".swift"


def test_spm_vs_xcodeproj(tmp_path):
    (tmp_path / "Package.swift").write_text("")
    assert swift.test_cmd(tmp_path, None) == ["swift", "test"]
    assert swift.coverage_cmd(tmp_path, None, tmp_path)[:3] == ["swift", "test", "--enable-code-coverage"]
    (tmp_path / "Package.swift").unlink()
    (tmp_path / "App.xcodeproj").mkdir()
    cmd = swift.test_cmd(tmp_path, None)
    assert cmd[:2] == ["xcodebuild", "test"] and "-scheme" in cmd and "App" in cmd


def test_xccov_parse_relativises_paths(tmp_path):
    (tmp_path / "xccov.json").write_text((FIX / "xccov.json").read_text())
    cov = swift._parse_xccov(tmp_path / "xccov.json", root="/Users/x/App")
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
    (tmp_path / "App.xcodeproj").mkdir()
    assert swift.missing(tmp_path) == ["xcodebuild"]
