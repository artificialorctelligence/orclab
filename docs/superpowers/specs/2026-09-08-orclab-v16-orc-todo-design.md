# Orclab v16: `/orc-todo` — the backlog you can talk to, and the collisions it prevents

**Status:** design, approved 2026-09-08. Supersedes the "next step" of BACKLOG #22.

## The problem

On 2026-09-08 two Claude sessions independently implemented the whole of the v12 artifact-preflight
plan, start to finish. The duplication surfaced only at `git merge`, as an add/add conflict.

Two distinct failures happened inside that one incident, and they need different mechanisms:

1. **Numbered-resource collision.** Both sessions allocated `VERIFICATION.md` Scenario 45; both took
   `BACKLOG.md` `#23` and `#24` from the same `#22` high-water mark. Each read the file, found the
   maximum, added one, and wrote — a read-then-write race with no shared state between them. This is
   BACKLOG #22 exactly.
2. **Duplicate work.** Two hours of implementation, twice. No number was involved. Nothing recorded
   that v12 was already being built, so nothing could have told the second session to stop.

An allocator fixes (1) and does nothing for (2). A lane record fixes (2) and has no opinion about
numbers. They ship together because they arose from one incident, not because they share machinery —
BACKLOG #22's own rule stands: **exclusion and ordering are different mechanisms and must not
merge.**

There is a third, adjacent gap this closes because it is cheap and already documented as unguarded:
`release-checklist` requires renumbering `RELEASING.md` steps when one is inserted mid-document, and
says outright that prose cross-references like "see step 9 below" shift too, **and nothing warns
about those**. In the real 2026-09-07 incident three references had to move and five correctly
stayed put, all by hand.

## What this is, and what it is not

`/orc-todo` is the user-facing command. It is how you look at and manipulate the backlog, and how
you see and shape lanes. Everything else in this spec is machinery it sits on top of.

**It is not** a scheduler, a daemon, a long-running coordinator, or a dependency graph. Lanes are
N sequential lists that happen to run concurrently. Nothing launches anything.

**It is not** a replacement for `backlog-discipline`. That skill still owns what an entry must
contain, how one is resolved, and when one may be deleted. `/orc-todo add` is a front door to those
rules, not a way around them: an entry that would not pass the skill does not pass the command.

## Architecture

Four components, deliberately separable.

### 1. The lock

Mutual exclusion for allocation. One lock, not one per resource, and lane-agnostic — settled in
BACKLOG #22 because per-resource locks reintroduce AB-BA deadlock the moment a work item needs two
numbers at once, which v12's own plan did (a backlog entry *and* a verification scenario).

- Acquired with a single atomic operation: `os.open(path, os.O_CREAT | os.O_EXCL)`. "Check if
  locked, then lock" is a time-of-check-to-time-of-use race and is the standard way this pattern is
  broken.
- The lock file records **PID, start time, and a short description** of what holds it.
- A waiter retries for a bounded period, then fails with a message naming the holder — never
  silently, never forever.
- **Never auto-cleared, even when the PID is provably dead.** direflail's own operational note: a
  lock found when none is expected is worth investigating rather than clearing reflexively. A
  waiter that finds a dead holder says so explicitly, names the PID and the age, and points at
  `/orc-todo lock clear`.

### 2. The allocator

Owns the write end to end — it allocates the number *and* writes the entry *and* commits, inside
one lock hold. Chosen over "hand out a number and trust the caller to write" because there is then
nothing to bypass: an agent cannot take a number and forget to use it, or write without taking one.

Sequence, entirely inside the lock:

1. Resolve the next number: `max(stored counter, highest number scanned from the canonical file)`,
   plus one. The scan is what makes the counter self-healing — a fresh clone or a cleaned `.git`
   loses the counter, and the file is still there to recover from.
2. Render the entry from the caller's text into the file's house format.
3. Insert it at the file's anchor.
4. Commit **that one file by path**. Never `git add -A` — the canonical checkout may hold unrelated
   work.
5. Update the stored counter, release the lock.

**One mechanism, two files, via a per-file descriptor** — not two implementations. A descriptor
carries: the heading pattern (`## #{n}: {title}` vs `## Scenario {n}: {title}`), the number-extraction
regex, and the insertion anchor. `BACKLOG.md` appends at end of file; `VERIFICATION.md` inserts
immediately before its trailing `## Recording the result` section.

### 3. The lane record

An ordered list of work items per lane, and which item is currently in progress. Queried, never
executed — nothing launches a session, which is what keeps this out of daemon territory.

A **lane item is a design spec or an implementation plan**, identified by its `vNN` name. Not a
backlog number: `#12` is a resolved entry about publish pipeline gaps while `v12` is the preflight
work, and the two have nothing to do with each other. The mapping is many-to-many in reality — v14
and v15 both derive primarily from `#17`, and v13 cites `#18`, `#21` and `#15` — so backlog numbers
cannot name lane items distinctly even setting the ambiguity aside.

**An unspecced item is refused entry to a lane, with an immediate offer to spec it.** Once the spec
exists, ask which lane it belongs in. This refusal is load-bearing rather than pedantic: `#17` alone
is ambiguous precisely because speccing it could produce either v14 or v15.

### 4. The `RELEASING.md` cross-reference check

Not part of the allocator, and deliberately so: `RELEASING.md` step numbers are **positional**, not
identities. `release-checklist` requires renumbering on mid-document insertion, so there is no "next
number" to hand out — inserting step 7 rewrites 7–11 into 8–12.

What is genuinely missing there is a check that prose references survived a renumber. This lives in
`skills/orc-release/scripts/orc_release/steps.py`, beside `numbering_warning`, which already does
the sibling job of catching non-contiguous headings. It scans step bodies for references of the form
"step N" and reports any that point past the end of the document, or at a step whose title no longer
matches what the reference implies.

## Where state lives

All shared state lives in **`$(git rev-parse --git-common-dir)/orclab/`**.

That path resolves to the *same* directory from the main checkout and from every worktree, which is
the whole point: yesterday's two sessions each held their own copy of `BACKLOG.md`, so a lock on
"the file" would have locked two different files and protected nothing. It is also outside every
working tree, so it never appears in a diff, never merges, and never conflicts.

| File | Holds |
|---|---|
| `lock` | Existence is the lock. Contents: PID, start time, holder description. |
| `counters.json` | Highest number issued per resource. A cache; the file scan is the truth. |
| `lanes.json` | Lane names, their ordered items, and which item is in progress since when. |

**The canonical file the allocator writes** is the one in the main checkout, resolved as
`<git-common-dir>/..`. This is BACKLOG #22's load-bearing decision: every agent reaches one real
file rather than its own copy.

Two consequences, both accepted:

- **An entry lands on the main checkout's branch, not the agent's feature branch.** Branches then
  never touch `BACKLOG.md` and cannot conflict on merge — a real benefit — but an entry survives
  even if the work that motivated it is abandoned. Acceptable for a findings ledger.
- **The allocator refuses when the canonical file has uncommitted changes**, naming the file and
  saying to commit or stash. It cannot commit "just its own addition" to a file someone is
  mid-edit in, and committing their work for them is worse than a legible refusal. The lock is held
  for well under a second, so this is rare and never a wait.

## The SessionStart hook

The lane record only prevents duplicate work if something reads it without being asked. Yesterday
nobody forgot to check — there was nothing to check and no rule to forget.

A `SessionStart` hook (matcher `startup|resume|clear|compact`, the shape already proven by
ponytail's own live hook and by Orclab's existing `PreToolUse` wiring for `secret_guard.py`) reads
the shared state and injects context when, and only when, there is something to say:

- any lane with an item in progress, with its name and how long it has been running
- any lock that exists, with its holder and age

Silent otherwise. A session that starts when nothing is running sees nothing.

## Command surface

```
/orc-todo                                   list open entries, one line each; lanes if any exist
/orc-todo <n>                               expand entry n in full
/orc-todo add [text]                        add an entry, through backlog-discipline's rules
/orc-todo remove <n>                        delete an entry, through backlog-discipline's rules
/orc-todo lane create <name> <v13,v14>      create a lane with an ordered item list
/orc-todo lane modify <name> <v14,v13>      reorder, add, or drop items
/orc-todo lane delete <name>                remove a lane
/orc-todo lock status                       what holds the lock, since when, whether it is alive
/orc-todo lock clear                        release a lock you have decided is stale
```

Listing shows one line per **open** entry — number, title, and a marker for partially-addressed
ones. 25 entries of which 12 are open, most several paragraphs long, is not a thing to dump.

`add` walks `backlog-discipline`: it takes what you give it, asks for the reasoning if what you gave
is thin, and refuses to write a stub. `remove` honours the rule that numbers are permanent — the
section goes, nothing is renumbered, and the number is never reissued.

## Reach

The backlog half works in **any project with a `BACKLOG.md`**, because `backlog-discipline` is
already a shipped skill that consuming projects use — Orcshot's own backlog is at `#198` and has the
identical race.

The `VERIFICATION.md` allocator and lanes activate only where those files exist, and say so plainly
rather than erroring.

## Changes to existing components

- **`backlog-discipline`**: the "Numbering" section stops saying "scan the file for the highest `N`"
  and says "call the allocator." Its git-history exception for a deleted maximum entry moves into
  the allocator, where it becomes the file scan that already backstops the counter.
- **`backlog-discipline`, the task-list line.** "Don't turn this into a general task list — it's for
  findings, not routine planned work" is removed. Ten of twelve open entries are things that need
  doing; the line describes a file that does not exist, and it is phrased by the intent a reader
  brings rather than the situation it applies to — the exact failure mode `CLAUDE.md` names. It is
  replaced by what it was actually protecting: *an entry earns its place by carrying reasoning
  someone would otherwise re-derive. Work you will finish this session is not an entry, it is work.*
- **`orc-release`**: gains the cross-reference check in `steps.py`, surfaced the way
  `numbering_warning` already is.
- **`release-checklist`**: its "nothing warns about those" note gains a pointer to the new check.
- **`hooks/hooks.json`**: gains the `SessionStart` entry.

## Error handling

| Situation | Behaviour |
|---|---|
| Lock held by a live process | Retry for a bounded period, then fail naming PID, age, holder |
| Lock held by a dead process | Fail immediately, name it as apparently stale, point at `lock clear` |
| Counter missing or behind the file | Silently self-heal by taking the file scan's maximum |
| Canonical file has uncommitted changes | Refuse before taking the lock; name the file; say commit or stash |
| Not a git repository | Every shared-state feature reports unavailable; nothing pretends to work |
| No `BACKLOG.md` in this project | `/orc-todo` says so; it never creates one silently |
| Lane item has no spec | Refused, with an offer to spec it now |
| `lock clear` with no lock present | Says so; not an error |

## Testing

Bundled Python, tested the way `orc-publish` and `orc-release` already are — `tests/` beside
`scripts/`, empty `conftest.py` at the `scripts/` root, run with
`cd skills/orc-todo/scripts && python3 -m pytest tests/ -v`.

The tests that matter most, because they cover what unit tests usually miss here:

- **Two real concurrent processes** both allocating, asserting they receive different numbers and
  both entries land. Not two sequential calls — the race is the thing being tested.
- **Atomicity of acquisition**: the `O_CREAT | O_EXCL` path, asserted to fail on an existing lock.
- **Counter self-heal**: delete `counters.json`, assert the next number still follows the file.
- **Refusal on a dirty canonical file**, asserted to happen *before* the lock is taken.
- **A stale lock is reported, never cleared** — the test fails if the lock file disappears.
- Per-file descriptor round-trips for both `BACKLOG.md` and `VERIFICATION.md`, including
  `VERIFICATION.md`'s insertion before `## Recording the result` rather than at end of file.

A `VERIFICATION.md` scenario covers the part unit tests cannot: that `/orc-todo`'s listing is
readable, and that a second session really is told about a lane in progress.

## Scope boundaries

- **Not a runner.** Lanes record order; nothing starts a session, supervises a process, or handles a
  crash.
- **Not a DAG.** Lanes are linear. Nothing expresses "v13 requires v12 *and* #19".
- **Not cross-machine.** PID liveness works on one host. Every real case here is one machine.
- **Not `RELEASING.md` step allocation.** Positional numbers, wrong shape; the cross-reference check
  is what that file actually needs.
- **Not `.git/index.lock`.** Git handles that, and worktrees already avoid it.
- **Scenario 1 of `VERIFICATION.md` must be updated by this work.** Its steps 1 and 3 currently
  encode the read-then-write race as expected behaviour ("note the highest `#N`" … "a new `#<N+1>`
  entry is added"). It is a live example of the bug and will describe the allocator instead.

## Decision log

Recorded so a later reader does not relitigate them.

| Decision | Why |
|---|---|
| Shared `.git` dir for state | Same path from every worktree; outside every working tree, so it cannot merge-conflict |
| Allocator owns the write | Nothing to bypass; a number cannot be taken and unused, or a write made unallocated |
| All three components in one build | direflail's call, over a narrower lock-and-allocator scope |
| Lanes are a record, not a runner | Honours #22's "not a daemon"; avoids supervision and partial-failure semantics |
| Lane items are specs, not backlog numbers | `#12` and `v12` are unrelated; the real mapping is many-to-many |
| Unspecced items refused from lanes | An unspecced entry is genuinely ambiguous — `#17` could become v14 or v15 |
| `RELEASING.md` gets a checker, not the allocator | Its numbers are positional and deliberately renumbered |
| Command named `/orc-todo` | The name direflail will type; the skill line it appeared to contradict was itself wrong |
| Never auto-clear a stale lock | direflail's note: an unexpected lock is a signal, not litter |
| `SessionStart` hook, not prose | Yesterday's failure was not a forgotten rule; it was no rule at all |
