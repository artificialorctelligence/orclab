# Orclab v16: `/orc-todo` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give direflail a command for looking at and manipulating the backlog, and stop two concurrent agents from taking the same number or building the same thing.

**Architecture:** Five separable components. Shared state (a lock, a counter, a lane record) lives in `$(git rev-parse --git-common-dir)/orclab/`, which resolves to the same directory from the main checkout and every worktree. An allocator hands out numbers and writes entries under that lock, into the *canonical* checkout's file, without committing. Two hooks make the state consulted without anyone remembering to. A separate cross-reference check lands in `orc-release`, because `RELEASING.md` numbers are positional and cannot use an allocator.

**Tech Stack:** Python 3.12 stdlib only — `os`, `json`, `re`, `pathlib`, `subprocess`, `argparse`, `contextlib`. pytest. No new dependency.

## Global Constraints

- Source of truth: `docs/superpowers/specs/2026-09-08-orclab-v16-orc-todo-design.md`.
- **Python 3.12 stdlib only. No new dependency.** PyYAML is already a dependency elsewhere but is not needed here.
- **Lock acquisition must be a single atomic operation** — `os.open(path, os.O_CREAT | os.O_EXCL)`. "Check then set" is a time-of-check-to-time-of-use race and is the standard way this pattern is broken. A test asserts the atomic call fails on an existing lock.
- **A stale lock is never auto-cleared**, even when its PID is provably dead. It is reported, and `/orc-todo lock clear` is the only thing that removes one.
- **The allocator never runs `git commit`.** It appends and stops.
- **The allocator never refuses because the canonical file is dirty.** It appends regardless.
- **One lock, not one per resource, and lane-agnostic.** Per-resource locks reintroduce AB-BA deadlock when one work item needs two numbers.
- **One allocator mechanism for both files, via a per-file descriptor** — never two implementations.
- Every new leaf of shared state degrades honestly: outside a git repository, or in a project with no `BACKLOG.md`, the affected feature reports itself unavailable and never invents a file.
- Backlog numbers are permanent and never reused. Nothing in this work may renumber an entry.
- Do **not** touch anything under `~/projects/orcshot`. Build fixtures in `tmp_path`.
- Run a skill's suite with `cd skills/<name>/scripts && python3 -m pytest tests/ -v`, and the hooks suite with `cd hooks/scripts && python3 -m pytest tests/ -v`.
- Every commit message ends with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `skills/orc-todo/scripts/orc_todo/state.py` | **New.** Shared-dir resolution, the atomic lock, staleness, counters | 1 |
| `skills/orc-todo/scripts/orc_todo/resources.py` | **New.** Per-file descriptors: scan, render, insert | 2 |
| `skills/orc-todo/scripts/orc_todo/allocate.py` | **New.** The allocator — ties 1 and 2 together under one lock hold | 3 |
| `skills/orc-todo/scripts/orc_todo/lanes.py` | **New.** The lane record and its spec-existence rule | 4 |
| `skills/orc-todo/scripts/orc_todo/cli.py` | **New.** Command surface | 5 |
| `skills/orc-todo/scripts/run.py`, `conftest.py`, `SKILL.md` | **New.** Entry point, pytest root, operator instructions | 5 |
| `hooks/scripts/orclab_shared.py` | **New.** The one copy of shared-dir resolution the hooks import | 6 |
| `hooks/scripts/lane_notice.py` | **New.** SessionStart: lanes in progress, locks, uncommitted entries | 6 |
| `hooks/scripts/backlog_guard.py` | **New.** PreToolUse: consent before a command discards uncommitted entries | 6 |
| `hooks/hooks.json` | Wire both hooks | 6 |
| `skills/orc-release/scripts/orc_release/steps.py` | The `RELEASING.md` cross-reference check | 7 |
| `skills/backlog-discipline/SKILL.md`, `skills/release-checklist/SKILL.md` | Prose changes the mechanism requires | 8 |
| `VERIFICATION.md`, `BACKLOG.md`, `.claude-plugin/*.json` | Close-out | 9 |

**On the duplicated shared-dir resolution (Task 6).** Hooks cannot import from a skill's `scripts/` directory — they run as standalone processes with their own working directory, and `${CLAUDE_PLUGIN_ROOT}/skills/orc-todo/scripts` is not on their path. `hooks/scripts/orclab_shared.py` is therefore a real second copy of ~15 lines. It is deliberate and its docstring must say so, naming `orc_todo/state.py` as the original. Do not "fix" it with a `sys.path` insertion into a skill directory: a hook that breaks when a skill moves is worse than fifteen duplicated lines.

---

### Task 1: Shared state and the lock

**Files:**
- Create: `skills/orc-todo/scripts/orc_todo/__init__.py` (empty), `skills/orc-todo/scripts/orc_todo/state.py`
- Create: `skills/orc-todo/scripts/conftest.py` (empty), `skills/orc-todo/scripts/tests/__init__.py` (do not create — tests dir needs no `__init__.py`, matching `orc-publish`)
- Test: `skills/orc-todo/scripts/tests/test_state.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `NotAGitRepo(Exception)`
  - `LockUnavailable(Exception)` — carries `.info` (a dict or `None`)
  - `git_common_dir(cwd=None) -> pathlib.Path` — absolute, raises `NotAGitRepo`
  - `shared_dir(cwd=None) -> pathlib.Path` — `<git-common-dir>/orclab`, created on demand
  - `canonical_root(cwd=None) -> pathlib.Path` — `<git-common-dir>/..`, the main checkout
  - `lock_path(cwd=None) -> pathlib.Path`
  - `lock_info(cwd=None) -> dict | None` — `{"pid", "started", "description", "alive", "age_seconds"}`
  - `held(description, cwd=None, timeout=10.0, poll=0.2)` — a context manager
  - `clear_lock(cwd=None) -> bool` — `True` if a lock was removed
  - `read_counters(cwd=None) -> dict`, `write_counters(mapping, cwd=None) -> None`

- [ ] **Step 1: Write the failing tests**

Create `skills/orc-todo/scripts/tests/test_state.py`:

```python
import json
import os
import subprocess

import pytest

from orc_todo import state


def make_repo(tmp_path):
    """A real git repo — these functions shell out to git, so a fake would prove nothing."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def test_shared_dir_is_inside_the_git_common_dir(tmp_path):
    repo = make_repo(tmp_path)
    assert state.shared_dir(repo) == (repo / ".git" / "orclab")
    assert state.shared_dir(repo).is_dir()


def test_a_worktree_resolves_to_the_same_shared_dir_as_its_main_checkout(tmp_path):
    """The whole design rests on this. Two checkouts, one shared directory - otherwise a lock
    locks two different files and protects nothing, which is what happened on 2026-09-08."""
    repo = make_repo(tmp_path)
    (repo / "f.txt").write_text("x")
    subprocess.run(["git", "-C", str(repo), "add", "f.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-qm", "init"], check=True)
    wt = tmp_path / "wt"
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", str(wt), "-b", "b"], check=True)
    assert state.shared_dir(wt) == state.shared_dir(repo)
    assert state.canonical_root(wt) == state.canonical_root(repo) == repo


def test_outside_a_git_repo_raises_rather_than_guessing(tmp_path):
    with pytest.raises(state.NotAGitRepo):
        state.git_common_dir(tmp_path)


def test_the_lock_is_acquired_and_released(tmp_path):
    repo = make_repo(tmp_path)
    with state.held("allocating #26", cwd=repo):
        assert state.lock_path(repo).exists()
        assert state.lock_info(repo)["description"] == "allocating #26"
    assert not state.lock_path(repo).exists()


def test_a_second_holder_times_out_and_names_the_first(tmp_path):
    repo = make_repo(tmp_path)
    with state.held("first holder", cwd=repo):
        with pytest.raises(state.LockUnavailable) as e:
            with state.held("second", cwd=repo, timeout=0.5, poll=0.1):
                pass
    assert e.value.info["description"] == "first holder"
    assert e.value.info["pid"] == os.getpid()


def test_acquisition_is_atomic_not_check_then_set(tmp_path):
    """O_CREAT|O_EXCL must be what fails, not a prior existence check - two processes can both
    pass a check and both proceed."""
    repo = make_repo(tmp_path)
    with state.held("holder", cwd=repo):
        with pytest.raises(FileExistsError):
            os.open(state.lock_path(repo), os.O_CREAT | os.O_EXCL | os.O_WRONLY)


def test_the_lock_is_released_even_when_the_body_raises(tmp_path):
    repo = make_repo(tmp_path)
    with pytest.raises(ValueError):
        with state.held("boom", cwd=repo):
            raise ValueError("boom")
    assert not state.lock_path(repo).exists()


def test_a_dead_holder_is_reported_as_not_alive_but_never_removed(tmp_path):
    """direflail's operational note: a lock found when none is expected is worth investigating,
    not clearing reflexively. Nothing auto-clears."""
    repo = make_repo(tmp_path)
    state.shared_dir(repo)
    state.lock_path(repo).write_text(json.dumps(
        {"pid": 999999, "started": "2026-09-08T00:00:00+00:00", "description": "ghost"}))
    info = state.lock_info(repo)
    assert info["alive"] is False
    assert info["description"] == "ghost"
    with pytest.raises(state.LockUnavailable):
        with state.held("mine", cwd=repo, timeout=0.3, poll=0.1):
            pass
    assert state.lock_path(repo).exists(), "a stale lock must never be auto-cleared"


def test_clear_lock_removes_it_and_reports_whether_there_was_one(tmp_path):
    repo = make_repo(tmp_path)
    state.shared_dir(repo)
    assert state.clear_lock(repo) is False
    state.lock_path(repo).write_text("{}")
    assert state.clear_lock(repo) is True
    assert not state.lock_path(repo).exists()


def test_a_corrupt_lock_file_still_reports_and_still_blocks(tmp_path):
    """A half-written lock must not read as 'no lock'."""
    repo = make_repo(tmp_path)
    state.shared_dir(repo)
    state.lock_path(repo).write_text("{not json")
    info = state.lock_info(repo)
    assert info is not None and info["pid"] is None and info["alive"] is True


def test_counters_round_trip_and_default_to_empty(tmp_path):
    repo = make_repo(tmp_path)
    assert state.read_counters(repo) == {}
    state.write_counters({"BACKLOG.md": 25}, repo)
    assert state.read_counters(repo) == {"BACKLOG.md": 25}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-todo/scripts && python3 -m pytest tests/test_state.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orc_todo'`

- [ ] **Step 3: Write the implementation**

Create `skills/orc-todo/scripts/orc_todo/__init__.py` as an empty file, and `skills/orc-todo/scripts/conftest.py` as an empty file (its only job is to make `pytest` treat `scripts/` as the rootdir so the suite runs from any working directory — the same reason `orc-publish` and `orc-release` each have one).

Create `skills/orc-todo/scripts/orc_todo/state.py`:

```python
"""Shared state for concurrent Orclab agents: where it lives, and the lock that guards it.

Everything here hangs off `git rev-parse --git-common-dir`, which resolves to the SAME
directory from the main checkout and from every worktree. That is the whole design: on
2026-09-08 two sessions each held their own copy of BACKLOG.md, so a lock on "the file" would
have locked two different files and protected nothing. See BACKLOG #22 and #25.

The directory is outside every working tree, so nothing here appears in a diff, merges, or
conflicts.
"""

import contextlib
import datetime
import json
import os
import pathlib
import subprocess
import time


class NotAGitRepo(Exception):
    """Raised rather than guessing a location. Every caller degrades honestly instead."""


class LockUnavailable(Exception):
    """The lock could not be taken. `.info` describes who holds it, when it can be read."""

    def __init__(self, message, info=None):
        super().__init__(message)
        self.info = info


def git_common_dir(cwd=None):
    """The shared .git directory, absolute. Identical from a worktree and its main checkout."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise NotAGitRepo(f"not a git repository: {cwd or os.getcwd()}") from e
    if not out:
        raise NotAGitRepo(f"not a git repository: {cwd or os.getcwd()}")
    base = pathlib.Path(cwd) if cwd else pathlib.Path.cwd()
    return (base / out).resolve()


def shared_dir(cwd=None):
    """<git-common-dir>/orclab, created on demand."""
    d = git_common_dir(cwd) / "orclab"
    d.mkdir(parents=True, exist_ok=True)
    return d


def canonical_root(cwd=None):
    """The main checkout - the working tree that owns the .git directory."""
    return git_common_dir(cwd).parent


def lock_path(cwd=None):
    return shared_dir(cwd) / "lock"


def _counters_path(cwd=None):
    return shared_dir(cwd) / "counters.json"


def _pid_alive(pid):
    if pid is None:
        return True  # unreadable holder: assume live, never invent grounds to clear it
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def lock_info(cwd=None):
    """Who holds the lock, or None when it is free.

    A corrupt or half-written lock reports pid None and alive True. Reading "no lock" from a
    file that exists would be the one failure mode a lock cannot have.
    """
    path = lock_path(cwd)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (ValueError, OSError):
        data = {}
    pid = data.get("pid")
    started = data.get("started")
    age = None
    if started:
        try:
            age = (
                datetime.datetime.now().astimezone()
                - datetime.datetime.fromisoformat(started)
            ).total_seconds()
        except ValueError:
            age = None
    return {
        "pid": pid,
        "started": started,
        "description": data.get("description"),
        "alive": _pid_alive(pid),
        "age_seconds": age,
    }


@contextlib.contextmanager
def held(description, cwd=None, timeout=10.0, poll=0.2):
    """Hold the lock for the duration of the block.

    Acquisition is one atomic os.open(O_CREAT|O_EXCL). "Check whether it is locked, then lock"
    is a time-of-check-to-time-of-use race - two processes both observe it free and both
    proceed - and is the standard way this pattern is broken.

    A stale lock (dead PID) is reported in the raised error, never removed. An unexpected lock
    is a signal worth investigating, not litter to sweep.
    """
    path = lock_path(cwd)
    deadline = time.monotonic() + timeout
    payload = json.dumps({
        "pid": os.getpid(),
        "started": datetime.datetime.now().astimezone().isoformat(),
        "description": description,
    })
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            if time.monotonic() >= deadline:
                info = lock_info(cwd)
                stale = info and not info["alive"]
                raise LockUnavailable(
                    ("lock appears stale - held by a process that is gone. "
                     "Investigate before clearing: /orc-todo lock status"
                     if stale else "lock is held by a running process"),
                    info,
                )
            time.sleep(poll)
            continue
        try:
            os.write(fd, payload.encode())
        finally:
            os.close(fd)
        break
    try:
        yield
    finally:
        with contextlib.suppress(FileNotFoundError):
            path.unlink()


def clear_lock(cwd=None):
    """Remove the lock. Returns True if one was there. Only ever called by an explicit request."""
    path = lock_path(cwd)
    if not path.exists():
        return False
    path.unlink()
    return True


def read_counters(cwd=None):
    path = _counters_path(cwd)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError):
        return {}  # a corrupt counter is recoverable: the file scan is the real source


def write_counters(mapping, cwd=None):
    _counters_path(cwd).write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd skills/orc-todo/scripts && python3 -m pytest tests/test_state.py -v`
Expected: PASS, 11 tests.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-todo/scripts/orc_todo/__init__.py skills/orc-todo/scripts/orc_todo/state.py skills/orc-todo/scripts/conftest.py skills/orc-todo/scripts/tests/test_state.py
git commit -m "$(cat <<'EOF'
orc-todo: shared state and an atomic lock

Everything hangs off git rev-parse --git-common-dir, which resolves to the
same directory from the main checkout and every worktree. That is the
design's load-bearing fact: on 2026-09-08 two sessions each held their own
copy of BACKLOG.md, so a lock on "the file" would have locked two
different files and protected nothing.

Acquisition is one atomic O_CREAT|O_EXCL open, with a test asserting that
is what fails rather than a prior existence check. A stale lock is
reported and never removed - an unexpected lock is a signal worth
investigating, not litter.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Resource descriptors

**Files:**
- Create: `skills/orc-todo/scripts/orc_todo/resources.py`
- Test: `skills/orc-todo/scripts/tests/test_resources.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `Resource` — a dataclass with `key`, `filename`, `heading`, `number_re`, `anchor`
  - `RESOURCES: dict[str, Resource]` — keys `"backlog"` and `"verification"`
  - `scan_max(text, resource) -> int` — 0 when the file holds no numbered sections
  - `render(resource, number, title, body) -> str`
  - `insert(text, resource, rendered) -> str`

- [ ] **Step 1: Write the failing tests**

Create `skills/orc-todo/scripts/tests/test_resources.py`:

```python
from orc_todo.resources import RESOURCES, insert, render, scan_max

BACKLOG = RESOURCES["backlog"]
VERIFICATION = RESOURCES["verification"]


def test_scan_max_finds_the_highest_backlog_number_not_the_last():
    """Entries are not necessarily in order, and gaps are expected and correct - a deleted
    entry's number is never reused."""
    text = "# Backlog\n\n## #7: a thing\n\nprose\n\n## #22: another\n\nprose\n\n## #9: third\n"
    assert scan_max(text, BACKLOG) == 22


def test_scan_max_finds_the_highest_scenario_number():
    text = "# V\n\n## Scenario 3: a\n\n## Scenario 45: b\n\n## Recording the result\n"
    assert scan_max(text, VERIFICATION) == 45


def test_scan_max_is_zero_on_a_file_with_no_entries():
    assert scan_max("# Backlog\n\nheader prose only\n", BACKLOG) == 0


def test_scan_max_ignores_a_number_inside_prose():
    """"see #40 above" in an entry body must not become the high-water mark."""
    text = "## #7: a thing\n\nrelated to #40 and #99, neither of which is a heading\n"
    assert scan_max(text, BACKLOG) == 7


def test_scan_max_ignores_a_resolved_suffix():
    text = "## #12: a thing (RESOLVED 2026-09-07)\n\nprose\n"
    assert scan_max(text, BACKLOG) == 12


def test_render_produces_the_house_heading_for_each_file():
    assert render(BACKLOG, 26, "a title", "body prose").startswith("## #26: a title\n")
    assert render(VERIFICATION, 46, "a title", "1. step").startswith("## Scenario 46: a title\n")


def test_render_separates_heading_from_body_with_a_blank_line():
    out = render(BACKLOG, 26, "t", "body prose")
    assert out == "## #26: t\n\nbody prose\n"


def test_insert_appends_a_backlog_entry_at_the_end():
    text = "# Backlog\n\n## #1: first\n\nprose\n"
    out = insert(text, BACKLOG, "## #2: second\n\nmore\n")
    assert out.endswith("## #2: second\n\nmore\n")
    assert "## #1: first" in out


def test_insert_puts_a_scenario_before_the_recording_section_not_at_the_end():
    """VERIFICATION.md ends with '## Recording the result'. Appending would put a new scenario
    after the closing section, where nobody running the script would reach it."""
    text = "# V\n\n## Scenario 1: a\n\nsteps\n\n## Recording the result\n\nnote it.\n"
    out = insert(text, VERIFICATION, "## Scenario 2: b\n\nsteps\n")
    assert out.index("## Scenario 2: b") < out.index("## Recording the result")
    assert out.endswith("note it.\n")


def test_insert_falls_back_to_appending_when_the_anchor_is_missing():
    text = "# V\n\n## Scenario 1: a\n\nsteps\n"
    out = insert(text, VERIFICATION, "## Scenario 2: b\n\nsteps\n")
    assert out.endswith("## Scenario 2: b\n\nsteps\n")


def test_insert_leaves_exactly_one_blank_line_between_sections():
    text = "# Backlog\n\n## #1: first\n\nprose\n"
    out = insert(text, BACKLOG, "## #2: second\n\nmore\n")
    assert "prose\n\n## #2: second" in out
    assert "prose\n\n\n" not in out
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-todo/scripts && python3 -m pytest tests/test_resources.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orc_todo.resources'`

- [ ] **Step 3: Write the implementation**

Create `skills/orc-todo/scripts/orc_todo/resources.py`:

```python
"""The two numbered resources, described rather than special-cased.

One allocator serves both files. What differs between them is captured here as data - the
heading shape, how a number is recognised, and where a new section goes. A second
implementation for the second file would be the duplication BACKLOG #22 warns about in a
different costume.

RELEASING.md is deliberately absent. Its step numbers are positional, not identities:
release-checklist requires renumbering when a step is inserted mid-document, so there is no
"next number" to hand out. Its real gap - prose cross-references surviving a renumber - is a
check in orc_release/steps.py instead.
"""

import dataclasses
import re


@dataclasses.dataclass(frozen=True)
class Resource:
    key: str
    filename: str
    heading: str          # format string with {n} and {title}
    number_re: str        # must anchor at line start; group 1 is the number
    anchor: str | None    # insert before this line; None or absent means append


RESOURCES = {
    "backlog": Resource(
        key="backlog",
        filename="BACKLOG.md",
        heading="## #{n}: {title}",
        number_re=r"^## #(\d+):",
        anchor=None,
    ),
    "verification": Resource(
        key="verification",
        filename="VERIFICATION.md",
        heading="## Scenario {n}: {title}",
        number_re=r"^## Scenario (\d+):",
        anchor="## Recording the result",
    ),
}


def scan_max(text, resource):
    """The highest number appearing as a real heading. 0 when there are none.

    Anchored at line start on purpose: an entry body citing "#40" must not become the
    high-water mark, and entries are not stored in numerical order - gaps are expected and
    correct, since a deleted entry's number is never reused.
    """
    numbers = [int(m) for m in re.findall(resource.number_re, text, flags=re.MULTILINE)]
    return max(numbers) if numbers else 0


def render(resource, number, title, body):
    """One section in the file's house format."""
    return resource.heading.format(n=number, title=title) + "\n\n" + body.rstrip("\n") + "\n"


def insert(text, resource, rendered):
    """Place a rendered section, at the resource's anchor or at the end of the file."""
    block = rendered.rstrip("\n") + "\n"
    if resource.anchor:
        at = text.find("\n" + resource.anchor)
        if at != -1:
            head = text[: at + 1].rstrip("\n") + "\n\n"
            return head + block + "\n" + text[at + 1 :]
    return text.rstrip("\n") + "\n\n" + block
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd skills/orc-todo/scripts && python3 -m pytest tests/test_resources.py -v`
Expected: PASS, 11 tests.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-todo/scripts/orc_todo/resources.py skills/orc-todo/scripts/tests/test_resources.py
git commit -m "$(cat <<'EOF'
orc-todo: describe the two numbered resources as data

One allocator serves BACKLOG.md and VERIFICATION.md. What differs between
them - heading shape, number recognition, insertion anchor - is a
descriptor rather than a branch, because a second implementation for the
second file is the duplication BACKLOG #22 warns about in a different
costume.

Number recognition is anchored at line start: an entry body citing "#40"
must not become the high-water mark, and entries are not in numerical
order, since a deleted number is never reused.

VERIFICATION.md inserts before its trailing "## Recording the result"
section rather than appending, or a new scenario would land after the
closing section where nobody running the script would reach it.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: The allocator

**Files:**
- Create: `skills/orc-todo/scripts/orc_todo/allocate.py`
- Test: `skills/orc-todo/scripts/tests/test_allocate.py`

**Interfaces:**
- Consumes: `state.held`, `state.canonical_root`, `state.read_counters`, `state.write_counters`, `state.LockUnavailable` (Task 1); `RESOURCES`, `scan_max`, `render`, `insert` (Task 2).
- Produces:
  - `ResourceMissing(Exception)`
  - `canonical_file(resource, cwd=None) -> pathlib.Path`
  - `next_number(resource, cwd=None) -> int` — **must be called inside a held lock**
  - `allocate(resource_key, title, body, cwd=None, timeout=10.0) -> int`

- [ ] **Step 1: Write the failing tests**

Create `skills/orc-todo/scripts/tests/test_allocate.py`:

```python
import multiprocessing
import subprocess

import pytest

from orc_todo import allocate as alloc
from orc_todo import state


def make_repo(tmp_path, backlog="# Backlog\n\n## #22: last one\n\nprose\n"):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "BACKLOG.md").write_text(backlog)
    return tmp_path


def test_allocate_returns_the_next_number_and_writes_the_entry(tmp_path):
    repo = make_repo(tmp_path)
    n = alloc.allocate("backlog", "a new finding", "real prose here", cwd=repo)
    assert n == 23
    text = (repo / "BACKLOG.md").read_text()
    assert "## #23: a new finding" in text
    assert "real prose here" in text
    assert "## #22: last one" in text, "existing entries must be untouched"


def test_allocate_never_commits(tmp_path):
    """Committing means running git in a checkout the agent does not own, sweeping up whatever
    uncommitted work is in that file."""
    repo = make_repo(tmp_path)
    alloc.allocate("backlog", "t", "b", cwd=repo)
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "BACKLOG.md"],
        capture_output=True, text=True, check=True).stdout
    assert status.strip(), "the entry must be left uncommitted"


def test_allocate_appends_even_when_the_file_is_dirty(tmp_path):
    """The earlier design refused here, which blocks an agent from recording a finding until a
    human intervenes. It appends instead; the guard protects the entry."""
    repo = make_repo(tmp_path)
    (repo / "BACKLOG.md").write_text("# Backlog\n\n## #22: last one\n\nEDITED BY HAND\n")
    alloc.allocate("backlog", "t", "b", cwd=repo)
    text = (repo / "BACKLOG.md").read_text()
    assert "EDITED BY HAND" in text, "the human's uncommitted edit must survive"
    assert "## #23: t" in text


def test_the_counter_is_updated_so_the_next_call_does_not_rescan_from_zero(tmp_path):
    repo = make_repo(tmp_path)
    alloc.allocate("backlog", "one", "b", cwd=repo)
    assert state.read_counters(repo)["backlog"] == 23


def test_a_lost_counter_self_heals_from_the_file(tmp_path):
    """A fresh clone or a cleaned .git loses the counter. The file is still there, so a lost
    counter must never reissue a number."""
    repo = make_repo(tmp_path)
    alloc.allocate("backlog", "one", "b", cwd=repo)
    state.write_counters({}, repo)
    assert alloc.allocate("backlog", "two", "b", cwd=repo) == 24


def test_a_counter_ahead_of_the_file_wins(tmp_path):
    """The reverse case: an entry was deleted, so the file's maximum went backwards. The
    counter must hold the line - backlog numbers are never reused."""
    repo = make_repo(tmp_path)
    state.write_counters({"backlog": 40}, repo)
    assert alloc.allocate("backlog", "t", "b", cwd=repo) == 41


def test_a_missing_resource_file_raises_rather_than_creating_one(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    with pytest.raises(alloc.ResourceMissing):
        alloc.allocate("backlog", "t", "b", cwd=tmp_path)


def test_allocation_fails_cleanly_when_the_lock_is_held(tmp_path):
    repo = make_repo(tmp_path)
    with state.held("someone else", cwd=repo):
        with pytest.raises(state.LockUnavailable):
            alloc.allocate("backlog", "t", "b", cwd=repo, timeout=0.4)


def _child(repo, title, out):
    try:
        out.put(alloc.allocate("backlog", title, "body", cwd=repo, timeout=30.0))
    except Exception as e:  # surface it rather than hanging the parent on an empty queue
        out.put(f"ERROR {e!r}")


def test_two_real_concurrent_processes_get_different_numbers(tmp_path):
    """The actual race, with two real processes - not two sequential calls. This is the test
    that would have failed on 2026-09-08, when both sessions took #23 and #24.
    """
    repo = make_repo(tmp_path)
    q = multiprocessing.Queue()
    procs = [multiprocessing.Process(target=_child, args=(repo, f"entry {i}", q))
             for i in range(2)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=60)
    results = sorted(q.get() for _ in procs)
    assert results == [23, 24], f"got {results}"
    text = (repo / "BACKLOG.md").read_text()
    assert "## #23:" in text and "## #24:" in text, "both entries must land"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-todo/scripts && python3 -m pytest tests/test_allocate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orc_todo.allocate'`

- [ ] **Step 3: Write the implementation**

Create `skills/orc-todo/scripts/orc_todo/allocate.py`:

```python
"""Allocate a number and write the entry, in one lock hold.

The allocator owns the write rather than handing out a number and trusting the caller, because
there is then nothing to bypass: an agent cannot take a number and forget to use it, or write
without taking one.

It stops short of committing. Correctness does not need it - every agent reads the same
canonical file, so an entry is visible the instant it is written - and committing would mean
running git in a checkout the agent does not own, sweeping whatever uncommitted work is in that
file into a commit that claims to be a backlog entry. The durability that buys is paid for
instead by hooks/scripts/backlog_guard.py, which asks before anything discards an uncommitted
entry.
"""

from . import state
from .resources import RESOURCES, insert, render, scan_max


class ResourceMissing(Exception):
    """The project has no such file. Never create one - a project without a BACKLOG.md has
    not opted into having one."""


def canonical_file(resource, cwd=None):
    """The one real file every agent reaches, in the main checkout - not the caller's copy."""
    return state.canonical_root(cwd) / resource.filename


def next_number(resource, cwd=None):
    """max(stored counter, file scan) + 1. Call only inside a held lock.

    Both sources are consulted because each covers the other's failure. A lost counter (fresh
    clone, cleaned .git) would reissue numbers the file already has; a file whose highest entry
    was deleted would reissue a number the counter remembers, and backlog numbers are permanent
    and never reused.
    """
    path = canonical_file(resource, cwd)
    if not path.exists():
        raise ResourceMissing(f"{resource.filename} not found at {path}")
    stored = state.read_counters(cwd).get(resource.key, 0)
    return max(stored, scan_max(path.read_text(), resource)) + 1


def allocate(resource_key, title, body, cwd=None, timeout=10.0):
    """Allocate the next number, write the entry into the canonical file, return the number."""
    resource = RESOURCES[resource_key]
    path = canonical_file(resource, cwd)
    if not path.exists():
        raise ResourceMissing(f"{resource.filename} not found at {path}")
    with state.held(f"allocating a {resource.key} number", cwd=cwd, timeout=timeout):
        number = next_number(resource, cwd)
        path.write_text(insert(path.read_text(), resource, render(resource, number, title, body)))
        counters = state.read_counters(cwd)
        counters[resource.key] = number
        state.write_counters(counters, cwd)
    return number
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd skills/orc-todo/scripts && python3 -m pytest tests/test_allocate.py -v`
Expected: PASS, 9 tests. The concurrency test is the slowest; it should still finish in seconds.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-todo/scripts/orc_todo/allocate.py skills/orc-todo/scripts/tests/test_allocate.py
git commit -m "$(cat <<'EOF'
orc-todo: the allocator, which owns the write but not the commit

Allocates a number and writes the entry in one lock hold. Owning the write
rather than handing out a number means there is nothing to bypass: an
agent cannot take a number and forget to use it, or write without taking
one.

It never commits. Every agent reads the same canonical file, so an entry
is visible the instant it is written, and committing would mean running
git in a checkout the agent does not own, sweeping its owner's uncommitted
work into a commit claiming to be a backlog entry. It also never refuses
on a dirty file - a refusal blocks an agent from recording a finding until
a human intervenes.

The number is max(counter, file scan) + 1 because each source covers the
other's failure: a lost counter would reissue numbers the file has, and a
file whose highest entry was deleted would reissue a number the counter
remembers - and backlog numbers are permanent.

Tested with two real concurrent processes, not two sequential calls. That
is the test that would have failed on 2026-09-08.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: The lane record

**Files:**
- Create: `skills/orc-todo/scripts/orc_todo/lanes.py`
- Test: `skills/orc-todo/scripts/tests/test_lanes.py`

**Interfaces:**
- Consumes: `state.shared_dir`, `state.held`, `state.canonical_root` (Task 1).
- Produces:
  - `UnspeccedItem(Exception)` — carries `.item`
  - `LaneMissing(Exception)`
  - `SPEC_DIRS = ("docs/superpowers/specs", "docs/superpowers/plans")`
  - `spec_files(item, cwd=None) -> list[pathlib.Path]`
  - `read_lanes(cwd=None) -> dict`
  - `create_lane(name, items, cwd=None) -> dict`
  - `modify_lane(name, items, cwd=None) -> dict`
  - `delete_lane(name, cwd=None) -> None`
  - `set_current(name, item, cwd=None) -> dict` — `item=None` clears it
  - `in_progress(cwd=None) -> list[dict]` — `{"lane", "item", "started"}`

- [ ] **Step 1: Write the failing tests**

Create `skills/orc-todo/scripts/tests/test_lanes.py`:

```python
import subprocess

import pytest

from orc_todo import lanes


def make_repo(tmp_path, specs=("v13", "v14", "v15")):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    d = tmp_path / "docs" / "superpowers" / "specs"
    d.mkdir(parents=True)
    for s in specs:
        (d / f"2026-09-08-orclab-{s}-something-design.md").write_text("# spec\n")
    return tmp_path


def test_a_lane_holds_its_items_in_order(tmp_path):
    repo = make_repo(tmp_path)
    lane = lanes.create_lane("B", ["v14", "v15"], cwd=repo)
    assert lane["items"] == ["v14", "v15"]
    assert lanes.read_lanes(repo)["B"]["items"] == ["v14", "v15"]


def test_an_unspecced_item_is_refused_and_names_itself(tmp_path):
    """The refusal is load-bearing, not pedantry: #17 alone is ambiguous because speccing it
    could produce either v14 or v15."""
    repo = make_repo(tmp_path)
    with pytest.raises(lanes.UnspeccedItem) as e:
        lanes.create_lane("A", ["v13", "v99"], cwd=repo)
    assert e.value.item == "v99"
    assert "A" not in lanes.read_lanes(repo), "a refused lane must not be half-created"


def test_a_plan_counts_as_a_spec_for_lane_membership(tmp_path):
    repo = make_repo(tmp_path, specs=())
    d = repo / "docs" / "superpowers" / "plans"
    d.mkdir(parents=True)
    (d / "2026-09-08-orclab-v12-artifact-preflight.md").write_text("# plan\n")
    assert lanes.create_lane("A", ["v12"], cwd=repo)["items"] == ["v12"]


def test_modify_replaces_the_item_list_so_it_can_reorder_add_and_drop(tmp_path):
    repo = make_repo(tmp_path)
    lanes.create_lane("B", ["v14", "v15"], cwd=repo)
    assert lanes.modify_lane("B", ["v15", "v13"], cwd=repo)["items"] == ["v15", "v13"]


def test_modify_on_a_missing_lane_raises(tmp_path):
    repo = make_repo(tmp_path)
    with pytest.raises(lanes.LaneMissing):
        lanes.modify_lane("nope", ["v13"], cwd=repo)


def test_delete_removes_the_lane(tmp_path):
    repo = make_repo(tmp_path)
    lanes.create_lane("B", ["v14"], cwd=repo)
    lanes.delete_lane("B", cwd=repo)
    assert "B" not in lanes.read_lanes(repo)


def test_modify_keeps_current_when_it_survives_and_clears_it_when_it_does_not(tmp_path):
    repo = make_repo(tmp_path)
    lanes.create_lane("B", ["v14", "v15"], cwd=repo)
    lanes.set_current("B", "v14", cwd=repo)
    assert lanes.modify_lane("B", ["v14", "v13"], cwd=repo)["current"] == "v14"
    assert lanes.modify_lane("B", ["v13", "v15"], cwd=repo)["current"] is None


def test_in_progress_reports_only_lanes_with_a_current_item(tmp_path):
    repo = make_repo(tmp_path)
    lanes.create_lane("A", ["v13"], cwd=repo)
    lanes.create_lane("B", ["v14"], cwd=repo)
    lanes.set_current("A", "v13", cwd=repo)
    running = lanes.in_progress(repo)
    assert [r["lane"] for r in running] == ["A"]
    assert running[0]["item"] == "v13" and running[0]["started"]


def test_setting_current_to_an_item_not_in_the_lane_raises(tmp_path):
    repo = make_repo(tmp_path)
    lanes.create_lane("A", ["v13"], cwd=repo)
    with pytest.raises(lanes.LaneMissing):
        lanes.set_current("A", "v15", cwd=repo)


def test_read_lanes_is_empty_rather_than_failing_when_nothing_exists(tmp_path):
    repo = make_repo(tmp_path)
    assert lanes.read_lanes(repo) == {}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-todo/scripts && python3 -m pytest tests/test_lanes.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orc_todo.lanes'`

- [ ] **Step 3: Write the implementation**

Create `skills/orc-todo/scripts/orc_todo/lanes.py`:

```python
"""Lanes: N ordered lists of work that run concurrently. A record, never a runner.

Nothing here launches a session, supervises a process, or handles a crash. Ordering and mutual
exclusion are deliberately separate mechanisms - a lane needs no lock to be ordered, and the
lock needs no lane to be correct (BACKLOG #22).

A lane item is a design spec or an implementation plan, named vNN. Not a backlog number: #12 is
a resolved entry about publish pipeline gaps while v12 is the preflight work, and the real
mapping is many-to-many - v14 and v15 both derive primarily from #17.
"""

import datetime
import json
import re

from . import state

SPEC_DIRS = ("docs/superpowers/specs", "docs/superpowers/plans")


class UnspeccedItem(Exception):
    """No spec or plan exists for this item, so it cannot join a lane yet."""

    def __init__(self, message, item):
        super().__init__(message)
        self.item = item


class LaneMissing(Exception):
    """No such lane, or no such item within it."""


def _lanes_path(cwd=None):
    return state.shared_dir(cwd) / "lanes.json"


def spec_files(item, cwd=None):
    """Every spec or plan file naming this item, e.g. v13 -> .../...-orclab-v13-...md."""
    root = state.canonical_root(cwd)
    pattern = re.compile(rf"(^|[-_]){re.escape(item)}([-_.]|$)")
    found = []
    for d in SPEC_DIRS:
        directory = root / d
        if directory.is_dir():
            found.extend(p for p in sorted(directory.glob("*.md")) if pattern.search(p.stem))
    return found


def _require_specced(items, cwd=None):
    for item in items:
        if not spec_files(item, cwd):
            raise UnspeccedItem(
                f"'{item}' has no spec or plan under {' or '.join(SPEC_DIRS)}. "
                "Spec it first - an unspecced item is genuinely ambiguous.",
                item,
            )


def read_lanes(cwd=None):
    path = _lanes_path(cwd)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError):
        return {}


def _write_lanes(data, cwd=None):
    _lanes_path(cwd).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def create_lane(name, items, cwd=None):
    _require_specced(items, cwd)   # validate before taking the lock, and before any write
    with state.held(f"creating lane {name}", cwd=cwd):
        data = read_lanes(cwd)
        data[name] = {"items": list(items), "current": None, "started": None}
        _write_lanes(data, cwd)
    return data[name]


def modify_lane(name, items, cwd=None):
    """Replace the item list. Covers reorder, add and drop in one operation.

    A current item that survives the change stays current; one that was dropped is cleared,
    because a lane cannot be in progress on something it no longer contains.
    """
    _require_specced(items, cwd)
    with state.held(f"modifying lane {name}", cwd=cwd):
        data = read_lanes(cwd)
        if name not in data:
            raise LaneMissing(f"no lane named '{name}'")
        lane = data[name]
        lane["items"] = list(items)
        if lane.get("current") not in items:
            lane["current"] = None
            lane["started"] = None
        _write_lanes(data, cwd)
    return data[name]


def delete_lane(name, cwd=None):
    with state.held(f"deleting lane {name}", cwd=cwd):
        data = read_lanes(cwd)
        if name not in data:
            raise LaneMissing(f"no lane named '{name}'")
        del data[name]
        _write_lanes(data, cwd)


def set_current(name, item, cwd=None):
    """Mark which item a lane is working on. item=None clears it."""
    with state.held(f"advancing lane {name}", cwd=cwd):
        data = read_lanes(cwd)
        if name not in data:
            raise LaneMissing(f"no lane named '{name}'")
        lane = data[name]
        if item is not None and item not in lane["items"]:
            raise LaneMissing(f"lane '{name}' does not contain '{item}'")
        lane["current"] = item
        lane["started"] = datetime.datetime.now().astimezone().isoformat() if item else None
        _write_lanes(data, cwd)
    return data[name]


def in_progress(cwd=None):
    """Every lane currently working on something. This is what stops a duplicate build."""
    return [
        {"lane": name, "item": lane["current"], "started": lane.get("started")}
        for name, lane in sorted(read_lanes(cwd).items())
        if lane.get("current")
    ]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd skills/orc-todo/scripts && python3 -m pytest tests/test_lanes.py -v`
Expected: PASS, 10 tests.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-todo/scripts/orc_todo/lanes.py skills/orc-todo/scripts/tests/test_lanes.py
git commit -m "$(cat <<'EOF'
orc-todo: the lane record

N ordered lists of work that run concurrently. A record, never a runner -
nothing launches a session, supervises a process, or handles a crash,
which is what keeps this out of the daemon territory BACKLOG #22 rules
out.

A lane item is a spec or plan named vNN, not a backlog number: #12 is a
resolved publish-pipeline entry while v12 is the preflight work, and the
real mapping is many-to-many. An unspecced item is refused, because #17
alone is ambiguous - speccing it could produce either v14 or v15.

Ordering and exclusion stay separate: a lane needs no lock to be ordered.
The lock appears here only to keep concurrent writes to lanes.json from
losing each other.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: The CLI and SKILL.md

**Files:**
- Create: `skills/orc-todo/scripts/orc_todo/cli.py`, `skills/orc-todo/scripts/run.py`, `skills/orc-todo/SKILL.md`
- Test: `skills/orc-todo/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: everything from Tasks 1–4.
- Produces: `main(argv=None) -> int`, and `run.py` as the entry point SKILL.md invokes.

**Command surface** — implement exactly this:

```
list                      open entries, one line each, then lanes if any exist
show <n>                  one entry in full
add <resource> <title>    body is read from stdin; prints the allocated number
remove <n>                delete a backlog entry; never renumbers
lane list
lane create <name> <items>        items comma-separated, e.g. v13,v14
lane modify <name> <items>
lane delete <name>
lane current <name> <item|->      '-' clears
lock status
lock clear
```

`add` takes its body on stdin rather than as an argument: a real entry is paragraphs, and shell
quoting for multi-paragraph prose is how a stub gets written instead.

- [ ] **Step 1: Write the failing tests**

Create `skills/orc-todo/scripts/tests/test_cli.py`:

```python
import subprocess

from orc_todo import lanes, state
from orc_todo.cli import main

BACKLOG = """# Backlog

## #7: an open one

prose about it

## #12: a closed one (RESOLVED 2026-09-07)

prose

## #22: another open one

more prose
"""


def make_repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "BACKLOG.md").write_text(BACKLOG)
    d = tmp_path / "docs" / "superpowers" / "specs"
    d.mkdir(parents=True)
    (d / "2026-09-08-orclab-v13-x-design.md").write_text("# s\n")
    (d / "2026-09-08-orclab-v14-y-design.md").write_text("# s\n")
    return tmp_path


def run(args, repo, capsys, stdin=None, monkeypatch=None):
    if monkeypatch is not None and stdin is not None:
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(stdin))
    # --cwd is a top-level option, so it MUST precede the subcommand. argparse assigns
    # options after a subcommand to that subparser, and this one is not defined there.
    code = main(["--cwd", str(repo), *args])
    return code, capsys.readouterr().out


def test_list_shows_open_entries_one_line_each_and_marks_resolved_ones_absent(tmp_path, capsys):
    repo = make_repo(tmp_path)
    code, out = run(["list"], repo, capsys)
    assert code == 0
    assert "#7: an open one" in out
    assert "#22: another open one" in out
    assert "#12" not in out, "resolved entries are not open work"
    assert "prose about it" not in out, "list is one line per entry, not the file"


def test_list_marks_a_partially_addressed_entry(tmp_path, capsys):
    """Partially-addressed entries are still open work, but knowing half of one is already
    done changes whether you pick it up."""
    repo = make_repo(tmp_path)
    (repo / "BACKLOG.md").write_text(
        BACKLOG + "\n## #30: half done (PARTIALLY ADDRESSED 2026-09-08 - rest still open)\n\nprose\n")
    code, out = run(["list"], repo, capsys)
    assert code == 0
    assert "#30" in out and "[partial]" in out


def test_show_prints_one_entry_in_full(tmp_path, capsys):
    repo = make_repo(tmp_path)
    code, out = run(["show", "7"], repo, capsys)
    assert code == 0
    assert "prose about it" in out
    assert "another open one" not in out


def test_show_on_a_missing_entry_is_an_error_not_an_empty_success(tmp_path, capsys):
    repo = make_repo(tmp_path)
    code, _ = run(["show", "999"], repo, capsys)
    assert code == 1


def test_add_allocates_and_writes_the_entry(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    code, out = run(["add", "backlog", "a real finding"], repo, capsys,
                    stdin="A genuine paragraph of context.\n", monkeypatch=monkeypatch)
    assert code == 0
    assert "23" in out
    assert "## #23: a real finding" in (repo / "BACKLOG.md").read_text()


def test_add_refuses_an_empty_body(tmp_path, capsys, monkeypatch):
    """backlog-discipline requires a real paragraph, never a stub. The command is a front door
    to that rule, not a way around it."""
    repo = make_repo(tmp_path)
    code, _ = run(["add", "backlog", "t"], repo, capsys, stdin="   \n", monkeypatch=monkeypatch)
    assert code == 1
    assert "## #23" not in (repo / "BACKLOG.md").read_text()


def test_remove_deletes_the_section_and_renumbers_nothing(tmp_path, capsys):
    repo = make_repo(tmp_path)
    code, _ = run(["remove", "7"], repo, capsys)
    assert code == 0
    text = (repo / "BACKLOG.md").read_text()
    assert "## #7:" not in text
    assert "## #12:" in text and "## #22:" in text, "no other entry may be renumbered"


def test_lane_create_and_list(tmp_path, capsys):
    repo = make_repo(tmp_path)
    assert run(["lane", "create", "B", "v13,v14"], repo, capsys)[0] == 0
    code, out = run(["lane", "list"], repo, capsys)
    assert code == 0 and "B" in out and "v13" in out


def test_lane_create_with_an_unspecced_item_fails_and_says_which(tmp_path, capsys):
    repo = make_repo(tmp_path)
    code, out = run(["lane", "create", "A", "v13,v99"], repo, capsys)
    assert code == 1
    assert "v99" in out


def test_list_shows_lanes_when_they_exist_and_omits_the_section_when_they_do_not(tmp_path, capsys):
    repo = make_repo(tmp_path)
    assert "lane" not in run(["list"], repo, capsys)[1].lower()
    run(["lane", "create", "B", "v13"], repo, capsys)
    assert "B" in run(["list"], repo, capsys)[1]


def test_lock_status_reports_free_and_held(tmp_path, capsys):
    repo = make_repo(tmp_path)
    assert "not held" in run(["lock", "status"], repo, capsys)[1].lower()
    with state.held("a real holder", cwd=repo):
        assert "a real holder" in run(["lock", "status"], repo, capsys)[1]


def test_lock_clear_removes_a_lock_and_says_so_when_there_was_none(tmp_path, capsys):
    repo = make_repo(tmp_path)
    assert run(["lock", "clear"], repo, capsys)[0] == 0
    state.shared_dir(repo)
    state.lock_path(repo).write_text("{}")
    assert run(["lock", "clear"], repo, capsys)[0] == 0
    assert not state.lock_path(repo).exists()


def test_outside_a_git_repo_it_reports_unavailable_rather_than_crashing(tmp_path, capsys):
    code, out = run(["list"], tmp_path, capsys)
    assert code == 1
    assert "git" in out.lower()


def test_a_project_with_no_backlog_is_told_so_and_none_is_created(tmp_path, capsys):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    code, out = run(["list"], tmp_path, capsys)
    assert code == 1
    assert "BACKLOG.md" in out
    assert not (tmp_path / "BACKLOG.md").exists()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-todo/scripts && python3 -m pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orc_todo.cli'`

- [ ] **Step 3: Write the implementation**

Create `skills/orc-todo/scripts/orc_todo/cli.py`:

```python
"""/orc-todo: look at and manipulate the backlog, and see the lanes.

Everything the lock and the allocator do is invisible from here on purpose. This is the only
part of v16 with a user in front of it.
"""

import argparse
import pathlib
import re
import sys

from . import lanes as lanemod
from . import state
from .allocate import ResourceMissing, allocate
from .resources import RESOURCES

RESOLVED = re.compile(r"\(RESOLVED\b")
PARTIAL = re.compile(r"\(PARTIALLY ADDRESSED\b")


def _backlog_path(cwd):
    return state.canonical_root(cwd) / "BACKLOG.md"


def _sections(text):
    """(number, title, body) for every backlog entry, in file order."""
    parts = re.split(r"^(## #(\d+): .*)$", text, flags=re.MULTILINE)
    out = []
    for i in range(1, len(parts), 3):
        heading, number, body = parts[i], int(parts[i + 1]), parts[i + 2]
        out.append((number, heading[len(f"## #{number}: "):].strip(), body))
    return out


def _read_backlog(cwd):
    path = _backlog_path(cwd)
    if not path.exists():
        raise ResourceMissing(f"no BACKLOG.md in this project (looked in {path.parent})")
    return path.read_text()


def cmd_list(args):
    text = _read_backlog(args.cwd)
    open_entries = [(n, t) for n, t, _ in _sections(text) if not RESOLVED.search(t)]
    if not open_entries:
        print("no open entries")
    for n, title in sorted(open_entries):
        mark = " [partial]" if PARTIAL.search(title) else ""
        print(f"  #{n}: {title}{mark}")
    running = {r["lane"]: r for r in lanemod.in_progress(args.cwd)}
    all_lanes = lanemod.read_lanes(args.cwd)
    if all_lanes:
        print("\nlanes:")
        for name, lane in sorted(all_lanes.items()):
            mark = f" (in progress: {running[name]['item']})" if name in running else ""
            print(f"  {name}: {', '.join(lane['items']) or '(empty)'}{mark}")
    return 0


def cmd_show(args):
    for n, title, body in _sections(_read_backlog(args.cwd)):
        if n == args.number:
            print(f"## #{n}: {title}")
            print(body.rstrip("\n"))
            return 0
    print(f"error: no entry #{args.number}", file=sys.stderr)
    return 1


def cmd_add(args):
    body = sys.stdin.read()
    if not body.strip():
        print(
            "error: an entry needs a real paragraph of context, not a stub - that is what "
            "makes it worth keeping. Pipe the body in on stdin.",
            file=sys.stderr,
        )
        return 1
    number = allocate(args.resource, args.title, body, cwd=args.cwd)
    print(f"allocated #{number} in {RESOURCES[args.resource].filename} (uncommitted)")
    return 0


def cmd_remove(args):
    """Delete an entry. Numbers are permanent: nothing is renumbered and the number is never
    reissued, which the counter guarantees by never going backwards."""
    path = _backlog_path(args.cwd)
    text = _read_backlog(args.cwd)
    kept, removed = [], False
    for n, title, body in _sections(text):
        if n == args.number:
            removed = True
            continue
        kept.append(f"## #{n}: {title}\n{body.rstrip(chr(10))}\n")
    if not removed:
        print(f"error: no entry #{args.number}", file=sys.stderr)
        return 1
    header = text[: text.index("## #")] if "## #" in text else text
    path.write_text(header.rstrip("\n") + "\n\n" + "\n".join(kept))
    print(f"removed #{args.number}; nothing renumbered, and #{args.number} is never reissued")
    return 0


def cmd_lane(args):
    items = [i.strip() for i in args.items.split(",") if i.strip()] if getattr(args, "items", None) else []
    if args.lane_command == "list":
        all_lanes = lanemod.read_lanes(args.cwd)
        if not all_lanes:
            print("no lanes")
        for name, lane in sorted(all_lanes.items()):
            current = f" (in progress: {lane['current']})" if lane.get("current") else ""
            print(f"  {name}: {', '.join(lane['items']) or '(empty)'}{current}")
    elif args.lane_command == "create":
        print(f"  {args.name}: {', '.join(lanemod.create_lane(args.name, items, args.cwd)['items'])}")
    elif args.lane_command == "modify":
        print(f"  {args.name}: {', '.join(lanemod.modify_lane(args.name, items, args.cwd)['items'])}")
    elif args.lane_command == "delete":
        lanemod.delete_lane(args.name, args.cwd)
        print(f"deleted lane {args.name}")
    elif args.lane_command == "current":
        item = None if args.item == "-" else args.item
        lanemod.set_current(args.name, item, args.cwd)
        print(f"  {args.name}: {'in progress on ' + item if item else 'idle'}")
    return 0


def cmd_lock(args):
    if args.lock_command == "status":
        info = state.lock_info(args.cwd)
        if not info:
            print("lock is not held")
            return 0
        age = f"{int(info['age_seconds'])}s" if info["age_seconds"] is not None else "unknown age"
        alive = "running" if info["alive"] else "NOT running - apparently stale"
        print(f"lock held by pid {info['pid']} ({alive}), {age}: {info['description']}")
        if not info["alive"]:
            print("A lock found when none is expected is worth investigating before clearing.")
        return 0
    print("cleared the lock" if state.clear_lock(args.cwd) else "no lock was held")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="orc-todo")
    p.add_argument("--cwd", default=None, help="operate on this project (default: current dir)")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list")
    show = sub.add_parser("show")
    show.add_argument("number", type=int)

    add = sub.add_parser("add")
    add.add_argument("resource", choices=sorted(RESOURCES))
    add.add_argument("title")

    rm = sub.add_parser("remove")
    rm.add_argument("number", type=int)

    lane = sub.add_parser("lane")
    lanesub = lane.add_subparsers(dest="lane_command", required=True)
    lanesub.add_parser("list")
    for name in ("create", "modify"):
        q = lanesub.add_parser(name)
        q.add_argument("name")
        q.add_argument("items")
    lanesub.add_parser("delete").add_argument("name")
    cur = lanesub.add_parser("current")
    cur.add_argument("name")
    cur.add_argument("item")

    lock = sub.add_parser("lock")
    locksub = lock.add_subparsers(dest="lock_command", required=True)
    locksub.add_parser("status")
    locksub.add_parser("clear")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.cwd = pathlib.Path(args.cwd) if args.cwd else pathlib.Path.cwd()
    handlers = {
        "list": cmd_list, "show": cmd_show, "add": cmd_add,
        "remove": cmd_remove, "lane": cmd_lane, "lock": cmd_lock,
    }
    try:
        return handlers[args.command](args)
    except state.NotAGitRepo as e:
        print(f"error: {e} - /orc-todo needs a git repository", file=sys.stderr)
        return 1
    except (ResourceMissing, lanemod.UnspeccedItem, lanemod.LaneMissing) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except state.LockUnavailable as e:
        print(f"error: {e}. See /orc-todo lock status", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

Create `skills/orc-todo/scripts/run.py` — identical in shape to `orc-release`'s:

```python
#!/usr/bin/env python3
"""Entry point for SKILL.md: puts the orc_todo package on sys.path, then runs its CLI."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orc_todo.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd skills/orc-todo/scripts && python3 -m pytest tests/ -v`
Expected: PASS — all 55 tests (11 + 11 + 9 + 10 + 14).

- [ ] **Step 5: Write SKILL.md**

Create `skills/orc-todo/SKILL.md`. Frontmatter:

```yaml
---
name: orc-todo
description: Use when the user explicitly asks to use orc-todo, or types /orc-todo, to see or change the backlog - listing open entries, reading one in full, adding or removing an entry, and creating or reordering the lanes that say which work runs in what order.
allowed-tools: Bash(python3 *)
---
```

Do **not** set `disable-model-invocation`. This is conversational and workflow-starting, which
per `CLAUDE.md`'s design checklist item 2 stays model-invocable.

The body must cover, in this order: running `python3 ${CLAUDE_SKILL_DIR}/scripts/run.py <args>`;
that `add` takes its body on stdin and must carry real reasoning, deferring to
`backlog-discipline` for what an entry contains; that `remove` never renumbers; that a lane item
must be specced and what to do when it is refused (offer to write the spec, then ask which lane);
that entries are written uncommitted and why; and that `lock clear` is for a lock you have
decided is stale, never a reflex.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-todo/
git commit -m "$(cat <<'EOF'
orc-todo: the command surface

The only part of v16 with a user in front of it. Everything the lock and
the allocator do stays invisible from here.

add takes its body on stdin rather than as an argument, because a real
entry is paragraphs and shell quoting for multi-paragraph prose is how a
stub gets written instead. An empty body is refused - the command is a
front door to backlog-discipline's rules, not a way around them.

remove renumbers nothing, and the counter never going backwards is what
guarantees the number is not reissued.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: The two hooks

**Files:**
- Create: `hooks/scripts/orclab_shared.py`, `hooks/scripts/lane_notice.py`, `hooks/scripts/backlog_guard.py`
- Modify: `hooks/hooks.json`
- Test: `hooks/scripts/tests/test_lane_notice.py`, `hooks/scripts/tests/test_backlog_guard.py`

**Interfaces:**
- Consumes: nothing at import time — hooks are standalone processes and must not import from a skill's `scripts/` directory. See the File Structure note about the deliberate duplication.
- Produces: two executables driven entirely by their stdin payload.

**Two findings settled before this task was written. Do not re-derive them.**

**1. `permissionDecision` has no `"ask"`.** Checked against the live docs at
`https://code.claude.com/docs/en/hooks` on 2026-09-09, twice — once for the enumeration and once
searching the page for the literal string. Only `"allow"` and `"deny"` are documented. So this
guard **denies**, and offers an escape marker the way `secret_guard.py` already does for
`# orclab:allow-secret`: re-running with a trailing `# orclab:discard-entries` proceeds. One
convention in the codebase, not two.

**2. The obvious list of "discarding" commands is wrong in both directions.** Tested empirically
on 2026-09-09 against a real repo with a tracked, modified file:

| Command | Discards a tracked edit? |
|---|---|
| `git checkout -- <path>`, `git checkout <path>`, `git restore <path>` | **yes**, unrecoverable |
| `git reset --hard` | **yes** |
| `git stash` | vanishes from the tree (recoverable from the stash) |
| `git clean -fdx` | **no** — only untracked files; a tracked BACKLOG.md is untouched |
| `git checkout <branch>` / `git switch <branch>` | **no** — the edit carries over, and git refuses rather than overwriting |

`git clean` and bare branch switching must **not** fire. `git checkout <branch>` is the most common
git command there is; a guard that fires on it is noise within a day, and noise gets waved through.

- [ ] **Step 2: Write the failing tests**

Create `hooks/scripts/tests/test_backlog_guard.py`:

```python
import json
import subprocess
import sys
import pathlib

GUARD = str(pathlib.Path(__file__).resolve().parent.parent / "backlog_guard.py")


def make_repo(tmp_path, dirty):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "BACKLOG.md").write_text("# Backlog\n\n## #7: committed one\n\nprose\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "BACKLOG.md"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "init"], check=True)
    if dirty:
        with open(tmp_path / "BACKLOG.md", "a") as f:
            f.write("\n## #8: an uncommitted finding\n\nreal prose\n")
    return tmp_path


def guard(command, repo):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    out = subprocess.run([sys.executable, GUARD], input=payload, capture_output=True,
                         text=True, cwd=str(repo))
    assert out.returncode == 0, "a hook must never wedge the shell"
    return json.loads(out.stdout) if out.stdout.strip() else None


def test_it_fires_on_a_discarding_command_when_entries_are_at_risk(tmp_path):
    repo = make_repo(tmp_path, dirty=True)
    decision = guard("git reset --hard HEAD", repo)
    assert decision is not None
    reason = decision["hookSpecificOutput"]["permissionDecisionReason"]
    assert "#8" in reason and "an uncommitted finding" in reason


def test_it_is_silent_on_a_discarding_command_when_nothing_is_at_risk(tmp_path):
    """A guard that fires on every checkout is noise, and noise gets waved through."""
    assert guard("git reset --hard HEAD", make_repo(tmp_path, dirty=False)) is None


def test_it_is_silent_on_a_harmless_command_even_with_entries_at_risk(tmp_path):
    assert guard("git status", make_repo(tmp_path, dirty=True)) is None
    assert guard("ls -la", make_repo(tmp_path, dirty=True)) is None


def test_it_covers_every_form_that_really_discards(tmp_path):
    repo = make_repo(tmp_path, dirty=True)
    for cmd in ["git checkout -- BACKLOG.md", "git checkout BACKLOG.md", "git checkout .",
                "git restore BACKLOG.md", "git reset --hard", "git reset --hard HEAD~1",
                "git stash", "git stash push -u"]:
        assert guard(cmd, repo) is not None, cmd


def test_it_stays_silent_on_commands_that_only_look_dangerous(tmp_path):
    """Verified empirically 2026-09-09: git clean touches only untracked files, and a branch
    switch carries the edit over rather than discarding it. git checkout <branch> is the most
    common git command there is - firing on it would make this guard noise within a day."""
    repo = make_repo(tmp_path, dirty=True)
    for cmd in ["git clean -fdx", "git clean -fd", "git checkout main", "git switch main",
                "git restore --staged BACKLOG.md", "git stash list", "git stash pop"]:
        assert guard(cmd, repo) is None, cmd


def test_the_escape_marker_lets_a_deliberate_discard_through(tmp_path):
    """Same convention secret_guard.py already uses for orclab:allow-secret, so the codebase
    has one escape idiom rather than two."""
    repo = make_repo(tmp_path, dirty=True)
    assert guard("git reset --hard  # orclab:discard-entries", repo) is None


def test_the_decision_is_deny_since_ask_is_not_a_documented_value(tmp_path):
    repo = make_repo(tmp_path, dirty=True)
    decision = guard("git reset --hard", repo)
    assert decision["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_a_non_bash_tool_is_ignored(tmp_path):
    repo = make_repo(tmp_path, dirty=True)
    payload = json.dumps({"tool_name": "Read", "tool_input": {"file_path": "x"}})
    out = subprocess.run([sys.executable, GUARD], input=payload, capture_output=True,
                         text=True, cwd=str(repo))
    assert out.returncode == 0 and not out.stdout.strip()


def test_outside_a_git_repo_it_fails_open(tmp_path):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git reset --hard"}})
    out = subprocess.run([sys.executable, GUARD], input=payload, capture_output=True,
                         text=True, cwd=str(tmp_path))
    assert out.returncode == 0 and not out.stdout.strip()


def test_garbage_on_stdin_fails_open(tmp_path):
    out = subprocess.run([sys.executable, GUARD], input="{not json",
                         capture_output=True, text=True, cwd=str(tmp_path))
    assert out.returncode == 0 and not out.stdout.strip()
```

Create `hooks/scripts/tests/test_lane_notice.py`:

```python
import json
import subprocess
import sys
import pathlib

NOTICE = str(pathlib.Path(__file__).resolve().parent.parent / "lane_notice.py")


def notice(repo):
    out = subprocess.run([sys.executable, NOTICE], input=json.dumps({"hook_event_name": "SessionStart"}),
                         capture_output=True, text=True, cwd=str(repo))
    assert out.returncode == 0
    return out.stdout


def make_repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "BACKLOG.md").write_text("# Backlog\n")
    return tmp_path


def test_it_says_nothing_when_nothing_is_running(tmp_path):
    """Silence is the common case. A hook that speaks every session gets tuned out."""
    assert notice(make_repo(tmp_path)).strip() == ""


def test_it_reports_a_lane_in_progress(tmp_path):
    repo = make_repo(tmp_path)
    shared = repo / ".git" / "orclab"
    shared.mkdir(parents=True)
    (shared / "lanes.json").write_text(json.dumps(
        {"A": {"items": ["v13"], "current": "v13", "started": "2026-09-08T14:20:00+00:00"}}))
    out = notice(repo)
    assert "A" in out and "v13" in out


def test_it_reports_a_held_lock(tmp_path):
    repo = make_repo(tmp_path)
    shared = repo / ".git" / "orclab"
    shared.mkdir(parents=True)
    (shared / "lock").write_text(json.dumps(
        {"pid": 999999, "started": "2026-09-08T14:20:00+00:00", "description": "allocating"}))
    assert "lock" in notice(repo).lower()


def test_it_reports_uncommitted_entries(tmp_path):
    repo = make_repo(tmp_path)
    subprocess.run(["git", "-C", str(repo), "add", "BACKLOG.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "init"], check=True)
    (repo / "BACKLOG.md").write_text("# Backlog\n\n## #8: unsaved finding\n\nprose\n")
    out = notice(repo)
    assert "#8" in out


def test_outside_a_git_repo_it_says_nothing_and_exits_clean(tmp_path):
    out = subprocess.run([sys.executable, NOTICE], input="{}", capture_output=True,
                         text=True, cwd=str(tmp_path))
    assert out.returncode == 0 and out.stdout.strip() == ""
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd hooks/scripts && python3 -m pytest tests/ -v`
Expected: FAIL — the two new test files error because their scripts do not exist. The existing
`test_secret_guard.py` must still pass.

- [ ] **Step 4: Write the implementation**

Create `hooks/scripts/orclab_shared.py`:

```python
"""Shared-dir resolution and uncommitted-entry detection, for the hooks.

A deliberate second copy of what skills/orc-todo/scripts/orc_todo/state.py already does. Hooks
run as standalone processes with their own working directory; a skill's scripts/ directory is
not on their path, and a sys.path insertion pointing into one would break the moment that skill
moved. Fifteen duplicated lines beat a hook that fails silently.

Everything here fails open: a hook that raises is worse than a hook that says nothing.
"""

import pathlib
import re
import subprocess

TRACKED = ("BACKLOG.md", "VERIFICATION.md")
ENTRY_RE = re.compile(r"^\+(## (?:#(\d+)|Scenario (\d+)): .*)$", re.MULTILINE)


def git(args, cwd=None):
    """Run git, returning stdout, or None if git failed for any reason at all."""
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def shared_dir(cwd=None):
    """<git-common-dir>/orclab, or None outside a repo. Never created here."""
    out = git(["rev-parse", "--git-common-dir"], cwd)
    if not out or not out.strip():
        return None
    base = pathlib.Path(cwd) if cwd else pathlib.Path.cwd()
    return (base / out.strip()).resolve() / "orclab"


def canonical_root(cwd=None):
    d = shared_dir(cwd)
    return d.parent.parent if d else None


def uncommitted_entries(cwd=None):
    """Entry headings added but not committed, as [(filename, heading)].

    Read from the diff rather than by parsing the file, because only the diff distinguishes an
    entry that was just added from the hundreds already committed.
    """
    root = canonical_root(cwd)
    if root is None:
        return []
    found = []
    for name in TRACKED:
        if not (root / name).exists():
            continue
        diff = git(["-C", str(root), "diff", "--", name], cwd)
        if not diff:
            continue
        found.extend((name, m.group(1)) for m in ENTRY_RE.finditer(diff))
    return found
```

Create `hooks/scripts/backlog_guard.py`:

```python
#!/usr/bin/env python3
"""PreToolUse guard: consent before a command discards an uncommitted backlog entry.

The allocator writes entries without committing them - see orc_todo/allocate.py for why - so
real findings sit in the canonical working tree until someone commits. Several ordinary git
commands throw exactly that away.

Two conditions, both required, and the second is what keeps this usable: the command must
really discard a tracked modification, AND there must actually be an uncommitted entry to lose.
A guard that fires on every `git checkout` is noise, and noise gets waved through - which is the
failure it exists to prevent.

Which commands qualify was settled empirically, not by intuition (2026-09-09): `git clean` only
removes untracked files, and `git checkout <branch>` carries a modification over rather than
discarding it. Neither belongs here, and both were in the first draft.

`permissionDecision` has no "ask" - only "allow" and "deny", per the live hooks docs checked
2026-09-09. So this denies, with a `# orclab:discard-entries` escape marker mirroring
secret_guard.py's `# orclab:allow-secret`.

Contract: read the hook payload as JSON on stdin, print a `hookSpecificOutput` decision on
stdout, exit 0. Any other exit status is a non-blocking error, so every unexpected failure here
lets the command through rather than wedging the shell.
"""

import json
import re
import sys

from orclab_shared import uncommitted_entries

ALLOW_MARKER = "orclab:discard-entries"

# Only forms that really discard a TRACKED modification - verified empirically 2026-09-09.
# `git clean` touches only untracked files, and `git checkout <branch>` carries the edit over
# (git refuses rather than overwriting), so neither belongs here. A guard that fires on
# `git checkout main` is noise, and noise gets waved through.
DISCARDS = re.compile(
    r"\bgit\s+(?:"
    r"reset\s+(?:--hard|--merge|--keep)\b"
    r"|stash\b(?!\s+(?:list|show|apply|pop))"
    r"|restore\b(?!\s+--staged\b)"
    r"|checkout\s+(?:--\s|\.(?:\s|$)|\S*(?:BACKLOG|VERIFICATION)\.md\b)"
    r")"
)


def evaluate(command):
    """The refusal reason, or None when this command is not a risk right now."""
    if ALLOW_MARKER in command:
        return None
    if not DISCARDS.search(command):
        return None
    at_risk = uncommitted_entries()
    if not at_risk:
        return None
    listed = "\n".join(f"  {name}: {heading}" for name, heading in at_risk)
    return (
        "This command discards uncommitted work, and these entries are not committed yet:\n"
        f"{listed}\n"
        "They were written by the allocator, which never commits. Commit them first, or "
        f"re-run with a trailing `# {ALLOW_MARKER}` to discard them deliberately."
    )


def main():
    try:
        payload = json.load(sys.stdin)
        if payload.get("tool_name") != "Bash":
            return 0
        reason = evaluate(payload.get("tool_input", {}).get("command", ""))
        if reason:
            json.dump(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        # "ask" is not a documented value - only allow and deny. Checked
                        # against the live hooks docs 2026-09-09. The escape marker above is
                        # what stands in for consent.
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                },
                sys.stdout,
            )
    except Exception:
        return 0  # fail open, always
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Create `hooks/scripts/lane_notice.py`:

```python
#!/usr/bin/env python3
"""SessionStart: tell a new session what is already going on.

On 2026-09-08 two sessions built the same feature for two hours because nothing recorded that
the first had started. Nobody forgot to check - there was nothing to check. This is what makes
the lane record consulted without anyone remembering to.

Silent unless there is something to say. A hook that speaks every session gets tuned out.
"""

import json
import pathlib
import sys

from orclab_shared import shared_dir, uncommitted_entries


def _load(path):
    try:
        return json.loads(pathlib.Path(path).read_text())
    except (OSError, ValueError):
        return {}


def notice():
    d = shared_dir()
    if d is None:
        return ""
    lines = []
    for name, lane in sorted(_load(d / "lanes.json").items()):
        if lane.get("current"):
            since = f" since {lane['started']}" if lane.get("started") else ""
            lines.append(f"  lane {name}: {lane['current']} in progress{since}")
    lock = _load(d / "lock")
    if (d / "lock").exists():
        lines.append(f"  lock held: {lock.get('description', 'unknown')} (pid {lock.get('pid')})")
    for filename, heading in uncommitted_entries():
        lines.append(f"  uncommitted in {filename}: {heading}")
    if not lines:
        return ""
    return "Orclab shared state:\n" + "\n".join(lines)


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    try:
        text = notice()
    except Exception:
        return 0  # fail open
    if text:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Wire both hooks**

Modify `hooks/hooks.json` to add the `SessionStart` event and a second `PreToolUse` Bash matcher.
The existing `secret_guard.py` entry must be left exactly as it is:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/lane_notice.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/secret_guard.py\""
          },
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/scripts/backlog_guard.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 6: Run the whole hooks suite**

Run: `cd hooks/scripts && python3 -m pytest tests/ -v`
Expected: PASS — the existing `secret_guard` tests plus 15 new ones.

- [ ] **Step 7: Commit**

```bash
git add hooks/
git commit -m "$(cat <<'EOF'
hooks: consent before discarding an entry, and a lane notice at session start

The guard pays for the allocator not committing. It fires only when the
command can discard uncommitted work AND there is actually an entry to
lose - both conditions, because a guard that fires on every git checkout
is noise, and noise gets waved through.

The SessionStart notice is what makes the lane record consulted without
anyone remembering to. On 2026-09-08 two sessions built the same feature
for two hours; nobody forgot to check, there was nothing to check.

orclab_shared.py duplicates ~15 lines of orc_todo/state.py deliberately.
Hooks are standalone processes and a sys.path insertion into a skill
directory breaks the moment that skill moves. Both hooks fail open.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: The RELEASING.md cross-reference check

**Files:**
- Modify: `skills/orc-release/scripts/orc_release/steps.py`
- Test: `skills/orc-release/scripts/tests/test_steps.py`

**Interfaces:**
- Consumes: the existing `parse_steps(text)` in that module.
- Produces: `crossref_warning(steps) -> str | None`, shaped exactly like the existing
  `numbering_warning(steps)` beside it.

**Read `numbering_warning` and `parse_steps` first** and match their conventions exactly —
return `None` when clean, a single `warning: ...` string otherwise. Match how `parse_steps`
represents a step (number, title, body) rather than assuming.

- [ ] **Step 1: Write the failing tests**

Append to `skills/orc-release/scripts/tests/test_steps.py`:

```python
def test_crossref_warning_is_none_when_every_reference_resolves():
    text = ("## 1. First\n\nDo a thing.\n\n"
            "## 2. Second\n\nSee step 1 above.\n")
    assert crossref_warning(parse_steps(text)) is None


def test_crossref_warning_catches_a_reference_past_the_end():
    """The renumber hazard release-checklist documents: headings shift, prose does not, and
    nothing warned about it."""
    text = ("## 1. First\n\nSee step 9 below.\n\n"
            "## 2. Second\n\nDone.\n")
    warning = crossref_warning(parse_steps(text))
    assert warning is not None
    assert "9" in warning and "step 1" in warning


def test_crossref_warning_reports_every_bad_reference_not_just_the_first():
    text = ("## 1. First\n\nSee step 7 and step 8.\n\n"
            "## 2. Second\n\nAlso step 9.\n")
    warning = crossref_warning(parse_steps(text))
    for n in ("7", "8", "9"):
        assert n in warning


def test_crossref_warning_ignores_a_self_reference():
    text = "## 1. First\n\nThis is step 1.\n\n## 2. Second\n\nDone.\n"
    assert crossref_warning(parse_steps(text)) is None


def test_crossref_warning_ignores_step_numbers_inside_fenced_code():
    """parse_steps already excludes fenced regions from heading detection; a shell comment
    saying 'step 12' must not become a false positive either."""
    text = ("## 1. First\n\n```bash\n# step 12 of the upstream guide\necho hi\n```\n\n"
            "## 2. Second\n\nDone.\n")
    assert crossref_warning(parse_steps(text)) is None
```

Add `crossref_warning` to that file's existing import from `orc_release.steps`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-release/scripts && python3 -m pytest tests/test_steps.py -v`
Expected: FAIL — `ImportError: cannot import name 'crossref_warning'`

- [ ] **Step 3: Write the implementation**

Add to `skills/orc-release/scripts/orc_release/steps.py`, immediately after `numbering_warning`:

```python
_CROSSREF = re.compile(r"\bstep\s+(\d+)\b", re.IGNORECASE)


def crossref_warning(steps):
    """Warn when a step's prose references a step number that does not exist.

    release-checklist requires renumbering when a step is inserted mid-document, and says
    outright that prose references like "see step 9 below" shift too and nothing warns about
    them. In the real 2026-09-07 incident three references had to move and five correctly
    stayed put, all by hand. This is that missing check.

    It catches only references past the end of the document - a reference that still resolves
    but now points at the wrong step is indistinguishable from a correct one without reading
    the prose, and a checker that guesses at meaning would cry wolf. Narrow and reliable beats
    broad and ignored.
    """
    if not steps:
        return None
    numbers = {s.number for s in steps}
    highest = max(numbers)
    bad = []
    for step in steps:
        body = _strip_fenced(step.body)
        for match in _CROSSREF.finditer(body):
            target = int(match.group(1))
            if target != step.number and target > highest:
                bad.append((step.number, target))
    if not bad:
        return None
    detail = ", ".join(f"step {s} references step {t}" for s, t in bad)
    return (
        f"warning: {detail} - no such step (the document ends at {highest}). "
        "A renumber shifts headings but not prose; see release-checklist."
    )
```

`_strip_fenced(text)` must remove fenced code blocks before scanning. `steps.py` already has
`_get_fenced_regions` and `_scan_fences` for the heading parser — **reuse whichever of those
fits rather than writing a third fence scanner**, and if neither works on a bare body string,
add a small `_strip_fenced` built on the existing one. Do not duplicate the fence logic.

`parse_steps` returns a list of `Step` dataclasses with `.number`, `.title` and `.body` — verified
2026-09-08, so the code above is correct as written. `.body` preserves fenced content, which is why
`_strip_fenced` is needed at all; `_get_fenced_regions` takes a text string and returns offsets
relative to it, so it works directly on a step body.

- [ ] **Step 4: Run the whole orc-release suite**

Run: `cd skills/orc-release/scripts && python3 -m pytest tests/ -v`
Expected: PASS — 102 existing plus 5 new.

- [ ] **Step 5: Surface it where `numbering_warning` is surfaced**

Find every place `numbering_warning` is called or reported (`grep -rn numbering_warning
skills/orc-release/`) and call `crossref_warning` alongside it, in the same style. If
`SKILL.md` documents the numbering warning, document this one in the same place and register.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-release/
git commit -m "$(cat <<'EOF'
orc-release: warn when a renumber breaks a prose cross-reference

release-checklist requires renumbering when a step is inserted
mid-document, and says outright that references like "see step 9 below"
shift too and nothing warns about them. In the 2026-09-07 incident three
references had to move and five correctly stayed put, all by hand.

Catches only references past the end of the document. A reference that
still resolves but now points at the wrong step is indistinguishable from
a correct one without reading the prose, and a checker that guesses at
meaning cries wolf. Narrow and reliable beats broad and ignored.

This is why RELEASING.md is not part of v16's allocator: its step numbers
are positional and deliberately renumbered, so there is no next number to
hand out. This is the check that file actually needed.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Skill prose the mechanism requires

**Files:**
- Modify: `skills/backlog-discipline/SKILL.md`
- Modify: `skills/release-checklist/SKILL.md`

- [ ] **Step 1: Replace `backlog-discipline`'s numbering rule**

Its "Numbering" section currently says to scan the file for every `## #N:` heading and take the
highest, plus a `git log -S` exception for when the highest-numbered entry was itself deleted.

Replace the whole section with an instruction to call the allocator:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/orc-todo/scripts/run.py add backlog "<title>"
```

with the body on stdin, which prints the allocated number. The new text must say why: two
agents scanning the same file both find the same maximum and both write it, which happened for
real on 2026-09-08 — both took `#23` and `#24`. Point at BACKLOG #22 and #25.

The `git log -S` exception is **deleted, not moved** — the allocator's counter never goes
backwards, so a deleted maximum entry can no longer cause a reissue. Say that explicitly, so a
reader who remembers the old rule knows it was retired rather than lost.

If `/orc-todo` is unavailable (no allocator, not a git repo), fall back to the old scan and say
so — a consuming project without Orclab installed still needs the skill to work.

- [ ] **Step 2: Replace the task-list line**

Delete this line from "What NOT to do":

```
- Don't turn this into a general task list — it's for findings, not routine planned work.
```

Replace it with what it was actually protecting:

```
- An entry earns its place by carrying reasoning someone would otherwise have to re-derive —
  not by being a thing to do. Work you will finish this session isn't an entry, it's work.
```

The old line was written 2026-09-04 with no recorded rationale and describes a file that does
not exist: ten of twelve open entries are things that need doing. It is also phrased by the
intent a reader brings rather than the situation it applies to, which is the failure mode
`CLAUDE.md` names.

- [ ] **Step 3: Point `release-checklist` at the new check**

Find its passage saying nothing warns about prose cross-references shifting during a renumber.
Leave the warning intact — the advice is still correct — and append that `/orc-release` now
reports references pointing past the end of the document, while a reference that still resolves
but now means the wrong step remains unchecked and still needs a human eye.

- [ ] **Step 4: Verify no suite broke**

Run: `cd skills/orc-todo/scripts && python3 -m pytest tests/ -q` and the same for
`skills/orc-release/scripts` and `hooks/scripts`. Documentation-only changes must not move any
count.

- [ ] **Step 5: Commit**

```bash
git add skills/backlog-discipline/SKILL.md skills/release-checklist/SKILL.md
git commit -m "$(cat <<'EOF'
backlog-discipline: ask the allocator, and stop calling this not-a-task-list

"Scan the file for the highest N" is a read-then-write race. Two agents
both find the same maximum and both write it, which happened for real on
2026-09-08 - both took #23 and #24. The rule was followed exactly by both;
it was racy, not ignored.

The git log -S exception for a deleted maximum entry is retired rather
than moved: the allocator's counter never goes backwards, so that path
cannot reissue a number any more.

"Don't turn this into a general task list" is replaced by what it
protected. It was written 2026-09-04 with no recorded rationale, describes
a file that does not exist - ten of twelve open entries are things that
need doing - and is phrased by the intent a reader brings rather than the
situation it applies to, which is the failure mode CLAUDE.md names.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Verification, backlog, version

**Files:**
- Modify: `VERIFICATION.md`, `BACKLOG.md`
- Modify: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` — **via `/orc-version`, never by hand**

- [ ] **Step 1: Fix Scenario 1, which encodes the bug**

`VERIFICATION.md`'s Scenario 1 currently reads "Note the highest `#N`" then "**Expected:** a new
`## #<N+1>: ...` entry is added". That is the read-then-write race written into the test script.

Rewrite those steps to expect the allocator: the number comes from `/orc-todo add`, and the
entry is written **uncommitted**. Leave the rest of the scenario — the resolve and delete
halves — exactly as it is.

- [ ] **Step 2: Add the new scenario**

Allocate its number with the tool this work just built, from the repository root:

```bash
python3 skills/orc-todo/scripts/run.py add verification "concurrent allocation, lanes, and the guard"
```

Give it a body covering what unit tests cannot: that `/orc-todo`'s listing is readable at a
glance; that two terminals both running `/orc-todo add` produce two different numbers and two
entries; that a fresh session really is told about a lane in progress; and that `git reset
--hard` asks for consent when an uncommitted entry would be lost and stays silent when none
would.

This step is also the first real use of the allocator. If it misbehaves, that is a finding worth
an entry, not something to work around.

- [ ] **Step 3: Resolve the backlog entries**

Per `orclab:backlog-discipline`, append resolutions — never rewrite the original text:

- **#22** — resolved. Note which parts were built (lock, allocator, lanes) and which of its
  proposals were deliberately not: pre-assigned ranges, serialization, and any DAG or scheduler
  beyond N linear lanes. Record that its "do not build ahead of a real concurrent run" trigger
  fired on 2026-09-08.
- **#25** — resolved. Both halves it describes now have a mechanism: the allocator for the
  numbers, the lane record and SessionStart hook for the duplicate work.

Do **not** resolve #23 or #24 — the action-shape warning and the dry-run exit code are untouched
by this work.

- [ ] **Step 4: Bump the version through `/orc-version`, not by hand**

Invoke `/orc-version 0.14.0` — a minor bump, since this adds a command and two hooks. It updates
both `.claude-plugin/*.json`, prepends the changelog entry, commits, and tags.

**Do not hand-edit either JSON file.** BACKLOG #13 records that every release before v0.11.0
bypassed `/orc-version`, and that two went untagged as the direct mechanical cost. If it fails or
misses a file, that is a real finding worth an entry — report it rather than working around it.

- [ ] **Step 5: Validate the plugin**

```bash
claude plugin validate .claude-plugin/plugin.json
```

Name the file explicitly. The bare `claude plugin validate .` validates the *marketplace*
manifest and stops, which is green for the right input and the wrong one alike. Do not pass
`--strict`: it promotes Orclab's one expected warning — that root `CLAUDE.md` is not loaded as
project context — into an error, and that layout is deliberate.

Expect `✔ Validation passed with warnings`, with that one warning. A pass says nothing about
frontmatter; never write a release step that implies otherwise.

- [ ] **Step 6: Run every suite one last time**

```bash
cd skills/orc-todo/scripts && python3 -m pytest tests/ -q
cd skills/orc-publish/scripts && python3 -m pytest tests/ -q
cd skills/orc-release/scripts && python3 -m pytest tests/ -q
cd hooks/scripts && python3 -m pytest tests/ -q
```

Report the real counts. `orc-publish` is untouched by this work and must be unchanged at 126.
