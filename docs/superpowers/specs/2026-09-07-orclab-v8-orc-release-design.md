# Orclab v8: `/orc-release` — design

## Goal

Give Orclab the ability to actually drive a project's own documented release process end to end —
guiding through `RELEASING.md`'s real ordered steps, enforcing its gates, checking preconditions
before acting, handing off cleanly at human steps, and remembering where it is across the hours or
days a real release spans.

That includes owning the version's whole lifecycle across the release, not just setting it once:
writing it consistently to every file that holds it, verifying that consistency rather than
assuming it, carrying it through all the steps, and — when a release is abandoned partway — rolling
back what can be rolled back while stating plainly what cannot.

## Why this exists

Found dogfooding `/orc-publish` against Orcshot's real release (2026-09-06/07), and recorded as
BACKLOG #12. direflail named the pattern directly: "i feel like you're finding out what to do one
piece at a time and then finding out later and we're patching up the process to fix it. do you
understand the whole process we're trying to do, and then are we applying that to the framework?"

The answer was no. Orcshot's `.orclab/publish/channels.yaml` had been written against
`RELEASING.md` step 6 in isolation, without the document having been read end to end. Everything
that followed — a `../*.changes` glob that would have tried to `dput` 33 accumulated past builds, a
near-miss uploading a version already live on Launchpad, a near-miss releasing on top of
uncommitted in-progress work, repeated confusion about step ordering — was a consequence of that,
patched one symptom at a time.

Mapping the whole 11-step process against what Orclab actually had:

| Step | Owned before v8 |
|---|---|
| 1. Pick a version | `/orc-version` — but only `CHANGELOG.md`/plugin manifests, not `pyproject.toml`/`debian/changelog` |
| 2-5. Tests, security check, build, lint | nothing |
| 6. Upload to PPA | `/orc-publish` |
| 7. Install-test on three real targets | nothing (human/VM steps) |
| 8. Commit, tag, push | `/orc-version` |
| 9. Confirm CI green | nothing |
| 10. Publish the GitHub Release | `/orc-version release` |
| 11. Sanity-check the update checker | nothing (human step) |

`/orc-publish` is not at fault — v7 was honestly scoped to "push built artifacts," and its fan-out
model held up well under real use. The gap is that that slice turned out to be roughly one step of
eleven. A real release is mostly an ordered pipeline; v7 built the fan-out.

## Scope

**In scope:**
- A new `/orc-release` skill — pipeline runner and state cursor.
- **The version's whole lifecycle across a release**: setting it consistently across every file
  that holds it, verifying that consistency, carrying it through all steps, and backing it out on
  abort. This closes **BACKLOG #6** and resolves the **`/orc-version` ordering conflict** below,
  rather than deferring them.
- **Four** optional new prose conventions in `release-checklist`.
- The bundled scripts + tests supporting all of the above.

**Explicitly out of scope:**
- **Any change to `/orc-publish`.** It is reached from a release via delegation, unchanged.
- **Populating any real project's release content.** Orclab ships the mechanism; a consuming
  project's `RELEASING.md` and `.orclab/` content are its own, per `CLAUDE.md`'s dogfooding rules.
- **Version-file formats no real project here uses.** See "Per-format handlers" below — this is a
  deliberate limit, not an oversight.

### Why the version lifecycle is in scope (it nearly wasn't)

This spec's first draft treated version handling as out of scope, reasoning that `RELEASING.md`
step 1 carries literal file-editing instructions, so the runner could just follow them. direflail
rejected that, correctly: "we need a version number to be set and to be consistent, and it is
eventually going to have to survive all steps of the process... if a step fails, you report on it.
we either back out the version change on the steps it did work on, or if we can't you tell me about
it."

That is right, and the original scoping was routing around a gap rather than closing it. Following
step 1's instructions covers *setting* a version once. It does not cover keeping two files
agreeing, carrying the version through eleven steps, or deciding what happens to those edits when
step 4 fails. Nothing in the design owned any of that.

### The `/orc-version` ordering conflict

`/orc-version`'s "Apply the new version" flow does draft-changelog → update-manifests →
**commit → tag** as one atomic move. That is correct for Orclab itself, where a version bump
essentially *is* the release. It does not survive a packaged-app release: Orcshot's process
deliberately separates those by six steps — step 1 *edits* the version files, and commit/tag/push
does not happen until step 8, *after* the build, lint, PPA upload and install-tests have all
passed. That ordering is the safety property. Committing at step 1 means every failed release
attempt leaves a `Release vX.Y.Z` commit behind for something that never released.

This is a design assumption, not a missing feature — and v8 resolves it via `--no-commit` below.

## Architecture

Five pieces, one of which is "nothing changes."

### 1. `/orc-release` — the pipeline runner

A skill (no `commands/*.md` — same reasoning as v7: skills work on both CLI and Desktop, commands
do not work on Desktop at all).

Behavior:

1. Locate the project's `RELEASING.md`. If there isn't one, say so plainly and stop — suggest
   `release-checklist` for creating one. Never invent a release process.
2. **Read `RELEASING.md` in full before acting on any step.** This is the `whole-process-first`
   discipline enforced by the framework rather than left to hope — and it is the specific failure
   that produced this entire spec.
3. Check for existing state (below). If a release is in progress, report position and resume;
   never silently start a second one.
4. Check preconditions — see below. In short: whatever the doc's own steps declare, plus two
   built-in checks (no release already in progress; a working-tree report at entry).
5. Walk the steps in the doc's own order. For each step: run its commands and judge the result
   against the doc's own "what done looks like"; or, if it delegates, invoke the named `/orc-*`
   command; or, if it is marked performed-by-hand, present it and stop for confirmation.
6. Record each step's completion in the state cursor as it goes.

**`/orc-release` halts on failure. This is deliberately opposite to `/orc-publish`, which
continues past one.** The two model genuinely different relationships between units of work:
`/orc-publish`'s leaves are independent destinations (a Snap Store outage says nothing about
whether Flathub would work, so one pass should report all of them), while a release's steps are a
dependent chain (if step 2's tests fail, step 4 builds broken code and step 6 uploads it
irreversibly to a public PPA). Fan-out tolerates a failed sibling; a gated pipeline must not.

The two compose at step 6: `/orc-release` delegates to `/orc-publish`, which attempts every
selected channel and reports each honestly; `/orc-release` then treats "any channel failed" as
*that step* having failed and halts the release there.

### 2. The state cursor

`.orclab/release/state.json` in the consuming project. Holds:

- the target version, and the version it replaced (needed to roll back)
- the path to the `RELEASING.md` being driven, and a hash of its content
- which steps are complete, by number **and** title
- which steps were skipped, each with its recorded reason
- which completed steps were marked irreversible in the document
- when the release started, and when state was last updated

This is a position marker, not a second description of the process — there is exactly one
definition of the steps (`RELEASING.md`) and nothing here to drift out of sync with it.

**The content hash is load-bearing, not incidental.** `release-checklist` explicitly renumbers
steps when a new one is inserted mid-document. If the doc changed since the release began, "step 7"
may no longer mean the step 7 that was started. On resume, a changed hash produces a warning and a
stop, not a silent continue.

### 3. The version lifecycle — `/orc-version` extended

The version is the spine of a release: set at step 1, it must stay consistent across every file
that holds it, survive all eleven steps, and be recoverable if the release is abandoned. All of
this lives in `/orc-version`, not in `/orc-release` — one place owns what it means to set a
project's version. `/orc-release` delegates.

**Per-format handlers, not generic detection.** v8 implements exactly the formats real projects
here use:

| Format | Shape |
|---|---|
| `.claude-plugin/plugin.json` + `marketplace.json` | existing behavior, unchanged |
| `pyproject.toml` | a `version = "X.Y.Z"` field |
| `debian/changelog` | **not a field to overwrite** — a new entry to prepend |

More formats get added when a real project needs one. BACKLOG #6's own reasoning stands and is
being followed, not overridden: each format carries real syntax and a real risk that a sloppy write
breaks a build, so this is a per-format feature rather than one speculative "detect any manifest"
abstraction.

`debian/changelog` deserves its own note because it is structurally unlike the others: it takes a
new entry with a strict format (package name, version, target series, urgency, body, and an
RFC-2822 signature line), where the *series* must be a real Ubuntu series the PPA supports —
Orcshot's own `RELEASING.md` warns that `unstable` is rejected outright by Launchpad. But
`/orc-version` already drafts changelog content from real git history for `CHANGELOG.md`; this is
the same drafting rendered into a different format. That unifies existing behavior rather than
duplicating it.

**`--no-commit`** resolves the ordering conflict. `/orc-version`'s apply flow splits: draft content
→ write every version-holding file → **stop**. Committing and tagging become the caller's business.
Default behavior is unchanged, so Orclab's own bump flow keeps working exactly as today.
`/orc-release` passes `--no-commit` at step 1, and the document's own step 8 does the committing.

**Consistency is verified, not assumed.** After setting, every version-holding file is read back and
confirmed to agree; a mismatch is reported rather than silently shipped. Orcshot's `RELEASING.md`
already states why this matters — the two files "must match, or the built `.deb`'s own version
won't line up with the source tree that produced it" — but nothing verified it until now. Because
the state cursor records the target version, `/orc-release` can re-run this check cheaply at any
later step, catching a stray edit or a bad merge mid-release.

**Rollback on abort, honest about its limits.** `/orc-release abort` backs out what it did locally —
version-file edits, and any commit or tag it created — and for steps marked irreversible (see the
fourth convention below) that already completed, it reports plainly what stands and cannot be
undone. Aborting at step 9 does not pretend it can unpublish step 6's PPA upload; it tells you the
upload is permanent and that the version number is consumed.

### 4. `release-checklist` grows four optional conventions

Added to its existing "Structuring steps" guidance (which today covers why-the-step-exists, exact
commands, and what-done-looks-like). All four are plain prose, human-first — someone following the
document by hand wants "don't start this if X" every bit as much as the runner does.

- **Preconditions** — what must be true before the step starts. Orcshot's step 6 would state that
  this version is not already published to the PPA, and that `gpg-agent` is unlocked: the two
  checks that would have caught this session's real near-misses.
- **Performed by hand** — stated plainly. A step may be *partly* manual: Orcshot's step 6 runs
  `dput` and then needs a human Launchpad "Copy packages" click for the resolute series. The runner
  executes what it can, then stops for the human portion.
- **Delegation** — a step may name an `/orc-*` command to run instead of literal commands.
- **Irreversible** — the step does something that cannot be undone (publishing to a public archive,
  pushing a tag, creating a release). This is what gives abort a real basis for separating what it
  can roll back from what it must simply report. It is equally useful to a human reader deciding
  whether to proceed.

**All four are optional, and absence is not an error.** Orcshot's `RELEASING.md` exists today with
none of them and must remain driveable — the runner simply has less information and asks more.
Adopting them improves a document; it is never a migration requirement. In particular, with no
irreversibility markers, abort reports every completed step and states plainly that it cannot
determine which were reversible, rather than guessing.

### 5. `/orc-publish` — unchanged

No rework. It becomes reachable from a release through delegation.

## Command surface

```
/orc-release                    start a new release, or resume one in progress
/orc-release status             report position; change nothing
/orc-release skip <reason>      skip the current step, recording the reason
/orc-release abort              abandon the release: roll back what is reversible,
                                report what is not (confirmed first)
```

`abort` is not merely "forget the state file." It rolls back the version-file edits and any commit
or tag the release created, then reports every completed irreversible step as something that
stands. See "Rollback on abort" above.

## What stops a run

Four things, and they are not all failures:

1. **A step's commands fail, or its "what done looks like" is not met.** Records where and why,
   reports the real output, and does not retry or skip on its own. The human fixes it and re-runs;
   the release resumes at that step.
2. **A precondition fails** — checked before the step runs, not after.

   **There are exactly two built-in checks.** Everything else comes from the document's own steps.

   1. **No release already in progress** — a hard stop.
   2. **A working-tree report at entry** — a warning that asks, not a hard block, and run only
      when *starting* a release, never on resume.

   The second one needs its reasoning recorded, because the obvious stricter version is wrong.
   "The working tree must be clean," enforced per step, would fail at every step after Orcshot's
   step 1 — that process intentionally leaves the version-file edits uncommitted until step 8, so a
   dirty tree from step 2 onward is correct, not suspicious. Enforced as a hard block even just at
   entry, it is *concretely* broken: Orcshot's repo carries a permanently untracked `.claude/`
   directory, so a hard block would refuse every release until someone committed it, ignored it, or
   disabled the check — and a check that cannot be satisfied gets deleted, leaving nothing.

   Leaving it entirely to the document was the cleanest option architecturally and was rejected for
   a specific reason: Orcshot's `RELEASING.md` does not declare that precondition today and
   realistically would not have, because nobody knew to write it until this session hit the
   problem. A design motivated by that failure that would not have prevented it is the wrong trade
   for tidiness.

   So: at entry, print the real `git status --short` output verbatim and ask whether to proceed.
   **Printing the actual file list is the entire value, not the warning itself** — a bare "the tree
   is dirty" gets waved through, while `src/orcshot/app.py | 237 ++------` with 215 deletions is
   instantly recognizable as unrelated in-progress work. Untracked and modified entries are both
   shown as git reports them; no classifier tries to suppress one, since that is how the real
   signal gets suppressed too. This is a stop-and-ask, not a rhetorical pause.

   **This is a floor, not a ceiling.** A document can still declare a stricter, more precise
   precondition on top of it — "only `pyproject.toml` and `debian/changelog` may be modified" is
   better than anything generic — and should. The built-in only guarantees a project gets something
   before anyone has thought it through.
3. **A human step** — a handoff, not a failure. The runner cannot verify a VM install-test or a
   web-UI click, so it takes the human's word, but it records *what was claimed done* rather than
   silently marking the step complete.
4. **A delegated command reports failure.**

**Skipping is allowed but never silent.** Real releases legitimately skip steps — Orcshot's own doc
already records one: step 11 for 0.2.0 was "covered incidentally rather than via a dedicated
re-test... Accepted as sufficient (direflail, 2026-08-27)." `/orc-release skip` requires a reason
and records it in state, mirroring how the document itself already records such calls.

**Tracking is per-step, not per-checkbox.** Orcshot's step 7 lists three install-test targets; those
stay the human's own tracking inside the document. Modeling sub-items would add structure for very
little gain.

## Script/prose split

Mirroring v7's division, which held up well:

- **The bundled scripts own what is deterministic and has real bug surface**: extracting numbered
  step boundaries from a markdown document; reading/writing/advancing the state cursor (including
  hash comparison, skip recording, and irreversible-step recording); and **reading and writing each
  version file format**, since a malformed `pyproject.toml` or `debian/changelog` write breaks a
  real build.
- **Claude owns the judgment**: reading a step's body for the optional prose markers, drafting
  changelog content from git history, and deciding whether a step's real output means it passed.

## Testing

Two layers, the same hard rule as v7:

1. **Real automated tests** for the bundled scripts, committed to Orclab:
   - step extraction from a markdown document, including one using none of the optional conventions
   - state read/write/advance, doc-hash change detection, skip-with-reason recording
   - **per-format version read/write**: `pyproject.toml`, `debian/changelog` (correct entry format,
     correct prepending, target series preserved), `plugin.json`/`marketplace.json`
   - **consistency verification**, including a deliberately mismatched pair being detected
   - **rollback**: restoring the prior version across every file it wrote
2. **`VERIFICATION.md` scenarios** for the command's end-to-end behavior, run against a **synthetic
   throwaway `RELEASING.md` whose steps are no-ops** — never against a real release, from Orclab's
   own repo. Scenarios must cover: halting on a failed step (and *not* proceeding to the next),
   resuming at the right step afterward, refusing to start while a release is in progress, warning
   on a changed document hash, recording a skip with its reason, stopping at a performed-by-hand
   step, the entry working-tree report (showing the real modified/untracked file list, continuing
   on "proceed", and **not** firing again on resume), and **abort rolling back version edits while
   reporting a completed irreversible step as standing**.

## Global Constraints

- Ships as a **skill only** (`skills/orc-release/SKILL.md`), no `commands/orc-release.md`.
- `RELEASING.md` is the **single definition** of the steps. The state cursor records position only,
  never step definitions.
- The runner **reads `RELEASING.md` in full before acting on any step**.
- **Halt on failure.** Never continue past a failed step, and never auto-retry or auto-skip.
- The four `release-checklist` conventions are **optional**; a document using none of them must
  still be driveable. With no irreversibility markers, abort reports every completed step and says
  plainly it cannot determine which were reversible, rather than guessing.
- **One place owns version-setting.** `/orc-version` does it; `/orc-release` delegates. Version
  logic is never duplicated into the runner.
- `/orc-version`'s **default behavior is unchanged** — `--no-commit` is additive, so Orclab's own
  existing bump flow keeps working exactly as it does today.
- Version files are **verified consistent** after being set, never assumed.
- **Per-format version handlers only** for formats a real project here uses (`plugin.json`,
  `marketplace.json`, `pyproject.toml`, `debian/changelog`). No speculative generic
  manifest-detection abstraction.
- **Abort never overstates what it can undo.** It rolls back local edits/commits/tags and reports
  completed irreversible steps as permanent.
- **Never invent a release process.** No `RELEASING.md` means report and stop.
- Exactly **two built-in checks**: no release already in progress (hard stop), and a working-tree
  report at entry (prints real `git status --short`, asks whether to proceed, **never blocks**, and
  runs only when starting a release — never on resume, since step 1 legitimately dirties the tree).
  Every other precondition comes from the document's own steps.
- Skips require a recorded reason.
- A changed `RELEASING.md` hash mid-release warns and stops rather than resuming on step numbers
  that may have shifted.
- Per-step tracking only; no sub-step/checkbox modeling.
- Orclab's own repo contains **zero consuming-project release content**; all test fixtures are
  synthetic.
- Version: **0.8.0**.
