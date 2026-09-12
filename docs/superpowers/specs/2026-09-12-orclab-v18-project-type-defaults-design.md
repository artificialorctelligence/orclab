# Orclab v18: project-type defaults and stack facets — `/orc-code` proposes a stack from what you tick, and every stack skill answers the same questions

**Status:** design, approved 2026-09-12. Resolves BACKLOG #4. Feeds #2.

## The problem

`/orc-code`'s defaults table is keyed by *language*: "Java / Desktop → Spring + JavaFX", "Dart /
Mobile → Flutter". That is backwards from how a project starts. Nobody arrives saying "I want a
Dart project"; they arrive saying "I want a mobile app" or "a desktop app for Linux and Windows",
and the language is the *answer*, not the question. Keyed by language, the table cannot say what
to propose for "a mobile game" (no row), cannot tell "Android only" from "Android and iOS" (both
are `Kotlin`/`Dart` rows the reader has to already understand), and has no place for the platform
scope that actually decides the choice.

Separately, the five stack skills that exist (`stack-flutter`, `stack-android-native`,
`stack-ios-native`, `stack-unity`, `stack-godot`) were written for one purpose — reach the store
without a refactor — and say nothing about three things every real app has to decide early:
**how it stays present when it is not in front** (a tray icon on the desktop; a status-bar icon
and notifications on a phone), **which UI framework it is built with**, and **where it keeps its
own config and data**. Orcshot's tray work is the live example: "mostly Python" turned into a
GNOME Shell extension in JavaScript and a Cinnamon applet, because the knowledge that the Linux
tray depends on the desktop environment was absent at the moment the decision was made.

BACKLOG #4 has held the list of undecided stacks since 2026-09-05. direflail settled it in a
brainstorming pass on 2026-09-12; this spec records the result.

## What is decided

### 1. Project type is the key; platform scope is a question `/orc-code` asks

`/orc-code`'s new-project flow asks two things before proposing a stack:

1. **Type:** app or game.
2. **Scope:** a checklist — any subset of **Linux, Windows, Mac, Android, iOS, web**.

The pair maps to exactly one row of the table below. Matching is exact: the user ticks boxes; no
row is described in words like "maybe the other later". A project whose scope changes after
scaffolding — an Android app that wants iOS two days in — is handled by `/orc-code`'s
add-a-feature flow, not by this table. The one trace that concern leaves here is *knowledge*: a
stack skill says plainly when its choice is a one-way door (Swift has no Android path; Python has
no real mobile path), so the door is visible when the scope is chosen.

Families, for the rows below: **desktop** = Linux, Windows, Mac; **mobile** = Android, iOS;
**web** = web.

### 2. The table

| Type | Scope ticked | Default | Alternatives |
|---|---|---|---|
| App | one or more desktops, nothing else | Python | Java + Spring + JavaFX; C# / .NET **only when Windows is the sole platform** |
| App | Android only | Kotlin | Java *(stub)* |
| App | iOS only | Swift | Objective-C *(stub)* |
| App | Android + iOS, nothing else | React Native *(pending pass 11)* | Flutter; Kotlin Multiplatform |
| App | web only | *decided by the web research pass* | — |
| App | two or more of desktop / mobile / web, **iOS ticked** | React Native + React web *(pending pass 11)* | Flutter; Kotlin Multiplatform + Compose Multiplatform |
| App | two or more of desktop / mobile / web, iOS not ticked | Flutter | React Native + React web; Kotlin Multiplatform + Compose Multiplatform |
| Game | desktops only | Godot | Unity |
| Game | mobile only | Godot | Unity |
| Game | desktop + mobile | Godot | Unity |
| Game | web (alone or with others) | Godot — *web export is a stub: the skill exists, its web section does not* | — |

**Default** is what `/orc-code` proposes. **Alternatives** are offered when the user asks, or when
the stack skill's own concern line applies (§4). Anything not in the table falls through to
asking directly, as today.

**Stub** means: the row exists, no stack skill exists, and the row says "not researched —
research before first use, per `CLAUDE.md`". No file is written for a stub; where the stack skill
already exists (Godot on web), the row says which section is missing instead. Stubs are things
direflail wants listed and does not expect to use: the two legacy mobile languages (for an
existing codebase, never a new one) and browser games.

**Two alternatives that are rows only, not stubs and not researched now:** Java + Spring + JavaFX
and C# / .NET on the desktop row. direflail: *"likely we'll stick with python as default and never
use these ... but i still want them as alternatives."* They are researched on first want, same
as a stub; they differ from stubs only in that direflail has actually chosen them.

**Decisions behind the rows, so the next reader does not re-derive them:**

- *Python for desktop, one codebase for Linux/Windows/Mac, any platform omittable.* Orcshot was
  designed Linux-first and stays that way; new desktop apps are multi by default. The UI toolkit
  is not decided here — it is the first question the Python-desktop research pass answers, with
  Qt (PySide6), GTK and Tkinter as the candidates and "easiest that works on all three, and what
  breaks if you pick the easy one" as the test. GTK on Windows/Mac is the known concern.
- *C# only on Windows.* direflail: "i don't see us using it on linux or mac ever."
- *pygame dropped* from the game row: a library, not an engine, and a different kind of choice
  from Unity.
- *Games keep one stack across every scope.* Godot and Unity export to every platform ticked;
  what changes by scope is knowledge (§3, scope divergence), not the engine.
- *Kotlin Multiplatform is the "native UI on both, shared logic" option.* It is the one multi
  choice that *reuses* the Kotlin and Swift rows for the UI halves rather than replacing them,
  and the migration path from an Android-only Kotlin app to both platforms. Its pass has one
  extra question: does structuring a Kotlin app KMP-shaped from day one cost anything? If not,
  the Android-only row should say to start that way.
- *React Native is the default wherever iOS is ticked and the stack is not native Swift.* It
  started as a stub; it stopped being one when web was ticked in, and it became the default when
  direflail named the constraint that decides it: the leading candidate for building and signing
  iOS apps from Linux is EAS Build, Expo's service, and direflail's understanding is that it
  requires a React Native project. If that is where iOS builds happen, the stack choice is made
  for us. The "pending pass 11" marker on those rows is literal: pass 11 verifies live whether
  EAS in fact requires React Native, and whether Codemagic or GitHub's macOS runners build a
  Flutter app well enough to remove the constraint. If the constraint holds, the rows stay as
  written; if it does not, they revert to Flutter and React Native becomes the alternative. Rows
  with no iOS in them are untouched either way — Flutter stays their default. The cross-family
  contest is otherwise as before: Flutter (one codebase, canvas-rendered web) against React
  Native + React web (one ecosystem, two codebases, native-ish mobile).
- *Web is its own row and its own pass.* #4's toolset (HTML5/CSS/JS/React/Python) names the
  candidates: React in front; Python or Node behind. Nothing is the default until the pass says.
  A web app that only *talks to* a mobile app is two projects — a "shared server" is an
  ordinary client/server split and needs no row.
- *Linux flavors are not a row.* The stack is the same Python on Ubuntu, Mint and Fedora. What
  differs by distro is packaging (already `orc-package`'s job) and the tray (§3, presence). Both
  live as sections inside the Python-desktop skill, not as scaffold choices.

### 3. The facets every stack skill carries

The existing stack-skill shape — toolchain, project layout, how each platform's artifact is
produced, and the table mapping each store rule to a file and a check — stays. Three sections are
added to every stack skill, and a fourth to game skills:

- **Presence** — how the app stays visible and reachable when it is not in front. Desktop: the
  tray icon, per OS and — on Linux — per desktop environment. Mobile: the status-bar icon and
  notification-tray notifications, including what limited interaction they allow. direflail's
  ambition is modest ("i'm not looking to get really crazy with these"); the section states what
  is available and the easiest way to use it, not a design. Games: one line, "not researched,
  unlikely to be needed".

  *Linux subtree.* The presence section for Linux splits into **Ubuntu, Mint, Fedora**. Within
  each, it splits further by version, X11/Wayland, and packaging **only where the research finds
  those actually diverge** — not pre-emptively. macOS and Windows get the same question asked
  ("what splits by version or display layer here?") and split only if the answer is yes. The
  research covers GNOME, Cinnamon and KDE, and Fedora's defaults — not only what Orcshot met.

- **UI** — which UI frameworks bind to this stack and which its language excludes (UIKit and
  SwiftUI are Swift's; Compose and Views are Kotlin's; GTK, Qt and Tkinter are Python's), the
  easiest default, and for multi stacks whether one UI serves every platform ticked. This section
  is what BACKLOG #2 will translate a base design system *into*; #2 stays open and gets a note.

- **Storage** — the internal default for config and saved data on this stack and platform:
  the database (SQLite nearly everywhere, but the pass confirms) and each platform's convention
  for where config lives. External databases are parked (§6).

- **Scope divergence** *(game skills only)* — what the engine's own conventions keep shared
  versus per-platform (Godot's export presets, feature tags and input map; Unity's equivalents),
  and what has to be *designed* differently per scope: input model (touch vs keyboard/mouse/
  gamepad), UI scaling and aspect ratios, performance budgets, and where per-platform desktop
  differences (Linux/Windows/Mac) bite versus where the export preset absorbs them. #33 named
  this as "the differences direflail expects but cannot yet name"; the pass finds the list.

**Shared tree vs. platform-specific is the framework's convention, always.** Flutter's `lib/`
with `android/`, `ios/`, `linux/` … beside it; KMP's `commonMain` / `androidMain` / `iosMain`;
Godot's export presets. The "where things live" section each skill already has answers this for
multi stacks. Orclab keeps no config of its own on the side; if a pass finds a gap the framework
does not cover, that is a BACKLOG entry, not a design decision made here in advance.

### 4. The selection rule

Written once, followed by every pass: **present the easiest option that works as the default,
and name an alternative only where the default has a serious concern — stated in the skill, next
to the default.** The concern line is what tells a reader when to reach past the default. A skill
that lists alternatives without saying what would make you choose them has not done the work.

### 5. Research passes

Every pass runs under `currency-discipline` and `CLAUDE.md`'s "Before the first project builds on
a stack or ships to a channel Orclab has never met": live sources, a "confirmed live YYYY-MM-DD"
stamp on every claim, and a marker on anything no project has built with yet. The spec holds the
questions each pass must answer; it holds none of the answers.

| # | Pass | Produces |
|---|---|---|
| 1 | Python desktop | `skills/stack-python-desktop/SKILL.md` — toolkit decision (Qt/GTK/Tkinter, §2), layout, per-OS artifacts, all facets; the Linux flavor subtree; the one-way-door line |
| 2 | Kotlin Multiplatform | `skills/stack-kotlin-multiplatform/SKILL.md` — logic sharing with SwiftUI/Compose fronts; Compose Multiplatform's desktop and iOS state; the "KMP-shaped from day one" question |
| 3 | React Native | `skills/stack-react-native/SKILL.md` — mobile; with React web for the cross-family case; the iOS-ticked default's first real content |
| 4 | Web | `skills/stack-web/SKILL.md` — the web-only row's default and its concern lines; front and back candidates from #4 |
| 5 | Cross-family | The two cross-family rows' concern lines, from pitting passes 1–4's findings against Flutter's per-platform reality — Flutter on Linux desktop and on web, and React Native's desktop story, are the claims that most need checking live. Lands as sections in `stack-flutter`, `stack-react-native`, and whichever alternative earns a concern line |
| 6–10 | Facets on the five existing skills | Presence, UI, Storage added to `stack-flutter`, `stack-android-native`, `stack-ios-native`; those three plus Scope divergence added to `stack-godot`, `stack-unity` |
| 11 | iOS build/sign from Linux | A named cloud option in `stack-ios-native`, `stack-flutter` and `stack-react-native` (Codemagic, GitHub Actions macOS runners, EAS) — today the first two say "a Mac at hand or a cloud Mac" and name nothing. **This pass settles the "pending pass 11" rows in §2**: does EAS require React Native, and can the others build Flutter for iOS well enough? |

Sequence: 1 and 6–10 first (they touch what exists and what is most likely to be used next),
then 11 (it decides two rows of the table, so it runs before the passes that write them), then
2, 3, 4, then 5 (it depends on 2–4). Each pass is
one plan task; a pass that finds a real gap it is not filling writes a BACKLOG entry, not a
placeholder section.

### 6. Parked, on purpose

- **Docker** and **observability** (Grafana/Prometheus/Loki) — "probably going to remain open".
  No row, no facet.
- **External databases** — an app that connects to a server is that server's concern; parked
  until one exists.
- **Signing up for the Apple Developer Program and Google Play Console** — the *how* is already
  each store ingredient's "§2 Registration". *Doing* it is a real account action belonging in a
  session centred on the first app, per `CLAUDE.md`'s dogfooding rule. Not an Orclab entry.
- **Android SDK / Studio / emulator setup** — already in `stack-android-native` with versions.

### 7. What does not change

`/orc-code`'s add-a-feature and refactor flows; `/orc-package`, `/orc-publish`, `/orc-test`;
the five existing stack skills' existing sections; the ingredients. `/orc-help`'s listing is
unaffected — stack skills are not `orc-*` components. No code changes: `/orc-code` is prose, and
the table and scope question are edits to `skills/orc-code/SKILL.md`.

## BACKLOG

- **#4** — resolved by this spec: every line it names is a row, a stub, or parked in §6.
- **#2** — note: §3's UI facet produces the list of frameworks a base design system translates
  into. Stays open.
- **#33** — already resolved; its "differences direflail cannot yet name" line is §3's scope
  divergence facet.

## Verification

Prose only — the test is the reader's. After the table lands in `orc-code`, four scaffold
requests are walked by hand and each must land on exactly one row with no judgment call:
"a mobile game", "an Android app", "a mobile and web app with no desktop", "a Linux and Windows
desktop app". After each research pass, its skill is read once as the person who will build
with it, per `CLAUDE.md`'s "explain it again from the reader's side"; a facet section that names
tools before the reader could say what the facet *is* gets rewritten.
