# Backlog

Open items not yet scheduled into a task. Each entry keeps the context that led to it — not just
"what," but "why this matters" — so picking it up later doesn't require re-deriving the reasoning
from scratch.

## #1: `/orc-*` command namespace with parameter routing and stack defaults — a future sub-project, not v1

Raised by direflail while reviewing the Orclab v1 (process core) design (2026-09-04), explicitly
as spitballing to check whether it should change v1's scope. It shouldn't, and doesn't — v1 (see
`docs/superpowers/specs/2026-09-04-orclab-v1-process-core-design.md`) is three behavioral skills
(`backlog-discipline`, `release-checklist`, `environment-registry`); this idea is a different kind
of thing entirely: a command/intent layer for directing *new* project work, not a discipline for
tracking existing project state.

**The idea, as described:**
- A `/orc-` command base, e.g. `/orc-code` to signal "code needs to be written."
- Subcommand parameters that change behavior significantly — e.g. `/orc-code refactor` means the
  project is changing language or language version, which should trigger an extended
  question-asking phase to nail down scope before anything happens (echoes the brainstorming
  skill's own "classify, then ask" shape, but scoped specifically to refactor/migration work).
- Natural-language routing: a plain request like "I'd like to use /orc-code to write a hello world
  project in Java" should be recognized as the `/orc-code` path with `java` as the inferred
  language parameter, without requiring the literal command syntax.
- Defaults, per language and per project type — e.g. Java desktop apps default to
  Java + Spring + JavaFX — with version/specifics still confirmed via questions rather than
  silently assumed.

**Why this matters:** if useful, this becomes the primary way Orclab gets used day-to-day
(starting new work), which is a different value proposition than v1's "keep track of what's
already true about a project." Worth designing well, not bolted onto v1 as an afterthought.

**Implementation mechanism, confirmed live (2026-09-04, corrected from this entry's own first
draft, which wrongly guessed plugins couldn't do this):** Claude Code plugins register real slash
commands via a `commands/*.md` file per command, with an `argument-hint` frontmatter field and
`$ARGUMENTS`/`$1`/`$2`-style positional parsing in the body — a real installed example,
`code-modernization`'s `modernize-assess.md`, takes `<system-dir> [--show-secrets] | --portfolio
<parent-dir>` and branches on `$ARGUMENTS` directly. This directly supports the `/orc-code
refactor`-style subcommand-as-parameter idea with no new mechanism needed. Still open: how many
commands beyond `/orc-code` are needed (this entry only describes the one example given), how the
natural-language-routing case ("use /orc-code to write X" without the literal slash) gets
recognized without a literal invocation, and how per-language/per-stack defaults get
stored/overridden per project.

**Next step, when picked up:** a fresh `superpowers:brainstorming` pass (Architectural path,
given it's a new subsystem with its own command surface and inference logic), separate from v1's
spec and plan.

## #2: A base visual/design-system layer for apps Orclab helps build — a future sub-project, not v1

Raised by direflail (2026-09-04), separately from #1 and from v1's process-core scope: right now
Orclab has no opinion at all about how the apps it helps build actually *look* — how desktop apps,
mobile apps, and web apps are styled, scaled, and made to behave visually, across platforms. The
concrete comparison direflail gave: Caterpillar (their employer) has an internal framework called
"Blocks," built on React, that fills exactly this role there — but it's employer-owned and can't
be used outside work, so a real gap exists for personal/other-project work.

**What this is NOT**: not another web framework (React/Vue/Angular/Svelte) — those were already
ruled out as beside the point in this same conversation; direflail was explicit that the ask is
about the visual/design layer that sits *on top of* those, not the framework itself. Also not
CSS-utility libraries (Bootstrap, Semantic UI) or admin-panel generators (Refine, react-admin) —
those came up in initial research but don't match the "controls look/scale/behavior across
desktop and web platforms" framing once direflail clarified the actual ask.

**Real candidates surfaced by research (not yet evaluated hands-on, not yet decided)**, roughly in
three layers that would likely need to be picked in combination, not as a single choice:

- **Full design systems** (closest analogs to Caterpillar's Blocks — token-driven theming plus a
  complete component set plus cross-platform scaling rules): Material Design 3 (Google), Fluent UI
  (Microsoft — adaptive layouts scaling across Windows desktop/web/mobile), Carbon (IBM —
  framework-agnostic: React/Angular/Vue/Svelte/web components), Ant Design (strong for data-dense,
  desktop-style apps), GitHub Primer (developer-tool focused).
- **UI component libraries** (the practical implementation layer): shadcn/ui (copy-paste model on
  Radix primitives + Tailwind — you own the source directly, no vendored dependency to work
  around), Chakra UI, MUI (works for web and Electron desktop), Radix UI (unstyled, accessible
  primitives only — maximum control, bring your own visual design).
- **Design tokens** (the actual cross-platform-scaling mechanism underneath either of the above):
  Style Dictionary (Amazon — transforms tokens into CSS/iOS/Android/etc. — the current industry
  standard), Diez (compose tokens in TypeScript, compile to native iOS/Android/Web libraries), the
  W3C Design Tokens spec (stable v1 as of October 2025 — vendor-neutral token format).

No hands-on evaluation of any of these has happened yet — this is raw research, not a decision.
An initial framing (not a recommendation to commit to) leaned toward Fluent UI or Carbon as the
closest single-framework analogs to Blocks, versus shadcn/ui + Radix + Tailwind + a token system
as the more modern, full-code-ownership alternative — but this needs real comparison against
Orclab's actual target platforms (desktop apps, mobile apps, web apps specifically) before
choosing, not just a feature-list comparison.

**Why this matters:** without this, every app Orclab helps scaffold or build would need its visual
styling decided from scratch each time, with no consistent base — the same kind of repeated,
undistilled decision-making this whole framework project exists to avoid.

**Next step, when picked up:** a fresh `superpowers:brainstorming` pass (Architectural path — this
is a new subsystem, and the choice of base framework has wide-reaching downstream consequences for
anything built on it), separate from v1's spec/plan and from #1's command-layer work. Likely needs
its own research spike comparing 2-3 real candidates against Orclab's actual target platforms
before a design gets proposed, not a decision made from the comparison table alone.

## #3: Real enforcement for the discipline v1 only guides — not yet decided how

Raised by direflail (2026-09-04) right after v1 shipped, once it became clear that v1's three
skills (`backlog-discipline`, `release-checklist`, `environment-registry`) are pure guidance: text
Claude reads and follows, with nothing that fails a commit or blocks an action if the discipline
is violated (wrong `BACKLOG.md` numbering, a `RELEASING.md` step silently duplicating CI, an
environment-registry entry that leaked into git instead of memory). direflail had been planning to
build enforcement via the `/orc-*` command idea (#1), but flagged this as possibly its own
consideration, separate from #1, worth discussing before deciding where it belongs.

**What "enforcement" would actually mean, concretely** (not yet built, not yet designed): a
Claude Code `hooks/` script that runs on a real event (e.g. before a commit, or after Claude edits
`BACKLOG.md`) and actually checks the discipline mechanically — re-parses `BACKLOG.md` for
duplicate or reused entry numbers, checks that a resolved entry's original text is still present
verbatim, or similar — rather than trusting that Claude read and correctly applied the SKILL.md
prose. This is a fundamentally different kind of thing than a skill: a skill shapes behavior by
being read; a hook (or a CI lint step) verifies an outcome regardless of how it was produced.

**Open question, explicitly not resolved here:** whether this belongs inside the `/orc-*`
command-layer sub-project (#1), as its own sub-project, or as small additions directly to v1's
existing three skills (each skill could ship its own optional lint script, without needing the
command layer at all). direflail asked to hold off deciding and talk it through first.

**Next step, when picked up:** a conversation (or a fresh `superpowers:brainstorming` pass, if it
turns out to be Architectural-sized) specifically about where enforcement fits relative to #1 and
to v1's existing skills — before any hook or lint script gets designed.

## #4: Real per-language/per-domain default stacks for /orc-code — mostly undecided, one confirmed

Raised by direflail (2026-09-05) while designing `/orc-code`'s defaults table (part of #1's work).
When asked for real personal stack preferences to bake in (replacing the original idea's
illustrative placeholder), only one came back genuinely settled; everything else surfaced is real
signal about direction but not yet a decision:

- **Confirmed**: Java desktop → Java + Spring + JavaFX.
- **Unsettled, named as real interests or open questions, not decisions**: Python desktop (unsure
  of the modern stack, guessed "close to what Orcshot uses" but not confirmed), .NET 8 + C# for
  possible Windows desktop work, Unity for game development (wants to explore), mobile (wants
  Android native, iOS native, AND something cross-platform, but hasn't picked any of the three),
  web (HTML5/CSS/JS/React/Python confirmed as the toolset, but not yet mapped into specific
  default combos), database strategy across all of the above ("we'll need to discuss what to use
  in which case" — explicitly not resolved), containerization (Docker — wants to explore),
  observability (Grafana/Prometheus/Loki — wants to explore).

**Why this matters:** `/orc-code`'s defaults table is meant to reflect direflail's real, settled
preferences so the tool proposes something genuinely useful — baking in a guess for a stack
that isn't actually decided would give false-confidence suggestions, working against the whole
"built for me" premise of this project.

**Scope boundary, decided for now:** `/orc-code` v1's defaults table contains only the one
confirmed entry (Java desktop). Every other case falls through to asking directly — which was
already the design's fallback behavior when no default exists, so this isn't a workaround, just
an accurate reflection of what's actually settled today.

**Next step, when picked up:** likely several separate conversations/research passes, not one —
these domains (desktop-per-language, mobile strategy, web-stack-to-default mapping, database
strategy, containerization, observability) are different enough from each other that treating them
as one research question would repeat the same "too much at once" problem this entry itself was
split out to avoid.

## #5: `/orc-data` — a command for tracking legacy-system info during refactor work

Raised by direflail (2026-09-05) alongside `/orc-code`'s design, describing the real motivation
behind the whole Orclab project: direflail's day job involves bringing 20-year-old Java/C# systems
up to modern standards, and wants a dedicated way to store and organize information about the
system being refactored, to support actually moving it to the new one.

**Real overlap worth checking before designing anything new:** `code-modernization` (the same
plugin `/orc-code refactor` already wraps, per #1's design) ships `modernize-map` and
`modernize-extract-rules` commands — real, existing steps in its workflow that sound like they
may already cover exactly this need (mapping a legacy system's structure, extracting its rules).
Worth reading what those two commands actually do, concretely, before assuming `/orc-data` needs
to be built from scratch — the same "wrap, don't reinvent" instinct already applied to
`/orc-code refactor` itself.

**Scope boundary:** nothing decided yet — no data shape, no fields, no relationship to
`modernize-map`/`modernize-extract-rules` has been evaluated. Not part of #1's `/orc-code` work.

**Next step, when picked up:** read `code-modernization`'s `modernize-map.md` and
`modernize-extract-rules.md` in full first — if they already solve this, `/orc-data` might end up
being a thin wrapper (same shape as `/orc-code refactor`) rather than new logic. Then a fresh
`superpowers:brainstorming` pass for whatever gap remains.
