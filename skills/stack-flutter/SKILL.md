---
name: stack-flutter
description: Background knowledge for any work in a Flutter/Dart project - creating one, building for Android or iOS, configuring signing, versions or permissions, choosing a dependency, or preparing a Google Play or App Store release. Says what the current toolchain is, where things live in the project, and where each store rule lands in the build. Not a command; Claude reads it when Flutter is in play.
user-invocable: false
---

# Flutter (Dart) — the cross-platform mobile stack

**Checked against live sources on 2026-09-11.** Flutter stable **3.47.4** (released that day;
Dart **3.13.3**), from Flutter's own release feed. Every version and default below has a date;
Flutter ships a stable every ~quarter, so anything here older than one is suspect —
`orclab:currency-discipline` says re-check, and the "Sources" section says where.

**Nobody here has shipped a Flutter app yet.** This is researched knowledge, in the sense
BACKLOG #33 defines: verified against the vendor's current docs and source, not against a
release. The first real app corrects it.

## When this is the stack

direflail's settled choice for **cross-platform mobile** (BACKLOG #4, 2026-09-11): one Dart
codebase producing an Android `.aab` and an iOS `.ipa`, both to be shipped — the point is both
stores from one source. Flutter also targets Linux, macOS, Windows and web from the same code,
which matters when a mobile app grows a desktop sibling.

Not this stack: games (Unity or Godot — `stack-unity`, `stack-godot`), and anything that must be
native-only (`stack-android-native`, `stack-ios-native`).

## Toolchain, as of 2026-09-11

| Thing | Current | Where it was read |
|---|---|---|
| Flutter stable | 3.47.4 (2026-09-11) | `storage.googleapis.com/flutter_infra_release/releases/releases_linux.json` — the feed `flutter upgrade` reads |
| Dart | 3.13.3, bundled with Flutter | same |
| Android: default `compileSdk` / `targetSdk` / `minSdk` | **36 / 36 / 24** | `FlutterExtension.kt` on the `stable` branch |
| Android: default NDK | **28.2.13676358** (r28) | same |
| Android: supported API levels | 24–37 | docs.flutter.dev supported platforms |
| iOS: supported versions | 15–26 | same |
| iOS: Swift Package Manager | **on by default since 3.44**; CocoaPods still installed as fallback for plugins that lack SwiftPM support. CocoaPods' registry goes read-only 2026-12-02 | docs.flutter.dev SwiftPM page |
| Android build host | Linux, macOS or Windows; Android Studio (latest stable) with SDK Platform 36, Build-Tools, command-line tools, Platform-Tools, CMake, NDK (side by side); `flutter doctor --android-licenses` | docs.flutter.dev Android setup |
| iOS build host | **macOS only**, latest Xcode (App Store uploads need Xcode 26 / iOS 26 SDK since 2026-04-28), CocoaPods installed | docs.flutter.dev iOS setup; App Store ingredient |

Install: download the SDK, put `flutter/bin` on `PATH`, run `flutter doctor` and fix what it
lists. `flutter doctor` is the check for every row above and is the first thing to run in any
Flutter session on a new machine.

**On this machine (Linux):** Android builds work in full. iOS builds do not — see the App Store
ingredient's `local` / `cloud` choice. Everything in the iOS column below is still *configured*
here, in files under `ios/`; it is only the build that needs a Mac.

## Project layout — where things live

`flutter create --org <reverse.domain> --platforms android,ios <name>` makes:

| Path | What |
|---|---|
| `pubspec.yaml` | Dependencies, assets, and **`version: 1.0.0+1`** — the single source of the app's version. `1.0.0` becomes Android `versionName` and iOS `CFBundleShortVersionString`; `+1` becomes `versionCode` and `CFBundleVersion`. Both stores require the build number to increase on every upload. `/orc-version` should bump this line. |
| `lib/main.dart`, `lib/` | The app. |
| `test/`, `integration_test/` | `flutter test` unit/widget tests; integration tests run on a device or emulator. |
| `analysis_options.yaml` | Lints; `flutter_lints` is the default package. `flutter analyze` is the lint command. |
| `android/app/build.gradle.kts` | `applicationId` (**fixed forever once uploaded to Play**), `minSdk`/`targetSdk`/`compileSdk` (default to `flutter.*` — leave them so they track Flutter), `signingConfigs`. Kotlin DSL is the current template; older projects have `build.gradle`. |
| `android/app/src/main/AndroidManifest.xml` | Permissions, app label, intent filters. |
| `android/key.properties` | Upload-keystore path and passwords — **git-ignored, never committed**. |
| `ios/Runner.xcworkspace` | What Xcode opens. Never `Runner.xcodeproj` directly. |
| `ios/Runner/Info.plist` | Bundle name, permission usage strings (`NS*UsageDescription`), orientation. |
| `ios/Runner/PrivacyInfo.xcprivacy` | **Does not exist in the template** — has to be added (see the App Store row below). |
| `ios/ExportOptions.plist` | Export method and signing for `flutter build ipa`; Xcode writes one the first time you export by hand. |
| `build/` | Outputs. Git-ignored. |

## Build, run, test

```bash
flutter pub get                       # after any pubspec change
flutter analyze && flutter test       # the check before any build
flutter run                           # on whatever `flutter devices` lists
flutter build appbundle --release     # -> build/app/outputs/bundle/release/app-release.aab
flutter build ipa --release --export-options-plist=ios/ExportOptions.plist   # macOS only -> build/ios/ipa/*.ipa
```

Confirm the output filenames with `ls` after the first build rather than trusting this file —
the PPA ingredient learned that lesson with tarball names. Release builds shrink and obfuscate by
default (R8 on Android); `--split-debug-info=<dir>` keeps symbols for crash reports.

Coverage, mutation testing and test lint for this language: `skills/orc-test/languages/dart.md` —
`/orc-test` reads it.

### Building without a Mac

Apple's toolchain runs only on macOS: `flutter build ipa` is Xcode underneath, and there is no iOS
SDK for Linux. A developer on this machine can write, analyze and test the whole app, and build
Android here, but the `.ipa` has to be produced on a Mac somewhere — so a Linux developer rents one
by the minute from a build service. What each service needs from you is the same: a paid Apple
Developer Program membership, and an **App Store Connect API key** (App Store Connect → Users and
Access → Integrations) so the service can talk to Apple on your behalf. The distribution
certificate and provisioning profile are what differ: the default below generates them; GitHub
Actions expects you to hand them over.

**Default: Codemagic** (confirmed live 2026-09-12). Its Flutter quick-start is the whole path in
one file: *"This guide will illustrate all of the necessary steps to successfully build and
publish a Flutter app with Codemagic. It will cover the basic steps such as build versioning, code
signing and publishing."* — and the build step is the same `flutter build ipa --release
--export-options-plist=...` as above, on `instance_type: mac_mini_m2`. Signing: put the API key
in Codemagic's Team settings and *"you can also generate a new Apple Development or Apple
Distribution certificate"* there — the private key never touches this machine — then
`ios_signing: distribution_type: app_store` + `bundle_identifier:` in `codemagic.yaml` fetches the
matching profile from Apple, and `xcode-project use-profiles` applies it before the build.
Upload: `publishing: app_store_connect:` with the same key (`submit_to_testflight` /
`submit_to_app_store`). Cost: *"500 free minutes per month on macOS M2 machines on a personal
account"*, reset on the 1st; beyond that **$0.095/minute** on M2, $0.114 on M4 (free minutes are
not available on a Team). Flutter's own iOS deployment doc points here too (Sources). The App
Store ingredient's `cloud` shape is written for this.

Alternatives (each confirmed live 2026-09-12), with the one thing that would make you reach for it:

- **GitHub Actions macOS runner** — already there if the repo is on GitHub; `macos-latest` is macOS
  26 arm64 with Xcode 26.6 default and 27 on the `xcode-27` preview label. Concern: **signing is
  yours to script** — GitHub's own guide has you export the certificate (`.p12`) and profile,
  base64 them into secrets and import into the runner's keychain; nothing is generated for you.
  And cost: macOS is **$0.062/minute** against $0.006 for Linux. GitHub's pages once documented a
  10x multiplier on included minutes for macOS; the current pages give only the rate table, so
  whether the 2,000 free minutes deplete at the macOS rate is not stated (checked 2026-09-12,
  public repos are free either way).
- **Apple Xcode Cloud** — 25 compute hours/month come with the membership. Concern: *"To get
  started, configure a workflow in Xcode"* — the first setup happens inside Xcode, so it needs a
  Mac once, which is the problem this section exists for.
- **EAS Build (Expo)** — not an option: its prerequisite is *"A React Native Android or iOS
  project"* and its pipeline runs `npm install` and `fastlane gym` in `ios/`. A Flutter project
  has no seat there. (Its intro's *"any native project, whether or not you use Expo"* means bare
  React Native — the next sentence names only React Native's CLIs.)

## Beyond mobile — desktop and web

A project that ticks two families — a phone app that must also be a desktop program, or a
website, or both — is choosing between one codebase that draws the same screens everywhere and
two or three codebases that each use the platform's own widgets. Flutter is the first kind on all
five targets and is the `/orc-code` default on both cross-family rows; this section says how good
each non-phone target actually is, from Flutter's own docs, then the one concern that would move
a project to each alternative.

**Desktop.** docs.flutter.dev's desktop page (dated 2026-07-31, confirmed live 2026-09-12):
*"Flutter provides support for compiling a native Windows, macOS, or Linux desktop app."* The
supported-platforms page (2026-08-12) grades desktop no differently from mobile — Windows 10–11,
macOS 12–26, Debian 10–13 and Ubuntu 20.04–24.04 LTS are all *"Supported: The platforms and
versions that the Flutter team supports"*, Debian 12 and Ubuntu 22.04 CI-tested on every commit;
neither page calls desktop beta. **On Linux the app is a GTK 3 program**: the Linux setup page
(2026-09-10) installs `libgtk-3-dev`, the build page (2026-06-08) says a target machine needs
`libgtk-3-0`, and the engine's `fl_view.h` on `stable` reads *"#FlView is a GTK widget that is
capable of displaying a Flutter application"* (all confirmed live 2026-09-12) — GTK owns the
window, Flutter paints inside it. That is why the Linux tray answer in `## Presence` holds
unchanged: `tray_manager`'s `libayatana-appindicator3` is itself GTK 3, so its
GNOME-needs-the-extension caveat is the whole Linux caveat. Release path: `flutter build linux
--release` gives a `bundle/` directory, and the docs' only Linux distribution guide is the Snap
Store (`deployment/linux`, 2026-07-31); a `.deb` is the packaging ingredient's job, not Flutter's.

**Web.** Flutter paints the page itself rather than building it out of HTML. Two renderers do
that — **CanvasKit** for the JavaScript build, **skwasm** for `flutter build web --wasm` — and
they are the only two: `flutter_tools`' `WebRendererMode` on `stable` has exactly those members,
`defaultForJs = canvaskit`, `defaultForWasm = skwasm` (confirmed live 2026-09-12). The HTML
renderer is gone, and the docs page that described the choice was deleted on 2026-07-23 (*"remove
obsolete renderers page"*); the overview it redirects to says only *"Using a combination of DOM,
Canvas, and WebAssembly"*. What web is for, per that overview (2026-07-23): *"Single Page
Application ... Existing mobile applications"*; what it is not for: *"Not every HTML scenario is
ideally suited for Flutter at this time. For example, text-rich, flow-based, static content such
as blog articles benefit from the document-centric model that the web is built around, rather
than the app-centric services that a UI framework like Flutter can deliver."* The web FAQ
(2026-08-04) is plainer on search — *"application output doesn't align with what search engines
need to properly index"* — and its remedy is to split the product: *"consider separating your
primary application experience (created in Flutter), from your landing page, marketing content,
and help content (created using search engine optimized HTML)."* Text is painted too: *"Flutter
widgets are not selectable by default"* (`SelectionArea` API docs, confirmed live 2026-09-12) —
wrap a screen in `SelectionArea` or select-and-copy does nothing on it. The Wasm build needs two
HTTP headers (`Cross-Origin-Embedder-Policy`, `Cross-Origin-Opener-Policy`) to run multithreaded
and *"can't run on the iOS version of any browser"* (wasm page, 2026-08-18); the JavaScript build
is the one that runs everywhere.

### The two cross-family rows

Both rows keep Flutter as the default because it is the only one of the three stacks whose every
target its own vendor rates Supported or Stable — React Native has no maintained Linux desktop,
and Compose Multiplatform's web is Beta. The concern that moves a project off it, one per
alternative:

- **React Native + React web** (`stack-react-native`, `## React web and desktop`) — choose it
  when the web tick is a website: pages people find through search, read, select from and link
  to. Its web half is React DOM, the web-only row's own stack, so the FAQ's Flutter-plus-HTML
  split above never happens, and the phones get native widgets. What your project gives up: Linux
  desktop (nothing maintained), and Windows and macOS become a bare RN project per OS that trails
  RN by three to six minors.
- **Kotlin Multiplatform + Compose Multiplatform** (`stack-kotlin-multiplatform`, `## Compose
  Multiplatform beyond mobile`) — choose it when the Android app already exists in Kotlin and
  Jetpack Compose, or the team writes Kotlin: the Android half stays as it is, and desktop
  arrives Stable as a JVM app with a tray built in and self-contained `.deb`/`.msi`/`.dmg`
  installers. What your project gives up: a web tick lands on a Beta target, and the iOS half
  needs a Mac exactly as Flutter's does.

**Which to live in, iOS ticked — what the sources imply.** The Mac question is the same for all
three (Codemagic here and for KMP, EAS or Codemagic for RN), so the row turns on the other tick.
If it is web, the docs above make a Flutter web build an application in a canvas whose indexable
pages are written in HTML beside it — one Dart app plus a small HTML site; React Native + React
web is one TypeScript codebase whose website is the same React DOM the web-only row already
builds, with the web-only row's own concern still applying: a content site that must render on
the server (SEO, first paint) moves from Vite to Next.js — see `stack-web`'s `## The stack
decision`. If the other tick is desktop with Linux in it, Flutter is the only
one of the three with a maintained Linux answer. The default stays Flutter because it is the one
stack that covers every combination the row can hold; the RN line above is the one that fires
most often, whenever the web tick means a website.

**Which to live in, iOS not ticked — what the sources imply.** Android plus desktop, web or
both, and no Mac anywhere. Android plus desktop with no web is a close call: Flutter is one
toolchain and one new language (Dart) with every target Supported; Compose Multiplatform's
Android half is the very Jetpack Compose `stack-android-native` already uses, its desktop is
Stable with a tray and installers in the box, and its cost is Gradle and the JVM. The selection
rule keeps Flutter only because CMP is a second toolchain on top of the Android one — unless that
Android toolchain is already there, which is the concern line. Add a web tick and it stops being
close: CMP's web is Beta, so it is Flutter (canvas app plus HTML pages) or React Native (a real
site, no Linux).

## Presence

Presence is how the app stays visible and reachable when it is not in front. On a phone that is
a notification: an icon in the status bar, a card in the notification tray the user can tap,
expand, or act on with buttons. On a desktop it is a tray icon — panel (Linux), notification area
(Windows) or menu bar (macOS) — with a menu, keeping the app alive with no window showing. No
project has been built with these facets yet; the first one corrects them. In Flutter both are
plugins, one per mechanism: **`flutter_local_notifications` 22.3.0** (published 2026-08-08;
Android, iOS, macOS, Linux, Windows, web; 7.3k likes, 2.78M weekly downloads — confirmed live
2026-09-12) for notifications, **`tray_manager` 0.5.3** (2026-06-09; Linux, macOS, Windows; 289
likes, 230k downloads — confirmed live 2026-09-12) for the tray.

### Android

Notifications through `flutter_local_notifications`. What Android lets one do (confirmed live
2026-09-12, developer.android.com, page dated 2026-09-01): *"it first appears as an icon in the
status bar"*, the user opens the drawer to *"view more details and take actions"*; *"A
notification can offer up to three action buttons"*; direct reply (API 24+) *"lets users enter
text directly into the notification"*; Android 13+ needs the `POST_NOTIFICATIONS` runtime
permission. The plugin exposes all of it — actions are set on the notification itself, with a
`showsUserInterface` switch for whether tapping one opens the app or runs a background isolate —
and its 21.0.0 changelog *"bumped `compileSdk` to 36"* (Android 16), its `build.gradle` says
`compileSdk 36`, so it builds against this stack's default (confirmed live 2026-09-12; its README
still reads "35 at a minimum" — the code wins). Actions need its `<receiver>` in the manifest.

### iOS

Same plugin. What iOS lets one do (developer.apple.com UserNotifications, confirmed live
2026-09-12): *"Notifications can display an alert, play a sound, or badge the app's icon"*, and
actionable notifications show *"one or more buttons in addition to the notification interface"*,
declared as categories at launch — which is why the plugin has actions configured in
`initialize` on iOS/macOS, not per notification. **There is no persistent status-bar icon for an
app on iOS**; the framework overview offers alert, sound and badge and nothing else, so the badge
count is the closest thing. The app must ask permission first (the plugin's
`requestAlertPermission` / `requestBadgePermission` / `requestSoundPermission`).

### Linux

`tray_manager` is the tray on Linux, Windows and macOS alike; nothing splits by OS version.
**Linux depends on the desktop environment, not on Flutter**: the plugin is built on
`libayatana-appindicator3` (its README's `apt-get install libayatana-appindicator3-dev`, confirmed
live 2026-09-12) — *"a GTK implementation of the StatusNotifierItem Specification (SNI)"*, its own
README (confirmed live 2026-09-12) — so KDE Plasma and Cinnamon show it natively and GNOME needs
the AppIndicator shell extension — the README says so in its own words: *"In GNOME desktop
environment, the AppIndicator extension may be required to display the icon."* Which distro
preinstalls that extension is in `skills/stack-python-desktop/SKILL.md`'s Presence section and
holds here unchanged — same protocol. The concern that library carries too: its upstream
repository is marked OBSOLETE (`stack-python-desktop`'s Sources record it), so the tray rests on
a library that will stop moving; `nativeapi`, below, is the announced way off it. Desktop
notifications come from the same `flutter_local_notifications`, through freedesktop Desktop
Notifications on Linux (its README, confirmed live 2026-09-12).

### Windows

`tray_manager` for the notification-area icon. Notifications are Windows toasts through
`flutter_local_notifications` — no repeating ones, and `cancel()` only when MSIX-packaged (its
README, confirmed live 2026-09-12).

### macOS

`tray_manager` for the menu-bar icon. Notifications go through UserNotifications from the same
`flutter_local_notifications`, with the permission asks the iOS section describes.

Alternatives, each with the concern that would pick it: `system_tray` 2.0.3 — same three
platforms, but last published 2023-04-19 with a Dart `<3.0.0` SDK bound, so it does not resolve
on Dart 3.13 at all (confirmed live 2026-09-12); only if `tray_manager` breaks and a fork of
`system_tray` is the fix. `nativeapi` 0.2.4 (published 2026-09-12, five platforms, "Work in
Progress" in its own README) is `tray_manager`'s announced successor — its README carries *"This
plugin is being migrated to libnativeapi/nativeapi-flutter"* — and is the choice once it reaches
1.0 or `tray_manager` stops releasing; not before, at 28 likes and 2.11k downloads.

None of the four plugins this section and `## Storage` recommend has had `## Choosing
dependencies`' three store checks run against it; the first real build is the moment.

## UI

No project has been built with these facets yet; the first one corrects them. Flutter draws its
own widgets on every platform; the UI framework is Flutter itself, and the choice is only which
widget set. **Default: Material 3 in a `MaterialApp`, with the `.adaptive()`
constructors where the docs recommend them.** docs.flutter.dev (confirmed live 2026-09-12):
*"Material 3 is the default design language of Flutter, enabling you to design and build
beautiful, usable apps that can adapt to any platform"* — the default since 3.16. Flutter adapts
scrolling physics, page transitions, typography, back navigation and text editing to the platform
on its own; for controls *"tightly integrated with the operating system"* its adaptations page
(dated 2026-05-05) says *"we recommend that you follow platform conventions"* via
`Switch.adaptive()`, `Slider.adaptive()`, `AlertDialog.adaptive()` and the like, which become
Cupertino on iOS. Those adaptive constructors are opt-in per widget, not the default — a plain
`Switch` is Material on both platforms. Cupertino (`CupertinoApp`, 60+ widgets following Apple's
Human Interface Guidelines) is the alternative when the app is iOS-first and must look native
there, at the cost of looking iOS on Android. BACKLOG #2's design system translates into the
frameworks above.

## Storage

No project has been built with these facets yet; the first one corrects them. Storage is what the
app keeps between launches: saved data and config.

**Saved data: `sqflite` 2.4.4** (published 2026-09-10; Android, iOS, macOS — confirmed live
2026-09-12): SQLite, one file, no server, plain SQL; the file lives under `getDatabasesPath()` —
*"the default database directory on Android and the documents directory on iOS/MacOS"* (its
README). It is mobile-only by itself; `sqflite_common_ffi` 2.4.3 (2026-09-10) is the same API on
Linux and Windows. **`drift` 2.35.0** (2026-09-09; with `drift_flutter` 0.3.1, `NativeDatabase`
on Android, iOS, Windows, Linux, macOS, SQLite bundled since 2.32 — its platforms page, confirmed
live 2026-09-12) is the alternative when the schema is large enough to want typed Dart queries
and stream-based reactive reads, at the cost of `build_runner` code generation.

**Config: `shared_preferences` 2.5.5** (published 2026-03-25; Android, iOS, Linux, macOS, Windows,
web — confirmed live 2026-09-12), using the `SharedPreferencesAsync` / `SharedPreferencesWithCache`
API — its README: *"We highly encourage any new users of the plugin to use the newer
SharedPreferencesAsync or SharedPreferencesWithCache APIs instead"*; the old `SharedPreferences`
*"will be deprecated in the future."* Where each platform keeps it, from the README's table:
Android DataStore Preferences (or SharedPreferences); iOS and macOS `NSUserDefaults`; Linux a
file in `XDG_DATA_HOME`; Windows a file in the roaming AppData directory; web LocalStorage.
External databases are out of scope for this skill.

## Where each store rule lands

The two store ingredients (`skills/orc-package/ingredients/play`, `.../app-store`) state the rules
and own them. This table is the other half: for each rule, the file in *this* stack where it is
satisfied, and how to check. When a store changes a rule, the ingredient changes; when Flutter
changes where it lands, this table changes.

### Google Play

| Rule (Play ingredient) | Where it lands in Flutter | Check |
|---|---|---|
| Target API 36 (since 2026-08-31) | `targetSdk = flutter.targetSdkVersion` in `android/app/build.gradle.kts` — **36 by default on 3.47**. Only a project that overrode it is at risk. | `grep -n 'targetSdk' android/app/build.gradle.kts` shows the `flutter.` form, or a literal ≥36 |
| 16 KB page alignment (native code, Android 15+; since 2025-11-01, hard 2027-02-01) | Flutter's engine is native and is built with NDK r28+, so the engine's `.so` files are aligned. **Plugins with their own native code are the risk** — each must be built with a current toolchain. The project's default NDK (r28) covers plugins built from source in the project. | `bundletool dump config --bundle=build/app/outputs/bundle/release/app-release.aab \| grep alignment` → `PAGE_ALIGNMENT_16K`. Run it on the real bundle, after adding any plugin. |
| 64-bit | `flutter build appbundle` includes arm64-v8a by default. | Default; nothing to do. |
| Signed with the upload key | `signingConfigs.release` in `android/app/build.gradle.kts` reading `android/key.properties` (the Flutter deployment doc's exact snippet). | `key.properties` exists, is git-ignored (`git check-ignore android/key.properties`), and a release build does not say "signed with debug key". |
| `applicationId` = Play package name | `defaultConfig.applicationId` in `android/app/build.gradle.kts`. Set with `--org` at create time; changing it later means a new app on Play. | matches the Play ingredient's `__PACKAGE__` |
| Version code increases every upload | `pubspec.yaml` `version: x.y.z+N` — bump `N`. | Play refuses a reused `versionCode`; `/orc-version` should refuse a bump that leaves `+N` unchanged. |
| Data safety form is truthful | Not a file — but the answer is decided by which plugins you add. Any plugin that sends data off-device (analytics, crash reporting, ads) makes the form non-empty. Read each plugin's README before adding it, and keep a list. | `flutter pub deps --style=compact` lists them; answer the form from that list. |
| Account deletion in-app + web | App code (`lib/`) and a public web page. Only if the app creates accounts. | — |
| Permissions declared | `android/app/src/main/AndroidManifest.xml` `<uses-permission>`. Plugins merge their own in; the merged manifest is what Play sees. | `build/app/intermediates/merged_manifests/release/AndroidManifest.xml` after a build, or the App Bundle Explorer in Play Console. |

### Apple App Store

| Rule (App Store ingredient) | Where it lands in Flutter | Check |
|---|---|---|
| Built with Xcode 26 / iOS 26 SDK (since 2026-04-28) | The Mac's Xcode. Flutter 3.47 supports iOS 15–26; `ios/Runner.xcodeproj` deployment target defaults to what Flutter sets (13+ in the deployment doc; raise if a SwiftPM plugin demands it). | On the Mac: `xcodebuild -version` ≥ 26. |
| **Privacy manifest** (`PrivacyInfo.xcprivacy`, rejected at upload if wrong) | **Not in the app template.** Add `ios/Runner/PrivacyInfo.xcprivacy` to the Runner target (Xcode: File → New → App Privacy) declaring the app's own collected data types and required-reason APIs. Flutter's engine ships its own manifest inside `Flutter.framework`; each plugin with native code must ship its own — Apple's ITMS-91061 rejection names the plugin that lacks one. | `ls ios/Runner/PrivacyInfo.xcprivacy`; after an archive, Xcode's Product → Generate Privacy Report shows the merged result. |
| Public APIs only | Flutter and its first-party plugins comply; a third-party plugin is the risk. | Review at upload. |
| Bundle identifier | `PRODUCT_BUNDLE_IDENTIFIER` in `ios/Runner.xcodeproj/project.pbxproj`, set from `--org` at create time; must match the App Store ingredient's `__BUNDLE_ID__` and the identifier registered on the developer site. | `grep -m1 PRODUCT_BUNDLE_IDENTIFIER ios/Runner.xcodeproj/project.pbxproj` |
| Signing (distribution certificate + App Store profile) | Xcode → Runner target → Signing & Capabilities → *Automatically manage signing* with the team selected; `ios/ExportOptions.plist` `method` = `app-store-connect`. On a cloud Mac, the service's signing setup (Codemagic's CLI tools are what Flutter's own iOS deployment doc shows). | A `flutter build ipa` that completes without a signing error. |
| Permission usage strings | `ios/Runner/Info.plist` — every `NS*UsageDescription` for a capability the app or a plugin touches (camera, photos, location, …). Missing one is a crash on first use and a review rejection. | `plutil -p ios/Runner/Info.plist \| grep UsageDescription` |
| Privacy policy reachable in-app (5.1.1(i)) | App code — a link in settings/about. | — |
| Account deletion in-app (5.1.1(v)); private login alongside any social login (4.8) | App code. Sign in with Apple is a capability on the bundle id plus the `sign_in_with_apple` plugin, if the app has any third-party login. | — |
| Build number increases every upload | `pubspec.yaml` `version: x.y.z+N` → `CFBundleVersion`. | App Store Connect refuses a reused build number for the same version. |
| Age rating, App Privacy answers, EU trader status | App Store Connect, not the project. The App Privacy answers are decided by the same plugin list as Play's Data safety form — answer both from one list. | — |

## Choosing dependencies

`pub.dev` is the registry; `flutter pub add <package>` adds one. Before adding any plugin with
native code, check three things because each is a store rule above: does it ship an iOS privacy
manifest (its `ios/` or `darwin/` directory has `PrivacyInfo.xcprivacy`); is it built for 16 KB
pages (recent release, current NDK — or run the `bundletool` check after adding it); and what it
sends off-device (the Data safety / App Privacy answers). `orclab:currency-discipline` applies to
the version: `flutter pub outdated` shows what is current.

**Deliberately not decided here** — ask, per `/orc-code`'s rule against inventing defaults: state
management, navigation package, HTTP client, backend. These are project choices and this file
records no preference until direflail has one. Local storage is decided — see `## Storage` above.

## Games

Not this stack. A Flutter app that grows a game is a Unity or Godot project embedded or beside it;
that is `stack-unity`'s or `stack-godot`'s concern.

## Sources (live on 2026-09-11; facets and no-Mac builds 2026-09-12)

- Current release and Dart version: `https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json`
- Android defaults: `https://raw.githubusercontent.com/flutter/flutter/stable/packages/flutter_tools/gradle/src/main/kotlin/FlutterExtension.kt`
- App template contents (no `PrivacyInfo.xcprivacy` under `templates/app/ios.tmpl/Runner`; plugin templates have one): `https://github.com/flutter/flutter/tree/stable/packages/flutter_tools/templates`
- Android deployment: `https://docs.flutter.dev/deployment/android`
- iOS deployment: `https://docs.flutter.dev/deployment/ios`
- Supported platforms: `https://docs.flutter.dev/reference/supported-platforms`
- Swift Package Manager: `https://docs.flutter.dev/packages-and-plugins/swift-package-manager/for-app-developers`
- Android setup: `https://docs.flutter.dev/platform-integration/android/setup`; iOS setup: `https://docs.flutter.dev/platform-integration/ios/setup`
- Privacy manifest tracking in Flutter: `https://github.com/flutter/flutter/issues/143232`
- Store rules themselves: the Play and App Store ingredients under `skills/orc-package/ingredients/`, each with its own sources.
- Facets (2026-09-12) — notifications: `https://pub.dev/packages/flutter_local_notifications` (+ `/versions`, and `https://pub.dev/api/packages/flutter_local_notifications` for exact dates), README and CHANGELOG at `https://raw.githubusercontent.com/MaikuB/flutter_local_notifications/master/flutter_local_notifications/README.md`, `.../CHANGELOG.md`, `.../android/build.gradle`; Android: `https://developer.android.com/develop/ui/compose/notifications` (where `.../develop/ui/views/notifications` redirects), `https://developer.android.com/develop/ui/compose/notifications/create-notification` (where `.../views/notifications/build-notification` redirects); Apple: `https://developer.apple.com/documentation/usernotifications`, `https://developer.apple.com/documentation/usernotifications/declaring-your-actionable-notification-types` (read via `developer.apple.com/tutorials/data/documentation/usernotifications.json` — the HTML page is script-rendered)
- Facets — tray: `https://pub.dev/packages/tray_manager` (+ `/versions`, `/changelog`), `https://raw.githubusercontent.com/leanflutter/tray_manager/main/README.md`; `https://pub.dev/packages/system_tray` (+ `/versions`); `https://pub.dev/packages/nativeapi`; `https://github.com/AyatanaIndicators/libayatana-appindicator`; exact dates and SDK bounds from `https://pub.dev/api/packages/<name>`
- Facets — UI: `https://docs.flutter.dev/ui/widgets/material`, `https://docs.flutter.dev/ui/widgets/cupertino`, `https://docs.flutter.dev/ui/adaptive-responsive/platform-adaptations`
- Building without a Mac (2026-09-12) — Codemagic: `https://docs.codemagic.io/yaml-quick-start/building-a-flutter-app/`, `https://docs.codemagic.io/yaml-code-signing/signing-ios/`, `https://docs.codemagic.io/yaml-publishing/app-store-connect/`, `https://docs.codemagic.io/billing/pricing/`; GitHub Actions: `https://docs.github.com/en/actions/reference/runners/github-hosted-runners`, `https://docs.github.com/en/billing/managing-billing-for-your-products/about-billing-for-github-actions`, `https://docs.github.com/en/billing/reference/actions-runner-pricing`, `https://docs.github.com/en/actions/how-tos/deploy/deploy-to-third-party-platforms/sign-xcode-applications`, image contents `https://github.com/actions/runner-images/blob/main/images/macos/macos-26-arm64-Readme.md` and `https://github.com/actions/runner-images/blob/main/README.md`; Xcode Cloud: `https://developer.apple.com/xcode-cloud/`; EAS (why it is not an option): `https://docs.expo.dev/build/setup/`, `https://docs.expo.dev/build/introduction/`, `https://docs.expo.dev/build-reference/limitations/`, `https://docs.expo.dev/build-reference/ios-builds/`
- Beyond mobile (2026-09-12) — desktop: `https://docs.flutter.dev/platform-integration/desktop`, `https://docs.flutter.dev/platform-integration/linux/setup`, `https://docs.flutter.dev/platform-integration/linux/building`, `https://docs.flutter.dev/deployment/linux`, the embedder header `https://raw.githubusercontent.com/flutter/flutter/stable/engine/src/flutter/shell/platform/linux/public/flutter_linux/fl_view.h`; web: `https://docs.flutter.dev/platform-integration/web`, `https://docs.flutter.dev/platform-integration/web/faq`, `https://docs.flutter.dev/platform-integration/web/wasm`, `https://docs.flutter.dev/platform-integration/web/initialization`, renderer defaults in `https://raw.githubusercontent.com/flutter/flutter/stable/packages/flutter_tools/lib/src/web/compile.dart`, the renderers-page removal via `https://api.github.com/repos/flutter/website/commits?path=sites/docs/src/content/platform-integration/web/renderers.md`, `https://api.flutter.dev/flutter/material/SelectionArea-class.html`
- Facets — storage: `https://pub.dev/packages/sqflite`, `https://raw.githubusercontent.com/tekartik/sqflite/master/sqflite/README.md`, `https://pub.dev/packages/sqflite_common_ffi`, `https://pub.dev/packages/drift`, `https://drift.simonbinder.eu/setup/`, `https://drift.simonbinder.eu/platforms/`, `https://pub.dev/packages/shared_preferences`, `https://raw.githubusercontent.com/flutter/packages/main/packages/shared_preferences/shared_preferences/README.md`
