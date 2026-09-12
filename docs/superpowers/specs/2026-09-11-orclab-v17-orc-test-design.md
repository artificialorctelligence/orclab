# Orclab v17: `/orc-test` and `test-discipline` — tests that are proven to catch something

**Status:** design, approved 2026-09-11.

## The problem

Orclab has a rule for *when* tests get written — `superpowers:test-driven-development`, which every
session loads — and a command that *runs* them before a merge (`/orc-git merge`, step 3). It has
nothing that says what a good test looks like, nothing that measures whether a green suite would
actually notice a defect, and nothing that repairs a suite once that measurement comes back bad.

Coverage alone does not answer the second question. A test that calls a function and asserts
nothing scores 100% on lines and catches nothing. The measurement that does answer it is
mutation testing — plant a defect, run the suite, see whether it goes red — which is the
automated form of Test Case Effectiveness (TCE): of the defects that existed, how many did the
tests catch. Done by a tool, the planted defects *are* the mutants, so TCE and mutation score are
one number.

direflail asked (2026-09-11) for two things: a set of principles every test written under Orclab
follows, and a `/orc-test` command that runs, measures, and repairs across every language a
project contains. This spec is both.

## What already covered parts of this

Searched, per CLAUDE.md's rule, before designing: all 22 `skills/*/SKILL.md`, `CLAUDE.md`,
`BACKLOG.md`, `hooks/scripts/`, `skills/*/scripts/`, and every spec under `docs/superpowers/`.

- **TDD** — `superpowers:test-driven-development`. Not duplicated; `test-discipline` points at it.
- **Running every suite in the repo** — half exists in `/orc-git merge` step 3
  (`skills/orc-git/SKILL.md:178`), a loop over Orclab's Python suites with a prose fallback for
  other projects. That loop moves into `/orc-test`, and merge calls it.
- **Per-language test tooling** — the five stack skills carry a Testing row each. Per BACKLOG #33
  stack knowledge lives there; but test tooling is per-*language*, not per-stack (Python desktop
  and Python web both run pytest), and Python, JS, Java and C# have no stack skill (BACKLOG #4).
  So this spec adds a third box beside #33's two: `skills/orc-test/languages/<lang>.md`, one per
  language, which stack skills' Testing rows point at.
- **"Intentionally introduce defects to verify the tests fail"** — is mutation testing by hand.
  `test-discipline` rule 5 and `/orc-test analyze` are the same idea at two speeds.
- **Coverage thresholds, mocking rules, synthetic data, test lint** — nothing. Genuine gap.

## Two components

### 1. `test-discipline` — the background skill

`skills/test-discipline/SKILL.md`, `user-invocable: false`. Not a command. Claude reads it whenever
it is about to write or change a test — inside `/orc-code`, inside a subagent executing a plan,
inside a bug fix. Same shape as `secret-hygiene`.

Its rules, in order:

1. **Know what you are testing before you write.** The code under test is open; the project's
   framework is known (from `languages/<lang>.md`); the scenarios that matter are listed before
   any test exists — empty and null inputs, a large input, the async path, the error path.
2. **TDD.** State the expected behaviour in one plain sentence, write the test, watch it fail,
   then write the code. This *points at* `superpowers:test-driven-development`; it does not
   restate it. One law, not two.
3. **Realistic data.** Test data that looks like production, including the edge cases the code's
   shape alone would not suggest. Not `foo`, `bar`, `1`, `2`.
4. **Isolation.** Anything that leaves the process — a database, an HTTP call, the clock, the
   filesystem — is mocked, so a test never fails because of the network or leftover state.
5. **Prove the test can fail.** After writing it, break the code on purpose once and confirm the
   test goes red, then revert. This is stated as a step with an output — "changed X, the test
   failed with Y, reverted" — not as advice, because it doubles the cost of every test and is the
   rule most tempting to skip. A test that cannot fail is the worst kind of debt.
6. **80% line coverage** on the code the change touches, checked before saying "done".
   `/orc-test coverage <path>` is how.

### 2. `/orc-test` — the command

`skills/orc-test/SKILL.md`, default-invocable. `run`, `coverage` and `analyze` only read; the one
subcommand that writes, `generate`, carries the "whose idea was it" rule inside itself (below)
rather than a skill-wide `disable-model-invocation`, which would hide `run` from "run the tests" —
the case CLAUDE.md records for `/orc-git`.

Every subcommand runs as `python3 ${CLAUDE_SKILL_DIR}/scripts/run.py <args>`, prints every
external command it executes, and takes an optional path to narrow its scope.

#### Language detection

A project answers "which language" on its own; `/orc-test` never asks which stack:

| Marker | Language |
|---|---|
| `pyproject.toml`, `setup.py`, `setup.cfg` | Python |
| `package.json` | JavaScript / TypeScript |
| `pom.xml`, `build.gradle`, `build.gradle.kts` | Java; Kotlin if `.kt` files are present |
| `*.csproj`, `*.sln` | C# |
| `pubspec.yaml` | Dart / Flutter |
| `Package.swift`, `*.xcodeproj` | Swift |
| `project.godot` | GDScript |

A repo can hit several; every hit runs. A project's own declared test command wins over the
default — a `test` script in `package.json`, a `Makefile` target named `test`, a `[tool.pytest]`
section — and `.orclab/test.yaml` can override detection outright. The report always states what
was detected so a wrong guess is visible.

#### `/orc-test` (no subcommand) — does the code work?

Runs each language's test command. One report: per language, passed / failed / duration. Any
failure exits non-zero. A path runs only the tests belonging to that code, via each framework's own
targeting. Does not install a missing tool (names it, prints the install line, skips that
language) and does not touch git.

`/orc-git merge` step 3 changes to call this. Same behaviour, one place.

#### `/orc-test coverage` — how much is exercised?

Runs the tests with coverage on and holds each language to 80% of lines. **The gate is computed
by `run.py` from each tool's report** — lcov for Python, JS, C#, Dart and GDScript; JaCoCo XML for
Java and Kotlin; xccov JSON for Swift — so the per-file worst-first list and the pass/fail come
from one read of one file, and a coverage failure is never confused with a test failure in the exit
code. The tools' own threshold switches (`--cov-fail-under`, jest `coverageThreshold`, JaCoCo
`check`, Kover `verify`, coverlet `/p:Threshold`) are documented in `languages/<lang>.md` for the
deferred `ci` subcommand, which is where a project-side gate belongs. (Amended 2026-09-11 while
planning: the original wording had the tool gate and `run.py` both deciding.)

Report per language: lines covered / total, percentage, pass/fail, then files under threshold
sorted worst first — the list `generate` consumes. Per-line detail stays in the tool's own HTML
report; the summary says where that landed. The gate applies per language, so a well-tested half
cannot hide an untested one. Generated, vendored and test files are excluded by each tool's own
defaults, which the command does not override. Exits non-zero on any language under threshold.

#### `/orc-test analyze` — do the tests actually catch defects?

Includes `coverage`. Per language, in order:

1. Run the tests. Red → stop for that language; a red suite cannot be measured.
2. Coverage, gate 80.
3. Mutation, gate 70. Incremental mode wherever the tool has one (StrykerJS, Pitest,
   Stryker.NET; mutmut keeps a cache). Before a whole-repo first run it says how big the job is —
   the number of source files in scope, since most tools cannot count mutants without generating
   them — then proceeds; the user typed it. A path narrows it. `--no-mutation`
   skips this step and the report says "TCE skipped".
4. Test lint — assertion-free tests, `sleep` in tests, disabled or skipped tests, duplicate test
   names. Through the language's linter where one has those rules; for Python it is a small
   stdlib `ast` scan in `run.py`, because ruff's `PT` rules have no assertion-free check (run
   against one, 2026-09-11: no findings).

Summary:

```
Python     coverage 84%  ✓    TCE 61%  ✗ (min 70)    lint: 3 findings
JS/TS      coverage 71%  ✗    TCE 78%  ✓             lint: 0
GDScript   coverage 92%  ✓    TCE not measurable — no mutation tool exists for GDScript
```

followed, for each failing gate, by the specifics: files under threshold; **surviving mutants**
(file, line, what changed) — the actionable list; lint findings.

When something cannot be measured, the table says so in words, never a fake number. The words
come from `languages/<lang>.md`, which is where a fix lands when a tool changes.

If any gate fails, `analyze` ends by saying which and **offers** to run `generate`. It does not
start it. `generate` writes and deletes tests, so it runs on the user's yes, not on a threshold.
The one exception is when `generate` itself called `analyze` — then `analyze` is reporting back
and the loop rule below applies.

The 70% floor is below the 80% coverage floor on purpose: some mutants are equivalent to the
original code and cannot be killed, so mutation scores run lower than coverage in practice.

#### `/orc-test generate` — repair what `analyze` found

Starts from the most recent `analyze` result for the same path. If none exists, or files changed
since, it runs `analyze` first. It never guesses what is weak.

Work, in priority order, every test written under `test-discipline`:

1. **Surviving mutants.** Each is a concrete defect no test caught; the fix is a test that goes red
   on that change. Rule 5 is free here — the mutant is the planted defect, and re-running the
   mutation on that file confirms the kill.
2. **Uncovered code**, worst file first.
3. **Lint findings.** Give an assertion-free test an assertion, or if it genuinely tests nothing,
   propose deleting it.

**Deletion.** Any test `generate` wants to remove — assertion-free, duplicate, testing code that
no longer exists, permanently skipped — goes on a list shown to the user: file, test name, one
line saying why. Nothing is deleted until the user says yes to that list; items can be struck off.

**When done writing**, it runs the tests (all must be green), then runs `analyze` and shows
before → after per number. If a gate still fails it asks: "Coverage 76% (was 61%), TCE 68% (was
44%). Another round?" It never starts a third round on its own.

**Writes uncommitted**, like `/orc-todo add`. Committing is the user's step.

`generate` is not in `run.py`. Writing tests is Claude's work; `run.py` feeds it the list and
measures the result.

## Directory shape

```
skills/test-discipline/
└── SKILL.md
skills/orc-test/
├── SKILL.md
├── languages/
│   ├── python.md  javascript.md  java.md  kotlin.md
│   ├── csharp.md  dart.md  swift.md  gdscript.md
└── scripts/
    ├── run.py        detect · run · coverage · analyze · the lcov reader
    ├── conftest.py
    └── tests/
```

Each `languages/<lang>.md` states: detection markers; test command; coverage command, where its
result lands, and whether the tool gates itself or `run.py` reads lcov; mutation tool, its
incremental switch and install line; lint and its test rules; caveats; a *researched-on* date and
a *last real run* line, per #33's pattern.

`.orclab/test.yaml`, optional and project-owned: `coverage: 80`, `tce: 70`, per-language test
command overrides.

## The eight languages, as researched 2026-09-11

Every version was read from the live registry or GitHub releases on that date. **Maven Central's
search API is stale** (it reported Pitest 1.19.1; GitHub releases showed 1.30.0) — the JVM files
say to check GitHub releases, not `search.maven.org`.

| Language | Runner | Coverage + gate | Mutation (TCE) | Test lint |
|---|---|---|---|---|
| Python | pytest 9.1.1 | pytest-cov 7.1.0, lcov report | mutmut 3.7.0 (most active); cosmic-ray 8.7.0 alternative. **mutmut 3 copies tests into `mutants/`; every later pytest needs `--ignore=mutants`** (hit live 2026-09-11) | own `ast` scan (ruff `PT` has no assertion-free rule) |
| JS/TS | vitest 5.0.0 / jest 30.5.1 | `@vitest/coverage-v8` 5.0.0 / jest `coverageThreshold` | StrykerJS 10.0.0, incremental, runners for both | `@vitest/eslint-plugin` 1.6.27 / `eslint-plugin-jest` 29.16.6 |
| Java | JUnit 5 | JaCoCo 0.8.15 `check` | Pitest 1.30.0 + junit5-plugin, `scmMutationCoverage` incremental | PMD / Error Prone test rules |
| Kotlin | JUnit 5 via Gradle | Kover 0.9.9 `verify` | Pitest on bytecode (junk mutants); Arcmutate Kotlin plugin is clean but **commercial, free for open source** | detekt |
| C# | xUnit / NUnit, `dotnet test` | coverlet 10.0.1 `/p:Threshold`; or Microsoft.Testing.Platform coverage 18.11.2 | Stryker.NET 5.0.0 (2026-09-11, targets .NET 10; 4.16 for older) | `xunit.analyzers` 2.0.0 |
| Dart/Flutter | `dart test` / `flutter test` (test 1.32.0) | `--coverage` → lcov, `package:coverage` 1.15.1; **no threshold flag** | `mutation_test` 1.8.0 (pub.dev, knows Flutter); `dart_mutant` (Rust, MIT) alternative — both young | `dart analyze` only |
| Swift | Swift Testing / XCTest | `swift test --enable-code-coverage` / `xcodebuild -enableCodeCoverage YES` + `xccov`; **no threshold flag**; Mac required | Muter — active (Jul 2026) but **open bugs #307/#310 report SPM scores stuck at 0%**, no tagged release since 2023 | SwiftLint 0.65.1 |
| GDScript | gdUnit4 6.2.1 CLI / GUT 9.6.1 | nano-coverage — **alpha, build from source**, gdUnit4 hooks, emits lcov; script gate | **none exists** | gdlint (gdtoolkit 4.5.0) |

**Kotlin and the licence.** Arcmutate is free only for open-source projects. `analyze` reads the
project's own licence declaration (`LICENSE`, `pyproject.toml`, `package.json`, `build.gradle`):
a recognised open-source licence allows the plugin; none, or proprietary, falls back to plain
Pitest and the report marks TCE approximate and says why. Nothing new in `.orclab/`; the day a
project closes, the licence file is what changes, and the next run notices. Known edge: a private
repo with an MIT file passes the check — Arcmutate's term means *publicly* open source, and that
stays the user's to keep straight.

## Error handling

One rule: say what, say the command, stop that language, continue the others.

- Tool not installed → name it, print the install line, skip that language.
- Tests red under `analyze` or `generate` → stop; nothing to measure.
- Mutation run interrupted → the incremental file keeps what finished; the next run resumes.
- A language detected with no tests at all → "0 tests, 0% coverage", never a silent pass. An empty
  suite is a finding.
- Wrong detection → `.orclab/test.yaml` override; the report always shows what it detected.

## Testing

`run.py` gets the usual suite, `cd skills/orc-test/scripts && python3 -m pytest tests/ -v`:
detection against fixture trees; the lcov reader against real lcov files; each tool's real output
captured into fixtures and parsed. Following the split BACKLOG #15 settled — unit tests for what is
*true*, hand-run scenarios for what is *readable* — a `VERIFICATION.md` scenario per language runs
against a real project and asks whether the summary reads right. Orclab itself is the Python
scenario from day one, so the mutation tools' first real run is on Orclab's own suites.

## Changes to existing components

- `/orc-git merge` step 3 calls `/orc-test` instead of carrying its own loop.
- Each stack skill's Testing row points at the matching `languages/<lang>.md`.
- BACKLOG #4 gets a note: a new stack skill's Testing row links here rather than restating.
- A new BACKLOG entry records the GDScript mutation gap.

## Deferred, by name

- **`/orc-test ci`** — writes a GitHub Actions workflow running `run` and `coverage`, so the gate
  holds when nobody is running Orclab. Never mutation (too slow per push) and never `generate`
  (nothing that rewrites tests runs unattended). Not built until the four subcommands settle.
- **Kotlin via Arcmutate** — spec'd and gated, not exercised until a Kotlin project exists.
- **Dart's mutation pick** (`mutation_test`) and **Swift's Muter bug** — "corrected on first real
  use", per #33.
- **GDScript mutation** — no tool exists; BACKLOG entry; `languages/gdscript.md` gets a row if one
  appears.

## Decision log

- **Mutation stays inside `analyze` by default**, cost managed by incremental mode, a size
  announcement, and a path argument — not a `--mutation` opt-in flag, because then the default
  `analyze` would report a quality score that is not one. `--no-mutation` exists for the fast pass.
- **No separate "coverage + analyze" subcommand** — `analyze` already includes coverage; the spec
  says so in words so nobody reads it as mutation-only.
- **`analyze` offers `generate`; it does not start it.** Whose-idea-was-it rule.
- **Two `analyze` runs per `generate`, then ask.** Never an endless loop.
- **Deletions are a list the user approves**, never silent.
- **Language files, not stack files, hold tooling** — a third box beside #33's channel and stack
  boxes, because test tooling is per-language. Ships without waiting on #4.
- **Thresholds 80 / 70**, overridable per project in `.orclab/test.yaml`.
- **`generate` writes uncommitted.**
