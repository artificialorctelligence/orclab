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

## Relationship to superpowers

This skill covers environment-registry discipline only — what a good entry contains and when to
write one. It doesn't replace `superpowers`' generic process skills (`superpowers:brainstorming`,
`superpowers:subagent-driven-development`, etc.), which remain available for everything outside
registering and reading back real test environments.

## What NOT to do

- Don't write speculative entries for environments that might exist someday — only real, actually-
  used ones.
- Don't compress away a gotcha's specific detail to keep the entry short — the specific failure
  mode is what makes it useful later.
- Don't put this content in a git-tracked project file — it belongs in memory.
