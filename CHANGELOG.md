# Changelog

All notable changes to this project are documented here, newest first.

## [0.6.0] - 2026-09-06

### Added
- A matching `skills/<name>/SKILL.md` for each of the five `/orc-*` commands (`orc-code`,
  `orc-version`, `orc-help`, `orc`, `orc-git`) — each a thin pointer to its real `commands/*.md`
  content, mirroring `orc.md`'s own existing pattern. Fixes a real, confirmed bug: the Claude
  Desktop client never registered plugin `commands/*.md` files as slash commands at all, so none
  of the `/orc-*` commands worked there even though the plugin showed installed. Skills don't have
  this problem — Desktop supports them. `commands/*.md` are unchanged and still serve the CLI.
- `CLAUDE.md` — real, verified guidance on Claude Code's command/skill system, used to design the
  five wrapper skills above: all five stay default-invocable (no `disable-model-invocation`),
  matching `/cat-code`-style dual invocation, since none of their primary behavior is a pure
  one-shot side effect the way the docs' own `/deploy` example is.

## [0.5.0] - 2026-09-06

### Added
- `currency-discipline` — checks that a chosen dependency, version, or technical approach is
  actually current, and that research relied on is checked for age, before trusting it. Names
  real verification mechanisms per ecosystem (registry APIs, official release pages), not just
  "check if it's current."
- `verify-before-asserting` — verifies a challenged factual/technical claim instead of defending
  it, and reinforces (without duplicating) superpowers' own `systematic-debugging` signal
  recognition and test-based root-cause localization.

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
