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
