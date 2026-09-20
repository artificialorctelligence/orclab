# /orc-test

## What it's for

You want to know whether your project's tests actually pass, how much of the code they exercise,
and whether they'd actually notice a real bug — and, when they're weak, have Orclab write and fix
tests to close the gap. `/orc-test` does all of this across whatever language or languages your
project is written in, without you telling it which.

## What you type

| You type | What it does |
|---|---|
| `/orc-test` (or `/orc-test run`) | Runs every test suite in the project and reports pass or fail |
| `/orc-test coverage` | Reports what percent of the code the tests actually exercise, held to a minimum of 80% |
| `/orc-test audit` | Checks every dependency the project declares against the public list of known vulnerabilities and names any that are affected, with the version that fixes each where the tool reports it |
| `/orc-test analyze` | Runs coverage, then mutation testing — plants a small, deliberate defect in the code and reruns the tests to see whether any of them notice — and reports a score for that, called TCE (Test Case Effectiveness), held to a minimum of 70%, plus a check over the test files themselves for problems like a test with no assertion or one that's silently skipped |
| `/orc-test generate` | Writes and fixes tests to repair whatever the last `analyze` found weak |
| `/orc-test detect` | Lists which languages it found in the project and which command it will use to test each, without running anything |

A defect that a test catches, the run just moves past; one that no test catches is called a
*survivor* — a real gap in what your tests would actually catch in production, and the most useful
thing `analyze` produces.

Add a path after any of these (for example `/orc-test coverage src/billing`) to narrow it to one
part of the project. Put `--cwd <project>` or `--lang <key>` before the subcommand to run against
a different project, or restrict it to one language. A project can also override the 80%/70%
minimums, or name its own test command per language, by writing its own `.orclab/test.yaml` file —
`/orc-test` reads that file if it's there instead of guessing.

It finds the language itself, by looking for each language's own marker file (`package.json` for
JavaScript, `pyproject.toml` for Python, and so on) at the project's root or a couple of folders
down — you never tell it what language the project is in, and a project with more than one
language gets every one of them run.

A project that chose, when it was scaffolded, to keep its toolchain in a container rather than on
this machine has its tests run inside that container — the same commands, one layer over, with
nothing installed here beyond the container engine itself (Podman by default, Docker if that is
what you have). The report's first line says so: `detected: Python (in container)`. To change
that for just this checkout, put either of these in `.orclab/test.yaml`: `container: false` to
run on this machine instead, or `runner: docker` (or `podman`) to pick the engine.

## What it will ask you

Nothing, for `run`, `coverage`, `analyze`, and `detect` — each one runs the moment you type it. A
first `analyze` on a real project takes a while, since planting and testing each defect one at a
time is slow (later runs are faster, since the tool re-checks only what changed since last time,
where it's able to); it tells you how many files it's about to work through before it starts, but
it doesn't stop to ask, because typing the command is already your go-ahead.

For `generate`:
- Before deleting any test, it shows you the full list of what it wants to remove and why, and
  waits for you to say yes — you can strike out individual items to keep them instead. Nothing is
  deleted until you answer.
- After it finishes a round of writing and fixing, it shows you the coverage and TCE numbers
  before and after. If either is still short of its minimum, it asks whether to run another round
  and waits for your answer — it never starts a third round of repairs on its own.

## What it changes

- `run` and `detect`: nothing. They only report back to you.
- `coverage`: writes its report under `.orclab/test/<language>/` — one folder per language found.
- `analyze`: writes those same per-language reports, plus `.orclab/test/analyze.json`, a saved
  record of exactly what it found weak. `generate` reads that file afterward instead of guessing.
- `generate`: writes new test files and, once you've said yes to the deletion list, removes the
  ones on it. Every one of these changes is left **uncommitted** — writing tests and committing
  them are two separate steps, so you get to read the new tests first. Committing them afterward
  is your own step, for example with [`/orc-git commit`](orc-git.md).
- The mutation-testing tool itself also leaves behind its own working files while `analyze` runs —
  for example a `mutants/` folder and a `.coverage` file for a Python project. Orclab doesn't
  create these to track anything; they're the tool's own scratch space, and the recommendation is
  to add them to your project's `.gitignore` so they don't show up as changes in `git status`.

## What it will never do without asking

- It will never run outside a git-tracked project. It says so and stops, rather than trying to
  test whatever it happens to find.
- It will never install a missing testing or mutation tool, or the dependency-audit tool, on your
  behalf — and that includes the container engine itself. If one isn't installed, it names the
  missing tool and the command to install it, and skips just that language — every other
  language it found still runs.
- It will never run a containerised project's tests on this machine instead when the container
  can't be used — no engine installed, or an image that fails to build — it says why and stops
  for that project.
- It will never run git itself — no commits, no branches — no matter which subcommand you run.
- It will never guess which language a project is written in. If it can't find that language's own
  marker file, it leaves that language out rather than assuming.
- It will never show a percentage — for coverage or for TCE — for something it actually couldn't
  measure, for example a missing mutation tool or a test run that came back red. It says in words
  what it couldn't measure instead of showing a misleading 0%.
- `generate` will never run on its own because coverage or TCE fell below its minimum — only
  because you typed the command yourself, or because you answered yes to its "another round?"
  question after a repair pass.
- `generate` is never offered, and doesn't run, when the test suite itself is failing and nothing
  else was found wrong — a failing suite has to be fixed by hand first, since there's nothing
  meaningful yet for it to repair.
- `generate` will never guess what's weak. It always starts from the last `analyze` for that same
  part of the project, re-running `analyze` first if that record is missing or the code has
  changed since — never from a hunch.
- It will never delete a test without showing you the full list first and getting a yes.
- It will never report a language with no tests at all as passing. An empty test suite shows up as
  a failure, not a clean result — having no tests is itself a problem, not something to skip past.
- If running the planted defects during `analyze` somehow leaves one of your project's own
  already-committed files changed (outside its report folders and the mutation tool's own working
  files), it won't score that run at all — it names which files changed instead, so you can fix
  the tests before trusting the number.
