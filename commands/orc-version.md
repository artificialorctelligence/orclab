---
description: Set or increment the current project's version, draft a changelog entry from real git history, tag the commit, and optionally cut a real GitHub Release.
argument-hint: <major>.<minor>[.<point>] | increment <major|minor|point> | release [tag] [--no-commit]
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

1. If `$ARGUMENTS` starts with `release` — go to **Release Flow** below.
2. If `$ARGUMENTS` starts with `increment ` — go to **Increment Flow** below.
3. If `$ARGUMENTS` matches a version pattern (`<digits>.<digits>` or `<digits>.<digits>.<digits>`)
   — go to **Absolute-Set Flow** below.
4. If `$ARGUMENTS` is empty — go to **Bare Invocation** below.

## Bare Invocation

Report the current version (from Step 0). If no current version exists yet, say so plainly. Then
show this menu:

```
To bump the version:
  /orc-version increment major   (resets minor and point to 0)
  /orc-version increment minor   (resets point to 0)
  /orc-version increment point
Or set a specific version directly:
  /orc-version <major>.<minor>[.<point>]
```

Stop here — do not proceed to any bump logic on a bare invocation.

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
   root is the parent of the `commands/` directory this file lives in:

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
   `/orc-version release` is the separate, explicit next step if this version should become a
   real, public GitHub Release.

## Release Flow

1. Determine the target tag: the tag named in `$ARGUMENTS` after `release ` (e.g.
   `/orc-version release v1.2.0`), or the most recent local tag if none was given.
2. Confirm the tag exists locally:
   ```bash
   git tag --list '<tag>'
   ```
   If it doesn't exist, report this plainly and stop — do not guess what tag was meant.
3. Push the commit and tag to `origin` if they aren't already there:
   ```bash
   git push origin HEAD
   git push origin <tag>
   ```
4. Create the real GitHub Release, using the corresponding `CHANGELOG.md` section (if present) as
   the release notes body:
   ```bash
   gh release create <tag> --notes-file <path to a temp file containing that section's content>
   ```
   (Extract just that one version's section from `CHANGELOG.md` — from its `## [X.Y.Z]` heading
   to the next `## [` heading or end of file — into a temp file first, then pass that file's path.)
5. Report the real Release URL that `gh release create` prints.
