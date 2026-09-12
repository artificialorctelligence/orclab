# Orclab v17: `/orc-test` and `test-discipline` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A background `test-discipline` skill that governs every test Claude writes, and an `/orc-test` command that runs, measures (coverage 80%, mutation/TCE 70%, test lint) and repairs test suites across eight languages.

**Architecture:** `skills/test-discipline/SKILL.md` is prose only. `skills/orc-test/scripts/orc_test/` is a Python package in the `/orc-todo` shape: `run.py` entry point → `cli.py` subcommands (`detect`, `run`, `coverage`, `analyze`) → one module per language under `langs/` sharing a fixed contract, with the report parsers (`lcov`, `stryker`, `jacoco`, `pitest`) shared where formats are shared. `generate` is prose in `SKILL.md`: Claude writes tests from `analyze`'s result file; `run.py` only measures. Each `languages/<lang>.md` is the researched, dated tooling knowledge for one language.

**Tech Stack:** Python 3.12 stdlib + PyYAML (already used by `orc-publish`), pytest for the package's own tests. No new dependencies. External tools (pytest-cov, mutmut, Stryker, Pitest, …) are invoked by subprocess and never bundled.

**Spec:** `docs/superpowers/specs/2026-09-11-orclab-v17-orc-test-design.md`. Read it first.

## Global Constraints

- Thresholds: **80%** lines coverage, **70%** mutation score (TCE), per language, overridable in `.orclab/test.yaml` (`coverage:`, `tce:`).
- Every external command `run.py` executes is printed as `$ <command>` before it runs.
- The gate is computed by `run.py` from each tool's report file; never from the tool's own threshold flag.
- Python commands always pass `--ignore=mutants` to pytest (mutmut 3 copies tests into `mutants/`).
- A missing tool is named with its install line and that language is skipped; nothing is installed.
- `run.py` never runs git and never writes outside `.orclab/test/` and the tools' own output dirs.
- When a measurement is impossible for a language, the report says so in words from the language module's `CAVEATS`/`MUTATION_UNAVAILABLE`; never a fake number.
- New skill is named `orc-test` (the `orc` prefix is what `/orc-help` enumerates). `test-discipline` has no prefix on purpose: it is not a command.
- Package tests run with `cd skills/orc-test/scripts && python3 -m pytest tests/ -v` and must stay green at every commit.
- Fixture files under `tests/fixtures/` are real tool output where it could be captured (marked `# captured 2026-09-11`) or built from the tool's documented schema (marked `# from documented schema — verify on first real run`).
- Commit after every task. Commit messages describe what changed. End each with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## File Structure

```
skills/test-discipline/SKILL.md                 Task 1
skills/orc-test/
├── SKILL.md                                    Task 6 (v1), Task 17 (final)
├── languages/{python,javascript,java,kotlin,csharp,dart,swift,gdscript}.md   Tasks 9–16
└── scripts/
    ├── run.py                                  Task 2
    ├── conftest.py                             Task 2 (empty)
    ├── orc_test/
    │   ├── __init__.py                         Task 2
    │   ├── model.py        Coverage / Mutation / Survivor / Finding dataclasses     Task 2
    │   ├── runner.py       run(cmd, cwd) — prints, executes, captures              Task 2
    │   ├── config.py       .orclab/test.yaml → thresholds + overrides               Task 3
    │   ├── detect.py       which languages, declared test commands                 Task 3
    │   ├── lcov.py         lcov → Coverage                                          Task 4
    │   ├── cli.py          argparse + subcommands                                   Tasks 6–8
    │   ├── stryker.py      Stryker JSON → Mutation (JS, C#)                         Task 10
    │   ├── jacoco.py       JaCoCo XML → Coverage (Java, Kotlin/Kover)               Task 11
    │   ├── pitest.py       Pitest XML → Mutation (Java, Kotlin)                     Task 11
    │   ├── licence.py      open-source licence detection (Kotlin/Arcmutate gate)    Task 12
    │   └── langs/
    │       ├── __init__.py  ALL = [python, javascript, ...] in table order          Task 5
    │       ├── python.py                                                            Task 5
    │       ├── javascript.py                                                        Task 10
    │       ├── java.py                                                              Task 11
    │       ├── kotlin.py                                                            Task 12
    │       ├── csharp.py                                                            Task 13
    │       ├── dart.py                                                              Task 14
    │       ├── swift.py                                                             Task 15
    │       └── gdscript.py                                                          Task 16
    └── tests/
        ├── fixtures/...
        └── test_*.py
```

### The language-module contract (every `langs/<lang>.py` implements exactly this)

```python
KEY = "python"                  # used in .orclab/test.yaml and the analyze result file
LABEL = "Python"                # used in reports
MARKERS = ["pyproject.toml", "setup.py", "setup.cfg"]   # glob patterns, matched at depth ≤ 2
TOOLS = {"pytest_cov": "pip install pytest-cov", ...}   # tools `run`/`coverage` need → install line
CAVEATS = ["..."]               # sentences printed under the language's report block

def missing(root) -> list[str]                     # names from TOOLS that are not installed
def test_cmd(root, target) -> list[str]            # target: path relative to root, or None
def coverage_cmd(root, target, out) -> list[str]   # writes report(s) into Path `out`
def coverage_parse(root, out) -> Coverage
def mutation_unavailable(root) -> str | None       # a sentence when TCE cannot be measured (no tool
                                                   # for the language, tool not installed, licence)
def mutation_cmd(root, target, out) -> list[str]   # only called when mutation_unavailable is None
def mutation_parse(root, out) -> Mutation
def lint(root, target, out) -> list[Finding] | str # a str is the reason lint did not run
```

`TOOLS` lists only what `run` and `coverage` need; a missing mutation or lint tool is reported
inside `analyze`'s block for that language, not by skipping the language.

`target` is the path argument the user gave, relative to `root`, or `None` for the whole project.
`out` is a fresh directory `root/.orclab/test/<KEY>/` that `cli.py` creates before calling.

---

### Task 1: `test-discipline` skill

**Files:**
- Create: `skills/test-discipline/SKILL.md`
- Test: `hooks/scripts/tests/test_test_discipline_frontmatter.py`

**Interfaces:**
- Produces: nothing programmatic. `skills/orc-test/SKILL.md` (Task 17) and `languages/*.md` refer to it by name.

- [ ] **Step 1: Write the failing test**

```python
# hooks/scripts/tests/test_test_discipline_frontmatter.py
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "test-discipline" / "SKILL.md"


def _frontmatter():
    text = SKILL.read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md must start with YAML frontmatter"
    return dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)


def test_is_background_only():
    fm = _frontmatter()
    assert fm["name"].strip() == "test-discipline"
    assert fm["user-invocable"].strip() == "false"
    assert "disable-model-invocation" not in fm


def test_six_rules_and_points_at_tdd():
    text = SKILL.read_text()
    for n in range(1, 7):
        assert re.search(rf"^## {n}\. ", text, re.M), f"rule {n} missing"
    assert "superpowers:test-driven-development" in text
    assert "/orc-test coverage" in text
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd hooks/scripts && python3 -m pytest tests/test_test_discipline_frontmatter.py -v`
Expected: FAIL — `FileNotFoundError` on `SKILL.read_text()`.

- [ ] **Step 3: Write the skill**

```markdown
---
name: test-discipline
description: Background rules for any test Claude is about to write or change, in any language - inside /orc-code, inside a subagent executing a plan, inside a bug fix. Know the code and the scenarios first, TDD, realistic data, mock everything that leaves the process, prove the test can fail, 80% line coverage on what the change touches. Not a command; Claude reads it whenever a test is about to be written.
user-invocable: false
---

# Test Discipline

The failure this exists to close: a test that calls the code and asserts nothing scores 100% on
lines and catches nothing. Every rule here is a way of making sure a test written under Orclab is
*proven* to catch something, not assumed to.

Applies whenever a test is about to be written or changed — a new feature, a bug fix, a refactor,
a subagent's task — whatever the language. The rules are in the order the work happens.

## 1. Know what you are testing before you write

- The code under test is open in front of you, not remembered.
- The project's framework and runner are known. `skills/orc-test/languages/<lang>.md` says which
  for each language `/orc-test` supports; a project's own config wins over that file.
- The scenarios that matter are listed *before* any test exists: empty and null inputs, a large
  input, the async path, the error path, the boundary the code's own `if` names.

## 2. TDD — one law, not two

State the expected behaviour in one plain sentence, write the test, watch it fail, then write the
code. That is `superpowers:test-driven-development`, which every session already loads; this
rule points at it and adds nothing. If you did not watch the test fail, you do not know it tests
the right thing.

## 3. Realistic data

Test data that looks like production, including the edge cases the code's shape alone would not
suggest — a name with a quote in it, a date at a month boundary, a list of ten thousand, a
zero-length file. Not `foo`, `bar`, `1`, `2`.

## 4. Isolation

Anything that leaves the process — a database, an HTTP call, the clock, the filesystem, an
environment variable — is mocked or replaced with a fake, so the test never fails because of the
network, the time of day, or state a previous test left behind. A test that needs the real thing
is an integration test and is named as one.

## 5. Prove the test can fail

After writing it, break the code on purpose once, run the test, confirm it goes red, and revert.
This is a step with an output, not advice:

> Changed `clamp`'s `<` to `<=`; `test_clamp_low_boundary` failed with `assert 0 == 1`; reverted.

It doubles the cost of every test and is the rule most tempting to skip. A test that cannot fail
is the worst kind of debt: it is green forever and means nothing. `/orc-test analyze` does this
at scale later (mutation testing plants the defects for you); this rule is the one-defect version
you run by hand while the code is in front of you.

## 6. 80% line coverage on what the change touches

Before saying "done", `/orc-test coverage <path to what you changed>`. Under 80% on a file you
touched means the work is not finished. The number is per file, not per repo, so a well-tested
neighbour cannot cover for the file you actually changed.

## What this is not

- Not a coverage target for the whole repo — that is `/orc-test coverage` with no path.
- Not the place that says how a language's tools are invoked — that is `languages/<lang>.md`.
- Not a substitute for reading the code. The ladder shortens the solution, never the reading.
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd hooks/scripts && python3 -m pytest tests/test_test_discipline_frontmatter.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/test-discipline/SKILL.md hooks/scripts/tests/test_test_discipline_frontmatter.py
git commit -m "Add test-discipline: the six rules every test written under Orclab follows

Background skill, user-invocable: false. Points at superpowers TDD rather than
restating it; rule 5 (prove the test can fail) is stated as a step with an
output because it is the one most tempting to skip.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Package scaffold — `run.py`, `model.py`, `runner.py`

**Files:**
- Create: `skills/orc-test/scripts/run.py`, `skills/orc-test/scripts/conftest.py` (empty), `skills/orc-test/scripts/orc_test/__init__.py` (empty), `skills/orc-test/scripts/orc_test/model.py`, `skills/orc-test/scripts/orc_test/runner.py`
- Test: `skills/orc-test/scripts/tests/test_model.py`, `skills/orc-test/scripts/tests/test_runner.py`

**Interfaces:**
- Produces:
  - `model.Coverage(covered: int, total: int, files: dict[str, tuple[int, int]])` with `.percent -> float` (0.0 when total is 0) and `.under(threshold) -> list[tuple[str, float]]` sorted worst first.
  - `model.Survivor(file: str, line: int, description: str)`
  - `model.Mutation(killed: int, total: int, survivors: list[Survivor])` with `.score -> float` (0.0 when total is 0).
  - `model.Finding(file: str, line: int, message: str)`
  - `runner.run(cmd: list[str], cwd, env=None) -> subprocess.CompletedProcess` — prints `$ ` + shell-quoted command to stdout first, captures stdout+stderr as text, never raises on non-zero exit.

- [ ] **Step 1: Write the failing tests**

```python
# skills/orc-test/scripts/tests/test_model.py
from orc_test.model import Coverage, Mutation, Survivor


def test_coverage_percent_and_under_sorted_worst_first():
    cov = Coverage(covered=7, total=10, files={
        "src/a.py": (9, 10), "src/b.py": (1, 4), "src/c.py": (3, 6)})
    assert cov.percent == 70.0
    assert cov.under(80) == [("src/b.py", 25.0), ("src/c.py", 50.0)]


def test_coverage_empty_is_zero_not_error():
    assert Coverage(0, 0, {}).percent == 0.0
    assert Coverage(0, 0, {}).under(80) == []


def test_mutation_score():
    m = Mutation(killed=7, total=10, survivors=[Survivor("src/a.py", 3, "< -> <=")])
    assert m.score == 70.0
    assert Mutation(0, 0, []).score == 0.0
```

```python
# skills/orc-test/scripts/tests/test_runner.py
import sys

from orc_test.runner import run


def test_run_prints_command_and_captures_output(capsys, tmp_path):
    cp = run([sys.executable, "-c", "print('hi'); raise SystemExit(3)"], cwd=tmp_path)
    assert cp.returncode == 3
    assert cp.stdout.strip() == "hi"
    assert capsys.readouterr().out.startswith("$ ")


def test_run_missing_binary_does_not_raise(tmp_path):
    cp = run(["definitely-not-a-real-binary-xyz"], cwd=tmp_path)
    assert cp.returncode == 127
    assert "not found" in cp.stdout
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd skills/orc-test/scripts && python3 -m pytest tests/ -v`
Expected: `ModuleNotFoundError: No module named 'orc_test'`.

- [ ] **Step 3: Write the scaffold**

```python
#!/usr/bin/env python3
# skills/orc-test/scripts/run.py
"""Entry point for SKILL.md: puts the orc_test package on sys.path, then runs its CLI."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orc_test.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
```

```python
# skills/orc-test/scripts/orc_test/model.py
"""The three things every language reports in the same shape, whatever tool produced them."""

from dataclasses import dataclass, field


def _pct(part, whole):
    return round(100.0 * part / whole, 1) if whole else 0.0


@dataclass
class Coverage:
    covered: int
    total: int
    files: dict = field(default_factory=dict)   # path -> (covered, total)

    @property
    def percent(self):
        return _pct(self.covered, self.total)

    def under(self, threshold):
        """[(path, percent)] for files below threshold, worst first."""
        rows = [(p, _pct(c, t)) for p, (c, t) in self.files.items() if _pct(c, t) < threshold]
        return sorted(rows, key=lambda r: (r[1], r[0]))


@dataclass
class Survivor:
    file: str
    line: int
    description: str


@dataclass
class Mutation:
    killed: int
    total: int
    survivors: list = field(default_factory=list)

    @property
    def score(self):
        return _pct(self.killed, self.total)


@dataclass
class Finding:
    file: str
    line: int
    message: str
```

```python
# skills/orc-test/scripts/orc_test/runner.py
"""One place every external command goes through, so every one is printed before it runs."""

import shlex
import subprocess


def run(cmd, cwd, env=None):
    print("$ " + shlex.join(cmd), flush=True)
    try:
        return subprocess.run(cmd, cwd=str(cwd), env=env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        return subprocess.CompletedProcess(cmd, 127, stdout=f"{cmd[0]}: not found\n", stderr="")
```

Create `skills/orc-test/scripts/conftest.py` and `skills/orc-test/scripts/orc_test/__init__.py` as empty files. `cli.py` does not exist yet — `run.py` is not executed until Task 6.

- [ ] **Step 4: Run to verify they pass**

Run: `cd skills/orc-test/scripts && python3 -m pytest tests/ -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-test/scripts
git commit -m "orc-test: package scaffold — result models and the printing command runner

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: `config.py` and `detect.py`

**Files:**
- Create: `skills/orc-test/scripts/orc_test/config.py`, `skills/orc-test/scripts/orc_test/detect.py`
- Test: `skills/orc-test/scripts/tests/test_config.py`, `skills/orc-test/scripts/tests/test_detect.py`

**Interfaces:**
- Consumes: nothing from earlier tasks. Language modules arrive in Task 5; `detect` takes the list as a parameter so it is testable with stubs.
- Produces:
  - `config.load(root) -> dict` with keys `coverage` (int, default 80), `tce` (int, default 70), `languages` (dict of KEY → {"test": str} overrides, default `{}`). Reads `root/.orclab/test.yaml` if present.
  - `detect.project_root(cwd) -> pathlib.Path` — `git rev-parse --show-toplevel`; raises `detect.NotAProject` outside git.
  - `detect.languages(root, modules) -> list[module]` — modules whose `MARKERS` match at depth ≤ 2, skipping `node_modules`, `.git`, `venv`, `.venv`, `mutants`, `build`, `dist`. Order = order in `modules`.
  - `detect.declared_test_cmd(root, key, cfg) -> list[str] | None` — `.orclab/test.yaml` override first; then `package.json` `scripts.test` (returns `["npm","test"]`), a `Makefile` with a `test:` target (`["make","test"]`); else `None`.

- [ ] **Step 1: Write the failing tests**

```python
# skills/orc-test/scripts/tests/test_config.py
from orc_test import config


def test_defaults_without_file(tmp_path):
    assert config.load(tmp_path) == {"coverage": 80, "tce": 70, "languages": {}}


def test_file_overrides_thresholds_and_commands(tmp_path):
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text(
        "coverage: 90\nlanguages:\n  python:\n    test: make check\n")
    cfg = config.load(tmp_path)
    assert cfg["coverage"] == 90 and cfg["tce"] == 70
    assert cfg["languages"]["python"]["test"] == "make check"
```

```python
# skills/orc-test/scripts/tests/test_detect.py
import subprocess
import types

import pytest

from orc_test import detect


def _mod(key, markers):
    return types.SimpleNamespace(KEY=key, MARKERS=markers)


PY = _mod("python", ["pyproject.toml", "setup.py"])
JS = _mod("javascript", ["package.json"])
CS = _mod("csharp", ["*.csproj", "*.sln"])


def test_project_root_requires_git(tmp_path):
    with pytest.raises(detect.NotAProject):
        detect.project_root(tmp_path)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    assert detect.project_root(tmp_path) == tmp_path.resolve()


def test_languages_by_marker_depth_two_and_skips_node_modules(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "App.csproj").write_text("")
    (tmp_path / "node_modules" / "x").mkdir(parents=True)
    (tmp_path / "node_modules" / "x" / "package.json").write_text("{}")
    found = detect.languages(tmp_path, [PY, JS, CS])
    assert [m.KEY for m in found] == ["python", "csharp"]


def test_declared_test_cmd_precedence(tmp_path):
    (tmp_path / "package.json").write_text('{"scripts": {"test": "vitest run"}}')
    (tmp_path / "Makefile").write_text("test:\n\tpytest\n")
    cfg = {"languages": {"python": {"test": "make check"}}}
    assert detect.declared_test_cmd(tmp_path, "python", cfg) == ["make", "check"]
    assert detect.declared_test_cmd(tmp_path, "javascript", {"languages": {}}) == ["npm", "test"]
    assert detect.declared_test_cmd(tmp_path, "dart", {"languages": {}}) == ["make", "test"]
    (tmp_path / "Makefile").unlink()
    assert detect.declared_test_cmd(tmp_path, "dart", {"languages": {}}) is None
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd skills/orc-test/scripts && python3 -m pytest tests/test_config.py tests/test_detect.py -v`
Expected: `ImportError` for both modules.

- [ ] **Step 3: Write the modules**

```python
# skills/orc-test/scripts/orc_test/config.py
"""`.orclab/test.yaml` — optional, project-owned. Thresholds and per-language command overrides."""

import pathlib

import yaml

DEFAULTS = {"coverage": 80, "tce": 70, "languages": {}}


def load(root):
    path = pathlib.Path(root) / ".orclab" / "test.yaml"
    cfg = dict(DEFAULTS)
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}
        for k in ("coverage", "tce"):
            if k in data:
                cfg[k] = int(data[k])
        cfg["languages"] = dict(data.get("languages") or {})
    return cfg
```

```python
# skills/orc-test/scripts/orc_test/detect.py
"""Which languages a project contains, and whether it already says how to run its tests."""

import json
import pathlib
import re
import shlex
import subprocess

SKIP_DIRS = {"node_modules", ".git", "venv", ".venv", "mutants", "build", "dist", "__pycache__"}
MAX_DEPTH = 2


class NotAProject(Exception):
    pass


def project_root(cwd):
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(cwd), text=True,
                             capture_output=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise NotAProject(f"{cwd} is not inside a git repository")
    return pathlib.Path(out).resolve()


def _candidates(root):
    root = pathlib.Path(root)
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if len(rel.parts) > MAX_DEPTH or SKIP_DIRS & set(rel.parts):
            continue
        yield p


def languages(root, modules):
    files = list(_candidates(root))
    found = []
    for m in modules:
        if any(f.match(pat) for pat in m.MARKERS for f in files):
            found.append(m)
    return found


def declared_test_cmd(root, key, cfg):
    root = pathlib.Path(root)
    override = (cfg.get("languages") or {}).get(key, {}).get("test")
    if override:
        return shlex.split(override)
    pkg = root / "package.json"
    if key == "javascript" and pkg.exists():
        if (json.loads(pkg.read_text()).get("scripts") or {}).get("test"):
            return ["npm", "test"]
    mk = root / "Makefile"
    if mk.exists() and re.search(r"^test\s*:", mk.read_text(), re.M):
        return ["make", "test"]
    return None
```

- [ ] **Step 4: Run to verify they pass**

Run: `cd skills/orc-test/scripts && python3 -m pytest tests/ -v`
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-test/scripts
git commit -m "orc-test: detect languages by marker file; read .orclab/test.yaml thresholds

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: `lcov.py` — the shared coverage reader

**Files:**
- Create: `skills/orc-test/scripts/orc_test/lcov.py`, `skills/orc-test/scripts/tests/fixtures/coverage.lcov`
- Test: `skills/orc-test/scripts/tests/test_lcov.py`

**Interfaces:**
- Consumes: `model.Coverage`.
- Produces: `lcov.parse(path) -> Coverage`. Uses `LF:`/`LH:` per `SF:` record when present, else counts `DA:` lines. File keys are the `SF:` path as written (relative or absolute — the tool's choice; `cli.py` displays them as-is).

- [ ] **Step 1: Write the fixture (real pytest-cov 7 output, captured 2026-09-11) and the failing test**

```
# skills/orc-test/scripts/tests/fixtures/coverage.lcov   (no comment lines in the real file)
SF:src/calc/__init__.py
DA:1,1
DA:2,1
DA:3,0
DA:4,1
DA:5,0
DA:6,1
LF:6
LH:4
FN:1,6,clamp
FNDA:1,clamp
FNF:1
FNH:1
end_of_record
SF:src/other.py
DA:1,1
DA:2,1
end_of_record
```

```python
# skills/orc-test/scripts/tests/test_lcov.py
import pathlib

from orc_test import lcov

FIX = pathlib.Path(__file__).parent / "fixtures" / "coverage.lcov"


def test_parse_uses_lf_lh_and_falls_back_to_da_counts():
    cov = lcov.parse(FIX)
    assert cov.files == {"src/calc/__init__.py": (4, 6), "src/other.py": (2, 2)}
    assert (cov.covered, cov.total) == (6, 8)
    assert cov.percent == 75.0
    assert cov.under(80) == [("src/calc/__init__.py", 66.7)]
```

- [ ] **Step 2: Run to verify it fails** — `ImportError`.

- [ ] **Step 3: Write it**

```python
# skills/orc-test/scripts/orc_test/lcov.py
"""lcov → Coverage. The one reader for every tool that emits lcov: pytest-cov, vitest/jest,
coverlet, dart, nano-coverage."""

import pathlib

from .model import Coverage


def parse(path):
    files, cur, lf, lh, da_hit, da_all = {}, None, None, None, 0, 0
    for raw in pathlib.Path(path).read_text().splitlines():
        line = raw.strip()
        if line.startswith("SF:"):
            cur, lf, lh, da_hit, da_all = line[3:], None, None, 0, 0
        elif line.startswith("DA:"):
            da_all += 1
            da_hit += int(line[3:].split(",")[1]) > 0
        elif line.startswith("LF:"):
            lf = int(line[3:])
        elif line.startswith("LH:"):
            lh = int(line[3:])
        elif line == "end_of_record" and cur is not None:
            files[cur] = (lh, lf) if lf is not None and lh is not None else (da_hit, da_all)
            cur = None
    return Coverage(sum(c for c, _ in files.values()), sum(t for _, t in files.values()), files)
```

- [ ] **Step 4: Run to verify it passes** — `cd skills/orc-test/scripts && python3 -m pytest tests/ -v` → 11 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-test/scripts
git commit -m "orc-test: lcov reader shared by five languages

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---
### Task 5: `langs/python.py` — the first language, end to end

**Files:**
- Create: `skills/orc-test/scripts/orc_test/langs/__init__.py`, `skills/orc-test/scripts/orc_test/langs/python.py`, `skills/orc-test/scripts/tests/fixtures/mutmut_results.txt`, `skills/orc-test/scripts/tests/fixtures/mutmut_show.txt`
- Test: `skills/orc-test/scripts/tests/test_lang_python.py`

**Interfaces:**
- Consumes: `model.*`, `lcov.parse`, `runner.run`.
- Produces: the module contract above. `langs.ALL` is the ordered list of language modules; this task starts it with `[python]`; later tasks append.

**What was verified live on 2026-09-11 (mutmut 3.3.1, pytest-cov 7, ruff 0.16.7):**
- `mutmut run` reads `[tool.mutmut]` from `pyproject.toml` (`paths_to_mutate`, `tests_dir`), writes its cache to `mutants/` (incremental by function hash) and copies the tests there — so every later plain `pytest` needs `--ignore=mutants` or it fails with "import file mismatch".
- `mutmut results` prints one mutant per line: `    calc.x_clamp__mutmut_1: survived`. Statuses seen in its own legend: `killed`, `survived`, `timeout`, `suspicious`, `skipped`, `no tests`.
- `mutmut show <key>` prints `# <key>: <status>` then a unified diff of the mutation.
- ruff's `PT` rules report nothing for an assertion-free test or a bare `@pytest.mark.skip` — hence the `ast` scan below.

- [ ] **Step 1: Write the fixtures and the failing tests**

```
# skills/orc-test/scripts/tests/fixtures/mutmut_results.txt   (captured 2026-09-11)
    calc.x_clamp__mutmut_1: survived
    calc.x_clamp__mutmut_2: killed
    calc.x_clamp__mutmut_3: survived
    calc.x_other__mutmut_1: no tests
```

```
# skills/orc-test/scripts/tests/fixtures/mutmut_show.txt   (captured 2026-09-11)
# calc.x_clamp__mutmut_1: survived
--- src/calc/__init__.py
+++ src/calc/__init__.py
@@ -1,5 +1,5 @@
 def clamp(x, lo, hi):
-    if x < lo:
+    if x <= lo:
         return lo
     if x > hi:
         return hi
```

```python
# skills/orc-test/scripts/tests/test_lang_python.py
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
    (tmp_path / "results.txt").write_text((FIX / "mutmut_results.txt").read_text())
    monkeypatch.setattr(py, "_show", lambda root, key: (FIX / "mutmut_show.txt").read_text())
    m = py.mutation_parse(tmp_path, tmp_path)
    assert (m.killed, m.total) == (1, 3)          # "no tests" is not a mutant that was tested
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
```

- [ ] **Step 2: Run to verify they fail** — `ImportError: cannot import name 'python'`.

- [ ] **Step 3: Write the module**

```python
# skills/orc-test/scripts/orc_test/langs/__init__.py
"""Every language /orc-test knows, in the order the spec's table lists them."""

from . import python

ALL = [python]
```

```python
# skills/orc-test/scripts/orc_test/langs/python.py
"""Python: pytest, pytest-cov (lcov), mutmut 3, and a stdlib ast scan for test smells.

mutmut 3 copies the tests into mutants/ for its own runs; a later plain pytest collects both
copies and dies with "import file mismatch". Every command here passes --ignore=mutants.
"""

import ast
import importlib.util
import pathlib
import re

from .. import lcov
from ..model import Finding, Mutation, Survivor
from ..runner import run

KEY = "python"
LABEL = "Python"
MARKERS = ["pyproject.toml", "setup.py", "setup.cfg"]
TOOLS = {"pytest": "pip install pytest", "pytest_cov": "pip install pytest-cov"}
CAVEATS = ["mutmut writes its cache and a copy of the tests to mutants/; add it to .gitignore."]

_IGNORE = "--ignore=mutants"
_RESULT = re.compile(r"^\s*(\S+): (.+)$")
_HUNK = re.compile(r"^@@ -(\d+)")


def missing(root):
    return [t for t in TOOLS if importlib.util.find_spec(t) is None]


def test_cmd(root, target):
    return ["python3", "-m", "pytest", "-q", _IGNORE] + ([target] if target else [])


def coverage_cmd(root, target, out):
    src = target or "."
    return ["python3", "-m", "pytest", "-q", _IGNORE, f"--cov={src}",
            f"--cov-report=lcov:{out / 'coverage.lcov'}", f"--cov-report=html:{out / 'html'}"]


def coverage_parse(root, out):
    return lcov.parse(out / "coverage.lcov")


def mutation_unavailable(root):
    if importlib.util.find_spec("mutmut") is None:
        return "mutmut not installed — pip install mutmut"
    return None


def mutation_cmd(root, target, out):
    # mutmut takes its paths from pyproject.toml; `target` narrows nothing here, and the
    # report says so. Results are written by mutation_parse's own `mutmut results` call.
    return ["python3", "-m", "mutmut", "run"]


def _show(root, key):
    return run(["python3", "-m", "mutmut", "show", key], cwd=root).stdout


def mutation_parse(root, out):
    text = run(["python3", "-m", "mutmut", "results"], cwd=root).stdout
    killed, total, survivors = 0, 0, []
    for line in text.splitlines():
        m = _RESULT.match(line)
        if not m or m.group(2) == "no tests":
            continue
        total += 1
        if m.group(2) == "killed":
            killed += 1
        elif m.group(2) == "survived":
            survivors.append(_survivor(root, m.group(1)))
    return Mutation(killed, total, survivors)


def _survivor(root, key):
    """File, line and replacement text of one surviving mutant, from `mutmut show`'s diff.
    The mutated line is the hunk's start plus the context lines before the first `-` line."""
    diff = _show(root, key)
    file, line, context, change = "?", 0, 0, ""
    for raw in diff.splitlines():
        if raw.startswith("--- "):
            file = raw[4:].strip()
        elif (h := _HUNK.match(raw)):
            line, context = int(h.group(1)), 0
        elif raw.startswith("-") and not raw.startswith("---"):
            line += context
            context = None            # frozen: the mutated line is found
        elif raw.startswith("+") and not raw.startswith("+++"):
            change = raw[1:].strip()
            break
        elif raw.startswith(" ") and context is not None:
            context += 1
    return Survivor(file, line, change)


def lint(root, target, out):
    base = pathlib.Path(root) / (target or ".")
    findings = []
    for path in sorted(base.rglob("test_*.py")):
        if "mutants" in path.parts:
            continue
        findings += _scan(path, path.relative_to(root))
    return findings


def _scan(path, rel):
    tree = ast.parse(path.read_text())
    seen, out = set(), []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test"):
            continue
        if node.name in seen:
            out.append(Finding(str(rel), node.lineno, f"duplicate test name {node.name}"))
        seen.add(node.name)
        body = list(ast.walk(node))
        if any(_is_skip(d) for d in node.decorator_list):
            out.append(Finding(str(rel), node.lineno, f"skipped: {node.name}"))
        if not any(isinstance(n, ast.Assert) or _is_assert_call(n) for n in body):
            out.append(Finding(str(rel), node.lineno, f"no assertion in {node.name}"))
        for n in body:
            if isinstance(n, ast.Call) and _dotted(n.func).endswith("sleep"):
                out.append(Finding(str(rel), n.lineno, f"sleep in {node.name}"))
    return out


def _dotted(func):
    parts = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if isinstance(func, ast.Name):
        parts.append(func.id)
    return ".".join(reversed(parts))


def _is_skip(dec):
    d = dec.func if isinstance(dec, ast.Call) else dec
    return _dotted(d).endswith(("mark.skip", "mark.skipif"))


def _is_assert_call(n):
    if isinstance(n, ast.Call):
        name = _dotted(n.func)
        return name.endswith("raises") or ".assert_" in name or name.startswith("assert")
    return isinstance(n, ast.With) and any(_is_assert_call(i.context_expr) for i in n.items)
```

- [ ] **Step 4: Run to verify they pass** — `cd skills/orc-test/scripts && python3 -m pytest tests/ -v` → 15 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-test/scripts
git commit -m "orc-test: Python — pytest, pytest-cov lcov, mutmut 3 results, ast test-smell scan

mutmut 3 copies tests into mutants/; every pytest here passes --ignore=mutants
(hit live 2026-09-11). ruff's PT rules have no assertion-free check, so the
four smells are a stdlib ast scan.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---
### Task 6: `cli.py` — `detect` and `run`, and `SKILL.md` v1

**Files:**
- Create: `skills/orc-test/scripts/orc_test/cli.py`, `skills/orc-test/SKILL.md`
- Test: `skills/orc-test/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: `detect.*`, `config.load`, `langs.ALL`, `runner.run`.
- Produces:
  - `cli.main(argv) -> int`. Top-level `--cwd PATH` before the subcommand (same rule as `/orc-todo`). Subcommands: `detect [path]`, `run [path]`.
  - `cli._each_language(args) -> list[tuple[module, root, target]]` — the per-language loop every later subcommand reuses: resolves root, loads config, detects languages (all of `langs.ALL`, or only the one named by `--lang KEY`), prints the "detected:" line, and drops languages with missing tools after printing their install lines.
  - `cli._out(root, mod) -> Path` — creates and returns `root/.orclab/test/<KEY>/`, emptied first.
  - `cli._test_cmd(root, mod, target, cfg) -> list[str]` — `detect.declared_test_cmd` if any, else `mod.test_cmd`.

- [ ] **Step 1: Write the failing tests**

```python
# skills/orc-test/scripts/tests/test_cli.py
import subprocess
import types

import pytest

from orc_test import cli, langs


def make_repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok():\n    assert 1\n")
    return tmp_path


def run(args, repo, capsys):
    code = cli.main(["--cwd", str(repo), *args])
    out = capsys.readouterr()
    return code, out.out + out.err


def test_outside_git_says_so(tmp_path, capsys):
    code, out = run(["detect"], tmp_path, capsys)
    assert code == 1 and "not inside a git repository" in out


def test_detect_lists_languages(tmp_path, capsys):
    code, out = run(["detect"], make_repo(tmp_path), capsys)
    assert code == 0 and "detected: Python" in out


def test_run_green_suite_exits_zero_and_prints_command(tmp_path, capsys):
    code, out = run(["run"], make_repo(tmp_path), capsys)
    assert code == 0
    assert "$ python3 -m pytest -q --ignore=mutants" in out
    assert "Python" in out and "passed" in out


def test_run_red_suite_exits_nonzero(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "tests" / "test_bad.py").write_text("def test_bad():\n    assert 0\n")
    code, out = run(["run"], repo, capsys)
    assert code == 1 and "failed" in out


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
    code, out = run(["run"], repo, capsys)
    assert "$ make test" in out and "make-ran" in out
```

- [ ] **Step 2: Run to verify they fail** — `ImportError: cannot import name 'cli'`.

- [ ] **Step 3: Write `cli.py`**

```python
# skills/orc-test/scripts/orc_test/cli.py
"""/orc-test: run, measure and (via SKILL.md prose) repair a project's tests, per language."""

import argparse
import pathlib
import re
import shutil
import sys
import time

from . import config, detect, langs
from .runner import run

_PYTEST_SUMMARY = re.compile(r"(\d+) passed|(\d+) failed|(\d+) error")


def _each_language(args):
    root = detect.project_root(args.cwd)
    cfg = config.load(root)
    mods = [m for m in langs.ALL if not args.lang or m.KEY == args.lang]
    found = detect.languages(root, mods)
    target = None
    if args.path:
        target = str(pathlib.Path(args.path).resolve().relative_to(root)) if pathlib.Path(args.path).is_absolute() else args.path
    print("detected: " + (", ".join(m.LABEL for m in found) or "no supported language"))
    usable = []
    for m in found:
        gone = m.missing(root)
        if gone:
            for tool in gone:
                print(f"{m.LABEL}: missing {tool} — {m.TOOLS[tool]} — skipped")
            continue
        usable.append((m, root, target, cfg))
    return usable


def _out(root, mod):
    out = pathlib.Path(root) / ".orclab" / "test" / mod.KEY
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    return out


def _test_cmd(root, mod, target, cfg):
    return detect.declared_test_cmd(root, mod.KEY, cfg) or mod.test_cmd(root, target)


def _run_tests(mod, root, target, cfg):
    """(ok, one-line summary). Prints the tool's output tail on failure."""
    t0 = time.monotonic()
    cp = run(_test_cmd(root, mod, target, cfg), cwd=root)
    secs = time.monotonic() - t0
    ok = cp.returncode == 0
    if not ok:
        print(cp.stdout[-3000:])
    counts = " ".join(m.group(0) for m in _PYTEST_SUMMARY.finditer(cp.stdout)) or (
        "passed" if ok else "failed")
    return ok, f"{mod.LABEL:<10} {'✓' if ok else '✗'} {counts} ({secs:.1f}s)"


def cmd_detect(args):
    for m, root, target, cfg in _each_language(args):
        print(f"  {m.LABEL}: test command {' '.join(_test_cmd(root, m, target, cfg))}")
    return 0


def cmd_run(args):
    failed = False
    lines = []
    for m, root, target, cfg in _each_language(args):
        ok, line = _run_tests(m, root, target, cfg)
        failed |= not ok
        lines.append(line)
    print("\n" + "\n".join(lines) if lines else "nothing to run")
    return 1 if failed else 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="orc-test")
    p.add_argument("--cwd", default=".")
    p.add_argument("--lang", help="only this language KEY (python, javascript, ...)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("detect", cmd_detect), ("run", cmd_run)):
        sp = sub.add_parser(name)
        sp.add_argument("path", nargs="?")
        sp.set_defaults(fn=fn)
    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except detect.NotAProject as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
```

- [ ] **Step 4: Write `SKILL.md` v1** (Task 17 extends it; the frontmatter and the first table are final now)

```markdown
---
name: orc-test
description: Use when the user explicitly asks to use orc-test, or types /orc-test, or asks to run the tests, check coverage, measure test quality, or improve the tests - runs every test suite in the project across its languages, holds coverage to 80% and mutation score (TCE) to 70%, and repairs weak suites from what analyze found.
allowed-tools: Bash(python3 *)
---

# orc-test

Run every command as:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py [--cwd <project>] [--lang <key>] <subcommand> [path]
```

`--cwd` and `--lang` go **before** the subcommand. `path` narrows every subcommand to that part
of the project. Outside a git repository the command says so and stops.

| Subcommand | Question it answers | Writes |
|---|---|---|
| `run` (or nothing) | Does the code work? | nothing |
| `coverage` | How much of it do the tests exercise? (gate 80%) | `.orclab/test/<lang>/` |
| `analyze` | Would the tests notice a defect? (coverage + TCE at 70% + lint) | `.orclab/test/<lang>/`, `.orclab/test/analyze.json` |
| `generate` | Fix what `analyze` found | tests, uncommitted — see below |
| `detect` | Which languages, and which test command each | nothing |

Typing `/orc-test` with no subcommand means `run`.

## How it finds the languages

By marker file, at the project root or up to two directories down: `pyproject.toml`/`setup.py`
→ Python; `package.json` → JavaScript/TypeScript; `pom.xml`/`build.gradle` → Java (Kotlin if
`.kt` files exist); `*.csproj` → C#; `pubspec.yaml` → Dart; `Package.swift`/`*.xcodeproj` →
Swift; `project.godot` → GDScript. Every hit runs. The first line of every report is
`detected: …` so a wrong guess is visible. What each language's tools are, and their gotchas, is
in `languages/<lang>.md` beside this file — read the relevant one before interpreting a report.

A project's own declared test command wins: a `test` script in `package.json`, a `Makefile`
`test:` target, or `.orclab/test.yaml`:

```yaml
coverage: 80        # percent of lines, per language
tce: 70             # mutation score, per language
languages:
  python:
    test: make check
```

## What it never does

Install a tool (it names the missing one and its install line, and skips that language). Run
git. Guess a language it cannot see a marker for.
```

- [ ] **Step 5: Run the tests** — `cd skills/orc-test/scripts && python3 -m pytest tests/ -v` → 21 passed.

- [ ] **Step 6: Run it for real on Orclab** — from the repo root:

```bash
python3 skills/orc-test/scripts/run.py run
```
Expected: `detected: Python`, then the printed pytest command, then a summary line. Note: Orclab's suites live under `skills/*/scripts/tests` and `hooks/scripts/tests`, each with its own `conftest.py`; a root-level `pytest` collects all of them. If any collection error appears, record it — do not fix Orclab's tests in this task.

- [ ] **Step 7: Commit**

```bash
git add skills/orc-test
git commit -m "orc-test: run and detect subcommands, and the skill's first page

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: `coverage` subcommand

**Files:**
- Modify: `skills/orc-test/scripts/orc_test/cli.py`
- Test: `skills/orc-test/scripts/tests/test_cli_coverage.py`

**Interfaces:**
- Consumes: `mod.coverage_cmd`, `mod.coverage_parse`, `Coverage.under`.
- Produces: `cli._coverage(mod, root, target, cfg, out) -> Coverage | None` (None when the run failed), and `cli._coverage_block(mod, cov, threshold) -> str` — the per-language report text. Both reused by `analyze`.

- [ ] **Step 1: Write the failing tests**

```python
# skills/orc-test/scripts/tests/test_cli_coverage.py
import pytest

from orc_test import cli
from tests.test_cli import make_repo, run

pytest.importorskip("pytest_cov")


def _src(repo, body):
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "calc.py").write_text(body)
    (repo / "tests" / "test_calc.py").write_text(
        "import sys; sys.path.insert(0, 'src')\nfrom calc import clamp\n"
        "def test_mid():\n    assert clamp(5, 0, 10) == 5\n")


def test_coverage_under_threshold_lists_files_worst_first_and_fails(tmp_path, capsys):
    repo = make_repo(tmp_path)
    _src(repo, "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n"
               "    if x > hi:\n        return hi\n    return x\n")
    code, out = run(["coverage", "src"], repo, capsys)
    assert code == 1
    assert "Python" in out and "66.7%" in out and "✗" in out
    assert "src/calc.py" in out
    assert (repo / ".orclab" / "test" / "python" / "coverage.lcov").exists()
    assert "html report:" in out


def test_coverage_threshold_from_config(tmp_path, capsys):
    repo = make_repo(tmp_path)
    _src(repo, "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n"
               "    if x > hi:\n        return hi\n    return x\n")
    (repo / ".orclab").mkdir()
    (repo / ".orclab" / "test.yaml").write_text("coverage: 60\n")
    code, out = run(["coverage", "src"], repo, capsys)
    assert code == 0 and "✓" in out


def test_coverage_with_red_tests_stops_that_language(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / "tests" / "test_bad.py").write_text("def test_bad():\n    assert 0\n")
    code, out = run(["coverage"], repo, capsys)
    assert code == 1 and "tests failed; coverage not measured" in out
```

- [ ] **Step 2: Run to verify they fail** — `argparse` error: invalid choice `coverage`.

- [ ] **Step 3: Add to `cli.py`**

```python
def _coverage(mod, root, target, cfg, out):
    cp = run(mod.coverage_cmd(root, target, out), cwd=root)
    if cp.returncode != 0:
        print(cp.stdout[-3000:])
        print(f"{mod.LABEL}: tests failed; coverage not measured")
        return None
    return mod.coverage_parse(root, out)


def _coverage_block(mod, cov, threshold, out):
    ok = cov.percent >= threshold
    lines = [f"{mod.LABEL:<10} coverage {cov.percent}% ({cov.covered}/{cov.total} lines) "
             f"{'✓' if ok else '✗ (min ' + str(threshold) + ')'}"]
    for path, pct in cov.under(threshold):
        lines.append(f"    {pct:5.1f}%  {path}")
    html = out / "html"
    if html.exists():
        lines.append(f"    html report: {html}")
    return "\n".join(lines)


def cmd_coverage(args):
    failed, blocks = False, []
    for m, root, target, cfg in _each_language(args):
        cov = _coverage(m, root, target, cfg, _out(root, m))
        if cov is None:
            failed = True
            continue
        failed |= cov.percent < cfg["coverage"]
        blocks.append(_coverage_block(m, cov, cfg["coverage"], _out_path(root, m)))
    print("\n" + "\n\n".join(blocks) if blocks else "nothing measured")
    return 1 if failed else 0


def _out_path(root, mod):
    return pathlib.Path(root) / ".orclab" / "test" / mod.KEY
```

Register it in `main`: add `("coverage", cmd_coverage)` to the subparser loop. `_out` empties the directory, so `cmd_coverage` calls it once and `_out_path` (no emptying) afterwards.

- [ ] **Step 4: Run** — `cd skills/orc-test/scripts && python3 -m pytest tests/ -v` → 24 passed (or 21 + 3 skipped if `pytest_cov` is absent locally — install it: `pip install pytest-cov`; it is needed for Task 19 anyway).

- [ ] **Step 5: Commit**

```bash
git add skills/orc-test/scripts
git commit -m "orc-test: coverage subcommand — per-language 80% gate computed from the report file

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: `analyze` subcommand

**Files:**
- Modify: `skills/orc-test/scripts/orc_test/cli.py`
- Test: `skills/orc-test/scripts/tests/test_cli_analyze.py`

**Interfaces:**
- Consumes: `_coverage`, `_coverage_block`, `mod.mutation_cmd/mutation_parse/lint/MUTATION_UNAVAILABLE/CAVEATS`.
- Produces: `.orclab/test/analyze.json` — the file `generate` reads:
  ```json
  {"when": 1757600000, "target": "src", "languages": {"python": {
     "coverage": {"percent": 66.7, "under": [["src/calc.py", 66.7]]},
     "tce": {"score": 33.3, "survivors": [["src/calc.py", 2, "if x <= lo:"]]},   // or {"unavailable": "..."} or {"skipped": true}
     "lint": [["tests/test_a.py", 3, "no assertion in test_nothing"]]}}}
  ```

- [ ] **Step 1: Write the failing tests** (mutation and lint are stubbed through a fake language module so the test does not need mutmut installed)

```python
# skills/orc-test/scripts/tests/test_cli_analyze.py
import json
import types

from orc_test import cli, langs
from orc_test.model import Coverage, Finding, Mutation, Survivor
from tests.test_cli import make_repo, run


def fake(mutation=None, unavailable=None, cov=(9, 10), lint=None):
    m = types.SimpleNamespace(
        KEY="fake", LABEL="Fake", MARKERS=["pyproject.toml"], TOOLS={}, CAVEATS=["a caveat"],
        mutation_unavailable=lambda root: unavailable, missing=lambda root: [],
        test_cmd=lambda root, t: ["true"],
        coverage_cmd=lambda root, t, out: ["true"],
        coverage_parse=lambda root, out: Coverage(*cov, {"src/a.py": cov}),
        mutation_cmd=lambda root, t, out: ["true"],
        mutation_parse=lambda root, out: mutation,
        lint=lambda root, t, out: lint if lint is not None else [
            Finding("tests/test_a.py", 3, "no assertion in test_x")])
    return m


def test_analyze_lint_not_run_is_a_reason_not_a_count(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(9, 10, []), lint="eslint not configured")])
    code, out = run(["analyze"], make_repo(tmp_path), capsys)
    assert "lint: not run — eslint not configured" in out


def test_analyze_all_gates_and_result_file(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(6, 10, [Survivor("src/a.py", 2, "x <= 1")]))])
    code, out = run(["analyze"], repo, capsys)
    assert code == 1
    assert "coverage 90.0%" in out and "TCE 60.0% ✗ (min 70)" in out and "lint: 1 finding" in out
    assert "src/a.py:2  x <= 1" in out and "a caveat" in out
    assert "gates failed: tce — run `/orc-test generate` to repair" in out
    data = json.loads((repo / ".orclab" / "test" / "analyze.json").read_text())
    assert data["languages"]["fake"]["tce"]["survivors"] == [["src/a.py", 2, "x <= 1"]]


def test_analyze_unavailable_mutation_is_words_not_a_number(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(unavailable="no mutation tool exists for Fake")])
    code, out = run(["analyze"], make_repo(tmp_path), capsys)
    assert "TCE not measurable — no mutation tool exists for Fake" in out
    assert "TCE 0" not in out


def test_analyze_no_mutation_flag(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(9, 10, []))])
    code, out = run(["analyze", "--no-mutation"], make_repo(tmp_path), capsys)
    assert "TCE skipped" in out and "$ true" in out


def test_analyze_announces_size_on_whole_repo(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    for i in range(3):
        (repo / f"m{i}.py").write_text("x = 1\n")
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(9, 10, []))])
    code, out = run(["analyze"], repo, capsys)
    assert "mutating 4 files" in out    # 3 modules + tests/test_ok.py; first run, no cache yet
```

- [ ] **Step 2: Run to verify they fail** — invalid choice `analyze`.

- [ ] **Step 3: Add to `cli.py`**

```python
import json

_SOURCE_EXT = {"python": ".py", "javascript": ".js", "java": ".java", "kotlin": ".kt",
               "csharp": ".cs", "dart": ".dart", "swift": ".swift", "gdscript": ".gd"}


def _source_count(root, mod, target):
    base = pathlib.Path(root) / (target or ".")
    ext = _SOURCE_EXT.get(mod.KEY, "")
    return sum(1 for p in base.rglob(f"*{ext}") if not detect.SKIP_DIRS & set(p.relative_to(root).parts))


def _mutation(mod, root, target, cfg, out):
    why = mod.mutation_unavailable(root)
    if why:
        return {"unavailable": why}
    if not target:
        print(f"{mod.LABEL}: mutating {_source_count(root, mod, None)} files"
              " — a first run on the whole project takes a while; later runs are incremental")
    cp = run(mod.mutation_cmd(root, target, out), cwd=root)
    if cp.returncode not in (0, 1, 2):        # tools exit non-zero on survivors; a crash is higher
        print(cp.stdout[-3000:])
        return {"unavailable": f"mutation tool exited {cp.returncode}"}
    mut = mod.mutation_parse(root, out)
    return {"score": mut.score, "killed": mut.killed, "total": mut.total,
            "survivors": [[s.file, s.line, s.description] for s in mut.survivors]}


def _tce_line(tce, threshold):
    if "unavailable" in tce:
        return f"TCE not measurable — {tce['unavailable']}"
    if tce.get("skipped"):
        return "TCE skipped"
    ok = tce["score"] >= threshold
    return f"TCE {tce['score']}% {'✓' if ok else '✗ (min ' + str(threshold) + ')'}"


def cmd_analyze(args):
    result = {"when": int(time.time()), "target": args.path, "languages": {}}
    failed_gates, blocks = set(), []
    project = detect.project_root(args.cwd)
    for m, root, target, cfg in _each_language(args):
        out = _out(root, m)
        ok, _ = _run_tests(m, root, target, cfg)
        if not ok:
            print(f"{m.LABEL}: tests failed; nothing measured")
            failed_gates.add("tests")
            continue
        cov = _coverage(m, root, target, cfg, out)
        if cov is None:
            failed_gates.add("tests")
            continue
        tce = {"skipped": True} if args.no_mutation else _mutation(m, root, target, cfg, out)
        lint = m.lint(root, target, out)
        lint_note = lint if isinstance(lint, str) else None
        lint = [] if lint_note else lint
        if cov.percent < cfg["coverage"]:
            failed_gates.add("coverage")
        if "score" in tce and tce["score"] < cfg["tce"]:
            failed_gates.add("tce")
        result["languages"][m.KEY] = {
            "coverage": {"percent": cov.percent, "under": cov.under(cfg["coverage"])},
            "tce": tce, "lint": [[f.file, f.line, f.message] for f in lint], "lint_note": lint_note}
        lint_txt = f"not run — {lint_note}" if lint_note else f"{len(lint)} finding{'s' if len(lint) != 1 else ''}"
        lines = [_coverage_block(m, cov, cfg["coverage"], _out_path(root, m)),
                 f"{'':<10} {_tce_line(tce, cfg['tce'])}    lint: {lint_txt}"]
        for s in tce.get("survivors", []):
            lines.append(f"    survived  {s[0]}:{s[1]}  {s[2]}")
        for f in lint:
            lines.append(f"    lint      {f.file}:{f.line}  {f.message}")
        for c in m.CAVEATS:
            lines.append(f"    note: {c}")
        blocks.append("\n".join(lines))
    if blocks:
        (project / ".orclab" / "test" / "analyze.json").write_text(json.dumps(result, indent=1))
    print("\n" + "\n\n".join(blocks) if blocks else "nothing measured")
    if failed_gates:
        print(f"\ngates failed: {', '.join(sorted(failed_gates))} — run `/orc-test generate` to repair")
    return 1 if failed_gates else 0
```

Register: `("analyze", cmd_analyze)` in the loop, and add `sp.add_argument("--no-mutation", action="store_true")` for every subparser (harmless on the others). Set `args.no_mutation` default `False` for subcommands that don't define it via `p.set_defaults(no_mutation=False)`.

- [ ] **Step 4: Run** — `cd skills/orc-test/scripts && python3 -m pytest tests/ -v` → 29 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-test/scripts
git commit -m "orc-test: analyze — coverage, mutation score (TCE) and test lint in one report, saved for generate

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: `languages/python.md`

**Files:**
- Create: `skills/orc-test/languages/python.md`
- Test: `hooks/scripts/tests/test_orc_test_languages.py` (checks every `languages/*.md` has the required sections; grows with each language task)

- [ ] **Step 1: Write the failing test**

```python
# hooks/scripts/tests/test_orc_test_languages.py
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
LANG_DIR = ROOT / "skills" / "orc-test" / "languages"
REQUIRED = ["## Detect", "## Run", "## Coverage", "## Mutation (TCE)", "## Test lint",
            "## Caveats", "Researched on:", "Last real run:"]
EXPECTED = {"python"}   # each language task adds its key here


@pytest.mark.parametrize("key", sorted(EXPECTED))
def test_language_file_has_every_section(key):
    text = (LANG_DIR / f"{key}.md").read_text()
    for section in REQUIRED:
        assert section in text, f"{key}.md lacks {section!r}"
    assert re.search(r"Researched on: 2026-\d\d-\d\d", text)
```

- [ ] **Step 2: Run to verify it fails** — `FileNotFoundError`.

- [ ] **Step 3: Write the file**

```markdown
# Python

Researched on: 2026-09-11 (versions read from PyPI that day). Last real run: none yet — the
first is Task 19 of the v17 plan, on Orclab itself.

## Detect
`pyproject.toml`, `setup.py` or `setup.cfg` at the root or up to two directories down.

## Run
`python3 -m pytest -q --ignore=mutants [path]` — pytest 9.1.1. A `[tool.pytest.ini_options]`
section is the project's own config and is honoured by pytest itself. `--ignore=mutants` is not
optional: see Caveats.

## Coverage
pytest-cov 7.1.0: `--cov=<path> --cov-report=lcov:.orclab/test/python/coverage.lcov
--cov-report=html:.orclab/test/python/html`. `run.py` reads the lcov and applies the 80% gate.
For a project-side gate in CI, pytest-cov's own switch is `--cov-fail-under=80`.

## Mutation (TCE)
mutmut 3.7.0 (PyPI, 2026-07-31). Config in `pyproject.toml`:
```toml
[tool.mutmut]
paths_to_mutate = ["src/"]
tests_dir = ["tests/"]
```
`python3 -m mutmut run`, then `run.py` reads `python3 -m mutmut results` (one line per mutant:
`<key>: killed|survived|timeout|suspicious|skipped|no tests`) and `python3 -m mutmut show <key>`
for each survivor's diff. Incremental: mutmut caches per function hash in `mutants/`; only
changed functions re-run. A path argument does not narrow mutmut — it mutates `paths_to_mutate`.
Alternative, not used: cosmic-ray 8.7.0 (more configurable, longer setup).

## Test lint
No tool. ruff's `PT` rules (flake8-pytest-style) report nothing for an assertion-free test or a
bare `@pytest.mark.skip` — checked 2026-09-11 with ruff 0.16.7. `run.py` scans `test_*.py` with
the stdlib `ast` module for: no assertion (an `assert`, `pytest.raises`, or a `.assert_*` call
counts), `sleep` calls, `@pytest.mark.skip`/`skipif`, duplicate test names.

## Caveats
- **mutmut 3 copies the tests into `mutants/`.** A later plain `pytest` collects both copies and
  fails with "import file mismatch". Every pytest here passes `--ignore=mutants`; a project should
  also add `mutants/` to `.gitignore`.
- mutmut needs the tests to import the code under test the way the project runs — `pythonpath`
  in `[tool.pytest.ini_options]` or an installed package — or every mutant reports `no tests`.
```

- [ ] **Step 4: Run** — `cd hooks/scripts && python3 -m pytest tests/test_orc_test_languages.py -v` → 1 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-test/languages/python.md hooks/scripts/tests/test_orc_test_languages.py
git commit -m "orc-test: languages/python.md — researched 2026-09-11, with the mutants/ gotcha

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---
### Task 10: `stryker.py` + `langs/javascript.py` + `languages/javascript.md`

**Files:**
- Create: `skills/orc-test/scripts/orc_test/stryker.py`, `skills/orc-test/scripts/orc_test/langs/javascript.py`, `skills/orc-test/scripts/tests/fixtures/stryker.json`, `skills/orc-test/languages/javascript.md`
- Modify: `skills/orc-test/scripts/orc_test/langs/__init__.py` (append `javascript`), `hooks/scripts/tests/test_orc_test_languages.py` (`EXPECTED` gains `"javascript"`)
- Test: `skills/orc-test/scripts/tests/test_stryker.py`, `skills/orc-test/scripts/tests/test_lang_javascript.py`

**Interfaces:**
- Produces: `stryker.parse(path, root) -> Mutation` — reads the Stryker mutation-report JSON (schema v2; used by StrykerJS, Stryker.NET and dart_mutant). Statuses: `Killed`, `Survived`, `NoCoverage`, `CompileError`, `RuntimeError`, `Timeout`, `Ignored`, `Pending`. Score = Killed+Timeout / (Killed+Timeout+Survived+NoCoverage) — Stryker's own definition. Survivors = `Survived` + `NoCoverage`. `stryker.find(out) -> Path | None` — newest `*.json` under `out` whose top-level has `"files"`.

- [ ] **Step 1: Fixture (from the documented schema — verify on first real run) and failing tests**

```json
{"schemaVersion": "2", "thresholds": {"high": 80, "low": 60},
 "files": {"src/clamp.js": {"language": "javascript", "source": "...", "mutants": [
   {"id": "1", "mutatorName": "ConditionalExpression", "status": "Killed",
    "location": {"start": {"line": 2, "column": 7}, "end": {"line": 2, "column": 13}}, "replacement": "true"},
   {"id": "2", "mutatorName": "EqualityOperator", "status": "Survived",
    "location": {"start": {"line": 2, "column": 7}, "end": {"line": 2, "column": 13}}, "replacement": "x <= lo"},
   {"id": "3", "mutatorName": "BlockStatement", "status": "NoCoverage",
    "location": {"start": {"line": 4, "column": 15}, "end": {"line": 6, "column": 4}}, "replacement": "{}"},
   {"id": "4", "mutatorName": "StringLiteral", "status": "Ignored",
    "location": {"start": {"line": 8, "column": 1}, "end": {"line": 8, "column": 9}}, "replacement": "\"\""}]}}}
```

```python
# skills/orc-test/scripts/tests/test_stryker.py
import pathlib

from orc_test import stryker

FIX = pathlib.Path(__file__).parent / "fixtures" / "stryker.json"


def test_parse_scores_like_stryker_and_lists_survivors():
    m = stryker.parse(FIX, root=".")
    assert (m.killed, m.total) == (1, 3)              # Ignored is not counted
    assert [(s.file, s.line, s.description) for s in m.survivors] == [
        ("src/clamp.js", 2, "EqualityOperator → x <= lo"),
        ("src/clamp.js", 4, "BlockStatement → {} (no test reaches it)")]


def test_find_newest_report(tmp_path):
    (tmp_path / "old.json").write_text('{"files": {}}')
    new = tmp_path / "sub"
    new.mkdir()
    (new / "mutation.json").write_text('{"files": {}}')
    (tmp_path / "other.json").write_text('{"not": "a report"}')
    assert stryker.find(tmp_path) == new / "mutation.json"
```

```python
# skills/orc-test/scripts/tests/test_lang_javascript.py
import json

from orc_test.langs import javascript as js


def _pkg(tmp_path, dev):
    (tmp_path / "package.json").write_text(json.dumps({"devDependencies": dev}))


def test_vitest_when_present_else_jest(tmp_path):
    _pkg(tmp_path, {"vitest": "^5"})
    assert js.test_cmd(tmp_path, None) == ["npx", "vitest", "run"]
    assert js.test_cmd(tmp_path, "src/x") == ["npx", "vitest", "run", "src/x"]
    _pkg(tmp_path, {"jest": "^30"})
    assert js.test_cmd(tmp_path, None) == ["npx", "jest"]


def test_coverage_cmd_writes_lcov_into_out(tmp_path):
    _pkg(tmp_path, {"vitest": "^5"})
    out = tmp_path / "out"
    cmd = js.coverage_cmd(tmp_path, None, out)
    assert cmd[:4] == ["npx", "vitest", "run", "--coverage"]
    assert f"--coverage.reportsDirectory={out}" in cmd and "--coverage.reporter=lcov" in cmd


def test_mutation_unavailable_without_stryker(tmp_path):
    _pkg(tmp_path, {"vitest": "^5"})
    assert "npm i -D @stryker-mutator/core" in js.mutation_unavailable(tmp_path)
    _pkg(tmp_path, {"vitest": "^5", "@stryker-mutator/core": "^10"})
    assert js.mutation_unavailable(tmp_path) is None


def test_lint_needs_eslint_plugin(tmp_path):
    _pkg(tmp_path, {"vitest": "^5"})
    assert js.lint(tmp_path, None, tmp_path).startswith("eslint not configured")
```

- [ ] **Step 2: Run to verify they fail** — `ImportError`.

- [ ] **Step 3: Write them**

```python
# skills/orc-test/scripts/orc_test/stryker.py
"""The Stryker mutation-report JSON (schema v2): StrykerJS, Stryker.NET and dart_mutant all
write it. Score is Stryker's own: killed+timeout over everything that was actually testable."""

import json
import pathlib

from .model import Mutation, Survivor

_KILLED = {"Killed", "Timeout"}
_ALIVE = {"Survived", "NoCoverage"}


def find(out):
    hits = []
    for p in pathlib.Path(out).rglob("*.json"):
        try:
            if "files" in json.loads(p.read_text()):
                hits.append(p)
        except (ValueError, OSError):
            pass
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def parse(path, root):
    data = json.loads(pathlib.Path(path).read_text())
    killed, total, survivors = 0, 0, []
    for file, entry in data.get("files", {}).items():
        for mut in entry.get("mutants", []):
            status = mut.get("status")
            if status in _KILLED:
                killed += 1
                total += 1
            elif status in _ALIVE:
                total += 1
                desc = f"{mut.get('mutatorName')} → {mut.get('replacement', '')}".strip()
                if status == "NoCoverage":
                    desc += " (no test reaches it)"
                survivors.append(Survivor(file, mut["location"]["start"]["line"], desc))
    return Mutation(killed, total, survivors)
```

```python
# skills/orc-test/scripts/orc_test/langs/javascript.py
"""JavaScript/TypeScript: vitest or jest, lcov via their coverage reporters, StrykerJS."""

import json
import pathlib
import shutil

from .. import lcov, stryker
from ..model import Finding
from ..runner import run

KEY = "javascript"
LABEL = "JS/TS"
MARKERS = ["package.json"]
TOOLS = {"npx": "install Node.js (https://nodejs.org) — npx ships with npm"}
CAVEATS = ["Stryker's incremental file is reports/stryker-incremental.json; commit it or add it "
           "to .gitignore, either is fine, but do not delete it between runs."]


def _deps(root):
    pkg = pathlib.Path(root) / "package.json"
    data = json.loads(pkg.read_text()) if pkg.exists() else {}
    return {**data.get("dependencies", {}), **data.get("devDependencies", {})}


def _runner(root):
    return "vitest" if "vitest" in _deps(root) else "jest"


def missing(root):
    return [t for t in TOOLS if shutil.which(t) is None]


def test_cmd(root, target):
    base = ["npx", "vitest", "run"] if _runner(root) == "vitest" else ["npx", "jest"]
    return base + ([target] if target else [])


def coverage_cmd(root, target, out):
    if _runner(root) == "vitest":
        return ["npx", "vitest", "run", "--coverage", "--coverage.reporter=lcov",
                "--coverage.reporter=html", f"--coverage.reportsDirectory={out}"] + ([target] if target else [])
    return ["npx", "jest", "--coverage", "--coverageReporters=lcov", "--coverageReporters=html",
            f"--coverageDirectory={out}"] + ([target] if target else [])


def coverage_parse(root, out):
    return lcov.parse(pathlib.Path(out) / "lcov.info")


def mutation_unavailable(root):
    if "@stryker-mutator/core" not in _deps(root):
        return ("StrykerJS not installed — npm i -D @stryker-mutator/core "
                f"@stryker-mutator/{_runner(root)}-runner, then npx stryker init")
    return None


def mutation_cmd(root, target, out):
    cmd = ["npx", "stryker", "run", "--incremental", "--reporters", "json,progress",
           f"--jsonReporter.fileName={pathlib.Path(out) / 'mutation.json'}"]
    if target:
        cmd += ["--mutate", f"{target}/**/*"]
    return cmd


def mutation_parse(root, out):
    return stryker.parse(stryker.find(out), root)


def lint(root, target, out):
    deps = _deps(root)
    plugin = next((p for p in ("@vitest/eslint-plugin", "eslint-plugin-jest") if p in deps), None)
    if not plugin or "eslint" not in deps:
        return "eslint not configured with @vitest/eslint-plugin or eslint-plugin-jest"
    cp = run(["npx", "eslint", "--format", "json", "--no-error-on-unmatched-pattern", target or "."], cwd=root)
    try:
        results = json.loads(cp.stdout[cp.stdout.index("["):])
    except ValueError:
        return f"eslint produced no JSON (exit {cp.returncode})"
    prefix = "vitest/" if plugin.startswith("@vitest") else "jest/"
    return [Finding(str(pathlib.Path(r["filePath"]).relative_to(root)), m["line"], m["message"])
            for r in results for m in r["messages"] if (m.get("ruleId") or "").startswith(prefix)]
```

Append `javascript` to `langs/__init__.py`: `from . import javascript, python` / `ALL = [python, javascript]`.

- [ ] **Step 4: Write `languages/javascript.md`** with the same eight sections as `python.md`. Content, researched 2026-09-11 (npm registry): vitest 5.0.0 / jest 30.5.1 (vitest chosen when in `devDependencies`, else jest); coverage `@vitest/coverage-v8` 5.0.0 — `--coverage.reporter=lcov --coverage.reportsDirectory=<out>` → `<out>/lcov.info`; jest `--coverage --coverageReporters=lcov --coverageDirectory=<out>`; project-side gate: vitest `coverage.thresholds.lines: 80`, jest `coverageThreshold.global.lines: 80`. Mutation: StrykerJS 10.0.0 (`@stryker-mutator/core` + `@stryker-mutator/vitest-runner` or `jest-runner`), `npx stryker run --incremental` (incremental file `reports/stryker-incremental.json`), JSON report read from `<out>/mutation.json`; a path becomes `--mutate <path>/**/*`. Lint: `@vitest/eslint-plugin` 1.6.27 or `eslint-plugin-jest` 29.16.6 through the project's own eslint config (rules `vitest/expect-expect`, `vitest/no-disabled-tests`, `vitest/no-identical-title`, and the `jest/` equivalents); not run when the plugin is absent, and the report says so. Caveats: `eslint-plugin-vitest` (no scope) is the abandoned 2024 package — the maintained one is `@vitest/eslint-plugin`; Stryker's incremental diff only sees mutated and test files. Add `"javascript"` to `EXPECTED` in `hooks/scripts/tests/test_orc_test_languages.py`.

- [ ] **Step 5: Run both suites** — `cd skills/orc-test/scripts && python3 -m pytest tests/ -v` → 35 passed; `cd hooks/scripts && python3 -m pytest tests/test_orc_test_languages.py -v` → 2 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-test hooks/scripts/tests/test_orc_test_languages.py
git commit -m "orc-test: JavaScript/TypeScript — vitest or jest, lcov, StrykerJS via the shared Stryker JSON reader

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 11: `jacoco.py` + `pitest.py` + `langs/java.py` + `languages/java.md`

**Files:**
- Create: `skills/orc-test/scripts/orc_test/jacoco.py`, `skills/orc-test/scripts/orc_test/pitest.py`, `skills/orc-test/scripts/orc_test/langs/java.py`, `skills/orc-test/scripts/tests/fixtures/jacoco.xml`, `skills/orc-test/scripts/tests/fixtures/mutations.xml`, `skills/orc-test/languages/java.md`
- Modify: `langs/__init__.py` (append `java`), `hooks/scripts/tests/test_orc_test_languages.py` (`"java"`)
- Test: `skills/orc-test/scripts/tests/test_jacoco_pitest.py`, `skills/orc-test/scripts/tests/test_lang_java.py`

**Interfaces:**
- Produces: `jacoco.parse(path) -> Coverage` (per `<sourcefile>` `<counter type="LINE">`; file key `package/name`), `pitest.parse(path) -> Mutation` (statuses `KILLED`, `TIMED_OUT` count as killed; `SURVIVED`, `NO_COVERAGE` as survivors; `NON_VIABLE`, `MEMORY_ERROR`, `RUN_ERROR` not counted). `jacoco.find(root, out) -> Path | None` and `pitest.find(root) -> Path | None` locate the report the build wrote (Maven and Gradle put them in different places).

- [ ] **Step 1: Fixtures (from the documented XML formats — verify on first real run) and failing tests**

```xml
<!-- skills/orc-test/scripts/tests/fixtures/jacoco.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<report name="demo">
  <package name="com/example">
    <class name="com/example/Clamp" sourcefilename="Clamp.java">
      <counter type="LINE" missed="2" covered="4"/>
    </class>
    <sourcefile name="Clamp.java">
      <line nr="3" mi="0" ci="1"/><line nr="4" mi="1" ci="0"/>
      <counter type="INSTRUCTION" missed="5" covered="9"/>
      <counter type="LINE" missed="2" covered="4"/>
    </sourcefile>
    <sourcefile name="Other.java">
      <counter type="LINE" missed="0" covered="3"/>
    </sourcefile>
    <counter type="LINE" missed="2" covered="7"/>
  </package>
  <counter type="LINE" missed="2" covered="7"/>
</report>
```

```xml
<!-- skills/orc-test/scripts/tests/fixtures/mutations.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<mutations>
<mutation detected='true' status='KILLED' numberOfTestsRun='1'><sourceFile>Clamp.java</sourceFile><mutatedClass>com.example.Clamp</mutatedClass><mutatedMethod>clamp</mutatedMethod><methodDescription>(III)I</methodDescription><lineNumber>4</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.ConditionalsBoundaryMutator</mutator><indexes><index>5</index></indexes><blocks><block>0</block></blocks><killingTest>com.example.ClampTest.[engine:junit-jupiter]/[class:com.example.ClampTest]/[method:low()]</killingTest><description>changed conditional boundary</description></mutation>
<mutation detected='false' status='SURVIVED' numberOfTestsRun='1'><sourceFile>Clamp.java</sourceFile><mutatedClass>com.example.Clamp</mutatedClass><mutatedMethod>clamp</mutatedMethod><methodDescription>(III)I</methodDescription><lineNumber>6</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.ConditionalsBoundaryMutator</mutator><indexes><index>9</index></indexes><blocks><block>2</block></blocks><killingTest/><description>changed conditional boundary</description></mutation>
<mutation detected='false' status='NO_COVERAGE' numberOfTestsRun='0'><sourceFile>Other.java</sourceFile><mutatedClass>com.example.Other</mutatedClass><mutatedMethod>go</mutatedMethod><methodDescription>()V</methodDescription><lineNumber>9</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.VoidMethodCallMutator</mutator><indexes><index>1</index></indexes><blocks><block>0</block></blocks><killingTest/><description>removed call to log</description></mutation>
<mutation detected='false' status='NON_VIABLE' numberOfTestsRun='0'><sourceFile>Other.java</sourceFile><mutatedClass>com.example.Other</mutatedClass><mutatedMethod>go</mutatedMethod><methodDescription>()V</methodDescription><lineNumber>10</lineNumber><mutator>x</mutator><indexes><index>2</index></indexes><blocks><block>1</block></blocks><killingTest/><description>x</description></mutation>
</mutations>
```

```python
# skills/orc-test/scripts/tests/test_jacoco_pitest.py
import pathlib

from orc_test import jacoco, pitest

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_jacoco_per_sourcefile_line_counters():
    cov = jacoco.parse(FIX / "jacoco.xml")
    assert cov.files == {"com/example/Clamp.java": (4, 6), "com/example/Other.java": (3, 3)}
    assert (cov.covered, cov.total) == (7, 9)


def test_pitest_statuses():
    m = pitest.parse(FIX / "mutations.xml")
    assert (m.killed, m.total) == (1, 3)
    assert [(s.file, s.line) for s in m.survivors] == [("com/example/Clamp.java", 6), ("com/example/Other.java", 9)]
    assert m.survivors[0].description == "changed conditional boundary"
    assert "(no test reaches it)" in m.survivors[1].description


def test_find_maven_and_gradle_locations(tmp_path):
    (tmp_path / "target" / "site" / "jacoco").mkdir(parents=True)
    (tmp_path / "target" / "site" / "jacoco" / "jacoco.xml").write_text("<report/>")
    assert jacoco.find(tmp_path) == tmp_path / "target" / "site" / "jacoco" / "jacoco.xml"
    g = tmp_path / "build" / "reports" / "jacoco" / "test"
    g.mkdir(parents=True)
    (g / "jacocoTestReport.xml").write_text("<report/>")
    assert jacoco.find(tmp_path) == g / "jacocoTestReport.xml"       # newest wins
    (tmp_path / "target" / "pit-reports" / "202609111200").mkdir(parents=True)
    (tmp_path / "target" / "pit-reports" / "202609111200" / "mutations.xml").write_text("<mutations/>")
    assert pitest.find(tmp_path).name == "mutations.xml"
```

```python
# skills/orc-test/scripts/tests/test_lang_java.py
from orc_test.langs import java


def test_maven_vs_gradle(tmp_path):
    (tmp_path / "pom.xml").write_text("<project/>")
    assert java.test_cmd(tmp_path, None) == ["mvn", "-q", "test"]
    assert java.test_cmd(tmp_path, "src/main/java/com/x") == ["mvn", "-q", "test", "-Dtest=com.x.*"]
    (tmp_path / "pom.xml").unlink()
    (tmp_path / "build.gradle.kts").write_text("")
    assert java.test_cmd(tmp_path, None) == ["./gradlew", "test"]


def test_coverage_cmd_maven_fully_qualified(tmp_path):
    (tmp_path / "pom.xml").write_text("<project/>")
    cmd = java.coverage_cmd(tmp_path, None, tmp_path)
    assert cmd == ["mvn", "-q", "org.jacoco:jacoco-maven-plugin:prepare-agent", "test",
                   "org.jacoco:jacoco-maven-plugin:report"]


def test_mutation_needs_junit5_plugin_declared(tmp_path):
    (tmp_path / "pom.xml").write_text("<project><dependencies></dependencies></project>")
    assert "pitest-junit5-plugin" in java.mutation_unavailable(tmp_path)
    (tmp_path / "pom.xml").write_text("<project><artifactId>pitest-junit5-plugin</artifactId></project>")
    assert java.mutation_unavailable(tmp_path) is None
```

- [ ] **Step 2: Run to verify they fail** — `ImportError`.

- [ ] **Step 3: Write them**

```python
# skills/orc-test/scripts/orc_test/jacoco.py
"""JaCoCo XML → Coverage. Kover (Kotlin) writes the same format."""

import pathlib
import xml.etree.ElementTree as ET

from .model import Coverage

_LOCATIONS = ["target/site/jacoco/jacoco.xml", "build/reports/jacoco/test/jacocoTestReport.xml",
              "build/reports/kover/report.xml"]


def find(root):
    hits = [p for loc in _LOCATIONS if (p := pathlib.Path(root) / loc).exists()]
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def parse(path):
    files = {}
    for pkg in ET.parse(path).getroot().iter("package"):
        for sf in pkg.iter("sourcefile"):
            c = next((c for c in sf.iter("counter") if c.get("type") == "LINE"), None)
            if c is not None:
                covered, missed = int(c.get("covered")), int(c.get("missed"))
                files[f"{pkg.get('name')}/{sf.get('name')}"] = (covered, covered + missed)
    return Coverage(sum(c for c, _ in files.values()), sum(t for _, t in files.values()), files)
```

```python
# skills/orc-test/scripts/orc_test/pitest.py
"""Pitest mutations.xml → Mutation. Java and Kotlin both."""

import pathlib
import xml.etree.ElementTree as ET

from .model import Mutation, Survivor

_KILLED = {"KILLED", "TIMED_OUT"}
_ALIVE = {"SURVIVED", "NO_COVERAGE"}


def find(root):
    hits = list(pathlib.Path(root).glob("target/pit-reports/**/mutations.xml")) + \
           list(pathlib.Path(root).glob("build/reports/pitest/**/mutations.xml"))
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def parse(path):
    killed, total, survivors = 0, 0, []
    for m in ET.parse(path).getroot().iter("mutation"):
        status = m.get("status")
        if status in _KILLED:
            killed += 1
            total += 1
        elif status in _ALIVE:
            total += 1
            pkg = m.findtext("mutatedClass", "").rsplit(".", 1)[0].replace(".", "/")
            desc = m.findtext("description", "")
            if status == "NO_COVERAGE":
                desc += " (no test reaches it)"
            survivors.append(Survivor(f"{pkg}/{m.findtext('sourceFile')}", int(m.findtext("lineNumber", "0")), desc))
    return Mutation(killed, total, survivors)
```

```python
# skills/orc-test/scripts/orc_test/langs/java.py
"""Java: JUnit 5 through Maven or Gradle, JaCoCo, Pitest, PMD's unit-test rules."""

import json
import pathlib
import shutil

from .. import jacoco, pitest
from ..model import Finding
from ..runner import run

KEY = "java"
LABEL = "Java"
MARKERS = ["pom.xml", "build.gradle", "build.gradle.kts"]
TOOLS = {"java": "install a JDK (https://adoptium.net)"}
CAVEATS = ["Gradle projects must apply the `jacoco` plugin (and `pitest` for TCE) themselves; "
           "Maven needs nothing in the pom for coverage, only the pitest-junit5-plugin dependency for TCE."]

_JACOCO = "org.jacoco:jacoco-maven-plugin"


def _maven(root):
    return (pathlib.Path(root) / "pom.xml").exists()


def _gradle_cmd(root):
    return ["./gradlew"] if (pathlib.Path(root) / "gradlew").exists() else ["gradle"]


def missing(root):
    gone = [t for t in TOOLS if shutil.which(t) is None]
    if _maven(root) and shutil.which("mvn") is None:
        gone.append("mvn")
        TOOLS["mvn"] = "install Maven (https://maven.apache.org)"
    return gone


def _pkg_filter(target):
    # src/main/java/com/x → com.x.* ; anything else: no narrowing
    parts = pathlib.Path(target).parts
    if "java" in parts:
        return ".".join(parts[parts.index("java") + 1:]) + ".*"
    return None


def test_cmd(root, target):
    if _maven(root):
        f = _pkg_filter(target) if target else None
        return ["mvn", "-q", "test"] + ([f"-Dtest={f}"] if f else [])
    return _gradle_cmd(root) + ["test"]


def coverage_cmd(root, target, out):
    if _maven(root):
        return ["mvn", "-q", f"{_JACOCO}:prepare-agent", "test", f"{_JACOCO}:report"]
    return _gradle_cmd(root) + ["test", "jacocoTestReport"]


def coverage_parse(root, out):
    return jacoco.parse(jacoco.find(root))


def mutation_unavailable(root):
    if _maven(root):
        if "pitest-junit5-plugin" not in (pathlib.Path(root) / "pom.xml").read_text():
            return ("Pitest needs the org.pitest:pitest-junit5-plugin dependency in the pom "
                    "(plus JUnit 5) — see languages/java.md")
        return None
    build = next(pathlib.Path(root).glob("build.gradle*")).read_text()
    return None if "pitest" in build else "Gradle project does not apply the pitest plugin (info.solidsoft.pitest)"


def mutation_cmd(root, target, out):
    if _maven(root):
        cmd = ["mvn", "-q", "org.pitest:pitest-maven:mutationCoverage", "-DoutputFormats=XML,HTML",
               "-DwithHistory", "-DtimestampedReports=false"]
        f = _pkg_filter(target) if target else None
        return cmd + ([f"-DtargetClasses={f}"] if f else [])
    return _gradle_cmd(root) + ["pitest"]


def mutation_parse(root, out):
    return pitest.parse(pitest.find(root))


def lint(root, target, out):
    if shutil.which("pmd") is None:
        return "PMD not installed — https://pmd.github.io (`pmd check` with the unit-test rules)"
    tests = pathlib.Path(root) / (target or "src/test")
    cp = run(["pmd", "check", "-d", str(tests), "-f", "json", "--no-progress", "-R",
              "category/java/bestpractices.xml/UnitTestShouldIncludeAssert,"
              "category/java/bestpractices.xml/UnitTestContainsTooManyAsserts"], cwd=root)
    try:
        data = json.loads(cp.stdout[cp.stdout.index("{"):])
    except ValueError:
        return f"PMD produced no JSON (exit {cp.returncode})"
    return [Finding(str(pathlib.Path(f["filename"]).relative_to(root)), v["beginline"], v["description"])
            for f in data.get("files", []) for v in f.get("violations", [])]
```

Append `java` to `langs/__init__.py`.

- [ ] **Step 4: Write `languages/java.md`** — eight sections. Researched 2026-09-11: JUnit 5; Maven or Gradle (Gradle when no `pom.xml`; `./gradlew` if the wrapper exists). Coverage JaCoCo 0.8.15 (GitHub releases; **Maven Central's search API reported 0.8.13 — stale, check GitHub**): Maven fully-qualified goals need no pom change, report at `target/site/jacoco/jacoco.xml`; Gradle needs `plugins { jacoco }` and `jacocoTestReport { reports { xml.required = true } }`, report at `build/reports/jacoco/test/jacocoTestReport.xml`; project-side gate: `jacoco:check` with `minimum 0.80` on `LINE`. Mutation Pitest 1.30.0 (2026-08-27) + pitest-junit5-plugin 1.2.2: Maven `org.pitest:pitest-maven:mutationCoverage -DoutputFormats=XML -DwithHistory -DtimestampedReports=false` → `target/pit-reports/mutations.xml`; incremental via `-DwithHistory` (history file in `target/`) and `scmMutationCoverage` for changed-files-only; Gradle via `info.solidsoft.pitest` plugin → `build/reports/pitest/mutations.xml`. A path under `src/main/java/<pkg>` becomes `-DtargetClasses=<pkg>.*`. Lint: PMD 7 rules `UnitTestShouldIncludeAssert`, `UnitTestContainsTooManyAsserts`; `@Disabled` tests are not caught by PMD — grep is the fallback (`grep -rn @Disabled src/test`). Caveats: the JUnit 5 plugin is a pom dependency, not a CLI flag; Pitest exits non-zero when below its own `mutationThreshold` (leave that unset — `run.py` gates). Add `"java"` to `EXPECTED`.

- [ ] **Step 5: Run both suites** — package: 43 passed; hooks languages test: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-test hooks/scripts/tests/test_orc_test_languages.py
git commit -m "orc-test: Java — Maven/Gradle, JaCoCo XML reader, Pitest XML reader, PMD unit-test rules

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---
### Task 12: `licence.py` + `langs/kotlin.py` + `languages/kotlin.md`

**Files:**
- Create: `skills/orc-test/scripts/orc_test/licence.py`, `skills/orc-test/scripts/orc_test/langs/kotlin.py`, `skills/orc-test/languages/kotlin.md`
- Modify: `langs/__init__.py` (append `kotlin`), `langs/java.py` (MARKERS stay; Kotlin claims a Gradle project when `.kt` files exist — see `detect` note), `hooks/scripts/tests/test_orc_test_languages.py` (`"kotlin"`)
- Test: `skills/orc-test/scripts/tests/test_licence.py`, `skills/orc-test/scripts/tests/test_lang_kotlin.py`

**Interfaces:**
- Produces: `licence.open_source(root) -> str | None` — the recognised licence name (`MIT`, `Apache-2.0`, `GPL`, `LGPL`, `AGPL`, `BSD`, `MPL-2.0`, `ISC`, `Unlicense`) found in `LICENSE`, `LICENSE.md`, `LICENSE.txt`, `LICENCE*`, `COPYING`, or the `license` field of `pyproject.toml`/`package.json`; else `None`.
- Kotlin overrides `MARKERS` matching: a Gradle project is Kotlin when any `*.kt` file exists at depth ≤ 4 under `src/`; then **Java does not also run** for it. Implement in `kotlin.py` as `def claims(root) -> bool` and teach `detect.languages` to skip `java` when `kotlin.claims(root)` — add the two-line rule to `detect.py` with a test.

- [ ] **Step 1: Write the failing tests**

```python
# skills/orc-test/scripts/tests/test_licence.py
from orc_test import licence


def test_recognises_common_licences(tmp_path):
    (tmp_path / "LICENSE").write_text("MIT License\n\nCopyright (c) 2026 ...")
    assert licence.open_source(tmp_path) == "MIT"
    (tmp_path / "LICENSE").write_text("Apache License\nVersion 2.0, January 2004")
    assert licence.open_source(tmp_path) == "Apache-2.0"
    (tmp_path / "LICENSE").write_text("GNU GENERAL PUBLIC LICENSE\nVersion 3")
    assert licence.open_source(tmp_path) == "GPL"


def test_none_when_missing_or_proprietary(tmp_path):
    assert licence.open_source(tmp_path) is None
    (tmp_path / "LICENSE").write_text("All rights reserved. Proprietary.")
    assert licence.open_source(tmp_path) is None


def test_manifest_field(tmp_path):
    (tmp_path / "package.json").write_text('{"license": "ISC"}')
    assert licence.open_source(tmp_path) == "ISC"
```

```python
# skills/orc-test/scripts/tests/test_lang_kotlin.py
from orc_test import detect, langs
from orc_test.langs import java, kotlin


def _gradle_kotlin(tmp_path):
    (tmp_path / "build.gradle.kts").write_text("plugins { kotlin(\"jvm\") }\n")
    (tmp_path / "src" / "main" / "kotlin").mkdir(parents=True)
    (tmp_path / "src" / "main" / "kotlin" / "A.kt").write_text("class A\n")
    return tmp_path


def test_kotlin_claims_gradle_project_and_java_steps_aside(tmp_path):
    repo = _gradle_kotlin(tmp_path)
    assert kotlin.claims(repo)
    assert [m.KEY for m in detect.languages(repo, [java, kotlin])] == ["kotlin"]


def test_coverage_is_kover(tmp_path):
    repo = _gradle_kotlin(tmp_path)
    assert kotlin.coverage_cmd(repo, None, tmp_path)[-2:] == ["test", "koverXmlReport"]


def test_arcmutate_only_with_open_source_licence(tmp_path):
    repo = _gradle_kotlin(tmp_path)
    (repo / "build.gradle.kts").write_text("plugins { id(\"info.solidsoft.pitest\") }\n")
    assert kotlin.mutation_unavailable(repo) is None
    assert "approximate" in kotlin.CAVEATS_FOR(repo)[0]
    (repo / "LICENSE").write_text("MIT License")
    assert "Arcmutate" in kotlin.CAVEATS_FOR(repo)[0] and "approximate" not in kotlin.CAVEATS_FOR(repo)[0]
```

- [ ] **Step 2: Run to verify they fail** — `ImportError`.

- [ ] **Step 3: Write them**

```python
# skills/orc-test/scripts/orc_test/licence.py
"""Is this project open source? Read from what the project already declares — never a new
setting. Arcmutate's Kotlin plugin is free only for open source; the day a project closes, its
LICENSE file is what changes, and the next run notices."""

import json
import pathlib
import re

_PATTERNS = [
    ("Apache-2.0", r"Apache License"), ("AGPL", r"AFFERO GENERAL PUBLIC LICENSE"),
    ("LGPL", r"LESSER GENERAL PUBLIC LICENSE"), ("GPL", r"GNU GENERAL PUBLIC LICENSE"),
    ("MPL-2.0", r"Mozilla Public License"), ("MIT", r"\bMIT License\b"),
    ("BSD", r"BSD \d-Clause|Redistribution and use in source and binary forms"),
    ("ISC", r"\bISC License\b"), ("Unlicense", r"This is free and unencumbered software"),
]
_FIELD = re.compile(r"^(Apache-2\.0|AGPL|LGPL|GPL|MPL-2\.0|MIT|BSD|ISC|Unlicense)", re.I)


def open_source(root):
    root = pathlib.Path(root)
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "LICENCE.md", "COPYING"):
        p = root / name
        if p.exists():
            text = p.read_text(errors="replace")
            for label, pat in _PATTERNS:
                if re.search(pat, text, re.I):
                    return label
    pkg = root / "package.json"
    if pkg.exists():
        field = json.loads(pkg.read_text()).get("license", "")
        if (m := _FIELD.match(str(field))):
            return m.group(1)
    py = root / "pyproject.toml"
    if py.exists():
        m = re.search(r'^license\s*=\s*"([^"]+)"', py.read_text(), re.M)
        if m and (f := _FIELD.match(m.group(1))):
            return f.group(1)
    return None
```

```python
# skills/orc-test/scripts/orc_test/langs/kotlin.py
"""Kotlin: Gradle + JUnit 5, Kover (JaCoCo-format XML), Pitest with or without Arcmutate."""

import pathlib
import shutil

from .. import jacoco, licence, pitest
from ..model import Finding
from ..runner import run

KEY = "kotlin"
LABEL = "Kotlin"
MARKERS = ["build.gradle", "build.gradle.kts"]
TOOLS = {"java": "install a JDK (https://adoptium.net)"}
CAVEATS = []          # computed per project — see CAVEATS_FOR


def claims(root):
    src = pathlib.Path(root) / "src"
    return src.exists() and any(True for _ in src.rglob("*.kt"))


def CAVEATS_FOR(root):
    if licence.open_source(root):
        return [f"TCE via Pitest + Arcmutate's Kotlin plugin (free for open source; this project "
                f"declares {licence.open_source(root)}). Arcmutate filters the junk mutants plain Pitest "
                "produces on Kotlin bytecode."]
    return ["TCE is approximate: plain Pitest on Kotlin bytecode reports junk mutants from compiler-"
            "generated code. Arcmutate's Kotlin plugin fixes that but needs an open-source licence, "
            "and this project does not declare one."]


def _gradle(root):
    return ["./gradlew"] if (pathlib.Path(root) / "gradlew").exists() else ["gradle"]


def missing(root):
    return [t for t in TOOLS if shutil.which(t) is None]


def test_cmd(root, target):
    return _gradle(root) + ["test"]


def coverage_cmd(root, target, out):
    return _gradle(root) + ["test", "koverXmlReport"]


def coverage_parse(root, out):
    return jacoco.parse(jacoco.find(root))


def mutation_unavailable(root):
    build = next(pathlib.Path(root).glob("build.gradle*")).read_text()
    return None if "pitest" in build else "Gradle project does not apply the pitest plugin (info.solidsoft.pitest)"


def mutation_cmd(root, target, out):
    return _gradle(root) + ["pitest"]


def mutation_parse(root, out):
    return pitest.parse(pitest.find(root))


def lint(root, target, out):
    if shutil.which("detekt") is None:
        return "detekt not installed — https://detekt.dev/docs/gettingstarted/cli"
    tests = pathlib.Path(root) / (target or "src/test")
    report = pathlib.Path(out) / "detekt.xml"
    run(["detekt", "--input", str(tests), "--report", f"xml:{report}"], cwd=root)
    import xml.etree.ElementTree as ET
    if not report.exists():
        return "detekt wrote no report"
    return [Finding(str(pathlib.Path(f.get("name")).relative_to(root)), int(e.get("line")), e.get("message"))
            for f in ET.parse(report).getroot().iter("file") for e in f.iter("error")]
```

In `detect.py`, after `found` is built:

```python
    keys = {m.KEY for m in found}
    if "kotlin" in keys and "java" in keys:
        kot = next(m for m in found if m.KEY == "kotlin")
        if kot.claims(root):
            found = [m for m in found if m.KEY != "java"]
        else:
            found = [m for m in found if m.KEY != "kotlin"]
```

`cli.cmd_analyze` prints `m.CAVEATS_FOR(root)` when the module defines it, else `m.CAVEATS`: replace the caveat loop with `for c in (m.CAVEATS_FOR(root) if hasattr(m, "CAVEATS_FOR") else m.CAVEATS):`.

- [ ] **Step 4: Write `languages/kotlin.md`** — researched 2026-09-11: Gradle + JUnit 5 (`./gradlew test`); coverage Kover 0.9.9 (`org.jetbrains.kotlinx.kover` plugin, `koverXmlReport` → `build/reports/kover/report.xml`, JaCoCo-format; project-side gate `kover { reports { verify { rule { minBound(80) } } } }`); mutation Pitest 1.30.0 via `info.solidsoft.pitest` Gradle plugin, and **Arcmutate's Kotlin plugin (`com.arcmutate:pitest-kotlin-plugin`, requires pitest ≥ 1.22.0, commercial, free for open source, licence file `arcmutate-licence.txt` at the project root)** — `run.py` reads the project's LICENSE to decide which caveat to print; the original `pitest-kotlin` open-source plugin is unmaintained. Lint: detekt (no test-specific rules; `@Disabled` and assertion-free tests are not caught — grep is the fallback). Caveats: junk mutants without Arcmutate; a private repo carrying an MIT file passes the licence check — Arcmutate's term is *publicly* open source, and that stays the user's to keep straight. Add `"kotlin"` to `EXPECTED`.

- [ ] **Step 5: Run both suites** — package: 50 passed; hooks: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-test hooks/scripts/tests/test_orc_test_languages.py
git commit -m "orc-test: Kotlin — Kover, Pitest, Arcmutate gated on the project's own licence file

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 13: `langs/csharp.py` + `languages/csharp.md`

**Files:**
- Create: `skills/orc-test/scripts/orc_test/langs/csharp.py`, `skills/orc-test/languages/csharp.md`
- Modify: `langs/__init__.py` (append `csharp`), `hooks/scripts/tests/test_orc_test_languages.py` (`"csharp"`)
- Test: `skills/orc-test/scripts/tests/test_lang_csharp.py`

**Interfaces:**
- Consumes: `lcov.parse` (coverlet's lcov), `stryker.parse/find` (Stryker.NET writes the same JSON).

- [ ] **Step 1: Write the failing tests**

```python
# skills/orc-test/scripts/tests/test_lang_csharp.py
from orc_test.langs import csharp as cs


def test_commands(tmp_path):
    (tmp_path / "App.sln").write_text("")
    assert cs.test_cmd(tmp_path, None) == ["dotnet", "test"]
    assert cs.test_cmd(tmp_path, "tests/App.Tests") == ["dotnet", "test", "tests/App.Tests"]
    out = tmp_path / "out"
    cmd = cs.coverage_cmd(tmp_path, None, out)
    assert cmd[:3] == ["dotnet", "test", "--collect:XPlat Code Coverage"]
    assert f"--results-directory={out}" in cmd
    assert "DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=lcov" in " ".join(cmd)


def test_coverage_parse_finds_lcov_under_results(tmp_path):
    d = tmp_path / "guid-1"
    d.mkdir()
    (d / "coverage.info").write_text("SF:App/A.cs\nDA:1,1\nDA:2,0\nend_of_record\n")
    assert cs.coverage_parse(tmp_path, tmp_path).files == {"App/A.cs": (1, 2)}


def test_mutation_needs_stryker_tool(tmp_path, monkeypatch):
    monkeypatch.setattr(cs.shutil, "which", lambda name: None)
    assert "dotnet tool install -g dotnet-stryker" in cs.mutation_unavailable(tmp_path)
    monkeypatch.setattr(cs.shutil, "which", lambda name: "/usr/bin/dotnet-stryker")
    assert cs.mutation_unavailable(tmp_path) is None
    cmd = cs.mutation_cmd(tmp_path, "src/App", tmp_path / "out")
    assert cmd[:3] == ["dotnet", "stryker", "--reporter"] and "--with-baseline" in cmd
    assert "--mutate" in cmd and "src/App/**/*.cs" in cmd


def test_lint_parses_xunit_analyzer_warnings(tmp_path, monkeypatch):
    out = ("App.Tests/AT.cs(12,9): warning xUnit2013: Do not use Assert.Equal() to check for collection size. "
           "[/x/App.Tests/App.Tests.csproj]\n"
           "App.Tests/AT.cs(20,5): warning xUnit1004: Test methods should not be skipped. [/x/App.Tests/App.Tests.csproj]\n"
           "App.Tests/AT.cs(30,1): warning CS0168: unrelated [/x/App.Tests/App.Tests.csproj]\n")
    monkeypatch.setattr(cs, "run", lambda cmd, cwd: type("R", (), {"stdout": out, "returncode": 0})())
    findings = cs.lint(tmp_path, None, tmp_path)
    assert [(f.file, f.line) for f in findings] == [("App.Tests/AT.cs", 12), ("App.Tests/AT.cs", 20)]
```

- [ ] **Step 2: Run to verify they fail** — `ImportError`.

- [ ] **Step 3: Write the module**

```python
# skills/orc-test/scripts/orc_test/langs/csharp.py
"""C#: dotnet test, coverlet (lcov), Stryker.NET (Stryker JSON), xunit.analyzers via dotnet build."""

import pathlib
import re
import shutil

from .. import lcov, stryker
from ..model import Finding
from ..runner import run

KEY = "csharp"
LABEL = "C#"
MARKERS = ["*.csproj", "*.sln"]
TOOLS = {"dotnet": "install the .NET SDK (https://dotnet.microsoft.com/download)"}
CAVEATS = ["Stryker.NET 5.0.0 targets .NET 10; on an older SDK pin 4.16.0 "
           "(dotnet tool install -g dotnet-stryker --version 4.16.0)."]

_COLLECT = "--collect:XPlat Code Coverage"
_WARN = re.compile(r"^(?P<file>[^(]+)\((?P<line>\d+),\d+\): warning (?P<code>xUnit\d+): (?P<msg>.*?) \[", re.M)


def missing(root):
    return [t for t in TOOLS if shutil.which(t) is None]


def test_cmd(root, target):
    return ["dotnet", "test"] + ([target] if target else [])


def coverage_cmd(root, target, out):
    return ["dotnet", "test", _COLLECT, f"--results-directory={out}",
            "--", "DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=lcov"] + \
           ([target] if target else [])


def coverage_parse(root, out):
    hits = list(pathlib.Path(out).rglob("coverage.info")) + list(pathlib.Path(out).rglob("*.lcov"))
    return lcov.parse(max(hits, key=lambda p: p.stat().st_mtime))


def mutation_unavailable(root):
    if shutil.which("dotnet-stryker") is None:
        return "Stryker.NET not installed — dotnet tool install -g dotnet-stryker"
    return None


def mutation_cmd(root, target, out):
    cmd = ["dotnet", "stryker", "--reporter", "json", "--reporter", "progress",
           "--with-baseline", "--output", str(out)]
    if target:
        cmd += ["--mutate", f"{target}/**/*.cs"]
    return cmd


def mutation_parse(root, out):
    return stryker.parse(stryker.find(out), root)


def lint(root, target, out):
    cp = run(["dotnet", "build", "--no-incremental", "-warnaserror-"] + ([target] if target else []), cwd=root)
    return [Finding(m["file"], int(m["line"]), f"{m['code']}: {m['msg']}") for m in _WARN.finditer(cp.stdout)]
```

Append `csharp` to `langs/__init__.py`.

- [ ] **Step 4: Write `languages/csharp.md`** — researched 2026-09-11 (NuGet): xUnit or NUnit under `dotnet test`; coverage coverlet.collector 10.0.1 via `--collect:"XPlat Code Coverage"` with the lcov format switch, results under `<out>/<guid>/coverage.info`; alternative `Microsoft.Testing.Extensions.CodeCoverage` 18.11.2 for Microsoft.Testing.Platform projects; project-side gate `coverlet.msbuild` `/p:Threshold=80 /p:ThresholdType=line`. Mutation Stryker.NET 5.0.0 (released 2026-09-11, .NET 10) / 4.16.0 for older SDKs: `dotnet stryker --reporter json --with-baseline --output <out>`; baseline (incremental) stored under the output path since 5.0; project-side gate `--break-at 70`. Lint: `xunit.analyzers` 2.0.0 runs at build — `run.py` parses `xUnit####` warnings from `dotnet build` (xUnit1004 skipped test, xUnit2013 collection size, xUnit1013 public method not a test, …); NUnit projects: `NUnit.Analyzers` warnings are `NUnit####` — not yet parsed, noted as a gap. Caveats: `dotnet-stryker` is a global tool, found on PATH as `dotnet-stryker`. Add `"csharp"` to `EXPECTED`.

- [ ] **Step 5: Run both suites** — package: 54 passed; hooks: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-test hooks/scripts/tests/test_orc_test_languages.py
git commit -m "orc-test: C# — dotnet test, coverlet lcov, Stryker.NET, xunit.analyzers warnings

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 14: `langs/dart.py` + `languages/dart.md`

**Files:**
- Create: `skills/orc-test/scripts/orc_test/langs/dart.py`, `skills/orc-test/scripts/tests/fixtures/mutation_test_junit.xml`, `skills/orc-test/languages/dart.md`
- Modify: `langs/__init__.py` (append `dart`), `hooks/scripts/tests/test_orc_test_languages.py` (`"dart"`)
- Test: `skills/orc-test/scripts/tests/test_lang_dart.py`

**Interfaces:**
- `mutation_test` (pub.dev 1.8.0) has no JSON; its `junit` report lists each mutation as a `<testcase>`, with `<failure>` for a survivor. Parser is local to this module.

- [ ] **Step 1: Fixture (from mutation_test's documented junit output — verify on first real run) and failing tests**

```xml
<!-- skills/orc-test/scripts/tests/fixtures/mutation_test_junit.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="lib/clamp.dart" tests="3" failures="1">
    <testcase name="lib/clamp.dart:3:10 &lt; replaced with &lt;=" classname="lib/clamp.dart"/>
    <testcase name="lib/clamp.dart:5:10 &gt; replaced with &gt;=" classname="lib/clamp.dart">
      <failure message="mutation survived">if (x &gt;= hi) return hi;</failure>
    </testcase>
    <testcase name="lib/clamp.dart:7:3 return replaced" classname="lib/clamp.dart"/>
  </testsuite>
</testsuites>
```

```python
# skills/orc-test/scripts/tests/test_lang_dart.py
import pathlib
import shutil

from orc_test.langs import dart

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_flutter_vs_dart(tmp_path):
    (tmp_path / "pubspec.yaml").write_text("name: x\ndependencies:\n  flutter:\n    sdk: flutter\n")
    assert dart.test_cmd(tmp_path, None) == ["flutter", "test"]
    assert dart.coverage_cmd(tmp_path, None, tmp_path / "out")[:3] == ["flutter", "test", "--coverage"]
    (tmp_path / "pubspec.yaml").write_text("name: x\n")
    assert dart.test_cmd(tmp_path, "test/a_test.dart") == ["dart", "test", "test/a_test.dart"]


def test_coverage_parse_reads_lcov_the_tool_wrote(tmp_path):
    (tmp_path / "coverage").mkdir()
    (tmp_path / "coverage" / "lcov.info").write_text("SF:lib/a.dart\nDA:1,1\nDA:2,0\nend_of_record\n")
    assert dart.coverage_parse(tmp_path, tmp_path / "out").files == {"lib/a.dart": (1, 2)}


def test_mutation_junit_parse():
    m = dart._parse_junit(FIX / "mutation_test_junit.xml")
    assert (m.killed, m.total) == (2, 3)
    assert (m.survivors[0].file, m.survivors[0].line) == ("lib/clamp.dart", 5)
    assert ">= " in m.survivors[0].description or "replaced" in m.survivors[0].description


def test_mutation_needs_dev_dependency(tmp_path):
    (tmp_path / "pubspec.yaml").write_text("name: x\n")
    assert "dart pub add --dev mutation_test" in dart.mutation_unavailable(tmp_path)
    (tmp_path / "pubspec.yaml").write_text("name: x\ndev_dependencies:\n  mutation_test: ^1.8.0\n")
    assert dart.mutation_unavailable(tmp_path) is None
```

- [ ] **Step 2: Run to verify they fail** — `ImportError`.

- [ ] **Step 3: Write the module**

```python
# skills/orc-test/scripts/orc_test/langs/dart.py
"""Dart/Flutter: dart test or flutter test, lcov via package:coverage, mutation_test (junit)."""

import pathlib
import re
import shutil
import xml.etree.ElementTree as ET

from .. import lcov
from ..model import Finding, Mutation, Survivor
from ..runner import run

KEY = "dart"
LABEL = "Dart"
MARKERS = ["pubspec.yaml"]
TOOLS = {"dart": "install the Dart SDK (https://dart.dev/get-dart) or Flutter"}
CAVEATS = ["mutation_test is young (pub.dev 1.8.0, 2026-02); its report is read from junit XML. "
           "dart_mutant (Rust, Stryker JSON) is the alternative if this proves unreliable.",
           "No test-specific lint exists for Dart; `dart analyze` runs, but it cannot see an "
           "assertion-free test."]

_CASE = re.compile(r"^(?P<file>[^:]+):(?P<line>\d+):\d+ (?P<what>.*)$")


def _flutter(root):
    return "sdk: flutter" in (pathlib.Path(root) / "pubspec.yaml").read_text()


def _tool(root):
    return "flutter" if _flutter(root) else "dart"


def missing(root):
    return [] if shutil.which(_tool(root)) else [_tool(root)] if _tool(root) == "dart" else ["flutter"]


def test_cmd(root, target):
    return [_tool(root), "test"] + ([target] if target else [])


def coverage_cmd(root, target, out):
    # both write coverage/lcov.info at the project root; --coverage on dart test needs
    # package:coverage's format step, which `dart test --coverage=DIR` does not run itself.
    if _flutter(root):
        return ["flutter", "test", "--coverage"] + ([target] if target else [])
    return ["bash", "-c", "dart test --coverage=coverage " + (target or "") +
            " && dart run coverage:format_coverage --lcov --in=coverage --out=coverage/lcov.info --packages=.dart_tool/package_config.json --report-on=lib"]


def coverage_parse(root, out):
    return lcov.parse(pathlib.Path(root) / "coverage" / "lcov.info")


def mutation_unavailable(root):
    if "mutation_test" not in (pathlib.Path(root) / "pubspec.yaml").read_text():
        return "mutation_test not installed — dart pub add --dev mutation_test"
    return None


def mutation_cmd(root, target, out):
    return ["dart", "run", "mutation_test", "-f", "junit", "-o", str(out)] + ([target] if target else [])


def mutation_parse(root, out):
    report = max(pathlib.Path(out).rglob("*.xml"), key=lambda p: p.stat().st_mtime)
    return _parse_junit(report)


def _parse_junit(path):
    killed, total, survivors = 0, 0, []
    for case in ET.parse(path).getroot().iter("testcase"):
        total += 1
        if case.find("failure") is None:
            killed += 1
            continue
        m = _CASE.match(case.get("name", ""))
        if m:
            survivors.append(Survivor(m["file"], int(m["line"]), m["what"]))
        else:
            survivors.append(Survivor(case.get("classname", "?"), 0, case.get("name", "")))
    return Mutation(killed, total, survivors)


def lint(root, target, out):
    return "no test-specific lint exists for Dart (dart analyze has no assertion-free rule)"
```

Append `dart` to `langs/__init__.py`.

- [ ] **Step 4: Write `languages/dart.md`** — researched 2026-09-11 (pub.dev): `test` 1.32.0; `flutter test --coverage` writes `coverage/lcov.info` directly; plain Dart needs `package:coverage` 1.15.1's `format_coverage` step (command above); **no threshold flag in either — `run.py` gates**. Mutation: `mutation_test` 1.8.0 (`dart pub add --dev mutation_test`, `dart run mutation_test -f junit -o <out>`; defaults to `dart test` and `lib/`; its own gate is an XML config, unused); alternative `dart_mutant` (github.com/Nimblesite/dart_mutant, MIT, Rust, Stryker JSON — `run.py`'s `stryker.py` would read it unchanged). Lint: none. Caveats as in the module; the `-f junit` name-format assumption is the first thing to check on a real run. Add `"dart"` to `EXPECTED`.

- [ ] **Step 5: Run both suites** — package: 58 passed; hooks: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-test hooks/scripts/tests/test_orc_test_languages.py
git commit -m "orc-test: Dart/Flutter — lcov via package:coverage, mutation_test junit report

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 15: `langs/swift.py` + `languages/swift.md`

**Files:**
- Create: `skills/orc-test/scripts/orc_test/langs/swift.py`, `skills/orc-test/scripts/tests/fixtures/xccov.json`, `skills/orc-test/scripts/tests/fixtures/muter.json`, `skills/orc-test/languages/swift.md`
- Modify: `langs/__init__.py` (append `swift`), `hooks/scripts/tests/test_orc_test_languages.py` (`"swift"`)
- Test: `skills/orc-test/scripts/tests/test_lang_swift.py`

**Interfaces:**
- xccov JSON (`xcrun xccov view --report --json <x>.xcresult`): `{"lineCoverage": 0.8, "coveredLines": 8, "executableLines": 10, "targets": [{"name": ..., "files": [{"path": "/abs/Sources/A.swift", "coveredLines": 4, "executableLines": 6, "lineCoverage": 0.66}]}]}`.
- Muter JSON (`muter --format json --output <file>`), from `MuterTestReport` in its source (read 2026-09-11): `{"globalMutationScore": 62, "totalAppliedMutationOperators": 8, "numberOfKilledMutants": 5, "fileReports": [{"fileName": "Clamp.swift", "mutationScore": 50, "appliedOperators": [...]}]}`. `appliedOperators` entries' inner shape is not confirmed — the parser uses only the file-level numbers and marks survivors by file with line 0 until a real run supplies the shape.

- [ ] **Step 1: Fixtures (from documented output — verify on first real run) and failing tests**

```json
{"lineCoverage": 0.7, "coveredLines": 7, "executableLines": 10, "targets": [{"name": "App", "files": [
  {"path": "/Users/x/App/Sources/App/Clamp.swift", "coveredLines": 4, "executableLines": 6, "lineCoverage": 0.6667},
  {"path": "/Users/x/App/Sources/App/Other.swift", "coveredLines": 3, "executableLines": 4, "lineCoverage": 0.75}]}]}
```

```json
{"globalMutationScore": 62, "totalAppliedMutationOperators": 8, "numberOfKilledMutants": 5, "projectCodeCoverage": 70,
 "fileReports": [{"fileName": "Clamp.swift", "mutationScore": 50, "appliedOperators": [{}, {}, {}, {}]},
                 {"fileName": "Other.swift", "mutationScore": 75, "appliedOperators": [{}, {}, {}, {}]}],
 "timeElapsed": "00:03:12.000"}
```

```python
# skills/orc-test/scripts/tests/test_lang_swift.py
import pathlib

from orc_test.langs import swift

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_spm_vs_xcodeproj(tmp_path):
    (tmp_path / "Package.swift").write_text("")
    assert swift.test_cmd(tmp_path, None) == ["swift", "test"]
    assert swift.coverage_cmd(tmp_path, None, tmp_path)[:3] == ["swift", "test", "--enable-code-coverage"]
    (tmp_path / "Package.swift").unlink()
    (tmp_path / "App.xcodeproj").mkdir()
    cmd = swift.test_cmd(tmp_path, None)
    assert cmd[:2] == ["xcodebuild", "test"] and "-scheme" in cmd and "App" in cmd


def test_xccov_parse_relativises_paths(tmp_path):
    (tmp_path / "xccov.json").write_text((FIX / "xccov.json").read_text())
    cov = swift._parse_xccov(tmp_path / "xccov.json", root="/Users/x/App")
    assert cov.files == {"Sources/App/Clamp.swift": (4, 6), "Sources/App/Other.swift": (3, 4)}
    assert (cov.covered, cov.total) == (7, 10)


def test_muter_parse_uses_file_level_numbers():
    m = swift._parse_muter(FIX / "muter.json")
    assert (m.killed, m.total) == (5, 8)
    assert [(s.file, s.line) for s in m.survivors] == [("Clamp.swift", 0), ("Other.swift", 0)]
    assert "50%" in m.survivors[0].description


def test_needs_mac(tmp_path, monkeypatch):
    monkeypatch.setattr(swift.platform, "system", lambda: "Linux")
    (tmp_path / "App.xcodeproj").mkdir()
    assert swift.missing(tmp_path) == ["xcodebuild"]
```

- [ ] **Step 2: Run to verify they fail** — `ImportError`.

- [ ] **Step 3: Write the module**

```python
# skills/orc-test/scripts/orc_test/langs/swift.py
"""Swift: swift test (SPM, any OS) or xcodebuild (Mac only); xccov for coverage; Muter for TCE."""

import json
import pathlib
import platform
import shutil

from ..model import Coverage, Finding, Mutation, Survivor
from ..runner import run

KEY = "swift"
LABEL = "Swift"
MARKERS = ["Package.swift", "*.xcodeproj"]
TOOLS = {"swift": "install Swift (https://swift.org/install) — Xcode on a Mac"}
CAVEATS = ["Muter has two open bugs (muter#307, #310, 2026) where SPM projects score 0%; treat "
           "a 0% TCE on an SPM package as the bug until a real run says otherwise.",
           "Muter's per-mutant detail is not parsed yet — survivors are listed per file."]


def _xcodeproj(root):
    return next(pathlib.Path(root).glob("*.xcodeproj"), None)


def missing(root):
    if _xcodeproj(root) and (platform.system() != "Darwin" or shutil.which("xcodebuild") is None):
        return ["xcodebuild"]
    return [] if shutil.which("swift") else ["swift"]


def _scheme(root):
    return _xcodeproj(root).stem


def test_cmd(root, target):
    if (proj := _xcodeproj(root)):
        return ["xcodebuild", "test", "-project", proj.name, "-scheme", _scheme(root),
                "-destination", "platform=macOS"] + ([f"-only-testing:{target}"] if target else [])
    return ["swift", "test"] + (["--filter", target] if target else [])


def coverage_cmd(root, target, out):
    if _xcodeproj(root):
        return ["xcodebuild", "test", "-project", _xcodeproj(root).name, "-scheme", _scheme(root),
                "-destination", "platform=macOS", "-enableCodeCoverage", "YES",
                "-resultBundlePath", str(pathlib.Path(out) / "result.xcresult")]
    return ["swift", "test", "--enable-code-coverage"]


def coverage_parse(root, out):
    out = pathlib.Path(out)
    if _xcodeproj(root):
        cp = run(["xcrun", "xccov", "view", "--report", "--json", str(out / "result.xcresult")], cwd=root)
        (out / "xccov.json").write_text(cp.stdout)
        return _parse_xccov(out / "xccov.json", root)
    cp = run(["swift", "test", "--show-codecov-path"], cwd=root)
    return _parse_xccov(cp.stdout.strip(), root)   # SPM's codecov JSON has the same lineCoverage/files shape


def _parse_xccov(path, root):
    data = json.loads(pathlib.Path(path).read_text())
    files = {}
    for target in data.get("targets", [data]):
        for f in target.get("files", []):
            p = f["path"]
            rel = str(pathlib.Path(p).relative_to(root)) if str(p).startswith(str(root)) else p
            files[rel] = (int(f["coveredLines"]), int(f["executableLines"]))
    return Coverage(sum(c for c, _ in files.values()), sum(t for _, t in files.values()), files)


def mutation_unavailable(root):
    if shutil.which("muter") is None:
        return "Muter not installed — brew install muter-mutation-testing/formulae/muter"
    if not (pathlib.Path(root) / "muter.conf.yml").exists():
        return "no muter.conf.yml — run `muter init` once in the project"
    return None


def mutation_cmd(root, target, out):
    cmd = ["muter", "run", "--format", "json", "--output", str(pathlib.Path(out) / "muter.json")]
    if target:
        cmd += ["--files-to-mutate", f"{target}/**/*.swift"]
    return cmd


def mutation_parse(root, out):
    return _parse_muter(pathlib.Path(out) / "muter.json")


def _parse_muter(path):
    data = json.loads(pathlib.Path(path).read_text())
    survivors = [Survivor(f["fileName"], 0, f"file mutation score {f['mutationScore']}%")
                 for f in data.get("fileReports", []) if f.get("mutationScore", 100) < 100]
    return Mutation(int(data.get("numberOfKilledMutants", 0)),
                    int(data.get("totalAppliedMutationOperators", 0)), survivors)


def lint(root, target, out):
    if shutil.which("swiftlint") is None:
        return "SwiftLint not installed — brew install swiftlint"
    cp = run(["swiftlint", "lint", "--reporter", "json", "--quiet", target or "."], cwd=root)
    try:
        data = json.loads(cp.stdout[cp.stdout.index("["):])
    except ValueError:
        return f"swiftlint produced no JSON (exit {cp.returncode})"
    return [Finding(str(pathlib.Path(v["file"]).relative_to(root)), v["line"], f"{v['rule_id']}: {v['reason']}")
            for v in data if "test" in v["file"].lower()]
```

Append `swift` to `langs/__init__.py`.

- [ ] **Step 4: Write `languages/swift.md`** — researched 2026-09-11: Swift Testing (`@Test`, `#expect`) or XCTest; SPM `swift test` on any OS, `xcodebuild test` on a Mac (the stack skill `stack-ios-native` already says a Mac is required for app targets); coverage `swift test --enable-code-coverage` + `--show-codecov-path`, or `-enableCodeCoverage YES -resultBundlePath` + `xcrun xccov view --report --json`; **no threshold flag — `run.py` gates**. Mutation: Muter (github.com/muter-mutation-testing/muter, `brew install muter-mutation-testing/formulae/muter`, last pushed 2026-07-21, no tagged release since 16/2023; `muter init` writes `muter.conf.yml` with `executable` and `arguments`; `--format json --output`; `--files-to-mutate` narrows; **open issues #307/#310: SPM score always 0%**); Swift Testing failure detection landed (#306 closed). Lint: SwiftLint 0.65.1 `--reporter json`, filtered to test files. Caveats as above. Add `"swift"` to `EXPECTED`.

- [ ] **Step 5: Run both suites** — package: 62 passed; hooks: 7 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-test hooks/scripts/tests/test_orc_test_languages.py
git commit -m "orc-test: Swift — swift test / xcodebuild, xccov JSON, Muter JSON (file-level until a real run)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 16: `langs/gdscript.py` + `languages/gdscript.md`

**Files:**
- Create: `skills/orc-test/scripts/orc_test/langs/gdscript.py`, `skills/orc-test/languages/gdscript.md`
- Modify: `langs/__init__.py` (append `gdscript`), `hooks/scripts/tests/test_orc_test_languages.py` (`"gdscript"`)
- Test: `skills/orc-test/scripts/tests/test_lang_gdscript.py`

- [ ] **Step 1: Write the failing tests**

```python
# skills/orc-test/scripts/tests/test_lang_gdscript.py
from orc_test.langs import gdscript as gd


def test_gdunit4_runner_and_exit_codes(tmp_path, monkeypatch):
    (tmp_path / "project.godot").write_text("")
    (tmp_path / "addons" / "gdUnit4").mkdir(parents=True)
    (tmp_path / "addons" / "gdUnit4" / "runtest.sh").write_text("")
    monkeypatch.setenv("GODOT_BIN", "/opt/godot")
    assert gd.test_cmd(tmp_path, None) == ["./addons/gdUnit4/runtest.sh", "-a", "test"]
    assert gd.test_cmd(tmp_path, "test/player") == ["./addons/gdUnit4/runtest.sh", "-a", "test/player"]
    assert gd.missing(tmp_path) == []
    monkeypatch.delenv("GODOT_BIN")
    assert gd.missing(tmp_path) == ["GODOT_BIN"]


def test_no_gdunit4_is_a_missing_tool(tmp_path, monkeypatch):
    (tmp_path / "project.godot").write_text("")
    monkeypatch.setenv("GODOT_BIN", "/opt/godot")
    assert gd.missing(tmp_path) == ["gdUnit4"]


def test_mutation_is_never_available(tmp_path):
    assert "no mutation tool exists for GDScript" in gd.mutation_unavailable(tmp_path)


def test_coverage_needs_nano_coverage_and_reads_its_lcov(tmp_path):
    (tmp_path / "project.godot").write_text("")
    assert "nano-coverage" in gd.coverage_unavailable(tmp_path)
    (tmp_path / "addons" / "nano_coverage").mkdir(parents=True)
    assert gd.coverage_unavailable(tmp_path) is None
    (tmp_path / "lcov.info").write_text("SF:res://player.gd\nDA:1,1\nDA:2,0\nend_of_record\n")
    assert gd.coverage_parse(tmp_path, tmp_path).files == {"res://player.gd": (1, 2)}


def test_gdlint_parse(tmp_path, monkeypatch):
    out = "test/test_player.gd:12: Error: Function name 'testJump' is not valid (function-name)\n"
    monkeypatch.setattr(gd, "run", lambda cmd, cwd: type("R", (), {"stdout": out, "returncode": 1})())
    monkeypatch.setattr(gd.shutil, "which", lambda n: "/usr/bin/gdlint")
    assert [(f.file, f.line) for f in gd.lint(tmp_path, None, tmp_path)] == [("test/test_player.gd", 12)]
```

- [ ] **Step 2: Run to verify they fail** — `ImportError`.

- [ ] **Step 3: Write the module.** This language adds one contract member, `coverage_unavailable(root) -> str | None`, because its coverage tool is alpha and may be absent; `cli._coverage` must call it when present (`getattr(mod, "coverage_unavailable", lambda r: None)(root)`) and print `"<LABEL>: coverage not measurable — <reason>"` instead of running — add that check and a test in `test_cli_coverage.py` with a fake module.

```python
# skills/orc-test/scripts/orc_test/langs/gdscript.py
"""GDScript (Godot 4): gdUnit4's CLI runner; nano-coverage (alpha) for lcov; no mutation tool."""

import os
import pathlib
import re
import shutil

from .. import lcov
from ..model import Finding
from ..runner import run

KEY = "gdscript"
LABEL = "GDScript"
MARKERS = ["project.godot"]
TOOLS = {"gdUnit4": "install the gdUnit4 addon (Godot Asset Library) — it ships addons/gdUnit4/runtest.sh",
         "GODOT_BIN": "export GODOT_BIN=/path/to/godot (the 4.x binary gdUnit4 should run)"}
CAVEATS = ["gdUnit4 exits 100 on test failures and 101 on warnings.",
           "nano-coverage is alpha and built from source; its lcov lands at the project root."]
_GDLINT = re.compile(r"^(?P<file>[^:]+):(?P<line>\d+): (?P<msg>.*)$", re.M)


def _runner(root):
    return pathlib.Path(root) / "addons" / "gdUnit4" / "runtest.sh"


def missing(root):
    if not _runner(root).exists():
        return ["gdUnit4"]
    return [] if os.environ.get("GODOT_BIN") else ["GODOT_BIN"]


def test_cmd(root, target):
    return ["./addons/gdUnit4/runtest.sh", "-a", target or "test"]


def coverage_unavailable(root):
    if not (pathlib.Path(root) / "addons" / "nano_coverage").exists():
        return "nano-coverage addon not installed (github.com/IgorBayerl/nano-coverage-godot, alpha, build from source)"
    return None


def coverage_cmd(root, target, out):
    # nano-coverage hooks gdUnit4's session and writes lcov.info at the project root
    return test_cmd(root, target)


def coverage_parse(root, out):
    return lcov.parse(pathlib.Path(root) / "lcov.info")


def mutation_unavailable(root):
    return "no mutation tool exists for GDScript (checked 2026-09-11)"


def mutation_cmd(root, target, out):
    raise NotImplementedError


def mutation_parse(root, out):
    raise NotImplementedError


def lint(root, target, out):
    if shutil.which("gdlint") is None:
        return "gdlint not installed — pip install gdtoolkit"
    cp = run(["gdlint", target or "test"], cwd=root)
    return [Finding(m["file"], int(m["line"]), m["msg"]) for m in _GDLINT.finditer(cp.stdout)]
```

Append `gdscript` to `langs/__init__.py`. In `cli._run_tests`, treat gdUnit4's exit 100/101 as failure — they are non-zero, so nothing changes; note it in the SKILL.md.

- [ ] **Step 4: Write `languages/gdscript.md`** — researched 2026-09-11: gdUnit4 6.2.1 (`addons/gdUnit4/runtest.sh -a <dir>`, `GODOT_BIN` env, JUnit XML at `reports/results.xml`, exit 0/100/101) or GUT 9.6.1 (not wired — a `.orclab/test.yaml` `test:` override runs it); coverage nano-coverage (alpha, build from source, gdUnit4 session hooks, `lcov.info` at project root; **no threshold — `run.py` gates**); **mutation: none exists**; lint gdlint (gdtoolkit 4.5.0, `pip install gdtoolkit`) — style rules only, no assertion-free rule. Caveats as above. Add `"gdscript"` to `EXPECTED`.

- [ ] **Step 5: Run both suites** — package: 68 passed; hooks: 8 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-test hooks/scripts/tests/test_orc_test_languages.py
git commit -m "orc-test: GDScript — gdUnit4 runner, nano-coverage lcov, TCE honestly not measurable

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---
### Task 17: `SKILL.md` final — `generate`, the hand-off, the loop rule, deletions, errors

**Files:**
- Modify: `skills/orc-test/SKILL.md` (append to the v1 from Task 6)
- Test: `hooks/scripts/tests/test_orc_test_skill.py`

- [ ] **Step 1: Write the failing test**

```python
# hooks/scripts/tests/test_orc_test_skill.py
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills" / "orc-test" / "SKILL.md").read_text()


def test_frontmatter_is_default_invocable():
    fm = re.match(r"---\n(.*?)\n---\n", TEXT, re.S).group(1)
    assert "name: orc-test" in fm and "disable-model-invocation" not in fm
    assert "allowed-tools: Bash(python3 *)" in fm


def test_every_rule_the_spec_names_is_stated():
    for phrase in ["## generate", "analyze.json", "Nothing is deleted until", "Another round?",
                   "never starts a third round", "**offers**", "does not start it",
                   "test-discipline", "uncommitted", "## When something goes wrong",
                   "## Deferred", "ci"]:
        assert phrase in TEXT, phrase
```

- [ ] **Step 2: Run to verify it fails** — the `generate` phrases are absent.

- [ ] **Step 3: Append to `SKILL.md`**

```markdown
## `run` — does the code work?

`python3 ${CLAUDE_SKILL_DIR}/scripts/run.py run [path]`. One line per language: ✓/✗, counts,
seconds. Exit 1 on any failure. `/orc-git merge` calls this before and after landing a branch.

## `coverage` — how much do the tests exercise?

`... coverage [path]`. Per language: percent, lines, ✓ or ✗ against 80 (or `.orclab/test.yaml`),
then every file under the threshold, worst first — that list is where to go next. The tool's own
HTML report path is printed; per-line detail lives there, not in the summary.

## `analyze` — would the tests notice a defect?

`... analyze [path] [--no-mutation]`. Includes `coverage`. Then mutation testing: the tool plants
one defect at a time (a `<` becomes `<=`, a branch is deleted, a call is removed) and re-runs the
suite; a mutant the suite does not catch *survived*. The share caught is the mutation score —
Test Case Effectiveness, TCE — gated at 70. Then a lint over the test files for the four smells:
no assertion, `sleep`, skipped, duplicate name.

Read it like this:

```
Python     coverage 84.0% (420/500 lines) ✓
           TCE 61.0% ✗ (min 70)    lint: 3 findings
    survived  src/billing.py:42  if x <= limit:
    lint      tests/test_api.py:88  no assertion in test_status
JS/TS      coverage 71.0% (…) ✗ (min 80)
    64.0%  src/cart.js
           TCE 78.0% ✓    lint: 0 findings
GDScript   coverage 92.0% (…) ✓
           TCE not measurable — no mutation tool exists for GDScript (checked 2026-09-11)
```

Every surviving mutant is a concrete defect no test caught, with its file, line and what changed.
That list is the most valuable thing this command produces.

**Before a whole-project run it says how many files it is about to mutate** and that a first
run takes a while (later runs are incremental where the tool supports it). It does not ask —
you typed the command. Give it a path to narrow it. `--no-mutation` skips the slow step and the
report says `TCE skipped` rather than showing a number that is not one.

**When it cannot measure something it says so in words** — no mutation tool for the language,
the tool not installed (with the install line), Kotlin without an open-source licence, a tests
run that was red. It never prints 0% for "did not measure".

**Hand-off.** If any gate failed, the last line is
`gates failed: … — run /orc-test generate to repair`. `analyze` **offers** `generate`; it
**does not start it**. `generate` writes and deletes tests, so it runs on the user's yes — or on
the user typing it — never on a threshold. The one exception is when `generate` itself called
`analyze` to measure its own work; then the loop rule below applies.

The result is saved to `.orclab/test/analyze.json` for `generate`.

## `generate` — repair what `analyze` found

This is the one subcommand with no `run.py` code behind it. Writing tests is Claude's work, under
`test-discipline` (the background skill — read it now if you have not this session). `run.py`
feeds the list and measures the result.

**Where it starts.** `.orclab/test/analyze.json` for the same path. If it is missing, or any file
under the path changed after it was written, run `analyze` first. Never guess what is weak.

**Work, in this order:**

1. **Surviving mutants first.** Each one says: "at this file and line, this change went
   unnoticed." Write the test that goes red on exactly that change. `test-discipline` rule 5
   ("prove the test can fail") is free here — the mutant *is* the planted defect; re-run
   `analyze <that file>` and confirm it is now killed.
2. **Uncovered code next**, worst file first from the coverage list. Realistic data, mocks for
   anything that leaves the process, per the discipline.
3. **Lint findings last.** Give an assertion-free test an assertion. If it genuinely tests
   nothing, it goes on the deletion list.

**Deleting tests.** Anything `generate` wants to remove — assertion-free, duplicate, testing code
that no longer exists, permanently skipped — goes on a list shown to the user first:

```
Proposed deletions:
  tests/test_api.py::test_status      no assertion; the endpoint it named was removed in v3
  tests/test_old_import.py::test_x    duplicate of tests/test_import.py::test_x
Delete these? (strike any you want kept)
```

**Nothing is deleted until the user says yes to that list.** Items can be struck off.

**When done writing:** `run` (everything must still be green), then `analyze` again and show
before → after for every number. That is the second `analyze` of the cycle. If a gate still
fails, ask — `"Coverage 76% (was 61%), TCE 68% (was 44%). Another round?"` — and wait. It
**never starts a third round** on its own.

**Everything it writes is uncommitted.** Committing is the user's step, so they can read the
new tests first. `/orc-git commit` is the way.

## When something goes wrong

One rule: say what, show the command, stop that language, continue the others.

- Tool missing → its name and install line, language skipped. Nothing is installed.
- Tests red under `analyze` → "tests failed; nothing measured" for that language.
- Mutation run interrupted → the tool's incremental file keeps what finished; run again.
- A language detected with no tests → `0 tests`, `0.0%` — an empty suite is a finding, not a
  pass.
- Wrong detection → override the command in `.orclab/test.yaml`; the `detected:` line always
  shows what it saw.
- gdUnit4 exits 100 (failures) / 101 (warnings); both are failures here.

## Deferred, by name

- `ci` — writes a GitHub Actions workflow that runs `run` and `coverage` on every push, so the
  gate holds when nobody is running Orclab. Never mutation (too slow per push), never `generate`
  (nothing that rewrites tests runs unattended). Not built until the four subcommands settle.
- Kotlin via Arcmutate, Dart's `mutation_test`, Swift's Muter: spec'd from research, corrected on
  first real use — each `languages/<lang>.md` carries a "Last real run" line.
- GDScript mutation: no tool exists (BACKLOG entry). `languages/gdscript.md` gets a row if one
  appears.
```

- [ ] **Step 4: Run** — `cd hooks/scripts && python3 -m pytest tests/test_orc_test_skill.py -v` → 2 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-test/SKILL.md hooks/scripts/tests/test_orc_test_skill.py
git commit -m "orc-test: generate, the analyze hand-off, the two-round rule, deletions by consent

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 18: Integration — merge calls `/orc-test`, stack skills link, backlog and verification entries, plugin description

**Files:**
- Modify: `skills/orc-git/SKILL.md` (merge step 3 and 5), `skills/stack-ios-native/SKILL.md`, `skills/stack-android-native/SKILL.md`, `skills/stack-flutter/SKILL.md`, `skills/stack-unity/SKILL.md`, `skills/stack-godot/SKILL.md`, `.claude-plugin/plugin.json`, `BACKLOG.md` (via `/orc-todo`), `VERIFICATION.md` (via `/orc-todo`)
- Test: existing `hooks/scripts/tests/` stay green; `skills/orc-git` has no script tests — verify by reading.

- [ ] **Step 1: `/orc-git merge` step 3** — replace the Python loop and the "for any other project" prose with:

```markdown
3. **Run the project's test suites on the branch as it stands, before merging** — with
   `/orc-test`:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/orc-test/scripts/run.py" --cwd <path to the branch's tree> run
   ```
   `/orc-test` finds every language in the project and each one's own test command
   (`skills/orc-test/SKILL.md`), so this step no longer carries a per-project loop. Run it
   against the branch's tree — check it out in its worktree if it has one (`git worktree list`),
   otherwise `git stash` is *not* the tool (the tree is clean by step 1); use `git worktree add`
   to a temporary path and remove it as soon as the run finishes, whichever way it went — a
   leftover temporary worktree blocks `git switch <branch>`, which is the next thing a user does
   after a failing suite. If `/orc-test` exits non-zero, report the failure and stop. Nothing
   has been merged.
```

Step 5's "Run the same suites" becomes "Run `/orc-test` again on the merged result", same rule.

- [ ] **Step 2: Stack skills' Testing rows** — in each of the five, add one sentence to the row (or the "Build, run, test" section) pointing at the language file: `stack-ios-native` → `skills/orc-test/languages/swift.md`; `stack-android-native` → `kotlin.md`; `stack-flutter` → `dart.md`; `stack-unity` → `csharp.md`; `stack-godot` → `gdscript.md`. Form: *"Coverage, mutation testing and test lint for this language: `skills/orc-test/languages/<lang>.md` — `/orc-test` reads it."* Do not restate any tool version there.

- [ ] **Step 3: `plugin.json` description** — append one sentence: *"/orc-test runs every test suite in a project across its languages, holds coverage to 80% and mutation score to 70%, and repairs weak suites; test-discipline is the background rule set every test is written under."* Then `claude plugin validate .claude-plugin/plugin.json` — expect `✔ Validation passed with warnings` with the one known CLAUDE.md warning (per CLAUDE.md, this proves manifest structure only, not frontmatter).

- [ ] **Step 4: BACKLOG, through the shipped command** (the number is allocated; do not hand-write it):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/orc-todo/scripts/run.py" add backlog "GDScript has no mutation-testing tool, so /orc-test cannot measure TCE for Godot projects" <<'EOF'
Found researching v17 (2026-09-11): Python, JS/TS, Java, Kotlin, C#, Dart and Swift each have at
least one mutation tool; GDScript has none — searched GitHub, the Godot Asset Library and the
awesome-mutation-testing list. `/orc-test analyze` therefore reports "TCE not measurable — no
mutation tool exists for GDScript" in words rather than a number (spec: never a fake number).

What would close it: any tool that mutates `.gd` files and re-runs gdUnit4 or GUT. When one
appears, `skills/orc-test/languages/gdscript.md` gets a Mutation row, `langs/gdscript.py`'s
`mutation_unavailable` returns None when it is installed, and this entry is resolved. Until then,
`test-discipline` rule 5 (break the code by hand once, watch the test go red) is the only TCE a
Godot project gets, and `/orc-test` says so.
EOF
```

And a note on **#4** (read it first with `... show 4`; append by editing the entry's body, not its heading): *"2026-09-11, v17: a new stack skill's Testing row links to `skills/orc-test/languages/<lang>.md` rather than restating tools — that is where `/orc-test` reads them from."*

- [ ] **Step 5: VERIFICATION scenarios, through the shipped command** — three scenarios, each via `... add verification "<title>"` with the body on stdin:

1. *"/orc-test run on Orclab reads right"* — steps: run `python3 skills/orc-test/scripts/run.py run` at the repo root; expected: first line `detected: Python`, the printed `$ python3 -m pytest -q --ignore=mutants` line, one summary line with ✓ and a passed count; then create a failing test file, run again, expected ✗, the failure tail, exit 1; delete the file.
2. *"/orc-test analyze on Orclab: the summary reads as an operator would read it"* — run `analyze` on `skills/orc-todo/scripts`; expected: coverage block with files under 80 listed worst first; a TCE line that is either a percentage with ✓/✗ or the words `TCE not measurable — mutmut not installed — pip install mutmut`; lint count; `gates failed: … — run /orc-test generate` if any failed; `.orclab/test/analyze.json` exists. The judgement asked for: could you act on this without opening any other file?
3. *"/orc-test on a language with a missing tool is a sentence, not a crash"* — in a scratch git repo with an empty `package.json` and no `node_modules`, run `run`; expected: `detected: JS/TS`, then either the npx test attempt's failure tail or `JS/TS: missing npx — … — skipped`, exit code 0 when skipped, and nothing installed.

- [ ] **Step 6: Run every suite** — `for d in skills/*/scripts hooks/scripts; do [ -d "$d/tests" ] && (cd "$d" && python3 -m pytest tests/ -q); done` — all green.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "orc-test lands in the rest of Orclab: merge calls it, stack skills link to languages/, backlog and verification entries

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 19: First real run — `/orc-test analyze` on Orclab itself

**Files:**
- Modify: `skills/orc-test/languages/python.md` ("Last real run" line), possibly `langs/python.py` and `.gitignore` (add `mutants/` and `.orclab/test/`), `BACKLOG.md` if something is found

This is the VERIFICATION scenario 2 above, run for real, plus the mutation tools' first contact with a real suite. Orclab has never had a TCE score.

- [ ] **Step 1: Install the two tools into the environment Orclab's suites already run in** — `pip install pytest-cov mutmut` (or into `skills/orc-publish/scripts/venv` if that is what runs the suites; check `which python3` and how `/orc-git merge` step 3 runs them — the same interpreter).

- [ ] **Step 2: Give Orclab a `[tool.mutmut]` section.** Orclab has no root `pyproject.toml`; create one containing only:

```toml
[tool.mutmut]
paths_to_mutate = ["skills/orc-todo/scripts/orc_todo/"]
tests_dir = ["skills/orc-todo/scripts/tests/"]

[tool.pytest.ini_options]
testpaths = ["skills", "hooks"]
norecursedirs = ["mutants", "venv", ".orclab"]
```

`orc-todo` is the target because it is the newest suite and the one whose spec named "the tests that matter most". Add `mutants/` and `.orclab/test/` to `.gitignore`.

- [ ] **Step 3: Run it**

```bash
python3 skills/orc-test/scripts/run.py analyze skills/orc-todo/scripts
```

Expected: the summary block. Record the three numbers. If mutmut reports every mutant as `no tests`, the import path is the cause (see `languages/python.md` Caveats) — fix `pythonpath` in `[tool.pytest.ini_options]` and rerun; that fix is the first thing `Last real run` records.

- [ ] **Step 4: Write it down** — in `languages/python.md`, replace the `Last real run: none yet` line with the date, the command, the three numbers, and whatever had to change to get there. If the survivors list reveals a real weakness in `orc-todo`'s tests, that is a BACKLOG entry (via `/orc-todo add`), not a fix in this task — `generate` is the tool for it, and its first real use should be a session of its own.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "orc-test: first real run on Orclab — orc-todo's suite gets its first TCE score

<the three numbers, and what had to change>

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-review against the spec (done while writing; recorded so the reviewer can check it)

- **Spec coverage.** `test-discipline` six rules → Task 1. Detection table → Task 3 (+ Kotlin claim, Task 12). `run` → Task 6. `coverage` gate from the report file, per-file worst first, HTML path → Task 7. `analyze` order (tests → coverage → mutation → lint), size announcement, `--no-mutation`, words-not-numbers, offer-not-start → Task 8 + Task 17. `generate` priority order, deletion consent, two rounds then ask, uncommitted → Task 17. Eight `languages/*.md` with dated research → Tasks 9–16. Licence gate for Kotlin → Task 12. `.orclab/test.yaml` → Task 3. Error handling → Tasks 6/8/17. `/orc-git merge` change, stack links, BACKLOG #4 note, GDScript entry, VERIFICATION scenarios, `plugin.json` → Task 18. First real run on Orclab → Task 19. `ci` deferred → Task 17 prose.
- **Placeholders.** None: every step has its code or its exact text. The `languages/*.md` bodies for Tasks 10–16 are given as content lists rather than verbatim markdown; each must carry the same eight sections `python.md` shows and the test in Task 9 enforces it.
- **Type consistency.** `mutation_unavailable(root)` (function) everywhere after the Task-5 patch; `lint()` may return `str`; `CAVEATS_FOR(root)` is Kotlin-only and `cli` uses `hasattr`; `coverage_unavailable(root)` is GDScript-only and `cli._coverage` uses `getattr` with a default. `stryker.parse(path, root)`, `pitest.parse(path)`, `jacoco.parse(path)`, `lcov.parse(path)` — the two-argument one is Stryker only, matching its tests.
- **Counts.** The "N passed" totals in Steps are cumulative estimates; a reviewer should trust the suite, not the number.
