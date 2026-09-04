# Orclab v1: process core — design

## Goal

Distill the project-discipline patterns proven out in Orcshot (`~/projects/orcshot`) into a
reusable Claude Code plugin — "Orclab" (working name, pending anything better) — so future
projects, Orcshot included, get them without re-deriving or copy-pasting by hand.

direflail's own framing (2026-09-04, right after Orcshot's Flathub-readiness work merged): take
"what we've learned in this project" and turn it into "a more formalized framework or plugin" for
reuse across future projects, not just Orcshot.

## Scope

This spec covers **v1 only**: the process core. It is deliberately narrow — three skills plus the
plugin scaffolding to hold them.

**In scope now:**
- A Claude Code plugin, `.claude-plugin/plugin.json` + `skills/`, matching the standard plugin
  layout (verified live against the installed `superpowers` plugin, not assumed).
- Three skills: `backlog-discipline`, `release-checklist`, `environment-registry` — each with a
  `references/` subfolder holding a worked example adapted from Orcshot's own real files.
- A standing requirement that any agent Orclab ever defines has its model deliberately pinned via
  the agent definition's `model:` frontmatter field, never left to inherit by default.
- Validation by dogfooding: installing Orclab into Orcshot itself and using it for real, since
  Orcshot already has all three file types in exactly the shape being modeled from.

**Explicitly out of scope for v1, but not designed against:**
- CI/packaging workflow templates (the cross-channel apt/Snap/Flatpak build+verify pipeline
  structure) — a distinct, more concrete, more platform-specific sub-project (Orclab v2), to be
  spec'd once v1 exists to hang it on.
- The release-automation pipeline research (dput+GPG for the PPA, `snapcraft push` for the Snap
  Store, Flathub's git-push-triggered Buildbot model) — Orclab v3, same reasoning. This research
  was reported to direflail in a 2026-09-04 conversation but not yet written down anywhere
  permanent; it should be re-derived or re-requested when v3 is spec'd, not assumed still fresh.
- Standing personal/project feedback rules (e.g. "show the real final artifact before shipping",
  "root cause not band-aid") — these are already captured by the platform's built-in auto-memory
  system (feedback/project/user/reference types), which Orcshot used well but did not build.
  Nothing new needs building here.

## Repository

New standalone repo at `~/projects/orclab`, `git init`'d with a `main` branch, no GitHub remote
yet (direflail's own call — created/pushed later, not automated here). Orcshot is a future
*consumer* of this plugin, not its home; nothing in Orclab's design assumes Orcshot-specific paths
or content beyond the worked examples in `references/`.

## Plugin structure

```
orclab/
  .claude-plugin/
    plugin.json
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
```

No `agents/` directory in v1 — none of the three skills need to dispatch to a subagent (they are
behavioral: shape how Claude writes to a file or memory, not standalone tasks worth isolating).
If a future version of any skill needs one (e.g. a checklist-review step), that agent's `model:`
gets pinned deliberately when it's defined — see "Standing requirement" below — not scaffolded
speculatively now.

`plugin.json` fields mirror the verified real example (`superpowers`'s own manifest): `name`,
`description`, `version`, `author`, `repository`, `license`. No dependency-declaration mechanism
exists for plugins today (not found in the installed plugin's manifest, and not documented
anywhere checked during this design) — so Orclab does not hard-depend on superpowers being
installed. Instead, each skill's own text says explicitly that it assumes superpowers' generic
process skills for anything it doesn't itself cover (see "Relationship to superpowers" below).

## Standing requirement: model pinning for any agent Orclab defines

Confirmed live (2026-09-04): agents (`agents/*.md`, either project-local or inside a plugin)
support a `model:` frontmatter field pinning that agent to a specific model — real example,
`code-simplifier` pins `model: opus`. Skills (`SKILL.md`) have no such field anywhere across every
plugin checked, which is architecturally correct: a skill loads instructions into the *current*
session, it doesn't spawn a separate model invocation.

Applied to Orclab: no agents exist in v1, so there is nothing to audit yet. The requirement is
forward-looking — the day any Orclab skill's design calls for dispatching to an agent, that
agent's model is chosen and pinned as part of defining it, not left to default/inherit.

## The three skills

### `backlog-discipline` — git-tracked project file (`BACKLOG.md`)

Adapted from Orcshot's own `BACKLOG.md` (764 lines, ~195 entries at time of writing), a single
flat file tracking open findings with the reasoning that led to them, not just a task title.

**Triggers:** a real finding worth tracking is surfaced but not fixed right now — a genuine gap,
a deferred decision, an open question with a real (not hypothetical) consequence.

**Rules:**
- One `## #N: title` entry per finding. `N` is monotonically increasing across the file's history
  and is **never reused**, even for a deleted entry — Orcshot's own #188 was deleted outright and
  no later entry has claimed #188 again. The skill determines the next `N` by scanning existing
  entries for the current maximum, not by counting remaining entries.
- An entry keeps its original diagnostic context — what was found and why it matters, with real
  consequences spelled out, not just a one-line task description.
- Resolving an entry **appends** a resolution note (e.g. a `(RESOLVED YYYY-MM-DD)` suffix on the
  title plus a paragraph explaining what actually fixed it) — it never replaces or trims the
  original diagnostic record. The "why this mattered" stays legible after the fix.
- An entry is deleted outright — not left "marked resolved," not archived — only when direflail
  (or, in a future project, whoever owns the backlog) explicitly judges it no longer worth
  tracking. The skill surfaces this judgment call; it never deletes unilaterally.

**Scaffolding:** if `BACKLOG.md` doesn't exist when the skill would write its first entry, it
creates the file with the standard header (see `references/example-entries.md`) before adding the
entry.

### `release-checklist` — git-tracked project file (`RELEASING.md`)

Adapted from Orcshot's own `RELEASING.md`, a numbered, dependency-ordered checklist for cutting a
release, mixing manual judgment calls with copy-pasteable commands.

**Triggers:** setting up a release process for a new project, or updating an existing checklist
when a new step is learned (e.g. a security-scan step added after a real gap was found).

**Rules:**
- Steps are numbered and ordered by real dependency (e.g. "pick a version" before "build," "build"
  before "lint the build output"), not by arbitrary convenience.
- Each step mixes prose judgment calls (what to decide, what "done" looks like) with exact,
  copy-pasteable commands where the step is mechanical.
- Any step already automated in CI gets an explicit cross-reference to the workflow file that
  covers it (e.g. "this also runs automatically via `.github/workflows/apt.yml`"), so the
  checklist never silently duplicates a guarantee CI already provides, and a reader always knows
  whether running a step by hand is the fast feedback loop or the only feedback loop.
- The pattern generalizes past Linux packaging: a web app's deploy checklist or a library's
  publish checklist follows the same shape (version bump → tests → security check → build → tag →
  publish → verify) even though none of Orcshot's own packaging-specific steps apply.

**Scaffolding:** if `RELEASING.md` doesn't exist when the skill would add its first step, it
creates the file with a minimal skeleton (see `references/example-checklist.md`).

### `environment-registry` — Claude memory, not a git-tracked file

Adapted from Orcshot's own `project_orcshot_vm_access.md` memory file, but generalized: the
pattern is about registering any real, live test environment, not specifically VirtualBox VMs.

**Why memory, not a repo file:** environment access details (VM identifiers, local SSH configs,
host-specific network setup) are dev-machine-specific and don't belong in a shared, git-tracked
repo the way `BACKLOG.md`/`RELEASING.md` do. This maps directly onto the platform's existing
`project`-type auto-memory (already available, not something Orclab builds) — so this skill's job
is teaching the discipline of what a good environment-registry memory contains and when to write
one, not building new storage.

**Rules:**
- Register real, live test environments — VMs, containers, staging servers, physical devices,
  whatever the project actually uses — as a memory file: what exists, how to reach it (SSH key,
  kubectl context, whatever applies), the credentials policy for it, and known gotchas specific to
  driving it (GUI-automation focus quirks, clipboard unreliability, timing issues — anything that
  cost real debugging time once and would cost it again if re-derived).
- **Never store, ask for, or type an actual password.** Every credential path should resolve to a
  key, token, or passwordless-sudo grant; if an action genuinely needs a live password, the skill's
  job is to surface the prompt plainly and hand off to the human — never type it, never ask for it
  in chat, never record it.
- Re-verify the roster of real environments at the start of any session that needs one, rather
  than trusting a memory file that may have gone stale (a VM roster changes; a memory file doesn't
  update itself).

**Scaffolding:** none in the git sense — the skill's "scaffolding" is simply writing the first
memory entry for a project the first time a real environment is registered, per the platform's
existing memory-write mechanism.

## Relationship to superpowers

Orclab does not reimplement the brainstorm → spec → plan → build → verify → merge cycle —
`superpowers:brainstorming`, `superpowers:writing-plans`, and `superpowers:subagent-driven-
development` already cover that generically, for any kind of software project, not just packaged
Linux apps. Orclab's three skills are the domain discipline that sits *alongside* that cycle: a
finding surfaced mid-review becomes a `backlog-discipline` entry; cutting a release follows
`release-checklist`, whose own non-trivial steps may themselves trigger a fresh round of
brainstorming.

No plugin-level dependency is declared (no such mechanism exists to declare it), so each skill's
own text states this relationship explicitly, so a Claude reading it in a project without
superpowers installed knows the gap is real, rather than a skill silently assuming or reinventing
a process it doesn't actually own.

## Validation

Since this is behavioral — shaping how Claude writes to files and memory, not code with unit tests
— validation is dogfooding: install Orclab into Orcshot itself once v1 is built, and drive each
skill through a real scenario there, confirming:
- `backlog-discipline` picks the correct next `N`, appends rather than replaces on resolution, and
  only deletes on an explicit call.
- `release-checklist` cross-references CI steps correctly against Orcshot's real
  `.github/workflows/*.yml` files.
- `environment-registry` lands in memory, not in a git-tracked file, and never records a password.

Orcshot already has all three file types in exactly the shape this design is modeled from, making
it a strictly better validation target than a throwaway test project would be.

## Out of scope, deferred to future specs

- **Orclab v2** — CI/packaging workflow templates, extracted from the real cross-channel
  apt/Snap/Flatpak build+verify pipeline (see Orcshot's own
  `docs/superpowers/specs/2026-08-29-cross-channel-build-pipeline-design.md` and its three
  `docs/superpowers/plans/*-channel.md` companions for the proven pattern this will draw from).
- **Orclab v3** — the release-automation pipeline (PPA `dput`+GPG, Snap Store `snapcraft push`,
  Flathub's Buildbot model), per direflail's own explicit instruction that this work lands in the
  reusable framework rather than in Orcshot's own `.github/workflows/`.
