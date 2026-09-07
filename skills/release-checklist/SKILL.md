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

### Optional markers a step can carry

Five optional prose markers. They are read by `/orc-release` when it drives the checklist, but
they are written for a human first — someone following the document by hand wants "don't start
this if X" every bit as much as an automated runner does. **All five are optional; a document
using none of them is still complete and still driveable.**

- **Preconditions** — what must be true before the step starts, written as
  `**Preconditions:** <what must be true>`. Prefer the specific and checkable ("this version is
  not already published to the PPA") over the generic ("everything is ready").
- **Performed by hand** — `**Performed by hand.**` for a step (or part of one) a person carries
  out rather than a command: a click in a web UI, a manual install-test on real hardware, a
  visual confirmation. A step may be partly manual; say so where the manual part begins.
- **Delegation** — `**Run:** /some-command` when the step's work is done by an existing command
  rather than by literal shell commands written out here.
- **Irreversible** — `**Irreversible.**` when the step does something that cannot be undone:
  publishing to a public archive, pushing a tag, creating a release. This is what lets an
  abandoned release distinguish what can be rolled back from what merely has to be reported.
- **One-time setup** — `**One-time setup:** <what it is, and what it is scoped to — per machine,
  per account, per project>` for something done once and then never again: registering a store
  name, submitting an app for review, creating a signing key, adding a per-machine config file.
  Write it inside the step that needs it, not in a separate section of its own.

  A one-time-setup block **must state how to tell it is already in place** — a real command, or a
  real observation — held to the same standard as `**Preconditions:**` above: specific and
  checkable, not generic. Without that, a runner has nothing to test and is reduced to asking
  blind, and a reader coming back six months later can't tell whether they already did it.
  Follow the check with the setup commands themselves.

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

## Relationship to superpowers

This skill covers the release-checklist discipline only. Deciding whether a new checklist step
needs its own design pass first, or executing the work a step requires, is `superpowers`' job
(`superpowers:brainstorming`, `superpowers:subagent-driven-development`) — this skill doesn't
reimplement that cycle, it assumes it's available.

## What NOT to do

- Don't write a step you haven't actually verified works — a checklist step that silently fails
  when followed is worse than no checklist.
- Don't duplicate a step CI already fully covers without saying so — cross-reference it instead.
- Don't hardcode this project's specific target list (channels, environments) into another
  project's checklist — each project's steps come from its own real release path.
