---
name: orc-publish
description: Use when the user explicitly asks to use orc-publish, or types /orc-publish, to push a project's built artifacts to their real distribution destinations (a PPA, the Snap Store, Flathub, npm, etc.) as configured in the project's own .orclab/publish/channels.yaml and distro.yaml. Also reads back each channel's own published download/install numbers with --metrics.
allowed-tools: Bash(python3 *)
---

# orc-publish

Publishes a project's built artifacts to whatever real destinations it has configured in its own
`.orclab/publish/channels.yaml` (and, for a distro-scoped query, `.orclab/publish/distro.yaml`).
Orclab itself ships no real channel/distro content for any project — only a project that has
populated these two files can actually publish anything.

## Step 0: Confirm PyYAML is available

Run:

```
python3 -c "import yaml"
```

If this fails, tell the user plainly that `PyYAML` isn't installed (`pip install pyyaml`) and
stop.

## Step 1: Read `$ARGUMENTS` and confirm the right tree file exists

- If `$ARGUMENTS` contains `--for <path>`, this is a read-only query against the **distro** tree
  only — it never needs `channels.yaml`. Confirm `.orclab/publish/distro.yaml` exists:
  ```
  python3 -c "import pathlib,sys; sys.exit(0 if pathlib.Path('.orclab/publish/distro.yaml').exists() else 1)"
  ```
  If it doesn't, tell the user this project has no distro configuration yet and stop. Otherwise
  skip straight to running the script with `--for <path>` and report its output — nothing to
  confirm, nothing executes.
- Otherwise, confirm `.orclab/publish/channels.yaml` exists:
  ```
  python3 -c "import pathlib,sys; sys.exit(0 if pathlib.Path('.orclab/publish/channels.yaml').exists() else 1)"
  ```
  If it doesn't, tell the user this project has no publish configuration yet and stop — never
  invent one. Otherwise, the rest of `$ARGUMENTS` are selection tokens (dotted paths, optionally
  `!`-prefixed to exclude). Pass them through to the script exactly as given.

## Step 2: Always resolve in dry-run mode first

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py <selection tokens> --dry-run
```

Show the user the exact list this prints — every leaf, its real action, its `timeout:` line, and
any `requirement:`/`issue:` lines beneath it, verbatim, not paraphrased. A leaf's requirements/issues
often name something the user needs to do *before* confirming (e.g. unlocking a signing key) —
don't let those scroll by unread. This is the safety gate. **Never skip straight to execution**,
even if the request sounded confident ("just publish everything," "ship it all").

## Step 3: Get an explicit go-ahead for that specific list

Ask the user to confirm the list from Step 2. A vague "sounds good" earlier in the conversation,
about something else, doesn't count — wait for a clear yes to *this* resolved list.

## Step 4: Execute for real

Once confirmed, run the identical command without `--dry-run`:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py <same selection tokens>
```

Report the exact summary it prints, per leaf: success (with the real output, if any), failed
(with the real error text), timed out (with the real limit), or not attempted. Never paraphrase a
failure away, and never claim success for a leaf the summary doesn't confirm succeeded.

## Reading a channel's own download numbers (`--metrics`)

`--metrics` runs each selected leaf's `metrics:` command instead of its `action:`. It is a
**read**, not a publish: it reports numbers a distribution channel already publishes about
itself. **It never needs the dry-run/confirm gate above** — go straight to:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py <selection tokens> --metrics
```

Nothing is uploaded, nothing is changed, no credentials are involved. This is explicitly not
telemetry: never add tracking, analytics, or phone-home code to a project to produce these
numbers. If a channel doesn't publish a number of its own, the honest answer is that there
isn't one.

A leaf with no `metrics:` reports `(known channel, no metrics source)` — the same real,
deliberate state as an action-less leaf, not a misconfiguration.

A leaf's `prepare:` and `preflight:` apply to its `action:` only, and are skipped entirely
under `--metrics`. A metrics query publishes nothing, so there is no irreversible step to gate
— and running a project's build to answer a read-only download-count question would be wrong.
A leaf can therefore report its numbers before its artifact has ever been built.

**Relay the tool's own caveat line, don't strip it.** These counters measure fetches, and
mirrors and indexers are counted alongside people. A bare total presented as "downloads" reads
as users and will be wrong by an order of magnitude.

### What to put in a leaf's `metrics:`

`$ORC_PUBLISH_SCRIPTS` is exported to every leaf command and points at this skill's own
`scripts/` directory, so a project's `channels.yaml` can call Orclab's bundled readers without
knowing where the plugin is installed.

| Channel | `metrics:` command | Status |
|---|---|---|
| Launchpad PPA | `python3 $ORC_PUBLISH_SCRIPTS/metrics/launchpad_ppa.py <owner>/<ppa> --package <name> --series <series>` | Confirmed live 2026-09-08 |
| GitHub Releases | `gh release list -L 50 --json tagName --jq '.[].tagName' \| while read t; do gh release view "$t" --json assets --jq "\"$t: \" + ([.assets[].downloadCount] \| add // 0 \| tostring)"; done` | Confirmed live 2026-09-08 (real field, all zero for Orcshot) |
| Snap Store | `snapcraft metrics <snap-name> --format table --name weekly_installed_base_by_operating_system` | **Unverified** — see below |
| Flathub | `curl -sS https://flathub.org/api/v2/stats/<app-id>` | **Unverified** — see below |

The Snap and Flathub rows are named mechanisms, not confirmed ones: no Orclab-adjacent project
has been onboarded to either, so neither has ever been run against a real published app. Before
putting one in a real `channels.yaml`, verify it live and correct this table — do not present an
unverified command as if it worked. `orclab:currency-discipline` covers exactly this.

## Notes

- `--for <distro-path>` reporting "no channel set (known target, not yet actionable)" is normal,
  not an error — relay that exact string, don't paraphrase it.
- A selection token that doesn't resolve, or resolves ambiguously, is reported by the script as an
  `error:` line on stderr with a non-zero exit — relay that message plainly rather than guessing
  what the user meant.
- A missing or malformed `channels.yaml`/`distro.yaml` (past Step 1's existence check — e.g. bad
  YAML syntax) is reported the same way: an `error:` line on stderr. Relay it plainly.
- Every action runs under a timeout — a leaf's own `timeout:` (seconds) if it sets one, otherwise
  600 seconds. `--timeout <seconds>` changes that default for a whole run; a leaf's own value
  still wins over it. The dry-run plan prints each actionable leaf's effective timeout, so it is
  visible in the Step 2 list before you confirm anything.
- A leaf reported as `timed out` is distinct from one reported as `failed`, and the distinction is
  worth relaying exactly. Because actions run with their output captured, a command waiting on
  stdin for a passphrase produces no visible prompt at all — a timeout is often the only signal
  that something is waiting on input rather than working. One case no longer reaches a timeout at
  all: a prompt on the terminal rather than on stdin (gpg/pinentry, which is what `debsign` uses)
  now fails fast as `failed`, with its own `/dev/tty` error text, because the action runs in its
  own session with no controlling terminal. So the timeout is the signal for the *other* kinds of
  wait — relay that error text plainly when you see it rather than waiting out the limit.
- A channel leaf with no `action:` reports as `(known channel, not yet actionable)` and is never
  attempted. That is a real, deliberate state — a target the project knows about but has no
  publish mechanism for yet — not a misconfiguration to fix.
- A leaf may declare `prepare:` (a command run first), `artifact:` (the archive to inspect) and
  `preflight:` (which named rule sets apply). When it does, the order is **prepare → inspect →
  act**, and a tripped rule reports as `timed out`'s sibling status **`refused`**: the act never
  ran, because what was about to be published is wrong — though a declared `prepare:` already may
  have, real side effects a refusal doesn't undo. That is a different thing from `failed`, which
  means a command you ran returned non-zero — relay the distinction rather than flattening it.
- `artifact:` must name the **archive itself**, not a manifest that references it. Inspecting a
  `.changes` file instead of the `.tar.xz` it lists would check the wrong thing while reporting
  success.
- The rules are `no-vcs`, `no-tool-state` and `no-prebuilt-binaries`, opt-in per leaf. They cannot
  be global: a `.snap` is squashfs and legitimately contains `.so` files.
- A `preflight:` declared on an archive format the inspector cannot read is **refused**, saying the
  format is unsupported. That is deliberate — a silent pass on an uninspectable artifact is exactly
  the failure preflight exists to prevent, wearing a green tick.
- `--allow-preflight-failure` downgrades refusals to warnings for one run and still prints every
  finding. Never pass it on the user's behalf; an irreversible publish over a known-bad artifact is
  their call to make explicitly.
- A dry-run inspects the artifact if it already exists and says so if it does not. It never runs
  `prepare` — a dry run that builds is not a dry run.
