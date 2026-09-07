# Changelog

All notable changes to this project are documented here, newest first.

## [0.11.0] - 2026-09-07

### Added
- `**One-time setup:**` — a fifth optional marker in `release-checklist`, for the step that
  happens once and then never again (registering a store name, submitting an app for review,
  creating a signing key, a per-machine config file). It must carry a checkable "how to tell it is
  already in place," to the same standard as `**Preconditions:**`.
- `/orc-release`'s rule for that marker: run **only** the check. Passing, say so and carry on;
  failing, stop, name what is missing, and ask whether the user wants it set up — asking whatever
  the setup itself needs. Setup commands never run unprompted. Standing up a distribution channel
  is always something the user asks for directly.
- A `timeout:` key on a `/orc-publish` channel leaf, a 600-second default, and a `--timeout`
  override for a whole run that a leaf's own value still beats. The dry-run plan prints each
  actionable leaf's effective timeout, so it appears in the list the user confirms.

### Changed
- A `/orc-publish` action that hangs now reports `timed out` — a status distinct from `failed` —
  with a detail naming the real limit and saying the action may be waiting on stdin. Because
  actions run with output captured, a passphrase prompt produces no visible prompt at all, so the
  timeout is often the only signal. The kill reaches the action's whole **process group**, not
  just the `/bin/sh -c` it started, and fires on interrupt as well as on timeout:
  `subprocess.run`'s own timeout kills only that shell, so a compound action like
  `dpkg-buildpackage && debsign && dput` would be reported as `timed out` while `dput` kept
  uploading — and a retry then double-uploads to a public archive. One consequence worth knowing
  about: the action now runs with no controlling terminal, so a gpg/pinentry passphrase prompt
  fails fast with its own error rather than hanging to the limit. Closes BACKLOG #11.
- A channel leaf with no `action:` reports as `(known channel, not yet actionable)` instead of
  `(no action set)`, matching the wording the distro tree already used for the same idea. A
  deliberate placeholder for a real but not-yet-onboarded channel no longer reads as an omission.

## [0.10.0] - 2026-09-07

### Added
- `skills/secret-hygiene/SKILL.md` — a discipline skill for keeping credentials out of the
  transcript. Covers why a printed secret is unrecoverable (it lands in the model's context,
  every subsequent API request, and the on-disk session JSONL at once), masked alternatives for
  the commands that emit credentials, verify-by-effect over verify-by-value, and the recovery
  procedure when one leaks anyway. Its description triggers on situations — debugging auth,
  reading config/env/logs — rather than intent, because nobody sets out to leak a secret.
- `hooks/hooks.json` and `hooks/scripts/secret_guard.py` — Orclab's first hook. A `PreToolUse`
  guard on `Bash` that denies the narrow set of commands whose entire stdout is a credential,
  naming the safe alternative in every denial so a block redirects the work instead of ending it.
  Fails open on any internal error; a `# orclab:allow-secret` marker bypasses it explicitly. 48
  tests, run with `cd hooks/scripts && python3 -m pytest tests/ -v`. Closes BACKLOG #3.

### Changed
- Every `/orc-*` component is now a skill. The five that had both a `commands/*.md` body and a
  wrapper skill were folded into their `SKILL.md`, carrying `argument-hint` across.
- `/orc-help`'s Step 3 enumerates a single source, `skills/orc*/SKILL.md` — no hyphen, so
  `skills/orc` is caught alongside `skills/orc-*` — and its merge-by-name branch is gone.
- `CLAUDE.md`'s commands-vs-skills guidance corrected against the primary docs, which describe
  `commands/` as "Skills as flat Markdown files. Use `skills/` for new plugins." Its previous
  claim that `commands/*.md` "stays for CLI use" was wrong: a skill wins any name collision, so
  each wrapper shadowed its own command file on the CLI too.
- Recorded two findings verified live rather than assumed: `claude plugin validate` does not
  check SKILL.md frontmatter (proven with a negative control), and a plugin skill's invocable
  name comes from its directory, not its `name:` field (proven against the installed `aikido`
  plugin).

### Removed
- The `commands/` directory.

## [0.9.0] - 2026-09-07

### Added
- `/orc-reload` — reinstalls the plugin in the current project so a fresh session picks up your
  latest changes. Built because "I changed the plugin, why is it still running the old version"
  has several genuinely different causes that all present identically: a `github`-sourced
  marketplace keeps a cached clone that does **not** refresh on reinstall, Desktop's Update button
  is often greyed out for a `directory`-sourced one, and a schema-invalid manifest reports a
  downstream symptom naming neither the field nor the validation. It distinguishes those, refuses
  to `reset --hard` anyone's checkout on their behalf, verifies the expected version actually
  landed rather than trusting a clean exit, and always ends by saying a reinstall cannot take
  effect in the running session. Ships as a skill only, and reads whatever plugin project it's
  invoked in — so it works for plugins other than Orclab.

### Fixed
- `find_project_root` now prefers the nearest `RELEASING.md` over the enclosing git root, so a
  subproject carrying its own release document inside a larger repo is no longer told that
  document doesn't exist.
- `/orc-release`'s `allowed-tools` narrowed from unscoped `Bash` back to `Read`,
  `Bash(python3 *)`, `Bash(git status *)`. Pre-approving arbitrary `Bash` removed the permission
  prompt from the project's own release commands — `dput`, `debuild` — which are precisely the
  irreversible operations that most deserve one. The prompt is the gate.
- The v8 spec listed `abort` as a release's only exit (the design error its own final review
  caught) and claimed `abort` rolls back commits and tags. It does neither — the CLI makes no git
  or shell call at all. Both corrected, with `finish` documented alongside `abort`.

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
  This is the first real per-format version handling in Orclab, covering the formats projects
  here actually use — it does not cover `pom.xml`, `package.json` or `Cargo.toml`, which is what
  BACKLOG #6 asked for, so that entry stays open for those.
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
