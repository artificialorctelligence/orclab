# Orclab v14: the forge boundary — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the one subcommand that pushes and publicly publishes out of `/orc-version` into `/orc-git release`; give `/orc-git` the one universal-git operation it was missing, `merge <branch>`; make `/orc-version` propose a bump with its reason when asked for nothing in particular; and state, in `/orc-git`'s own skill, which of its subcommands are git and which are GitHub.

**Architecture:** Three prose skills change and nothing else does. `/orc-git` gains two subcommands and a documented split. `/orc-version` loses its Release Flow (replaced by a moved-notice that names the new home and stops) and gains a proposal step on bare invocation. `/orc-release` is untouched — it already delegates through `RELEASING.md`'s `**Run:**` marker, which is the whole forge-agnostic mechanism. No scripts, no new files under `scripts/`; the checks are greps and `VERIFICATION.md` scenarios, as for every prose convention in this repo.

**Tech Stack:** Markdown. `git` and `gh`, both already assumed by `/orc-git`.

## Global Constraints

- Source of truth: `docs/superpowers/specs/2026-09-08-orclab-v14-forge-boundary-design.md`, as amended 2026-09-10 (#28 folded in as `/orc-git merge`; the #17 seam recorded as settled).
- **No new dependency.** No new top-level command. No forge abstraction — no `forge.yaml`, no provider field, no `/orc-gitlab`, no rename of `/orc-git`.
- **`/orc-release` is unchanged.** No file under `skills/orc-release/` is touched.
- **`/orc-git ci` is not built.** Its shape is recorded in the spec; the skill may mention it as future, nothing more.
- **`/orc-version release` is moved outright, no alias.** Invoking it reports the move, names `/orc-git release`, and stops — it never runs the release.
- **`/orc-version`'s proposal never writes a file.** It proposes a bump with its reason; applying it goes through the existing Apply flow only after the user confirms or overrides.
- **`/orc-git merge` decides nothing about how work lands.** It merges locally, gated by the test suites before and after, and cleans up the worktree and branch; it never opens a PR, never force-deletes, never merges over a dirty tree.
- **After this plan, `grep -rn "orc-version release" --include=*.md . | grep -v "docs/superpowers/\|BACKLOG.md\|CHANGELOG.md"` returns nothing.** Historical specs, plans, and backlog entries are records and stay as written.
- Out of scope, recorded here so nobody widens the plan silently: `CLAUDE.md` names `/orc-version release` and `/orc-git push` as the fit for `disable-model-invocation: true`, and neither `orc-git` nor `orc-version` sets it today. That is a pre-existing gap worth its own BACKLOG entry, not a change in this plan (the only `CLAUDE.md` edit here is the reference rename).
- No consuming project's content is written. Orcshot's `RELEASING.md` gains its step-11 delegation only in a session centred on Orcshot.
- Every commit message ends with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `skills/orc-git/SKILL.md` | Gains `release [tag]` and `merge <branch>`; the universal-vs-forge table; updated description, `argument-hint`, routing list, bare listing | 1 |
| `skills/orc-version/SKILL.md` | Release Flow removed; `release` routes to a moved-notice; bare invocation proposes a bump; Apply step 4 points at `/orc-git release` | 2 |
| `README.md:30-36` | Two bullets updated | 3 |
| `CLAUDE.md:121` | One reference renamed | 3 |
| `VERIFICATION.md` | Scenario 11 rewritten in place; three new scenarios | 3 |
| `BACKLOG.md` | `#20` and `#28` resolved, layered | 3 |

---

### Task 1: `/orc-git` — `release`, `merge`, and the forge boundary

**Files:**
- Modify: `skills/orc-git/SKILL.md`

**Interfaces:**
- Consumes: the Release Flow text being moved is reproduced verbatim below — do not open `skills/orc-version/SKILL.md`; Task 2 removes it from there.
- Produces: the subcommand names `release` and `merge` that Task 2's moved-notice and Task 3's scenarios and README reference.

- [ ] **Step 1: Record the before-state**

Run: `grep -c '^## ' skills/orc-git/SKILL.md`
Expected: `7` (bare, repo, commit, push, commit-push, branch, pr).

- [ ] **Step 2: Rewrite the frontmatter and the routing paragraph**

Replace lines 1–15 (from the opening `---` through the sentence ending `proceed without a required argument.`) with exactly:

````markdown
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
````

- [ ] **Step 3: Update the bare-invocation listing**

Replace the listing block under `## Bare invocation (no arguments)` with exactly:

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

- [ ] **Step 4: Add `merge <branch>` after the `branch`/`switch` section and before `pr`**

Insert exactly:

````markdown
## merge <branch>

Lands `<branch>` into the current branch, locally. It does exactly what its name says and decides
nothing about *how* work should land — whether this branch should be merged directly, go up as a
pull request, or be rebased first is a question for a person (or for
`superpowers:finishing-a-development-branch`, which asks it). Typing `/orc-git merge` is the
answer "merge it locally," and invoking it is the deliberate act, the same way `push` argues for
itself.

1. **Refuse a dirty tree.** `git status --porcelain` must print nothing. If it does, report what is
   uncommitted and stop — a merge over uncommitted work sweeps someone's half-done change into a
   merge commit that claims to be something else.
2. **Confirm the branch exists locally:** `git show-ref --verify --quiet refs/heads/<branch>`. If
   not, say so and stop; never guess which branch was meant.
3. **Run the project's test suites on the branch as it stands, before merging.** For a project
   with Python suites in Orclab's layout, that is every `skills/*/scripts/tests` and
   `hooks/scripts/tests` directory:
   ```bash
   for d in skills/*/scripts hooks/scripts; do [ -d "$d/tests" ] && (cd "$d" && python3 -m pytest tests/ -q); done
   ```
   For any other project, run whatever its own test command is (`npm test`, `cargo test`, `go test
   ./...`, `pytest`), found the way `superpowers:using-git-worktrees` finds it. Run them against
   the branch's tree — check it out in its worktree if it has one (`git worktree list`), otherwise
   `git stash` is *not* the tool (the tree is clean by step 1); use `git worktree add` to a
   temporary path and remove it after. If any suite fails, report the failure and stop. Nothing
   has been merged.
4. **Merge:** `git merge --no-ff <branch> -m "Merge <branch>: <one line saying what landed>"`.
   Draft that line from the branch's commit subjects (`git log <current>..<branch> --oneline`),
   not from the branch name. If the merge conflicts, stop and report the conflicting files; do
   not resolve conflicts on the user's behalf.
5. **Run the same suites on the merged result.** If any fails: stop, say so, and leave everything
   exactly as it is — the merge commit, the branch, and its worktree all still exist, nothing has
   been pushed, and `git reset --hard HEAD~1` is the user's call, not this command's.
6. **Clean up.** If `git worktree list` shows a worktree for `<branch>`, `git worktree remove
   <path>` (it is clean; step 1 and the merge guarantee that). Then `git branch -d <branch>` —
   lower-case `d`: if git refuses because it considers the branch unmerged, that is a signal worth
   reporting, not litter to force past with `-D`.
7. **Report:** the merge commit, the branch that landed, both suite results, and what was removed.

No confirmation prompt beyond the gates above — invoking the subcommand is the authorization.
````

- [ ] **Step 5: Add `release [tag]` after the `pr` section, at the end of the file**

This is `/orc-version`'s Release Flow, moved with its behaviour unchanged and `/orc-git`'s auth step in front. Append exactly:

````markdown
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
````

- [ ] **Step 6: Check the result mechanically**

Run: `grep -c '^## ' skills/orc-git/SKILL.md`
Expected: `10` (the seven from Step 1, plus "Two families", `merge`, `release`).

Run: `grep -n '^| `commit`' skills/orc-git/SKILL.md`
Expected: one line, containing `merge` on the left and `release` on the right.

Run: `grep -c 'orc-version' skills/orc-git/SKILL.md`
Expected: `1` — the single mention in `release`'s opening paragraph. `/orc-git` does not otherwise refer to the old home.

Run: `sed -n '1,/^---$/p' skills/orc-git/SKILL.md | sed '1d;$d' | grep -c '^argument-hint:.*merge <branch>.*release \[tag\]'`
Expected: `1`.

- [ ] **Step 7: Commit**

```bash
git add skills/orc-git/SKILL.md
git commit -m "v14: /orc-git gains release and merge, and states its git/GitHub split

release is /orc-version's Release Flow moved unchanged, with the auth step in front. merge
lands a branch locally with the suites run before and after, and decides nothing about
whether merging was the right way to land it.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: `/orc-version` — only about versions, and it proposes

**Files:**
- Modify: `skills/orc-version/SKILL.md`

**Interfaces:**
- Consumes: the subcommand name `/orc-git release` from Task 1 (it exists once Task 1 is committed).
- Produces: the bare-invocation behaviour Task 3's scenario tests.

- [ ] **Step 1: Record the before-state**

Run: `grep -n '^## Release Flow' skills/orc-version/SKILL.md`
Expected: one line (currently 166).

- [ ] **Step 2: Rewrite the frontmatter**

Replace lines 1–5 (through the closing `---`) with exactly:

```markdown
---
name: orc-version
description: Use when the user explicitly asks to use orc-version, or types /orc-version, to set or increment the current project's version, draft a changelog entry, and tag the commit locally - or, with no arguments, to be told what bump the commits since the last tag suggest and why.
argument-hint: <major>.<minor>[.<point>] | increment <major|minor|point> [--no-commit]
---
```

- [ ] **Step 3: Rewrite the routing step**

Replace the four numbered lines under `## Step 1: Parse $ARGUMENTS and route` with exactly:

```markdown
1. If `$ARGUMENTS` starts with `release` — go to **Moved: release** below. Do not run anything.
2. If `$ARGUMENTS` starts with `increment ` — go to **Increment Flow** below.
3. If `$ARGUMENTS` matches a version pattern (`<digits>.<digits>` or `<digits>.<digits>.<digits>`)
   — go to **Absolute-Set Flow** below.
4. If `$ARGUMENTS` is empty — go to **Bare Invocation** below.
```

- [ ] **Step 4: Rewrite Bare Invocation so it proposes**

Replace the whole `## Bare Invocation` section (from its heading to the line `Stop here — do not proceed to any bump logic on a bare invocation.`) with exactly:

````markdown
## Bare Invocation

Report the current version (from Step 0). If no current version exists yet, say so plainly and
show the four bump lines from the block below — everything after the `Apply …?` line — without a proposal: there is no range to read.

Otherwise, **propose a bump, with the reason stated.** Read the commits since the most recent
`v*` tag — the same range the changelog draft uses:

```bash
git log <tag>..HEAD --format='%B---COMMIT-BOUNDARY---'
```

If the range is empty, say there is nothing since `<tag>` and show the four bump lines from the block below, without the `Apply …?` line. If it is not, read
the messages (bodies, not just subjects) and classify what they describe:

- **major** — anything that removes or renames something a user of the project relies on: a
  command, a subcommand, a config key, a file format, a public function; or a message that says
  `BREAKING` or uses the `!:` subject convention.
- **minor** — otherwise, if anything was added: a new command, subcommand, option, skill, field,
  or capability.
- **point** — otherwise: only fixes, docs, refactors, tests.

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
````

- [ ] **Step 5: Point Apply step 4 at the new home**

In `## Apply the new version`, step 4 (**Tag — local only**), replace the sentence

`Do NOT push anything in this step. Report the new version and the tag, and mention that
`/orc-version release` is the separate, explicit next step if this version should become a
real, public GitHub Release.`

with

`Do NOT push anything in this step. Report the new version and the tag, and mention that
`/orc-git release` is the separate, explicit next step if this version should become a real,
public GitHub Release — it lives under `/orc-git` because it pushes and publishes, which nothing
in this command does.`

- [ ] **Step 6: Replace the Release Flow with the moved-notice**

Delete the entire `## Release Flow` section (from its heading to the end of the file) and append exactly:

````markdown
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
````

- [ ] **Step 7: Check the result mechanically**

Run: `grep -c '^## Release Flow' skills/orc-version/SKILL.md`
Expected: `0`.

Run: `grep -c 'gh release create\|git push origin' skills/orc-version/SKILL.md`
Expected: `0` — nothing in this skill pushes or publishes any more.

Run: `grep -c '/orc-git release' skills/orc-version/SKILL.md`
Expected: `3` (Apply step 4, and twice in the moved-notice).

Run: `grep -c 'orc-version release' skills/orc-version/SKILL.md`
Expected: `2` — both inside the moved-notice (its heading text and the message), nowhere else.

- [ ] **Step 8: Commit**

```bash
git add skills/orc-version/SKILL.md
git commit -m "v14: /orc-version is only about versions, and proposes a bump with its reason

The Release Flow is gone; 'release' reports the move to /orc-git release and stops. Bare
invocation reads the commits since the last tag and proposes major/minor/point with the
evidence that decided it, never writing a file until the user confirms.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: References, scenarios, and closing #20 and #28

**Files:**
- Modify: `README.md:30-36`
- Modify: `CLAUDE.md:121`
- Modify: `VERIFICATION.md` — Scenario 11 rewritten in place; three scenarios added before `## Recording the result`
- Modify: `BACKLOG.md` — `#20` and `#28` headings and layered resolutions

**Interfaces:**
- Consumes: `/orc-git merge`, `/orc-git release`, the moved-notice, and the bare-invocation proposal from Tasks 1–2.

- [ ] **Step 1: README bullets**

Replace the `/orc-version` bullet (three lines starting `- **/orc-version** — set or increment`) with:

```markdown
- **/orc-version** — set or increment the current project's version, draft a changelog entry from
  real git history, and tag the commit locally. With no arguments, proposes the bump the commits
  since the last tag suggest, and says why. Never pushes or publishes.
```

Replace the `/orc-git` bullet (two lines starting `- **/orc-git** — shortcuts for common git/GitHub`) with:

```markdown
- **/orc-git** — git and GitHub shortcuts: connect a repo, commit with a drafted message, push,
  commit-then-push (alias `cp`), branch/switch, merge a finished branch with the tests run before
  and after, check out a PR, and cut a GitHub Release from an existing tag. States which of its
  subcommands are plain git and which need `gh`.
```

- [ ] **Step 2: CLAUDE.md reference**

At `CLAUDE.md:121`, change `` `/orc-version release` (pushes and publishes) `` to `` `/orc-git release` (pushes and publishes) ``. Nothing else on that line or in that file.

- [ ] **Step 3: Rewrite Scenario 11 in place**

Replace the whole `## Scenario 11: /orc-version release` section (heading through the last `**Expected:**` line, before `## Scenario 12`) with:

```markdown
## Scenario 11: /orc-git release

**Caution:** if Scenario 9's probe bump wasn't kept (i.e. you already ran the revert commands
above), don't run this scenario against that reverted state — only run it against a real bump you
actually intend to publish. This is the only scenario in this script that makes something public
and irreversible.

1. After running Scenario 9 (or any real bump) and deciding to keep it, run `/orc-git release`
   with no tag.
2. **Expected:** it resolves the newest local `v*` tag, says which, pushes the commit and the tag
   to `origin`, and creates a real GitHub Release at
   `https://github.com/artificialorctelligence/orclab/releases` whose body is that version's
   `CHANGELOG.md` section — confirm at that URL or via `gh release list`.
3. Run `/orc-git release v0.0.1` (a tag that does not exist locally).
4. **Expected:** it says the tag does not exist and stops. Nothing is pushed, nothing created.
5. Run `/orc-version release`.
6. **Expected:** it reports that `release` has moved to `/orc-git release` and stops. It does not
   run the release, and `gh release list` shows nothing new.
```

- [ ] **Step 4: Add three scenarios with the allocator**

Use this worktree's own `python3 skills/orc-todo/scripts/run.py add verification "<title>" < body.md`, body from a scratch file. Titles and bodies, in this order — where a body says "Scenario X", write the number the allocator gave that scenario:

**X — `/orc-git merge lands a branch with the suites as its gates`**

```
1. In a scratch git repo with one committed file and a `tests/test_ok.py` containing a single
   passing test, create a branch `feature` with a worktree
   (`git worktree add ../feature-wt -b feature`), commit a second file on it, and return to the
   main checkout.
2. Run `/orc-git merge feature`.
3. **Expected:** the suite is run on the branch and reported passing; a `--no-ff` merge commit
   lands whose message says what the branch did (from its commit subject, not its name); the suite
   is run again on the merged result and reported passing; the worktree at `../feature-wt` is
   gone and `git branch --list feature` prints nothing.
4. Create a second branch `broken` whose one commit makes `tests/test_ok.py` fail. Run
   `/orc-git merge broken`.
5. **Expected:** the pre-merge suite fails, the command says so and stops; `git log --oneline -1`
   is unchanged and `broken` still exists.
6. Edit a tracked file in the main checkout without committing, then run `/orc-git merge broken`
   again.
7. **Expected:** it refuses before running anything, naming the uncommitted file.
8. Run `/orc-git merge no-such-branch`.
9. **Expected:** it says the branch does not exist and stops.
```

**Y — `/orc-version proposes a bump and says why`**

```
1. In a scratch repo with a `v0.1.0` tag, add three commits whose subjects are
   `Fix a typo`, `Add a --verbose flag`, and `Fix the exit code`. Run `/orc-version` with no
   arguments.
2. **Expected:** it reports the current version `0.1.0`, then proposes **minor** → `0.2.0`,
   citing the addition (`--verbose`) as the reason and counting the two fixes, and asks whether
   to apply it or pick another. `git status` is clean — no file was written.
3. Answer with `increment point` instead.
4. **Expected:** it honours the override: the changelog draft and version files go to `0.1.1`,
   not `0.2.0`.
5. In a scratch repo whose only commit since the tag has the subject `Remove the legacy
   --old flag`, run `/orc-version`.
6. **Expected:** it proposes **major**, naming the removal as the reason.
```

**Z — `/orc-git's split is stated, and the old home is gone`**

```
1. Run `/orc-git` with no arguments.
2. **Expected:** the listing shows `merge <branch>` and `release [tag]` among the subcommands.
3. Read `skills/orc-git/SKILL.md`'s "Two families under one name" table.
4. **Expected:** `merge` is on the universal-git side; `release`, `repo` and `pr` are on the
   `gh` side; `ci` is named as not built.
5. Run: `grep -rn "orc-version release" --include=*.md . | grep -v "docs/superpowers/\|BACKLOG.md\|CHANGELOG.md"`
6. **Expected:** the only hits are inside `skills/orc-version/SKILL.md`'s moved-notice. No other
   live file names the old command.
```

- [ ] **Step 5: Resolve #20 and #28**

`#20`'s heading gains ` (RESOLVED 2026-09-10)`; append to the entry's end:

```markdown
**Resolved 2026-09-10 — v14 shipped, as specced on 2026-09-08 and amended 2026-09-10.**
`/orc-version release` moved outright to `/orc-git release`, with a moved-notice in its old place
that names the new home and stops. `/orc-git` states its two families in its own skill — `commit`,
`push`, `branch`, `switch`, `merge` are git; `repo`, `pr`, `release` are `gh` — and is not renamed.
`/orc-release` did not change: `RELEASING.md`'s `**Run:**` marker was already the forge-agnostic
delegation mechanism, and #19 had made it carry the verb. `/orc-git ci` is a recorded shape, not
a build. `/orc-version` with no arguments now proposes a bump and states the evidence, never
writing until confirmed. Orclab still has no `RELEASING.md` of its own; `/orc-git release` is
directly typable, which is the path this entry said must exist.
```

`#28`'s heading gains ` (RESOLVED 2026-09-10)`; append:

```markdown
**Resolved 2026-09-10 — folded into v14 as `/orc-git merge <branch>`, decided by direflail
between three shapes.** It merges locally with the test suites as gates before and after, removes
the branch's worktree and deletes the branch with `-d`, and decides nothing about whether merging
was the right way to land — that question stays with a person, or with
`superpowers:finishing-a-development-branch`, which asks it. Typing the subcommand is the answer
"merge it locally," the same argument `push` makes for itself. The alternative, a `/orc-git land`
wrapping that skill's menu, was rejected as a name that adds no capability plus an availability
guard for the thing it wraps. The 2026-09-10 session that decided this had landed four branches
by hand, each with the same seven steps the subcommand now performs.
```

- [ ] **Step 6: The global grep**

Run: `grep -rn "orc-version release" --include=*.md . | grep -v "docs/superpowers/\|BACKLOG.md\|CHANGELOG.md"`
Expected: only lines from `skills/orc-version/SKILL.md` (the moved-notice) and `VERIFICATION.md` Scenario 11 step 5 (which deliberately invokes the old name to test the notice).

- [ ] **Step 7: Commit**

```bash
git add README.md CLAUDE.md VERIFICATION.md BACKLOG.md
git commit -m "v14 close-out: references moved, Scenario 11 rewritten, three scenarios, #20 and #28 resolved

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-review against the spec

- **The move, unchanged in behaviour, with auth in front; no alias; moved-notice that names and stops** → Task 1 Step 5, Task 2 Step 6. ✔
- **`/orc-git release` keeps reading `CHANGELOG.md`, tag→heading convention** → Task 1 Step 5 item 5. ✔ (The `--generate-notes` fallback when no section exists is an addition the spec did not state; it replaces a silent empty body and names which path was taken.)
- **Forge boundary table in the skill; not renamed; `ci` shape recorded, not built** → Task 1 Step 2. ✔
- **`/orc-git merge`: dirty-tree refusal, branch check, suites before, `--no-ff`, suites after, stop-and-leave on failure, worktree removal, `-d` not `-D`** → Task 1 Step 4, steps 1–7 match the spec's seven. ✔
- **Version suggestion: no-argument invocation, the changelog's own range, proposes with reason, never decides, never writes** → Task 2 Step 4. ✔
- **Four live references updated** → README (Task 3 Step 1), CLAUDE.md (Step 2), Scenario 11 (Step 3), orc-version's own text (Task 2). ✔
- **Testing: Scenario 11 rewritten covering named, defaulted, and nonexistent tag; the moved-notice; version suggestion incl. override and never-writes; boundary documented; the global grep** → Task 3 Steps 3, 4, 6. ✔
- **Global constraints: no dependency, no new top-level command, `/orc-release` untouched, no consuming project written** → Global Constraints; no task touches `skills/orc-release/` or `~/projects/orcshot`. ✔
- **Name consistency:** `merge <branch>` and `release [tag]` are spelled identically in the argument-hint, the routing list, the bare listing, the section headings, the README, and the scenarios. ✔
