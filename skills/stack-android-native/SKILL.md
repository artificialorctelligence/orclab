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
iOS UI. Kotlin Multiplatform is the decided path to iOS from here —
`skills/stack-kotlin-multiplatform/SKILL.md`. **Start KMP-shaped on day one** (confirmed live
2026-09-12): keep the business logic in its own Gradle module that imports nothing from `android.*`
or `java.*`; kotlinlang.org's *Make your Android application work on iOS* guide then makes the move
one wizard (*Kotlin Multiplatform Shared Module*) and one package move into `commonMain`, with each
Android-only import the only thing to rewrite.

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

Coverage, mutation testing and test lint for this language: `skills/orc-test/languages/kotlin.md`
— `/orc-test` reads it.

## Presence

No project has been built with these facets yet; the first one corrects them. Presence is how
the app stays visible and reachable when it is not in front. On Android that is one thing, a
**notification**: it puts a small icon in the status bar at the top of the screen, and a card in
the tray the user pulls down, which they can tap to open the app, expand for more, or act on
with buttons. There is no separate "status-bar icon" to build — the notification's small icon
*is* it. Google's own words (confirmed live 2026-09-12, page dated 2026-09-01): *"When you issue a
notification, it first appears as an icon in the status bar"*; users open the drawer to *"view
more details and take actions with the notification."*

**Mechanism: `NotificationCompat.Builder` from `androidx.core`, posted with
`NotificationManagerCompat.notify()`** — plain Android, not Compose. Google's notification guides
now sit under the site's Compose section, yet they say *"the code in this page uses the
`NotificationCompat` APIs from the AndroidX Library"*, and the Views page says the same — *"you
use the Android system APIs and `NotificationCompat`"* (confirmed live 2026-09-12). Nothing here
is Compose-specific. Required: `setSmallIcon()` — *"the only user-visible content that's
required"* — and, since Android 8.0, a `NotificationChannel` registered with
`createNotificationChannel()` before the first post (confirmed live 2026-09-12).

What Android 16 / API 36 requires, both older rules still in force (confirmed live 2026-09-12,
pages dated 2026-09-01):
- **Notification permission, since Android 13 (API 33):** `POST_NOTIFICATIONS` in the manifest
  and requested at runtime (`ActivityResultContracts.RequestPermission`, as the Play table
  says). Targeting 13+ gives *"complete control over when the permission dialog is displayed"*;
  an app that never asks posts nothing. Foreground services are exempt from *asking* — *"Apps
  don't need to request the `POST_NOTIFICATIONS` permission in order to launch a foreground
  service"* — but not from showing a notification.
- **Foreground-service types, since Android 14 (API 34):** *"you must declare an appropriate
  service type for each foreground service"* — `android:foregroundServiceType` on the `<service>`,
  plus `FOREGROUND_SERVICE` and the type's own permission (`FOREGROUND_SERVICE_CAMERA`,
  `FOREGROUND_SERVICE_MEDIA_PLAYBACK`, one per type) in the manifest. Undeclared, the
  system *"throws a `MissingForegroundServiceTypeException` upon calling `startForeground()`"*.
  The Android 16 behaviour-changes page adds nothing on notifications or foreground services
  (confirmed live 2026-09-12).

What a notification can do (confirmed live 2026-09-12; `NotificationCompat.Builder` reference):
- **Action buttons** — `addAction(icon, label, pendingIntent)`; *"up to three action buttons"*,
  and they *"must not duplicate the action performed when the user taps the notification."*
- **Direct reply** — an action carrying a `RemoteInput`; *"introduced in Android 7.0 (API level
  24), lets users enter text directly into the notification"* without opening an activity.
- **Progress** — `setProgress(max, progress, indeterminate)`. Android 16 adds
  `Notification.ProgressStyle` (a journey with points and segments — rideshare, delivery) and
  **Live Updates** — `setRequestPromotedOngoing(true)` (`androidx.core` 1.17.0+) plus the
  `POST_PROMOTED_NOTIFICATIONS` permission — which show *"as a chip in the status bar"*.
- **Ongoing** — `setOngoing(true)`: *"cannot be dismissed by the user, so your application or
  service must take care of canceling them."* A foreground service's notification is this by
  construction: start with `context.startForegroundService()`, then inside the service
  `ServiceCompat.startForeground(service, id, notification, type)`; the notification *"can't be
  dismissed like other notifications"* until the service stops.

No alternative mechanism to name: a notification is the only way an Android app is present when
not in front. A foreground service keeps the app *running* behind one, and only for a task
*"noticeable by the user, even when they're not directly interacting with the app"* (confirmed
live 2026-09-12).

## UI

No project has been built with these facets yet; the first one corrects them. The UI is what the
user sees and touches; on Android the choice is which toolkit draws it. **Default: Jetpack
Compose** — the toolchain row above, Compose BOM **2026.08.00** (`androidx.compose:compose-bom`,
→ `compose.ui` 1.12.0, `material3` 1.4.0; confirmed live 2026-09-12 on
`developer.android.com/develop/ui/compose/bom`, where `/jetpack/compose/bom` redirects, page
dated 2026-09-01). One BOM line in `libs.versions.toml` pins every Compose library; no
per-library versions. Google's Views page itself says *"Jetpack Compose is the recommended UI
toolkit for Android"* (confirmed live 2026-09-12). **Alternative: Views/XML** — only for an
existing Views codebase being extended rather than rewritten, or a specific widget with no
Compose equivalent. The two co-exist: `ComposeView` puts Compose inside a View layout,
`AndroidView` / `AndroidViewBinding` put a View inside Compose (interoperability page, confirmed
live 2026-09-12) — so the Views alternative is a per-screen or per-widget choice, never a
project-wide one. BACKLOG #2's design system translates into the frameworks above.

## Storage

No project has been built with these facets yet; the first one corrects them. Storage is what the
app keeps on the device between launches: records the user creates (a database) and settings
(config). Everything below lives in the app's private internal storage — *"Other apps cannot
access files stored within internal storage"* and *"When the user uninstalls your app, the files
saved in app-specific storage are removed"* (confirmed live 2026-09-12). External databases are
out of scope for this skill.

**Saved data: Room 3 over SQLite — `androidx.room3:room3-runtime` and
`ksp("androidx.room3:room3-compiler")`, 3.0.3** (released 2026-09-09; the training guide's snippet
still says 3.0.2 — confirmed live 2026-09-12). Google: *"We recommend using Room instead of using
the SQLite APIs directly."* Room 3 (July 2026) is *"a major version update of Room 2.x package
(`androidx.room`) that focuses on Kotlin Multiplatform"*: same `@Entity` / `@Dao` / `@Database`,
but *"All database operations are now Coroutine APIs based. Kotlin code generation only"*, and
*"Kotlin Symbol Processing (KSP) is required"*. The database file is wherever
`Context.getDatabasePath(name)` points; *"the returned path may change over time"*, so persist
only relative paths (confirmed live 2026-09-12). Alternative: **Room 2 (`androidx.room` 2.8.5**,
also 2026-09-09) only for an existing Room 2 codebase, Java sources, or a library that still
needs the SupportSQLite APIs Room 3 dropped.

**Config: Preferences DataStore — `androidx.datastore:datastore-preferences` 1.2.1** (2026-03-11;
confirmed live 2026-09-12): key-value, coroutines and `Flow`, *"asynchronously, consistently, and
transactionally"*; files are `*.preferences_pb` under the app's `files/datastore/` and are in
Auto Backup by default. Proto DataStore (`androidx.datastore:datastore`, same version) is the
alternative when the settings are a typed object and a schema is worth the protobuf `Serializer`.
**`SharedPreferences` is the legacy path** — Google's own page: *"DataStore is a modern data
storage solution that you should use instead of `SharedPreferences`"* (confirmed live
2026-09-12); still picked only to read an existing app's preference files, or where a
third-party library hands you a `SharedPreferences` and nothing else. Neither is for records —
for *"large or complex datasets, partial updates, or referential integrity"* the DataStore page
says Room.

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

## Sources (live on 2026-09-11; facets 2026-09-12)

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
- Facets (2026-09-12) — presence: `https://developer.android.com/develop/ui/views/notifications`, `https://developer.android.com/develop/ui/compose/notifications`, `.../compose/notifications/create-notification`, `.../compose/notifications/notification-permission`, `.../compose/notifications/progress-centric`, `.../compose/notifications/live-update`, `https://developer.android.com/reference/androidx/core/app/NotificationCompat.Builder`; foreground services: `https://developer.android.com/develop/background-work/services/fgs`, `.../fgs/service-types`, `.../fgs/declare`, `.../fgs/launch`; `https://developer.android.com/about/versions/16/behavior-changes-16`
- Facets — UI: `https://developer.android.com/develop/ui/compose/bom` (where `/jetpack/compose/bom` redirects), `https://developer.android.com/develop/ui/compose/bom/bom-mapping`, `https://developer.android.com/develop/ui/compose/migrate/interoperability-apis`
- Facets — storage: `https://developer.android.com/training/data-storage/room`, `https://developer.android.com/jetpack/androidx/releases/room3`, `https://developer.android.com/jetpack/androidx/releases/room`, `https://developer.android.com/topic/libraries/architecture/datastore`, `https://developer.android.com/jetpack/androidx/releases/datastore`, `https://developer.android.com/training/data-storage/shared-preferences`, `https://developer.android.com/training/data-storage/app-specific`, `https://developer.android.com/reference/android/content/Context`
