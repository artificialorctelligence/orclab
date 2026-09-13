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
   3. **`/orc-test generate`** for what the baseline `analyze` listed — surviving mutants,
      uncovered code, test-lint findings — under `generate`'s own rules: deletions are proposed
      as a list, never done unasked.
4. **before → after, every number**, in the shape `generate` reports: findings by rule,
   coverage, TCE, lint. If a gate still fails: say which, and ask — "Another round?" — and
   wait. Never say "clean" without the second `analyze`.

Two things this mode refuses. It does not apply unsafe autofixes (above). And it does not add an
`ignore` list to the linter config to make the number fall: a rule the project's own config
enables is either fixed or suppressed at the one site with a reason — `code-discipline` rule 7,
"applies even in cases where the analyzer gives an erroneous warning".

Architecture opinions — whether the code is over-engineered, whether a module should exist —
are not this mode's. Name them as a follow-up if they show; do not act on them here.

### Migration mode

(Task 4 fills this section.)

1. Run the **Plugin-Discovery Procedure** below, searching for a plugin named `code-modernization`.
2. **If not found**: same missing-dependency handling as the Add-to-Existing Flow above, naming
   `code-modernization` instead.
3. **If found**:
   - Check whether `commands/modernize-status.md` exists in the located plugin directory. If it
     does, read and follow it first to check whether prior modernization work already exists for
     this project.
   - If `modernize-status` reports existing progress, continue from whatever step it indicates.
   - If `modernize-status` reports no prior work, isn't available, or doesn't exist in this
     installed version, start from `commands/modernize-preflight.md` instead.
   - Read whichever command file applies in full, and follow its instructions directly, exactly as
     if the user had invoked that command themselves with the same `$ARGUMENTS`. Tell the user
     plainly that you're using code-modernization's own workflow for this.

## Plugin-Discovery Procedure

Given a plugin name to find (e.g. `feature-dev`, `code-modernization`):

1. Search for every `.claude-plugin/plugin.json` file under both of these roots:
   - `~/.claude/plugins/marketplaces/`
   - `~/.claude/plugins/cache/`
2. For each one found, read it and check its `"name"` field.
3. The first one whose `"name"` matches the target plugin exactly is the match — its containing
   directory (the directory holding that `.claude-plugin/` folder) is the plugin's root. Use that
   root to locate the plugin's `commands/*.md` files.
4. If no match is found under either root, the plugin is not installed.

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
