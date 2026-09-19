# Orclab v22: `security-discipline` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every project Orclab touches carries a small, sourced set of security rules; a project strangers can reach carries a second set; `/orc-code` asks which at scaffold, every stack skill says where the rules land, and `/orc-test audit` gates a push on a dependency audit.

**Architecture:** A background skill (`security-discipline`) mirrors `code-discipline`: rules in prose with sources, a `## Security — where security-discipline lands` section in each of the nine `stack-*` skills, and enforcement that rides what exists — `lint_on_write` for the linter rules, the v21 `/orc-git` gate for a new `/orc-test audit` subcommand, and `code-modernization:modernize-harden` wrapped for refactors. The only new code is `audit` in `/orc-test`'s Python package: one subcommand in `cli.py`, four members on each language module.

**Tech Stack:** Markdown skills; Python 3.12 / pytest for `/orc-test` and the pinning tests (run from the repo root, whose `pyproject.toml` sets `testpaths` and `pythonpath`); live research via WebFetch against primary sources.

**Spec:** `docs/superpowers/specs/2026-09-19-orclab-v22-security-discipline-design.md`. Read it first; every task below names the section it rests on.

## Global Constraints

- **Nothing is written from memory.** Every tool name, version, flag, rule number and platform fact in a skill carries a "confirmed live YYYY-MM-DD" stamp and a URL in that skill's `## Sources`; a tool candidate the research cannot confirm is dropped, not softened (`currency-discipline`; spec §1, §2).
- **Rule count in `security-discipline` is single digits** (spec §1). Two tiers, named **Every project** and **Reachable by strangers**, every rule tagged with one.
- **Every stack section says "no project has been through this yet"** until one has (spec §2). Where a language has no free security linter or no audit tool, the section says **"none free"** in those words (spec §2).
- **`/orc-test` never installs a tool**: a missing audit tool is `missing <tool> — <install line> — skipped`, the existing wording in `cli.py::_resolve` (spec §3).
- **No skip flag on any `/orc-git` subcommand**; `hooks/scripts/tests/test_orc_git_skill.py::test_no_subcommand_offers_a_way_to_skip_the_gate` enforces it (spec §3).
- **`lint_on_write` is not modified** (spec §3).
- **Docs pages change in the same commit as the skill they describe** (`CLAUDE.md` checklist item 7) and keep exactly their five `##` headings in order (`hooks/scripts/tests/test_docs.py`).
- The heading text is exactly `## Security — where security-discipline lands` (em dash, as the Lint heading has).
- Tests run from the repo root: `cd /home/direflail/projects/orclab && python3 -m pytest -q <path>`. The whole suite is `python3 -m pytest -q`.
- Commit messages end with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- Write skills for the reader who has not been in this session (`CLAUDE.md`, "explain it again from the reader's side"): what happens and what they see first; tool names after.
- Work in a worktree branched from `origin/main` (direflail's standing preference); `main` must be pushed first — the plan's commit is on `main` and not yet on `origin`.

## File structure

| File | Responsibility | Task |
|---|---|---|
| `skills/orc-test/scripts/orc_test/cli.py` | `cmd_audit`, registered as the `audit` subcommand | 1 |
| `skills/orc-test/scripts/orc_test/langs/python.py` | `AUDIT_TOOL`, `audit_unavailable`, `audit_cmd`, `audit_findings` for pip-audit | 1 |
| `skills/orc-test/scripts/tests/test_cli_audit.py` (create), `test_lang_python.py` | The subcommand's three outcomes with the fake module; pip-audit's JSON parse from a captured fixture | 1 |
| `skills/orc-test/scripts/tests/fixtures/pip_audit.json` + `.README` (create) | Captured pip-audit output, and how it was captured | 1 |
| `skills/orc-test/languages/python.md`, `skills/orc-test/SKILL.md`, `docs/commands/orc-test.md` | `## Audit` on the page; `audit` in the subcommand table and the page's "What you type" | 1 |
| `skills/orc-test/scripts/orc_test/langs/{javascript,java,kotlin,csharp,dart,swift,gdscript}.py` + `languages/<lang>.md` + `tests/test_lang_<lang>.py` | Each language's audit members, from live research; `AUDIT_TOOL = None` + `AUDIT_NONE` where none free | 2 |
| `hooks/scripts/tests/test_orc_test_languages.py` | `## Audit` joins `REQUIRED` | 2 |
| `skills/security-discipline/SKILL.md` (create) | The skill, spec §1 | 3 |
| `hooks/scripts/tests/test_security_discipline.py` (create) | Frontmatter, two tiers, rule ceiling, "What this is not", and — parametrised over `EXPECTED` — the Security section in each stack skill | 3, then 4–8 add names |
| `skills/stack-python-desktop/SKILL.md`, `skills/stack-web/SKILL.md` | Security sections: Python and JS/TS | 4 |
| `skills/stack-android-native/SKILL.md`, `skills/stack-kotlin-multiplatform/SKILL.md` | Security sections: Kotlin/JVM, Android secrets | 5 |
| `skills/stack-ios-native/SKILL.md` | Security section: Swift, Keychain | 6 |
| `skills/stack-flutter/SKILL.md`, `skills/stack-react-native/SKILL.md` | Security sections: Dart/pub, RN/npm, secure storage on both platforms | 7 |
| `skills/stack-godot/SKILL.md`, `skills/stack-unity/SKILL.md` | Security sections: GDScript, Unity C# | 8 |
| `skills/orc-code/SKILL.md`, `docs/commands/orc-code.md`, `hooks/scripts/tests/test_orc_code_skill.py` | The exposure question, scaffold's security config and exposed-tier pieces, quality mode's `modernize-harden` wrap | 9 |
| `skills/test-discipline/SKILL.md` | One line in rule 1's scenario list | 9 |
| `skills/orc-git/SKILL.md`, `docs/commands/orc-git.md`, `hooks/scripts/tests/test_orc_git_skill.py` | `audit` beside `coverage` and `analyze` in the gate | 10 |
| `BACKLOG.md` | This entry; the deferred secret-scan-hook entry; the v23 pointer | 11 |

Order matters twice: Task 1 defines the module interface Task 2 fills in; Task 3 defines the section shape Tasks 4–8 write. Tasks 4–8 are independent of each other and may run in parallel worktrees if the executor supports it. Tasks 9 and 10 need Task 3's skill to exist by name; Task 10 needs Task 1's `audit`.

---

### Task 1: `/orc-test audit` — the subcommand, and Python through pip-audit

**Files:**
- Modify: `skills/orc-test/scripts/orc_test/cli.py` (new `cmd_audit`; `main`'s subcommand tuple)
- Modify: `skills/orc-test/scripts/orc_test/langs/python.py`
- Create: `skills/orc-test/scripts/tests/test_cli_audit.py`
- Modify: `skills/orc-test/scripts/tests/test_lang_python.py`
- Create: `skills/orc-test/scripts/tests/fixtures/pip_audit.json`, `pip_audit.json.README`
- Modify: `skills/orc-test/scripts/tests/helpers.py` (the `fake()` module gains audit members)
- Modify: `skills/orc-test/languages/python.md`, `skills/orc-test/SKILL.md`, `docs/commands/orc-test.md`

**Interfaces:**
- Produces, on every language module (Task 2 fills the other seven):
  - `AUDIT_TOOL: tuple[str, str] | None` — `(what audit_unavailable checks for, install line)`; `None` means no free tool exists for this language, and then `AUDIT_NONE: str` says why.
  - `audit_unavailable(root) -> str | None` — the `missing … — skipped` reason when the tool is not installed, else `None`.
  - `audit_cmd(root) -> list[str]` — the command, run from the language's marker directory.
  - `audit_findings(stdout: str, returncode: int) -> list[str]` — one line per vulnerable dependency, `"<name> <version>: <ids> — fix <versions>"`; `[]` is clean. Raises nothing: unparseable output is `["audit output not understood — see above"]` and the caller prints the tail.
- Produces: the `audit` subcommand's report lines, which Task 10's gate wording quotes:
  - `Python     audit ✓ 0 vulnerable` / `Python     audit ✗ 2 vulnerable` followed by one indented line per finding
  - `Python     audit not available — <AUDIT_NONE>`
  - `Python: missing pip-audit — pip install pip-audit — skipped` (printed by the subcommand, same shape as `_resolve`'s)
  - exit 1 iff any language printed ✗.

- [ ] **Step 1: Extend the fake module in `helpers.py`**

In `fake()`'s `types.SimpleNamespace(...)`, add these members (keyword arguments to `fake` with defaults so every existing call is unchanged):

```python
def fake(mutation=None, unavailable=None, cov=(9, 10), lint=None, test_cmd=None, coverage_unavailable=None,
         audit_tool=("faketool", "install faketool"), audit_unavailable=None, audit_findings=None):
    m = types.SimpleNamespace(
        ...existing members...,
        AUDIT_TOOL=audit_tool, AUDIT_NONE="no free audit tool for Fake",
        audit_unavailable=lambda root: audit_unavailable,
        audit_cmd=lambda root: ["true"],
        audit_findings=lambda stdout, rc: audit_findings if audit_findings is not None else [])
    return m
```

- [ ] **Step 2: Write the subcommand tests, red**

Create `skills/orc-test/scripts/tests/test_cli_audit.py`:

```python
"""`/orc-test audit` (spec 2026-09-19-orclab-v22-security-discipline-design.md §3): one line per
language, ✓/✗ on vulnerable dependencies, never installs, 'not available' where no free tool exists."""

from orc_test import langs
from tests.helpers import fake, make_repo, run


def _with(monkeypatch, m):
    monkeypatch.setattr(langs, "ALL", [m])


def test_clean_audit_is_a_tick_and_exit_zero(tmp_path, capsys, monkeypatch):
    _with(monkeypatch, fake())
    code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert code == 0 and "Fake       audit ✓ 0 vulnerable" in out


def test_findings_are_a_cross_listed_and_exit_one(tmp_path, capsys, monkeypatch):
    _with(monkeypatch, fake(audit_findings=["requests 2.19.0: CVE-2018-18074 — fix 2.20.0",
                                             "urllib3 1.24: CVE-2019-11324 — fix 1.24.2"]))
    code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert code == 1 and "Fake       audit ✗ 2 vulnerable" in out
    assert "    requests 2.19.0: CVE-2018-18074 — fix 2.20.0" in out


def test_missing_tool_is_named_with_its_install_line_and_skipped(tmp_path, capsys, monkeypatch):
    _with(monkeypatch, fake(audit_unavailable="faketool not installed"))
    code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert code == 0 and "Fake: missing faketool — install faketool — skipped" in out
    assert "✓" not in out and "✗" not in out


def test_language_with_no_free_tool_says_so_and_is_not_a_failure(tmp_path, capsys, monkeypatch):
    _with(monkeypatch, fake(audit_tool=None))
    code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert code == 0 and "Fake       audit not available — no free audit tool for Fake" in out


def test_no_language_prints_nothing_audited(tmp_path, capsys, monkeypatch):
    m = fake()
    m.MARKERS = ["no-such-marker.xyz"]
    _with(monkeypatch, m)
    code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert code == 0 and "nothing audited" in out


def test_audit_prints_the_command_it_ran(tmp_path, capsys, monkeypatch):
    _with(monkeypatch, fake())
    _code, out = run(["audit"], make_repo(tmp_path), capsys)
    assert "$ true" in out
```

- [ ] **Step 3: Run them red**

Run: `cd /home/direflail/projects/orclab && python3 -m pytest -q skills/orc-test/scripts/tests/test_cli_audit.py`
Expected: every test fails — argparse rejects `audit` (`invalid choice`), exit code 2 propagates as `SystemExit`.

- [ ] **Step 4: Implement `cmd_audit` in `cli.py`**

Add after `cmd_coverage`:

```python
def _audit_line(mod, d):
    """One language's audit line (plus indented findings), and whether it failed the gate."""
    if getattr(mod, "AUDIT_TOOL", None) is None:
        return f"{mod.LABEL:<10} audit not available — {mod.AUDIT_NONE}", False
    why = mod.audit_unavailable(d)
    if why:
        tool, install = mod.AUDIT_TOOL
        return f"{mod.LABEL}: missing {tool} — {install} — skipped", False
    cp = run(mod.audit_cmd(d), cwd=d)
    findings = mod.audit_findings(cp.stdout, cp.returncode)
    if findings == ["audit output not understood — see above"]:
        print(cp.stdout[-3000:])
    mark = "✗" if findings else "✓"
    lines = [f"{mod.LABEL:<10} audit {mark} {len(findings)} vulnerable"] + [f"    {f}" for f in findings]
    return "\n".join(lines), bool(findings)


def cmd_audit(args):
    _root, _cfg, usable = _resolve(args)
    failed, blocks = False, []
    for m, d, _target in usable:
        block, bad = _audit_line(m, d)
        failed |= bad
        blocks.append(block)
    print("\n" + "\n".join(blocks) if blocks else "nothing audited")
    return 1 if failed else 0
```

In `main`, extend the tuple: `("coverage", cmd_coverage), ("audit", cmd_audit), ("analyze", cmd_analyze)`.

- [ ] **Step 5: Run the subcommand tests green, then the whole orc-test suite**

Run: `python3 -m pytest -q skills/orc-test/scripts/tests/test_cli_audit.py` → 6 passed.
Run: `python3 -m pytest -q skills/orc-test/scripts/tests` → all green (the fake gained members; nothing else changed).

- [ ] **Step 6: Capture a real pip-audit fixture**

pip-audit's README (raw.githubusercontent.com/pypa/pip-audit/main/README.md, read 2026-09-19) documents: a positional `project_path` audits *"a local Python project at the given path"* (reads `pyproject.toml`); `-r` audits a requirements file; no argument audits the environment; exit `0` clean, `1` *"One or more known vulnerabilities were found"*, and *"pip-audit's exit code cannot be suppressed"*; `-f json`. Capture the JSON shape from a real run in a scratch venv — not hand-built:

```bash
cd /tmp/claude-1000/-home-direflail-projects-orclab/*/scratchpad && python3 -m venv pa && . pa/bin/activate
pip install -q pip-audit
printf 'requests==2.19.0\n' > req.txt
pip-audit -r req.txt -f json --no-deps > pip_audit.json; echo "exit $?"
python3 -c "import json;d=json.load(open('pip_audit.json'));print(type(d).__name__, list(d)[:3] if isinstance(d,dict) else d[0].keys())"
pip-audit --version
```

Copy `pip_audit.json` to `skills/orc-test/scripts/tests/fixtures/pip_audit.json`. Write `pip_audit.json.README` beside it: the pip-audit version printed, the date, the exact command, that `--no-deps` was used so the file names only the pinned package, and the top-level shape the last command printed (a dict with a `dependencies` list, or a bare list — whichever it is, the parser in Step 8 handles both and the README says which the tool produced).

- [ ] **Step 7: Write the Python module tests, red**

Append to `skills/orc-test/scripts/tests/test_lang_python.py`:

```python
def test_audit_tool_and_command():
    assert python.AUDIT_TOOL == ("pip-audit", "pip install pip-audit")
    assert python.audit_cmd("/x") == ["python3", "-m", "pip_audit", "-f", "json", "--progress-spinner", "off", "."]


def test_audit_findings_from_captured_json():
    text = (FIX / "pip_audit.json").read_text()
    lines = python.audit_findings(text, 1)
    assert len(lines) >= 1
    assert lines[0].startswith("requests 2.19.0: ") and " — fix " in lines[0]


def test_audit_clean_and_unreadable():
    assert python.audit_findings('{"dependencies": [], "fixes": []}', 0) == []
    assert python.audit_findings("Traceback (most recent call last)", 2) == ["audit output not understood — see above"]


def test_audit_unavailable_names_pip_audit(monkeypatch):
    monkeypatch.setattr(python.importlib.util, "find_spec", lambda name: None)
    assert "pip-audit" in python.audit_unavailable("/x")
```

`FIX` and `python` are already imported at the top of that file (check; add `FIX = pathlib.Path(__file__).parent / "fixtures"` if not).

- [ ] **Step 8: Implement the Python audit members**

In `langs/python.py`, after `SANDBOX`:

```python
AUDIT_TOOL = ("pip-audit", "pip install pip-audit")
_UNREADABLE = ["audit output not understood — see above"]


def audit_unavailable(root):
    return None if importlib.util.find_spec("pip_audit") else "pip-audit not installed"


def audit_cmd(root):
    # `.` audits the project's own declared dependencies (pyproject.toml), not whatever happens to
    # be in the environment; README: "audit a local Python project at the given path".
    return ["python3", "-m", "pip_audit", "-f", "json", "--progress-spinner", "off", "."]


def audit_findings(stdout, returncode):
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return _UNREADABLE
    deps = data.get("dependencies", []) if isinstance(data, dict) else data
    out = []
    for dep in deps:
        for v in dep.get("vulns", []):
            ids = ", ".join([v.get("id", "?")] + v.get("aliases", []))
            fix = ", ".join(v.get("fix_versions", [])) or "none published"
            out.append(f"{dep['name']} {dep['version']}: {ids} — fix {fix}")
    return out
```

If Step 6's real output disagrees with a key name here (`vulns`, `fix_versions`, `aliases`, `dependencies`), the code follows the captured file and this step's text is corrected — the fixture is the authority.

- [ ] **Step 9: Run green**

Run: `python3 -m pytest -q skills/orc-test/scripts/tests/test_lang_python.py skills/orc-test/scripts/tests/test_cli_audit.py` → all passed.

- [ ] **Step 10: The page, the skill table, the doc page**

`skills/orc-test/languages/python.md`: add a section `## Audit` between `## Test lint` and `## Caveats`:

```markdown
## Audit
pip-audit <version from Step 6> (`pip install pip-audit`), confirmed live 2026-09-19 against its README:
`python3 -m pip_audit -f json --progress-spinner off .` audits the project's declared dependencies
from `pyproject.toml` — not the environment — and exits 1 when any has a known vulnerability
(*"pip-audit's exit code cannot be suppressed"*). `run.py` reads the JSON: one line per
vulnerable package with its advisory ids and the versions that fix it. First resolution can take
as long as a `pip install`. Last real run: <the line Task 11 records>.
```

`skills/orc-test/SKILL.md`: add a row to the subcommand table after `coverage`:
`| \`audit\` | Do the dependencies carry a known vulnerability? (gate: none) | nothing |`
and one paragraph after the `## coverage` section (or wherever the subcommands are described in order) headed `## audit — are the dependencies known-vulnerable?`:

```markdown
## `audit` — are the dependencies known-vulnerable?

`python3 ${CLAUDE_SKILL_DIR}/scripts/run.py audit`. One line per language: `✓ 0 vulnerable`, or
`✗ N vulnerable` with one indented line per package — name, version, advisory ids, the versions
that fix it. `languages/<lang>.md`'s `## Audit` says which tool each language uses; a language
whose tool is not installed prints `missing <tool> — <install line> — skipped` and is not a
failure; a language with no free audit tool prints `audit not available — <why>` and is not a
failure either. Exit 1 only when a vulnerable dependency was actually found. `/orc-git push`,
`cp` and `release` run it before touching a remote (v22; `security-discipline`'s every-project
rule "dependencies audited").
```

`docs/commands/orc-test.md`, "What you type" table, after the `coverage` row:
`| \`/orc-test audit\` | Checks every dependency the project declares against the public list of known vulnerabilities and names any that are affected, with the version that fixes each |`
And in "What it will never do without asking", the "never install" bullet already covers the audit tool — add ", or the dependency-audit tool" after "mutation tool" in that bullet.

- [ ] **Step 11: Whole suite, then commit**

Run: `cd /home/direflail/projects/orclab && python3 -m pytest -q` → green (the `hooks` docs test sees the page still has five headings).

```bash
git add skills/orc-test docs/commands/orc-test.md
git commit -m "orc-test audit: dependency audit per language — Python through pip-audit, read from a captured fixture (v22 §3)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: The other seven languages' audit — from live research

**Files:**
- Modify: `skills/orc-test/scripts/orc_test/langs/{javascript,java,kotlin,csharp,dart,swift,gdscript}.py`
- Modify: `skills/orc-test/languages/{javascript,java,kotlin,csharp,dart,swift,gdscript}.md` (each gains `## Audit`)
- Modify: `skills/orc-test/scripts/tests/test_lang_{javascript,java,kotlin,csharp,dart,swift,gdscript}.py`
- Create: fixtures + `.README` for each language that has a tool
- Modify: `hooks/scripts/tests/test_orc_test_languages.py` (`"## Audit"` appended to `REQUIRED`)

**Interfaces:**
- Consumes: Task 1's four members and their contract. Every module must have `AUDIT_TOOL`; when it is `None`, `AUDIT_NONE` is required.

- [ ] **Step 1: Make the page test red**

In `hooks/scripts/tests/test_orc_test_languages.py`, append `"## Audit"` to `REQUIRED`. Run: `python3 -m pytest -q hooks/scripts/tests/test_orc_test_languages.py` → 7 fail (python passes from Task 1).

- [ ] **Step 2: Research, one language at a time, primary sources only**

For each, open the tool's own docs (not a blog) and record: the command, whether it reads the project's manifest or a lock file, the exit code on findings, the machine-readable output flag, and the current version. Candidates to *check* — any that does not confirm is dropped:

| Language | Candidate | Where to read |
|---|---|---|
| JavaScript/TypeScript | `npm audit --json` (exit 1 on findings; `npm audit --audit-level`) | docs.npmjs.com/cli/commands/npm-audit |
| Java (Maven) | OWASP Dependency-Check Maven plugin `dependency-check:check`; or a Maven-native option if one now exists | jeremylong.github.io/DependencyCheck, maven.apache.org |
| Kotlin (Gradle) | OWASP Dependency-Check Gradle plugin `dependencyCheckAnalyze` | same |
| C# | `dotnet list package --vulnerable --format json` — check its exit code on findings (it may be 0; then parse) | learn.microsoft.com/dotnet/core/tools/dotnet-list-package |
| Dart/Flutter | `dart pub get` / `dart pub outdated` advisories — pub.dev security advisories exist; check whether any command exits non-zero or prints machine-readable output | dart.dev/tools/pub/security-advisories |
| Swift | none built into SwiftPM as of the last check — confirm on swift.org / GitHub swift-package-manager; if still none: `AUDIT_TOOL = None` | swift.org, github.com/swiftlang/swift-package-manager |
| GDScript | none — Godot addons have no advisory database; `AUDIT_TOOL = None` | godotengine.org/asset-library docs |

- [ ] **Step 3: Per language with a tool — fixture, test, implementation**

Same three moves as Task 1 Steps 6–9, per language: capture the tool's machine-readable output from a real run where the tool is installed on this machine (`npm` is; `dotnet`, `dart`, `mvn`, `gradle` only if present — otherwise hand-build the fixture from the tool's documented schema and say so in its `.README`, the `mutation_test_junit.xml.README` precedent); a test that parses it; `audit_unavailable` via `shutil.which` (or the project's own manifest for a plugin-based tool — a Gradle plugin is "installed" when `build.gradle(.kts)` names it, and the install line is the plugin block to add).

Per language with none: `AUDIT_TOOL = None` and `AUDIT_NONE = "<one sentence: what was checked and when>"`, and a one-line test asserting both.

- [ ] **Step 4: Each language page gets `## Audit`**

Same shape as Python's: tool and version, the command, what it reads, exit code, confirmed-live date, `Last real run: none yet` (Python's says the same until Task 11). For a `None` language the section is the `AUDIT_NONE` sentence plus what was checked.

- [ ] **Step 5: Green, then commit per language or all at once**

Run: `python3 -m pytest -q skills/orc-test/scripts/tests hooks/scripts/tests/test_orc_test_languages.py` → green.

```bash
git add skills/orc-test hooks/scripts/tests/test_orc_test_languages.py
git commit -m "orc-test audit: the other seven languages, from each tool's own docs; Swift and GDScript say 'none free' (v22 §3)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: `security-discipline` — the skill, and the test that defines the stack section

**Files:**
- Create: `skills/security-discipline/SKILL.md`
- Create: `hooks/scripts/tests/test_security_discipline.py`

**Interfaces:**
- Produces: the rule numbers and tier names Tasks 4–8 cite (`security-discipline` rule N) and the section shape they must write; the `EXPECTED` set each of those tasks appends to.

- [ ] **Step 1: Write the pinning test, red**

```python
# hooks/scripts/tests/test_security_discipline.py
"""security-discipline (spec 2026-09-19-orclab-v22-security-discipline-design.md): the skill's
frontmatter and shape, and the Security section every stack skill carries (§2)."""

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "security-discipline" / "SKILL.md"
HEADING = "## Security — where security-discipline lands"
SUBHEADINGS = ["### Static analysis", "### Dependency audit", "### Secrets", "### Reachable by strangers"]
EXPECTED = set()   # each stack task adds its skill's directory name here


def _frontmatter():
    m = re.match(r"---\n(.*?)\n---\n", SKILL.read_text(), re.DOTALL)
    assert m, "SKILL.md must start with YAML frontmatter"
    return dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)


def test_is_background_only():
    fm = _frontmatter()
    assert fm["name"].strip() == "security-discipline"
    assert fm["user-invocable"].strip() == "false"
    assert "disable-model-invocation" not in fm


def test_two_tiers_named_and_every_rule_tagged():
    text = SKILL.read_text()
    rules = re.findall(r"^## (\d+)\. .*$", text, re.MULTILINE)
    assert 1 <= len(rules) <= 9, "single digits (spec §1)"
    assert [int(n) for n in rules] == list(range(1, len(rules) + 1))
    for n in rules:
        body = text.split(f"## {n}. ")[1].split("\n## ")[0]
        assert "*Every project*" in body or "*Reachable by strangers*" in body, f"rule {n} has no tier tag"
    assert "**Every project**" in text and "**Reachable by strangers**" in text


def test_every_rule_names_its_source():
    text = SKILL.read_text()
    assert "## Sources" in text
    assert re.search(r"confirmed live 2026-\d\d-\d\d", text)
    assert "owasp.org" in text and "cwe.mitre.org" in text


def test_what_this_is_not_points_at_secret_hygiene_and_the_stack_sections():
    text = SKILL.read_text()
    tail = text[text.index("## What this is not"):]
    for phrase in ["secret-hygiene", "penetration", "Not enforced by this file", HEADING, "lint_on_write", "/orc-test audit"]:
        assert phrase in tail, phrase


@pytest.mark.parametrize("stack", sorted(EXPECTED))
def test_stack_skill_has_the_security_section(stack):
    text = (ROOT / "skills" / stack / "SKILL.md").read_text()
    assert HEADING in text, stack
    body = text[text.index(HEADING):]
    body = body.split("\n## ", 1)[0]
    for sub in SUBHEADINGS:
        assert sub in body, f"{stack}: {sub}"
    assert "no project has been through this yet" in body, stack
    assert re.search(r"confirmed live 2026-\d\d-\d\d", body), stack


def test_every_stack_skill_is_expected():
    """A stack skill added later must be listed here, so it cannot ship without the section."""
    stacks = {p.parent.name for p in (ROOT / "skills").glob("stack-*/SKILL.md")}
    assert stacks == EXPECTED
```

Run: `python3 -m pytest -q hooks/scripts/tests/test_security_discipline.py` → red (`SKILL.md` missing; `test_every_stack_skill_is_expected` fails until Task 8 — that is deliberate and is the one red the branch carries between Tasks 3 and 8; note it in each commit message).

- [ ] **Step 2: Research the rule set from the primary sources**

Read, on the day, and note the URL and what it says:
1. OWASP Top 10 — `https://owasp.org/Top10/` (the current edition's list page; each category's page).
2. OWASP ASVS — `https://owasp.org/www-project-application-security-verification-standard/` (current major version; chapters on authentication, session, access control, validation, error handling, configuration, secrets).
3. CWE Top 25 — `https://cwe.mitre.org/top25/` (the current year's list).
4. For the *Every project* tier the sources are thinner; check OWASP's Mobile Top 10 and the CWE entries for hardcoded credentials (CWE-798), missing integrity check on downloaded code (CWE-494), and excessive permissions.

Method (BACKLOG #40's): list every candidate; keep only those that map to (a) a linter rule some stack's tooling has, (b) a scaffold piece, or (c) a command (`audit`). Everything else is a review item at most. Aim for 6–9 rules.

- [ ] **Step 3: Write the skill**

Frontmatter, exactly:

```yaml
---
name: security-discipline
description: Background rules for any code Claude is about to write or change, in any language - what every project owes (secrets out of the repo and the artifact, dependencies audited, downloads verified, least permission) and what a project strangers can reach owes on top (every network input hostile, every route authenticated, errors that leak nothing, encrypted transport, rate limits). Each rule traced to OWASP or CWE, with where each stack's tooling enforces it. Not a command; Claude reads it whenever code is about to be written, and /orc-code asks the one question that decides the tier.
user-invocable: false
---
```

Body shape (mirror `code-discipline`'s opening paragraph — say what its sibling is, why the set is small, the research date):

```markdown
# Security Discipline

`code-discipline` says how code is shaped. This says what it must never let in or let out. <N>
rules in two tiers, each traced to OWASP or CWE so the next reader can judge it… (researched
2026-09-19; BACKLOG #<Task 11's number>).

**Every project** — Orcshot's tier: … one sentence naming the situation.
**Reachable by strangers** — the tier of anything that accepts a connection from someone you did
not invite: … one sentence.

How Claude knows which: from the code when there is code (a route handler is a route handler);
from `/orc-code`'s one question when there is not yet any.

## 1. <rule> — *Every project*
…
## N. <rule> — *Reachable by strangers*
…

## What this is not

- Not `secret-hygiene` — that keeps a credential out of the transcript; this keeps it out of the
  repo and the artifact, and points there for the rest.
- Not a penetration test, and not runtime protection.
- Not enforced by this file. The checkable rules are linter configuration — each `stack-*`
  skill's `## Security — where security-discipline lands` section — and Orclab's `lint_on_write`
  hook runs the project's configured linter on every write. The dependency rule is `/orc-test
  audit`, which `/orc-git` runs before anything reaches a remote. Bringing an existing codebase
  up to these rules is `/orc-code refactor`'s quality mode.

## Sources (live on 2026-09-19)
- every URL read in Step 2
```

Each rule: the situation it fires in, phrased so the code shows it; the source quoted (a short quote, cited); the tier tag in italics in the heading line; where it lands — "linted", "scaffolded", "`audit`", or "reviewed, not linted" — so the stack tasks know which to configure.

- [ ] **Step 4: Reader-side pass, then run the skill tests**

Run: `python3 -m pytest -q hooks/scripts/tests/test_security_discipline.py -k "not stack"` → green.

- [ ] **Step 5: Commit**

```bash
git add skills/security-discipline hooks/scripts/tests/test_security_discipline.py
git commit -m "security-discipline: N rules in two tiers, traced to OWASP and CWE; the test that every stack skill must carry a Security section (v22 §1) — test_every_stack_skill_is_expected stays red until the ninth stack section lands

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Tasks 4–8: the Security section in each stack skill — the shared procedure

Each of Tasks 4–8 follows this procedure for its skills; the task text below lists only what is specific to that stack. **Section shape**, inserted immediately after the skill's `## Lint — where code-discipline lands` section (and its subsections, if any), before the next `##`:

```markdown
## Security — where security-discipline lands

`security-discipline`'s rules for this stack, confirmed live YYYY-MM-DD. No project has been
through this yet; the first one corrects it.

### Static analysis
<the security ruleset in the SAME config file the Lint section owns — the exact lines to add, or
"none free: <what was checked>">. Which security-discipline rules it covers, by number.

### Dependency audit
<the `/orc-test audit` tool for this language — one line pointing at `skills/orc-test/languages/<lang>.md`'s
`## Audit`, and the install line — or "none free">.

### Secrets
<where a secret lives on each platform this stack targets (env / keychain / keystore / the OS
secure store), the `.gitignore` entries, and what must never be in the built artifact>.

### Reachable by strangers
<for the exposed tier: what `/orc-code` scaffolds from day one — the auth layer, the
public/private split, error handling that returns no internals, transport — as the stack does
it; or "this stack does not accept connections: n/a" for a purely client-side stack, with one
line on the client-side rules that still apply (embedded keys, certificate validation)>.
```

Each task: (1) read the skill in full and the spec §2; (2) research from primary sources — the linter's own rule docs, the platform's own secure-storage docs; (3) write the section; (4) extend `## Sources`; (5) add the skill's directory name to `EXPECTED` in `hooks/scripts/tests/test_security_discipline.py`; (6) run `python3 -m pytest -q hooks/scripts/tests/test_security_discipline.py -k stack` → its new case green; (7) reader-side pass; (8) commit.

### Task 4: Python and web — `stack-python-desktop`, `stack-web`

**Files:** `skills/stack-python-desktop/SKILL.md`, `skills/stack-web/SKILL.md`, `hooks/scripts/tests/test_security_discipline.py` (`EXPECTED |= {"stack-python-desktop", "stack-web"}`)

- [ ] **Research:** ruff's `S` rules (`https://docs.astral.sh/ruff/rules/#flake8-bandit-s`) — which to `extend-select` (the whole `S` category, then which to leave off for a desktop app and why — `S101` assert in tests is the known one; say whether a per-file ignore for `tests/` is the answer); pyright has nothing security-specific — say so. JS/TS: `eslint-plugin-security` on npm (current version, whether it has an oxlint port — check `oxc_linter/src/rules/` for a `security` directory; if oxlint has none, the section says the ESLint plugin runs beside oxlint and how). FastAPI: its security docs (`/tutorial/security/`) for the auth layer scaffolded on the exposed tier; `fastapi run` behind a reverse proxy holding TLS (already in the Deployment section — cross-reference, do not repeat). Secrets: env vars via `pydantic-settings` or `os.environ` — the FastAPI settings page; browser side: nothing secret ever in `web/`. Python desktop secrets: `keyring` on PyPI (current version, which backends per OS).
- [ ] **Write both sections; `stack-python-desktop`'s "Reachable by strangers" is "n/a: a desktop app accepts no connections" plus the client-side line.**
- [ ] Commit: `stack-python-desktop, stack-web: Security — where security-discipline lands (v22 §2)`.

### Task 5: Kotlin — `stack-android-native`, `stack-kotlin-multiplatform`

**Files:** the two skills; `EXPECTED |= {"stack-android-native", "stack-kotlin-multiplatform"}`

- [ ] **Research:** detekt's rule sets (`https://detekt.dev/docs/rules/`) — whether any security rules exist (there is no `security` set as of the last known; confirm); Android Lint's security checks (`https://googlesamples.github.io/android-custom-lint-rules/checks/` — the `Security` category, and `lintOptions`/`lint { warningsAsErrors }` in the Android Gradle plugin docs); the OWASP Dependency-Check Gradle plugin (Task 2's finding — reference `languages/kotlin.md`); Android secrets: `EncryptedSharedPreferences` is deprecated (confirm on developer.android.com — the Jetpack Security release notes) and what replaces it; Android Keystore. KMP: the same on the Android side; on iOS, Keychain via a KMP library (`multiplatform-settings` or the platform API) — confirm on the library's GitHub.
- [ ] Commit: `stack-android-native, stack-kotlin-multiplatform: Security sections (v22 §2)`.

### Task 6: Swift — `stack-ios-native`

**Files:** the skill; `EXPECTED |= {"stack-ios-native"}`

- [ ] **Research:** SwiftLint's rule list (`https://realm.github.io/SwiftLint/rule-directory.html`) — any security rule; if none, "none free" and what was checked. Keychain Services (`https://developer.apple.com/documentation/security/keychain-services`); App Transport Security (`https://developer.apple.com/documentation/bundleresources/information-property-list/nsapptransportsecurity`) — on by default, and what an exception costs at review. Dependency audit: Task 2's Swift finding.
- [ ] Commit: `stack-ios-native: Security section (v22 §2)`.

### Task 7: Flutter and React Native — `stack-flutter`, `stack-react-native`

**Files:** the two skills; `EXPECTED |= {"stack-flutter", "stack-react-native"}`

- [ ] **Research:** Dart: `analysis_options.yaml` — any security lints in `https://dart.dev/tools/linter-rules` (search the page for "secur", "unsafe"); `flutter_secure_storage` on pub.dev (version, which platform store each OS uses). Dart audit: Task 2's finding. RN: `eslint-plugin-security` (Task 4's finding applies), `expo-secure-store` on docs.expo.dev (what it wraps per platform, size limit), `npm audit`. Both: the embedded-API-key rule — an app binary is not a secret store; say where the key goes instead (a server the app calls).
- [ ] Commit: `stack-flutter, stack-react-native: Security sections (v22 §2)`.

### Task 8: Games — `stack-godot`, `stack-unity`

**Files:** the two skills; `EXPECTED |= {"stack-godot", "stack-unity"}`

- [ ] **Research:** GDScript: gdlint's rule list (`https://github.com/Scony/godot-gdscript-toolkit/wiki`) — none security; Godot's own docs on `OS.get_environment`, `ConfigFile` with encryption (`config_file.load_encrypted`), and that an exported `.pck` is readable — the "no secret in the build" rule's concrete form. Unity: Roslyn analyzers for C# security — check whether `SecurityCodeScan` on NuGet is still maintained (last release date) and whether Unity's own package manager can load it (docs.unity3d.com "Roslyn analyzers"); `dotnet list package --vulnerable` for a Unity project's `.csproj` — Task 2's C# finding and whether it applies to Unity-generated projects; Unity's docs on `PlayerPrefs` (not secure) and the secure alternative. Both "Reachable by strangers": n/a for a single-player game; a line on multiplayer being out of scope with a BACKLOG pointer if the research shows it matters.
- [ ] After the commit, `test_every_stack_skill_is_expected` is green: run the full file `python3 -m pytest -q hooks/scripts/tests/test_security_discipline.py` and say so in the commit message.
- [ ] Commit: `stack-godot, stack-unity: Security sections; all nine stack skills now carry one (v22 §2)`.

---

### Task 9: `/orc-code` asks the question, scaffolds to the tier, wraps `modernize-harden`; `test-discipline` gets its line

**Files:**
- Modify: `skills/orc-code/SKILL.md` (New-Project Flow steps 3–7; Quality mode steps 1 and 3)
- Modify: `docs/commands/orc-code.md` ("What it will ask you" list; "What it changes")
- Modify: `hooks/scripts/tests/test_orc_code_skill.py`
- Modify: `skills/test-discipline/SKILL.md` (rule 1, the scenario bullet)

**Interfaces:**
- Consumes: Task 3's skill name and section heading; Tasks 4–8's `### Reachable by strangers` subsections (what scaffold builds).

- [ ] **Step 1: Pinning tests, red**

Append to `hooks/scripts/tests/test_orc_code_skill.py`:

```python
def test_new_project_flow_asks_exposure_after_platforms_and_before_starting_point():
    flow = TEXT[TEXT.index("## New-Project Flow"):TEXT.index("## Add-to-Existing Flow")]
    q = "Will anyone you didn't invite be able to reach this?"
    assert q in flow
    assert flow.index("Which platforms?") < flow.index(q) < flow.index("minimal example")
    for phrase in ["I'll assume yes", "I'll assume no", "security-discipline", "not recorded"]:
        assert phrase in flow, phrase


def test_scaffold_writes_the_security_config_and_the_exposed_tier_pieces():
    flow = TEXT[TEXT.index("## New-Project Flow"):TEXT.index("## Add-to-Existing Flow")]
    scaffold = flow[flow.index("**Scaffold**"):flow.index("**Verify**")]
    for phrase in ["## Security — where security-discipline lands", "### Reachable by strangers"]:
        assert phrase in scaffold, phrase


def test_quality_mode_writes_security_config_and_wraps_modernize_harden():
    q = TEXT[TEXT.index("### Quality mode"):TEXT.index("### Migration mode")]
    assert "## Security — where security-discipline lands" in q
    assert "modernize-harden" in q and "Plugin-Discovery Procedure" in q
    assert q.index("one function at a time") < q.index("modernize-harden") < q.index("/orc-test generate")
    assert "isn't currently installed" in q or "not installed" in q


def test_test_discipline_names_the_hostile_scenario():
    td = (ROOT / "skills" / "test-discipline" / "SKILL.md").read_text()
    r1 = td[td.index("## 1. "):td.index("## 2. ")]
    assert "trust boundary" in r1 and "unauthenticated" in r1
```

Run: `python3 -m pytest -q hooks/scripts/tests/test_orc_code_skill.py` → 4 new failures.

- [ ] **Step 2: The exposure question — New-Project Flow**

In `skills/orc-code/SKILL.md`, after step 3 (Scope) and its bullets, insert a new step 4 and renumber Starting point → 5, Scaffold → 6, Verify → 7, Report → 8 (and the sentence "Once all four are answered:" → "Once all five are answered:"):

```markdown
4. **Exposure**: "Will anyone you didn't invite be able to reach this?" — with the proposed
   answer already in the question, so it is a confirmation, not a blank: web ticked → "You
   ticked web, so I'll assume yes — right?"; desktop or mobile only → "Nothing you ticked
   accepts connections, so I'll assume no — right?". The answer is which of
   `security-discipline`'s two tiers the scaffold builds to: *Every project*, or *Reachable by
   strangers*. It is not recorded anywhere — what step 6 scaffolds is the record, and from then
   on the code says which tier it is (a route handler is a route handler).
```

- [ ] **Step 3: The scaffold step**

Extend the (now) step 6 Scaffold with, after its existing sentence:

```markdown
   Also write the stack skill's `## Lint — where code-discipline lands` config and its
   `## Security — where security-discipline lands` static-analysis config — the same file — and
   the `.gitignore` entries the Security section's `### Secrets` names. If the answer to step 4
   was yes, scaffold what that section's `### Reachable by strangers` lists for this stack: the
   auth layer, the public/private split, error handling that returns no internals, transport.
   `/orc-code` names no framework itself; the stack skill does.
```

- [ ] **Step 4: Quality mode**

Step 1 of Quality mode ("The stack's lint config is present, or is written first"): after the sentence ending `tell the user the project has just adopted `code-discipline`, and commit the config on its own.` add: `The same for the `## Security — where security-discipline lands` static-analysis config, in the same file — one commit says the project adopted both.`

Insert a new sub-step 3.3 (renumber the existing 3.3 `/orc-test generate` to 3.4):

```markdown
   3. **The security scan, through `modernize-harden`.** Run the Plugin-Discovery Procedure
      below for `code-modernization`. Found: run `/modernize-harden` on the project — it scans
      for OWASP, CWE, dependency and secrets findings and produces a reviewable patch; review
      each hunk against `security-discipline`'s rules and apply what holds, under the same
      "suite green after every file" rule. Not found: say plainly "`code-modernization` isn't
      currently installed", offer the install line the procedure gives, and — if the user
      declines — read `security-discipline` against the code by hand, one rule at a time, the
      way step 3.2 reads `code-discipline`.
```

- [ ] **Step 5: `test-discipline` rule 1**

In `skills/test-discipline/SKILL.md`, rule 1's third bullet ends `…the boundary the code's own `if` names.` Append to that bullet: ` At every trust boundary, the hostile case — an unauthenticated request, malformed input — is on the list, and the test proves it is refused (`security-discipline`).`

Run: `python3 -m pytest -q hooks/scripts/tests/test_test_discipline_frontmatter.py` → still green (six rules, unchanged).

- [ ] **Step 6: The doc page**

`docs/commands/orc-code.md`, "What it will ask you", the numbered new-project list: insert after item 3 (platforms) and renumber:

```markdown
4. Whether anyone you didn't invite will be able to reach it — a public website or API, yes; an
   app that runs only on your own machine or phone, no. It guesses from the platforms you ticked
   and asks you to confirm, and the answer decides which security rules the new project is built
   to from the start.
```

"What it changes", the **New project** bullet: append ` It also writes the project's lint and security-check settings, and — when you said strangers can reach it — the pieces those rules need from day one: a login layer, a public folder separate from the code, error pages that give nothing away.` The **Quality mode** bullet: after `writes one and commits it on its own`, add `(the security-check settings are written the same way)`, and append a sentence: `If the `code-modernization` plugin is installed, it also runs that plugin's security scan and applies what holds up; if not, it tells you and reviews the code against the security rules by hand.`

- [ ] **Step 7: Green, whole suite, commit**

Run: `python3 -m pytest -q` → green.

```bash
git add skills/orc-code skills/test-discipline docs/commands/orc-code.md hooks/scripts/tests/test_orc_code_skill.py
git commit -m "orc-code: asks whether strangers can reach the project, scaffolds to that tier, wraps modernize-harden in quality mode; test-discipline names the hostile scenario (v22 §2)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 10: `/orc-git` — `audit` joins the gate

**Files:**
- Modify: `skills/orc-git/SKILL.md` (`push` step 3, `release` step 4, bare listing, family table)
- Modify: `docs/commands/orc-git.md`
- Modify: `hooks/scripts/tests/test_orc_git_skill.py`

**Interfaces:**
- Consumes: Task 1's report lines (`audit ✗ N vulnerable`, `not available`, `missing … — skipped`).

- [ ] **Step 1: Widen the pinning test, red**

In `hooks/scripts/tests/test_orc_git_skill.py`:

```python
def test_push_runs_audit_beside_coverage_and_a_vulnerable_dependency_stops_it():
    body = section(SKILL, "push")
    audit_cmd = f'{RUN_PY} --cwd <repo root> audit'
    assert audit_cmd in body
    assert body.index("nothing to push") < body.index(audit_cmd) < body.index("git push -u origin")
    for phrase in ["vulnerable", "not available", "nothing is pushed"]:
        assert phrase in body, phrase


def test_release_runs_audit_too():
    body = section(SKILL, "release [tag]")
    assert f'{RUN_PY} --cwd <repo root> audit' in body


def test_listing_and_page_name_the_audit():
    listing = section(SKILL, "Bare invocation (no arguments)")
    assert "after /orc-test coverage and audit pass" in listing
    changes = section(PAGE, "What it changes")
    assert "known vulnerabilit" in changes
    never = section(PAGE, "What it will never do without asking")
    assert "known vulnerabilit" in never
```

Run → 3 new failures.

- [ ] **Step 2: The skill**

`push` step 3: after the coverage command block and before "Three outcomes", add:

```markdown
   and then the dependency audit:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/orc-test/scripts/run.py" --cwd <repo root> audit
   ```
   `audit` checks every dependency the project declares against the public advisory lists —
   `security-discipline`'s every-project rule. A `✗ N vulnerable` line is a failed gate exactly
   like coverage: show the report (each line names the package and the version that fixes it),
   say "bump the named packages", and stop — **nothing is pushed**. `audit not available` or
   `missing <tool> — skipped` is carried into the report and the push continues, the same as a
   `not measurable` coverage line.
```

Then in "Three outcomes", first bullet becomes `It exits 0 with every gate ✓ — both commands — continue to the push.` `release` step 4: the same block after the `analyze` command, with the same sentence. Bare listing: `push — push the current branch, after /orc-test coverage and audit pass`; `release … after /orc-test analyze and audit pass`. Family table: `push` and `release` run `/orc-test` — add `(coverage or analyze, then audit)`.

- [ ] **Step 3: The page**

`docs/commands/orc-git.md`: "What you type" `push` row: `Runs the project's tests with coverage and checks its dependencies for known vulnerabilities first, then pushes…`; `release` row likewise. "What it changes": in the push bullet after `each held to 80%`, add ` — and checks every dependency the project uses against the public lists of known vulnerabilities`. "What it will never do without asking", the "never push while…" bullet: add ` or while any dependency has a known vulnerability (it names the package and the version that fixes it)`. The "When it can't measure" bullet: add ` — or the project's language has no dependency-audit tool —`.

- [ ] **Step 4: Green, commit**

Run: `python3 -m pytest -q hooks/scripts/tests/test_orc_git_skill.py hooks/scripts/tests/test_docs.py` → green.

```bash
git add skills/orc-git docs/commands/orc-git.md hooks/scripts/tests/test_orc_git_skill.py
git commit -m "orc-git: push, cp and release run /orc-test audit beside the v21 gate — a known-vulnerable dependency stops the push (v22 §3)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 11: Live verification, the BACKLOG record, the plugin reload

**Files:**
- Modify: `skills/orc-test/languages/python.md` (`Last real run:` line)
- Modify: `BACKLOG.md` via `/orc-todo add` (never by hand; it never commits)

- [ ] **Step 1: `audit` on Orclab itself**

```bash
cd /home/direflail/projects/orclab && python3 skills/orc-test/scripts/run.py audit
```

Expected: `detected: Python` then either `Python     audit ✓ 0 vulnerable` or the `missing pip-audit — pip install pip-audit — skipped` line (this machine may not have it — if so, `pip install pip-audit` into the venv Orclab's suites use, and run again; the *command* never installs, the developer may). Paste the line into `python.md`'s `Last real run:`.

- [ ] **Step 2: Orclab's own Python Security section, measured not fixed**

```bash
ruff check --select S . 2>/dev/null | tail -3
```

Record the finding count. Do **not** fix them in this task — that is `/orc-code refactor`'s quality mode on Orclab, a separate session. The number goes in the entry.

- [ ] **Step 3: The scaffold, live**

In the scratchpad, a throwaway: `/orc-code` → new → name `v22check` → app → web → confirm "yes" to the exposure question → minimal example. Check: the stack's lint config carries the security ruleset; the exposed-tier pieces `stack-web`'s `### Reachable by strangers` lists exist; `git init` it and run `python3 <orclab>/skills/orc-test/scripts/run.py audit` inside it. Record what was and was not there. Then delete the directory.

- [ ] **Step 4: The entries**

Use `orclab:backlog-discipline` (read it first; it owns the format). Two entries through `/orc-todo add backlog "<title>"` with the body on stdin:

1. Title: `security-discipline: every project's rules and the extra set for one strangers can reach — v22 (RESOLVED 2026-09-19)`. Body: the request quoted (direflail's two sentences from the spec's "The problem"), the decision order ("B. it needs to happen before anything"), what shipped per spec section, the rule count and sources, the search that found nothing covering it (the spec's list), the live lines from Steps 1–3 pasted, and the ruff `S` count with "Orclab's own adoption is a quality-mode pass, not done here".
2. Title: `A secret-scan hook over git history is not built; security-discipline's repo rule is prose plus .gitignore`. Body: two sentences — the rule that covers it today, what a hook would add, and that it waits for a real case (cite this spec §3).

And a third *if not already present*: `PHP as a /orc-code alternative on the web row — v23, starts when v22 ships`, body: the DreamHost facts confirmed live 2026-09-19 (php.net support table: 8.3 security-only to 2027-12-31, 8.4 active to 2026-12-31, 8.5 to 2027-12-31; DreamHost's version page lists 8.5/8.4/8.3/8.2; Composer install steps on DreamHost's own page; orcshot.org set to 8.5; Mint 22.3 apt has 8.3), and that the stack skill is born with a Security section.

- [ ] **Step 5: Commit, then reload the plugin**

```bash
git add BACKLOG.md skills/orc-test/languages/python.md
git commit -m "BACKLOG: v22 security-discipline shipped and verified live; the deferred secret-scan hook; PHP as v23

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

Then `/orc-reload`, and in a fresh session confirm `security-discipline` is listed among the skills and `/orc-test audit` is accepted.

---

## Self-review against the spec

- **§1 the skill** — Task 3: frontmatter, two tiers, single-digit ceiling, sources live, "What this is not" pointing at `secret-hygiene`, `lint_on_write`, `audit`. The "how Claude knows the tier" paragraph is in Task 3 Step 3's body shape; the question is Task 9.
- **§2 stack sections** — Tasks 4–8, nine skills, one shape, `EXPECTED` grows to all nine and `test_every_stack_skill_is_expected` closes the gap; Security named as the fourth facet is in the spec (nine; the spec was corrected with this plan). **`/orc-code` three changes** — Task 9 Steps 2–4. **`test-discipline` one line** — Task 9 Step 5.
- **§3 enforcement** — hook untouched (Global Constraints); `audit` Tasks 1–2; gate Task 10; `modernize-harden` wrap Task 9 Step 4. Not built: named in Task 11's second entry.
- **§4 tests** — `test_security_discipline.py` (Task 3), `test_cli_audit.py` + per-language (Tasks 1–2), `test_orc_git_skill.py` widened (Task 10), `test_orc_code_skill.py` (Task 9). **Docs** — orc-test (Task 1), orc-code (Task 9), orc-git (Task 10), each in the same commit as its skill. **Records** — Task 11.
- **Verification** — Task 11 Steps 1–3 are the spec's three checks.
- **Out of scope** — nothing here touches PHP, shared-hosting publishing, runtime protection, git-history scanning, or a `.orclab/` exposure record.
- **Placeholders** — the `<…>` in Task 1 Step 11 (`<version from Step 7>`, `<the line Task 11 records>`) and Task 3 (`<N>`, `<rule>`) are values the executing task produces in an earlier step of the same plan; none is "TBD".
- **Names** — `AUDIT_TOOL`, `AUDIT_NONE`, `audit_unavailable`, `audit_cmd`, `audit_findings`, `cmd_audit`, `_audit_line` are used with the same spelling in Tasks 1, 2 and 10; the heading string and `EXPECTED` are spelled identically in Tasks 3–9.
