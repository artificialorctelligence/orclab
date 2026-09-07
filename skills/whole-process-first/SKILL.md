---
name: whole-process-first
description: Use before acting on any step of a documented multi-step process (a release checklist, a runbook, a migration guide, a setup procedure) - read the whole document end to end first, and model the real shape of the work, before executing or automating any single step of it.
---

# Read the Whole Process First

When a documented process exists — a `RELEASING.md`, a runbook, a migration guide, a setup
procedure — read it completely before acting on any part of it, and before building anything that
automates a part of it.

The failure this closes off isn't getting a step wrong. It's discovering the process one step at a
time, patching each problem as it surfaces, and never seeing the shape of the whole thing. That
pattern is expensive in a specific way: every patch looks locally reasonable, so nothing triggers a
stop-and-reconsider, while the real defect (a wrong model of the work) stays invisible and keeps
generating new symptoms.

## What "the whole process" means

Not just reading every line. Model these explicitly, and write down what you find:

- **Order and gates.** Which steps must precede which? Which are hard gates (a test suite that must
  be green, a CI run that must pass) versus merely conventional ordering?
- **Preconditions and state.** What does each step assume is already true — of the working tree, of
  the remote/destination, of the machine? A step that uploads a version assumes that version isn't
  already published. A step that builds assumes the tree holds what you think it holds.
- **Steps that aren't commands.** Real processes contain human steps: a click in a web UI, a manual
  test on real hardware, a visual confirmation. These are invisible to anything that only models
  shell commands, and they are frequently the steps that can't be skipped.
- **Scope per step.** Which steps are global to the whole operation, and which are per-target,
  per-channel, per-environment? Mistaking one for the other produces a structure that can't
  represent the real work.
- **Irreversibility.** Which steps can't be undone (a publish, a push to a shared branch, a
  release)? Those set where the real gates belong.

## When automating part of a process

Read the whole process before writing the automation for any part of it, even a part that looks
self-contained. An automation designed against one step in isolation will encode that step's
assumptions and silently omit everything the surrounding steps were handling.

Two concrete signals that the model is wrong, both worth stopping for:

- **A step's automation has to smuggle in work from a neighboring step to function at all** (a
  "publish this artifact" action that has to build the artifact first). That means the boundary
  drawn is not a real boundary.
- **The process's own steps keep needing patches as you reach them.** One surprise is a surprise;
  a third patch in a row is a wrong model, and the fix is to stop and re-read, not to patch again.

## Exceptions

This is about documented multi-step processes, not about every task:

- **Genuine exploration**, where no process document exists yet and finding the shape *is* the
  work. Reading first doesn't apply when there's nothing to read.
- **A single, self-contained step** someone explicitly asks for in isolation ("just run the
  tests"), with no intent to proceed through the rest. Do that step. But if it becomes the first
  step of actually running the process, read the whole thing then.
- **Emergencies with a known, narrow fix**, where the cost of delay genuinely exceeds the cost of
  an incomplete model. Say plainly that this is what's happening, and read the rest afterward.

The exception is never "the process looks obvious from step 1," or "I'll read the next step when I
get to it."

## What NOT to do

- Don't read a process document in fragments, pulling up each section only as it becomes relevant.
- Don't build automation against one step and assume the rest will fit around it later.
- Don't treat a third consecutive patch as bad luck.
- Don't skip the parts of a process document that describe manual/human steps because they aren't
  automatable — those are exactly the parts an automated model will otherwise silently drop.
