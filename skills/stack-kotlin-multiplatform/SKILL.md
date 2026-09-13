---
name: stack-kotlin-multiplatform
description: Background knowledge for any work in a Kotlin Multiplatform (KMP) project - one Kotlin module holding the app's logic, used by a native Jetpack Compose app on Android and a native SwiftUI app on iOS, or with Compose Multiplatform drawing both; creating one, turning an Android-only Kotlin app into one, building the iOS framework, choosing a storage library, or preparing a store release. Says what the current toolchain is, where things live in the project, and where each store rule lands in the build. Not a command; Claude reads it when Kotlin Multiplatform is in play.
user-invocable: false
---

# Kotlin Multiplatform — shared logic, native UI on each side

No project has been built with this yet; the first one corrects it.

**Checked against live sources on 2026-09-12.** Kotlin **2.4.20**, Compose Multiplatform **1.12.0**
(2026-08-25), Room 3 **3.0.3** (2026-09-09). The KMP Gradle plugin *is* Kotlin, so anything here
older than one Kotlin tooling release (three months) is suspect — `orclab:currency-discipline` says
re-check, "Sources" says where.

## When this is the stack

An app that must ship on both Android and iOS, written so that the part with no screen in it —
validation, data, networking, the rules of the app — exists once, in Kotlin, and each phone runs its
own native screens on top: Jetpack Compose on Android, SwiftUI on iOS. Google's page (confirmed live
2026-09-12, dated 2026-08-27): *"Kotlin Multiplatform (KMP) is officially supported by Google for
sharing business logic between Android and iOS. Kotlin Multiplatform is stable and
production-ready."* It is the **alternative, not the default**, on two rows of `/orc-code`'s
Defaults Table — *Android + iOS, nothing else* and *two or more of desktop / mobile / web, iOS
ticked* — where Flutter is the default. Reach for it when both UIs must be truly native, or when
there is already an Android app in Kotlin. The UI halves *are*
`skills/stack-android-native/SKILL.md` and `skills/stack-ios-native/SKILL.md`; this file covers only
the shared module and the seam between it and them.

**The migration path from an Android-only Kotlin app, and the day-one answer.** kotlinlang.org's
guide *Make your Android application work on iOS* (confirmed live 2026-09-12, dated 2026-07-21) is
three moves: add a module with Android Studio's **Kotlin Multiplatform Shared Module** wizard;
*"Move the business logic code ... from the `app` directory to the ... `shared/src/commonMain`
directory"* as a package move; then *"Remove Android-specific code by replacing it with
cross-platform Kotlin code"* (its sample: three JVM-only calls, one becoming an `expect fun` with an
`actual` per platform). Its rule for what to share: *"share what you want to reuse as much as
possible. The business logic is often the same for both Android and iOS, so it's a great candidate
for reuse."* The cost of converting is the number of `android.*` and `java.*` imports in the logic.
**Recommendation for the Android-only row (confirmed live 2026-09-12): start KMP-shaped — business
logic in its own Gradle module importing nothing from `android.*` or `java.*`; add the shared module
the day iOS is decided, one wizard and one package move.** Not the shared module itself from day
one: it pins AGP to Kotlin's compatibility table (below) for no gain yet.

## Toolchain, as of 2026-09-12

| Thing | Current | Where it was read |
|---|---|---|
| Kotlin, and with it the KMP Gradle plugin `org.jetbrains.kotlin.multiplatform` | **2.4.20** — *"the Kotlin Multiplatform Gradle plugin (same as the Kotlin version in your project)"* | kotlinlang.org compatibility guide; releases page |
| What 2.4.20 is compatible with | Gradle 7.6.3–9.7.0; **Android Gradle Plugin 8.5.2–9.3.1**; **Xcode 26.4** | compatibility guide's table (confirmed live 2026-09-12) |
| Android target in the shared module | Google's `com.android.kotlin.multiplatform.library` plugin, `androidLibrary {}` block — the older `androidTarget` name is deprecated since Kotlin 2.3.0 | compatibility guide; the integrate-existing-app tutorial's snippet |
| IDE | **Default: Android Studio** — already installed for the Android half, *"another stable solution for Kotlin Multiplatform"*, needs ≥ Otter 2025.2.1 plus the **Kotlin Multiplatform IDE plugin** (iOS run/debug, preflight checks). Alternative: **IntelliJ IDEA** (≥ 2025.2.2), which JetBrains lists first as *"full Kotlin Multiplatform support"* — the concern is *"specific updates may not be released simultaneously"*, so a KMP-tooling feature missing in Studio is the reason to open IDEA. **Fleet is gone**: JetBrains' blog (2025-02) *"will no longer be releasing a standalone IDE for KMP"*. | recommended-IDEs page (dated 2026-01-27); quickstart; JetBrains blog |
| iOS half | *"To create iOS applications, you need a macOS host with Xcode installed. Your IDE will run Xcode under the hood to build iOS frameworks."* Everything in `stack-ios-native`'s "The Mac requirement" holds; App Store minimum is its Xcode 26. | quickstart (dated 2026-07-21) |
| Compose Multiplatform (only if UI is shared) | 1.12.0 → Jetpack Compose 1.12.0 on Android; *"always compatible with the latest version of Kotlin"*; release *"usually 1–3 months"* behind Jetpack Compose | compatibility-and-versions page (dated 2026-08-25) |

**Two things this table says that the native skills do not (confirmed live 2026-09-12):** AGP tops
out at **9.3.1** while `stack-android-native` runs 9.4.0 — a KMP project holds AGP there until
Kotlin's table moves (create-first-app tutorial: *"Kotlin Multiplatform is not compatible with the
latest AGP version"*); and Xcode is **26.4** while `stack-ios-native` names the 27 RC — use 26 until
27 appears there.

Install: Android Studio per `stack-android-native`, the Kotlin Multiplatform IDE plugin,
`ANDROID_HOME` set; on the Mac, Xcode per `stack-ios-native`, launched once by hand after every
update (the quickstart says so). The plugin's preflight checks are the check.

## Project layout — where things live

The project wizard (*Kotlin Multiplatform*, Android + iOS, **Do not share UI**) and the
shared-module wizard both make KMP's own layout (project-structure page, confirmed live 2026-09-12):

| Path | What |
|---|---|
| `shared/build.gradle.kts` | Targets (`androidLibrary {}`, `iosArm64()`, `iosSimulatorArm64()`, `iosX64()`), each iOS target's `binaries.framework { baseName = "sharedKit" }` — the framework name Swift imports — and per-source-set dependencies. |
| `shared/src/commonMain/kotlin/` | The logic. Compiles to every target; *"you can't use the `java.io.File` dependency from the common code"* — the compiler refuses JDK and Android APIs here. Only multiplatform libraries (klibs.io indexes them). |
| `shared/src/androidMain/kotlin/`, `shared/src/iosMain/kotlin/` | `actual` implementations for `expect` declarations in common code, and anything that must touch a platform API. |
| `shared/src/commonTest/kotlin/` | Tests of the logic, `kotlin.test` — *"The `commonTest` source set stores all common tests"*; run per target, on the JVM/Android here and Kotlin/Native's own runner for iOS on a Mac. |
| `androidApp/` (or the existing `app/`) | The native Android app of `stack-android-native`, with `implementation(project(":shared"))`. Unchanged otherwise. |
| `iosApp/` | The native Xcode project of `stack-ios-native`. Consumes the shared module as an iOS framework — never Kotlin directly. |

**How iOS consumes the module — default: direct integration** (iOS-integration-methods page,
confirmed live 2026-09-12): a Run Script build phase in Xcode (before *Compile Sources*, sandboxing
off) running `./gradlew :shared:embedAndSignAppleFrameworkForXcode`. *"If you use the Kotlin
Multiplatform IDE plugin, direct integration is applied by default"*. Alternatives, each with the
one concern that picks it: **SwiftPM with a local package** — the iOS project already uses Swift
packages and has *"no irreplaceable CocoaPods dependencies"*; **CocoaPods** — only if *"you import
CocoaPods dependencies in your Kotlin Multiplatform project"*, and CocoaPods' registry goes
read-only 2026-12-02 (`stack-ios-native`); **remote XCFramework via SwiftPM** — the iOS app lives in
another repository and wants the shared code *"like a regular third-party dependency"*. One shared
module — *"Works great as a starting point"* (project-configuration page) — until it hurts.

## Build, run, test

```bash
./gradlew :shared:check                    # commonTest, run for the Android target on Linux — check is Gradle's lifecycle task and runs whatever the module registers
./gradlew :androidApp:bundleRelease        # the Android skill's build, unchanged
xcodebuild -scheme iosApp -configuration Release -archivePath build/iosApp.xcarchive archive   # Mac only; runs Gradle for the framework — confirm the scheme name with `xcodebuild -list`
```

From Linux the shared module and the Android app build in full; the iOS framework needs Xcode on a
Mac, so `stack-ios-native`'s "Building without a Mac" applies unchanged — Codemagic's KMP
quick-start (*"build and publish a Kotlin Multiplatform Mobile app"*, confirmed live 2026-09-12)
runs the same `xcode-project build-ipa` inside `iosApp/`. Coverage, mutation testing and test lint:
`skills/orc-test/languages/kotlin.md` (shared module, Android app) and
`skills/orc-test/languages/swift.md` (iOS app) — `/orc-test` reads them.

## Presence

Presence is how the app stays visible and reachable when it is not in front — a notification on
either phone, on iOS also a Live Activity. **The shared module has no presence of its own**: no
screen, no notification API; common code cannot reach `NotificationCompat` or `UserNotifications`.
Each platform's mechanism is the native skill's, unchanged — `stack-android-native`'s `## Presence`
and `stack-ios-native`'s `## Presence`. The shared module may decide *that* and *what* to notify;
posting it is platform code.

## UI

The UI is what the user sees and touches; here the choice is whether each phone draws its own.
**Default: native on each side** — Jetpack Compose in the Android app, SwiftUI in the iOS app, as
the two native skills describe, the shared module below both. That is the wizard's *"Do not share UI
option to keep the UI native"* (create-first-app tutorial, confirmed live 2026-09-12).
**Alternative: Compose Multiplatform on both** — JetBrains' toolkit that *"extends Google's Jetpack
Compose toolkit for Android by supporting additional target platforms"* (its
relationship-to-Jetpack-Compose page). kotlinlang.org's stability page (dated 2025-09-10, confirmed
live 2026-09-12) rates it **iOS: Stable**. The concern that decides: Google's page says only that
*"developers can also share UI across platforms"* and nothing about its readiness; the screens are
Compose's, not SwiftUI's, so they look and behave native only as far as the app makes them; and each
release lands *"usually 1–3 months"* after the Jetpack Compose it tracks. Choose it when one UI
codebase outweighs native feel — usually a desktop or web target on the same row. BACKLOG #2's
design system translates into the frameworks above.

## Compose Multiplatform beyond mobile

A project that ticks phones plus a desktop or a website is choosing between one drawn UI on every
platform and a native UI per platform; on the two cross-family rows of `/orc-code`'s Defaults
Table this stack is the alternative that keeps everything in Kotlin — the shared module below,
Compose Multiplatform drawing every screen — and Flutter is the default (the comparison lives in
`stack-flutter`'s `## Beyond mobile — desktop and web`). kotlinlang.org's supported-platforms page
(dated 2025-09-10, confirmed live 2026-09-12) rates the UI framework per target — *"Android
Stable iOS Stable Desktop (JVM) Stable Web based on Kotlin/Wasm Beta"* — and defines the words:
Stable means *"you can use it even in the most conservative of scenarios"*, Beta *"It's almost done,
so user feedback is especially important now."* **Desktop is a JVM program**: *"Compose
Multiplatform targets the JVM"* (its README, confirmed live 2026-09-12), and the Gradle plugin's
`nativeDistributions` block builds *"self-contained, installable binaries that include all the
necessary Java runtime components, without requiring a JDK to be installed on the target system"*
— `.deb`/`.rpm`, `.msi`/`.exe`, `.dmg`/`.pkg`, through jpackage on JDK 17 or newer
(native-distribution page, dated 2026-08-25, confirmed live 2026-09-12). Presence is in the box: the `Tray()` composable and
`TrayState.sendNotification()` (tray page, dated 2026-08-18, confirmed live 2026-09-12) sit on `java.awt.SystemTray`
(`Tray.desktop.kt` on `jb-main`), so *"Not every desktop environment has a system tray"* — check
`isTraySupported` first. Web compiles through Kotlin/Wasm, itself *"still in Beta"* (Kotlin/Wasm
overview, dated 2026-09-01, confirmed live 2026-09-12).

**The concern that picks it over Flutter:** the Android app already exists in Kotlin and Jetpack
Compose, or the team writes Kotlin — the Android half does not change, and desktop arrives Stable
with installers and a tray and no plugin to vet. What the project accepts: a web tick lands on a
Beta target, and the iOS half still needs a Mac (Codemagic, above). With no Kotlin in the
building, the row's default stands.

## Storage

Storage is what the app keeps between launches: records (a database) and settings (config); both
live in common code. **Saved data: Room 3 over the bundled SQLite** — `androidx.room3:room3-runtime`
+ `androidx.sqlite:sqlite-bundled` in `commonMain`, `room3-compiler` through KSP per target,
`@Database`/`@Dao`/`@Entity` in common code, only the database *path* per platform
(`Context.getDatabasePath` on Android, `NSDocumentDirectory` on iOS) — Google's KMP Room page
(confirmed live 2026-09-12, dated 2026-08-26); the same Room 3 the Android skill picks.
`BundledSQLiteDriver` *"is the recommended driver"* — one SQLite on both phones. Alternative:
**SQLDelight 2.3.2** (2026-03-16) — *"generates typesafe Kotlin APIs from your SQL statements"* —
the concern that picks it is wanting the schema written as SQL, or a target Room does not ship
(web).

**Config: Preferences DataStore** — `androidx.datastore:datastore-preferences-core` **1.2.1** in
`commonMain`, with the file path per platform; *"Only DataStore Preferences is supported in KMP
projects"* (Google's KMP DataStore page, confirmed live 2026-09-12); the Android skill's own pick.
Alternative: **`multiplatform-settings` 1.3.0** (2024-11-29, no release since — confirmed live
2026-09-12), which wraps `SharedPreferences` on Android and `NSUserDefaults` on iOS; the concern
that picks it is a SwiftUI screen that must read the same values through `UserDefaults` /
`@AppStorage`, the iOS skill's own config store. External databases are out of scope here.

## Where each store rule lands

The shared module changes nothing in either table. `stack-android-native`'s *Where each Play rule
lands* holds for `androidApp/` — target SDK, signing, `applicationId`, version code are in the app's
`build.gradle.kts`, not in `shared/`. `stack-ios-native`'s *Where each App Store rule lands* holds
for `iosApp/`. Two seams: the Xcode script phase signs the Kotlin framework (*"Handles the code
signing process of the embedded framework"*, direct-integration page), and a required-reason API a
multiplatform library calls on iOS goes in the *app's* `PrivacyInfo.xcprivacy` (Kotlin's docs have a
*Privacy manifest for iOS apps* page). Versions stay one per app; `/orc-version` bumps both.

## Sources (live on 2026-09-12)

- Google's status and library table: `https://developer.android.com/kotlin/multiplatform`; Room 3 releases: `https://developer.android.com/jetpack/androidx/releases/room3`; add to an existing project: `https://developer.android.com/kotlin/multiplatform/migrate`; Room: `https://developer.android.com/kotlin/multiplatform/room`; DataStore: `https://developer.android.com/kotlin/multiplatform/datastore`
- Migration guide (day-one answer): `https://kotlinlang.org/docs/multiplatform/multiplatform-integrate-in-existing-app.html`
- Toolchain: `https://kotlinlang.org/docs/multiplatform/multiplatform-compatibility-guide.html`, `https://kotlinlang.org/docs/releases.html`, `https://kotlinlang.org/docs/multiplatform/quickstart.html`, `https://kotlinlang.org/docs/multiplatform/recommended-ides.html`, `https://blog.jetbrains.com/kotlin/2025/02/kotlin-multiplatform-tooling-shifting-gears/` (Fleet)
- Layout, tests and iOS consumption: `https://kotlinlang.org/docs/multiplatform/multiplatform-discover-project.html`, `https://kotlinlang.org/docs/multiplatform/multiplatform-run-tests.html`, `https://kotlinlang.org/docs/multiplatform/multiplatform-privacy-manifest.html`, `https://kotlinlang.org/docs/multiplatform/multiplatform-create-first-app.html`, `https://kotlinlang.org/docs/multiplatform/multiplatform-ios-integration-overview.html`, `https://kotlinlang.org/docs/multiplatform/multiplatform-direct-integration.html`, `https://kotlinlang.org/docs/multiplatform/multiplatform-project-configuration.html`
- UI: `https://kotlinlang.org/docs/multiplatform/supported-platforms.html`, `https://kotlinlang.org/docs/multiplatform/compose-multiplatform-and-jetpack-compose.html`, `https://kotlinlang.org/docs/multiplatform/compose-compatibility-and-versioning.html`
- Beyond mobile (2026-09-12): `https://kotlinlang.org/docs/multiplatform/compose-native-distribution.html`, `https://kotlinlang.org/docs/multiplatform/compose-desktop-tray.html`, `https://kotlinlang.org/docs/wasm-overview.html`, `https://raw.githubusercontent.com/JetBrains/compose-multiplatform/master/README.md`, `https://raw.githubusercontent.com/JetBrains/compose-multiplatform-core/jb-main/compose/ui/ui/src/desktopMain/kotlin/androidx/compose/ui/window/Tray.desktop.kt`
- Storage: `https://kotlinlang.org/docs/multiplatform/multiplatform-ktor-sqldelight.html`, `https://sqldelight.github.io/sqldelight/latest/`, `https://api.github.com/repos/sqldelight/sqldelight/releases/latest`, `https://raw.githubusercontent.com/russhwolf/multiplatform-settings/main/README.md`, `https://api.github.com/repos/russhwolf/multiplatform-settings/releases/latest`
- Building without a Mac: `https://docs.codemagic.io/yaml-quick-start/building-a-kmm-app/`. Store rules themselves: the two native skills' tables and `skills/orc-package/ingredients/`.
