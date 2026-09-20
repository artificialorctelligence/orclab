"""A project that runs its toolchain in a container: compose.yaml with an `orclab` service
(spec 2026-09-20-orclab-v23-containers-design.md §1–§2)."""

import os
import stat

from orc_test import container, runner

COMPOSE = "services:\n  orclab:\n    build: .\n    volumes:\n      - .:${PWD}\n    working_dir: ${PWD}\n"


def fake_runner(tmp_path, name="docker"):
    """A script on PATH that prints its argv, so the prefix is observable."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    p = bin_dir / name
    p.write_text('#!/bin/sh\necho "argv: $*"\n')
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return bin_dir


def test_no_compose_means_no_container(tmp_path):
    assert container.detect(tmp_path, {"container": True, "runner": None}) is None


def test_compose_without_orclab_service_is_not_the_record(tmp_path):
    (tmp_path / "compose.yaml").write_text("services:\n  web:\n    image: nginx\n")
    assert container.detect(tmp_path, {"container": True, "runner": None}) is None


def test_orclab_service_is_the_record_and_runner_is_the_first_on_path(tmp_path, monkeypatch):
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    monkeypatch.setenv("PATH", f"{fake_runner(tmp_path, 'podman')}:{os.environ['PATH']}")
    monkeypatch.setattr(container, "RUNNERS", ("docker", "podman"))
    monkeypatch.setattr(container.shutil, "which", lambda n: str(tmp_path / "bin" / n) if n == "podman" else None)
    c = container.detect(tmp_path, {"container": True, "runner": None})
    assert c == container.Container(root=tmp_path, runner="podman")


def test_runner_override_wins_even_when_absent_from_path(tmp_path, monkeypatch):
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    monkeypatch.setattr(container.shutil, "which", lambda n: None)
    c = container.detect(tmp_path, {"container": True, "runner": "podman"})
    assert c.runner is None      # named but not installed: the caller says so; never the host


def test_container_false_opts_this_checkout_out(tmp_path):
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    assert container.detect(tmp_path, {"container": False, "runner": None}) is None


def test_no_engine_on_path_is_a_container_with_no_runner(tmp_path, monkeypatch):
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    monkeypatch.setattr(container.shutil, "which", lambda n: None)
    assert container.detect(tmp_path, {"container": True, "runner": None}).runner is None


def test_malformed_compose_is_not_the_record(tmp_path):
    (tmp_path / "compose.yaml").write_text("services: [\n")
    assert container.detect(tmp_path, {"container": True, "runner": None}) is None


def test_wrap_is_compose_run_at_the_same_path():
    c = container.Container(root="/p", runner="docker")
    assert container.wrap(c, ["python3", "-m", "pytest"], "/p/app") == [
        "docker", "compose", "run", "--rm", "-T", "--workdir", "/p/app", "orclab", "python3", "-m", "pytest"]
    assert container.build_cmd(c) == ["docker", "compose", "build", "orclab"]


def test_run_prefixes_when_a_container_is_active(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PATH", f"{fake_runner(tmp_path)}:{os.environ['PATH']}")
    runner.use(container.Container(root=tmp_path, runner="docker"))
    cp = runner.run(["python3", "-c", "print(1)"], cwd=tmp_path / "sub")
    assert cp.stdout.strip() == f"argv: compose run --rm -T --workdir {tmp_path / 'sub'} orclab python3 -c print(1)"
    assert capsys.readouterr().out.startswith("$ docker compose run --rm -T --workdir")


def test_run_is_unchanged_without_a_container(tmp_path, capsys):
    cp = runner.run(["echo", "hi"], cwd=tmp_path)
    assert cp.stdout == "hi\n" and capsys.readouterr().out == "$ echo hi\n"


def test_run_on_host_is_never_wrapped(tmp_path, capsys):
    runner.use(container.Container(root=tmp_path, runner="docker"))
    cp = runner.run_on_host(["echo", "host"], cwd=tmp_path)
    assert cp.stdout == "host\n" and capsys.readouterr().out == "$ echo host\n"
