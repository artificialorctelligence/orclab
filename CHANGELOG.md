# Changelog

All notable changes to this project are documented here, newest first.

## [0.4.0] - 2026-09-05

### Added
- `/orc-git` — shortcuts for common git/GitHub operations: connect a repo (`repo <url>`), commit
  with a drafted message (`commit`), push (`push`), commit-then-push (`commit-push`/`cp`),
  branch/switch (`branch`/`switch`), and check out a PR (`pr <id>`). The first command to actually
  populate `.orclab/` (a connected repo's URL), reserved since v3 but unused until now.

## [0.3.0] - 2026-09-05

### Added
- `/orc-version` — set or increment the current project's version, draft a changelog entry from
  real git history, tag the commit, and optionally cut a real GitHub Release (`/orc-version
  release`).
- `/orc-help` (and `/orc` as an alias) — reports Orclab's own running version and a synopsis of
  its available commands, aware of whether it's running in Orclab's own repo or a project that
  has it installed.
- The `.orclab/` directory convention — reserved as a future, per-project home for Orclab's own
  private bookkeeping. Not yet created, populated, or gitignored by anything in this release —
  decided as a convention for later use, not built yet.
