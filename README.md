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

## Installing

Register this directory as a local plugin marketplace, then install the plugin:

    /plugin marketplace add ~/projects/orclab
    /plugin install orclab@orclab

## Status

v1 (process core) + v2 (`/orc-code`) + v3 (`/orc-version`, `/orc-help`/`/orc`) + v4 (`/orc-git`) +
v5 (`currency-discipline`, `verify-before-asserting`) shipped. See `docs/superpowers/specs/` for
the design history, `CHANGELOG.md` for what actually changed release to release, and `BACKLOG.md`
for what's deliberately deferred (real per-stack defaults research is #4, `/orc-data` is #5,
hook-based enforcement is #3, per-language manifest version-sync is #6, distribution-channel
metrics is #7). See `VERIFICATION.md` for the dogfood script that confirms everything actually
works once installed in a real project.
