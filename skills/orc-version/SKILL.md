---
name: orc-version
description: Use when the user explicitly asks to use orc-version, or types /orc-version, to set or increment the current project's version, draft a changelog entry, and tag the commit locally - or, with no arguments, to be told what bump the commits since the last tag suggest and why.
argument-hint: <major>.<minor>[.<point>] | increment <major|minor|point> [--no-commit]
---
# /orc-version

You are managing version numbers via the `/orc-version` command. This operates on the CURRENT
project — when run inside Orclab's own repo, "the current project" is Orclab itself; when run
inside any other project, it's that project.

## Step 0: Determine the current version

1. If `.claude-plugin/plugin.json` exists in the current project, read its `"version"` field —
   that's the current version.
2. Otherwise, find the most recent `v*`-prefixed git tag:
   ```bash
   git tag --list 'v*' --sort=-v:refname | head -1
   ```
   Strip the leading `v` — that's the current version.
3. If neither exists, there is no current version yet — treat this as the very first version
   being established.
4. **If both exist and disagree**: the most recent `v*` git tag is always authoritative — report
   both values plainly and use the tag's version as the current version, not `plugin.json`'s. A
   `plugin.json` that drifted out of sync (a hand-edit, a bad merge) should never silently become
   the new source of truth for computing the next version.

## Step 1: Parse $ARGUMENTS and route

1. If `$ARGUMENTS` starts with `release` — go to **Moved: release** below. Do not run anything.
2. If `$ARGUMENTS` starts with `increment ` — go to **Increment Flow** below.
3. If `$ARGUMENTS` matches a version pattern (`<digits>.<digits>` or `<digits>.<digits>.<digits>`)
   — go to **Absolute-Set Flow** below.
4. If `$ARGUMENTS` is empty — go to **Bare Invocation** below.

## Bare Invocation

Report the current version (from Step 0). If no current version exists yet, say so plainly and
show the four bump lines from the block below — everything after the `Apply …?` line — without
a proposal: there is no range to read.

Otherwise, **propose a bump, with the reason stated.** Read the commits since the most recent
`v*` tag — the same range the changelog draft uses:

```bash
git log <tag>..HEAD --format='%B---COMMIT-BOUNDARY---'
```

If the range is empty, say there is nothing since `<tag>` and show the four bump lines from the
block below, without the `Apply …?` line. If it is not, read
the messages (bodies, not just subjects) and classify what they describe:

- **major** — anything that removes or renames something a user of the project relies on: a
  command, a subcommand, a config key, a file format, a public function; or a message that says
  `BREAKING` or uses the `!:` subject convention.
- **minor** — otherwise, if anything was added: a new command, subcommand, option, skill, field,
  or capability.
- **point** — otherwise: only fixes, docs, refactors, tests.

If the current major is `0`, a breaking change proposes **minor** and the sentence says it is
breaking — `1.0.0` is a declaration a commit range cannot make.

State the proposal as a sentence that shows its evidence — the counts and one or two subjects
that decided it — for example: *"Since v0.14.0: 3 fixes (#24, #29, #30), 1 addition
(`/orc-package`), nothing removed — so **minor**: `0.14.0` → `0.15.0`."* Then ask:

```
Apply 0.15.0? Or pick another:
  /orc-version increment major   (resets minor and point to 0)
  /orc-version increment minor   (resets point to 0)
  /orc-version increment point
  /orc-version <major>.<minor>[.<point>]
```

**The proposal never writes a file.** If the user says yes, proceed to **Apply the new version**
with the proposed version exactly as if they had typed it. If they pick something else, honour
that instead. If they say nothing decisive, stop. Semver is a judgment about intent and commit
messages are evidence, not proof — a refactor described as a fix can still break a consumer —
which is why this proposes and never decides.

## Absolute-Set Flow

Parse `$ARGUMENTS` as `<major>.<minor>` or `<major>.<minor>.<point>`. If `<point>` is omitted,
treat it as `0`. The new version is exactly what was parsed (always stored as three-part, e.g.
`1.2` becomes `1.2.0`). Proceed to **Apply the new version** below.

## Increment Flow

Parse the target component from `$ARGUMENTS` (`major`, `minor`, or `point` — the word after
`increment `). Using the current version from Step 0 (if none exists yet, treat it as `0.0.0`
before incrementing):

- **major**: `major + 1`, reset minor to `0`, reset point to `0`.
- **minor**: major unchanged, `minor + 1`, reset point to `0`.
- **point**: major and minor unchanged, `point + 1`.

Example: current version `0.1.4`, `increment major` → `1.0.0`. Proceed to **Apply the new
version** below.

## Apply the new version

Once the new version string is determined (from either flow above):

1. **Draft the changelog entry.**
   - Determine the git range: from the most recent `v*` tag to `HEAD` (`<tag>..HEAD`), or from the
     repository's first commit to `HEAD` if no tag exists yet.
   - Read the full commit messages in that range (not `--oneline` — the real content is in the
     message bodies):
     ```bash
     git log <range> --format='%B---COMMIT-BOUNDARY---'
     ```
   - Condense these into a changelog entry following the
     ["Keep a Changelog"](https://keepachangelog.com) convention:
     ```markdown
     ## [X.Y.Z] - YYYY-MM-DD

     ### Added
     - <thing added, if anything was>

     ### Changed
     - <thing changed, if anything was>

     ### Fixed
     - <thing fixed, if anything was>
     ```
     Only include the `### Added`/`### Changed`/`### Fixed`/`### Removed` subsections that
     actually apply — never force in an empty section. Use today's real date for `YYYY-MM-DD`.
   - If `CHANGELOG.md` doesn't exist yet, create it first with this header:
     ```markdown
     # Changelog

     All notable changes to this project are documented here, newest first.
     ```
   - **Show the drafted entry to the user and ask: "Here's the changelog entry I drafted from the
     commit history — want to add or change anything before I write it?"** Incorporate their
     answer into the final entry. Do not skip this question — the whole point of auto-drafting is
     to save you from having to remember everything that happened, not to bypass your judgment on
     what's worth recording.
   - Prepend the finalized entry to `CHANGELOG.md`, directly below its header.

2. **Update every version-holding file.**

   Run Orclab's own version-file module rather than hand-editing — it is the single owner of
   version-setting, it handles each format's real syntax, and it is covered by real tests. The
   script lives at `<orclab plugin root>/skills/orc-release/scripts/run.py`, where the plugin
   root is two levels above this skill's own directory (`${CLAUDE_SKILL_DIR}/../..`):

   ```bash
   python3 <orclab plugin root>/skills/orc-release/scripts/run.py version-set X.Y.Z
   ```

   For a project with a `debian/changelog`, pass the changelog body too (the same content
   drafted in step 1, as Debian-style `*` bullets):

   ```bash
   python3 <...>/run.py version-set X.Y.Z --changelog-body '* What changed.'
   ```

   Supported formats: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
   `pyproject.toml`, `debian/changelog`. A project using none of them has no version file to
   update; say so plainly rather than inventing one.

   Then confirm every file agrees:

   ```bash
   python3 <...>/run.py version-verify
   ```

3. **Commit — unless `--no-commit` was passed.**

   If `$ARGUMENTS` contains `--no-commit`, **stop here**. Report the new version and which files
   were changed, and do not commit or tag. This exists because a real release process often
   separates setting the version from committing it: a packaged app builds, lints, publishes and
   install-tests against the uncommitted version edits, and commits only once the artifact is
   verified — so committing at bump time would leave a `Release vX.Y.Z` commit behind for every
   attempt that never released.

   Otherwise (the default, unchanged behavior):

   ```bash
   git add CHANGELOG.md .claude-plugin/plugin.json .claude-plugin/marketplace.json
   git commit -m "Bump version to X.Y.Z"
   ```

   (Only `git add` the files that actually exist and were updated.)

4. **Tag — local only.**
   ```bash
   git tag vX.Y.Z
   ```
   Do NOT push anything in this step. Report the new version and the tag, and mention that
   `/orc-git release` is the separate, explicit next step if this version should become a real,
   public GitHub Release — it lives under `/orc-git` because it pushes and publishes, which nothing
   in this command does.

## Moved: release

`/orc-version release` no longer exists. Say exactly this, and stop:

```
/orc-version release has moved to /orc-git release.

Everything else this command does is local and reversible - a manifest edit, a changelog entry,
a commit, a local tag. Pushing a tag and creating a GitHub Release is neither, and it now lives
with the other forge operations: /orc-git release [tag]
```

Do not run `/orc-git release` on the user's behalf. A redirect that names the new home teaches it;
one that quietly still works preserves the old habit.
