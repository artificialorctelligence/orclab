# Orclab v3: /orc-version, /orc-help, /orc Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three new commands to Orclab — `/orc-version` (set/increment the current project's version, draft a changelog from git history, tag, optionally release), `/orc-help` (report Orclab's own version and command synopsis, aware of core vs. project context), and `/orc` (a thin alias pointer to `/orc-help`) — and establish the `.orclab/` directory as a reserved, not-yet-populated convention.

**Architecture:** Three new command files at the plugin root, following the same shape as `commands/orc-code.md`. `/orc-help` reuses `/orc-code`'s Plugin-Discovery Procedure conceptually (searching the same known install roots) to locate Orclab's own installed files. `/orc.md` is a two-line pointer to `orc-help.md`, working around the confirmed absence of a native command-alias mechanism. Orclab's own version gets bumped to 0.3.0 as part of shipping this, manually establishing `CHANGELOG.md` in the exact format `/orc-version` is designed to produce going forward.

**Tech Stack:** Markdown (command content), JSON (plugin manifests), git (tags). No code, no test framework — same as v1/v2, this is natural-language instructions shaping Claude's own behavior. Verification is mechanical content checks plus a written dogfood script.

**Spec:** `docs/superpowers/specs/2026-09-05-orclab-v3-orc-version-orc-help-design.md`

## Global Constraints

- `/orc-version` operates on "the current project" — checks `.claude-plugin/plugin.json` first, falls back to the most recent `v*` git tag, falls back to "no version yet" if neither exists.
- The stored version is always three-part (`X.Y.Z`) — a two-part absolute-set input (`X.Y`) is stored with `Z` defaulting to `0`.
- Incrementing a component resets everything to its right to `0`: major resets minor+point; minor resets point; point resets nothing.
- The version-bump behavior (absolute-set or increment) is **local only** — no `git push`, no GitHub Release. Only `/orc-version release` pushes and creates a Release, and only when explicitly invoked.
- The changelog draft must be shown to the user with a question before being finalized — never written silently.
- `marketplace.json`'s `plugins[0].version` field must be added if missing, not just updated if present (a confirmed real gap — omitting it causes Claude Code's installer to record the plugin's version as literal `"unknown"`).
- `/orc-help`'s core-vs-project context check is based on the current working directory, not on where Orclab's installed files happen to live.
- No command in this plan may declare a `model:` frontmatter field (commands, like skills, don't take one).
- The `.orclab/` directory is decided as a convention in this plan but not created or populated by anything in it.

---

## File Structure

```
orclab/
  commands/
    orc-version.md      (new)
    orc-help.md          (new)
    orc.md               (new)
  .claude-plugin/
    plugin.json           (modified: version bump to 0.3.0)
    marketplace.json       (modified: version bump to 0.3.0)
  CHANGELOG.md             (new: first entry, in the format /orc-version will use going forward)
  README.md                (modified: mention the three new commands)
  VERIFICATION.md          (modified: new /orc-version and /orc-help scenarios)
```

---

### Task 1: `/orc-version` command

**Files:**
- Create: `commands/orc-version.md`

**Interfaces:**
- Consumes: nothing (first task of this plan).
- Produces: a complete `/orc-version` command. No other task in this plan depends on its internal content — Task 3's version bump is performed manually by the plan author, not by invoking this command (this command can't be exercised live until Orclab is reinstalled in a fresh session).

- [ ] **Step 1: Write `commands/orc-version.md`**

```markdown
---
description: Set or increment the current project's version, draft a changelog entry from real git history, tag the commit, and optionally cut a real GitHub Release.
argument-hint: <major>.<minor>[.<point>] | increment <major|minor|point> | release [tag]
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

2. **Update manifests, if present.**
   - If `.claude-plugin/plugin.json` exists, update its `"version"` field to the new version.
   - If `.claude-plugin/marketplace.json` also exists, update its `plugins[0].version` field to
     the new version too — **add the field if it doesn't already exist**. (A real, confirmed gap:
     omitting this field causes Claude Code's own plugin installer to record the plugin's version
     as the literal string `"unknown"`, with a genuinely broken install directory to match — this
     isn't cosmetic.)

3. **Commit.**
   ```bash
   git add CHANGELOG.md .claude-plugin/plugin.json .claude-plugin/marketplace.json
   git commit -m "Bump version to X.Y.Z"
   ```
   (Only `git add` the manifest files if they actually exist and were updated.)

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
```

- [ ] **Step 2: Verify frontmatter and required sections**

```bash
python3 -c "
import re
text = open('commands/orc-version.md').read()
m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
assert m, 'no frontmatter block found'
assert 'description:' in m.group(1)
assert 'argument-hint:' in m.group(1)
assert 'model:' not in m.group(1)
for section in ['## Step 0: Determine the current version', '## Step 1: Parse \$ARGUMENTS and route', '## Bare Invocation', '## Absolute-Set Flow', '## Increment Flow', '## Apply the new version', '## Release Flow']:
    assert section in text, f'missing section: {section}'
print('OK: commands/orc-version.md frontmatter and all required sections present')
"
```
Expected: `OK: commands/orc-version.md frontmatter and all required sections present`

- [ ] **Step 3: Self-review against the spec's rules**

Confirm each of these is explicitly present in the file just written:
- [ ] States the three-tier current-version lookup (plugin.json → git tag → none yet)
- [ ] States the increment example matches the spec exactly (`0.1.4` + major → `1.0.0`)
- [ ] States the version-bump flow is local-only (no push, no release) and points to a separate `release` action
- [ ] States the changelog draft must be shown to the user with a question before finalizing
- [ ] States `marketplace.json`'s version field must be added if missing, not just updated
- [ ] States the Release Flow pushes before creating the release, and confirms the tag exists first

- [ ] **Step 4: Commit**

```bash
git add commands/orc-version.md
git commit -m "Add /orc-version command"
```

---

### Task 2: `/orc-help` and `/orc` commands

**Files:**
- Create: `commands/orc-help.md`
- Create: `commands/orc.md`

**Interfaces:**
- Consumes: nothing new from Task 1 (no shared content — `/orc-help` and `/orc-version` are independent commands).
- Produces: two complete commands. `orc.md`'s only job is pointing at `orc-help.md` by exact filename — Task 3's README update references both commands by name.

- [ ] **Step 1: Write `commands/orc-help.md`**

```markdown
---
description: Show Orclab's own running version and a synopsis of its available commands, noting whether you're currently in Orclab's own repo or a project that has it installed.
---

# /orc-help

## Step 1: Determine context

Check whether the CURRENT WORKING DIRECTORY contains `.claude-plugin/plugin.json` with
`"name": "orclab"`. If it does, you're inside Orclab's own repo — this is **core** context
(developing Orclab itself). If it doesn't, you're in some other project that has Orclab installed
as a plugin — this is **project** context. This checks where you currently are, not where
Orclab's installed plugin files happen to live — those can be different places.

## Step 2: Find Orclab's own installed files and report its version

Run the same discovery approach `/orc-code` uses for finding other plugins, applied to find
Orclab itself: search for every `.claude-plugin/plugin.json` file under
`~/.claude/plugins/marketplaces/` and `~/.claude/plugins/cache/`, and find the one whose `"name"`
field is exactly `orclab`. Its containing directory is Orclab's own installed root. Read that
file's `"version"` field.

If you're in core context (Step 1), this discovered location IS the current working directory —
report its version directly. If you're in project context, this discovered location is wherever
Orclab actually got installed from (which may differ from the current directory) — report its
version the same way.

## Step 3: List available commands

In the discovered plugin root from Step 2, list every file under `commands/*.md`. For each one,
read its `description` frontmatter field. Present a one-line synopsis per command, in this shape:

```
Orclab vX.Y.Z (running in <core|project> context)

Commands:
  /orc-code     — <real description field from orc-code.md>
  /orc-version  — <real description field from orc-version.md>
  /orc-help     — <real description field from orc-help.md>
  /orc          — <real description field from orc.md>
```

Always read the REAL `description` field from each real command file found in Step 3 — the
example above shows the format, not literal text to reuse. If a future command is added, it
appears here automatically because this step lists whatever `commands/*.md` files actually exist,
rather than a hardcoded list.
```

- [ ] **Step 2: Write `commands/orc.md`**

```markdown
---
description: Alias for /orc-help.
---

# /orc

Read the file `orc-help.md` in this same plugin's `commands/` directory in full, and follow its
instructions exactly, using the same `$ARGUMENTS` this invocation received.
```

- [ ] **Step 3: Verify frontmatter for both files**

```bash
python3 -c "
import re
for f in ['commands/orc-help.md', 'commands/orc.md']:
    text = open(f).read()
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    assert m, f'{f}: no frontmatter block found'
    assert 'description:' in m.group(1)
    assert 'model:' not in m.group(1)
    print(f'OK: {f} frontmatter valid')
"
```
Expected: `OK: commands/orc-help.md frontmatter valid` and `OK: commands/orc.md frontmatter valid`

- [ ] **Step 4: Self-review against the spec's rules**

Confirm each of these is explicitly present:
- [ ] `orc-help.md` states the context check is based on the current working directory, not the installed plugin's location
- [ ] `orc-help.md` states the command list is read live from real files, not hardcoded
- [ ] `orc.md` points at `orc-help.md` by exact filename and forwards `$ARGUMENTS`

- [ ] **Step 5: Commit**

```bash
git add commands/orc-help.md commands/orc.md
git commit -m "Add /orc-help command and /orc alias pointer"
```

---

### Task 3: Version bump, CHANGELOG.md, and README update

**Files:**
- Create: `CHANGELOG.md`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `README.md`

**Interfaces:**
- Consumes: Tasks 1 and 2's completed command files (README references them by name; the changelog entry describes what they are).
- Produces: Orclab at version `0.3.0`, tagged locally as `v0.3.0`. Task 4's verification scenarios reference this version and tag.

- [ ] **Step 1: Create `CHANGELOG.md`**

This is written by hand this one time, in the exact format `/orc-version` (Task 1) is designed to
produce going forward — establishing the file and the pattern together.

```markdown
# Changelog

All notable changes to this project are documented here, newest first.

## [0.3.0] - 2026-09-05

### Added
- `/orc-version` — set or increment the current project's version, draft a changelog entry from
  real git history, tag the commit, and optionally cut a real GitHub Release (`/orc-version
  release`).
- `/orc-help` (and `/orc` as an alias) — reports Orclab's own running version and a synopsis of
  its available commands, aware of whether it's running in Orclab's own repo or a project that
  has it installed.
- The `.orclab/` directory convention — reserved, gitignored, per-project home for Orclab's own
  future private bookkeeping (not yet populated by anything in this release).
```

- [ ] **Step 2: Update `.claude-plugin/plugin.json`**

Replace the entire file content with:

```json
{
  "name": "orclab",
  "description": "Project-discipline skills and commands distilled from real practice: backlog tracking, release checklists, live-environment registries, a deterministic /orc-code entry point for new-project, existing-project, and refactor work, and /orc-version for versioning the current project.",
  "version": "0.3.0",
  "author": {
    "name": "direflail"
  }
}
```

- [ ] **Step 3: Update `.claude-plugin/marketplace.json`**

Replace the entire file content with:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "orclab",
  "description": "Project-discipline skills and commands distilled from real practice: backlog tracking, release checklists, live-environment registries, a deterministic /orc-code entry point for new-project, existing-project, and refactor work, and /orc-version for versioning the current project.",
  "owner": {
    "name": "direflail"
  },
  "plugins": [
    {
      "name": "orclab",
      "description": "Project-discipline skills and commands distilled from real practice: backlog tracking, release checklists, live-environment registries, a deterministic /orc-code entry point for new-project, existing-project, and refactor work, and /orc-version for versioning the current project.",
      "version": "0.3.0",
      "source": "./"
    }
  ]
}
```

- [ ] **Step 4: Verify manifests and changelog**

```bash
python3 -c "
import json
p = json.load(open('.claude-plugin/plugin.json'))
m = json.load(open('.claude-plugin/marketplace.json'))
assert p['name'] == m['plugins'][0]['name'] == 'orclab'
assert p['version'] == m['plugins'][0]['version'] == '0.3.0'
assert m['plugins'][0]['source'] == './'
print('OK: plugin.json/marketplace.json valid, consistent, version 0.3.0, marketplace.json has a version field')
"
grep -c "## \[0.3.0\]" CHANGELOG.md
```
Expected: `OK: plugin.json/marketplace.json valid, consistent, version 0.3.0, marketplace.json has a version field`, then `1`

- [ ] **Step 5: Update `README.md`**

Find:
```
## Commands

- **/orc-code** — start a new project, add to an existing one, or refactor/migrate existing code.
  Routes deterministically to one of three flows, wrapping the `feature-dev` and
  `code-modernization` plugins where applicable rather than reimplementing their work.
```

Replace with:
```
## Commands

- **/orc-code** — start a new project, add to an existing one, or refactor/migrate existing code.
  Routes deterministically to one of three flows, wrapping the `feature-dev` and
  `code-modernization` plugins where applicable rather than reimplementing their work.
- **/orc-version** — set or increment the current project's version, draft a changelog entry from
  real git history, tag the commit, and optionally cut a real GitHub Release
  (`/orc-version release`).
- **/orc-help** (alias: **/orc**) — reports Orclab's own running version and a synopsis of its
  available commands.
```

Find:
```
## Status

v1 (process core) + v2 (`/orc-code`) shipped. See `docs/superpowers/specs/` for the design history
and `BACKLOG.md` for what's deliberately deferred (real per-stack defaults research is #4,
`/orc-data` is #5, hook-based enforcement is #3). See `VERIFICATION.md` for the dogfood script
that confirms everything actually works once installed in a real project.
```

Replace with:
```
## Status

v1 (process core) + v2 (`/orc-code`) + v3 (`/orc-version`, `/orc-help`/`/orc`) shipped. See
`docs/superpowers/specs/` for the design history, `CHANGELOG.md` for what actually changed release
to release, and `BACKLOG.md` for what's deliberately deferred (real per-stack defaults research is
#4, `/orc-data` is #5, hook-based enforcement is #3, per-language manifest version-sync is #6). See
`VERIFICATION.md` for the dogfood script that confirms everything actually works once installed in
a real project.
```

- [ ] **Step 6: Commit and tag**

```bash
git add CHANGELOG.md .claude-plugin/plugin.json .claude-plugin/marketplace.json README.md
git commit -m "Bump version to 0.3.0, add CHANGELOG.md"
git tag v0.3.0
```

Do NOT push the tag or create a GitHub Release — that matches `/orc-version`'s own designed
behavior (local-only bump, release is a separate explicit step) and is out of scope for this task.

---

### Task 4: Dogfood verification scenarios

**Files:**
- Modify: `VERIFICATION.md`

**Interfaces:**
- Consumes: the completed commands from Tasks 1-2 and the version state from Task 3.
- Produces: a complete verification script covering v1, v2, and v3. No later task depends on this.

- [ ] **Step 1: Add new scenarios to `VERIFICATION.md`**

Find:
```
## Recording the result
```

Replace with:
```
## Scenario 9: /orc-version increment, local-only

1. In Orclab's own repo, run `/orc-version increment major`.
2. **Expected:** since the current version is `0.3.0`, the result is `1.0.0` — both `plugin.json`
   and `marketplace.json`'s version fields update to `"1.0.0"`, a changelog entry is drafted from
   real git history since the `v0.3.0` tag, you're asked whether to add/change anything before
   it's written, and a new commit + local tag `v1.0.0` are created.
3. **Expected throughout:** nothing is pushed anywhere, and no GitHub Release is created — confirm
   with `git log origin/main..HEAD` that the new commit hasn't reached the remote.
4. Revert this probe afterward (`git reset --hard v0.3.0` — a real, deliberate throwaway test, not
   a change to keep) unless you actually want to keep the bump.

## Scenario 10: /orc-version bare invocation

1. In Orclab's own repo, run `/orc-version` with no arguments.
2. **Expected:** the current version (`0.3.0`, or whatever it's been bumped to) is reported,
   followed by the increment/set menu — and nothing else happens; no files change.

## Scenario 11: /orc-version release

1. After running Scenario 9 (or any real bump) and deciding to keep it, run
   `/orc-version release`.
2. **Expected:** the commit and tag get pushed to `origin`, and a real GitHub Release is created
   at `https://github.com/artificialorctelligence/orclab/releases` — confirm by checking that URL
   or via `gh release list`.

## Scenario 12: /orc-help in core vs. project context

1. In Orclab's own repo, run `/orc-help`.
2. **Expected:** reports "core" context, the real current version, and a live-read synopsis of
   all commands present in `commands/*.md` at the time it's run (not a stale hardcoded list).
3. In a different project that has Orclab installed (e.g. Orcshot, once dogfooded there), run
   `/orc-help` again.
4. **Expected:** reports "project" context, the same Orclab version as step 1 (assuming no bump
   happened in between), and the same command synopsis.
5. Run `/orc` (bare) in either location.
6. **Expected:** identical output to `/orc-help` in the same location.

## Recording the result
```

- [ ] **Step 2: Commit**

```bash
git add VERIFICATION.md
git commit -m "Add /orc-version and /orc-help dogfood scenarios to verification script"
```

---

## Self-Review Notes (from writing this plan)

- **Spec coverage:** all three commands covered (Tasks 1-2), version storage/authoritative-source
  logic covered in Task 1's command content, changelog-drafting mechanism covered, GitHub Release
  flow covered, `.orclab/` convention explicitly addressed (decided, not populated — Global
  Constraints states this plainly, no task creates the directory), version bump + dogfooding
  bootstrap covered (Task 3), verification scenarios cover all three commands' real behaviors
  (Task 4). BACKLOG #6 (per-language manifest sync) correctly absent from this plan — deferred.
- **Placeholder scan:** no TBD/TODO; every content block is complete, not a stub.
- **Consistency check:** the increment example (`0.1.4` + major → `1.0.0`) matches the spec
  exactly. `marketplace.json`'s version field is added (not assumed pre-existing) consistently in
  both Task 1's command content and Task 3's actual manifest update. The version bump target
  (`0.3.0`) is consistent between Task 3's manifest edits, its `CHANGELOG.md` entry, its git tag,
  and Task 4's verification scenarios (which reference `0.3.0` as the pre-bump baseline). Command
  names (`/orc-code`, `/orc-version`, `/orc-help`, `/orc`) are spelled identically everywhere they
  appear across all four tasks.
