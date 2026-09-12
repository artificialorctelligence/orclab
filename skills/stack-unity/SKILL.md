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
are answered. They are named in "What games change" and left open.

## When this is the stack

direflail's choice, with Godot, for **cross-platform games including mobile** (BACKLOG #4,
2026-09-11). Neither is preferred over the other yet. Unity is the larger ecosystem — more
packages, more platform SDK integrations (ads, IAP, analytics), more hiring — and is C#. Godot
(`stack-godot`) is smaller, open source, GDScript or C#. A game that must ship on both stores is
fine in either; the store ingredients apply to both unchanged.

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

## What games change — named, not answered

direflail expects mobile games to follow the store rules above but to differ "somewhat" from
apps, and does not yet know how. What the research can say now:

- **Store records:** Play asks "app or game" at creation and games get a different listing
  layout; the IARC content rating questionnaire is the same mechanism. Apple's Game Center is
  optional and a capability on the bundle id.
- **Controls, and a desktop sibling:** Unity's *Input System* package maps actions to devices
  (touch, keyboard, gamepad) so one game can run on a phone and a desktop with different
  controls. Designing input as actions from day one is what makes a desktop version possible
  later; which actions, and whether a desktop build ships at all, is the game's decision.
- **Desktop distribution** is Steam, itch.io, or the desktop channels Orclab already knows (PPA,
  snap, Flathub) — Unity builds a Linux standalone; none of those store ingredients exist yet
  except the Linux ones.

## Sources (live on 2026-09-11)

- Current editor: `https://unity.com/releases/editor/whats-new`
- Pricing and Personal threshold: `https://unity.com/pricing`; Runtime Fee cancellation:
  `https://unity.com/blog/unity-is-canceling-the-runtime-fee`
- Android build process: `https://docs.unity3d.com/Manual/android-BuildProcess.html`;
  requirements: `https://docs.unity3d.com/6000.2/Documentation/Manual/android-requirements-and-compatibility.html`
- iOS build process: `https://docs.unity3d.com/Manual/iphone-BuildProcess.html`
- Privacy manifest: `https://docs.unity3d.com/6000.2/Documentation/Manual/apple-privacy-manifest-policy.html`
- Command line: `https://docs.unity3d.com/6000.2/Documentation/Manual/EditorCommandLineArguments.html`
- Store rules themselves: the Play and App Store ingredients under `skills/orc-package/ingredients/`.
