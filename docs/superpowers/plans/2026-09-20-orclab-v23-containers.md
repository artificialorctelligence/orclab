# Orclab v23: containers as an opt-in development environment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A project can opt, at `/orc-code` scaffold, to run its toolchain in a container; `/orc-test` (and so `/orc-git`'s gates) and `lint_on_write` then run every tool through it, every stack skill says whether it can, and nothing is ever silently run on the host instead.

**Architecture:** The committed `compose.yaml` with a service named `orclab` is the opt-in record; the project is mounted inside at its own host path, so every report path is valid on both sides. `/orc-test` changes in one place — `runner.run`, the chokepoint every language module already uses — plus a small `container.py` that reads the record and picks the engine; the tool-presence checks in each language module go through the same chokepoint. `lint_on_write` is a standalone hook and gets its own fifteen-line copy of the detection (the hooks' documented convention). A `## Containers` facet lands in all nine stack skills, pinned by a test like v22's Security one.

**Tech Stack:** Python 3.12 / pytest; PyYAML (already a `/orc-test` dependency); Docker Engine or Podman via `compose run` (research picks the default; both are in Mint's apt); Markdown skills.

**Spec:** `docs/superpowers/specs/2026-09-20-orclab-v23-containers-design.md`. Read it first; each task names the section it rests on.

## Global Constraints

- **The record is `compose.yaml` at the project root with a service named `orclab`** (spec §1). Nothing under `.orclab/` records the opt-in — `.orclab/` is git-ignored.
- **Same-path mount convention:** the container's working directory for every command is the same absolute path as on the host (spec §1); `runner.wrap` passes it explicitly with `--workdir`.
- **Per-checkout override in `.orclab/test.yaml`:** `container: false` (host run in this checkout) and `runner: docker|podman` (spec §1). Absent `runner`: the first of the research-picked default order that is on PATH.
- **Never a silent fallback to the host** (spec §2): runner missing → `<Label>: container runner not found — install docker or podman — skipped`; image build fails → its output printed, then `container build failed — see above`, exit 1 from every subcommand.
- **`/orc-test` never installs a tool — including the engine** (spec §2).
- **The eight language modules' commands do not change** (spec §2); only how they are run and how their tools' presence is checked.
- **Hooks duplicate rather than import** (`hooks/scripts/orclab_shared.py`'s docstring): `lint_on_write` gets its own detection, no `sys.path` into a skill, no PyYAML dependency in the hook.
- **Every stack section stamps "confirmed live YYYY-MM-DD"** and says "Runs in a container: yes" or "Runs in a container: no" in those words (spec §3); every claim has a URL in `## Sources`.
- **Docs pages change in the same commit as their skill** and keep exactly five `##` headings (`hooks/scripts/tests/test_docs.py`).
- **The engine install on this machine is direflail's to run** — the live task shows the command and waits (spec §4).
- Tests from the repo root: `cd /home/direflail/projects/orclab && python3 -m pytest -q <path>`; whole suite `python3 -m pytest -q` (770 passed at v0.22.0).
- Commit messages end with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- Skills are written for the reader who has not been in this session.
- Work in a worktree from `origin/main`; `main` is one commit (the spec, `cd81b76`) plus this plan ahead of origin and must be pushed first.

## File structure

| File | Responsibility | Task |
|---|---|---|
| `skills/orc-test/scripts/orc_test/container.py` (create) | Read the record and the override; pick the runner; build the `compose run` prefix. The only place that knows compose exists. | 1 |
| `skills/orc-test/scripts/orc_test/runner.py` | `use(container)` / `active()`; `run` prefixes when active. | 1 |
| `skills/orc-test/scripts/orc_test/config.py` | `.orclab/test.yaml` gains `container` and `runner`. | 1 |
| `skills/orc-test/scripts/tests/test_container.py` (create), `test_runner.py`, `test_config.py` | The above, with a fake runner script on PATH. | 1 |
| `skills/orc-test/scripts/orc_test/probe.py` (create) | `which(tool)` / `python_module(name)` — host checks when no container is active, a command through `runner.run` when one is. | 2 |
| `skills/orc-test/scripts/orc_test/langs/*.py` (eight) | `missing()` uses `probe`. | 2 |
| `skills/orc-test/scripts/orc_test/cli.py` | `_resolve` activates the container, builds the image once, prints `(in container)`, the runner-missing line. | 2 |
| `skills/orc-test/scripts/tests/test_probe.py` (create), `test_cli.py`, `test_lang_*.py` | The above. | 2 |
| `hooks/scripts/lint_on_write.py`, `hooks/scripts/tests/test_lint_on_write.py` | The duplicated detection; the prefix; the on-PATH check inside. | 3 |
| `skills/orc-test/SKILL.md`, `docs/commands/orc-test.md`, `hooks/scripts/tests/test_orc_test_skill.py` | `## Containers` (the engine, from live research), the override, the never-installs line. | 4 |
| `hooks/scripts/tests/test_stack_containers.py` (create) | The facet test, `EXPECTED` growing over Tasks 5–7. | 5 |
| `skills/stack-python-desktop/SKILL.md`, `skills/stack-web/SKILL.md` | `## Containers`: yes. | 5 |
| `skills/stack-android-native`, `stack-kotlin-multiplatform`, `stack-flutter`, `stack-react-native` | `## Containers`: Android half yes, iOS half no. | 6 |
| `skills/stack-ios-native`, `stack-godot`, `stack-unity` | `## Containers`: no; headless builds researched. | 7 |
| `skills/orc-code/SKILL.md`, `docs/commands/orc-code.md`, `hooks/scripts/tests/test_orc_code_skill.py` | The question, the two files, Verify through the container. | 8 |
| `BACKLOG.md`, the live-check lines in `skills/orc-test/languages/python.md` | Entries; the live check. | 9 |

Task 1 defines `container.Container` and `runner.use` that Tasks 2–3 consume; Task 4's research settles the runner order that Task 1 hard-codes as a constant (Task 4 edits the constant if research disagrees); Tasks 5–7 are independent of each other and of 8; Task 8 needs Task 4's section to point at; Task 9 needs everything.

---

### Task 1: `container.py`, `runner.use`, the config keys

**Files:**
- Create: `skills/orc-test/scripts/orc_test/container.py`
- Modify: `skills/orc-test/scripts/orc_test/runner.py`
- Modify: `skills/orc-test/scripts/orc_test/config.py`
- Create: `skills/orc-test/scripts/tests/test_container.py`
- Modify: `skills/orc-test/scripts/tests/test_runner.py`, `test_config.py`

**Interfaces:**
- Produces `container.Container` — `@dataclass(frozen=True)`: `root: pathlib.Path`, `runner: str | None` (None when no engine is on PATH).
- Produces `container.detect(root, cfg) -> Container | None` — None when the project is not containerised or `cfg["container"] is False`.
- Produces `container.RUNNERS = ("docker", "podman")` — the default order; Task 4 may reorder.
- Produces `container.wrap(c, cmd, cwd) -> list[str]` — `[c.runner, "compose", "run", "--rm", "-T", "--workdir", str(cwd), "orclab", *cmd]`.
- Produces `container.build_cmd(c) -> list[str]` — `[c.runner, "compose", "build", "orclab"]`.
- Produces `runner.use(c: Container | None)` and `runner.active() -> Container | None`; `runner.run` wraps when active and runs from `c.root`.
- Produces `runner.run_on_host(cmd, cwd, input=None)` — the same as `run` but never wrapped, for the few commands that belong to the host (git).
- Produces `config.load` keys `container: bool` (default True — "honour the record") and `runner: str | None`.

- [ ] **Step 1: Write the tests, red**

Create `skills/orc-test/scripts/tests/test_container.py`:

```python
"""A project that runs its toolchain in a container: compose.yaml with an `orclab` service
(spec 2026-09-20-orclab-v23-containers-design.md §1–§2)."""

import os
import stat

import pytest

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


@pytest.fixture(autouse=True)
def no_container():
    runner.use(None)
    yield
    runner.use(None)


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
```

Append to `test_config.py`:

```python
def test_container_keys_default_and_read(tmp_path):
    cfg = config.load(tmp_path)
    assert cfg["container"] is True and cfg["runner"] is None
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text("container: false\nrunner: podman\n")
    cfg = config.load(tmp_path)
    assert cfg["container"] is False and cfg["runner"] == "podman"


def test_runner_must_be_a_known_engine(tmp_path):
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text("runner: rkt\n")
    with pytest.raises(config.BadConfig, match="runner"):
        config.load(tmp_path)
```

(`test_config.py` imports `config`; add `import pytest` if it is not already there.)

- [ ] **Step 2: Run red**

`python3 -m pytest -q skills/orc-test/scripts/tests/test_container.py skills/orc-test/scripts/tests/test_config.py` → the container tests fail on import; the config ones on the missing keys.

- [ ] **Step 3: `container.py`**

```python
"""A project that runs its toolchain in a container (v23). The record is compose.yaml at the
project root with a service named `orclab` — committed, so a clone keeps the opt-in; nothing
under .orclab/ can serve, that directory is git-ignored. Inside, the project is mounted at its
own host path, so every path in every report is valid on both sides and nothing is translated."""

import pathlib
import shutil
from dataclasses import dataclass

import yaml

RUNNERS = ("docker", "podman")     # default order when .orclab/test.yaml names none; Task 4's research may reorder
SERVICE = "orclab"


@dataclass(frozen=True)
class Container:
    root: pathlib.Path
    runner: str | None          # None: the engine is not on PATH — the caller says so, never runs on the host


def detect(root, cfg):
    """The project's Container, or None when it is not containerised or this checkout opted out."""
    root = pathlib.Path(root)
    if cfg.get("container") is False or not _has_service(root / "compose.yaml"):
        return None
    wanted = cfg.get("runner")
    names = (wanted,) if wanted else RUNNERS
    return Container(root, next((n for n in names if shutil.which(n)), None))


def _has_service(path):
    try:
        data = yaml.safe_load(path.read_text()) if path.is_file() else None
    except yaml.YAMLError:
        return False
    return isinstance(data, dict) and isinstance(data.get("services"), dict) and SERVICE in data["services"]


def wrap(c, cmd, cwd):
    # -T: no pseudo-tty (stdout is a pipe); --workdir: the same absolute path as on the host
    return [c.runner, "compose", "run", "--rm", "-T", "--workdir", str(cwd), SERVICE, *cmd]


def build_cmd(c):
    return [c.runner, "compose", "build", SERVICE]
```

- [ ] **Step 4: `runner.py`**

```python
"""One place every external command goes through, so every one is printed before it runs — and,
for a containerised project (v23), the one place the `compose run` prefix is added."""

import shlex
import subprocess

from . import container

_ACTIVE = None


def use(c):
    """Every later run() goes through `c` (a container.Container), or the host when None."""
    global _ACTIVE
    _ACTIVE = c


def active():
    return _ACTIVE


def run(cmd, cwd, env=None, input=None):
    if _ACTIVE is not None:
        cmd, cwd = container.wrap(_ACTIVE, cmd, cwd), _ACTIVE.root   # compose reads compose.yaml from cwd
    return run_on_host(cmd, cwd, env=env, input=input)


def run_on_host(cmd, cwd, env=None, input=None):
    """Never wrapped: git, and anything else that is the host's business even when a container
    is active."""
    print("$ " + shlex.join(cmd), flush=True)
    try:
        return subprocess.run(cmd, check=False, cwd=str(cwd), env=env, input=input, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        return subprocess.CompletedProcess(cmd, 127, stdout=f"{cmd[0]}: not found\n", stderr="")
```

Add to `test_container.py`:

```python
def test_run_on_host_is_never_wrapped(tmp_path, capsys):
    runner.use(container.Container(root=tmp_path, runner="docker"))
    cp = runner.run_on_host(["echo", "host"], cwd=tmp_path)
    assert cp.stdout == "host\n" and capsys.readouterr().out == "$ echo host\n"
```

- [ ] **Step 5: `config.py`**

After the thresholds loop, before `cfg["languages"] = ...`:

```python
    cfg["container"] = data.get("container", True) is not False
    runner = data.get("runner")
    if runner is not None and runner not in ("docker", "podman"):
        raise BadConfig(f"{path}: runner must be docker or podman, got {runner!r}")
    cfg["runner"] = runner
```

and the default dict becomes `{"coverage": 80, "tce": 70, "languages": {}, "container": True, "runner": None}`. Update the module docstring: "Thresholds, per-language command overrides, and the per-checkout container override (v23)."

- [ ] **Step 6: Green, whole orc-test suite, commit**

`python3 -m pytest -q skills/orc-test/scripts/tests` → green (existing runner tests unaffected: nothing is active by default).

```bash
git add skills/orc-test/scripts/orc_test/container.py skills/orc-test/scripts/orc_test/runner.py skills/orc-test/scripts/orc_test/config.py skills/orc-test/scripts/tests/test_container.py skills/orc-test/scripts/tests/test_config.py
git commit -m "orc-test: container.py reads the compose.yaml record and the per-checkout override; runner.run prefixes compose run at the same path when a container is active (v23 §1–2)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: `_resolve` activates it; `probe` moves the tool checks inside; the detect line

**Files:**
- Create: `skills/orc-test/scripts/orc_test/probe.py`
- Modify: `skills/orc-test/scripts/orc_test/cli.py` (`_resolve`, `main`)
- Modify: `skills/orc-test/scripts/orc_test/langs/{python,javascript,java,kotlin,csharp,dart,swift,gdscript}.py` (`missing()` only)
- Create: `skills/orc-test/scripts/tests/test_probe.py`
- Modify: `skills/orc-test/scripts/tests/test_cli.py`, and each `test_lang_*.py` that monkeypatches `shutil.which` or `importlib.util.find_spec` in a `missing` test (grep for `which` and `find_spec` in `tests/` — those tests now monkeypatch `probe.which` / `probe.python_module` instead)

**Interfaces:**
- Consumes Task 1's `container.detect`, `container.build_cmd`, `runner.use`, `runner.active`.
- Produces `probe.which(tool) -> bool` — `shutil.which` on the host; `sh -c 'command -v <tool>'` through `runner.run` when a container is active (exit 0 means present).
- Produces `probe.python_module(name) -> bool` — `importlib.util.find_spec` on the host; `python3 -c "import <name>"` through `runner.run` when active.
- Produces `cli.ContainerUnavailable(Exception)` — raised by `_resolve` when the image fails to build; `main` prints `container build failed — see above` and returns 1.
- Produces the lines: `detected: Python (in container)`; `Python: container runner not found — install docker or podman — skipped`.

- [ ] **Step 1: `test_probe.py`, red**

```python
from orc_test import container, probe, runner


def test_host_checks_when_no_container(monkeypatch):
    runner.use(None)
    monkeypatch.setattr(probe.shutil, "which", lambda n: "/usr/bin/x" if n == "x" else None)
    assert probe.which("x") and not probe.which("y")
    assert probe.python_module("json") and not probe.python_module("no_such_module_anywhere")


def test_container_checks_go_through_run(monkeypatch, tmp_path):
    seen = []
    runner.use(container.Container(root=tmp_path, runner="docker"))
    monkeypatch.setattr(probe.runner, "run", lambda cmd, cwd: seen.append(cmd) or _cp(0 if "pytest" in cmd[-1] else 1))
    try:
        assert probe.python_module("pytest") and not probe.python_module("nope")
        assert probe.which("pytest") and not probe.which("nope")
    finally:
        runner.use(None)
    assert seen[0] == ["python3", "-c", "import pytest"]
    assert seen[2] == ["sh", "-c", "command -v pytest"]


def _cp(code):
    import subprocess
    return subprocess.CompletedProcess([], code, stdout="", stderr="")
```

- [ ] **Step 2: `test_cli.py` additions, red**

```python
def test_detect_says_in_container_and_probes_inside(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    (repo / "compose.yaml").write_text("services:\n  orclab:\n    build: .\n")
    bin_dir = repo / "fakebin"
    bin_dir.mkdir()
    (bin_dir / "docker").write_text("#!/bin/sh\necho \"argv: $*\"\nexit 0\n")
    (bin_dir / "docker").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    code, out = run(["detect"], repo, capsys)
    assert code == 0 and "detected: Python (in container)" in out
    assert "$ docker compose build orclab" in out
    assert "$ docker compose run --rm -T --workdir" in out and "import pytest" in out


def test_runner_missing_skips_the_language_and_never_runs_on_the_host(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    (repo / "compose.yaml").write_text("services:\n  orclab:\n    build: .\n")
    monkeypatch.setattr(cli.container.shutil, "which", lambda n: None)
    code, out = run(["run"], repo, capsys)
    assert code == 0 and "Python: container runner not found — install docker or podman — skipped" in out
    assert "$ python3 -m pytest" not in out


def test_build_failure_is_exit_one_with_the_output(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    (repo / "compose.yaml").write_text("services:\n  orclab:\n    build: .\n")
    bin_dir = repo / "fakebin"
    bin_dir.mkdir()
    (bin_dir / "docker").write_text("#!/bin/sh\necho 'ERROR: failed to solve'\nexit 17\n")
    (bin_dir / "docker").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    code, out = run(["run"], repo, capsys)
    assert code == 1 and "failed to solve" in out and "container build failed — see above" in out
    assert "$ python3 -m pytest" not in out
```

(`test_cli.py` imports `os` and `cli` — add `import os` and `from orc_test import cli` if missing; `run` and `make_repo` come from `tests.helpers`.) Run red: `python3 -m pytest -q skills/orc-test/scripts/tests/test_probe.py skills/orc-test/scripts/tests/test_cli.py`.

- [ ] **Step 3: `probe.py`**

```python
"""Is a tool present where the project's commands run? On the host, the cheap checks; inside a
container (v23), a command through the same chokepoint the tools run through — "missing" then
means missing where it matters, not on the developer's machine."""

import importlib.util
import shutil

from . import runner


def which(tool):
    if runner.active() is None:
        return shutil.which(tool) is not None
    return runner.run(["sh", "-c", f"command -v {tool}"], cwd=runner.active().root).returncode == 0


def python_module(name):
    if runner.active() is None:
        return importlib.util.find_spec(name) is not None
    return runner.run(["python3", "-c", f"import {name}"], cwd=runner.active().root).returncode == 0
```

- [ ] **Step 4: `_resolve` and `main` in `cli.py`**

Add after the imports: `from . import container` and

```python
class ContainerUnavailable(Exception):
    """The project is containerised and its image did not build; nothing runs on the host instead."""
```

In `_resolve`, after `found = detect.languages(root, mods)` and before the `detected:` print:

```python
    c = container.detect(root, cfg)
    runner.use(c)
    suffix = " (in container)" if c else ""
    print("detected: " + (", ".join(_name(m, d, root) + suffix for m, d in found) or "no supported language"))
    if c and c.runner is None:
        for m, _d in found:
            print(f"{m.LABEL}: container runner not found — install docker or podman — skipped")
        return root, cfg, []
    if c:
        cp = runner.run_on_host(container.build_cmd(c), cwd=root)   # the engine is a host command — never through the (now active) wrap
        if cp.returncode != 0:
            print(cp.stdout[-3000:])
            raise ContainerUnavailable
```

(`_name` and `suffix`: keep `_name` as is; the suffix is appended per language so `Dart (app/) (in container)` reads correctly. Replace the existing `print("detected: ...")` line with the one above.) Add `from .runner import run` stays; add `from . import runner` for `runner.use`. In `main`'s `try`, add `except ContainerUnavailable: print("container build failed — see above", file=sys.stderr); return 1` beside the other two excepts.

- [ ] **Step 5: `_dirty` stays on the host** — in `cli.py`, `_dirty` calls `run(["git", "status", "--porcelain"], cwd=root)`; change it to `runner.run_on_host(...)` (git is the host's; the container has no `.git` view it should be trusted with). Add to `test_cli_analyze.py` (or `test_cli.py`) one test: with a fake container active (`runner.use(container.Container(root=repo, runner="docker"))` and a fake `docker` on PATH), `cli._dirty(repo, set())` runs `$ git status --porcelain` — assert the printed command does not start with `$ docker`.

- [ ] **Step 6: every `missing()` through `probe` — and every other "is the tool here" check too.** Task 2's review (2026-09-20) found the spec named only `missing()`, but `audit_unavailable`, `mutation_unavailable` and `lint`'s own tool checks ask the same question and would ask it of the host: `python.py` (`find_spec("pip_audit")`, `find_spec("mutmut")`), `java.py` (`which("pmd")`), `csharp.py` (two), `javascript.py` (one), `kotlin.py` (one), `dart.py` (one), `swift.py` (two), `gdscript.py` (two). Every one of those becomes `probe.which` / `probe.python_module` as well — a containerised Python project whose host lacks mutmut must not say "mutmut not installed" when the image has it. Also: `_resolve` builds the image only when `found` is non-empty (`if c and found:`), and `probe.which` quotes the tool name with `shlex.quote`.

Each module: `from .. import probe` and

- `python.py`: `return [t for t in TOOLS if not probe.python_module(t)]`
- `javascript.py`, `csharp.py`: `return [t for t in TOOLS if not probe.which(t)]`
- `java.py`, `kotlin.py`: the `needed` dict logic unchanged, final line `return [t for t in needed if not probe.which(t)]`
- `dart.py`: `return [] if probe.which(tool) else [tool]`
- `swift.py`: `xcodebuild` branch unchanged (host-only by nature — a Mac); last line `return [] if probe.which("swift") else ["swift"]`
- `gdscript.py`: unchanged — `GODOT_BIN` is a host environment variable and gdUnit4 is a file in the project; its Containers section (Task 7) says the Godot binary path must be inside the image. Add a one-line comment saying so.

Remove now-unused `import shutil` / `import importlib.util` from modules that no longer use them (ruff will say). Update tests that monkeypatched `shutil.which`/`find_spec` for `missing` to monkeypatch `probe.which`/`probe.python_module`.

- [ ] **Step 7: Green, ruff, whole suite, commit**

`python3 -m pytest -q skills/orc-test/scripts/tests` → green. `python3 -m ruff check skills/orc-test/scripts/orc_test/ --output-format concise` → only the two pre-existing findings (`python.py` `mutation_parse` nesting; `mutmut_diffs.py` blind-except). `python3 -m pytest -q` → green.

```bash
git add skills/orc-test/scripts
git commit -m "orc-test: a containerised project builds its image once, probes its tools inside, and says (in container) — runner missing skips, build failure is exit 1, never the host (v23 §2)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: `lint_on_write` through the container

**Files:**
- Modify: `hooks/scripts/lint_on_write.py`
- Modify: `hooks/scripts/tests/test_lint_on_write.py`

**Interfaces:**
- Consumes nothing from Task 1 (hooks duplicate); produces `lint_on_write.container_prefix(root) -> list[str]` — `[]` on the host, else `[runner, "compose", "run", "--rm", "-T", "--workdir", str(root), "orclab"]`.

- [ ] **Step 1: Tests, red** — append to `test_lint_on_write.py` (the file's `project()` and `fake_tool()` helpers and the `run` fixture exist; read them first):

```python
COMPOSE = "services:\n  orclab:\n    build: .\n"


def test_containerised_project_lints_through_compose_run(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    f = src / "a.py"
    f.write_text("x = 1\n")
    bin_dir = fake_tool(tmp_path, "docker", "argv: $*\nsrc/a.py:1:1: E999 fake finding", exit_code=1)
    r = run(f, bin_dir=bin_dir)
    assert r.returncode == 2
    assert f"compose run --rm -T --workdir {tmp_path} orclab ruff check --no-fix" in r.stderr


def test_container_false_in_test_yaml_lints_on_the_host(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text("container: false\n")
    f = src / "a.py"
    f.write_text("x = 1\n")
    bin_dir = fake_tool(tmp_path, "ruff", "src/a.py:1:1: E999 fake finding", exit_code=1)
    r = run(f, bin_dir=bin_dir)
    assert r.returncode == 2 and "compose run" not in r.stderr


def test_containerised_project_with_no_engine_says_nothing(tmp_path, run):
    src = project(tmp_path, "pyproject.toml", "[tool.ruff]\n")
    (tmp_path / "compose.yaml").write_text(COMPOSE)
    f = src / "a.py"
    f.write_text("x = 1\n")
    r = run(f, bin_dir=fake_tool(tmp_path, "ruff", "finding", exit_code=1))   # ruff on the host, no docker
    assert r.returncode == 0    # fail open — the hook never runs a containerised project's linter on the host
```

(`fake_tool`'s real signature in that file — check it: the helper that writes a script printing `output` and exiting `exit_code`; `$*` in the heredoc must expand, so if the helper quotes the heredoc, write the docker fake by hand as Task 2's test does.)

- [ ] **Step 2: Implement** — in `lint_on_write.py`, add:

```python
# v23: a containerised project (compose.yaml with an `orclab` service at the git root) lints
# through the container. A deliberate copy of skills/orc-test/scripts/orc_test/container.py's
# detection, by the rule in orclab_shared.py's docstring; no PyYAML here, a regex is enough for
# the one shape Orclab itself writes.
SERVICE_RE = re.compile(r"^services:\s*$(?:\n(?!\S).*)*?^  orclab:\s*$", re.MULTILINE)
RUNNERS = ("docker", "podman")


def container_prefix(root):
    """[] on the host; the compose-run prefix when `root` is containerised and this checkout has
    not opted out; None when it is containerised but no engine is on PATH (then lint nothing)."""
    compose = pathlib.Path(root) / "compose.yaml"
    if not compose.is_file() or not SERVICE_RE.search(compose.read_text()):
        return []
    override = pathlib.Path(root) / ".orclab" / "test.yaml"
    text = override.read_text() if override.is_file() else ""
    if re.search(r"^container:\s*false\s*$", text, re.MULTILINE):
        return []
    m = re.search(r"^runner:\s*(\w+)\s*$", text, re.MULTILINE)
    names = (m.group(1),) if m else RUNNERS
    engine = next((n for n in names if shutil.which(n)), None)
    if engine is None:
        return None
    return [engine, "compose", "run", "--rm", "-T", "--workdir", str(root), "orclab"]
```

`root` for the prefix is the git root, not the config dir: use `orclab_shared`-style `git rev-parse --show-toplevel` from `root` (add a tiny helper, or reuse `_config_dir`'s git-root logic if it exposes one). In `command_for`, the on-PATH check `shutil.which(tool) is None` becomes: when the prefix is `[]`, as today; when it is a list, skip the host check (the tool lives inside); when it is `None`, return None. In `main`, `argv = prefix + argv` before `subprocess.run`, and `cwd=root` stays (compose reads `compose.yaml` from the git root — pass the git root as `cwd` when the prefix is non-empty).

- [ ] **Step 3: Green, commit**

`python3 -m pytest -q hooks/scripts/tests/test_lint_on_write.py` → green; whole suite green.

```bash
git add hooks/scripts/lint_on_write.py hooks/scripts/tests/test_lint_on_write.py
git commit -m "lint_on_write: a containerised project lints through compose run; no engine means no lint, never the host (v23 §2)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: the engine, from live research — `/orc-test`'s `## Containers`, the docs page

**Files:**
- Modify: `skills/orc-test/SKILL.md` (new `## Containers` section after `## How it finds the languages`; one sentence in `## What it never does`)
- Modify: `docs/commands/orc-test.md`
- Modify: `hooks/scripts/tests/test_orc_test_skill.py`
- Modify (only if research reorders): `skills/orc-test/scripts/orc_test/container.py::RUNNERS`, `hooks/scripts/lint_on_write.py::RUNNERS`, and Task 1's/3's tests that assert the order

**Interfaces:**
- Produces the runner default order and the `compose.yaml` text every stack section (Tasks 5–7) and `/orc-code` (Task 8) reuse verbatim.

- [ ] **Step 1: Pinning test, red** — append to `test_orc_test_skill.py`:

```python
def test_containers_section_names_the_record_the_override_and_the_engine():
    s = TEXT[TEXT.index("## Containers"):]
    s = s[:s.index("\n## ", 1)]
    for phrase in ["compose.yaml", "`orclab`", "container: false", "runner:", "docker", "podman",
                   "confirmed live 2026-", "(in container)", "container runner not found",
                   "container build failed", "never the host"]:
        assert phrase in s, phrase
    never = TEXT[TEXT.index("## What it never does"):TEXT.index("## `run`")]
    assert "engine" in never
```

- [ ] **Step 2: Research, primary sources only** — record every URL:
  1. Docker Engine on Ubuntu/Mint: `https://docs.docker.com/engine/install/ubuntu/` (already read 2026-09-20: Mint "not officially supported (though it may work)"; the codename detection); the Mint apt `docker.io` package as the no-third-party-source route; rootless: `https://docs.docker.com/engine/security/rootless/`; the `docker` group and what it grants.
  2. Podman: `https://podman.io/docs/installation` (Ubuntu apt `podman`), `podman compose` — `https://docs.podman.io/en/latest/markdown/podman-compose.1.html` (it delegates to `docker-compose` or `podman-compose`; which is needed on Ubuntu and whether Mint's apt has `podman-compose`); rootless by default.
  3. `docker compose run` reference — `https://docs.docker.com/reference/cli/docker/compose/run/`: confirm `--rm`, `-T`, `--workdir` (`-w`), that `run` builds a missing image, and that stdin is attached (mutmut_diffs feeds stdin).
  4. Compose file interpolation — `https://docs.docker.com/reference/compose-file/interpolation/`: `${PWD}` from the environment; the `volumes` short syntax `.:${PWD}`; `working_dir`.
  5. Licensing — already confirmed (spec); cite the same page.
  Decide the default order from what the research shows (a daemonless, rootless engine whose `compose` works out of the box is the better default *if* it does; otherwise Docker Engine). If the order changes from `("docker", "podman")`, edit both `RUNNERS` constants and the tests that assert order, in this task.

- [ ] **Step 3: Write `## Containers`** in `skills/orc-test/SKILL.md`, for a reader who has not seen the spec:

```markdown
## Containers

A project can run its whole toolchain in a container instead of on this machine (v23). The
record is a `compose.yaml` at the project root with a service named `orclab` — committed, so a
clone keeps it — whose Dockerfile installs the language's toolchain *and* every tool this
command needs, so a run inside never installs anything. Inside, the project is mounted at its
own host path, so every path in every report is valid on both sides:

```yaml
services:
  orclab:
    build: .
    volumes:
      - .:${PWD}
    working_dir: ${PWD}
```

Every command runs as `<engine> compose run --rm -T --workdir <dir> orclab <cmd>`; the first
line of the report says `detected: Python (in container)`. The engine, confirmed live
YYYY-MM-DD: <the research's answer — which is the default, why, the install line for each on
Ubuntu/Mint, rootless>. `.orclab/test.yaml` overrides per checkout: `container: false` runs on
the host here even though the repo is containerised; `runner: podman` (or `docker`) names the
engine. Nothing is ever silently run on the host instead: no engine on PATH prints
`<Language>: container runner not found — install docker or podman — skipped`; an image that
does not build prints its output and `container build failed — see above`, exit 1 — never the
host. The engine is a tool like any other: this command never installs it.
```

In `## What it never does`: "Install a tool — the container engine included — …".

- [ ] **Step 4: The docs page** — `docs/commands/orc-test.md`: in "What it's for" or after the language paragraph in "What you type", one paragraph: a project that chose to run in a container at scaffold has its tests run inside it, the report's first line says so, and the two `.orclab/test.yaml` lines to change that for this checkout. In "What it will never do without asking": the install bullet gains "— and that includes the container engine itself"; a new bullet: "It will never run a containerised project's tests on this machine instead when the container can't be used — it says why and stops for that project."

- [ ] **Step 5: Green, commit**

`python3 -m pytest -q hooks/scripts/tests/test_orc_test_skill.py hooks/scripts/tests/test_docs.py skills/orc-test/scripts/tests` → green.

```bash
git add skills/orc-test/SKILL.md docs/commands/orc-test.md hooks/scripts/tests/test_orc_test_skill.py skills/orc-test/scripts hooks/scripts
git commit -m "orc-test: Containers — the record, the override, the engine from live research; the page says a containerised project's tests run inside and are never run here instead (v23 §3)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Tasks 5–7: `## Containers` in every stack skill — shared procedure

**Section shape**, inserted immediately after `## Security — where security-discipline lands` (and its `###`s), before the next `##`:

```markdown
## Containers

Runs in a container: **yes** | **no** — confirmed live YYYY-MM-DD. <One sentence: what runs
inside and what cannot.>

<yes:> The `Dockerfile` `/orc-code` writes when the user says yes to the container question —
base image and tag from <the image's own registry page>, the toolchain, and every tool
`skills/orc-test/languages/<lang>.md` names (runner, coverage, mutation, audit):

```dockerfile
FROM <image>:<tag>
RUN <install lines>
```

The `compose.yaml` is the one in `skills/orc-test/SKILL.md`'s Containers section, unchanged.
What cannot happen inside: <GUI window / emulator / signing / …>, so <those steps> run on the
host. The proposal `/orc-code` makes for this stack's container question: <yes|no>, because
<reason>.

<no:> <Why — the platform requirement — and what part, if any, could run headless in a
container (a build without the editor, a test suite without a device), with its image, or
"nothing" said plainly.> `/orc-code` skips the container question for this stack.
```

Each task: read the skill and the spec §3; research the base image (the official image's Docker Hub or registry page: current tags, what it includes) and each `/orc-test` tool's install line in that image (the tool's own docs); write the section; extend `## Sources`; add the skill's directory name to `EXPECTED` in `hooks/scripts/tests/test_stack_containers.py`; run it; reader-side pass; commit. **Nothing from memory**; "not run here — the first project records it" on any Dockerfile that was not built on this machine (none can be until Task 9's install).

### Task 5: the facet test, and Python + web

**Files:** create `hooks/scripts/tests/test_stack_containers.py`; modify `skills/stack-python-desktop/SKILL.md`, `skills/stack-web/SKILL.md`.

- [ ] **Step 1: The test, red**

```python
# hooks/scripts/tests/test_stack_containers.py
"""v23: every stack skill says whether it runs in a container (spec §3)."""

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
HEADING = "## Containers"
EXPECTED = set()   # each stack task adds its skill's directory name here


@pytest.mark.parametrize("stack", sorted(EXPECTED))
def test_stack_skill_has_the_containers_section(stack):
    text = (ROOT / "skills" / stack / "SKILL.md").read_text()
    assert HEADING in text, stack
    body = text[text.index(HEADING):].split("\n## ", 1)[0]
    assert re.search(r"Runs in a container: \*\*(yes|no)\*\*", body), stack
    assert re.search(r"confirmed live 2026-\d\d-\d\d", body), stack
    if "**yes**" in body:
        assert "```dockerfile" in body and "FROM " in body, stack
    assert "container question" in body, stack


@pytest.mark.xfail(strict=True, reason="until Task 7 lands the ninth section; Task 7 removes this marker")
def test_every_stack_skill_is_expected():
    stacks = {p.parent.name for p in (ROOT / "skills").glob("stack-*/SKILL.md")}
    assert stacks == EXPECTED
```

- [ ] **Step 2: Research and write** — Python: the official `python` image (`https://hub.docker.com/_/python`, the `3.14`-line tag that exists), `pip install pytest pytest-cov mutmut pip-audit ruff` in the Dockerfile; what cannot: the PySide6 window (build and tests yes, running the app no — say what a headless Qt test needs, `QT_QPA_PLATFORM=offscreen`, confirmed on Qt's docs). Web: the Python back end as above plus Node — the official `node` image or `python` + NodeSource; one image or two services? (One image: the `/orc-test` chokepoint runs one service. Say how Node gets into the Python image, or vice-versa, from a primary source.) `npm`, `npx vitest`, `npm audit` need no extra install; oxlint via `npm`. Proposal for the question: "no" for both (toolchains common on a dev machine) — say so.
- [ ] **Step 3:** `EXPECTED = {"stack-python-desktop", "stack-web"}`; `python3 -m pytest -q hooks/scripts/tests/test_stack_containers.py` → 2 passed, 1 xfailed. Commit: `stack-python-desktop, stack-web: Containers — runs in one, the Dockerfile with every /orc-test tool (v23 §3)`.

### Task 6: the mobile stacks — Android half yes, iOS half no

**Files:** `skills/stack-android-native`, `stack-kotlin-multiplatform`, `stack-flutter`, `stack-react-native`; `EXPECTED |= {those four}`.

- [ ] **Research:** an Android SDK image that is not a personal one — Google's own `gcr.io/android`? (check `https://github.com/android/`, or the `cimg/android`/`thyrlian/android-sdk` question: prefer one maintained by a vendor or foundation; if only community images exist, say so and name the most maintained with its last-push date); JDK version per `stack-android-native`'s toolchain; `./gradlew` inside; what cannot: the emulator (KVM), device install, Play upload. Flutter: the official `ghcr.io/cirruslabs/flutter` or the Flutter docs' own container guidance (`https://docs.flutter.dev/get-started/install/linux` says nothing about containers? confirm); `flutter test`, `flutter build apk` inside, iOS half no. RN: `node` image + Android SDK for a local `expo prebuild`/`gradlew`; EAS Build is already a cloud container — say the relationship. KMP: same as Android + the iOS half "no". Proposal: "no" by default for all four (the Android SDK image is large and the emulator can't run inside; the case for yes is a machine with no SDK) — say the size.
- [ ] Commit: `stack-android-native, stack-kotlin-multiplatform, stack-flutter, stack-react-native: Containers — Android half runs in one, iOS half cannot (v23 §3)`.

### Task 7: iOS (no), Godot and Unity (headless), and closing the test

**Files:** `skills/stack-ios-native`, `stack-godot`, `stack-unity`; `EXPECTED |= {those three}`; remove the `xfail` marker.

- [ ] **Research:** iOS: **no** — macOS required (the skill's "The Mac requirement" section already says why; cite it, and say the cloud-Mac route is the container-shaped answer that exists). Godot: the official headless export — `https://docs.godotengine.org/en/stable/tutorials/export/exporting_projects.html#exporting-from-the-command-line` and whether an official image exists (`https://hub.docker.com/` search for godot: community only? say so); gdUnit4's own CI image or action; `GODOT_BIN` inside the image (Task 2's gdscript note). Unity: Unity's own licensing for a container (a personal licence activation inside an image — `https://docs.unity3d.com/Manual/` "Command line arguments", `-batchmode -nographics`, and the GameCI images `https://game.ci/docs/docker/versions` as the maintained community route; whether Unity's licence terms allow it — cite). Likely: Godot **yes** for headless export and tests, Unity **no** by default with the GameCI route named as "exists, not researched into a default".
- [ ] Remove `@pytest.mark.xfail(...)` from `test_every_stack_skill_is_expected`; `python3 -m pytest -q hooks/scripts/tests/test_stack_containers.py` → all green, no xfail. Commit: `stack-ios-native, stack-godot, stack-unity: Containers; all nine stack skills now carry the section (v23 §3)`.

---

### Task 8: `/orc-code` asks, writes the two files, verifies inside

**Files:**
- Modify: `skills/orc-code/SKILL.md` (New-Project Flow: new step 5 after Exposure; Starting point → 6, Scaffold → 7, Verify → 8, Report → 9; "Once all five" → "six"; Defaults Table paragraph's "generic step 6" → 7; quality-mode step 1's `3.4` reference unchanged)
- Modify: `docs/commands/orc-code.md`
- Modify: `hooks/scripts/tests/test_orc_code_skill.py`

- [ ] **Step 1: Pinning tests, red**

```python
def test_new_project_flow_asks_container_after_exposure_and_before_starting_point():
    flow = TEXT[TEXT.index("## New-Project Flow"):TEXT.index("## Add-to-Existing Flow")]
    q = "Run this project's toolchain in a container, so nothing has to be installed on this machine?"
    assert q in flow
    assert flow.index("didn't invite") < flow.index(q) < flow.index("minimal example")
    for phrase in ["compose.yaml", "`orclab`", "Dockerfile", "## Containers", "skips the container question",
                   "not what ships", "Once all six are answered"]:
        assert phrase in flow, phrase


def test_scaffold_and_verify_run_through_the_container():
    flow = TEXT[TEXT.index("## New-Project Flow"):TEXT.index("## Add-to-Existing Flow")]
    scaffold = flow[flow.index("**Scaffold**"):flow.index("**Verify**")]
    verify = flow[flow.index("**Verify**"):flow.index("**Report**")]
    assert "Dockerfile" in scaffold and "compose.yaml" in scaffold
    assert "compose run" in verify or "through the container" in verify
```

- [ ] **Step 2: The skill** — insert after step 4 (Exposure):

```markdown
5. **Container**: "Run this project's toolchain in a container, so nothing has to be installed
   on this machine?" The proposed answer is no — most toolchains are already on a dev machine —
   unless the stack skill's `## Containers` section says to propose yes for this stack (a
   toolchain unusual on a dev machine). A stack whose section says "Runs in a container:
   **no**" skips the container question; say why in one sentence from that section. The
   container is a development environment, not what ships: it holds the toolchain and every
   `/orc-test` tool, and what it produces is ordinary project files.
```

Scaffold (now step 7), after the security sentence: "If the answer to step 5 was yes, write the `Dockerfile` from the stack skill's `## Containers` section and the `compose.yaml` from `skills/orc-test/SKILL.md`'s `## Containers` — both at the project root, both committed; the compose service is named `orclab`, and that name is what `/orc-test` and `lint_on_write` recognise." Verify (now step 8): "When the project opted into a container, run the verification command *through* it — `<engine> compose run --rm -T --workdir <project> orclab <cmd>`, the same prefix `/orc-test` uses — so "exits cleanly" means clean in the environment that will be used; a build failure here is the report, not a reason to try the host." Renumber every cross-reference (grep `step 5`, `step 6`, `step 7`, `all five`).

- [ ] **Step 3: The page** — `docs/commands/orc-code.md`: the numbered "What it will ask you" list gains, after the exposure item: "Whether to run the project's tools inside a container, so nothing has to be installed on your machine — it proposes no unless the stack is one that's unusual to have installed, and skips the question for a stack that can't (iOS needs a Mac). The container is only where the tools live while you develop; what you ship is the ordinary project files." "What it changes", the New project bullet: "…and, if you said yes to the container, a `Dockerfile` and a `compose.yaml` at the project root, committed, that the test command and the on-write linter then use."

- [ ] **Step 4: Green, commit**

`python3 -m pytest -q hooks/scripts/tests/test_orc_code_skill.py hooks/scripts/tests/test_docs.py` → green; whole suite green.

```bash
git add skills/orc-code docs/commands/orc-code.md hooks/scripts/tests/test_orc_code_skill.py
git commit -m "orc-code: asks whether to run the toolchain in a container, writes the Dockerfile and compose.yaml, verifies through it (v23 §1)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: the live check on this machine, and the record

**Files:**
- Modify: `skills/orc-test/languages/python.md` (`Last real run:` gains the in-container line)
- Modify: `BACKLOG.md` via `/orc-todo add`

**Interfaces:**
- Consumes everything.

- [ ] **Step 1: The engine — direflail installs it.** Show the install command Task 4's research picked, e.g. `sudo apt install docker.io` and `sudo usermod -aG docker $USER` (then a new login), or `sudo apt install podman podman-compose`, **and stop: report NEEDS_CONTEXT with the exact command** — the controller relays it to direflail, who runs it and says when it is done. Nothing in this task runs `sudo`. When re-dispatched, confirm with `<engine> --version` and `<engine> compose version`.

- [ ] **Step 2: The scaffold, live** — in the scratchpad, follow this worktree's `skills/orc-code/SKILL.md` New-Project Flow with the answers: new, name `v23check`, app, web, exposure no, container **yes**, minimal example; stack `stack-web`'s Containers section for the Dockerfile. `git init` it. Record: the two files as written, the image build's time and size (`<engine> images`), and whether the build needed anything the section did not say.

- [ ] **Step 3: `/orc-test` through it** — from this worktree: `python3 skills/orc-test/scripts/run.py --cwd <scratch>/v23check detect`, then `run`, `coverage`, `analyze`, `audit`. Paste every report line: `detected: Python (in container)` (and JS/TS), the ✓ lines, the TCE line, the audit lines. Then write `container: false` into `<scratch>/v23check/.orclab/test.yaml` and run `detect` and `run` again — the lines without "(in container)" prove the override. Then remove that file, rename `docker`/`podman` off PATH for one run (`PATH=/usr/bin:/bin` minus the engine, or a `runner: podman` override when only docker is installed) and paste the `container runner not found` line. Then break the Dockerfile (`FROM no-such-image:0`), run `run`, paste the `container build failed — see above` line and its exit code.

- [ ] **Step 4: `lint_on_write` inside** — simulate the hook: `echo '{"tool_name":"Write","tool_input":{"file_path":"<scratch>/v23check/api/app.py"}}' | python3 hooks/scripts/lint_on_write.py` after writing a file with a nesting violation; paste its stderr, which must show the `compose run` prefix. Delete the scratch project.

- [ ] **Step 5: `python.md`** — `Last real run:` gains one line: the in-container `analyze` line from Step 3 with the date.

- [ ] **Step 6: BACKLOG, through `/orc-todo add`** (read `skills/backlog-discipline/SKILL.md` first; the allocator writes into the canonical checkout — copy each entry into this worktree's `BACKLOG.md` by hand; the controller discards the canonical draft at merge):
  1. `Containers as an opt-in development environment — v23 (RESOLVED 2026-09-20)`: the request quoted (direflail's "this shouldn't be just for php…"), the licensing facts and their page, the design in one paragraph per spec section, every live line from Steps 2–4 verbatim, the engine chosen and why.
  2. `A devcontainer.json beside the Dockerfile, for editors that attach to the container` — deferred; two sentences; cites spec §"Out of scope" and `build.dockerfile`.
  3. `Deploying a project as a container: a production image as an orc-package ingredient` — deferred; direflail 2026-09-20 quoted; two sentences on the shape (no test tools, the stack's Deployment section decides).
  4. Update #50 (PHP): append a layered note — "v24, after v23 (containers); its live check runs in the container".
  5. Update #33 (v18): append — "v18 §6 parked Docker; v23 unparked it as an opt-in dev environment, spec `2026-09-20-orclab-v23-containers-design.md`."

- [ ] **Step 7: Commit**

```bash
git add BACKLOG.md skills/orc-test/languages/python.md
git commit -m "BACKLOG: v23 containers shipped and verified live through a real engine; devcontainer and deploy-as-container deferred; PHP is v24

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-review against the spec

- **§1** — the question, the two files, the record, the override, Verify: Task 8 (question, files, Verify), Task 1 (record and override read), Task 4 (the `compose.yaml` text and the override documented).
- **§2** — `runner.run` prefix: Task 1; detection beside config: Task 1; `(in container)`: Task 2; what stays on the host: `run.py` is host Python, and `_dirty`'s `git status` goes through `runner.run_on_host` (Task 1 defines it, Task 2 Step 5 uses it, one test each) — a gap this self-review found and folded in. Runner missing / build failure: Task 2. `missing()` inside: Task 2. `lint_on_write`: Task 3. Gates: no change.
- **§3** — nine sections: Tasks 5–7; the engine section: Task 4.
- **§4** — tests: Tasks 1–3, 5, 8; docs: Tasks 4, 8; live check: Task 9 with the install shown, not run.
- **§5** — Task 9 Step 6.
- **Out of scope** — nothing here ships a container, writes a devcontainer, adds a service, or touches CI or PHP.
- **Placeholders** — `<engine>`, `<image>:<tag>`, `YYYY-MM-DD` are values the research or the live run produces inside the same task; none is "TBD".
- **Names** — `container.Container(root, runner)`, `container.detect`, `container.wrap`, `container.build_cmd`, `container.RUNNERS`, `container.SERVICE`, `runner.use`, `runner.active`, `runner.run_on_host`, `probe.which`, `probe.python_module`, `cli.ContainerUnavailable`, `lint_on_write.container_prefix` — spelled identically in every task that names them.
