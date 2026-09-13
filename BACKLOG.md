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

**Note 2026-09-12 (v18):** every stack skill now carries a `## UI` section, and each one ends with the same sentence — "BACKLOG #2's design system translates into the frameworks above." — naming this entry directly: `skills/stack-android-native/SKILL.md`, `skills/stack-flutter/SKILL.md`, `skills/stack-godot/SKILL.md`, `skills/stack-ios-native/SKILL.md`, `skills/stack-kotlin-multiplatform/SKILL.md`, `skills/stack-python-desktop/SKILL.md`, `skills/stack-react-native/SKILL.md`, `skills/stack-unity/SKILL.md`, `skills/stack-web/SKILL.md` — all nine of v18's stack skills. Whatever base design system this entry eventually settles on has a concrete, enumerated set of UI frameworks to translate into: SwiftUI, Jetpack Compose, GTK/Qt/Tkinter, Flutter widgets, Compose Multiplatform, React Native's core components plus React web, React (Vite), and each game engine's own UI toolkit (Godot Control nodes/themes, Unity UGUI/UI Toolkit). This entry stays open; nothing here picks a design system.

## #3: Real enforcement for the discipline v1 only guides — not yet decided how (RESOLVED 2026-09-07)

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

**Update (2026-09-07), from a real leak — enforcement now has a concrete highest-value target:**
A session diagnosing a `gh` auth banner printed a live OAuth token straight into the transcript by
running `gh auth token` as a throwaway diagnostic. That produced a new discipline skill,
`skills/secret-hygiene/SKILL.md` — which is guidance in exactly the sense this entry is about:
prose Claude reads, with nothing that mechanically stops the command from running next time.

It also sharpens this entry's open question rather than just adding to it. For `BACKLOG.md`
numbering, guidance-only is survivable — a wrong entry number is caught later and corrected. A
printed secret is not correctable at all: it lands in the model's context, every subsequent API
request, and the on-disk session JSONL simultaneously, and the only remedy is rotation, which is
the user's work. That asymmetry makes `secret-hygiene` the discipline with by far the strongest
case for real enforcement, and the natural first hook to build if this entry gets picked up —
ahead of the `BACKLOG.md` linting this entry originally imagined.

**Mechanism, confirmed live (2026-09-07):** a Claude Code plugin really can ship hooks, via a
`hooks/hooks.json` file at the plugin root alongside `.claude-plugin/plugin.json` — verified
against the real installed `gitkraken-hooks` plugin in this environment, which registers
`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `SessionStart`, `SessionEnd`,
`UserPromptSubmit` and `Notification`, each as `{matcher, hooks: [{type: "command", command}]}`.
Orclab ships no `hooks/` directory today. **Still unverified, and the thing to check first:** the
exact contract by which a `PreToolUse` hook *denies* a tool call rather than merely observing it —
do not design against a remembered answer, confirm it against the current docs (`currency-discipline`).


**RESOLVED 2026-09-07 — enforcement exists, scoped to the one discipline that most needed it.**
Shipped: `hooks/hooks.json` registering a `PreToolUse` hook matched to `Bash`, backed by
`hooks/scripts/secret_guard.py`. Run its suite with
`cd hooks/scripts && python3 -m pytest tests/ -v` (48 tests). It denies the narrow set of commands
whose entire stdout is a credential, and every denial names the safe alternative so a block
redirects the work instead of dead-ending it.

**The three-way open question above is answered by what shipped, and the answer is the third
option** — small additions alongside the existing skills, not inside #1's command layer and not
its own sub-project. Enforcement turned out to be per-discipline rather than a general mechanism:
this hook knows about secrets specifically, and a future `BACKLOG.md` linter would share the
`hooks/` directory with it and nothing else.

**Deliberate scope limits, not oversights:**
- Only `secret-hygiene` is enforced. The `BACKLOG.md` numbering and `RELEASING.md` step checks
  this entry opened with are still guidance-only, and stayed that way on purpose: those failures
  are correctable after the fact, while a printed secret never is. Raise a fresh entry if the
  numbering discipline actually starts drifting in practice — don't pre-build for it.
- The guard fails open on any internal error, and a `# orclab:allow-secret` marker bypasses it.
  Both are intentional. A hook that wedges every Bash call in every project Orclab is installed
  in would be a worse outcome than the leak it prevents, and a bypass that must be typed
  explicitly leaves the decision visible in the transcript.

**A real bug its own tests caught, worth remembering:** the first implementation read the trailing
`2>&1` of the motivating leak command as a stdout capture and allowed it straight through — the
guard would have missed the exact incident that produced it. Redirect detection now requires a
genuine stdout redirect (no fd digit before `>`, no `>&` form). Writing the regression test for
the real command first, rather than for a tidied-up version of it, is what surfaced that.


## #4: Real per-language/per-domain default stacks for /orc-code — mostly undecided, one confirmed (PARTIALLY RESOLVED 2026-09-11 — mobile and game stacks chosen) (RESOLVED 2026-09-12)

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

**Vocabulary from #17's design pass, 2026-09-08 — a language default is an *ingredient*.**
direflail's framing while scoping `/orc-package`: Orclab ships **ingredients** (reusable units of
knowledge — how to stand up a PPA channel, a default stack for a language), and each project
assembles the ones it needs into its own **recipe**, which is the project's real, existing config —
`channels.yaml`, `RELEASING.md`, and for `/orc-code`'s purposes whatever a scaffolded project ends
up with. Orclab is itself a project with its own recipe, drawing on the same core ingredients as
anyone else.

That reframes this entry usefully. The "defaults table" is really *the ingredients Orclab ships for
`/orc-code`*, and its documented fall-through — ask directly when no default exists — is "no
ingredient for this case yet," which is the same honest state `/orc-publish` reports for a known
but un-onboarded channel. The scope boundary above is not a workaround; it is an accurate
ingredient list with one entry in it.

**Deliberate caution, agreed when the framing was raised: take the vocabulary, not a shared
mechanism.** A channel ingredient (registration, credentials, publish action, confirmation) and a
language ingredient (framework choices, project layout, build tooling) may share nothing beyond the
metaphor. They are consumed by different commands and have different shapes. Unifying them into one
ingredient *system* on the strength of two examples — one of which does not exist yet — would be
exactly the speculative generality this repo keeps deleting. See **#17**, which takes the same
vocabulary and holds the same line.

**One question this raises and does not answer:** #17's design lets a user *capture* a channel
ingredient Orclab does not ship, stored user-level so it survives a plugin reinstall and works for
someone who will never touch Orclab's source. Whether a settled language stack should be capturable
the same way — direflail's real Java-desktop preference living somewhere reusable rather than only
in Orclab's own table — is a genuine question, and is not decided here.

**Partially resolved 2026-09-11 (BACKLOG #33).** direflail settled three of the open lines:
cross-platform mobile is **Flutter + Dart**; cross-platform games (including mobile) are **Unity
and Godot**; Android native and iOS native are wanted alongside, with "current accepted" toolchains
to be determined by #33's research pass. The open question above — whether a settled stack should
live somewhere reusable rather than only in the table — is answered by #33: each stack becomes a
background knowledge skill (`skills/stack-<name>/SKILL.md`, `user-invocable: false`), and the
Defaults Table row points at it. Python desktop, .NET, web combos, database strategy, Docker and
observability remain as undecided as before.

2026-09-11, v17: a new stack skill's Testing row or Build section links to
`skills/orc-test/languages/<lang>.md` rather than restating tools — that is where `/orc-test`
reads them from.

**Resolved for real, not just tracked:** `docs/superpowers/specs/2026-09-12-orclab-v18-project-type-defaults-design.md` (v18) closes every line this entry ever named. Its eleven research passes ran as plan Tasks 2-12: Task 2 `stack-python-desktop` (PySide6 chosen); Tasks 3-7 the Presence/UI/Storage/Scope-divergence facets (the facets every stack skill now answers — presence, meaning how the app stays reachable when not in front; UI framework; storage; and for games what diverges by platform) on `stack-flutter`, `stack-android-native`, `stack-ios-native`, `stack-godot`, `stack-unity`; Task 8 iOS build/sign from Linux — EAS Build does require a React Native project, but Codemagic builds and signs Flutter for iOS on 500 free macOS minutes a month, so the spec's assumed constraint did not hold and both iOS-ticked cross-family rows (cross-family meaning a project ticking two or more of desktop, mobile, web) reverted to Flutter as the default, with React Native as the first alternative (the spec's own §2 said this was the rule if the constraint broke); Task 9 `stack-kotlin-multiplatform` — the native-UI-on-both alternative, Kotlin business logic shared into an iOS app with a SwiftUI front, and the migration path from an Android-only Kotlin app to both platforms, so the Android-only row now advises keeping business logic in its own Android-free module from day one to keep that move cheap; Task 10 `stack-react-native` — React Native with Expo, the first alternative on both iOS-ticked rows, one React ecosystem spanning phones and a real React-DOM website at the cost of no maintained Linux desktop target and Windows/macOS as separate bare projects; Task 11 `stack-web` — the web-only row's default is decided as React (Vite, TypeScript) + FastAPI, SQLite via SQLModel; Task 12 the cross-family comparison — both cross-family rows stand on Flutter, the only stack whose every targeted platform its own vendor rates Supported/Stable. Two live sources overturned what the spec expected going in, and the shipped skills follow the sources, not the expectation: Unity 6.6's own docs recommend uGUI at runtime with UI Toolkit as the alternative (the spec assumed the reverse), and kotlinlang.org rates Compose Multiplatform's iOS target Stable. Three rows are stubs, by direflail's call on 2026-09-12: Java on Android and Objective-C on iOS (existing codebases only, never a new one) and Godot's web export (not researched). Java + Spring + JavaFX and C# / .NET remain listed as desktop alternatives but are not researched, per direflail: "likely we'll stick with python as default and never use these ... but i still want them as alternatives." What stays parked, per the spec's §6: Docker, observability (Grafana/Prometheus/Loki), and external databases; signing up for the Apple Developer Program and Google Play Console belongs in a session centred on a real first app, not here; Android SDK/Studio/emulator setup was already covered in `stack-android-native` before this spec.

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

## #6: Per-language manifest version detection/sync for /orc-version — deferred, same reasoning as #4 (PARTIALLY ADDRESSED 2026-09-07 — still open for the formats it names)

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

**Partially addressed by v8 (2026-09-07), and deliberately NOT closed.** v8's `/orc-release`
work built the mechanism this entry describes — real per-format read/write handlers in
`skills/orc-release/scripts/orc_release/versionfiles.py`, detection of which version-holding
files a project actually has, consistency verification across all of them, and rollback — and it
followed this entry's own "one format at a time" reasoning exactly rather than overriding it.

**But none of the three formats this entry names shipped.** v8 implemented `pyproject.toml` and
`debian/changelog` (plus the pre-existing `.claude-plugin/plugin.json` / `marketplace.json`),
because those are the formats real projects here use today — Orcshot's release needed them. `#6`
was raised about `pom.xml`, `package.json` and `Cargo.toml`, and not one of those has a handler.
v8's own `CHANGELOG.md` entry originally claimed "Closes BACKLOG #6"; that claim was wrong and
has been corrected to say what actually shipped. Recording that here rather than quietly deleting
it: the mechanism landing is not the same as the ask landing.

**What remains open, concretely:** add a handler for `package.json`, `Cargo.toml`, or `pom.xml`
when a real project here needs one. The cost is now much lower than when this entry was written —
`versionfiles.py` is the single place that owns version-setting, so a new format is one
read/write pair plus its entry in `KNOWN_FORMATS`, not a new mechanism. The first-touch
"suggest a starting version from what's already there" half of the original ask is also still
unbuilt.

## #7: Distribution-channel download/install metrics — carried over from Orcshot #186, direflail wants Orclab to own this eventually (PARTIALLY ADDRESSED 2026-09-10 — Launchpad and Flathub confirmed, Snap blocked until a snap exists)

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

**Launchpad's capability confirmed live, 2026-09-08 — it does count PPA downloads.** The entry
above framed this as a known Launchpad gap that might not exist at all. That framing was wrong,
and it is the reason this was left unresearched for two days. Launchpad's public API exposes a
real per-binary-publication download counter, anonymously, no auth and no credentials file:

```bash
curl -sS "https://api.launchpad.net/1.0/~<owner>/+archive/ubuntu/<ppa>?ws.op=getPublishedBinaries"
# then, per entry in that result:
curl -sS "<entry.self_link>?ws.op=getDownloadCount"
```

Run against the real `ppa:artificialorctelligence/orcshot`: 82 binary publications, **90 downloads
in total**, all of it on `0.1.1-2` and `0.1.1-3`; `0.2.0` and `0.3.0` were at zero. A
`getDailyDownloadTotals` operation exists on the same object and returned `{}` for a zero-count
publication — real, but not yet seen returning data.

**Two caveats that shape what the number means, both found in that same run**, and both worth
carrying into whatever gets built rather than presenting a bare total as if it were users:
- The count is **per binary publication** — one record per (package, version, series,
  architecture). That is not double counting: a 24.04 user really does fetch the `noble`
  publication and a 26.04 user the `resolute` one, so summing across series is correct. It does
  mean there is no single "downloads for this PPA" number to read; you have to list every
  publication and ask each one, ~75 HTTP round trips for a PPA this small.
- Every architecture within a series read **identically** — `0.1.1-3` is exactly 4 on `amd64`,
  and also 4 on `s390x`, `riscv64`, `i386`, `armhf`, `ppc64el`, `arm64`. Orcshot has no plausible
  s390x users, and a real user population does not distribute itself uniformly across seven
  architectures. That is something walking the archive index, not people. So the honest reading
  of "90" is closer to *a handful of automated passes over two versions* than to 90 anyone. The
  counter is real; what it counts is fetches of the `.deb`. This caveat is printed as part of the
  tool's own output rather than left in documentation, because a bare total invites exactly the
  misreading this bullet had to correct once already.

**Still genuinely unverified:** `snapcraft metrics` and Flathub's stats API. Not for lack of
trying — Orcshot has never been onboarded to either (its own `channels.yaml` records both as
action-less leaves, confirmed live 2026-09-07: `snap info orcshot` finds no such snap, and both
the Flathub API and `flathub/org.orcshot.Orcshot` 404). There is no real published project to
check them against yet, so these stay unverified until a real Snap Store or Flathub publish
exists — see Orcshot's own BACKLOG #198/#197.

**Design settled, same day, and built:** this became `--metrics` on `/orc-publish` rather than a
component of its own. The reasoning is in the "Why this belongs in Orclab" paragraph above, taken
one step further — the config that declares *where a project publishes* is the same config that
says where to go count, so the metrics read is a second command key (`metrics:`) on the same
`channels.yaml` leaf that already carries `action:`. No new tree, no new selection syntax, no new
config file. See **#18**, whose proposed `status:` key is the identical shape against the same
leaves; that entry stays open, but its mechanism is now a two-line change rather than a design.

**Flathub confirmed live, 2026-09-10 — and it never needed Orcshot to be on Flathub.** The
paragraph above said both remaining rows "stay unverified until a real Snap Store or Flathub
publish exists." Half of that was wrong, and it kept this entry parked for two more days for the
same reason the Launchpad half was: the check was assumed to be blocked instead of tried.
Flathub's stats endpoint is public and takes any app id, so it was checked against a real
published app instead:

```bash
curl -fsS https://flathub.org/api/v2/stats/org.gimp.GIMP
```

returns 200 with `installs_total` (3,816,552), `installs_last_month`, `installs_last_7_days`,
180 days of `installs_per_day` and ~250 `installs_per_country` figures; the same call for
`org.orcshot.Orcshot` returns 404, and `-f` turns that into a failed leaf rather than a parsed
error body. The shape is `StatsResultApp` in Flathub's own live `openapi.json`, which is where
the field names come from. The `/orc-publish` table row now carries a one-liner that prints the
three totals — the raw body is far too much to put in front of someone who asked for one number.
The schema does not say whether `installs` includes updates, so the count carries the same
"fetches, not people" caveat the PPA count does.

**Snap is not unverified; it is blocked, and the block is a fact about the Store, not about
Orclab.** The live snapcraft reference (`ubuntu.com/docs/snapcraft/9/reference/metrics/`,
2026-09-10) lists the real metric names — `weekly_installed_base_by_operating_system` is one of
twelve, all real — and the how-to says outright: *"As snap metrics are confidential, only a
snap's author can access them."* The Store API demands a `package_metrics` permission on a
logged-in account, and `snapcraft whoami` on this machine has no credentials. So the command's
options and output shape are checked, but it cannot produce output until someone owns a snap.
That is Orcshot's own BACKLOG #198 (publish to the Snap Store), a real account-gated action that
belongs in a session centred on Orcshot, per `CLAUDE.md`'s dogfooding rule. When that snap
exists, running the row once and correcting the table's "Never run" is the whole remaining work
here; there is no Orclab-side design left in this entry.

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

## #10: Solidify /orc-publish's testing strategy beyond what the spec settles for v7 (RESOLVED 2026-09-07)

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

**Resolved 2026-09-07.** Asked, as this entry's own next step required, rather than guessing.
direflail scoped it to the second of the two candidates above — the synthetic-tree fixture
question — and the first was already closed by events: the resolver's unit tests now assert on
`desktop.python.linux.ppa.noble`, five segments, which is exactly Orcshot's real tree depth.

**The fixture question resolves as "no change," and the reason is the interesting part: the
premise didn't hold.** The concern was three inline copies of a synthetic tree drifting apart.
Looking at them, they are not copies — they are deliberately different trees testing different
properties: Scenario 23/24's `desktop.python.linux.{snap,flatpak}` (resolution, the dry-run gate,
execution), Scenario 42's `test.{hangs,snap}` (timeout reporting and an action-less leaf), and
Scenario 43's `test.compound` (the process-group kill). There is no shared tree to extract.
Scenario 24 already reuses 23's by reference rather than copying it. A single fixture would mean
one tree serving all three, coupling unrelated scenarios so a change made for one silently alters
the others — and these are hand-run by a person reading the document, where the YAML sitting
beside its own expectation is the point rather than an accident.

**The audit did find a real gap in the same strategy, and it is the opposite shape from the one
this entry guessed at.** The gap is not tree management; it is that unit tests and hand-run
scenarios cover different failure classes, and one class had nothing. #15's fix passed every unit
test both before and after a real defect in it — the captured output was placed mid-sentence,
stranding the stdin hint under the log's last line — because the tests assert substrings and
substrings survive reordering. Only reading the real rendered output caught it. That is precisely
what a `VERIFICATION.md` scenario is for, and no scenario covered it. Added as **Scenario 44**,
which asks the reader to judge the summary as an operator would rather than search it for words.

**So the strategy's two layers hold, with the split sharpened:** unit tests for what is true,
hand-run scenarios for what is *readable* — and a behaviour whose failure mode is presentation
rather than logic needs the second, because the first will pass either way.

## #11: `/orc-publish`'s `execute_plan` has no subprocess timeout — a real hang risk, not yet fixed (RESOLVED 2026-09-07)

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

**Fixed for real (2026-09-07, Orclab v11).** All three decisions this entry asked for before
implementation got real answers, in
`docs/superpowers/specs/2026-09-07-orclab-v11-publish-pipeline-gaps-design.md`:

- **Per-leaf, with a default.** `timeout` is a leaf key; `execute_plan` uses a leaf's own value
  when set, and `--timeout <seconds>` moves the default for a whole run without overriding a leaf
  that deliberately set a tighter one.
- **600 seconds.** Deliberately a "something is wrong" ceiling rather than a performance budget.
  This entry's own objection — that `dput` and a local build script don't share a reasonable
  timeout — is answered by the per-leaf override, not by the default.
- **A distinct `timed out` status**, as this entry anticipated, whose detail names the real limit
  *and* says the action may be waiting on stdin. That last clause exists because
  `capture_output=True` is precisely why a `debsign` prompt is invisible, which is the confusion
  this entry recorded ("it just looks like the command has frozen").

The scope boundary held: nothing here routes around `debsign`'s own interactive behaviour.

**The finding that mattered more than the timeout itself, recorded because the method is worth as
much as the fact.** The plan prescribed `subprocess.run(..., shell=True, timeout=N)`, and that is
not sufficient — mid-branch review caught it, and the human ruled the finding over the plan.
`subprocess.run`'s own timeout kills only the `/bin/sh -c` process it started. A compound action —
which is what a real publish leaf is, `dpkg-buildpackage && debsign && dput` — does its real work
in a *grandchild* of that shell, and killing the shell orphans it. The operator is told `timed
out` while `dput` goes on uploading, and a retry then double-uploads to a public archive. So
`execute_plan` uses `subprocess.Popen(..., start_new_session=True)` with `communicate(timeout=)`
and kills the whole process group, not just the shell.

**Two consequences of that deviation, both found in the final fix round rather than assumed.**
First, the group kill has to fire on *any* exit from `communicate`, not only `TimeoutExpired`: the
same `start_new_session` that makes the group killable also means a terminal Ctrl-C no longer
reaches the action, so a timeout-only handler recreated the identical orphan on interrupt.
Verified both ways under a real SIGINT — in the same process group the grandchild died with the
interrupt; in a new session with a timeout-only handler it survived. Second, with no controlling
terminal `/dev/tty` cannot be opened at all, so a gpg/pinentry passphrase prompt — the very case
this entry was written about — now fails in about a second with a real error rather than hanging
to the limit. That is an improvement, but it is a *behaviour change* this entry's own scope
boundary did not anticipate, so it is named here instead of left to be rediscovered.

## #12: `/orc-publish` models channel fan-out, but a real release is mostly an ordered pipeline — the framework can't yet drive Orcshot's own release (RESOLVED 2026-09-07)

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

**Already closed by v8 (recorded 2026-09-07).** This entry's open design question — "does Orclab
need a pipeline concept — ordered steps, gates/preconditions, and a way to represent a step a
*human* performs — with `/orc-publish` becoming one stage within it" — was answered yes and built
as `/orc-release`. Ordered steps that halt on failure, `**Preconditions:**`, `**Performed by
hand.**`, `**Run:** /some-command` delegation, and a cross-session state cursor all shipped in
v0.8.0. This entry's own "next step" (a fresh brainstorming pass from a complete read of Orcshot's
`RELEASING.md`) is what produced that design.

It is recorded here rather than left ambiguous because v11's brainstorming pass initially treated
this entry as open and nearly re-designed something that already exists. What v11 *did* find was
narrower and genuinely uncovered by v8 — one-time onboarding, honest reporting of a not-yet-usable
channel, and #11's timeout — all three closed in v11.

## #13: v0.7.0 was never tagged either — the same gap as #9, and #9's own mitigation didn't hold (RESOLVED 2026-09-07)

Found 2026-09-07 while direflail challenged whether `/orc-version` was actually a good idea, which
prompted checking how version bumps have really been done rather than assuming. `git tag --list`
showed `v0.3.0` through `v0.6.0` — no `v0.7.0`, despite v7 having shipped, been reviewed, and been
pushed.

**This is the second occurrence of the exact pattern #9 recorded**, and it is worth being blunt
that #9's stated mitigation failed. #9's "next step" read: "Worth remembering during future
plan-writing for any Orclab version-bump task: copy the git-tag step from an existing plan (e.g.
v4's) rather than re-deriving the task from scratch." v7's plan was written after that entry
existed, by the same author, and still omitted the tag step. A note reminding a human (or Claude)
to remember something is not a mechanism.

**The wider finding this surfaced, which matters more than the missing tag:** `/orc-version` has
essentially never been used, including in its own home project. Its Apply flow commits with the
exact message `Bump version to X.Y.Z` and nothing else, and tags automatically as step 4. But the
real bump commits read `orc-publish: SKILL.md, bump to 0.7.0, CHANGELOG, README, VERIFICATION
scenarios` (`0470c26`), `Add Desktop-compatible skill wrappers..., bump to 0.6.0` (`cfbdaee`), and
`Add /orc-git command, bump version to 0.4.0` (`427c62b`) — implementation-plan tasks that edited
the manifests by hand alongside everything else. `1eb34c7`'s message matches `/orc-version`'s
format, but #9 already established that one was manual too (its plan omitted tagging, which
`/orc-version` would have done automatically).

So a component was designed, specced, reviewed and shipped in v3, and then every subsequent release
bypassed it. Both missing tags are the direct, mechanical cost of that.

**Fixed for real:** `v0.7.0` tagged at `ecad9d3` (2026-09-07, local-only per convention) — the
commit where v7's fix rounds completed and the work was declared done. Commits after that point
(`0217e59` onward, including `0ac9541`'s real change to `/orc-publish`'s dry-run output) are
unreleased work accumulating toward the next version, not part of 0.7.0.

**Why no further mitigation is being written here:** the real fix is already in flight. v8's design
(`docs/superpowers/specs/2026-09-07-orclab-v8-orc-release-design.md`) makes `/orc-version` the one
place that owns version-setting, with `/orc-release` delegating to it — so tagging stops being
something a plan author has to remember and becomes something the mechanism does. This entry exists
as the evidence for that decision, not as a request for another reminder-style note. If v8 ships
and a third version still goes untagged, that is a real signal the approach is wrong.

## #14: `claude plugin validate --strict` fails on Orclab's own CLAUDE.md — settle before writing a RELEASING.md (RESOLVED 2026-09-07)

Found 2026-09-07 while confirming that a `metadata:` marker in SKILL.md frontmatter is accepted
(it is — see `CLAUDE.md`). `claude plugin validate` emits exactly one warning against Orclab:

```
❯ root: CLAUDE.md at the plugin root is not loaded as project context. To ship context with your
  plugin, use a skill (skills/<name>/SKILL.md) instead.
```

Plain `validate` passes with the warning. `--strict` promotes warnings to errors and **fails,
exit 1, on that warning alone** — confirmed live.

**The warning is accurate, and the current layout is still correct.** Consumers who install
Orclab genuinely never see `CLAUDE.md`; it is not injected into their sessions. That is exactly
what `CLAUDE.md` says about itself ("not something Orclab ships to consuming projects"), and it
still does its real job — inside the orclab repo it is that project's own `CLAUDE.md` and loads
normally. This is a false positive against intent, not a defect to fix.

**Two ways it bites later, which is why it's tracked rather than ignored:**
- `plugin validate` appears nowhere in this repo today, and Orclab has no `RELEASING.md` of its
  own — despite shipping `/orc-release`, which drives other projects' release processes. The
  moment someone writes one and adds the obvious `claude plugin validate --strict` gate, Orclab
  fails its own release gate on a file that is deliberately, correctly there. A landmine planted
  ahead of the process that will step on it.
- The warning recommends the wrong remedy for this case. "Use a skill instead" would move
  Orclab's internal development guidance into a shipped skill, pushing it into every consuming
  project's context — precisely the boundary `CLAUDE.md` draws against. A future session with
  less context will read a helpful-sounding suggestion and do the wrong thing.

**Decision needed when picked up:** whether Orclab's eventual `RELEASING.md` runs `plugin
validate` without `--strict`, waives this one warning explicitly, or skips validate altogether.
Not urgent — nothing runs it today — but it has to be settled *before* the release process is
written, not after it fails.

**Correction, layered on 2026-09-07 (v11's final fix round): the bare command does not emit that
warning at all, and the reason makes this entry more urgent, not less.** This entry says "`claude
plugin validate` emits exactly one warning against Orclab." In this repo's dual-manifest layout
that is not what the bare command does. Reproduced independently, twice:

```
❯ claude plugin validate .
Validating marketplace manifest: .../.claude-plugin/marketplace.json
✔ Validation passed

❯ claude plugin validate .claude-plugin/plugin.json
Validating plugin manifest: .../.claude-plugin/plugin.json
Validating plugin: .../CLAUDE.md
⚠ Found 1 warning: ❯ root: CLAUDE.md at the plugin root is not loaded as project context...
✔ Validation passed with warnings
```

Given a directory holding both manifests, it validates the **marketplace** one and stops. The
warning this entry describes appears only when `plugin.json` is named explicitly.

**Why this belongs to `CLAUDE.md`'s negative-control argument, not just to accuracy.** A
`RELEASING.md` gate running the bare `claude plugin validate .` would check the marketplace
manifest's structure and *nothing whatsoever* about the plugin, its skills, or the frontmatter
that carries this project's load-bearing behaviour — and it would print `✔ Validation passed`
either way. That is precisely what `CLAUDE.md`'s own negative-control section rules out: a check
that passes for both the right and the wrong input is not a check. The landmine the two bullets
above describe is real, but the worse outcome is the opposite one — a green gate that never looked
at the plugin, and a release process that believes it verified something.

So the decision this entry defers now has a third input: whichever way `--strict` goes, the gate
has to name `.claude-plugin/plugin.json` explicitly, or it validates the wrong file.

**Resolved 2026-09-07 — the decision is made, and it is written where it will actually be found.**
direflail's call: the gate is `claude plugin validate .claude-plugin/plugin.json`, naming the file
explicitly, **without** `--strict`.

- **Name the file** because the bare form validates the marketplace manifest and stops. A gate
  that prints `✔ Validation passed` without ever looking at the plugin is green for the right
  input and the wrong one alike — this entry's own correction above, in live form.
- **No `--strict`** because it promotes to an error the single warning Orclab gets, on a layout
  that is deliberate and correct. Failing a release on `CLAUDE.md` doing exactly its job is the
  landmine the second bullet above predicted, and the warning's suggested remedy would push
  Orclab's internal guidance into every consuming project's context.

**The resolution is recorded in `CLAUDE.md`'s "`claude plugin validate` does not check skill
frontmatter" section, not only here.** A resolved BACKLOG entry is not where someone writing a
release process looks; that section is about this exact tool and is on the minimum search surface.
Leaving the decision only in the backlog would have reproduced the failure this entry is about —
a correct answer nobody finds at the moment it matters.

**What is not resolved, deliberately:** Orclab still has no `RELEASING.md`. This entry asked only
for the decision to be settled *before* one is written, and it now is. Writing that document is
separate work, and whoever does it inherits a decision instead of a landmine.


## #15: a timed-out `/orc-publish` leaf says "no output captured" when output was in fact captured (RESOLVED 2026-09-07)

Found 2026-09-07 during v11's final fix round, checking a code comment rather than trusting it. A
timed-out leaf reports:

```
<path>: timed out (timed out after 600s - no output captured, the action may be waiting on stdin)
```

`subprocess.TimeoutExpired` does carry whatever was captured before the timeout. Verified
directly: after `echo hello; sleep 5` timed out at 1s, `TimeoutExpired.stdout` was `b'hello\n'` —
present, and **undecoded bytes** despite `text=True`, because the exception is built from the raw
buffers before the text wrapper ever sees them.

**Why this matters more than a stray adjective.** The flagship action is
`dpkg-buildpackage && debsign && dput` — a wall of build output, and *then* a hang. That is
precisely the output-then-hang shape where the operator is told nothing was captured while the
build log that would say how far it got is discarded. The other half of the detail line ("may be
waiting on stdin") stays true and stays useful; it is only the "no output captured" clause that is
sometimes a lie.

**Deliberately deferred, not overlooked.** Surfacing partial output was explicitly ruled out of
v11's fix round by direflail. The in-code comment at the `except subprocess.TimeoutExpired` handler
in `skills/orc-publish/scripts/orc_publish/cli.py` was corrected to say what is actually true — the
output exists and is not surfaced yet — rather than the false claim that capture never completed.
`docs/superpowers/specs/2026-09-07-orclab-v11-publish-pipeline-gaps-design.md` carries the same
correction against its own hardcoded example.

**Next step, when picked up:** surface `e.stdout`/`e.stderr` in the timeout detail the same way the
`failed` branch surfaces `e.stderr`, and reword the clause so it is honest when there is genuinely
nothing (a leaf that hung before printing anything is a real and different signal). It needs a
`.decode()` — the bytes are not decoded for you on this path, and the `failed` branch's strings
are, so the two branches cannot share the same handling as written. One test per shape: output
then hang, and hang with no output.

**Resolved 2026-09-07.** The timeout detail now surfaces what was captured, decoded defensively
for both `bytes` and `str` and tolerating a `None` stream. Both shapes were checked against a real
run, not just against assertions:

```
a: timed out (timed out after 1s - the action may be waiting on stdin. Output captured before it hung:
build-line-1
build-line-2
build-line-3)

b: timed out (timed out after 1s - no output captured, the action may be waiting on stdin)
```

"no output captured" survives, correctly, as the honest report for the second shape — a leaf that
hung before printing anything is a real and different signal, exactly as this entry anticipated.

**One thing the entry did not anticipate, found only by looking at real output.** The first
implementation put the captured output in the middle of the sentence, leaving
`build-line-3, the action may be waiting on stdin` — the stdin hint stranded under the last line
of the log, reading as part of it, and with a real `dpkg-buildpackage` capture it would sit
hundreds of lines below the fold. The clause order is now inverted: the actionable sentence first,
the dump last. **Every test passed both before and after that fix**, because they assert
substrings and substrings survive reordering, so a test now asserts the ordering itself
(`detail.index("waiting on stdin") < detail.index("hello")`). Rendering is not covered by
asserting that the right words are present somewhere.


## #16: the process-group-kill tests can't tell "killed" from "waited out" — narrowed by two live controls, not closed (RESOLVED 2026-09-07)

Found 2026-09-07 reviewing the two tests written for BACKLOG #11's fix,
`test_execute_plan_kills_the_whole_process_group_on_timeout` and
`test_execute_plan_kills_the_whole_process_group_on_interrupt` in
`skills/orc-publish/scripts/tests/test_cli.py`, together with `grandchild_action` and
`assert_process_gone` that they share. The real gap: nothing bounds the wall clock of either test,
and the `except BaseException:` handler in `execute_plan` (`skills/orc-publish/scripts/orc_publish/cli.py`)
calls `proc.wait()` after the kill attempt — a call that blocks until the child tree actually
exits, kill or no kill. So a test that never kills anything can still pass, by blocking on
`proc.wait()` until the grandchild's own sleep runs out on its own, and reporting the same "timed
out" / `KeyboardInterrupt`-raised outcome the real fix produces.

**Both controls were actually run (2026-09-07), and the real results are the finding — not the
theory of what they'd probably show:**

- **Control A** — swap `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` for `proc.kill()`, i.e.
  the real pre-fix `subprocess.run` behavior, the actual regression these tests exist to catch:
  **both tests fail**, with `Failed: grandchild <pid> survived - its process group was not
  killed`, in `2 failed in 11.16s`.
- **Control B** — delete the kill line entirely, leaving only `proc.wait()`: **both tests pass**,
  but in `60.11s` instead of the usual ~1.2s — the outer shell waits on its own grandchild, and
  `proc.wait()` waits on the outer shell, so by the time `assert_process_gone` runs, the grandchild
  is already gone on its own.

**So the tests are not vacuous.** They genuinely catch the regression they were written for —
control A proves that plainly, and this matters more than the gap below, because a reader who only
sees the gap might reasonably conclude the tests should be deleted. They shouldn't. The real gap is
narrower: a 50x slowdown is the *only* signal separating a real kill (control A's failure mode
inverted, i.e. the fix working, ~1.2s) from a wait-it-out pass (control B, ~60s) — and nothing in
either test asserts on wall-clock time, so nothing currently fails if a future change quietly
regresses the kill back to a no-op that happens to still finish inside CI's patience.

**Scope boundary:** this is not a claim that the fix in BACKLOG #11 is broken — control A shows the
current code does perform the group kill. This is only about the tests' own ability to *notice* if
that ever stops being true.

**Two candidate fixes, not chosen between:** assert a wall-clock ceiling on `execute_plan`'s return
(it should come back at about the leaf's `timeout`, not at the grandchild's full 30s sleep — a
loose bound like "under 5s" would separate the two cases cleanly without being a flaky tight
bound); or lengthen the grandchild's sleep relative to `assert_process_gone`'s poll window (already
5s) enough that a wait-it-out pass becomes wall-clock-impractical for a test suite to tolerate,
forcing a real kill to be the only way to pass at all.

**How this was found is as much the point as what was found.** An implementer ran control B, saw
both tests pass, and reported that the tests do not detect a broken kill. That inference was wrong
on its own terms: deleting the kill line entirely is not the regression these tests exist to catch
— the real pre-fix behavior was a *child-only* kill (`subprocess.run`'s own timeout, which reaches
only the `/bin/sh -c` process), not *no* kill at all. Testing "no kill" tests a scenario no real
regression produces; only control A — swapping in the actual pre-fix kill call — tests the real
regression. Two earlier agents had separately claimed these tests were verified against negative
controls, and a third claimed the opposite (that they were vacuous); only actually running the
correct control resolved the disagreement. This repo's own `CLAUDE.md` already makes the point that
a check which passes for both the right and the wrong input is not a check (the `claude plugin
validate` frontmatter finding) — this is the same lesson from the other direction: **a negative
control that removes the wrong thing proves nothing either**, and can produce a confident, wrong
conclusion in exactly the shape this one did.

**Resolved 2026-09-07 — candidate one, the wall-clock ceiling.** direflail chose it over the
sleep-tuning alternative, on the reasoning that it asserts the actual property (the kill happened,
promptly) rather than tuning two sleeps into a gap a slow CI box could still close — the same
timing-race shape this file's own tests had just been cleaned of.

`KILL_CEILING_SECONDS = 10` and `assert_returned_promptly()` in
`skills/orc-publish/scripts/tests/test_cli.py`; both process-group tests now time `execute_plan`
and assert it returned inside that ceiling. Ten sits far above the real ~1.2s and far below the
30s a wait-it-out takes, so it is not a race on a loaded machine.

**Both controls were re-run against the new assertion, since a fix to a test is worthless unless
the test now fails where it used to pass:**

- **Control B** (delete the kill entirely, leave `proc.wait()`) — the one that previously passed in
  60s and proved nothing: now **fails**, `the interrupted execute_plan took 30.0s, over the 10s
  ceiling - the process group was probably not killed, and this only finished because the
  grandchild's own sleep ran out`. `2 failed in 60.14s`.
- **Control A** (child-only `proc.kill()`, the real pre-fix regression): still **fails**, `2 failed
  in 11.16s` — the existing survival assertion catches it first, as before.

So the tests now fail under both a real regression and the degenerate no-kill case, and the
message names the actual cause rather than leaving a reader to infer it from a slow run.

**Worth keeping from the same day, one entry over:** #15's fix passed every test both before and
after a real defect in it, because the tests asserted substrings and the defect was ordering. The
lesson generalises to this entry — asserting that the right things are *true* is not the same as
asserting they are true *for the right reason*, and a control that used to pass is the cheapest
way to tell the difference.

## #17: what belongs in a `/orc-package` component, and what belongs elsewhere — scope undecided (RESOLVED 2026-09-10)

Raised by direflail 2026-09-07, immediately after automating Orcshot's Launchpad
noble→resolute copy: "this whole process is going to have to be done for any new project... i'm
thinking this should be part of the first-time setup stuff for ppa." Then, asked whether it should
be PPA-only: "it definitely needs to be broader (what if i make a mobile app? cross platform
windows/linux app?). but i'm not sure what belongs HERE versus elsewhere yet."

**Confirmed by search, not assumed:** nothing in Orclab covers standing up a distribution channel
today. Searched the minimum surface (`skills/*/SKILL.md`, `CLAUDE.md`, `BACKLOG.md`,
`hooks/scripts/`, `skills/*/scripts/`). The three hits for PPA/dput/Launchpad are all incidental —
`release-checklist` uses "already published to the PPA" as an example of a good precondition and
explicitly warns against assuming `dpkg-buildpackage`-style steps belong everywhere; `orc-publish`
mentions `debsign` in a timeout note; `orc-release` uses `dput` as its example of a risky command.
None of them tells you how to make a channel exist.

**"Packaging" is currently four different things wearing one word.** Naming them is most of the
scoping problem:

| | Thing | What it was for the PPA |
|---|---|---|
| 1 | Produce the artifact | `debian/` layout, `dpkg-buildpackage` |
| 2 | Stand up the destination | create the PPA on Launchpad |
| 3 | Credentials for it | GPG key registered to Launchpad, `~/.dput.cf`, the OAuth authorization |
| 4 | Wire it into Orclab | `channels.yaml`, `distro.yaml`, `RELEASING.md` steps |

The 2026-09-07 work did 2, 3 and 4. It never touched 1 — Orcshot's `debian/` already existed.

**The observation a design should start from: 2, 3 and 4 repeat across every channel; 1 does not.**
Every distribution channel has the same shape — a one-time registration, a credential mechanism, a
per-release publish action, and often an asynchronous review (see **#18**). The mechanisms differ
wildly between a PPA, the Snap Store, Flathub, npm, PyPI, the App Store, Play Console and winget;
the shape does not. That is why the `**One-time setup:**` marker shipped in v0.11.0 fitted the PPA
copy on its first real use without having been written for it. Producing the artifact is the
opposite: `debian/control`, an Android keystore and an `.msix` manifest share essentially nothing.

**A supporting argument already in the code:** `/orc-publish`'s tree is already channel-shaped —
`desktop.python.linux.ppa.noble` is component/platform/os/channel/series. A `/orc-package` scoped
to channels would *populate* that tree; `/orc-publish` executes it. A mobile app becomes
`mobile.<lang>.android.play`; a cross-platform desktop app grows `desktop.<lang>.windows.winget`
beside its Linux channels. Same tree, same fan-out, same `--for` queries, no new structure.

**A candidate cleave, explicitly not a decision:** `/orc-package` owns channels (2, 3, 4), not
build systems. Producing the artifact is closer to `/orc-code`'s territory, which already owns
per-language and per-stack defaults — **#4** is the open entry for exactly that. Running the
release stays `/orc-release`'s.

**What is genuinely unknown, and must not be assumed away:** that shape is proven for exactly one
channel. Snap and Flathub are researched but unbuilt (Orcshot **#198**). The App Store and Play
Console add binary signing and multi-day human review, and whether "one-time setup plus a
per-release action" survives contact with App Store Connect has not been checked at all.

**Next step, when picked up:** a `superpowers:brainstorming` pass (Architectural — new component,
new command surface, and a taxonomy question underneath it), using the 2026-09-07 PPA walkthrough
as the one worked example that actually exists.

**An open disagreement to settle in that pass, not before it.** The Orcshot 0.3.0 handover proposes
that Orclab own "the series-copy mechanism generalised from the existing script" — i.e. a Launchpad
API client living in the framework. The position taken while building that script was the opposite:
Orclab ships the mechanism, projects ship their actions, which is the same boundary that keeps
`dput` in Orcshot's own `channels.yaml` rather than in `/orc-publish`. Generalizing a
forge-specific client into Orclab would make the framework know about one particular hosting
provider. Both positions are defensible; the handover's is the stronger one if several projects
ever publish to Launchpad, and the weaker one if they do not. What is *not* in dispute is which
properties any implementation must keep, all proven live: a `--check` mode that answers "has the
one-time authorization happened" without triggering it, a `--dry-run` that authenticates
anonymously so preconditions are verifiable on an unconfigured machine, refusal to act when the
source is not `Published` or has no built binaries, and a credentials file at `chmod 0600` that is
never printed. Two questions were deliberately left unanswered
when this was raised: whether the component dispatches per channel (`/orc-package ppa`) or is
PPA-only, and whether it writes the config and `RELEASING.md` steps itself or only instructs.
Answer **#18** first or alongside — a channel that isn't finished when the command exits changes
what "set up a channel" even means.

**Resolved 2026-09-10 — v15 shipped.** The cleave the entry called "a candidate, explicitly not a
decision" is the one taken: `/orc-package` owns standing up the channel (registration, credentials,
wiring into the recipe) and not producing the artifact, which stays with `/orc-code` and **#4**.
The four things wearing one word are now three places: the artifact is `/orc-code`'s, the channel
is an *ingredient* `/orc-package` applies, the release is `/orc-release`'s. The parked disagreement
about a Launchpad client is settled by the ingredient carrying the copy script as a *template*
instantiated into the project — Orclab ships the knowledge, the project owns the code.

One correction found while planning, recorded in the spec: the PPA has no machine-local config.
`~/.dput.cf` was named as the worked example and was never needed; `dput` resolves `ppa:` through
`/etc/dput.cf`. The shape is still proven for exactly one channel, and the first capture — snap,
per Orcshot #198 — is where it gets tested against a second.

## #18: a publish can be accepted without being done — nothing models the wait, or how to check (RESOLVED 2026-09-09)

Raised by direflail 2026-09-07, while scoping **#17**: "we're probably waiting for multi-day
(probably) human review and be able to check status on where those are at (either via api or by
giving links to the pages we can check)."

**The gap:** `/orc-publish` reports a leaf as `success` when its action exits 0. For several real
channels, exit 0 means *accepted*, not *published* — and the difference is hours to days.

| Channel | What exit 0 actually means | How the real state is checkable |
|---|---|---|
| PPA upload (`dput`) | queued; Launchpad's build farm has not built it | Launchpad API — `getPublishedSources` / `getPublishedBinaries`, confirmed live 2026-09-07 |
| PPA series copy | requested; files can take up to 20 minutes to appear | same API |
| Flathub first submission | a pull request opened, reviewed by people over days | GitHub PR status |
| Snap Store | uploaded; some confinements need Canonical review | `snapcraft status` / the developer dashboard |
| App Store / Play | submitted for multi-day human review | App Store Connect / Play Console APIs |

**This is already being worked around by hand, which is the tell that it belongs in the
framework.** Orcshot's own `ppa.resolute` leaf carries this as a prose `issues:` note: *"The copy
is asynchronous... A green exit means the copy was accepted, not that it has landed."* That is the
same pattern the `**One-time setup:**` marker came from — Orcshot's `RELEASING.md` had invented it
inline twice, inconsistently, before it became a real convention. A per-project prose note is how a
missing mechanism announces itself.

**Two distinct forms a status check takes**, and a design has to allow both rather than assuming
the first: a **programmatic** check (a command or API call that returns the real state — the
Launchpad one is proven, and `scripts/ppa-copy-series.py`'s own precondition check is already
exactly this), and a **link** to a page a human reads when no API exists or none is worth wiring.
Both are legitimate; only the first can gate a later step automatically.

**Why this is not just an `/orc-publish` concern:** it interacts with `/orc-release`, where a step
may not be completable in the session that started it — Orcshot's real release already has this
shape, since the resolute copy cannot run until the noble build has *succeeded*, not merely been
accepted. `/orc-release`'s state cursor already survives across sessions, so the pieces may
largely exist; what is missing is a way for a channel to declare "here is how you find out whether
this actually landed."

**Scope boundary:** this is about *observing* an asynchronous publish, not about polling or waiting
on one. Nothing here proposes that Orclab block, retry, or sleep — inventing a polling loop for a
multi-day human review would be worse than the prose note it replaces.

**Next step, when picked up:** decide whether this is a new leaf field in `channels.yaml` (a
`status:` command and/or URL alongside `action:`), a `release-checklist` marker for a step that
completes later, or both. Answer it alongside **#17**, whose "stand up a channel" question is
incomplete without it.

**Corroborated independently, and with a live incident, 2026-09-07.** The session driving
Orcshot's `0.3.0` release reached the same finding from the other direction — not "how do I check
status" but "this step cannot be tracked honestly." Orcshot's step 6 was three operations with a
remote wait in the middle: `dpkg-buildpackage`/`debsign`/`dput` (local, seconds), **Launchpad's
build farm building the upload (remote, ~28 minutes on that release)**, then the copy to
`resolute`, valid only after the build succeeded. `/orc-release` has one completion state per step,
so `run.py complete 6` was called while the copy had not happened and *could not* for another half
hour. **The release was recorded as further along than it was**, and only a manual note to the user
kept the record straight.

That adds a third option, cheaper than either above and worth weighing first because it needs no
code at all: **a documented convention that "wait for X, then do Y" must be split into two numbered
steps.** Orcshot's own document already renumbered to do exactly that (upload is step 6, copy is
step 7), which is why the same release would now be trackable. A `release-checklist` rule would
generalize it.

Also worth recording from that release: `dput` printing `Successfully uploaded packages.` says
nothing about whether the package *built*. The build farm's result is a separate gate from the
upload's success, which is this entry's whole point stated in the most concrete possible form.

**The mechanism half of this got built for a different reason, 2026-09-08 (see #7).** `/orc-publish`
now takes `--metrics`, which runs a leaf's `metrics:` command instead of its `action:` — the same
selection, timeout, process-group kill and capture path, parameterized by which key holds the
command. That is exactly the shape this entry's "next step" proposes for `status:`: adding it is
now a two-line change (`tree.LEAF_KEYS`, and `cli.NOT_SET`, which is where the per-key wording for
an unset command lives), not a design.

What that does **not** settle is everything this entry is actually about: whether a `status:`
command is even the right answer versus a link a human reads, versus the no-code option of
splitting "wait for X, then do Y" into two numbered release steps. The cheap mechanism arriving
first is a reason to be more careful here, not less — it makes the wrong answer as easy to build
as the right one. Decide it alongside **#17** as this entry already says.

**Resolved 2026-09-09 (Orclab v13) — two of the three candidate answers shipped, deliberately not
the third.** This entry's own "next step" named three options: a `status:`-shaped leaf field, a
`release-checklist` marker for a step that completes later, or the no-code convention of splitting
"wait for X, then do Y" into two numbered steps. The answer is the field and the convention —
`confirm:` on a leaf, plus a new `release-checklist` rule generalizing exactly the split Orcshot's
own `0.3.0` document already made by hand. Neither a new `/orc-release` marker nor a polling loop
was built; the scope boundary this entry stated ("not about polling or waiting on one") held.

`confirm:` is a mapping of `command` and/or `url` — the same two forms this entry called out as
both legitimate (a programmatic check; a link a human reads) — and a leaf declaring it reports
`accepted`, not `success`, on a zero-exit action. `--confirm` is a new, separate mode that runs a
leaf's `confirm.command` and reports `confirmed` / `not confirmed` / `needs a human` / `no confirm
declared`; it never runs `action:`. Documented in `skills/orc-publish/SKILL.md`. The
`release-checklist` addition ("a step that waits on external state must be two steps") and its
worked example (`**Preconditions:** ... Check with /orc-publish --confirm <path>`) are in
`skills/release-checklist/SKILL.md`, citing the same `0.3.0` incident this entry already recorded.
Verified by the existing `orc-publish` unit test suite (149 passing) and a new `VERIFICATION.md`
scenario (#47) asking an operator to read a real `accepted` line, action output included, and
confirm it reads as "not finished" rather than as success — exactly the failure mode a substring
assertion (see #15) cannot catch.

**This entry's own warning about the cheap mechanism is worth confirming held, not just repeating
it.** `--metrics` arrived first and is the identical shape (a second command key on the same leaf,
reusing selection/timeout/capture) this entry's "next step" once proposed for `status:` — and
flagged as a reason to be *more* careful, since the wrong answer had become as easy to build as
the right one. `confirm:` deliberately does not reuse that shape: it is a mapping with two
sub-fields and its own refusal (`confirm_error`, for a `confirm:` naming neither `command` nor
`url`), not a bare command string, and it reports four statuses of its own rather than the
three-state `success`/`failed`/`not attempted` the `action:`/`metrics:` path shares. The cheap
shape was available and was not taken.

**#17 is not resolved by this, and is not touched here.** This entry told whoever picked it up to
decide alongside #17, whose "stand up a channel" design still has two open questions of its own
(dispatch shape, whether it writes config or only instructs) that this work does not answer. What
does change is that #17's own ingredient shape no longer depends on a field that doesn't exist yet
— `confirm:` is now real, built, and documented, so a future `/orc-package` design can assume it
rather than design around its absence. #17 stays open.

## #19: `/orc-release`'s `**Run:**` marker silently drops its arguments (RESOLVED 2026-09-08)

Found 2026-09-07 while considering whether Orcshot's `RELEASING.md` step 11 should delegate the
GitHub Release to a command. The delegation marker is parsed by
`skills/orc-release/scripts/orc_release/steps.py`:

```python
_DELEGATES = re.compile(r"\*\*Run:\*\*\s*(/[\w-]+)", re.IGNORECASE)
```

It captures the command name and nothing else. Checked directly rather than inferred from reading
the pattern:

```
'**Run:** /orc-publish desktop.python.linux.ppa.resolute' -> delegates_to = '/orc-publish'
'**Run:** /orc-version release'                           -> delegates_to = '/orc-version'
'**Run:** /orc-version release v0.3.0'                    -> delegates_to = '/orc-version'
```

**Two different severities hide in that, and the second is the real finding.** For `/orc-publish`
the lost argument is a *target*: "publish something" instead of "publish `resolute`". Bad, but the
command is still the right command. For `/orc-version` the lost word changes **what the command
does** — `/orc-version` sets a version number, `/orc-version release` pushes a tag and creates a
public GitHub Release. A structured field saying `/orc-version` for a step that cuts a release is
not merely incomplete, it names a different action.

**This already affects a real document.** Orcshot's step 7, written 2026-09-07, is
`**Run:** /orc-publish desktop.python.linux.ppa.resolute` — the channel is being dropped today.

**Why it probably hasn't bitten yet, and why that isn't reassuring.** `/orc-release`'s SKILL.md
has Claude read each step's full body, so the prose carries the argument even when the parsed
field doesn't. The behaviour is likely correct in practice. But a structured field that is
confidently wrong is worse than one that is absent — it is exactly the "check that passes for both
the right and the wrong input" shape `CLAUDE.md` argues against, and the same class of defect as
the heading/body divergence in #12 and the sub-numbered steps now covered in `release-checklist`.

**Fix shape:** widen the capture to take the rest of the line (`(/[\w-]+(?:\s+\S+)*)` or simply
capture to end-of-line and strip), expose it as the delegation's full invocation, and add tests
for a bare command, a command with one argument, and a command with several. Check whether
anything consumes `delegates_to` expecting a bare name before widening it.

**Blocks nothing outright, but see #20** — that entry's proposed step 11 delegation
(`**Run:** /orc-git release`) is the case where the dropped word is most misleading, so fixing
this first makes that change clean.

**Resolved 2026-09-08.** The capture is widened to the rest of the line and stripped:

```python
_DELEGATES = re.compile(r"\*\*Run:\*\*\s*(/[\w-]+.*)", re.IGNORECASE)
```

`.` does not match a newline without `re.DOTALL`, so this stays single-line by construction — which
matters, because `**Preconditions:**` deliberately spans lines and this marker must not start
behaving like it. Verified directly rather than assumed, against the three cases this entry named
plus two it did not:

```
bare         -> '/orc-publish'
one arg      -> '/orc-publish desktop.python.linux.ppa.resolute'
two args     -> '/orc-version release v0.3.0'
trailing ws  -> '/orc-git release'
prose on following lines -> not captured; the next step's own field stays None
```

**The pre-existing bare-command test passed unchanged**, which is the real regression check: it
proves the widening did not over-capture. Confirmed before changing the field's meaning that nothing
branches on `delegates_to` — it is declared on the `Step` dataclass, set once in the parser, and
otherwise only asserted in tests.

`skills/orc-release/SKILL.md` needed no change: its instruction is "Marked **Run: /some-command** →
invoke that command," which was already correct and is now actually served by the parsed field.
Suites green at 102 / 62 / 48.

## #20: where release-adjacent responsibilities live — `/orc-version release` is misplaced (RESOLVED 2026-09-10)

Raised by direflail 2026-09-07, after asking what the difference between `/orc-version release`
and `/orc-release` actually is — a question the current naming does not answer. His own framing:
"that frees up `/orc-version` to JUST be in charge of the version, and `/orc-release` can focus on
the release, delegating to `/orc-version` as needed."

**The diagnosis, sharpened from naming to risk class.** Everything `/orc-version` does is local and
reversible: edit a manifest, write a changelog entry, commit, tag locally (tags stay local by this
project's own convention — see #13). `release` is the single subcommand that pushes to a remote
*and* creates a public artifact. A dangerous verb sheltering under a benign command name is the
part that matters, more than the fact that `/orc-version release` and `/orc-release` read alike.

**One correction that constrains any redesign: it must not move *into* `/orc-release`.** That
skill's first rule is that `RELEASING.md` is the single definition of the steps and it "never
invents a release process." A `/orc-release` that knew how to create GitHub Releases would be
doing something the project's own document never asked for — and would be wrong for every project
that releases to PyPI, an internal deploy, or a Debian archive and nowhere else.

**Proposed destination, agreed in principle but not built: `/orc-git release <tag>`.** `/orc-git`
already owns forge operations (`gh pr checkout`, connecting a repo); `gh release create` is the
same family. The earlier objection — that `/orc-git` has no confirmation gates — was against
bundling a release into `cp` as a chained side effect. As its own explicitly typed subcommand,
invoking it *is* the deliberate act, exactly as `push` already argues for itself.

**How `/orc-release` then reaches it, and why no new mechanism is needed.** direflail's instinct
was that the repository host is "another link in that tree" — the project decides it uses GitHub,
and that delegates to `/orc-git`. That mechanism already exists and it is `RELEASING.md` itself:

```markdown
## 11. Publish the GitHub Release
**Run:** /orc-git release
```

`/orc-release` stays forge-agnostic by construction, because it only follows the document. If a
project moves to GitLab or Codeberg, that line changes and nothing in `/orc-release` does — the
same way step 7 delegates a Launchpad copy to `/orc-publish` without `/orc-release` knowing what
Launchpad is. No `forge.yaml`, no new abstraction. (See **#19** — the delegation marker currently
drops the `release` argument, which is why that should be fixed first.)

**The insight generalizes past the Release step, which nobody had noticed.** Auditing Orcshot's
own process for forge coupling: step 9 (`git push`) is host-agnostic and works anywhere; step 10
is **three `gh run list` calls** and is just as GitHub-specific as step 11. Any real "delegate the
forge" design has to cover CI confirmation too, not only the Release.

**A hard constraint on any answer, confirmed live 2026-09-07:** Orclab itself has **no
`RELEASING.md`, 9 tags, and 0 GitHub Releases**. It is precisely the project that would be
stranded if this capability were reachable only through `/orc-release`, which refuses to run
without that document. Whatever is decided must leave a directly typable path for a project that
tags versions but has no written process.

**A latent problem to settle at the same time, not urgent:** `/orc-git` conflates two things.
`commit`, `push`, `branch` are universal git and work against any host; `repo`, `pr` — and
`release`, if it lands there — are `gh`, GitHub-only. The name says git; half the command is
GitHub. Harmless while GitHub is the only forge in use, and the thing that has to be untangled the
day it isn't.

**An adjacent feature direflail raised, worth building with this rather than after it:** when
`/orc-release` reaches its "pick a version" step, it should *propose* one rather than only asking —
reading the commits since the last tag and saying why ("no breaking changes, four features, so a
minor bump"). Today `/orc-version` takes a number you supply or an explicit `increment
major|minor|point`. The suggestion is a version decision and belongs in `/orc-version`; the
plumbing to reach it from a release already exists (`/orc-release` delegates version-setting with
`--no-commit`).

**Next step, when picked up:** a `superpowers:brainstorming` pass — this moves responsibilities
across three shipped commands and touches naming, so it is not an inline edit. Fix **#19** first
or alongside. Nothing here is urgent: `/orc-version release` works today, and the only real cost
of the status quo is that nobody can tell the two commands apart from their names.

**Resolved 2026-09-10 — v14 shipped, as specced on 2026-09-08 and amended 2026-09-10.**
`/orc-version release` moved outright to `/orc-git release`, with a moved-notice in its old place
that names the new home and stops. `/orc-git` states its two families in its own skill — `commit`,
`push`, `branch`, `switch`, `merge` are git; `repo`, `pr`, `release` are `gh` — and is not renamed.
`/orc-release` did not change: `RELEASING.md`'s `**Run:**` marker was already the forge-agnostic
delegation mechanism, and #19 had made it carry the verb. `/orc-git ci` is a recorded shape, not
a build. `/orc-version` with no arguments now proposes a bump and states the evidence, never
writing until confirmed. Orclab still has no `RELEASING.md` of its own; `/orc-git release` is
directly typable, which is the path this entry said must exist.

## #21: nothing inspects an artifact before it is irreversibly published (RESOLVED 2026-09-08)

Raised 2026-09-07 from a handover written by the session that drove Orcshot's `0.3.0` release end
to end. Everything below was measured from real tarballs during that release, not reasoned about
afterwards.

**Two publicly-uploaded PPA source packages carried the repository's own `.git` directory.** The
third was caught only because someone looked:

| Tarball | `.git` entries | agent-state entries | Size |
|---|---|---|---|
| `0.1.1-3` (**uploaded, public**) | 1,415 | 0 | 10.8 MB |
| `0.2.0-1` (**uploaded, public**) | 1,882 | 3 | 14.8 MB |
| `0.3.0-1` (caught before upload) | 3,061 | 1,330 | 22.6 MB |

By `0.3.0` the payload included whole stale git worktrees carrying a built `.deb` and a `.whl` —
prebuilt binaries inside a *source* package, which is what lintian's `source-contains-prebuilt-*`
family exists to catch. After the fix the same tarball was **1.02 MB**.

**Why this is not recoverable after the fact:** a PPA will not accept a re-upload of an existing
version. There is no undo and no fixing it in place — a mistake costs a version number, and the bad
artifact stays public.

**The sharpest argument for inspecting the artifact rather than trusting the build config**, and
the reason a generic check would have caught this on the *first* release: the packaging config was
actively wrong about its own behaviour. `debian/source/options` listed `tar-ignore = "<pattern>"`
entries, and its own comment asserted the default VCS/backup exclusions were active. They never
were. Per `dpkg-source(1)`, quoted from the real man page rather than from memory:

> `-I` by itself adds default `--exclude` options that will filter out control files and
> directories of the most common revision control systems, backup and swap files and Libtool build
> output directories.

Those defaults apply **only** when `-I` appears with no pattern. So the config claimed an exclusion
set it had never enabled, and nothing downstream ever compared the claim to the output.
(Debian-specific coda, since it fails open and would otherwise be rediscovered: in
`debian/source/options` the defaults must be re-enabled with the long form and no value —
`tar-ignore` alone on a line. A bare `-I` there is rejected with
`dpkg-source: warning: short option not allowed in debian/source/options`, the warning scrolls
past, and the defaults stay off.)

**What Orclab should own — a preflight, as an `/orc-publish` responsibility.** It is the component
that knows both the artifact and the destination, and it already has the dry-run gate where such a
report belongs. A cheap check would list the archive and fail on `.git/`, on agent/tool state
directories, and on `*.deb`/`*.whl`/`*.so`/`*.exe`, and warn when the size is wildly out of line
with the previous release. Every one of those three uploads trips at least one of those rules.

**The second lesson is structural rather than a missing check, and it generalizes further:**

> Lint the thing you are shipping, not its sibling.

Orcshot's step 5 ran `lintian` on the binary `.deb` and passed clean every time, while the *source*
package — the artifact actually being uploaded in the next step — was the broken one. **A checklist
that lints one artifact and ships a different one has a blind spot by construction**, regardless of
how good either check is. That belongs in `release-checklist` as a rule about what a verification
step must be pointed at, not only in `/orc-publish`.

**Scope boundary:** this is about *inspecting* what is about to be published, not about producing
it correctly. Orcshot's own `debian/source/options` fix is already committed on its side and is not
Orclab's business; the generic capability is.

**Next step, when picked up:** decide the shape — always-on inspection in `/orc-publish` before any
irreversible action, an opt-in `preflight:` declaration on a channel leaf (patterns are
format-specific: a `.tar.xz`, a `.snap` and a `.flatpak` are not inspected the same way), or a
`release-checklist` convention that a build step must be followed by a check *of that artifact*.
Probably the last one plus one of the first two. Related: **#18** (a publish accepted but not
landed) and **#20** (where release-adjacent responsibilities live).

**Resolved 2026-09-08 (Orclab v12).** A leaf may declare `prepare:`, `artifact:` and `preflight:`;
`/orc-publish` runs prepare, inspects the artifact against the named rules, and reports `refused`
without running the action when a rule trips. Non-zero exit, siblings continue, offending entries
capped at five with the real total. `--allow-preflight-failure` downgrades a refusal for one run and
still prints every finding.

**The framing this entry started with was wrong, and the correction is the design.** The first pass
claimed a leaf whose action builds what it publishes could not be inspected at all. It can: the
tarball exists after the build, `debsign` is local and reversible, and only `dput` is irreversible.
The real constraint was narrower — one opaque shell string admits no gate between two of its
commands — which `prepare:` fixes without anyone restructuring a release. That also answers #12's
standing complaint that a publish action had to smuggle a build into itself.

The size-anomaly rule was cut deliberately: it needs persistent state Orclab does not keep and is
the most false-positive-prone of the four, and all three real incidents trip a content rule.
`filename_template` and `render_filename` were removed as part of this — shipped dead in v7 and
superseded by `artifact:`.

The structural half lives in `release-checklist` as **"lint the thing you are shipping, not its
sibling,"** which generalises past this design: a checklist that verifies one artifact and ships a
different one has a blind spot however good either check is.

## #22: concurrent Orclab agents can collide on numbered resources — a lock, an allocator, and ordered queues (RESOLVED 2026-09-09)

Raised by direflail 2026-09-08, immediately after asking which of the four then-unimplemented specs
could run concurrently. The map came back mostly clean on files — v12 and v13 both rewrite
`execute_plan` and must be sequential; #19, v14 and v15 touch disjoint files — but every one of them
appends a numbered scenario to `VERIFICATION.md`, and two concurrent streams would both read "ends
at 44" and both write "Scenario 45."

**The problem is two different things wearing one name, and one half is already solved.**

*Filesystem concurrency* — two agents contending for `.git/index.lock`, one's `git add` landing in
the middle of another's commit — is real and was hit for real on 2026-09-07, when an Orclab-centred
session and an Orcshot-centred session were both operating in Orcshot's single working tree. **Git
worktrees already fix that**, and `subagent-driven-development` already creates one per plan, which
is exactly why all of that day's Orclab work had zero contention while the Orcshot work had all of
it. Nothing to build.

*Semantic collision* is what survives worktrees **if each agent reads its own checked-out copy of the
file**. Two agents in separate checkouts derive the same "next number," and both are correct given
what they can see; no lock helps, because they are not contending for a resource at all.

**That framing is avoidable, and direflail's design avoids it — recorded because an earlier draft of
this entry assumed otherwise.** If every agent instead reaches out to **one canonical `BACKLOG.md`**,
rather than to its own worktree's copy, there are no divergent copies and the collision is an
ordinary shared-resource contention that a lock handles exactly as locks are meant to. The choice of
*which file agents write* is therefore the load-bearing decision here, not the locking primitive —
get that wrong and no amount of locking helps; get it right and the locking is textbook.

**Why detection alone is not enough, which is a correction to this entry's own first framing.** The
initial argument here was that a duplicate costs five minutes to renumber, so a one-line
`grep … | sort | uniq -d` beats building anything. That is true for `VERIFICATION.md` and **false
for `BACKLOG.md`**, and framing the problem around the weaker case got the conclusion wrong:

- Backlog entry numbers are **permanent and never reused** — a stated, load-bearing rule. If two
  agents both take `#22` and both commit, each referencing `#22` in its commit message and inside
  the entry text, it cannot be fixed by renumbering, because renumbering is precisely what the rule
  forbids. The damage is durable.
- The collision is **sometimes silent**. If both agents append immediately before the same trailing
  section, git conflicts and someone notices. If they insert in different regions, git merges
  cleanly and two `#22`s exist with no complaint at all.
- direflail does not read these files unsolicited (they are working memory for agents, not a status
  report), so a silent duplicate sits undisturbed until something trips over it.

**This bug class hit three times on 2026-09-07 in purely single-agent work**, which is the argument
that it is real rather than theoretical: duplicate `BACKLOG` numbers taken by two branches, a
`RELEASING.md` step renumber that made two steps vanish from the parsed release, and this. Only the
middle one has a mechanical check today (`/orc-release`'s step parser warns on non-contiguous
numbering); the other two have none.

### The design direflail proposed

**A file lock**, described accurately: a process arrives, finds no lock, takes it, does whatever is
needed to be assigned a number and write the file, then releases. A second process finds the lock
held, waits a few seconds, retries, and errors out after a reasonable period. Works for any number
of processes. Stale locks need a check — and, direflail's own operational note, a lock found when
none is expected is worth investigating rather than clearing reflexively.

**One technical correction, because it is the standard way this pattern is broken:** "check whether
it is locked, then set the lock" is a time-of-check-to-time-of-use race — two processes can both
observe it free and both proceed. The check and the set must be a single atomic operation:
`os.open(path, os.O_CREAT | os.O_EXCL)`, or `mkdir`, both atomic on POSIX. Everything else in the
description is right as stated.

**One lock, not one per resource, and lane-agnostic** — confirmed with direflail 2026-09-08. Every
process queues the same way regardless of which lane it belongs to. The reason is stronger than
simplicity: per-resource locks would reintroduce deadlock, since a work item can legitimately need
two numbers at once (v12's own plan adds both a `BACKLOG.md` entry and a `VERIFICATION.md`
scenario), and two agents acquiring them in opposite orders is textbook AB-BA. With a single lock
that is structurally impossible. The parallelism forgone is worthless anyway at millisecond hold
times.

**The critical section is take-a-number, not do-the-work** — otherwise lanes fully serialize and the
concurrency is pointless. But it should extend through the **commit**, not stop at the file write:
if the shared file lives in a worktree, two agents committing it concurrently are back to
`.git/index.lock` contention, which is the thing worktrees were supposed to have solved. Read,
append, commit, release — still sub-second.

**A consequence to know rather than fix:** writing to a shared ledger means the entry is not part of
the agent's own branch commit. Branches then never touch `BACKLOG.md` and cannot conflict on merge,
which is a real benefit — but an entry survives even if the work that motivated it is abandoned.
Acceptable for a findings ledger; surprising if unexpected.

**On wait times:** a queue of lanes contending for a sub-second append is not time-critical. Even
unlucky timing across several lanes costs seconds, which is the correct trade for eliminating a
class of collision that cannot be cleaned up afterwards.

**The real cost is not the lock.** A lock protects a resource only if *every* writer takes it. Today
"add a backlog entry" is `backlog-discipline` prose instructing Claude to scan the file for the
highest `N` and edit it directly. An agent doing that without going through an allocator defeats the
lock completely and silently — it will not even know it should have. So the actual work is
converting a prose-driven edit into a tool-mediated one: the skill must say "get your number from
the allocator" rather than "scan for the maximum." That is a larger change than the locking, and it
is the part that needs deciding. It is also the direction several 2026-09-07 findings already
pointed: mechanically checkable beats "be careful."

### Ordered queues — and yes, it becomes a scheduler

direflail's follow-on, and the case that makes this more than a lock: *"what if i want to run 12
then 13 but also simultaneously 19 and 14?"*

That is two lanes, each internally ordered, running in parallel:

```
lane A:  v12 → v13
lane B:  #19 → v14
```

**"Arguably yes" it is a scheduler — but a deliberately small one.** It is N sequential lanes running
concurrently, not a dependency graph. Nothing needs to express "v13 requires v12 *and* #19"; every
real ordering constraint found so far is linear within a lane. Keeping it to lanes avoids a DAG
resolver, cycle detection, and partial-failure semantics, none of which any real case here has
needed.

**Exclusion and ordering are different mechanisms and should not merge.** The lock gives mutual
exclusion on a shared resource; the lane gives ordering between work items. Conflating them is how a
lock grows into a general scheduler nobody asked for. A lane needs no lock to be ordered, and a lock
needs no lane to be correct.

### Alternatives worth weighing before building

- **Deferred numbering.** Agents write a placeholder (`## Scenario NEXT`) and the number is assigned
  at merge. Lock-free, no shared state, and it works well for `VERIFICATION.md`. **It does not work
  for `BACKLOG.md`**, where the entry number is referenced in the commit message and inside the entry
  text *while the work is happening* — a commit saying "BACKLOG #NEXT" is not usable. The two
  resources have genuinely different constraints and may deserve different answers, which is worth
  settling before assuming one mechanism covers both.
- **Pre-assigned ranges per lane** (lane A takes scenarios 45–47, lane B 48–50). No lock, no
  allocator, trivially correct. Goes stale the moment scope shifts, and does nothing for `BACKLOG.md`
  where numbering is global and permanent.
- **Just serialize.** Costs wall-clock time and nothing else. Genuinely the right answer if
  concurrent runs stay rare — the collision rate to date is zero, because concurrent streams have
  never actually been run.

### Scope boundaries

- **Not cross-machine.** PID-liveness staleness checks work on one host and do not survive
  containers or a shared network filesystem. Every real case here is one machine.
- **Not a daemon.** No long-running coordinator; a lock file and a lane definition are enough.
- **Not a DAG.** See above.
- **Not for `.git/index.lock`.** Git already handles that, and worktrees avoid it.

### Next step, when picked up

A `superpowers:brainstorming` pass. It needs to settle: whether one mechanism covers both
`BACKLOG.md` and `VERIFICATION.md` or they get different treatments; whether the allocator is a
bundled script or a hook; how `backlog-discipline` changes from "scan for the maximum" to "ask the
allocator," and what happens when an agent ignores it; and what a lane definition actually looks
like given that `subagent-driven-development` already owns per-plan execution and may be the natural
home rather than a new component. Add to that list, from the 2026-09-08 refinement: **where the
canonical file actually lives** — the main worktree's checkout, or a path outside every worktree —
since that decision is what makes the lock meaningful or useless.

**Do not build ahead of a real concurrent run.** The honest state is that this is a well-understood
hazard with a zero incident rate under concurrency, because concurrency has not been used yet. The
right trigger is the first time two lanes are actually launched.

**Resolved 2026-09-09 by v16** (`docs/superpowers/specs/2026-09-08-orclab-v16-orc-todo-design.md`
and its plan), shipped as `/orc-todo` in v0.14.0.

**What was built, and it is this entry's own design rather than a substitute for it.** The
load-bearing decision this entry identified — *which* file agents write — was taken the way the
entry argued: one canonical file, reached through `git rev-parse --git-common-dir`, which resolves
to the same place from the main checkout and from every worktree. With no divergent copies the
collision becomes ordinary shared-resource contention, and the lock is textbook: a single atomic
`os.open(O_CREAT|O_EXCL)`, one lock rather than one per resource (per-resource locks reintroduce
AB-BA deadlock the moment one work item needs two numbers), and a stale lock reported but never
auto-cleared. The allocator owns the write as well as the number, so there is nothing to bypass:
an agent cannot take a number and forget to use it, or write without taking one.

**One mechanism serves both files, via a per-file descriptor.** This entry left open whether
`BACKLOG.md` and `VERIFICATION.md` needed different treatments. They did not — what differs
between them is the heading shape, how a number is recognised, and where a new section goes, and
all three are data. The deferred-numbering alternative this entry raised was rejected for the
reason the entry itself gave: a commit saying "BACKLOG #NEXT" is not usable.

**And lanes stayed a record, never a runner**, honouring this entry's own boundaries. Nothing
launches a session, supervises a process, or handles a crash. Exclusion and ordering remained
separate mechanisms: the lock appears in the lane code only to keep concurrent writes to
`lanes.json` from losing each other, never to give lanes their ordering.

**Deliberately not built**, all three named as alternatives here and all three declined: pre-assigned
per-lane ranges (goes stale the moment scope shifts, and does nothing for a global numbering),
plain serialization (costs wall-clock and was the honest answer only while the collision rate was
zero), and any DAG or scheduler beyond N linear lanes.

**This entry's own trigger fired first.** It says "do not build ahead of a real concurrent run",
and names the first launch of two lanes as the right moment. That is exactly what happened — see
**#25**, the 2026-09-08 incident. The entry was not overridden; its condition was met.

**What it did not anticipate, and #25 did:** every guard proposed here protects a *write*. Nothing
here announces an *intent to start*, which is the half that cost the real money. The lane record
and the SessionStart hook exist because of #25, not because of this entry.

## #23: the action-shape warning misses a repeated publish verb (RESOLVED 2026-09-09)

Found by a code review of v12's action-shape check (2026-09-08), verified live against the real
implementation.

`cli.action_shape_warning()` warns when a leaf's single `action:` both builds and irreversibly
publishes, because no gate can run between the two. It compares only the **leftmost** occurrence
of each verb - `action.find(publish)` against `action.find(build)` - rather than every pair. So an
action that publishes, builds, then publishes again:

```
dput ppa:x a.changes && dpkg-buildpackage -S && dput ppa:x b.changes
```

genuinely has the build-then-irreversible-publish shape the check exists to catch, and produces no
warning at all: the first `dput` precedes the build, so the ordering test fails and the second
`dput` is never considered.

**Scope boundary, and the reason this is small:** the check warns and never refuses. A miss costs
a warning, not a bad publish - the real gate is `preflight:`, which inspects the artifact itself
and is not a heuristic over a shell string. This is a gap in an advisory hint, not in the safety
mechanism.

**The fix, if it is ever worth taking:** compare every `build` occurrence against every `publish`
occurrence rather than only the first of each. Worth weighing against the opposite risk - the
check already has false positives by design (any substring match counts, so
`cargo build-tools-checked && dput ...` warns today), and widening the search widens those too.

**Provenance, added after the fact.** Two sessions independently executed the whole of the v12
artifact-preflight plan in parallel on separate branches, neither aware of the other (see #25).
This branch's own final review of the action-shape check noticed the same repeated-verb gap and
set it aside as minor without formally filing it; it was the parallel session's own, independent
review that actually filed this entry's finding. Worth recording for what it says about the
review process, not just about the code: the same diff got two genuinely separate passes, and
only one of them turned an observation into a tracked entry.

**Resolved for real, not just tracked, 2026-09-09.** `action_shape_warning()` now uses
`action.rfind(publish)` against `action.find(build)` - one word changed. That is exactly
equivalent to the every-pair comparison this entry asks for, and the equivalence is worth stating
because the fix looks too small otherwise: if any build precedes any publish, then
`first_build < last_publish`; and if `first_build < last_publish`, that pair is itself a
build-then-publish. No loop, no helper.

Taking it this way answers the entry's own objection - that widening the search widens the
existing false positives. It doesn't. The substring looseness the entry names
(`cargo build-tools-checked && dput ...` warns today) is untouched, deliberately, because it is
not this entry.

Verified against the entry's own three-command example, now a test:
`dput ppa:x a.changes && dpkg-buildpackage -S && dput ppa:x b.changes` warns. Confirmed it fails
without the fix, not just that it passes with it. The one existing case that could have flipped -
`test_publish_before_build_does_not_warn` - has a single `dput`, so `rfind` and `find` return the
same index and it still correctly does not warn. 127 passed. The check remains advisory;
`preflight:` is untouched.

## #24: `--dry-run`'s exit code doesn't distinguish a resolvable plan from one already known broken (RESOLVED 2026-09-10)

Raised by the final review of v12 artifact preflight (2026-09-08) and deliberately scoped out of
that work's own fix wave rather than smuggled into it.

`/orc-publish --dry-run` exits 0 whenever it manages to resolve a selection, even when the plan it
prints already names a problem the tool has diagnosed with certainty. Confirmed live: a leaf with
a typo'd rule name (`preflight: ["no-vcss"]`) prints
`preflight result: unknown preflight rule(s): no-vcss` and exits 0.

**The concrete consequence** is not a bad publish - at execution that leaf is `refused`, nothing
is published, and `main` exits non-zero. It is that `--dry-run` is the gate `orc-publish`'s own
`SKILL.md` Step 2 asks a human to read and approve, and anything scripting around that step - a CI
preflight, a `RELEASING.md` check - cannot tell "this plan is fine" from "this plan is already
broken and I am saying so in the output you are about to approve."

**Why this is a design decision rather than a one-line fix.** The typo is not the only dry-run
condition that reports a problem and exits 0: `preflight is declared but no artifact: is set`,
`artifact not found:`, `unsupported archive format`, and `artifact path expansion timed out` all
behave the same way. Making only the statically-detectable ones non-zero draws an arbitrary line
through the middle of one category; making all of them non-zero changes what `--dry-run`'s exit
code means to every existing caller. The real question is what the dry-run contract is - a report
that succeeded in being produced, or a verdict on the plan - and it should be answered in one
deliberate pass.

**Scope boundary:** this is about the exit code only. The messages are already printed and already
correct.

**Provenance, added after the fact.** This finding came from the parallel session's own,
independent review of the same v12 artifact-preflight plan (see #25) - a second, genuinely
separate pass over the same diff this branch had already reviewed and shipped. It is deferred
here, not decided, deliberately: whether exit 0 is defensible (the dry run's job is to resolve
and print, and it did) or a real gap (a wrapper doing `orc-publish --dry-run && orc-publish`
proceeds anyway) is a design question for whoever picks this up, not something to settle in the
act of filing it.

**Resolved 2026-09-10 — the exit code is a verdict on the plan.** `--dry-run` exits 1 when the
plan it printed contains a refusal the real run would give, and 0 when every leaf is clean,
deferred to after `prepare`, or carries only a warning. All five conditions the entry listed
went together, plus a real inspection finding on an artifact that already exists, which the entry
did not list and which is the same thing. The line is the one `main` already draws for a real
run: would this leaf be `refused` as things stand.

**Why this reading and not the other.** The dry run's own `SKILL.md` already said it "reports the
refusal the real run will give" — the text was a verdict and only the code was a receipt. Nothing
in the repo consumed exit 0 as "report produced": the one caller is Step 2, where a person reads
the output. The only reason anyone checks the code is the `--dry-run && publish` wrapper, and for
that caller the old meaning was a lie. Deciding it by the plan's own words, not by what existing
callers happened to tolerate, is what the entry asked for in "one deliberate pass."

Implemented as `plan()` returning `(text, refused)` with `format_plan` kept as its text-only face
for the tests that only read the plan, and the verdict computed in the same walk that prints it —
an artifact expansion can time out, and a second walk to compute the verdict would wait out that
timeout twice. Four existing tests that pinned exit 0 on a printed refusal were the old contract
written down; they now pin 1.

## #25: BACKLOG #22's collision happened - two agents built the same feature, neither could see the other (RESOLVED 2026-09-09)

Not a prediction any more. On 2026-09-08 two concurrent sessions each implemented the whole of the
v12 artifact-preflight plan, in full, independently. One worked on `main` directly; the other in a
worktree branched from `origin/main` at `092a327`. Both produced a complete feature with a passing
suite (120 tests and 119 tests), both wrote their own `VERIFICATION.md` Scenario 45, both resolved
BACKLOG #21, and both allocated new BACKLOG numbers from the same `#22` high-water mark. The
duplication surfaced only at `git merge`, as an add/add conflict on `tests/test_inspect.py`.

**What made it invisible for the entire run, and this is the part worth keeping.** #22 frames the
hazard as two agents *taking the same number*. That happened here, but it was the cheap part - a
renumber. The expensive part was that the two agents never contended for any shared resource at
all until the very end: the worktree session branched from `origin/main` and pushed nothing, and
the `main` session committed locally and pushed nothing, so for the whole of both runs there was
no observable state either could have polled to discover the other. A lock around number
allocation - #22's proposed remedy - would not have fired once. Every guard in #22's design
protects a *write*; nothing announces an *intent to start*.

**The concrete cost:** roughly a full implementation's worth of agent time and tokens, spent
twice, plus the review passes on both. Not recoverable, and not detectable until the end.

**One real consolation worth recording**, because it argues against treating duplication as pure
waste: the two implementations were not identical, and each caught something the other missed.
`main`'s routed `expand_path` through `_run` (closing a process-group hole the worktree's version
left open and had filed as a backlog entry); the worktree's fixed a scalar `preflight:` being read
one character per rule, and a non-string one raising `TypeError` out of the property ahead of
every caller's containment - both of which `main`'s had. The surviving branch was `main`'s, with
the worktree's two fixes ported onto it as `596d970`. That is a real argument for deliberate
N-version work on a genuinely risky component - but as a decision someone makes, not as an
accident nobody noticed.

**Scope boundary:** this entry records the incident and what it disproves about #22's framing. It
does not propose the mechanism - that belongs in #22, whose design needs an "announce intent to
start" step that its current one-lock-around-allocation shape does not have.

**Correction, 2026-09-08, same day - the paragraph above claiming #22's lock "would not have fired
once" is wrong, and the error is worth more than the claim was.** It asserted that the two sessions
never contended for a shared resource. They did, twice. **Both allocated `VERIFICATION.md` Scenario
45** - the surviving one is from the `main` session's `5684150`, and the worktree session's Task 7
independently resolved the same number from the same "scenarios run to 44" scan. **Both also took
BACKLOG `#23` and `#24`** from the same `#22` high-water mark, with different content. That is
precisely the collision #22 describes, on precisely the two resources it names. An allocator asked
for a scenario number twice returns 45 and 46; asked for a backlog number twice returns 23 and 24.
It would have fired four times and prevented all four collisions.

**How the wrong conclusion was reached, since the reasoning error is the reusable part:** the
duplicate *implementation* and the numbered-resource *collision* were treated as one event. They are
not. #22 has never claimed to prevent two agents building the same feature - its scope is numbered
resources, and on that scope it was exactly right. Judging it by whether it would have prevented the
duplicate build measured it against a promise it never made, then generalised that to "the design is
wrong."

**The second error compounds the first:** an unbuilt mechanism was declared disproven by a run that
did not have it. The sessions allocated numbers by scanning a file for the maximum, because that is
what `backlog-discipline` says to do and no allocator exists. Observing that no lock was taken in a
run containing no lock is not evidence about the lock. It is evidence about the absence.

**What survives from this incident as real input to #22's design:** the collision rate is no longer
zero, so #22's own "do not build ahead of a real concurrent run" trigger has genuinely fired. And
one detail worth carrying in - neither session pushed until the end, so the canonical-file question
#22 already flags (the main checkout, or a path outside every worktree) is load-bearing rather than
incidental. A lock on a file inside each worktree would have protected nothing here.

**Resolved 2026-09-09 by v16**, shipped as `/orc-todo` in v0.14.0. Both halves this entry
distinguishes now have a mechanism, and they are different mechanisms — which is this entry's
central point and the thing #22's design would have missed.

**The cheap half — the numbers — is the allocator.** See #22's resolution. `test_allocate.py`'s
concurrency test spawns two real processes rather than making two sequential calls, and it is the
test that would have failed on 2026-09-08. Measured against a lock-free control during review, it
detects a missing lock in about 90% of runs, so a single green run is not proof.

**The expensive half — two agents doing the same work, unobservably — is the lane record and a
SessionStart hook.** This entry's sharpest observation is that no lock would have fired once,
because the two sessions never contended for anything until `git merge`. So the answer is not a
stronger guard on writes; it is a record of what has *started*, and something that reads it
without anyone remembering to. `hooks/scripts/lane_notice.py` tells a new session what lane is in
progress, what lock is held, and what entries are sitting uncommitted. It is silent when there is
nothing to say, because a hook that speaks every session gets tuned out.

**Its own words are in the code.** `lane_notice.py`'s docstring records why it exists: *"Nobody
forgot to check - there was nothing to check."*

**One thing this entry argued for that was NOT built, deliberately.** It records that the two
implementations each caught what the other missed, and calls that "a real argument for deliberate
N-version work on a genuinely risky component - but as a decision someone makes, not as an
accident nobody noticed." Nothing in v16 schedules duplicate work. Lanes make deliberate
concurrency visible; choosing to run the same item in two lanes remains a person's call.

**A postscript worth keeping, because it repeated the pattern in miniature.** v16's own execution
found eight defects in its plan and eleven review findings, one Critical: `/orc-todo remove` did a
read-modify-write on the canonical file with no lock while `add` took one — the same class of
lost update this entry is about, inside the mechanism built to prevent it. Reproduced live before
it was fixed. A mechanism does not exempt its own code from the failure it models.

## #26: Claude's designs and explanations are built inside-out — the user has to ask for facts Claude already had (RESOLVED 2026-09-10)

Raised by direflail 2026-09-09, at the end of the session that produced v16's spec and plan, and
raised as a working-relationship problem rather than a defect: *"your plans are good, if you're an
AI... i just want us to work better together."*

**The pattern, stated more precisely than "be more user-centric":** Claude reasons from the
mechanism outward and explains from the conclusion backwards. Both are natural from inside a context
where every premise is already loaded, and both are invisible from there — nothing feels missing,
because for Claude nothing is. The user is the only party who can see the gap, so the user ends up
doing the work of finding it.

**Five real instances from that one session**, recorded concretely because a vague pattern is
unfixable:

1. **A design built outward from a lock.** Claude proposed an `/orc-lane` command whose surface was
   organised around the lock, the allocator and the lane record — three pieces of machinery, two of
   which a person can never interact with. direflail: *"what you're designing doesn't make sense to
   a user. there's no command i can call to do something to the file lock."* The reframe to
   `/orc-todo`, organised around the backlog a person actually looks at, came entirely from them.
2. **Designing against a file never shown.** Claude spent several exchanges arguing that
   `VERIFICATION.md` belonged in the allocator's scope without once showing what it contains.
   direflail had to ask outright: *"tell me what VERIFICATION.md stores and give me an example of
   format."* The answer took one command and immediately made the scope question decidable.
3. **A premise skipped entirely.** Claude reported that an allocated entry "lands on main's branch,
   not the feature branch" as though that followed obviously. It only follows if you already know
   `subagent-driven-development` creates a worktree per plan, so a repo holds N copies of
   `BACKLOG.md`. direflail: *"i don't understand what the repo has to do with any of this."*
4. **An assumption never stated, then mistaken for a proposal.** Because Claude never said lanes do
   not create branches, direflail reasonably asked whether they did — *"are you proposing that each
   lane creates its own branch and the merge is where the trouble here is?"* The answer was no on
   both counts, and neither had ever been written down.
5. **A four-day-old line cited as settled authority.** Claude quoted `backlog-discipline`'s "Don't
   turn this into a general task list" as a constraint on the design. direflail: *"IS BACKLOG.md a
   task list? ... and who wrote backlog-discipline and why does it say this"*. Checking took one
   `git log`: they wrote it on 2026-09-04, the commit body is empty, and ten of twelve open entries
   are things that need doing. The line was deleted.

A sixth, different in kind but the same root: Claude reopened the already-settled decision that all
agents write one canonical `BACKLOG.md`, and direflail had to say *"i thought we had resolved
that."* Settled context decayed silently rather than being tracked.

**What should already have covered this, and why none of it fired.** `verify-before-asserting`
covers a claim that gets challenged — it fires after the user pushes back, which is exactly one step
too late here. `whole-process-first` covers reading a document before acting on it, not showing it
to the person you are designing with. `superpowers:brainstorming` requires asking questions one at a
time and proposing trade-offs, and Claude did both; it says nothing about surfacing the artifacts a
person needs in order to answer those questions. `CLAUDE.md`'s "name what should already have
covered it" is about mechanisms, not explanations. **There is a genuine gap, and it is not a matter
of widening an existing trigger.**

**Why this is harder than it looks, and the reason it is an entry rather than a fix.** The obvious
remedy — a rule saying "explain more" or "show your sources" — is the weakest possible form, and
`CLAUDE.md` already says why: prose fires only if the skill was invoked, the section was read, and
the reader classified themselves into its trigger. Worse, this failure is *self-concealing*. Every
other rule in this repo fires on a situation Claude can observe. Here the situation is "the user
lacks a fact I have," which Claude by construction cannot see — the fact is present, so nothing
registers as absent. A trigger phrased around noticing the gap will never fire, because noticing is
the part that fails.

That points at cheap structural habits rather than judgment: showing the artifact under discussion
before arguing about it, stating premises about the environment before conclusions that rest on
them, checking the provenance of any in-repo rule before citing it as a constraint, and keeping
settled decisions somewhere they cannot quietly decay. All four are mechanical and none require
Claude to detect its own blind spot first. Whether they belong in a skill, in `CLAUDE.md`, or in the
brainstorming flow is undecided.

**Scope boundary:** this is about how Claude designs and explains, not about output length. Four of
the five instances above were Claude being *too brief on premises while being long on conclusions* —
more words would not have fixed any of them, and the fix for #2 and #5 was one shell command each.

**One incidental confirmation, recorded because it settles a live question:** direflail opened this
request with *"add one task to the backlog."* `backlog-discipline`'s "not a general task list" line
is being removed by v16 partly on the argument that the file is substantially a task list. Its owner
calling an entry a task, unprompted, is the strongest evidence available that the removal is right.

**Correction, same day, from direflail — this entry flattened a distinction that matters.** The ask
was *"think more user-centric"*, and it was written up above as *be* more user-centric. direflail's
own words: *"the former means you still think and act as yourself, but you spare some cycles to
think things through as if you were a human, particularly when it comes to user-facing stuff."* Not
a request to become a different kind of reasoner - a request to spend cycles simulating the other
side of the table.

**The reasoning error that produced the flattening, which is the part worth keeping.** The paragraph
above argues the failure is self-concealing, and concludes the fix must therefore be mechanical
habit *instead of* judgment. That conflates two different capacities:

- **Noticing** that the user lacks a fact - genuinely unavailable, for the reason given: the fact is
  present, so nothing registers as absent.
- **Simulating** a reader who has not seen what this context has seen - a check that can be run on
  purpose, needing no prior noticing at all.

Only the first is blocked. The argument slid from "I cannot perceive the gap" to "so do not try to,"
and those do not connect. The four habits remain right, but they are the floor rather than the
answer: a deliberate pass over any user-facing design, read as someone who has not been in this
conversation, is the thing actually being asked for.

**And the cost argument was under-weighted.** direflail: *"that's going to help keep us from going
in two different directions and having to go back and refactor."* This is not only about clarity in
the moment. `/orc-lane` was designed, argued for, and had questions built on top of it before the
reframe to `/orc-todo` arrived - all of which was thrown away. That is the same economics as **#25**:
work done twice because two views of the problem never met early enough. A simulated pass during
design is paid in a paragraph; skipping it is paid in a rewrite.

**A first mechanism, 2026-09-10 — recorded as an attempt, not a resolution.** `CLAUDE.md` now
carries "Before any answer that says what to do next, show what it rests on." The entry stays
open deliberately: this is the weakest kind of fix by this entry's own argument, and a
`(RESOLVED)` heading would tell the next reader the problem was solved.

**What changed the diagnosis.** The covering memory
(`show-the-ground-not-just-the-conclusion`) was already correctly worded, widened the day before
after its trigger proved too narrow, and sitting in context for the whole of the session that
then violated it. So this is no longer "the trigger was phrased too narrowly" - that was the
previous finding and it was fixed. The rule was right, loaded, and not recognised at the moment
it applied. `CLAUDE.md` removes two of the three failure conditions named in "Why prose is the
weakest place to put a rule" (always loaded, short enough to read); only recognition survives,
which is why the new trigger is written to be hard to describe your own work out of rather than
merely accurate.

**The instance it was written from.** Asked what to work on next, Claude ranked three backlog
entries and argued the ordering across two turns before direflail decided on it, without ever
running `ls docs/superpowers/specs`. All three already had written specs; **#17**, described as
"a brainstorming pass on an undecided taxonomy," is a 260-line design document. The same
reasoning went wrong twice more in that session and was corrected each time only by reading an
artifact - the v14 spec's own text on ordering, and `tree.py` showing `confirm` was not yet in
`LEAF_KEYS`.

**The wording was tested rather than argued into place**, across eight subagent runs on fourteen
situations, and the record is worth more than the final text:

- An **exemption for small answers became the loophole in every form it took.** Self-assessed
  importance, then reversibility - both judged by the party who wants to skip, and judged
  *before* the pass, on exactly the ignorance the pass exists to remove. It was cut entirely.
  The argument for having one ("a rule that is always on gets ignored") assumed the pass has a
  fixed cost; it does not, since an answer that turns on nothing has nothing to open.
- **Patching a loophole moved it four times running** - floor, then reversibility, then a clause
  defending the rule's own cheapness, then citing a file while having read only its headings.
- **The clause written to close that last one did not work**, and only a test that exercised the
  *pass* rather than the trigger revealed it: it catches a response that admits its own
  shallowness and has no purchase on one that simply does not say. What discriminates is
  requiring a quote, because a quote is externally checkable and a claim about your own reading
  is not. Hence "quote the sentence that decided it."
- The most dangerous candidate response in that test was not the laziest. It name-checked the
  rule's own required locations, used its vocabulary, and attached a **true but irrelevant**
  premise to the wrong claim - surviving a checklist while getting the answer wrong.
- **"Quote the sentence that decided it" was itself wrong**, found by a ninth run on a different
  question with a different kind of evidence. It excluded a line of code by its literal wording,
  excluded a grep result, and had no answer at all for evidence that is an *absence* - where the
  only move left is a self-report the next clause disqualifies. Now "quote the exact text ... and
  where what decided it is an absence, show the search that establishes it."
- **And the honest ceiling, worth more than the wording:** the pass tests whether an answer is
  *checkable*, not whether it is *complete*. A response that shows its grep output satisfies every
  clause and can still be wrong because the grep missed a caller. No wording inside the pass can
  fix that; the surface paragraph now asks for callers "found by a search you show rather than one
  you assume", which is as far as prose reaches.

**What is still open**, and what a next attempt should not do: the next step after a failure is
not a fourth rewording. It is a mechanism, and the question nobody has answered is what event a
machine can observe that co-occurs with "about to state a conclusion." A `model` field on a tool
call is observable, which is why the model floor could be a hook; a property of prose is not.
`UserPromptSubmit` injecting the check on question-shaped messages is the only shape found so
far, and a hook that speaks every turn gets tuned out - which `hooks/scripts/lane_notice.py` says
in its own docstring.

**A second mechanism, 2026-09-10 — the simulation itself, and the first time it was watched
working.** Asked to fix #30, Claude wrote a design that satisfied every clause of the
show-what-it-rests-on section — the deciding line quoted, the file:line cited — in the vocabulary
of `canonical_root`, `--show-toplevel` and `in_canonical_checkout`. direflail: *"i'll admit, i
don't understand what you're talking about. it's ok. can you explain where someone from my
viewpoint can understand?"* The rewrite in a person's terms — two copies of the project, the text
went into the wrong one, keep the shared number and write where you ran it — was understood and
approved on first read. direflail: *"i think this is the solution we've been looking for
regarding you explaining things 'inside-out'"*, and asked for it in `CLAUDE.md`, accepting the
cost: *"it seems well worth it if it works."*

`CLAUDE.md` now carries "Before explaining anything, explain it again from the reader's side" as
a sibling of the evidence pass. It is the *simulating* capacity this entry's own correction
identified as the thing actually asked for, which had lived only in the memory file
`show-the-ground-not-just-the-conclusion` — loaded in the session that produced the unreadable
explanation, and not run. Still open: this remains prose, and the paragraph above on what a next
attempt should not do still stands. What is new is a checkable before/after on one real
explanation, which no prior wording had.

**Resolved 2026-09-10, by direflail, at the end of the session that added the second mechanism.**
Asked to talk briefly about this entry, then: *"i've been more comfortable with your explanations.
we can close this."* That is the only judge this entry ever had - the user is the one party who can
see the gap - and it is the judgement.

What closes it is not a wording. The two `CLAUDE.md` sections stay as written, prose remains the
weakest place for a rule, and the paragraph above about a next attempt needing a mechanism is
still true. What changed is the evidence: one session in which every design and every merge
summary after the morning's correction was written from the reader's side, and the reader said
so. If the pattern returns, this is the entry to reopen - it holds the diagnosis, the six worked
instances, the corrected framing ("think user-centric, not be user-centric"), and the record of
what each wording did and did not catch.

## #27: three deferred minors from v16's own review, worth tracking rather than losing (RESOLVED 2026-09-09)

Raised by v16's own final whole-branch review (2026-09-09), which triaged the deferred minors its
per-task reviews had accumulated. Most were genuinely fine to leave. These three were not — not
because any is urgent, but because each is the kind of thing that reads as fine forever and then
costs an afternoon.

**1. The concurrency test hangs instead of failing when a child dies.** In
`skills/orc-todo/scripts/tests/test_allocate.py`,
`test_two_real_concurrent_processes_get_different_numbers` calls `p.join(timeout=60)`, which
returns without killing a hung child, then `q.get()` with no timeout at all. A child killed by a
signal, or dying before its `put`, blocks the parent forever. Separately, if a child does put its
`ERROR ...` string, `sorted()` over mixed `int` and `str` raises `TypeError` — still a failure,
just an opaque one. The fix is `q.get(timeout=30)`, and it is worth taking precisely because this
is the test that would have caught the 2026-09-08 collision: a test that hangs CI is a test people
learn to skip.

**2. Two test names in the same file promise setup that `make_repo` does not perform.** It never
commits, so nothing in the fixture is ever tracked. Consequently
`test_allocate_appends_even_when_the_file_is_dirty` never creates a git-dirty file — it tests that
existing content survives, which is the behaviour that matters, but not the named condition; and
`test_allocate_never_commits` asserts a non-empty `git status` on a file that was already
untracked before the call, so it would pass on a no-op. Each still discriminates something real.
Each asserts a weaker property than its name claims, which is how a test stops protecting what
someone believes it protects.

**3. `_sections()` treats any line starting `## #N: ` as a heading, including inside an entry's own
prose.** In `skills/orc-todo/scripts/orc_todo/cli.py`, an entry that illustrates the heading format
by quoting it splits into a phantom extra section, affecting `list` and `show` as well as the span
arithmetic in `remove`. Verified harmless against the real `BACKLOG.md` today — `list` returns
exactly the open entries — but this file is one about its own format, which makes it likelier than
usual to quote a heading someday.

**Scope boundary:** all three are inside v16's own code and tests. None affects the allocator's
correctness under concurrency, which the review verified separately and by control.

**Why one entry rather than three:** they share a cause and a moment. Each was seen during v16's
review, judged not worth a fix round, and would otherwise live only in a ledger that was deleted
with the worktree. Splitting them buys nothing, and the shared context — what the reviewer was
looking at, and why they were deferred rather than fixed — is most of what a future reader needs.

**Resolved for real, not just tracked, 2026-09-09.** All three, plus a fourth found while fixing
the third. 64 tests passing before the extension, 65 after.

**1.** `test_two_real_concurrent_processes_get_different_numbers` now uses `q.get(timeout=30)` and
asserts every result is an `int` - naming the offending value in the message - before sorting. A
child killed by a signal fails the test after 30s instead of blocking the parent forever, and a
child's `ERROR ...` string is reported verbatim rather than surfacing as an opaque `TypeError`
from `sorted()`.

**2.** `make_repo` now commits its fixture, so "dirty" and "never commits" are real conditions
rather than artefacts of everything being untracked. The negative control matters more than the
fix here: the *old* `test_allocate_never_commits` passes against a deliberately no-op allocator -
exactly the weakness this entry described - and the new one fails against the same no-op.

**3.** `_sections()` now routes through a `_headings()` helper that drops matches inside fenced
code blocks. `cmd_remove` routes both its heading scan and its `_NEXT_SECTION` end-boundary scan
through the same helper, so a fenced `## ` line inside the entry being removed can no longer cut
its span short. Column-0 was already enforced by `re.MULTILINE`; the fence was the only missing
discriminator, and indentation would not have served - a fenced example is usually flush left,
which is the point of showing it.

**4, not in the original entry.** `resources.scan_max()` had the identical blind spot, and the
first judgment on it was to leave it: it can only ever inflate the next number, never reissue one,
so it is safe by the allocator's own invariant. That reasoning is correct about *uniqueness* and
wrong about what the numbering is for. A quoted `## #99:` would silently jump the next entry to
`#100`, and this file's own rule is that a gap is the record of a deleted entry - a phantom gap is
that record lying. So `_headings()` moved down into `resources.py` (`cli.py` already imports from
it, so the direction was already there) and `scan_max` uses it. Negative control run: on the same
input the old implementation returns 99 and the new one returns 7.

Fixing it here rather than filing it is deliberate. Two functions with the same regex-over-markdown
blind spot in one package is the case for fixing it once where both route through, and the helper
the third fix had just written made that a five-line change.

**One correction to this entry's own text, made in place 2026-09-09 at direflail's direction.**
Item 2 originally read "Three test names" and then named two. There is no third whose *name* claims
tracked-file setup - the nearest, `test_a_lost_counter_self_heals_from_the_file`, has a docstring
mentioning "a fresh clone or a cleaned `.git`" but asserts only counter behaviour. Committing in
`make_repo` covers it either way. The word was corrected to "Two" rather than left standing with a
note, which is the one place this resolution departs from `backlog-discipline`'s "never rewrite the
original diagnostic text" - a miscount is not reasoning worth preserving, and the original wording
is recorded here.

## #28: should /orc-git land a branch, or is finishing-a-development-branch the answer (RESOLVED 2026-09-10)

Raised by direflail 2026-09-09, immediately after a session said "merge and push" as though
`/orc-git` covered it. It does not: its subcommands are `repo`, `commit`, `push`,
`commit-push`/`cp`, `branch`/`switch`, and `pr`. Every one of those either prepares work or
publishes a commit; none of them lands a branch.

**The concrete consequence** is small but real and already happened twice in one session. A branch
finished under Orclab's own workflow has to leave it to be landed - either through
`superpowers:finishing-a-development-branch` or through raw `git merge`/`gh pr create`. The memory
rule "use the shipped command, not the raw mechanism" says to flag the fallback when it is needed;
here the fallback is needed every single time a branch finishes, which is the shape of a missing
command rather than an occasional exception.

**What should already have covered it, and mostly does.**
`superpowers:finishing-a-development-branch` exists precisely for this decision - merge directly,
open a PR, or rebase first - and Orclab's own standing rule is to wrap real existing skills rather
than rebuild them. So this is explicitly *not* a proposal to implement merging. If anything is
built it is a thin `/orc-git merge` that delegates, with the availability guard `orc-code`'s flows
already use for `feature-dev`.

**The argument on each side, neither settled.** For: `branch` and `pr` are already in `/orc-git`,
and a user who has just run `/orc-git cp` has no reason to know the next step lives in a different
plugin's vocabulary. Against: `finishing-a-development-branch` asks real questions about how to
land work, and a `/orc-git merge` that answers them by defaulting would be worse than not having
it - `/orc-git`'s existing subcommands are all deliberately unsurprising, and this one is not.

**Where this should be decided: inside v14, not beside it.** The v14 spec
(`docs/superpowers/specs/2026-09-08-orclab-v14-forge-boundary-design.md`, closing #20) is already
about `/orc-git`'s scope and where host-specific release work lives. Deciding "does `/orc-git` land
branches" in a separate pass would split one scope question across two designs. This entry exists
so the question is tracked if v14 ships without addressing it - not to schedule its own work.

**Scope boundary:** this is about who owns the *command surface*, not about merge strategy,
conflict handling, or branch protection. None of those change whichever way it goes.

**Searched before filing**, per CLAUDE.md: every shipped `skills/*/SKILL.md`, `CLAUDE.md`,
`BACKLOG.md`, and the bundled scripts under `hooks/scripts/` and `skills/*/scripts/`. Nothing in
Orclab lands a branch; the only hits for merging are `orc-git`'s `pr` subcommand, which checks a
pull request out rather than landing it.

**Resolved 2026-09-10 — folded into v14 as `/orc-git merge <branch>`, decided by direflail
between three shapes.** It merges locally with the test suites as gates before and after, removes
the branch's worktree and deletes the branch with `-d`, and decides nothing about whether merging
was the right way to land — that question stays with a person, or with
`superpowers:finishing-a-development-branch`, which asks it. Typing the subcommand is the answer
"merge it locally," the same argument `push` makes for itself. The alternative, a `/orc-git land`
wrapping that skill's menu, was rejected as a name that adds no capability plus an availability
guard for the thing it wraps. The 2026-09-10 session that decided this had landed four branches
by hand, each with the same seven steps the subcommand now performs.

## #29: a bare YAML scalar in action: or metrics: aborts the whole run instead of failing one leaf (RESOLVED 2026-09-10)

Found by v13's own final whole-branch review (2026-09-09), with a live reproduction, and
deliberately scoped out of that branch's fix wave rather than smuggled into it.

`action: true` in a `channels.yaml` leaf is valid YAML and parses as a Python `bool`. Two things
then happen, neither of them the tool's stated behaviour:

- `cli.action_shape_warning()` does `action = leaf.action or ""`, and `True or ""` is `True`, so
  the next line calls `.rfind()` on a bool and raises `AttributeError`.
- `cli._run()` passes it to `subprocess.Popen(command, shell=True, ...)`, which with a non-str,
  non-bytes argument does `list(args)` and raises `TypeError: 'bool' object is not iterable`.

**The concrete consequence is not a bad publish - it is that one malformed leaf takes the whole
run down.** `/orc-publish` continues past `failed`, `timed out` and `refused` everywhere else, on
purpose, so a healthy sibling channel still publishes and still reports. Here the traceback
escapes `execute_plan` entirely: no summary is printed at all, and a sibling leaf that would have
succeeded is never even attempted. Verified live on v13's branch against `confirm.command`, which
shares `_run`.

**This is a known class in this codebase, already fixed once at a different site.** `tree.py`'s
`preflight` property carries a long docstring about exactly this: a non-string scalar
(`preflight: 5`) used to raise `TypeError` out of the property "ahead of every caller's own
containment, so one malformed leaf aborted the whole run and its healthy siblings never executed."
The fix there was to make the property refuse to crash and leave refusal to the caller. `action:`
and `metrics:` never got the same treatment.

**Why v13 fixed only its own field.** v13 added `confirm.command`/`confirm.url` and shipped a type
guard inside `confirm_error`, which already runs before anything executes. Extending that guard
outward to `action:` and `metrics:` in the same branch would have been a different change with a
different blast radius - every existing `channels.yaml` in the world is validated by it - and the
review's own triage said so: file the wider case separately, and fix it at the one place all three
converge rather than as three guards.

**The candidate fix, not a decision:** a shared "is this a usable command string" check applied
where the command is read, so a malformed leaf is refused with a real message and its siblings
still run. The open question is where that belongs - `Node.command()`, a `command_error(leaves)`
sibling to `timeout_error`/`confirm_error`, or inside `execute_plan`'s per-leaf loop so the refusal
lands as a normal `(leaf, status, detail)` result rather than a pre-flight error. Only the third
preserves "one bad leaf, everything else still runs", which is the property this entry is about.

**Scope boundary:** this is about a leaf whose command is not a string. It says nothing about a
command that is a valid string and simply fails, which is already handled correctly.

**Searched before filing**, per CLAUDE.md: every shipped `skills/*/SKILL.md`, `CLAUDE.md`,
`BACKLOG.md`, `hooks/scripts/` and `skills/*/scripts/`. `tree.py`'s `preflight` property is the
only place the class is handled; nothing covers `action:` or `metrics:`.

**Resolved 2026-09-10 — the second candidate, not the third, chosen by direflail.** A
`command_error(leaves)` sibling to `timeout_error` and `confirm_error`, run in the same place
before anything executes: a non-string `action:`, `metrics:` or `prepare:` is refused with
`<leaf>: <key> must be a command string, got <value>`, exit 1, nothing run. `prepare:` was added
to the entry's two because it reaches `_run` the same way and had the same hole.

**Why the whole-run refusal, against the entry's own lean.** The entry framed the property as
"one bad leaf, everything else still runs," which is how a command that *runs and fails* is
treated. But a non-string command is not a failed run, it is a malformed declaration — the class
`timeout_error` and `confirm_error` already handle, and both stop the run before anything
happens. Making this one field behave differently would be a distinction nobody would remember.
And a publish is irreversible: letting the healthy siblings go out and then re-running after the
typo is fixed means re-publishing what already went. Stopping first is the safer default. The
real defect the entry recorded — a traceback escaping with no summary printed — is gone either
way. Both live crashes (`rfind` on a bool in the dry-run plan, `Popen` on an int in the real run)
are reproduced by the tests and closed by the one check.

## #30: /orc-todo's allocator writes to the canonical checkout, which is right for BACKLOG.md and wrong for a feature branch's VERIFICATION.md (RESOLVED 2026-09-10)

Hit for real 2026-09-09 while executing the v13 plan in a git worktree. Task 5 ran
`/orc-todo add verification ...` from inside the worktree; the allocator resolved to the shared
canonical checkout and wrote the new scenario into `/home/direflail/projects/orclab/VERIFICATION.md`
- on `main`, describing a `confirm:` field that existed only on the branch. The implementer noticed,
reverted the stray edit on main, and replicated the allocator-assigned scenario (#47) into the
worktree's own copy. Verified afterwards: main was clean, the worktree's file correct, and the
number genuinely consumed so it can never be reissued.

**This is v16's design working exactly as specified, not a bug in the allocator.** One canonical
file is the whole answer to #22 and #25 - two agents scanning the same file at the same time both
found the same highest N and both wrote it. Routing every writer to the canonical checkout is what
makes the counter authoritative. Nothing here proposes changing that.

**The finding is that the two resources want different things from it.** A `BACKLOG.md` entry is a
finding about the project, true the moment it is written, and belongs on main immediately - that is
why writing it uncommitted to the canonical file is right. A `VERIFICATION.md` scenario written
during feature work describes behaviour that does not exist yet outside the branch. Landing it on
main early advertises a check nobody can run.

**The number and the text want different homes, which is the shape of the answer.** The allocation
must stay canonical - that is the anti-collision property, and it worked here. The prose arguably
belongs on the branch, arriving on main when the feature does. What the workaround did by hand -
take the number from the shared counter, write the text on the branch - may simply be the correct
behaviour, in which case the fix is for the command to do it rather than for a person to notice.

**Cost of leaving it:** whoever hits this next has to notice it at all. This session's implementer
did, and said so; a session that did not would leave main describing an unshipped feature, and the
error would be invisible because both files are plausible.

**Options, none chosen:** teach `add verification` to write into the invoking worktree while still
allocating from the canonical counter; or leave the behaviour and document it in `orc-todo`'s
SKILL.md so it is a known property rather than a surprise; or decide scenarios are canonical too
and that landing early is acceptable. The third is defensible and would need no code.

**Scope boundary:** `BACKLOG.md` is not in question. Its canonical-write behaviour is correct and
should not change. This is only about `VERIFICATION.md`, and only about where the text lands.

**Related:** #26 records a session where an allocated entry landing on main's branch rather than a
feature branch was reported as though it followed obviously, when it only follows if you already
know a worktree exists per plan. This entry is that same property, met from the other direction.

**Searched before filing**, per CLAUDE.md: `skills/orc-todo/SKILL.md`, `skills/backlog-discipline/
SKILL.md`, `CLAUDE.md`, `BACKLOG.md`, and the scripts under `skills/orc-todo/scripts/`. The
canonical-root behaviour is implemented in `orc_todo/state.py` and documented nowhere as a
worktree-facing consequence.

**Resolved 2026-09-10 — the first option, chosen by direflail.** The command now does what the
v13 implementer did by hand: the number still comes from the shared counter, and a verification
scenario's text goes into the checkout the command ran in. `Resource` carries one new field,
`canonical_text`, true for backlog and false for verification; `allocate.target_file` picks the
file from it; `next_number` scans both the canonical file and the target so a lost counter
cannot reissue a branch-only scenario. `BACKLOG.md` is untouched, as the scope boundary said.

**One consequence the entry did not foresee.** `hooks/scripts/backlog_guard.py` stayed silent in
any worktree, on the premise — its own docstring — that "the allocator writes canonically, so an
uncommitted entry normally lives there." Once scenarios land on the branch, a `git reset --hard`
there would have discarded one unprotected. The fix was a deletion: `uncommitted_entries` diffs
the tree the command runs in rather than the canonical root, and `in_canonical_checkout` and
its gate are gone. In the main checkout that is the same tree as before; in a worktree it now
guards what that tree actually holds, and still never denies a reset over an entry the tree
does not contain. `lane_notice.py` shares the helper and so now reports a session's own tree's
uncommitted entries rather than main's — which is the only ones that session could commit.

Confirmed live on itself: Scenario 48 was added from this fix's own worktree with the branch's
`run.py`, and landed in the worktree's `VERIFICATION.md` with main's untouched. Done directly,
without a spec or plan, on #27's precedent for fixes of this size.

## #31: disable-model-invocation is per-skill, and /orc-git now holds both families (RESOLVED 2026-09-10)

Found while planning v14 (2026-09-10) and confirmed by its final review; kept out of that plan's
scope deliberately so it would not be changed silently in either direction.

`CLAUDE.md`'s `disable-model-invocation` section names the "real fit for Orclab" as *"anything
genuinely one-shot and side-effecting the moment it runs — `/orc-git release` (pushes and
publishes), `/orc-git push`."* Neither `skills/orc-git/SKILL.md` nor `skills/orc-version/SKILL.md`
sets the flag. `grep -l 'disable-model-invocation' skills/*/SKILL.md` finds only `orc-package`,
`orc-publish` and `orc-release` (2026-09-10). So the guidance and the frontmatter have disagreed
since v4, and the design checklist's item 2 — which every new `/orc-*` is supposed to answer —
was answered "default" for `/orc-git` without the reasoning being recorded anywhere.

**v14 turned an oversight into a granularity problem.** The flag is per-*skill*, and `release`
now lives in the same skill as `commit`, `branch` and `switch` — the conversational, ambiently
useful subcommands. Setting the flag on `/orc-git` to protect `release` and `push` would hide the
whole command from ambient matching: "commit this for me" would stop reaching it. Not setting it
leaves two irreversible, outward-facing subcommands reachable by Claude's own judgment, which is
exactly what the flag exists to prevent.

**Options, none chosen:** (a) accept the status quo and rewrite the `CLAUDE.md` sentence so it
stops naming subcommands the flag cannot isolate; (b) split the side-effecting subcommands into
their own skill (`orc-git-release`? — the naming is the objection, and it is the `commit`/`cp`
alias problem in reverse); (c) rely on the subcommands' own text ("invoking it is the
authorization") plus the fact that ambient matching lands on the *skill*, not a subcommand — a
Claude that ambiently reaches `/orc-git` still has to choose `release`, which the skill's own
routing does not do for it. Option (c) may already be the real answer; if so, (a) is the fix.

**Scope boundary:** this is about the three skills named above and the `CLAUDE.md` sentence. It
does not reopen the determinism spectrum itself, which is settled.

**Searched before filing**, per CLAUDE.md: `CLAUDE.md` (the section quoted), every
`skills/*/SKILL.md` frontmatter, `BACKLOG.md`, `hooks/scripts/`. Nothing tracks it; the v14 plan's
Global Constraints is the only place it is written down, and a plan is not a tracker.

**Resolved 2026-09-10, the same day, by direflail — none of the three options as written.** Asked
who wrote the `CLAUDE.md` sentence: `9f64d88`, 2026-09-06, the commit that created the file, empty
body, four days before `/orc-git` held a `release`. An illustration of what the flag is for that
later read as a requirement. direflail's ruling: *"i don't think it's reasonable that you can't
call these commands when you feel you need to. i do feel like you do need to ask."*

**What shipped:** one rule with two cases, carried inside the irreversible subcommands rather than
as a per-skill flag. If the user typed the command, it runs. If Claude reached for it — the user
asked for something else and Claude decided this subcommand was the way — Claude says exactly what
it is about to run and waits for a yes. `skills/orc-git/SKILL.md` gains a "Whose idea was it"
section stating it once; `push`, `merge` and `release` each point at it in place of their old "no
confirmation prompt — invoking it is the authorization" line, which was true for one case and
silent about the other. `CLAUDE.md`'s paragraph now names the skills that genuinely fit the flag
(`/orc-publish`, `/orc-release`, `/orc-package`, all of which carry it), records why `/orc-git`
does not, and points at the two-case rule as the reference form.

**Why this is better than (a), (b) or (c).** (a) fixed the sentence and left the ask unstated; (b)
bought a flag at the cost of a second command; (c) argued the routing already protects. The ask is
what direflail actually wanted, and Claude always knows which case it is in — so unlike the flag,
it is a rule that can be applied per subcommand, and unlike #26's rules, its trigger is a concrete
event ("about to run `git push`"), not a property of prose. Still prose, and no hook can enforce it
today: the hooks interface has allow/deny and no "ask" (checked against the live docs 2026-09-09,
per `hooks/scripts/backlog_guard.py`). If that changes, a PreToolUse hook on `git push` and
`gh release create` is the mechanical form.

## #32: write documentation for all the commands, in simple language with clear explanations

Requested by direflail 2026-09-10, via `/orc-todo add`. Orclab has ten `/orc-*` commands
(`orc`, `orc-code`, `orc-git`, `orc-help`, `orc-package`, `orc-publish`, `orc-release`,
`orc-reload`, `orc-todo`, `orc-version`) and no documentation written for the person who will
type them. What exists today:

- `README.md`'s "Commands" section: one dense paragraph per command, written from the builder's
  side. It leans on words a first-time user has no way to unpack — "an allocator holding a lock
  over one canonical file", "applying an *ingredient*", "a position cursor" — and several
  entries end with "Ships as a skill only — see `CLAUDE.md` for why", which points a user at
  Orclab's own internal workshop notes.
- Each `skills/<name>/SKILL.md`: the instructions Claude follows to run the command. They are
  addressed to Claude, not to a user, and a user only sees them by opening the plugin cache.
- `docs/` holds only `docs/superpowers/` (specs and plans) — design records, not user docs.

The concrete consequence: someone who installs Orclab and runs `/orc-help` gets a synopsis, and
the next place to look for "what does this actually do, what will it ask me, what will it never
do on its own" is the README paragraph above, which assumes they already know how the thing is
built. `/orc-git`'s "if it was Claude's idea, it asks first" rule, `/orc-todo`'s "add never
commits", `/orc-version`'s "never pushes" — the properties a user most needs to trust a command
are stated, but in the builder's vocabulary and mixed in with implementation detail.

The ask is one document (or one per command — that is a design call for the spec) that a person
who has never opened `SKILL.md` can read: for each command, what it is for, what you type, what
it will ask you, what it changes, and what it will not do without asking. Plain words, no
`CLAUDE.md` pointers, no lock/allocator/ingredient vocabulary unless it is explained on the spot.
`CLAUDE.md`'s "explain it again from the reader's side" section is the standard the writing has
to meet; the README's current paragraphs are the before-picture.

Scope boundary: this is not about `CLAUDE.md`, which is deliberately Orclab's internal notes and
stays that way, and not about the `SKILL.md` bodies, which are Claude's instructions and are
correct as they are. It is a new, user-facing layer on top of both.

## #33: Orclab ships researched platform knowledge for every store and stack it targets — reversing v15's "capture is how they arrive" (RESOLVED 2026-09-12)

Decided by direflail 2026-09-11, in a brainstorming pass on iOS and Android publishing. The
argument: Orclab should carry accurate, at least base-level, knowledge about every platform it
can publish to *before* anyone ships through it. Not having that has cost Orcshot two refactors
so far (one in progress as this is written) — arriving at a store with no baseline, building
against assumptions, and rebuilding when the store's actual rules turned out to differ.

**What this reverses.** The v15 `/orc-package` spec (2026-09-08) lists as an explicit non-goal:
"Ingredients for snap, Flathub, npm, App Store, Play, winget. Nobody here has published to them.
Writing recipes for stores we have not used would be inventing. Capture is how they arrive." That
rule guarded against *invented* knowledge — instructions written from memory that look as
authoritative as ones learned live. What direflail is asking for is *researched, live-verified*
knowledge under `currency-discipline`, with dated stamps. The v15 wording blurred "not used" into
"not known"; those are different states. The non-goal is amended in the spec (same commit as this
entry) to: an ingredient for a store nobody here has shipped through is researched and
live-verified, carries a marker saying no release has gone through it, and is corrected by
capture on first real use. Capture stays; its job changes from "how knowledge arrives" to "how
the first real release corrects what research got wrong."

**Where the knowledge lives — two boxes, one existing and one new.**

1. *Channel knowledge* — Play Store, App Store, snap, Flathub, and the PPA update — lives in
   `skills/orc-package/ingredients/<channel>/ingredient.md`, the shape that already exists. Store
   governance (privacy declarations, data-safety forms, age rating, signing requirements, review
   guidelines, target-SDK deadlines) is *channel* knowledge: it is the store's rule, stated once,
   here. A Flutter app, a Kotlin app and a Unity game all publish through the same two mobile
   ingredients.

2. *Stack knowledge* — Android native, iOS native, Flutter/Dart now; Unity and Godot later —
   lives as **background knowledge skills**: `skills/stack-<name>/SKILL.md` with
   `user-invocable: false`. This is the documented Claude Code shape for exactly this case
   (`CLAUDE.md` quotes the docs' `legacy-system-context` example). Chosen over the alternative —
   stack files under `skills/orc-code/` read only at scaffold time — because the Orcshot
   refactors happened when knowledge was absent *at the moment a decision was made*, and most
   decisions are made mid-development, not at scaffold. A file only `/orc-code` reads reproduces
   that failure mode; a skill whose description sits in every session's context does not.
   `/orc-code`'s Defaults Table gains a row per stack that points at the skill.

   Each stack skill states the current accepted toolchain, project layout, how it produces each
   platform's artifact, and — the cross-reference that prevents the refactors — *where in this
   stack's build each store rule lands*. The rule itself is not repeated; the stack skill points
   at the channel ingredient.

**Games are stacks, not stores.** Mobile games publish through the same two channel ingredients.
The differences direflail expects but cannot yet name (controls, a desktop sibling with different
input) will live in the Unity and Godot stack skills when those are written. No third kind of
thing is needed. Not in focus now.

**Currency.** The mechanism is the one the PPA ingredient already uses: every claim carries a
"confirmed live YYYY-MM-DD" stamp, and `currency-discipline` governs re-checking before use.
Nothing more is built until that proves insufficient.

**Sequence agreed:** settle storage (this entry) → research each platform live → write the
ingredients and stack skills → build a first Flutter app in a separate session, which is the
first real test of both. Orcshot's in-progress apt/snap/flatpak work will be handed over in the
PPA ingredient's section shape, as the form to fill.

**Partially resolves #4:** cross-platform mobile is Flutter + Dart; cross-platform games are
Unity and Godot. Android native and iOS native are wanted alongside, not instead. Which native
toolchains are "current accepted" is what the research pass determines.

Scope boundary: this changes what Orclab *ships*, not what `/orc-publish` or `/orc-package` *do*.
`/orc-publish` stays channel-agnostic and executes whatever the leaf says; `/orc-package` applies
an ingredient the same way whether it was researched or captured. Neither command's code changes
for this entry.

**Progress 2026-09-11, same day — the mobile half is written.** Research and writing ran in one
session: the Play and App Store channel ingredients (`7e9c227`), then `stack-flutter`
(`fe93b8a`), `stack-android-native` and `stack-ios-native` (`ff0df3a`). Two things the research
changed about the design, recorded here so the entry stays true:

- *The ingredient shape moved.* Both stores have a stage between "the account exists" and "every
  release" — a store listing, privacy declarations, Play's 12-testers-for-14-days gate, Apple's
  age rating and EU trader status. The PPA-derived eight sections had no place for it, so
  ingredients now have nine: `## 5. Per-app setup`. Section 1 also states what machine can build
  the artifact, because the App Store needs macOS and nothing before it had a platform
  requirement.
- *The cross-reference is load-bearing, not decorative.* Every stack skill ends up with a table
  mapping each store rule to a file and a check. Two findings from writing them are exactly the
  kind of thing the Orcshot refactors came from: a fresh Flutter 3.47 project already meets Play's
  target-SDK and 16 KB rules (defaults read from Flutter's own source), and *neither* Flutter's
  nor Xcode's app template ships the App Store's mandatory `PrivacyInfo.xcprivacy`.

**Later the same day:** direflail asked for Unity and Godot after all; `stack-unity` and
`stack-godot` landed (`2c3e4de`), thinner by design. One finding worth its own line: Godot's iOS
export *generates* the App Store privacy manifest from preset options, where Flutter, Xcode and
Unity all leave it to be added by hand.

**The snap and Flathub ingredients arrived by a different route than expected, and were committed
by accident.** They were first named as living under `orcshot/skills/orc-package/ingredients/`,
where nothing existed. The Orcshot session wrote them directly into *this* tree instead, between
two of the commits above, and the `git add -A` in `2c3e4de` swept both files into the game-stacks
commit — whose message does not mention them. Recorded here so the history reads right: `2c3e4de`
carries four new files, not two. Two small reconciliations were made afterwards: each leaf gained
the `metrics:` command `/orc-publish` had already verified (Flathub live, Snap against the
reference) instead of its own "verify at first use" note, and each section 1 gained the
"Built on" line the nine-section shape requires.

Still open under this entry: the first real release through any of the researched ingredients,
which is what turns "researched" into "proven" and is the reason this entry is not resolved — and
the `ego` / `spices` follow-up in the next paragraph.

**Update 2026-09-11 (late) — snap and flatpak ingredients written; follow-up owed.** Both live in
`skills/orc-package/ingredients/{snap,flatpak}/`, in the nine-section shape, from Orcshot's
research that day: Snap's login/name registration/`review-tools` run were real, the upload was
not; Flathub is from its live docs plus a real sandbox test, with no submission yet. direflail's
standing instruction on committing them: **update the ingredient lists once Orcshot's #205 and
#198 resolve.** Concretely, when Orcshot's first real snap upload, Flathub submission,
extensions.gnome.org upload and Cinnamon Spices PR have gone through: (1) correct `snap` and
`flatpak` with whatever the real run contradicted (the "verify at first use" markers name the
spots — metric names, the Flathub manifest `sed` shape, moderation-hold behaviour); (2) write the
two ingredients deliberately not written from research alone, `ego` (GNOME Shell extensions via
`gnome-extensions upload`, needs GNOME Shell ≥ 50 on the publishing machine) and `spices`
(Cinnamon applets via PR to `linuxmint/cinnamon-spices-applets`), from the captured runs; (3)
drop the "no release has gone through this" marker from each. Orcshot's spec
`docs/superpowers/specs/2026-09-11-snap-compliant-extension-delivery-design.md` §5 holds the
leaf shapes those two ingredients will start from.

**Resolved 2026-09-12 — the deliverables are written and the rule now lives where it fires.**
Asked whether the "first real release" condition above was a real reason to keep this open,
direflail said no: this entry was meant as guidance — research any new platform or language
before Orclab is used with it — not as an ongoing tracker, and some projects will only ever be
private and never released, so a release-gated closure would never arrive. Checked the tree: all
five ingredients (`app-store`, `play`, `ppa`, `snap`, `flatpak`) and all five stack skills
(`stack-flutter`, `stack-android-native`, `stack-ios-native`, `stack-unity`, `stack-godot`) exist.
The "proven by a real release" job is done by the marker each unproven ingredient carries in its
own first paragraph (`skills/orc-package/SKILL.md`, "An ingredient for a channel no one here has
shipped through says so"), which the reader of the ingredient sees and this entry's reader does
not. The guidance itself was stated for channels (v15 spec's amended non-goal, `orc-package`
rules) but nowhere for stacks; it is now a section of `CLAUDE.md`, "Before the first project
builds on a stack or ships to a channel Orclab has never met", phrased by the situation so it
fires for a private project too. The one pending action with a real trigger — correcting `snap`
and `flatpak` and writing `ego`/`spices` once Orcshot's #198 and #205 resolve — is split out as
**#37**, so this heading no longer hides it.

## #34: Mutation-testing orc-todo's suite writes test data into the real BACKLOG.md, VERIFICATION.md and .git/orclab — a cwd→None mutant falls back to the process cwd

Found 2026-09-12 by the first real `/orc-test analyze skills/orc-todo/scripts` (v17, Task 19). Until this is fixed, **running mutation testing on orc-todo's suite overwrites the real repo's BACKLOG.md, VERIFICATION.md and `.git/orclab/` state.** It did: after the run the main checkout's BACKLOG.md was a 33-line test fixture (`## #23: t` / `b`), the worktree's VERIFICATION.md had nine "Scenario 62–70: on the branch" stubs appended, `.git/orclab/lock` held `{not json`, `counters.json` said 23 and `lanes.json` held the test lane "B". All restored the same session (main's BACKLOG.md from its commit, byte-identical; `lock clear`; `lane delete B`); the worktree's VERIFICATION.md was still carrying the stubs when Task 19 finished — `git checkout -- VERIFICATION.md # orclab:discard-entries` removes them.

Why. Every orc-todo test isolates itself by building a throwaway git repo under `tmp_path` and passing it as `cwd`. That isolation holds exactly as long as the code honours the argument. mutmut plants, among its ~930 mutants, some forty that replace a `cwd` argument with `None` or drop it (`read_lanes(None)`, `state.held(..., )`, `_write_lanes(data, )` …), and every `cwd=None` path falls back to the process cwd — which during the run is `skills/orc-todo/scripts/mutants/`, inside the real repo. The test then does exactly what it says: allocates a backlog number into the canonical file, appends a scenario to the invoking root's VERIFICATION.md, writes a corrupt lock to see that it still blocks. On the real files. And the mutant survives, because the tmp repo the assertion looks at is untouched.

`test-discipline` rule 4 (Isolation) already says the filesystem is replaced with a fake; the miss is that the fake was supplied as an argument and nothing pinned the ambient state a dropped argument falls back to. Task 19 widened that rule by a sentence. The fix in orc-todo's tests is one autouse fixture in `skills/orc-todo/scripts/tests/conftest.py` (or the existing empty `conftest.py` at `scripts/`): `monkeypatch.chdir(tmp_path)` into a throwaway `git init`'d dir — then a `cwd → None` mutant lands in the sandbox, where the assertion sees it, and those forty survivors die for free. Not done in Task 19 because the brief says orc-todo's tests are `generate`'s job, in a session of its own; but this one is the precondition for that session, not part of it: run it first, or the `generate` session's own `analyze` calls do the damage again.

Also worth a line in the shipped skill: `/orc-test analyze` runs the project's suite hundreds of times with the code deliberately broken, so a test that reaches anything outside its temp dir will, under some mutant, reach the real thing. `languages/python.md` carries this now; the other seven `languages/*.md` should say it when their first real run lands.

## #35: orc-todo's tests run the code but do not pin it: TCE 68.6%, the specific gaps

Found 2026-09-12 by the first real `/orc-test analyze skills/orc-todo/scripts` (v17, Task 19): coverage 95.3%, TCE 68.6% — 637 of 928 mutants killed, 291 survived, gate 70. Coverage is high and the score is just under the gate, which is the shape `analyze` exists to expose: the lines run, the assertions do not pin them. The survivors list (in `.orclab/test/analyze.json` after a run; the numbers are in `skills/orc-test/languages/python.md`) sorts into real gaps and noise.

The real gaps, by what a test would have to do:

- `lane delete` and `lane current` are never exercised through the CLI (`cli.cmd_lane`, 56 survivors). Every mutation of those two calls survives — arguments swapped for `None`, dropped entirely — and so does inverting the "no lanes yet" branch of `lane list`. The `-` that clears a lane's current item is never sent through the parser.
- `lock` subcommand: `return 0` → `return 1` and the inverted `if not info["alive"]` both survive (`cli.cmd_lock`), so its exit codes and the stale-vs-running branch are unproven; `state.lock_info`'s `started`/`age_seconds` are never asserted at all.
- `list`: inverting `if not open_entries` survives, and so does `mark = None` for the "(in progress: …)" suffix — a listing with an in-progress lane is never checked.
- The `--cwd` plumbing: some forty `cwd` → `None` mutations survive across `allocate`, `lanes` and `cli`, because every test runs with the process cwd equal to the default. One test per layer that passes an explicit `cwd` different from `os.getcwd()` would kill all of them.
- Whitespace normalisation in `resources.insert` and `cli.cmd_remove`: `rstrip("\n")` → `rstrip(None)`, `at + 1` → `at + 2`, `find` → `rfind` survive; the blank-line contract is pinned only for the one happy input shape (no trailing spaces, anchor appearing once).
- `allocate(..., timeout=)` is never propagated: dropping the `timeout` argument to `state.held` survives, as does the `ResourceMissing` message.
- `build_parser`: `required=True` on all three subparser groups survives — nothing checks that a bare `orc-todo`, `orc-todo lane` or `orc-todo lock` errors.

The noise: mutmut mutates every string literal three ways and every keyword argument to `None`, so `cli.py`'s messages (172 of the 291) and the `held(...)` lock descriptions are survivors that no test should chase; read the list for branch, comparison and argument mutations.

Fixing this is `/orc-test generate`'s first real use and should be its own session, per the Task 19 brief — not a side quest of v17's landing. Rerun `analyze` on the same path afterwards; the before → after is the point.

## #36: GDScript has no mutation-testing tool, so /orc-test cannot measure TCE for Godot projects (UPDATED 2026-09-12 — a tool exists; re-scoped to adopting it)

Found researching v17 (2026-09-11): Python, JS/TS, Java, Kotlin, C#, Dart and Swift each have at
least one mutation tool; GDScript has none — searched GitHub, the Godot Asset Library and the
awesome-mutation-testing list. `/orc-test analyze` therefore reports "TCE not measurable — no
mutation tool exists for GDScript" in words rather than a number (spec: never a fake number).

What would close it: any tool that mutates `.gd` files and re-runs gdUnit4 or GUT. When one
appears, `skills/orc-test/languages/gdscript.md` gets a Mutation row, `langs/gdscript.py`'s
`mutation_unavailable` returns None when it is installed, and this entry is resolved. Until then,
`test-discipline` rule 5 (break the code by hand once, watch the test go red) is the only TCE a
Godot project gets, and `/orc-test` says so.

**Numbering note.** v17's Task 18 first allocated this finding #34 (2026-09-12, uncommitted in
the main checkout). The incident recorded as #34 — a mutation run that replaced the main
checkout's BACKLOG.md with a test fixture — destroyed that uncommitted entry, the file was
restored from its last commit, and #34 was reissued to the incident itself before anyone noticed
the first allocation was gone. The allocator's "never reissued" rule held as far as it could see:
the number it lost was in a file that no longer existed. This entry is the same finding, renumbered.

**Update 2026-09-12 — the premise is wrong; a tool exists.** Asked whether anything was in
development so this could be closed, a fresh search found `gdmutant` (PyPI, MIT,
https://github.com/kphutt/gdmutant): "Mutation testing for GDScript and Godot: find the bugs your
green tests would miss." v0.1.2 was released 2026-08-07 — a month *before* the 2026-09-11 search
above recorded "none exists". It was missed because it is tiny (2 stars, one maintainer) and lives
on PyPI, not the Godot Asset Library or the awesome-mutation-testing list that search covered.
Checked live against PyPI and the GitHub README on 2026-09-12: Godot 4.3+ (verified on 4.7.0),
both GUT 9.x and gdUnit4 6.x via `--runner gut|gdunit4`, `pip install gdmutant`, prints a
mutation score ("Mutation score: 61.1% killed: 11 timeout: 0 survived: 7"), and `--json` writes
the mutation-testing-elements schema — the same Stryker report format
`skills/orc-test/scripts/orc_test/stryker.py` already parses for JS, C# and Dart.

So this entry meets its own closing condition ("any tool that mutates `.gd` files and re-runs
gdUnit4 or GUT") and is re-scoped from "no tool exists" to "adopt gdmutant". The work is what the
original text predicted, and the parser half is already written: a Mutation row in
`skills/orc-test/languages/gdscript.md`; `langs/gdscript.py`'s `mutation_unavailable` returning
None when `gdmutant` is on PATH; `mutation_cmd` building `gdmutant run <target> --project <root>
--runner <gut|gdunit4> --json` (GUT needs `--tests res://test/unit` spelled out, gdUnit4 does
not); `mutation_parse` calling `stryker.parse`. Same shape as `langs/csharp.py`.

Caveat that shapes the work, not whether to do it: gdmutant is a one-month-old 0.1.x from a single
maintainer. Wire it as optional — `mutation_unavailable` already makes an absent tool plain words
rather than a fake number — and before resolving, actually install it and run it against a small
gdUnit4 project headless; a README claim is not the same as it working. If it goes unmaintained,
Godot projects fall back to exactly what they get today.

## #37: Correct the snap and flatpak ingredients from Orcshot's first real runs, and write ego and spices from the captured ones

Split out of #33 on 2026-09-12 when that entry was resolved: #33 was a decision and a day's
writing, and this is the one pending action it carried that has a real trigger of its own.

The `snap` and `flatpak` ingredients under `skills/orc-package/ingredients/` were written
2026-09-11 from Orcshot's research: Snap's login, name registration and `review-tools` run were
real, the upload was not; Flathub is from its live docs plus a real sandbox test, with no
submission yet. Both carry "verify at first use" spots — metric names, the Flathub manifest `sed`
shape, moderation-hold behaviour — that only a real run can settle.

**Trigger: Orcshot's #198 (first real Snap Store upload and Flathub submission) and #205
(GNOME Shell extension delivery via extensions.gnome.org, and the Cinnamon Spices PR) resolve.**
Checked 2026-09-12: neither is; Orcshot's latest work is the XApp tray (#208, #211). Nothing
here can move until they do, and nothing in Orclab is blocked on this in the meantime.

direflail's standing instruction, given 2026-09-11 when the two ingredients were committed, is
what to do then: (1) correct `snap` and `flatpak` with whatever the real run contradicted; (2)
write the two ingredients deliberately not written from research alone — `ego` (GNOME Shell
extensions via `gnome-extensions upload`, needs GNOME Shell ≥ 50 on the publishing machine) and
`spices` (Cinnamon applets via PR to `linuxmint/cinnamon-spices-applets`) — from the captured
runs, starting from the leaf shapes in Orcshot's
`docs/superpowers/specs/2026-09-11-snap-compliant-extension-delivery-design.md` §5; (3) drop the
"no release has gone through this" marker from each ingredient a release actually went through.

Scope boundary: this is Orcshot-gated ingredient maintenance only. The rule that new stacks and
channels are researched before first use now lives in `CLAUDE.md` ("Before the first project
builds on a stack or ships to a channel Orclab has never met"), not here.

## #38: app-store ingredient still says GitHub macOS minutes are billed at 10× — wording GitHub retired; two stack skills now say otherwise (RESOLVED 2026-09-12)

`skills/orc-package/ingredients/app-store/ingredient.md`, section 1 (line 33), lists the cloud-Mac options for a Linux developer and describes GitHub Actions macOS runners as "minutes are billed at 10×". That sentence reads as a fact about GitHub's current billing, and it is not one any more: the v18 stack skills, checking GitHub's pages live on 2026-09-12, found that `https://docs.github.com/en/billing/managing-billing-for-your-products/about-billing-for-github-actions` and `https://docs.github.com/en/billing/reference/actions-runner-pricing` now give only a per-minute rate table — macOS **$0.062/minute** against Linux **$0.006/minute**, a ratio of about 10.3× — and no longer document a multiplier applied to a plan's included minutes at all. Both `skills/stack-flutter/SKILL.md` (`### Building without a Mac`) and `skills/stack-ios-native/SKILL.md` (the same section) now record exactly that: "GitHub's pages once documented a 10x multiplier on included minutes for macOS; the current pages give only the rate table, so whether the 2,000 free minutes deplete at the macOS rate is not stated." So the ingredient and the two skills that point at it disagree about what GitHub says, and a reader who compares them cannot tell which is current.

It was not fixed on the v18 branch because the spec (`docs/superpowers/specs/2026-09-12-orclab-v18-project-type-defaults-design.md`, §7) leaves every `orc-package` ingredient unchanged; that branch only writes stack skills and the `/orc-code` Defaults Table. The fix is one line in the ingredient's section 1 — replace "minutes are billed at 10×" with the rate-table wording the two skills use ($0.062/min macOS vs $0.006/min Linux, ≈10.3×; the included-minutes multiplier is no longer on GitHub's pages) — plus the ingredient's "checked against live sources" stamp, since that line is the only thing in it that the stack skills' 2026-09-12 fetch contradicts.

**Resolved for real, not just tracked** (2026-09-12): section 1 of the ingredient now carries the rate-table wording — $0.062/minute macOS against $0.006 Linux, about 10.3×, with the retired included-minutes multiplier named as retired — and the opening stamp records the 2026-09-12 GitHub check beside the 2026-09-11 Apple one. `grep -n "10×" skills/orc-package/ingredients/app-store/ingredient.md` now matches only the corrected line, so the ingredient and the two stack skills agree.

## #39: v18 stack-skill polish: three wrong page dates in the KMP skill, stale game-skill openers, and the citation tidy-ups the final review parked (RESOLVED 2026-09-12)

Left over from v18's final whole-branch review (2026-09-12), which allowed one fix wave and one
re-review; these are the items ruled real but not load-bearing — none changes a default or a
concern line — and parked rather than opening a second wave. Each is a few minutes with the file
open; none needs new research except where a live look is named.

- `skills/stack-kotlin-multiplatform/SKILL.md` ~145–146 and ~149: three kotlinlang.org page dates
  are the site's `built-on` build stamp, not the page's `last-modified`. Live on 2026-09-12: the
  native-distribution page is 25 August 2026, the tray page 18 August 2026; the overview's
  "2026-09-10" was not checked. Same mistake the fix wave corrected at ~122/137 for the
  stability page (10 September 2025).
- `skills/stack-godot/SKILL.md` ~13–15 and `skills/stack-unity/SKILL.md` ~13–16: the openers
  still say the game-specific questions are "named and left open"; `## Scope divergence` now
  answers them from the engines' docs. One sentence each.
- `skills/stack-flutter/SKILL.md` `## Presence`: unbuilt marker only in Presence, not UI/Storage;
  one `### Linux, Windows, macOS` heading where the sibling skills split per platform; a stray
  comma near the libayatana line; "its fork" ambiguous near the `system_tray` concern. Also: the
  tray default rests on `libayatana-appindicator3`, whose upstream `stack-python-desktop` ~242
  records as marked OBSOLETE — Flutter's section does not carry that concern (`nativeapi` is
  already named as successor). And `## Choosing dependencies` says to run three store checks
  before adding any native plugin; the four plugins the facet sections recommend have not had
  them run — the first real build is the moment.
- `skills/stack-flutter/SKILL.md` ~25–26 and ~365 (pre-existing, 2026-09-11): "their own stack
  skills, when written" for Godot/Unity/Kotlin/Swift — all four exist now.
- `skills/stack-ios-native/SKILL.md` ~105: Codemagic "Xcode 26.6 default, 27.0 as `edge`" has no
  URL in Sources (came from site navigation); add the machine-spec page or drop the version.
- `skills/stack-web/SKILL.md` ~57 vs ~32: alternatives say "React Router v7" (react.dev's label)
  while Toolchain lists 8.3.1; needs a live look at whether react.dev still says "v7".
- `skills/orc-test/`: 14 "Task N of the v17 plan" references shipped in v17 — the same
  SDD-number-in-shipped-text defect v18's review removed from `stack-react-native`. Out of v18's
  scope; noted here so it is not rediscovered.

Ground for the ruling: `docs/superpowers/specs/2026-09-12-orclab-v18-project-type-defaults-design.md`
§5 says each pass writes research, and the plan's subagent-driven process caps fixes at one wave
after the final review. Nothing above moves a table row.

**Resolved for real, not just tracked** (2026-09-12, worked through directly from `/orc-todo show
39`): every item above is applied. The three KMP dates now read from each page's own
`last-modified` footer, fetched live the same day — native-distribution 25 August, tray 18 August,
Wasm overview 01 September 2026 (the `built-on` meta was 2026-09-09/10, confirming the earlier
mistake). Godot's opener now points at `## Scope divergence` the way Unity's already did — Unity's
turned out not to need the change. Flutter: the unbuilt marker now opens UI and Storage too, the
desktop tray is split into Linux/Windows/macOS like `stack-python-desktop`, the stray comma and
"its fork" are gone, the Linux section carries the OBSOLETE upstream concern with `nativeapi` as
the way off it, the "when written" references name the four existing skills, and a closing
sentence records that the four recommended plugins have not had the store checks run. iOS:
Codemagic's spec pages are titled "Xcode 26.6.x (default)" and "Xcode 27.0.x (edge)" live, both
URLs added to Sources. Web: react.dev's heading is still "React Router (v7)" live, and the
alternatives line now says so beside npm's 8.3.1. orc-test: the 14 "Task 19 of the v17 plan"
references (seven `languages/*.md`, seven fixture READMEs) are gone; `grep -rn "v17\|Task 19"
skills/orc-test/` is empty and its 148 tests still pass.
