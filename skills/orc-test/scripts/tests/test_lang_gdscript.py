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


def test_mutation_needs_gdmutant(tmp_path, monkeypatch):
    monkeypatch.setattr(gd.shutil, "which", lambda n: None)
    assert "pip install 'gdmutant==0.1.*'" in gd.mutation_unavailable(tmp_path)
    monkeypatch.setattr(gd.shutil, "which", lambda n: "/usr/bin/gdmutant")
    assert gd.mutation_unavailable(tmp_path) is None


def test_mutation_cmd_picks_the_runner_and_godot(tmp_path, monkeypatch):
    monkeypatch.setenv("GODOT_BIN", "/opt/godot")
    out = tmp_path / "out"
    cmd = gd.mutation_cmd(tmp_path, None, out)
    assert cmd[:3] == ["gdmutant", "run", "."]
    assert cmd[cmd.index("--json") + 1] == str(out / "mutation-report.json")
    assert cmd[cmd.index("--runner") + 1] == "gut" and "res://test/unit" in cmd     # no gdUnit4 addon
    assert cmd[cmd.index("--godot") + 1] == "/opt/godot"
    (tmp_path / "addons" / "gdUnit4").mkdir(parents=True)
    (tmp_path / "addons" / "gdUnit4" / "runtest.sh").write_text("")
    cmd = gd.mutation_cmd(tmp_path, "src", out)
    assert cmd[2] == "src" and cmd[cmd.index("--runner") + 1] == "gdunit4" and "--tests" not in cmd
    monkeypatch.delenv("GODOT_BIN")
    assert "--godot" not in gd.mutation_cmd(tmp_path, None, out)


def test_mutation_parse_reads_the_stryker_report_or_nothing(tmp_path):
    from orc_test.model import Mutation
    out = tmp_path / "out"
    assert gd.mutation_parse(tmp_path, out) == Mutation(0, 0)
    out.mkdir()
    (out / "mutation-report.json").write_text(
        '{"files": {"player.gd": {"mutants": [{"status": "Killed", "location": {"start": {"line": 1}}},'
        ' {"status": "Survived", "mutatorName": "Arith", "replacement": "-", "location": {"start": {"line": 4}}}]}}}')
    mut = gd.mutation_parse(tmp_path, out)
    assert (mut.killed, mut.total) == (1, 2)
    assert [(s.file, s.line) for s in mut.survivors] == [("player.gd", 4)]


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


def test_source_count_skips_addons(tmp_path):
    """gdmutant never mutates addons/; the 'mutating N files' line must not count them either."""
    from orc_test import cli
    (tmp_path / "addons" / "gdUnit4").mkdir(parents=True)
    (tmp_path / "addons" / "gdUnit4" / "x.gd").write_text("")
    (tmp_path / "player.gd").write_text("")
    assert cli._source_count(tmp_path, gd, None) == 1
