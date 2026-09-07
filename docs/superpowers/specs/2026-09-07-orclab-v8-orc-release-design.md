# Orclab v8: `/orc-release` — design

## Goal

Give Orclab the ability to actually drive a project's own documented release process end to end —
guiding through `RELEASING.md`'s real ordered steps, enforcing its gates, checking preconditions
before acting, handing off cleanly at human steps, and remembering where it is across the hours or
days a real release spans.

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

**In scope:** a new `/orc-release` skill (pipeline runner + state cursor), three optional new prose
conventions in `release-checklist`, and the bundled script + tests supporting them.

**Explicitly out of scope:**
- **BACKLOG #6** (per-language manifest version bumping — `pyproject.toml`, `debian/changelog`) and
  the **`/orc-version` commit-ordering conflict** described below. Both stay open. Because
  `RELEASING.md` is the source of truth and its steps carry literal commands, Orcshot's steps 1, 8
  and 10 are driveable without `/orc-version` at all — so neither blocks this work.
- **Any change to `/orc-publish`.** It is reached from a release via delegation, unchanged.
- **Populating any real project's release content.** Orclab ships the mechanism; a consuming
  project's `RELEASING.md` and `.orclab/` content are its own, per `CLAUDE.md`'s dogfooding rules.

### The `/orc-version` ordering conflict (documented, not fixed here)

Worth recording because it was found during this design and is not obvious: `/orc-version`'s
"Apply the new version" flow does draft-changelog → update-manifests → **commit → tag** as one
atomic move. Orcshot's real process deliberately splits those — step 1 *edits* the version files,
and commit/tag/push does not happen until step 8, *after* the build, lint, PPA upload and
install-tests have all passed. The point is not committing a release until the artifact is
verified. Running `/orc-version` on Orcshot today would commit at step 1, violating its real
dependency order. This is a design assumption that does not survive a packaged-app release, not a
missing feature. It needs its own pass; it does not block v8.

## Architecture

Four pieces, one of which is "nothing changes."

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
4. Check preconditions — see below. In short: whatever the doc's own steps declare, plus exactly
   one built-in check (no release already in progress).
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

- the target version
- the path to the `RELEASING.md` being driven, and a hash of its content
- which steps are complete, by number **and** title
- which steps were skipped, each with its recorded reason
- when the release started, and when state was last updated

This is a position marker, not a second description of the process — there is exactly one
definition of the steps (`RELEASING.md`) and nothing here to drift out of sync with it.

**The content hash is load-bearing, not incidental.** `release-checklist` explicitly renumbers
steps when a new one is inserted mid-document. If the doc changed since the release began, "step 7"
may no longer mean the step 7 that was started. On resume, a changed hash produces a warning and a
stop, not a silent continue.

### 3. `release-checklist` grows three optional conventions

Added to its existing "Structuring steps" guidance (which today covers why-the-step-exists, exact
commands, and what-done-looks-like). All three are plain prose, human-first — someone following the
document by hand wants "don't start this if X" every bit as much as the runner does.

- **Preconditions** — what must be true before the step starts. Orcshot's step 6 would state that
  this version is not already published to the PPA, and that `gpg-agent` is unlocked: the two
  checks that would have caught this session's real near-misses.
- **Performed by hand** — stated plainly. A step may be *partly* manual: Orcshot's step 6 runs
  `dput` and then needs a human Launchpad "Copy packages" click for the resolute series. The runner
  executes what it can, then stops for the human portion.
- **Delegation** — a step may name an `/orc-*` command to run instead of literal commands.

**All three are optional, and absence is not an error.** Orcshot's `RELEASING.md` exists today with
none of them and must remain driveable — the runner simply has less information and asks more.
Adopting them improves a document; it is never a migration requirement.

### 4. `/orc-publish` — unchanged

No rework. It becomes reachable from a release through delegation.

## Command surface

```
/orc-release                    start a new release, or resume one in progress
/orc-release status             report position; change nothing
/orc-release skip <reason>      skip the current step, recording the reason
/orc-release abort              discard in-progress release state (confirmed first)
```

## What stops a run

Four things, and they are not all failures:

1. **A step's commands fail, or its "what done looks like" is not met.** Records where and why,
   reports the real output, and does not retry or skip on its own. The human fixes it and re-runs;
   the release resumes at that step.
2. **A precondition fails** — checked before the step runs, not after.

   **There is exactly one built-in precondition: no release is already in progress.** Everything
   else comes from the document's own steps. This is deliberate, and the tempting built-in is
   actively wrong: "the working tree is clean" would fail at every step after Orcshot's step 1,
   because that process intentionally leaves the version-file edits uncommitted until step 8. A
   runner cannot reliably tell a release's own in-flight edits from unrelated in-progress work, and
   guessing would either block every real release or wave through exactly the case that nearly bit
   this session. The project's own document is where that judgment belongs — a step that must not
   run against a dirty tree can say so, in the terms that are actually true for that project.
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

- **The bundled script owns what is deterministic and has real bug surface**: extracting numbered
  step boundaries from a markdown document, and reading/writing/advancing the state cursor
  (including hash comparison and skip recording).
- **Claude owns the judgment**: reading a step's body for the optional prose markers, and deciding
  whether a step's real output means it passed.

## Testing

Two layers, the same hard rule as v7:

1. **Real automated tests** for the bundled script, committed to Orclab: step extraction from a
   markdown document (including a document using none of the optional conventions), state
   read/write/advance, doc-hash change detection, and skip-with-reason recording.
2. **`VERIFICATION.md` scenarios** for the command's end-to-end behavior, run against a **synthetic
   throwaway `RELEASING.md` whose steps are no-ops** — never against a real release, from Orclab's
   own repo. Scenarios must cover: halting on a failed step (and *not* proceeding to the next),
   resuming at the right step afterward, refusing to start while a release is in progress, warning
   on a changed document hash, recording a skip with its reason, and stopping at a
   performed-by-hand step.

## Global Constraints

- Ships as a **skill only** (`skills/orc-release/SKILL.md`), no `commands/orc-release.md`.
- `RELEASING.md` is the **single definition** of the steps. The state cursor records position only,
  never step definitions.
- The runner **reads `RELEASING.md` in full before acting on any step**.
- **Halt on failure.** Never continue past a failed step, and never auto-retry or auto-skip.
- The three `release-checklist` conventions are **optional**; a document using none of them must
  still be driveable.
- **Never invent a release process.** No `RELEASING.md` means report and stop.
- Exactly **one built-in precondition** (no release already in progress). Every other precondition
  comes from the document's own steps — notably, there is no built-in clean-working-tree check.
- Skips require a recorded reason.
- A changed `RELEASING.md` hash mid-release warns and stops rather than resuming on step numbers
  that may have shifted.
- Per-step tracking only; no sub-step/checkbox modeling.
- Orclab's own repo contains **zero consuming-project release content**; all test fixtures are
  synthetic.
- Version: **0.8.0**.
