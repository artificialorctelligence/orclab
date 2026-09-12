from orc_test.langs import gdscript as gd


def test_source_ext():
    assert gd.SOURCE_EXT == ".gd"


def test_gdunit4_runner_and_godot_bin(tmp_path, monkeypatch):
    (tmp_path / "project.godot").write_text("")
    (tmp_path / "addons" / "gdUnit4").mkdir(parents=True)
    (tmp_path / "addons" / "gdUnit4" / "runtest.sh").write_text("")
    monkeypatch.setenv("GODOT_BIN", "/opt/godot")
    assert gd.test_cmd(tmp_path, None) == ["./addons/gdUnit4/runtest.sh", "-a", "test"]
    assert gd.test_cmd(tmp_path, "test/player") == ["./addons/gdUnit4/runtest.sh", "-a", "test/player"]
    assert gd.missing(tmp_path) == []
    monkeypatch.delenv("GODOT_BIN")
    assert gd.missing(tmp_path) == ["GODOT_BIN"]


def test_no_gdunit4_is_a_missing_tool(tmp_path, monkeypatch):
    (tmp_path / "project.godot").write_text("")
    monkeypatch.setenv("GODOT_BIN", "/opt/godot")
    assert gd.missing(tmp_path) == ["gdUnit4"]


def test_mutation_is_never_available(tmp_path):
    assert "no mutation tool exists for GDScript" in gd.mutation_unavailable(tmp_path)


def test_coverage_needs_nano_coverage_and_reads_its_lcov(tmp_path):
    (tmp_path / "project.godot").write_text("")
    assert "nano-coverage" in gd.coverage_unavailable(tmp_path)
    (tmp_path / "addons" / "nano_coverage").mkdir(parents=True)
    assert gd.coverage_unavailable(tmp_path) is None
    (tmp_path / "lcov.info").write_text("SF:res://player.gd\nDA:1,1\nDA:2,0\nend_of_record\n")
    assert gd.coverage_parse(tmp_path, tmp_path).files == {"res://player.gd": (1, 2)}


def test_coverage_parse_no_report(tmp_path):
    """Absent-report guard: no lcov.info at the root means nothing measured, not an error."""
    from orc_test.model import Coverage
    assert gd.coverage_parse(tmp_path, tmp_path) == Coverage(0, 0)


def test_gdlint_parse(tmp_path, monkeypatch):
    out = "test/test_player.gd:12: Error: Function name 'testJump' is not valid (function-name)\n"
    monkeypatch.setattr(gd, "run", lambda cmd, cwd: type("R", (), {"stdout": out, "returncode": 1})())
    monkeypatch.setattr(gd.shutil, "which", lambda n: "/usr/bin/gdlint")
    assert [(f.file, f.line) for f in gd.lint(tmp_path, None, tmp_path)] == [("test/test_player.gd", 12)]
