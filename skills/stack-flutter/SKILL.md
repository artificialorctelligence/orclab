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

Not this stack: games (Unity or Godot — their own stack skills, when written), and anything that
must be native-only (Kotlin/Android or Swift/iOS skills, when written).

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

### Linux, Windows, macOS

`tray_manager` is the tray on all three; nothing splits by OS version. **Linux depends on the
desktop environment, not on Flutter**: the plugin is built on `libayatana-appindicator3` (its
README's `apt-get install libayatana-appindicator3-dev`, confirmed live 2026-09-12), — *"a GTK
implementation of the StatusNotifierItem Specification (SNI)"*, its own README (confirmed live
2026-09-12) — so KDE Plasma and Cinnamon show it natively and GNOME
needs the AppIndicator shell extension — the README says so in its own words: *"In GNOME
desktop environment, the AppIndicator extension may be required to display the icon."* Which distro
preinstalls that extension is in `skills/stack-python-desktop/SKILL.md`'s Presence section and
holds here unchanged — same protocol. Desktop notifications come from the same
`flutter_local_notifications`: freedesktop Desktop Notifications on Linux, toasts on Windows (no
repeating ones; `cancel()` only when MSIX-packaged), UserNotifications on macOS — per its README
(confirmed live 2026-09-12).

Alternatives, each with the concern that would pick it: `system_tray` 2.0.3 — same three
platforms, but last published 2023-04-19 with a Dart `<3.0.0` SDK bound, so it does not resolve
on Dart 3.13 at all (confirmed live 2026-09-12); only if `tray_manager` breaks and its fork is
the fix. `nativeapi` 0.2.4 (published 2026-09-12, five platforms, "Work in Progress" in its own
README) is `tray_manager`'s announced successor — its README carries *"This plugin is being
migrated to libnativeapi/nativeapi-flutter"* — and is the choice once it reaches 1.0 or
`tray_manager` stops releasing; not before, at 28 likes and 2.11k downloads.

## UI

Flutter draws its own widgets on every platform; the UI framework is Flutter itself, and the
choice is only which widget set. **Default: Material 3 in a `MaterialApp`, with the `.adaptive()`
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
that is the game stacks' concern when they are written.

## Sources (live on 2026-09-11; facets 2026-09-12)

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
- Facets — storage: `https://pub.dev/packages/sqflite`, `https://raw.githubusercontent.com/tekartik/sqflite/master/sqflite/README.md`, `https://pub.dev/packages/sqflite_common_ffi`, `https://pub.dev/packages/drift`, `https://drift.simonbinder.eu/setup/`, `https://drift.simonbinder.eu/platforms/`, `https://pub.dev/packages/shared_preferences`, `https://raw.githubusercontent.com/flutter/packages/main/packages/shared_preferences/shared_preferences/README.md`
