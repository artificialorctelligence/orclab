---
name: orc-git
description: Use when the user explicitly asks to use orc-git, or types /orc-git, for git and GitHub shortcuts - connecting a repo, committing, pushing, branching, merging a finished branch, checking out a PR, or cutting a GitHub Release from an existing tag.
argument-hint: repo <url> | commit [text] | push | commit-push [text] | cp [text] | branch <name> | switch <name> | merge <branch> | pr <id> | release [tag]
---
# /orc-git

You are running git and GitHub shortcuts via the `/orc-git` command. Route based on the first
word of `$ARGUMENTS`.

If the first word doesn't match any of the subcommands below (`repo`, `commit`, `push`,
`commit-push`, `cp`, `branch`, `switch`, `merge`, `pr`, `release`), or a subcommand that requires
an argument (`repo`, `branch`, `switch`, `merge`, `pr`) is invoked without one, say so plainly,
show the bare-invocation listing below, and stop — don't guess at an unlisted git operation or
proceed without a required argument.

## Two families under one name

`/orc-git` holds two different things, and the split is stated here so the next person meets it
as a fact rather than a surprise:

| Universal git — works against any host, or none | Forge-specific — `gh`, GitHub only |
|---|---|
| `commit`, `push`, `branch`, `switch`, `merge` | `repo`, `pr`, `release` |

The name under-describes the right-hand column. It is not renamed: renaming a shipped command for
a hypothetical second forge is speculative work, and the day a second forge is real is the day
this table tells you what has to move. A `ci` subcommand (confirm named workflows are green for
the current commit) would also sit on the right; it is not built — it has exactly one example to
design from, and that is one too few.

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
  merge <branch>       — land a finished branch into the current one, tests before and after
  pr <id>              — check out an existing pull request by number
  release [tag]        — push a tag and create the GitHub Release for it (default: newest local tag)
```

Stop here — do not proceed to any subcommand logic on a bare invocation.

## repo <url>

1. **Ensure GitHub auth**: run `gh auth status`. If it reports not logged in, run `gh auth login`
   first. If already authenticated, continue.
2. **Determine the current directory's git state**:
   - **Already a git repo** (`git rev-parse --show-toplevel` succeeds AND its output matches the
     current directory — this correctly distinguishes "cwd is itself a repo root" from "cwd is
     merely inside some ancestor repo," which a bare `git rev-parse --git-dir` check would wrongly
     treat as the same case): check the current `origin` remote with `git remote get-url origin`
     (this may fail if none is set — that's fine).
     - No `origin` set: run `git remote add origin <url>`.
     - `origin` already set and matches `<url>`: nothing to change, report that it's already
       connected.
     - `origin` already set and differs from `<url>`: show the current value plainly and ask for
       explicit confirmation before running `git remote set-url origin <url>` — never silently
       overwrite a differing existing remote.
   - **Not a git repo, and the directory is empty**: run `git clone <url> .`.
   - **Not a git repo, and the directory has files**: ask directly whether to clone `<url>` into a
     new subdirectory named after the repo (`git clone <url> <repo-name>`, where `<repo-name>` is
     the repo's own name parsed from `<url>`) instead, or initialize the current directory as a
     git repo with `<url>` set as `origin` via `git init && git remote add origin <url>` (without
     pulling any history). Don't guess between these two outcomes.
3. **Save the connection — only if one was actually established.** Skip this step entirely if the
   user declined to overwrite a differing `origin` in Step 2, or otherwise chose not to proceed.
   Otherwise, create `.orclab/` if it doesn't exist **in the directory that actually ended up
   connected** (the new subdirectory, if the user chose to clone into one; the current working
   directory in every other case), and write `.orclab/git-repo.json` there with this exact content
   (substituting the real URL):
   ```json
   {"url": "<url>"}
   ```
   If that same directory's `.gitignore` doesn't already contain a `.orclab/` entry, append one on
   its own line — check first with a search so you don't add a duplicate entry if one's already
   there.

## commit [text]

1. Stage everything: `git add -A`.
2. Check what's staged: `git diff --cached --stat`. If nothing is staged (a clean tree), report
   this plainly and make no commit — never attempt an empty one. Invoked as `commit`, that ends
   the command; invoked as part of `commit-push`/`cp`, it ends only this half (see below).
3. Draft a real commit message from the actual staged changes (`git diff --cached --stat` and
   `git diff --cached` for content) — describe what genuinely changed, not a generic placeholder.
4. If `$ARGUMENTS` has text after `commit` (or after `commit-push`/`cp`, when this behavior is
   reused by those subcommands below), fold that text into the drafted message as an addition —
   append it, don't replace the drafted content with it.
5. Commit: `git commit -m "<final message>"`. No confirmation pause before committing — this
   subcommand doesn't ask before finalizing, unlike `/orc-version`'s changelog step.

## push

1. Determine the current branch: `git branch --show-current`. If this returns empty (a detached
   HEAD), report that plainly and stop — there's no branch to push.
2. Check whether the branch is actually ahead of its upstream:
   `git rev-list --count @{upstream}..HEAD` (this fails if there's no upstream — treat that as
   "there is something to push," since the branch has never been published). If it reports `0`,
   say so plainly and stop: already in sync, nothing to push.
3. Check if it has an upstream: `git rev-parse --abbrev-ref <branch>@{upstream}` (this fails if
   there's no upstream set — that's the signal to use the second command below instead of the
   first).
   - Has an upstream: `git push`.
   - No upstream: `git push -u origin <branch>`.
4. No confirmation prompt — invoking this command directly is the authorization.

## commit-push [text] / cp [text]

Run the full **commit** behavior above (including the same `[text]` folding-in behavior), then
run the full **push** behavior above. Both subcommand names run this identical sequence.

**Each half is independently conditional — an empty half does not end the command.** This is the
whole point of the combined form, and getting it wrong makes `cp` useless in a common case:

- Tree dirty → commit it. Tree clean → say so, and carry on to the push.
- Branch ahead of its upstream → push it. Nothing ahead → say so, and stop.

Both halves being no-ops at once is a legitimate result, not a failure: report it as nothing to
commit, nothing to push, already in sync.

Found 2026-09-07 by running `/orc-git cp` on a clean tree that had seven unpushed commits. Read
literally, `commit`'s "stop" ended the whole command and nothing was pushed — the exact situation
`cp` exists for.

## branch <name> / switch <name>

Both subcommand names run this identical logic:
1. Check if the branch exists: `git show-ref --verify --quiet refs/heads/<name>`.
2. If it exists: `git switch <name>`.
3. If it doesn't: `git switch -c <name>`.

## merge <branch>

Lands `<branch>` into the current branch, locally. It does exactly what its name says and decides
nothing about *how* work should land — whether this branch should be merged directly, go up as a
pull request, or be rebased first is a question for a person (or for
`superpowers:finishing-a-development-branch`, which asks it). Typing `/orc-git merge` is the
answer "merge it locally," and invoking it is the deliberate act, the same way `push` argues for
itself.

1. **Refuse a dirty tree.** `git status --porcelain` must print nothing. If it does, report what is
   uncommitted and stop — a merge over uncommitted work sweeps someone's half-done change into a
   merge commit that claims to be something else. If `<branch>` has a worktree (`git worktree
   list`), the same check applies there — `git -C <path> status --porcelain` must also print
   nothing; otherwise the pre-merge suite would test content that is not what merges, and `git
   worktree remove` would refuse at the end.
2. **Confirm the branch exists locally:** `git show-ref --verify --quiet refs/heads/<branch>`. If
   not, say so and stop; never guess which branch was meant. Also confirm `<branch>` is not the
   current branch (`git branch --show-current`); if it is, say so and stop — merging a branch into
   itself is "Already up to date" followed by deleting it.
3. **Run the project's test suites on the branch as it stands, before merging.** For a project
   with Python suites in Orclab's layout, that is every `skills/*/scripts/tests` and
   `hooks/scripts/tests` directory:
   ```bash
   for d in skills/*/scripts hooks/scripts; do [ -d "$d/tests" ] && { (cd "$d" && python3 -m pytest tests/ -q) || break; }; done
   ```
   For any other project, run whatever its own test command is (`npm test`, `cargo test`, `go test
   ./...`, `pytest`), found the way `superpowers:using-git-worktrees` finds it. Run them against
   the branch's tree — check it out in its worktree if it has one (`git worktree list`), otherwise
   `git stash` is *not* the tool (the tree is clean by step 1); use `git worktree add` to a
   temporary path and remove it as soon as the suites finish, whichever way they went — a leftover
   temporary worktree blocks `git switch <branch>`, which is the next thing a user does after a
   failing suite. If any suite fails, report the failure and stop. Nothing has been merged.
4. **Merge:** `git merge --no-ff <branch> -m "Merge <branch>: <one line saying what landed>"`.
   Draft that line from the branch's commit subjects (`git log <current>..<branch> --oneline`),
   not from the branch name. If the merge conflicts, stop and report the conflicting files; do
   not resolve conflicts on the user's behalf. The tree is mid-merge; `git merge --abort` is the
   user's call, not this command's.
5. **Run the same suites on the merged result.** If any fails: stop, say so, and leave everything
   exactly as it is — the merge commit, the branch, and its worktree all still exist, nothing has
   been pushed, and `git reset --hard HEAD~1` is the user's call, not this command's.
6. **Clean up.** If `git worktree list` shows a worktree for `<branch>`, `git worktree remove
   <path>` (it is clean; step 1 and the merge guarantee that). Then `git branch -d <branch>` —
   lower-case `d`: if git refuses because it considers the branch unmerged, that is a signal worth
   reporting, not litter to force past with `-D`.
7. **Report:** the merge commit, the branch that landed, both suite results, and what was removed.

No confirmation prompt beyond the gates above — invoking the subcommand is the authorization.

## pr <id>

Run `gh pr checkout <id>` — this requires the same GitHub authentication already covered by the
`repo` subcommand's Step 1.

## release [tag]

Pushes an existing local tag and creates the GitHub Release for it. This is the one subcommand
here that both pushes to a remote *and* creates a public artifact; that is why it lives under the
command that owns forge operations and not under `/orc-version`, whose every other action is local
and reversible.

1. **Ensure GitHub auth**, exactly as `repo` does: `gh auth status`; run `gh auth login` first if
   it reports not logged in.
2. **Determine the target tag:** the tag named after `release ` (e.g. `/orc-git release v1.2.0`),
   or the most recent local tag if none was given:
   ```bash
   git tag --list 'v*' --sort=-v:refname | head -1
   ```
3. **Confirm the tag exists locally:** `git tag --list '<tag>'`. If it doesn't, report this plainly
   and stop — do not guess what tag was meant.
4. **Push the commit and tag to `origin`** if they aren't already there:
   ```bash
   git push origin HEAD
   git push origin <tag>
   ```
5. **Create the real GitHub Release**, using the corresponding `CHANGELOG.md` section (if present)
   as the release notes body:
   ```bash
   gh release create <tag> --notes-file <path to a temp file containing that section's content>
   ```
   Extract just that one version's section from `CHANGELOG.md` — from its `## [X.Y.Z]` heading
   (the tag with its leading `v` stripped) to the next `## [` heading or end of file — into a temp
   file first, then pass that file's path. If there is no `CHANGELOG.md` or no matching section,
   say so and create the Release with `--generate-notes` instead, naming which happened.
6. **Report the real Release URL** that `gh release create` prints.

No confirmation prompt — invoking this subcommand directly is the authorization, as with `push`.
It is not reachable from `/orc-version`; that command reports the move and stops.
