---
name: orc-release
description: Use when the user explicitly asks to use orc-release, or types /orc-release, to drive a project's own RELEASING.md release process end to end - running its ordered steps, enforcing its gates, and tracking where the release is across sessions.
allowed-tools: Bash(python3 *), Bash(git status *)
---

# orc-release

Drives this project's own `RELEASING.md` from start to finish. `RELEASING.md` is the single
definition of the steps — this skill never invents a release process, and never reorders one.

**This halts on failure.** That is deliberate and is the opposite of `/orc-publish`, which
continues past a failed channel. Publish channels are independent siblings; release steps are a
dependent chain, where step 6 uploading irreversibly to a public archive is only valid because
step 2's tests actually passed.

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

Relay its output exactly. It rolls back version-file edits and reports which completed steps
cannot be undone. **Never claim more was undone than it actually reports** — telling someone a
release was cleaned up when a public upload already happened is worse than saying nothing.

## Version handling

Version files are set through `/orc-version`, so there is one implementation — never write a
version file yourself. Reach it by reading its real file,
`${CLAUDE_SKILL_DIR}/../../commands/orc-version.md`, and following its instructions yourself
(the same pattern this plugin's other components use to reach one another).

Whatever arguments you hand it must include `--no-commit`. Within a release the version is set
early, at this step, but must **not** be committed here — the document's own later step does the
committing, once the artifact is verified. Committing at set-time would leave a release commit
behind for every attempt that never shipped.

After setting a version, always confirm the files agree:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py version-verify
```

## Notes

- A document using none of the optional markers is completely valid. You simply have less
  information: ask the user rather than assuming a step is safe to automate.
- Report each step's real output. Never paraphrase a failure into something softer.
