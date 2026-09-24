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

## #2: A base visual/design-system layer for apps Orclab helps build — a future sub-project, not v1 (UPDATED 2026-09-13 — re-scoped: design tokens with a brand tree and an unbranded default are the foundation and reach all nine stacks; a React component layer comes later, with a React project; first slice is Orctool's skin system)

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

**Update 2026-09-13 — talked through with direflail against what Orclab is now; the entry is
re-scoped.** Three things had changed under it since 2026-09-04:

- **The candidates above are web-only.** Fluent, Carbon, MUI, shadcn, Radix, Chakra are all
  React/web. Since v18 Orclab has nine stacks and one is web; the other eight draw their own
  widgets (SwiftUI, Compose, Flutter, Qt, GTK, the game engines' UI) and none can consume a
  React component. The "compare Fluent vs Carbon vs shadcn" next step would have decided the
  look of one stack and nothing else. It is withdrawn.
- **v18 already made the "full design system" choice per stack, without naming it.** Flutter's
  skill: *"Material 3 is the default design language of Flutter"*; Android is Material 3 via
  Compose; iOS is Apple's HIG via SwiftUI; Python desktop: *"Qt will choose the most appropriate
  style for the user's platform."* Each is a token-driven theme plus a full component set plus
  scaling rules — the entry's own definition of the Blocks layer — and it comes with the
  framework. Blocks exists at Caterpillar because the web has no platform conventions; eight of
  nine Orclab stacks do. So this entry is not "pick a design system"; it is what sits *on top of*
  each platform's own.
- **There is a first real case, and it is one stack.** Orctool (brainstormed 2026-09-13,
  Flutter): *"Skinnable UI; one skin LCARS-adjacent."* A skin is a token set swapped at runtime.
  Orctool's slice 1 is "skeleton + skin system", so the token format and its Flutter translation
  get designed against a real need the moment that spec is written.

**What direflail wants (2026-09-13):** the thing, with **multiple brand identities and subtrees
under them** — the workplace case: a parent company's brand, and subsidiaries branded
separately on the same underlying everything except colours and styling — and an **unbranded
option** when none applies. Not a shared look across their own apps: Orcshot and Orctool have
wildly different interfaces and should keep them. No attachment to Blocks as such; the ask is
"port to as many places as possible", and the leaning toward React from the work so far was
discussed and separated (below).

**The shape, in layers:**

1. **Design tokens with a brand tree — the foundation; the only layer that reaches all nine
   stacks**, including the game engines (Unity's UI Toolkit styles with USS, a CSS-like
   language; Godot has theme resources), because any framework can consume a generated file of
   constants. Structure: `base` is the semantic vocabulary only (`color.surface`,
   `color.accent`, `type.body`, `space.3`, `radius.control`) with no values that are anyone's;
   `brand/<company>` overrides base (palette, type family, radii, mark);
   `brand/<company>/<subsidiary>` overrides the brand, colours and styling only. **Unbranded is
   base only**: every stack falls through to its platform's own theme untouched. Output is
   generated per (brand, stack): one subsidiary's tokens become a Flutter `ThemeData`, a Compose
   theme, SwiftUI constants, a Qt stylesheet or GTK CSS, CSS variables for React. Format: the W3C
   design-tokens spec the entry names; tool: Style Dictionary, the one non-web item in the list
   above, whose own examples I recall include a multi-brand, multi-platform build — both the
   spec's "stable v1, October 2025" claim and that recollection are confirmed live at build time
   under `currency-discipline`, not taken from this entry. A brand fixes colour, type, spacing
   rhythm and radii and says nothing about layout or what is on the screen: two apps on one
   brand read as the same family and can look nothing alike — the subsidiaries' case exactly.
2. **A React component layer — the Blocks analog — later, when a React project exists**, built
   on the tokens so it is brand-aware from birth. Two claims were separated here: *tokens* port
   everywhere; *components* port only within one rendering engine. A React DOM component runs on
   the web and in a web view (Electron/Tauri); React Native is a different renderer, and "one
   library on both" exists only through a universal layer on top (Tamagui, Gluestack,
   react-native-web — a research question for that day, not a fact). At its best the React
   family covers three rows of v18's table (web, the React Native mobile row, multi-platform
   with iOS) and none of Flutter, Compose, SwiftUI, Qt/GTK or the game engines. And v18 lists
   React Native as the mobile default *pending pass 11* — not yet researched — while Orctool
   chose Flutter over it for stated reasons, so a React component layer would not touch
   direflail's first app; only tokens would.
3. **Per-stack rules stay in the stack skills' `## UI` sections**, where v18 put them: how the
   tokens land in that framework, and what the platform's own conventions forbid overriding
   (the brand layer has to be the part that is *allowed* to differ — overriding GNOME's
   conventions on Orcshot would fight Flathub's own guidelines).

**First slice, and how the first brand gets proven:** the token format and the Flutter
translation, designed inside Orctool's slice-1 spec for its skin system. Then the test direflail
asked for: **put Orctool's skin on Orcshot** — the same token set translated to GTK CSS, no
layout change — and look. If it reads as the same family, the brand layer works; if it fights
GNOME's conventions, that is the layer-3 boundary showing itself. A mockup, cheap once the skin
exists; a test of the *brand*, not a plan to reskin Orcshot, which stays unbranded unless
direflail says otherwise. Later translations arrive with the next stack that ships something;
the web one waits for a web project.

Still open; nothing is built until Orctool's slice-1 spec.

**Correction, later the same day — the first slice is already in progress, in Orctool, in
Dart.** `~/projects/orctool` is a Flutter project with a slice-1 spec and plan
(`docs/superpowers/specs/2026-09-13-orctool-slice-1-design.md`) and ten commits, the newest
*"Skins: OrcTheme extension, plain and console skins, Antonio (OFL)"*. What is there is this
entry's shape without a token file: `plain` is Material 3 following the system — the unbranded
case, base only; `console` is a set of overrides — a brand; the spec's rule *"no colour or
radius literal lives outside `skins/`"* is the discipline tokens exist to enforce; and
`OrcTheme`'s eight fields (`accent`, `onAccent`, `panel`, `ground`, `railRadius`, `railStripe`,
`uppercase`, `displayFont` — what Material's theme does not carry and a brand needs to) are the
first draft of the token vocabulary. **So the direction is the reverse of "start #2 on
Orctool": Orctool keeps building skins in Dart, and the token format is extracted from what
`OrcTheme` turned out to need once slice 1 lands.** Do not add a token file or a Style
Dictionary build to Orctool ahead of that — it would be the pipeline built before the case it
serves. The one thing to hold in Orctool meanwhile: `OrcTheme` stays "things a brand sets", with
no per-instrument or layout value creeping in, so the extraction is clean.

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

## #5: `/orc-data` — a command for tracking legacy-system info during refactor work (UPDATED 2026-09-13 — the gap is the database itself, which nothing in code-modernization covers; a step of /orc-code's refactor flows, not a front door; ships the procedure, researches each engine at conversion time)

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

**Note 2026-09-13 (v19):** both commands were run for real on itsdangerous 1.1.0 (#41). `map`
writes a one-off `extract_topology.py` and from it `topology.json` — every module with its LOC
and file, grouped into domains, every import/dispatch edge, entry points, dead-end candidates,
3–7 architect observations, and 2–4 persona flows in business language — plus the plugin's
interactive `TOPOLOGY.html` viewer and three Mermaid diagrams. `extract-rules` writes
`BUSINESS_RULES.md`: one card per rule (category, priority, `file:line`, plain English,
Given/When/Then, parameters, edge cases, suspected defect, confidence and the exact SME question
when below High) with a summary table and an SME-confirmation section, and `DATA_OBJECTS.md`
(entities, fields, which rules consume them, wire formats). On a 1k-line library that was 26
rules and 8 SME questions, every citation checked against the source. Does this cover #5's ask?
**For the structure-and-rules half, yes** — this is the "information about the system being
refactored, organized to support moving it" #5 describes, and it lands in `analysis/<name>/`
under `.orclab/modernize/` with the brief copying the useful parts into `docs/`. What it does
not cover: anything learned *about* the system that is not in its source — environment facts,
who owns what, why a decision was made, the SME's answers to those 8 questions — which the
plugin scatters across `PREFLIGHT.md`'s Check 0 answers, `PLAYBOOK.md`'s "environment facts"
and the brief's open questions, with no single place and no way to add a fact between commands.
If `/orc-data` is built, that residue is its scope: a wrapper over `map`/`extract-rules` for the
source-derived half, plus one file for the human-derived half. Stays open.

**Update 2026-09-13 — talked through with direflail; the entry is now a shape, not a question.**
What the plugin's analysis holds about data, read from its command files rather than remembered:
`map`'s data-dependency graph (which modules read and write which stores, by logical name —
table, schema, dataset — with datastore nodes in `topology.json`) and `extract-rules`'
`DATA_OBJECTS.md` (entities, fields, types, which rules consume them). That is the
*application's* view of its data. Nothing in the plugin treats the database as a thing in
itself — the schema DDL, constraints and indexes, the logic living in stored procedures and
triggers, data volume, moving the data — and its own `architecture-critic` says so: *"What's
the data migration story? 'We'll figure it out' is a finding."* It flags the gap and leaves it.
**That gap is `/orc-data`'s scope, and it is not a wrapper over anything.** The earlier "read
`modernize-map` first, it might already cover this" is answered: it does not.

direflail's intended use (2026-09-13): only when porting another project — "like Greenshot →
Orcshot was, but with data" — or when bringing an old project up to date; never as a
standalone job. Both are `/orc-code refactor`'s modes, so **this is a step inside those flows,
not a front door**: migration mode's step 5 runs it when `topology.json` has datastore nodes
or the tree has DDL, ORM mappings, a migrations directory or embedded SQL (all of which
`assess` and `map` already look for), and its output goes into the brief *before* the human
approves the target architecture — so the critic's question has an answer at the moment it is
asked. A `/orc-data` name can exist to re-run only that step (the same shape as `/orc-test`,
a command `/orc-code` also calls), but nothing in the design assumes anyone types it cold.

Orclab is meant to be public, and other people will meet engines direflail never will. With no
first case in hand, pre-writing `stack-db-oracle`, `-sqlserver`, `-db2`, `-mysql`, `-mongo` from
research would be Orcshot-before-the-stores five times over (`CLAUDE.md`, "Before the first
project builds on a stack … Orclab has never met"). So **what ships is the procedure, which
holds for any engine**: what to find out about the source (the schema as an artifact, the logic
in procedures and triggers, volumes, the constraints the app silently relies on); what to
decide about the target; the fixed set of questions every engine gets — which dialect, what in
it does not translate, the type-mapping table to the usual targets, the migration tooling
(`ora2pg`, `pgloader`, the cloud vendors' schema converters, Flyway/Liquibase for the new
schema's versioning), and how equivalence is proven (row counts, checksums, a dual-run window);
how the answers feed the brief; and the gate before "done." Engine-specific facts are
**researched live at conversion time** under `currency-discipline`, stamped, and **saved into
the consuming project** next to the brief so that project's later sessions reuse them — other
people's research stays in their project, which is where it belongs. An engine met in
direflail's own work gets its research promoted to a real `stack-db-<engine>` skill, the v18
shape, for everyone after.

Still separate, and still untracked: facts about a system that are not in its source — owners,
why a decision was made, the SME's answers to `extract-rules`' questions. Not this entry's
name; it gets its own when something needs it.

**Trigger to build:** the first port or uplift with a data store, direflail's or a spec written
against one. Not before — the procedure needs one real run to be corrected by, the same as
every other component here.

## #6: Per-language manifest version detection/sync for /orc-version — deferred, same reasoning as #4 (PARTIALLY ADDRESSED 2026-09-07 — still open for the formats it names) (UPDATED 2026-09-13 — re-scoped from pom/package.json/Cargo to the version files of Orclab's own stacks; two-number model needed) (UPDATED 2026-09-13 — AppStream metainfo handler shipped for Orcshot 0.4.0; the plan is three steps, this was the first) (UPDATED 2026-09-22 — step 2's trigger moved: orcweather, not Orctool, is the first Flutter project heading for a store) (UPDATED 2026-09-22 — step 2 shipped: pubspec.yaml handled, build number always increments; still open for steps 3's formats)

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

**Update 2026-09-13 — re-scoped, because the formats that matter changed under it.** No project
here uses `pom.xml`, `package.json` or `Cargo.toml` as its version source. v18's nine stack skills
do name what their projects use, and seven of them told a consuming project that `/orc-version`
already edits it — Flutter's `pubspec.yaml` `version: x.y.z+N`, Android's `versionCode`/
`versionName` in `build.gradle.kts`, iOS's `MARKETING_VERSION`/`CURRENT_PROJECT_VERSION` in the
pbxproj, Expo's `app.json`, Godot's `export_presets.cfg` `version/code`/`version/name`, Unity's
`ProjectSettings.asset` `bundleVersion`/`AndroidBundleVersionCode`, KMP's two apps. It edits none:
`versionfiles.py`'s `KNOWN_FORMATS` is still `[PYPROJECT, PLUGIN_JSON, MARKETPLACE_JSON,
DEBIAN_CHANGELOG]`. The seven sentences now say "does not edit this file yet … BACKLOG #6; bump it
by hand and check it before every upload" — a skill that misdescribes a shipped command is fixed
before the command is. `CLAUDE.md`'s "show what it rests on" section now names this case: a claim
about an Orclab component is a claim about code and gets the same pass as a claim about a store.

**What the handlers need that the mechanism lacks:** every store-facing format above carries
*two* numbers — the human version string and a build/version code the store refuses to see
reused. `versionfiles.py` has a one-version model. So the first stack handler brings the model
change with it: `write_version` takes (or derives) the build number, `verify_consistency` checks
both, and a bump that leaves the build number unchanged is refused — the stack skills already
promise that refusal. The entry's own rule still holds: one format at a time, when a real project
on that stack reaches a release; Flutter's single `version:` line is the likeliest and easiest
first case. The first-touch "suggest a starting version from what's already there" half remains
unbuilt too.

**Update 2026-09-13, later the same day — what this entry is for, and the order it gets done.**
direflail asked, given the stack skills already say where each stack keeps its version, what #6
is *for*. Answer, recorded so the entry cannot be mistaken for the knowledge: the stack skills say
*where* the version lives; #6 is `/orc-version` being able to *write* it. `/orc-version` step 2
hands off to `orc-release/scripts/run.py version-set`, which is `versionfiles.py`, so a format
added there is picked up by the command with no other plumbing. Three steps, ordered by the real
releases that will hit them, not by the entry's list of stacks:

1. **The AppStream metainfo — done today, ahead of Orcshot's 0.4.0.** Orcshot's `RELEASING.md`
   step 1 said to add the `<release version="X.Y.Z" date="...">` by hand and recorded that
   0.3.0 was never added; Flathub's linter fails a metainfo whose newest release is not the
   built version. Same shape as `debian/changelog` — prepend, never stack a duplicate on a
   re-run, stamp the date — so `_write_metainfo` mirrors `_write_changelog`: `detect` finds a
   `*.metainfo.xml` / `*.appdata.xml` at the root, `read_version` is the newest `<release>`,
   `write_version` prepends one with `--changelog-body`'s bullets as a `<ul>` (or a bare
   dated `<release/>` without a body), edited as text so the file's own formatting and
   comments survive. `version-set` now passes the body to every format (the field formats
   ignore it). Verified on a copy of Orcshot's real `pyproject.toml` + metainfo: `version-set
   0.4.0` wrote both, `version-verify` agreed, `appstreamcli validate --pedantic` and Flathub's
   own `flatpak-builder-lint appstream` both pass on the result. Nine new tests. Not done:
   Orcshot's `RELEASING.md` step 1 still says "by hand" — it is true until Orcshot's installed
   Orclab carries this, so it changes in an Orcshot session after the next Orclab release.
2. **Two numbers, then `pubspec.yaml` — when Orctool reaches its store slice.** Orctool
   (brainstormed 2026-09-13, Flutter, Android + iOS, no code yet) is the first project on any
   of the seven stacks; its slice 5 is store onboarding, and that is the first moment a build
   number can be checked against a real store. The model change above comes with that handler.
3. **Each other stack's file when a project on it ships**, one at a time; the first-touch
   "suggest a starting version" half rides along with any of them.

Kept out on purpose: Orcshot's GNOME extension `metadata.json` `version-name` (already `0.4.0`
while the app is `0.3.0`) moves on its own cadence by `RELEASING.md`'s own rule, so it is not a
version file for `verify_consistency` — which means the check will one day need "these agree,
that one is independent" as a per-project statement; not built until a second such file exists.

**Update 2026-09-20 — `composer.json` joins the list (v24).** `stack-php` (spec
`docs/superpowers/specs/2026-09-20-orclab-v24-php-design.md`, §3) puts `composer.json` at the
project root as the version file and says, like the seven stack sentences above, that
`/orc-version` does not edit it yet — `KNOWN_FORMATS` is unchanged. One number, not two: no store
build code, so it is the `pyproject.toml` shape, the easy kind. Same rule as the rest: added when
a real PHP project reaches a release.

**Update 2026-09-22 — step 2 names the wrong project; the trigger has moved to orcweather.**
Found while direflail was setting up Apple Developer Program enrollment, in a session about
getting iOS development working at all. Step 2 above says the `pubspec.yaml` handler arrives
"when Orctool reaches its store slice," and names Orctool as "the first project on any of the
seven stacks ... no code yet." Both halves are now stale, checked directly rather than assumed:

- **Orctool has code.** `git log` in `~/projects/orctool` shows shipped slices and two merged
  PRs — a compass off the fused rotation-vector sensor, instruments with Show/Log/More switches,
  per-instrument `.xlsx` export. It is at `version: 1.0.0+1`. The "no code yet" parenthetical
  dates from the 2026-09-13 brainstorm and has simply been overtaken.
- **Orcweather, not Orctool, is going to a store first.** direflail decided on 2026-09-22 that
  orcweather is the first app to reach an iPhone, and began Apple Developer Program enrollment
  (Individual, $99/year) for it that day. Orcweather is Flutter, at `version: 1.0.0+6`, with
  `ios/Runner.xcworkspace` scaffolded and bundle id `com.artificialorctelligence.orcweather`.

**Why this is worth correcting rather than leaving to be noticed:** step 2 is the step that
carries the two-number model change, and the entry currently sends whoever picks it up to a
project that is not the one about to need it. The concrete consequence is orcweather's: App
Store Connect refuses an upload that reuses a build number, so the `+N` in `version: 1.0.0+N`
has to increment on **every** upload — including rejected builds and every TestFlight round —
and `KNOWN_FORMATS` is still `[PYPROJECT, PLUGIN_JSON, MARKETPLACE_JSON, DEBIAN_CHANGELOG]`
(re-read 2026-09-22), so `/orc-version` cannot touch `pubspec.yaml` at all. Until the handler
lands, that number is edited by hand, and the failure mode for getting it wrong is a refused
upload rather than anything local and visible.

**Scope boundary — what this update does not change.** The handler's design is untouched: still
`pubspec.yaml`'s single `version: x.y.z+N` line, still carrying the two-number model change
described above, still one format at a time. Only the triggering project and its timing move.
Orctool's own store slice remains a real future trigger for the same handler; whichever of the
two gets there first proves it, and the second one costs nothing extra. Nothing here touches
step 1 (shipped) or step 3, and the `composer.json` note below step 3 is unaffected.

**Step 2 shipped 2026-09-22 — `pubspec.yaml`, with the two-number model.** `PUBSPEC` joins
`KNOWN_FORMATS`; `read_version` returns only the human half of `version: 1.0.0+6`, so the build
number stays out of cross-file consistency and a Flutter project still compares cleanly against a
`plugin.json` beside it. `write_version` **derives the build number and always increases it** —
`build=` may be passed explicitly and is refused if it does not increase, which is the refusal
`stack-flutter`'s Play and App Store rows promised.

**Why always-increment rather than only-on-change**, since the entry's earlier wording ("refuse a
bump that leaves `+N` unchanged") suggested a check rather than a derivation: setting the same
version twice is not a mistake to refuse, it is the real re-upload-after-rejection case, and it
still needs a number the store has never seen. Deriving it makes the promised property true by
construction instead of by error message. `_roll_back_versions` calls `write_version` with no
`build=`, so an aborted release leaves the build number advanced — deliberate, and the safe
direction: a number that may already have been uploaded is never handed out twice.

Twelve tests in `tests/test_versionfiles.py` (suite 32 → 44, whole scripts suite 130 green;
`hooks/scripts` 189 green). Proven against orcweather's real `pubspec.yaml` on a copy, not a
fixture: `version-set 1.0.1` took `1.0.0+6` to `1.0.1+7`, a second `version-set 1.0.1` took it to
`+8`, `version-verify` agreed, and a `diff` of everything but the version line was empty —
including the nested `version: 2.1.0` under a pinned dependency, which is why the pattern anchors
to column 0. Removing the `+ 1` from the derivation fails four of the twelve, so the tests bite.

**Docs corrected in the same commit**, per `CLAUDE.md`'s rule that a skill misdescribing a shipped
command is fixed before the command is: `stack-flutter` said `/orc-version` "does not edit this
file yet" and that the handler "when written ... must refuse a bump that leaves `+N` unchanged" —
both now describe what ships. Five other stack skills (`stack-godot`, `stack-unity`,
`stack-react-native`, `stack-android-native`, `stack-ios-native`) enumerate the handled formats in
a sentence about their *own* still-unhandled file; the enumeration gained `pubspec.yaml` and the
rest of each sentence stays true. `docs/commands/orc-version.md` gained the format and a paragraph
on the build number in a user's terms.

**What stays open:** step 3 — every other stack's file, one at a time, when a project on it ships
— and the first-touch "suggest a starting version from what's already there" half, still unbuilt.
`verify_consistency` still has nothing to cross-check a build number *against*, because
`pubspec.yaml` is the only format here that carries one; the day a second does (Android's
`versionCode` in `build.gradle.kts`, iOS's `CURRENT_PROJECT_VERSION`) is the day that check earns
its code, and not before.


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

## #32: write documentation for all the commands, in simple language with clear explanations (RESOLVED 2026-09-14)

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

**Resolved for real, not just tracked** (2026-09-14, v20): eleven pages under `docs/commands/`,
one per `skills/orc*/SKILL.md`, each with the same five headings (what it's for, what you type,
what it will ask you, what it changes, what it will never do without asking), each written from
its skill read in full that day and then re-read as someone who has never opened a `SKILL.md`;
each reviewed twice — once by a reader given the page alone, once against the skill for the
"never does" section both ways. `README.md` rewritten as a front page listing and linking every
page, every discipline skill and every stack that exists (checked both ways against `ls
skills/`). `/orc-help <name>` shows a page inside Claude from the same file GitHub renders — one
source, no second copy. `hooks/scripts/tests/test_docs.py` holds the set complete and the shape
fixed; `CLAUDE.md`'s design checklist item 7 carries the rule that a command change touches its
page. Found on the way, by the page reviews: `skills/orc-publish/SKILL.md` and
`skills/orc-release/SKILL.md` had never carried `disable-model-invocation: true` — checked at
their first commits (`0470c26`, `8fe01a6`) — while `CLAUDE.md`'s sub-skill-isolation section said
all three side-effecting commands did; both now carry it (commit `bf9ec0e`), pinned by
`hooks/scripts/tests/test_side_effecting_skills_frontmatter.py`, so the pages' "Claude never runs
this on its own" is true. Spec: `docs/superpowers/specs/2026-09-13-orclab-v20-command-docs-design.md`.

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

**Update 2026-09-20.** v18 §6 parked Docker — *"probably going to remain open. No row, no
facet."* v23 unparked it as an opt-in development environment, not a shipping unit: spec
`2026-09-20-orclab-v23-containers-design.md`, BACKLOG #58. Every stack skill now carries a fifth
facet, `## Containers`; shipping *as* a container stays parked and is #60.

## #34: Mutation-testing orc-todo's suite writes test data into the real BACKLOG.md, VERIFICATION.md and .git/orclab — a cwd→None mutant falls back to the process cwd (RESOLVED 2026-09-13)

Found 2026-09-12 by the first real `/orc-test analyze skills/orc-todo/scripts` (v17, Task 19). Until this is fixed, **running mutation testing on orc-todo's suite overwrites the real repo's BACKLOG.md, VERIFICATION.md and `.git/orclab/` state.** It did: after the run the main checkout's BACKLOG.md was a 33-line test fixture (`## #23: t` / `b`), the worktree's VERIFICATION.md had nine "Scenario 62–70: on the branch" stubs appended, `.git/orclab/lock` held `{not json`, `counters.json` said 23 and `lanes.json` held the test lane "B". All restored the same session (main's BACKLOG.md from its commit, byte-identical; `lock clear`; `lane delete B`); the worktree's VERIFICATION.md was still carrying the stubs when Task 19 finished — `git checkout -- VERIFICATION.md # orclab:discard-entries` removes them.

Why. Every orc-todo test isolates itself by building a throwaway git repo under `tmp_path` and passing it as `cwd`. That isolation holds exactly as long as the code honours the argument. mutmut plants, among its ~930 mutants, some forty that replace a `cwd` argument with `None` or drop it (`read_lanes(None)`, `state.held(..., )`, `_write_lanes(data, )` …), and every `cwd=None` path falls back to the process cwd — which during the run is `skills/orc-todo/scripts/mutants/`, inside the real repo. The test then does exactly what it says: allocates a backlog number into the canonical file, appends a scenario to the invoking root's VERIFICATION.md, writes a corrupt lock to see that it still blocks. On the real files. And the mutant survives, because the tmp repo the assertion looks at is untouched.

`test-discipline` rule 4 (Isolation) already says the filesystem is replaced with a fake; the miss is that the fake was supplied as an argument and nothing pinned the ambient state a dropped argument falls back to. Task 19 widened that rule by a sentence. The fix in orc-todo's tests is one autouse fixture in `skills/orc-todo/scripts/tests/conftest.py` (or the existing empty `conftest.py` at `scripts/`): `monkeypatch.chdir(tmp_path)` into a throwaway `git init`'d dir — then a `cwd → None` mutant lands in the sandbox, where the assertion sees it, and those forty survivors die for free. Not done in Task 19 because the brief says orc-todo's tests are `generate`'s job, in a session of its own; but this one is the precondition for that session, not part of it: run it first, or the `generate` session's own `analyze` calls do the damage again.

Also worth a line in the shipped skill: `/orc-test analyze` runs the project's suite hundreds of times with the code deliberately broken, so a test that reaches anything outside its temp dir will, under some mutant, reach the real thing. `languages/python.md` carries this now; the other seven `languages/*.md` should say it when their first real run lands.

**Resolved for real, not just tracked** (2026-09-13): the one autouse fixture, in
`skills/orc-todo/scripts/conftest.py` — `monkeypatch.chdir` into a fresh `git init`'d temp dir
with a stub BACKLOG.md, before every test. Proven with a negative control rather than assumed:
`cwd = None` planted by hand at the top of `allocate.allocate` and `lanes.read_lanes`, suite run
once with the fixture and once with it removed. With it: 22 tests fail (the mutant dies) and the
real repo is untouched — `git status` clean, counter still 39. Without it: the same 22 fail, and
the real BACKLOG.md gained fourteen fixture entries (#40–#53), VERIFICATION.md two stub scenarios,
and `.git/orclab/counters.json` read 53/63 — this entry's incident, reproduced on demand. All
restored (the discard hook caught the checkout and needed its `# orclab:discard-entries` marker;
the counter was set back to 39/61 by hand, since `.git/orclab/` is untracked). The isolation
warning python.md carries is now in `languages/gdscript.md` too, whose first real run landed
2026-09-12 (#36); the other six still wait for theirs.

## #35: orc-todo's tests run the code but do not pin it: TCE 68.6%, the specific gaps (UPDATED 2026-09-13 — #34 closed, clean before-number is 69.4%; `generate` is the next step) (RESOLVED 2026-09-13)

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

**Update 2026-09-13 — where this stands.** #34 is closed (the fixture is in
`skills/orc-todo/scripts/tests/conftest.py`, where mutmut's copy carries it — its first home,
`scripts/conftest.py`, was never copied and the first analyze after it rewrote the real files one
more time; restored, counter reset to 40/61). The first clean `analyze skills/orc-todo/scripts`
then reported **TCE 69.4%**, tree untouched — that, not 68.6%, is the before-number for the
`generate` pass, since the forty `cwd → None` survivors died for free as predicted. Next step is
`/orc-test generate` against that run's `.orclab/test/analyze.json`, working the gap list above
(lane delete/current, lock exit codes, list with an in-progress lane, whitespace normalisation,
timeout propagation, `required=True`), then `analyze` again for the after-number.

**Resolved for real, not just tracked** (2026-09-13, `/orc-test generate`'s first real use):
**TCE 69.4% → 82.3%** (gate 70), coverage 91.8% → 96.1%, suite 68 → 78 tests, all green. Ten
tests, one per gap above: `lane current`/`lane delete` through the parser with the lane file read
back after each step and `-` clearing; `list` with nothing open; `lock status` on a dead pid with
an hour-old start (exit 0, "NOT running", the age) and on a live one with no start ("unknown
age"); bare `orc-todo`/`lane`/`lock` exiting 2; `remove` pinned byte-for-byte around the seam
with trailing spaces kept; `insert` exact about the seam, the body's own trailing spaces, and the
first of two anchors; `lock_info`'s `started`/`age_seconds`/pid-1 alive; `NotAGitRepo` naming
the directory; `allocate(timeout=0.3)` raising in under 3s while the lock is held. Two proven red
by hand before the run (the `-` clear planted as `item = args.item`; `timeout` dropped from
`held()` — the test waited the full 10s and failed on time), then the mutation run did the rest.

One defect in the cycle itself, found because the second `analyze` returned 69.4% verbatim:
mutmut's cache hashes source functions only, so new tests never invalidate it and `generate`'s
after-number is its before-number on every Python project. `langs/python.py`'s `mutation_cmd`
now drops `mutants/` when any test file is newer than the cached verdicts (the verdict files
cannot go alone — mutmut then reports 0 mutants; that was tried). Unit-tested both ways, and
checked live: a rerun with tests unchanged kept the six `.meta` files and reported 82.3% again.
`languages/python.md` records it. The remaining 17.7% is the string-literal noise the entry
already names — not chased.

## #36: GDScript has no mutation-testing tool, so /orc-test cannot measure TCE for Godot projects (UPDATED 2026-09-12 — a tool exists; re-scoped to adopting it) (RESOLVED 2026-09-12)

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

**Resolved for real, not just tracked** (2026-09-12): wired exactly as the update predicted —
`langs/gdscript.py`'s `mutation_unavailable` returns None when `gdmutant` is on PATH,
`mutation_cmd` builds `gdmutant run <target> --project <root> --exclude 'test/*' --json … --runner
gdunit4|gut [--tests res://test/unit] --godot $GODOT_BIN`, `mutation_parse` goes through the shared
`stryker.py`; `languages/gdscript.md` has the Mutation section. And actually run, not read about:
Godot 4.7.2 headless and gdUnit4 v6.1.3 were fetched into the session scratchpad, gdmutant's own
`corpus/` sample was made a git repo, and `run.py --cwd corpus run` then `analyze` went end to end
through `/orc-test`'s own surface — `turn_order.gd` scored 11 killed / 7 survived = 61.1%, the
README's own figure, with the survivors listed by line and the tracked-tree guard passing. Two
things only the run could find, both now in the language file's Caveats and in `CAVEATS`: a fresh
checkout needs one `$GODOT_BIN --headless --import` or gdUnit4's scripts fail to parse, and the
"mutating N files" line counted `addons/` (233 for a 6-file project) — fixed with a per-language
`SKIP_DIRS` that `cli._source_count` now honours. Suite: 151 passed.

## #37: Correct the snap and flatpak ingredients from Orcshot's first real runs, and write ego and spices from the captured ones (UPDATED 2026-09-13 — spices withdrawn; ego is uploaded and in review; snap's first upload is held)

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

**Update 2026-09-13 — re-checked against Orcshot's own backlog; the trigger is narrower now.**
Read Orcshot `BACKLOG.md` #198 and #205 as they stand today (Orcshot commits `49d5cd8`,
`db75263`, both 2026-09-13):

- **Spices is off the table.** #205 (2026-09-12): the Cinnamon applet was dropped — a real
  Cinnamon panel showed the mandatory About/Remove menu items every applet carries, direflail
  did not want them, and the applet is being replaced by an app-owned `XApp.StatusIcon`
  (Orcshot #208). The Spices leaf, RELEASING.md step and sync script are gone from the branch.
  There will be no PR to `linuxmint/cinnamon-spices-applets`, so there is no captured run to
  write a `spices` ingredient from; item (2) above is `ego` only. If a later project ships a
  Cinnamon applet, `CLAUDE.md`'s "Before the first project builds on a stack or ships to a
  channel Orclab has never met" is what governs, not this entry.
- **EGO has a captured run.** #205 (2026-09-12): `gnome-extensions upload --accept-tos` was run
  for real on the GNOME 50 VM (the command does not exist on the Mint host); "Orcshot (0.4.0)"
  sits in extensions.gnome.org's public review queue, not yet in `extension-query` results —
  the expected pre-approval state. The `ego` ingredient can be drafted from that run once the
  listing exists to confirm against; it is not written yet.
- **Snap's first upload has happened and is held, as the ingredient predicted.** #198
  (2026-09-13): the upload went up as revision 1 and is held on the `dbus` slot — the exact
  hold `skills/orc-package/ingredients/snap/ingredient.md` line 6 and section 5 describe. The
  declaration request on the Snapcraft forum waits on a forum account being approved by a
  moderator. `review-tools` against the CI artifact shows exactly one `human review required`
  line, the slot's. Nothing in the ingredient has been contradicted so far; its "verify at
  first upload" spots past the hold (the grant, the release to a channel, `snap info`
  confirming) are still ahead.
- **Flathub preconditions are done; the submission waits on Orcshot's `v0.4.0` tag.** #198
  (2026-09-13): GitHub 2FA on, `flathub/flathub` forked with the `new-pr` branch. The
  submission PR itself is gated on the tag, which is gated on the Snap grant.

**Trigger, restated:** the Snap declaration is granted and a revision is released to a channel;
the Flathub PR is merged; EGO accepts the extension. Item (1) — correcting `snap` and `flatpak`
— needs the first two; item (2) — writing `ego` — needs the third; item (3) — dropping the
"no release has gone through this" markers — follows each. Still nothing Orclab-side can move
today.

## #38: app-store ingredient still says GitHub macOS minutes are billed at 10× — wording GitHub retired; two stack skills now say otherwise (RESOLVED 2026-09-12)

`skills/orc-package/ingredients/app-store/ingredient.md`, section 1 (line 33), lists the cloud-Mac options for a Linux developer and describes GitHub Actions macOS runners as "minutes are billed at 10×". That sentence reads as a fact about GitHub's current billing, and it is not one any more: the v18 stack skills, checking GitHub's pages live on 2026-09-12, found that `https://docs.github.com/en/billing/managing-billing-for-your-products/about-billing-for-github-actions` and `https://docs.github.com/en/billing/reference/actions-runner-pricing` now give only a per-minute rate table — macOS **$0.062/minute** against Linux **$0.006/minute**, a ratio of about 10.3× — and no longer document a multiplier applied to a plan's included minutes at all. Both `skills/stack-flutter/SKILL.md` (`### Building without a Mac`) and `skills/stack-ios-native/SKILL.md` (the same section) now record exactly that: "GitHub's pages once documented a 10x multiplier on included minutes for macOS; the current pages give only the rate table, so whether the 2,000 free minutes deplete at the macOS rate is not stated." So the ingredient and the two skills that point at it disagree about what GitHub says, and a reader who compares them cannot tell which is current.

It was not fixed on the v18 branch because the spec (`docs/superpowers/specs/2026-09-12-orclab-v18-project-type-defaults-design.md`, §7) leaves every `orc-package` ingredient unchanged; that branch only writes stack skills and the `/orc-code` Defaults Table. The fix is one line in the ingredient's section 1 — replace "minutes are billed at 10×" with the rate-table wording the two skills use ($0.062/min macOS vs $0.006/min Linux, ≈10.3×; the included-minutes multiplier is no longer on GitHub's pages) — plus the ingredient's "checked against live sources" stamp, since that line is the only thing in it that the stack skills' 2026-09-12 fetch contradicts.

**Resolved for real, not just tracked** (2026-09-12): section 1 of the ingredient now carries the rate-table wording — $0.062/minute macOS against $0.006 Linux, about 10.3×, with the retired included-minutes multiplier named as retired — and the opening stamp records the 2026-09-12 GitHub check beside the 2026-09-11 Apple one. `grep -n "10×" skills/orc-package/ingredients/app-store/ingredient.md` now matches only the corrected line, so the ingredient and the two stack skills agree. Re-checked directly the same day, not taken from the skills: both GitHub pages named above carry the $0.062 / $0.006 table, contain the word "multiplier" zero times, and say only that usage is *"consumed from your account or organization's existing plan entitlement"* — nothing about macOS drawing it down faster.

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

## #40: Evaluate a found list of seven code-shape rules (linear control flow, loop ceilings, two assertions per function …) and decide whether Orclab's discipline skills should carry them (UPDATED 2026-09-13 — evaluated and adopted; `code-discipline` shipped; re-scoped to the lint configs and the hook) (RESOLVED 2026-09-13)

direflail brought this on 2026-09-13, as a screenshot of a bulleted list found elsewhere, with the
question "see if orclab can use it" — might help AI development. The list, transcribed verbatim:

- Keep control flow linear, no more than two levels of nesting
- Every loop gets an explicit ceiling, not "it'll never exceed N"
- Close everything you open, on the error path too
- One function does one job and fits on a page, about 60 lines
- At least two assertions in every function, so it fails loudly
- Never swallow an error, a bare `except: pass` is not handling
- Zero compiler warnings from day one, not zero errors

The source is not known; the shape closely resembles the NASA/JPL "Power of Ten" rules for
safety-critical C (Holzmann, 2006), which have the same items — bounded loops, no recursion,
function length, assertion density, zero warnings — restated in plain language. Whoever picks this
up should find the real origin first (`currency-discipline`), because the answer to "should Orclab
adopt it" differs between "a well-known rule set for flight software" and "someone's blog post".

What this is asking for, in Orclab's terms: a rule that Claude follows while writing code in any
consuming project. Orclab has one place today where such rules live — `test-discipline` (rules for
tests, background skill) — and no equivalent for production code; the shipped `ponytail` plugin
carries a different, partly opposing philosophy (shortest diff, "trivial one-liners need no test")
and is not Orclab's. So the evaluation is: (1) which of the seven already fall out of existing
skills or the model's defaults and need no rule; (2) which are genuinely worth adding, and where —
a new `code-discipline` background skill in `test-discipline`'s shape is the obvious home, and
`CLAUDE.md`'s "Before building anything, name what should already have covered it" applies
before it is created; (3) which conflict with what Orclab already ships (the two-assertions rule
against Python idiom, the 60-line rule against `ponytail`'s "fewest files"), and how that gets
decided rather than left as two rules that disagree.

Not this: rewriting any existing code to these rules, or adopting them into Orclab's own bundled
scripts before the decision is made. This is an evaluation and a decision, and its output is
either a skill or a line here saying why not.

**Update 2026-09-13 — evaluated against primary sources; the decision is "adopt all seven, one
restated", and the first layer is shipped.** The list's own wording is not findable (two searches
on its most distinctive phrases return nothing) — a paraphrase, not a published list. Five rules
are Holzmann's "Power of Ten" (JPL, 2006; `spinroot.com/gerard/pdf/P10.pdf`), the nesting limit
is Martin's *Clean Code* ("one or two"; Linux says three), and "close what you open" / "never
swallow" are the resource and exception idioms Holzmann's C had no need of. The one that does not
transfer literally is the assertion density: in his C an assertion is a shipped check with "an
explicit recovery action"; in every one of Orclab's seven stack languages the `assert` keyword is
debug-only (each verified against its own docs — Python `-O`, Kotlin `-ea`, Swift `-O`, Dart
production, C# `[Conditional("DEBUG")]`, GDScript release), so a literal reading produces checks
that vanish from the shipped app. Restated as "validate inputs from outside the function with a
check that survives release; the count is not kept — TCE measures interception directly."

The search this entry asked for: `skills/*/SKILL.md`, `CLAUDE.md`, `hooks/scripts/`, this file —
nothing covered any of the seven; `orc-test`'s lint covers tests only. So a new background skill,
`skills/code-discipline/SKILL.md`, in `test-discipline`'s shape (`user-invocable: false`, sits in
every session), with each rule's source quoted so the next reader can judge it. `test-discipline`
and `plugin.json` point at it. direflail's question that shaped it — "is all code written through
/orc-code?" — no: a bug fix in chat, a subagent's task and `/orc-test generate` all write code
without it, which is why the rules are a background skill and not a section of `/orc-code`.

**What this entry now tracks — the two layers a prose rule cannot supply** (`CLAUDE.md`: a rule in
a skill body fires only if read; Holzmann's rule 10 wants the checker run daily):

1. **Lint configuration in what `/orc-code` scaffolds**, one stack at a time: nesting depth,
   function length, empty catch, and warnings-as-errors, each in that stack's native tool — ruff
   + pyright, ESLint (`max-depth`, `max-lines-per-function`, `no-empty`), detekt, SwiftLint,
   Dart analyzer, the C# analyzers, gdlint + `project.godot` warning severities. Each `stack-*`
   skill's toolchain section says where the switch lands; the "confirmed live" stamp per
   `currency-discipline`. The first project on a stack is the moment, per `CLAUDE.md`'s "before
   the first project builds on a stack".
2. **A `PostToolUse` hook on `Edit`/`Write`** in `hooks/hooks.json`, in `model_floor.py`'s shape,
   that runs the project's configured linter on the file just written and reports findings —
   mechanical, every write, subagents included. Only worth building once (1) gives it something
   to run; a hook with no config behind it is `/orc-test`'s "lint: not run" in a new place.

**Resolved for real, not just tracked** (2026-09-13, all three layers shipped the same day):

1. `skills/code-discipline/SKILL.md` — the rules, sourced (above).
2. A `## Lint — where code-discipline lands` section in all nine `stack-*` skills, each rule name,
   default and switch confirmed against the tool's own sources that day (listed in each skill's
   Sources): ruff `PLR1702`/`PLR0915`/`E722`/`S110` + pyright strict; oxlint — the Vite template's
   actual linter, checked in `create-vite/template-react-ts` — and ESLint for Expo; detekt's four
   rules + Kotlin `allWarningsAsErrors`; SwiftLint `nesting` (default already 2) and
   `function_body_length`, a custom rule for empty `catch` because SwiftLint has none, and
   `SWIFT_TREAT_WARNINGS_AS_ERRORS` from Apple's `Swift.xcspec`; Dart `empty_catches` + analyzer
   severities, with the honest gap that the free linter has no nesting or length rule;
   SonarAnalyzer.CSharp `S134`/`S138`/`S108`/`S2486` with the two thresholds in `SonarLint.xml`
   (the analyzer's `ParameterLoader.cs` reads them there — `.editorconfig` cannot set them);
   gdlint, whose `max-nested-blocks` and `max-statements` are commented out in its own config,
   plus `project.godot`'s 49 per-warning severities.
3. `hooks/scripts/lint_on_write.py`, `PostToolUse` on `Edit|Write|MultiEdit`: runs the project's
   configured linter on the file just written — only when the tool is on PATH *and* its config
   file sits between the file and the git root, so it never brings an opinion the project has
   not adopted — and reports findings on stderr with exit 2, the documented way a PostToolUse
   hook reaches Claude. Eight tests with a fake linter on PATH; then real: ruff 0.16.7 with the
   Python skill's `pyproject.toml` verbatim on a file nesting five deep with a bare
   `except: pass` — the hook reported `too-many-nested-blocks (5 > 2)`, `bare-except` and
   `try-except-pass`, exit 2. A clean file costs 40 ms; a file with no config, 20 ms. C# is left
   to the build (no per-file analyzer finishes in seconds), and Orclab's own scripts have no
   `[tool.ruff]` yet, so the hook is silent on them until they adopt it — a real remaining gap:
   Orclab does not yet dogfood its own code-discipline config.

**Gap closed the same day.** The Python skill's `[tool.ruff]` block, verbatim, at Orclab's root
`pyproject.toml`: 190 findings on first run — 44 from code-discipline's four rules (41 nesting
sites in 31 functions, one 50+-statement `main`, one `try-except-pass`), 146 from ruff's own
defaults, which since 0.16 are five whole categories rather than `E4/E7/E9/F` (a fact the stack
skill now states). All 190 to zero across five commits: safe autofixes, then by hand — explicit
`check=False` at every `subprocess.run`, the hooks' fail-open `except Exception`s marked with
the rule's own `noqa` and reason (rule 6's named, commented suppression), 31 functions flattened
with guard clauses and extracted helpers (`_analyze_one`, `_gate`/`_run_leaf`, `_wait_or_raise`,
`_roll_back_versions`, orc-publish's `main` split four ways). 611 tests green throughout; the
"8 failed" that appeared between runs was the scratch venv holding ruff sitting first on PATH,
so orc-test's subprocess `python3` had no pytest — my shell, not the code. `lint_on_write` now
fires on every Python file Orclab itself writes.

## #41: /orc-code refactor has two flavours — a code-quality pass and a language/version migration — and today delivers neither: the wrapped plugin is not installed, the wrapper hands over with no stack and no exit gate (RESOLVED 2026-09-13)

direflail asked on 2026-09-13 whether Orclab has a skill that refactors a codebase, in two
flavours: (A) make the code better in place, and (B) move it to a different version of its
language or a different language, factoring in the stack and proving everything still works.

What exists, checked against the files rather than remembered: `/orc-code`'s description claims
"refactor/migrate existing code", and its Refactor Flow "wraps the `code-modernization` plugin's
own real workflow rather than reimplementing it" — Anthropic's plugin, whose own description is
flavour B almost verbatim ("cross-stack rewrites, greenfield reimagining, and same-stack version
uplifts"), with a preflight / assess / map / extract-rules / brief / (reimagine | transform |
uplift) / harden / status pipeline. Two gaps found the same day:

- The plugin is present in the `claude-plugins-official` marketplace clone on this machine but
  **not installed** (`~/.claude/plugins/installed_plugins.json` does not list it), so
  `/orc-code refactor` here lands on its own "not installed" branch. The wrapper has never been
  exercised for real; CLAUDE.md's "check it's actually available, tell the user plainly if not"
  guard exists, but nothing past it has been confirmed live.
- The wrapper hands over completely. It does not tell the plugin which stack Orclab would choose
  for the target, and nothing gates the result. "Factor in the stack" and "make sure everything
  still works" — direflail's two conditions — are exactly what is missing; the plugin's `harden`
  step is generic.

Flavour A has no command at all. The pieces exist — `code-discipline` (the rules),
`lint_on_write` (enforces them on each new write), `/orc-test analyze` + `generate` (the tests) —
and 2026-09-13's dogfood was flavour A done by hand on Orclab's own scripts: the stack skill's
lint config in, 190 findings to zero, 31 functions flattened, 611 tests green throughout, with one
lesson worth carrying — the linter's *unsafe* autofixes applied wholesale made the code worse and
broke eight tests; the rule findings are fixed by hand, per function, with the suite as the check.

The decision (direflail, same day): one spec for `/orc-code refactor` with both modes. A is the
quality pass — ensure the stack's lint config, baseline with the linter and `analyze`, fix
autofixes → rule findings by hand → `generate`, suite green after every file, before → after for
every number. B keeps wrapping `code-modernization` and adds Orclab's two contributions: the
target stack comes from `/orc-code`'s own Defaults Table and its stack skill is the brief's
constraint (the migrated project looks like one `/orc-code` would have scaffolded); and the exit
gate is the *old* suite green on the new code, with `analyze` reporting coverage and TCE no lower
than the baseline — which means a source project with no real suite gets `analyze` + `generate`
on the old code *before* a line is migrated, because a port cannot be verified against tests that
do not exist. Spec: `docs/superpowers/specs/2026-09-13-orclab-v19-orc-code-refactor-design.md`.

Related: #5 (`/orc-data`, legacy-system facts during refactor work) belongs to B's map /
extract-rules phase and may be partly covered by the plugin; check before building #5.

Scope boundary: this does not build a migration engine — that is the plugin's — and does not
touch `/orc-code`'s new-project or add-feature flows.

**Quality mode, first real run (2026-09-13):** on a scratch clone of Orcshot (`git clone
~/projects/orcshot` into the scratchpad; never pushed, deleted at the end), through
`skills/orc-code/SKILL.md`'s `### Quality mode` as written, by a subagent (Task 6 of the v19
plan). Before → after: ruff findings 376 → 0 (code-discipline's four rules 58 → 0 — PLR1702 41,
PLR0915 17, E722 0, S110 0; the other 318 were ruff 0.16's defaults — the baseline marked 186 of
them safe-fixable, and `ruff check --fix` fixed 222, because a fix exposes further fixable
findings and ruff iterates until none remain; the last 96 by hand); coverage 77.9% → 78.3% (4308/5531 → 4349/5553 lines, gate 80 still failing);
TCE 75.6% → 76.3% (8347/11035 → 8509/11151, gate 70 passing); test-lint 7 → 1; tests
1260 → 1277; suite green after every file. For the four rules, 38 functions reshaped by hand
across 18 modules (21 of the 58 findings in the 6200-line `editor_window.py`); the 96 remaining
default findings were one-line fixes at their sites; 12 commits in the clone. Four
things the skill text had wrong, corrected the same day in `SKILL.md`: (1) a fresh clone is not
the developer's checkout — the suite reported 10 collection errors because `import orcshot`
resolved to the machine's installed `.deb` copy, not `src/`; the project's own documented install
comes before the gate, now step 0; (2) step 1 wrote the lint config but not the mutation config,
so `analyze` said "TCE not measurable" — `[tool.mutmut]` is written and committed the same way;
(3) "suite green after every file" proves nothing for the 17 of 85 source files the suite never
imports (GTK windows, 31 of the 58 findings) — the fix there is limited to a mechanical move
checked by ruff's undefined-name rules and an import, and the commit says so; (4) the coverage
gate's remaining gap is entirely in those files, which another round of `generate` cannot close.
Three `orc-test` findings from the same run, tracked as #42, not fixed
here: in Orcshot's src-layout, orc-test's `--cov=.` did not walk into the never-imported files
— coverage.py only lists unexecuted files in directories that have an `__init__.py`, and `src/`
has none, so the lcov held the 68 files something imported and Orclab's coverage denominator
(5531 lines) silently excluded the other 17; `analyze`'s survivor line numbers are relative to
the function, not the file (it reads `mutmut show`'s per-function diff), so `generate` cannot
navigate by them; and ~75% of a whole-project `analyze`'s wall clock (35 of 45 minutes) is one
`mutmut show` subprocess per survivor. Full report:
`.superpowers/sdd/2026-09-13-orclab-v19-orc-code-refactor/task-6-report.md`.

**Migration mode, first real run (2026-09-13):** subject `pallets/itsdangerous` at tag 1.1.0
(2018; pure Python, 1,075 source lines, 417 pytest tests, declares Python 2.7/3.4+), cloned into
the scratchpad, uplifted to **Python 3.12** — not the plan's 3.13, because `/usr/bin/python3.12`
is the only interpreter on the machine and the exit gate has to run on a real runtime; the
target-stack line handed to the plugin said so. Plugin: `code-modernization@claude-plugins-official`,
installed by Task 7's Step 1; its manifest has no `version` and `installed_plugins.json` records
`"unknown"` — the cache directory is `f0dce59fec06`. Contrary to CLAUDE.md's marketplace gotcha
4, the Desktop session that installed it saw its agents and skills without a restart. Baseline
on 3.12 before any change: 417 green (with 107 `datetime.utcfromtimestamp` DeprecationWarnings;
97 tests red under `-W error`), coverage 97.4%, TCE 74.8% (602/805) once `[tool.mutmut]` was
written, as quality mode's step 0 says. Every command file read in full from the installed copy
and followed: `status` (nothing yet); `preflight` (asked its five Check 0 questions of the human
— answered from the run's context; found no source runtime, no `pyupgrade`, standalone repo:
Ready-with-gaps); `assess` (no `scc`/`cloc`, `find`+`wc` fallback; two `legacy-analyst` and one
`security-auditor` agents in parallel → `ASSESSMENT.md`, `ARCHITECTURE.mmd`; the auditor
reproduced a High, CWE-502 in `loads_unsafe`, that no uplift touches); `map` (a 90-line
`extract_topology.py` over the package's imports and MRO → `topology.json`, `TOPOLOGY.html` from
the plugin's template, three `.mmd`); `extract-rules` (no Workflow tool in this client, so Method
B: three `business-rules-extractor` agents → 26 rule cards in `BUSINESS_RULES.md`, 8 needing SME
answers, `DATA_OBJECTS.md`); `uplift` Step 3 first, because `brief` refuses without it
(`version-delta-analyst` → `DELTA_CATALOG.md`: nine deltas, one Judgment call on the path —
naive vs aware datetimes — verdict "minimal-diff uplift"); `brief` (`MODERNIZATION_BRIEF.md`,
three S-sized phases, approval block signed by this task's standing instruction, not a person);
`uplift` (`BASELINE.md` as the target-only oracle; `test-engineer` added six characterization
tests at the delta sites, the two for DELTA-001 deliberately without freezegun under
`TZ=America/New_York` because freezegun hides the wrong fix; pilot = the whole package: two
lines changed in `timed.py`/`jws.py`, then metadata and tox/Travis; `PLAYBOOK.md`,
`UPLIFT_NOTES.md`). Uplift diff: 8 files, +118/−66, six lines in `src/`. **Exit gate passed:**
423 green (417 old + 6 new; 0 warnings under `-W error`), coverage 97.4% → 97.6%, TCE 74.8% →
75.1% (609/811). Not run: `harden` (assess's security section stands in). Not done: DELTA-005
(pre-commit pins, unverifiable offline), DELTA-002 (Sphinx pins, docs out of scope), DELTA-006
(deleting the Py2 shims — behaviour-identical, smaller diff wins), and the stack skill's
`[project]`/ruff layout, which `uplift`'s own minimal-diff rule defers to the quality pass. What
the skill was corrected to say (`skills/orc-code/SKILL.md` `### Migration mode`, spec §3 (a),
(c), (d)): the discovery step's fresh-session claim is now "check first, fresh session as
fallback"; step 3 also runs the suite with deprecation warnings as errors (a green suite hid
every runtime delta) and copies `analyze.json` aside; step 4's symlink layout held but any walk
following symlinks loops, and `uplift`'s literal `cp -r legacy/<name> …` copies the symlink —
seed with `rsync` from `readlink -f`, and the working copy needs its own venv; step 5 names the
real sequence (`brief` needs `map`, `extract-rules` and the delta catalog first), preflight's
five human questions, the absent Workflow tool, the plugin's own human gates, and that `status`
flags the brief stale after every pilot; step 6 copies `modernized/<name>-uplifted/` (not
`modernized/<name>/`) back; for an uplift only the toolchain version is the target, not the
stack skill's layout. Full report:
`.superpowers/sdd/2026-09-13-orclab-v19-orc-code-refactor/task-7-report.md`.

**Resolved for real, not just tracked:** spec
`docs/superpowers/specs/2026-09-13-orclab-v19-orc-code-refactor-design.md`, plan
`docs/superpowers/plans/2026-09-13-orclab-v19-orc-code-refactor.md`. Both modes were run once for
real, not just written to. **Quality mode** — this entry's "Quality mode, first real run"
paragraph above — took Orcshot's ruff findings 376 → 0, coverage 77.9% → 78.3% (the remaining gap
entirely in the 17 GTK files the suite never imports), TCE 75.6% → 76.3%, and forced 4 corrections
to the skill's prose. **Migration mode** — this entry's "Migration mode, first real run" paragraph
above — uplifted `itsdangerous` 1.1.0 to Python 3.12 through `code-modernization`: exit gate
passed, 97 tests red under `-W error` on the 3.12 baseline → 423 green with 0 warnings under
`-W error`, coverage 97.4% → 97.6%, TCE 74.8% → 75.1%, and forced 9 corrections. Execution found
two defects in the plan itself, not just in the skill's prose it was writing: Task 4 wrote
`hooks/scripts/tests/test_orc_code_skill.py` pinning the unbuilt-marker placeholder text that
Task 7 then had to remove and replace once the run was real; and the Plugin-Discovery Procedure's
"a fresh session is needed" claim was itself wrong — the Desktop session that installed the
plugin picked it up with no restart, corrected to "check first, fresh session as the fallback."
Three defects in `orc-test` itself, found during the quality-mode run, are recorded on this entry
and tracked as #42: in a `src/`-layout project with no `__init__.py`,
coverage's denominator silently drops the files nothing imports; `analyze`'s survivor line numbers
are relative to the function rather than the file, so `generate` cannot navigate by them; and a
whole-project `analyze`'s wall clock is dominated by one `mutmut show` subprocess per survivor.
The one open thread is #5's note (added the same day, above): the plugin's `map`/`extract-rules`
cover the structure-and-rules half of `/orc-data`'s ask but not environment facts, ownership, or
the SME answers the plugin scatters across its own files with no single place to add one; #5
stays open.

## #42: orc-test: coverage denominator omits never-imported files in a src/ layout without __init__.py; survivor line numbers are function-relative; per-survivor `mutmut show` dominates analyze (RESOLVED 2026-09-13)

Three defects in `orc-test` itself, found on 2026-09-13 during `/orc-code refactor`'s first real
quality-mode run on a scratch clone of Orcshot (BACKLOG #41, "Quality mode, first real run";
full report `.superpowers/sdd/2026-09-13-orclab-v19-orc-code-refactor/task-6-report.md`). Left
for this entry there; none is fixed yet. All three live in
`skills/orc-test/scripts/orc_test/langs/python.py`.

**The coverage denominator silently omits the files nothing imports, in a `src/` layout with no
`__init__.py`.** Observed: Orcshot has 85 source files; 17 of them (GTK windows, no headless
test) are imported by nothing in the suite, and `coverage.py` only lists an *unexecuted* file
when its directory has an `__init__.py` — Orcshot's `src/` has none — so the lcov held the 68
files something imported and Orclab's denominator (5531 lines) excluded the other 17.
Consequence: the 80% coverage gate read a number that flattered the suite (77.9% → 78.3% on a
denominator that was missing the least-tested fifth of the tree), and step 2's "which files the
suite never imports" list had to be built by diffing the coverage report's file list against
the tree by hand. Where: `coverage_parse` builds `Coverage` from the lcov alone; `coverage_cmd`
passes `--cov=<target>` with no `source`/`--cov-config` that would make coverage.py walk
unexecuted directories.

**Survivor line numbers are function-relative, not file-relative.** Observed: `analyze`'s
survivor list gave lines that did not point at the mutated statements; `mutmut show <key>` prints
a diff of the *function's own source*, so the hunk header's start line is line 1 of the function,
and `_survivor`'s "hunk start plus context lines before the first `-`" is correct within that
diff but wrong for the file for every function not at line 1. Consequence: `generate` cannot
navigate to a survivor by the line it is given; the file and the replacement text are right, the
line is not. Where: `_survivor` (called per survivor from `mutation_parse`), which parses
`mutmut show`'s output — the function's start line in the file has to come from somewhere else
(mutmut's own metadata, or an `ast` lookup of the function name the key carries).

**One `mutmut show` subprocess per survivor dominates `analyze`'s wall clock.** Observed: the
whole-project `analyze` on Orcshot (26k mutants) took ~45 minutes, ~10 of them mutmut's own run
and ~35 in the per-survivor `mutmut show` loop `_survivor` runs — ~75% of the total, for
information (file, line, replacement) that mutmut has already computed once. Consequence: a
first `analyze` on a real project is long enough that the skill now tells the user to start it
and read the baseline findings while it waits. Where: `mutation_parse` → `_survivor` → `_show`,
one subprocess per surviving mutant; a fix for the line-number defect above that reads mutmut's
metadata instead of `show`'s diff would remove the loop at the same time.

Scope: Python only — the other languages' `langs/*.py` read their tools' own reports and are not
known to share any of the three. Not touched by #41's resolution, which corrected `/orc-code
refactor`'s prose and left orc-test's code alone.

**Resolved for real, not just tracked** (2026-09-13, all three in `langs/python.py`, the first
also read from the outside in `languages/python.md`'s Coverage section):

*Denominator.* The mechanism was narrower than the entry says: coverage.py 7's own
`find_python_files` walks down from each `--cov` dir and prunes any *sub*directory without an
`__init__.py` — the dir named by `--cov` is itself exempt. With no target `run.py` passes
`--cov=.`, so Orcshot's init-less `src/` was pruned whole; `--cov=src` would have found the
windows. Reproduced on a two-file scratch project (`--cov=.` lists `src/used.py` only; the
never-imported `src/unused.py` appears the moment `src` is a root). Fix: `_cov_roots` adds one
`--cov=<dir>` for every init-less directory on the way to a `.py` file, so each is a root of its
own; overlapping roots produce no duplicate lcov records (checked). coverage.py's
`include_namespace_packages` does the same but is config-file-only, and `--cov-config` would
replace the project's own config. Verified by `test_coverage_denominator_includes_a_file_nothing_
imports_under_an_init_less_src` (real pytest-cov: 4/8 lines where it read 4/6) and by the real
`analyze skills/orc-todo/scripts`, whose report now lists the never-imported `run.py` and
`conftest.py` it used to omit — which surfaced that an empty file read as "0.0%" in the
under-threshold list; `Coverage.under` now skips a file with no lines.

*Line numbers and the `show` loop, one fix.* `mutation_parse` no longer runs `mutmut results`
or `mutmut show`: it reads `mutants/<file>.meta`, the JSON mutmut itself writes with every
mutant's exit code (1/3 killed, 36/24/-24/152/255 timeout, 0 survived), which is all `results`
prints and what `show` walks to find a key's file. Survivors' diffs come from one subprocess,
`orc_test/mutmut_diffs.py`, calling the function `show` calls (`get_diff_for_mutant`) with the
file already known — ~1 ms each in-process against ~370 ms per `show` process. The diff is still
of the function alone, so the line is now found by looking the removed line's text up inside the
function's real span (`ast`), the function named by the key. Verified on orc-todo's real cache:
764 killed / 164 survived / 1 suspicious, identical to `mutmut results --all true`; every
spot-checked survivor line (`allocate.py` 54, 55, 56, 61, 67; `state.py` 75, 172–174, 216)
holds the statement shown; 164 diffs in 1.1 s where the loop took ~60 s. The whole
`analyze skills/orc-todo/scripts` ran in 1m21s, mutmut's own run being nearly all of it.

Left as it was: a mutant that only *deletes* (an argument dropped, no `+` line) still reports an
empty replacement, as before; and a statement repeated verbatim inside one function resolves to
its first occurrence (the diff's context lines would tell them apart — `ponytail:` comment on
`_line_of`).

## #43: orc-publish's skill says a misconfigured leaf is "refused the same way" and its siblings run; the code stops the whole run before anything publishes

Found 2026-09-14 by v20's final whole-branch review, checking `docs/commands/orc-publish.md`
against the code rather than the skill. `skills/orc-publish/SKILL.md`'s Notes (around lines
157-162) say a leaf with an unusable configuration — a non-string `action:`/`metrics:`/
`prepare:`, a bad `timeout:`, a bad `confirm:` — is "refused the same way … never a run in which
the healthy siblings published while this one crashed". What `orc_publish/cli.py` does:
`_load_leaves` (around 612-621) validates every leaf before the plan is printed, and any
problem returns a whole-run `error:` from `main()` (635-637) — nothing publishes, no leaf is
labelled `refused` (that word is only the preflight-inspection outcome, ~432), and the healthy
siblings do not run either. The behaviour is the safer one and is not the defect; the skill's
sentence is. The page written in v20 was first drafted from the skill's wording and promised
users a per-leaf `refused` and siblings-keep-running; it now says what the code does.

Consequence: anyone writing about or extending this from the skill alone — the next page, a
release note, a `channels.yaml` author expecting one bad leaf to be skipped — inherits the false
claim. `CLAUDE.md`'s "a claim about a component is a claim about code" is exactly the rule; the
skill's own Notes are where it was missed.

Fix: reword the skill's Notes to what `_load_leaves` does (one unusable leaf stops the run
before anything is sent, naming the leaf and the value; a leaf whose *action* fails at run time
does not stop its siblings — `execute_plan`, ~390), or change the code to the per-leaf refusal
the skill describes and update the page. Either is small; the first matches what has been
shipped and dogfooded. Out of v20's scope by its spec §5 (skill bodies unchanged), which is why
this is an entry and not a commit.

## #44: orc-reload's skill says "a reinstall never takes effect in the conversation that ran it — and no command can"; CLAUDE.md's 2026-09-13 Desktop refinement says the installing session was handed the new plugin

Found 2026-09-14 by v20's final whole-branch review. `skills/orc-reload/SKILL.md` line 13
states, as the one thing the command cannot do: a reinstall never takes effect in the
conversation that ran it, "and no command can" — and `docs/commands/orc-reload.md`, written
from the skill in v20, says the same, correctly to its source. `CLAUDE.md`'s marketplace
gotcha #4 carries a refinement confirmed live on 2026-09-13 in the Desktop client: the
`code-modernization` plugin was installed with `claude plugin install` and the *same session*
was immediately handed its agents and skills, no restart needed; `/orc-code`'s Plugin-Discovery
step 5 was corrected that day to "picked up by the installing session; a fresh session is the
fallback, not the rule". The CLI case has not been re-checked since 2026-09-06.

So the skill's absolute is stale for at least one client, and the page repeats it. The user-
visible cost is small — being told to open a new session when the current one would have
worked — but the sentence is stated as a law, and `CLAUDE.md`'s own rule is that a skill's claim
about behaviour is verified, not remembered.

Fix, when someone is in a session that can test it: run `/orc-reload` on Orclab itself in
Desktop and in the CLI, note in each whether the reinstalled version is reachable in the same
session (the `Skill` tool naming an `orclab:` skill, or `/orc-help` reporting the new version),
then rewrite the skill's Step 5 and line 13 to what was observed per client, with the
"confirmed live" date, and update the page's sentence to match. v20 left the page true to the
skill on purpose (spec §5: skill bodies unchanged); the fix is one skill edit and one page edit
in the same commit, per `CLAUDE.md`'s checklist item 7.

## #45: Tomorrow (2026-09-16): execute the v21 push-gate plan, then spec the three /orc-test config gaps found getting Orclab to 80/70

Set by direflail 2026-09-15 at the end of the session that wrote the v21 spec and plan: "push
and then put writing the plan in an /orc-todo task for tomorrow." The plan is written and
pushed — `docs/superpowers/plans/2026-09-15-orclab-v21-push-gate.md`, commit `2a93d52` — so
what is left for tomorrow is running it, and the item behind it.

**1. Execute the v21 plan.** Five tasks: the pinning test written red, `skills/orc-git/SKILL.md`
(`push`/`cp` run `/orc-test coverage`, `release` runs `/orc-test analyze`, a red gate stops with
the report and nothing is pushed, no skip flag), `docs/commands/orc-git.md`, a live check on
Orclab itself, and the BACKLOG record. Subagent-driven in a worktree, per direflail's standing
preference; `main` is pushed, so the worktree will branch from current `origin/main`. The spec
is `docs/superpowers/specs/2026-09-15-orclab-v21-push-gate-design.md`, approved as is.

**2. Then, direflail's item 2 — "fix what's wrong with our mutmut config", which they settled as
"a and b are both needed"**, plus a third found on the way. All three are `/orc-test` changes
and get a brainstorm → spec → plan of their own; the v21 spec's §6 names them as out of scope:

- (a) `/orc-test analyze` on a project with several `scripts/` dirs measured one suite of six
  and said only "TCE not measurable — check its configuration" for the root. It should find
  each Python suite (a `tests/` dir with a package or scripts beside it) and say, per suite,
  which has no `[tool.mutmut]` — or write it.
- (b) The two traps orc-publish hit, now fixed for Orclab and recorded in
  `skills/orc-test/languages/python.md`'s Caveats: a `conftest.py` beside the package is not
  loaded under mutation (it has to be `tests/conftest.py`), and a test that kills a process
  group can kill the harness when a mutant drops `start_new_session`. `/orc-test` should
  detect the first (a package-level conftest and no `tests/conftest.py`) and say so.
- (c) `launchpad_ppa.py`'s 195 mutants all scored "no tests" for days because its test loaded
  the module under a name mutmut did not derive — and the file silently dropped out of
  orc-publish's 78.9%. `run.py` counts "the rest" as not counted; it should report how many
  mutants no test reached, per file, the way coverage reports an uncovered file.

**Ground, so tomorrow's session does not redo today's search:** whole-project coverage is 92.9%
and every suite is over 70% TCE (commits `28f9ae4`, `3383b5d`, `dddf3d3`, `788aa67`);
`hooks/scripts/pyproject.toml` and `skills/{orc-package,orc-publish,orc-release,orc-test}/…/pyproject.toml`
carry the mutmut configs written today; `python.md`'s "Last real run" line has the per-suite
numbers.

**Item 1 done 2026-09-16** — merge `033e47c`, record in #46, one spec gap it surfaced in #47.
Item 2 (the three `/orc-test` config gaps, brainstorm → spec → plan) is what remains open here.

## #46: /orc-git runs /orc-test before push, cp and release — the v21 gate (RESOLVED 2026-09-16)

Requested by direflail 2026-09-15: "any time the user is going to push to github, /orc-test
runs and makes sure the tests are 80% covered and that the test quality is high." Design in
`docs/superpowers/specs/2026-09-15-orclab-v21-push-gate-design.md`, plan in
`docs/superpowers/plans/2026-09-15-orclab-v21-push-gate.md`; executed 2026-09-16 (#45 item 1).

**The prerequisite came first.** direflail: "we need to get orclab up to 80/70 first." Before
this entry, `/orc-test analyze` could measure one of Orclab's six suites; commits `28f9ae4`,
`3383b5d`, `dddf3d3`, `788aa67` gave every suite its mutmut config, moved orc-package's and
the hooks' tests in-process, and tested `launchpad_ppa.py`. Result: whole-project coverage
84.8% → 92.9%, every suite over 70% TCE. Three `/orc-test` defects found on the way are #45's
item 2.

**What shipped** (merge `033e47c`): `push`/`cp` run `/orc-test coverage` after the "anything to
push?" check; `release` runs `/orc-test analyze` after the tag check. A red gate stops with the
report and nothing is pushed; no skip flag (plain `git push` is the escape); an exit-0 run with
no ✓ (`not measurable`, `missing … — skipped`, `nothing measured`) is reported and the push
proceeds. Pinned by `hooks/scripts/tests/test_orc_git_skill.py`; said for the user on
`docs/commands/orc-git.md`.

**The spec was wrong about Orclab's own code, and the final review caught it.** Spec §3 said
`coverage`'s report "ends with `gates failed: …`"; that line is printed only by `analyze`
(`cli.py:261,263`) — `cmd_coverage` (`cli.py:137-151`) returns 1 with no hand-off line. §4 keyed
the "can't measure" outcome to a `not measurable` line that two of its three cases never print.
Both were carried faithfully into the skill and the page by Tasks 2-3 and found by the
whole-branch review against `cli.py`. Fixed spec-first (`a4997ef`) then skill/page/test
(`086082e`); the pinning test now asserts the full `--cwd <repo root> coverage` command, so a
gate weakened to `run` fails it (proved red/green). Same shape as CLAUDE.md's "a claim about
Orclab's own code is a claim about code" — the review that opened `cli.py` was the pass the
spec's author skipped.

**Verified live 2026-09-16** (plan Task 4), through the real surface: `/orc-git push` on `main`
with 7 commits ahead — `Python coverage 94.1% (2889/3070 lines) ✓`, exit 0, pushed
`2a93d52..033e47c`. Red branch `scratch-v21-red` with one `assert False` — `1 failed, 712
passed`, `Python: tests failed; coverage not measured`, `nothing measured`, exit 1, stopped,
`git ls-remote --heads origin scratch-v21-red` empty; `git push -u origin scratch-v21-red` by
hand then worked (the escape, on purpose); branch deleted both ends. `cp` path: this entry is
the committed-not-pushed change it ran on — see the commit that carries it. `release`'s gate is
unverified until the v21 tag is cut; verify it then (six suites of `analyze`, expect ten to
fifteen minutes) and update this entry. One spec gap found by the final review and not fixed
here is #47.

## #47: /orc-git release measures HEAD, not the tagged commit, when HEAD has moved past the tag

Found by the v21 whole-branch review, 2026-09-16 (#46). `release [tag]` accepts any existing
local tag — the newest by default, or one named — and its new step 4 runs `/orc-test analyze`
on the working tree as it stands. When HEAD is the tagged commit, which is the common case
right after `/orc-version`, that is the tree being released. When HEAD has moved past the tag
(a commit or two landed after `/orc-version` and before `/orc-git release`), the gate measures
a tree that is not the one the tag names, and a green report says nothing about what people
will download. The spec's dirty-tree line (§2) covers uncommitted changes but not this.

Not a v21 defect to fix in the gate's own commit — the spec did not decide it — but one line of
the same shape as the dirty-tree line would close it: if `git rev-parse <tag>^{commit}` is not
`HEAD`, say so in the report. The alternative, checking the tag out into a temporary worktree
and running `analyze` there, is what `merge` step 3 already does for a branch; whether a
release should measure the tag's tree rather than warn is a decision for whoever picks this up.
Scope: `release` only; `push` and `cp` always push HEAD, so what they measure is what they push.

## #48: security-discipline: every project's rules and the extra set for one strangers can reach — v22 (RESOLVED 2026-09-19)

Requested by direflail 2026-09-19, while putting an API on DreamHost (which serves PHP and nothing
else): *"if running this sans framework is going to make us vulnerable, i need to know now. i
haven't run php in literally 20 years."* Then, generalised: *"security needs to be a part of
every project. what that means may depend on the project itself (something running locally like
orcshot doesn't need the security of something sitting out on a webhost where bad actors can
detect it)."* Asked whether the general rule comes before or after the PHP stack skill: *"B. it
needs to happen before anything."* PHP is v23 (#50). Design in
`docs/superpowers/specs/2026-09-19-orclab-v22-security-discipline-design.md`, plan in
`docs/superpowers/plans/2026-09-19-orclab-v22-security-discipline.md`, executed the same day.

**What should already have covered it, and did not** (the spec's own search, per CLAUDE.md's
"Before building anything"): every shipped `SKILL.md`, `CLAUDE.md`, `BACKLOG.md` and the bundled
scripts. `code-discipline` — seven rules on the shape of code, none about trust, input, secrets or
transport. `test-discipline` — "know the scenarios first", never the hostile one. `secret-hygiene`
— keeps a credential out of the transcript, not out of the repo or the built artifact.
`aikido:scan` — a real SAST plugin on this machine, not part of Orclab. `code-modernization`'s
`security-auditor` / `modernize-harden` — a scanner for existing code, nothing for a project being
born. Nothing said "this project is reachable by people you did not invite, so these rules apply."

**What shipped**, by spec section. §1: `skills/security-discipline/SKILL.md`, `user-invocable:
false`, nine rules in two tiers — rules 1–4 *Every project* (no secret in the repo or artifact;
dependencies audited; anything downloaded or run at runtime verified first; least permission) and
rules 5–9 *Reachable by strangers* (network input hostile until validated; every route
authenticates unless deliberately public in the code; no internals in an error; transport
encrypted and plain HTTP refused; rate limits exist) — each traced to the OWASP Top 10:2025, OWASP
ASVS 5.0.0 or the 2025 CWE Top 25, read live 2026-09-19; nine and not a hundred for
`code-discipline`'s reason, a hundred-rule list is not read. §2: `## Security — where
security-discipline lands` in all nine `skills/stack-*/SKILL.md` (static-analysis ruleset,
dependency-audit command, where secrets live and the `.gitignore` lines, what the exposed tier
scaffolds), pinned by `test_every_stack_skill_is_expected`; `/orc-code`'s New-Project Flow asks
"Will anyone you didn't invite be able to reach this?" with the answer proposed from the platforms
ticked, scaffolds the security lint config and the exposed tier's pieces, and quality mode wraps
`code-modernization:modernize-harden` behind an availability check; `test-discipline` names the
hostile case at every trust boundary. §3: `/orc-test audit` for all eight languages (Swift and
GDScript say "none free"), joined to `/orc-git push`, `cp` and `release` beside the v21 gate — a
known-vulnerable dependency stops the push; `lint_on_write` unchanged, since the security rules
sit in the same linter config. §4: `test_security_discipline.py`, `test_cli_audit.py` plus a
captured fixture per language with a README saying which were real captures, `test_orc_git_skill.py`
widened to `audit`, `test_orc_code_skill.py`; `docs/commands/orc-test.md`, `orc-code.md`,
`orc-git.md` in the same commits as their skills. Not built, by decision: a secret-scan hook over
git history (#49), runtime protection, penetration testing.

**Verified live 2026-09-19** (spec "Verification", plan Task 11), every line as printed.

*`/orc-test audit` on Orclab itself.* First run: `Python: missing pip-audit — pip install pip-audit
— skipped`, exit 0 — the command never installs; pip-audit 2.10.1 was installed by hand into the
user site the suites already use. Second run: ``ERROR:pip_audit._cli:pyproject file pyproject.toml
does not contain `project` section`` then `Python: audit output not understood — see above`, exit
1. Orclab's root `pyproject.toml` is tool configuration only and declares no dependencies, so
pip-audit refuses it, and with the merge `/orc-git push` on Orclab is red until that is settled —
#54, not fixed in Task 11 because both fixes were design calls (the v22 review chose one the same
day; #54 is resolved, and the line on Orclab is now `Python     audit not available — nothing
declared: pyproject.toml has no [project] table`, exit 0).

*`ruff check --select S .` on Orclab:* `Found 1487 errors.` — 1352 of them `S101` (`assert`, i.e.
the test suites), 54 `S603`, 48 `S607`, 21 `S404`, 4 `S314`, 4 `S405`, 3 `S310`, 1 `S602`. Under
`stack-python-desktop`'s own two config lines (`ignore = ["S4"]`, `"tests/**" = ["S101"]`) it is
still `Found 1462 errors.`, because ruff anchors `tests/**` at the project root and Orclab's tests
live at `skills/*/scripts/tests/` and `hooks/scripts/tests/`; with `**/tests/**` it is `Found 110
errors.` (54 `S603`, 48 `S607`, 4 `S314`, 3 `S310`, 1 `S602`; no `S101` outside tests). Orclab's
own adoption is a quality-mode pass, not done here.

*The scaffold.* Verdict first: everything `stack-web`'s `### Reachable by strangers` says the
exposed tier scaffolds was there — auth, the public/private split, bounded input, the
internals-free error handler, the rate limit — plus the security lint config and the secrets
layout; the one absent piece, transport, is the one the section itself defers to the reverse
proxy's config on the first project; and the one red line the audit printed was a parser bug in
`/orc-test`, fixed the same day, not the scaffold's. The evidence: `/orc-code` was followed from
this branch's `skills/orc-code/SKILL.md` (the
installed plugin was v0.21.0) with the answers new project, `v22check`, app, web, exposure "yes",
minimal example, into a scratch directory, per `stack-web`. Node 20.20.2 on this machine satisfies
Vite 8 (≥ 20.19) but not Vitest 5 (≥ 22.12); network was up. Against `stack-web`'s Security
section, item by item: static analysis — `web/.oxlintrc.json` with the Lint section's three rules
plus `react/no-danger` and `react/jsx-no-script-url` (the template's own `react/rules-of-hooks`
and `react/only-export-components` kept — the section's "written once" block omits them), and
`pyproject.toml` with `extend-select = [..., "S"]`, `ignore = ["S4"]`, `"tests/**" = ["S101"]`,
present; dependency audit — present, below; secrets — `app/config.py` `Settings(BaseSettings)`
with `secret_key: str` and `env_file=".env"`, root `.gitignore` carrying `.env`, present; reachable
by strangers — auth (`pyjwt` 2.14.0, `pwdlib[argon2]` 0.3.1, `/api/token`, `get_current_user`
raising 401), the public/private split (`APIRouter(dependencies=[Depends(get_current_user)])`
beside a bare one), input as a Pydantic model with `Field(min_length=1, max_length=64)`, errors
(`@app.exception_handler(Exception)` returning `{"error": "internal error", "id": …}`; `debug`
left `False`), rate limit (`slowapi` 0.1.10, `@limiter.limit("5/minute")` on `/token`), all
present; transport — absent, as the section says: the redirect and HSTS are the reverse proxy's
config, "written into the proxy config the scaffold leaves, per proxy, on the first project", and
no proxy config was written. Every package resolved to the version the skill's table names
(FastAPI 0.141.1, pydantic-settings 2.15.0, SQLModel 0.0.42). The installed v0.21.0
`lint_on_write` fired on the first write of `app/main.py` with the project's own config — §3's
first mechanism, live: `hardcoded-password-string: Possible hardcoded password assigned to:
"token_type"` on FastAPI's tutorial `token_type: str = "bearer"`; answered with the named
per-line suppression. `npm run build` exit 0; `npx oxlint --deny-warnings` first failed on the
template's own 110-line demo `App.tsx` against the Lint section's `max-lines-per-function: 60`
(replaced by the minimal example, then exit 0); `ruff check .` `All checks passed!`; pytest `3
passed` with the two hostile-case tests `test-discipline` now names (unauthenticated → 401,
malformed → 422) — PyJWT 2.14.0 warned `InsecureKeyLengthWarning` on a 26-byte test key, which
`openssl rand -hex 32` never produces; `npx vitest run`: `No test files found`. After `git init`,
this branch's `run.py --cwd <scratch>/v22check audit`: `detected: Python, JS/TS (web/)`, then at
first `Python: audit output not understood — see above` beside `JS/TS      audit ✓ 0 vulnerable`,
exit 1 — a parser bug, not the scaffold's: `runner.run` merges stderr into stdout and pip-audit
prints `No known vulnerabilities found` (or `Found 36 known vulnerabilities in 3 packages`, both
captured live) on stderr ahead of its JSON, so every real Python run was "not understood" and the
fixture tests, fed pure JSON, could not see it. Fixed in the same pass the way `csharp.py` already
reads its tool (`raw_decode` from the first `{`), pinned by
`test_audit_findings_skips_pip_audits_stderr_summary`; rerun: `Python     audit ✓ 0 vulnerable`,
`JS/TS      audit ✓ 0 vulnerable`, exit 0. The directory was deleted. `/orc-git push` on it, the
spec's last check, was not run — the scaffold had no remote, and the gate's own live check is #46's.

**Also found on the way**, each its own entry: #51 (the Gradle audit reads only the root project),
#52 (`stack-unity`'s Lint block may never reach Unity's compiler), #53 (a multiplayer game's
server has no stack skill), #54 (Orclab's own audit line).

## #49: A secret-scan hook over git history is not built; security-discipline's repo rule is prose plus .gitignore

Today `security-discipline` rule 1 ("no secret in the repo or the built artifact") is prose plus
the `.gitignore` entries each stack skill's `### Secrets` names, and ruff's `S105`–`S107` on
the Python side at write time — nothing looks at what is already committed, so a key that
reached a commit before the rule existed, or through a path the linter does not see, stays in
history unnoticed. A hook over git history would add that: scanning every commit's content for
credential shapes on `push` (the way `/orc-git`'s gate already runs `audit` there) and stopping
the push before the history leaves the machine. It waits for a real case — the v22 spec
(`docs/superpowers/specs/2026-09-19-orclab-v22-security-discipline-design.md`, §3 "Deliberately
not built") names it as "a BACKLOG entry citing this spec", and no project has yet leaked a
secret into Orclab-managed history; `secret-hygiene` holds the recovery procedure when one does.

## #50: PHP as a /orc-code alternative on the web row — v24 (RESOLVED 2026-09-20)

direflail is putting an API on DreamHost, which serves PHP and nothing else; the request that
became v22 (#48) started as "add PHP to `/orc-code`", and direflail's decision was that the
security rule comes first — *"B. it needs to happen before anything."* This is the second half:
PHP as an alternative on the Defaults Table's web row, with a `skills/stack-php/SKILL.md` that,
per CLAUDE.md's "Before the first project builds on a stack ... Orclab has never met", is written
from live research before the first project, and is born with the `## Security — where
security-discipline lands` section v22 defined (static-analysis ruleset, dependency-audit
command for `/orc-test audit` — Composer's `audit` is the candidate to confirm — where secrets
live, what the exposed tier scaffolds).

**Confirmed live 2026-09-19, so the research does not start from zero:** php.net's supported
versions table — 8.3 is security-only until 2027-12-31, 8.4 active until 2026-12-31 and then
security-only, 8.5 supported until 2027-12-31; DreamHost's PHP-version page lists 8.5, 8.4, 8.3
and 8.2 as selectable per domain; DreamHost's own page has the Composer install steps for a
shared account; orcshot.org is set to 8.5; Linux Mint 22.3's apt has 8.3. Shared-hosting
publishing (DreamHost as the confirmed-live example) is a separate task, not PHP-specific, and
direflail wants it written from a real deployment, not before one. Starts when v22 ships.

**Update 2026-09-20 — v24, after v23 (containers).** The "how do we run PHP 8.5 locally"
question this entry's brainstorm opened became v23 first, by direflail's decision (#58): a
container as an opt-in development environment for any stack, not just PHP. This entry is now
v24 and starts when v23 ships; its live check runs in the container `stack-php`'s Containers
section will define — the toolchain and Composer's audit inside the image, nothing installed on
the machine — with the section proposing "yes" to `/orc-code`'s container question, PHP being
the toolchain unusual on a dev machine that §1 of the v23 spec had in mind.

**Update 2026-09-20 — spec written and approved:**
`docs/superpowers/specs/2026-09-20-orclab-v24-php-design.md`. Scope is the skill *and* the
machinery (direflail: "B") — `stack-php`, a `php.py` module for `/orc-test` with `languages/php.md`
and captured fixtures, a `.php` row in `lint_on_write`, PHP on the web row's Alternatives column —
but not the real DreamHost API, which is its own session and gets a handoff file
(`docs/handoffs/<date>-php-first-project.md`). Order is prove-then-write (direflail: "A"): the
image is built and every tool run inside it on a sample project first, so the Containers section
is the first that says "run here." The "back end or whole row" question was withdrawn — a PHP
server emits JSON or HTML, one stack; the framework is decided by live research under three
constraints (shared hosting, JSON first, OpenAPI from code), runner-up stubbed. The audit command
this entry promised for `/orc-test audit` is now something `/orc-test` can actually run rather
than a sentence in a skill. Opens #64 (shared-hosting publishing) and #65 (cross-project
dependencies); `composer.json` goes on #6's list.

**Resolved for real, not just tracked.** v24 shipped: `skills/stack-php/SKILL.md`, PHP support in
`/orc-test` (`skills/orc-test/scripts/orc_test/langs/php.py`, four captured fixtures), a `.php`
row in `lint_on_write`, and PHP on the Defaults Table's web row — each proven against a real,
uncommitted sample project (`v24check`) run live inside a Podman container, not assumed.
`php8.5-cli` was already on the host from the Surý PPA since 2026-09-19 (not by v24); Composer
and every PHP tool were not, and all of them ran through the container — the premise "nothing
PHP on the host" in the plan was narrower in truth than in wording.

**The framework:** Slim 4 (`slim/slim` 4.15.3, `slim/psr7` 1.8.0, `zircote/swagger-php` 6.9.0) —
"the easiest option that meets all three of spec §2's constraints on a first-party page: Slim's
own deployment docs have a section headed 'Deploying to a shared server', its JSON response is
three lines, and swagger-php produces a valid OpenAPI document from one `#[OA\Info]` and one
`#[OA\Get]`/`#[OA\Response]` pair on the handler" (Task 1 report). Laravel 13 + Scramble was
stubbed as runner-up; Symfony/API Platform and plain PHP were each given a sentence on which
constraint they lost.

**The image's Dockerfile**, as it ended up after Task 2's live fixes:
```dockerfile
FROM php:8.5-cli
COPY --from=docker.io/library/composer:2 /usr/bin/composer /usr/local/bin/composer
RUN apt-get update && apt-get install -y unzip
RUN pecl install pcov-1.0.12 && docker-php-ext-enable pcov
```
Three fixes Task 2 needed to reach it, each recorded with its reason: (1) `COPY --from=composer:2`
→ `docker.io/library/composer:2` — Podman resolves `FROM php:8.5-cli` through its own
`shortnames.conf` but has no alias for a bare `composer`, so the short name in `COPY --from` had
nowhere to go on either engine; (2) `RUN apt-get update && apt-get install -y unzip` — `php:8.5-cli`
ships neither `unzip`/`7z` nor the `zip` extension, and installing the extension instead made
Composer warn that unpacking through it loses executable-bit permissions, so `unzip` is the
smaller, warning-free fix; (3) not a Dockerfile fix but a procedural one — `podman compose build`
exits 0 even when the underlying build failed, so its output has to be read for
`COMMIT`/`Successfully tagged` rather than trusted by exit code.

**The real `/orc-test analyze` and `audit` output**, run live in the container against the
`v24check` sample (Task 3 Step 7), verbatim:
```
PHP        coverage 20.0% (1/5 lines) ✗ (min 80)
      0.0%  <SCRATCH>/src/GreetAction.php
    html report: <SCRATCH>/.orclab/test/php/html
           TCE 20.0% ✗ (min 70)    lint: not run — no test-specific lint exists for PHP (no PHPStan rule reports an assertion-free test)
    note: vendor/bin/phpunit, infection and phpstan are the project's own require-dev packages; `composer install` once, and again when composer.json changes.
    note: Infection needs a coverage driver (pcov or xdebug) loaded in the PHP that runs it.

gates failed: coverage, tce
```
```
PHP        audit ✓ 0 vulnerable
```
Both coverage and TCE gates failing on the sample was honest, not a bug: `Greeting.php` is tested
(1/1), the invokable `GreetAction.php` route handler is not (0/4) — the PHP twin of
`python.md`'s "route handler is not mutated usefully" caveat Task 1 flagged in advance.

**The live `lint_on_write` hook run** (Task 4 Step 6), stderr's opening line verbatim (paths
abbreviated to `.../v24check`):
```
orclab lint_on_write: `.../v24check/vendor/bin/phpstan analyse` on .../v24check/src/Bad.php exited 1 - code-discipline's checkable rules, from the project's own config. Set ORCLAB_LINT_ON_WRITE_OFF=1 to disable.
```
PHPStan, run through the project's own `vendor/bin/phpstan` (preferred over PATH the same way JS
linters already prefer `node_modules/.bin`), reported the undefined-variable and always-true-
condition findings on the deliberately bad `Bad.php`; exit code 2.

**#64 and #65 remain open.** #64 (shared-hosting publishing) waits for the first-project session
that actually deploys the API to DreamHost and records what a real upload takes, through
`release-checklist`, in its own `RELEASING.md`. #65 (cross-project dependencies) waits for the
first session that works on a project calling another project's API — the orcweather session that
adds a client against this PHP API — to either find the contract from `stack-php`'s Layout section
and close the entry saying a sentence was the record, or stumble on something that becomes the
entry's material.

**Update 2026-09-20 — the first project reported back.** orcweather's `docs/orclab-php-findings.md`
is the report the v24 handoff asked for. Every version the skill named came out of the image
exactly, and none of the three Dockerfile fixes had to be rediscovered — the "run every tool
live before writing" method held. What the skill had wrong or missing, each now corrected in
`skills/stack-php/SKILL.md`: `pdo_sqlite` is on the host (was "not checked"); the host-PHP dev
loop is a trap (that machine's PHP had no `curl`) and the `ports:` line is now the proposal;
Infection's "tests must be in a passing state" has a second cause — any stderr byte, which
`error_log()` produces in the CLI — fixed in `phpunit.xml`; OpenAPI attributes are ten points of
MSI under `--with-uncovered`, excluded by regex in `infection.json5`; `addErrorMiddleware`'s third
argument logs a stack trace per 404 and is now `false` for a public API; `JSON_PRESERVE_ZERO_FRACTION`
for GeoJSON; the `-o` form of `openapi` confirmed. Two findings were not the skill's: `/orc-test`
cannot run a containerised sub-project (#66, new), and `/orc-version` does not bump
`composer.json` (#6, already listed). One was `/orc-code`'s — the session reached for a second
repository for `server/` and needed reminding that one repository holds every part; the Route
step now says so.

## #51: /orc-test audit on a multi-module Gradle build reads only the root project's dependencies until dependencyCheckAggregate is wired

Found writing v22's `/orc-test audit` for Kotlin and Java (#48, plan Tasks 2 and 5):
`./gradlew dependencyCheckAnalyze` audits the project it is applied to, and `java.py`'s
`_report_cmd` (which `kotlin.py` reuses) reads the root project's
`build/reports/dependency-check-report.json`, so on a multi-module build the
audit sees only the root's own dependencies — and the root of a Kotlin Multiplatform project or
a root-plus-`app/` Android project declares none, so every one of them audits nothing and
reports it as clean. `skills/orc-test/languages/kotlin.md`'s `## Audit` records the gap in its
own words: *"A multi-module build wants `dependencyCheckAggregate`, not wired here."* The fix
is that task — `dependencyCheckAggregate` walks every subproject and writes one report at the
root — plus a captured fixture from a real multi-module run; until then a Kotlin or Android
project's audit line is only meaningful when its dependencies are declared at the root.

## #52: stack-unity's Lint block installs analyzers through the .csproj, which Unity's own docs say may never reach its compiler

Found writing `stack-unity`'s Security section (v22, #48, plan Task 8): the skill's Lint section
(2026-09-13) installs SonarAnalyzer through a `<PackageReference>` in the `.csproj` and sets
severity in `.editorconfig`, but Unity's own docs, read live 2026-09-19, install an analyzer as
the DLL itself under `Assets/` with the asset label `RoslynAnalyzer` and set severity through a
`.ruleset` — Unity regenerates the `.csproj` for the IDE and says of its own analyzers that a
package reference *"isn't configured automatically in the Unity Editor"*. So the Lint block's
four shape rules may reach only the IDE and never Unity's compiler or a batch-mode build; the
Security section says so in its "How the analyzer reaches Unity's compiler is not the `.csproj`"
paragraph and works around it with `Assets/Default.ruleset`. The first Unity project through
`/orc-code` settles it — whether Unity 6's compiler loads the Sonar DLL, whether a ruleset
`Error` stops a batch-mode build, and whether the Lint section's `SonarLint.xml` parameters
reach the compiler by that path at all — and corrects the Lint section the same day if the
`.csproj` form is IDE-only, as `skills/stack-unity/SKILL.md` already promises.

## #53: A multiplayer game's server is the Reachable-by-strangers tier and no stack skill covers it; the first multiplayer game researches the server side

Both game skills' Security sections (v22, #48, plan Task 8) scope themselves to the *Every
project* tier and say multiplayer is out of scope: a game whose server other players reach is
the *Reachable by strangers* tier on that server, and no stack skill covers a game server.
Godot's own *High-level multiplayer* page (read live 2026-09-19) states `security-discipline`
rules 5 and 9 in its words — *"treat all client input as untrusted"*, *"Validate RPC arguments
before applying them to the game state"*, *"Add safety checks and rate limits to actions that
can be triggered frequently"* — and Unity's *Multiplayer* page sends a game that *"hosts
players locally or over a network"* to its Multiplayer Center. What is missing is the server
side as a stack: where the server runs, what it is written in, how rules 5–9 land in that
toolchain, and what `/orc-code` scaffolds for it. Per CLAUDE.md's "Before the first project
builds on a stack ... Orclab has never met", the first multiplayer game writes that from live
research before its server is built; until then `skills/stack-godot/SKILL.md` and
`skills/stack-unity/SKILL.md` point here.

## #54: /orc-test audit is red on Orclab itself: pip-audit refuses a pyproject.toml with no [project] table, so /orc-git push on Orclab stops (RESOLVED 2026-09-19)

Found running v22's live verification (#48, plan Task 11 Step 1) on 2026-09-19: `python3
skills/orc-test/scripts/run.py audit` on Orclab itself prints ``ERROR:pip_audit._cli:pyproject
file pyproject.toml does not contain `project` section`` and then `Python: audit output not
understood — see above`, exit 1. Orclab's root `pyproject.toml` holds `[tool.pytest.ini_options]`
and `[tool.ruff]` only — it is a plugin, its scripts import the standard library, and pytest,
mutmut, ruff and pip-audit are installed by hand — so it declares nothing for pip-audit to audit,
and pip-audit's `.` form refuses a pyproject with no `[project]` table. The consequence is
immediate once v22 merges: `/orc-git push` and `cp` on Orclab go red on every run — the gate
treats an unreadable audit as a stop, by design (#46's rule, widened to `audit` by v22 §3) — and
the only way to push Orclab is plain `git push`, the escape that is meant for the exception, not
the rule. Every consuming project whose `pyproject.toml` exists only to configure tools (a
plugin, a script collection, a repo whose Python is glue) hits the same line.

Two fixes, each a design call, which is why neither was made in Task 11. (a) Give Orclab's
`pyproject.toml` a `[project]` table with `dependencies = []`: pip-audit then returns an empty
`dependencies` list and the line is `Python     audit ✓ 0 vulnerable` — honest, since nothing is
declared — but `orc_release/versionfiles.py`'s `detect()` says *"pyproject.toml only counts if it
has a [project] table"*, so from then on `/orc-version` writes a version into a file that has
never carried Orclab's version (`.claude-plugin/plugin.json` does), a second copy to keep in
step. (b) Teach `langs/python.py`'s `audit_unavailable` to recognise a `pyproject.toml` with no
`[project]` table and report it as the gate's "can't measure" outcome (`docs/commands/orc-git.md`:
*"When it can't measure … it says so in the report and pushes anyway"*), which adds a fifth line
shape to the four `_audit_line` prints and to `/orc-git`'s gate prose, and has to be phrased so
that "nothing declared" is not mistaken for "nothing vulnerable". Scope: the Python line only —
the JS/TS half reads `package-lock.json` and is unaffected, and a project whose `pyproject.toml`
has a `[project]` table (`stack-web`'s and `stack-python-desktop`'s layout tables both describe
`pyproject.toml` as holding the name, the `version` `/orc-version` writes and `dependencies`,
which is that table) audits correctly, shown live the same day on the v22check scaffold.

**Resolved for real, not just tracked** — fix (b), decided by the v22 review the same day and
cheaper than the paragraph above claims: `cli.py` already printed `audit not available — <reason>`
for a language with no free tool, and `orc-git/SKILL.md` already said that line *"is carried into
the report and the push continues"*, so there was no fifth line shape and no gate prose to write.
What was added (commit `1c66836`): an optional language-module member `audit_nothing(root)`,
which `_audit_line` consults *before* `audit_unavailable` — so a tool-only repository without
pip-audit is never told to install a tool that will then refuse it — and whose reason prints on
that existing line with the gate left green. Python's returns `nothing declared: pyproject.toml
has no [project] table` when the file is absent or has no `project` key, else `None`; `[project]`
only, because `audit_cmd`'s `.` reads only that table (`requirements.txt` would be a different
`audit_cmd`, not this). Pinned by `test_audit_nothing_is_a_pyproject_without_a_project_table`
(missing file, tool-only, `[project]`) and
`test_nothing_declared_is_not_available_and_never_asks_for_the_tool` (the fake's
`audit_unavailable` raises if consulted). Live on this worktree, `python3
skills/orc-test/scripts/run.py --cwd . audit`: `detected: Python` then `Python     audit not
available — nothing declared: pyproject.toml has no [project] table`, exit 0 — where the same
command had printed `Python: audit output not understood — see above`, exit 1. Fix (a) was not
taken: Orclab's version stays in `.claude-plugin/plugin.json` alone.

## #55: orc-test audit: cli.py::_resolve gates audit on the test tools, not the audit tool

Found during the v22 whole-branch review (final-fix-report, 2026-09-19), reading `cli.py`'s
`_resolve`/`_audit_line`/`cmd_audit` together. `cmd_audit` iterates `usable`, and `usable` comes
entirely from `_resolve` (`cli.py:_resolve`, ~line 37): for each detected language module it
calls `m.missing(d)` — Python's `TOOLS = {"pytest": ..., "pytest_cov": ...}` — and if anything is
missing, prints `"{m.LABEL}: missing {tool} — {m.TOOLS[tool]} — skipped"` and excludes that
module from `usable` entirely, before `cmd_audit` (or any other subcommand) ever sees it.

The consequence: a Python project with `pip-audit` installed but without `pytest-cov` never gets
audited. `/orc-test audit` (and therefore `/orc-git push`'s audit gate, which runs the same
`cmd_audit` path) prints `Python: missing pytest_cov — pip install pytest-cov — skipped` and
nothing else for that language — not `audit not available`, not a vulnerability count, nothing
that says "audit". The push proceeds. This is a way the security gate `security-discipline` rule
2 exists to enforce (`dependencies audited`) silently does not run, for a reason that has nothing
to do with whether dependencies can be audited — the missing tool is a *test* tool, and audit's
own tool (`AUDIT_TOOL`, `audit_unavailable`) is never consulted.

Scope: this is specific to how `_resolve` builds `usable` — it conflates "can I test this
language" with "can I do anything at all with this language," and `audit` inherits the narrower
gate. It does not affect a project where the test tools are present (the common case Orclab's
own dogfooding has exercised so far), which is likely why the v22 live runs (BACKLOG #48) never
tripped it. Fix shape: `cmd_audit` needs its own resolution path — one that checks the audit
tool's own availability (`audit_unavailable`/`audit_nothing`) rather than reusing `_resolve`'s
test-tool gate, or `_resolve` needs to keep a language usable for audit even when its test tools
are missing.

## #56: orc-test audit: python.audit_nothing calls a setup.py/requirements.txt-only project green with nothing audited

Found during the v22 whole-branch review (final-fix-report, 2026-09-19), reading
`skills/orc-test/scripts/orc_test/langs/python.py`'s `audit_nothing` after BACKLOG #54 shipped it.
`audit_nothing` returns `None` (declares something, audit proceeds) only when `pyproject.toml`
exists and has a `[project]` table; otherwise it returns `"nothing declared: pyproject.toml has
no [project] table"`, which `_audit_line` prints as `audit not available — ...` — honest about
*why*, green on the gate.

The consequence: a project whose dependencies are declared in `setup.py` or `requirements.txt`
alone — no `pyproject.toml` `[project]` table at all — reports the exact same "nothing declared"
line as a project with no Python dependencies whatsoever. That is wrong in spirit, not just
technically: `setup.py`/`requirements.txt`-only is a common, ordinary shape for exactly the kind
of API/backend project v22's `security-discipline` was written for (a FastAPI service predating
the `pyproject.toml` convention, or one that never adopted it), and its dependencies are real and
auditable — `pip-audit -r requirements.txt` reads them directly, no `[project]` table needed.
Today that project gets "not available," never audited, and the push gate is green.

Scope: this is `audit_nothing`'s own decision procedure, not `audit_cmd`'s `.` form (which
`#54` correctly restricted to declared-`[project]` pyproject.toml — that fix stands). The fix is
additive: `audit_cmd` needs a second shape — `["python3", "-m", "pip_audit", "-f", "json",
"--progress-spinner", "off", "-r", "requirements.txt"]` — chosen when `requirements.txt` exists
and there is no `[project]` table, with `audit_nothing` only returning "nothing declared" when
neither shape has anything to read. `setup.py`-only (no `requirements.txt`) is a real remaining
gap even after that — pip-audit has no direct way to read `install_requires` from `setup.py`
without invoking it — and may need its own note in `languages/python.md` when this is picked up,
rather than a promise to solve it silently.

## #57: orc-test audit: yarn/pnpm projects hit npm's ENOLOCK, and javascript.md's advice to fix it is wrong for them

Found during the v22 whole-branch review (final-fix-report, 2026-09-19), reading
`skills/orc-test/scripts/orc_test/langs/javascript.py`'s `audit_cmd`/`audit_findings` and
`skills/orc-test/languages/javascript.md`'s Audit section together. `audit_cmd` always runs
`npm audit --json`, which requires a `package-lock.json` or `npm-shrinkwrap.json` — *"npm requires
a package-lock or shrinkwrap in order to run the audit"* (the doc quote already in
`javascript.md`). A project whose lockfile is `yarn.lock` or `pnpm-lock.yaml` instead has no
`package-lock.json`, so `npm audit` returns an `ENOLOCK` error document, which `audit_findings`
correctly lands on the `_UNREADABLE` sentinel — but that sentinel fails the gate (`_audit_line`:
`audit output not understood — see above`, and `cmd_audit` returns 1). The result: a yarn or
pnpm project gets a red `/orc-git push` gate on every single push, forever, not because of a
vulnerability but because the audit tool `orc_test` runs doesn't match the project's package
manager.

`javascript.md`'s Audit section makes it worse, not better: its documented remedy for `ENOLOCK` is
*"run `npm install` first"* — which is actively wrong advice for a yarn/pnpm project. Running
`npm install` there either fails outright (workspaces set up for yarn/pnpm) or creates a second,
unwanted `package-lock.json` alongside the real lockfile, which is exactly the kind of tooling
confusion a project that deliberately chose yarn or pnpm does not want.

Scope: this bites only an *existing* project that already uses yarn or pnpm — every one of
Orclab's own stacks that generates a JS/TS project (`stack-web`, `stack-react-native`) scaffolds
with npm, so a project built through `/orc-code` never hits this. It is real for anyone bringing
an existing yarn/pnpm codebase under `/orc-test`/`/orc-git`, which is a supported, ordinary case
— `code-discipline`'s tooling is meant to work on code Orclab didn't scaffold. Fix shape: detect
the lockfile actually present (`yarn.lock` → `yarn npm audit --json` or `yarn audit --json`
depending on Yarn version; `pnpm-lock.yaml` → `pnpm audit --json`) and pick the audit command and
its findings-shape parser accordingly, the same way `_runner` already picks vitest vs. jest from
`package.json`; then correct `javascript.md`'s remedy line to match whichever manager the
lockfile names instead of unconditionally naming `npm install`.

## #58: Containers as an opt-in development environment — v23 (RESOLVED 2026-09-20)

The request, direflail 2026-09-20, in the brainstorm that had started as "how do we run PHP
locally": *"this shouldn't be just for php, we need to figure out how containerization fits best
into orclab and provide it as an option when building a project."* PHP became v24 (#50) and this
became v23: a container as an opt-in *development environment* — the toolchain and every
`/orc-test` tool live in it so nothing has to be installed on the machine — asked once at
scaffold, never the default, and never what ships. Spec:
`docs/superpowers/specs/2026-09-20-orclab-v23-containers-design.md`.

**Licensing, confirmed live 2026-09-20** (docs.docker.com/subscription/desktop-license): Docker
*Desktop* is free only for personal use, education, non-commercial open source, and businesses
under 250 employees *and* $10M revenue; Docker *Engine* is separate — *"The licensing and
distribution terms for Docker and Moby open-source projects, such as Docker Engine, aren't
changing."* On Linux, Engine installs without Desktop (docs.docker.com/engine/install/ubuntu,
which says Mint is *"not officially supported (though it may work)"*); Mint 22.3's apt has
`docker.io` 29.1.3 and `podman` 4.9.3, both Apache-2.0.

**The design, one paragraph per spec section.** *§1, the opt-in:* `/orc-code`'s New-Project
Flow gained a fifth question after Exposure — *"Run this project's toolchain in a container, so
nothing has to be installed on this machine?"* — proposed "no" unless the stack's `## Containers`
section says to propose "yes", skipped with a reason for a stack that cannot (iOS). "Yes" writes
two committed files at the root: a `Dockerfile` from the stack skill (toolchain plus every
`/orc-test` tool for that language) and a `compose.yaml` with one service named `orclab` that
mounts the project at its own host path and sets it as the working directory, so every path in
every report is valid on both sides. The committed `compose.yaml` with an `orclab` service *is*
the record (nothing under git-ignored `.orclab/` could be); `.orclab/test.yaml` overrides per
checkout with `container: false` and `runner: docker|podman`. Verify runs the build/test command
through the container. *§2, `/orc-test` through it:* one change in the one chokepoint,
`runner.run`, which becomes `<engine> compose run --rm -T --workdir <dir> orclab <cmd>` from the
project root after one `<engine> compose build orclab`; detection lives beside the config
(`container.detect`); `detect`'s first line says `(in container)`; `missing()` asks inside
(`probe.which`, `probe.python_module`); git and `/orc-test` itself stay on the host
(`runner.run_on_host`); no engine on PATH prints `container runner not found — install podman or
docker — skipped`, a failed build prints its output and `container build failed — see above`,
exit 1 — never the host as a fallback. `lint_on_write` gets the same prefix
(`container_prefix`). *§3, stacks and engine:* all nine `stack-*` skills carry `## Containers`
(yes with a Dockerfile, or cannot with the reason — iOS and every stack's iOS half); the engine
is settled once in `skills/orc-test/SKILL.md`'s `## Containers`. *§4:* tests red-first for every
piece, `docs/commands/orc-code.md` and `orc-test.md` in the same commits, and this live check.
*§5:* this entry, #59, #60, #50 and #33 updated — and #61, #62, #63 from the review and the check.

**The engine: Podman, Docker Engine the alternative; with both installed Podman is used.** The
one-sentence reason from `skills/orc-test/SKILL.md`: *"Podman runs as your own user with nothing
to join — a file it writes into the project 'is actually owned by your user on the host' — while
Docker Engine's daemon runs as root, and the `docker` group that lets you use it without `sudo`
'grants root-level privileges to the user'."* direflail installed `podman` 4.9.3 and
`podman-compose` 1.0.6 from Mint's apt on 2026-09-20; `podman info` says rootless, overlay;
`/etc/subuid` and `/etc/subgid` already held a range for the user.

**The live check, 2026-09-20, on this machine.** The scaffold `v23check` — `stack-web`, answers
new / app / web / exposure no / container **yes** / minimal example — was built by following this
branch's `skills/orc-code/SKILL.md` by hand (the installed plugin was v0.22.0). The host's Node is
20.20.2, below Vite's 22.12 floor, which is exactly the case `stack-web`'s section says to answer
"yes" for; the Vite half was therefore scaffolded *through* the container. The two files, as
written — `Dockerfile` verbatim from `stack-web`'s section:

```dockerfile
FROM node:24-trixie AS nodejs
FROM python:3.14
COPY --from=nodejs /usr/local/bin/node /usr/local/bin/node
COPY --from=nodejs /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
RUN pip install --no-cache-dir "fastapi[standard]" sqlmodel pytest pytest-cov mutmut pip-audit ruff
```

and `compose.yaml` verbatim from `skills/orc-test/SKILL.md`:

```yaml
services:
  orclab:
    build: .
    volumes:
      - .:${PWD}
    working_dir: ${PWD}
```

`podman compose build orclab`: **23.95 s wall**, first time, with the two base images pulled;
`podman images`: `localhost/v23check_orclab latest 1.46 GB` (`python:3.14` 1.14 GB,
`node:24-trixie` 1.25 GB). Inside: Node v24.21.0, npm 11.19.0, Python 3.14.7, pytest 9.1.1,
mutmut 3.8.0, ruff 0.16.8, pip-audit 2.10.1, `id` = root — and every file the container wrote
into the tree (`web/` from `npm create vite@latest web -- --template react-ts`, `node_modules`,
`mutants/`) came out owned by `direflail`, the rootless claim seen for real. The section's
Dockerfile needed nothing it did not say. Verify through the container: `npm run build` → `✓
built in 97ms`; `python3 -m pytest -q` → `3 passed`.

`/orc-test`, `python3 skills/orc-test/scripts/run.py --cwd <scratch>/v23check <sub>`, every
report line verbatim:

- `detect` → `detected: Python (in container), JS/TS (web/) (in container)` /
  `$ podman compose build orclab` / `$ podman compose run --rm -T --workdir <scratch>/v23check
  orclab python3 -c 'import pytest'` (and `pytest_cov`, `sh -c 'command -v npx'`) /
  `  Python: test command python3 -m pytest -q --ignore-glob=*mutants/*` / `  JS/TS: test
  command npx vitest run`, exit 0.
- `run` → `Python     ✓ 3 passed (1.1s)` / `JS/TS      ✓ 1 passed 1 passed (0.9s)`, exit 0.
- `coverage` → `Python     coverage 100.0% (8/8 lines) ✓` / `JS/TS      coverage 100.0% (1/1
  lines) ✓`, exit 0.
- `analyze`, first run → `Python     coverage 100.0% (8/8 lines) ✓` / `           TCE not
  measurable — mutation tool produced no mutants — check its configuration    lint: 0 findings`.
  Not the container: mutmut ignores decorated functions by design (`file_mutation.py`, naming
  `@app.post("/foo")`), so the FastAPI route was never mutated, and the one plain function
  returned a bare f-string, which mutmut has nothing to mutate — verified with 3.7.0 in a
  throwaway container, same result, and with a plain `def f(a): return a + 1`, 6 mutants.
  `languages/python.md` gained the caveat. With the logic moved into the plain function,
  `analyze` → `Python     coverage 100.0% (9/9 lines) ✓` / `           TCE 100.0% ✓    lint: 0
  findings` (10 mutants, all killed), exit 0. JS/TS the same run: `           TCE not measurable
  — mutation tool produced no mutants — check its configuration    lint: not run — eslint not
  configured with @vitest/eslint-plugin or eslint-plugin-jest` — Stryker 10.0.0 rejected
  `/orc-test`'s own flag, `error: unknown option '--jsonReporter.fileName=…'`; that is **#63**,
  not this.
- `audit` → `Python     audit ✓ 0 vulnerable` / `JS/TS      audit ✗ 2 vulnerable` / `    qs 2.2.5
  - 6.15.3: GHSA-q8mj-m7cp-5q26, GHSA-x5fp-wj9c-mxmx, GHSA-4mjr-xmp4-gh2g — fix npm audit fix` /
  `    typed-rest-client 2.3.1 - 3.1.0: via qs — fix npm audit fix`, exit 1 — real advisories in
  Stryker's own dependency tree, reported through the container exactly as they would be on a
  host.

The three negatives. `container: false` in `.orclab/test.yaml`: `detect` → `detected: Python,
JS/TS (web/)`; `run` → `$ python3 -m pytest -q '--ignore-glob=*mutants/*'` … `ModuleNotFoundError:
No module named 'fastapi'` / `Python     ✗ 1 error 1 error (0.3s)` / `JS/TS      ✓ 1 passed 1
passed (0.5s)`, exit 1 — the override holds, and the host run fails because FastAPI is not on
this machine, which is what the container was for. `runner: docker` (docker is not installed
here): `detect` and `run` → `detected: Python (in container), JS/TS (web/) (in container)` /
`Python: container runner not found — install podman or docker — skipped` / `JS/TS: container
runner not found — install podman or docker — skipped` / `nothing to run`, exit 0. `FROM
no-such-image:0`: `run` → `$ podman compose build orclab` / `container build failed — see above`
/ `podman build -f ./Dockerfile -t v23check_orclab .` / `STEP 1/1: FROM no-such-image:0` /
`Error: creating build container: short-name "no-such-image:0" did not resolve to an alias and
no unqualified-search registries are defined in "/etc/containers/registries.conf"` / `exit code:
125`, exit 1 — **after a fix this check found**, below.

`lint_on_write`, `echo '{"tool_name":"Write","tool_input":{"file_path":"<scratch>/v23check/app/
deep.py"}}' | python3 hooks/scripts/lint_on_write.py` on a four-deep loop: stderr `orclab
lint_on_write: `ruff check` on <scratch>/v23check/app/deep.py exited 1 - code-discipline's
checkable rules, from the project's own config. Set ORCLAB_LINT_ON_WRITE_OFF=1 to disable.` /
`too-many-nested-blocks: Too many nested blocks (4 > 2)` … `Found 1 error.`, then the engine's
own lines `podman run --name=v23check_orclab_tmp43165 --rm -i … -w <scratch>/v23check
v23check_orclab ruff check --no-fix <scratch>/v23check/app/deep.py` and `Error: executing
/usr/bin/podman-compose run --rm -T --workdir <scratch>/v23check orclab ruff check --no-fix
<scratch>/v23check/app/deep.py: exit status 1`, exit 2. The scratch project, its image, the two
base images and the `v23check_default` network were deleted afterwards; `podman images` is empty.

**What the plan got wrong, and what fixed it.** Research and review, before this check: the plan
had the image build going through `runner.run` — i.e. through the `compose run` wrap — where it
must go through `run_on_host` (the engine is a host command); `${PWD}` in `compose.yaml` is read
from the *environment* of the process calling the engine, and `cwd=` does not rewrite the
inherited `PWD`, so `runner.run_on_host` sets it explicitly; the tool-presence checks that had to
move inside were more than `missing()` — `audit_unavailable`, `mutation_unavailable` and the
hook's on-PATH check all asked the host; and gdUnit4 needed `--headless --ignoreHeadlessMode` to
run at all without a display. **This check found two more.** (1) `podman-compose` 1.0.6 — Mint's apt, the
version the install line names — **exits 0 when `podman build` fails**: `compose_build` discards
`build_one`'s result and only logs `exit code: 125` (1.6.0 returns the status; read in both
sources). The broken-Dockerfile negative "passed" the first time and ran the tests in the *stale*
image from the earlier build — the silent outcome §2 forbids, one layer under the guard. What
should have caught it, `cli._resolve`'s `cp.returncode != 0`, was widened rather than doubled:
`container.build_failed` also reads that logged line; one test with a fake engine that prints it
and exits 0; a fifth fact in `skills/orc-test/SKILL.md`'s engine bullet. (2) Four tests in
`test_cli.py` put a fake `docker` on PATH and were written on a machine with no engine; with
podman installed, `RUNNERS`' preference picked the real one and all four went red. The fixture
now pins `runner: docker`. `languages/python.md`'s `Last real run` carries the in-container
`analyze` line.

**Resolved**: v23 is shipped and was exercised on this machine through a real rootless engine
end to end — scaffold, build, all five `/orc-test` subcommands, the override, the two refusals,
and the hook — with every line above produced by the code as committed.

## #59: A devcontainer.json beside the Dockerfile, for editors that attach to the container

Deferred from v23 (#58) by direflail — *"A, leave B as an /orc-todo"* — and named in spec
`2026-09-20-orclab-v23-containers-design.md` §"Out of scope, by name": the devcontainer standard
(`.devcontainer/devcontainer.json`) describes a container environment for editors (VS Code,
Codespaces) and can point at the very `Dockerfile` v23 writes through its `build.dockerfile`
property, so adding it is one small file per project beside the existing two, not a second
mechanism. Written when someone wants their editor attached to the container; until then the
`compose.yaml` and `Dockerfile` are the whole record and nothing reads a devcontainer file.

## #60: Deploying a project as a container: a production image as an orc-package ingredient

direflail, 2026-09-20, while v23 (#58) was being designed: *"we probably will need to deploy a
container eventually, but that can be an /orc-todo as well."* v23's container is a development
environment and deliberately not production-shaped — it carries pytest, mutmut, Stryker and the
rest, and what it produces is ordinary project files that ship however the stack's `##
Deployment` section or `orc-package` ingredient says. Deploying *as* a container is a different
artefact: a production image with the runtime and the built code and no test tools, produced by
a new `orc-package` ingredient in the nine-section shape, and it is the stack's `## Deployment`
section that decides whether a stack ships that way at all (today none does — `stack-web`'s
still says shipping a container is parked). Written when the first project that deploys as a
container arrives, from that deployment, not before.

## #61: gdscript.py reads GODOT_BIN on the host and forwards --godot; inside a container the host must export the image's path

Found by Task 7's review of v23 (#58), 2026-09-20, and deferred from it. `gdscript.py`'s
`missing()` reads `GODOT_BIN` on the host on purpose (its own comment: *"GODOT_BIN is a host
environment variable"*) and `mutation_cmd` forwards the value to gdmutant as `--godot <path>`;
`compose run` passes no host variable into the container, so for a containerised Godot project
the host must `export GODOT_BIN=/usr/local/bin/godot` — the *image's* path, where the command
actually runs, not any Godot the host may have. `skills/stack-godot/SKILL.md`'s Containers
section documents exactly that mirror (*"`GODOT_BIN` is set in the image, and the host mirrors
it"*), so it works, but it is a value the developer has to know to set to a path that is not on
their machine, and a wrong one is reported as `GODOT_BIN` missing rather than as the mismatch it
is. The cleaner fix is the shape v23 gave every other tool check: a probe-style check where the
commands run — `probe.which("godot")` or reading `$GODOT_BIN` *inside* via `sh -c` through the
chokepoint — and passing `--godot` from what the container reports, so the host variable is only
consulted on a host run. Scope: GDScript projects that opted into a container; a host run is
unchanged. Not done in v23 because no Godot project has been built through a container yet, and
the host-mirror line in the stack skill covers the first one.

## #62: languages/python.md pins mutmut 3.7.0; PyPI has 3.8.0 (2026-09-12)

`skills/orc-test/languages/python.md`'s Mutation section still opens with *"mutmut 3.7.0 (PyPI,
2026-07-31)"*, while PyPI has had 3.8.0 since 2026-09-12 — noticed while writing
`stack-web`'s Containers section, and confirmed for real on 2026-09-20 when v23's (#58) live check
built its image from the unpinned `pip install … mutmut` line and got 3.8.0, which ran the
scaffold's suite to `TCE 100.0% ✓` with the same `[tool.mutmut]` keys and the same `mutants/`
cache shape `run.py` reads. A currency line, not a defect: the version stated is one release
behind what a fresh install gets, and the module's claims have now been seen to hold on the
newer one; the fix is the version and date in that line, under `currency-discipline`.

## #63: orc-test analyze: Stryker 10.0.0 rejects --jsonReporter.fileName, so no JS/TS project gets a TCE

Found by v23's live check (#58), 2026-09-20 — the first time `/orc-test`'s JavaScript mutation
step has met a real StrykerJS: `languages/javascript.md`'s previous "last real run" (2026-09-19,
the v22check scaffold) stopped at `No test files found`, so `mutation_cmd` had never actually
reached Stryker. On the v23check scaffold (`stack-web`, `web/` with `vitest` 5.0.1,
`@stryker-mutator/core` 10.0.0 and `@stryker-mutator/vitest-runner` 10.0.0 installed by the
project), `run.py analyze` ran `npx stryker run --incremental --reporters json,progress
--jsonReporter.fileName=<root>/.orclab/test/javascript/mutation.json` and Stryker answered
`error: unknown option '--jsonReporter.fileName=…'`, exit 1; the report line was `JS/TS
TCE not measurable — mutation tool produced no mutants — check its configuration`, which
misnames the cause — the tool never started. `npx stryker run --help` on 10.0.0 lists
`--reporters`, `--incremental`, `--incrementalFile` and the `--dashboard.*` options, and no
`--jsonReporter.*` one; `jsonReporter.fileName` exists in Stryker's config file, not as a CLI
flag (or not in this major — the research is whoever fixes this). The flag is
`skills/orc-test/scripts/orc_test/langs/javascript.py:102`, and `javascript.md`'s Mutation
section states the same command as fact. Consequence: no JS/TS project gets a TCE from
`/orc-test` today, containerised or not — the same failure on a host — and the
`--incremental` reporting also never ran, so the caveat about `reports/stryker-incremental.json`
is unverified. Fix shape: write the reporter's file name the way Stryker 10 accepts it (a
`--configFile` Orclab generates, or read Stryker's default `reports/mutation/mutation.json`
under the project instead of `<out>` — `stryker.py`'s reader already takes the newest `*.json`
with a `files` key under the directory it is given), run it live on a scaffold with a real test,
and record the run in `javascript.md`. Not fixed in v23 because it is the JS module's own
contract with Stryker, not the container layer, and the live check's job was to record it.

## #64: Shared-hosting publishing (DreamHost the confirmed-live example) — written from the first real deployment, not before one (RESOLVED 2026-09-20)

Opened by the v24 spec (`docs/superpowers/specs/2026-09-20-orclab-v24-php-design.md`, §7).
#50 has said since 2026-09-19 that shared-hosting publishing "is a separate task, not
PHP-specific, and direflail wants it written from a real deployment, not before one"; this is
that task, given its own number so `stack-php`'s Deployment section has something to point at
instead of pretending to know DreamHost.

**What is known, confirmed live 2026-09-19 (#50):** DreamHost's PHP-version page lists 8.5, 8.4,
8.3 and 8.2 as selectable per domain; DreamHost's own page has the Composer install steps for a
shared account; orcshot.org is set to 8.5. Nothing about upload, what a first deploy takes, or
where a `RELEASING.md` step lands has been run.

**Where the input comes from.** The v24 handoff file (`docs/handoffs/<date>-php-first-project.md`)
asks the first-project session — the one that actually deploys the API to DreamHost — to record
in its own `RELEASING.md`, through `release-checklist`: selecting the PHP version per domain,
Composer on the shared account, what is uploaded and how, and what the first deploy actually took.
Those lines are this entry's material. Until that session has run, this entry holds nothing to
build.

**What it becomes when picked up:** an `/orc-package` ingredient under
`skills/orc-package/ingredients/<name>/` in the nine-section shape, per CLAUDE.md's "Before the
first project ... ships to a channel Orclab has never met" — written from the recorded lines, each
stamped with the date the first project ran it. Not a PHP thing: a static React build lands on the
same host the same way.

**Resolved for real, not just tracked (2026-09-20).** The first project deployed the same day
the entry was opened: orcweather's API to DreamHost, recorded in its `server/RELEASING.md`
(eight steps plus a teardown, every one run) and `docs/orclab-php-findings.md` (the five answers
in the handoff's order). The ingredient is
`skills/orc-package/ingredients/shared-hosting/ingredient.md`, nine sections, every line
stamped 2026-09-20 or marked as not run. What the deployment settled, against what this entry
guessed: Composer is not installed on the host and never needs to be — `vendor/` is built
`--no-dev` in the dev container and rsynced (7.9 MB, 1.6 s); the document root is a per-domain
panel field (`<domain>/public`) set *before* the first upload, so Slim's `.htaccess`-in-the-web-
root recipe is unnecessary there; `display_errors = Off`, `log_errors = On` was already the
host's default; HTTPS was already on; the first deploy took ~2 minutes. `stack-php`'s
Deployment section now says this instead of "not yet written". Not covered, and said so in
both places: a `stack-web` front end served from the same `public/`, and a host that is not
DreamHost — the shape holds, the panel paths will not.

## #65: Cross-project dependencies — orcweather's app stacks will call the v24 PHP API; what, if anything, Orclab records about one project depending on another

Raised by direflail 2026-09-20 in the v24 brainstorm (spec
`docs/superpowers/specs/2026-09-20-orclab-v24-php-design.md`, §7): *"when we've got one stack
depending upon another, like orcweather's android/ios stacks depending on this php api stack, is
this something that needs to be recorded? if so, to what extent."*

**Nothing in Orclab records this today.** Searched every shipped `SKILL.md` and `docs/commands/`
page for a cross-project notion — "other project", "contract", "openapi", "sibling repo": the only
hits are "the project you're in", and every `.orclab/` file that exists (`git-repo.json`,
`publish/channels.yaml`, `publish/distro.yaml`, `test.yaml`, `test/analyze.json`) is one
project's own settings. A real gap, not a rule that failed to fire.

**What v24 does about it, and what it deliberately does not.** Does: `stack-php`'s Layout says
where the API's OpenAPI description lives and which tool produces it — the file a consuming app's
Dart or Swift client is written or generated against, and the thing a change to actually breaks;
"a framework that produces OpenAPI from the code" is one of the three constraints on v24's
framework research; the handoff file asks the first-project session to say in the API's README
where the contract is. Does not: a record in the *consuming* project ("calls that API, contract
at this path, deployed at this URL"). Nothing in Orclab would read it — no command asks "what does
this project depend on" — and a `.orclab/` file with no reader is config for its own sake.

**Trigger:** the first session that works on a project which calls another project's API — the
orcweather session that adds the client against the PHP API.

**Sequence, so "when" has an answer:** (1) opened here by v24; (2) the API's first-project session
writes the contract and the README sentence; (3) the orcweather client session either finds the
contract from that sentence and works — in which case a sentence *is* the record and this entry
closes saying so — or stumbles: cannot find the contract, does not know which deployed URL to
point at, changes the app against a contract that has since moved. Whatever it stumbled on is
what the record must hold, and only then is the shape designed; (4) built, if step 3 says so, by
whichever command turned out to need the reader — `/orc-code`'s add-a-feature flow asking "does
this change an API another project calls?", or `/orc-release` warning that an app depends on what
is being released. Its own small spec then. Could be v25, could be never.

**Not this:** anything that versions or locks the two repos together mechanically. Two repos with
a contract file between them is how this is normally done; Orclab should not invent a coupling.

## #66: /orc-test finds a language's marker two directories down but looks for its compose.yaml only at the repository root — a containerised sub-project is detected and then skipped (RESOLVED 2026-09-20)

Found by the first PHP project (orcweather, 2026-09-20; its `docs/orclab-php-findings.md`), whose
API is `server/` inside the Flutter app's repository — the layout `stack-php`'s Layout section
now names as the right one, and the one `stack-web` uses for `web/`. From the repo root, `run.py
detect` printed `PHP (server/)` — the marker two directories down, exactly as `skills/orc-test/SKILL.md`
"How it finds the languages" documents — and then `PHP: missing composer … or run inside the
stack-php container — skipped`.

**Why.** `skills/orc-test/scripts/orc_test/cli.py:53` calls `container.detect(root, cfg)` once,
with the repository root, and `container.py:26` reads `root / "compose.yaml"`. The marker walk
(`detect.py`) is per directory; the container lookup is not. So a `compose.yaml` beside
`server/composer.json` is never opened, `/orc-test` concludes the project is not containerised,
looks for `composer` on the host, and skips PHP. The consequence for that repo: `/orc-test` covers
Dart and Kotlin and the PHP tools are run by hand with the `podman compose run …` prefix from
`server/`, which is precisely the by-hand path the command exists to replace.

**A second observation from the same session, recorded so the fixer knows it exists:**
`run.py --cwd server detect` still detected Kotlin, Dart and PHP from the whole repository and
skipped PHP the same way — `--cwd` did not scope detection to `server/`. Whether that is intended
(detection from the git root regardless of `--cwd`) or a second defect is for whoever picks this
up to decide; it is not separately tracked.

**Shape of the fix, not done here.** Look for `compose.yaml` in the marker's directory first and
fall back to the root — `container.detect` takes the directory, not the root, and `runner.use()`
becomes per language rather than one global `_ACTIVE` (`runner.py`'s module-level container is
the thing that assumes one container per repo). `compose.yaml`'s `${PWD}` mount then has to be
set to the marker directory for that language's runs, which is what `runner.run_on_host` already
does for the root. The alternative — writing "one containerised project per repository" into
`skills/orc-test/SKILL.md` — is the smaller change and the wrong one: it would forbid the layout
the stacks recommend.

**What it does not affect.** A containerised project whose `compose.yaml` is at the repository
root (every fixture and every project before orcweather) is unchanged; a sub-project that is not
containerised runs on the host as before.

**Resolved for real, not just tracked (2026-09-20, same day).** `container.detect(d, cfg, root)`
now looks for `compose.yaml` beside the language's marker first and at the repository root
second; `cli._resolve` resolves one container per language, builds each distinct `compose.yaml`
once, and `_each(usable)` makes that language's container active before each loop body, so every
`run()` and every probe goes through the right one — `runner`'s single active container stays,
set per language instead of once. Proven two ways: `tests/test_cli.py::
test_containerised_sub_project_is_run_in_its_own_container` reproduces orcweather's shape (Python
at the root on the host, `server/composer.json` with its own `compose.yaml`) and failed before
the change with the exact "missing composer" line; and `run.py detect` on the real orcweather
repo printed `detected: Kotlin (android/), Dart, Swift (ios/), PHP (server/) (in container)`,
probed `composer` through `podman compose run … --workdir …/server`, and listed `PHP: test
command vendor/bin/phpunit`. 239 tests pass. The `--cwd server` observation: intended —
`detect.project_root` is `git rev-parse --show-toplevel`, so the project is always the
repository, and `--cwd` says where you are, not what to scope to; not a second defect.

## #67: /orc-test run reports Kotlin ✓ passed when Gradle's test task is NO-SOURCE — a language with zero tests passes instead of failing (RESOLVED 2026-09-20)

Found 2026-09-20 running `/orc-test` (no subcommand, i.e. `run`) from orcweather's root. The
report was:

```
detected: Kotlin (android/), Dart, Swift (ios/), PHP (server/) (in container)
Kotlin     ✓ passed (5.4s)
Dart       ✓ passed (4.8s)
PHP        ✓ passed (0.6s)
```

But the Gradle output above the Kotlin line ended `> Task :app:testDebugUnitTest NO-SOURCE` —
`android/app/src/test/` does not exist; the car module (six `.kt` files under
`android/app/src/main/kotlin/…/car/`) has no unit tests at all. Gradle exits 0 on a NO-SOURCE
task, so the build "succeeded" and `cli._run_tests` printed ✓.

The skill's own rule (`SKILL.md`, "When something goes wrong"): *"A language detected with no
tests → `0 tests ✗`, nothing measured — an empty suite is a failure, not a pass."* The code
implements that rule only for pytest: `_run_tests` sets `empty` from `"no tests ran" in
cp.stdout or cp.returncode == 5`, both pytest signals. Gradle's signal is the `NO-SOURCE`
outcome on the test task (and, when a test source set exists but is empty, a run with no
`tests completed` line); neither is looked for, so ✓ with no count is what a Kotlin project
with no tests gets. The same hole is presumably open for every other runner whose empty-suite
signal is not pytest's — Swift's `xcodebuild test` with no test target, Godot with no
`test/` directory, Stryker/Jest with no matching files — each language's `## Run` section
should say what its "zero tests" looks like and `_run_tests` (or a per-module hook) should
read it.

Consequence: the gate this command exists for is silently open for that language. `/orc-git
merge` runs `run` before and after landing a branch and would have waved the Kotlin car module
through with nothing tested. The owner's rule, stated the same day: **if a language is in a
project, it needs testing — full stop.** Detection already gets this right (Kotlin *was*
detected); the failure is only in what "passed" means afterwards.

Does not affect: `coverage` or `analyze` for Kotlin — untried on this project, and JaCoCo with
no test task would presumably fail loudly on its own; that is not verified. Does not affect
Dart or PHP, both of which printed real counts.

Companion in orcweather: its own BACKLOG records that the car module has no tests — that is
the project's debt, this entry is the tool's.

**Resolved (2026-09-20, same day).** `cli._run_tests` no longer decides "did anything run" with
pytest's signals for every language: a language module may carry `test_summary(root, cp) ->
(ran, counts)`, and `_pytest_summary` is the default for the ones that do not. `java.test_summary`
— shared into `kotlin` the way `audit_findings` already is — reads the JUnit XML under the
project's `build/test-results/` (Gradle) and `target/surefire-reports/` (Maven): none is `0 tests
✗`, otherwise the line carries the count (`12 passed 1 failed`), which Kotlin never had. Reading
the results files rather than the task lines does two things at once: it ignores the pub-cache
plugin modules a Flutter `android/` build also tests (their XML is outside the project — #68),
and it survives `UP-TO-DATE` runs that print nothing. Verified before relying on it: on Gradle
9.3.1 (orcweather's wrapper) a scratch project with one JUnit test wrote
`build/test-results/test/TEST-ATest.xml`; deleting the test and re-running removed the whole
`test-results` directory, so a deleted suite cannot pass on stale XML. The Maven glob is from
Surefire's documented layout, no `mvn` on this host. Proven two ways: `tests/test_cli.py::
test_language_that_says_nothing_ran_is_zero_tests_even_on_exit_zero` and `tests/test_lang_java.py::
test_summary_counts_junit_xml_under_the_project_only` both failed before the change (the first
printed `✓ passed`, the second `AttributeError`); and `run.py --cwd ~/projects/orcweather --lang
kotlin run` now prints `Kotlin ✗ 0 tests (1.5s)` and exits 1. 241 tests pass. `languages/kotlin.md`
and `java.md` now say what zero tests looks like for their runners. The other runners the entry
presumed open (Swift, Godot, Jest/Stryker, Dart, PHP, C#) are unchanged and unverified here —
each needs its own live "zero tests" run before its module gets a `test_summary`; that is
per-language work as each one meets a project with no tests, not one entry.

## #68: /orc-test's default Kotlin test command in a Flutter `android/` runs every pub-cache plugin's unit tests, not just the app's

Found 2026-09-20 reproducing #67. `kotlin.test_cmd` is `./gradlew test`; Flutter's generated
`android/settings.gradle.kts` includes every plugin project from `~/.pub-cache`, so that command
compiles and runs the plugins' own JUnit suites — on orcweather, `:geolocator_android`,
`:jni`, `:jni_flutter`, `:package_info_plus`, `:sensors_plus` and `:shared_preferences_android`
all got `testDebugUnitTest` tasks, and `shared_preferences_android` ran 12 tests and failed one
(`BUILD FAILED`, exit 1). That failure is not orcweather's and would print `Kotlin ✗ failed` on
a project whose own tests are green. orcweather already sidesteps it in `.orclab/test.yaml`
(`test: ./gradlew :app:testDebugUnitTest`, with a comment saying why) — the workaround is
recorded in `languages/kotlin.md` under "Flutter's `android/` is a special case", but nothing in
Orclab does it by default. `coverage_cmd` (`test koverXmlReport`) has the same shape.

Not just Flutter: any Gradle build that includes projects from outside the repository has it.
Which module is "the project's" is the question — the `build.gradle(.kts)` files under the
language's directory name them (`android/app/` → `:app`), and AGP's real task is
`test<Variant>UnitTest`, not the `test` lifecycle task that runs every variant. Not done in #67
because #67 is about what "passed" means and this is about what runs; and because `:app:test`
versus `:app:testDebugUnitTest` (one variant or three compiles) is a choice that wants a second
project to look at.

## #69: /orc-test analyze from a root with no [tool.mutmut] said "not measurable" although six packages below it each had one — v0.25.0 was released with no TCE (RESOLVED 2026-09-20)

Found 2026-09-20 by direflail asking, after `/orc-git release` for v0.25.0, "orclab has no
mutation testing?". It has six: `hooks/scripts`, `orc-package`, `orc-publish`, `orc-release`,
`orc-test` and `orc-todo` each carry a `pyproject.toml` with `[tool.mutmut]`, and #35 and #42
were measured through them. But `analyze` from the repository root printed `TCE not measurable
— no [tool.mutmut] found in any pyproject.toml at or above /home/direflail/projects/orclab` and
exited 0, because `langs/python.py`'s `_mutmut_config` only ever walked *up* from the target,
and the root's `pyproject.toml` deliberately has no `[tool.mutmut]` (mutmut has to run from
inside each package's directory to import the code under the name it mutates —
`languages/python.md`). `/orc-git release`'s rule — *"exit 0 but no language got a ✓ → continue
and carry it into the report"* — was written for a project with no mutation tool and treated
this the same way, so the release went out on coverage alone. Claude read the line, reported
it, and did not stop to ask why a repository with six configs said "no config" — the
before-explaining pass would have caught it; the release step was followed as a checklist.

**What should have covered it.** `mutation_unavailable`'s own message named the gap ("at or
above") and every earlier Orclab TCE run had been done with a path (`analyze skills/orc-todo/
scripts`, #35), so the root form had never been exercised as a gate until `release` started
running it (v21). Searched: `python.md`, `SKILL.md`, `docs/commands/orc-test.md`, `BACKLOG.md`
— nothing recorded that the root form could not see the sub-projects.

**Resolved (same day).** `mutation_cwd(root, target)` is now `mutation_cwds`, a list: the
nearest config at or above the target as before, or, when there is none, every `pyproject.toml`
with `[tool.mutmut]` below it (`mutants/` and the other `SKIP_DIRS` excluded, since mutmut
copies a pyproject into its cache). `cli._mutation` runs the tool in each, sums killed and
total into one score for the language, and rebases each run's survivors to the root as before;
a run producing no mutants names its directory. `mutation_unavailable` fires only when neither
form finds a config. Proven: `tests/test_lang_python.py::
test_mutation_runs_every_config_below_when_the_root_has_none` and `tests/test_cli_analyze.py::
test_analyze_sums_tce_over_every_sub_project_config` failed before the change; `analyze` from
Orclab's root now prints `TCE 80.5% ✓` (7032/8737, survivors listed per skill) — the gate
v0.25.0 should have been held to, and would have passed. 243 tests pass. `release`'s
"not measurable → continue" rule is unchanged: it is right for a project with no tool, and the
misconfigured-project case it mishandled no longer produces that line.

## #70: /orc-test wrote every report to <root>/.orclab/test/<lang>/, a path a sub-project's container cannot see — orcweather's PHP coverage was "not measurable" while phpunit said "done" (RESOLVED 2026-09-20)

Found 2026-09-20 on the first `/orc-test analyze` of orcweather after #66 — the first project
with a containerised sub-project (`server/compose.yaml` beside `server/composer.json`, the
layout `stack-php` recommends). The report said `PHP        coverage not measurable — no coverage
report found — see languages/php.md`, and `.orclab/test/php/` at the root was empty. Run by hand
from `server/`, `podman compose run ... vendor/bin/phpunit --coverage-clover
/home/direflail/projects/orcweather/.orclab/test/php/clover.xml` printed `Generating code
coverage report in Clover XML format ... done` — and left nothing on the host. The sub-project's
compose file mounts only its own directory (`.:${PWD}`, `${PWD}` = `server/`), so the root-level
report path exists *inside the container only*; phpunit wrote it there and `--rm` threw it away.
`cli._resolve`'s docstring stated the rule that broke: "every tool runs from [the marker dir]
while reports and `.orclab/test/` stay at the root" — true on the host, and for a root-level
container that mounts the whole repo, false for the one-container-per-language layout #66
introduced the same day. Infection was not affected only because its log path is relative to its
own cwd (`infection.json5`'s `logs.json`), which is how the run produced a 3.8 MB
`server/.orclab/test/php/infection.json` beside an empty root dir.

Scope: every language whose marker sits below the root *and* runs in its own container. A
sub-project on the host, or one whose container is the root's (mounting the whole repo), was
never affected. `analyze.json` is written by `run.py` on the host and was never at risk.

**Resolved (same day).** `_out(d, mod)`: each language's `.orclab/test/<lang>/` is now beside its
marker — `server/.orclab/test/php/` — the one host path its container is guaranteed to reach, and
where Infection already wrote; `analyze.json` alone stays at the root. Proven by
`tests/test_cli_analyze.py::test_analyze_reports_land_beside_a_sub_project_marker` (red before
the change) and by orcweather: `PHP        coverage 84.2% (144/171 lines) ✓`, `clover.xml`, `html/`
and `infection.json` all in `server/.orclab/test/php/`. `SKILL.md`'s Containers section and its
"Writes" column say where reports land now. A sub-project needs its own `.gitignore` line for
`.orclab/` (orcweather's `server/.gitignore` already had one).

## #71: /orc-test analyze read mutation_test's exit code 255 as a crash and said "TCE not measurable" beside a complete 662-mutant report; its survivors would have printed with line 0 (RESOLVED 2026-09-20)

Found 2026-09-20 on the first real Dart mutation run (`languages/dart.md` had carried "Last real
run: none yet" since 2026-09-11) — orcweather, mutation_test 1.8.1, 23 files, about three minutes.
`run.py` printed `TCE not measurable — mutation tool exited 255` while
`.orclab/test/dart/mutation-test.junit.xml` (156 KB, 662 `<testcase>`s, 255 `<failure>`s — TCE
61.5%) sat finished beside it. `bin/mutation_test.dart:169`: `if (!foundAll) { exit(-1); }` —
any surviving mutant is -1, which is 255 on Linux. `cli._mutation` accepted only exit codes 0, 1
and 2 as "survivors" and called anything higher a crash, an assumption made from the tools that
had been run for real (mutmut, Stryker, PIT). Reading the report next: `_parse_junit`'s
`_CASE` regex expected the survivor's file, line and change in the testcase `name`
(`lib/clamp.dart:5:10 > replaced with >=`) — the shape the hand-built fixture
`mutation_test_junit.xml` assumed, whose README said "verify on first real run". The real report
has `name="Line16_builtin.op.eq_0" classname="lib/debug_alerts.dart"` and puts the mutation in
the `<failure>` element's text (`File: … / Line: … / Original line: … / Mutation: …`, several
lines when the statement spans them). The fallback branch would have printed all 255 survivors as
`lib/main.dart:0  Line128_builtin.op.eq_0` — the score right, the list `generate` works from
useless.

Scope: Dart only for the parser; the exit-code rule was shared by every language, and any other
tool with a non-0/1/2 survivor exit would have hit it the same way.

**Resolved (same day).** `cli._mutation` reads the report first and lets the exit code speak only
when there is no report (the report dir is emptied before each run — #70 — so a report there is
this run's). `_parse_junit` reads the `<failure>` text with `_FAILURE` (dotall, for multi-line
statements), keeps the old `_CASE` branch as a fallback, and prefixes the mutator name from
`name=` (`removeVoidCall1: if (…) {`) because a deleted statement leaves the mutated code
looking unchanged. New fixture `mutation_test_junit_real.xml`, six cases cut from orcweather's
report, with a README saying so. Proven: `test_analyze_reads_the_report_when_the_tool_exits_high`,
`test_analyze_no_report_and_a_high_exit_code_names_the_exit_code` and
`test_mutation_junit_parse_real_shape` (the first and third red before the change); orcweather
re-run: `TCE 61.5% ✗ (min 70)` with 255 survivors as `lib/debug_alerts.dart:16  eq: final lat =
parts.length != 2 ? …`. `dart.md` has its first "Last real run" line.

## #72: /orc-test read infection.json5 with a whole-line-comment-only JSON5 stripper; orcweather's end-of-line // comment made analyze say "produced no mutants" beside a 407-mutant log (RESOLVED 2026-09-20)

Found 2026-09-20, same orcweather run as #70. `PHP ... TCE not measurable — mutation tool produced
no mutants in server — check its configuration`, while Infection's own output above it ended
`407 mutations were generated ... MSI: 80%` and named the log it wrote. `server/infection.json5`
line 3 ends `"excludes": ["Fetch.php"] }, // Fetch is the network edge; ...` — a comment at the
end of a line, which JSON5 allows and Infection reads. `langs/php.py`'s `_JSON5_COMMENT` was
`^\s*//.*$` — whole-line comments only, the case `test_mutation_parse_tolerates_json5_comments`
covered. `json.loads` failed, `_infection_log_path` fell back to `<out>/infection.json` (at the
root then — #70), found nothing, `Mutation(0, 0)`. `mutation_unavailable` had the same parse
failure and, by design, returned None ("degrades") rather than refusing — so the run happened,
and the log it produced was looked for in the wrong place. `php.md:54` documented the degrade for
trailing commas; it did not say a trailing comment was the same case, and nothing said the
degraded path silently produces "no mutants" instead of "could not read your config".

Scope: PHP only; only a project whose `infection.json5` carries JSON5 syntax beyond whole-line
`//` comments. Infection's own run is unaffected; only Orclab's reading of where the log went.

**Resolved (same day).** Two regex passes, each with a group-1 alternative that matches a string
literal and keeps it so `"http://x//y"` and a comma inside a string survive: `_JSON5_COMMENT`
strips `//` to end of line anywhere, then `_JSON5_COMMA` strips a comma before `}`/`]` — two
passes because a comma before a comment before `}` is only trailing once the comment is gone.
Block comments still degrade. Proven: `test_mutation_parse_reads_trailing_comments_and_commas`
(orcweather's line, a comma inside the comment, a `//` inside a string, a trailing comma; red
before); the old fallback test now uses a `/* block */` comment for the case that still cannot be
read. orcweather re-run: `TCE 71.0% ✓` (289/407 — `run.py` counts the 46 mutants the project
told Infection to ignore as alive, where Infection's MSI excludes them and says 80%; not tracked
separately because the OpenAPI-attribute mutants it ignores are the project's own call and the
gate passed either way — worth a look if a project's gate ever turns on that difference).

## #73: /orc-test analyze showed nothing for the minutes the mutation tool ran — its output was captured and printed only on failure, though every tool prints a progress bar and mutation_test an ETA (RESOLVED 2026-09-20)

Found 2026-09-20 during orcweather's first Dart mutation run: direflail asked whether there was
"a means of determining how much of these tests are done (and/or an ETA)". There was — on the
tool's side. `runner.run` used `subprocess.run(..., stdout=PIPE)`, so the terminal showed
`$ dart run mutation_test -f junit -o …` and then nothing for three minutes; the captured output
was printed only when the step failed (`cp.stdout[-3000:]`). mutation_test writes a per-file
line and a `\r`-rewritten bar with an ETA computed from elapsed/progress
(`app_progress_bar.dart:_createText`: `File [###   ] Total [##    ] 34% ~2m 40s`) even when stdout
is not a TTY; Infection prints a `( 50 / 407)` count per fifty mutants but `mutation_cmd` passed
`--no-progress`, a flag chosen for a captured run. A three-minute Dart run is the short case —
Orclab's own Python TCE (#69, 8737 mutants) runs for much longer with the same silence.

Scope: the mutation step of `analyze` only. `run` and `coverage` finish in seconds and stay
captured; `audit` too.

**Resolved (same day).** `runner.run(..., stream=True)`: `Popen`, `os.read` of 4096-byte chunks —
bytes, not lines, because a progress bar is one `\r`-rewritten line for minutes — echoed to
stdout as they arrive and joined into `cp.stdout` unchanged for the parsers. `cli._mutation` is
its only caller; `input` is refused under `stream` (the mutation commands never feed stdin — the
mutmut diff helper does, and stays captured). Infection's `--no-progress` is dropped. Proven:
`tests/test_runner.py::test_run_stream_echoes_output_as_it_arrives_and_still_captures_it`, and
orcweather's PHP re-run showing Infection's `IIII............MM.U   ( 50 / 407)` lines live. In a
non-TTY transcript the `\r` frames arrive as text rather than a moving bar; in a terminal they
render as the tool intends.

## #74: /orc-test analyze streams the mutation tools' progress, but mutmut and Infection count without an ETA — the runner now appends one from the rate it observes (RESOLVED 2026-09-21)

Found 2026-09-20, the same question that produced #73: direflail asked for "how much of the
mutation tests are done (and/or an ETA)". #73 let each tool's own progress through. That is
enough for Dart (`mutation_test` prints `Total [##    ] 34% ~2m 40s`) and Stryker (its bar
carries `remaining: ~1m`), and no help for the two stacks Orclab itself runs most: mutmut prints
`⠋ 312/625  🎉 280 🫥 0  ⏰ 1 …` (its `print_stats`, one `\r`-rewritten line, no time at all —
the per-mutant durations it keeps go to ordering and timeouts, never to a sum), and Infection
prints `IIII......MM.U   ( 50 / 407)` once per fifty mutants. Orclab's own analyze is ~8900
mutmut mutants; the counter says where it is and nothing about when it ends.

Scope: the mutation step of `analyze`, Python and PHP. Languages whose tool prints its own ETA
pass through untouched; a language with no `MUTATION_PROGRESS` gets the tool's line and nothing
more.

**Resolved (2026-09-21).** `runner.run(..., progress=<regex>)`: for each streamed chunk the
last line (after the last `\r` or `\n`) is matched against the language's `MUTATION_PROGRESS`
(`done`/`total` groups — `langs/python.py`, `langs/php.py`), and `_eta()` appends `~2m 40s`
to the terminal — never to `cp.stdout`, which the parsers read. The rate is measured from the
*first* counter reading, not from the run's start, because an incremental mutmut run opens on
the cached count. Known ceiling, marked `ponytail:` in `_eta`: mutmut runs its estimated-fastest
mutants first, so the early figure reads low and climbs. Proven live on a fresh copy of
`hooks/scripts` (625 mutants, `mutants/` wiped): `⠋ 24/625 … ~7s` from the second reading on,
the run ending in mutmut's own `31.45 mutations/second` with the capture unchanged;
`tests/test_runner.py::test_run_stream_appends_eta_when_progress_regex_reads_done_of_total` and
`::test_mutation_progress_regexes_read_each_tool_s_real_line` (Infection's line is #73's, as
seen on orcweather — no Infection here to re-run). Through Claude's Bash tool the line still
arrives when the run ends; in a terminal it is live.

## #75: The platform-ceiling skills are read when a platform is in play, not when the work is scoped — orcweather designed a car app for a surface Apple never allows

Found 2026-09-22, in orcweather. The app grew an Android Auto car surface — a Flutter engine
drawing a map into the host's surface, a Kotlin car module, a conditions card, a spoken summary,
zoom and pan over a channel. When iOS came up (the user's son has an iPhone with CarPlay in his
own car), the answer turned out to be: none of the car work can go there. Weather is not a CarPlay
app category and only navigation apps may draw a map on the car screen. The realistic iOS car
surface is a widget or Live Activity — a different design, not a port.

**The knowledge was already here and dated before the code.** `skills/car-carplay/SKILL.md` has
said *"Weather is not a CarPlay app category"* and *"Navigation apps are the only app category
that have access to this window"* since 2026-09-14, checked against Apple's own PDF. The car work
in orcweather was scoped and built after that. Nothing failed; the skill simply is not read at the
moment it would change a decision. Its own description says Claude reads it "when CarPlay is in
play" — and CarPlay was not in play that day, because the project was thinking about Android. By
the time CarPlay is in play, the shape of the thing has been built for another platform.

The user's conclusion, worth quoting because it names the fix precisely: *"always check what you
can get away with on every platform before you start coding."*

**What would actually change.** The background skills that carry *ceilings* — `car-carplay`
(weather cannot draw a map), `car-android-auto` (which categories and templates exist),
`map-openstreetmap` (attribution must stay visible, no bulk downloading), `source-*` (what a feed
does and does not serve) — are consulted per-platform and reactively. Scoping a feature that will
live on more than one platform should read the ceiling for *every* target platform first, and
record which ones were checked, so "this cannot exist on iOS" is known while the design is still
cheap. Where that belongs is the open question: `/orc-code`'s planning step is the obvious home
(it already asks the security-tier question), and an alternative is a short "platform ceilings"
section that each `car-*`/`stack-*` skill answers uniformly so a scoping pass can read them all
at once. Not decided here.

Cost this time was low only by luck: the Android Auto work is still good for the Android half, and
the iOS phone app needs none of it. A project that had designed its *core* interaction around the
car screen would have lost much more.

## #76: A Mac on the LAN is a third build-machine shape Orclab has no word for — and direflail wants an /orc- command for driving one from Linux (UPDATED 2026-09-22 — the Mac is real, it is borrowed, and teardown is a condition of using it) (UPDATED 2026-09-22 — SSH works; the Mac is on macOS 13.0 and cannot build for the App Store) (UPDATED 2026-09-22 — access torn down the same night; the two Sharing toggles need a human) (UPDATED 2026-09-22 — the owner is upgrading macOS; retry planned 2026-09-23)

Raised by direflail 2026-09-22, in the session that set up Apple Developer enrollment: *"since
i'm on a linux machine, it might be good to be able to virtual desktop / ssh into the mac i have
access to so i don't have to have it right in front of me while you make calls to it"*, then
*"take notes on how hooking a local-network mac works, i think i want to add an /orc- command for
making this easier to develop ios/mac stuff."* This entry is those notes. Nothing was built.

**The gap, stated exactly.** `skills/orc-package/ingredients/app-store/ingredient.md` section 6
offers precisely two leaf shapes, and says so in its own words: **"Local shape — a Mac is this
machine"** and **"Cloud shape — no Mac here; a CI service builds, signs and uploads."** A Mac on
the same LAN is neither. The artifact really is produced on a machine the user controls, so the
cloud shape's whole premise ("no `.ipa` is ever on this machine", no `prepare:`, no `artifact:`,
no `preflight:`) is wrong; but it is not on *this* filesystem, so the local shape's `prepare:`,
`artifact:` and `preflight: [no-vcs, no-tool-state]` are wrong too — every one of them names a
path this machine would have to hold. `skills/stack-ios-native/SKILL.md`'s "Building without a
Mac" has the same blind spot from the other side: it names Codemagic, Xcode Cloud, GitHub Actions
and EAS — four *rented* Macs — and says "a Mac at hand or a cloud Mac" without ever covering a Mac
that is neither in front of you nor rented.

**Searched before concluding nothing covers it** (`CLAUDE.md`, "name what should already have
covered it"): every shipped `SKILL.md`, every `orc-package` ingredient, `hooks/scripts/*.py` and
`skills/*/scripts/**.py`. `grep -rln "ssh |Remote Login|Screen Sharing|remote build"` over the
skills and ingredients matches four files — `security-discipline`, `stack-godot`, `stack-unity`
and `orc-package/ingredients/shared-hosting`. The same grep for `ssh` over every bundled script
matches nothing outside `mutants/`. So no component sets up or drives a remote host today.

**But one of those four is a real precedent, and the command should wrap it rather than invent a
second mechanism.** `shared-hosting` — the ingredient behind `orcshot.org`, and the reason
`~/.ssh/config` already holds an `orcweather-api` alias — has solved this exact shape:
- The connection is an **`~/.ssh/config` alias**, substituted into the recipe as `__SSH__`. Not a
  host, user and key threaded separately; one name the user owns.
- Its liveness check is `ssh -o BatchMode=yes __SSH__ true` exiting 0 — "the key is loaded and
  accepted", with no password prompt possible.
- `rsync` moves the tree; the remote runs its own toolchain; **"`rsync` always runs on this
  machine."**
- **"Orclab never generates or copies a key on the user's behalf."**

That last line is a live convention and was broken in this very session — a `~/.ssh/mac_build`
keypair was generated before the precedent was found. Harmless (nothing trusts it until the user
runs `ssh-copy-id`) and reported to direflail at the time, but it is exactly the kind of thing the
new command must not do, and it is recorded here because the next person will feel the same pull.

**Mechanism notes, verified live on 2026-09-22 rather than remembered:**
- **Discovery works and should be the command's first step.** `avahi-browse -at` on this machine
  returned 32 services on the LAN (a Nest Hub, a Roku, a garage-door opener, two TVs), so mDNS is
  healthy here and `avahi-utils` is already installed. No Apple device appeared — direflail
  confirmed the Mac was powered off, which is the correct negative result, not a broken scan. An
  awake Mac advertises `_device-info._tcp` and usually `_companion-link._tcp`; Remote Login adds
  `_ssh._tcp` and Screen Sharing adds `_rfb._tcp`, so the browse doubles as a check of whether
  the two services are actually enabled. `avahi-resolve` is present, so `<name>.local` resolves
  without anyone learning an IP.
- **Turning it on is one pane.** System Settings → General → Sharing holds both Remote Login
  (SSH) and Screen Sharing (VNC), confirmed against Apple's current mac-help page. Remote Login's
  info panel offers "All users" vs "Only these users", and an "Allow full disk access for remote
  users" toggle that a build does not need. The pane **displays the exact `ssh username@hostname`
  string**, which is the one thing worth reading off the machine by hand.
- **The GUI half needs a client this machine lacks.** Apple's own Screen Sharing app is Mac-only,
  so Linux connects as a plain VNC viewer; `remmina` + `remmina-plugin-vnc` are in Mint 22.3's
  repos (1.4.43) and neither is installed. Whether current macOS still exposes the "VNC viewers
  may control screen with password" option, and where it sits, was **not** verified — check it on
  the machine before writing it into anything.
- **SSH is the half that matters.** `flutter build ipa`, `xcodebuild archive`/`-exportArchive`
  and `altool --upload-app` are all headless. The GUI is wanted only for the first Xcode Cloud
  workflow setup, occasional signing dialogs, and Product → Generate Privacy Report — so a
  command that does SSH well and leaves VNC to a documented one-liner is the right split.

**Why a LAN Mac changes a decision already made in this session, which is what gives this entry
its stakes.** `stack-ios-native` says of Xcode Cloud: *"To get started, configure a workflow in
Xcode — the first setup happens inside Xcode, so it needs a Mac once; with one at hand, even
borrowed, prefer it over Codemagic for this stack."* direflail having a Mac on the LAN satisfies
that "once", which moves the default for orcweather's iOS builds from Codemagic (500 free
minutes, then $0.095/min) to Xcode Cloud (25 compute hours included in the $99 membership) — or
to the LAN Mac directly, at no per-minute cost at all. So this is not only ergonomics; it changes
which build service the App Store ingredient should be instantiated against, and that decision is
currently written down the other way.

**Not decided here, deliberately:** the command's name and whether it is even a new command
rather than a widened `orc-package` ingredient plus a paragraph in `stack-ios-native` — the
latter is the smaller change and `CLAUDE.md` says to prefer widening a trigger over adding a
mechanism beside it. Also undecided: whether the third leaf shape is genuinely a third shape or
just the local shape with `prepare:`/`action:` prefixed by `ssh __SSH__`, which would make the
ingredient change a few lines rather than a new section. Whoever picks this up should answer that
before writing any code, because the two answers differ by an order of magnitude in size.

**Blocked on nothing but hardware.** The Mac was off when this was written; the first real step
is `avahi-browse -at` with it awake, then the Sharing pane, then `ssh-copy-id`. None of it can be
designed further from guesses — the first live connection will correct half of the above.

**Update, same day — the machine is real, and it is not direflail's.** With the Mac powered on,
`avahi-browse -art` found it immediately: **`Sarahs-Laptop.local`, 192.168.40.145**, advertising
`_companion-link._tcp`, AirPlay and AirTunes — and **neither `_ssh._tcp` nor `_rfb._tcp`**, so
Remote Login and Screen Sharing are both still off at their factory default. That negative is
worth keeping: the browse is a working check of whether the two services are enabled, so a
command can tell "Mac asleep", "Mac awake, sharing off" and "ready" apart without touching the
machine, and without a port scan of hardware that belongs to someone else.

**It is a borrowed laptop, and the owner set a condition.** direflail asked and got permission,
*"provided i clean up after myself when all done"*. That turns teardown from good manners into a
requirement of the design, and it lands on three things this entry previously treated as
one-way: the authorized key in Sarah's `~/.ssh/authorized_keys`, the two Sharing toggles, and
whatever toolchain a build needs (Xcode is tens of gigabytes). **Whatever gets built here ships
its teardown in the same change as its setup** — not as a documented afterthought, because the
person who has to run it will be finishing a project and least inclined to go looking. The
`shared-hosting` precedent this entry leans on has no teardown half at all, since a hosting
account is meant to stay; that is the one place the precedent does not carry over, and it is the
half most likely to be skipped by someone copying its shape.

**Two further constraints that follow from "borrowed laptop" rather than "build machine":**
- **It is intermittently present.** It leaves the LAN, sleeps, and changes address. Anything that
  assumes the Mac answers is wrong; `ssh -o BatchMode=yes -o ConnectTimeout=5 __SSH__ true` and a
  plain "not reachable right now, here is what to turn on" are the normal path, not the error
  path.
- **Its footprint should be the narrowest that builds.** Prefer what is already on a stock macOS
  or removable in one command; prefer a build directory under the user's own home that a single
  `rm -rf` clears. Full-disk-access for remote users is not needed and was deliberately left off.

**Where this leaves the immediate work:** blocked on one in-person visit to the Mac — System
Settings → General → Sharing, Remote Login on, "Only these users", and read off the
`ssh username@hostname` line it displays. Nothing else can proceed remotely, because there is no
remote path to enabling remote access. A re-run of the browse confirms it from this side the
moment it is done.

**Update, same day — connected, and the machine cannot do the job.** Remote Login went on and
`_ssh._tcp` appeared in the browse exactly as predicted, so the mDNS readiness check is confirmed
working in all three of its states. `~/.ssh/config` gained a `mac-build` alias in the
`shared-hosting` shape (HostName, User, IdentityFile, `IdentitiesOnly yes`) plus `ConnectTimeout`
and `ServerAlive*`, because a borrowed laptop sleeps. Key auth verified against
`sarahdukes@sarahs-laptop.lan` (192.168.40.145), OpenSSH_9.0.

**The blocker, and it is the whole point of the exercise:** the Mac runs **macOS 13.0** (build
22A380 — the original Ventura, never updated) on an **M1 Pro** with 730 GB free and **no Xcode
installed at all**. Apple's own SDK-and-system-requirements table, read live 2026-09-22: Xcode 26
needs **macOS Tahoe 26.6**, Xcode 16 needs macOS 14.5, Xcode 15 needs macOS 13.5. The App Store
has required Xcode 26 / iOS 26 SDK since 2026-04-28. So this machine is thirteen versions short of
an App Store build, and 0.5 short of even the newest Ventura-era Xcode.

**This reverses a decision made earlier in the same session, which is why it is written down.**
`stack-ios-native` says of Xcode Cloud: *"the first setup happens inside Xcode, so it needs a Mac
once; with one at hand, even borrowed, prefer it over Codemagic for this stack."* A Mac that
cannot run a current Xcode does not satisfy that "once", so Xcode Cloud is unreachable and
**Codemagic returns as the default** for orcweather's iOS builds. The rule in the skill is not
wrong; the rule's premise is "a Mac at hand" and nobody had written down that the premise means
*a Mac that can run the current Xcode*. That is the correction worth carrying: **"has a Mac" is
not the question — "has a Mac on a macOS the required Xcode runs on" is.** Any future `/orc-`
command that probes for a build machine should report the macOS version against the current Xcode
requirement, not merely that a Mac answered.

**A middle option was considered and rejected on honest grounds.** A `13.0 → 13.5` point update is
a small, same-major-version ask that would unlock Xcode 15.2, which might be enough to build and
run on a physical iPhone for testing while store builds went to the cloud. Flutter's own iOS setup
docs say only *"install and set up the latest version of Xcode"* and publish no minimum version
number, so whether current Flutter tolerates Xcode 15.2 is **unverified** — and the only way to
find out is to install ~30 GB of Xcode on a borrowed laptop to see. Imposing on the owner in order
to discover whether the imposition even helps is the wrong trade; recorded so it is not
re-proposed as a fresh idea.

**Cleanup performed already, per the owner's condition.** `ssh-copy-id` without `-i` ignores
`~/.ssh/config` and copies whatever the agent holds — here three keys, including the
`orcweather-api` production host key and the orcshot dev-VM key, none of which belong on a
borrowed laptop. `authorized_keys` was trimmed to the single `orclab-linux-to-mac` key behind a
guard that refuses to write an empty or wrong file (locking yourself out is the one unrecoverable
mistake in this procedure), fresh-connection login was re-verified afterwards, and the backup was
removed. **`ssh-copy-id -i <pubkey> <alias>` is the only correct form here** and any command built
on this should hardcode it. Outstanding on the Mac: Remote Login and Screen Sharing still on, and
the one authorized key.

**One side effect worth knowing:** running `xcodebuild -version` over SSH on a Mac with no
developer tools pops the *"install command line developer tools"* GUI dialog on the owner's
screen. A probe should use `xcode-select -p` (which fails quietly) or `ls /Applications/Xcode.app`
instead.

**Teardown, same night — and the half that cannot be automated.** direflail asked for everything
removed from the owner's machine. `~/.ssh/authorized_keys` was deleted and `~/.ssh` itself
removed with `rmdir` (not `rm -rf`: it refuses a directory holding anything unexpected, which is
the guard worth having when the directory is on someone else's computer). `stat` confirmed the
directory had been **created that evening at 21:34:44** by `ssh-copy-id` itself, so nothing
pre-existing was destroyed — worth checking before deleting, because had the owner already had
keys of her own there, the earlier `grep`-based trim would have taken them out. Revocation was
then *proved* rather than assumed: a fresh connection returns
`Permission denied (publickey,password,keyboard-interactive)`. Nothing was ever installed — the
GUI dialog the `xcodebuild` probe triggered was dismissed without downloading, confirmed by the
absence of both `/Library/Developer/CommandLineTools` and `/Applications/Xcode.app`.

**What an agent cannot take back, and the design consequence.** `sudo -n true` returns *"a
password is required"*, so Remote Login and Screen Sharing **cannot be turned off over SSH** —
the same asymmetry that made turning them on an in-person job. Worse, turning off Remote Login is
the one action that severs the connection performing it. So the teardown any future command ships
has a hard ceiling: it can remove keys, files and build directories, and must then *tell a person*
which GUI toggles remain and where. Any design that promises full automated teardown is promising
something the platform does not allow, and a checklist that silently stops at the toggles leaves
the owner's machine reachable by anyone on that LAN indefinitely.

**Still outstanding at the machine, for the owner or direflail in person:** System Settings →
General → Sharing → Remote Login **off**, Screen Sharing **off**. Nothing else.

**Left on direflail's own machine deliberately**, since it costs the owner nothing and is what a
second attempt would otherwise have to rebuild: the `mac-build` alias in `~/.ssh/config`, the
`~/.ssh/mac_build` keypair, and the `sarahs-laptop.lan` host-key line in `known_hosts`. If this is
never revisited, those three are the local litter to clear.

**Local side cleared too, same night — superseding the paragraph above.** direflail asked for the
three local remnants gone as well, so the `mac-build` stanza was cut from `~/.ssh/config` (the
`orcweather-api` stanza asserted intact before the write), the `~/.ssh/mac_build` keypair deleted,
and the `sarahs-laptop.lan` line dropped from `known_hosts` with `ssh-keygen -R` — plus the
`known_hosts.old` that command leaves behind, which is itself litter worth naming. A `grep -ril`
over `~/.ssh` for the host, the IP and the key name returns nothing. The keypair that should never
have been generated no longer exists.

**One reusable gotcha, worth more than the cleanup itself:** on this machine the SSH agent is
**gnome-keyring** (`SSH_AUTH_SOCK=/run/user/1000/keyring/ssh`), and `ssh-add -d` against it
printed *"Identity removed"* while `ssh-add -l` still listed the same fingerprint
(`SHA256:+Fxg/5dI…`) afterwards. The key only left the agent once the file on disk was deleted.
So **`ssh-add -d` cannot be trusted as a teardown step under gnome-keyring** — it reports success
and does nothing durable. Any teardown that claims to have unloaded a key must verify with
`ssh-add -l` and compare fingerprints rather than trusting the exit code, which is the same
"verify by effect, not by the tool's own say-so" habit `secret-hygiene` already argues for.

**Next step, agreed 2026-09-22 evening:** Sarah is upgrading the Mac, and direflail will try again
on **2026-09-23**. That changes the conclusion two paragraphs up rather than merely deferring it —
**if the upgrade lands on macOS 26.6 or later, Xcode 26 becomes installable and Xcode Cloud comes
back on the table**, reversing tonight's reversal and restoring `stack-ios-native`'s original
advice (25 compute hours/month included in the $99 membership, against Codemagic's 500 free
minutes then $0.095/min). If it lands anywhere below 26.6 — an upgrade to 14 or 15 is still an
upgrade — Xcode 26 will not install and Codemagic stands. **So the first thing to check tomorrow
is `sw_vers -productVersion` against Xcode 26's macOS 26.6 requirement, before any other work**,
and the answer decides the build service. direflail's Codemagic decision is therefore not
outstanding so much as not yet answerable.

**Tomorrow starts from nothing, deliberately.** Both sides were torn down tonight, so the sequence
is: the owner turns Remote Login back on (an OS upgrade may reset it regardless, so it needs
checking rather than assuming), then `ssh-keygen` a fresh key — **by direflail, not by Claude**,
per the rule `secret-hygiene` gained today — then `ssh-copy-id -i <pubkey> <alias>` **with `-i`**,
then the `~/.ssh/config` stanza in the `shared-hosting` shape. Every one of those steps is written
out above with its verification, so the rebuild is minutes, not a re-derivation. The probe order
that avoids the GUI dialog is `xcode-select -p`, then `sw_vers`, then `ls /Applications/Xcode.app`
— never `xcodebuild -version` first.

**And the cleanup clock restarts with it.** The owner's condition was cleanup when done, and tonight
proved the teardown has a ceiling an agent cannot cross (the two Sharing toggles need a person).
A second round adds Xcode itself — tens of gigabytes on someone else's laptop — which is a
materially larger thing to remove than a 101-byte `authorized_keys`. Worth agreeing *before*
installing it who removes it and when.

## #77: Would /orc-test and /orc-code be better run as parallel cloud sessions?

Both commands are serial by nature and slow for the same reason: they wait on
work that does not depend on each other. `/orc-test` runs every suite in a
project across its languages, then coverage, then mutation testing - a
multi-language project runs them one stack at a time, and mutation testing in
particular is long. `/orc-code`'s refactor flow runs a full measurement pass
before it changes anything, and its plan execution is a sequence of tasks many
of which touch different files.

A cloud session is a plausible unit of parallelism for that, and the economics
turn out to favour it in a way worth recording. Anthropic's own documentation
(read 2026-09-24, https://code.claude.com/docs/en/claude-code-on-the-web):
"cloud sessions share rate limits with all other Claude and Claude Code usage
within your account. Running multiple tasks in parallel consumes more rate
limits proportionately. There is no separate compute charge for the cloud VM."
So N parallel sessions cost the same rate limit as N serial ones and finish in
roughly the time of the slowest, with the VM thrown in. Each gets 4 vCPUs,
16 GB RAM and 30 GB of disk of its own, so they do not contend.

What is genuinely unknown, and why this is an entry rather than a change:

- Whether the split is worth the join. Each session is a fresh clone that
  pushes a branch; collecting several branches of test repairs back into one
  coherent change may cost more than the wall-clock saved.
- Whether a stack's toolchain even installs in a cloud container. Measured
  2026-09-24 against the default Trusted network policy: Python, Node, Java,
  Gradle, Rust, PHP, Ruby, Go, Docker, Postgres and Redis are pre-installed;
  Flutter is fetchable; the Android SDK is not, because dl.google.com is not
  on the default allowlist. A parallel run that silently skips the stack it
  could not build would be worse than a slow serial one.
- Whether it should be automatic at all, or a thing the user asks for. Fanning
  out sessions on someone's account without being asked spends their rate
  limit at several times the expected rate.

The pieces to prototype against already exist and were used today: sessions
are created with the claude-code-remote MCP server's create_session, and their
results collected by having each push a branch, since a parent session cannot
read a child's transcript.

## #78: /orc-version treats an empty local tag list as 'never tagged' — in a cloud session that is always true, and it is never right

Found 2026-09-24 while bumping to 0.26.0 from a cloud session. `git tag --list
'v*'` returned nothing, so `/orc-version` Step 0 fell to its third case, "no
current version yet", and its changelog range rule ("from the repository's
first commit to HEAD if no tag exists yet") would have drafted Orclab's entire
history as one entry.

The project is not untagged. `git ls-remote --tags origin` shows fourteen tags,
v0.8.0 through v0.25.1. They are simply not in this checkout: a cloud session's
clone carries `+refs/heads/*:refs/remotes/origin/*` and is shallow, so it
fetches branches and no tags at all. The same is true of any `--depth` or
`--no-tags` clone, a fresh CI checkout, or a second machine - the cloud is just
where it is guaranteed.

Two commands read that empty list as fact:

- `/orc-version` Step 0 case 4 says "the most recent `v*` git tag is always
  authoritative" and exists precisely to catch a `plugin.json` that has drifted
  from the real released version. Where no tags are fetched, that check cannot
  fire and the command silently trusts the manifest - the one input the rule was
  written not to trust. Step 1's proposal and the changelog draft both read the
  same empty range.
- `/orc-git release [tag]` defaults to "newest local tag". In such a checkout
  there is none, so the default cannot resolve.

This is not #9 or #13 recurring, and should not be merged into them. Those were
about tags never being *created*, because plan authors bypassed `/orc-version`;
#13 closed by making the mechanism own the tagging, and it worked - fourteen
tags exist. This is the opposite shape: the tags exist and the reader cannot
see them. Same symptom, different cause, and #13's fix is not at fault.

The bump this was found during came out right despite the gap: the range used
was the commit that last touched `CHANGELOG.md` (`a6e06da`), and `v0.25.1` on
the remote points at exactly that commit. That was reasoning from the changelog
rather than from the tag, and it agreed by construction - but nothing in the
skill tells anyone to do that, so the next person in a fresh checkout gets the
whole-history draft.

Fix direction, not decided: Step 0 could fetch tags before reading them
(`git fetch --tags --quiet`, which is cheap and safe even in a shallow clone),
or read `git ls-remote --tags origin` when the local list is empty and a remote
exists, or distinguish "no tags anywhere" from "no tags here" and say which. The
distinction matters for the message as much as the logic: "this project has
never been tagged" is a very different thing to tell someone than "this checkout
has no tags, the newest on the remote is v0.25.1".
