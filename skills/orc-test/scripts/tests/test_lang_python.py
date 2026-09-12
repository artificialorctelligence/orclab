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
    assert py.mutation_unavailable(tmp_path) is None


def test_commands_ignore_mutants_and_honour_target(tmp_path):
    assert py.test_cmd(tmp_path, None) == ["python3", "-m", "pytest", "-q", "--ignore=mutants"]
    assert py.test_cmd(tmp_path, "src/x") == ["python3", "-m", "pytest", "-q", "--ignore=mutants", "src/x"]
    cmd = py.coverage_cmd(tmp_path, None, tmp_path / "out")
    assert "--ignore=mutants" in cmd and f"--cov-report=lcov:{tmp_path / 'out' / 'coverage.lcov'}" in cmd


def test_mutation_parse_reads_results_and_diffs(monkeypatch, tmp_path):
    monkeypatch.setattr(py, "_results", lambda root: (FIX / "mutmut_results.txt").read_text())
    monkeypatch.setattr(py, "_show", lambda root, key: (FIX / "mutmut_show.txt").read_text())
    m = py.mutation_parse(tmp_path, tmp_path)
    # killed + timeout count as killed; suspicious/skipped/"no tests" don't count at all
    assert (m.killed, m.total) == (2, 4)
    assert [s.file for s in m.survivors] == ["src/calc/__init__.py"] * 2
    assert m.survivors[0].line == 2
    assert "x <= lo" in m.survivors[0].description


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
