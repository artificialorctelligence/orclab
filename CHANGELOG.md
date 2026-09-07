# Changelog

All notable changes to this project are documented here, newest first.

## [0.8.0] - 2026-09-07

### Added
- `/orc-release` — drives a project's own `RELEASING.md` end to end: reads the whole document
  before acting, walks its steps in real dependency order, halts on failure (deliberately the
  opposite of `/orc-publish`, since release steps are a dependent chain and publish channels are
  independent siblings), stops for human-performed steps, and tracks position across sessions in
  `.orclab/release/state.json` — a cursor holding only *where* a release is, never a second copy
  of its steps.
- Version-lifecycle handling across a whole release: per-format read/write for `pyproject.toml`,
  `debian/changelog`, `.claude-plugin/plugin.json` and `marketplace.json`; consistency
  verification after setting; and rollback on abort that reports plainly what it cannot undo.
  Closes BACKLOG #6.
- `/orc-version --no-commit` — sets the version without committing, so a release can build, lint,
  publish and install-test against the uncommitted edits and commit only once the artifact is
  verified. The previous behavior (bump, commit, tag as one move) is unchanged by default.

### Changed
- `release-checklist` documents four optional step markers — preconditions, performed-by-hand,
  delegation, and irreversible — all backward-compatible, since a document using none of them
  stays fully driveable.

## [0.7.0] - 2026-09-06

### Added
- `/orc-publish` — resolves a project's own `.orclab/publish/channels.yaml` (and, for a
  distro-scoped query via `--for`, `distro.yaml`) into a concrete list of publish actions, shows
  it before doing anything, executes it, and reports per-leaf success/failure/not-attempted.
  Ships as a skill only (no separate `commands/orc-publish.md`) — the first `/orc-*` component
  designed knowing skills already work on both CLI and Desktop, so there's no reason to create a
  commands file that would need its own wrapper just to work everywhere. See
  `docs/superpowers/specs/2026-09-06-orclab-v7-orc-publish-design.md` for the full design,
  including why distro and channel are modeled as two separate trees rather than one.
- Orclab's own repo ships zero real channel/distro content for any project, Orcshot included —
  populating a real project's `.orclab/publish/` trees is a separate follow-on task.

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
