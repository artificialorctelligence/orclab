# Orclab v23: containers as an opt-in development environment — `/orc-code` asks, `/orc-test` runs through it

**Status:** design, approved section by section in conversation 2026-09-20. It began as "how do
we run PHP locally for v23" and became this first, by direflail's decision: *"this shouldn't be
just for php, we need to figure out how containerization fits best into orclab and provide it as
an option when building a project."* PHP is now v24 and starts when this ships (BACKLOG #50 is
renumbered by §5).

## The problem

The first project Orclab will build on a stack this machine does not have — PHP 8.5, matching
direflail's DreamHost host — needs a toolchain from somewhere. Installing it on the machine is one
answer; direflail chose the other: a container, and not just for PHP. Two commands at least have
to work with it: `/orc-code`, which scaffolds and verifies, and `/orc-test`, which runs every
tool a project has.

**Licensing, confirmed live 2026-09-20** (docs.docker.com/subscription/desktop-license): Docker
*Desktop* is free only for personal use, education, non-commercial open source, and businesses
under 250 employees *and* $10M revenue; Docker *Engine* — the open-source daemon and CLI — is
separate: *"The licensing and distribution terms for Docker and Moby open-source projects, such
as Docker Engine, aren't changing."* On Linux, Engine installs without Desktop
(docs.docker.com/engine/install/ubuntu — which says Mint is *"not officially supported (though it
may work)"*); Mint 22.3's own apt has `docker.io` 29.1.3 and `podman` 4.9.3, both Apache-2.0.
Nothing is installed on this machine yet.

**What should already have covered it** (`CLAUDE.md`, "Before building anything"): v18 §6 parked
Docker on purpose — *"probably going to remain open. No row, no facet."* It is open now because
the first stack that cannot reasonably run on the host has arrived. Searched every shipped
`SKILL.md`, `CLAUDE.md`, `BACKLOG.md` and the bundled scripts: nothing runs a project's tools
anywhere but the host.

**Two things this is not**, stated because they are easy to conflate:

- **Not a shipping unit.** The container is a *development environment*: the toolchain lives in
  it so it need not live on the machine. What it produces is ordinary project files — the same
  `src/`, manifest and dependencies a host install would produce — and those are what ship,
  however that stack's Deployment section or `orc-package` ingredient says. direflail's API on
  DreamHost is the first case: DreamHost never sees a container; it gets the files and runs them
  with its own PHP. The `Dockerfile` Orclab writes is deliberately *not* production-shaped — it
  carries test and mutation tools. A stack that one day deploys *as* a container is a different
  thing: a production image, and a new `orc-package` ingredient, not this.
- **Not the default.** direflail: *"opt-in, asked at scaffold."* For a Python or Flutter project on
  a machine that already has the toolchain, a container is friction; the case for it is "the
  toolchain isn't, or shouldn't be, on this machine."

## What is decided

### 1. The opt-in and what it writes

**The question**, in `/orc-code`'s New-Project Flow after Exposure (step 4) and before Starting
point: *"Run this project's toolchain in a container, so nothing has to be installed on this
machine?"* The proposed answer is "no"; a stack skill's Containers section (§3) may flip the
proposal to "yes" for a stack whose toolchain is unusual on a dev machine — PHP's will. A stack
that cannot run in one (iOS) skips the question, and the flow says why.

**What "yes" writes, at the project root, committed:**

- `Dockerfile` — from the stack skill's Containers section: base image and tag, the toolchain,
  *and every tool `/orc-test` needs for that language* (runner, coverage, mutation, audit), so a
  run inside the container never installs anything (`/orc-test`'s standing rule, now holding
  inside the container as well as on the host).
- `compose.yaml` with one service named **`orclab`**: builds that `Dockerfile`, mounts the
  project directory at **its own host path** and sets it as the working directory. This
  convention is what makes every path in every report — lcov `SF:` lines, mutation survivors,
  lint findings — valid on both sides with no translation.

**How a project is recognised as containerised:** the committed `compose.yaml` with an `orclab`
service *is* the record. It is unambiguous (Orclab names the service), it travels with the repo,
and it is read off the project the way v22's exposure is read off the code. Nothing under
`.orclab/` can serve: `/orc-git repo` adds `.orclab/` to `.gitignore`, so a clone would lose the
opt-in. An existing project opts in by adding the same two files; the stack skill's section shows
them.

**Per-checkout override**, in `.orclab/test.yaml` (already `/orc-test`'s config, already
per-checkout):

```yaml
container: false      # run on the host in this checkout, though the repo is containerised
runner: podman        # or docker; absent: whichever is on PATH, the research-picked default first
```

**Verify** (`/orc-code`'s step 7) runs the stack's build/test command *through* the container
when the project opted in: "exits cleanly" means clean in the environment that will be used.

### 2. `/orc-test` runs through the container

**One change in one place.** `skills/orc-test/scripts/orc_test/runner.py::run(cmd, cwd)` is the
chokepoint every language module already goes through — *"One place every external command goes
through."* It gains one step: if the project is containerised and this checkout has not opted
out, the command becomes `<runner> compose run --rm orclab <cmd>`, run from the project root, with
`cwd` passed as the working directory inside the container (the same path, by §1's convention).
The eight language modules do not change — `python3 -m pytest`, `npm audit --json`, `dart test`
are the same strings on either side.

**Detection** lives beside the config: `config.load` reads `.orclab/test.yaml` today; it also
reads `compose.yaml` at the root for an `orclab` service, applies the override, and picks the
runner. `detect`'s first line gains one phrase — `detected: Python (in container)` — so a wrong
guess is visible, the reason it names the marker directory today.

**What stays on the host:** `/orc-test` itself (Orclab's Python, not the project's); `git` (the
mutation sandbox check runs `git status` on the host); reading the reports (host paths, valid by
the convention); `.orclab/test/` (inside the project, so both sides see it).

**Checked rather than assumed, and never a silent fallback:**

- The runner is on PATH; if not: `Python: container runner not found — install podman or docker
  — skipped` — "never installs a tool", applied to the engine itself.
- The image builds; a failed build is printed and that language is `tests failed; nothing
  measured`. A project that said "container" and got a host run would pass a gate in an
  environment it did not ask for, so the host is never the fallback.

**`missing()` moves inside.** Each module asks `shutil.which("dart")` or
`importlib.util.find_spec("pytest")` *on the host* today — the wrong question for a containerised
project. Those checks become a command through the same chokepoint (`which dart`,
`python3 -c "import pytest"`), so "missing" means missing where the tools run.

**`lint_on_write`** — the hook that lints on every write — has its own one `subprocess.run`
(`hooks/scripts/lint_on_write.py`); it gets the same prefix when the project is containerised,
and its on-PATH check moves inside too. Without it a containerised project silently loses
on-write linting.

**`/orc-git`'s gates** change nothing: they call `/orc-test`.

### 3. The stack skills and the engine

**Every stack skill gets `## Containers`** — the fifth facet after v18's three and v22's
Security, pinned the same way: a test with an `EXPECTED` set that grows to all nine, strict-xfail
until the last lands. Each section says one of two things:

- **Runs in a container: yes** — base image and tag (confirmed live), the `Dockerfile` lines that
  install the toolchain and every `/orc-test` tool for that language, the `compose.yaml` service,
  and what cannot happen inside (a desktop GUI can build but not show a window; an Android build
  runs but an emulator needs the host's KVM). Candidates: Python desktop, web, Android native,
  KMP's Android half, Flutter's Android half, React Native's Android half, Godot's and Unity's
  headless builds — research confirms each.
- **Cannot** — iOS (needs macOS) and each cross-platform stack's iOS half; the section says so
  and `/orc-code` skips the question for that row.

**The engine**, settled by research and written once where every consumer reads it — a
`## Containers` section in `skills/orc-test/SKILL.md`: Docker Engine from the distro's apt vs
Podman; whether `podman compose` is CLI-compatible with `docker compose` for the one subcommand
Orclab uses (`compose run --rm`); the Ubuntu-derivative install; rootless. Whichever is the
default, `runner:` names the other.

### 4. Tests, docs, live check

**Tests:** `runner.run`'s prefix with a fake runner on PATH; `config.load` reading `compose.yaml`
and the override; `detect`'s "(in container)"; `missing()` through the chokepoint; the
`lint_on_write` prefix; the stack-section test; `/orc-code`'s pinning test gains the question.

**Docs, same commit as their skills:** `docs/commands/orc-code.md` (the question, the two files,
that the container is a dev environment and not what ships); `docs/commands/orc-test.md` (the
container line, the override, "never installs the engine either").

**Live check:** a throwaway Python scaffold on this machine with "yes" to the container question,
`/orc-test analyze` and `audit` through it, and `lint_on_write` firing on a write inside it. That
needs an engine on this machine: the plan's live task **shows direflail the install command**
(`sudo apt install docker.io` or `podman`, whichever the research picked) **and waits** — it is
their machine and needs `sudo`; nothing in the plan runs that itself.

### 5. Records

BACKLOG: this spec's entry; two deferred entries from §"Out of scope" — the devcontainer file, and
deploying a container as a production artefact; #50 renumbered PHP to v24;
v18 §6's "Docker — parked" line gets its resolution recorded in the v18 entry (#33) or this one.

## Out of scope, by name

- **Shipping a container** — `orc-publish` and `orc-package` untouched (see "Two things this is
  not"). direflail, 2026-09-20: *"we probably will need to deploy a container eventually, but
  that can be an /orc-todo as well"* — a BACKLOG entry, written now, for a production image as a
  new `orc-package` ingredient when the first project that deploys as a container arrives.
- **The devcontainer standard (`.devcontainer/devcontainer.json`).** It describes a container
  environment for editors (VS Code, Codespaces); it can point at the very `Dockerfile` §1 writes
  (`build.dockerfile`), so adding it later is one small file per project, not a second mechanism.
  direflail: *"A, leave B as an /orc-todo."* Written when someone wants their editor attached.
- **A database or service container beside the app** — compose could; YAGNI until a project
  needs one.
- **CI** — `ci` stays deferred in `/orc-test`.
- **PHP** — v24.

## Verification

- The suites green with the new tests added red first.
- The live check in §4, recorded in the entry with the day's date: the scaffold's two files, the
  `detected: Python (in container)` line, `analyze`'s and `audit`'s lines, one `lint_on_write`
  report from inside the container, and — with `container: false` in `.orclab/test.yaml` — the
  same commands on the host, to show the override works.
