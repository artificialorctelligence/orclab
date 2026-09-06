# Orclab v4: `/orc-git` — design

## Goal

Add `/orc-git`, a small family of git-operation shortcuts, to Orclab. Unlike `/orc-version` and
`/orc-help`, this doesn't manage Orclab's own identity — it's a thin convenience layer over
everyday git/GitHub operations, useful in any project. Core category, per direflail's own
taxonomy: applies to every project Orclab touches, including Orclab itself.

## Scope

**In scope now:** one command, `commands/orc-git.md`, with subcommands `repo`, `commit`, `push`,
`commit-push`/`cp`, `branch`/`switch`, `pr`, plus a bare-invocation listing. First real content
for the `.orclab/` directory (reserved but unpopulated since v3) — the connected repo URL.

**Explicitly out of scope:** anything beyond these seven subcommands. No merge/rebase/stash
shortcuts, no conflict resolution helpers — direflail's own framing was "doesn't do much other
than provide shortcuts," and the seven listed cover what was actually asked for.

## Command surface and routing

One command file, `commands/orc-git.md`. Every form below is a different `$ARGUMENTS` string
routed within that one file — no separate command files, no alias-mechanism workaround needed
anywhere in this design (unlike `/orc`'s pointer-to-`orc-help.md` case in v3): a bare
`/orc-git` and `/orc-git <subcommand>` are the same literal command name, differing only in what
follows it.

- **Bare `/orc-git`**: lists the subcommands below with a one-line description each. Since all
  seven live in this one file, this is a static list written directly into the file's own
  content — not a discovery scan across other files the way `/orc-help`'s command listing needed.
- **`/orc-git repo <url>`**: connect the current project to a GitHub repo (see "Repo connection"
  below).
- **`/orc-git commit [extra text]`**: stage everything and commit with a drafted message (see
  "Commit drafting" below).
- **`/orc-git push`**: push the current branch (see "Push" below).
- **`/orc-git commit-push [extra text]`** and **`/orc-git cp [extra text]`**: identical behavior —
  run the commit subcommand's full behavior, then the push subcommand's full behavior.
- **`/orc-git branch <name>`** and **`/orc-git switch <name>`**: identical behavior — switch to
  `<name>` if it exists, create and switch to it if it doesn't.
- **`/orc-git pr <id>`**: check out an existing PR by number (see "PR checkout" below).

## Repo connection: `/orc-git repo <url>`

1. **Ensure GitHub auth**: run `gh auth status`. If it reports not logged in, run `gh auth login`
   first (this itself opens a browser for GitHub's OAuth device flow — that's `gh`'s own
   mechanism, not something this command builds). If already authenticated, skip straight to the
   next step.
2. **Determine the current directory's git state**:
   - **Already a git repo**: check the current `origin` remote (`git remote get-url origin`,
     if any). If none is set, set it to `<url>` (`git remote add origin <url>`). If one is already
     set and matches `<url>`, nothing to change. If one is already set and *differs* from `<url>`,
     show the current value plainly and ask for explicit confirmation before overwriting it with
     `git remote set-url origin <url>` — never silently replace an existing remote.
   - **Not a git repo, and the directory is empty**: clone directly into it (`git clone <url> .`).
   - **Not a git repo, and the directory has files**: ambiguous — ask directly whether to clone
     `<url>` into a new subdirectory (named after the repo) or initialize the current directory as
     a git repo with `<url>` set as `origin` (without pulling any history). Don't guess between
     these two meaningfully different outcomes.
3. **Save the connection**: write `<url>` to `.orclab/git-repo.json` as `{"url": "<url>"}` — the
   first real content the `.orclab/` directory has ever held (reserved but unpopulated since v3).
   If `.gitignore` doesn't already have a `.orclab/` entry, add one (check first — don't duplicate
   an existing entry).

## Commit drafting: `/orc-git commit [extra text]`

1. Stage everything: `git add -A`.
2. If nothing is staged after that (a clean tree), report this plainly and stop — don't attempt an
   empty commit.
3. Draft a commit message from the real staged diff (`git diff --cached --stat` and
   `git diff --cached` for content) — same evidence-based drafting principle as `/orc-version`'s
   changelog step, but **no confirmation pause here** — this is a deliberate difference from
   `/orc-version`, per direflail's own explicit choice.
4. If `$ARGUMENTS` has text after `commit` (the `[extra text]`), fold it into the drafted message
   as an addition — not a replacement. This is the mechanism for adding context without a forced
   question each time.
5. Commit: `git commit -m "<final message>"`.

`commit-push` and `cp` run this exact behavior first, then the push behavior below — including the
same `[extra text]` handling (text after `commit-push`/`cp` gets folded in the same way).

## Push: `/orc-git push`

1. Determine the current branch: `git branch --show-current`.
2. If it already has an upstream, `git push`. If not, `git push -u origin <branch>`.
3. **No confirmation prompt** — invoking the command directly is the authorization, the same
   reasoning already applied to `/orc-version`'s own push step in its Release Flow.

## Branch/switch: `/orc-git branch <name>` / `/orc-git switch <name>`

`git switch <name>` if it exists; `git switch -c <name>` if it doesn't. Both subcommand names run
identical logic.

## PR checkout: `/orc-git pr <id>`

`gh pr checkout <id>` — the standard, real command for exactly this, requiring the same `gh` auth
already covered by the repo-connection step.

## Relationship to existing Orclab work

Core category — no coupling to the three v1 skills or to `/orc-version`/`/orc-help` beyond shared
conventions already established (evidence-based drafting without silent guessing, `.orclab/` as
the reserved per-project state location). This is the first command to actually write into
`.orclab/`, fulfilling the reservation made in v3's design without it ever having been used.

## Validation

Same dogfooding principle as v1-v3 — no automated test suite applies to command content.
Validation is running `/orc-git` for real, in a fresh session, confirming:
- `/orc-git repo <url>` correctly distinguishes its three directory-state branches (already a
  repo with matching/differing/absent origin; empty directory; non-empty non-repo directory) and
  never silently overwrites a differing existing remote.
- `/orc-git commit` drafts a real message from a real diff, correctly folds in extra text when
  given, and reports plainly (without committing) on a clean tree.
- `/orc-git push` sets upstream correctly on a branch that's never been pushed before.
- `/orc-git commit-push`/`cp` and `/orc-git branch`/`switch` produce identical results under their
  respective alias pairs.
- `/orc-git pr <id>` successfully checks out a real, existing PR number.

This isn't written up as new `VERIFICATION.md` scenarios yet — an implementation-plan-level detail,
added the same way v1-v3's were.
