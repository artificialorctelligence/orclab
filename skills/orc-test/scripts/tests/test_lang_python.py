import json
import pathlib
import textwrap

from orc_test import langs, probe
from orc_test.langs import python as py

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_registered_first_and_mutation_needs_mutmut(tmp_path, monkeypatch):
    assert langs.ALL[0] is py and py.KEY == "python"
    monkeypatch.setattr(probe, "python_module", lambda name: False)
    assert py.mutation_unavailable(tmp_path) == "mutmut not installed — pip install mutmut"
    monkeypatch.setattr(probe, "python_module", lambda name: True)
    (tmp_path / "pyproject.toml").write_text("[tool.mutmut]\nsource_paths = ['pkg/']\n")
    assert py.mutation_unavailable(tmp_path) is None


def test_mutation_unavailable_names_the_missing_tool_mutmut_section(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "python_module", lambda name: True)
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    why = py.mutation_unavailable(tmp_path, "src")
    assert why.startswith(f"no [tool.mutmut] found in any pyproject.toml at or above {tmp_path / 'src'}")
    assert "source_paths" in why and "languages/python.md" in why


def test_commands_ignore_mutants_and_honour_target(tmp_path):
    (tmp_path / "src" / "x").mkdir(parents=True)
    (tmp_path / "src" / "x" / "test_x.py").write_text("")
    assert py.test_cmd(tmp_path, None) == ["python3", "-m", "pytest", "-q", "--ignore-glob=*mutants/*"]
    assert py.test_cmd(tmp_path, "src/x") == ["python3", "-m", "pytest", "-q", "--ignore-glob=*mutants/*", "src/x"]
    cmd = py.coverage_cmd(tmp_path, None, tmp_path / "out")
    assert "--ignore-glob=*mutants/*" in cmd and f"--cov-report=lcov:{tmp_path / 'out' / 'coverage.lcov'}" in cmd


def test_source_only_path_runs_the_whole_suite(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "calc.py").write_text("x = 1\n")
    assert py.test_cmd(tmp_path, "src") == ["python3", "-m", "pytest", "-q", "--ignore-glob=*mutants/*"]
    assert py.coverage_cmd(tmp_path, "src", tmp_path / "out")[5] == "--cov=src"   # still narrows what is measured
    (tmp_path / "src" / "calc_test.py").write_text("")
    assert py.test_cmd(tmp_path, "src")[-1] == "src"
    assert py.test_cmd(tmp_path, "src/calc_test.py")[-1] == "src/calc_test.py"


def test_coverage_parse_drops_test_files_from_the_denominator(tmp_path):
    (tmp_path / "coverage.lcov").write_text(
        "SF:src/calc.py\nDA:1,1\nDA:2,0\nend_of_record\n"
        "SF:tests/test_calc.py\nDA:1,1\nDA:2,1\nDA:3,1\nend_of_record\n"
        "SF:pkg/foo_test.py\nDA:1,1\nend_of_record\n"
        "SF:test_root.py\nDA:1,1\nend_of_record\n")
    cov = py.coverage_parse(tmp_path, tmp_path)
    assert cov.files == {"src/calc.py": (1, 2)} and (cov.covered, cov.total) == (1, 2)


def _meta(root, file, codes):
    meta = root / "mutants" / (file + ".meta")
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(json.dumps({"exit_code_by_key": codes}))


def test_coverage_cmd_names_every_dir_coverage_would_not_walk_into(tmp_path):
    """coverage.py lists a never-imported file only under a --cov dir reached through
    __init__.py-bearing dirs; a src/ without one hid every such file (BACKLOG #42)."""
    for f in ["src/pkg/__init__.py", "src/pkg/a.py", "src/gui/w.py", "src/gui/sub/__init__.py",
              "src/gui/sub/x.py", "tests/test_a.py", "venv/lib/y.py", "top.py"]:
        (tmp_path / f).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / f).write_text("")
    covs = [a for a in py.coverage_cmd(tmp_path, None, tmp_path / "out") if a.startswith("--cov=")]
    assert covs == ["--cov=.", "--cov=src", "--cov=src/gui", "--cov=tests"]
    covs = [a for a in py.coverage_cmd(tmp_path, "src", tmp_path / "out") if a.startswith("--cov=")]
    assert covs == ["--cov=src", "--cov=src/gui"]


def test_mutation_parse_reads_verdicts_from_mutmut_cache_and_diffs_survivors_in_one_go(monkeypatch, tmp_path):
    (tmp_path / "calc.py").write_text("x = 1\n\n\ndef clamp(x, lo, hi):\n    if x < lo:\n        return lo\n")
    _meta(tmp_path, "calc.py", {"calc.x_clamp__mutmut_1": 0, "calc.x_clamp__mutmut_2": 1,
                                "calc.x_clamp__mutmut_3": 0, "calc.x_other__mutmut_1": 33,
                                "calc.x_other__mutmut_2": 36, "calc.x_other__mutmut_3": 35,
                                "calc.x_other__mutmut_4": 34, "calc.x_other__mutmut_5": None})
    _meta(tmp_path, "gone.py", {"gone.x_f__mutmut_1": 0})     # stale cache: the file no longer exists
    asked = []
    diff = (FIX / "mutmut_show.txt").read_text()
    monkeypatch.setattr(py, "_diffs", lambda root, alive: asked.append(alive) or
                        {k: diff for k, _ in alive})
    m = py.mutation_parse(tmp_path, tmp_path)
    # killed + timeout count as killed; suspicious/skipped/"no tests"/not-checked don't count at all
    assert (m.killed, m.total) == (2, 4)
    assert asked == [[("calc.x_clamp__mutmut_1", "calc.py"), ("calc.x_clamp__mutmut_3", "calc.py")]]
    assert [s.file for s in m.survivors] == ["calc.py"] * 2
    assert m.survivors[0].line == 5                       # the file's line, not the function's
    assert "x <= lo" in m.survivors[0].description


def test_survivor_from_a_multi_line_removal_is_the_first_removed_line(tmp_path):
    # seen live on orc-todo: mutmut replaces a two-line string argument with None
    (tmp_path / "cli.py").write_text(textwrap.dedent("""\
        import sys


        def cmd_add():
            body = sys.stdin.read()
            if not body.strip():
                print(
                    "error: an entry needs a real paragraph of context, not a stub - that is what "
                    "makes it worth keeping. Pipe the body in on stdin.",
                    file=sys.stderr,
                )
        """))
    diff = textwrap.dedent("""\
        --- cli.py
        +++ cli.py
        @@ -2,8 +2,7 @@
             body = sys.stdin.read()
             if not body.strip():
                 print(
        -            "error: an entry needs a real paragraph of context, not a stub - that is what "
        -            "makes it worth keeping. Pipe the body in on stdin.",
        +            None,
                     file=sys.stderr,
        """)
    s = py._survivor(tmp_path, "cli.x_cmd_add__mutmut_3", "cli.py", diff)
    assert (s.file, s.line, s.description) == ("cli.py", 8, "None,")


def test_survivor_line_of_a_method_is_looked_up_inside_its_class(tmp_path):
    (tmp_path / "m.py").write_text(textwrap.dedent("""\
        def go():
            return 1


        class A:
            def go(self):
                return 1
        """))
    diff = "--- m.py\n+++ m.py\n@@ -1,2 +1,2 @@\n def go(self):\n-    return 1\n+    return 2\n"
    assert py._survivor(tmp_path, "m.xǁAǁgo__mutmut_1", "m.py", diff).line == 7
    assert py._survivor(tmp_path, "m.x_go__mutmut_1", "m.py", diff).line == 2
    assert py._survivor(tmp_path, "m.x_nope__mutmut_1", "m.py", diff).line == 0


def test_diffs_asks_one_process_for_every_survivor(monkeypatch, tmp_path):
    seen = []
    out = "# a.x_f__mutmut_1\n--- a.py\n-x\n+y\n# a.x_f__mutmut_2\n--- a.py\n-x\n+z\n"
    monkeypatch.setattr(py, "run", lambda cmd, cwd, input: seen.append((cmd, input)) or
                        type("R", (), {"stdout": out})())
    d = py._diffs(tmp_path, [("a.x_f__mutmut_1", "a.py"), ("a.x_f__mutmut_2", "a.py")])
    assert len(seen) == 1 and seen[0][0] == ["python3", "-c", py.MUTMUT_DIFFS.read_text()]
    assert seen[0][1] == "a.x_f__mutmut_1 a.py\na.x_f__mutmut_2 a.py\n"
    assert d == {"a.x_f__mutmut_1": "--- a.py\n-x\n+y", "a.x_f__mutmut_2": "--- a.py\n-x\n+z"}
    assert py._diffs(tmp_path, []) == {} and len(seen) == 1


def test_lint_finds_the_four_smells(tmp_path):
    t = tmp_path / "tests"
    t.mkdir()
    (t / "test_a.py").write_text(textwrap.dedent("""
        import time, pytest
        def test_nothing():
            x = 1
        def test_sleeps():
            time.sleep(1)
            assert True
        @pytest.mark.skip
        def test_skipped():
            assert True
        def test_dup():
            assert 1
        def test_dup():
            assert 2
        def test_raises_is_an_assertion():
            with pytest.raises(ValueError):
                int("x")
    """))
    msgs = sorted((f.line, f.message) for f in py.lint(tmp_path, None, tmp_path))
    assert msgs == [
        (3, "no assertion in test_nothing"),
        (6, "sleep in test_sleeps"),
        (8, "skipped: test_skipped"),
        (13, "duplicate test name test_dup"),
    ]


def test_lint_skips_venv_and_unparseable_files(tmp_path):
    (tmp_path / "venv" / "lib" / "x" / "tests").mkdir(parents=True)
    (tmp_path / "venv" / "lib" / "x" / "tests" / "test_y.py").write_text("def test_nothing():\n    x = 1\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_broken.py").write_text("def test_(:\n")
    (tmp_path / "tests" / "test_ok.py").write_text("def test_nothing():\n    x = 1\n")
    assert [f.file for f in py.lint(tmp_path, None, tmp_path)] == ["tests/test_ok.py"]


def test_lint_finds_star_test_py_too(tmp_path):
    t = tmp_path / "tests"
    t.mkdir()
    (t / "foo_test.py").write_text("def test_nothing():\n    x = 1\n")
    msgs = [(f.line, f.message) for f in py.lint(tmp_path, None, tmp_path)]
    assert msgs == [(1, "no assertion in test_nothing")]


def test_duplicate_name_is_scoped_per_class(tmp_path):
    t = tmp_path / "tests"
    t.mkdir()
    (t / "test_classes.py").write_text(textwrap.dedent("""
        class TestA:
            def test_run(self):
                assert True
        class TestB:
            def test_run(self):
                assert True
        def test_run():
            assert True
        def test_run():
            assert True
    """))
    msgs = [(f.line, f.message) for f in py.lint(tmp_path, None, tmp_path)]
    assert msgs == [(10, "duplicate test name test_run")]


def test_mutation_runs_where_the_nearest_tool_mutmut_config_is(tmp_path):
    sub = tmp_path / "skills" / "x" / "scripts"
    (sub / "pkg").mkdir(parents=True)
    (sub / "pyproject.toml").write_text("[tool.mutmut]\nsource_paths = ['pkg/']\n")
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    assert py.mutation_cwd(tmp_path, "skills/x/scripts/pkg") == sub
    assert py.mutation_cwd(tmp_path, "skills/x") == tmp_path
    assert py.mutation_cwd(tmp_path, None) == tmp_path


def test_mutation_cwd_ignores_a_commented_out_tool_mutmut_line(tmp_path):
    (tmp_path / "pyproject.toml").write_text("# [tool.mutmut]\n[tool.pytest.ini_options]\n")
    assert py.mutation_cwd(tmp_path, None) == tmp_path


def test_mutation_cwd_never_searches_above_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "pyproject.toml").write_text("[tool.mutmut]\nsource_paths = ['x/']\n")
    assert py.mutation_cwd(root, "../outside") == root


def test_mutation_cmd_drops_cached_verdicts_when_a_test_is_newer_than_them(tmp_path):
    """mutmut's cache hashes source functions only; a new test must force a full rerun or
    `generate`'s after-number is the before-number (BACKLOG #35)."""
    import os
    meta = tmp_path / "mutants" / "pkg" / "mod.py.meta"
    meta.parent.mkdir(parents=True)
    meta.write_text("{}")
    test = tmp_path / "tests" / "test_mod.py"
    test.parent.mkdir()
    test.write_text("def test_x(): pass\n")
    os.utime(test, (1_700_000_000, 1_700_000_000))     # tests older than the cache: keep it
    assert py.mutation_cmd(tmp_path, None, tmp_path) == ["python3", "-m", "mutmut", "run"]
    assert meta.exists()
    os.utime(meta, (1_600_000_000, 1_600_000_000))     # now the test is newer: verdicts go
    py.mutation_cmd(tmp_path, None, tmp_path)
    assert not meta.exists()


def test_audit_tool_and_command():
    assert py.AUDIT_TOOL == ("pip-audit", "pip install pip-audit")
    assert py.audit_cmd("/x") == ["python3", "-m", "pip_audit", "-f", "json", "--progress-spinner", "off", "."]


def test_audit_findings_from_captured_json():
    # 36 raw (dependency, vuln) records in the fixture, 18 distinct (name, version, id) triples —
    # pip-audit lists the same advisory id twice for one package when it comes from more than
    # one source; deduped, ✗ N is a count of distinct vulnerabilities, not of records.
    text = (FIX / "pip_audit.json").read_text()
    lines = py.audit_findings(text, 1)
    assert len(lines) == 18
    assert lines[0].startswith("requests 2.19.0: ") and " — fix " in lines[0]


def test_audit_findings_dedupes_the_same_id_for_the_same_package():
    data = ('{"dependencies": [{"name": "x", "version": "1", "vulns": ['
            '{"id": "CVE-1", "fix_versions": ["2"], "aliases": []},'
            '{"id": "CVE-1", "fix_versions": ["2"], "aliases": []}]}]}')
    assert py.audit_findings(data, 1) == ["x 1: CVE-1 — fix 2"]


def test_audit_clean_and_unreadable():
    assert py.audit_findings('{"dependencies": [], "fixes": []}', 0) == []
    assert py.audit_findings("Traceback (most recent call last)", 2) == ["audit output not understood — see above"]


def test_audit_findings_skips_pip_audits_stderr_summary():
    # runner.run merges stderr into stdout, and pip-audit always prints a one-line summary on
    # stderr before the JSON — both captured live 2026-09-19 with pip-audit 2.10.1: "No known
    # vulnerabilities found" on the v22check scaffold, "Found 36 known vulnerabilities in 3
    # packages" on a pyproject pinning requests==2.19.0 (a cachecontrol WARNING line came ahead
    # of it on a cold cache). Read as pure JSON, every real run was "not understood", a red gate.
    clean = 'No known vulnerabilities found\n{"dependencies": [{"name": "fastapi", "version": "0.141.1", "vulns": []}], "fixes": []}\n'
    assert py.audit_findings(clean, 0) == []
    vuln = ('WARNING:cachecontrol.controller:Cache entry deserialization failed, entry ignored\n'
            'Found 36 known vulnerabilities in 3 packages\n{"dependencies": [{"name": "x", "version": "1", "vulns": ['
            '{"id": "CVE-1", "fix_versions": ["2"], "aliases": []}]}], "fixes": []}\n')
    assert py.audit_findings(vuln, 1) == ["x 1: CVE-1 — fix 2"]
    # No JSON at all — pip-audit's own error line, as on a pyproject.toml with no [project] table.
    assert py.audit_findings("ERROR:pip_audit._cli:pyproject file pyproject.toml does not contain `project` section\n", 1) == [
        "audit output not understood — see above"]


def test_audit_findings_never_raises_on_valid_but_wrong_shaped_json():
    # Valid JSON, but not the shape pip-audit documents: must land on the sentinel, not crash
    # cmd_audit with a KeyError/TypeError/AttributeError.
    assert py.audit_findings('{"dependencies": [{"vulns": [{}]}]}', 1) == ["audit output not understood — see above"]
    assert py.audit_findings("42", 1) == ["audit output not understood — see above"]
    assert py.audit_findings('{"dependencies": [{"name": "x", "version": "1", "vulns": [1]}]}', 1) == [
        "audit output not understood — see above"]


def test_audit_nothing_is_a_pyproject_without_a_project_table(tmp_path):
    # Orclab's own shape (BACKLOG #54): pyproject.toml exists for tool config only, and pip-audit's
    # `.` form refuses it. Not red, not "install pip-audit" — nothing declared to audit.
    reason = "nothing declared: pyproject.toml has no [project] table"
    assert py.audit_nothing(tmp_path) == reason                           # no file at all
    (tmp_path / "pyproject.toml").write_text('[tool.ruff]\npreview = true\n')
    assert py.audit_nothing(tmp_path) == reason                           # tool-only
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0"\n')
    assert py.audit_nothing(tmp_path) is None                             # declares something


def test_audit_unavailable_names_pip_audit(monkeypatch):
    monkeypatch.setattr(probe, "python_module", lambda name: False)
    assert "pip-audit" in py.audit_unavailable("/x")
