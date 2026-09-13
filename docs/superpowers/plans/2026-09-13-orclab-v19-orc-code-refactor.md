# Orclab v19: `/orc-code refactor` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/orc-code refactor` has two modes — a code-quality pass that brings an existing codebase up to `code-discipline` with the suite green throughout, and a migration that wraps `code-modernization` while landing on Orclab's own stack and proving the old suite passes on the new code — and each mode has been run once for real.

**Architecture:** Prose in `skills/orc-code/SKILL.md`, pinned by a prose test in `hooks/scripts/tests/` (the shape `test_orc_test_skill.py` already uses), plus one paragraph each in `orc-test` and `code-discipline`. No new command, no code in `orc-code`. Two live runs at the end — one per mode — correct the prose with what they contradict. Spec: `docs/superpowers/specs/2026-09-13-orclab-v19-orc-code-refactor-design.md` — read it in full before any task.

**Tech Stack:** Markdown skills; `python3 -m pytest` for the prose tests (run from the repo root); `claude plugin install` for Task 7; the scratch venv holding `ruff` for Task 6.

## Global Constraints

Every task's requirements include these. Copied from the spec and from `CLAUDE.md`.

- **Verify the description before acting on it** (`CLAUDE.md`, "show what it rests on", widened 2026-09-13): a sentence in a skill about what another Orclab component does is a claim about code. Before writing it, open the code and cite it; if it is not true yet, write "does not yet" and the backlog number. This plan's own claims about `code-modernization` were checked against its command files on 2026-09-13; a task that finds one wrong corrects the spec first (`feedback_correct_the_plan_before_the_code`), then the skill.
- **No unsafe autofixes** (spec §2): quality mode runs `ruff check --fix` / `oxlint --fix` and never `--unsafe-fixes` / `--fix-suggestions`. The 2026-09-13 dogfood record: `--unsafe-fixes` produced `lines.extend((...))` for two `append`s and eight red tests.
- **No `ignore` list to make the number go down** (spec §2, `code-discipline` rule 7): a rule the project's config enables is fixed, or suppressed at the one site with a reason.
- **Tests before migration** (spec §3(b)): a source project with no green, gated suite gets `/orc-test analyze` and `generate` on the old code before any `modernize-*` command runs.
- **Exit gate** (spec §3(b)): `/orc-test run` green on the migrated code and `analyze` reporting coverage and TCE no lower than the source baseline. "Done" is not said before it.
- **Wrapped, not rebuilt** (spec §3, `CLAUDE.md` "The specific case: wrapping real, existing skills"): the plugin's commands are read from its own directory and followed; nothing in them is copied into Orclab.
- **Unbuilt marker** (spec "How it is verified"): until Task 7 has run, the migration section's first paragraph carries *"No migration has gone through this yet; the first one corrects it."*
- **Prose tests** live in `hooks/scripts/tests/test_orc_code_skill.py`, run from the repo root as `python3 -m pytest hooks/scripts/tests/test_orc_code_skill.py -q`. Each task that changes `orc-code`'s SKILL.md adds its phrases there first and watches the test fail.
- **Commit messages** end with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`. Commit per task; do not push — pushing is `/orc-git push`, on direflail's word.
- **The reader-side pass** (`CLAUDE.md`, "Before explaining anything, explain it again from the reader's side"): every report at the end of a task is written for someone who has not read the files.

---

### Task 1: Correct the spec — discovery finds the marketplace copy, and that is not "installed"

**Files:**
- Modify: `docs/superpowers/specs/2026-09-13-orclab-v19-orc-code-refactor-design.md` (§3(d) and "How it is verified")

**Interfaces:**
- Produces: the corrected §3(d) that Task 4's Plugin-Discovery wording implements.

The spec says the flow "lands on its own 'not installed' branch". Checked 2026-09-13 while writing this plan: `/orc-code`'s Plugin-Discovery Procedure searches `~/.claude/plugins/marketplaces/` as well as `cache/`, and `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/code-modernization/.claude-plugin/plugin.json` exists. So discovery *finds* the plugin and follows its `commands/*.md` — but those commands say *"spawn the **test-engineer** subagent"*, *"Spawn the **architecture-critic** subagent"*, and the eight files under its `agents/` are registered only when the plugin is installed (`~/.claude/plugins/installed_plugins.json` does not list it). The flow would proceed and degrade silently at the first agent spawn. That is worse than the branch the spec describes.

- [ ] **Step 1: Replace §3(d)'s first two sentences**

Replace:

```
**(d) Availability, confirmed rather than assumed.** The Plugin-Discovery Procedure stays, and
the "not installed" message names the install command (`claude plugin install
code-modernization@claude-plugins-official`). But the flow past that line has never run.
```

with:

```
**(d) Availability, confirmed rather than assumed — and "found" is not "installed".** The
Plugin-Discovery Procedure searches `~/.claude/plugins/marketplaces/` as well as `cache/`, so it
finds a plugin that is merely *available* in a marketplace clone and follows its command files —
which then say "spawn the **test-engineer** subagent", and the plugin's eight agents exist only
once it is installed (checked 2026-09-13: the marketplace copy is present, `installed_plugins.json`
does not list it). The procedure therefore distinguishes the two: a plugin whose root is under
`marketplaces/` and whose name is absent from `installed_plugins.json` is *available, not
installed*, and the flow stops with the install command (`claude plugin install
code-modernization@claude-plugins-official`) and the note that a fresh session is needed after
installing (`CLAUDE.md`, marketplace gotcha 4). The flow past that line has never run.
```

- [ ] **Step 2: In "How it is verified", correct the last bullet**

Replace `prints the install command and stops. That is the one path confirmed today.` with `prints the install command and stops — confirmed by Task 4's prose test and by running the flow once with the plugin uninstalled. Before this plan, discovery would have found the marketplace copy and gone on without the agents.`

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-09-13-orclab-v19-orc-code-refactor-design.md
git commit -m "v19 spec: discovery finds the marketplace copy; found is not installed

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: `/orc-code refactor` classifies the request — quality or migration, or one question

**Files:**
- Create: `hooks/scripts/tests/test_orc_code_skill.py`
- Modify: `skills/orc-code/SKILL.md` — Step 0 item 1 (lines 13–18) and the `## Refactor Flow` heading paragraph (line 79–81)

**Interfaces:**
- Produces: the section headings `## Refactor Flow`, `### Which mode`, `### Quality mode`, `### Migration mode` that Tasks 3 and 4 fill; the test file Tasks 3–5 extend.

- [ ] **Step 1: Write the failing prose test**

```python
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills" / "orc-code" / "SKILL.md").read_text()


def test_frontmatter_still_routes_refactor():
    fm = re.match(r"---\n(.*?)\n---\n", TEXT, re.DOTALL).group(1)
    assert "name: orc-code" in fm
    assert "refactor/migrate existing code" in fm
    assert "argument-hint: [refactor]" in fm


def test_refactor_flow_has_two_modes_and_asks_when_unsure():
    for phrase in ["### Which mode", "### Quality mode", "### Migration mode",
                   "changes neither the language nor its version",
                   "names a different language, framework or version",
                   "ask — one question", "Never guess"]:
        assert phrase in TEXT, phrase
    # the modes are introduced before either is described
    assert TEXT.index("### Which mode") < TEXT.index("### Quality mode") < TEXT.index("### Migration mode")
```

- [ ] **Step 2: Run it to see it fail**

Run: `python3 -m pytest hooks/scripts/tests/test_orc_code_skill.py -q`
Expected: `test_refactor_flow_has_two_modes_and_asks_when_unsure` FAILS on `### Which mode`; the frontmatter test passes (nothing there changes).

- [ ] **Step 3: Rewrite Step 0 item 1 and the Refactor Flow opening**

Replace Step 0's item 1 with:

```
1. If invoked as `/orc-code refactor ...`, OR if `$ARGUMENTS` itself clearly describes refactoring
   or migrating existing code ("clean this up", "bring it up to code-discipline", "migrate this
   to Kotlin," "upgrade from .NET Framework to .NET 8," "port this to Python") — go to **Refactor
   Flow** below. Recognize this from reading `$ARGUMENTS` the same way you'd recognize which skill
   applies to a request — don't require the literal word "refactor" if the intent is already
   clear.
```

Replace the current `## Refactor Flow` heading and its first paragraph ("This flow wraps the `code-modernization` plugin's own real workflow rather than reimplementing it.") with:

```
## Refactor Flow

Two different jobs share this name, and they have different exit gates and different blast
radius, so the first thing this flow does is tell them apart.

### Which mode

- **Quality mode** — the request changes neither the language nor its version: "clean this up",
  "bring it up to code-discipline", "reduce the nesting in the CLI", or a bare
  `/orc-code refactor`. The code stays where it is and gets better.
- **Migration mode** — the request names a different language, framework or version: "port
  this to Kotlin", "move from .NET Framework 4.8 to .NET 8", "rewrite the front end in React".

If `$ARGUMENTS` could be either ("modernize this"), ask — one question, the two modes as the
options, each with what it does in a sentence. Never guess: a quality pass that turns into a
rewrite, or a rewrite someone wanted as a tidy-up, is the expensive mistake this question is
cheaper than.

### Quality mode

(Task 3 fills this section.)

### Migration mode

(Task 4 fills this section.)
```

The existing numbered handover steps (1–3, "Run the Plugin-Discovery Procedure… `modernize-status`… `modernize-preflight`…") move under `### Migration mode` unchanged for now; Task 4 rewrites them.

- [ ] **Step 4: Run the test to see it pass**

Run: `python3 -m pytest hooks/scripts/tests/test_orc_code_skill.py -q`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add hooks/scripts/tests/test_orc_code_skill.py skills/orc-code/SKILL.md
git commit -m "/orc-code refactor: two modes, one question when unsure

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Quality mode — the 2026-09-13 procedure, written down

**Files:**
- Modify: `skills/orc-code/SKILL.md` — the `### Quality mode` placeholder from Task 2
- Modify: `hooks/scripts/tests/test_orc_code_skill.py`
- Read: `skills/stack-python-desktop/SKILL.md` `## Lint — where code-discipline lands` (the config shape every stack section shares); `skills/orc-test/SKILL.md` `## generate`; BACKLOG #40's resolution (the dogfood record)

**Interfaces:**
- Consumes: `### Quality mode` heading (Task 2).
- Produces: the phrases Task 6's live run follows literally.

- [ ] **Step 1: Add the failing test**

```python
def test_quality_mode_is_the_dogfood_procedure_in_order():
    q = TEXT[TEXT.index("### Quality mode"):TEXT.index("### Migration mode")]
    for phrase in ["## Lint — where code-discipline lands", "a project's own settings win",
                   "/orc-test analyze", "before", "safe", "never `--unsafe-fixes`",
                   "one function at a time", "suite green after every file",
                   "/orc-test generate", "before → after", "Another round?"]:
        assert phrase in q, phrase
    for refused in ["`--unsafe-fixes`", "`ignore`"]:
        assert refused in q
    # order: config, baseline, autofix, by hand, generate, report
    marks = [q.index(p) for p in ("## Lint", "Baseline", "safe autofixes", "one function at a time",
                                   "/orc-test generate", "before → after")]
    assert marks == sorted(marks)
```

- [ ] **Step 2: Run it to see it fail**

Run: `python3 -m pytest hooks/scripts/tests/test_orc_code_skill.py -q -k quality`
Expected: FAIL on `## Lint — where code-discipline lands`.

- [ ] **Step 3: Write the section**

Replace `(Task 3 fills this section.)` with:

```
The procedure that brought Orclab's own scripts from 190 findings to zero on 2026-09-13
(BACKLOG #40), in the order that worked. Each step's output is the next step's input.

1. **The stack's lint config is present, or is written first.** Detect the language(s) the way
   `/orc-test detect` does. For each, the matching `stack-*` skill's section
   `## Lint — where code-discipline lands` names the config file and its contents. If the
   project already has that file, use it as it is — a project's own settings win, and this mode
   does not edit them. If not, write that section's config verbatim, tell the user the project
   has just adopted `code-discipline`, and commit the config on its own.
2. **Baseline, in numbers.** The linter over the whole tree (the stack section's command —
   `ruff check .`, `oxlint .`, `./gradlew detekt`, and so on) and `/orc-test analyze` on the
   same path. Write down: findings by rule, coverage, TCE, test-lint count. This is the "before";
   the report at the end is measured against it.
3. **Fix, in this order, with the suite green after every file:**
   1. The linter's **safe autofixes only** — `ruff check --fix`, `oxlint --fix` — and never
      `--unsafe-fixes` or `--fix-suggestions`: on 2026-09-13 the unsafe set turned two
      `append`s into `lines.extend((…))` and broke eight tests. Run the suite. Commit.
   2. **The rule findings, by hand, one function at a time.** Nesting depth: a guard clause
      that returns early, or the inner block extracted into a helper with a name. Function
      length: split at the seam the code already has (a comment that says "now do X" is the
      seam). Swallowed errors: handle it, or a *named, commented* suppression at that one site.
      Warnings: fix what the warning names. `code-discipline` is the reference for what each
      fix looks like. A change that needs a test the suite does not have gets that test first
      (`test-discipline` rule 2). Run the suite after each file; commit per module.
   3. **`/orc-test generate`** for what the baseline `analyze` listed — surviving mutants,
      uncovered code, test-lint findings — under `generate`'s own rules: deletions are proposed
      as a list, never done unasked.
4. **Before → after, every number**, in the shape `generate` reports: findings by rule,
   coverage, TCE, lint. If a gate still fails: say which, and ask — "Another round?" — and
   wait. Never say "clean" without the second `analyze`.

Two things this mode refuses. It does not apply unsafe autofixes (above). And it does not add an
`ignore` list to the linter config to make the number fall: a rule the project's own config
enables is either fixed or suppressed at the one site with a reason — `code-discipline` rule 7,
"applies even in cases where the analyzer gives an erroneous warning".

Architecture opinions — whether the code is over-engineered, whether a module should exist —
are not this mode's. Name them as a follow-up if they show; do not act on them here.
```

- [ ] **Step 4: Run the test to see it pass**

Run: `python3 -m pytest hooks/scripts/tests/test_orc_code_skill.py -q`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add hooks/scripts/tests/test_orc_code_skill.py skills/orc-code/SKILL.md
git commit -m "/orc-code refactor: quality mode is the dogfood procedure, written down

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Migration mode — the wrapper plus Orclab's three additions, and "found is not installed"

**Files:**
- Modify: `skills/orc-code/SKILL.md` — `### Migration mode` (the moved handover steps) and `## Plugin-Discovery Procedure`
- Modify: `hooks/scripts/tests/test_orc_code_skill.py`
- Read: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/code-modernization/commands/modernize-{preflight,brief,transform,uplift,status}.md` — confirm the argument shapes named below are still what the files say (`<system-dir> [target-stack]` for preflight and brief; `<system-dir> <module> <target-stack>` for transform; `<system-dir> <source-version> <target-version> [project-pattern]` for uplift; the `legacy/$1`, `analysis/$1/`, `modernized/$1/` layout). If any differs, correct the spec §3 first, then write the skill to match the files.

**Interfaces:**
- Consumes: `### Migration mode` heading (Task 2); spec §3(d) as corrected by Task 1.
- Produces: the phrases Task 7's live run follows literally; the "available, not installed" wording Task 7 exercises with the plugin uninstalled.

- [ ] **Step 1: Add the failing tests**

```python
def test_migration_mode_adds_stack_tests_worktree_and_gate():
    m = TEXT[TEXT.index("### Migration mode"):TEXT.index("## Plugin-Discovery Procedure")]
    assert "No migration has gone through this yet; the first one corrects it." in m
    for phrase in ["Defaults Table", "stack-*", "[target-stack]",
                   "characterization", "/orc-test analyze", "/orc-test generate",
                   "before any `modernize-", "legacy/", "analysis/", "modernized/",
                   "worktree", "/orc-test run", "no lower than", "modernize-status",
                   "modernize-preflight"]:
        assert phrase in m, phrase


def test_discovery_tells_available_from_installed():
    d = TEXT[TEXT.index("## Plugin-Discovery Procedure"):TEXT.index("## Defaults Table")]
    for phrase in ["installed_plugins.json", "available, not installed",
                   "claude plugin install code-modernization@claude-plugins-official",
                   "fresh session"]:
        assert phrase in d, phrase
```

- [ ] **Step 2: Run them to see them fail**

Run: `python3 -m pytest hooks/scripts/tests/test_orc_code_skill.py -q -k "migration or discovery"`
Expected: both FAIL.

- [ ] **Step 3: Write the Migration mode section**

Replace everything under `### Migration mode` (the placeholder line and the three moved handover steps) with:

```
No migration has gone through this yet; the first one corrects it.

The engine is Anthropic's `code-modernization` plugin — its preflight → assess → map →
extract-rules → brief → (transform per module | uplift for a same-stack version bump) → harden
→ status pipeline and its specialist agents. This flow wraps it rather than reimplementing any
of it, and adds the three things it does not know about: which stack Orclab would choose, that
"still works" has to be provable, and that a project is a repository rather than a `legacy/`
subtree.

1. **Find the plugin** with the Plugin-Discovery Procedure below. If it is *not installed* —
   including the case where a marketplace clone holds a copy — stop with the install command
   the procedure gives. Do not follow a marketplace copy's commands: they spawn the plugin's own
   subagents (`test-engineer`, `architecture-critic`, …), which exist only once it is installed,
   and the run would degrade silently at the first spawn.
2. **Decide the target the way a new project is decided.** Ask the New-Project Flow's two
   questions — type, and the platforms ticked — for the *target*, and take the Defaults Table's
   row. That row's `stack-*` skill is the migration's constraint: its toolchain versions, its
   project layout, its `## Lint — where code-discipline lands` config, its store-rules table.
   Read it in full now. If the row is a stub or there is no row, `CLAUDE.md`'s "Before the first
   project builds on a stack … Orclab has never met" applies: the research comes first, and this
   flow stops until it exists.
3. **Tests before any `modernize-*` command runs.** `/orc-test analyze` on the source project.
   If the suite is red, a language has no runnable suite, or coverage is under the gate, the
   first work is `/orc-test generate` *on the old code* — characterization tests that pin what
   it does today, under `test-discipline`. The plugin's `extract-rules` will document the
   business rules; these tests are what make them executable, and without them the gate in step
   6 has nothing to measure. Record the baseline: coverage, TCE, test count. This step is not
   optional and it is not the plugin's.
4. **Lay out a worktree the plugin's way.** Every `modernize-*` command addresses the source as
   `legacy/<name>` and writes to `analysis/<name>/` and `modernized/<name>/`. Create a worktree
   for the branch (`superpowers:using-git-worktrees`), and inside it a scratch directory —
   `.orclab/modernize/` — holding `legacy/<name>` as a symlink to the worktree root, so the
   plugin reads the real files and its `analysis/` and `modernized/` land under `.orclab/` where
   nothing else looks. Run every plugin command from `.orclab/modernize/`.
5. **Hand over, with the stack as the brief's constraint.** `modernize-status <name>` first; if
   it reports prior work, continue from there, otherwise `modernize-preflight <name>
   <target-stack>` and on through the plugin's own sequence, reading each command file in full
   from the plugin's directory and following it exactly as if the user had typed it.
   `<target-stack>` — for `preflight`, `brief` and `transform` — is the stack skill's own
   naming, in one line: e.g. `Kotlin + Jetpack Compose, per Orclab's stack-android-native: AGP
   9.x, compileSdk 36, app/build.gradle.kts layout`. When `brief` produces its target
   architecture, check it against the stack skill's layout section before the user approves it,
   and correct the brief, not the result, if it lands elsewhere. A same-stack version bump goes
   through `modernize-uplift <name> <source-version> <target-version>` instead of `transform`.
6. **Exit gate.** Copy `modernized/<name>/` back over the worktree as the branch's content, and
   the brief and rule catalogue from `analysis/<name>/` into `docs/`. Then `/orc-test run` must
   be green on the migrated code, and `/orc-test analyze` must report coverage and TCE **no
   lower than** step 3's baseline. If either fails, the migration is not done: say which, and
   what the plugin's `status` shows, and stop. "Done" is not said before this gate.
7. **Report** in reader terms: what moved, what the old suite proved, the numbers before and
   after, and what `harden` found.
```

- [ ] **Step 4: Rewrite the Plugin-Discovery Procedure's step 4 and add step 5**

Replace step 4 (`If no match is found under either root, the plugin is not installed.`) with:

```
4. **Found is not installed.** A match whose root is under `~/.claude/plugins/marketplaces/` is
   a marketplace *copy*; the plugin is installed only if its name appears in
   `~/.claude/plugins/installed_plugins.json` (a `<plugin>@<marketplace>` key). Read that file.
   A copy with no entry is *available, not installed* — its command files can be read, but the
   agents they spawn are not registered, so treat it as not installed.
5. If no match is found, or the match is available but not installed, stop and tell the user
   plainly, with the command: `claude plugin install code-modernization@claude-plugins-official`
   (or the plugin's own name and marketplace) — and that a **fresh session** is needed after
   installing; a plugin installed mid-conversation is not visible to the session that installed
   it (`CLAUDE.md`, marketplace gotcha 4, confirmed on both Desktop and the CLI).
```

- [ ] **Step 5: Run the tests to see them pass**

Run: `python3 -m pytest hooks/scripts/tests/test_orc_code_skill.py -q`
Expected: `5 passed`.

- [ ] **Step 6: Exercise the "available, not installed" branch by hand**

With the plugin not installed (`grep code-modernization ~/.claude/plugins/installed_plugins.json` prints nothing), follow the Plugin-Discovery Procedure as written for `code-modernization`. Confirm: the marketplace copy is found under `marketplaces/claude-plugins-official/plugins/`, step 4 classifies it as available-not-installed, step 5's message is what the flow would print. Note the three paths and the outcome in the commit message.

- [ ] **Step 7: Commit**

```bash
git add hooks/scripts/tests/test_orc_code_skill.py skills/orc-code/SKILL.md
git commit -m "/orc-code refactor: migration mode wraps code-modernization with Orclab's stack, tests-first, a worktree and an exit gate; found is not installed

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: `orc-test` and `code-discipline` point at the mode that uses them

**Files:**
- Modify: `skills/orc-test/SKILL.md` — under `## generate — repair what \`analyze\` found`, after the "When done writing" paragraph
- Modify: `skills/code-discipline/SKILL.md` — `## What this is not`, the "Not enforced by this file" bullet
- Modify: `hooks/scripts/tests/test_orc_test_skill.py` (add one phrase to `test_every_rule_the_spec_names_is_stated`'s list) and `hooks/scripts/tests/test_orc_code_skill.py`

**Interfaces:**
- Consumes: the mode names from Task 2.

- [ ] **Step 1: Add the failing assertions**

In `test_orc_test_skill.py`, add `"characterization tests"` to the phrase list of `test_every_rule_the_spec_names_is_stated`. In `test_orc_code_skill.py`, add:

```python
def test_code_discipline_names_the_quality_mode():
    cd = (ROOT / "skills" / "code-discipline" / "SKILL.md").read_text()
    assert "`/orc-code refactor`'s quality mode" in cd
```

- [ ] **Step 2: Run to see them fail**

Run: `python3 -m pytest hooks/scripts/tests/test_orc_test_skill.py hooks/scripts/tests/test_orc_code_skill.py -q`
Expected: two FAIL.

- [ ] **Step 3: Write the two paragraphs**

In `orc-test`'s `## generate` section, after the "When done writing" paragraph, add:

```
**`generate` is also the first step of a migration.** `/orc-code refactor`'s migration mode
runs `analyze` on the *old* code before any migration command, and where the suite is red,
absent or under the gate, runs `generate` there first — characterization tests that pin what
the code does today, so the migrated code can be measured against them. The same `analyze` is
that mode's exit gate: coverage and TCE no lower than the baseline, on the new code.
```

In `code-discipline`'s "Not enforced by this file" bullet, append the sentence: `Bringing an *existing* codebase up to these rules is `/orc-code refactor`'s quality mode — the same config, the suite green after every file.`

- [ ] **Step 4: Run to see them pass**

Run: `python3 -m pytest hooks/scripts/tests/ -q`
Expected: all pass (previously 103 + this plan's 6).

- [ ] **Step 5: Commit**

```bash
git add skills/orc-test/SKILL.md skills/code-discipline/SKILL.md hooks/scripts/tests/
git commit -m "orc-test and code-discipline point at /orc-code refactor's modes

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Quality mode, run once for real, through the skill as written

**Files:**
- Read and follow: `skills/orc-code/SKILL.md` `### Quality mode`
- Modify: `skills/orc-code/SKILL.md` (only if the run contradicts it), `BACKLOG.md` (a note on #41 with the numbers)

**Interfaces:**
- Consumes: Task 3's procedure.

The subject is a **scratch clone of Orcshot** — `git clone ~/projects/orcshot /tmp/claude-1000/<scratchpad>/orcshot-quality` — never the real checkout and never pushed: `CLAUDE.md`'s dogfooding rule keeps a consuming project's real actions out of an Orclab-centred session, and a scratch clone is how the procedure gets exercised without one. Orcshot is Python (PySide6, `stack-python-desktop`) with a real suite.

- [ ] **Step 1: Clone, and confirm the suite is green before anything**

```bash
S=/tmp/claude-1000/-home-direflail-projects-orclab/01dd085c-45dd-49a1-84f3-3db02c08a974/scratchpad
git clone -q ~/projects/orcshot $S/orcshot-quality
python3 skills/orc-test/scripts/run.py --cwd $S/orcshot-quality run
```
Expected: `Python ✓`. If red, stop: quality mode's own step 1 of `generate` says a red suite is fixed first, and that is Orcshot's work, not this task's. Record it on #41 and end the task there.

- [ ] **Step 2: Follow `### Quality mode` literally, from step 1**

Step 1 (config): Orcshot's `pyproject.toml` — does it have `[tool.ruff]`? If not, write `stack-python-desktop`'s block verbatim and commit in the clone. Step 2 (baseline): `ruff check . --statistics` (ruff from the scratch venv: `$S/venv/bin/ruff`; keep the venv *off* `PATH` — with it first, orc-test's subprocess `python3` has no pytest, the 2026-09-13 "8 failed") and `python3 skills/orc-test/scripts/run.py --cwd $S/orcshot-quality analyze`. Write both down. Step 3: safe autofixes, suite, commit; then the rule findings by hand, one function at a time, suite after each file, commit per module; then `generate` per its own rules. Step 4: the second `analyze` and the before → after table.

- [ ] **Step 3: Record what the run contradicted**

Anything the skill text said that did not match what happened — an order that was wrong, a step that needed a substep, a refusal that was too strict or too loose — is corrected in `skills/orc-code/SKILL.md` now, with the reason in the commit. If nothing contradicted it, say so in the commit message; that is a result too.

- [ ] **Step 4: Note on #41**

Append to #41's body a paragraph beginning **Quality mode, first real run (<date>):** the subject (a scratch clone of Orcshot, not pushed), the before → after numbers, how many functions were touched by hand, and what (if anything) the skill text was corrected to say. #41 stays open until Task 8.

- [ ] **Step 5: Commit (Orclab only; the clone is discarded)**

```bash
git add skills/orc-code/SKILL.md BACKLOG.md
git commit -m "v19: quality mode run once for real on a scratch clone of Orcshot

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
rm -rf /tmp/claude-1000/-home-direflail-projects-orclab/01dd085c-45dd-49a1-84f3-3db02c08a974/scratchpad/orcshot-quality
```

---

### Task 7: Migration mode, run once for real — install the plugin, uplift a small real project, correct the prose

**Files:**
- Read and follow: `skills/orc-code/SKILL.md` `### Migration mode` and `## Plugin-Discovery Procedure`
- Modify: `skills/orc-code/SKILL.md` (remove the unbuilt marker; correct what the run contradicted), `docs/superpowers/specs/2026-09-13-orclab-v19-orc-code-refactor-design.md` §3 (same), `BACKLOG.md` (#41 note; #5 note)

**Interfaces:**
- Consumes: Task 4's procedure and its "available, not installed" branch.

**This task needs a fresh session after the install** — a plugin installed mid-conversation is invisible to the session that installed it (`CLAUDE.md`, marketplace gotcha 4). Step 1 is done, then the task is resumed in a new session from Step 2.

The subject: a **small real project with a real suite, taken through a same-stack `uplift`** — the cheapest of the plugin's paths that still exercises assess → brief → a transformation → the exit gate. Use `pallets/itsdangerous` at tag `1.1.0` (2018; pure Python, ~1 k lines, a pytest suite, declares Python 2.7 / 3.4+): clone it into the scratchpad and uplift it to Python 3.13. It is real code with real version deltas (removed stdlib names, `setup.py`-era packaging) and a suite that either passes on 3.13 or says exactly why not. If cloning it is impossible, any project meeting the same description — a runnable suite of at least twenty tests, under two thousand lines, an old runtime floor — substitutes, and the choice is recorded on #41.

- [ ] **Step 1: Confirm the not-installed branch, then install**

Run: `grep -c code-modernization ~/.claude/plugins/installed_plugins.json` → `0`. Following the skill's Migration mode step 1 as written must stop with the install command. Then:

```bash
claude plugin install code-modernization@claude-plugins-official
grep -c code-modernization ~/.claude/plugins/installed_plugins.json
```
Expected: `1`. End this session's part of the task; resume from Step 2 in a fresh session.

- [ ] **Step 2: Clone the subject and take the source baseline (Migration mode step 3)**

```bash
S=/tmp/claude-1000/-home-direflail-projects-orclab/01dd085c-45dd-49a1-84f3-3db02c08a974/scratchpad
git clone -q --branch 1.1.0 https://github.com/pallets/itsdangerous $S/uplift-subject
python3 skills/orc-test/scripts/run.py --cwd $S/uplift-subject run
python3 skills/orc-test/scripts/run.py --cwd $S/uplift-subject analyze
```
Write down: tests green or not on the current Python, coverage, TCE. If the suite does not run at all on the current Python (that is plausible for a 2018 tag), that is itself the migration's first finding — record it, and run the suite under the oldest Python the machine has; if none runs it, `generate` characterization tests per Migration mode step 3 before continuing.

- [ ] **Step 3: Follow Migration mode steps 2, 4, 5 literally**

Target: type "app" (a library counts as an app), scope "Linux" → `stack-python-desktop`; the `<target-stack>` line is that skill's own naming (Python 3.13, `pyproject.toml` with `[project]`, `src/` layout per its layout section). Worktree: the clone is already a scratch checkout, so `.orclab/modernize/legacy/itsdangerous` → symlink to the clone root, and run every plugin command from `.orclab/modernize/`. Then `modernize-status itsdangerous`, `modernize-preflight itsdangerous <target-stack>`, `modernize-assess`, `modernize-brief`, and `modernize-uplift itsdangerous "Python 3.4" "Python 3.13"` — each command file read in full from the *installed* plugin's directory (`~/.claude/plugins/cache/claude-plugins-official/code-modernization/<version>/commands/`) and followed as written. Where a command asks for something the skill did not anticipate (a telemetry source, a build toolchain, a `[project-pattern]`), answer it and write down that it asked.

- [ ] **Step 4: Exit gate (Migration mode step 6)**

Copy `modernized/itsdangerous/` back over the clone's tree; run `python3 skills/orc-test/scripts/run.py --cwd $S/uplift-subject run` and `analyze` under Python 3.13. Record green/red, coverage, TCE against Step 2's baseline. The gate's verdict is the task's headline, whichever way it went.

- [ ] **Step 5: Correct the prose with what the run contradicted, and remove the marker**

In `skills/orc-code/SKILL.md` `### Migration mode`: delete the first line *"No migration has gone through this yet; the first one corrects it."* and replace it with one sentence naming the run: *"Run once for real on <date>: itsdangerous 1.1.0 uplifted to Python 3.13 — see BACKLOG #41."* Then every place the run contradicted the text — the symlink layout, what `brief` needed, whether `uplift` honoured the target-stack line, what `status` reported — is corrected in the skill and in spec §3, each with the reason. If the plugin's layout assumption in step 4 did not survive contact (the spec flagged it as "most likely to need correcting at first real use"), rewrite step 4 to what actually worked.

- [ ] **Step 6: Note on #41 and on #5**

#41: a paragraph beginning **Migration mode, first real run (<date>):** the subject, the plugin version installed, each plugin command run and what it produced, the exit-gate numbers, and what the skill was corrected to say. #5: a paragraph beginning **Note <date> (v19):** what the plugin's `map` and `extract-rules` produced about the legacy system, and whether that covers #5's `/orc-data` ask (it tracks legacy-system facts during refactor work) — a sentence either way. #5 stays open; do not mark its heading.

- [ ] **Step 7: Commit**

```bash
git add skills/orc-code/SKILL.md docs/superpowers/specs/2026-09-13-orclab-v19-orc-code-refactor-design.md BACKLOG.md
git commit -m "v19: migration mode run once for real — itsdangerous 1.1.0 uplifted to 3.13 through code-modernization; prose corrected

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
rm -rf /tmp/claude-1000/-home-direflail-projects-orclab/01dd085c-45dd-49a1-84f3-3db02c08a974/scratchpad/uplift-subject
```

---

### Task 8: Resolve #41, final read

**Files:**
- Modify: `BACKLOG.md` (#41 heading and resolution paragraph, per `backlog-discipline`'s "Resolving an entry")
- Read: `skills/orc-code/SKILL.md` in full; `docs/superpowers/specs/2026-09-13-orclab-v19-orc-code-refactor-design.md`

- [ ] **Step 1: Confirm no placeholder or marker survived**

Run: `grep -n "Task [0-9] fills\|No migration has gone through this yet" skills/orc-code/SKILL.md`
Expected: no output. If anything prints, the task that owned it did not finish — fix that first.

- [ ] **Step 2: Walk the spec's four verification bullets against the skill**

Quality mode verified (Task 6's note on #41 has numbers); migration mode verified once live and the marker removed (Task 7); availability branch confirmed with the plugin uninstalled (Task 4 Step 6 and Task 7 Step 1); `hooks/scripts/tests/` all green — run `python3 -m pytest -q` from the repo root and paste the count.

- [ ] **Step 3: The reader-side pass over the whole Refactor Flow**

Read `## Refactor Flow` top to bottom as someone who has not seen the spec. Every sentence a reader could not act on without opening another file gets the file named; every "it" with no clear referent gets its noun. Fix inline.

- [ ] **Step 4: Resolve #41**

Invoke `orclab:backlog-discipline` and follow "Resolving an entry": append `(RESOLVED <date>)` to #41's heading; append a paragraph beginning **Resolved for real, not just tracked:** naming the spec and plan, the two live runs by their #41 notes, and the one open thread (#5's note from Task 7).

- [ ] **Step 5: Commit**

```bash
git add BACKLOG.md skills/orc-code/SKILL.md
git commit -m "Resolve BACKLOG #41 (v19 shipped): /orc-code refactor has two modes, each run once for real

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

Then tell direflail: the branch is ready for `/orc-version` and `/orc-git merge`, on their word.

---

## Self-review against the spec

- **§1 two modes, one question** → Task 2. **§2 quality procedure, the two refusals, architecture opinions excluded** → Task 3; run for real → Task 6. **§3(a) target from the Defaults Table, stack skill as the brief's constraint** → Task 4 step 2 and 5. **§3(b) tests before migration, exit gate** → Task 4 steps 3 and 6, Task 5's `orc-test` paragraph, Task 7 steps 2 and 4. **§3(c) worktree laid out the plugin's way** → Task 4 step 4; corrected by Task 7 step 5 if it did not survive. **§3(d) availability, found-is-not-installed** → Task 1 (spec corrected), Task 4 step 4–5 of the discovery procedure, Task 4 Step 6 and Task 7 Step 1 (exercised uninstalled), Task 7 (the live run). **§4 not built** → no task creates a command or copies plugin content; #5 gets a note, not a build (Task 7 Step 6). **"What changes, by file"** → `orc-code` (Tasks 2–4), `orc-test` and `code-discipline` (Task 5), `BACKLOG.md` (Tasks 6–8); CHANGELOG and version are `/orc-version`'s, on direflail's word (Task 8's last line). **"How it is verified"** → Tasks 6, 7, 4 Step 6, and the prose tests in every task.
- Placeholder scan: the only "(Task N fills this section.)" lines are written *to be replaced* by Tasks 3 and 4, and Task 8 Step 1 greps that they are gone.
- Names used across tasks: `### Which mode`, `### Quality mode`, `### Migration mode`, `## Plugin-Discovery Procedure`, `## Lint — where code-discipline lands`, `.orclab/modernize/`, `legacy/<name>`, `analysis/<name>/`, `modernized/<name>/`, `installed_plugins.json`, test file `hooks/scripts/tests/test_orc_code_skill.py`. Checked consistent between the tests in Tasks 2–5 and the prose they pin.
