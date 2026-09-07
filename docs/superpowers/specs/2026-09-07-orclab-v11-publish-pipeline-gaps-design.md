# Orclab v11: the three gaps snap/flatpak exposed — design

## Goal

Close the three real framework gaps that surfaced when asking what it would take for Orclab to
drive a genuine apt/snap/flatpak pipeline, so a consuming project can configure a
not-yet-onboarded distribution channel honestly and run a long publish action without hanging.

Three parts, no new components:

- **A.** A fifth optional marker in `release-checklist` — `**One-time setup:**` — and the rule
  `/orc-release` follows when it meets one.
- **B.** `/orc-publish` reporting a deliberately-empty channel leaf in the same honest wording the
  distro tree already uses.
- **C.** A timeout strategy for `execute_plan` — closing **BACKLOG #11**.

## Why this exists

The starting question was "complete the work in getting the apt/snap/flatpak pipeline working with
Orclab." Checking the real state first (2026-09-07, live) changed what that means:

| Channel | Real state |
|---|---|
| apt (PPA) | Working. `ppa.noble` has a genuine `dpkg-buildpackage`/`debsign`/`dput` action. |
| snap | `snap info orcshot` → *no snap found*. The name has never been registered in the Snap Store. CI only builds and installs `--dangerous`. |
| flatpak | `flathub.org/api/v2/appstream/org.orcshot.Orcshot` → 404, `github.com/flathub/org.orcshot.Orcshot` → 404. Never submitted. CI only builds and lints. |

So snap and flatpak are not "missing an action." They have never been onboarded — a one-time,
account-gated, externally-reviewed step that no existing Orclab component models.

### BACKLOG #12 is already closed, and this spec is not it

#12 asked whether Orclab needed a pipeline concept: ordered steps, gates/preconditions, and a way
to represent a step a *human* performs. v8 shipped exactly that, and the mapping is complete:

| #12 asked for | v8 shipped |
|---|---|
| Ordered steps with real gates | `/orc-release` walks `RELEASING.md` in order and halts on failure |
| Preconditions | the `**Preconditions:**` marker |
| Steps a human performs (a Launchpad "Copy packages" click, install-testing on real VMs) | the `**Performed by hand.**` marker |
| `/orc-publish` as one stage rather than the whole thing | the `**Run:** /some-command` delegation marker |
| Position tracked across sessions | `run.py`'s state cursor |

This spec deliberately does **not** revisit that. What snap and flatpak expose is narrower and
genuinely uncovered by v8.

## Scope

**In scope:**
- The `**One-time setup:**` marker in `release-checklist`, and `/orc-release`'s rule for it.
- `format_plan`/`execute_plan` wording for an action-less channel leaf.
- A per-leaf `timeout:` key, a default, a `--timeout` override, and a distinct `timed out` status.
- Tests for all of the above, in the existing `skills/orc-publish/scripts/tests/` suite.

**Explicitly out of scope:**
- **Populating any real project's content.** No Orcshot `RELEASING.md` step, `channels.yaml` leaf,
  or setup guide is written here. Per `CLAUDE.md`'s dogfooding rules, Orclab ships the mechanism;
  a consuming project's own content is its own. Orcshot's BACKLOG #197 remains Orcshot's.
- **Performing any real onboarding.** No `snapcraft register`, no Flathub submission. Both are
  account-gated, irreversible, and externally reviewed; part A exists precisely so they are never
  done blindly.
- **Routing around `debsign`'s interactive prompt** (`--no-tty`, a pre-supplied passphrase).
  BACKLOG #11's own scope boundary already excludes this, and it still belongs to whoever wires up
  a real leaf, not to the generic mechanism.

## A. `**One-time setup:**`

### The convention

A fifth optional prose marker, written inside the step that needs it:

```markdown
**One-time setup:** <what this is, and what it is scoped to — per machine, per account, per project>

<how to tell it is already in place — a real command or a real observation>

<the setup commands themselves>
```

This is not invented. Orcshot's own `RELEASING.md` already does it twice, organically and
inconsistently: step 3 writes `**One-time setup**, once per machine` for Semgrep's login; step 6
writes the same idea as loose prose for the `~/.dput.cf` entry. The skill has never mentioned it,
so every project rediscovers the pattern, and two spellings already coexist in one document.

The block MUST carry a **checkable** "how to tell it is already in place" — the same standard the
skill already sets for `**Preconditions:**` ("prefer the specific and checkable over the generic").
Without it the runner has nothing to test and is reduced to asking blind.

### The rule `/orc-release` follows

When a step carries a `**One-time setup:**` block:

1. **Run only the check.** It is read-only by construction.
2. **Check passes** → the setup is already in place. Say so, and carry on with the rest of the
   step. Nothing to do.
3. **Check fails** → **stop.** Name exactly what is missing, in the document's own words. Ask
   whether the user wants it set up now, and ask whatever questions the setup itself needs
   (which account, which key, which store name). Only run the setup commands once they say yes.
4. **Never run a setup command unprompted**, and never treat a failed check as a step failure that
   the runner can resolve on its own initiative.

**Standing up a distribution channel is always something the user asks for directly.** This is the
load-bearing rule of part A, and it is why the check/setup split exists rather than a single
"run the setup" instruction.

Two concrete failures this prevents, both real:
- `snapcraft register orcshot` succeeds exactly once. A runner that executes a setup block blindly
  halts release 2 on a step that was already fine.
- A Flathub submission is a pull request reviewed by other people over days. It is not a command
  that completes inside a release, and it must never be opened as a side effect of one.

### Why setup state is not tracked

`/orc-release`'s state cursor is per-release. Setup is per-machine and per-account: it survives
every release, and it disappears the moment the release is cut somewhere else. A stored "setup
done" flag would be confidently wrong on a new machine — the exact failure mode a check that reads
the real world cannot have. Checking is cheaper than tracking and cannot go stale.

## B. Honest reporting for a deliberately-empty channel leaf

Today a channel leaf with no `action:` renders as `(no action set)` in the plan and
`not attempted (no action set)` in the summary. Orcshot's `snap: {}` and `flatpak: {}` are
deliberate — they record a known, real target with no publish mechanism yet — and that wording
makes them read as an omission.

The distro tree already has the right words for this exact idea:
`no channel set (known target, not yet actionable)`. The channel side adopts the parallel form:

- `format_plan`: `<path>: (known channel, not yet actionable)`
- `execute_plan` detail: `known channel, not yet actionable`, status unchanged at `not attempted`.

**No schema change is needed**, and none is added. `snap: {}` is already unambiguous: a misspelled
key is not a subset of `LEAF_KEYS`, so the node parses as a *branch* yielding no leaves at all,
which cannot be confused with an empty leaf. Only the wording was wrong.

## C. Timeout strategy for `execute_plan`

BACKLOG #11 asked for three decisions before implementation — default value, whether it is per-leaf
configurable, and what the summary line says. All three are answered here.

- **Per-leaf, with a default.** `timeout` joins `LEAF_KEYS`; `Node.timeout` returns it (seconds,
  `None` when unset). `execute_plan(leaves, default_timeout=600)` uses `leaf.timeout` when set and
  the default otherwise. A `--timeout <seconds>` flag changes *the default* for the whole run;
  a leaf's own `timeout:` still wins over it, so a run-wide override never silently loosens a
  leaf that deliberately tightened its own limit. A non-integer `timeout:` is reported as an
  `error:` line on stderr with a non-zero exit, the same as any other malformed config.
- **600 seconds.** This is a "something is wrong" ceiling, not a performance budget. #11's own
  objection — that `dput` and a local build script do not share a reasonable timeout — is answered
  by the per-leaf override, not by the default. A snap upload on slow upstream can legitimately
  exceed ten minutes; that leaf sets its own `timeout:`.
- **A distinct `timed out` status**, not folded into `failed`. `subprocess.TimeoutExpired` produces:

  ```
  <path>: timed out (timed out after 600s - no output captured, the action may be waiting on stdin)
  ```

  The trailing clause is the point. `capture_output=True` is *why* an interactive prompt is
  invisible, and an operator reading a bare "timed out" has no reason to suspect stdin. This is the
  specific confusion #11 recorded ("it just looks like the command has frozen").

  **Correction, made during v11's final fix round.** "no output captured" was written before
  anyone checked, and it is not reliably true. `subprocess.TimeoutExpired` carries whatever was
  captured before the timeout — verified directly, and as undecoded `bytes` despite `text=True`.
  The flagship action, `dpkg-buildpackage && debsign && dput`, is exactly the output-then-hang
  shape where that matters most. Surfacing it is deliberately deferred, so the string above is
  still what ships; the gap is recorded as BACKLOG #15.
- **Visible before you confirm.** The dry-run plan prints each leaf's effective timeout, so the
  Step 2/3 safety gate in `SKILL.md` shows it alongside the action, requirements, and issues.
- **Exit code.** A timeout is non-zero exit, the same as a failure. The status string differs; the
  process's verdict does not.
- **Fan-out is unchanged.** A timed-out leaf does not stop its siblings, exactly as a failed one
  does not. Channels are independent; that was v7's deliberate design and it still holds.

## Testing

Everything mechanical lands in the existing suite at `skills/orc-publish/scripts/tests/`, run with
`cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`.

- **B:** `format_plan` and `execute_plan` render the new wording for an action-less leaf, and a
  leaf with an action is unaffected.
- **C:** a leaf's own `timeout:` is parsed and preferred over both the default and `--timeout`; the default applies when
  unset; a real timing-out action produces `timed out` (not `failed`) with the stdin clause in its
  detail; a timed-out leaf does not stop a following leaf; the run exits non-zero; the dry-run plan
  shows the effective timeout.

Part A is prose in two `SKILL.md` files and has no bundled script, so it is verified the way
Orclab's other prose conventions are: a `VERIFICATION.md` scenario walking a `RELEASING.md` step
that carries a `**One-time setup:**` block whose check fails, confirming the runner stops and asks
rather than running the setup.

## Global constraints

- `CLAUDE.md`'s design checklist applies. Both touched components are existing skills; no new
  component, no new frontmatter decision, no `orc`-prefix question.
- `CLAUDE.md`'s dogfooding boundary applies throughout: this is Orclab framework work only. No
  consuming project's content is written and no consuming project's real action is executed.
- BACKLOG discipline: #11 gets a resolution layered onto its existing text, never overwriting it.
  #12 gets a note recording that v8 already closed it and that this spec is not a second attempt.
