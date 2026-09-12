# Orclab v18: project-type defaults and stack facets — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/orc-code` proposes a stack from a project type and a ticked platform scope, and every stack skill answers the same questions — presence, UI, storage, and (for games) what diverges by scope — from live-verified research.

**Architecture:** All prose, no code. One task rewrites `/orc-code`'s new-project questions and defaults table to the spec's shape. Each remaining task is one research pass under `currency-discipline`: it reads live sources, writes or extends one `skills/stack-*/SKILL.md`, stamps every claim, and updates its row in `/orc-code`'s table. Spec: `docs/superpowers/specs/2026-09-12-orclab-v18-project-type-defaults-design.md` — read it in full before any task.

**Tech Stack:** Markdown skills; `WebFetch`/`WebSearch` for live sources; `python3` + PyYAML for the frontmatter check.

## Global Constraints

Every task's requirements include these. They are copied from the spec and from `CLAUDE.md`.

- **Research-before-first-use** (`CLAUDE.md`, "Before the first project builds on a stack or ships to a channel Orclab has never met"): every claim in a stack skill is checked against a live source in the task, not written from memory. A claim the task could not verify live is not written.
- **Stamps** (spec §5): every factual claim carries the date it was confirmed, in the form the existing skills use — a section heading `## Toolchain, as of YYYY-MM-DD`, an inline `(confirmed live YYYY-MM-DD)`, and a closing `## Sources (live on YYYY-MM-DD)` section listing every URL read. Use the real date the task runs, not 2026-09-12.
- **Unbuilt marker** (spec §5): a skill or section no project has yet built with carries, in its first paragraph, the sentence *"No project has been built with this yet; the first one corrects it."*
- **Selection rule** (spec §4): the easiest option that works is the default; an alternative is named only with the concern that would make you choose it, on the line next to the default. An alternative with no stated concern is a plan failure.
- **Framework conventions, never Orclab's own** (spec §3): shared-vs-platform layout is the framework's convention. If a pass finds something the framework does not cover, it writes a `BACKLOG.md` entry via `/orc-todo add backlog` and does not design a side-config.
- **Facet section shape** (spec §3). Each facet is a `## ` section with exactly this heading and this minimum content:
  - `## Presence` — one paragraph defining the facet for this stack in plain words (desktop: tray icon; mobile: status-bar icon and notification-tray notifications and what interaction they allow; games: the single line *"Not researched; unlikely to be needed."*), then per platform ticked-for-this-stack: the easiest mechanism, the API or package, the concern line if any, and the stamp.
  - `## UI` — which UI frameworks bind to this stack and which its language excludes, the easiest default with its concern line, and for multi stacks whether one UI serves every platform. Ends with the sentence *"BACKLOG #2's design system translates into the frameworks above."*
  - `## Storage` — the internal default for saved data (the database) and for config (the platform's convention for where it lives), per platform, with stamps. One sentence saying external databases are out of scope.
  - `## Scope divergence` (game skills only) — what the engine's own conventions keep shared versus per-platform, then what must be designed differently per scope: input model, UI scaling and aspect ratio, performance budget, per-platform desktop differences. Replaces `stack-godot`'s and `stack-unity`'s existing "What games change — named, not answered" section, keeping that section's content that still holds.
- **Linux presence subtree** (spec §3): the Linux part of a desktop `## Presence` section has `### Ubuntu`, `### Mint`, `### Fedora` subsections. Each splits further by version, X11/Wayland or packaging **only where the research found a real divergence**, and says in one line when it did not. Windows and macOS get one line each answering "does anything here split by version or display layer?" and split only on yes.
- **Frontmatter** of every new stack skill, exactly:
  ```yaml
  ---
  name: stack-<name>
  description: Background knowledge for any work in a <stack> project - <what it covers, in one sentence>. Says what the current toolchain is, where things live in the project, and where each store rule lands in the build. Not a command; Claude reads it when <stack> is in play.
  user-invocable: false
  ---
  ```
  The description names the stack's real words (the language, the framework) so ambient matching has a literal cue — see `CLAUDE.md`, "The determinism spectrum".
- **Frontmatter check**, run before every commit that touches a stack skill (`claude plugin validate` does not read frontmatter — `CLAUDE.md`):
  ```bash
  python3 - <<'EOF'
  import re, sys, yaml, pathlib
  bad = []
  for p in pathlib.Path("skills").glob("stack-*/SKILL.md"):
      fm = yaml.safe_load(re.match(r"---\n(.*?)\n---", p.read_text(), re.S).group(1))
      if fm.get("name") != p.parent.name or fm.get("user-invocable") is not False or not fm.get("description"):
          bad.append((str(p), fm))
  print("frontmatter ok" if not bad else bad); sys.exit(1 if bad else 0)
  EOF
  ```
  Expected: `frontmatter ok`.
- **Reader-side pass** (`CLAUDE.md`, "Before explaining anything, explain it again from the reader's side"): before committing a skill, read each new section once as the person who will build with it and has not read the sources. A section that names a tool before the reader could say what the facet *is* gets its first paragraph rewritten.
- **Testing row**: a stack skill's build/test section links to `skills/orc-test/languages/<lang>.md` for coverage and mutation tooling instead of restating it (BACKLOG #4's last paragraph). The files that exist: `csharp dart gdscript java javascript kotlin python swift`.
- **Commits**: one per task, message body says what was researched and which sources decided it, ending `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`. Never `git push`; never edit `BACKLOG.md` except through `/orc-todo add` or the resolution steps in Task 13.
- **Model floor**: nothing under Sonnet 5 runs a task (Orclab's `model_floor` hook enforces it).

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `skills/orc-code/SKILL.md` | New-Project Flow questions 1–3; the Defaults Table (the only place the type × scope → stack mapping lives) | 1, then a row edit in every research task |
| `skills/stack-python-desktop/SKILL.md` | New. Python desktop: toolkit decision, layout, per-OS artifacts, all facets, Linux subtree, one-way-door line | 2 |
| `skills/stack-flutter/SKILL.md` | Existing. Gains Presence, UI, Storage; cross-family concern lines; a named iOS cloud build option | 3, 8, 12 |
| `skills/stack-android-native/SKILL.md` | Existing. Gains Presence, UI, Storage; the KMP-shaped-from-day-one answer | 4, 9 |
| `skills/stack-ios-native/SKILL.md` | Existing. Gains Presence, UI, Storage; the one-way-door line; a named iOS cloud build option | 5, 8 |
| `skills/stack-godot/SKILL.md` | Existing. Gains Presence (one line), UI, Storage, Scope divergence; web export stub line | 6 |
| `skills/stack-unity/SKILL.md` | Existing. Gains Presence (one line), UI, Storage, Scope divergence | 7 |
| `skills/stack-kotlin-multiplatform/SKILL.md` | New | 9 |
| `skills/stack-react-native/SKILL.md` | New; includes React web for the cross-family case | 10 |
| `skills/stack-web/SKILL.md` | New; the web-only row's default | 11 |
| `BACKLOG.md` | #4 resolved, #2 noted, any gaps found | 13 (and `/orc-todo add` from any task) |

---

### Task 1: `/orc-code` asks type and scope, and the table is keyed by them

**Files:**
- Modify: `skills/orc-code/SKILL.md:27-44` (New-Project Flow questions 1–3)
- Modify: `skills/orc-code/SKILL.md:109-124` (Defaults Table and the paragraph under it)

**Interfaces:**
- Produces: the table rows every later task edits. Row shape: `| Type | Scope ticked | Default | Alternatives | Knowledge |`. Later tasks fill a row's **Knowledge** cell with `` `skills/stack-<name>/SKILL.md` — read it in full before scaffolding `` once that skill exists.

- [ ] **Step 1: Read the spec §1–2 and the current flow**

Read `docs/superpowers/specs/2026-09-12-orclab-v18-project-type-defaults-design.md` sections 1 and 2, and `skills/orc-code/SKILL.md` lines 27–56 and 109–124.

- [ ] **Step 2: Replace questions 1–3 of the New-Project Flow**

Replace the three numbered items at lines 32–40 with:

```markdown
1. **Project name**: "What would you like to name the project?"
2. **Type**: "Is this an app or a game?" (CLI tools and libraries are apps for this purpose;
   if the answer is something else entirely, there is no default — say so and ask what stack
   they want.)
3. **Scope**: "Which platforms? Tick any of: Linux, Windows, Mac, Android, iOS, web." Any subset
   is valid. Once you have type + scope, find the one row of the Defaults Table below whose
   *Scope ticked* column matches — the rows are exact, and every subset lands on exactly one:
   - If the row has a Default, propose it: "For a [type] on [platforms], I'd default to
     [stack] — sound good, or would you like something different?" Name the row's alternatives
     only if asked, or if the stack skill's own concern line applies to what the user has said.
   - If the row's Default is a stub, or no row matches, don't propose one — say there is no
     researched default yet and ask what stack they want. Before scaffolding with a stack that
     has no skill, `CLAUDE.md`'s "Before the first project builds on a stack ... Orclab has
     never met" applies: the research comes first.
   - If the user changes scope after scaffolding ("we should add iOS"), that is the
     Add-to-Existing Flow, not this table.
```

- [ ] **Step 3: Replace the Defaults Table and its paragraph**

Replace lines 109–124 (`## Defaults Table` through `...generic step 5.`) with:

```markdown
## Defaults Table

Keyed by what the user ticked, not by language — the language is the answer. Families: desktop
= Linux, Windows, Mac; mobile = Android, iOS. *(pending pass 11)* marks a default that
Task 8 of the v18 plan settles: it holds only if EAS Build in fact requires React Native.

| Type | Scope ticked | Default | Alternatives | Knowledge |
|---|---|---|---|---|
| App | one or more desktops, nothing else | Python | Java + Spring + JavaFX; C# / .NET only when Windows is the sole platform | *no skill yet — research first* |
| App | Android only | Kotlin + Jetpack Compose | Java *(stub — existing codebases only)* | `skills/stack-android-native/SKILL.md` — read it in full before scaffolding |
| App | iOS only | Swift + SwiftUI | Objective-C *(stub — existing codebases only)* | `skills/stack-ios-native/SKILL.md` — same; needs a Mac or a cloud Mac to build |
| App | Android + iOS, nothing else | React Native *(pending pass 11)* | Flutter; Kotlin Multiplatform | *no skill yet — research first*; Flutter: `skills/stack-flutter/SKILL.md` |
| App | web only | *decided by research — none yet* | — | *no skill yet — research first* |
| App | two or more of desktop / mobile / web, iOS ticked | React Native + React web *(pending pass 11)* | Flutter; Kotlin Multiplatform + Compose Multiplatform | *no skill yet — research first* |
| App | two or more of desktop / mobile / web, iOS not ticked | Flutter | React Native + React web; Kotlin Multiplatform + Compose Multiplatform | `skills/stack-flutter/SKILL.md` — same |
| Game | desktops only | Godot 4 | Unity 6 | `skills/stack-godot/SKILL.md`, `skills/stack-unity/SKILL.md` — read the chosen one in full; neither is preferred over the other, ask which |
| Game | mobile only | Godot 4 | Unity 6 | same |
| Game | desktop + mobile | Godot 4 | Unity 6 | same |
| Game | web, alone or with others | Godot 4 *(stub — web export not researched)* | — | `skills/stack-godot/SKILL.md` has no web section yet |

Do not invent additional defaults beyond what's listed here — if a scope isn't in this table,
ask directly in the New-Project Flow's step 3 instead of guessing. A row's **Knowledge** column
names the background skill that holds the stack's current toolchain, project layout, store
rules, and the facets every stack skill answers — presence, UI, storage (v18 spec §3). When a
row has one, its scaffold step follows that file rather than this one's generic step 5. A row
marked *stub* or *no skill yet* is not a default to propose; it is a name to research.
```

- [ ] **Step 4: Walk the spec's four scaffold requests by hand**

For each, state which row it lands on. Every one must land on exactly one row with no judgment call, or the table is wrong:

| Request | Expected row |
|---|---|
| "a mobile game" | Game / mobile only |
| "an Android app" | App / Android only |
| "a mobile and web app with no desktop" | App / two or more families, iOS ticked (Android + iOS + web) — or *iOS not ticked* if they tick only Android + web |
| "a Linux and Windows desktop app" | App / one or more desktops |

Record the four results in the commit message. If any request is ambiguous, fix the *Scope ticked* wording until it is not.

- [ ] **Step 5: Check the rest of the file still reads**

Run: `grep -n "language + type\|Language\*\*: \"What language" skills/orc-code/SKILL.md`
Expected: no output — nothing left refers to the old language-first question.

- [ ] **Step 6: Commit**

```bash
git add skills/orc-code/SKILL.md
git commit -m "orc-code: ask type and scope, key the Defaults Table by them (v18 spec §1–2)

Walked: 'a mobile game' → Game/mobile only; 'an Android app' → App/Android only;
'a mobile and web app with no desktop' → App/two or more families (iOS ticked or not,
by what they tick); 'a Linux and Windows desktop app' → App/desktops.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: `stack-python-desktop` — research pass 1

**Files:**
- Create: `skills/stack-python-desktop/SKILL.md`
- Modify: `skills/orc-code/SKILL.md` (the App / desktops row's Knowledge cell)

**Interfaces:**
- Produces: the toolkit decision (one of PySide6 / GTK 4 via PyGObject / Tkinter) that Task 12 compares against Flutter's and React Native's desktop stories.

- [ ] **Step 1: Read the spec §2 "Python for desktop" and §3, and one existing skill as the model**

Read `skills/stack-flutter/SKILL.md` in full for the section shape: `When this is the stack`, `Toolchain, as of <date>`, `Project layout — where things live`, `Build, run, test`, `Where each store rule lands`, `Choosing dependencies`, `Sources`.

- [ ] **Step 2: Answer the toolkit question from live sources**

Questions, each answered with a URL and the date:
1. Current stable versions: Python (python.org/downloads), PySide6 (pypi.org/project/PySide6), PyGObject + GTK 4 (pygobject.gnome.org), Tkinter (ships with Python — confirm Tk version in the Python docs).
2. For each toolkit: does it run on Linux, Windows and macOS from one codebase, and what does the toolkit's own documentation say about each platform (PySide6: doc.qt.io/qtforpython; PyGObject: the Windows/macOS install pages on pygobject.gnome.org; Tkinter: docs.python.org/3/library/tkinter.html)?
3. Packaging into a per-OS artifact: what each toolkit's docs recommend (PyInstaller, Briefcase, flatpak/snap for Linux — check pyinstaller.org and briefcase.readthedocs.io for current versions and supported toolkits).
4. Licence: PySide6 is LGPL — confirm on the Qt for Python page; GTK is LGPL; Tk is BSD-style. State what each requires of a closed-source app in one line.

Apply the selection rule: the easiest toolkit that genuinely works on all three is the default; each other toolkit gets one concern line saying when to choose it instead. The known concern to confirm or refute live: GTK's look and packaging on Windows/macOS.

- [ ] **Step 3: Answer the Presence facet, with the Linux subtree**

Questions:
1. Linux tray icons: the StatusNotifierItem / AppIndicator protocol and which desktop environments show one natively — GNOME (needs an extension; name the current one on extensions.gnome.org and its GNOME Shell version support), Cinnamon (native XApp status icon — Orcshot's own choice, cite `~/projects/orcshot` only as the example, verify against Linux Mint docs), KDE Plasma (native). Fedora's default is GNOME on Wayland: does that change anything beyond the GNOME answer?
2. For each of Ubuntu, Mint, Fedora: current releases (ubuntu.com/about/release-cycle, linuxmint.com/download_all.php, fedoraproject.org/wiki/Releases), default desktop, X11 or Wayland by default, and whether any of that changes the tray answer. Split the subsection only where it does.
3. The Python package that does the tray for the chosen toolkit (PySide6: `QSystemTrayIcon` in the Qt docs; GTK: no native tray in GTK 4 — confirm and say what people use; Tkinter: none — confirm).
4. Windows: `QSystemTrayIcon` covers it, or name the alternative; does anything split by Windows version? macOS: menu-bar extras via the same or via `rumps`/`pyobjc`; does anything split by macOS version?

- [ ] **Step 4: Answer the UI and Storage facets**

UI: which frameworks bind to Python for desktop (the three toolkits, plus any the toolkit docs name as alternatives — Kivy, Dear PyGui — one line each on why they are not the default). Storage: `sqlite3` from the standard library (confirm the version bundled with current Python), and the per-OS config directory convention — XDG on Linux, `%APPDATA%` on Windows, `~/Library/Application Support` on macOS — with the package the ecosystem uses to resolve them (`platformdirs` on PyPI: confirm current version).

- [ ] **Step 5: Write the skill**

Create `skills/stack-python-desktop/SKILL.md` with the Global Constraints frontmatter (`name: stack-python-desktop`), then:

```markdown
# Python — the desktop stack (Linux, Windows, macOS from one codebase)

No project has been built with this yet; the first one corrects it.

## When this is the stack
<the App / desktops row; any subset of the three OSes; the one-way-door line: "Python has no
real path to Android or iOS — if mobile is plausible later, start from the multi rows instead">

## Toolchain, as of <date>
<table: component, version, source URL — Python, the chosen toolkit, packager>

## The toolkit decision
<default and its reason; each alternative with its concern line; licence line each>

## Project layout — where things live
<pyproject.toml, src/ layout, where per-OS packaging config lives — the packager's convention>

## Build, run, test
<venv, run, per-OS artifact command; link to skills/orc-test/languages/python.md>

## Presence
<per Global Constraints; ### Ubuntu / ### Mint / ### Fedora under Linux; Windows; macOS>

## UI
<per Global Constraints>

## Storage
<per Global Constraints>

## Where each store rule lands
<Linux channels: point at skills/orc-package/ingredients/{ppa,snap,flatpak}; Windows and macOS:
one line each saying no ingredient exists and which store would need one>

## Sources (live on <date>)
```

- [ ] **Step 6: Frontmatter check and reader-side pass**

Run the Global Constraints frontmatter check. Expected: `frontmatter ok`. Then read `## The toolkit decision` and `## Presence` as someone who has never packaged a Python app; rewrite any first paragraph that leads with a product name.

- [ ] **Step 7: Point the table row at the skill**

In `skills/orc-code/SKILL.md`, the App / "one or more desktops" row: replace `*no skill yet — research first*` with `` `skills/stack-python-desktop/SKILL.md` — read it in full before scaffolding ``.

- [ ] **Step 8: Commit**

```bash
git add skills/stack-python-desktop/SKILL.md skills/orc-code/SKILL.md
git commit -m "stack-python-desktop: Python desktop stack from live research (v18 pass 1)

<toolkit chosen and why; the Linux tray answer per DE; which sources decided each>

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Facets on `stack-flutter` — research pass 6

**Files:**
- Modify: `skills/stack-flutter/SKILL.md` (insert `## Presence`, `## UI`, `## Storage` after `## Build, run, test`, before `## Where each store rule lands`; extend `## Sources`)

**Interfaces:**
- Produces: Flutter's per-platform presence and storage answers that Task 12 compares.

- [ ] **Step 1: Read the existing skill in full and spec §3**

- [ ] **Step 2: Answer Presence from live sources**

1. Android: the notification and status-bar icon path from Flutter — `flutter_local_notifications` on pub.dev (current version, and whether it supports Android 16 / API 36 notification changes), and what Android itself allows a notification to do (actions, replies — developer.android.com/develop/ui/views/notifications).
2. iOS: the same package's iOS support; what iOS allows (banner, actions, no persistent status-bar icon — confirm on developer.apple.com/documentation/usernotifications).
3. Desktop (Linux, Windows, macOS): tray support in Flutter — `tray_manager` or `system_tray` on pub.dev; current versions, which platforms each supports, and whether Linux support depends on the desktop environment.

- [ ] **Step 3: Answer UI and Storage from live sources**

UI: Flutter's own widgets are the UI on every platform; Material 3 vs Cupertino — what docs.flutter.dev recommends for a single UI across both; one line on whether platform-adaptive widgets are the default. Storage: `sqflite` and `drift` on pub.dev (versions; which supports desktop); `shared_preferences` for config and where each platform stores it (the package's README says).

- [ ] **Step 4: Write the three sections, per the Global Constraints shape**

Insert after `## Build, run, test`. Add every URL read to `## Sources`.

- [ ] **Step 5: Frontmatter check, reader-side pass, commit**

```bash
git add skills/stack-flutter/SKILL.md
git commit -m "stack-flutter: presence, UI and storage facets from live research (v18 pass 6)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Facets on `stack-android-native` — research pass 7

**Files:**
- Modify: `skills/stack-android-native/SKILL.md` (insert `## Presence`, `## UI`, `## Storage` after its build/test section; extend `## Sources`)

- [ ] **Step 1: Read the existing skill in full and spec §3**

- [ ] **Step 2: Answer Presence from live sources**

1. Status-bar icon: a notification's small icon is the status-bar icon — confirm on developer.android.com/develop/ui/views/notifications, and what Android 16 requires (notification permission since 13; foreground-service types since 14 — cite the current page).
2. What a notification can do: actions, direct reply, progress, ongoing (foreground service) — one line each with the API.
3. Compose-side: is there anything Compose-specific, or is this plain Android? Say which.

- [ ] **Step 3: Answer UI and Storage from live sources**

UI: Jetpack Compose is the default (already the row); Views/XML is the alternative with its concern line (existing codebases; a specific widget with no Compose equivalent). Confirm Compose's current BOM version on developer.android.com/jetpack/compose/bom. Storage: Room over SQLite (current version, developer.android.com/training/data-storage/room) and DataStore for config (developer.android.com/topic/libraries/architecture/datastore) — say plainly that SharedPreferences is the legacy path.

- [ ] **Step 4: Write the three sections, frontmatter check, reader-side pass, commit**

```bash
git add skills/stack-android-native/SKILL.md
git commit -m "stack-android-native: presence, UI and storage facets from live research (v18 pass 7)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Facets on `stack-ios-native` — research pass 8

**Files:**
- Modify: `skills/stack-ios-native/SKILL.md` (insert `## Presence`, `## UI`, `## Storage`; add the one-way-door line to `## When this is the stack`; extend `## Sources`)

- [ ] **Step 1: Read the existing skill in full and spec §1 (the one-way door) and §3**

- [ ] **Step 2: Answer Presence from live sources**

1. iOS has no app-owned persistent status-bar icon — confirm on developer.apple.com (Human Interface Guidelines, status bar) and say so first.
2. Notifications: `UserNotifications` — banners, actions via categories, what a user can do from the notification without opening the app (developer.apple.com/documentation/usernotifications).
3. Live Activities / Dynamic Island as the nearest "persistent presence" — what they can show and on which devices (developer.apple.com/documentation/activitykit). One paragraph; direflail's ambition is modest.

- [ ] **Step 3: Answer UI and Storage from live sources**

UI: SwiftUI default; UIKit alternative with its concern line (a control SwiftUI lacks; an existing UIKit codebase); confirm both are current on developer.apple.com and note UIKit-in-SwiftUI interop in one line. Storage: SwiftData (developer.apple.com/documentation/swiftdata) as the default, Core Data as the alternative with its concern line, `UserDefaults` for config; where each lives on device.

- [ ] **Step 4: Add the one-way-door line**

In `## When this is the stack`, append: *"Swift has no Android path. If Android is plausible later, start from the Android + iOS row instead — moving to it later is a rewrite, not a port."*

- [ ] **Step 5: Write the sections, frontmatter check, reader-side pass, commit**

```bash
git add skills/stack-ios-native/SKILL.md
git commit -m "stack-ios-native: presence, UI and storage facets, and the one-way-door line (v18 pass 8)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Facets and scope divergence on `stack-godot` — research pass 9

**Files:**
- Modify: `skills/stack-godot/SKILL.md` (insert `## Presence`, `## UI`, `## Storage` after `## Build`; replace `## What games change — named, not answered` at lines 84–92 with `## Scope divergence`; add the web-export stub line to `## When this is the stack`; extend `## Sources`)

- [ ] **Step 1: Read the existing skill in full and spec §3 (scope divergence)**

- [ ] **Step 2: Answer Scope divergence from Godot's own docs**

1. What the engine keeps per-platform for you: export presets (docs.godotengine.org — "Exporting projects"), feature tags (`OS.has_feature`, "Feature tags" page), the InputMap (already in the existing section — keep it).
2. Input: touch vs keyboard/mouse/gamepad — the InputMap pattern, `TouchScreenButton`, and what the docs say about designing actions once (keep the existing paragraph; add the URL).
3. UI scaling and aspect ratio: the "Multiple resolutions" page — stretch modes and aspect settings; which the docs recommend for mobile vs desktop.
4. Performance: the mobile renderer vs Forward+ ("Renderers" page) — when the docs say to pick which.
5. Per-platform desktop differences: what the Linux/Windows/macOS export pages say differs (code signing on macOS, notarisation; nothing on Linux) — one line each.

- [ ] **Step 3: Answer the other facets**

Presence: the single line *"Not researched; unlikely to be needed."* UI: Godot's Control nodes are the UI; one line on theming; the closing BACKLOG #2 sentence. Storage: `ConfigFile` and `user://` (the "File paths in Godot projects" page — where `user://` resolves per OS), SQLite only via an addon — name the current one on the Asset Library and its concern line.

- [ ] **Step 4: Add the web stub line**

In `## When this is the stack`, append: *"Web export exists in Godot but is not researched here — the Game / web row is a stub; research before the first browser game."*

- [ ] **Step 5: Write the sections, frontmatter check, reader-side pass, commit**

```bash
git add skills/stack-godot/SKILL.md
git commit -m "stack-godot: scope divergence, presence, UI and storage from Godot's docs (v18 pass 9)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Facets and scope divergence on `stack-unity` — research pass 10

**Files:**
- Modify: `skills/stack-unity/SKILL.md` (insert `## Presence`, `## UI`, `## Storage` after its build section; replace its "What games change" section with `## Scope divergence`; extend `## Sources`)

- [ ] **Step 1: Read the existing skill in full and spec §3**

- [ ] **Step 2: Answer Scope divergence from Unity's own docs**

1. What the engine keeps per-platform: build profiles (docs.unity3d.com — "Build Profiles", Unity 6), platform-dependent compilation (`#if UNITY_ANDROID` — the "Platform dependent compilation" page).
2. Input: the Input System package — action maps bound to touch, keyboard, gamepad; on-screen controls (docs.unity3d.com/Packages/com.unity.inputsystem — current version).
3. UI scaling: Canvas Scaler modes for UGUI, and UI Toolkit's panel settings — which the docs recommend for multiple resolutions.
4. Performance: URP quality levels per platform; the mobile-specific guidance page.
5. Per-platform desktop differences: what the Windows/macOS/Linux build pages say differs — one line each.

- [ ] **Step 3: Answer the other facets**

Presence: *"Not researched; unlikely to be needed."* UI: UI Toolkit vs UGUI — which Unity 6's docs call the default for new work, and the concern line for the other; the closing BACKLOG #2 sentence. Storage: `Application.persistentDataPath` per OS (the docs page says where), `PlayerPrefs` for config with its size caveat, SQLite via a package — name the current one and its concern line.

- [ ] **Step 4: Write the sections, frontmatter check, reader-side pass, commit**

```bash
git add skills/stack-unity/SKILL.md
git commit -m "stack-unity: scope divergence, presence, UI and storage from Unity's docs (v18 pass 10)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: iOS build and sign from Linux — research pass 11; settles the two *(pending pass 11)* rows

**Files:**
- Modify: `skills/stack-ios-native/SKILL.md` (the "a Mac at hand or a cloud Mac" paragraph at line 33 gains a `### Building without a Mac` subsection)
- Modify: `skills/stack-flutter/SKILL.md` (same subsection under `## Build, run, test`)
- Modify: `skills/orc-code/SKILL.md` (the two *(pending pass 11)* rows)

**Interfaces:**
- Produces: the decision `EAS_REQUIRES_RN` — true or false — recorded in the commit message and in the orc-code table. Tasks 10 and 12 read the table, not this task.

- [ ] **Step 1: Read spec §2's React Native paragraph and §5 pass 11**

- [ ] **Step 2: Answer from live sources**

1. **EAS Build** (docs.expo.dev/build/introduction and docs.expo.dev/build-reference): what project types it builds — Expo/React Native only, or any iOS project? Quote the line that says. Pricing tier with iOS builds; whether it signs and submits (EAS Submit).
2. **Codemagic** (docs.codemagic.io): Flutter, native iOS, React Native support — quote; free-tier macOS minutes; signing and App Store Connect upload.
3. **GitHub Actions macOS runners** (docs.github.com/actions — runner images and per-minute pricing): can a private repo build and sign a Flutter or native iOS app there; the current macOS image and Xcode version; cost multiplier for macOS minutes.
4. **Bitrise** — one line, only if the Codemagic or Expo docs compare against it; otherwise omit.

- [ ] **Step 3: Decide, by the selection rule**

- If EAS builds only React Native/Expo projects (`EAS_REQUIRES_RN = true`): the two rows stay React Native. Record the quoted line.
- If EAS builds any iOS project, or Codemagic / GitHub Actions build Flutter for iOS with signing at comparable ease (`EAS_REQUIRES_RN = false`): the two rows revert to Flutter as default with React Native as the first alternative, per spec §2. Edit both rows in `skills/orc-code/SKILL.md`, and remove *(pending pass 11)* either way.

- [ ] **Step 4: Write `### Building without a Mac` in both skills**

Under the existing build section of `stack-ios-native` and `stack-flutter`: the easiest named option with cost and what it needs from the developer (an Apple Developer account, App Store Connect API key), one concern line per alternative, stamps.

- [ ] **Step 5: Frontmatter check, reader-side pass, commit**

```bash
git add skills/stack-ios-native/SKILL.md skills/stack-flutter/SKILL.md skills/orc-code/SKILL.md
git commit -m "iOS builds from Linux: named cloud options; settles the pending-pass-11 rows (v18 pass 11)

EAS_REQUIRES_RN = <true|false>: '<the quoted line from docs.expo.dev>'. Rows now read: <...>.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: `stack-kotlin-multiplatform` — research pass 2

**Files:**
- Create: `skills/stack-kotlin-multiplatform/SKILL.md`
- Modify: `skills/stack-android-native/SKILL.md` (lines 27–29, the "Neither KMP nor CMP is a decided stack here" sentence — now it is; and the KMP-shaped-from-day-one answer in `## When this is the stack`)
- Modify: `skills/orc-code/SKILL.md` (the Android + iOS row's Knowledge cell gains `; KMP: \`skills/stack-kotlin-multiplatform/SKILL.md\``)

- [ ] **Step 1: Read spec §2's KMP paragraph, `stack-android-native` and `stack-ios-native` in full**

- [ ] **Step 2: Answer from live sources**

1. KMP's status and Google's recommendation — developer.android.com/kotlin/multiplatform and kotlinlang.org/docs/multiplatform: quote the current wording on business logic; quote what is said about Compose Multiplatform for iOS UI (stable or not, as of the date).
2. Toolchain: Kotlin version, KMP Gradle plugin, the IDE story (Android Studio vs Fleet vs IntelliJ — what kotlinlang.org currently says), Xcode requirement for the iOS half.
3. Layout: `commonMain` / `androidMain` / `iosMain` — the "Project structure" page; how the iOS app consumes the shared module (framework via CocoaPods or SPM — which the docs now recommend).
4. **The day-one question**: what does kotlinlang.org's "Make your Android app cross-platform" guide say it takes to convert an existing Android app? If the answer is "move logic into a shared module, which you could have started with", the Android-only row should say to start KMP-shaped — write the one-line recommendation and its stamp.
5. Facets: Presence (each platform's native mechanism — point at `stack-android-native` and `stack-ios-native`'s Presence sections; say the shared module has no presence of its own), UI (native Compose and SwiftUI on each side, or Compose Multiplatform on both — with the concern line from question 1), Storage (SQLDelight or Room KMP — which kotlinlang.org's docs list; `multiplatform-settings` for config).

- [ ] **Step 3: Write the skill**

Frontmatter `name: stack-kotlin-multiplatform`. Sections: the standard shape plus the three facets, opening with the unbuilt marker. `## When this is the stack`: the Android + iOS row's "native UI on both, shared logic" alternative, and the migration path from an Android-only Kotlin app. `## Where each store rule lands`: point at the two native skills' tables — the shared module changes nothing there.

- [ ] **Step 4: Update `stack-android-native`**

Replace the sentence at lines 27–29 ending "Neither KMP nor CMP is a decided stack here." with a pointer: *"Kotlin Multiplatform is the decided path to iOS from here — `skills/stack-kotlin-multiplatform/SKILL.md`."* Add the day-one recommendation from Step 2.4 to `## When this is the stack`.

- [ ] **Step 5: Table row, frontmatter check, reader-side pass, commit**

```bash
git add skills/stack-kotlin-multiplatform/SKILL.md skills/stack-android-native/SKILL.md skills/orc-code/SKILL.md
git commit -m "stack-kotlin-multiplatform: shared logic with native UI, from live research (v18 pass 2)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 10: `stack-react-native` — research pass 3

**Files:**
- Create: `skills/stack-react-native/SKILL.md`
- Modify: `skills/orc-code/SKILL.md` (the Android + iOS row and the "iOS ticked" cross-family row: Knowledge cell → `` `skills/stack-react-native/SKILL.md` — read it in full before scaffolding ``, whichever of default or alternative React Native is after Task 8)

- [ ] **Step 1: Read spec §2's React Native paragraph, the orc-code table as Task 8 left it, and `stack-flutter` as the model**

- [ ] **Step 2: Answer from live sources**

1. Toolchain: React Native version (reactnative.dev/docs/getting-started — and whether the docs now say to start with Expo; quote), Expo SDK version (docs.expo.dev), Node LTS, the New Architecture status (reactnative.dev blog — is it the default?).
2. Layout: an Expo project's layout vs a bare one; where `android/` and `ios/` live and when they are generated (prebuild).
3. Build, run, test: `npx expo run:android`, EAS Build for iOS (Task 8's finding — cite it, do not redo it); Jest; link `skills/orc-test/languages/javascript.md`.
4. **React web for the cross-family case**: `react-native-web` (npm — current version, what Expo says about web targets) versus a separate React web app sharing only non-UI code — which the docs recommend, and the concern line for each. Desktop: `react-native-windows` and `react-native-macos` (Microsoft — current versions and support status); Linux desktop — what exists, honestly (likely nothing maintained; say so).
5. Facets: Presence (`expo-notifications` on both platforms — current version and what it exposes; desktop tray — none, say so), UI (React Native core components; Expo Router; the "same UI on both" claim and its concern line — platform-specific look), Storage (`expo-sqlite` and `@react-native-async-storage/async-storage` — versions; where they live per platform).
6. Where each store rule lands: Expo's `app.json` fields for versions, permissions, privacy manifest (docs.expo.dev — the privacy manifest page) — the table shape the other skills use, pointing at `skills/orc-package/ingredients/{play,app-store}`.

- [ ] **Step 3: Write the skill, table rows, frontmatter check, reader-side pass, commit**

Frontmatter `name: stack-react-native`. Unbuilt marker. Standard shape plus the three facets plus a `## React web and desktop` section from Step 2.4.

```bash
git add skills/stack-react-native/SKILL.md skills/orc-code/SKILL.md
git commit -m "stack-react-native: mobile, React web and desktop reach, from live research (v18 pass 3)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 11: `stack-web` — research pass 4

**Files:**
- Create: `skills/stack-web/SKILL.md`
- Modify: `skills/orc-code/SKILL.md` (the App / web only row: Default cell → the chosen stack; Knowledge cell → the skill)

- [ ] **Step 1: Read spec §2's web paragraph and BACKLOG #4's original web line ("HTML5/CSS/JS/React/Python confirmed as the toolset")**

- [ ] **Step 2: Answer from live sources**

1. Front end: React (react.dev — current version and what the docs say to start with: a framework, and which ones they name), Vite (vitejs.dev — current version) as the build tool if React's docs still list it; TypeScript or JavaScript — what react.dev's start page defaults to. Selection rule: easiest that works; the concern line for the alternatives named in react.dev.
2. Back end, two candidates from #4's toolset: Python — FastAPI (fastapi.tiangolo.com) and Django (djangoproject.com), current versions and each one's own "when to use" wording; Node — the framework react.dev's start page names (Next.js or otherwise). Default by the selection rule; state the concern that swings it — a Python back end shares nothing with a React front end but keeps direflail in the language they know; a Node back end shares the language with the front end.
3. Layout: the chosen front-end framework's scaffold layout; monorepo or two directories — what the chosen back end's docs show for serving a React front.
4. Build, run, test: dev server, production build, and the test runner each framework's docs name; link `skills/orc-test/languages/javascript.md` and `python.md`.
5. Facets: Presence (Web Notifications API and service-worker push — MDN; what a PWA can do on desktop and mobile, one paragraph), UI (the component approach react.dev shows; a CSS strategy only if react.dev names one; the BACKLOG #2 sentence), Storage (server-side: SQLite via the back end's default ORM for a single-host app, with the concern line for Postgres; client-side: `localStorage`/IndexedDB — MDN).
6. Deployment: no store — say so, and that no ingredient exists; name in one line what the front-end framework's docs say about static hosting.

- [ ] **Step 3: Write the skill, table row, frontmatter check, reader-side pass, commit**

Frontmatter `name: stack-web`. Unbuilt marker. Standard shape (with `## Where each store rule lands` replaced by `## Deployment`), plus the three facets.

```bash
git add skills/stack-web/SKILL.md skills/orc-code/SKILL.md
git commit -m "stack-web: the web-only default from live research (v18 pass 4)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 12: Cross-family concern lines — research pass 5

**Files:**
- Modify: `skills/stack-flutter/SKILL.md` (new `## Beyond mobile — desktop and web` section after `## Build, run, test`)
- Modify: `skills/stack-react-native/SKILL.md` (its `## React web and desktop` section gains the comparison's concern lines)
- Modify: `skills/stack-kotlin-multiplatform/SKILL.md` (a `## Compose Multiplatform beyond mobile` section)
- Modify: `skills/orc-code/SKILL.md` (the two cross-family rows, if the comparison moves a default — record why in the commit if it does not)

- [ ] **Step 1: Read Tasks 2, 3, 9, 10, 11's outputs in full — this task pits them against each other**

- [ ] **Step 2: Answer from live sources — the claims that most need checking**

1. Flutter on Linux desktop: docs.flutter.dev's desktop support page — which Linux toolkit it renders through (GTK), what is "stable" vs not, and whether the tray/presence answer from Task 3 holds on Linux.
2. Flutter on web: docs.flutter.dev/platform-integration/web — the renderer (CanvasKit / skwasm / HTML), what the docs say it is and is not for (quote the line about content-heavy sites if it still exists), SEO and text selection caveats.
3. React Native on desktop: Task 10's finding — restate in one line, with the Linux answer.
4. Compose Multiplatform on desktop (JVM) and web (Wasm): kotlinlang.org — stability per target, quoted.
5. For each of the two cross-family rows (iOS ticked / not ticked), write the concern line that would move a project from the row's default to each alternative — and answer the spec's question, "which one direflail would rather live in", in one honest paragraph per row, from what the sources say, not from preference.

- [ ] **Step 3: Write the sections; move a default only if the sources compel it**

If a default moves, edit the row in `skills/orc-code/SKILL.md` and say in the commit which quoted line moved it. If not, say in the commit that the comparison was run and the rows stand.

- [ ] **Step 4: Frontmatter check, reader-side pass, commit**

```bash
git add skills/stack-flutter/SKILL.md skills/stack-react-native/SKILL.md skills/stack-kotlin-multiplatform/SKILL.md skills/orc-code/SKILL.md
git commit -m "cross-family: Flutter, React Native and Compose Multiplatform beyond mobile — concern lines from live sources (v18 pass 5)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 13: Resolve BACKLOG #4, note #2, final read of the table

**Files:**
- Modify: `BACKLOG.md` (#4 heading and a resolution paragraph; #2 a note paragraph — by hand, per `backlog-discipline`'s "Resolving an entry")
- Read: `skills/orc-code/SKILL.md`

- [ ] **Step 1: Confirm nothing in the table still says *pending* or *no skill yet* except the rows the spec leaves as stubs**

Run: `grep -n "pending pass\|no skill yet" skills/orc-code/SKILL.md`
Expected: no output. (Stub rows say *stub*, not *no skill yet*.) If anything prints, a task above did not update its row — fix that first.

- [ ] **Step 2: Walk the spec's four scaffold requests once more against the finished table**

Same four as Task 1 Step 4. Each lands on one row whose Knowledge cell names a real file. Run `ls` on each named file.

- [ ] **Step 3: Resolve #4**

Invoke `orclab:backlog-discipline` and follow "Resolving an entry": append `(RESOLVED <date>)` to #4's heading; append a paragraph beginning **Resolved for real, not just tracked:** naming the spec, the eleven passes by task number, which rows are stubs and why (direflail's call, 2026-09-12), and what stays parked (Docker, observability, external databases — spec §6).

- [ ] **Step 4: Note on #2**

Append to #2's body a paragraph beginning **Note <date> (v18):** every stack skill now has a `## UI` section ending "BACKLOG #2's design system translates into the frameworks above" — list the skills — so #2's translation targets are enumerated. #2 stays open; do not mark its heading.

- [ ] **Step 5: Commit**

```bash
git add BACKLOG.md
git commit -m "Resolve BACKLOG #4 (v18 shipped); note #2's translation targets

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-review against the spec

- **§1 scope question** → Task 1. **§2 table and every row's reasoning** → Task 1; rows filled by Tasks 2, 8, 9, 10, 11, 12. **§3 facets on all skills** → Tasks 2–7, 9–11; Linux subtree → Task 2 Step 3; scope divergence → Tasks 6, 7; framework-conventions rule → Global Constraints. **§4 selection rule** → Global Constraints, applied in every research step. **§5 eleven passes** → passes 1–11 are Tasks 2, 9, 10, 11, 12, 3, 4, 5, 6, 7, 8 respectively; sequence matches §5 (1, 6–10, 11, 2, 3, 4, 5). **§6 parked** → Task 13 Step 3 records it. **§7 unchanged** → no task touches `/orc-package`, `/orc-publish`, `/orc-test` or the ingredients. **Verification** → Task 1 Step 4 and Task 13 Step 2 (the four walks); the reader-side pass in every task.
- No task produces code; the "test" in each is the frontmatter check plus the by-hand walk, which is what the spec's Verification section specifies.
- Names used across tasks: `stack-python-desktop`, `stack-kotlin-multiplatform`, `stack-react-native`, `stack-web`; section headings `## Presence`, `## UI`, `## Storage`, `## Scope divergence`, `### Building without a Mac`, `## React web and desktop`, `## Beyond mobile — desktop and web`, `## Compose Multiplatform beyond mobile`; the flag `EAS_REQUIRES_RN`. Checked consistent.
