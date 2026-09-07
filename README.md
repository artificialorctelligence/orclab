# Orclab

Reusable project-discipline skills and commands for Claude Code, distilled from real practice on
other projects (starting with Orcshot).

## Skills

- **backlog-discipline** — maintain a single flat `BACKLOG.md` of real, open findings, with
  permanent entry numbers and resolution history layered on top of (never replacing) the original
  diagnostic record.
- **release-checklist** — maintain a numbered, dependency-ordered `RELEASING.md`, cross-referenced
  against whatever CI already automates.
- **environment-registry** — register real, live test environments (VMs, containers, staging
  servers, devices) as Claude memory, never as a git-tracked file, never storing credentials.
- **currency-discipline** — check that a chosen dependency, version, or technical approach is
  actually current before committing to it, with real, concrete per-ecosystem verification
  mechanisms.
- **verify-before-asserting** — verify a challenged factual/technical claim instead of defending
  it; reinforces superpowers' own `systematic-debugging` signal recognition.

## Commands

Each command below also ships as a matching skill (`skills/<name>/SKILL.md`, a thin pointer to the
same content) so it works in Claude Desktop too, not just the CLI — see "Known gap, now fixed"
below.

- **/orc-code** — start a new project, add to an existing one, or refactor/migrate existing code.
  Routes deterministically to one of three flows, wrapping the `feature-dev` and
  `code-modernization` plugins where applicable rather than reimplementing their work.
- **/orc-version** — set or increment the current project's version, draft a changelog entry from
  real git history, tag the commit, and optionally cut a real GitHub Release
  (`/orc-version release`).
- **/orc-help** (alias: **/orc**) — reports Orclab's own running version and a synopsis of its
  available commands.
- **/orc-git** — shortcuts for common git/GitHub operations: connect a repo, commit with a
  drafted message, push, commit-then-push (alias `cp`), branch/switch, and check out a PR.
- **/orc-publish** — push a project's built artifacts to its own configured distribution
  channels (PPA, Snap Store, Flathub, npm, etc.), resolved from `.orclab/publish/channels.yaml`
  and `distro.yaml`. Ships as a skill only — see `CLAUDE.md` for why.
- **/orc-release** — drive this project's own `RELEASING.md` end to end: ordered steps, real
  gates, human-step handoffs, and a position cursor so a release survives across sessions. Halts
  on failure. Ships as a skill only.
- **/orc-reload** — reinstall the plugin you're currently developing so a fresh session picks up
  your changes, distinguishing the several causes that all look like "the reinstall didn't work"
  and verifying the expected version actually landed. Works for any plugin project, not just
  Orclab. Ships as a skill only.

## Installing

Register this directory as a local plugin marketplace, then install the plugin:

    /plugin marketplace add ~/projects/orclab
    /plugin install orclab@orclab

**Every `/orc-*` component is a skill** (`skills/<name>/SKILL.md`). Orclab briefly shipped a
parallel `commands/*.md` layer as well; that was removed in v0.10.0 once the docs settled the
question — `commands/` is the legacy flat form of a skill, and a skill wins any name collision,
so the command files were shadowed by their own wrappers everywhere. See `CLAUDE.md` for the full
story and the design checklist it produced.

## Status

v1 (process core) + v2 (`/orc-code`) + v3 (`/orc-version`, `/orc-help`/`/orc`) + v4 (`/orc-git`) +
v5 (`currency-discipline`, `verify-before-asserting`) + v6 (Desktop-compatible skill wrappers for
every `/orc-*` command) + v7 (`/orc-publish`) + v8 (`/orc-release`) + v9 (`/orc-reload`) shipped.
See `docs/superpowers/specs/` for the design history,
`CHANGELOG.md` for what actually changed release to release, and `BACKLOG.md`
for what's deliberately deferred (real per-stack defaults research is #4, `/orc-data` is #5,
hook-based enforcement is #3, per-language manifest version-sync is #6, distribution-channel
metrics is #7, stale VERIFICATION.md version literals is #8). See `VERIFICATION.md` for the
dogfood script that confirms everything actually works once installed in a real project.

## Developing Orclab

See `CLAUDE.md` for real, verified guidance on how Claude Code's command/skill system actually
works — commands vs. skills, invocation determinism, `disable-model-invocation`, sub-skill
isolation, and bundling scripts — learned while building `/orc-code` through `/orc-git`. Read it
before designing the next `/orc-*` command or skill.
