import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import types

import pytest
from lint_on_write import OFF, main

# The real script, for the one test that runs it as a process: under /orc-test analyze this
# file runs from mutmut's mutants/ copy, whose scripts are rewritten and not runnable alone.
_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent
HOOK = str((_SCRIPTS.parent if _SCRIPTS.name == "mutants" else _SCRIPTS) / "lint_on_write.py")


def fake_tool(bin_dir, name, exit_code, output):
    """A stand-in linter on PATH that prints `output` and exits `exit_code`."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    p = bin_dir / name
    p.write_text(f"#!/bin/sh\ncat <<'ORC'\n{output}\nORC\nexit {exit_code}\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return bin_dir


@pytest.fixture
def run(run_hook, monkeypatch):
    """run(file_path, tool_name="Write", bin_dir=None, env_extra=None) -> an object with the
    hook's returncode, stdout and stderr, the shape subprocess.run used to give these tests."""
    monkeypatch.delenv(OFF, raising=False)
    path = os.environ["PATH"]

    def write(file_path, tool_name="Write", bin_dir=None, env_extra=None):
        monkeypatch.setenv("PATH", f"{bin_dir}:{path}" if bin_dir is not None else path)
        for k, v in (env_extra or {}).items():
            monkeypatch.setenv(k, v)
        code, out, err = run_hook(main, {"tool_name": tool_name, "tool_input": {"file_path": str(file_path)}})
        monkeypatch.delenv(OFF, raising=False)
        return types.SimpleNamespace(returncode=code, stdout=out, stderr=err)
    return write


def project(tmp_path, config_name, config_text=""):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / config_name).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / config_name).write_text(config_text)
    src = tmp_path / "src"
    src.mkdir()
    return src


def test_findings_reach_claude_as_exit_2_on_stderr(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\nline-length = 100\n")
    f = src / "app.py"
    f.write_text("try:\n    x = 1\nexcept:\n    pass\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "ruff", 1, "src/app.py:3:1: E722 Do not use bare `except`"))
    assert out.returncode == 2
    assert "E722" in out.stderr and "ruff check" in out.stderr and "lint_on_write" in out.stderr
    assert out.stdout == ""


def test_a_clean_file_says_nothing(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    f = src / "ok.py"
    f.write_text("x = 1\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "ruff", 0, "All checks passed!"))
    assert (out.returncode, out.stdout, out.stderr) == (0, "", "")


def test_no_config_means_no_run_even_with_the_tool_installed(tmp_path, run):
    """The hook runs the project's configured linter, never its own opinion."""
    src = project(tmp_path, "pyproject.toml", "[project]\nname = 'x'\n")   # no [tool.ruff]
    f = src / "app.py"
    f.write_text("except: pass\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "ruff", 1, "would have complained"))
    assert (out.returncode, out.stderr) == (0, "")


def test_config_is_found_between_the_file_and_the_git_root(tmp_path, run):
    """A sub-project's own pyproject (skills/x/scripts/pyproject.toml) wins over none at the root."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    sub = tmp_path / "skills" / "x" / "scripts"
    sub.mkdir(parents=True)
    (sub / "pyproject.toml").write_text("[tool.ruff]\n")
    f = sub / "pkg.py"
    f.write_text("x = 1\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "ruff", 1, "F401 unused import"))
    assert out.returncode == 2 and "F401" in out.stderr


def test_a_pyproject_without_tool_ruff_does_not_stop_the_search(tmp_path, run):
    """ruff's own discovery skips such a file; Orclab's orc-todo pyproject is mutmut-only."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n")
    sub = tmp_path / "skills" / "x" / "scripts"
    sub.mkdir(parents=True)
    (sub / "pyproject.toml").write_text("[tool.mutmut]\n")
    f = sub / "pkg.py"
    f.write_text("x = 1\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "ruff", 1, "PLR1702 too many nested blocks"))
    assert out.returncode == 2 and "PLR1702" in out.stderr


def test_javascript_prefers_the_projects_own_node_modules_binary(tmp_path, run):
    src = project(tmp_path, ".oxlintrc.json", "{}")
    f = src / "a.ts"
    f.write_text("if (a) { if (b) { if (c) {} } }\n")
    fake_tool(tmp_path / "node_modules" / ".bin", "oxlint", 1, "max-depth: Blocks are nested too deeply (3)")
    out = run(f)                                   # nothing on PATH; node_modules/.bin must be used
    assert out.returncode == 2 and "max-depth" in out.stderr


def test_php_prefers_the_projects_own_vendor_bin_phpstan(tmp_path, run):
    src = project(tmp_path, "phpstan.neon", "parameters:\n  level: max\n")
    f = src / "Greeting.php"
    f.write_text("<?php\n$x = $undefined;\n")
    fake_tool(tmp_path / "vendor" / "bin", "phpstan", 1, "Greeting.php:2:Undefined variable: $undefined")
    out = run(f)                                   # nothing on PATH; vendor/bin must be used
    assert out.returncode == 2 and "Undefined variable" in out.stderr


def test_php_without_phpstan_neon_is_not_linted(tmp_path, run):
    src = project(tmp_path, "composer.json", "{}")
    f = src / "a.php"
    f.write_text("<?php\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "phpstan", 1, "should not run"))
    assert out.returncode == 0 and out.stderr == ""


def test_phpstan_neon_dist_configures_php_when_phpstan_neon_does_not(tmp_path, run):
    """PHPStan's own lookup order (phpstan.org/config-reference): phpstan.neon, then
    phpstan.neon.dist, then phpstan.dist.neon - a project shipping only the .dist file must
    still be linted."""
    src = project(tmp_path, "phpstan.neon.dist", "parameters:\n  level: max\n")
    f = src / "a.php"
    f.write_text("<?php\n")
    fake_tool(tmp_path / "vendor" / "bin", "phpstan", 1, "Undefined variable: $x")
    out = run(f)                                   # nothing on PATH; vendor/bin must be used
    assert out.returncode == 2 and "Undefined variable" in out.stderr


def test_eslint_config_is_the_fallback_when_there_is_no_oxlint_config(tmp_path, run):
    src = project(tmp_path, "eslint.config.js", "export default [];\n")
    f = src / "a.tsx"
    f.write_text("x\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "eslint", 1, "no-empty: Empty block statement"))
    assert out.returncode == 2 and "no-empty" in out.stderr


def test_unlinted_languages_and_other_tools_are_ignored(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    cs = src / "a.cs"
    cs.write_text("class A {}\n")
    assert run(cs, bin_dir=fake_tool(tmp_path / "bin", "ruff", 1, "no")).returncode == 0
    py = src / "a.py"
    py.write_text("x\n")
    assert run(py, tool_name="Bash", bin_dir=tmp_path / "bin").returncode == 0
    assert run(py, bin_dir=tmp_path / "bin", env_extra={"ORCLAB_LINT_ON_WRITE_OFF": "1"}).returncode == 0
    assert run(tmp_path / "missing.py", bin_dir=tmp_path / "bin").returncode == 0


def test_a_long_report_is_truncated_not_dropped(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    f = src / "a.py"
    f.write_text("x\n")
    many = "\\n".join(f"line {i}" for i in range(60))
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    p = bin_dir / "ruff"
    p.write_text(f"#!/bin/sh\nprintf '{many}\\n'\nexit 1\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    out = run(f, bin_dir=bin_dir)
    assert out.returncode == 2 and "line 39" in out.stderr and "line 40" not in out.stderr
    assert "20 more lines" in out.stderr


# --- from the first mutation run (2026-09-15): the survivors that were real gaps ----------------

def test_edit_and_multiedit_are_writes_too(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    f = src / "a.py"
    f.write_text("x\n")
    bin_dir = fake_tool(tmp_path / "bin", "ruff", 1, "E722 bare except")
    for tool in ("Edit", "MultiEdit"):
        assert run(f, tool_name=tool, bin_dir=bin_dir).returncode == 2, tool


def test_ruff_toml_configures_python_when_pyproject_does_not(tmp_path, run):
    src = project(tmp_path, "ruff.toml", "line-length = 100\n")
    f = src / "a.py"
    f.write_text("x\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "ruff", 1, "E501 line too long"))
    assert out.returncode == 2 and "E501" in out.stderr


def test_the_config_search_stops_at_the_git_root(tmp_path, run):
    """A pyproject in a parent directory above the project is someone else's configuration."""
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n")
    inner = tmp_path / "project"
    inner.mkdir()
    subprocess.run(["git", "init", "-q", str(inner)], check=True)
    f = inner / "a.py"
    f.write_text("x\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "ruff", 1, "would have complained"))
    assert (out.returncode, out.stderr) == (0, "")


def test_the_linter_runs_from_the_config_directory_with_the_absolute_path(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    f = src / "a.py"
    f.write_text("x\n")
    # The fake prints its own cwd and argv, so the report shows where and how it was run.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    ruff = bin_dir / "ruff"
    ruff.write_text('#!/bin/sh\necho "cwd=$(pwd) argv=$*"\nexit 1\n')
    ruff.chmod(ruff.stat().st_mode | stat.S_IEXEC)
    out = run(f, bin_dir=bin_dir)
    assert f"cwd={tmp_path.resolve()} argv=check --no-fix {f.resolve()}" in out.stderr


def test_javascript_extensions_all_reach_the_js_linter(tmp_path, run):
    src = project(tmp_path, ".oxlintrc.json", "{}")
    bin_dir = fake_tool(tmp_path / "bin", "oxlint", 1, "no-unused-vars")
    for name in ("a.js", "b.jsx", "c.ts", "d.tsx"):
        f = src / name
        f.write_text("x\n")
        assert run(f, bin_dir=bin_dir).returncode == 2, name


def test_exactly_the_line_limit_is_shown_whole(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    f = src / "a.py"
    f.write_text("x\n")
    forty = "\\n".join(f"line {i}" for i in range(40))
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    p = bin_dir / "ruff"
    p.write_text(f"#!/bin/sh\nprintf '{forty}\\n'\nexit 1\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    out = run(f, bin_dir=bin_dir)
    assert "line 39" in out.stderr and "more lines" not in out.stderr


def test_a_linter_that_hangs_is_cut_off_and_the_write_goes_through(tmp_path, run, monkeypatch):
    import lint_on_write
    monkeypatch.setattr(lint_on_write, "TIMEOUT", 0.2)
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    f = src / "a.py"
    f.write_text("x\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    p = bin_dir / "ruff"
    p.write_text("#!/bin/sh\nsleep 5\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    assert run(f, bin_dir=bin_dir).returncode == 0


# --- v23: a containerised project lints through compose run -----------------------------------

COMPOSE = "services:\n  orclab:\n    build: .\n"


def test_containerised_project_lints_through_compose_run(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    f = src / "a.py"
    f.write_text("x = 1\n")
    bin_dir = tmp_path / "dockerbin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text('#!/bin/sh\necho "argv: $*"\nexit 1\n')
    docker.chmod(docker.stat().st_mode | stat.S_IEXEC)
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text("runner: docker\n")   # not the real podman this machine has
    r = run(f, bin_dir=bin_dir)
    assert r.returncode == 2
    assert f"argv: compose run --rm -T --workdir {tmp_path} orclab ruff check --no-fix" in r.stderr
    assert "`ruff check`" in r.stderr    # the header names the linter, never the engine prefix


def test_container_false_in_test_yaml_lints_on_the_host(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text("container: false\n")
    f = src / "a.py"
    f.write_text("x = 1\n")
    bin_dir = fake_tool(tmp_path / "bin", "ruff", 1, "src/a.py:1:1: E999 fake finding")
    r = run(f, bin_dir=bin_dir)
    assert r.returncode == 2 and "compose run" not in r.stderr


def test_container_false_with_yaml_boolean_spelling_and_a_comment_lints_on_the_host(tmp_path, run):
    """`False` (YAML's capitalised spelling of false) and a trailing comment - both of which the
    real `yaml.safe_load` in config.py accepts - must not be missed by the hand-rolled scan."""
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text("container: False  # note\n")
    f = src / "a.py"
    f.write_text("x = 1\n")
    bin_dir = fake_tool(tmp_path / "bin", "ruff", 1, "src/a.py:1:1: E999 fake finding")
    r = run(f, bin_dir=bin_dir)
    assert r.returncode == 2 and "compose run" not in r.stderr


def test_runner_with_a_comment_is_honored_over_the_default_order(tmp_path, run):
    """`runner: docker  # note` must win even with `podman` also on PATH - a missed comment strip
    would silently fall back to the default RUNNERS order (podman first), the opposite of what
    the user wrote."""
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text("runner: docker  # note\n")
    f = src / "a.py"
    f.write_text("x = 1\n")
    bin_dir = tmp_path / "enginebin"
    bin_dir.mkdir()
    for name in ("docker", "podman"):
        engine = bin_dir / name
        engine.write_text('#!/bin/sh\necho "argv: $*"\nexit 1\n')
        engine.chmod(engine.stat().st_mode | stat.S_IEXEC)
    r = run(f, bin_dir=bin_dir)
    assert r.returncode == 2
    assert f"compose run --rm -T --workdir {tmp_path} orclab ruff check --no-fix" in r.stderr
    assert "podman compose" not in r.stderr


def test_the_engine_sees_pwd_as_the_git_root(tmp_path, run):
    """compose.yaml's `${PWD}` is read from the environment; `cwd=` alone leaves the session's
    PWD in place, which is wherever Claude's shell sits, not necessarily this project."""
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    f = src / "a.py"
    f.write_text("x = 1\n")
    bin_dir = tmp_path / "enginebin"
    bin_dir.mkdir()
    engine = bin_dir / "podman"      # python, not sh: a shell rewrites PWD to its real cwd on start
    engine.write_text('#!/usr/bin/env python3\nimport os\nprint("pwd:", os.environ.get("PWD"))\nraise SystemExit(1)\n')
    engine.chmod(engine.stat().st_mode | stat.S_IEXEC)
    r = run(f, bin_dir=bin_dir, env_extra={"PWD": "/somewhere/else"})
    assert r.returncode == 2 and f"pwd: {tmp_path}" in r.stderr


def test_a_file_outside_any_git_repo_lints_on_the_host_as_before(tmp_path, run):
    """No git root rules out being containerised outright (the record can only ever live at a
    git root), so this is the plain host case - pre-v23 behaviour, unchanged."""
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "pyproject.toml").write_text("[tool.ruff]\n")
    f = proj / "a.py"
    f.write_text("x = 1\n")
    bin_dir = fake_tool(tmp_path / "bin", "ruff", 1, "src/a.py:1:1: E999 fake finding")
    r = run(f, bin_dir=bin_dir)
    assert r.returncode == 2
    assert "E999 fake finding" in r.stderr
    assert "compose run" not in r.stderr


def test_containerised_project_with_no_engine_says_nothing(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    f = src / "a.py"
    f.write_text("x = 1\n")
    # ruff and git on the host and nothing else: no engine, whatever this machine has (it has
    # podman since 2026-09-20, and the real PATH would have found it)
    bin_dir = fake_tool(tmp_path / "bin", "ruff", 1, "finding")
    (bin_dir / "git").symlink_to(shutil.which("git"))
    r = run(f, env_extra={"PATH": str(bin_dir)})
    assert r.returncode == 0    # fail open - the hook never runs a containerised project's linter on the host


def test_an_unrecognised_runner_value_lints_nothing(tmp_path, run):
    """`runner:` outside {docker, podman} - config.py's BadConfig for this same value - must not
    reach shutil.which, which resolves a path and would run it as the engine. An absolute path
    to a real executable (standing in for `runner: ./x`) proves it: if the guard is missing, this
    script is what `compose run` shells out to, and its own marker text shows up in the report."""
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    (tmp_path / ".orclab").mkdir()
    rogue = tmp_path / "x"
    rogue.write_text('#!/bin/sh\necho "ROGUE RAN: $*"\nexit 1\n')
    rogue.chmod(rogue.stat().st_mode | stat.S_IEXEC)
    (tmp_path / ".orclab" / "test.yaml").write_text(f"runner: {rogue}\n")
    f = src / "a.py"
    f.write_text("x = 1\n")
    bin_dir = fake_tool(tmp_path / "bin", "ruff", 1, "src/a.py:1:1: E999 fake finding")
    r = run(f, bin_dir=bin_dir)
    assert r.returncode == 0
    assert "compose run" not in r.stderr and "ROGUE RAN" not in r.stderr


def test_as_a_process_findings_are_exit_2_on_stderr(tmp_path):
    """The contract Claude Code sees; the one test here that runs the script for real."""
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    f = src / "app.py"
    f.write_text("except: pass\n")
    bin_dir = fake_tool(tmp_path / "bin", "ruff", 1, "src/app.py:1:1: E722 Do not use bare `except`")
    out = subprocess.run([sys.executable, HOOK], check=False,
                         input=json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(f)}}),
                         capture_output=True, text=True, env={"PATH": f"{bin_dir}:/usr/bin:/bin"})
    assert out.returncode == 2 and "E722" in out.stderr and out.stdout == ""

