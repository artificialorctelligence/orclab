import pathlib
import textwrap

from orc_test import langs
from orc_test.langs import python as py

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_registered_first_and_mutation_needs_mutmut(tmp_path, monkeypatch):
    assert langs.ALL[0] is py and py.KEY == "python"
    monkeypatch.setattr(py.importlib.util, "find_spec", lambda name: None)
    assert py.mutation_unavailable(tmp_path) == "mutmut not installed — pip install mutmut"
    monkeypatch.setattr(py.importlib.util, "find_spec", lambda name: object())
    (tmp_path / "pyproject.toml").write_text("[tool.mutmut]\nsource_paths = ['pkg/']\n")
    assert py.mutation_unavailable(tmp_path) is None


def test_mutation_unavailable_names_the_missing_tool_mutmut_section(tmp_path, monkeypatch):
    monkeypatch.setattr(py.importlib.util, "find_spec", lambda name: object())
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


def test_mutation_parse_reads_results_and_diffs(monkeypatch, tmp_path):
    monkeypatch.setattr(py, "_results", lambda root: (FIX / "mutmut_results.txt").read_text())
    monkeypatch.setattr(py, "_show", lambda root, key: (FIX / "mutmut_show.txt").read_text())
    m = py.mutation_parse(tmp_path, tmp_path)
    # killed + timeout count as killed; suspicious/skipped/"no tests" don't count at all
    assert (m.killed, m.total) == (2, 4)
    assert [s.file for s in m.survivors] == ["src/calc/__init__.py"] * 2
    assert m.survivors[0].line == 2
    assert "x <= lo" in m.survivors[0].description


def test_survivor_from_a_multi_line_removal_is_the_first_removed_line(monkeypatch, tmp_path):
    # seen live on orc-todo: mutmut replaces a two-line string argument with None
    diff = textwrap.dedent("""\
        # orc_todo.cli.x_cmd_add__mutmut_3: survived
        --- orc_todo/cli.py
        +++ orc_todo/cli.py
        @@ -2,8 +2,7 @@
             body = sys.stdin.read()
             if not body.strip():
                 print(
        -            "error: an entry needs a real paragraph of context, not a stub - that is what "
        -            "makes it worth keeping. Pipe the body in on stdin.",
        +            None,
                     file=sys.stderr,
        """)
    monkeypatch.setattr(py, "_show", lambda root, key: diff)
    s = py._survivor(tmp_path, "orc_todo.cli.x_cmd_add__mutmut_3")
    assert (s.file, s.line, s.description) == ("orc_todo/cli.py", 5, "None,")


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


def test_results_asks_mutmut_for_every_mutant_not_just_the_unkilled(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(py, "run", lambda cmd, cwd: seen.append(cmd) or type("R", (), {"stdout": ""})())
    py._results(tmp_path)
    assert seen == [["python3", "-m", "mutmut", "results", "--all", "true"]]
