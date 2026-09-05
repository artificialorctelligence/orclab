# Orclab v2: the `/orc-code` command — design

## Goal

Add a single Claude Code slash command, `/orc-code`, to the Orclab plugin: a deterministic entry
point for starting new project work, adding to existing projects, and refactoring/migrating
existing code — built primarily for direflail's own day-to-day use, with any wider distribution
treated as a peripheral side effect, not a design driver.

direflail's own framing, across this design conversation (2026-09-04/05): chose slash commands
over pure natural-language routing specifically for their determinism, having seen freeform intent
recognition struggle at work (a similar internal framework, at Caterpillar, saw low adoption for
reasons later traced to team fit and awareness rather than syntax — see BACKLOG.md's own #1-#5 for
the fuller origin story). The explicit design goal is a toolkit that glues together other existing
tools (skills, plugins) under one consistent, growing command surface, not a single-purpose script.

## Scope

**In scope now:** one command, `/orc-code`, with two literal invocation forms (`/orc-code [args]`
and `/orc-code refactor [args]`), covering three real flows (new project, add to existing project,
refactor/migrate), a shared plugin-discovery mechanism the wrapping flows depend on, and a minimal
defaults table (one confirmed entry).

**Explicitly out of scope for this spec, tracked separately:**
- Any command beyond `/orc-code` (direflail's own explicit call — get one command right first).
- Real enforcement (hooks/lint) for v1's three skills — BACKLOG #3, relationship to this command
  layer still undecided.
- The full per-domain default-stack research (desktop-per-language, mobile, web-stack mapping,
  database strategy, containerization, observability) — BACKLOG #4, mostly unsettled today.
- `/orc-data` (a separate command for tracking legacy-system info during refactors) — BACKLOG #5,
  needs its own evaluation of whether `code-modernization`'s `modernize-map`/`modernize-extract-
  rules` already cover the need before any new design.

## Command surface and routing

One command file: `commands/orc-code.md`, at the plugin root (matching the real layout observed in
every installed command-bearing plugin checked during this design — `agent-sdk-dev`, `feature-dev`,
`code-modernization` all place `commands/*.md` directly under the plugin root, not nested).

**Two literal forms:**
- `/orc-code refactor [description of the change]` — explicit refactor/migration request.
- `/orc-code [description]` — everything else; the description may or may not already make the
  intent clear.

**Routing logic, in order:**
1. If invoked with the literal `refactor` subcommand, OR if `$ARGUMENTS` itself clearly describes
   a language/version-migration intent ("change this Java project to do X," "migrate this to
   Kotlin," "upgrade from .NET Framework to .NET 8") — route to the **refactor flow**, without
   requiring the literal keyword. This uses the same read-and-classify reasoning that already
   drives Claude Code's own skill-description matching (verified working throughout this
   conversation's own skill invocations) — not a separate classifier, not a filesystem heuristic.
2. Otherwise, if the intent isn't already clear from what was typed, ask exactly one question:
   "Starting something new, or working on an existing project?" Route to the **new-project flow**
   or the **add-to-existing flow** based on the answer.

No filesystem heuristics anywhere in this routing (no guessing from directory emptiness, git
history, or manifest presence) — every classification is either explicit in what was typed or
resolved by asking directly. This preserves the determinism direflail chose slash commands for:
the two things that matter (which flow, and what stack) are never silently inferred from disk
state.

## The three flows

### New-project flow

Modeled directly on the real, proven pattern in `agent-sdk-dev`'s `new-sdk-app.md` (read in full
during this design) — ask one question at a time, skip a question if `$ARGUMENTS` already answered
it, verify before declaring done:

1. Ask language (skip if given in `$ARGUMENTS`).
2. Ask project name (skip if given).
3. Ask project type/platform (desktop, web, mobile, CLI, etc.). Look up the defaults table for
   this language+type combination; if a default exists, propose it and let the user confirm or
   override by simply answering differently. If no default exists (the common case today — see
   "Defaults table" below), ask directly with no proposed default.
4. Ask starting point: a minimal example, a basic scaffold with common features, or a specific
   described use case.
5. Scaffold: create the project directory (if needed), initialize the language's standard tooling,
   write starter files reflecting the confirmed stack.
6. Verify: run that stack's standard build/test command (e.g. `mvn compile`, `npm run build`,
   `cargo build` — whatever is standard for the confirmed language/stack) and confirm it exits
   clean. Fix before declaring the task done, the same "don't consider it complete until it
   verifies" standard `new-sdk-app.md` itself uses — but via a generic build/test check rather than
   a dedicated per-language verifier subagent, since Orclab must support arbitrary languages, not
   one SDK (direflail's own explicit call, given building N specialist verifier agents up front
   isn't proportionate to a single-user tool still finding its real usage patterns).
7. Report what was built and how to run it.

### Add-to-existing flow

Wraps `feature-dev` (Anthropic's own plugin: "Guided feature development with codebase
understanding and architecture focus" — discovery → codebase exploration → clarifying questions →
design → implementation, read in full during this design).

1. Run the plugin-discovery procedure (below) for `feature-dev`.
2. If not found: tell direflail plainly that this flow needs the `feature-dev` plugin, which isn't
   currently installed, and offer to help install it (surfacing `SearchPlugins`'s result or the
   relevant marketplace-install command) — direflail's own explicit call, over silently attempting
   a worse job without it.
3. If found: locate its actual `commands/feature-dev.md` and follow its real instructions
   directly — noting transparently that this is feature-dev's own workflow, not reimplemented
   Orclab logic. direflail was explicit that hiding this would misrepresent whose work is being
   used; the goal is a good, honest toolkit assembled from real pieces, not the appearance of
   having built everything from scratch.

### Refactor flow

Wraps `code-modernization` (Anthropic's own plugin — real, mature workflow for legacy-codebase
modernization: `preflight → assess → map → extract-rules → brief → reimagine|transform|uplift →
harden → status`, including "same-stack version uplifts" — the exact scenario the original
`/orc-code refactor` idea described).

1. Run the plugin-discovery procedure for `code-modernization`.
2. If not found: same missing-dependency handling as the add-to-existing flow.
3. If found: check whether prior modernization work already exists for this project via
   `code-modernization`'s own `modernize-status` command (if available) — if it reports existing
   progress, continue from there; if it reports no prior work (or `modernize-status` isn't
   available in the installed version), start from `modernize-preflight`. Follow whichever
   command's actual instructions directly, transparently.

## Plugin-discovery procedure

Shared by both wrapping flows. Three real, distinct install layouts were directly observed on this
machine during this design (not assumed):
- A versioned cache path: `~/.claude/plugins/cache/<marketplace>/<plugin-name>/<version>/`
  (e.g. `superpowers`).
- A nested marketplace path: `~/.claude/plugins/marketplaces/<marketplace>/plugins/<plugin-name>/`
  (e.g. `code-modernization`, `feature-dev`, both under `claude-plugins-official`).
- A self-hosted single-plugin repo at a marketplace's own root:
  `~/.claude/plugins/marketplaces/<plugin-name>/` (e.g. `ponytail`).

The procedure: search `~/.claude/plugins/marketplaces/**/.claude-plugin/plugin.json` and
`~/.claude/plugins/cache/**/.claude-plugin/plugin.json` for a `name` field matching the target
plugin (`feature-dev` or `code-modernization`), and use that file's containing directory as the
plugin's root. If no match is found anywhere, the plugin is not installed (triggers the
missing-dependency handling above). This is genuinely reusable logic, not something to inline
separately per flow — the plan should implement it once.

## Defaults table

Baked directly into `commands/orc-code.md` itself (direflail's own call — no separate config file
format to design and maintain; overriding a default just means answering the stack question
differently when asked).

**v1 contents: exactly one entry.** Java desktop → Java + Spring + JavaFX. Every other
language/platform combination has no default and falls through to asking directly — an accurate
reflection of what's actually settled today (see BACKLOG #4 for the much larger, explicitly
deferred research space this table will eventually grow to cover: Python, .NET/C#, Unity, mobile,
web-stack-to-default mapping, database strategy per stack, containerization, observability).

The table is expected to grow by direct edits to this file as real decisions get made — not by
this spec attempting to anticipate them.

## Relationship to v1's skills

No special coupling needed. `/orc-code`'s own work (writing code, scaffolding files) may
independently trigger `backlog-discipline` (if something worth tracking surfaces mid-task) or any
other applicable skill, the same way any other Claude Code activity would — skills fire on
description-match regardless of whether the surrounding work was started via a slash command or
free text. Nothing in `/orc-code`'s design assumes or requires the three v1 skills to be present.

## Validation

Same dogfooding principle as v1: no automated test suite is applicable to a command file (natural-
language instructions, not executable code), so validation is running `/orc-code` through real
scenarios in a fresh Claude Code session after installing/reinstalling Orclab, and confirming:
- A new-project request for a language with no default (e.g. Python) asks directly rather than
  guessing.
- A new-project request for "Java desktop" proposes Java + Spring + JavaFX and accepts an override.
- An add-to-existing request correctly locates and defers to `feature-dev` if installed, or gives
  the plain missing-dependency message if not.
- A refactor request (both the literal `/orc-code refactor ...` form and a bare `/orc-code migrate
  this Java project to Kotlin`-style request) correctly routes to the refactor flow and correctly
  locates `code-modernization`.

This isn't written up as a separate `VERIFICATION.md` scenario set yet — that's an implementation-
plan-level detail, not a design-level one, and should be added the same way v1's was.
