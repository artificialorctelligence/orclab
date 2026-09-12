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

## `run` — does the code work?

`python3 ${CLAUDE_SKILL_DIR}/scripts/run.py run [path]`. One line per language: ✓/✗, counts where
the runner prints a `N passed` summary, seconds. Exit 1 on any failure. `/orc-git merge` calls
this before and after landing a branch.

## `coverage` — how much do the tests exercise?

`... coverage [path]`. Per language: percent, lines, ✓ or ✗ against 80 (or `.orclab/test.yaml`),
then every file under the threshold, worst first — that list is where to go next. The tool's own
HTML report path is printed; per-line detail lives there, not in the summary.

## `analyze` — would the tests notice a defect?

`... analyze [path] [--no-mutation]`. Includes `coverage`. Then mutation testing: the tool plants
one defect at a time (a `<` becomes `<=`, a branch is deleted, a call is removed) and re-runs the
suite; a mutant the suite does not catch *survived*. The share caught is the mutation score —
Test Case Effectiveness, TCE — gated at 70. Then a lint over the test files for the four smells:
no assertion, `sleep`, skipped, duplicate name — where the language's linter has those rules;
`languages/<lang>.md` says which. A language with no test lint of its own (Dart, or
JS/TS without the eslint plugin) reports `lint: not run — <reason>` instead of a count.

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

**Before a whole-project run it says how many files it is about to mutate**, once per language,
and that a first run takes a while (later runs are incremental where the tool supports it). It
does not ask — you typed the command. Give it a path to narrow it — how far a path narrows the
mutation step is per language; `languages/<lang>.md` says. `--no-mutation` skips the
slow step and the report says `TCE skipped` rather than showing a number that is not one.

**When it cannot measure something it says so in words** — no mutation tool for the language,
the tool not installed (with the install line), a tests run that was red. It never prints 0% for
"did not measure". Kotlin without an open-source licence still gets a number, marked approximate
in a `note:` line.

**Hand-off.** If any gate failed, the last line is
`gates failed: … — run /orc-test generate to repair`. `analyze` **offers** `generate`; it
**does not start it**. `generate` writes and deletes tests, so it runs on the user's yes — or on
the user typing it — never on a threshold. The one exception is when `generate` itself called
`analyze` to measure its own work; then the loop rule below applies.

The result is saved to `.orclab/test/analyze.json` for `generate`.

## generate — repair what `analyze` found

This is the one subcommand with no `run.py` code behind it. Writing tests is Claude's work, under
`test-discipline` (the background skill — read it now if you have not this session). `run.py`
feeds the list and measures the result.

**Where it starts.** `.orclab/test/analyze.json` for the same path. If it is missing, or any file
under the path changed after it was written, run `analyze` first. Never guess what is weak.

**Work, in this order:**

1. **Surviving mutants first.** Each one says: "at this file and line, this change went
   unnoticed." Write the test that goes red on exactly that change. `test-discipline` rule 5
   ("prove the test can fail") is free here — the mutant *is* the planted defect; re-run
   `analyze` and confirm it is now killed.
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
- A language detected with no tests → `0 tests ✗`, nothing measured — an empty suite is a
  failure, not a pass.
- Wrong detection → override the command in `.orclab/test.yaml`, or run with `--lang <key>` to
  narrow to one language; the `detected:` line always shows what it saw.
- gdUnit4 exits 100 (failures) / 101 (warnings); both are failures here.

## Deferred, by name

- `ci` — writes a GitHub Actions workflow that runs `run` and `coverage` on every push, so the
  gate holds when nobody is running Orclab. Never mutation (too slow per push), never `generate`
  (nothing that rewrites tests runs unattended). Not built until the four subcommands settle.
- Kotlin via Arcmutate, Dart's `mutation_test`, Swift's Muter: spec'd from research, corrected on
  first real use — each `languages/<lang>.md` carries a "Last real run" line.
- GDScript mutation: no tool exists (BACKLOG entry). `languages/gdscript.md` gets a row if one
  appears.
