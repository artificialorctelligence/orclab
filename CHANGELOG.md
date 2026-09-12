# Changelog

All notable changes to this project are documented here, newest first.

## [0.16.0] - 2026-09-11

### Added
- Four `/orc-package` ingredients beside the PPA one, each saying in its first paragraph how far
  it has been proven: **Google Play** and the **Apple App Store**, researched against the stores'
  own live pages with no release through them yet; the **Snap Store** and **Flathub**, stood up
  for Orcshot up to the first upload/submission. Play carries the closed-test gate on new personal
  accounts, target API 36, 16 KB page alignment and the Data Safety form, publishes via fastlane
  with a real dry run, and reads installs from the Play stats bucket; the App Store carries the
  macOS requirement as a `local` / `cloud` choice of leaf shape, Xcode 26 and the privacy
  manifest, uploads with `altool`, and ships `appstore-status.py`, whose `state` mode makes
  `--confirm` report `READY_FOR_SALE` programmatically.
- Five background stack skills, `user-invocable: false`, read by Claude whenever that stack is in
  play: `stack-flutter`, `stack-android-native` (Kotlin + Compose), `stack-ios-native` (Swift +
  SwiftUI), `stack-unity` and `stack-godot`. Each states the current toolchain with dates, where
  things live in the project, and — the reason they exist — a table per store mapping each rule the
  ingredient states to the file where it is satisfied and the check that proves it.
  `/orc-code`'s Defaults Table gains a row per stack pointing at its skill.
- A ninth ingredient section, `## 5. Per-app setup`: what has to be done once per app, before its
  first release, and is neither registration nor a per-release act — a store listing, privacy
  declarations, Play's 12-testers-for-14-days gate, Apple's age rating. Section 1 now also states
  what machine can build the artifact.

### Changed
- Orclab now ships researched, live-verified knowledge for stores nobody here has shipped
  through, reversing the v15 spec's "capture is how they arrive" non-goal (BACKLOG #33). Such an
  ingredient carries a marker saying no release has gone through it; capture becomes how the
  first real release corrects it.

### Fixed
- `/orc-publish`'s metrics table: the Flathub row is confirmed live (against `org.gimp.GIMP`) and
  prints three totals instead of the raw body; the Snap row is marked "never run" — its metrics
  are confidential to the snap's publisher — rather than "unverified" (BACKLOG #7).

## [0.15.0] - 2026-09-10

### Added
- `/orc-package <channel>` — stand up a distribution channel by applying an *ingredient* (the
  reusable knowledge of how to set up a PPA, a store, a registry) to the project's own
  `channels.yaml`, `distro.yaml` and `RELEASING.md`. Ships the PPA ingredient, written from
  Orcshot's real channel, with the Launchpad series-copy script as a template. A channel it
  doesn't ship is captured into your own config directory through an interview, and a user-level
  ingredient shadows a shipped one. Runs only an ingredient's checks, never its account-gated
  setup; never writes or prints a credential.
- `/orc-git merge <branch>` — land a finished branch locally: refuses a dirty tree or a self-merge,
  runs the test suites before and after, removes the worktree, deletes the branch with `-d`. It
  decides nothing about whether merging was the right way to land.
- `/orc-git release [tag]` — push a tag and create its GitHub Release from the matching
  `CHANGELOG.md` section (moved here from `/orc-version`, see Changed).
- `/orc-version` with no arguments now proposes a bump — major, minor or point — and states the
  evidence that decided it, with the changelog entry that version would get, as one question. It
  never writes until you confirm; an override is honoured. On a `0.x` project a breaking change
  proposes minor and says it is breaking rather than declaring `1.0.0`.
- `/orc-publish --confirm` — for a channel whose publish is asynchronous (a remote build, a human
  review), checks whether an accepted publish has actually landed, and publishes nothing. A leaf
  declares `confirm:` with a `command` and/or a `url`; declaring it is what marks the publish
  asynchronous, and such a leaf reports `accepted` rather than `success` on a zero-exit action.
- A `PreToolUse` hook enforcing a model floor: a subagent dispatched below Sonnet to write code is
  rewritten to Sonnet, with a message naming what it replaced.
- `/orc-git` states which of its subcommands are plain git (`commit`, `push`, `branch`, `switch`,
  `merge`) and which need `gh` (`repo`, `pr`, `release`), and carries one rule for the irreversible
  ones: if you typed the command it runs; if reaching for it was Claude's idea, Claude says what
  it is about to run and waits for a yes.

### Changed
- **`/orc-version release` has moved to `/orc-git release`.** Typing the old form reports the move
  and stops; it does not run the release. `/orc-version` is now only about versions — every action
  it takes is local and reversible.
- `/orc-publish --dry-run`'s exit code is a verdict on the plan, not a receipt for printing it: it
  exits non-zero when the plan already names a refusal the real run would give (an unknown
  preflight rule, a missing artifact with no `prepare:`, a timed-out expansion). A wrapper doing
  `--dry-run && publish` now stops where a person reading the plan would.
- `/orc-todo add verification` writes the scenario into the checkout the command ran in, so a
  scenario written on a feature branch stays there until the branch lands. The number still comes
  from the one shared counter; `BACKLOG.md` entries still go to the main checkout. The discard
  guard now watches whichever checkout the command runs in.

### Fixed
- `orc-publish`: a non-string `action:`, `metrics:` or `prepare:` (`action: true` is valid YAML)
  is refused before anything runs, naming the leaf and the value — previously a traceback with no
  summary, and healthy siblings never attempted.
- `orc-publish`: the build-and-publish-in-one warning no longer misses an action that publishes,
  builds, then publishes again.
- Four small `/orc-todo` findings from its own review.

## [0.14.0] - 2026-09-09

### Added
- `/orc-todo` — look at and change the backlog: list what's open, read one entry in full, add or
  remove one, and set up lanes saying which work runs in what order.
- A number allocator holding a lock over one canonical file, so two agents working at once can't
  take the same `BACKLOG.md` or `VERIFICATION.md` number. One mechanism serves both files via a
  per-file descriptor. It writes the entry and stops — never commits, and never refuses because
  the file is dirty.
- A lane record of what work is in progress, and a `SessionStart` hook that tells a new session
  about it without anyone remembering to ask. This is the half a lock cannot cover: on 2026-09-08
  two sessions built the same feature for hours because nothing recorded that the first had
  started.
- A `PreToolUse` guard asking for consent before a command discards an uncommitted backlog entry —
  the price of the allocator not committing. It fires only when the command really can discard AND
  something is actually at risk.
- `/orc-release` now warns when renumbering a `RELEASING.md` step leaves a prose reference pointing
  past the end of the document.

### Changed
- `backlog-discipline` asks the allocator for a number instead of scanning the file for the highest
  one. That scan was a read-then-write race: on 2026-09-08 two agents both took `#23` and `#24`,
  following the rule exactly. It was racy, not ignored.
- `backlog-discipline`'s "don't turn this into a general task list" line is replaced by what it was
  actually protecting. It was written with no recorded rationale and described a file that doesn't
  exist — ten of twelve open entries were things that needed doing.
- `VERIFICATION.md`'s Scenario 1 no longer encodes the race in the verification script itself.

### Fixed
- `orc-publish`: a `preflight:` list containing a non-string item no longer crashes.

## [0.13.1] - 2026-09-08

### Fixed
- A scalar `preflight:` on a `/orc-publish` channel leaf is now read as one rule rather than one
  rule per character. `preflight: no-vcs` instead of `preflight: [no-vcs]` is an easy YAML slip,
  and it used to report `unknown preflight rule(s): n, o, -, v, c, s` — naming neither the real
  mistake nor anything actionable. A non-string scalar (`preflight: 5`) was worse: it raised
  `TypeError` out of the property itself, ahead of every caller's own containment, so one
  malformed leaf aborted the whole run and its healthy siblings never executed. It now refuses
  just that leaf.

## [0.13.0] - 2026-09-08

### Added
- Artifact preflight for `/orc-publish`. A channel leaf may now declare three optional fields:
  `prepare:` (a local, reversible command run before the gate — building the artifact),
  `artifact:` (the archive path to inspect, shell-expanded like `action:` already is, so a
  project can derive a version the way it already does, e.g.
  `../orcshot_$(dpkg-parsechangelog --show-field Version).tar.xz`), and `preflight:` (which
  named rule sets apply: `no-vcs`, `no-tool-state`, `no-prebuilt-binaries`). `/orc-publish` then
  runs **prepare → inspect → act** for a leaf declaring these.
- A new `refused` status, distinct from `failed` for the same reason `timed out` is: a tripped
  preflight rule means nothing was published, because what was about to go out was wrong — not
  that the publish attempt itself broke. Exits non-zero; sibling leaves still run. Offending
  entries in a report are capped at five with the real total shown (one motivating archive had
  3,061 of them).
- `orc_publish/inspect.py`, a new stdlib-only module that reads tar and zip archives for the
  preflight rules above. An archive in a format it can't read is refused, never silently passed.
- `--allow-preflight-failure`, which downgrades refusals to warnings for one run and still
  prints every finding. Deliberately has no config-level equivalent — an irreversible publish
  over a known-bad artifact should cost a deliberate keystroke every time.
- The `--dry-run` plan now reports everything the real run will refuse that it can already know
  at plan time: an unknown rule name, a missing `artifact:`, an artifact that will never exist.
  The plan is the list an operator consents to, so it must not approve a configuration that can
  only refuse.
- A warning — never a refusal, since it's a regex over a shell string — when one leaf's
  `action:` both builds and irreversibly publishes in a single command, since no gate can run
  between the two.
- `release-checklist` gained a rule: lint the artifact you are actually shipping, not a sibling
  of it. The motivating project linted its binary `.deb` clean every release while the *source*
  package it uploaded carried 1,415 then 1,882 `.git` entries into a public archive.

### Changed
- All subprocess spawning in `orc-publish` now goes through one `_run` helper carrying the
  process-group kill, so a compound command's grandchild can't be orphaned. The `--metrics`
  path added in 0.12.0 now shares it too.

### Removed
- `filename_template` and `render_filename`, shipped dead since v7 and superseded by
  `artifact:`.

Closes BACKLOG #21.

## [0.12.0] - 2026-09-08

### Added
- `--metrics` on `/orc-publish`, and a `metrics:` key on a channel leaf: a read-only report of
  the download/install numbers a distribution channel already publishes about itself. It runs
  the leaf's `metrics:` command instead of its `action:`, sharing the whole execution path —
  selection, timeout, process-group kill, output capture — so the only thing that differs is
  which key holds the command. Explicitly not telemetry: nothing is added to a project, and a
  channel with no public counter honestly reports having none, as
  `(known channel, no metrics source)`. Closes the researched half of BACKLOG #7.
- `metrics/launchpad_ppa.py`, the one channel needing real code. Launchpad counts per
  (package, version, series, architecture) publication and offers no archive-wide total, so
  reading one number means ~75 concurrent HTTP round trips. Anonymous and read-only.
  `--series` restricts it to one Ubuntu series, which is what stops two leaves of the same PPA
  from each reporting the same total. Confirmed live against a real PPA.
- `$ORC_PUBLISH_SCRIPTS`, exported to every leaf command, so a project's `channels.yaml` can
  call Orclab's bundled readers without knowing where the plugin is installed.
  `$CLAUDE_SKILL_DIR` was confirmed unset in contexts where those commands really run, so it
  cannot be relied on from a project's own config.

### Fixed
- `/orc-release`'s `**Run:**` marker kept only the command name and discarded the rest of the
  line, so a step reading `**Run:** /orc-version release` recorded `delegates_to` as
  `/orc-version` — a field naming a materially different action, since one sets a version and
  the other cuts a public GitHub Release. Closes BACKLOG #19.


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
