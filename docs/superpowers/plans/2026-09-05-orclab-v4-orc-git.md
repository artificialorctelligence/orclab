# Orclab v4: /orc-git Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/orc-git` to Orclab — shortcuts for connecting a repo, committing, pushing, branching, and checking out PRs — and bump Orclab to 0.4.0 with a real `CHANGELOG.md` entry.

**Architecture:** One new command file, `commands/orc-git.md`, following the same shape as the other `commands/*.md` files. Every subcommand (`repo`, `commit`, `push`, `commit-push`/`cp`, `branch`/`switch`, `pr`) is routed within this one file via `$ARGUMENTS` — no separate command files or alias workaround needed, since (unlike `/orc` in v3) none of these need to be typed as their own bare top-level slash command.

**Tech Stack:** Markdown (command content), JSON (plugin manifests), git/gh CLI commands (real, standard operations — `git remote`, `git clone`, `git add`/`commit`/`push`, `git switch`, `gh auth`, `gh pr checkout`). No code, no test framework — same as v1-v3.

**Spec:** `docs/superpowers/specs/2026-09-05-orclab-v4-orc-git-design.md`

## Global Constraints

- `/orc-git repo <url>` must never silently overwrite a differing existing `origin` remote — it must show the current value and ask for confirmation first.
- `/orc-git repo <url>` must correctly distinguish three directory states: already a repo, empty non-repo directory, non-empty non-repo directory — the third case must ask rather than guess.
- `/orc-git commit` stages everything (`git add -A`), reports plainly and stops on a clean tree (no empty commit), drafts a message from the real diff, and folds in any `[extra text]` as an addition rather than a replacement — **no confirmation pause**, a deliberate difference from `/orc-version`'s changelog step.
- `/orc-git push` never prompts for confirmation — invoking it is the authorization.
- `commit-push` and `cp` must run identical behavior to each other; `branch` and `switch` must run identical behavior to each other.
- The connected repo URL is saved to `.orclab/git-repo.json` — the first real content `.orclab/` has ever held. A `.gitignore` entry for `.orclab/` must be added if one doesn't already exist, without duplicating an existing entry.
- `commands/orc-git.md` must not declare a `model:` frontmatter field.

---

## File Structure

```
orclab/
  commands/
    orc-git.md          (new)
  .claude-plugin/
    plugin.json           (modified: version bump to 0.4.0)
    marketplace.json       (modified: version bump to 0.4.0)
  CHANGELOG.md             (modified: new entry)
  README.md                (modified: mention /orc-git)
  VERIFICATION.md          (modified: new /orc-git scenarios)
```

---

### Task 1: `/orc-git` command, version bump, and CHANGELOG

**Files:**
- Create: `commands/orc-git.md`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `CHANGELOG.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: nothing (first task of this plan).
- Produces: a complete `/orc-git` command, Orclab at version `0.4.0`. Task 2's verification scenarios reference this command's real behavior and the new version.

- [ ] **Step 1: Write `commands/orc-git.md`**

```markdown
---
description: Shortcuts for common git/GitHub operations - connect a repo, commit, push, branch, and check out PRs - so you don't have to remember or type the full commands each time.
argument-hint: repo <url> | commit [text] | push | commit-push [text] | cp [text] | branch <name> | switch <name> | pr <id>
---

# /orc-git

You are running git/GitHub shortcuts via the `/orc-git` command. Route based on the first word of
`$ARGUMENTS`.

## Bare invocation (no arguments)

List the available subcommands:

```
/orc-git subcommands:
  repo <url>          — connect the current project to a GitHub repo
  commit [text]        — stage everything and commit with a drafted message
  push                 — push the current branch
  commit-push [text]   — commit, then push (alias: cp)
  cp [text]            — alias for commit-push
  branch <name>        — switch to a branch, creating it if it doesn't exist (alias: switch)
  switch <name>        — alias for branch
  pr <id>              — check out an existing pull request by number
```

Stop here — do not proceed to any subcommand logic on a bare invocation.

## repo <url>

1. **Ensure GitHub auth**: run `gh auth status`. If it reports not logged in, run `gh auth login`
   first. If already authenticated, continue.
2. **Determine the current directory's git state**:
   - **Already a git repo** (`git rev-parse --git-dir` succeeds): check the current `origin`
     remote with `git remote get-url origin` (this may fail if none is set — that's fine).
     - No `origin` set: run `git remote add origin <url>`.
     - `origin` already set and matches `<url>`: nothing to change, report that it's already
       connected.
     - `origin` already set and differs from `<url>`: show the current value plainly and ask for
       explicit confirmation before running `git remote set-url origin <url>` — never silently
       overwrite a differing existing remote.
   - **Not a git repo, and the directory is empty**: run `git clone <url> .`.
   - **Not a git repo, and the directory has files**: ask directly whether to clone `<url>` into a
     new subdirectory (named after the repo) instead, or initialize the current directory as a git
     repo with `<url>` set as `origin` via `git init && git remote add origin <url>` (without
     pulling any history). Don't guess between these two outcomes.
3. **Save the connection**: create `.orclab/` if it doesn't exist, and write
   `.orclab/git-repo.json` with this exact content (substituting the real URL):
   ```json
   {"url": "<url>"}
   ```
   If `.gitignore` doesn't already contain a `.orclab/` entry, append one on its own line — check
   first with a search so you don't add a duplicate entry if one's already there.

## commit [text]

1. Stage everything: `git add -A`.
2. Check what's staged: `git diff --cached --stat`. If nothing is staged (a clean tree), report
   this plainly and stop — do not attempt an empty commit.
3. Draft a real commit message from the actual staged changes (`git diff --cached --stat` and
   `git diff --cached` for content) — describe what genuinely changed, not a generic placeholder.
4. If `$ARGUMENTS` has text after `commit` (or after `commit-push`/`cp`, when this behavior is
   reused by those subcommands below), fold that text into the drafted message as an addition —
   append it, don't replace the drafted content with it.
5. Commit: `git commit -m "<final message>"`. No confirmation pause before committing — this
   subcommand doesn't ask before finalizing, unlike `/orc-version`'s changelog step.

## push

1. Determine the current branch: `git branch --show-current`.
2. Check if it has an upstream: `git rev-parse --abbrev-ref <branch>@{upstream}` (this fails if
   there's no upstream set — that's the signal to use the second command below instead of the
   first).
   - Has an upstream: `git push`.
   - No upstream: `git push -u origin <branch>`.
3. No confirmation prompt — invoking this command directly is the authorization.

## commit-push [text] / cp [text]

Run the full **commit** behavior above (including the same `[text]` folding-in behavior), then
run the full **push** behavior above. Both subcommand names run this identical sequence.

## branch <name> / switch <name>

Both subcommand names run this identical logic:
1. Check if the branch exists: `git show-ref --verify --quiet refs/heads/<name>`.
2. If it exists: `git switch <name>`.
3. If it doesn't: `git switch -c <name>`.

## pr <id>

Run `gh pr checkout <id>` — this requires the same GitHub authentication already covered by the
`repo` subcommand's Step 1.
```

- [ ] **Step 2: Verify frontmatter and required sections**

```bash
python3 -c "
import re
text = open('commands/orc-git.md').read()
m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
assert m, 'no frontmatter block found'
assert 'description:' in m.group(1)
assert 'argument-hint:' in m.group(1)
assert 'model:' not in m.group(1)
for section in ['## Bare invocation (no arguments)', '## repo <url>', '## commit [text]', '## push', '## commit-push [text] / cp [text]', '## branch <name> / switch <name>', '## pr <id>']:
    assert section in text, f'missing section: {section}'
print('OK: commands/orc-git.md frontmatter and all required sections present')
"
```
Expected: `OK: commands/orc-git.md frontmatter and all required sections present`

- [ ] **Step 3: Self-review against the spec's rules**

Confirm each of these is explicitly present in the file just written:
- [ ] States the three-way directory-state handling for `repo <url>` (existing repo, empty dir, non-empty non-repo dir)
- [ ] States that a differing existing `origin` requires explicit confirmation before being overwritten
- [ ] States `commit` stops plainly on a clean tree rather than attempting an empty commit
- [ ] States `commit` has no confirmation pause, unlike `/orc-version`'s changelog step
- [ ] States `push` has no confirmation prompt
- [ ] States `.orclab/git-repo.json`'s exact content shape and the `.gitignore` entry requirement

- [ ] **Step 4: Update `.claude-plugin/plugin.json`**

Replace the entire file content with:

```json
{
  "name": "orclab",
  "description": "Project-discipline skills and commands distilled from real practice: backlog tracking, release checklists, live-environment registries, a deterministic /orc-code entry point for new-project, existing-project, and refactor work, /orc-version for versioning the current project, and /orc-git for common git/GitHub shortcuts.",
  "version": "0.4.0",
  "author": {
    "name": "direflail"
  }
}
```

- [ ] **Step 5: Update `.claude-plugin/marketplace.json`**

Replace the entire file content with:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "orclab",
  "description": "Project-discipline skills and commands distilled from real practice: backlog tracking, release checklists, live-environment registries, a deterministic /orc-code entry point for new-project, existing-project, and refactor work, /orc-version for versioning the current project, and /orc-git for common git/GitHub shortcuts.",
  "owner": {
    "name": "direflail"
  },
  "plugins": [
    {
      "name": "orclab",
      "description": "Project-discipline skills and commands distilled from real practice: backlog tracking, release checklists, live-environment registries, a deterministic /orc-code entry point for new-project, existing-project, and refactor work, /orc-version for versioning the current project, and /orc-git for common git/GitHub shortcuts.",
      "version": "0.4.0",
      "source": "./"
    }
  ]
}
```

- [ ] **Step 6: Verify manifests**

```bash
python3 -c "
import json
p = json.load(open('.claude-plugin/plugin.json'))
m = json.load(open('.claude-plugin/marketplace.json'))
assert p['name'] == m['plugins'][0]['name'] == 'orclab'
assert p['version'] == m['plugins'][0]['version'] == '0.4.0'
assert m['plugins'][0]['source'] == './'
print('OK: plugin.json/marketplace.json valid, consistent, version 0.4.0')
"
```
Expected: `OK: plugin.json/marketplace.json valid, consistent, version 0.4.0`

- [ ] **Step 7: Update `CHANGELOG.md`**

Find:
```
# Changelog

All notable changes to this project are documented here, newest first.

## [0.3.0] - 2026-09-05
```

Replace with:
```
# Changelog

All notable changes to this project are documented here, newest first.

## [0.4.0] - 2026-09-05

### Added
- `/orc-git` — shortcuts for common git/GitHub operations: connect a repo (`repo <url>`), commit
  with a drafted message (`commit`), push (`push`), commit-then-push (`commit-push`/`cp`),
  branch/switch (`branch`/`switch`), and check out a PR (`pr <id>`). The first command to actually
  populate `.orclab/` (a connected repo's URL), reserved since v3 but unused until now.

## [0.3.0] - 2026-09-05
```

- [ ] **Step 8: Verify CHANGELOG.md**

```bash
grep -c "## \[0.4.0\]" CHANGELOG.md
grep -c "## \[0.3.0\]" CHANGELOG.md
```
Expected: `1` and `1` (both entries present, newest first).

- [ ] **Step 9: Update `README.md`**

Find:
```
- **/orc-help** (alias: **/orc**) — reports Orclab's own running version and a synopsis of its
  available commands.
```

Replace with:
```
- **/orc-help** (alias: **/orc**) — reports Orclab's own running version and a synopsis of its
  available commands.
- **/orc-git** — shortcuts for common git/GitHub operations: connect a repo, commit with a
  drafted message, push, commit-then-push (alias `cp`), branch/switch, and check out a PR.
```

Find:
```
## Status

v1 (process core) + v2 (`/orc-code`) + v3 (`/orc-version`, `/orc-help`/`/orc`) shipped. See
`docs/superpowers/specs/` for the design history, `CHANGELOG.md` for what actually changed release
to release, and `BACKLOG.md` for what's deliberately deferred (real per-stack defaults research is
#4, `/orc-data` is #5, hook-based enforcement is #3, per-language manifest version-sync is #6). See
`VERIFICATION.md` for the dogfood script that confirms everything actually works once installed in
a real project.
```

Replace with:
```
## Status

v1 (process core) + v2 (`/orc-code`) + v3 (`/orc-version`, `/orc-help`/`/orc`) + v4 (`/orc-git`)
shipped. See `docs/superpowers/specs/` for the design history, `CHANGELOG.md` for what actually
changed release to release, and `BACKLOG.md` for what's deliberately deferred (real per-stack
defaults research is #4, `/orc-data` is #5, hook-based enforcement is #3, per-language manifest
version-sync is #6). See `VERIFICATION.md` for the dogfood script that confirms everything
actually works once installed in a real project.
```

- [ ] **Step 10: Commit**

```bash
git add commands/orc-git.md .claude-plugin/plugin.json .claude-plugin/marketplace.json CHANGELOG.md README.md
git commit -m "Add /orc-git command, bump version to 0.4.0"
```

---

### Task 2: Dogfood verification scenarios

**Files:**
- Modify: `VERIFICATION.md`

**Interfaces:**
- Consumes: the completed `commands/orc-git.md` from Task 1.
- Produces: a complete verification script covering v1-v4. No later task depends on this.

- [ ] **Step 1: Add new scenarios to `VERIFICATION.md`**

Find:
```
## Recording the result
```

Replace with:
```
## Scenario 13: /orc-git repo, all three directory states

1. In a throwaway empty scratch directory, run `/orc-git repo <a real, small test repo URL>`.
   **Expected:** the repo is cloned directly into the (empty) directory.
2. In a different throwaway directory that's already a git repo with no `origin` set, run
   `/orc-git repo <some URL>`. **Expected:** `origin` is set to that URL, no confirmation asked
   (since nothing existing was being overwritten).
3. In that same directory, run `/orc-git repo <a different URL>`. **Expected:** Claude shows the
   currently-set URL and asks for confirmation before changing it — it does not silently overwrite.
4. **Expected throughout:** `.orclab/git-repo.json` is created with the connected URL, and
   `.gitignore` gains a `.orclab/` entry if it didn't already have one.

## Scenario 14: /orc-git commit, clean tree and real changes

1. In a project with no uncommitted changes, run `/orc-git commit`. **Expected:** Claude reports
   there's nothing to commit and stops — no empty commit is created.
2. Make a real, small change, then run `/orc-git commit`. **Expected:** a real commit message is
   drafted from the actual diff (not a generic placeholder) and committed immediately — no
   confirmation question asked first.
3. Make another change, then run `/orc-git commit this is extra context`. **Expected:** the
   drafted message includes "this is extra context" as an addition, not as a replacement of the
   drafted description.

## Scenario 15: /orc-git push, commit-push/cp, and branch/switch aliases

1. After Scenario 14 commits something, run `/orc-git push` on a branch that's never been pushed
   before. **Expected:** it pushes with `-u origin <branch>` (sets upstream), with no confirmation
   prompt.
2. Make another small change, run `/orc-git commit-push`, then separately (on a different real
   change) run `/orc-git cp`. **Expected:** both produce identical commit-then-push behavior.
3. Run `/orc-git branch a-test-branch-name` (a branch that doesn't exist yet), then run
   `/orc-git switch a-test-branch-name` again. **Expected:** the first call creates and switches to
   it; the second call just switches (branch already exists) — both subcommand names behave
   identically.

## Scenario 16: /orc-git pr

1. In a project with at least one real open (or closed) PR, run `/orc-git pr <a real PR number>`.
   **Expected:** `gh pr checkout <id>` runs and the PR's branch is checked out locally.

## Recording the result
```

- [ ] **Step 2: Commit**

```bash
git add VERIFICATION.md
git commit -m "Add /orc-git dogfood scenarios to verification script"
```

---

## Self-Review Notes (from writing this plan)

- **Spec coverage:** all seven subcommands covered in Task 1's command content
  (bare/repo/commit/push/commit-push/cp/branch/switch/pr), `.orclab/git-repo.json` and
  `.gitignore` handling covered, version bump + changelog covered, verification scenarios cover
  all three directory states for `repo`, both clean-tree and real-change cases for `commit`, both
  alias pairs, and `pr`. No scope creep beyond the seven subcommands.
- **Placeholder scan:** no TBD/TODO; every content block is complete, not a stub.
- **Consistency check:** version `0.4.0` is consistent across `plugin.json`, `marketplace.json`,
  the `CHANGELOG.md` entry, and README's Status line. `commit-push`/`cp` and `branch`/`switch`
  each reference their shared behavior identically in the command file, the plan's Global
  Constraints, and Task 2's verification scenarios. `.orclab/git-repo.json`'s content shape
  (`{"url": "<url>"}`) is stated identically in the spec and the command content.
