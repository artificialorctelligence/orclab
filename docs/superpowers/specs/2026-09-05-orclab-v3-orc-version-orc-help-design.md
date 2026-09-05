# Orclab v3: `/orc-version`, `/orc-help`/`/orc`, and the `.orclab/` foundation — design

## Goal

Give Orclab (and, by extension, any project it's pointed at) a real, deterministic way to manage
its own version — bump it, record what changed, tag it, optionally cut a real GitHub Release —
plus a way to ask "what version of Orclab am I running, and what commands does it have?" This
emerged directly from `/orc-code`'s own design conversation, once it became clear two different
version numbers were in play: the framework's own version, and the version of whatever project
the framework is being used on.

## Scope

**In scope now:**
- `/orc-version` — set or increment the *current project's* version (which, when run inside
  Orclab's own repo, means Orclab's own version — dogfooding, not a special case).
- `/orc-help` (and `/orc` as a thin pointer to it) — reports Orclab's own running version and a
  command synopsis, aware of whether it's running inside Orclab's own repo or a consuming project.
- The `.orclab/` directory convention — reserved, gitignored, per-project home for Orclab's own
  future private bookkeeping. Established now because it's foundational plumbing multiple future
  features will want, not because `/orc-version` itself needs to populate it yet.

**Explicitly out of scope for this spec, tracked separately:**
- Detecting and syncing version fields in established per-language manifests (Maven's `pom.xml`,
  npm's `package.json`, Cargo's `Cargo.toml`, etc.) when `/orc-version` runs on a project that has
  one. Real, valuable, and — like the stack-defaults research in BACKLOG #4 — too broad to fold in
  here without it swallowing the rest of this design. Tracked as BACKLOG #6.
- Any actual content living inside `.orclab/` — the directory's existence and purpose are decided
  here; what specifically gets cached there is deferred until a real feature needs it.

## Command surface: `/orc-version`

One command, `commands/orc-version.md`, three invocation shapes:

1. **Absolute set**: `/orc-version <major>.<minor>[.<point>]` — parses and assigns directly.
   `<point>` may be omitted (defaults to `0`); the stored version is always three-part
   (`1.2` → stored as `1.2.0`).
2. **Relative increment**: `/orc-version increment <major|minor|point>` — bumps the named
   component by 1, and **resets everything to its right to 0** (incrementing major resets minor
   and patch; incrementing minor resets patch; incrementing patch resets nothing, since nothing
   sits to its right). Example: `0.1.4` + `increment major` → `1.0.0`.
3. **Bare invocation**: `/orc-version` with no arguments — displays the current version and a
   short menu of what to run to bump it (`increment major`, `increment minor`, `increment point`,
   or set a specific version directly).

A fourth, separate form — `/orc-version release [tag]` — is a distinct action (see "GitHub
Release" below), not a version-setting operation itself.

## Determining "the current version"

Two real answers, tried in order:

1. If `.claude-plugin/plugin.json` exists in the current project (true for Orclab itself, and for
   any other Claude Code plugin `/orc-version` might be pointed at), its `"version"` field is
   authoritative for computing the *next* version, and gets updated alongside everything else.
2. Otherwise, the most recent `v*`-prefixed git tag reachable from `HEAD`
   (`git tag --list 'v*' --sort=-v:refname | head -1`) is the current version. If no such tag
   exists yet, there is no current version — the first `/orc-version` invocation on that project
   just establishes one.

**The git tag is the authoritative record, always** — `CHANGELOG.md`'s newest heading and
`plugin.json`'s `version` field (when present) are both meant to match it exactly, the same
relationship `plugin.json` and `marketplace.json` already have for Orclab's own name/description
fields. If they ever disagree, the tag is what's trusted.

## Version-bump behavior

Once a new version is determined (via either the absolute-set or increment form):

1. **Draft the changelog entry.** Find the git range since the last relevant point (the most
   recent `v*` tag, or the repository's first commit if none exists yet). Read the full commit
   messages in that range (not `--oneline` — the actual content lives in the message bodies) and
   condense them into a real entry, following the
   ["Keep a Changelog"](https://keepachangelog.com) convention: a `## [X.Y.Z] - YYYY-MM-DD`
   heading with only the `### Added` / `### Changed` / `### Fixed` / `### Removed` subsections
   that actually apply — never all four forced in in every entry. Show the drafted entry to the
   user and ask if they want to add or change anything before it's finalized. If `CHANGELOG.md`
   doesn't exist yet, scaffold it with a standard header first, matching every other file-writing
   skill in this project.
2. **Update manifests, if present.** If `.claude-plugin/plugin.json` exists, update its
   `"version"` field. If `.claude-plugin/marketplace.json` also exists, update its
   `plugins[0].version` field too — adding the field if it was missing entirely (a real gap found
   in Orclab's own `marketplace.json` during this design, confirmed to matter: the installed
   `playwright` plugin, which has no `version` field anywhere, gets recorded by Claude Code's own
   plugin installer as `"version": "unknown"` with a literal `unknown`-named install directory —
   real, observed dysfunction from omitting this field, not theoretical).
3. **Commit.** Stage the changed files (`CHANGELOG.md`, and the manifests if updated) and commit
   with the message `Bump version to X.Y.Z`.
4. **Tag.** Create a git tag `vX.Y.Z` pointing at that commit. **This step is local only** — no
   push happens here, and no GitHub Release gets created. Report the new version and tag, and
   mention `/orc-version release` as the separate, explicit next step if the user wants this
   version to actually become public.

## GitHub Release: `/orc-version release [tag]`

A separate, explicit action — never automatic on a version bump, per direflail's own call ("only
when asked," since a project might bump its version several times while iterating before anything
is actually ready to call a release).

1. Determine the target tag: the one named in `$ARGUMENTS`, or the most recent local tag if none
   given.
2. Confirm the tag exists locally; if not, report the error plainly rather than guessing what was
   meant.
3. Push the commit and tag to `origin` if they aren't already there (pushing is bundled into this
   explicit action, not the plain version-bump step — this is the one command that makes anything
   public, so it's the one that pushes).
4. Run `gh release create <tag>`, using the corresponding `CHANGELOG.md` section (if present) as
   the release notes body.
5. Report the real Release URL.

## `/orc-help` and `/orc`

`commands/orc-help.md`, no arguments:

1. **Determine context**: does the *current working directory* contain a
   `.claude-plugin/plugin.json` with `"name": "orclab"`? If yes, this is Orclab's own repo —
   "core" context (developing Orclab itself). If no, this is some other project with Orclab
   installed as a plugin — "project" context. This is a check on *where the user currently is*,
   not on where Orclab's installed files happen to live — those can be different places (e.g.
   Orclab installed via the marketplace mechanism while working in an unrelated project directory).
2. **Report Orclab's own running version**: locate Orclab's own installed plugin files via the
   same Plugin-Discovery Procedure `/orc-code` already uses (searching for a plugin named
   `orclab` specifically, across the same real install layouts already verified during `/orc-code`'s
   design), read its `plugin.json`'s `"version"` field, and report "Orclab vX.Y.Z."
3. **List available commands**: enumerate `commands/*.md` in Orclab's own discovered root, read
   each file's `description` frontmatter field, and present a one-line synopsis per command.
4. **State the context plainly** (core vs. project), from step 1.

`commands/orc.md`: a thin pointer, not a duplicate. Its entire content instructs Claude to read
`orc-help.md` (in this same plugin's `commands/` directory) and follow its instructions exactly,
passing along the same `$ARGUMENTS` — working around the real, confirmed absence of any native
command-aliasing mechanism in Claude Code (verified by scanning every real command file's
frontmatter across every installed plugin on this machine: only `allowed-tools`, `argument-hint`,
`description`, `disable-model-invocation`, and `hide-from-slash-command-tool` ever appear — no
`alias` field exists anywhere).

## The `.orclab/` directory

A reserved, gitignored, per-project directory — Orclab's own private bookkeeping space for
whatever project it's pointed at, distinct from that project's own git-tracked files. Established
now because it's foundational: any future Orclab feature that needs to remember something about a
specific project (a detected build system, an answer to an init question so it isn't re-asked
every time) needs a home, and `/orc-version` shouldn't be the one to invent that home ad hoc.

**Not populated by this spec.** `/orc-version`'s own lookups (checking for `plugin.json`, reading
the most recent git tag) are cheap single operations — caching them would be speculative
complexity with no real cost being solved yet. The directory's existence and purpose are decided
here; what actually goes in it waits for a feature that genuinely needs it. Nothing in this spec
creates the directory or adds a `.gitignore` entry for it — that happens whenever something first
needs to write there.

## Relationship to existing Orclab work

`/orc-version` and `/orc-help` are "core" category under direflail's own taxonomy (guidance/tooling
useful to every project Orclab touches, including Orclab itself) — not "project" category as
originally assumed when this idea first came up, since the whole point is that they operate on
"the current project," whatever that happens to be. No coupling to the three v1 skills or to
`/orc-code` beyond reusing the Plugin-Discovery Procedure pattern already proven there.

## Validation

Same dogfooding principle as v1 and v2 — no automated test suite applies to command content, so
validation is running `/orc-version` and `/orc-help` for real, in a fresh session, after
installing/reinstalling Orclab, confirming:
- `/orc-version increment major` on Orclab's own repo (currently `0.2.0`) produces `1.0.0`,
  updates both manifests, drafts a real changelog entry from actual git history, and creates a
  local-only tag.
- `/orc-version release` (run afterward, deliberately) pushes and creates a real GitHub Release,
  and *not* before that command is explicitly run.
- `/orc-help`, run inside Orclab's own repo, reports "core" context; run from a different
  directory (after installing Orclab there), reports "project" context — same running version
  either way.
- `/orc`, invoked directly, produces identical output to `/orc-help`.

This isn't written up as new `VERIFICATION.md` scenarios yet — that's an implementation-plan-level
detail, added the same way v1's and v2's were.
