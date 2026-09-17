# Orclab v21: `/orc-git` runs `/orc-test` before anything reaches GitHub

**Status:** design, approved in conversation 2026-09-15 (direflail: "approved as is, write the
spec"). The design was settled in two steps that day: the shape ("coverage before push, analyze
before release") first, then the prerequisite direflail set before building it — "we need to
get orclab up to 80/70 first" — which landed as commits `28f9ae4`, `3383b5d`, `dddf3d3` and
`788aa67` (every Orclab suite measured, all six over 70% TCE, whole project 92.9% coverage).

## The problem

direflail, 2026-09-15: *"any time the user is going to push to github, /orc-test runs and makes
sure the tests are 80% covered and that the test quality is high."*

Three `/orc-git` subcommands push: `push`, `commit-push`/`cp`, and `release` (its step 4 runs
`git push origin HEAD` and `git push origin <tag>`). Today none of them runs a test. `merge` is
the one subcommand that does — its step 3 runs `/orc-test run` on the branch before merging and
again after — and it is the pattern to copy: the gate is prose inside the subcommand's own
steps, not a hook (BACKLOG #31 records that the hooks interface has allow/deny and no "ask",
and a gate that stops with a report is a skill's job).

`/orc-test` has two levels that map to the two halves of the request, and they cost very
different amounts (`skills/orc-test/SKILL.md`, `languages/python.md`):

- `coverage` — runs every suite and holds 80% line coverage. One test run per language.
- `analyze` — `coverage` plus mutation testing (TCE at 70%), which is what "test quality" means
  in Orclab's vocabulary. Slow: ~45 minutes on Orcshot's 26k mutants, minutes on each of
  Orclab's own suites.

## What is decided

### 1. Where the gate sits

Inside each pushing subcommand's own numbered steps, after the check that there is something to
push and before the `git push` itself:

- **`push`**: a new step between today's step 2 ("is the branch ahead of its upstream? if not,
  stop") and step 3 (the push). Nothing runs when there is nothing to push.
- **`commit-push` / `cp`**: inherits it, because `cp` is "the full `commit` behavior, then the
  full `push` behavior". The commit happens first; the gate runs on the committed tree; a failing
  gate leaves the commit made and unpushed, and the report says exactly that — "committed
  `abc123`; not pushed: coverage 71% (min 80)".
- **`release`**: a new step between step 3 ("the tag exists locally") and step 4 (the pushes).
- **`merge`**: unchanged. It does not push, and it already runs the suite twice.

### 2. Which check

| Subcommand | Command | Holds |
|---|---|---|
| `push`, `cp` | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/orc-test/scripts/run.py" --cwd <repo root> coverage` | tests green, 80% coverage per language |
| `release` | `… analyze` | the above, plus 70% TCE and the test lint |

`coverage` runs the tests itself (a red suite is a failed gate — `cli.py` line 141–143: a
suite that fails to run sets `failed`), so no separate `run` step. `release` gets `analyze`
because a release is rare and public, and the minutes it costs are spent on the one push whose
artifact other people download.

Both run against the working tree as it stands, from the repo root. If `git status --porcelain`
is non-empty when a bare `push` runs the gate, the report carries one line saying the tree had
uncommitted changes, since what was measured is then not exactly what was pushed. `cp` has just
committed, so this line is rare there; `release` pushes a tag whose commit is already made, so
the same line applies.

### 3. When the gate fails: stop, and nothing is pushed

`/orc-test` exits non-zero. The subcommand reports `/orc-test`'s own output and stops. What
that output ends with differs by check (`cli.py`): `analyze` (used by `release`) ends with a
`gates failed: …` hand-off line naming what to do — `gates failed: tests — fix the failing
tests first` (`cli.py:261`) or `gates failed: coverage — run \`/orc-test generate\` to
repair`-style (`cli.py:263`). `coverage` (used by `push`/`cp`) has no such line: `cmd_coverage`
(`cli.py:137–151`) prints a `tests failed; coverage not measured` line per failing language, or
a `✗ (min 80)` line with the files under it — the subcommand itself has to say what fixes it.
Three things it does not do:

- **It does not start `/orc-test generate`.** `generate` writes and deletes tests, and
  `orc-test`'s own rule is that it runs on the user's yes or on the user typing it, never on a
  threshold. The gate names it; the user types it.
- **It has no skip flag.** `git push` exists; typing it is the deliberate act of pushing past a
  red gate, and the raw command is Orclab's stated fallback when a shipped command refuses. A
  `--no-test` on the shipped command would be a second way to do the thing the command exists
  not to do.
- **It does not special-case a project with no tests.** `/orc-test` already treats a detected
  language with no tests as `0 tests ✗` — "an empty suite is a failure, not a pass" — so the
  first `/orc-git push` on a testless project refuses and points at `/orc-test generate`.
  Decided by direflail 2026-09-15 with that consequence stated ("approved as is").

### 4. When the gate cannot measure: it says so, and the push goes ahead

`/orc-test` exits 0 whenever no language ends up with a ✓, without that being a gate failure —
and the three ways that happens each print a different line (`cli.py:137–151`), not one shared
"not measurable" line: a missing coverage tool prints `<Lang>: missing <tool> — <install> —
skipped` (`cli.py:51`) and that language is dropped before it runs; a report that never got
produced prints `<Lang> coverage not measurable — <reason>` (`cli.py:146`); no language
detected at all prints `detected: no supported language`, and since no blocks were produced,
`nothing measured` (`cli.py:150`). The push proceeds, and the report carries whichever line
applied. This is `/orc-test`'s existing policy — it never installs a tool and never prints 0%
for "did not measure" — and the gate inherits it rather than inventing a stricter one. A
project that wants the gate to bite installs the tool `/orc-test` names.

Outside a git repository `/orc-test` exits 1 with `error: … is not inside a git repository`;
`push` cannot reach that state (step 1 has already read the current branch), so it needs no
handling.

### 5. What changes, file by file

**`skills/orc-git/SKILL.md`**

- `push`: the new step, with the command, the three outcomes (green → continue; red → report
  and stop; not measurable → report and continue), and the dirty-tree line.
- `commit-push` / `cp`: one sentence under the existing "each half is independently
  conditional" rule: the gate is part of the push half, and a failing gate reports the commit
  as made and unpushed.
- `release`: the new step, `analyze`, same three outcomes.
- The bare-invocation listing: `push` reads `push the current branch, after /orc-test coverage
  passes`; `release` gains `after /orc-test analyze passes`; `cp` unchanged (it says "commit,
  then push", and push now means the gated one).
- "Two families under one name": the left column's "works against any host, or none" stays
  true; add one sentence that `push` now depends on `/orc-test`, which is Orclab's own, not a
  host's.

**`docs/commands/orc-git.md`** — the page a user reads (spec v20; `test_docs.py` holds the five
headings, nothing checks the prose, so this is the item-7 obligation of `CLAUDE.md`'s checklist):

- "What you type": `push` and `release` rows say the test run happens first.
- "What it changes": `push`'s bullet says it runs the project's test suite with coverage
  first; `release`'s says the same with mutation testing, and that this takes minutes.
- "What it will never do without asking": a bullet each — it will never push while the tests
  are red or coverage is under 80%, and never release while mutation testing is under 70% —
  with the "it stops and shows you the report; it never writes tests on its own" sentence, and
  the plain statement that when it cannot measure it says so and pushes anyway.

**`hooks/scripts/tests/test_orc_git_skill.py`** — new, the shape of `test_orc_test_skill.py`:
the `push`, `commit-push` and `release` sections of the skill each name the `/orc-test`
command they run (`coverage` for the first two, `analyze` for the third); `merge` still names
`run`; the bare listing's `push` and `release` lines carry the "after /orc-test" phrase; and
the doc page's "never do" section names both thresholds. A test that pins the sentence, so a
later edit that drops the gate fails a test rather than a reader.

**`CHANGELOG.md`** — the v21 entry, written by `/orc-version` when this is cut.

### 6. What is not in this spec

- Any change to `/orc-test` itself. The gate calls it as it is. The three `/orc-test`
  improvements found while getting Orclab to 80/70 — per-suite detection of a missing
  `[tool.mutmut]`, detecting the conftest-placement and process-group traps, and reporting how
  many mutants no test reached — are direflail's item 2 of the same day and get their own
  spec after this one.
- A `ci` subcommand or workflow. `orc-test`'s "Deferred, by name" still owns that.
- Any change to `merge`.
- A way to push without the gate from inside `/orc-git`. See §3.

## Why not a hook

A `PreToolUse` hook on `git push` would fire on every push from every source, including the raw
`git push` that §3 relies on as the escape, and could only deny — not report and stop with the
suite's output in front of the user, which is the whole value. BACKLOG #31 reached the same
conclusion for the "whose idea was it" rule; the same reasoning holds here.

## Verification

1. `hooks/scripts/tests/test_orc_git_skill.py` green; `test_docs.py` still green (headings
   unchanged).
2. Live, in Orclab itself: `/orc-git push` on a branch with one unpushed commit runs
   `coverage` (~30s), reports 92.9% ✓, pushes. Then, with a test deliberately broken and
   committed on a scratch branch: `/orc-git push` reports the red suite and stops; `git log
   origin/<branch>` shows nothing arrived; `git push` by hand still works.
3. Live: `/orc-git release` on the v21 tag runs `analyze` and reports every suite's TCE
   before the pushes.
