---
name: orc-code
description: Use when the user explicitly asks to use orc-code, or types /orc-code, to start a new project, add a feature to an existing project, or refactor/migrate existing code.
argument-hint: [refactor] <description of what to build, add, or change>
---
# /orc-code

You are helping with code work via the `/orc-code` command. Your first job is routing to the
right flow below — do this before anything else.

## Step 0: Route

1. If invoked as `/orc-code refactor ...`, OR if `$ARGUMENTS` itself clearly describes refactoring
   or migrating existing code ("clean this up", "bring it up to code-discipline", "migrate this
   to Kotlin," "upgrade from .NET Framework to .NET 8," "port this to Python") — go to **Refactor
   Flow** below. Recognize this from reading `$ARGUMENTS` the same way you'd recognize which skill
   applies to a request — don't require the literal word "refactor" if the intent is already
   clear.
2. Otherwise, if it isn't already obvious from `$ARGUMENTS` whether this is new work or existing
   work, ask exactly one question: "Starting something new, or working on an existing project?"
   - "New" → **New-Project Flow**
   - "Existing" → **Add-to-Existing Flow**

Never guess this from the filesystem (an empty directory, presence of a git history, manifest
files, etc.) — always resolve it from what was typed or by asking directly.

## New-Project Flow

Ask these questions **one at a time**, waiting for each answer before asking the next. Skip any
question `$ARGUMENTS` already answered.

1. **Project name**: "What would you like to name the project?"
2. **Type**: "Is this an app or a game?" (CLI tools and libraries are apps for this purpose;
   if the answer is something else entirely, there is no default — say so and ask what stack
   they want.)
3. **Scope**: "Which platforms? Tick any of: Linux, Windows, Mac, Android, iOS, web." Any subset
   is valid. Once you have type + scope, find the one row of the Defaults Table below whose
   *Scope ticked* column matches — the rows are exact, and every subset lands on exactly one:
   - If the row has a Default, propose it: "For a [type] on [platforms], I'd default to
     [stack] — sound good, or would you like something different?" Name the row's alternatives
     only if asked, or if the stack skill's own concern line applies to what the user has said.
   - If the row's Default is a stub, or no row matches, don't propose one — say there is no
     researched default yet and ask what stack they want. Before scaffolding with a stack that
     has no skill, `CLAUDE.md`'s "Before the first project builds on a stack ... Orclab has
     never met" applies: the research comes first.
   - If the user changes scope after scaffolding ("we should add iOS"), that is the
     Add-to-Existing Flow, not this table.
4. **Starting point**: "Would you like a minimal example, a basic scaffold with common features,
   or something specific — describe your use case."

Once all four are answered:

5. **Scaffold**: create the project directory (if it doesn't already exist), initialize the
   language's standard tooling (e.g. `npm init`, `cargo init`, a Maven/Gradle project layout,
   `python -m venv` + `pyproject.toml`, whatever is standard for the confirmed language), and
   write starter files reflecting the confirmed stack and starting point.
6. **Verify**: run the stack's standard build/test command (e.g. `mvn compile`, `npm run build`,
   `cargo build`, `python -m py_compile` or the project's own test command) and confirm it exits
   cleanly. If it fails, fix the issue before continuing — do not report this flow as complete
   until the verification command actually passes.
7. **Report**: tell the user what was created, the exact command to run it, and any relevant next
   steps.

## Add-to-Existing Flow

This flow wraps the `feature-dev` plugin's own real workflow rather than reimplementing it.

1. Run the **Plugin-Discovery Procedure** below, searching for a plugin named `feature-dev`.
2. **If not found**: tell the user plainly: "This needs the `feature-dev` plugin, which isn't
   currently installed." Offer to help — use the `SearchPlugins` tool with keywords like
   `["feature development", "guided implementation"]` if available, or point at the marketplace
   install flow (`/plugin marketplace add ...` / `/plugin install ...`) if you know where it's
   published. Stop here; do not attempt this flow without it.
3. **If found**: Read the `commands/feature-dev.md` file inside the located plugin's directory in
   full, and follow its instructions directly, exactly as if the user had invoked
   `/feature-dev $ARGUMENTS` themselves. Tell the user plainly that you're using feature-dev's own
   guided workflow for this — don't obscure that this is someone else's real, existing work.

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

The procedure that brought Orclab's own scripts from 190 findings to zero on 2026-09-13
(BACKLOG #40), in the order that worked, and Orcshot from 376 to zero the same day (#41). Each
step's output is the next step's input.

0. **The checkout can run its own suite.** `/orc-test run` must be green *in this checkout*
   before anything is measured — and on a checkout that is not the developer's own (a fresh
   clone, a worktree) that means doing the project's documented install first (its README's
   venv and `pip install -e`, or the stack's equivalent) and running `/orc-test` with that
   interpreter — concretely, the project's own venv `bin` first on `PATH` for the orc-test
   commands, because orc-test's `run.py` invokes a bare `python3`; and only a venv that has pytest
   installed, since any other venv first on `PATH` breaks the runner the other way (the
   scratch venv of 2026-09-13: "8 failed", no pytest in it). Found 2026-09-13: a clone of Orcshot reported 10 collection errors because
   `import orcshot` resolved to the machine's installed `.deb` copy, not `src/`. That is not a
   red suite; it is the wrong interpreter. A suite that is red *with* the right interpreter is
   fixed by hand first — `orc-test`'s own "When something goes wrong" rule: `generate` is not
   offered on a red suite — and that is not this mode's work either.
1. **The stack's lint config is present, or is written first.** Detect the language(s) the way
   `/orc-test detect` does. For each, the matching `stack-*` skill's section
   `## Lint — where code-discipline lands` names the config file and its contents. If the
   project already has that file, use it as it is — a project's own settings win, and this mode
   does not edit them. If not, write that section's config verbatim, tell the user the project
   has just adopted `code-discipline`, and commit the config on its own. **The same for the
   mutation config** `orc-test`'s `languages/<lang>.md` names (`[tool.mutmut]` for Python):
   without it `analyze` reports "TCE not measurable", step 2 has no TCE and step 3.3 has no
   survivors to work from. Its own commit, like the lint config.
2. **Baseline, in numbers.** The linter over the whole tree (the stack section's command —
   `ruff check .`, `oxlint .`, `./gradlew detekt`, and so on) and `/orc-test analyze` on the
   same path. Write down: findings by rule, coverage, TCE, test-lint count, and **which source
   files the suite never imports** — the coverage report's file list against the tree. This is
   the "before"; the report at the end is measured against it. A first `analyze` on a real
   project is long (Orcshot: 26k mutants, ~10 min of mutmut and ~35 min of one `mutmut show`
   per survivor) — start it, then read the findings while it runs; nothing may be edited until
   its mutation run has finished.
3. **Fix, in this order, with the suite green after every file:**
   1. The linter's **safe autofixes only** — `ruff check --fix`, `oxlint --fix` — and never `--unsafe-fixes`
      or `--fix-suggestions`: on 2026-09-13 the unsafe set turned two
      `append`s into `lines.extend((…))` and broke eight tests. Run the suite. Commit.
   2. **The rule findings, by hand, one function at a time.** Nesting depth: a guard clause
      that returns early, or the inner block extracted into a helper with a name. Function
      length: split at the seam the code already has (a comment that says "now do X" is the
      seam). Swallowed errors: handle it, or a *named, commented* suppression at that one site.
      Warnings: fix what the warning names. `code-discipline` is the reference for what each
      fix looks like. A change that needs a test the suite does not have gets that test first
      (`test-discipline` rule 2). Run the suite after each file; commit per module.
      **For a file the suite never imports** (step 2's list — on Orcshot, 17 of 85 files and
      31 of the 58 findings, GTK windows whose own docstrings say they have no headless test),
      a green suite proves nothing about the change. There the fix is limited to a mechanical
      move — the block into a named helper, verbatim, its free variables as parameters — and
      the net is the linter's undefined-name rules plus an import of the module; the commit
      says so. Do those files last, and never rewrite logic in them under this mode.
   3. **`/orc-test generate`** for what the baseline `analyze` listed — surviving mutants,
      uncovered code, test-lint findings — under `generate`'s own rules: deletions are proposed
      as a list, never done unasked.
4. **before → after, every number**, in the shape `generate` reports: findings by rule,
   coverage, TCE, lint. If a gate still fails: say which, and ask — "Another round?" — and
   wait. If the gap is in the files step 2 listed as never imported, say that too: another
   round of `generate` cannot close it, and whether those files get a live-driven test is the
   user's decision, not this mode's. Never say "clean" without the second `analyze`.

Two things this mode refuses. It does not apply unsafe autofixes (above). And it does not add an
`ignore` list to the linter config to make the number fall: a rule the project's own config
enables is either fixed or suppressed at the one site with a reason — `code-discipline` rule 7,
"applies even in cases where the analyzer gives an erroneous warning".

Architecture opinions — whether the code is over-engineered, whether a module should exist —
are not this mode's. Name them as a follow-up if they show; do not act on them here.

### Migration mode

Run once for real on 2026-09-13: itsdangerous 1.1.0 uplifted to Python 3.12 — see BACKLOG #41.
That run is where every correction below comes from; the gate passed (423 tests green, coverage
97.4% → 97.6%, TCE 74.8% → 75.1%).

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
   and the run would degrade silently at the first spawn. Installed, the agents are reachable as
   `code-modernization:<agent>` through the Agent tool and that is how "spawn the test-engineer
   subagent" in one of the plugin's own command files is carried out. The plugin's manifest
   carries no `version`; `~/.claude/plugins/installed_plugins.json` records `"unknown"` — cite
   the cache directory name instead.
2. **Decide the target the way a new project is decided.** Ask the New-Project Flow's two
   questions — type, and the platforms ticked — for the *target*, and take the Defaults Table's
   row. That row's `stack-*` skill is the migration's constraint: its toolchain versions, its
   project layout, its `## Lint — where code-discipline lands` config, its store-rules table.
   Read it in full now. If the row is a stub or there is no row, `CLAUDE.md`'s "Before the first
   project builds on a stack … Orclab has never met" applies: the research comes first, and this
   flow stops until it exists. **For a same-stack version bump only the toolchain version is
   the target**: `uplift`'s own rule is "smallest diff that builds; defer all optional
   modernization", and its critic treats a layout change as a finding. The stack skill's layout
   and lint block are the first items of the quality-mode pass that follows the uplift, and the
   brief says so in its target-architecture section rather than pretending the uplift will do it.
   On 2026-09-13 the target was Python 3.12 because that was the only interpreter present
   (`stack-python-desktop` names 3.14) and installing a newer one was not attempted. A future run should
   install the stack skill's named version first (`uv python install <version>`, or pyenv) and
   fall back to the machine's interpreter only if that fails — and say which happened in the
   target-stack line.
3. **Tests before any `modernize-*` command runs.** `/orc-test analyze` on the source project,
   with quality mode's step 0 interpreter rule, so the baseline and step 6's gate are measured
   the same way. If the suite is red, it is fixed by hand first (`orc-test`'s own rule: `generate`
   is not offered on a red suite). If a language has no runnable suite, or coverage is under the
   gate, the first work is `/orc-test generate` *on the old code* — characterization tests that
   pin what it does today, under `test-discipline`. The plugin's `extract-rules` will document the
   business rules; these tests are what make them executable, and without them the gate in step
   6 has nothing to measure. Record the baseline: coverage, TCE, test count. This step is not
   optional and it is not the plugin's. Two things the first run added: **run the suite with
   deprecation warnings promoted to errors as well** (`python -W error::DeprecationWarning -m
   pytest` for Python) — itsdangerous was 417/417 green on the target and every runtime delta it
   had was hiding in 107 warnings, 97 tests red under `-W error`; and **copy
   `.orclab/test/analyze.json` aside**, because step 6's `analyze` overwrites it and the
   comparison needs both.
4. **Lay out a scratch directory the plugin's way.** Every `modernize-*` command addresses the
   source as `legacy/<name>` and writes to `analysis/<name>/` and `modernized/<name>/`. Inside
   the checkout (a worktree via `superpowers:using-git-worktrees`, or a scratch clone), create
   `.orclab/modernize/` holding `legacy/<name>` as a symlink to the checkout root, add
   `.orclab/` to `.gitignore`, and run every plugin command from `.orclab/modernize/`. This
   survived contact with two corrections. The symlink points *up* into the tree that contains
   it, so **any walk that follows symlinks loops** — every `find -L`, every subagent prompt,
   prunes `.orclab`, `.venv`, `mutants` and `.git`. And **`uplift`'s own seeding command,
   `cp -r legacy/<name> modernized/<name>-uplifted`, copies the symlink, not the tree** (GNU
   `cp -r` does not dereference a command-line link): followed literally, "editing in place
   under `modernized/`" edits the real files. Seed with
   `rsync -a --exclude .venv --exclude .orclab --exclude mutants … "$(readlink -f legacy/<name>)/" modernized/<name>-uplifted/`
   and give the working copy **its own venv** — the checkout's venv has the package installed
   editable from the checkout's `src/`, so a suite run in the copy with that venv tests the
   wrong tree (`python -c "import <pkg>; print(<pkg>.__file__)"` is the check).
5. **Hand over, with the stack as the brief's constraint.** `modernize-status <name>` first; if
   it reports prior work, continue from there, otherwise `modernize-preflight <name>
   [target-stack]` and on through the plugin's own sequence, reading each command file in full
   from the plugin's directory and following it exactly as if the user had typed it. The target
   stack — optional in `preflight`'s and `brief`'s own `[target-stack]`, required in
   `transform`'s `<target-stack>` — is the stack skill's own naming, in one line: e.g.
   `Kotlin + Jetpack Compose, per Orclab's stack-android-native: AGP 9.x, compileSdk 36, app/build.gradle.kts layout`.
   When `brief` produces its target architecture, check it against the stack skill's layout
   section before the user approves it, and correct the brief, not the migrated code, if it lands
   elsewhere — or, for an uplift, record in the brief why it lands elsewhere (step 2). A
   same-stack version bump goes through `modernize-uplift <name> <source-version>
   <target-version>` instead of `transform`; it takes versions, not a stack line, and never
   sees the target-stack line at all.

   What "the plugin's own sequence" is, learned by running it: **`brief` reads
   `ASSESSMENT.md`, `topology.json` and `BUSINESS_RULES.md` and stops if any is missing**, so
   `map` and `extract-rules` are not optional between `assess` and `brief`; and for an uplift it
   also requires `DELTA_CATALOG.md`, which is `uplift`'s Step 3, run before `brief` and reused
   by `uplift` afterwards. The order that works: `status`, `preflight`, `assess`, `map`,
   `extract-rules`, `uplift` Step 3 (delta catalog), `brief`, `uplift`. Three more facts of the
   handover: `preflight`'s Check 0 asks the human five questions (scope, local build, bespoke
   build machinery, prior attempts, off-limits) — put them to the user and record the answers
   verbatim, `brief` reads them; the plugin's "Workflow tool" paths do not exist in this client
   and every command's stated fallback (direct subagents through the Agent tool) is what runs;
   and the plugin has human gates of its own — `brief`'s approval block, `uplift`'s Step 2 plan
   and Step 5a pilot review — where "as if the user had typed it" means stopping and showing,
   not signing on the user's behalf. `status` at the start reports nothing; run it again after the
   pilot — it flags the brief stale, because the pilot appends what it learned to the delta
   catalog — expected, not a defect.
6. **Exit gate.** Copy the plugin's output back over the checkout as the branch's content —
   `modernized/<name>-uplifted/` for an uplift (not `modernized/<name>/`, which is
   `transform`'s), excluding its `.venv`, `.git`, `mutants` and the `UPLIFT_NOTES.md` the plugin
   writes there — and the brief, rule catalogue, delta catalogue and `PLAYBOOK.md` from
   `analysis/<name>/`, plus those uplift notes, into `docs/`. Then `/orc-test run` must be green
   on the migrated code, and `/orc-test analyze` must report coverage and TCE **no lower than**
   step 3's baseline. If either fails, the
   migration is not done: say which, and what the plugin's `status` shows, and stop. "Done" is
   not said before this gate.
7. **Report** in reader terms: what moved, what the old suite proved, the numbers before and
   after, and what `harden` found — or, if `harden` did not run, what `assess`'s security
   section found, which on the first run was a High (CWE-502 in `loads_unsafe`) that no uplift
   touches and the report has to say so.

## Plugin-Discovery Procedure

Given a plugin name to find (e.g. `feature-dev`, `code-modernization`):

1. Search for every `.claude-plugin/plugin.json` file under both of these roots:
   - `~/.claude/plugins/marketplaces/`
   - `~/.claude/plugins/cache/`
2. For each one found, read it and check its `"name"` field.
3. The first one whose `"name"` matches the target plugin exactly is the match — its containing
   directory (the directory holding that `.claude-plugin/` folder) is the plugin's root. Use that
   root to locate the plugin's `commands/*.md` files.
4. **Found is not installed.** A match whose root is under `~/.claude/plugins/marketplaces/` is
   a marketplace *copy*; the plugin is installed only if its name appears in
   `~/.claude/plugins/installed_plugins.json` (a `<plugin>@<marketplace>` key). Read that file.
   A copy with no entry is *available, not installed* — its command files can be read, but the
   agents they spawn are not registered, so treat it as not installed.
5. If no match is found, or the match is available but not installed, stop and tell the user
   plainly, with the command: `claude plugin install code-modernization@claude-plugins-official`
   (or the plugin's own name and marketplace). On 2026-09-13 (Desktop) the installing session
   picked the plugin up itself — its agents and skills were announced with no restart — so
   check for them first; if they are not visible, a fresh session is the fallback
   (`CLAUDE.md`, marketplace gotcha 4, which recorded the older behaviour on 2026-09-06).

Real install layouts you may encounter (all three have been directly observed): a versioned cache
path (`.../cache/<marketplace>/<plugin-name>/<version>/`), a nested marketplace path
(`.../marketplaces/<marketplace>/plugins/<plugin-name>/`), and a self-hosted single-plugin repo at
a marketplace's own root (`.../marketplaces/<plugin-name>/`). Search broadly enough to find all
three — don't assume only one shape.

## Defaults Table

Keyed by what the user ticked, not by language — the language is the answer. Families: desktop
= Linux, Windows, Mac; mobile = Android, iOS. The iOS-ticked rows default to Flutter because
building for iOS from Linux does not force React Native: EAS Build alone does (its prerequisite is
*"A React Native Android or iOS project"*, docs.expo.dev/build/setup, 2026-09-12), but Codemagic's
Flutter quick-start covers *"build versioning, code signing and publishing"* for iOS on its free
500 macOS minutes a month — see `stack-flutter`'s "Building without a Mac". The two cross-family
rows' concern lines — what would move a project from Flutter to either alternative — live in
`stack-flutter`'s "Beyond mobile — desktop and web".

| Type | Scope ticked | Default | Alternatives | Knowledge |
|---|---|---|---|---|
| App | one or more desktops, nothing else | Python | Java + Spring + JavaFX; C# / .NET only when Windows is the sole platform | `skills/stack-python-desktop/SKILL.md` — read it in full before scaffolding |
| App | Android only | Kotlin + Jetpack Compose | Java *(stub — existing codebases only)* | `skills/stack-android-native/SKILL.md` — read it in full before scaffolding |
| App | iOS only | Swift + SwiftUI | Objective-C *(stub — existing codebases only)* | `skills/stack-ios-native/SKILL.md` — same; needs a Mac or a cloud Mac to build |
| App | Android + iOS, nothing else | Flutter | React Native; Kotlin Multiplatform | `skills/stack-flutter/SKILL.md` — same; iOS builds without a Mac are in its "Building without a Mac"; RN: `skills/stack-react-native/SKILL.md`; KMP: `skills/stack-kotlin-multiplatform/SKILL.md` |
| App | web only | React (Vite, TypeScript) + FastAPI | Next.js (front, or Node back end); Django | `skills/stack-web/SKILL.md` — read it in full before scaffolding |
| App | two or more of desktop / mobile / web, iOS ticked | Flutter | React Native + React web; Kotlin Multiplatform + Compose Multiplatform | `skills/stack-flutter/SKILL.md` — same; RN: `skills/stack-react-native/SKILL.md`; KMP: `skills/stack-kotlin-multiplatform/SKILL.md` |
| App | two or more of desktop / mobile / web, iOS not ticked | Flutter | React Native + React web; Kotlin Multiplatform + Compose Multiplatform | `skills/stack-flutter/SKILL.md` — same; RN: `skills/stack-react-native/SKILL.md`; KMP: `skills/stack-kotlin-multiplatform/SKILL.md` |
| Game | desktops only | Godot 4 | Unity 6 | `skills/stack-godot/SKILL.md` — read it in full before scaffolding; Unity: `skills/stack-unity/SKILL.md` |
| Game | mobile only | Godot 4 | Unity 6 | same |
| Game | desktop + mobile | Godot 4 | Unity 6 | same |
| Game | web, alone or with others | Godot 4 *(stub — web export not researched)* | — | `skills/stack-godot/SKILL.md` has no web section yet |

Do not invent additional defaults beyond what's listed here — if a scope isn't in this table,
ask directly in the New-Project Flow's step 3 instead of guessing. A row's **Knowledge** column
names the background skill that holds the stack's current toolchain, project layout, store
rules, and the facets every stack skill answers — presence, UI, storage (v18 spec §3). When a
row has one, its scaffold step follows that file rather than this one's generic step 5. A row
marked *stub* is not a default to propose; it is a name to research.
