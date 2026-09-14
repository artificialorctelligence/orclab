# Orclab v20: command docs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eleven pages under `docs/commands/`, one per `/orc-*` command, that a person who has never opened a `SKILL.md` can read; a `README.md` that is a front page and links to every one; `/orc-help <command>` showing a page inside Claude; one test that keeps the set complete and the shape fixed.

**Architecture:** Markdown only, plus one pytest file. Each page is written from its command's `SKILL.md` read in full that day, in a fixed five-heading shape, then re-read as a stranger and rewritten. The test (`hooks/scripts/tests/test_docs.py`) is written first and stays green at every commit: it checks the shape of whatever pages exist from Task 1, and gains the completeness assertions (every command has a page; the README links every page) in Task 12, once every page exists. Spec: `docs/superpowers/specs/2026-09-13-orclab-v20-command-docs-design.md` — read it in full before any task.

**Tech Stack:** Markdown; `python3 -m pytest hooks/scripts/tests/test_docs.py -q` from the repo root (the root `pyproject.toml` already collects `hooks/` and puts `hooks/scripts` on the path — no configuration changes).

## Global Constraints

Every task's requirements include these. Copied from the spec and from `CLAUDE.md`.

- **The five headings, as `##`, in this order, and no others** (spec §1): `What it's for` · `What you type` · `What it will ask you` · `What it changes` · `What it will never do without asking`. The test enforces this; a page with a sixth heading or a reordered one fails.
- **A page is a claim about the command** (spec §1; `CLAUDE.md` "show what it rests on"): written from that command's `SKILL.md` read in full on the day, not from memory of it and not from the README paragraph it replaces. Nothing is promised the skill does not carry. If a skill's rule turns out unclear while writing, that is a `/orc-todo add backlog` entry, not an edit to the skill (spec §5).
- **Plain words** (spec §1): a term Orclab coined — *lane*, *ingredient*, *channel*, *gate*, *TCE*, *recipe*, *leaf* — is explained in the sentence where it first appears on that page. No pointer to `CLAUDE.md`, `BACKLOG.md`, a spec or a `SKILL.md`; a page may link to another command's page (`orc-git.md`, relative). No lock/allocator/cursor/frontmatter vocabulary unless the sentence is about what the user sees, and then the effect is named, not the mechanism. Files the command writes are named, because the user will see them in `git status`.
- **The reader's-side pass is a step** (spec §4): after the first draft, read the page as someone who has never opened a `SKILL.md`, and rewrite every sentence they would stumble on. The question, answered yes before the task ends: *could this reader say, in their own words, what the command does, what it will ask, and what it will not do — from this page alone?*
- **Review, two-stage, per page** (spec "How it is verified" 2–3): the spec-compliance reviewer is given the page **alone** and answers the reader's-side question; the second reviewer is given the page **and** the `SKILL.md` and checks "What it will never do without asking" both ways — every rule on the page is in the skill, every refusal in the skill is on the page.
- **One source, two renderings** (spec §3): there is no terminal-shaped copy of any page. `/orc-help <name>` reads the same file GitHub renders.
- **Commit messages** end with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`. Commit per task; do not push — pushing is `/orc-git push`, on direflail's word.
- **The suite is green at every commit.** `python3 -m pytest hooks/ -q` before each commit.

---

### Task 1: The shape test, green on an empty set

**Files:**
- Create: `hooks/scripts/tests/test_docs.py`
- Create: `docs/commands/` (the directory; the first page arrives in Task 2)

**Interfaces:**
- Produces: `HEADINGS`, the list of five heading strings every later task's page must carry verbatim; `PAGES`, the glob every later task's page must land in (`docs/commands/*.md`).

- [ ] **Step 1: Write the test**

```python
# hooks/scripts/tests/test_docs.py
"""The user-facing pages under docs/commands/ (spec: 2026-09-13-orclab-v20-command-docs-design.md).
Shape and presence only; a page saying what its command does today is a discipline, not a test."""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
PAGES = sorted((ROOT / "docs" / "commands").glob("*.md"))
HEADINGS = [
    "## What it's for",
    "## What you type",
    "## What it will ask you",
    "## What it changes",
    "## What it will never do without asking",
]


def _headings(text):
    return [line.rstrip() for line in text.splitlines() if line.startswith("## ")]


def test_every_page_has_exactly_the_five_headings_in_order():
    for page in PAGES:
        assert _headings(page.read_text()) == HEADINGS, page.name


def test_every_page_is_a_command_that_exists():
    for page in PAGES:
        assert (ROOT / "skills" / page.stem / "SKILL.md").is_file(), page.name


def test_no_page_points_the_reader_at_the_workshop():
    for page in PAGES:
        text = page.read_text()
        for banned in ["CLAUDE.md", "BACKLOG.md", "SKILL.md", "docs/superpowers"]:
            assert banned not in text, f"{page.name} mentions {banned}"
```

- [ ] **Step 2: Create the directory and run the test**

```bash
mkdir -p docs/commands
python3 -m pytest hooks/scripts/tests/test_docs.py -q
```
Expected: 3 passed (vacuously — no pages yet). Then prove the shape check can fail: write `docs/commands/orc-nonesuch.md` containing `## Wrong`, run again, expect 2 failures (`headings`, `command that exists`), delete the file, run again, expect 3 passed.

- [ ] **Step 3: Commit**

```bash
git add hooks/scripts/tests/test_docs.py
git commit -m "v20: shape test for docs/commands/ — five headings, a real command, no workshop pointers

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```
(`docs/commands/` is empty and git does not track it; Task 2's page creates it in the tree.)

---

### The page skeleton every page task uses

Every page task below writes this file, with the command's own content under each heading. Copy it exactly; the test checks the headings byte for byte.

```markdown
# /orc-<name>

## What it's for

<One paragraph: the situation you are in when you reach for it.>

## What you type

<The invocation. For a command with subcommands or modes, a table:>

| You type | What it does |
|---|---|
| `/orc-<name> <sub>` | <one sentence> |

## What it will ask you

<The questions, in the order it asks them — or "Nothing.">

## What it changes

<Files it writes, by name. Commands it runs that leave a mark — a commit, a tag, a file under `.orclab/`. What it leaves alone.>

## What it will never do without asking

<The command's own rules, restated in plain words. If a rule turns on whose idea it was, say so the way the skill does: typed by you, it runs; Claude's own idea, it asks.>
```

And every page task has the same six steps. They are written out in Task 2 in full; Tasks 3–11 name only what is specific to that command, and otherwise follow Task 2's steps exactly.

---

### Task 2: `docs/commands/orc-git.md`

**Files:**
- Read in full: `skills/orc-git/SKILL.md`
- Create: `docs/commands/orc-git.md`

**Interfaces:**
- Produces: the first page; the pattern Tasks 3–11 repeat.

What the skill states that the page must carry (found by reading it; these are pointers, not the text): the two families — plain git (`commit`, `push`, `branch`/`switch`, `merge`) and GitHub-only via `gh` (`repo`, `pr`, `release`); the bare-invocation listing of ten subcommands and their aliases (`cp`, `switch`); "Whose idea was it" — `push`, `merge` and `release` run when you typed them and ask first when they were Claude's idea; `commit` stages everything (`git add -A`) and never pauses before committing; `merge` refuses a dirty tree, runs `/orc-test` before and after, deletes the branch with `-d` not `-D`, never resolves conflicts for you; `release` pushes the tag and creates a public GitHub Release; `repo` never silently overwrites a differing `origin`.

- [ ] **Step 1: Read `skills/orc-git/SKILL.md` in full.** Every section, including the subcommand ones you think you know. Note each "never", "ask", "stop", and "refuse" as you go — these are the last heading's content.

- [ ] **Step 2: Write the page** from the skeleton above. "What you type" is a table with one row per subcommand (`repo <url>`, `commit [text]`, `push`, `commit-push [text]` / `cp`, `branch <name>` / `switch`, `merge <branch>`, `pr <id>`, `release [tag]`). "What it changes" names: the commit it makes, the `.orclab/git-repo.json` and `.gitignore` line `repo` writes, the branch `merge` deletes, the tag and Release `release` pushes and creates. "What it will never do without asking" carries the whose-idea rule in the skill's own two cases, `merge`'s refusals, and `repo`'s.

- [ ] **Step 3: The reader's-side pass.** Read the page again as someone who has never opened a `SKILL.md` and does not know what a worktree, a PR, an upstream, or `gh` is. Every sentence they would stop on gets rewritten or gets its term explained where it stands. Answer, honestly: *could this reader say in their own words what `/orc-git` does, what it will ask, and what it will not do — from this page alone?* If no, rewrite until yes.

- [ ] **Step 4: Run the test**

```bash
python3 -m pytest hooks/scripts/tests/test_docs.py -q
```
Expected: 3 passed. A heading typo fails the first test with the page's name.

- [ ] **Step 5: Report** for the reviewers, in reader terms: what the page says the command never does without asking, and where in the skill each of those lives (section names).

- [ ] **Step 6: Commit**

```bash
git add docs/commands/orc-git.md
git commit -m "v20: docs/commands/orc-git.md

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

**Reviewers (both stages, this and every page task):** stage one is given `docs/commands/orc-git.md` alone and answers the reader's-side question — yes or no, and what they stumbled on. Stage two is given the page and `skills/orc-git/SKILL.md` and lists any rule on the page not in the skill, and any refusal in the skill not on the page. Either finding sends the task back.

---

### Task 3: `docs/commands/orc-version.md`

**Files:**
- Read in full: `skills/orc-version/SKILL.md`
- Create: `docs/commands/orc-version.md`

What the skill states that the page must carry: the bare invocation proposes a bump from the commits since the last tag and says why — *"the proposal never writes a file"*, it proposes and never decides; the absolute-set and increment forms (`major`/`minor`/`patch`, `X.Y.Z`); the changelog step drafts an entry and pauses for you to edit it; the version files it edits — `CHANGELOG.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `pyproject.toml`, `debian/changelog`, a `*.metainfo.xml`/`*.appdata.xml` at the root — and that a project with none of them gets the changelog and tag only; the commit and the **local** tag; `--no-commit`; it never pushes, never publishes, and `release` has moved to `/orc-git release`. Where the skill says how the current version is found when `plugin.json` and the newest tag disagree, the page says which wins.

Steps 1–6 as Task 2, for this command; the commit message is `v20: docs/commands/orc-version.md`.

---

### Task 4: `docs/commands/orc-todo.md`

**Files:**
- Read in full: `skills/orc-todo/SKILL.md`
- Create: `docs/commands/orc-todo.md`

What the skill states that the page must carry: the twelve subcommands in its table (`list`, `show`, `add`, `remove`, `lane list/create/modify/delete/current`, `lock status/clear`); `add` reads the body from what you pipe in, refuses an empty one, and **never commits** — committing is your step; `remove` never renumbers and a number is never reused, so a gap is a record, not a mistake; a lane (say what one is: a named, ordered list of the specs or plans to work through) refuses an item with no spec or plan and says which; a backlog entry lands in the main checkout's `BACKLOG.md` even from a worktree, a verification scenario in the checkout you ran it from; `lock clear` is for a lock you have looked at and judged stale, never a reflex; outside a git repository or without a `BACKLOG.md` it says so and creates nothing.

Steps 1–6 as Task 2; commit message `v20: docs/commands/orc-todo.md`.

---

### Task 5: `docs/commands/orc-test.md`

**Files:**
- Read in full: `skills/orc-test/SKILL.md` (194 lines) and the "What it never does" section twice
- Create: `docs/commands/orc-test.md`

What the skill states that the page must carry: the four subcommands — `run` (do the tests pass), `coverage` (how much of the code they exercise, held to 80%), `analyze` (would they notice a defect — mutation testing, explained in one sentence as "plants a small defect and checks a test fails"; the score is called TCE, held to 70%), `generate` (repairs what `analyze` found); it finds every language in the project on its own; the whole of "What it never does"; `generate` runs only when you type it and never on a threshold, offers a second round and never starts a third on its own, and is not offered on a red suite; what it writes — `.orclab/test/` (the reports, `analyze.json`) and, for `generate`, test files it leaves **uncommitted**; the mutation tool's own scratch (`mutants/`, `.coverage`) and the note to `.gitignore` it; a first `analyze` on a real project takes a while.

Steps 1–6 as Task 2; commit message `v20: docs/commands/orc-test.md`.

---

### Task 6: `docs/commands/orc-code.md`

**Files:**
- Read in full: `skills/orc-code/SKILL.md` (335 lines — the longest; read all of it, including the Defaults Table and the Plugin-Discovery Procedure)
- Create: `docs/commands/orc-code.md`

What the skill states that the page must carry: the three flows and how it picks one — new project, add to an existing one, refactor — and that it never guesses which from the filesystem; the new-project questions in order (name; app or game; which platforms; starting point) and that it proposes a stack from the answers and waits for a yes; refactor's two modes — a quality pass (same language, brought up to the house rules with the suite green throughout) and a migration (a different language, framework or version, using Anthropic's `code-modernization` plugin, which it wraps and which must be installed — say what happens if it is not); the modes' own stops — the quality pass never uses unsafe autofixes, the migration has an exit gate (tests green, coverage and TCE no lower than before) before it says "done" and stops at the plugin's own approval points; what it writes — the scaffolded project, and for a migration `.orclab/modernize/`, a worktree or branch, and the brief and catalogues copied into `docs/`; it wraps `feature-dev` and `code-modernization` and tells you plainly when one is not installed.

"What you type" is a table of the three entry forms (`/orc-code` bare, `/orc-code <description>`, `/orc-code refactor [what]`) and the two refactor modes.

Steps 1–6 as Task 2; commit message `v20: docs/commands/orc-code.md`.

---

### Task 7: `docs/commands/orc-package.md`

**Files:**
- Read in full: `skills/orc-package/SKILL.md`
- Create: `docs/commands/orc-package.md`

What the skill states that the page must carry: what an ingredient is, in the sentence it first appears (the reusable, written-down knowledge of how to set a project up for one distribution channel — a PPA, a store, a registry); which ship — Launchpad PPA, Snap Store, Flathub, Google Play, App Store — and that each says in its first paragraph whether a real release has gone through it; it asks you for the ingredient's inputs and never guesses a value; it runs only the ingredient's **checks** and **never performs the setup** — creating the account, registering a key, authorising anything is yours; what it writes — `.orclab/publish/channels.yaml`, `distro.yaml`, `RELEASING.md` — by **merging, never overwriting**; machine-local config's three rules; never writes a credential; for a channel it does not ship, it offers to **capture** one into your own project's config directory and never fails silently or invents one.

Steps 1–6 as Task 2; commit message `v20: docs/commands/orc-package.md`.

---

### Task 8: `docs/commands/orc-publish.md`

**Files:**
- Read in full: `skills/orc-publish/SKILL.md` (248 lines)
- Create: `docs/commands/orc-publish.md`

What the skill states that the page must carry: it pushes built artifacts to the channels the project itself configured in `.orclab/publish/channels.yaml` and `distro.yaml` (say what a channel and a leaf are where they first appear); it **always resolves in dry-run first**, shows you the exact list of what would be published where, and needs an explicit go-ahead **for that specific list** — never straight to execution; each leaf's outcome is reported as it really was — accepted, refused, failed with the real error, timed out, not attempted — and a failure is never paraphrased away nor success claimed for something that did not land; `--metrics` reads each channel's own download numbers; `--confirm` checks whether an asynchronous publish actually landed; with no publish configuration it says so and stops. It ships with `disable-model-invocation: true` — on the page, say the effect: Claude never runs this on its own; only you typing it, or a release process that names it, reaches it.

Steps 1–6 as Task 2; commit message `v20: docs/commands/orc-publish.md`.

---

### Task 9: `docs/commands/orc-release.md`

**Files:**
- Read in full: `skills/orc-release/SKILL.md` (224 lines)
- Create: `docs/commands/orc-release.md`

What the skill states that the page must carry: it drives **your project's own `RELEASING.md`** — it never invents a release process, never invents a step, never reorders one, never widens a step's command beyond what is written; it reads the whole document before acting on any step; it keeps its place across sessions (say what the user sees: `status` tells you where a release stands, `start` begins one, resuming continues from where it stopped); gates halt it; a manual step is yours to do and confirm — it records what you say you did and never marks it complete on its own; `skip` and `abort` and what each leaves behind; version handling delegates to `/orc-version`'s files; what it writes — the version files, `CHANGELOG.md`, and its own state under `.orclab/`. It ships with `disable-model-invocation: true`; say the effect as in Task 8.

Steps 1–6 as Task 2; commit message `v20: docs/commands/orc-release.md`.

---

### Task 10: `docs/commands/orc-reload.md`

**Files:**
- Read in full: `skills/orc-reload/SKILL.md`
- Create: `docs/commands/orc-reload.md`

What the skill states that the page must carry: it is for someone **developing a Claude Code plugin** (any plugin, not only Orclab) who wants a fresh session to pick up their latest changes; it confirms the current directory is a plugin project, finds how the plugin's marketplace is registered (by directory — the live tree — or by GitHub — a cached clone that does not refresh on its own, which it refreshes), reinstalls, and verifies the expected version actually landed; the one thing it cannot do: a reinstall never takes effect in the conversation that ran it — a fresh session is where it shows up, and it tells you so; what it changes — the installed plugin under `~/.claude/plugins/`, nothing in your project.

Steps 1–6 as Task 2; commit message `v20: docs/commands/orc-reload.md`.

---

### Task 11: `/orc-help <command>`, then `docs/commands/orc-help.md` and `orc.md`

**Files:**
- Modify: `skills/orc-help/SKILL.md` — Step 3's format block and a new Step 4
- Modify: `hooks/scripts/tests/test_orc_help_skill.py` — create it (there is none today), in the shape of `test_orc_test_skill.py`
- Create: `docs/commands/orc-help.md`, `docs/commands/orc.md`

**Interfaces:**
- Consumes: the ten pages from Tasks 2–10 (Step 4 reads `docs/commands/<name>.md`).
- Produces: the argument form `/orc-help <name>` that Task 13's verification scenario exercises.

- [ ] **Step 1: Write the prose test first**

```python
# hooks/scripts/tests/test_orc_help_skill.py
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills" / "orc-help" / "SKILL.md").read_text()


def test_step_4_shows_a_command_page_and_the_synopsis_points_at_it():
    for phrase in ["## Step 4", "docs/commands/", "for any command, /orc-help <name>",
                   "There is no `/orc-", "with or without"]:
        assert phrase in TEXT, phrase
```

Run: `python3 -m pytest hooks/scripts/tests/test_orc_help_skill.py -q` — expected: 1 failed.

- [ ] **Step 2: Edit `skills/orc-help/SKILL.md`.** In Step 3's format block, add a last line after the commands list:

```
  for any command, /orc-help <name>
```

Then append Step 4 after Step 3's closing paragraph:

```markdown
## Step 4: Show one command's page, when a name was given

If `$ARGUMENTS` names a command — with or without the leading `/` and the `orc-` prefix, so
`git`, `orc-git` and `/orc-git` all mean the same — skip Step 3's synopsis and instead read
`docs/commands/<name>.md` in the plugin root Step 2 established. Present it in chat in the page's
own order — its five headings, and its table if it has one — the way you would relay any
document to the person in front of you, not as pasted Markdown. There is exactly one copy of
each page and this is it; never summarise from memory of the command instead of reading the
file.

If no such page exists: "There is no `/orc-<name>` command; `/orc-help` lists what exists." —
and stop.
```

Run the test — expected: 1 passed. `skills/orc/SKILL.md` needs no change: it already forwards `$ARGUMENTS` to `orc-help`.

- [ ] **Step 3: Write `docs/commands/orc-help.md`** from the skeleton, from the skill as it now reads: what it's for (find out what Orclab you are running and what it can do); what you type (`/orc-help` — the version and one line per command; `/orc-help <name>` — that command's page); it asks nothing; it changes nothing; it never does anything but read and report. Then `docs/commands/orc.md`:

```markdown
# /orc

## What it's for

`/orc` is the short name for `/orc-help`. Everything on [orc-help.md](orc-help.md) applies.

## What you type

`/orc`, or `/orc <name>` — exactly as you would type `/orc-help`.

## What it will ask you

Nothing.

## What it changes

Nothing.

## What it will never do without asking

It never does anything but read and report.
```

- [ ] **Step 4: The reader's-side pass** on `orc-help.md` (as Task 2 Step 3).

- [ ] **Step 5: Run both tests**

```bash
python3 -m pytest hooks/scripts/tests/test_docs.py hooks/scripts/tests/test_orc_help_skill.py -q
```
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-help/SKILL.md hooks/scripts/tests/test_orc_help_skill.py docs/commands/orc-help.md docs/commands/orc.md
git commit -m "v20: /orc-help <command> shows the command's page; docs/commands/orc-help.md and orc.md

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 12: The README as a front page, and the completeness assertions

**Files:**
- Modify: `README.md` — rewritten top to bottom
- Modify: `hooks/scripts/tests/test_docs.py` — two assertions added

**Interfaces:**
- Consumes: all eleven pages (Tasks 2–11).

- [ ] **Step 1: Add the completeness assertions to `test_docs.py`** and watch them fail against today's README:

```python
def test_every_command_has_a_page():
    commands = sorted(p.parent.name for p in (ROOT / "skills").glob("orc*/SKILL.md"))
    assert [p.stem for p in PAGES] == commands


def test_readme_links_every_page():
    readme = (ROOT / "README.md").read_text()
    for page in PAGES:
        assert f"docs/commands/{page.name}" in readme, page.name
```

Run: `python3 -m pytest hooks/scripts/tests/test_docs.py -q` — expected: `test_readme_links_every_page` fails (eleven names), `test_every_command_has_a_page` passes.

- [ ] **Step 2: List what exists, so the README lists exactly that**

```bash
ls skills/
```
Expected: `backlog-discipline code-discipline currency-discipline environment-registry orc orc-code orc-git orc-help orc-package orc-publish orc-release orc-reload orc-test orc-todo orc-version release-checklist secret-hygiene stack-android-native stack-flutter stack-godot stack-ios-native stack-kotlin-multiplatform stack-python-desktop stack-react-native stack-unity stack-web test-discipline verify-before-asserting whole-process-first`. If the list differs, the README lists what `ls` shows, not this line.

- [ ] **Step 3: Rewrite `README.md`** with exactly the spec's five sections, in this order, and nothing from the old file kept unless it is named here:

```markdown
# Orclab

<Three sentences: a Claude Code plugin; what it gives you — commands for the work around code
(versions, releases, publishing, tests, the backlog) and background knowledge Claude reads on its
own; where it came from — real practice on Orcshot, then on Orclab itself.>

## Installing

    /plugin marketplace add ~/projects/orclab
    /plugin install orclab@orclab

A new install shows up in a fresh session, not the one you ran the install from.

## Commands

One line each, the name linked to its page, one sentence written for this list:

- [/orc-code](docs/commands/orc-code.md) — <sentence>
- [/orc-git](docs/commands/orc-git.md) — <sentence>
- [/orc-help](docs/commands/orc-help.md) — <sentence>; `/orc` is its short name ([orc.md](docs/commands/orc.md))
- [/orc-package](docs/commands/orc-package.md) — <sentence>
- [/orc-publish](docs/commands/orc-publish.md) — <sentence>
- [/orc-release](docs/commands/orc-release.md) — <sentence>
- [/orc-reload](docs/commands/orc-reload.md) — <sentence>
- [/orc-test](docs/commands/orc-test.md) — <sentence>
- [/orc-todo](docs/commands/orc-todo.md) — <sentence>
- [/orc-version](docs/commands/orc-version.md) — <sentence>

Inside Claude, `/orc-help <name>` shows any of these pages.

## What Claude reads on its own

<One line each, grouped. Discipline: backlog-discipline, code-discipline, currency-discipline,
environment-registry, release-checklist, secret-hygiene, test-discipline,
verify-before-asserting, whole-process-first. Stacks: the nine stack-* skills, one line each,
saying when Claude reaches for it. Each sentence is written from that skill's own
`description` field read that day — not from memory.>

## Changing Orclab

<One paragraph: `CLAUDE.md` is the workshop notes for people changing Orclab, `BACKLOG.md` the
open findings, `CHANGELOG.md` what changed release to release, `docs/superpowers/` the design
history, `VERIFICATION.md` the install check. For people changing Orclab, not for users.>
```

Each `<sentence>` for a command is written from that command's page (Tasks 2–11), not from the skill's `description`. Removed and not moved: the v1–v9 status paragraph; "also ships as a matching skill … thin pointer"; "Known gap, now fixed"; every "Ships as a skill only — see `CLAUDE.md` for why"; the `commands/`-removal history.

- [ ] **Step 4: Check the lists both ways, by hand**

```bash
for d in $(ls skills); do grep -q "$d" README.md || echo "missing from README: $d"; done
grep -o '\*\*[a-z-]*\*\*\|`[a-z-]*`' README.md | tr -d '*`' | sort -u | while read n; do [ -d "skills/$n" ] || [ -f "docs/commands/$n.md" ] || echo "in README, not in skills/: $n"; done
```
Expected: nothing printed by the first loop. The second prints file names that are not skills (`CLAUDE.md` and the like) — those are fine; a lower-case hyphenated name that is not a directory under `skills/` is not.

- [ ] **Step 5: The reader's-side pass** on the README, as a stranger deciding whether to install this.

- [ ] **Step 6: Run the whole hooks suite**

```bash
python3 -m pytest hooks/ -q
```
Expected: all passed, including the two new assertions.

- [ ] **Step 7: Commit**

```bash
git add README.md hooks/scripts/tests/test_docs.py
git commit -m "v20: README is a front page; every command has a page and the README links every page

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 13: The rule that keeps pages true, the verification scenario, and #32 resolved

**Files:**
- Modify: `CLAUDE.md` — "Checklist for designing a new `/orc-*` thing", item 7
- Modify: `VERIFICATION.md` — Scenario 12, new steps
- Modify: `BACKLOG.md` — #32 resolved (via `backlog-discipline`'s "Resolving an entry": marker on the title line, paragraph below the original text)

- [ ] **Step 1: Append item 7 to the checklist in `CLAUDE.md`**, after item 6:

```markdown
7. Does it have `docs/commands/<name>.md`, and does a change to what an existing command asks,
   changes, or refuses touch its page in the same commit? The page is the one a user reads
   (spec `2026-09-13-orclab-v20-command-docs-design.md`); `hooks/scripts/tests/test_docs.py`
   fails a command with no page and a page with the wrong headings, and nothing mechanical
   checks the prose — that is this item.
```

- [ ] **Step 2: Extend `VERIFICATION.md` Scenario 12** with:

```markdown
7. Run `/orc-help git`, `/orc-help orc-git` and `/orc-help /orc-git`.
8. **Expected:** each presents `docs/commands/orc-git.md` — its five headings and its subcommand
   table — in chat, not the bare synopsis.
9. Run `/orc-help nonesuch`.
10. **Expected:** "There is no `/orc-nonesuch` command; `/orc-help` lists what exists." and nothing
    else.
11. Run `/orc-help` bare.
12. **Expected:** the synopsis ends with `for any command, /orc-help <name>`.
```

- [ ] **Step 3: Resolve #32.** Add ` (RESOLVED 2026-09-13)` to its title line, and below its original text:

```markdown
**Resolved for real, not just tracked** (2026-09-13, v20): eleven pages under `docs/commands/`,
one per `skills/orc*/SKILL.md`, each with the same five headings (what it's for, what you type,
what it will ask you, what it changes, what it will never do without asking), each written from
its skill read in full that day and then re-read as someone who has never opened a `SKILL.md`;
each reviewed twice — once by a reader given the page alone, once against the skill for the
"never does" section both ways. `README.md` rewritten as a front page listing and linking every
page, every discipline skill and every stack that exists (checked both ways against `ls
skills/`). `/orc-help <name>` shows a page inside Claude from the same file GitHub renders — one
source, no second copy. `hooks/scripts/tests/test_docs.py` holds the set complete and the shape
fixed; `CLAUDE.md`'s design checklist item 7 carries the rule that a command change touches its
page. Spec: `docs/superpowers/specs/2026-09-13-orclab-v20-command-docs-design.md`.
```

- [ ] **Step 4: Run everything and commit**

```bash
python3 -m pytest hooks/ -q
git add CLAUDE.md VERIFICATION.md BACKLOG.md
git commit -m "v20: checklist item 7 (a command change touches its page), Scenario 12 steps 7-12, BACKLOG #32 resolved

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 14: Version, reload, and the live check — direflail's steps

This task is run by direflail, or by Claude on direflail's word, because each step is one the memory rules reserve: `/orc-version` is the shipped command for a bump, `/orc-reload` for the reinstall, and the check needs a fresh session.

- [ ] **Step 1:** `/orc-version minor` → 0.20.0, changelog entry drafted from the commits above.
- [ ] **Step 2:** `/orc-reload`, then a **new** session.
- [ ] **Step 3:** In the new session, run `VERIFICATION.md` Scenario 12 steps 7–12. Any expected line that does not appear is a defect in `skills/orc-help/SKILL.md`'s Step 4, fixed and re-checked before the version is pushed.
- [ ] **Step 4:** `/orc-git push` and `/orc-git release`, on direflail's word.
