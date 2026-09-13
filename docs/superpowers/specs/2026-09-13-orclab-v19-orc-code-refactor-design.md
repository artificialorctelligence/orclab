# Orclab v19: `/orc-code refactor` — a code-quality pass, and a migration that lands on Orclab's stack and proves it still works

**Status:** design, approved in conversation 2026-09-13 (direflail: "open the backlog entry, then
write the spec"). Resolves BACKLOG #41. Touches #5.

## The problem

`/orc-code` says it can "refactor/migrate existing code", and its Refactor Flow wraps Anthropic's
`code-modernization` plugin. Checked on 2026-09-13, against the files: the plugin is in the
marketplace clone on this machine and **not installed**, so the flow has only ever reached its
own "not installed" branch; and when it does hand over, it hands over everything — it tells the
plugin nothing about which stack Orclab would choose for the target, and nothing checks the
result afterwards. direflail's two conditions for a migration — *factor in the stack* and *make
sure everything still works* — are the two things the wrapper does not do.

And there is no command at all for the other kind of refactor: making the code better where it
is. The pieces exist — `code-discipline` states the rules, `lint_on_write` enforces them on every
new write, `/orc-test analyze` and `generate` do the same for the tests — but bringing an
*existing* codebase up to them is a by-hand job. 2026-09-13's dogfood on Orclab's own scripts
was that job done once: 190 findings to zero, 31 functions flattened, 611 tests green
throughout. It had a clear shape, and one lesson: the linter's unsafe autofixes, applied
wholesale, made the code worse and broke eight tests.

## What is decided

### 1. Two modes under one entry point, told apart by whether the language or its version changes

`/orc-code refactor <description>` stays the entry (its description already says "refactor/
migrate existing code", and `$ARGUMENTS` that reads as a migration intent already routes here).
The first thing the flow does is classify:

- **Quality mode** — the request changes neither the language nor its version: "clean this up",
  "bring it up to code-discipline", "reduce the nesting in the CLI", or a bare
  `/orc-code refactor`.
- **Migration mode** — the request names a different language, framework or version: "port this
  to Kotlin", "move from .NET Framework 4.8 to .NET 8", "rewrite the front end in React".

When the request is ambiguous ("modernize this"), ask — one question, the two modes as the
options, with what each does in a sentence. Never guess: the two modes have different exit gates
and different blast radius.

### 2. Quality mode — the procedure 2026-09-13 already proved, written down

The order matters; each step's output is the next step's input.

1. **The stack's lint config is present, or is written first.** Detect the language(s) as
   `/orc-test detect` does. For each, the matching `stack-*` skill's `## Lint — where
   code-discipline lands` section names the config file and its contents. If the project has
   it, use it as is — a project's own settings win. If not, write that section's config verbatim
   and say so; the project has just adopted `code-discipline`, and the commit that adds the
   config is its own.
2. **Baseline, in numbers.** The linter over the whole tree (`ruff check .`, `oxlint .`, and so
   on — the stack section's command) and `/orc-test analyze` on the same path. Record the
   finding count by rule, coverage, TCE, and lint count. This is the "before".
3. **Fix, in this order, with the suite green after every file:**
   1. The linter's **safe** autofixes only (`ruff check --fix`, never `--unsafe-fixes`; oxlint's
      `--fix`, not `--fix-suggestions`). Run the suite. Commit.
   2. **The rule findings, by hand, one function at a time** — nesting depth with guard clauses
      and extracted helpers, function length by splitting at the seam the code already has,
      swallowed errors by handling or by a *named, commented* suppression (rule 6), warnings by
      fixing what they name. `code-discipline` is the reference for what each fix looks like.
      Run the suite after each file. A change that needs a test the suite does not have gets
      that test first (`test-discipline` rule 2). Commit per module.
   3. **`/orc-test generate`** for whatever `analyze`'s baseline listed — survivors, uncovered
      code, test lint — under the existing `generate` rules (deletions proposed, never done
      unasked).
4. **Before → after, every number**, in the same shape `generate` reports: findings by rule,
   coverage, TCE, lint. If a gate still fails, say so and ask about another round; never claim
   "clean" without the second `analyze`.

Two things the mode refuses. It does not apply unsafe autofixes — the dogfood showed
`lines.extend((...))` for two `append`s and eight red tests. And it does not add an `ignore`
list to the linter config to make the number go down: a rule the project's own config enables
is either fixed or suppressed at the one site with a reason, per `code-discipline` rule 7's
"applies even in cases where the analyzer gives an erroneous warning".

### 3. Migration mode — wrap `code-modernization`, and add the two things it lacks

The plugin stays the engine. Its pipeline (`preflight` → `assess` → `map` → `extract-rules` →
`brief` → `transform` per module or `uplift` for a same-stack version bump → `harden` →
`status`) is far more than Orclab should rebuild, and CLAUDE.md's rule for a capability that
already exists as a real skill is to wrap it with an availability check. Orclab adds:

**(a) The target is Orclab's stack.** Before the handover, `/orc-code` answers "what would I
scaffold for this?" with its own Defaults Table — the target's type and platform scope, as the
new-project flow asks them — and the matching `stack-*` skill becomes the migration's constraint:
its toolchain versions, its project layout, its `## Lint` config, its store-rules table. Concretely,
the plugin's `brief` and `transform` take a free-form `[target-stack]` argument; `/orc-code`
passes the stack skill's own naming (e.g. "Kotlin + Jetpack Compose, per Orclab's
stack-android-native: AGP 9.x, compileSdk 36, `app/build.gradle.kts` layout") and, when the
brief is produced, checks it against the skill's layout section before the user approves it. The
migrated project should look like one `/orc-code` would have scaffolded; a brief that lands
elsewhere is corrected before `transform` runs, not after.

**(b) "Still works" means the old suite passes on the new code.** A port cannot be verified
against tests that do not exist, so the gate has a precondition:

1. **Before any migration step**, `/orc-test analyze` on the source project. If it reports
   tests red, a language with no runnable suite, or coverage under the gate, the first work is
   `/orc-test generate` *on the old code* — characterization tests that pin what it does today.
   The plugin's `extract-rules` documents the business rules; the tests are what make them
   executable. This step is not optional and is not the plugin's: it is the reason the gate can
   exist.
2. **Exit gate**, after `transform`/`uplift` and before the work is called done: `/orc-test run`
   green on the migrated code, and `/orc-test analyze` reporting coverage and TCE **no lower
   than the source baseline**. The plugin's `uplift` already runs "one test suite on both
   runtimes"; Orclab's gate is the cross-stack equivalent and the number that survives the
   session in `.orclab/test/analyze.json`.

**(c) The plugin's layout is not a consuming project's layout.** Every `modernize-*` command
addresses the source as `legacy/<system-dir>` and writes to `analysis/<system-dir>/` and
`modernized/<system-dir>/`. A consuming project is a repository, not a `legacy/` subtree.
`/orc-code refactor` therefore runs the plugin from a **worktree** (`superpowers:using-git-
worktrees`, as every Orclab build does) laid out the plugin's way — the project checked out or
symlinked as `legacy/<name>` — and brings `modernized/<name>/` back into the real tree as the
branch's content once the exit gate passes. `analysis/` stays in the worktree; its useful parts
(the brief, the rule catalogue) are copied into `docs/` on the branch. This is the part most
likely to need correcting at first real use; the skill says so.

**(d) Availability, confirmed rather than assumed.** The Plugin-Discovery Procedure stays, and
the "not installed" message names the install command (`claude plugin install
code-modernization@claude-plugins-official`). But the flow past that line has never run. The
first task of the plan is to install the plugin here and drive the full Refactor Flow once on a
small real project, worktree layout and exit gate included, and to correct this spec with what
that run contradicts — the same "no release has gone through this" honesty the `orc-package`
ingredients carry.

### 4. What is *not* built

- No migration engine, no assessment tooling, no topology viewer — the plugin's.
- No new command. `/orc-code refactor` is the name; `/orc-help` already lists it.
- Quality mode does not decide what "better" means beyond `code-discipline` and the project's
  own lint config. Architecture opinions (ponytail's over-engineering review, for instance) are
  other tools; this mode may *name* them as a follow-up, not run them.
- #5 (`/orc-data`) is not built here. The plugin's `map` and `extract-rules` produce a catalogue
  of the legacy system's facts; whether that covers #5's ask is checked at first real use and
  recorded on #5.

## What changes, by file

- `skills/orc-code/SKILL.md` — the Refactor Flow becomes §1's classification, §2's quality
  procedure, and §3's migration handover (stack constraint, pre-gate `analyze`/`generate`,
  worktree layout, exit gate). The Plugin-Discovery Procedure and the missing-dependency wording
  stay; the message gains the install command.
- `skills/orc-test/SKILL.md` — one paragraph under `generate`: it is also the first step of a
  migration (characterization tests on the old code) and the exit gate's second `analyze`.
- `skills/code-discipline/SKILL.md` — one line: bringing an existing codebase up to these rules
  is `/orc-code refactor`'s quality mode.
- `BACKLOG.md` — #41 resolved by the first confirmed-live run; #5 gets its note.
- `CHANGELOG.md`, version bump via `/orc-version`, as every release.

## How it is verified

- **Quality mode** is verified on Orcshot or the next real Python/TypeScript project: baseline,
  fixes, before → after, suite green — the dogfood repeated through the command instead of by
  hand, and the numbers recorded in the commit.
- **Migration mode** is verified once, live, per §3(d): the plugin installed, a small real project
  taken through preflight → brief → transform (or uplift) → exit gate in a worktree, and the spec
  corrected. Until that run, the skill's migration section carries "no migration has gone
  through this yet" in its first paragraph.
- **Availability branch**: with the plugin uninstalled, `/orc-code refactor "port to Kotlin"`
  prints the install command and stops. That is the one path confirmed today.

## Sources, checked 2026-09-13

- `skills/orc-code/SKILL.md` Refactor Flow and Plugin-Discovery Procedure (the wrapper as it
  stands).
- `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/code-modernization/`:
  `.claude-plugin/plugin.json` (description), `commands/modernize-{preflight,brief,transform,
  uplift,harden,status}.md` (the `legacy/$1` / `analysis/$1` / `modernized/$1` layout; `brief`
  and `transform`'s free-form `[target-stack]`; `uplift`'s "one test suite on both runtimes").
- `~/.claude/plugins/installed_plugins.json` — `code-modernization` absent.
- BACKLOG #40's resolution and the five dogfood commits of 2026-09-13 (the quality procedure and
  the unsafe-autofix lesson).
