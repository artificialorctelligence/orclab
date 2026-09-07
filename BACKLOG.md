# Backlog

Open items not yet scheduled into a task. Each entry keeps the context that led to it — not just
"what," but "why this matters" — so picking it up later doesn't require re-deriving the reasoning
from scratch.

## #1: `/orc-*` command namespace with parameter routing and stack defaults (RESOLVED 2026-09-05)

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

**Resolved for real, not just tracked**: shipped as `/orc-code` (Orclab v2, 2026-09-05) — see
`docs/superpowers/specs/2026-09-05-orclab-v2-orc-code-command-design.md` and its companion plan.
Both of this entry's own open questions got real answers: natural-language routing without a
literal invocation is handled by reading `$ARGUMENTS` for intent (the same read-and-classify
mechanism Claude Code's own skill matching already uses, not a separate classifier) rather than
requiring the literal keyword; per-language/stack defaults are baked directly into
`commands/orc-code.md`'s own Defaults Table, editable in place, currently holding exactly one
real, confirmed entry (see #4 for the much larger, still-open research behind which defaults
belong there). `/orc-code` covers new-project, add-to-existing, and refactor work by wrapping
`feature-dev` and `code-modernization` rather than reimplementing them. Whether more `/orc-*`
commands beyond `/orc-code` get built is now a separate, forward-looking question — `/orc-data` is
already tracked on its own as #5.

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

## #6: Per-language manifest version detection/sync for /orc-version — deferred, same reasoning as #4

Raised by direflail (2026-09-05) while designing `/orc-version` (see
`docs/superpowers/specs/2026-09-05-orclab-v3-orc-version-orc-help-design.md`): when Orclab is
pointed at a project that already has an established version-holding file — Maven's `pom.xml`,
npm's `package.json`, Cargo's `Cargo.toml`, and others — `/orc-version` could detect it at
first-touch and suggest a starting version from what's already there, and/or keep that file's own
version field in sync on every future bump (or at minimum ask each time whether to).

**Why this is deferred, not built now:** real and valuable, but each format has its own real
syntax and its own real risk of a sloppy write breaking a build — this is genuinely a per-format
feature, not one generic mechanism. The same shape of problem as BACKLOG #4's stack-defaults
research: broad enough that folding it into `/orc-version`'s own v1 design would have let it
swallow everything else being decided there.

**Scope boundary, decided for now:** v1 of `/orc-version` only touches `.claude-plugin/plugin.json`
/ `marketplace.json` (when present) and falls back to `CHANGELOG.md` + a git tag otherwise. It does
not detect or write to any other language's version-holding file.

**Next step, when picked up:** likely one format at a time (Maven first, or whatever direflail
actually needs first for real work), each with its own real syntax handled correctly — not a
generic "detect any manifest" abstraction built speculatively ahead of a second real case.

## #7: Distribution-channel download/install metrics — carried over from Orcshot #186, direflail wants Orclab to own this eventually

Raised by direflail (2026-09-06), explicitly carrying over Orcshot's own `BACKLOG.md` #186 (raised
there 2026-08-28, still open, not resolved on that side) and widening it: direflail wants whatever
this becomes to live in Orclab, not as an Orcshot-specific script, since any project publishing to
multiple distribution channels would want the same thing. Not wanted yet — direflail's own words:
"it doesn't have to be done yet."

**The original ask, verbatim from Orcshot's #186:** "find out what metrics we can get about how
many downloads we get. i don't want anything but numbers to make myself feel good." An explicit
constraint, not just phrasing — this is about reading whatever numbers each distribution channel
already publishes on its own, never about adding tracking, telemetry, or analytics to a project
that doesn't already have it. No phone-home code, nothing that reports on real users.

**What Orcshot's #186 already confirmed real, carried over here rather than re-derived:**
GitHub Releases exposes a genuine per-asset download counter today — `gh release view <tag>
--json assets` returns a real `downloadCount` field per asset. Trivial to check for any project
with a real release.

**What Orcshot's #186 left unchecked, still genuinely open:** whether Launchpad exposes any public
download/install statistics for PPA packages at all — a known, long-standing gap/frustration in
the Launchpad community (unlike Debian's own opt-in popularity-contest mechanism), never confirmed
one way or the other. Also unchecked: whether a PPA `apt install` is even the kind of thing
Launchpad *could* count, since PPA downloads happen from Launchpad's own mirror infrastructure,
not a single trackable endpoint the way a GitHub Release asset is.

**Real widening beyond what #186 itself covers**, per direflail's own explicit framing today
(apt/Snap/Flatpak, not just apt/GitHub): Snap Store publishes real, documented install/metrics
data (`snapcraft metrics <snap-name>` and the Snap Store's own developer dashboard) — not yet
confirmed live for any real project, just known to exist as a real mechanism worth checking.
Flathub also publishes real public per-app download statistics (flathub.org/stats and a
documented API) — also not yet confirmed live, same status.

**Why this belongs in Orclab, not Orcshot:** the actual mechanism per channel (GitHub's API,
`snapcraft metrics`, Flathub's stats API, whatever Launchpad turns out to offer or not) is
identical for any project publishing through that channel — this is exactly the kind of "core"
guidance direflail's own taxonomy describes, not something specific to Orcshot's own packaging.

**Scope boundary:** nothing built, nothing even fully researched yet — Launchpad's real
availability is still unconfirmed, and Snap/Flatpak's mechanisms are named but not yet verified
live against a real project. Not assigned to a specific Orclab command yet either (could end up
inside `/orc-version`'s own territory, given its adjacency to release/versioning, or its own
command, or something else entirely) — that's an open design question for whenever this gets
picked up, not decided here.

**Next step, when picked up:** finish the real research first (confirm Launchpad's actual
capability one way or the other, verify `snapcraft metrics` and Flathub's stats API live against
a real published project) before any `superpowers:brainstorming` pass on what Orclab actually
builds from it.

## #8: Two stale version literals left in VERIFICATION.md, found during v5's own final review (RESOLVED 2026-09-06)

Found during the currency-discipline/verify-before-asserting (v5) final review's fix round
(2026-09-06). That review caught and fixed Scenario 9's version anchor (it hardcoded `0.4.0`/
`v0.4.0`, stale the moment the branch bumped Orclab past that version) — but two adjacent, real
instances of the same staleness pattern were spotted by the re-review as explicitly out of that
fix's scope, and parked here instead of looping further on an already-clean fix round.

**Instance 1 — Scenario 10's own hardcoded example:** `VERIFICATION.md`'s Scenario 10 still reads
"the current version (`0.4.0`, or whatever it's been bumped to)" — the hedge ("or whatever it's
been bumped to") makes the scenario still technically correct, but the literal `0.4.0` example is
now stale now that Orclab is at `0.5.0`. Same class of defect Scenario 9 just got fixed for, one
scenario left half-addressed.

**Instance 2 — Scenario 9's own revert command:** step 4's revert instruction hardcodes
`git tag -d v1.0.0 && git reset --hard HEAD~1`. This is only correct because Orclab's current
major version is `0` — any `increment major` from a `0.x.y` version lands on `1.0.0`, which is
what makes the literal tag name right today. The moment Orclab's own real version reaches `1.0.0`
and gets bumped again, this same probe (`increment major` from, say, `1.4.0`) would produce
`2.0.0`, and the hardcoded `v1.0.0` in the revert command would be wrong — deleting a tag that
was never created, and quietly reverting the wrong thing (or nothing at all) instead.

**Why this matters, concretely, not hypothetically:** `VERIFICATION.md` is the actual dogfood
script someone runs by hand — a stale literal here isn't cosmetic, it produces a confusing failure
or a silent no-op exactly when the script is supposed to be proving the real tool works.

**Scope boundary:** both instances are wording/literal fixes only — no change to `/orc-version`
itself, no design question open here. This is purely "make the verification script's own examples
stop hardcoding a version number that keeps changing."

**Next step, when picked up:** reword Scenario 10's example the same way Scenario 9's was just
fixed (reference "whatever `plugin.json` currently reports," not a literal number), and make
Scenario 9's revert instruction compute the expected new-major tag from the real current version
rather than assuming `v1.0.0` specifically — or, more simply, tell the reader to check
`git tag --list 'v*' --sort=-v:refname | head -1` right before deciding what to delete, rather
than hardcoding any literal tag name at all.

**Resolved for real, not just tracked:** both instances fixed exactly as described above. Scenario
10 now reads "the current version (whatever `plugin.json` currently reports)" with no literal
number. Scenario 9's revert step now finds the actual tag it just created via
`git tag --list 'v*' --sort=-v:refname | head -1` instead of assuming `v1.0.0`.

## #9: v5's plan never tagged its own release — caught only by tagging v0.6.0 and noticing v0.5.0 missing (RESOLVED 2026-09-06)

Found 2026-09-06 while tagging v0.6.0: `git tag --list 'v*'` showed `v0.3.0`, `v0.4.0`, `v0.6.0` —
no `v0.5.0`, despite the currency-discipline/verify-before-asserting release having been built,
merged, and pushed under that version number. Not a deleted or lost tag — `git log --oneline --all
| grep 0.5.0` confirmed the version-bump commit (`1eb34c7`) is real and on `main`; it was simply
never tagged. Checked against v3's and v4's own plans: both explicitly included a "create the git
tag" step in their versioning task. v5's plan, drafted the same way, dropped that step — a real
gap in the plan itself, not an execution slip.

**Fixed for real, not just tracked:** retroactively tagged `v0.5.0` at `1eb34c7` (2026-09-06,
local-only, matching the existing convention that tags stay local until an explicit release
action). All four version tags (`v0.3.0`–`v0.6.0`) now present and correct.

**Why this matters beyond the one missing tag:** every future `/orc-*`-command or version-bump
plan risks the same silent gap unless the versioning task template itself is checked against a
real prior example (v3/v4) before being reused, not just written from memory of "what a version
bump task looks like."

**Next step, when picked up:** none needed for this instance — closing it here as resolved. Worth
remembering during future plan-writing (`superpowers:writing-plans`) for any Orclab version-bump
task: copy the git-tag step from an existing plan (e.g. v4's) rather than re-deriving the task
from scratch.

## #10: Solidify /orc-publish's testing strategy beyond what the spec settles for v7

Raised by direflail (2026-09-06) during the `/orc-publish` design's testing section: the spec
settles for real unit tests on the tree-resolver script (path resolution, subtree-select+exclude,
shared-cascade merging, unset-channel skip) plus `VERIFICATION.md` scenarios run against a
synthetic throwaway tree with no-op leaf actions — deliberately never testing against a real
destination from Orclab's own repo. direflail wants this strategy solidified further, but was
explicit it doesn't need to happen before `/orc-publish` ships.

**What's already decided, not open for re-litigation here:** the two-layer split itself (real
automated tests for the resolver logic; hand-run dogfood scenarios for command behavior) and the
synthetic-tree-only rule for Orclab's own verification (real-destination testing is the separate
Orcshot dogfooding task's job, not this one).

**What's actually open:** unspecified — direflail flagged a general instinct that this needs more
rigor without naming the specific gap yet. Likely candidates worth raising when this is picked up:
whether the resolver's unit tests need to cover deeper trees than the two-to-three-level examples
seen during design (Orcshot's own real component/channel/distro trees, once dogfooded, would be a
real stress test), and whether the synthetic throwaway tree used in `VERIFICATION.md` should be
checked into the repo as a fixture (so its shape doesn't drift from what the scenarios assume) or
constructed inline by each scenario.

**Next step, when picked up:** ask direflail what specifically felt underspecified, rather than
guessing — this entry exists to hold the "come back to this" intent, not to pre-decide what's
missing.

## #11: `/orc-publish`'s `execute_plan` has no subprocess timeout — a real hang risk, not yet fixed

Found during the final whole-branch review of `/orc-publish` (v7, 2026-09-06). `execute_plan` in
`skills/orc-publish/scripts/orc_publish/cli.py` runs each leaf's `action` via `subprocess.run`
with no `timeout` argument. A leaf action that blocks on stdin hangs the entire `/orc-publish` run
indefinitely, with no way to know which leaf is stuck — `capture_output=True` means the process's
own prompt never even reaches the terminal, so it just looks like the command has frozen. This
isn't hypothetical: Orcshot's own real PPA publish step already uses `debsign`, which prompts
interactively for a GPG passphrase, and `debsign` is exactly the kind of action a real
`channels.yaml` leaf would wrap once Orcshot's own follow-on dogfooding task (populating real
`.orclab/publish/` content, per the design spec's explicit scope note) gets underway.

**Why this is deferred, not fixed now:** picking a correct timeout value is itself a real design
question, not something to guess at speculatively. Different real actions have legitimately
different normal durations — a `dput` upload and a local build script don't share a reasonable
timeout — so a single hardcoded number would either falsely abort a slow-but-healthy upload or
fail to catch a hang quickly enough. This needs its own real decision (a per-leaf configurable
timeout? a global default with an override? something else?), not a number picked to make this
finding go away.

**Scope boundary:** this is about the generic mechanism — `execute_plan` itself needing a timeout
strategy — not about routing around `debsign`'s own interactive-prompt behavior specifically (e.g.
via `--no-tty` or a pre-supplied passphrase). Those are separate, narrower questions that belong to
whoever actually wires up `debsign` as a real leaf action, not to this generic mechanism fix.

**Explicit flag for whoever picks up Orcshot's own follow-on dogfooding task:** know about this
risk before running `/orc-publish` against a real `debsign`-based action — you will hit it live,
with the run just appearing to hang, otherwise.

**Next step, when picked up:** design a timeout strategy for `execute_plan` (default value,
whether it's per-leaf configurable via the channel tree, what happens to the summary line for a
leaf that times out — presumably a new `"timed out"` status distinct from `"failed"`) before
implementing it.

## #12: `/orc-publish` models channel fan-out, but a real release is mostly an ordered pipeline — the framework can't yet drive Orcshot's own release

Found 2026-09-06/07, dogfooding `/orc-publish` against Orcshot's real release for the first time.
direflail named the pattern directly, and it's the right diagnosis: "i feel like you're finding out
what to do one piece at a time and then finding out later and we're patching up the process to fix
it. do you understand the whole process we're trying to do, and then are we applying that to the
framework?"

**What actually happened:** Orcshot's `.orclab/publish/channels.yaml` was written against
`RELEASING.md` step 6 in isolation, before anyone had read the document end to end. Every problem
that followed was a consequence of that, not bad luck — a `../*.changes` glob that would have tried
to `dput` 33 accumulated past builds (see the fix in Orcshot's own history), a near-miss uploading
a version already live on Launchpad, a near-miss releasing on top of uncommitted in-progress work,
and repeated confusion about step ordering. Each was patched individually as it surfaced.

**The real structural finding, once the whole 11-step process was actually read:**

| Orcshot's real release process | What `/orc-publish` models |
|---|---|
| 11 ordered steps with real gates (tests before build, lint before upload, CI green before the GitHub Release) | Independent leaves, no ordering, and by explicit design *continues past a failure* |
| Real preconditions ("is this version already on Launchpad?", "is the tree clean?") | None — no notion of checking destination or local state before acting |
| Steps that are not shell commands at all: a Launchpad web-UI "Copy packages" click, install-testing on three real machines/VMs, clicking a menu item to verify the update checker | `action:` is a shell string; these steps are invisible to the model entirely |
| Most steps (1-5, 8-11) are release-wide, not per-channel | Only models the per-channel fan-out |

**The tell, concretely:** Orcshot's own `ppa.noble` leaf had to smuggle `dpkg-buildpackage -S` — a
*build* — into what is nominally a *publish* action, just to work at all. A leaf action that has to
build the thing it publishes is a sign the "publish an already-built artifact" abstraction doesn't
fit the real work.

**In fairness to the v7 spec, this is not a bug in it:** `/orc-publish` was deliberately scoped to
"push a project's built artifacts to their real distribution destinations," with artifact
generation explicitly out of scope. It is internally consistent and it does the fan-out part
genuinely well (the channel/distro split, the dotted-path selection, the dry-run gate all held up
under real use). The gap is that *"push built artifacts" turned out to be a far thinner slice of
"release this project" than assumed when it was scoped* — roughly one step out of eleven, and even
that one doesn't cleanly fit. Orcshot's real process is mostly pipeline; v7 built the fan-out.

**The open design question, deliberately not answered here:** does Orclab need a pipeline concept —
ordered steps, gates/preconditions, and a way to represent a step a *human* performs (a web-UI
click, a manual install-test) rather than a shell command — with `/orc-publish` becoming one stage
within it rather than the whole thing? Adjacent existing pieces that must be considered rather than
duplicated: `release-checklist` (v1) already maintains a numbered, dependency-ordered
`RELEASING.md`, which is *exactly* the artifact this would be automating against — so this may be
much more about giving that skill real teeth than about inventing a new structure. `/orc-version`
also already owns part of the spine (version bump, changelog, tag, GitHub Release) and BACKLOG #6
already tracks its per-language manifest gap, which Orcshot hit live (it can't bump
`pyproject.toml`/`debian/changelog`).

**Why this is not a patch:** the previous items found during this dogfooding pass (#11, and the
Orcshot-side config fixes) were real but local. This one changes what the framework is for. It
needs the same `superpowers:brainstorming` → spec → plan treatment `/orc-publish` itself got, not
another inline fix.

**Next step, when picked up:** a fresh brainstorming pass (Architectural), starting from a real,
complete read of Orcshot's `RELEASING.md` as the worked example — the whole document first, before
any design is proposed. Read `release-checklist`'s SKILL.md and `/orc-version`'s command file in
full at the same time, since the answer may be "make these two work together properly" rather than
"add a new component."
