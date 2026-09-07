---
name: orc-release
description: Use when the user explicitly asks to use orc-release, or types /orc-release, to drive a project's own RELEASING.md release process end to end - running its ordered steps, enforcing its gates, and tracking where the release is across sessions.
allowed-tools: Read, Bash(python3 *), Bash(git status *)
---

# orc-release

Drives this project's own `RELEASING.md` from start to finish. `RELEASING.md` is the single
definition of the steps — this skill never invents a release process, and never reorders one.

**This halts on failure.** That is deliberate and is the opposite of `/orc-publish`, which
continues past a failed channel. Publish channels are independent siblings; release steps are a
dependent chain, where step 6 uploading irreversibly to a public archive is only valid because
step 2's tests actually passed.

`allowed-tools` deliberately pre-approves only this skill's own plumbing — `Read` for
`skills/orc-version/SKILL.md`, `python3` for the `run.py` calls below, and `git status` for the
working-tree report. **The project's own release commands are deliberately NOT pre-approved.**

That is a feature, not an oversight. `pytest` is harmless; `dput` uploads irreversibly to a public
archive. Since a downstream project's commands can't be enumerated ahead of time, the honest
choice is to let each one surface a permission prompt at the moment it runs — a visible
confirmation immediately before the irreversible thing happens, on exactly the operations that
most deserve one. Granting unscoped `Bash` would buy fewer prompts by removing that friction from
the riskiest steps in the whole process.

Expect several prompts during a real release, and treat each as the gate it is. The standing
obligation holds regardless: **only ever run commands the document itself states, or the `run.py`
calls below.** Never invent a command, and never widen a step's command beyond what is written.

## Commands

| Command | What it does |
|---|---|
| `run.py steps` | Parse `RELEASING.md` into its numbered steps |
| `run.py status` | Report position; changes nothing |
| `run.py start X.Y.Z` | Begin a release |
| `run.py complete <N>` | Record a step as done |
| `run.py skip <N> --reason "<why>"` | Record a deliberate skip |
| `run.py finish` | Close a release that actually shipped: summarize and clear state, rolling back **nothing** |
| `run.py abort` | Abandon a release: roll back what is reversible, report what is not |
| `run.py version-set`, `version-verify`, `version-rollback` | Version-file handling (see below) |

`run.py` finds the project root by walking up to the git root, so it works from any subdirectory.
`--root <path>` overrides that when you need to point it somewhere else.

## Step 0: Read the whole document first

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py steps
```

If this reports no `RELEASING.md`, tell the user plainly and stop — suggest the
`release-checklist` skill for creating one. Never invent steps.

Then **read the real `RELEASING.md` yourself, in full, before acting on any step.** The script
gives you structure; the document gives you the actual instructions, the gates, and the reasons
each step exists. Acting on step N without having read steps N+1 onward is the specific failure
this skill exists to prevent.

## Step 1: Establish where you are

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py status
```

- **A release is in progress** → report the position and resume at the next step. If status warns
  the document CHANGED, stop and tell the user: step numbers may have shifted, so re-read the
  document before continuing.
- **No release in progress** → this is a new release; continue to Step 2.
- `/orc-release status` on its own is a read-only query: report and stop.

## Step 2: Starting a new release (skip entirely when resuming)

Show the working tree before anything else:

```
git status --short
```

Show the user **the real output, verbatim**. This is not a formality: a bare "the tree is dirty"
gets waved through, while a real file list makes unrelated in-progress work instantly
recognizable. Ask whether to proceed. **This never blocks** — it is a stop-and-ask, and only
happens when starting, never on resume (a release legitimately dirties the tree at step 1).

Then confirm the target version with the user and start:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py start X.Y.Z
```

## Step 3: Walk the steps in order

For each step, in the document's own order:

1. **Check its preconditions**, if it states any. If one fails, stop and report — do not proceed.
2. **Carry it out:**
   - Marked **performed by hand** → present what the human must do, then stop and wait for their
     confirmation. Record what they say they did; never mark it complete on your own.
   - Marked **Run: /some-command** → invoke that command. If it reports any failure, this step has
     failed.
   - Otherwise → run the document's own commands.
3. **Judge the result against the document's own "what done looks like."** Not "did it exit 0" —
   the document's stated bar.
4. On success:
   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/run.py complete <N>
   ```
5. On failure: **stop.** Report what failed and the real output. Do not retry, do not skip, do not
   continue to the next step. The user fixes it and re-runs `/orc-release`, which resumes here.

If any `run.py` command — not just `status`; `complete` and `skip` warn on this too — reports
that `RELEASING.md` has changed, stop and re-read it before continuing.

If a command warns about an **unclosed code fence** or about **non-contiguous step numbers**, stop
and re-read the document before acting. Both mean the parsed step list may be shorter than the
real release — an unclosed fence swallows every step below it, so a release that looks finished
may never have reached its own test gate or its irreversible upload.

### Closing the release

When the **last** step passes, the release is over — close it:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py finish
```

It refuses while any step is still outstanding, and otherwise prints a summary (version, steps
completed, steps skipped with reasons, irreversible steps that now stand) and clears the state
cursor. **It rolls back nothing.** Relay its summary to the user.

**Never use `abort` to close a finished release.** `abort` is for *abandoning* one: it rolls the
version files back to their pre-release values, which on a repo whose release commit and tag
already exist is straightforwardly wrong. `finish` is the only correct end of a release that
shipped.

## Skipping a step

Only when the user explicitly asks, and only with a real reason:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py skip <N> --reason "<why>"
```

Never skip a step on your own initiative.

## Aborting

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py abort
```

Only for **abandoning** a release, never for closing one that shipped — use `finish` for that.

Relay its output exactly. It rolls back version-file edits and reports which completed steps
cannot be undone. **Never claim more was undone than it actually reports** — telling someone a
release was cleaned up when a public upload already happened is worse than saying nothing. Its
rollback is deliberately partial (a prepended `debian/changelog` entry is never rewritten
blindly), so it may report that the version files now disagree and name what to clean up by hand.
Pass that on in full; the user's tree really is inconsistent until they do it.

## Version handling

Version files are set through `/orc-version`, so there is one implementation — never write a
version file yourself. Reach it by reading its real file,
`${CLAUDE_SKILL_DIR}/../orc-version/SKILL.md`, and following its instructions yourself
(the same pattern this plugin's other components use to reach one another).

Whatever arguments you hand it must include `--no-commit`. Within a release the version is set
early, at this step, but must **not** be committed here — the document's own later step does the
committing, once the artifact is verified. Committing at set-time would leave a release commit
behind for every attempt that never shipped.

After setting a version, always confirm the files agree:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py version-verify
```

While a release is in progress this checks two things: that the version files agree with each
other, **and** that they agree with the release's target version — a bad merge that moves every
file to one consistent but wrong version is caught this way. Because of that second check, run it
only *after* the version has been set; before that the files legitimately still hold the old
version. It is cheap, so re-run it at any later step.

## Notes

- A document using none of the optional markers is completely valid. You simply have less
  information: ask the user rather than assuming a step is safe to automate.
- Report each step's real output. Never paraphrase a failure into something softer.
