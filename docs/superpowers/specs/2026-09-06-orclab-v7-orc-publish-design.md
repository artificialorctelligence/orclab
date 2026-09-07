# Orclab v7: `/orc-publish` — design

## Goal

Give Orclab a generic command for pushing a project's built artifacts to their real distribution
destinations — a PPA, the Snap Store, Flathub, npm, an app store, wherever — replacing manual
multi-step processes like Orcshot's current `debsign`/`dput` sequence with a single, safe,
selectable command, once a project has actually wired up the mechanism for its own destinations.

This spec grew out of an extended design conversation (2026-09-06) that started from "what's
built in to trigger an upload pipeline" and worked through two real tensions before converging:
distro vs. channel as genuinely different axes (a channel is *how* you publish; a distro is *what
you're publishing for*, and the two don't map one-to-one), and how deep a tree needs to go before
it stops being generic and starts being Orcshot-specific. Both are resolved below.

## Scope

**In scope now:** the generic mechanism — the two-tree data model, the `/orc-publish` command
surface, the selection language, the confirmation gate, and the bundled resolver script's tests.

**Explicitly out of scope:**
- **Orcshot's actual leaf content.** This spec defines the *shape* a channel/distro tree takes;
  it does not populate Orcshot's real `noble`/`resolute` PPA leaves, its real Snap/Flatpak leaves,
  or its real Mint/Ubuntu2404 × X11/Wayland distro fan-out. That's a separate follow-on dogfooding
  task against Orcshot itself, with its own safety review given it's the first time this ever
  touches a real, live destination. **Orclab's own repo contains zero Orcshot-specific
  channel/distro data** — any such content belongs only in a consuming project's own `.orclab/`
  directory.
- **`/orc-doc`** (artifact generation — PPTX/report/webpage creation). A future, separate command.
  `/orc-publish` only ships an artifact that already exists; it never creates one.
- **Any change to `/orc-version release`.** The two commands stay independent: `/orc-version
  release` publishes source/changelog to a GitHub Release; `/orc-publish` publishes built
  artifacts to distribution channels. A project may use either, both, or neither.
- **Real per-language/per-category default trees.** Same reasoning as BACKLOG #4 — populated one
  real project at a time, not designed speculatively ahead of a second real example.
- **Solidifying the testing strategy further than this spec settles.** Tracked as BACKLOG #10;
  explicitly deferred by direflail during design.

## Data Model

Both trees are **generic recursive structures with no fixed depth or schema**: a node is either a
**branch** (named children) or a **leaf** (an action/content). Depth follows what's actually real
for that project — a single-child branch is not over-modeling, it's just accurate; a project with
only one component, one distro family, or one series never has to show that grouping level at
all.

### Storage

Two files per consuming project, never present in Orclab's own repo with real content:
- `.orclab/publish/channels.yaml`
- `.orclab/publish/distro.yaml`

YAML, not JSON — these are meant to be hand-edited and reviewed in diffs, not only
machine-generated.

### Component layer

An optional top level, above category, on **both** trees. Invisible for a single-component
project (nothing renders it, nothing requires it). Becomes real the day a project has genuinely
separate publishable pieces — e.g. a Python desktop app with a bundled Node.js helper utility
published separately via npm. Each component gets its own independent channel tree and distro
tree underneath it; one component's tree can be far richer than another's (a Node helper's distro
tree might have no real content at all, since npm-published tools usually aren't distro-coupled).

A sub-component that is merely *bundled* into an existing artifact (e.g. Orcshot's own bundled
GNOME Shell extension JS, shipped as a packaged resource inside the same `.deb`/snap/flatpak) is
**not** a separate component — the channel tree tracks where things are *shipped*, not what
languages make up the codebase. `/orc-code`'s own language categorization already covers "what is
this project, primarily"; it does not recurse into every internal resource.

### Channel tree

`component` (optional) → the same top-level categories `/orc-code` already supports (desktop,
mobile, web, CLI, API, etc. — reused, never duplicated) → language → platform → channel, branching
further only where the real publish mechanism itself varies. A channel like PPA splits per series
(`ppa.noble`, `ppa.resolute`) because each is a genuinely distinct source upload with its own
`Distribution:` field; a channel like Snap or Flatpak never splits, because one build — bundling
its own runtime — serves every distro uniformly.

Each leaf carries:
- `action` — how to actually publish. This wraps a project's own existing, documented mechanism
  (e.g. a reference to Orcshot's own `debsign`/`dput` sequence, once that dogfooding task writes
  it) rather than reinventing publish logic generically. Same "wrap what's real, don't reinvent"
  principle already in `CLAUDE.md` for `feature-dev`/`code-modernization`/`pptx`.
- `filename_template` — a template for the artifact's generated filename (e.g.
  `orcshot_<version>.zip`; exact convention is per-project).
- optional `requirements` / `issues` — lists of links only, same rule as the distro tree below.

### Distro tree

A separate structure, one level finer-grained than a channel leaf: real environment combinations
that need their own tracked requirements/issues even when several of them reduce to the same
channel leaf at publish time (e.g. `mint.x11`, `mint.wayland`, `ubuntu2404.x11`,
`ubuntu2404.wayland` can all point at the same `ppa.noble` leaf — Mint and Ubuntu 24.04 are
binary-compatible with that one build, but each is a genuinely separate real-world target worth
its own known-issues tracking, e.g. "Wayland tray on Mint: untested").

Each real distro node carries:
- `channel` — an optional dotted-path pointer into the channel tree. **Optional is load-bearing**:
  a distro node with no `channel` set represents a known, real, tracked target that simply has no
  publish mechanism wired up yet (e.g. a Mint edition tracking a future Ubuntu series, expected in
  a few months, with no channel decided). `/orc-publish` skips any node with an unset channel
  entirely — no partial attempt, no error, just "nothing to do here."
- `requirements` / `issues` — lists of links only (a BACKLOG entry, an environment-registry memory
  entry, an external bug tracker URL) — **never inline content**. The tree is an index, not a
  content repository.

Many distro nodes may point at the same channel leaf (many-to-one). This is not duplication in
the sense that caused problems earlier in this design's history — the channel tree remains the
single source of truth for *how to publish*; the distro tree never re-describes that, it only
points at it.

### `shared` cascade

At any level of either tree, a `shared` sibling holds content common to everything below/beside
it. A leaf's effective `requirements`/`issues` are everything from every `shared` node on its path
from the root, plus its own — no explicit `extends` field needed; the cascade is implicit in tree
position. This is what lets `distro.shared` hold a truly universal baseline, `distro.ubuntu.shared`
hold an Ubuntu-family-wide baseline (only once a second distro family exists — Orcshot alone never
needs this level), and `distro.ubuntu.noble` hold only its own delta from both.

### Relationship to `environment-registry`

Distinct, non-redundant concerns that happen to sit close together. `environment-registry`
(Orclab v1) tracks **how to reach a machine** — VM identifiers, SSH access, credentials policy,
gotchas about driving it — and is memory-only, never git-tracked, because it's specific to one
developer's machine. The distro tree's `issues` track **product compatibility state** — "does the
Wayland tray actually work on Mint" — a fact about the project, true regardless of whose machine
tests it, and belongs in git. The connection: a distro-tree issue's link may point at an
environment-registry memory entry as its testing provenance; neither system duplicates the other's
actual content.

## Command Surface

```
/orc-publish [selection...] [--for <distro-path>] [--dry-run]
```

- **No selection** — resolves to every leaf with a set `channel`, across every component if the
  project has more than one (nothing requires narrowing to one component first — the confirmation
  list below is the safety net for "that's more than I meant"). Shows the full resolved leaf list
  and stops for confirmation before executing anything.
- **Dotted-path selection** — `desktop.linux` selects the whole subtree beneath it (every real
  leaf); `desktop.linux.ppa.noble` selects exactly one leaf. Short names auto-resolve when
  unambiguous within the project's actual tree; Orclab reports plainly when a short name is
  ambiguous rather than guessing which one was meant.
- **Exclude** — a selection prefixed with `!` subtracts from what precedes it:
  `desktop.linux !desktop.linux.snap` publishes everything under `desktop.linux` except the Snap
  leaf. Subtree-select plus exclude are the only two composition primitives — no separate
  numbered-alias or group-name mechanism is needed on top.
- **`--for <distro-path>`** — read-only: resolves and reports which channel-tree leaf(s) a given
  distro node's `channel` pointer(s) touch, without executing or prompting anything. Reports "no
  channel set" plainly for an unset node rather than erroring.
- **`--dry-run`** — resolves the selection and prints the full leaf list plus each leaf's `action`,
  without prompting for confirmation or executing anything.

Every path that would actually execute something (no-args default, explicit selection, exclude)
goes through the same confirmation gate, showing the resolved leaf list before anything runs.
`--for` and `--dry-run` are the only pure-read paths.

## Error Handling

- **Malformed tree or unresolvable selection** (invalid YAML, an unknown field, a dotted path that
  doesn't exist, an ambiguous short name) fails loudly *before* the confirmation prompt appears.
  Nothing executes, nothing partially resolves.
- **An unset-channel distro node** is not an error state — it's reported as "known target, no
  channel wired yet," consistent with the optional-`channel` semantics above.
- **A leaf's `action` fails mid-run**, with other leaves still selected: execution **continues**
  with the remaining leaves rather than aborting, since they are independent destinations (a Snap
  Store failure has no bearing on whether a Flatpak push succeeds). A final per-leaf summary
  reports succeeded / failed (with the real error) / not attempted, so a leaf that never ran is
  never confused with one that ran and failed.

## Testing Strategy

Two layers, deliberately kept separate:

1. **Real automated tests**, committed to Orclab's own repo, for the bundled resolver script (the
   thing that loads both YAML trees, resolves a selection expression to a concrete leaf list,
   applies `shared` cascades, and renders `filename_template`). Covers: path resolution, subtree-
   select + exclude composition, multi-level `shared` cascade merging, and the
   unset-channel-means-skip rule. This is real logic with real bug surface — not left to an LLM
   re-deriving the right answer by eye each time.
2. **`VERIFICATION.md` scenarios**, same hand-run dogfood pattern every other `/orc-*` command
   already has, covering the command's end-to-end behavior: the confirmation gate, `--dry-run`,
   `--for`, and a real (no-op) leaf action actually executing when confirmed. These run against a
   **synthetic throwaway tree with no-op actions** (e.g. `action: echo "would publish X"`) —
   **never against a real destination** from Orclab's own repo. Testing against Orcshot's actual
   PPA/Snap/Flatpak is explicitly the follow-on dogfooding task's job, not this one, given it's the
   one genuinely irreversible thing in this whole design.

Further hardening beyond this split (deeper real-tree stress tests, whether the synthetic tree
should be a checked-in fixture) is tracked as BACKLOG #10 — explicitly not blocking this work.

## Worked example (illustrative only — not shipped in Orclab)

Built from Orcshot's real, live-verified state during design (confirmed via `debian/changelog`
and Launchpad's own packages page, not assumed):

```
# channels.yaml (illustrative)
desktop:
  python:
    linux:
      ppa:
        noble:    { action: ..., filename_template: "orcshot_<version>_source.changes" }
        resolute: { action: ..., filename_template: "orcshot_<version>_source.changes" }
      snap:    { action: ... }
      flatpak: { action: ... }
```

```
# distro.yaml (illustrative)
shared: { requirements: [...] }
mint:
  shared: { requirements: [...] }
  x11:     { channel: desktop.python.linux.ppa.noble }
  wayland: { channel: desktop.python.linux.ppa.noble, issues: ["untested"] }
mint-next:            # placeholder: Mint edition tracking resolute, expected ~months out
  x11:     { }        # channel intentionally unset — no publish mechanism decided yet
  wayland: { }
ubuntu2404:
  shared: { requirements: [...] }
  x11:     { channel: desktop.python.linux.ppa.noble }
  wayland: { channel: desktop.python.linux.ppa.noble }
resolute:
  x11:     { channel: desktop.python.linux.ppa.resolute }
  wayland: { channel: desktop.python.linux.ppa.resolute }
```

Neither file ships in Orclab's own repo — this is documentation of the shape, reproduced here for
clarity, not real shipped content.

## Global Constraints

- Command name: `/orc-publish`. No separate `/orc-distro` command — the distro-scoped query is the
  `--for` flag.
- Storage paths, exact: `.orclab/publish/channels.yaml`, `.orclab/publish/distro.yaml`. YAML, not
  JSON.
- Both trees are generic recursive structures (branch or leaf), no fixed depth, no fixed schema
  beyond the leaf/branch distinction itself.
- Distro-tree `channel` field is **optional** — an unset channel is a valid, non-error state
  meaning "known target, not yet actionable," and must never be silently attempted.
- `requirements`/`issues` on any node are **lists of links only** — never inline content.
- `shared` nodes cascade to descendants by tree position — no explicit `extends` field.
- Selection language: dotted paths, subtree-select, and `!`-prefixed exclude are the only
  composition primitives. No numbered/positional selection anywhere in the design.
- Every executing invocation (default, explicit selection, exclude) requires an explicit
  confirmation showing the full resolved leaf list before anything runs. `--dry-run` and `--for`
  never execute or prompt.
- On a mid-run leaf failure, remaining independent leaves still execute; a final per-leaf summary
  (succeeded/failed/not attempted) is always reported.
- **Zero Orcshot-specific (or any other consuming-project-specific) content may exist in Orclab's
  own repo.** Real tree content lives only in a consuming project's own `.orclab/` directory,
  populated by a separate follow-on task per project.
- The resolver script (tree loading, selection resolution, `shared`-cascade merging,
  `filename_template` rendering) is real bundled code with real automated tests, not
  prose-only/LLM-interpreted logic.
