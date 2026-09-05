# Orclab v1: Process Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working Claude Code plugin ("Orclab") providing three behavioral skills — `backlog-discipline`, `release-checklist`, `environment-registry` — distilled from Orcshot's own proven project-discipline patterns, installable and dogfoodable in real projects.

**Architecture:** A standard single-plugin repo: `.claude-plugin/plugin.json` (plugin manifest) + `.claude-plugin/marketplace.json` (self-hosted single-plugin catalog, `"source": "./"`) at the root, three independent skill directories under `skills/`, each with a `SKILL.md` (the discipline) and a `references/` file (a worked example). No agents, no hooks, no commands in v1.

**Tech Stack:** Markdown (SKILL.md content), JSON (plugin manifests). No code, no test framework — these are natural-language instructions that shape Claude's own behavior, not executable logic. Verification is a written, runnable verification script (concrete scenarios + expected outcomes) rather than unit tests, since there is no code path to assert against.

**Spec:** `docs/superpowers/specs/2026-09-04-orclab-v1-process-core-design.md`

## Global Constraints

- Three skills only in v1: `backlog-discipline`, `release-checklist`, `environment-registry`. No CI/packaging templates, no release-automation pipeline, no `/orc-*` commands (all deferred — see `BACKLOG.md` #1 and the spec's "Out of scope" section).
- No `agents/` directory in v1. If any future Orclab version adds an agent, its `model:` frontmatter must be deliberately pinned, never left to inherit by default.
- `backlog-discipline` and `release-checklist` write to git-tracked project files (`BACKLOG.md`, `RELEASING.md`). `environment-registry` writes to Claude memory (the platform's existing `project`-type auto-memory) — never to a git-tracked file.
- `environment-registry` must never store, ask for, or type an actual password, under any circumstance.
- `BACKLOG.md` entry numbers are never reused, even after deletion. Resolving an entry appends a resolution note; it never replaces or trims the original diagnostic text.
- Every skill scaffolds its own target file (or memory entry) on first use if it doesn't already exist — no manual setup step required in a new project.

---

## File Structure

```
orclab/
  .claude-plugin/
    plugin.json
    marketplace.json
  skills/
    backlog-discipline/
      SKILL.md
      references/example-entries.md
    release-checklist/
      SKILL.md
      references/example-checklist.md
    environment-registry/
      SKILL.md
      references/example-registry.md
  README.md
  VERIFICATION.md
```

- `.claude-plugin/plugin.json` — the plugin's own identity (name, description, version, author).
- `.claude-plugin/marketplace.json` — lets `/plugin marketplace add <path>` treat this repo as an installable source, catalogsing the one plugin with `"source": "./"` (verified real pattern, matching the installed `ponytail` and `superpowers` plugins — both ship exactly this pair of files).
- Each skill directory is self-contained: `SKILL.md` states the discipline, `references/` holds one worked example adapted from Orcshot's real files. Skills don't reference each other's files.
- `README.md` — install instructions and a one-paragraph description per skill.
- `VERIFICATION.md` — the dogfood verification script from Task 5; the closest thing to a runnable check this kind of deliverable can have.

---

### Task 1: Plugin scaffold

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `README.md`
- Create: `skills/backlog-discipline/references/.gitkeep` (placeholder so the directory exists before Task 2 populates it — remove once Task 2 adds the real file)

**Interfaces:**
- Consumes: nothing (first task).
- Produces: a valid, installable plugin skeleton that Tasks 2–4 add skill content into. `plugin.json`'s `"name"` field (`"orclab"`) must match `marketplace.json`'s `plugins[0].name` field exactly — later tasks and the README's install instructions depend on this name.

- [ ] **Step 1: Write `plugin.json`**

```json
{
  "name": "orclab",
  "description": "Project-discipline skills distilled from real practice: backlog tracking, release checklists, and live-environment registries.",
  "version": "0.1.0",
  "author": {
    "name": "direflail"
  }
}
```

- [ ] **Step 2: Write `marketplace.json`**

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "orclab",
  "description": "Project-discipline skills distilled from real practice: backlog tracking, release checklists, and live-environment registries.",
  "owner": {
    "name": "direflail"
  },
  "plugins": [
    {
      "name": "orclab",
      "description": "Project-discipline skills distilled from real practice: backlog tracking, release checklists, and live-environment registries.",
      "source": "./"
    }
  ]
}
```

- [ ] **Step 3: Verify both files are valid JSON and the names match**

Run:
```bash
python3 -c "
import json
p = json.load(open('.claude-plugin/plugin.json'))
m = json.load(open('.claude-plugin/marketplace.json'))
assert p['name'] == m['plugins'][0]['name'] == 'orclab', 'name mismatch'
assert m['plugins'][0]['source'] == './', 'source must be ./'
print('OK: plugin.json and marketplace.json are valid and consistent')
"
```
Expected: `OK: plugin.json and marketplace.json are valid and consistent`

- [ ] **Step 4: Write `README.md`**

```markdown
# Orclab

Reusable project-discipline skills for Claude Code, distilled from real practice on other
projects (starting with Orcshot).

## Skills

- **backlog-discipline** — maintain a single flat `BACKLOG.md` of real, open findings, with
  permanent entry numbers and resolution history layered on top of (never replacing) the original
  diagnostic record.
- **release-checklist** — maintain a numbered, dependency-ordered `RELEASING.md`, cross-referenced
  against whatever CI already automates.
- **environment-registry** — register real, live test environments (VMs, containers, staging
  servers, devices) as Claude memory, never as a git-tracked file, never storing credentials.

## Installing

Register this directory as a local plugin marketplace, then install the plugin:

    /plugin marketplace add ~/projects/orclab
    /plugin install orclab@orclab

## Status

v1 — process core. See `docs/superpowers/specs/` for the design history and `BACKLOG.md` for
what's deliberately deferred (a `/orc-*` command layer is tracked as #1).
```

- [ ] **Step 5: Create skill directory skeletons**

```bash
mkdir -p skills/backlog-discipline/references
mkdir -p skills/release-checklist/references
mkdir -p skills/environment-registry/references
touch skills/backlog-discipline/references/.gitkeep
touch skills/release-checklist/references/.gitkeep
touch skills/environment-registry/references/.gitkeep
```

- [ ] **Step 6: Commit**

```bash
git add .claude-plugin README.md skills
git commit -m "Scaffold Orclab plugin: manifest, marketplace catalog, skill directories"
```

---

### Task 2: `backlog-discipline` skill

**Files:**
- Create: `skills/backlog-discipline/SKILL.md`
- Create: `skills/backlog-discipline/references/example-entries.md`
- Delete: `skills/backlog-discipline/references/.gitkeep`

**Interfaces:**
- Consumes: the directory skeleton from Task 1.
- Produces: a complete, independently-reviewable skill. No other task depends on this skill's internal content — Tasks 3 and 4 are structurally identical but independent.

- [ ] **Step 1: Write `skills/backlog-discipline/SKILL.md`**

```markdown
---
name: backlog-discipline
description: Use when a real finding, gap, or deferred decision surfaces that won't be fixed right now but is worth tracking — or when resolving, updating, or considering deletion of an existing BACKLOG.md entry. Maintains a single flat BACKLOG.md with permanent, non-reused entry numbers and layered (not overwritten) resolution history.
---

# Backlog Discipline

`BACKLOG.md` is a single flat file tracking real, open findings — not a task tracker, not a
wishlist. Each entry keeps the reasoning that led to it, not just a one-line title, so picking it
up later never requires re-deriving the "why" from scratch.

## When to add an entry

Add an entry when something real is found that:
- has a genuine consequence (not a hypothetical one), and
- isn't being fixed right now.

Don't add an entry for a task you're about to do in this same session — that's just work, not
backlog. Don't add an entry for speculative future-proofing with no concrete trigger.

## If `BACKLOG.md` doesn't exist yet

Create it first, with this exact header:

```markdown
# Backlog

Open items not yet scheduled into a task. Each entry keeps the context that
led to it - not just "what," but "why this matters" - so picking it up later
doesn't require re-deriving the reasoning from scratch.
```

Then add the first entry below it, numbered `#1`.

## Numbering

Scan the file for every `## #N:` heading and take the highest `N` seen. The new entry is `N + 1`.
Numbers are never reused (see Deletion below), so scanning the current file is always sufficient
— there's no need to consult git history for numbers that no longer appear.

## Writing a new entry

```markdown
## #<N>: <short, specific title describing the real problem>

<Context: what was found, when/how, and why. State the real, concrete consequence explicitly —
not "this could theoretically cause X" but the actual thing that happens. If discovered during a
specific piece of work, name it, so a future reader knows the circumstances.>

<If the finding has a clear scope boundary — what it does NOT affect — say so explicitly, the
same way you'd state what it does affect. This prevents both under- and over-reacting to the
entry later.>
```

Keep it a real paragraph or few, not a checklist stub. The entry should let someone with zero
memory of this conversation understand the problem and its stakes.

## Resolving an entry

**Never delete or rewrite the original diagnostic text.** Append to it instead:

1. Add `(RESOLVED YYYY-MM-DD)` to the end of the entry's title line.
2. Add a new paragraph below the original text, starting with something like "**Resolved for
   real, not just tracked**:" or "**Resolved**:", explaining what actually fixed it and how you
   know (what was verified, not just what was changed).

The original entry stays intact above the resolution note. A reader should be able to see both
the original problem *and* how it was actually closed out, in one place.

## Deleting an entry

Delete an entry outright — not "mark resolved," not archive it — only when the entry's owner
(ask, don't assume) explicitly judges it no longer worth tracking: e.g. the scenario it describes
can no longer affect any real user, or it was superseded by a different entry.

When deleting: remove the entire `## #N: ...` section. **Do not renumber any other entry, and do
not reuse `N` for a future entry.** A gap in the numbering (e.g. #187, #189, with no #188) is
expected and correct — it's a real signal that something was found and explicitly judged not
worth tracking, not a bug in the file.

## What NOT to do

- Don't turn this into a general task list — it's for findings, not routine planned work.
- Don't silently delete an entry because it looks stale to you — surface the judgment call.
- Don't compress or summarize an old entry's context to save space — the context is the point.
```

- [ ] **Step 2: Write `skills/backlog-discipline/references/example-entries.md`**

```markdown
# Worked example: BACKLOG.md entries

Real, lightly-genericized entries adapted from Orcshot's own BACKLOG.md, showing the three states
an entry goes through.

## Open entry (not yet fixed)

## #142: Snap channel has no working audio feedback on capture

Found while adding Snap packaging (2026-08-30): the Snap manifest never granted access to any
audio-sink interface, so `capture_feedback.py`'s shutter-sound playback silently fails under
strict confinement — `play_capture_sound()` throws, caught by an existing broad exception handler
that was written for a different failure mode entirely, so capture itself still succeeds; only
the sound is missing. Confirmed live: a real strict-confinement build produces no audible sound
on capture, with no error surfaced anywhere the user would see it.

Not blocking the Snap channel's initial ship (silent capture already works, sound was always
best-effort) but a real, user-visible gap once anyone notices it's missing.

## Resolved entry (append, don't overwrite)

## #142: Snap channel has no working audio feedback on capture (RESOLVED 2026-09-01)

Found while adding Snap packaging (2026-08-30): the Snap manifest never granted access to any
audio-sink interface, so `capture_feedback.py`'s shutter-sound playback silently fails under
strict confinement — `play_capture_sound()` throws, caught by an existing broad exception handler
that was written for a different failure mode entirely, so capture itself still succeeds; only
the sound is missing. Confirmed live: a real strict-confinement build produces no audible sound
on capture, with no error surfaced anywhere the user would see it.

Not blocking the Snap channel's initial ship (silent capture already works, sound was always
best-effort) but a real, user-visible gap once anyone notices it's missing.

**Resolved for real, not just tracked**: added the `audio-playback` plug to `snapcraft.yaml` and
connected it in the manifest's default-connections. Verified live: real audible playback confirmed
on a real strict-confinement build, not just "the plug exists now."

## Deleted entry (not "marked resolved" — gone, number never reused)

Entry #96 existed, describing a migration-path concern for users upgrading from a version that,
it later turned out, was never actually published anywhere. Once that was confirmed (zero real
download counts on every channel), the entry's owner judged it couldn't affect any real user and
deleted it outright. The file simply jumps from `## #95: ...` to `## #97: ...` — that gap is the
correct, permanent record that #96 was considered and explicitly dropped, not lost track of.
```

- [ ] **Step 3: Remove the placeholder and verify frontmatter parses**

```bash
rm skills/backlog-discipline/references/.gitkeep
python3 -c "
import re
text = open('skills/backlog-discipline/SKILL.md').read()
m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
assert m, 'no frontmatter block found'
assert 'name: backlog-discipline' in m.group(1)
assert 'description:' in m.group(1)
assert 'model:' not in m.group(1), 'skills must not declare a model field'
print('OK: backlog-discipline SKILL.md frontmatter is valid')
"
```
Expected: `OK: backlog-discipline SKILL.md frontmatter is valid`

- [ ] **Step 4: Self-review against the spec's rules**

Confirm each of these is explicitly present in the SKILL.md just written (all should be yes):
- [ ] States the file is scaffolded with the exact standard header if missing
- [ ] States numbering is `max(N) + 1`, scanned from the file itself
- [ ] States numbers are never reused, even after deletion
- [ ] States resolution appends a note rather than replacing/trimming original text
- [ ] States deletion requires the owner's explicit judgment call, not a unilateral decision
- [ ] States deleted numbers leave a permanent gap, not a renumbering

- [ ] **Step 5: Commit**

```bash
git add skills/backlog-discipline
git commit -m "Add backlog-discipline skill"
```

---

### Task 3: `release-checklist` skill

**Files:**
- Create: `skills/release-checklist/SKILL.md`
- Create: `skills/release-checklist/references/example-checklist.md`
- Delete: `skills/release-checklist/references/.gitkeep`

**Interfaces:**
- Consumes: the directory skeleton from Task 1.
- Produces: a complete, independently-reviewable skill, structurally parallel to Task 2 but with no shared content.

- [ ] **Step 1: Write `skills/release-checklist/SKILL.md`**

```markdown
---
name: release-checklist
description: Use when setting up a release/publish process for a new project, or when a new release step is learned (e.g. a new required check) and an existing RELEASING.md needs updating. Maintains a numbered, dependency-ordered checklist mixing manual judgment calls with copy-pasteable commands, cross-referenced against whatever CI already automates.
---

# Release Checklist Discipline

`RELEASING.md` is the numbered, dependency-ordered path from "code is done" to "a real release
exists." It exists so cutting a release is never a from-memory process, and so nothing that CI
already guarantees gets silently re-invented or silently skipped.

## If `RELEASING.md` doesn't exist yet

Create it with a title and one-sentence purpose statement, e.g.:

```markdown
# Cutting a <project> release

A checklist for going from "code on `main`" to a tagged, installable, discoverable release.
```

Then add steps as described below.

## Structuring steps

Steps are numbered in **real dependency order** — the order they must actually happen in, not the
order they were thought of. Renumber existing steps if a new one needs to be inserted in the
middle; don't append everything to the end regardless of where it actually belongs.

Each step is a `## N. <short imperative title>` heading, followed by:
- **Why this step exists**, if it's not obvious — especially if it was added because of a real
  past gap (name the gap and when it was found; that context is what stops the step from being
  quietly deleted later by someone who doesn't know why it's there).
- **Exact, copy-pasteable commands** for anything mechanical. Never describe a command in prose
  when the literal command can be given instead.
- **What "done" looks like** for anything requiring judgment (e.g. "must be fully green," "zero
  errors, warnings reviewed individually").

## Cross-referencing CI

If a step (or part of one) already runs automatically in CI, say so explicitly in that step, e.g.:

> This step, and the build+lint steps below, now also run automatically on every push and PR via
> `.github/workflows/<file>.yml` — running them by hand here is still the fastest local feedback
> loop, not a redundant step; see the final "confirm CI is green" step for cross-checking CI's own
> view before release.

This prevents two failure modes: someone skipping a step because "CI does it" when CI actually
only covers part of it, and someone assuming a step needs redoing by hand every time when CI
already guarantees it.

## Generalizing beyond one project type

The same shape applies regardless of what's being released — a packaged desktop app, a web app
deploy, a library publish. The steps differ; the shape (version bump → tests → security check →
build → [lint/verify] → tag/publish → post-release verification across every real target) doesn't.
Don't assume packaging-specific steps (e.g. `dpkg-buildpackage`) belong in a project that isn't
doing that kind of packaging — write the steps this project actually needs, in this project's own
real dependency order.

## Updating an existing checklist

When a new step is learned (usually: a real gap was found during an actual release), insert it in
correct dependency order, renumbering subsequent steps, and note briefly why it was added (which
release, what gap) the same way this skill's own security-check example above does — so a future
reader understands why the step exists, not just that it does.

## What NOT to do

- Don't write a step you haven't actually verified works — a checklist step that silently fails
  when followed is worse than no checklist.
- Don't duplicate a step CI already fully covers without saying so — cross-reference it instead.
- Don't hardcode this project's specific target list (channels, environments) into another
  project's checklist — each project's steps come from its own real release path.
```

- [ ] **Step 2: Write `skills/release-checklist/references/example-checklist.md`**

```markdown
# Worked example: a RELEASING.md excerpt

Adapted from a real project's release checklist, showing the pattern: numbered steps in
dependency order, commands given exactly, judgment calls stated plainly, and CI cross-referenced
rather than silently duplicated.

## 1. Pick a version

Decide the new version number (semver: `MAJOR.MINOR.PATCH`). Update it everywhere the project
records its own version — if there's more than one place, list them explicitly and note that they
must match, since a mismatch here is a real, silent failure mode later.

## 2. Full test suite

    pytest tests/ -q

Must be fully green before continuing. This step, and the build/lint steps below, now also run
automatically on every push and PR via `.github/workflows/ci.yml` — running them by hand here is
still the fastest local feedback loop, not a redundant step; see the final step for cross-checking
CI's own view before release.

## 3. Security check

Added after a real gap: an early release shipped without ever running a dependency/SAST scan.

    semgrep ci

Any new high/critical finding gets understood before continuing — not silently waved through, but
not automatically a blocker either; a finding can turn out to be a confirmed false positive.

## 4. Build

    <the project's real build command>

## 5. Tag and publish

    git tag vX.Y.Z && git push --tags
    <publish command for this project's real target(s)>

## 6. Confirm CI's own view

Check the CI dashboard for the tagged commit — a clean local run and a clean CI run are both
required; CI can catch environment differences a local run won't.
```

- [ ] **Step 3: Remove the placeholder and verify frontmatter parses**

```bash
rm skills/release-checklist/references/.gitkeep
python3 -c "
import re
text = open('skills/release-checklist/SKILL.md').read()
m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
assert m, 'no frontmatter block found'
assert 'name: release-checklist' in m.group(1)
assert 'description:' in m.group(1)
assert 'model:' not in m.group(1), 'skills must not declare a model field'
print('OK: release-checklist SKILL.md frontmatter is valid')
"
```
Expected: `OK: release-checklist SKILL.md frontmatter is valid`

- [ ] **Step 4: Self-review against the spec's rules**

Confirm each of these is explicitly present in the SKILL.md just written:
- [ ] States scaffolding behavior for a missing `RELEASING.md`
- [ ] States steps are ordered by real dependency, not by order thought of
- [ ] States each step mixes judgment calls with exact copy-pasteable commands
- [ ] States CI-covered steps must be cross-referenced, not silently duplicated
- [ ] States the pattern generalizes beyond packaging-specific projects

- [ ] **Step 5: Commit**

```bash
git add skills/release-checklist
git commit -m "Add release-checklist skill"
```

---

### Task 4: `environment-registry` skill

**Files:**
- Create: `skills/environment-registry/SKILL.md`
- Create: `skills/environment-registry/references/example-registry.md`
- Delete: `skills/environment-registry/references/.gitkeep`

**Interfaces:**
- Consumes: the directory skeleton from Task 1.
- Produces: a complete, independently-reviewable skill, structurally parallel to Tasks 2–3 but with no shared content.

- [ ] **Step 1: Write `skills/environment-registry/SKILL.md`**

```markdown
---
name: environment-registry
description: Use when a real, live test environment (a VM, container, staging server, physical device) is accessed or its access details/gotchas are learned, and would otherwise need re-deriving in a future session. Writes a project-type memory registering the environment, never storing credentials, generalized beyond any one environment kind.
---

# Environment Registry Discipline

Real test environments (VirtualBox VMs, staging servers, containers, physical devices) come with
access details and gotchas that are expensive to re-derive every session. This skill captures
them once, as a Claude memory file — not a git-tracked project file — so they survive across
sessions without leaking dev-machine-specific or credential-adjacent detail into a shared repo.

## Why memory, not a repo file

Environment specifics (VM identifiers, local network setup, SSH configs) are properties of *this
developer's machine*, not of the project's source. They don't belong in git next to
`BACKLOG.md`/`RELEASING.md`. Use the platform's `project`-type memory for this — the mechanism
already exists; this skill is about what a *good* entry contains and when to write one.

## When to write or update an entry

- The first time a real environment is actually used for this project (not "might be used
  someday" — actually reached, actually driven).
- Whenever something costs real debugging time to discover about driving it (a timing quirk, a
  focus-stealing bug, an unreliable clipboard, a naming gotcha) — write it down immediately, in
  the moment it's found, not from memory afterward.
- When the roster of available environments changes (one added, one decommissioned).

## What a good entry contains

- **Real inventory**: what environments actually exist right now, checked live (e.g. re-run the
  listing command — `VBoxManage list vms`, `kubectl config get-contexts`, whatever applies —
  rather than trusting what was true last time this was written).
- **Access method**: exactly how to reach each one (SSH command with the real port/key, a
  `kubectl` context name, a URL) — copy-pasteable, not described in prose.
- **Credentials policy**, stated explicitly (see below).
- **Known gotchas**, each with enough detail to actually avoid repeating the mistake — what went
  wrong, what actually fixed it, confirmed how.

## Credentials policy — non-negotiable

**Never store, ask for, or type an actual password**, in this memory file or anywhere else. Every
environment should be reachable via a key, token, or a passwordless-privilege grant already set
up on that environment. If an action genuinely requires a live password (unlocking a screen,
first-time sudo setup on an account with no grant yet):
1. Get to the exact point the password is needed.
2. Say plainly that the prompt is up, on which specific environment (if more than one could be in
   play, name it explicitly — don't assume it's obvious).
3. Ask the human to type it directly into that environment's own interface — never into chat,
   never taken over on their behalf.
4. Wait for confirmation before continuing.

This applies even to throwaway local dev environments with no real stakes — the boundary is the
mechanism, not the perceived risk of the specific credential.

## Re-verifying the roster

At the start of any session that will use a registered environment, re-check that the inventory
is still accurate (the live listing command, not the memory file's cached description) before
relying on it. A memory file doesn't update itself if an environment was added or removed since it
was last written.

## What NOT to do

- Don't write speculative entries for environments that might exist someday — only real, actually-
  used ones.
- Don't compress away a gotcha's specific detail to keep the entry short — the specific failure
  mode is what makes it useful later.
- Don't put this content in a git-tracked project file — it belongs in memory.
```

- [ ] **Step 2: Write `skills/environment-registry/references/example-registry.md`**

```markdown
# Worked example: an environment-registry memory

Adapted and generalized from a real project's VM-registry memory, showing the pattern applied to
VirtualBox VMs — the same shape applies to containers, staging servers, or physical devices.

Real environments on this host, checked live via `VBoxManage list vms`:

    "staging-vm"    {5d9651d9-...}
    "test-vm-A"     {e4fe8e9f-...}

## Credentials policy

Never store, ask for, or type an actual password. Every account below is reached via SSH key;
passwordless sudo is set up for the accounts listed. If a task ever needs an account without this,
sudo needs the human to type their own password live into that environment's own window — never
asked for in chat, never typed on their behalf, never recorded here.

## test-vm-A — SSH access

    ssh -i ~/.ssh/dev_vm_key -p 2222 devuser@localhost

## Known gotchas (cost real debugging time — read before repeating the mistake)

- **Clipboard between host and guest is unreliable.** Confirmed live; a Guest-Additions version
  mismatch was found and fixed but didn't resolve it — root cause is a known VirtualBox limitation
  on this guest OS. Don't rely on paste for getting content into the VM; type directly or drive
  input programmatically instead.
- **GUI focus silently drifts back to the host client between actions.** Always confirm the target
  window is focused immediately before typing or clicking — a real, observed failure mode where
  commands landed nowhere until this check was added.
```

- [ ] **Step 3: Remove the placeholder and verify frontmatter parses**

```bash
rm skills/environment-registry/references/.gitkeep
python3 -c "
import re
text = open('skills/environment-registry/SKILL.md').read()
m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
assert m, 'no frontmatter block found'
assert 'name: environment-registry' in m.group(1)
assert 'description:' in m.group(1)
assert 'model:' not in m.group(1), 'skills must not declare a model field'
print('OK: environment-registry SKILL.md frontmatter is valid')
"
```
Expected: `OK: environment-registry SKILL.md frontmatter is valid`

- [ ] **Step 4: Self-review against the spec's rules**

Confirm each of these is explicitly present in the SKILL.md just written:
- [ ] States this writes to memory, not a git-tracked file, and why
- [ ] States the non-negotiable credentials policy (never store/ask/type a password)
- [ ] States the roster must be re-verified live at session start, not trusted from the file
- [ ] Generalizes beyond VirtualBox specifically (containers/staging/devices mentioned)

- [ ] **Step 5: Commit**

```bash
git add skills/environment-registry
git commit -m "Add environment-registry skill"
```

---

### Task 5: Local install and dogfood verification

**Files:**
- Create: `VERIFICATION.md`

**Interfaces:**
- Consumes: the complete plugin from Tasks 1–4.
- Produces: a registered local marketplace/plugin installation, plus a written, runnable verification script. This is the closest equivalent to an automated test this deliverable can have — there is no code path to assert against, only Claude's own behavior when following the skills, which requires a live session to actually exercise.

- [ ] **Step 1: Register the local marketplace and install the plugin**

```bash
# Run inside a Claude Code session (slash commands, not shell):
/plugin marketplace add ~/projects/orclab
/plugin install orclab@orclab
```

Expected: Claude Code confirms the marketplace was added and the plugin installed. Note for
whoever runs this: **a new Claude Code session is required after installing for the skills to
appear in that session's available-skills listing** — this cannot be verified from within the
same session that ran the install command.

- [ ] **Step 2: Write `VERIFICATION.md`**

```markdown
# Orclab v1 verification script

Run these three scenarios in a **fresh Claude Code session, in the Orcshot project directory**
(`~/projects/orcshot`), after installing Orclab per `README.md`. Orcshot already has a real
`BACKLOG.md` and (once the second scenario is run) a real `RELEASING.md` in exactly the shape
these skills model from, making it a better verification target than a throwaway project.

## Scenario 1: backlog-discipline

1. Note the highest `#N` currently in Orcshot's `BACKLOG.md`.
2. Ask Claude to investigate something small and genuinely inconclusive (or describe a real,
   deliberately-deferred finding) and confirm it gets logged to the backlog.
3. **Expected:** a new `## #<N+1>: ...` entry is added, with a real paragraph of context (not a
   one-line stub), and the file's existing entries are untouched.
4. Ask Claude to resolve that same entry, describing a plausible fix.
5. **Expected:** the title gains a `(RESOLVED YYYY-MM-DD)` suffix, a new paragraph is appended
   below the original text, and the original paragraph is still present, word-for-word.
6. Ask Claude to delete the entry, stating explicitly that it's no longer worth tracking.
7. **Expected:** the `## #<N+1>: ...` section is removed entirely; no other entry is renumbered;
   the number `<N+1>` is confirmed as never appearing again in any later entry added during this
   verification pass.

## Scenario 2: release-checklist

1. Confirm Orcshot already has a `RELEASING.md`. Ask Claude to add a new step to it (e.g. a
   fictional "check translation completeness" step) and specify roughly where it belongs in the
   dependency order.
2. **Expected:** the new step is inserted in the correct position (not appended to the end
   regardless of order), existing steps are renumbered correctly, and the new step includes both
   an exact command (if applicable) and a stated "why this exists" if the reason isn't obvious.
3. Revert this change afterward (`git checkout -- RELEASING.md`) — it's a verification probe, not
   a real change to keep.

## Scenario 3: environment-registry

1. Ask Claude, in the Orcshot project, about a real environment it already has registered (e.g.
   the Ubuntu 26.04 VM) and confirm it re-verifies the live roster (e.g. re-running a listing
   command) rather than only reciting the stored memory content.
2. Describe a new, fictional environment gotcha for verification purposes and ask Claude to
   register it.
3. **Expected:** the gotcha is written to a memory file (`project` type), not to any git-tracked
   file in the Orcshot repo — confirm with `git status` in Orcshot that nothing changed there.
4. **Expected throughout:** at no point does Claude ask for, display, or type an actual password
   — if any step would require one, it should stop and describe the prompt instead.

## Recording the result

Note the outcome of each scenario (pass/fail, with specifics) either back in this conversation or
as a new `BACKLOG.md` entry in Orclab itself if something needs fixing before v1 is considered
done.
```

- [ ] **Step 3: Commit**

```bash
git add VERIFICATION.md
git commit -m "Add local install instructions and v1 dogfood verification script"
```

- [ ] **Step 4: Report installation status and hand off verification**

Since Scenarios 1–3 require a fresh Claude Code session to actually exercise the newly-installed
skills, this step is a handoff, not something the current session can complete on its own: tell
direflail that Orclab v1 is installed locally and ready, and that `VERIFICATION.md` is the script
to run in a new session against Orcshot to confirm it actually works before calling v1 done.

---

## Self-Review Notes (from writing this plan)

- **Spec coverage:** all three skills covered (Tasks 2–4), plugin scaffold covered (Task 1),
  validation-by-dogfooding covered (Task 5), model-pinning standing requirement stated in Global
  Constraints (nothing to implement now — no agents exist yet). Out-of-scope items (CI templates,
  release-automation, `/orc-*` commands) are correctly absent from this plan — they belong to
  future specs.
- **Placeholder scan:** no TBD/TODO; every code/content block is complete, not a stub.
- **Type/name consistency:** `plugin.json`'s `"name"` (`"orclab"`) matches `marketplace.json`'s
  `plugins[0].name` and the README's install command (`orclab@orclab`) throughout. Each skill's
  frontmatter `name:` matches its directory name (`backlog-discipline`, `release-checklist`,
  `environment-registry`) consistently across Tasks 2–4 and the verification script.
