---
name: stack-unity
description: Background knowledge for any work in a Unity project (C#, Unity 6) - creating one, building for Android, iOS or desktop, configuring signing, versions or SDK levels, choosing a package, licensing questions, or preparing a Google Play or App Store release of a game. Says what the current toolchain is, where things live, and where each store rule lands. Not a command; Claude reads it when Unity is in play.
user-invocable: false
---

# Unity — cross-platform games, C#

**Checked against live sources on 2026-09-11.** Unity **6000.6.0f1** (2026-08-31). Unity ships a
minor every ~2 months and patches weekly; treat anything here older than one minor as suspect —
`orclab:currency-discipline` says re-check, and "Sources" says where.

**Nobody here has shipped a Unity game, and games are not in focus** (direflail, 2026-09-11).
This file is deliberately thinner than the mobile stacks: enough that a game session starts from
verified ground, not enough to pretend the game-specific questions (controls, a desktop sibling)
are answered. "Scope divergence" below says what the docs say about them; no game has tested it.

## When this is the stack

The **alternative** on every game row of `/orc-code`'s Defaults Table — Godot (`stack-godot`) is
the default for desktop, mobile, or both — chosen when the concern below applies (v18 spec §2,
2026-09-12). Unity is the larger ecosystem — more packages, more platform SDK integrations (ads,
IAP, analytics), more hiring — and is C#. Godot is smaller, open source, GDScript or C#. A game
that must ship on both stores is fine in either; the store ingredients apply to both unchanged.

**Licensing, because it is the question people have about Unity.** Unity Personal is free for
individuals and organisations under **US$200K** revenue or funding in the prior 12 months; Pro is
**$2,310 per seat per year** ($210 monthly). The 2023 Runtime Fee was **cancelled** (Unity's blog,
September 2024) before it ever applied, and the "Made with Unity" splash screen is **optional on
Personal from Unity 6**. Personal still requires a Unity account and Unity Hub to activate.

## Toolchain, as of 2026-09-11

| Thing | Current | Where it was read |
|---|---|---|
| Unity Editor | 6000.6.0f1 (Unity 6.6), via Unity Hub, which manages editor versions and platform modules | unity.com/releases/editor/whats-new |
| Language | C#, the .NET profile Unity bundles (not the system .NET SDK) | Unity manual |
| Editor on Linux | Supported (Ubuntu). **Android builds work from this machine.** The *iOS Build Support* module installs on Linux but produces only an Xcode project — the archive needs a Mac, same as every other stack here. Unity Build Automation is Unity's paid cloud Mac. | Unity manual "Getting started with iOS"; Hub module list |
| Android module | Hub installs OpenJDK, Android SDK and NDK matched to the editor — do not point Unity at Android Studio's SDK unless you have to | Unity manual |
| Android API levels | Minimum API 23; Unity 6.x targets API 35 and 36 ("Target API Level" in Player Settings; *Automatic (highest installed)* is the default and picks what the Hub installed) | Unity manual "Android requirements and compatibility" |
| 16 KB page size | Supported in Unity 6 — "update to recent Unity patches"; **native plugins are the risk** and must be rebuilt aligned. Unity's own note: Firebase ≥ 12.10, Burst ≥ 1.8.21 | Unity manual; Unity discussions |
| Privacy manifest (iOS) | The engine **declares its own** required-reason APIs since 2021.3.35 / 2022.3.18 / 2023.2.7 (file timestamp, user defaults, system boot time, disk space); the *app's* manifest is yours, placed at `Assets/Plugins/PrivacyInfo.xcprivacy`; each third-party package ships its own | Unity manual "Apple's privacy manifest policy requirements" |
| Headless build | `Unity -batchmode -quit -projectPath <p> -buildTarget <Android\|iOS\|StandaloneLinux64> -executeMethod <Class.Method> -logFile <f>` where the static C# method calls `BuildPipeline.BuildPlayer` | Unity manual "Command line arguments" |

## Project layout — where things live

| Path | What |
|---|---|
| `Assets/` | Everything the game is made of: scenes, scripts, prefabs, art. `Assets/Plugins/` for native plugins and the iOS privacy manifest. |
| `Packages/manifest.json` | Package Manager dependencies (Unity registry, git URLs). The version pins. |
| `ProjectSettings/ProjectSettings.asset` | **Player Settings** — company/product name, `applicationIdentifier` (bundle id / package name, per platform), `bundleVersion` (version string), `AndroidBundleVersionCode`, iOS `buildNumber`, target API level, architectures, signing keystore path. Edited through *Edit → Project Settings → Player*; the asset is YAML and diffable. |
| `ProjectSettings/EditorBuildSettings.asset` | Scenes in the build. |
| `Library/`, `Temp/`, `Logs/`, `Build/` | Generated. Git-ignored (Unity's standard `.gitignore`). |
| Build Profiles (`File → Build Profiles`) | Per-platform build configuration; *Build App Bundle (Google Play)* lives here for Android. |

## Build

Android: Build Profiles → Android → *Build App Bundle (Google Play)* → Build, or the headless
form above. Output is wherever the build method says; `.aab` when the bundle option is on.
*Export Project* instead produces a Gradle project for Android Studio when the manifest or Gradle
needs hand-editing.

iOS: Build produces an **Xcode project**; from there the App Store ingredient's local shape
applies (`xcodebuild archive` / `-exportArchive`, or Xcode by hand). The Unity-generated project's
`Unity-iPhone` target is where signing and `PrivacyInfo.xcprivacy` end up.

Coverage, mutation testing and test lint for this language: `skills/orc-test/languages/csharp.md`
— `/orc-test` reads it.

## Presence

Not researched; unlikely to be needed.

## UI

No project has been built with these facets yet; the first one corrects them. The UI is the menus,
HUD and dialogs the player reads and taps, as distinct from the game world. Unity has two runtime
systems and its own docs pick one: the *Comparison of UI systems in Unity* table for Unity 6.6 puts,
for Runtime, **Recommendation: uGUI (Unity UI)**, **Alternative: UI Toolkit** (confirmed live
2026-09-12; the 6.3 LTS page carries the same table). **Default: uGUI** — a Canvas of GameObjects,
laid out in the Scene view like everything else; *"uGUI is the recommended solution for the
following: Easy referencing from MonoBehaviours"*, and it alone has *"In-scene authoring"*,
*"Serialized events"* and *"Integration with Animation Clips and Timeline"* (that page's feature
table); the package is `com.unity.ugui` 2.6 (confirmed live 2026-09-12). **Alternative: UI
Toolkit**, only for its concern — *"UI Toolkit is an alternative to uGUI (Unity UI) if you create a
screen overlay UI that runs on a wide variety of screen resolutions"* or with *"a significant
amount of user interfaces"*; it is *"web-like"*, *"document-based"*, edited in the UI Builder, and
*"in active development"* where uGUI is *"established and production-proven"* and *"updated
infrequently"*. Both work with the Input System package (*"Input system support"*, both ticked).
BACKLOG #2's design system translates into the frameworks above.

## Storage

No project has been built with these facets yet; the first one corrects them. Storage is what the
game keeps on the device between runs: settings, and saved progress. **Files go under
`Application.persistentDataPath`** — *"a directory path where you can store data that you want to
retain between runs"*; on iOS and Android *"The files can only be erased by users directly and not
by any app updates"* (confirmed live 2026-09-12, that Scripting API page). Where it is, per OS, from
the same page: Windows *"%userprofile%\AppData\LocalLow\<companyname>\<productname>"*; macOS player
*"~/Library/Application Support/unity.company name.product name"* (the Editor uses
`.../company name/product name`; the player *"uses the Editor path if that directory already
exists"*); Linux
*"$XDG_CONFIG_HOME/unity3d/Company/ProjectName"*, so `~/.config/unity3d/...`; Android
*"/storage/emulated/<userid>/Android/data/<packagename>/files"*; iOS
*"/var/mobile/Containers/Data/Application/<guid>/Documents"*; Web *"a location in the browser's
IndexedDB file system"*. The location follows the identity in Player Settings — *"If you keep the
same Bundle Identifier in future versions, the application keeps accessing the same location on
every update"* — so settle company, product and identifier before the first release. Build the full
path with `Path.Combine(Application.persistentDataPath, ...)`: the page warns that relative paths
land in the project folder on desktop. Saved progress is a file there: `JsonUtility.ToJson` on a
plain C# class (*"such as when saving game state"*; it serialises fields only, per Unity's
serializer rules — confirmed live 2026-09-12) written with `System.IO.File`. External databases are
out of scope for this skill.

**Config: `PlayerPrefs`** — *"stores Player preferences between game sessions"*, three value types
only (*"string, float and integer"*), unencrypted (*"Don't use PlayerPrefs data to store sensitive
data"*), and the size caveat is the Web platform's: *"Unity stores up to 1MB of PlayerPrefs data"*
there (confirmed live 2026-09-12, `PlayerPrefs` page, which also lists where it lands per OS: the
Windows registry, a `.plist`, `~/.config/unity3d`, `shared_prefs`, `NSUserDefaults`) — settings, not
saves. **SQLite only via a package**, and only when there are rows to query: Unity's manual names
none (a live search of docs.unity3d.com finds SQLite only as Visual Scripting's internal
dependency), so the current one is **`com.gilzoide.sqlite-net`** — SQLite-net 1.9.172 on SQLite
3.50.1, installed by git URL in the Package Manager
(`https://github.com/gilzoide/unity-sqlite-net.git#1.3.2`) or OpenUPM; latest tag 1.3.2, repository
active 2026-04 (confirmed live 2026-09-12). Its concern: a native binary per platform, so the
Android one falls under the 16 KB row in the store table — 1.3.2's own changelog line is *"Warning
about Android libraries not being aligned to 16kb page size"* — and *"Android and WebGL platforms
don't support loading SQLite databases from Streaming Assets and will always load them in memory"*,
so a database that must be written lives under `persistentDataPath`.



## Where each store rule lands

The store ingredients (`skills/orc-package/ingredients/play`, `.../app-store`) state the rules.

| Rule | Where it lands in Unity | Check |
|---|---|---|
| Play: target API 36 | Player Settings → Android → *Target API Level*. *Automatic* targets the highest SDK the Hub installed — confirm that is 36. | `grep AndroidTargetSdkVersion ProjectSettings/ProjectSettings.asset` (0 = automatic) and the SDK the Hub installed |
| Play: 16 KB alignment | Unity 6's own libraries are aligned; **every native plugin in `Assets/Plugins/Android`** and every package with native code must be. | `bundletool dump config --bundle=<out>.aab \| grep alignment` → `PAGE_ALIGNMENT_16K`, on the real bundle |
| Play: upload-key signing | Player Settings → Android → Publishing Settings → keystore path, alias, passwords. Unity stores the *path* in `ProjectSettings.asset` and asks for passwords per session unless supplied via the headless build's environment. Never commit the keystore. | `git check-ignore <keystore>` |
| Play: package name; version code increases | `applicationIdentifier` (Android) and `AndroidBundleVersionCode` in `ProjectSettings.asset`; `bundleVersion` is the version string. `/orc-version` edits these. | Play refuses a reused code |
| Play: Data safety | Decided by packages — Unity Analytics, Ads, IAP, Firebase all send data off-device. Keep the list. | `Packages/manifest.json` |
| App Store: Xcode 26+ | The Mac's Xcode, against the exported project. | `xcodebuild -version` |
| App Store: privacy manifest | Engine reasons are automatic (versions above). The app's own `Assets/Plugins/PrivacyInfo.xcprivacy` for anything beyond them — C# `File.GetLastWriteTime` and friends count as file-timestamp API use — plus each package's own. | present in the exported Xcode project's target; Xcode → Product → *Generate Privacy Report* after archiving |
| App Store: bundle id, signing, build number | `applicationIdentifier` (iOS), Player Settings → iOS → *Signing Team ID* / automatic signing, `buildNumber`. | exported project's General tab |
| App Store: usage strings | Player Settings → iOS → *Camera Usage Description*, *Microphone Usage Description*, *Location Usage Description*. Unity writes them into the exported `Info.plist`. | `plutil -p <exported>/Info.plist \| grep Usage` |
| Both: privacy policy in-app, account deletion, login rules | Game code. | — |

## Scope divergence

No project has been built with these facets yet; the first one corrects them. Scope divergence is
what happens when one game ships on a phone and on a desktop: some differences the engine keeps
apart for you in a setting, and some you have to design differently — a thumb is not a mouse, a
portrait phone is not a 16:9 monitor, a phone GPU is not a desktop one. Which actions a game has,
and whether a desktop build ships at all, stays the game's decision; desktop distribution is Steam,
itch.io, or the Linux channels Orclab already knows. On the store side Play asks at creation —
*"Specify whether your application is an app or a game. You can change this later."* (confirmed
live 2026-09-12, Play Console Help, *Create and set up your app*).

**What the engine keeps per platform.** A **build profile** per platform — *"a set of
configuration settings you can use to build your application on a particular platform"*, saved
*"as an asset file that is ready for use with version control"*; *"settings saved under build
profiles aren't shared across all the platforms"*, and Quality (below) can be customised per
profile (confirmed live 2026-09-12, *Introduction to build profiles*; *Quality project settings
reference*). **Scripting symbols** for the code that must differ: `#if UNITY_ANDROID`, `UNITY_IOS`,
`UNITY_STANDALONE_WIN`, `UNITY_STANDALONE_OSX`, `UNITY_STANDALONE_LINUX`, `UNITY_STANDALONE` (*"any
standalone platform"*), `UNITY_EDITOR` — the code inside is *"omitted entirely"* from other
targets, unlike a runtime `if` (confirmed live 2026-09-12, *Conditional compilation in Unity*;
*Unity scripting symbol reference*).

**Input.** The **Input System** package (`com.unity.inputsystem` 1.20.0, *"intended to be a
replacement for Unity's classic Input Manager"*): **actions** *"separate the purpose of an input
from the device controls which perform that input"* — a `Move` action bound to *"the left gamepad
stick and the keyboard's arrow keys"* is the docs' own example — and code reads the action, never
the device; **control schemes** *"let you enable or disable different sets of bindings for your
actions for different types of devices"* (confirmed live 2026-09-12, package manual *Actions*,
*Control schemes*). Touch on mobile: **on-screen controls** — *"stick and button widgets on
touchscreens to emulate a joystick or gamepad"*; an On-Screen Button whose control path is
`<Gamepad>/buttonSouth` means the Input System *"creates both a Gamepad and a Keyboard"* as
needed, *"automatically when the components are enabled"* — so the same bindings serve phone and
desktop and the widgets are simply not enabled on desktop; they *"don't have a predefined visual
representation"*, the sprite is yours (confirmed live 2026-09-12, *Introduction to on-screen
controls*). Designing input as actions from day one is what makes a desktop sibling possible.

**UI scaling and aspect ratio.** uGUI: the **Canvas Scaler** on the root Canvas (added by default
with a new Canvas), **UI Scale Mode = Scale With Screen Size** with a **Reference Resolution** —
*"the Canvas will keep having only the resolution of the reference resolution, but will scale up in
order to fit the screen"* — **Match** 0.5 so portrait and landscape scale evenly, and **anchors**
tying each element to its corner; that walk-through is *Designing UI for Multiple Resolutions*, and
the default (no scaler, or Constant Pixel Size) keeps pixel sizes, so elements *"take up a larger
or smaller proportion of the screen"* (confirmed live 2026-09-12, uGUI 2.6 *Canvas Scaler* and that page). UI Toolkit: the same
three modes and Match on the **Panel Settings** asset (*"Set how the panel's UI scales when the
screen size changes"*), with layout in Flexbox, which the best-practice guide calls *"a necessary
feature for any game that is targeting multiple platforms with different screen resolutions and
ratios"* (confirmed live 2026-09-12, *Panel Settings properties reference*; *Layouts*).

**Performance: quality levels.** **Edit → Project Settings → Quality** is a matrix of quality
levels × platforms with a default per platform — *"It's best to use lower quality on mobile devices
and older platforms"* — and each level *"Sets the render pipeline asset to use at this quality
level"*, so a mobile level points at a leaner **URP asset** than the desktop one; switching at
runtime belongs in *"loading screens or on static menus"* (confirmed live 2026-09-12, *Quality
project settings reference*; *Change the active URP asset at runtime*). The mobile-specific page is
*Configure for better performance in URP* — a list of URP-asset switches for *"lower-end mobile
platforms"* (Store Actions, LOD Cross Fade, the Baked Lit / Simple Lit shaders, Depth Priming
*"Disabled for mobile platforms"*); the *"mobile-friendly"* post effects are Bloom, Chromatic
Aberration, Color Grading, Lens Distortion, Vignette (confirmed live 2026-09-12; *Introduction to
post-processing in URP*).

**Per-platform desktop differences** (each build page, confirmed live 2026-09-12). **macOS**: an
architecture — *"Apple silicon is the recommended target architecture for new macOS builds"*,
Intel and universal are *"Deprecated"* — then *"Code signing & notarization"*: unsigned, *"the
device warns the end user before they open the application"*; notarization is Apple's check of
*"Developer ID-signed applications"*, which *"Digital distribution services often require"*. **Windows**: an architecture (Intel 64-bit,
Intel 32-bit, ARM 64-bit); the build page says nothing about signing your executable —
`UnityPlayer.dll` is *"signed with the Unity Technologies certificate"*, yours is not. **Linux**:
one `ProjectName.x86_64`, `UnityPlayer.so`, a `_Data` folder, and Unity ships `libdecor-0.so.0` so
the window is decorated *"across various compositors"* under Wayland; no signing.

## Sources (live on 2026-09-11; facets 2026-09-12)

- Current editor: `https://unity.com/releases/editor/whats-new`
- Pricing and Personal threshold: `https://unity.com/pricing`; Runtime Fee cancellation:
  `https://unity.com/blog/unity-is-canceling-the-runtime-fee`
- Android build process: `https://docs.unity3d.com/Manual/android-BuildProcess.html`;
  requirements: `https://docs.unity3d.com/6000.2/Documentation/Manual/android-requirements-and-compatibility.html`
- iOS build process: `https://docs.unity3d.com/Manual/iphone-BuildProcess.html`
- Privacy manifest: `https://docs.unity3d.com/6000.2/Documentation/Manual/apple-privacy-manifest-policy.html`
- Command line: `https://docs.unity3d.com/6000.2/Documentation/Manual/EditorCommandLineArguments.html`
- Store rules themselves: the Play and App Store ingredients under `skills/orc-package/ingredients/`.
- Facets (2026-09-12) — UI: `https://docs.unity3d.com/6000.6/Documentation/Manual/UI-system-compare.html` (the unversioned `/Manual/` path is 6000.6 today; `6000.3` carries the same table), `https://docs.unity3d.com/Packages/com.unity.ugui@latest/` (resolves to 2.6)
- Facets — storage: `https://docs.unity3d.com/6000.6/Documentation/ScriptReference/Application-persistentDataPath.html`, `https://docs.unity3d.com/6000.6/Documentation/ScriptReference/PlayerPrefs.html`, `https://docs.unity3d.com/6000.6/Documentation/ScriptReference/JsonUtility.html`, `https://github.com/gilzoide/unity-sqlite-net` (README, CHANGELOG, tags; Unity's docs name no SQLite package — a `site:docs.unity3d.com sqlite` search returns only Visual Scripting's internal dependency)
- Scope divergence: `https://docs.unity3d.com/6000.6/Documentation/Manual/build-profiles.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/platform-dependent-compilation.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/scripting-symbol-reference.html`, `https://docs.unity3d.com/Packages/com.unity.inputsystem@1.20/manual/index.html` (`@latest` resolves here), `.../Actions.html`, `.../control-schemes.html`, `.../introduction-on-screen-controls.html`, `https://docs.unity3d.com/Packages/com.unity.ugui@2.6/manual/script-CanvasScaler.html`, `https://docs.unity3d.com/Packages/com.unity.ugui@2.6/manual/HOWTO-UIMultiResolution.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/UIE-Runtime-Panel-Settings.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/best-practice-guides/ui-toolkit-for-advanced-unity-developers/layouts.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/class-QualitySettings.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/urp/urp-quality-settings-landing.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/urp/quality/quality-settings-through-code.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/urp/configure-for-better-performance.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/urp/integration-with-post-processing.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/macos-building.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/WindowsStandaloneBinaries.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/build-for-linux.html`, `https://support.google.com/googleplay/android-developer/answer/9859152`; read and found nothing to keep: `https://docs.unity3d.com/6000.6/Documentation/Manual/android-optimization.html` (a landing page — threads, startup, foldables), `https://docs.unity3d.com/6000.6/Documentation/Manual/Windows.html` (landing)
