import json
import os
import pathlib
import stat
import subprocess
import sys

HOOK = str(pathlib.Path(__file__).resolve().parent.parent / "lint_on_write.py")


def fake_tool(bin_dir, name, exit_code, output):
    """A stand-in linter on PATH that prints `output` and exits `exit_code`."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    p = bin_dir / name
    p.write_text(f"#!/bin/sh\ncat <<'ORC'\n{output}\nORC\nexit {exit_code}\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return bin_dir


def run(file_path, tool_name="Write", bin_dir=None, env_extra=None):
    env = dict(os.environ, **(env_extra or {}))
    if bin_dir is not None:
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
    return subprocess.run([sys.executable, HOOK],
                          input=json.dumps({"tool_name": tool_name, "tool_input": {"file_path": str(file_path)}}),
                          capture_output=True, text=True, env=env)


def project(tmp_path, config_name, config_text=""):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / config_name).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / config_name).write_text(config_text)
    src = tmp_path / "src"
    src.mkdir()
    return src


def test_findings_reach_claude_as_exit_2_on_stderr(tmp_path):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\nline-length = 100\n")
    f = src / "app.py"
    f.write_text("try:\n    x = 1\nexcept:\n    pass\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "ruff", 1, "src/app.py:3:1: E722 Do not use bare `except`"))
    assert out.returncode == 2
    assert "E722" in out.stderr and "ruff check" in out.stderr and "lint_on_write" in out.stderr
    assert out.stdout == ""


def test_a_clean_file_says_nothing(tmp_path):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    f = src / "ok.py"
    f.write_text("x = 1\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "ruff", 0, "All checks passed!"))
    assert (out.returncode, out.stdout, out.stderr) == (0, "", "")


def test_no_config_means_no_run_even_with_the_tool_installed(tmp_path):
    """The hook runs the project's configured linter, never its own opinion."""
    src = project(tmp_path, "pyproject.toml", "[project]\nname = 'x'\n")   # no [tool.ruff]
    f = src / "app.py"
    f.write_text("except: pass\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "ruff", 1, "would have complained"))
    assert (out.returncode, out.stderr) == (0, "")


def test_config_is_found_between_the_file_and_the_git_root(tmp_path):
    """A sub-project's own pyproject (skills/x/scripts/pyproject.toml) wins over none at the root."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    sub = tmp_path / "skills" / "x" / "scripts"
    sub.mkdir(parents=True)
    (sub / "pyproject.toml").write_text("[tool.ruff]\n")
    f = sub / "pkg.py"
    f.write_text("x = 1\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "ruff", 1, "F401 unused import"))
    assert out.returncode == 2 and "F401" in out.stderr


def test_javascript_prefers_the_projects_own_node_modules_binary(tmp_path):
    src = project(tmp_path, ".oxlintrc.json", "{}")
    f = src / "a.ts"
    f.write_text("if (a) { if (b) { if (c) {} } }\n")
    fake_tool(tmp_path / "node_modules" / ".bin", "oxlint", 1, "max-depth: Blocks are nested too deeply (3)")
    out = run(f)                                   # nothing on PATH; node_modules/.bin must be used
    assert out.returncode == 2 and "max-depth" in out.stderr


def test_eslint_config_is_the_fallback_when_there_is_no_oxlint_config(tmp_path):
    src = project(tmp_path, "eslint.config.js", "export default [];\n")
    f = src / "a.tsx"
    f.write_text("x\n")
    out = run(f, bin_dir=fake_tool(tmp_path / "bin", "eslint", 1, "no-empty: Empty block statement"))
    assert out.returncode == 2 and "no-empty" in out.stderr


def test_unlinted_languages_and_other_tools_are_ignored(tmp_path):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    cs = src / "a.cs"
    cs.write_text("class A {}\n")
    assert run(cs, bin_dir=fake_tool(tmp_path / "bin", "ruff", 1, "no")).returncode == 0
    py = src / "a.py"
    py.write_text("x\n")
    assert run(py, tool_name="Bash", bin_dir=tmp_path / "bin").returncode == 0
    assert run(py, bin_dir=tmp_path / "bin", env_extra={"ORCLAB_LINT_ON_WRITE_OFF": "1"}).returncode == 0
    assert run(tmp_path / "missing.py", bin_dir=tmp_path / "bin").returncode == 0


def test_a_long_report_is_truncated_not_dropped(tmp_path):
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
