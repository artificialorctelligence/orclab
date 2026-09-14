# /orc-git

## What it's for

You're working in a project that's under git, and you want to do the everyday jobs — connecting
the project to a GitHub repository, committing, pushing, switching branches, merging a finished
branch back in, checking out a pull request someone opened, or cutting a release — without typing
out the individual git and GitHub commands yourself.

## What you type

| You type | What it does |
|---|---|
| `/orc-git repo <url>` | Connects the current project to the GitHub repository at `<url>` |
| `/orc-git commit [text]` | Stages every change in the project and commits it, with a message it writes for you |
| `/orc-git push` | Pushes the branch you're on to its remote copy |
| `/orc-git commit-push [text]` (alias: `/orc-git cp [text]`) | Commits, then pushes |
| `/orc-git branch <name>` (alias: `/orc-git switch <name>`) | Switches you to branch `<name>`, creating it first if it doesn't exist yet |
| `/orc-git merge <branch>` | Merges `<branch>` into the branch you're currently on |
| `/orc-git pr <id>` | Checks out an existing pull request (a proposed set of changes someone opened on GitHub) by its number |
| `/orc-git release [tag]` | Pushes a version tag and publishes the GitHub Release for it (uses the most recent tag if you don't name one) |

Typing `/orc-git` by itself lists all of these. Typing a word it doesn't recognize, or leaving out
a `<url>`/`<name>`/`<branch>`/`<id>` a subcommand needs, gets you this same list instead of a
guess.

## What it will ask you

- Running `repo <url>` when the project is already connected to a *different* GitHub address: it
  shows you that existing address and asks before changing it.
- Running `repo <url>` in a folder that isn't a git project yet, but already has other files in
  it: it asks whether to copy the project into a new folder named after the repository, or
  connect the current folder to `<url>` without downloading its history.
- If Claude decides on its own to run `push`, `merge`, or `release` — rather than because you
  typed the command — it says exactly what it's about to do (for example, "Push it to origin?")
  and waits for you to say yes, every time. Typing the command yourself is already your answer,
  so in that case it just runs.

Every other subcommand runs immediately once you type it — nothing else is asked.

## What it changes

- `commit` (and the commit half of `commit-push`/`cp`): makes one real commit, after staging
  *every* changed file in the project — not only files you might expect. Look at what's
  uncommitted beforehand, or review the commit afterward, if you want to check exactly what went
  in.
- `push` (and the push half of `commit-push`/`cp`): pushes your current branch to its remote
  copy on GitHub.
- `repo`: writes `.orclab/git-repo.json` recording the connected URL, and adds a line for
  `.orclab/` to `.gitignore` if one isn't already there. It may also run a git clone or set up
  the folder as a new git project, depending on which case above applies.
- `branch`/`switch`: only moves you onto the named branch (creating it if it's new) — writes no
  files.
- `merge`: creates a merge commit, runs the project's test suite both before and after merging,
  and — once both runs pass — deletes the finished branch (and any separate folder that was
  checked out for it). It only deletes the branch if none of its work would be lost by doing so.
- `pr`: checks out the pull request's branch locally. Changes nothing else.
- `release`: pushes a tag to GitHub and creates a GitHub Release from it — a public page other
  people can see, listing what changed.

## What it will never do without asking

- It will never push, merge, or release on its own initiative without telling you first and
  waiting for a yes — only when you type the command yourself does it skip that and run right
  away.
- It will never merge into your current branch while you have uncommitted changes sitting
  around, or while the branch being merged does. It stops and tells you what's uncommitted
  instead.
- It will never guess which branch you meant: if the branch you named doesn't exist, or is the
  one you're already on, it stops and says so instead of merging.
- It will never merge if the test suite fails beforehand — it stops and reports the failure
  without merging anything. If the test suite fails *after* it has already merged, it doesn't
  undo that merge for you: the merge commit, the branch, and its separate folder (if it had one)
  are all left exactly as they are, nothing is pushed, and undoing the merge is your call.
- It will never resolve a merge conflict for you. If one comes up, it stops and reports which
  files conflict, and leaves the decision to you.
- It will never force through the branch deletion after a merge — if git considers the branch
  not fully merged, it stops and tells you rather than deleting it anyway.
- It will never overwrite an existing, different GitHub connection for the project without
  showing you the current one and asking first.
- It will never guess which tag you meant when releasing: if you name a tag that doesn't exist
  locally, it stops and says so instead.
