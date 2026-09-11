# Orclab v14: the forge boundary — `/orc-git release`, and where host-specific work lives

## Goal

Move the one subcommand that pushes and publicly publishes out of `/orc-version`, and state — once
— which release work is specific to the repository host and where it belongs. `/orc-version`
becomes only about versions; `/orc-release` stays host-agnostic by construction; `/orc-git` owns
forge operations and says so.

Closes **BACKLOG #20**, and — folded in 2026-09-10, after v15 shipped — **#28**.

**On the numbering:** `v12` (artifact preflight, **#21**), `v13` (async confirmation, **#18**) and
`v14` here reflect the order these were specced, not a required implementation order. All three are
independent of each other. The one real ordering constraint in this spec is **#19**, below.

## Two dependencies, stated before anything else

- **BACKLOG #19 gates part of the implementation.** `/orc-release`'s `**Run:**` marker parses as
  `^\*\*Run:\*\*\s*(/[\w-]+)` and drops everything after the command name, so
  `**Run:** /orc-git release` records `/orc-git` and loses `release`. For `/orc-publish` a dropped
  argument loses a *target*; here it loses the *verb*, and `/orc-git` alone names a different
  action. The delegation described below is not safe to rely on until #19 is fixed.
- **This spec was written before BACKLOG #17 shipped**, at direflail's explicit direction — #17
  (what `/orc-package` covers) is being implemented first so the two can be checked against each
  other. **Re-read the "Seam with #17" section against whatever #17 actually decides** before
  implementing this one. The seam is named there rather than assumed away.

## Why this exists

direflail asked what the difference between `/orc-version release` and `/orc-release` is — a
question the current naming does not answer, and the question is the finding.

**The sharpest diagnosis is risk class, not naming.** Everything else `/orc-version` does is local
and reversible: edit a manifest, write a changelog entry, commit, tag locally (tags stay local by
this project's convention, see #13). `release` is the single subcommand that pushes to a remote
*and* creates a public artifact. A dangerous verb sheltering under a benign command name is the
part that matters; that the two names read alike is a symptom.

**It must not move into `/orc-release`.** That skill's first rule is that `RELEASING.md` is the
single definition of the steps and it "never invents a release process." A `/orc-release` that knew
how to create GitHub Releases would do something the project's own document never asked for, and
would be wrong for every project releasing to PyPI, an internal deploy, or a Debian archive alone.

**And the capability must stay directly reachable.** Confirmed live 2026-09-07: Orclab itself has
**no `RELEASING.md`, 9 tags, and 0 GitHub Releases**. It is exactly the project that would be
stranded if this were reachable only through `/orc-release`, which refuses to run without that
document.

## Scope

**In scope:**
- `/orc-version release [tag]` → `/orc-git release [tag]`, moved outright.
- A documented split inside `/orc-git` between universal git and forge-specific operations.
- A **decision** about where CI confirmation belongs, and its shape — **not** an implementation of
  `/orc-git ci`. The section below says why building it now would be designing from one data point.
- A version-suggestion capability in `/orc-version`.
- Updating the four live Orclab references to the old command.
- **`/orc-git merge <branch>`** — the one universal-git operation `/orc-git` was missing (#28).

**Explicitly out of scope:**
- **Any forge abstraction.** No `forge.yaml`, no provider field, no second-forge command. See
  "No abstraction, deliberately."
- **Renaming `/orc-git`.** Its name under-describes it; that is recorded, not fixed.
- **Any change to `/orc-release`.** It gains nothing and loses nothing; it already delegates.
- **Fixing #19.** Its own entry; this spec depends on it and does not absorb it.

## The move

`/orc-git release [tag]` takes over `/orc-version`'s Release Flow unchanged in behaviour:

1. Resolve the target tag — named in arguments, or the most recent local tag.
2. Confirm it exists locally; stop plainly if not, never guessing what was meant.
3. `git push origin HEAD` and `git push origin <tag>` if not already pushed.
4. Create the Release with that version's `CHANGELOG.md` section as the notes body.
5. Report the real Release URL.

It inherits `/orc-git`'s existing GitHub-auth step, the same one `repo` already performs.

**Moved outright, with no deprecated alias.** Verified 2026-09-07: nothing outside Orclab
references `/orc-version release` — Orcshot's `RELEASING.md` contains no reference to
`/orc-version` or `/orc-git` at all. The live references are four Orclab files (`CLAUDE.md`,
`README.md`, `VERIFICATION.md` Scenario 11, and `orc-version/SKILL.md`); historical specs and plans
also mention it and are records, not code, so they stay as written. An alias would preserve
precisely the confusion this entry exists to remove.

**Not an alias, but not a bare failure either:** `/orc-version` invoked with `release` reports that
the subcommand moved and names `/orc-git release`, then stops. It does not run it. A redirect that
tells you where something went is not the same as one that quietly still works — the first teaches
the new name, the second preserves the old habit.

**`/orc-git release` keeps reading `CHANGELOG.md`.** The notes are a property of the release, and
the changelog is where this project keeps them; making the caller supply them would push extraction
into `/orc-release` or a human. The tag-to-heading convention (`v0.3.0` → `## [0.3.0]`) is the
small piece of version-shaped knowledge this accepts in exchange for not building plumbing.

## The forge boundary

`/orc-git`'s name hides two different families. The split is real today and goes in the skill
explicitly:

| Universal git — works against any host | Forge-specific — `gh`, GitHub only |
|---|---|
| `commit`, `push`, `branch`, `switch`, `merge` | `repo`, `pr`, `release`, and `ci` if it lands |

Auditing a real release for host coupling — Orcshot's, 2026-09-07 — gives three distinct answers,
which is the evidence that this split is the right one:

| Step | Host-coupled? |
|---|---|
| 9. Commit, tag, push | **No** — `git push` works against any host |
| 10. Confirm CI is green | **Yes** — three `gh run list` calls |
| 11. Publish the GitHub Release | **Yes** — `gh release create` |

**`/orc-git` is not renamed.** It under-describes what it holds, and that will need untangling the
day a second forge is real. Renaming a shipped command for a hypothetical is the speculative work
this repo keeps removing; the split above is documented so the next person meets it as a stated
fact rather than a surprise.

## No abstraction, deliberately

direflail's framing was that the repository host is "another link in that tree" — the project
decides it uses GitHub, and that delegates to `/orc-git`. **That mechanism already exists, and it
is `RELEASING.md` itself:**

```markdown
## 11. Publish the GitHub Release
**Run:** /orc-git release
```

`/orc-release` stays host-agnostic by construction because it only follows the document. A project
moving to GitLab or Codeberg changes that line; nothing in `/orc-release` changes, exactly as step
7 delegates a Launchpad copy to `/orc-publish` without `/orc-release` knowing what Launchpad is.

So: no `forge.yaml`, no provider field, no `/orc-gitlab`. The declaration point is the project's own
checklist, which is where the project's own decisions already live.

## `/orc-git ci` — shape only, and thin on purpose

The boundary says CI confirmation belongs in `/orc-git`. The design does not go further than shape,
and the reason is worth recording rather than discovering later: **it has exactly one example, and
that example needs something `release` does not.** Orcshot's step 10 is three `gh run list` calls
against three named workflow files (`apt.yml`, `snap.yml`, `flatpak.yml`). A release is identified
by a tag the command can resolve itself; a CI check needs a per-project list of what to look at.

That is a different signature, and forcing it into the same mould would be designing from one data
point. The shape:

```
/orc-git ci [<workflow> …]     # named workflows, or every workflow in .github/workflows
```

reporting each workflow's latest run status for the current commit, and failing if any is not
`success`. **Build it when a second project needs it**, or when Orcshot's step 10 is actually
delegated — not before.

## `/orc-git merge <branch>` — landing a branch, without deciding how

**Added 2026-09-10, folding in #28.** Raised the day after this spec was written: `/orc-git`'s
subcommands each prepare work or publish a commit, and none lands a branch. Every finished branch
under Orclab's own worktree-based workflow therefore leaves Orclab's vocabulary — four times in one
session on 2026-09-10, each by hand: test, `git merge --no-ff`, test again, remove the worktree,
delete the branch. The memory rule says raw git is a fallback to flag; a fallback needed every
single time is the shape of a missing command.

**#28's own objection, and how this answers it.** A landing command that *decides* merge-vs-PR
would be the one surprising thing in an otherwise unsurprising command. So this one does not
decide. `merge` means merge, and only that:

1. Refuse if the current working tree is dirty — a merge over uncommitted work is how someone's
   half-done change gets swept into a merge commit.
2. Confirm `<branch>` exists locally; stop plainly if not.
3. Run the project's test suites **on the branch as it stands** (for Orclab: every
   `skills/*/scripts/tests` and `hooks/scripts/tests` suite). Stop if any fails; nothing has
   been merged.
4. `git merge --no-ff <branch>` into the current branch, with a message naming what landed.
5. Run the same suites **on the merged result**. If any fails, stop and leave everything in
   place — the merge is local and recoverable, and the branch and its worktree still exist.
6. If `<branch>` has a worktree (`git worktree list`), remove it; then `git branch -d <branch>`.
   `-d`, not `-D`: a branch git considers unmerged is a signal, not litter.
7. Report: what landed, the suite results, what was cleaned up.

**"How should this land?" stays a human question.** `superpowers:finishing-a-development-branch`
is where it gets asked, if it has not been; `/orc-git merge` is what you type once the answer is
"merge it locally." This is the same argument `push` already makes for itself — invoking the
subcommand *is* the deliberate act — and it is why there is no `/orc-git land` wrapping that
skill's menu: a name that adds no capability, plus an availability guard for the skill it wraps.

**Universal git, left side of the table.** No `gh`, so it works against any host, and against
no host at all.

## Version suggestion in `/orc-version`

What `/orc-version` gains by becoming only about versions, and the reason it belongs here rather
than in its own entry: it is the other half of the same rebalancing.

Today `/orc-version` takes a version you supply, or `increment major|minor|point`. It never
proposes. When a release reaches its "pick a version" step, the person picking has to hold in their
head what changed since the last tag.

**The capability:** with no version and no increment word given, read the commits since the most
recent tag (`git log <tag>..HEAD --format='%B---COMMIT-BOUNDARY---'`, the range `/orc-version`'s
changelog drafting already uses) and propose a bump **with its reason stated** — "no breaking
changes, four features and two fixes, so minor: `0.11.0` → `0.12.0`."

**It proposes; it never decides.** The user confirms or overrides, exactly as the changelog draft
already works. Semver is a judgment about intent, and commit messages are evidence, not proof — a
refactor described as a fix can still break a consumer. A suggestion that presents its reasoning
lets that judgment be corrected; a silent auto-bump would not.

`/orc-release` needs no change to benefit: it already delegates version-setting to `/orc-version`
with `--no-commit`.

## Seam with #17 — read this against what #17 decides

**A GitHub Release is defensibly both a forge operation and a distribution channel**, and that is
the one place these two entries can collide.

As a forge operation it is `gh release create`, the same family as `gh pr`. As a channel it
genuinely distributes: Orcshot attaches the built `.deb` as a release asset, and its
`update_check.py` polls `releases/latest` — which is the entire reason Orcshot's `RELEASING.md`
exists at all.

**The resolution this spec takes:** `/orc-git release` is the *mechanism*. Whether a project also
treats it as a distribution channel is the project's own call, expressed as a `channels.yaml`
action pointing at it. So:

- **#17 decides** what standing up a distribution channel means and what `/orc-package` covers.
- **#20 decides** where host-specific operations live.
- A project that distributes via GitHub Releases uses both, and neither entry has to own the other.

If #17's design contradicts this — for instance by making GitHub Releases a first-class channel
type with its own setup flow — **that decision wins and this section is what gets revised**, since
#17 ships first and will have the worked examples.

**Settled 2026-09-10: #17 shipped as v15 and agreed.** Its spec's interlock reads *"`/orc-git
release` is the mechanism, and whether a project treats it as a channel is expressed in that
project's recipe. This spec agrees with that split."* The PPA ingredient it ships declares no
GitHub Release channel, and nothing in v15 makes one a first-class type. This section stands as
written; nothing here is revised.

## Testing

`/orc-git` and `/orc-version` are prose skills with no bundled scripts, so this is verified the way
Orclab's other prose conventions are — `VERIFICATION.md` scenarios:

- **Scenario 11 is rewritten**, not deleted: it currently exercises `/orc-version release` and
  becomes `/orc-git release`, covering a named tag, a defaulted tag, and a tag that does not exist
  locally (must stop, not guess).
- **`/orc-version release` is gone**: invoking it reports the move and points at `/orc-git release`
  rather than failing obscurely.
- **Version suggestion**: in a scratch repo with commits since a tag, `/orc-version` with no
  arguments proposes a bump *and states its reason*; overriding the proposal is honoured; the
  proposal alone never writes a file.
- **`/orc-git merge`**: in a scratch repo with a feature branch and a worktree for it, and a
  trivially passing test suite, `/orc-git merge <branch>` lands it, runs the suite twice, removes
  the worktree and deletes the branch. With a dirty tree it refuses before merging. With a suite
  that fails on the merged result, it stops with the branch, worktree and merge commit all still
  present and says so. With a branch name that does not exist, it stops without guessing.
- **The boundary is documented**: `/orc-git`'s skill states the universal-vs-forge split, and the
  four stale references to the old command are gone (`grep -rn "orc-version release"` over live
  files, excluding `docs/superpowers/` and `BACKLOG.md`, returns nothing).

## Global constraints

- No new dependency; `gh` and `git` are already assumed by `/orc-git`.
- No consuming project's content is written. Orcshot's `RELEASING.md` gains a step-11 delegation
  only in a session centred on Orcshot, and only after #19.
- `/orc-release` is unchanged.
- The `orc-` prefix rule holds: `/orc-git` already carries it, and no new top-level command is
  added.
