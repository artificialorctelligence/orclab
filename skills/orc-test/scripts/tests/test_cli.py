import os
import types

from orc_test import cli, container, langs, runner
from tests.helpers import fake, make_repo, run


def test_outside_git_says_so(tmp_path, capsys):
    code, out = run(["detect"], tmp_path, capsys)
    assert code == 1 and "not inside a git repository" in out


def test_detect_lists_languages(tmp_path, capsys):
    code, out = run(["detect"], make_repo(tmp_path), capsys)
    assert code == 0 and "detected: Python" in out


def test_run_green_suite_exits_zero_and_prints_command(tmp_path, capsys):
    code, out = run(["run"], make_repo(tmp_path), capsys)
    assert code == 0
    assert "$ python3 -m pytest -q '--ignore-glob=*mutants/*'" in out
    assert "Python" in out and "passed" in out


def test_no_subcommand_means_run(tmp_path, capsys):
    code, out = run([], make_repo(tmp_path), capsys)
    assert code == 0 and "$ python3 -m pytest" in out and "1 passed" in out


def test_green_suite_with_counts_does_not_print_the_output_tail(tmp_path, capsys):
    _code, out = run(["run"], make_repo(tmp_path), capsys)
    assert out.count("1 passed") == 1        # the summary line only, not pytest's own output too


def test_root_level_mutants_dir_is_ignored(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "mutants" / "tests").mkdir(parents=True)
    (repo / "mutants" / "tests" / "test_x.py").write_text("import no_such_module_anywhere\n")
    code, out = run(["run"], repo, capsys)
    assert code == 0 and "1 passed" in out


def test_marker_two_directories_down_runs_from_there(tmp_path, capsys, monkeypatch):
    """dart._flutter reads root/pubspec.yaml: a marker under app/ used to crash every subcommand."""
    repo = make_repo(tmp_path)
    (repo / "pyproject.toml").unlink()
    (repo / "app").mkdir()
    (repo / "app" / "pubspec.yaml").write_text("name: app\n")
    seen = []
    m = fake()
    m.MARKERS = ["pubspec.yaml"]
    m.test_cmd = lambda root, t: seen.append((root, t)) or ["true"]
    monkeypatch.setattr(langs, "ALL", [m])
    code, out = run(["detect"], repo, capsys)
    assert code == 0 and "detected: Fake (app/)" in out
    code, out = run(["run", "app/lib"], repo, capsys)
    assert code == 0 and seen[-1] == (repo / "app", "lib")     # cwd=app, path made app-relative
    code, out = run(["run", "docs"], repo, capsys)
    assert seen[-1] == (repo / "app", None) and "docs is not under app/" in out


def test_run_red_suite_exits_nonzero(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "tests" / "test_bad.py").write_text("def test_bad():\n    assert 0\n")
    code, out = run(["run"], repo, capsys)
    assert code == 1 and "failed" in out


def test_empty_suite_reports_zero_tests_not_failed(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "tests" / "test_ok.py").unlink()
    code, out = run(["run"], repo, capsys)
    assert code == 1
    assert "0 tests" in out and "✗" in out


def test_missing_tool_skips_language_with_install_line(tmp_path, capsys, monkeypatch):
    fake = types.SimpleNamespace(KEY="fake", LABEL="Fake", MARKERS=["pyproject.toml"],
                                 TOOLS={"faketool": "brew install faketool"},
                                 missing=lambda root: ["faketool"])
    monkeypatch.setattr(langs, "ALL", [fake])
    code, out = run(["run"], make_repo(tmp_path), capsys)
    assert "Fake: missing faketool — brew install faketool — skipped" in out
    assert code == 0


def test_declared_command_wins(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "Makefile").write_text("test:\n\t@echo make-ran\n")
    _code, out = run(["run"], repo, capsys)
    assert "$ make test" in out and "make-ran" in out


def test_bad_config_reports_error(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / ".orclab").mkdir()
    (repo / ".orclab" / "test.yaml").write_text("coverage: [unterminated\n")
    code, out = run(["detect"], repo, capsys)
    assert code == 1 and "invalid YAML" in out


# --- containers (v23 §2): built once, probed inside, never the host ---

def _fake_docker(repo, monkeypatch, script):
    bin_dir = repo / "fakebin"
    bin_dir.mkdir()
    (bin_dir / "docker").write_text(script)
    (bin_dir / "docker").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    # RUNNERS prefers podman; on a machine that has it (this one, since 2026-09-20) the real
    # engine would win over the fake — name the fake explicitly
    (repo / ".orclab").mkdir(exist_ok=True)
    (repo / ".orclab" / "test.yaml").write_text("runner: docker\n")


def test_detect_says_in_container_and_probes_inside(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    (repo / "compose.yaml").write_text("services:\n  orclab:\n    build: .\n")
    _fake_docker(repo, monkeypatch, "#!/bin/sh\necho \"argv: $*\"\nexit 0\n")
    code, out = run(["detect"], repo, capsys)
    assert code == 0 and "detected: Python (in container)" in out
    assert "$ docker compose build orclab" in out
    assert "$ docker compose run --rm -T --workdir" in out and "import pytest" in out


def test_runner_missing_skips_the_language_and_never_runs_on_the_host(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    (repo / "compose.yaml").write_text("services:\n  orclab:\n    build: .\n")
    (repo / ".orclab").mkdir()
    (repo / ".orclab" / "test.yaml").write_text("runner: podman\n")
    git_only = repo / "gitonly"          # a PATH with git and nothing else: podman is absent whatever this host has
    git_only.mkdir()
    (git_only / "git").symlink_to(cli.shutil.which("git"))
    monkeypatch.setenv("PATH", str(git_only))
    code, out = run(["run"], repo, capsys)
    assert code == 0 and "Python: container runner not found — install podman or docker — skipped" in out
    assert "$ python3 -m pytest" not in out


def test_tool_missing_inside_the_container_is_skipped_never_the_host(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    (repo / "compose.yaml").write_text("services:\n  orclab:\n    build: .\n")
    _fake_docker(repo, monkeypatch, '#!/bin/sh\ncase "$*" in\n  "compose build"*) exit 0 ;;\n  *) exit 1 ;;\nesac\n')
    code, out = run(["run"], repo, capsys)
    assert code == 0 and "Python: missing pytest — pip install pytest — skipped" in out
    assert "$ python3 -m pytest" not in out


def test_build_failure_is_exit_one_with_the_output(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    (repo / "compose.yaml").write_text("services:\n  orclab:\n    build: .\n")
    _fake_docker(repo, monkeypatch, "#!/bin/sh\necho 'ERROR: failed to solve'\nexit 17\n")
    code, out = run(["run"], repo, capsys)
    assert code == 1 and "failed to solve" in out and "container build failed — see above" in out
    assert "$ python3 -m pytest" not in out


def test_build_failure_logged_by_podman_compose_1_0_6_is_still_a_failure(tmp_path, capsys, monkeypatch):
    # podman-compose 1.0.6 (Mint's apt) logs podman's status as "exit code: N" on stderr and
    # exits 0 itself; seen live 2026-09-20 with FROM no-such-image:0 — the tests ran in the stale
    # image. The fake logs it on stderr too: build_failed sees it only because run_on_host merges
    repo = make_repo(tmp_path)
    (repo / "compose.yaml").write_text("services:\n  orclab:\n    build: .\n")
    _fake_docker(repo, monkeypatch, '#!/bin/sh\ncase "$*" in\n  "compose build"*) echo "STEP 1/1: FROM no-such-image:0"; echo "Error: creating build container"; echo "exit code: 125" >&2; exit 0 ;;\n  *) exit 0 ;;\nesac\n')
    code, out = run(["run"], repo, capsys)
    assert code == 1 and "exit code: 125" in out and "container build failed — see above" in out
    assert "$ python3 -m pytest" not in out


def test_dirty_asks_the_host_git_even_when_a_container_is_active(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    _fake_docker(repo, monkeypatch, "#!/bin/sh\necho \"argv: $*\"\nexit 0\n")
    runner.use(container.Container(root=repo, runner="docker"))
    assert cli._dirty(repo, set()) == set()
    out = capsys.readouterr().out
    assert out.startswith("$ git status --porcelain") and "$ docker" not in out


def test_containerised_sub_project_is_run_in_its_own_container(tmp_path, capsys, monkeypatch):
    """BACKLOG #66 (orcweather, 2026-09-20): compose.yaml beside server/composer.json, none at the
    root. The marker was found two directories down and the container was not — PHP was skipped
    as "missing composer" while Python ran on the host. Each language gets the container beside
    its own marker, falling back to the root's; the host is used only where neither exists."""
    repo = make_repo(tmp_path)
    (repo / "server").mkdir()
    (repo / "server" / "composer.json").write_text("{}\n")
    (repo / "server" / "compose.yaml").write_text("services:\n  orclab:\n    build: .\n")
    _fake_docker(repo, monkeypatch, "#!/bin/sh\necho \"argv: $*\"\nexit 0\n")
    code, out = run(["detect"], repo, capsys)
    assert code == 0
    assert "detected: Python, PHP (server/) (in container)" in out
    assert "missing composer" not in out
    assert "$ docker compose build orclab" in out
    assert f"--workdir {repo / 'server'} orclab sh -c 'command -v composer'" in out
    assert "import pytest" not in out          # Python's probe stayed on the host (importlib, no command printed)
    assert "PHP: test command vendor/bin/phpunit" in out


def test_language_that_says_nothing_ran_is_zero_tests_even_on_exit_zero(tmp_path, capsys, monkeypatch):
    """BACKLOG #67: Gradle exits 0 on a NO-SOURCE test task; the language module's own summary
    decides "ran", not pytest's exit-5 / 'no tests ran' signals."""
    repo = make_repo(tmp_path)
    m = fake()
    m.test_summary = lambda root, cp: (False, "")
    monkeypatch.setattr(cli.langs, "ALL", [m])
    code, out = run(["run"], repo, capsys)
    assert code == 1 and "0 tests" in out and "✗" in out
    m.test_summary = lambda root, cp: (True, "12 passed")
    code, out = run(["run"], repo, capsys)
    assert code == 0 and "✓ 12 passed" in out
