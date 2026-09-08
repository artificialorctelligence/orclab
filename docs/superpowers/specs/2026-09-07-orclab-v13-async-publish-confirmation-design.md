# Orclab v13: confirming an asynchronous publish — design

## Goal

Stop `/orc-publish` from reporting `success` for a publish that was only *accepted*, and give a
channel a way to declare how anyone finds out whether it actually landed.

Closes **BACKLOG #18**.

**On the numbering:** `v12` (artifact preflight, **#21**) and `v13` here reflect the order these
were specced on 2026-09-07, not a required implementation order. They are independent and either
can ship first; only the composition note under Testing assumes both eventually exist.

## Why this exists

`/orc-publish` reports a leaf as `success` when its action exits 0. For several real channels exit
0 means accepted, not published, and the gap is hours to days:

| Channel | What exit 0 actually means | How the real state is checkable |
|---|---|---|
| PPA upload (`dput`) | queued; Launchpad's build farm has not built it | Launchpad API — `getPublishedSources` / `getPublishedBinaries`, confirmed live 2026-09-07 |
| PPA series copy | requested; files can take up to 20 minutes to appear | same API |
| Flathub first submission | a pull request, reviewed by people over days | GitHub PR status |
| Snap Store | uploaded; some confinements need Canonical review | `snapcraft status` / the developer dashboard |
| App Store / Play | submitted for multi-day human review | App Store Connect / Play Console APIs |

**The most concrete statement of the problem**, from the `0.3.0` release: `dput` printing
`Successfully uploaded packages.` says nothing about whether the package *built*. The build farm's
result is a separate gate from the upload's success.

**It is already being worked around by hand, which is how a missing mechanism announces itself.**
Orcshot's `ppa.resolute` leaf carries this as prose: *"A green exit means the copy was accepted,
not that it has landed."* That is the same signal the `**One-time setup:**` marker came from —
invented inline, in one project, before it was a convention.

**And it cost a mistracked release.** Orcshot's step 6 was three operations with a remote wait in
the middle: build/sign/upload locally in seconds, **Launchpad's build farm taking ~28 minutes**,
then a copy valid only after that build succeeded. `/orc-release` has one completion state per
step, so `complete 6` was recorded while the copy had not happened and could not for another half
hour. The release was recorded as further along than it was.

## What already covers this, and what does not

`release-checklist`'s `**Preconditions:**` marker is the nearest existing thing, and it is not
enough on its own. `steps.py` captures the precondition as **free text**, and `/orc-release`'s
instruction is "check its preconditions, if it states any" — evaluated by judgment, never executed.
The skill already advises preferring "the specific and checkable" wording, but nothing ever runs
anything. So the *concept* of a gate exists; a mechanically checkable one does not.

## Scope

**In scope:**
- One additive leaf field, `confirm`, with optional `command` and `url`.
- A new `accepted` status for a successful publish of a leaf that declares `confirm`.
- A `--confirm` mode that checks and reports without publishing.
- Two `release-checklist` prose rules.

**Explicitly out of scope:**
- **Polling, waiting, retrying, or sleeping.** This is about *observing* an asynchronous publish.
  A retry loop against a multi-day human review would be worse than the prose note it replaces.
- **A new `/orc-release` marker.** Preconditions already exist and already permit naming a command;
  see below.
- **Whether the artifact was correct** — that is **#21** / v12. This spec answers "did it arrive,"
  not "should it have been sent."

## Design

### The `confirm` field

```yaml
noble:
  action: "… && dput ppa:artificialorctelligence/orcshot …"
  confirm:
    command: "python3 scripts/ppa-published.py --version $(dpkg-parsechangelog --show-field Version)"
    url: "https://launchpad.net/~artificialorctelligence/+archive/ubuntu/orcshot/+packages"
```

Both sub-fields are optional; at least one must be present. Like `action`, `command` is
shell-expanded, so a project derives a version the same way it already does.

**Declaring `confirm` is what marks the publish asynchronous.** There is no separate `async: true`
flag — a channel that knows how to check itself is exactly a channel whose publish does not settle
immediately, and one field cannot then disagree with the other.

A leaf with no `confirm` behaves exactly as it does today.

### `accepted`

On a publish run, a leaf that declares `confirm` and whose action exits 0 reports **`accepted`**
rather than `success`:

```
desktop.python.linux.ppa.noble: accepted (upload accepted; not yet confirmed - run --confirm, or see https://launchpad.net/~…/+packages)
```

Distinct from `success` for the same reason `timed out` is distinct from `failed`: the state is
materially different and so is what you do next. **Exit code stays 0** — nothing went wrong, the
upload genuinely succeeded, and confirming is a later, separate act. Making a healthy async publish
exit non-zero would conflate "still in flight" with "something broke" in the one signal automation
reads.

### `--confirm`

```
python3 run.py --confirm <selection tokens>
```

Resolves the selection exactly as a publish does, publishes **nothing**, runs each selected leaf's
`confirm.command`, and reports per leaf:

| Status | Meaning |
|---|---|
| `confirmed` | the command exited 0 |
| `not confirmed` | the command exited non-zero; its output is the detail |
| `needs a human` | only a `url` is declared — the URL is printed |
| `no confirm declared` | the leaf is synchronous; nothing to check |

**Exit-code semantics for `confirm.command`: 0 means confirmed, anything else means not
confirmed.** Deliberately not a three-state protocol distinguishing "not yet" from "the check
itself broke" — every project implementing `confirm` would have to honour it, and for gating
purposes both answers mean *do not advance*. Which one it was belongs in the command's own output,
which a human reads.

`--confirm` runs under the same per-leaf timeout as any other command, and continues past a leaf
that reports `not confirmed`, as `/orc-publish` does everywhere.

`--confirm` is its own mode and publishes nothing, so `--dry-run` alongside it is meaningless.
**Reject the combination with an `error:` line rather than ignoring one of the flags** — silently
dropping a flag the operator typed is how someone comes to believe a dry run happened when it
did not. `--timeout` applies normally, since a confirm command is a subprocess like any other.

### How `/orc-release` reaches it — no new marker

A step's precondition names the command, and the runner's existing "check its preconditions"
instruction already covers running it:

```markdown
## 7. Copy the built package to 26.04

**Preconditions:** the `noble` build has succeeded on Launchpad — not merely been accepted.
Check with `/orc-publish --confirm desktop.python.linux.ppa.noble`.
```

So step 6's "did it land?" and step 7's "may I start?" become **one declaration**, living on the
channel that knows how to answer it, rather than the same condition restated in two documents that
can drift apart.

A `url`-only confirm cannot be executed. `--confirm` prints the URL and reports `needs a human`;
`/orc-release` meeting such a precondition stops and asks, the same shape as a step marked
`**Performed by hand.**`.

## Two things this cannot do, stated rather than implied

- **Orclab cannot enforce that `confirm.command` is read-only.** A project can put anything there.
  The field is documented as a check and every real example is a query, but the guarantee is the
  project's, not the framework's. Anyone auditing a `channels.yaml` should read its `confirm`
  commands with that in mind.
- **A confirmed publish is confirmed *at that moment*.** Nothing is cached and nothing is watched.
  Re-running `--confirm` is how you find out again.

## `release-checklist` — two rules, no code

**1. A step that waits on external state must be two steps.** The local action is one; whatever
depends on the remote result is another, with a precondition. A single step cannot honestly
represent "the first half is done and the second half cannot start yet" — `/orc-release` has one
completion state per step, so marking it complete claims more than happened. Cite the `0.3.0`
release: upload, a 28-minute build, then a copy, all as step 6, recorded complete while the copy
was still half an hour away.

**2. Prefer a precondition that names a command over one that only describes a condition.**
"This version is not already published to the PPA" is good prose; a command that answers it is a
gate. The marker's existing advice to prefer "the specific and checkable" is extended to say what
checkable means when a check is available.

## Testing

Bundled-script tests, `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`:

- **Parsing**: `confirm` with `command` only, `url` only, both; a leaf with neither sub-field is a
  configuration error reported as an `error:` line, not silently ignored.
- **`accepted`**: a leaf declaring `confirm` reports `accepted` on a zero-exit action, exit code
  stays 0, and the detail names both the pending state and the URL when one is declared.
- **Unchanged**: a leaf without `confirm` still reports `success`.
- **`--confirm`**: publishes nothing (sentinel file the action would create must not appear); maps
  exit 0 to `confirmed` and non-zero to `not confirmed` with the real output as the detail;
  `url`-only reports `needs a human`; an undeclared leaf reports `no confirm declared`; a
  `not confirmed` leaf does not stop a following leaf.
- **Composition with v12**: a leaf declaring both `preflight` and `confirm` that is refused never
  reaches `accepted` — refusal precedes the action, so no confirmation state can exist.

A `VERIFICATION.md` scenario covers the thing unit tests cannot: that an `accepted` summary reads
to an operator as "not done yet." The word is doing the work here, and #15 already established that
substring assertions pass on output nobody can read.

## Global constraints

- No new dependency.
- Every new field and status is additive; no existing configuration changes behaviour.
- `/orc-publish` continues past an independent leaf's outcome, as it already does for `failed`,
  `timed out`, and (per v12) `refused`.
- Orclab ships the mechanism. No project's `channels.yaml` is written here; Orcshot adopting this
  is its own work, in a session centred on it.
