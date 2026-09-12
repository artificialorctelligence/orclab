---
name: stack-android-native
description: Background knowledge for any work in a native Android project (Kotlin, Jetpack Compose, Gradle) - creating one, building a release bundle, configuring signing, versions, SDK levels or permissions, choosing a library, or preparing a Google Play release. Says what the current toolchain is, where things live in the project, and where each Play rule lands in the build. Not a command; Claude reads it when native Android is in play.
user-invocable: false
---

# Android native — Kotlin + Jetpack Compose

**Checked against live sources on 2026-09-11.** Kotlin **2.4.20** (2026-09-07), Compose BOM
**2026.08.00**, Android Gradle Plugin **9.4.0** (2026-09), Android Studio **2026.1.4**. Google
ships Compose monthly and AGP roughly quarterly; treat anything here older than one Android
Studio release as suspect — `orclab:currency-discipline` says re-check, and "Sources" says where.

**Nobody here has shipped a native Android app yet.** Researched knowledge in BACKLOG #33's sense:
verified against Google's current docs, not against a release. The first real app corrects it.

## When this is the stack

direflail's choice for **native Android** (BACKLOG #4, 2026-09-11) — wanted *alongside* Flutter,
not instead of it. It is the right stack when the app is Android-only, or needs something
Flutter's plugin ecosystem does not reach (deep platform integration, a system-level feature, a
first-party Google library with no Flutter binding). Google's own words: *"Jetpack Compose is the
modern toolkit for building Android UI."* Views/XML is the older toolkit; Compose is what a new
project uses.

If the same app must also ship on iOS, the honest answers are Flutter (`stack-flutter`) or
Kotlin Multiplatform for shared logic with a native SwiftUI front end — Google calls KMP *"stable
and production-ready"* for **business logic**, and does *not* say that of Compose Multiplatform's
iOS UI. Neither KMP nor CMP is a decided stack here.

## Toolchain, as of 2026-09-11

| Thing | Current | Where it was read |
|---|---|---|
| Android Studio | 2026.1.4 ("Quail 4") | developer.android.com/studio |
| Android Gradle Plugin | 9.4.0; needs Gradle ≥ 9.6.0, **JDK 17** or newer, Build-Tools ≥ 36.0.0; default NDK 28.2.13676358; supports up to API 37 | AGP release notes |
| Kotlin | 2.4.20 | kotlinlang.org releases |
| Compose | BOM 2026.08.00 → `compose.ui` 1.12.0, `material3` 1.4.0; the Compose *compiler* is the Gradle plugin `org.jetbrains.kotlin.plugin.compose`, **versioned with Kotlin** since 2.0 (no separate compiler version to manage) | Compose BOM mapping; Compose compiler page |
| Target / compile SDK | **36** (Play requires targeting 36 since 2026-08-31); Android Studio's new-project wizard sets it | Play ingredient; AGP notes |
| Architecture Google recommends | UI layer (Compose + `ViewModel` state holders) → optional domain layer → data layer (repositories); unidirectional data flow; Kotlin coroutines and `Flow`; Hilt for dependency injection; a single source of truth per datum. Reference app: *Now in Android*. | developer.android.com/topic/architecture |
| Build host | Linux, macOS or Windows. **This machine builds Android in full.** | — |

Install: Android Studio (it bundles a JDK, the SDK manager and the emulator); from the SDK
manager take Platform 36, Build-Tools, command-line tools, Platform-Tools, and — only if
anything in the project has native code — CMake and NDK. Accept licences once
(`sdkmanager --licenses`). Command-line builds need `ANDROID_HOME` (or `local.properties`'s
`sdk.dir`) and a JDK 17+ on `PATH`.

## Project layout — where things live

Android Studio's "Empty Activity" (Compose) template makes:

| Path | What |
|---|---|
| `settings.gradle.kts`, `build.gradle.kts` (root) | Plugin versions come from the **version catalog** `gradle/libs.versions.toml` — that file is where Kotlin, AGP, Compose BOM and every library version live. Bump versions there, nowhere else. |
| `app/build.gradle.kts` | `namespace`, `defaultConfig { applicationId, minSdk, targetSdk, versionCode, versionName }`, `buildTypes.release` (R8 `isMinifyEnabled`), `signingConfigs`. `compileSdk` at the `android {}` level. |
| `app/src/main/AndroidManifest.xml` | Permissions, the launcher `<activity>`, app label and icon. Libraries merge their own manifests in; the merged one is what Play sees. |
| `app/src/main/java/<package>/` | Kotlin sources (the directory is still called `java`). `MainActivity.kt` calls `setContent { ... }`. |
| `app/src/main/res/` | Resources: strings, icons (`mipmap-*`), themes. Compose apps still put strings and icons here. |
| `app/src/test/`, `app/src/androidTest/` | JVM unit tests (`./gradlew test`); instrumented and Compose UI tests on a device/emulator (`./gradlew connectedAndroidTest`). |
| `keystore.properties` (project root) | Upload-keystore path and passwords — **git-ignored, never committed** (the exact snippet is in Google's app-signing page and reproduced in the table below). |
| `local.properties` | SDK path. Git-ignored. |
| `app/build/` | Outputs. Git-ignored. |

## Build, run, test

```bash
./gradlew lint test                  # the check before any build
./gradlew installDebug               # onto whatever `adb devices` lists
./gradlew bundleRelease              # -> app/build/outputs/bundle/release/app-release.aab
```

Confirm the output filename with `ls` after the first build rather than trusting this file. R8
shrinking/obfuscation is on when `isMinifyEnabled = true` in the release build type — the template
ships it off; turn it on and keep `proguard-rules.pro` for anything reflection-based. Keep the
`mapping.txt` R8 writes (`app/build/outputs/mapping/release/`) — Play Console takes it so crash
traces are readable.

## Where each Play rule lands

The Play ingredient (`skills/orc-package/ingredients/play`) states the rules and owns them. This
table is the other half.

| Rule (Play ingredient) | Where it lands | Check |
|---|---|---|
| Target API 36 (since 2026-08-31) | `targetSdk = 36` in `app/build.gradle.kts` `defaultConfig`, and `compileSdk = 36`. Nothing tracks this for you — the number is literal, so **every August** it needs bumping when Google moves the requirement. | `grep -n 'targetSdk\|compileSdk' app/build.gradle.kts` |
| 16 KB page alignment (native code, Android 15+; since 2025-11-01, hard 2027-02-01) | A pure Kotlin app has no native code and is compliant by construction. The risk is a dependency with `.so` files (a media, ML, database or crash-reporting SDK). AGP 9.4's default NDK r28 handles anything the project itself compiles; a prebuilt dependency must be a release built for 16 KB. | `bundletool dump config --bundle=app/build/outputs/bundle/release/app-release.aab \| grep alignment` → `PAGE_ALIGNMENT_16K`; Play Console's App Bundle Explorer also reports it. |
| 64-bit | Only relevant with native code; the NDK builds arm64-v8a by default. | Default. |
| Signed with the upload key | `signingConfigs.create("release")` reading `keystore.properties`, assigned to `buildTypes.release.signingConfig` — Google's own snippet: ```val keystoreProperties = Properties().apply { load(FileInputStream(rootProject.file("keystore.properties"))) }``` then `keyAlias`, `keyPassword`, `storeFile = file(...)`, `storePassword` from it. | `git check-ignore keystore.properties` succeeds; `bundleRelease` does not warn about a debug key. |
| `applicationId` = Play package name | `defaultConfig.applicationId`. **Fixed forever once uploaded.** `namespace` is separate (code packaging) and may differ. | matches the Play ingredient's `__PACKAGE__` |
| Version code increases every upload | `defaultConfig.versionCode` (integer) and `versionName` (string). Literal values in the build file — `/orc-version` needs to edit both, and refuse a bump that leaves `versionCode` unchanged. | Play refuses a reused `versionCode`. |
| Data safety form is truthful | Decided by dependencies: any library that sends data off-device (Firebase Analytics/Crashlytics, ads, Play Services with telemetry). Keep a list; answer the form from it. | `./gradlew :app:dependencies --configuration releaseRuntimeClasspath` |
| Account deletion in-app + web | App code and a public web page, only if the app creates accounts. | — |
| Permissions declared | `<uses-permission>` in `app/src/main/AndroidManifest.xml`; libraries add their own. Runtime permissions are requested in code (`ActivityResultContracts.RequestPermission`). | merged manifest at `app/build/intermediates/merged_manifests/release/AndroidManifest.xml` after a build |
| Play App Signing | Nothing in the project — enrolment is per app in Play Console, at first upload. The build only ever sees the upload key. | Play ingredient §3 |

## Choosing dependencies

Google Maven (`google()`) and Maven Central (`mavenCentral()`) are the repositories; every
version belongs in `gradle/libs.versions.toml`. **Jetpack (`androidx.*`) first** — it is
Google's own library set and the architecture guide is written against it: `lifecycle-viewmodel-
compose`, `navigation-compose`, `room`, `datastore`, `hilt`. Before adding a library with native
code, apply the 16 KB check above after the build. `orclab:currency-discipline` applies to every
version; Android Studio's "Upgrade Assistant" and `./gradlew dependencyUpdates` (a plugin) are
the tools.

**Deliberately not decided here**: networking client (Retrofit/Ktor), image loading, DI beyond
Google's Hilt recommendation, backend. Project choices; no preference recorded until direflail
has one.

## Games

Not this stack. An Android game is Unity or Godot, which produce their own `.aab` through their
own Gradle export; the Play ingredient applies to it unchanged.

## Sources (live on 2026-09-11)

- Android Studio current release: `https://developer.android.com/studio`
- AGP 9.4.0 requirements: `https://developer.android.com/build/releases/gradle-plugin`
- Compose BOM mapping: `https://developer.android.com/develop/ui/compose/bom/bom-mapping`;
  Compose compiler plugin: `https://developer.android.com/develop/ui/compose/compiler`
- "Modern toolkit": `https://developer.android.com/develop/ui/compose/documentation`
- Kotlin releases: `https://kotlinlang.org/docs/releases.html`
- Architecture guide: `https://developer.android.com/topic/architecture`
- Signing and `bundleRelease`: `https://developer.android.com/studio/publish/app-signing`
- KMP status: `https://developer.android.com/kotlin/multiplatform`
- Store rules themselves: the Play ingredient under `skills/orc-package/ingredients/play`, with its own sources.
