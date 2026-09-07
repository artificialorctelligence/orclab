# Orclab v8: `/orc-release` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/orc-release` to Orclab — a skill that drives a project's own `RELEASING.md` end to
end, enforcing its ordered gates, tracking position across sessions, and owning the version's whole
lifecycle including rollback — and bump Orclab to 0.8.0 with a real `CHANGELOG.md` entry **and a git
tag**.

**Architecture:** Ships as a skill only (`skills/orc-release/SKILL.md`), no `commands/*.md` — same
reasoning as v7. `RELEASING.md` is the single definition of the steps; a small state cursor at
`.orclab/release/state.json` records only *position*. Bundled Python owns what is deterministic and
breaks builds when wrong (parsing steps, state read/write, and per-format version file writing);
Claude owns judgment (did this step's output mean it passed, drafting changelog content). **All new
Python lives under `skills/orc-release/scripts/`, including version-file handling** — `/orc-version`
delegates to that same module rather than growing a second implementation, which satisfies the
spec's "one place owns version-setting" without inventing a shared-scripts convention Orclab does
not have today.

**Tech Stack:** Python 3.12 (stdlib `argparse`, `json`, `re`, `hashlib`, `tomllib`; no new runtime
dependencies — note `orc-publish` uses PyYAML but this skill needs none), pytest for tests,
Markdown for `SKILL.md`, JSON for manifests.

**Spec:** `docs/superpowers/specs/2026-09-07-orclab-v8-orc-release-design.md`

## Global Constraints

- Ships as a **skill only** (`skills/orc-release/SKILL.md`), no `commands/orc-release.md`.
- `RELEASING.md` is the **single definition** of the steps. The state cursor records position only,
  never step definitions.
- The runner **reads `RELEASING.md` in full before acting on any step**.
- **Halt on failure.** Never continue past a failed step, and never auto-retry or auto-skip. (This
  is deliberately opposite to `/orc-publish`'s continue-past-failure — release steps are a
  dependent chain, publish channels are independent siblings.)
- The four `release-checklist` conventions are **optional**; a document using none of them must
  still be driveable. With no irreversibility markers, abort reports every completed step and says
  plainly it cannot determine which were reversible, rather than guessing.
- **Never invent a release process.** No `RELEASING.md` means report and stop.
- Exactly **two built-in checks**: no release already in progress (hard stop), and a working-tree
  report at entry (prints real `git status --short`, asks whether to proceed, **never blocks**, and
  runs only when starting a release — never on resume, since step 1 legitimately dirties the tree).
  Every other precondition comes from the document's own steps.
- **One place owns version-setting.** `/orc-version` delegates to the same module `/orc-release`
  uses. Version logic is never duplicated.
- `/orc-version`'s **default behavior is unchanged** — `--no-commit` is additive.
- Version files are **verified consistent** after being set, never assumed.
- **Per-format version handlers only** for `plugin.json`, `marketplace.json`, `pyproject.toml`,
  `debian/changelog`. No speculative generic manifest-detection abstraction.
- **Abort never overstates what it can undo.** It rolls back local edits/commits/tags and reports
  completed irreversible steps as permanent.
- Skips require a recorded reason.
- A changed `RELEASING.md` hash mid-release warns and stops rather than resuming on shifted numbers.
- Per-step tracking only; no sub-step/checkbox modeling.
- Orclab's own repo contains **zero consuming-project release content**; all test fixtures are
  synthetic.
- An empty `conftest.py` sits at `skills/orc-release/scripts/` so the suite runs from any working
  directory (per `CLAUDE.md`'s "Running the bundled-script test suites").
- Version: **0.8.0**, and **the release must be git-tagged** (see Task 8 — BACKLOG #9 and #13 record
  two consecutive releases that shipped untagged because the plan omitted this step).

---

## File Structure

```
orclab/
  skills/
    orc-release/
      SKILL.md                              (new — Task 7)
      scripts/
        conftest.py                         (new — Task 1, empty)
        run.py                              (new — Task 6, entry point)
        orc_release/
          __init__.py                       (new — Task 1, empty)
          steps.py                          (new — Task 1: parse RELEASING.md)
          state.py                          (new — Task 2: the position cursor)
          versionfiles.py                   (new — Tasks 3+4: per-format version I/O)
          cli.py                            (new — Task 6: argparse orchestration)
        tests/
          test_steps.py                     (new — Task 1)
          test_state.py                     (new — Task 2)
          test_versionfiles.py              (new — Tasks 3+4)
          test_cli.py                       (new — Task 6)
  commands/
    orc-version.md                          (modify — Task 5: --no-commit + delegation)
  skills/
    release-checklist/SKILL.md              (modify — Task 5: four conventions)
  .claude-plugin/plugin.json                (modify — Task 8: 0.8.0)
  .claude-plugin/marketplace.json           (modify — Task 8: 0.8.0)
  CHANGELOG.md                              (modify — Task 8)
  README.md                                 (modify — Task 8)
  VERIFICATION.md                           (modify — Task 8: Scenarios 27-34)
```

---

### Task 1: Parse `RELEASING.md` into steps (`steps.py`)

**Files:**
- Create: `skills/orc-release/scripts/orc_release/__init__.py` (empty)
- Create: `skills/orc-release/scripts/conftest.py`
- Create: `skills/orc-release/scripts/orc_release/steps.py`
- Test: `skills/orc-release/scripts/tests/test_steps.py`

**Interfaces:**
- Consumes: nothing (foundation task).
- Produces: `orc_release.steps.Step` (a dataclass with fields `number: int`, `title: str`,
  `body: str`, `preconditions: list[str]`, `is_manual: bool`, `delegates_to: str | None`,
  `is_irreversible: bool`); `orc_release.steps.parse_steps(text: str) -> list[Step]`;
  `orc_release.steps.doc_hash(text: str) -> str`.

- [ ] **Step 1: Create the package skeleton**

```bash
mkdir -p skills/orc-release/scripts/orc_release skills/orc-release/scripts/tests
touch skills/orc-release/scripts/orc_release/__init__.py
cat > skills/orc-release/scripts/conftest.py <<'EOF'
"""Empty on purpose - its presence makes orc_release importable from any pytest invocation
(bare `pytest`, `python3 -m pytest` from any directory), not just from inside this scripts/
directory specifically."""
EOF
```

- [ ] **Step 2: Write the failing tests**

Create `skills/orc-release/scripts/tests/test_steps.py`:

```python
import textwrap

from orc_release.steps import Step, doc_hash, parse_steps


DOC_PLAIN = textwrap.dedent(
    """
    # Cutting a release

    Some preamble that is not a step.

    ## 1. Pick a version

    Edit the version files.

    ## 2. Full test suite

    Run: `pytest tests/ -q`

    Must be fully green.
    """
)


def test_parses_numbered_steps_in_order():
    steps = parse_steps(DOC_PLAIN)
    assert [(s.number, s.title) for s in steps] == [
        (1, "Pick a version"),
        (2, "Full test suite"),
    ]


def test_preamble_before_the_first_step_is_not_a_step():
    steps = parse_steps(DOC_PLAIN)
    assert all("preamble" not in s.body for s in steps)


def test_step_body_captures_everything_up_to_the_next_step():
    steps = parse_steps(DOC_PLAIN)
    assert "pytest tests/ -q" in steps[1].body
    assert "Must be fully green" in steps[1].body
    assert "Pick a version" not in steps[1].body


def test_a_document_using_none_of_the_conventions_still_parses():
    steps = parse_steps(DOC_PLAIN)
    for s in steps:
        assert s.preconditions == []
        assert s.is_manual is False
        assert s.delegates_to is None
        assert s.is_irreversible is False


def test_preconditions_are_extracted():
    steps = parse_steps(
        textwrap.dedent(
            """
            ## 6. Upload to the PPA

            **Preconditions:** this version is not already published; gpg-agent is unlocked.

            Run: `dput ...`
            """
        )
    )
    assert steps[0].preconditions == [
        "this version is not already published; gpg-agent is unlocked."
    ]


def test_performed_by_hand_is_detected():
    steps = parse_steps(
        textwrap.dedent(
            """
            ## 7. Install-test on every target

            **Performed by hand.** Copy the .deb to each VM and launch it.
            """
        )
    )
    assert steps[0].is_manual is True


def test_delegation_is_extracted():
    steps = parse_steps(
        textwrap.dedent(
            """
            ## 6. Publish to every channel

            **Run:** /orc-publish
            """
        )
    )
    assert steps[0].delegates_to == "/orc-publish"


def test_irreversible_is_detected():
    steps = parse_steps(
        textwrap.dedent(
            """
            ## 6. Upload to the PPA

            **Irreversible.** Once uploaded, the version number is consumed.
            """
        )
    )
    assert steps[0].is_irreversible is True


def test_markers_are_case_insensitive_and_survive_surrounding_prose():
    steps = parse_steps(
        textwrap.dedent(
            """
            ## 3. Ship it

            Some prose first.

            **performed by hand.** do the thing

            **irreversible.**
            """
        )
    )
    assert steps[0].is_manual is True
    assert steps[0].is_irreversible is True


def test_non_step_headings_are_ignored():
    steps = parse_steps(
        textwrap.dedent(
            """
            ## Overview

            Not a step.

            ## 1. Real step

            Body.

            ## Appendix

            Also not a step.
            """
        )
    )
    assert [s.number for s in steps] == [1]


def test_doc_hash_is_stable_and_changes_with_content():
    assert doc_hash("abc") == doc_hash("abc")
    assert doc_hash("abc") != doc_hash("abd")


def test_step_is_a_plain_dataclass_with_expected_fields():
    s = Step(number=1, title="x", body="y")
    assert s.preconditions == []
    assert s.is_manual is False
    assert s.delegates_to is None
    assert s.is_irreversible is False
```

- [ ] **Step 3: Run the tests to confirm they fail**

```bash
cd skills/orc-release/scripts && python3 -m pytest tests/test_steps.py -v
```

Expected: `ModuleNotFoundError: No module named 'orc_release.steps'`.

- [ ] **Step 4: Implement `steps.py`**

Create `skills/orc-release/scripts/orc_release/steps.py`:

```python
"""Parse a project's RELEASING.md into ordered steps.

RELEASING.md is the single definition of a release's steps - this module only reads it. The
four prose conventions (preconditions, performed-by-hand, delegation, irreversible) are all
OPTIONAL: a document using none of them parses fine, with every marker field left at its
default. That backward compatibility is load-bearing, not incidental - real documents predate
the conventions.
"""

import hashlib
import re
from dataclasses import dataclass, field

# "## 3. Security check" - a numbered step. "## Overview" is not a step.
_STEP_HEADING = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$", re.MULTILINE)

_PRECONDITION = re.compile(r"\*\*Preconditions?:\*\*\s*(.+?)$", re.IGNORECASE | re.MULTILINE)
_MANUAL = re.compile(r"\*\*Performed by hand\.?\*\*", re.IGNORECASE)
_IRREVERSIBLE = re.compile(r"\*\*Irreversible\.?\*\*", re.IGNORECASE)
_DELEGATES = re.compile(r"\*\*Run:\*\*\s*(/[\w-]+)", re.IGNORECASE)


@dataclass
class Step:
    number: int
    title: str
    body: str
    preconditions: list = field(default_factory=list)
    is_manual: bool = False
    delegates_to: str = None
    is_irreversible: bool = False


def parse_steps(text):
    """Return the document's numbered steps, in document order.

    A step's body runs from just after its heading to just before the next heading of any
    kind, so an unnumbered '## Appendix' correctly ends the previous step rather than being
    swallowed into it.
    """
    matches = list(_STEP_HEADING.finditer(text))
    steps = []
    for i, m in enumerate(matches):
        body_start = m.end()
        next_heading = re.compile(r"^##\s", re.MULTILINE).search(text, body_start)
        body_end = next_heading.start() if next_heading else len(text)
        body = text[body_start:body_end].strip()
        steps.append(
            Step(
                number=int(m.group(1)),
                title=m.group(2).strip(),
                body=body,
                preconditions=[p.strip() for p in _PRECONDITION.findall(body)],
                is_manual=bool(_MANUAL.search(body)),
                delegates_to=(_DELEGATES.search(body).group(1) if _DELEGATES.search(body) else None),
                is_irreversible=bool(_IRREVERSIBLE.search(body)),
            )
        )
    return steps


def doc_hash(text):
    """Stable content hash, used to detect a RELEASING.md edited mid-release."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
```

- [ ] **Step 5: Run the tests to confirm they pass**

```bash
cd skills/orc-release/scripts && python3 -m pytest tests/test_steps.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-release/scripts/conftest.py \
        skills/orc-release/scripts/orc_release/__init__.py \
        skills/orc-release/scripts/orc_release/steps.py \
        skills/orc-release/scripts/tests/test_steps.py
git commit -m "orc-release: parse RELEASING.md into ordered steps"
```

---

### Task 2: The state cursor (`state.py`)

**Files:**
- Create: `skills/orc-release/scripts/orc_release/state.py`
- Test: `skills/orc-release/scripts/tests/test_state.py`

**Interfaces:**
- Consumes: nothing from Task 1 at runtime (the caller passes values in).
- Produces: `orc_release.state.STATE_PATH` (the constant `".orclab/release/state.json"`);
  `start_release(root, version, previous_version, doc_path, doc_hash) -> dict`;
  `load_state(root) -> dict | None`; `save_state(root, state) -> None`;
  `is_in_progress(root) -> bool`; `mark_complete(state, number, title, irreversible=False) -> dict`;
  `mark_skipped(state, number, title, reason) -> dict`;
  `completed_numbers(state) -> list[int]`; `next_step_number(state, steps) -> int | None`;
  `irreversible_completed(state) -> list[dict]`; `clear_state(root) -> None`.

- [ ] **Step 1: Write the failing tests**

Create `skills/orc-release/scripts/tests/test_state.py`:

```python
import json

import pytest

from orc_release.state import (
    STATE_PATH,
    clear_state,
    completed_numbers,
    irreversible_completed,
    is_in_progress,
    load_state,
    mark_complete,
    mark_skipped,
    next_step_number,
    save_state,
    start_release,
)


def test_no_state_means_not_in_progress(tmp_path):
    assert is_in_progress(str(tmp_path)) is False
    assert load_state(str(tmp_path)) is None


def test_start_release_writes_state_that_loads_back(tmp_path):
    start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc123")
    assert is_in_progress(str(tmp_path)) is True
    state = load_state(str(tmp_path))
    assert state["version"] == "0.3.0"
    assert state["previous_version"] == "0.2.0"
    assert state["doc_path"] == "RELEASING.md"
    assert state["doc_hash"] == "abc123"
    assert state["completed"] == []
    assert state["skipped"] == []
    assert state["started_at"]


def test_state_lands_at_the_documented_path(tmp_path):
    start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    assert (tmp_path / STATE_PATH).exists()
    assert STATE_PATH == ".orclab/release/state.json"


def test_mark_complete_records_number_and_title(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_complete(state, 1, "Pick a version")
    save_state(str(tmp_path), state)
    reloaded = load_state(str(tmp_path))
    assert reloaded["completed"] == [
        {"number": 1, "title": "Pick a version", "irreversible": False}
    ]


def test_mark_complete_records_irreversibility(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_complete(state, 6, "Upload to the PPA", irreversible=True)
    assert irreversible_completed(state) == [
        {"number": 6, "title": "Upload to the PPA", "irreversible": True}
    ]


def test_mark_complete_is_idempotent_for_the_same_step(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_complete(state, 1, "Pick a version")
    state = mark_complete(state, 1, "Pick a version")
    assert completed_numbers(state) == [1]


def test_mark_skipped_requires_and_records_a_reason(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_skipped(state, 3, "Security check", "semgrep not set up on this machine")
    assert state["skipped"] == [
        {
            "number": 3,
            "title": "Security check",
            "reason": "semgrep not set up on this machine",
        }
    ]


def test_mark_skipped_rejects_an_empty_reason(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    with pytest.raises(ValueError, match="reason"):
        mark_skipped(state, 3, "Security check", "   ")


def test_a_skipped_step_counts_as_passed_for_advancing(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_skipped(state, 1, "Pick a version", "already done by hand")
    assert completed_numbers(state) == [1]


def test_next_step_number_returns_the_first_unfinished_step(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_complete(state, 1, "One")
    state = mark_complete(state, 2, "Two")
    assert next_step_number(state, [1, 2, 3, 4]) == 3


def test_next_step_number_is_none_when_everything_is_done(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    for n in (1, 2, 3):
        state = mark_complete(state, n, f"Step {n}")
    assert next_step_number(state, [1, 2, 3]) is None


def test_clear_state_removes_it(tmp_path):
    start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    clear_state(str(tmp_path))
    assert is_in_progress(str(tmp_path)) is False


def test_clear_state_on_absent_state_is_not_an_error(tmp_path):
    clear_state(str(tmp_path))


def test_state_file_is_valid_readable_json(tmp_path):
    start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    json.loads((tmp_path / STATE_PATH).read_text())
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd skills/orc-release/scripts && python3 -m pytest tests/test_state.py -v
```

Expected: `ModuleNotFoundError: No module named 'orc_release.state'`.

- [ ] **Step 3: Implement `state.py`**

Create `skills/orc-release/scripts/orc_release/state.py`:

```python
"""The release position cursor.

This records WHERE a release is, never WHAT its steps are - RELEASING.md is the single
definition of the steps, and nothing here duplicates it, so there is nothing to drift.

The stored doc_hash is load-bearing: release-checklist explicitly renumbers steps when one is
inserted mid-document, so a document edited mid-release can make a recorded "step 7" mean a
different step than the one that was actually run.
"""

import datetime
import json
import os

STATE_PATH = ".orclab/release/state.json"


def _path(root):
    return os.path.join(root, STATE_PATH)


def _now():
    return datetime.datetime.now().astimezone().isoformat()


def start_release(root, version, previous_version, doc_path, doc_hash):
    """Create and persist fresh release state. previous_version is what rollback restores."""
    state = {
        "version": version,
        "previous_version": previous_version,
        "doc_path": doc_path,
        "doc_hash": doc_hash,
        "completed": [],
        "skipped": [],
        "started_at": _now(),
        "updated_at": _now(),
    }
    save_state(root, state)
    return state


def load_state(root):
    """Return the in-progress release state, or None if there isn't one."""
    try:
        with open(_path(root)) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def save_state(root, state):
    state["updated_at"] = _now()
    path = _path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def is_in_progress(root):
    return load_state(root) is not None


def mark_complete(state, number, title, irreversible=False):
    """Record a step as done. Idempotent - re-running a step does not duplicate the entry."""
    if number not in completed_numbers(state):
        state["completed"].append(
            {"number": number, "title": title, "irreversible": bool(irreversible)}
        )
    return state


def mark_skipped(state, number, title, reason):
    """Record a step as deliberately skipped. A reason is required, never optional."""
    if not reason or not reason.strip():
        raise ValueError("a skip requires a real reason")
    state["skipped"].append(
        {"number": number, "title": title, "reason": reason.strip()}
    )
    return state


def completed_numbers(state):
    """Step numbers that are finished - completed or deliberately skipped."""
    done = [c["number"] for c in state.get("completed", [])]
    done += [s["number"] for s in state.get("skipped", [])]
    return sorted(set(done))


def next_step_number(state, all_numbers):
    """The first step number not yet finished, or None if the release is complete."""
    done = set(completed_numbers(state))
    for n in sorted(all_numbers):
        if n not in done:
            return n
    return None


def irreversible_completed(state):
    """Completed steps the document marked irreversible - what abort cannot undo."""
    return [c for c in state.get("completed", []) if c.get("irreversible")]


def clear_state(root):
    try:
        os.remove(_path(root))
    except FileNotFoundError:
        pass
```

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
cd skills/orc-release/scripts && python3 -m pytest tests/test_state.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-release/scripts/orc_release/state.py \
        skills/orc-release/scripts/tests/test_state.py
git commit -m "orc-release: the release position cursor"
```

---

### Task 3: Simple version-file formats and consistency (`versionfiles.py`, part 1)

**Files:**
- Create: `skills/orc-release/scripts/orc_release/versionfiles.py`
- Test: `skills/orc-release/scripts/tests/test_versionfiles.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `orc_release.versionfiles.detect(root) -> list[str]` (repo-relative paths of every
  version-holding file that exists); `read_version(root, relpath) -> str | None`;
  `write_version(root, relpath, version, **kwargs) -> None`;
  `verify_consistency(root) -> tuple[bool, dict]` (agreement flag, and a `{relpath: version}` map).
  Task 4 extends the same module with `debian/changelog` support.

- [ ] **Step 1: Write the failing tests**

Create `skills/orc-release/scripts/tests/test_versionfiles.py`:

```python
import json
import textwrap

import pytest

from orc_release.versionfiles import (
    detect,
    read_version,
    verify_consistency,
    write_version,
)


def write(tmp_path, relpath, content):
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip())
    return p


PYPROJECT = """
    [build-system]
    requires = ["setuptools"]

    [project]
    name = "orcshot"
    version = "0.2.0"
    dependencies = []
    """


def test_detect_finds_nothing_in_an_empty_project(tmp_path):
    assert detect(str(tmp_path)) == []


def test_detect_finds_pyproject(tmp_path):
    write(tmp_path, "pyproject.toml", PYPROJECT)
    assert detect(str(tmp_path)) == ["pyproject.toml"]


def test_detect_finds_plugin_manifests(tmp_path):
    write(tmp_path, ".claude-plugin/plugin.json", '{"name": "x", "version": "0.1.0"}')
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        '{"name": "x", "plugins": [{"name": "x", "version": "0.1.0"}]}',
    )
    assert sorted(detect(str(tmp_path))) == [
        ".claude-plugin/marketplace.json",
        ".claude-plugin/plugin.json",
    ]


def test_read_pyproject_version(tmp_path):
    write(tmp_path, "pyproject.toml", PYPROJECT)
    assert read_version(str(tmp_path), "pyproject.toml") == "0.2.0"


def test_write_pyproject_version_preserves_everything_else(tmp_path):
    p = write(tmp_path, "pyproject.toml", PYPROJECT)
    write_version(str(tmp_path), "pyproject.toml", "0.3.0")
    text = p.read_text()
    assert 'version = "0.3.0"' in text
    assert 'name = "orcshot"' in text
    assert "[build-system]" in text
    assert 'requires = ["setuptools"]' in text


def test_write_pyproject_does_not_touch_a_dependency_version_field(tmp_path):
    p = write(
        tmp_path,
        "pyproject.toml",
        """
        [project]
        name = "x"
        version = "0.2.0"

        [tool.other]
        version = "9.9.9"
        """,
    )
    write_version(str(tmp_path), "pyproject.toml", "0.3.0")
    text = p.read_text()
    assert 'version = "0.3.0"' in text
    assert 'version = "9.9.9"' in text


def test_read_and_write_plugin_json(tmp_path):
    write(tmp_path, ".claude-plugin/plugin.json", '{\n  "name": "x",\n  "version": "0.1.0"\n}\n')
    assert read_version(str(tmp_path), ".claude-plugin/plugin.json") == "0.1.0"
    write_version(str(tmp_path), ".claude-plugin/plugin.json", "0.2.0")
    data = json.loads((tmp_path / ".claude-plugin/plugin.json").read_text())
    assert data["version"] == "0.2.0"
    assert data["name"] == "x"


def test_read_and_write_marketplace_json_nested_version(tmp_path):
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        '{\n  "name": "x",\n  "plugins": [{"name": "x", "version": "0.1.0"}]\n}\n',
    )
    assert read_version(str(tmp_path), ".claude-plugin/marketplace.json") == "0.1.0"
    write_version(str(tmp_path), ".claude-plugin/marketplace.json", "0.2.0")
    data = json.loads((tmp_path / ".claude-plugin/marketplace.json").read_text())
    assert data["plugins"][0]["version"] == "0.2.0"


def test_write_marketplace_adds_a_missing_version_field(tmp_path):
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        '{\n  "name": "x",\n  "plugins": [{"name": "x"}]\n}\n',
    )
    write_version(str(tmp_path), ".claude-plugin/marketplace.json", "0.2.0")
    data = json.loads((tmp_path / ".claude-plugin/marketplace.json").read_text())
    assert data["plugins"][0]["version"] == "0.2.0"


def test_verify_consistency_passes_when_all_files_agree(tmp_path):
    write(tmp_path, "pyproject.toml", PYPROJECT)
    write(tmp_path, ".claude-plugin/plugin.json", '{"name": "x", "version": "0.2.0"}')
    ok, versions = verify_consistency(str(tmp_path))
    assert ok is True
    assert set(versions.values()) == {"0.2.0"}


def test_verify_consistency_detects_a_real_mismatch(tmp_path):
    write(tmp_path, "pyproject.toml", PYPROJECT)
    write(tmp_path, ".claude-plugin/plugin.json", '{"name": "x", "version": "9.9.9"}')
    ok, versions = verify_consistency(str(tmp_path))
    assert ok is False
    assert versions["pyproject.toml"] == "0.2.0"
    assert versions[".claude-plugin/plugin.json"] == "9.9.9"


def test_verify_consistency_on_a_project_with_no_version_files(tmp_path):
    ok, versions = verify_consistency(str(tmp_path))
    assert ok is True
    assert versions == {}


def test_unknown_format_raises_rather_than_guessing(tmp_path):
    with pytest.raises(ValueError, match="unsupported"):
        read_version(str(tmp_path), "Cargo.toml")
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd skills/orc-release/scripts && python3 -m pytest tests/test_versionfiles.py -v
```

Expected: `ModuleNotFoundError: No module named 'orc_release.versionfiles'`.

- [ ] **Step 3: Implement `versionfiles.py` (simple formats)**

Create `skills/orc-release/scripts/orc_release/versionfiles.py`:

```python
"""Read and write a project's version across every file that holds it.

Deliberately per-format, not a generic "detect any manifest" abstraction: each format carries
real syntax whose sloppy write breaks a real build. Formats are added when a real project needs
one. Supported today: pyproject.toml, .claude-plugin/plugin.json, .claude-plugin/marketplace.json,
and debian/changelog (see the changelog section below).

This module is the single owner of version-setting - /orc-release uses it directly, and
/orc-version delegates to it rather than carrying a second implementation.
"""

import json
import os
import re
import tomllib

PYPROJECT = "pyproject.toml"
PLUGIN_JSON = ".claude-plugin/plugin.json"
MARKETPLACE_JSON = ".claude-plugin/marketplace.json"
DEBIAN_CHANGELOG = "debian/changelog"

KNOWN_FORMATS = [PYPROJECT, PLUGIN_JSON, MARKETPLACE_JSON, DEBIAN_CHANGELOG]


def detect(root):
    """Repo-relative paths of every known version-holding file that actually exists."""
    return [rel for rel in KNOWN_FORMATS if os.path.exists(os.path.join(root, rel))]


def _read_text(root, relpath):
    with open(os.path.join(root, relpath)) as f:
        return f.read()


def _write_text(root, relpath, text):
    with open(os.path.join(root, relpath), "w") as f:
        f.write(text)


def read_version(root, relpath):
    """Current version in one file, or None if the file has no version to report."""
    if relpath == PYPROJECT:
        data = tomllib.loads(_read_text(root, relpath))
        return data.get("project", {}).get("version")
    if relpath == PLUGIN_JSON:
        return json.loads(_read_text(root, relpath)).get("version")
    if relpath == MARKETPLACE_JSON:
        plugins = json.loads(_read_text(root, relpath)).get("plugins", [])
        return plugins[0].get("version") if plugins else None
    if relpath == DEBIAN_CHANGELOG:
        return _changelog_current_version(_read_text(root, relpath))
    raise ValueError(f"unsupported version file format: {relpath}")


def write_version(root, relpath, version, **kwargs):
    """Set the version in one file, preserving everything else about it."""
    if relpath == PYPROJECT:
        return _write_pyproject(root, relpath, version)
    if relpath == PLUGIN_JSON:
        data = json.loads(_read_text(root, relpath))
        data["version"] = version
        return _write_text(root, relpath, json.dumps(data, indent=2) + "\n")
    if relpath == MARKETPLACE_JSON:
        data = json.loads(_read_text(root, relpath))
        for plugin in data.get("plugins", []):
            plugin["version"] = version
        return _write_text(root, relpath, json.dumps(data, indent=2) + "\n")
    if relpath == DEBIAN_CHANGELOG:
        return _write_changelog(root, relpath, version, **kwargs)
    raise ValueError(f"unsupported version file format: {relpath}")


def _write_pyproject(root, relpath, version):
    """Replace only [project]'s own version line.

    Targeted regex rather than a TOML round-trip: rewriting the parsed document would reformat
    the file and destroy comments, producing a noisy diff on every release.
    """
    text = _read_text(root, relpath)
    section = re.search(r"^\[project\]\s*$", text, re.MULTILINE)
    if not section:
        raise ValueError(f"{relpath} has no [project] section")
    next_section = re.compile(r"^\[", re.MULTILINE).search(text, section.end())
    end = next_section.start() if next_section else len(text)
    body = text[section.end() : end]
    new_body, count = re.subn(
        r'^(version\s*=\s*)"[^"]*"',
        lambda m: f'{m.group(1)}"{version}"',
        body,
        count=1,
        flags=re.MULTILINE,
    )
    if count == 0:
        raise ValueError(f"{relpath} has no version field in [project]")
    _write_text(root, relpath, text[: section.end()] + new_body + text[end:])


def verify_consistency(root):
    """Confirm every version-holding file agrees. Returns (ok, {relpath: version}).

    Orcshot's own RELEASING.md states why this matters: pyproject.toml and debian/changelog
    "must match, or the built .deb's own version won't line up with the source tree that
    produced it." Nothing verified that until now.
    """
    versions = {}
    for rel in detect(root):
        v = read_version(root, rel)
        if v is not None:
            versions[rel] = v
    return (len(set(versions.values())) <= 1, versions)
```

Note: `_changelog_current_version` and `_write_changelog` are referenced above and implemented
in Task 4. Until then those two `debian/changelog` branches raise `NameError` if reached; no test
in this task exercises them.

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
cd skills/orc-release/scripts && python3 -m pytest tests/test_versionfiles.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-release/scripts/orc_release/versionfiles.py \
        skills/orc-release/scripts/tests/test_versionfiles.py
git commit -m "orc-release: version read/write for pyproject and plugin manifests"
```

---

### Task 4: `debian/changelog` support (`versionfiles.py`, part 2)

**Files:**
- Modify: `skills/orc-release/scripts/orc_release/versionfiles.py`
- Modify: `skills/orc-release/scripts/tests/test_versionfiles.py`

**Interfaces:**
- Consumes: `versionfiles`'s existing `read_version`/`write_version` dispatch from Task 3.
- Produces: working `debian/changelog` branches for both, driven by
  `write_version(root, "debian/changelog", version, body="...", debian_revision="1")`.

**Why this is its own task:** `debian/changelog` is structurally unlike every other format. It is
not a field to overwrite but a log to prepend to, its entry format is strict (`dpkg-parsechangelog`
fails on a malformed entry), it is **not idempotent** unless guarded, and both the target series and
the maintainer must be inherited from the previous entry rather than guessed — Orcshot's own
`RELEASING.md` warns that Launchpad rejects an upload whose series is wrong, and `git config` is
whoever runs the command rather than the package's real maintainer.

- [ ] **Step 1: Write the failing tests**

Append to `skills/orc-release/scripts/tests/test_versionfiles.py`:

```python
CHANGELOG = """
    orcshot (0.2.0-1) noble; urgency=medium

      * Adds internationalization.

     -- Orcshot <orc@example.com>  Wed, 26 Aug 2026 21:02:48 -0500

    orcshot (0.1.1-3) noble; urgency=medium

      * Fixes a debconf warning.

     -- Orcshot <orc@example.com>  Sun, 23 Aug 2026 14:45:00 -0500
    """


def test_read_changelog_returns_the_top_entry_version(tmp_path):
    write(tmp_path, "debian/changelog", CHANGELOG)
    assert read_version(str(tmp_path), "debian/changelog") == "0.2.0"


def test_detect_finds_debian_changelog(tmp_path):
    write(tmp_path, "debian/changelog", CHANGELOG)
    assert detect(str(tmp_path)) == ["debian/changelog"]


def test_write_changelog_prepends_a_new_entry(tmp_path):
    p = write(tmp_path, "debian/changelog", CHANGELOG)
    write_version(str(tmp_path), "debian/changelog", "0.3.0", body="* Adds Snap and Flatpak.")
    text = p.read_text()
    assert text.startswith("orcshot (0.3.0-1) noble; urgency=medium")
    assert "orcshot (0.2.0-1) noble; urgency=medium" in text
    assert "Adds Snap and Flatpak." in text


def test_write_changelog_inherits_series_and_maintainer_from_the_previous_entry(tmp_path):
    p = write(
        tmp_path,
        "debian/changelog",
        """
        orcshot (0.2.0-1) jammy; urgency=low

          * Older.

         -- Real Maintainer <real@example.com>  Wed, 26 Aug 2026 21:02:48 -0500
        """,
    )
    write_version(str(tmp_path), "debian/changelog", "0.3.0", body="* New.")
    text = p.read_text()
    assert "orcshot (0.3.0-1) jammy; urgency=low" in text
    assert "-- Real Maintainer <real@example.com>" in text


def test_write_changelog_is_idempotent_for_the_same_version(tmp_path):
    p = write(tmp_path, "debian/changelog", CHANGELOG)
    write_version(str(tmp_path), "debian/changelog", "0.3.0", body="* First.")
    write_version(str(tmp_path), "debian/changelog", "0.3.0", body="* Second.")
    text = p.read_text()
    assert text.count("orcshot (0.3.0-1)") == 1
    assert "Second." in text
    assert "First." not in text


def test_write_changelog_produces_a_parseable_signature_line(tmp_path):
    p = write(tmp_path, "debian/changelog", CHANGELOG)
    write_version(str(tmp_path), "debian/changelog", "0.3.0", body="* New.")
    sig = [line for line in p.read_text().splitlines() if line.startswith(" -- ")][0]
    # Exactly one leading space, then "-- name <email>", then TWO spaces, then the date.
    assert re.match(r"^ -- .+ <.+>  \w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} [+-]\d{4}$", sig)


def test_write_changelog_honours_an_explicit_debian_revision(tmp_path):
    p = write(tmp_path, "debian/changelog", CHANGELOG)
    write_version(
        str(tmp_path), "debian/changelog", "0.3.0", body="* New.", debian_revision="2"
    )
    assert "orcshot (0.3.0-2) noble" in p.read_text()


def test_write_changelog_requires_a_body(tmp_path):
    write(tmp_path, "debian/changelog", CHANGELOG)
    with pytest.raises(ValueError, match="body"):
        write_version(str(tmp_path), "debian/changelog", "0.3.0")


def test_write_changelog_preserves_the_source_package_name(tmp_path):
    p = write(
        tmp_path,
        "debian/changelog",
        "someotherpkg (1.0.0-1) noble; urgency=medium\n\n  * x\n\n"
        " -- M <m@e.com>  Wed, 26 Aug 2026 21:02:48 -0500\n",
    )
    write_version(str(tmp_path), "debian/changelog", "1.1.0", body="* y")
    assert p.read_text().startswith("someotherpkg (1.1.0-1) noble")
```

Add `import re` to the top of the test file if it isn't already imported.

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd skills/orc-release/scripts && python3 -m pytest tests/test_versionfiles.py -v -k changelog
```

Expected: FAIL with `NameError: name '_changelog_current_version' is not defined`.

- [ ] **Step 3: Implement the changelog functions**

Append to `skills/orc-release/scripts/orc_release/versionfiles.py`:

```python
# --- debian/changelog -------------------------------------------------------
#
# Structurally unlike every other format here: a log to prepend to, not a field to overwrite.
# Three things this must get right, each a real failure mode rather than a hypothetical:
#   1. Idempotence. Prepending twice for one version leaves two entries for it; a re-run or a
#      resumed release would do exactly that. Guarded by replacing a matching top entry.
#   2. The target series is inherited from the previous entry, never guessed - Launchpad
#      rejects an upload whose series is not one the PPA supports.
#   3. The maintainer is inherited from the previous entry, not read from `git config` - the
#      previous entry is definitionally what the package uses, while git config is whoever
#      happens to be running the command.

import email.utils

_CL_HEADER = re.compile(
    r"^(?P<source>\S+) \((?P<version>[^)]+)\) (?P<series>\S+); urgency=(?P<urgency>\S+)\s*$",
    re.MULTILINE,
)
_CL_SIGNATURE = re.compile(r"^ -- (?P<maintainer>.+?)  (?P<date>.+?)\s*$", re.MULTILINE)


def _changelog_current_version(text):
    """Upstream version of the top entry (the Debian revision suffix stripped)."""
    m = _CL_HEADER.search(text)
    if not m:
        return None
    return m.group("version").rsplit("-", 1)[0]


def _write_changelog(root, relpath, version, body=None, debian_revision="1", **_ignored):
    if not body or not body.strip():
        raise ValueError("a debian/changelog entry requires a body")

    text = _read_text(root, relpath)
    top = _CL_HEADER.search(text)
    if not top:
        raise ValueError(f"{relpath} has no parseable top entry to inherit from")

    source = top.group("source")
    series = top.group("series")
    urgency = top.group("urgency")

    sig = _CL_SIGNATURE.search(text)
    if not sig:
        raise ValueError(f"{relpath} has no parseable signature line to inherit from")
    maintainer = sig.group("maintainer")

    # Idempotence guard: if the top entry is already this version, replace it rather than
    # stacking a duplicate (a resumed or re-run release hits this for real).
    if _changelog_current_version(text) == version:
        next_header = _CL_HEADER.search(text, top.end())
        rest = text[next_header.start() :] if next_header else ""
    else:
        rest = text

    indented = "\n".join(
        ("  " + line.strip()) if line.strip() else "" for line in body.strip().splitlines()
    )
    entry = (
        f"{source} ({version}-{debian_revision}) {series}; urgency={urgency}\n"
        f"\n{indented}\n\n"
        f" -- {maintainer}  {email.utils.formatdate(localtime=True)}\n"
    )
    _write_text(root, relpath, entry + ("\n" + rest.lstrip("\n") if rest.strip() else ""))
```

- [ ] **Step 4: Run the full versionfiles suite**

```bash
cd skills/orc-release/scripts && python3 -m pytest tests/test_versionfiles.py -v
```

Expected: all PASS, including the Task 3 tests.

- [ ] **Step 5: Verify the output is genuinely valid to Debian's own tooling**

```bash
cd /tmp && rm -rf cl-check && mkdir -p cl-check/debian && cd cl-check
printf 'orcshot (0.2.0-1) noble; urgency=medium\n\n  * Old.\n\n -- M <m@e.com>  Wed, 26 Aug 2026 21:02:48 -0500\n' > debian/changelog
python3 -c "
import sys; sys.path.insert(0, '$HOME/projects/orclab/skills/orc-release/scripts')
from orc_release.versionfiles import write_version
write_version('.', 'debian/changelog', '0.3.0', body='* Real new entry.')
"
dpkg-parsechangelog --show-field Version
dpkg-parsechangelog --show-field Distribution
cd /tmp && rm -rf cl-check
```

Expected: `0.3.0-1` and `noble`. This is the real check that the entry format is correct — the
unit tests confirm the shape, `dpkg-parsechangelog` confirms Debian's own parser accepts it.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-release/scripts/orc_release/versionfiles.py \
        skills/orc-release/scripts/tests/test_versionfiles.py
git commit -m "orc-release: debian/changelog entry prepending, idempotent and format-correct"
```

---

### Task 5: `release-checklist` conventions and `/orc-version --no-commit`

**Files:**
- Modify: `skills/release-checklist/SKILL.md`
- Modify: `commands/orc-version.md`

**Interfaces:**
- Consumes: `orc_release.versionfiles` (Task 3+4) — `/orc-version` delegates to it.
- Produces: documentation only; no new code interfaces.

**Why these are one task:** both are prose edits to existing files, of the same shape and the same
size, and a reviewer would sensibly accept or reject them together.

- [ ] **Step 1: Add the four conventions to `release-checklist`**

In `skills/release-checklist/SKILL.md`, immediately after the "Structuring steps" section's
existing bullet list (which ends with the "What 'done' looks like" bullet), insert:

```markdown
### Optional markers a step can carry

Four optional prose markers. They are read by `/orc-release` when it drives the checklist, but
they are written for a human first — someone following the document by hand wants "don't start
this if X" every bit as much as an automated runner does. **All four are optional; a document
using none of them is still complete and still driveable.**

- **Preconditions** — what must be true before the step starts, written as
  `**Preconditions:** <what must be true>`. Prefer the specific and checkable ("this version is
  not already published to the PPA") over the generic ("everything is ready").
- **Performed by hand** — `**Performed by hand.**` for a step (or part of one) a person carries
  out rather than a command: a click in a web UI, a manual install-test on real hardware, a
  visual confirmation. A step may be partly manual; say so where the manual part begins.
- **Delegation** — `**Run:** /some-command` when the step's work is done by an existing command
  rather than by literal shell commands written out here.
- **Irreversible** — `**Irreversible.**` when the step does something that cannot be undone:
  publishing to a public archive, pushing a tag, creating a release. This is what lets an
  abandoned release distinguish what can be rolled back from what merely has to be reported.
```

- [ ] **Step 2: Add the `--no-commit` flow to `/orc-version`**

In `commands/orc-version.md`, replace the **"Apply the new version"** section's numbered list
items 2 and 3 (the "Update manifests, if present" and "Commit" steps) with:

```markdown
2. **Update every version-holding file.**

   Run Orclab's own version-file module rather than hand-editing — it is the single owner of
   version-setting, it handles each format's real syntax, and it is covered by real tests. The
   script lives at `<orclab plugin root>/skills/orc-release/scripts/run.py`, where the plugin
   root is the parent of the `commands/` directory this file lives in:

   ```bash
   python3 <orclab plugin root>/skills/orc-release/scripts/run.py version-set X.Y.Z
   ```

   For a project with a `debian/changelog`, pass the changelog body too (the same content
   drafted in step 1, as Debian-style `*` bullets):

   ```bash
   python3 <...>/run.py version-set X.Y.Z --changelog-body '* What changed.'
   ```

   Supported formats: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
   `pyproject.toml`, `debian/changelog`. A project using none of them has no version file to
   update; say so plainly rather than inventing one.

   Then confirm every file agrees:

   ```bash
   python3 <...>/run.py version-verify
   ```

3. **Commit — unless `--no-commit` was passed.**

   If `$ARGUMENTS` contains `--no-commit`, **stop here**. Report the new version and which files
   were changed, and do not commit or tag. This exists because a real release process often
   separates setting the version from committing it: a packaged app builds, lints, publishes and
   install-tests against the uncommitted version edits, and commits only once the artifact is
   verified — so committing at bump time would leave a `Release vX.Y.Z` commit behind for every
   attempt that never released.

   Otherwise (the default, unchanged behavior):

   ```bash
   git add CHANGELOG.md .claude-plugin/plugin.json .claude-plugin/marketplace.json
   git commit -m "Bump version to X.Y.Z"
   ```

   (Only `git add` the files that actually exist and were updated.)
```

Also add `[--no-commit]` to the `argument-hint` frontmatter field so the flag is discoverable.

- [ ] **Step 3: Verify the two files are still coherent**

```bash
grep -n "no-commit" commands/orc-version.md
grep -n "Optional markers" skills/release-checklist/SKILL.md
head -4 commands/orc-version.md
```

Expected: the `--no-commit` flow and the marker section are both present, and `orc-version.md`'s
frontmatter still parses (a `description:` line and an `argument-hint:` line, no stray edits).

- [ ] **Step 4: Commit**

```bash
git add skills/release-checklist/SKILL.md commands/orc-version.md
git commit -m "release-checklist: four optional step markers; orc-version: --no-commit"
```

---

### Task 6: CLI orchestration (`cli.py`, `run.py`)

**Files:**
- Create: `skills/orc-release/scripts/orc_release/cli.py`
- Create: `skills/orc-release/scripts/run.py`
- Test: `skills/orc-release/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: `steps.parse_steps`, `steps.doc_hash` (Task 1); all of `state` (Task 2);
  `versionfiles.detect/read_version/write_version/verify_consistency` (Tasks 3-4).
- Produces: `orc_release.cli.main(argv=None) -> int`, exposing subcommands `steps`, `status`,
  `start`, `complete`, `skip`, `abort`, `version-set`, `version-verify`, `version-rollback`.

- [ ] **Step 1: Write the failing tests**

Create `skills/orc-release/scripts/tests/test_cli.py`:

```python
import json
import textwrap

from orc_release.cli import main
from orc_release.state import STATE_PATH, load_state


DOC = textwrap.dedent(
    """
    # Cutting a release

    ## 1. Pick a version

    Edit the files.

    ## 2. Upload

    **Irreversible.** Once uploaded it cannot be undone.

    ## 3. Verify

    **Performed by hand.** Check it works.
    """
)


def setup_project(tmp_path, doc=DOC):
    (tmp_path / "RELEASING.md").write_text(doc)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "0.1.0"\n'
    )
    return str(tmp_path)


def test_steps_subcommand_emits_parseable_json(tmp_path, capsys):
    root = setup_project(tmp_path)
    assert main(["--root", root, "steps"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert [s["number"] for s in data] == [1, 2, 3]
    assert data[1]["is_irreversible"] is True
    assert data[2]["is_manual"] is True


def test_steps_reports_plainly_when_there_is_no_releasing_md(tmp_path, capsys):
    assert main(["--root", str(tmp_path), "steps"]) == 1
    assert "RELEASING.md" in capsys.readouterr().err


def test_status_with_no_release_says_so(tmp_path, capsys):
    root = setup_project(tmp_path)
    assert main(["--root", root, "status"]) == 0
    assert "no release in progress" in capsys.readouterr().out.lower()


def test_start_records_state_with_the_doc_hash(tmp_path):
    root = setup_project(tmp_path)
    assert main(["--root", root, "start", "0.2.0"]) == 0
    state = load_state(root)
    assert state["version"] == "0.2.0"
    assert state["previous_version"] == "0.1.0"
    assert state["doc_hash"]


def test_start_refuses_when_a_release_is_already_in_progress(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    assert main(["--root", root, "start", "0.3.0"]) == 1
    assert "already in progress" in capsys.readouterr().err


def test_status_reports_the_next_step(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "complete", "1"])
    main(["--root", root, "status"])
    assert "2" in capsys.readouterr().out


def test_complete_records_irreversibility_from_the_document(tmp_path):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "complete", "2"])
    entry = [c for c in load_state(root)["completed"] if c["number"] == 2][0]
    assert entry["irreversible"] is True


def test_skip_requires_a_reason(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    assert main(["--root", root, "skip", "1", "--reason", "  "]) == 1
    assert "reason" in capsys.readouterr().err


def test_skip_records_the_reason(tmp_path):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "skip", "1", "--reason", "done by hand earlier"])
    assert load_state(root)["skipped"][0]["reason"] == "done by hand earlier"


def test_status_warns_when_the_document_changed_mid_release(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    (tmp_path / "RELEASING.md").write_text(DOC + "\n## 4. A new step\n\nInserted later.\n")
    main(["--root", root, "status"])
    out = capsys.readouterr().out.lower()
    assert "changed" in out


def test_version_set_writes_and_verify_confirms(tmp_path, capsys):
    root = setup_project(tmp_path)
    assert main(["--root", root, "version-set", "0.2.0"]) == 0
    assert 'version = "0.2.0"' in (tmp_path / "pyproject.toml").read_text()
    assert main(["--root", root, "version-verify"]) == 0
    assert "consistent" in capsys.readouterr().out.lower()


def test_version_verify_fails_on_a_real_mismatch(tmp_path, capsys):
    root = setup_project(tmp_path)
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin/plugin.json").write_text('{"name": "x", "version": "9.9.9"}')
    assert main(["--root", root, "version-verify"]) == 1
    assert "9.9.9" in capsys.readouterr().err


def test_version_rollback_restores_the_previous_version(tmp_path):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "version-set", "0.2.0"])
    assert main(["--root", root, "version-rollback"]) == 0
    assert 'version = "0.1.0"' in (tmp_path / "pyproject.toml").read_text()


def test_abort_reports_a_completed_irreversible_step_as_standing(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "complete", "2"])
    assert main(["--root", root, "abort"]) == 0
    out = capsys.readouterr().out.lower()
    assert "cannot" in out or "not undone" in out
    assert "upload" in out
    assert load_state(root) is None


def test_abort_on_a_document_with_no_markers_says_it_cannot_determine(tmp_path, capsys):
    root = setup_project(
        tmp_path, doc="# R\n\n## 1. One\n\nDo it.\n\n## 2. Two\n\nDo it.\n"
    )
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "complete", "1"])
    main(["--root", root, "abort"])
    assert "cannot determine" in capsys.readouterr().out.lower()


def test_abort_with_no_release_in_progress_is_reported_not_crashed(tmp_path, capsys):
    root = setup_project(tmp_path)
    assert main(["--root", root, "abort"]) == 1
    assert "no release in progress" in capsys.readouterr().err.lower()
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd skills/orc-release/scripts && python3 -m pytest tests/test_cli.py -v
```

Expected: `ModuleNotFoundError: No module named 'orc_release.cli'`.

- [ ] **Step 3: Implement `cli.py`**

Create `skills/orc-release/scripts/orc_release/cli.py`:

```python
"""/orc-release CLI: the deterministic half of driving a release.

This script never decides whether a step passed - that is Claude's judgment, made against the
document's own "what done looks like". What lives here is what must be exactly right every time:
parsing the document, tracking position, and writing version files.

There is no confirmation prompt anywhere in this module. The gates are conversational and live
in SKILL.md, the same division /orc-publish uses.
"""

import argparse
import dataclasses
import json
import os
import sys

from . import state as st
from . import versionfiles as vf
from .steps import doc_hash, parse_steps

DOC_NAME = "RELEASING.md"


def _load_doc(root):
    """Return (text, steps) or (None, None) after reporting a missing document."""
    path = os.path.join(root, DOC_NAME)
    try:
        with open(path) as f:
            text = f.read()
    except FileNotFoundError:
        print(
            f"error: no {DOC_NAME} in this project - nothing to drive. "
            f"Use the release-checklist skill to create one; never invent a release process.",
            file=sys.stderr,
        )
        return None, None
    return text, parse_steps(text)


def _require_state(root):
    state = st.load_state(root)
    if state is None:
        print("error: no release in progress", file=sys.stderr)
    return state


def cmd_steps(root, _args):
    text, steps = _load_doc(root)
    if text is None:
        return 1
    print(json.dumps([dataclasses.asdict(s) for s in steps], indent=2))
    return 0


def cmd_status(root, _args):
    state = st.load_state(root)
    if state is None:
        print("No release in progress.")
        return 0
    text, steps = _load_doc(root)
    if text is None:
        return 1
    print(f"Release {state['version']} in progress (was {state['previous_version']}).")
    if doc_hash(text) != state["doc_hash"]:
        print(
            f"WARNING: {DOC_NAME} has CHANGED since this release started. Step numbers may "
            f"have shifted - re-read it before continuing."
        )
    done = st.completed_numbers(state)
    print(f"Completed: {done or 'none'}")
    for s in state.get("skipped", []):
        print(f"  skipped {s['number']} ({s['title']}): {s['reason']}")
    nxt = st.next_step_number(state, [s.number for s in steps])
    print(f"Next: step {nxt}" if nxt else "All steps finished.")
    return 0


def cmd_start(root, args):
    if st.is_in_progress(root):
        print(
            "error: a release is already in progress - resume it or abort it first",
            file=sys.stderr,
        )
        return 1
    text, _ = _load_doc(root)
    if text is None:
        return 1
    detected = vf.detect(root)
    previous = vf.read_version(root, detected[0]) if detected else None
    st.start_release(root, args.version, previous, DOC_NAME, doc_hash(text))
    print(f"Started release {args.version} (previous: {previous}).")
    return 0


def _step_by_number(steps, number):
    for s in steps:
        if s.number == number:
            return s
    return None


def cmd_complete(root, args):
    state = _require_state(root)
    if state is None:
        return 1
    text, steps = _load_doc(root)
    if text is None:
        return 1
    step = _step_by_number(steps, args.number)
    if step is None:
        print(f"error: no step {args.number} in {DOC_NAME}", file=sys.stderr)
        return 1
    st.mark_complete(state, step.number, step.title, irreversible=step.is_irreversible)
    st.save_state(root, state)
    print(f"Step {step.number} ({step.title}) complete.")
    return 0


def cmd_skip(root, args):
    state = _require_state(root)
    if state is None:
        return 1
    text, steps = _load_doc(root)
    if text is None:
        return 1
    step = _step_by_number(steps, args.number)
    if step is None:
        print(f"error: no step {args.number} in {DOC_NAME}", file=sys.stderr)
        return 1
    try:
        st.mark_skipped(state, step.number, step.title, args.reason)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    st.save_state(root, state)
    print(f"Step {step.number} ({step.title}) skipped: {args.reason.strip()}")
    return 0


def cmd_abort(root, _args):
    state = _require_state(root)
    if state is None:
        return 1
    text, steps = _load_doc(root)
    marked = {s.number for s in (steps or []) if s.is_irreversible}
    completed = state.get("completed", [])

    if state.get("previous_version"):
        for rel in vf.detect(root):
            if rel == vf.DEBIAN_CHANGELOG:
                continue  # a prepended entry is removed by hand; never rewrite history blindly
            try:
                vf.write_version(root, rel, state["previous_version"])
            except ValueError:
                pass
        print(f"Rolled version files back to {state['previous_version']}.")

    if completed and not marked:
        print(
            "Completed steps: "
            + ", ".join(f"{c['number']} ({c['title']})" for c in completed)
        )
        print(
            "This document marks no steps irreversible, so I CANNOT DETERMINE which of these "
            "had effects outside this repo. Check them yourself before assuming anything was "
            "undone."
        )
    else:
        for c in st.irreversible_completed(state):
            print(
                f"Step {c['number']} ({c['title']}) is irreversible and completed - "
                f"it STANDS and was not undone."
            )
    if vf.DEBIAN_CHANGELOG in vf.detect(root):
        print(
            f"Note: {vf.DEBIAN_CHANGELOG}'s new entry was left in place - remove it by hand if "
            f"you want it gone."
        )
    st.clear_state(root)
    print("Release aborted; state cleared.")
    return 0


def cmd_version_set(root, args):
    detected = vf.detect(root)
    if not detected:
        print("error: no known version-holding file in this project", file=sys.stderr)
        return 1
    for rel in detected:
        kwargs = {}
        if rel == vf.DEBIAN_CHANGELOG:
            if not args.changelog_body:
                print(
                    f"error: {rel} needs --changelog-body (its entry is prose, not a field)",
                    file=sys.stderr,
                )
                return 1
            kwargs["body"] = args.changelog_body
        vf.write_version(root, rel, args.version, **kwargs)
        print(f"Set {rel} to {args.version}.")
    return 0


def cmd_version_verify(root, _args):
    ok, versions = vf.verify_consistency(root)
    if ok:
        print(f"Version files are consistent: {versions or 'none found'}")
        return 0
    print(f"error: version files disagree: {versions}", file=sys.stderr)
    return 1


def cmd_version_rollback(root, _args):
    state = _require_state(root)
    if state is None:
        return 1
    previous = state.get("previous_version")
    if not previous:
        print("error: no previous version recorded to roll back to", file=sys.stderr)
        return 1
    for rel in vf.detect(root):
        if rel == vf.DEBIAN_CHANGELOG:
            continue
        vf.write_version(root, rel, previous)
        print(f"Rolled {rel} back to {previous}.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="orc-release")
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("steps")
    sub.add_parser("status")
    sub.add_parser("abort")
    sub.add_parser("version-verify")
    sub.add_parser("version-rollback")

    p_start = sub.add_parser("start")
    p_start.add_argument("version")

    p_complete = sub.add_parser("complete")
    p_complete.add_argument("number", type=int)

    p_skip = sub.add_parser("skip")
    p_skip.add_argument("number", type=int)
    p_skip.add_argument("--reason", required=True)

    p_vset = sub.add_parser("version-set")
    p_vset.add_argument("version")
    p_vset.add_argument("--changelog-body")

    args = parser.parse_args(argv)
    handlers = {
        "steps": cmd_steps,
        "status": cmd_status,
        "start": cmd_start,
        "complete": cmd_complete,
        "skip": cmd_skip,
        "abort": cmd_abort,
        "version-set": cmd_version_set,
        "version-verify": cmd_version_verify,
        "version-rollback": cmd_version_rollback,
    }
    return handlers[args.cmd](args.root, args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Create the entry point**

Create `skills/orc-release/scripts/run.py`:

```python
#!/usr/bin/env python3
"""Entry point for SKILL.md: puts the orc_release package on sys.path, then runs its CLI."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orc_release.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the whole suite**

```bash
cd skills/orc-release/scripts && python3 -m pytest tests/ -v
```

Expected: every test across all four test files PASSES.

- [ ] **Step 6: Verify invocation-independence (the `conftest.py` from Task 1)**

```bash
cd skills/orc-release/scripts && pytest tests/ -q
cd ~/projects/orclab && python3 -m pytest skills/orc-release/scripts/tests/ -q
```

Expected: both report the same passing count. A "collected 0 items" from the repo root means
`conftest.py` is missing or misplaced.

- [ ] **Step 7: Commit**

```bash
git add skills/orc-release/scripts/orc_release/cli.py \
        skills/orc-release/scripts/run.py \
        skills/orc-release/scripts/tests/test_cli.py
git commit -m "orc-release: CLI orchestration for steps, state, and version files"
```

---

### Task 7: `SKILL.md` — the conversational runner

**Files:**
- Create: `skills/orc-release/SKILL.md`

**Interfaces:**
- Consumes: `skills/orc-release/scripts/run.py` (Task 6), invoked via
  `${CLAUDE_SKILL_DIR}/scripts/run.py`.
- Produces: the user-facing `/orc-release` behavior.

- [ ] **Step 1: Write `SKILL.md`**

Create `skills/orc-release/SKILL.md`:

```markdown
---
name: orc-release
description: Use when the user explicitly asks to use orc-release, or types /orc-release, to drive a project's own RELEASING.md release process end to end - running its ordered steps, enforcing its gates, and tracking where the release is across sessions.
allowed-tools: Bash(python3 *), Bash(git status *)
---

# orc-release

Drives this project's own `RELEASING.md` from start to finish. `RELEASING.md` is the single
definition of the steps — this skill never invents a release process, and never reorders one.

**This halts on failure.** That is deliberate and is the opposite of `/orc-publish`, which
continues past a failed channel. Publish channels are independent siblings; release steps are a
dependent chain, where step 6 uploading irreversibly to a public archive is only valid because
step 2's tests actually passed.

## Step 0: Read the whole document first

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py steps
```

If this reports no `RELEASING.md`, tell the user plainly and stop — suggest the
`release-checklist` skill for creating one. Never invent steps.

Then **read the real `RELEASING.md` yourself, in full, before acting on any step.** The script
gives you structure; the document gives you the actual instructions, the gates, and the reasons
each step exists. Acting on step N without having read steps N+1 onward is the specific failure
this skill exists to prevent.

## Step 1: Establish where you are

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py status
```

- **A release is in progress** → report the position and resume at the next step. If status warns
  the document CHANGED, stop and tell the user: step numbers may have shifted, so re-read the
  document before continuing.
- **No release in progress** → this is a new release; continue to Step 2.
- `/orc-release status` on its own is a read-only query: report and stop.

## Step 2: Starting a new release (skip entirely when resuming)

Show the working tree before anything else:

```
git status --short
```

Show the user **the real output, verbatim**. This is not a formality: a bare "the tree is dirty"
gets waved through, while a real file list makes unrelated in-progress work instantly
recognizable. Ask whether to proceed. **This never blocks** — it is a stop-and-ask, and only
happens when starting, never on resume (a release legitimately dirties the tree at step 1).

Then confirm the target version with the user and start:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py start X.Y.Z
```

## Step 3: Walk the steps in order

For each step, in the document's own order:

1. **Check its preconditions**, if it states any. If one fails, stop and report — do not proceed.
2. **Carry it out:**
   - Marked **performed by hand** → present what the human must do, then stop and wait for their
     confirmation. Record what they say they did; never mark it complete on your own.
   - Marked **Run: /some-command** → invoke that command. If it reports any failure, this step has
     failed.
   - Otherwise → run the document's own commands.
3. **Judge the result against the document's own "what done looks like."** Not "did it exit 0" —
   the document's stated bar.
4. On success:
   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/run.py complete <N>
   ```
5. On failure: **stop.** Report what failed and the real output. Do not retry, do not skip, do not
   continue to the next step. The user fixes it and re-runs `/orc-release`, which resumes here.

## Skipping a step

Only when the user explicitly asks, and only with a real reason:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py skip <N> --reason "<why>"
```

Never skip a step on your own initiative.

## Aborting

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py abort
```

Relay its output exactly. It rolls back version-file edits and reports which completed steps
cannot be undone. **Never claim more was undone than it actually reports** — telling someone a
release was cleaned up when a public upload already happened is worse than saying nothing.

## Version handling

Version files are set through `/orc-version` (which delegates to this same script), so there is
one implementation. Within a release, pass `--no-commit` so the version is set at step 1 without
committing — the document's own later step does the committing, once the artifact is verified.

After setting a version, always confirm the files agree:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py version-verify
```

## Notes

- A document using none of the optional markers is completely valid. You simply have less
  information: ask the user rather than assuming a step is safe to automate.
- Report each step's real output. Never paraphrase a failure into something softer.
```

- [ ] **Step 2: Verify the skill's frontmatter and script path resolve**

```bash
python3 - <<'EOF'
import os, re
p = "skills/orc-release/SKILL.md"
text = open(p).read()
assert text.startswith("---"), "missing frontmatter"
fm = text.split("---")[1]
assert re.search(r"^name: orc-release$", fm, re.M), "bad name"
assert re.search(r"^description: ", fm, re.M), "missing description"
target = os.path.normpath(os.path.join("skills/orc-release", "scripts/run.py"))
assert os.path.exists(target), f"script path does not resolve: {target}"
print("SKILL.md OK; script path resolves to", target)
EOF
```

Expected: `SKILL.md OK; script path resolves to skills/orc-release/scripts/run.py`.

- [ ] **Step 3: Commit**

```bash
git add skills/orc-release/SKILL.md
git commit -m "orc-release: SKILL.md, the conversational runner"
```

---

### Task 8: Version bump to 0.8.0, docs, verification scenarios, **and the git tag**

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `VERIFICATION.md`

**Interfaces:**
- Consumes: everything from Tasks 1-7.
- Produces: a tagged 0.8.0 release of Orclab.

**This task exists in this exact shape because of a real, repeated failure.** BACKLOG #9 and #13
record two consecutive Orclab releases (`v0.5.0`, `v0.7.0`) that shipped **untagged**, both because
the implementing plan folded the version bump into a task that omitted the tag step. #9's stated
mitigation was "remember to copy the tag step next time"; v7's plan was written after that and
omitted it anyway. **The git tag is Step 6 below and is not optional.**

- [ ] **Step 1: Bump both manifests to 0.8.0**

In `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` (the latter has the version
in `plugins[0]`), change `"version": "0.7.0"` to `"version": "0.8.0"`. Append to the shared
description text in both files (all three occurrences — top-level in both, plus `plugins[0]` in
marketplace.json): `" /orc-release drives a project's own RELEASING.md end to end."`

- [ ] **Step 2: Add the `CHANGELOG.md` entry**

Insert directly below the `# Changelog` header block, above the existing `## [0.7.0]` entry:

```markdown
## [0.8.0] - 2026-09-07

### Added
- `/orc-release` — drives a project's own `RELEASING.md` end to end: reads the whole document
  before acting, walks its steps in real dependency order, halts on failure (deliberately the
  opposite of `/orc-publish`, since release steps are a dependent chain and publish channels are
  independent siblings), stops for human-performed steps, and tracks position across sessions in
  `.orclab/release/state.json` — a cursor holding only *where* a release is, never a second copy
  of its steps.
- Version-lifecycle handling across a whole release: per-format read/write for `pyproject.toml`,
  `debian/changelog`, `.claude-plugin/plugin.json` and `marketplace.json`; consistency
  verification after setting; and rollback on abort that reports plainly what it cannot undo.
  Closes BACKLOG #6.
- `/orc-version --no-commit` — sets the version without committing, so a release can build, lint,
  publish and install-test against the uncommitted edits and commit only once the artifact is
  verified. The previous behavior (bump, commit, tag as one move) is unchanged by default.

### Changed
- `release-checklist` documents four optional step markers — preconditions, performed-by-hand,
  delegation, and irreversible — all backward-compatible, since a document using none of them
  stays fully driveable.
```

- [ ] **Step 3: Update `README.md`**

Add to the Commands section, after the `/orc-publish` bullet:

```markdown
- **/orc-release** — drive this project's own `RELEASING.md` end to end: ordered steps, real
  gates, human-step handoffs, and a position cursor so a release survives across sessions. Halts
  on failure. Ships as a skill only.
```

Update the Status line to append `+ v8 (\`/orc-release\`)` after the v7 mention.

- [ ] **Step 4: Add `VERIFICATION.md` scenarios**

Append after the existing Scenario 26:

```markdown
## Scenario 27: /orc-release refuses to invent a process

1. In a throwaway scratch directory with no `RELEASING.md`, run `/orc-release`.
2. **Expected:** it reports plainly that there's no `RELEASING.md` and stops, suggesting
   `release-checklist`. It must not propose or invent any steps.

## Scenario 28: /orc-release halts on a failed step

1. In a throwaway scratch directory, create a synthetic `RELEASING.md`:
   ```markdown
   # Cutting a test release

   ## 1. First

   Run: `echo one`

   ## 2. Fails

   Run: `exit 1`

   ## 3. Never reached

   Run: `echo three`
   ```
   Add a `pyproject.toml` with `[project]`, a `name`, and `version = "0.1.0"`.
2. Run `/orc-release`, proceed past the working-tree report, and let it run.
3. **Expected:** step 1 completes, step 2 fails and the run **stops there** — step 3 never runs.
   The real error output is reported, not paraphrased.

## Scenario 29: /orc-release resumes at the right step

1. Continuing from Scenario 28, fix step 2 (change `exit 1` to `echo two`) and run
   `/orc-release` again.
2. **Expected:** it resumes at step 2 — not step 1 — and warns that `RELEASING.md` changed since
   the release started.

## Scenario 30: /orc-release refuses to start a second release

1. With Scenario 28's release still in progress, ask to start a new release.
2. **Expected:** refused, with a plain statement that one is already in progress and that you must
   resume or abort it.

## Scenario 31: the entry working-tree report

1. In the scratch project, create a stray file (`touch scratch-file.txt`), abort any in-progress
   release, and start a fresh one.
2. **Expected:** the real `git status --short` output is shown, including `scratch-file.txt`, and
   you're asked whether to proceed. Answering yes continues normally — it must not block.
3. Stop mid-release and resume.
4. **Expected:** the working-tree report does **not** fire again on resume.

## Scenario 32: a skip is recorded with its reason

1. Mid-release, ask to skip a step, giving a reason.
2. **Expected:** it's recorded with that reason, and `/orc-release status` shows it. Asking to
   skip with no reason is refused.

## Scenario 33: abort is honest about what it can't undo

1. Create a synthetic `RELEASING.md` where step 2 carries `**Irreversible.**`, run the release
   through step 2, then abort.
2. **Expected:** version files are rolled back to the previous version, and step 2 is reported as
   irreversible, completed, and **standing** — not claimed as undone.
3. Repeat with a document carrying **no** markers at all.
4. **Expected:** abort states plainly that it **cannot determine** which completed steps had
   external effects, rather than guessing.

## Scenario 34: a human-performed step stops for the human

1. Create a synthetic `RELEASING.md` with a step marked `**Performed by hand.**`.
2. Run the release up to it.
3. **Expected:** it presents what to do and stops, waiting for your confirmation — it does not
   run anything for that step or mark it complete on its own.
```

- [ ] **Step 5: Run the full suite and confirm manifests agree**

```bash
cd skills/orc-release/scripts && python3 -m pytest tests/ -q
cd ~/projects/orclab && grep -h '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json
```

Expected: all tests pass; every version line reads `0.8.0`.

- [ ] **Step 6: Commit AND TAG**

**Do not skip the tag.** Two previous Orclab releases shipped untagged because a plan omitted
exactly this step (BACKLOG #9, #13).

```bash
cd ~/projects/orclab
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json \
        CHANGELOG.md README.md VERIFICATION.md
git commit -m "orc-release: bump to 0.8.0, CHANGELOG, README, VERIFICATION scenarios"
git tag v0.8.0
git tag --list 'v*'
```

Expected: `git tag --list 'v*'` shows `v0.3.0` through `v0.8.0` with **no gaps**. The tag stays
local — pushing it is a separate, explicit release action, per Orclab's existing convention.
