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
of the project (for Python a path narrows what coverage *measures*, not which tests run, unless
the path itself contains tests — `languages/python.md`). Outside a git repository the command
says so and stops.

| Subcommand | Question it answers | Writes |
|---|---|---|
| `run` (or nothing) | Does the code work? | nothing |
| `coverage` | How much of it do the tests exercise? (gate 80%) | `.orclab/test/<lang>/` |
| `audit` | Do the dependencies carry a known vulnerability? (gate: any finding) | nothing |
| `analyze` | Would the tests notice a defect? (coverage + TCE at 70% + lint) | `.orclab/test/<lang>/`, `.orclab/test/analyze.json` |
| `generate` | Fix what `analyze` found | tests, uncommitted — see below |
| `detect` | Which languages, and which test command each | nothing |

Typing `/orc-test` with no subcommand means `run`.

## How it finds the languages

By marker file, at the project root or up to two directories down: `pyproject.toml`/`setup.py`
→ Python; `package.json` → JavaScript/TypeScript; `pom.xml`/`build.gradle` → Java (Kotlin if
`.kt` files exist); `*.csproj` → C#; `pubspec.yaml` → Dart; `Package.swift`/`*.xcodeproj` →
Swift; `project.godot` → GDScript. Every hit runs, from the directory its marker was found in
— a marker under `app/` means that language's tools run with `app/` as their working directory,
and a `path` is made relative to it. The first line of every report is `detected: …`, naming
that directory when it is not the root (`Dart (app/)`), so a wrong guess is visible. What each
language's tools are, and their gotchas, is in `languages/<lang>.md` beside this file — read the
relevant one before interpreting a report.

A project's own declared test command wins: a `test` script in `package.json`, a `Makefile`
`test:` target, or `.orclab/test.yaml`:

```yaml
coverage: 80        # percent of lines, per language
tce: 70             # mutation score, per language
languages:
  python:
    test: make check
```

## Containers

A project can run its whole toolchain in a container instead of on this machine (v23). The
record is a `compose.yaml` at the project root with a service named `orclab` — committed, so a
clone keeps it — whose Dockerfile installs the language's toolchain *and* every tool this
command needs, so a run inside never installs anything. Inside, the project is mounted at its
own host path, so every path in every report is valid on both sides:

```yaml
services:
  orclab:
    build: .
    volumes:
      - .:${PWD}
    working_dir: ${PWD}
```

Every command runs as `<engine> compose run --rm -T --workdir <dir> orclab <cmd>`, after one
`<engine> compose build orclab`; the first line of the report says
`detected: Python (in container)`. `${PWD}` is filled in from the environment of the process
that calls the engine — Compose: *"You can use existing environment variables from your host
machine or from the shell environment where you execute docker compose commands"* — so `run.py`
sets `PWD` to the project root before every call (a child's `cwd` does not rewrite the `PWD` it
inherited; under `--cwd` that would be the wrong directory). Running `compose` by hand, do it
from the project root.
Nothing else in the file is engine-specific: `.:${PWD}` is the short volume syntax (*"a host
path on the platform hosting containers (bind mount)"*, *"the relative path is resolved from
the Compose file's parent directory"*) and `working_dir` *"overrides the container's working
directory which is specified by the image"* — both confirmed live 2026-09-20 on the Compose
services reference.

**The engine — confirmed live 2026-09-20.** Podman is the default, Docker Engine the alternative;
with both installed Podman is used. The reason, in one sentence: Podman runs as your own user with
nothing to join — a file it writes into the project *"is actually owned by your user on the
host"* — while Docker Engine's daemon runs as root, and the `docker` group that lets you use it
without `sudo` *"grants root-level privileges to the user"* — and, the daemon writing as root,
the files a run leaves in the tree (`.orclab/test/`, `mutants/`) come out root-owned unless the
image sets a user (inference from those two pages, not yet seen on this machine). Neither is
free of a second package: on Ubuntu-derived Mint, `compose` is a separate apt package for both.

- **Podman** — `sudo apt install podman podman-compose` (Mint 22.3's apt: `podman` 4.9.3,
  `podman-compose` 1.0.6; podman.io's install page says Mint follows the Ubuntu steps, which are
  `sudo apt-get -y install podman`). `podman compose` is *"a thin wrapper around an external
  compose provider such as docker-compose or podman-compose"* — it runs one or the other and
  points it at Podman; with neither installed it fails with *"looking up compose provider
  failed"*. Rootless is the default: it needs a range in `/etc/subuid` and `/etc/subgid` for
  your user (`grep $USER /etc/subuid` shows it; this machine already had one before either
  engine was installed), and nothing to join or start. `podman-compose` 1.0.6's source, read
  for the four facts the code depends on: `run` accepts `--rm`, `-T` and `--workdir`, always
  attaches stdin (`-i`), fills `${PWD}` from the environment, and does **not** build a missing
  image — which is why the command runs `compose build` first.
- **Docker Engine** — `sudo apt install docker.io docker-compose-v2` (Mint's apt: 29.1.3 and
  2.40.3; `docker.io` only *suggests* the compose plugin, so name both), then
  `sudo usermod -aG docker $USER` and log out and in. Docker's own repository is the other route
  (`docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin`), with the
  page's note that Mint is *"not officially supported (though it may work)"*. Rootless Docker
  exists (`dockerd-rootless-setuptool.sh install`, from `docker-ce-rootless-extras`, needing
  `uidmap`) but is a separate setup, not the default. `docker compose run`'s reference:
  `--rm` *"Automatically remove the container when it exits"*, `-T` *"Disable pseudo-TTY
  allocation"*, `-w, --workdir` *"Working directory inside the container"*, `-i` default `true`
  *"Keep STDIN open even if not attached"* (the mutation step feeds stdin). It does not say
  `run` builds a missing image — only `--build` *"Build image before starting container"* — so
  the explicit `compose build` covers Docker too. Docker Engine's licence is unchanged by the
  Desktop terms — *"The licensing and distribution terms for Docker and Moby open-source
  projects, such as Docker Engine, aren't changing"* — and Docker Desktop is not needed on Linux.

`.orclab/test.yaml` overrides per checkout: `container: false` runs on the host here even though
the repo is containerised; `runner: docker` (or `podman`) names the engine. Nothing is ever
silently run on the host instead: no engine on PATH prints
`<Language>: container runner not found — install podman or docker — skipped`; an image that
does not build prints its output and `container build failed — see above`, exit 1 —
never the host. The engine is a tool like any other: this command never installs it.

Sources: https://docs.docker.com/reference/cli/docker/compose/run/ ·
https://docs.docker.com/reference/compose-file/interpolation/ ·
https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/ ·
https://docs.docker.com/reference/compose-file/services/ ·
https://docs.docker.com/reference/compose-file/build/ ·
https://docs.docker.com/engine/install/ubuntu/ ·
https://docs.docker.com/engine/install/linux-postinstall/ ·
https://docs.docker.com/engine/security/rootless/ ·
https://docs.docker.com/subscription/desktop-license/ ·
https://podman.io/docs/installation ·
https://docs.podman.io/en/latest/markdown/podman-compose.1.html ·
https://github.com/containers/podman/blob/v4.9.3/cmd/podman/compose.go ·
https://github.com/containers/common/blob/v0.57.0/pkg/config/default.go ·
https://github.com/containers/podman-compose/blob/v1.0.6/podman_compose.py ·
https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md ·
https://packages.ubuntu.com/noble-updates/amd64/docker-compose-v2/filelist ·
`apt-cache policy` / `apt-cache depends` on Mint 22.3, 2026-09-20.

## What it never does

Install a tool — the container engine included — (it names the missing one and its install line,
and skips that language). Run git. Guess a language it cannot see a marker for.

## `run` — does the code work?

`python3 ${CLAUDE_SKILL_DIR}/scripts/run.py run [path]`. One line per language: ✓/✗, counts where
the runner prints a `N passed` summary, seconds. Exit 1 on any failure. `/orc-git merge` calls
this before and after landing a branch.

## `coverage` — how much do the tests exercise?

`... coverage [path]`. Per language: percent, lines, ✓ or ✗ against 80 (or `.orclab/test.yaml`),
then every file under the threshold, worst first — that list is where to go next. The tool's own
HTML report path is printed; per-line detail lives there, not in the summary.

## `audit` — are the dependencies known-vulnerable?

`python3 ${CLAUDE_SKILL_DIR}/scripts/run.py audit`. One line per language: `✓ 0 vulnerable`, or
`✗ N vulnerable` with one indented line per package — name, version, advisory ids and, where the
tool reports it, the version that fixes it. `languages/<lang>.md`'s `## Audit` says which tool
each language uses; a language whose tool is not installed prints `missing <tool> — <install
line> — skipped` and is not a failure; a language with no free audit tool prints `audit not
available — <why>` and is not a failure either. Exit 1 only when a vulnerable dependency was
actually found, or when a tool's output could not be read — that line is printed with the tool's
own output above it. `/orc-git push`, `cp` and `release` run it before touching a remote (v22;
`security-discipline`'s every-project rule "dependencies audited").

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
           TCE not measurable — gdmutant not installed — pip install 'gdmutant==0.1.*'
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

**`generate` is also the first step of a migration.** `/orc-code refactor`'s migration mode
runs `analyze` on the *old* code before any migration command; a red suite is fixed by hand
first (the rule below), and where the suite is absent or under the gate, `generate` runs there
first — characterization tests that pin what the code does today, so the migrated code can be
measured against them. The same `analyze` is that mode's exit gate: coverage and TCE no lower
than the baseline, on the new code.

**Everything it writes is uncommitted.** Committing is the user's step, so they can read the
new tests first. `/orc-git commit` is the way.

## When something goes wrong

One rule: say what, show the command, stop that language, continue the others.

- Tool missing → its name and install line, language skipped. Nothing is installed.
- Tests red under `analyze` → "tests failed; nothing measured" for that language.
- Mutation run interrupted → the tool's incremental file keeps what finished; run again.
- Mutation run changed a *tracked* file outside `.orclab/` and its language's own build/report
  output (e.g. `mutants/` for Python, `reports/` for JS/TS) → the paths are named, TCE is "not
  measurable", and the run is not scored: the suite wrote to the real tree under a planted
  defect (test-discipline rule 4; BACKLOG #34). Fix the tests' isolation first. An untracked
  file the tool left behind is never this — only a committed file changing is the signature.
- Mutation tool produced no mutants → its own output is shown above the line, since the usual
  cause (a missing `[tool.mutmut]`, a wrong test path) is in there.
- Tests red under `analyze` and nothing else → `generate` is not offered; a red suite is fixed
  by hand first.
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
- GDScript mutation via gdmutant (0.1.x, one maintainer): run for real once, on gdmutant's own
  sample project (2026-09-12), never yet on a project of ours — `languages/gdscript.md`'s Caveats
  carry what that run found.
