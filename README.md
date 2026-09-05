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

## Commands

- **/orc-code** — start a new project, add to an existing one, or refactor/migrate existing code.
  Routes deterministically to one of three flows, wrapping the `feature-dev` and
  `code-modernization` plugins where applicable rather than reimplementing their work.

## Installing

Register this directory as a local plugin marketplace, then install the plugin:

    /plugin marketplace add ~/projects/orclab
    /plugin install orclab@orclab

## Status

v1 (process core) + v2 (`/orc-code`) shipped. See `docs/superpowers/specs/` for the design history
and `BACKLOG.md` for what's deliberately deferred (real per-stack defaults research is #4,
`/orc-data` is #5, hook-based enforcement is #3). See `VERIFICATION.md` for the dogfood script
that confirms everything actually works once installed in a real project.
