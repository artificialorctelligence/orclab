# Orclab v21: `/orc-git` test gate before push — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/orc-git push`, `cp` and `release` run `/orc-test` before anything reaches GitHub — `coverage` (80%) before a push, `analyze` (adds 70% TCE) before a release — and stop with the report when it fails.

**Architecture:** Orclab commands are Markdown skills Claude follows step by step; there is no code path for `push`. The gate is therefore prose inside three subcommand sections of `skills/orc-git/SKILL.md`, mirroring how `merge` already calls `/orc-test run`. The user-facing page `docs/commands/orc-git.md` says the same in the user's words, and a new test in `hooks/scripts/tests/` pins the sentences so a later edit that drops the gate fails a test.

**Tech Stack:** Markdown skills; Python 3 / pytest for the pinning test (run from the repo root, where `pyproject.toml` sets `testpaths` and `pythonpath`).

**Spec:** `docs/superpowers/specs/2026-09-15-orclab-v21-push-gate-design.md`. Read it first; every sentence below rests on a numbered section there.

## Global Constraints

- Nothing in `/orc-test` changes. The gate calls `run.py` as it is (spec §6).
- No skip flag on any `/orc-git` subcommand (spec §3).
- `merge` is untouched (spec §1).
- `docs/commands/orc-git.md` keeps exactly its five `##` headings in order — `hooks/scripts/tests/test_docs.py` fails otherwise.
- Every test runs from the repo root: `cd /home/direflail/projects/orclab && python3 -m pytest -q hooks/scripts/tests/<file>`.
- Commit messages end with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- Write for the reader who types the command: what happens, in what order, what they see. Names of scripts come after that, not instead of it.

## File structure

| File | Responsibility |
|---|---|
| `hooks/scripts/tests/test_orc_git_skill.py` (create) | Pins the gate's presence in the skill's `push`, `commit-push`, `release` sections and bare listing, and both thresholds on the doc page. Same shape as `test_orc_test_skill.py` beside it: read the file, assert phrases. |
| `skills/orc-git/SKILL.md` (modify) | The instruction Claude follows. Three subcommand sections, the bare listing, one sentence in "Two families under one name". |
| `docs/commands/orc-git.md` (modify) | The page a user reads. "What you type", "What it changes", "What it will never do without asking". |

Task 1 writes the test red; Task 2 turns the skill half green; Task 3 turns the doc half green; Task 4 verifies live.

---

### Task 1: The pinning test, red

**Files:**
- Create: `hooks/scripts/tests/test_orc_git_skill.py`

**Interfaces:**
- Produces: the exact phrases Tasks 2 and 3 must write. They are listed in the test below and again in each task; if a task changes a phrase, it changes it here too.

- [ ] **Step 1: Write the test**

```python
"""The v21 gate (spec 2026-09-15-orclab-v21-push-gate-design.md): /orc-git runs /orc-test
before anything reaches GitHub. These pin the sentences in the skill Claude follows and the
page a user reads, so an edit that drops the gate fails here rather than in front of a user."""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = (ROOT / "skills" / "orc-git" / "SKILL.md").read_text()
PAGE = (ROOT / "docs" / "commands" / "orc-git.md").read_text()

RUN_PY = 'python3 "${CLAUDE_PLUGIN_ROOT}/skills/orc-test/scripts/run.py"'


def section(text, heading):
    """The body of one `## heading` up to the next `## `."""
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    assert m, heading
    return m.group(1)


def test_push_runs_coverage_after_the_nothing_to_push_check_and_before_the_push():
    body = section(SKILL, "push")
    assert f"{RUN_PY} --cwd" in body and " coverage" in body
    gate = body.index("coverage")
    assert body.index("nothing to push") < gate < body.index("git push -u origin")
    for phrase in ["exits non-zero", "nothing is pushed", "not measurable", "git status --porcelain",
                   "does not start `/orc-test generate`"]:
        assert phrase in body, phrase


def test_cp_says_the_gate_belongs_to_the_push_half():
    body = section(SKILL, "commit-push [text] / cp [text]")
    assert "committed" in body and "not pushed" in body
    assert "coverage" in body


def test_release_runs_analyze_after_the_tag_check_and_before_the_pushes():
    body = section(SKILL, "release [tag]")
    assert f"{RUN_PY} --cwd" in body and " analyze" in body
    gate = body.index(" analyze")
    assert body.index("Confirm the tag exists locally") < gate < body.index("git push origin HEAD")
    assert "TCE" in body and "minutes" in body


def test_merge_still_runs_run_not_coverage():
    body = section(SKILL, "merge <branch>")
    assert f"{RUN_PY} --cwd <path to the branch's tree> run" in body
    assert " coverage" not in body


def test_the_bare_listing_names_the_gate_on_push_and_release():
    listing = section(SKILL, "Bare invocation (no arguments)")
    assert "push the current branch, after /orc-test coverage passes" in listing
    assert "after /orc-test analyze passes" in listing


def test_the_family_table_names_the_dependency_on_orc_test():
    body = section(SKILL, "Two families under one name")
    assert "/orc-test" in body and "Orclab's own" in body


def test_no_subcommand_offers_a_way_to_skip_the_gate():
    for flag in ["--no-test", "--skip-test", "--no-gate", "--force-push"]:
        assert flag not in SKILL, flag


def test_the_page_says_when_the_tests_run_and_what_stops_a_push():
    typed = section(PAGE, "What you type")
    assert "test" in typed.split("`/orc-git push`")[1].split("\n")[0].lower()
    assert "test" in typed.split("`/orc-git release [tag]`")[1].split("\n")[0].lower()
    changes = section(PAGE, "What it changes")
    assert "80%" in changes and "coverage" in changes
    assert "70%" in changes and "mutation" in changes and "minutes" in changes
    never = section(PAGE, "What it will never do without asking")
    assert "under 80%" in never and "under 70%" in never
    assert "never writes tests on its own" in never
    assert "can't measure" in never or "cannot measure" in never
```

- [ ] **Step 2: Run it and confirm it fails on the skill and the page, not on the harness**

Run: `cd /home/direflail/projects/orclab && python3 -m pytest -q hooks/scripts/tests/test_orc_git_skill.py`
Expected: `test_merge_still_runs_run_not_coverage` and `test_no_subcommand_offers_a_way_to_skip_the_gate` PASS (they hold today); the other six FAIL with `AssertionError` on a phrase. If any fails with a `re` or `IndexError` instead, the `section()` helper or a heading name is wrong — fix the test, not the skill.

- [ ] **Step 3: Commit the red test**

```bash
cd /home/direflail/projects/orclab
git add hooks/scripts/tests/test_orc_git_skill.py
git commit -m "v21: pin the /orc-git test gate's sentences in the skill and the page (red until they are written)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: The skill — `push`, `cp`, `release`, the listing, the family table

**Files:**
- Modify: `skills/orc-git/SKILL.md` — sections `## Two families under one name`, `## Bare invocation (no arguments)`, `## push`, `## commit-push [text] / cp [text]`, `## release [tag]`
- Test: `hooks/scripts/tests/test_orc_git_skill.py` (Task 1)

**Interfaces:**
- Consumes: the phrases in Task 1's test. The exact strings the test looks for are marked ⟨pinned⟩ below.
- Produces: the three outcomes ("green → continue; red → report and stop; not measurable → report and continue") that Task 3 restates for the user.

Read `skills/orc-git/SKILL.md` in full before editing. Its `merge` section step 3 is the existing example of calling `/orc-test`; match its voice.

- [ ] **Step 1: The family table — one sentence**

In `## Two families under one name`, the paragraph after the table begins `The name under-describes the right-hand column.` Add this paragraph before it:

```markdown
One dependency cuts across the table: `push` and `release` run `/orc-test` before they touch a
remote (v21). That is Orclab's own, not a host's, so the left column still works against any
host — but it no longer works without the rest of the plugin.
```

⟨pinned⟩: `/orc-test`, `Orclab's own`.

- [ ] **Step 2: The bare listing — two lines**

In the code block under `## Bare invocation (no arguments)`, change:

```
  push                 — push the current branch
```
to
```
  push                 — push the current branch, after /orc-test coverage passes
```
and
```
  release [tag]        — push a tag and create the GitHub Release for it (default: newest local tag)
```
to
```
  release [tag]        — push a tag and create the GitHub Release for it, after /orc-test analyze passes (default: newest local tag)
```

⟨pinned⟩: both phrases verbatim.

- [ ] **Step 3: `push` — the gate step**

The section today has four numbered steps. Renumber so the gate is step 3 and the old 3 and 4 become 4 and 5. The new step, inserted after step 2 (the one ending `say so plainly and stop: already in sync, nothing to push.`):

```markdown
3. **Run the project's test suites with coverage, before pushing** — with `/orc-test`:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/orc-test/scripts/run.py" --cwd <repo root> coverage
   ```
   (`git rev-parse --show-toplevel` is the repo root.) `/orc-test` runs every language's own
   suite and holds each to 80% line coverage; a red suite is a failed gate too. Three outcomes:
   - **It exits 0 with every gate ✓** — continue to the push.
   - **It exits non-zero** — show its report, whose last line already says what to do
     (`gates failed: coverage — run /orc-test generate to repair`, or `gates failed: tests —
     fix the failing tests first`), and stop — **nothing is pushed**. This step does not start
     `/orc-test generate`: that writes tests, and runs only when the user types it or says yes.
     There is no flag to skip this gate; `git push` typed by hand is the way past a red one,
     and that is deliberate.
   - **It exits 0 but a line reads `not measurable`** (no coverage tool installed, no report
     produced, no language detected) — continue to the push, and carry that line into the
     report. `/orc-test` never installs a tool; a project that wants this gate to bite installs
     the one it names.

   The suite runs against the working tree as it stands. If `git status --porcelain` prints
   anything, add one line to the report: the tree had uncommitted changes, so what was measured
   is not exactly what is being pushed.
```

⟨pinned⟩: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/orc-test/scripts/run.py" --cwd`, ` coverage`, `exits non-zero`, `nothing is pushed` (lower-case, exactly as in the bullet above — the test's match is case-sensitive), `not measurable`, `git status --porcelain`, ``does not start `/orc-test generate` ``.

The order the test checks: `nothing to push` (in step 2) comes before the first `coverage`, which comes before `git push -u origin` (in the old step 3, now 4).

The old step 4 — `If the user typed this, it runs; if pushing was your idea, ask first` — becomes step 5, unchanged.

- [ ] **Step 4: `cp` — one paragraph**

In `## commit-push [text] / cp [text]`, after the two-bullet list (`Tree dirty → commit it. …` / `Branch ahead of its upstream → push it. …`) and before `Both halves being no-ops at once …`, add:

```markdown
The test gate is part of the push half, so it runs after the commit and on the committed tree.
When it fails, the commit stands and the report says exactly that — `committed abc123; not
pushed: coverage 71% (min 80)` — with `/orc-test`'s own output under it.
```

⟨pinned⟩: `committed`, `not pushed`, `coverage`.

- [ ] **Step 5: `release` — the gate step**

The section today has six numbered steps. Insert the gate as step 4 after step 3 (`**Confirm the tag exists locally:** …`), and renumber the old 4–6 to 5–7:

```markdown
4. **Run the project's test suites with coverage and mutation testing, before anything is
   pushed** — with `/orc-test`:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/orc-test/scripts/run.py" --cwd <repo root> analyze
   ```
   `analyze` is `coverage` plus mutation testing — it plants one defect at a time and checks
   the suite notices — held at 70% TCE per language, plus a lint of the test files. It takes
   minutes on a small project and longer on a large one; say so before running it. A release
   is the one push whose artifact other people download, which is why it gets the slow check.
   The same three outcomes as `push`'s gate: exit 0 with every gate ✓ → continue; exit
   non-zero → show the report and stop, nothing pushed, nothing released, `generate` not
   started; `not measurable` lines → continue and carry them into the report. If `git status
   --porcelain` prints anything, say so in the report.
```

⟨pinned⟩: the `run.py" --cwd` string, ` analyze`, `TCE`, `minutes`. Order: `Confirm the tag exists locally` < ` analyze` < `git push origin HEAD`.

- [ ] **Step 6: Run the test**

Run: `cd /home/direflail/projects/orclab && python3 -m pytest -q hooks/scripts/tests/test_orc_git_skill.py`
Expected: every test PASSES except `test_the_page_says_when_the_tests_run_and_what_stops_a_push` (Task 3's). If a skill test still fails, the assertion message names the missing phrase; add that exact phrase.

- [ ] **Step 7: Read the three edited sections once as Claude would follow them**

Open the file and read `push`, `commit-push`, `release` top to bottom. Check: the steps are numbered without a gap; each gate step names its command, its three outcomes, and the dirty-tree line; nothing in `merge` changed (`git diff skills/orc-git/SKILL.md` shows no hunk in that section).

- [ ] **Step 8: Commit**

```bash
cd /home/direflail/projects/orclab
git add skills/orc-git/SKILL.md
git commit -m "/orc-git push and cp run /orc-test coverage, release runs analyze, before anything reaches the remote; red gate stops with the report, nothing pushed

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: The page — what the user sees

**Files:**
- Modify: `docs/commands/orc-git.md` — `## What you type`, `## What it changes`, `## What it will never do without asking`
- Test: `hooks/scripts/tests/test_orc_git_skill.py::test_the_page_says_when_the_tests_run_and_what_stops_a_push`

**Interfaces:**
- Consumes: Task 2's three outcomes, restated in the reader's words — no script names, no `run.py`, no `TCE`.

Read `docs/commands/orc-git.md` in full first. Its voice is the v20 spec's: written for the person who types the command, who has not read the skill and will not. Keep the five `##` headings exactly as they are.

- [ ] **Step 1: "What you type" — two table rows**

Change the `push` row's right-hand cell from

```
Pushes the branch you're on to its remote copy
```
to
```
Runs the project's tests with coverage first, then pushes the branch you're on to its remote copy
```

and the `release [tag]` row's cell from

```
Pushes your current branch's commits and a version tag, then publishes the GitHub Release for it (uses the most recent tag if you don't name one)
```
to
```
Runs the project's tests with coverage and mutation testing first, then pushes your current branch's commits and a version tag, and publishes the GitHub Release for it (uses the most recent tag if you don't name one)
```

⟨pinned⟩: the word `test` on the same line as each of those two `You type` cells.

- [ ] **Step 2: "What it changes" — two bullets**

Replace the `push` bullet:

```markdown
- `push` (and the push half of `commit-push`/`cp`): pushes your current branch to its remote
  copy on GitHub.
```
with
```markdown
- `push` (and the push half of `commit-push`/`cp`): first runs the project's whole test suite
  and measures coverage — every language the project has, each held to 80% — then pushes your
  current branch to its remote copy on GitHub. The test run leaves a report under `.orclab/test/`
  and changes nothing else.
```

Replace the `release` bullet:

```markdown
- `release`: pushes your current branch's commits and a tag to GitHub, and creates a GitHub
  Release from it — a public page other people can see, listing what changed.
```
with
```markdown
- `release`: first runs the project's tests with coverage *and* mutation testing — it plants
  small defects in the code one at a time and checks that the tests notice, holding that to
  70% — which takes minutes; then pushes your current branch's commits and a tag to GitHub, and
  creates a GitHub Release from it — a public page other people can see, listing what changed.
```

⟨pinned⟩: `80%`, `coverage`, `70%`, `mutation`, `minutes`.

- [ ] **Step 3: "What it will never do without asking" — two bullets**

After the first bullet (`It will never push, merge, or release on its own initiative …`), add:

```markdown
- It will never push while the tests fail or coverage is under 80%, and never release while
  the tests fail, coverage is under 80% or mutation testing scores under 70%. It stops and
  shows you the test report, which ends by saying what would fix it; it never writes tests on
  its own — `/orc-test generate` does that, and only when you ask. There is no way to tell
  `/orc-git` to skip the check; if you want to push past a failing one, plain `git push` is the
  way, on purpose.
- When it can't measure — the project has no coverage tool installed, or no language it
  recognises — it says so in the report and pushes anyway. It never installs anything.
```

⟨pinned⟩: `under 80%`, `under 70%`, `never writes tests on its own`, `can't measure`.

- [ ] **Step 4: Run both tests**

Run: `cd /home/direflail/projects/orclab && python3 -m pytest -q hooks/scripts/tests/test_orc_git_skill.py hooks/scripts/tests/test_docs.py`
Expected: all PASS. `test_docs.py` proves the five headings survived.

- [ ] **Step 5: Read the page as the reader**

Read `docs/commands/orc-git.md` top to bottom once, as someone who has never opened a skill file. Any sentence that needs a file name or a script name to make sense gets rewritten without it. `TCE`, `run.py`, `CLAUDE_PLUGIN_ROOT` must not appear on the page.

- [ ] **Step 6: Commit**

```bash
cd /home/direflail/projects/orclab
git add docs/commands/orc-git.md
git commit -m "orc-git's page: the test run before push and release, both thresholds, and that a failing check stops the push and never writes tests on its own

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Live verification in Orclab itself

**Files:** none modified. This task produces evidence, not code.

**Interfaces:**
- Consumes: the skill as written in Task 2, followed literally by typing the command.

The point is spec §Verification: the gate works through the real surface, not through reading the prose. Do it in a fresh session if the plugin cache is what runs (`/orc-reload`, then a new session); or follow `skills/orc-git/SKILL.md` from the working tree directly, which is what this task assumes.

- [ ] **Step 1: The green path**

With Tasks 1–3 committed and unpushed on `main`, type `/orc-git push`. Expected, in order: the branch is ahead (three or four commits); `/orc-test … coverage` runs (~30 s); the report shows `Python coverage 9x.x% … ✓`; the push happens; the report names the commits pushed. Record the coverage number.

- [ ] **Step 2: The red path**

```bash
cd /home/direflail/projects/orclab
git switch -c scratch-v21-red
python3 - <<'EOF'
p = "skills/orc-todo/scripts/tests/test_lanes.py"
t = open(p).read()
open(p, "w").write(t + "\n\ndef test_deliberately_red():\n    assert False, 'v21 gate check'\n")
EOF
git commit -qam "scratch: a deliberately red test"
```

Type `/orc-git push`. Expected: the branch is ahead (no upstream → "something to push"); `/orc-test … coverage` runs and exits 1; the report shows `Python: tests failed; coverage not measured`, then `nothing measured` overall (`cmd_coverage`, `cli.py:117,150`, prints no `gates failed:` hand-off line — that's `cmd_analyze`'s only, `cli.py:261,263`); the command stops and says nothing was pushed; `git ls-remote --heads origin scratch-v21-red` prints nothing.

Then prove the escape: `git push -u origin scratch-v21-red` works by hand. Then clean up:

```bash
git push origin --delete scratch-v21-red
git switch main
git branch -D scratch-v21-red
```

- [ ] **Step 3: The `cp` path**

On `main`, make a trivial committed-not-pushed change — e.g. append a line to `BACKLOG.md`'s v21 entry (Task 5 creates it; if doing Task 4 first, touch `docs/commands/orc-git.md`'s trailing whitespace and restore it after). Type `/orc-git cp`. Expected: commit made; gate runs; push happens; report names both.

- [ ] **Step 4: The `release` path is verified at the real v21 release**

Not now: `release` needs a tag, and the tag is `/orc-version`'s to cut when v21 is done. Record in the BACKLOG entry (Task 5) that `release`'s gate is unverified until then, and verify it on the day — the `analyze` run on Orclab takes a few minutes per suite; six suites, so expect ten to fifteen minutes.

- [ ] **Step 5: Record what was seen**

Paste the three reports' key lines (coverage number from Step 1, the `gates failed` line from Step 2, the `committed … pushed` line from Step 3) into the BACKLOG entry Task 5 writes. If anything differed from "Expected", that is the finding — fix the skill text, rerun, and record the fix.

---

### Task 5: The record — BACKLOG entry and changelog note

**Files:**
- Modify: `BACKLOG.md` — append one entry at the end, resolved on creation
- Modify: `CHANGELOG.md` — nothing yet; `/orc-version` writes the v21 section when the version is cut. Leave the file alone in this task.

**Interfaces:**
- Consumes: Task 4's recorded output.

Use `orclab:backlog-discipline` — read it before writing; it owns the entry format (permanent number, heading with status, layered history). The entry number is whatever the allocator gives: `/orc-todo add` is the way, and it never commits.

- [ ] **Step 1: Add the entry through `/orc-todo add`**

Heading text (the allocator prefixes the number): `/orc-git runs /orc-test before push, cp and release — the v21 gate (RESOLVED 2026-09-15)`.

Body, in this shape:

```markdown
Requested by direflail 2026-09-15: "any time the user is going to push to github, /orc-test
runs and makes sure the tests are 80% covered and that the test quality is high." Design in
`docs/superpowers/specs/2026-09-15-orclab-v21-push-gate-design.md`, plan in
`docs/superpowers/plans/2026-09-15-orclab-v21-push-gate.md`.

**The prerequisite came first.** direflail: "we need to get orclab up to 80/70 first." Before
this entry, `/orc-test analyze` could measure one of Orclab's six suites; commits `28f9ae4`,
`3383b5d`, `dddf3d3`, `788aa67` gave every suite its mutmut config, moved orc-package's and
the hooks' tests in-process, and tested `launchpad_ppa.py`. Result: whole-project coverage
84.8% → 92.9%, every suite over 70% TCE. Three `/orc-test` defects found on the way are the
next entry.

**What shipped:** `push`/`cp` run `/orc-test coverage` after the "anything to push?" check;
`release` runs `/orc-test analyze` after the tag check. A red gate stops with the report and
nothing is pushed; no skip flag (plain `git push` is the escape); a "not measurable" line is
reported and the push proceeds. Pinned by `hooks/scripts/tests/test_orc_git_skill.py`.

**Verified live 2026-09-15** (plan Task 4): <paste Step 1's coverage line>; red branch: <paste
the `gates failed` line>, `git ls-remote` empty, `git push` by hand worked; `cp`: <paste the
committed/pushed line>. `release`'s gate is unverified until the v21 tag is cut — verify it
then and update this entry.
```

- [ ] **Step 2: Commit the entry**

```bash
cd /home/direflail/projects/orclab
git add BACKLOG.md
git commit -m "BACKLOG: the v21 push gate, its prerequisite, and what the live check showed

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-review against the spec

- §1 (where the gate sits): Task 2 Steps 3, 4, 5; `merge` untouched (Task 2 Step 7 checks the diff). ✓
- §2 (which check, dirty-tree line): Task 2 Steps 3 and 5; the `--cwd <repo root>` form. ✓
- §3 (fails → stop, no `generate`, no flag, no-tests project): Task 2 Step 3's second outcome; Task 1's `test_no_subcommand_offers_a_way_to_skip_the_gate`; Task 3 Step 3. The no-tests case needs no text of its own — it is `/orc-test`'s existing `0 tests ✗`, and the gate's "exits non-zero" outcome covers it. ✓
- §4 (not measurable → proceed): Task 2 Step 3's third outcome; Task 3 Step 3's second bullet. ✓
- §5 (files): skill — Task 2; page — Task 3; test — Task 1; `CHANGELOG.md` — deferred to `/orc-version`, stated in Task 5. ✓
- §6 (not in scope): no task touches `/orc-test`, `merge`, or adds a flag. ✓
- §Verification 1–2: Task 4 Steps 1–3. §Verification 3 (`release` live): Task 4 Step 4 defers it to the real tag with the reason, and Task 5 records that. ✓
- Placeholders: Task 5's `<paste …>` markers are filled from Task 4's output by the implementer; they are the recorded evidence, not unwritten design. No other `TBD`/`TODO`.
- Phrase consistency: every ⟨pinned⟩ phrase in Tasks 2 and 3 appears verbatim in Task 1's test; checked pairwise while writing.
