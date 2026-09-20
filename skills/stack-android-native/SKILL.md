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

## Lint — where code-discipline lands

Kotlin's own switch is in the Gradle build; the shape rules are detekt's (v1.23.8), whose default
config already carries all four, confirmed 2026-09-13 against `default-detekt-config.yml`:

```kotlin
// build.gradle.kts
kotlin { compilerOptions { allWarningsAsErrors.set(true) } }   // "Report an error if there are any warnings"
```

```yaml
# config/detekt/detekt.yml
complexity:
  NestedBlockDepth: { active: true, allowedDepth: 2 }   # detekt's default is 4
  LongMethod: { active: true, allowedLines: 60 }         # detekt's default, kept
exceptions:
  EmptyCatchBlock: { active: true }        # exempts `_`, `ignore*`, `expected*` names — the named suppression
  SwallowedException: { active: true }     # a caught exception neither rethrown nor used
```

Apply the detekt Gradle plugin and `./gradlew detekt` joins the check before any build. Rules 2,
3 and 5 (loop exits, `use {}` on the error path, `require`/`check` over `assert`) are reviewed,
not linted.

## Security — where security-discipline lands

`security-discipline`'s rules for this stack, confirmed live 2026-09-19;
no project has been through this yet, and the first one corrects it. A phone app is the
*Every project* tier — it accepts no connections — so rules 1–4 apply in full, and of 5–9 only
what a client owes: whether it checks the certificate of the server it talks to (rule 8's own
client half), and rule 5's *shape* — untrusted input reaching the point where it is used —
extended here to a value another app handed it over IPC, which the rule's text does not name.
That server carries 5–9 in its own stack.

### Static analysis

**detekt has no security rules — none free there — and it does not matter, because Android
Lint is this stack's security linter and the Build section already runs it.** detekt.dev's
rule index (read live 2026-09-19) lists twelve rule sets — comments, complexity, coroutines,
empty-blocks, exceptions, ktlint, libraries, naming, performance, potential-bugs, ruleauthors,
style — and no `security`; `config/detekt/detekt.yml` above stays as it is. Android Lint ships
with the Android Gradle Plugin, and its issue index (googlesamples.github.io's
android-custom-lint-rules, read live 2026-09-19) has a **Security** category of 87 checks: 62
built in, 24 from Google's separate `com.android.security.lint:lint` package, one from Slack's.
Of the 62, 59 are on by default (off: `EasterEgg`, `PermissionNamingConvention`,
`VulnerableCordovaVersion`, all three Warning severity); 48 are Warning severity, 11 Error, 3
Fatal — so 45 Warning-severity checks are on. `./gradlew lint` stops
the build on an Error or a Fatal — `abortOnError`, *"If set to true (default), stops the build
if errors are found"* — and only reports a Warning. So one line, in a block the Lint section
does not open:

```kotlin
// app/build.gradle.kts
android {
    lint {
        warningsAsErrors = true   // "Whether lint should treat all warnings as errors" — the 45 Warning-severity Security checks that are on now stop the build
    }
}
```

What the 59 cover, by rule (the index, and the eleven quoted check pages, read live
2026-09-19):

- **Rule 1 — narrowly.** `SecretInSource` (AGP 8.3+) sounds general and is not: its detector,
  `SecretDetector.kt`, fires on one thing, an `AIza…` literal passed to the Gemini SDK's
  `GenerativeModel` constructor. `PackagedPrivateKey` (Fatal: *"you should not package private
  key files inside your app"*) and `HardcodedDebugMode` (Fatal: a literal `android:debuggable`
  *"can lead to accidentally publishing your app with debug information"*) are the artifact
  half. A token typed into a Kotlin file is otherwise reviewed, not linted.
- **Rule 3.** `UnsafeDynamicallyLoadedCode` and `UnsafeNativeCodeLocation`: *"Dynamically
  loading code from locations other than the application's library directory or the Android
  platform's built-in library directories is dangerous, as there is an increased risk that the
  code could have been tampered with."* Play's Device and Network Abuse policy makes the rule
  absolute on this stack: *"an app may not download executable code (such as dex, JAR, .so
  files) from a source other than Google Play"*; the exception is code in an interpreter,
  *"such as JavaScript in a webview"*, which is where rule 3 is reviewed.
- **Rule 4.** `WorldReadableFiles`, `WorldWriteableFiles`, `SetWorldReadable`,
  `SetWorldWritable` (Mobile M8's file case), and the exported-component set —
  `ExportedService` (*"Without this, any application can use this service"*),
  `ExportedReceiver`, `ExportedContentProvider`, `GrantAllUris`. Whether a declared
  `<uses-permission>` is used: reviewed, as the rule says.
- **Rule 5's shape, extended to IPC** — the rule itself covers only input that arrives over
  the network. A value from another app arrives as an Intent, a content URI or inside a
  WebView: `UnsafeIntentLaunch`, `UnsafeImplicitIntentLaunch` (Error),
  `UnsanitizedFilenameFromContentProvider`, `SetJavaScriptEnabled`, `AddJavascriptInterface`,
  `JavascriptInterface` (Error).
- **Rule 8's client half.** `TrustAllX509TrustManager` (*"thus trusting any certificate
  chain"*), `CustomX509TrustManager`, `BadHostnameVerifier`, `AllowAllHostnameVerifier`,
  `SSLCertificateSocketFactoryGetInsecure`, `WebViewClientOnReceivedSslError` in code;
  `InsecureBaseConfiguration` (*"Permitting cleartext traffic could allow eavesdroppers to
  intercept data sent by your app"*) and `AcceptsUserCertificates` in
  `network_security_config.xml`. `UsingHttp` is the Gradle wrapper's own download URL.

Google's `com.android.security.lint:lint` 1.0.4 (Google Maven, 2025-12-12; its README: *"This
library uses the Apache license, as is Google's default"*, and *"more security-focused and
experimental than the built-in lint checks"*) adds the other 24 with
one line — `lintChecks("com.android.security.lint:lint:1.0.4")` in `app/build.gradle.kts`'s
`dependencies {}`. They are crypto algorithms, PRNGs, logcat leaks, FileProvider paths,
tapjacking and a cleartext check for apps targeting below 28 — nothing the built-in set and API
36's defaults do not already cover for the nine rules — and none has been run here, so the line is
not in the scaffold; a project that wants them adds it. Rule 3's checksum before use and rule
4's unused permission have no linter: reviewed.

### Dependency audit

One run, from `/orc-test audit`: the OWASP dependency-check Gradle plugin —
`skills/orc-test/languages/kotlin.md`, `## Audit`. Installed means, **in the root
`build.gradle.kts`**, `id("org.owasp.dependencycheck") version "13.0.0"` in `plugins {}` and
`dependencyCheck { formats = listOf("JSON") }` (rule 2). One thing that section says which
bites here: a multi-module build *"wants `dependencyCheckAggregate`, not wired here"*, and the
template is one — root plus `app/`, with every dependency in `app/` — so until it is wired,
`/orc-test audit` reads the root project's own dependency list, which is empty, not `app/`'s.

### Secrets

Three kinds of secret, three places, none of them a source file (rule 1; every quotation below
confirmed live 2026-09-19 on developer.android.com unless said otherwise):

- **The upload key.** `keystore.properties` and the `.jks` it names — the layout table's row.
  The app-signing page (dated 2026-03-06): *"Be sure to keep the `keystore.properties` file
  secure. This may include removing it from your source control system."* `.gitignore` gets
  `keystore.properties`, `*.jks` and `*.keystore` on day one, and `secrets.properties` the day
  the Maps-key case below arrives; the template already ignores
  `local.properties` and `build/` (the layout table), and what else Studio's template ignores
  was not checked — Now in Android's `.gitignore`, read live, has no keystore line. Lint's
  `PackagedPrivateKey` is the check that none of it went into the bundle.
- **A token the app holds for its user** (a session, a refresh token). Jetpack Security's
  `EncryptedSharedPreferences` is no longer a choice: its release notes, 1.1.0-alpha07
  (2025-04-09) and again at 1.1.0-beta01 (2025-06-04), *"Deprecated all APIs in favour of
  existing platform APIs and direct use of Android Keystore."* What replaces it is two things
  the Storage section and the Keystore page already give. The value sits in app-private storage
  (*"Other apps cannot access files stored within internal storage"*), encrypted under an
  **Android Keystore** key — an AES-GCM key from `KeyGenerator.getInstance(KEY_ALGORITHM_AES,
  "AndroidKeyStore")` with a `KeyGenParameterSpec`, the recipe on Google's *Hardcoded
  Cryptographic Secrets* risk page (dated 2024-09-24) — because *"Key material never enters the
  application process"* and, hardware-bound, *"is never exposed outside of secure hardware"*
  (Keystore page, dated 2026-03-06). The ciphertext file goes under `context.noBackupFilesDir`:
  Auto Backup copies `getFilesDir()`, shared preferences and the database directory to the cloud
  by default, *"always"* excludes `getNoBackupFilesDir()`, and its own tip is *"To back up user
  credentials and authentication tokens, don't store them in shared preferences or a file"* —
  its answer, Block Store, is a Play Services dependency and a Data-safety row, so the scaffold
  takes the no-backup directory, and a project that wants a token to follow the user to a new
  phone chooses Block Store on purpose (Auto Backup page, dated 2026-02-26).
- **An API key for a service the app calls.** The bundle is public — anyone who installs the
  app can unpack it — so a key in it is a key everyone has. Google's own API-key page
  (docs.cloud.google.com, dated 2026-09-16): *"Don't include API keys in client code or commit
  them to code repositories"*; *"The client should pass requests to the server, which can add the
  credential and issue the request."* That server is the *Reachable by strangers* tier of
  whatever stack it is in. The one exception is a key Google designs to ship in an app — a Maps
  key — which goes through the Secrets Gradle Plugin
  (`com.google.android.libraries.mapsplatform.secrets-gradle-plugin` 2.0.1, page dated
  2026-09-17): it reads a git-ignored `secrets.properties` and *"exposes those properties as
  variables in the Gradle-generated `BuildConfig` class and in the Android manifest file"* —
  out of the repository, not out of the artifact, which is the most any build plugin can do.

Never in the built bundle: the keystore, `keystore.properties`, `secrets.properties`,
`local.properties`, `.git`. `PackagedPrivateKey` and `HardcodedDebugMode` are the two checks
that run; whether `bundleRelease` can ever pick up a stray properties file was not checked — the
first project lists the bundle once (`unzip -l app/build/outputs/bundle/release/app-release.aab`)
and records the answer here.

### Reachable by strangers

This stack does not accept connections: n/a — a phone app has no route to authenticate, no error
to sanitise and no rate to limit; the service it talks to carries rules 5–9 in its own stack. What
still applies is rule 8's client half: refuse plain HTTP and trust only the system's certificate
store, which on API 36 is the platform default — *"Starting with Android 9 (API level 28),
cleartext support is disabled by default"*, with `<certificates src="system" />` as the only
trust anchor (network security configuration page, dated 2026-08-28, confirmed live
2026-09-19). So a `network_security_config.xml` that sets `cleartextTrafficPermitted="true"` or
adds `<certificates src="user" />`, and any `X509TrustManager` or `HostnameVerifier` of the
app's own, is a finding, and the Static analysis checks above catch both the XML and the code.
A CA for a development server belongs in `<debug-overrides>`, which the platform honours only
when `android:debuggable` is true — `AcceptsUserCertificates`' own advice. And the API-key
paragraph above: the bundle is not a secret store.

## Containers

Runs in a container: **yes** — confirmed live 2026-09-20. `./gradlew lint test`, every `/orc-test`
step, `lint_on_write`'s detekt and `bundleRelease` run inside; what cannot is anything that
needs a phone or a screen — the emulator, `installDebug`, `connectedAndroidTest` and the Play
upload — which stay on the host.

**No Android SDK image comes from Google or a foundation, so the `Dockerfile` builds one from
their downloads.** GitHub's `android` organisation has no repository matching "docker" (its
search API, read live: `total_count` 0), and Google's one container project,
`android-emulator-container-scripts`, is the emulator, not the SDK (below). What exists is
third-party, each someone else's arrangement of Google's own zip: CircleCI's `cimg/android`
(Docker Hub, `2026.08.1` pushed 2026-08-03, 3.42 GB compressed — the most maintained, a CI
vendor's convenience image), `mingc/android-build-box` (5.94 GB, 2026-08-10),
`thyrlian/android-sdk` (last pushed 2024-09-29), and Cirrus Labs' `ghcr.io/cirruslabs/android-sdk`,
whose sibling Flutter repository's README now says *"This repostiry will stop updating images
starting May 1st 2026 due to Cirrus Labs winding down operations after an acquisition"*. So the
Dockerfile does what they do, from the sources they read: the JDK from the Eclipse Foundation's
official `eclipse-temurin` image, and the SDK from Google's command-line tools zip, checked
against the SHA-256 on Google's download page (`security-discipline` rule 3), with `sdkmanager`
fetching the rest. JDK **17**, because the toolchain table's AGP 9.4 needs *"JDK 17 or newer"*,
Gradle 9.6 runs on *"a JVM version between 17 and 26"*, and React Native (whose image reuses
this one) *"currently recommends version 17"*.

The `Dockerfile` `/orc-code` writes when the user says yes to the container question — base
image and tag from the `eclipse-temurin` image's own tag list (`17-jdk` is `17.0.20_8-jdk`
on Ubuntu 26.04 "resolute" today, 211 MB compressed on Docker Hub), Google's command-line
tools and the SDK packages the toolchain table names (Platform 36, Build-Tools 36.0.0,
Platform-Tools), and every tool `skills/orc-test/languages/kotlin.md` names that is not a
Gradle plugin — which is detekt alone:

```dockerfile
FROM eclipse-temurin:17-jdk
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends unzip \
    && rm -rf /var/lib/apt/lists/*
RUN wget -q -O /tmp/cmdline-tools.zip https://dl.google.com/android/repository/commandlinetools-linux-15859902_latest.zip \
    && echo "4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583 /tmp/cmdline-tools.zip" | sha256sum -c - \
    && mkdir -p $ANDROID_HOME/cmdline-tools \
    && unzip -q /tmp/cmdline-tools.zip -d $ANDROID_HOME/cmdline-tools \
    && mv $ANDROID_HOME/cmdline-tools/cmdline-tools $ANDROID_HOME/cmdline-tools/latest \
    && rm /tmp/cmdline-tools.zip
RUN yes | sdkmanager --licenses >/dev/null \
    && sdkmanager "platform-tools" "platforms;android-36" "build-tools;36.0.0"
RUN wget -q -O /tmp/detekt.zip https://github.com/detekt/detekt/releases/download/v1.23.8/detekt-cli-1.23.8.zip \
    && echo "ff9f9258879ff2ec4349114740221498afec46a85cf6302c9f80b06eb4429501 /tmp/detekt.zip" | sha256sum -c - \
    && unzip -q /tmp/detekt.zip -d /opt \
    && ln -s /opt/detekt-cli-1.23.8/bin/detekt-cli /usr/local/bin/detekt \
    && rm /tmp/detekt.zip
ENV GRADLE_USER_HOME=/cache/gradle
```

Not run here — the first project records it. Why each line, so the next reader can check it:

- **`eclipse-temurin:17-jdk`.** Its Dockerfile (`adoptium/containers`, `17/jdk/ubuntu/resolute`)
  is `FROM ubuntu:26.04`, downloads Adoptium's tarball, checks its GPG signature and SHA-256,
  and sets `JAVA_HOME=/opt/java/openjdk` on `PATH` — the JDK a terminal build uses, per the
  jdks page: *"the `JAVA_HOME` environment variable (if set) determines which JDK runs the
  Gradle scripts"*. `wget` is in the image; `unzip` is not, hence the one apt line.
- **The command-line tools.** The Android Studio download page lists
  `commandlinetools-linux-15859902_latest.zip`, 181.8 MB, with the SHA-256 that is in the
  `RUN`. The unzip-and-move is the sdkmanager page's own instruction — *"In the unzipped
  `cmdline-tools` directory, create a sub-directory called `latest`"* and move the contents in.
  `ANDROID_HOME` is the variable Google names (*"Sets the path to the SDK installation
  directory"*; `ANDROID_SDK_ROOT` *"is deprecated"*), the one the Install paragraph above
  already asks for; `sdkmanager` uses *"the SDK containing this tool"*, so no `--sdk_root`.
- **Licences, then packages.** `sdkmanager --licenses` *"prompts you to accept any licenses that
  haven't already been accepted"*; `yes` answers the prompt. Then the three packages the
  toolchain table names, in the page's own syntax (`"platforms;android-36"`,
  `"build-tools;36.0.0"`, `"platform-tools"`) — about 300 MB on disk (135 + 147 + 22 MB,
  measured on this machine's SDK; the tools themselves 174 MB). Not installed: the NDK and
  CMake, which a pure Kotlin app does not use. A project with native code adds
  `"ndk;28.2.13676358" "cmake;3.22.1"` to the line (2.2 GB and 60 MB here), because otherwise
  AGP fetches them at build time — *"Android Gradle Plugin 4.2.0+ can automatically install
  the required NDK and CMake the first time you build your project if their licenses have
  been accepted in advance"* — into a container that is discarded after the command.
- **detekt** is the one tool on the language page that is not a Gradle plugin: `/orc-test`'s
  test lint and `lint_on_write`'s `.kt` line both call `detekt` on `PATH`. Java's `pmd`
  (`languages/java.md`) is never needed here: `detect.py` drops Java from a Gradle project
  whose `src/` holds `.kt` files, so the two never both run. The zip is the CLI
  page's *"Direct Download (Any OS)"* form; v1.23.8 (2025-02-21) is the latest non-prerelease
  on GitHub and the version the Lint section names. detekt publishes no checksum, so the
  SHA-256 on that line was computed here from the release asset on 2026-09-20 — pinned so a
  changed download fails, not vendor-attested. The unzipped script is `bin/detekt-cli`; the
  symlink gives it the name both callers use.
- **Kover, Pitest (and Arcmutate), dependency-check: installed by nothing here.** They are
  Gradle plugins in the project's own build file (`## Lint`, `### Dependency audit`,
  `languages/kotlin.md`), resolved by Gradle like any dependency; the wrapper likewise
  downloads its own distribution (`gradle-9.6.0-bin.zip` is 141 MB). All of it lands in the
  Gradle User Home — *"By default, the Gradle User Home (`~/.gradle` …)"* holds the wrapper
  distributions and the dependency cache, and *"It can be set with the environment variable
  `GRADLE_USER_HOME`"* (Gradle 9.7.1 docs) — which is why the last line moves it to
  `/cache/gradle`: `compose run --rm` throws the container away after every command, so a
  cache inside the image's filesystem would be refilled from the network on every `/orc-test`
  step. dependency-check's NVD copy goes with it — its Gradle plugin's convention is
  `"${project.gradle.gradleUserHomeDir}/dependency-check-data/11.0"` (`DataExtension.groovy`
  on `main`) — so the 20-minute first download happens once.

**The `compose.yaml`** is the one in `skills/orc-test/SKILL.md`'s Containers section with one
addition for that cache: a named volume, which Compose defines as *"persistent data stores
implemented by the container engine"*, declared at the top level and granted to the service
(the Compose volumes reference); `podman-compose` 1.0.6 creates it on first use (`assert_volume`
in its source: `podman volume inspect <name> || podman volume create <name>`):

```yaml
services:
  orclab:
    build: .
    volumes:
      - .:${PWD}
      - cache:/cache
    working_dir: ${PWD}
volumes:
  cache:
```

The volume is the engine's, not the project's: it survives `compose run --rm`, and
`<engine> volume rm` empties it. A plugin version bump in the build file resolves through it
like any dependency; the image is rebuilt (`<engine> compose build orclab`) when the Dockerfile
changes — a newer platform, a newer detekt — and there is nothing unpinned in it.

What cannot happen inside: **the emulator** — Google's own recipe for it in a container,
`android-emulator-container-scripts`, is *"still an experimental feature"* and runs with
`--device /dev/kvm` because *"KVM must be enabled on your host"*; the compose file above passes
no device, and a USB phone is not passed either, so `installDebug`, `connectedAndroidTest` and
`adb devices` are the host's. **The Play upload** — the Play ingredient's step, from the host,
with credentials that are never in the image. What *can*: `bundleRelease` signs inside, because
`keystore.properties` and the `.jks` are in the mounted working tree (the Secrets section's
rule that they are git-ignored is unchanged; the mount is the tree, not the repository). The
proposal `/orc-code` makes for this stack's container question: **no**, because the toolchain
row already installs Android Studio, which brings the SDK, a JDK and the emulator; the image is
a second SDK beside it (211 MB of JDK image plus ~480 MB of SDK, 2.2 GB more for native code),
and the emulator — the thing that makes Android development need an Android machine — cannot
move into it. Say yes on a machine with no Android Studio that only needs to build and test, or
one with no JDK 17.

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
| Version code increases every upload | `defaultConfig.versionCode` (integer) and `versionName` (string). Literal values in the build file. `/orc-version` does not edit this file yet (its `versionfiles.py` handles `pyproject.toml`, `debian/changelog`, an AppStream metainfo file and the plugin manifests — BACKLOG #6); bump it by hand and check it before every upload. A handler must edit both and refuse a bump that leaves `versionCode` unchanged. | Play refuses a reused `versionCode`. |
| Data safety form is truthful | Decided by dependencies: any library that sends data off-device (Firebase Analytics/Crashlytics, ads, Play Services with telemetry). Keep a list; answer the form from it. | `./gradlew :app:dependencies --configuration releaseRuntimeClasspath` |
| Account deletion in-app + web | App code and a public web page, only if the app creates accounts. | — |
| Permissions declared | `<uses-permission>` in `app/src/main/AndroidManifest.xml`; libraries add their own. Runtime permissions are requested in code (`ActivityResultContracts.RequestPermission`). | merged manifest at `app/build/intermediates/merged_manifests/release/AndroidManifest.xml` after a build |
| Play App Signing | Nothing in the project — enrolment is per app in Play Console, at first upload. The build only ever sees the upload key. | Play ingredient §3 |

## Choosing dependencies

Google Maven (`google()`) and Maven Central (`mavenCentral()`) are the repositories; every
version belongs in `gradle/libs.versions.toml`. **Jetpack (`androidx.*`) first** — it is
Google's own library set and the architecture guide is written against it: `lifecycle-viewmodel-
compose`, `navigation-compose`, `room3`, `datastore`, `hilt`. Before adding a library with native
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

- Lint — where code-discipline lands (2026-09-13): `https://raw.githubusercontent.com/detekt/detekt/main/detekt-core/src/main/resources/default-detekt-config.yml`, `https://kotlinlang.org/docs/gradle-compiler-options.html` (`allWarningsAsErrors`); detekt release from the GitHub releases API
- Security — where security-discipline lands (2026-09-19): detekt's rule-set index `https://detekt.dev/docs/rules/comments` (sidebar; `/docs/rules/` itself is a 404); Android Lint's issue index `https://googlesamples.github.io/android-custom-lint-rules/checks/categories.md.html` (Security, 87), `.../checks/severity.md.html`, `.../checks/vendors.md.html`, and the check pages `.../checks/{SecretInSource,UnsafeDynamicallyLoadedCode,TrustAllX509TrustManager,WorldReadableFiles,ExportedService,HardcodedDebugMode,PackagedPrivateKey,UsingHttp,DefaultCleartextTraffic,AcceptsUserCertificates,InsecureBaseConfiguration}.md.html`; `SecretDetector.kt` from `https://android.googlesource.com/platform/tools/base/+/mirror-goog-studio-main/lint/libs/lint-checks/src/main/java/com/android/tools/lint/checks/SecretDetector.kt`; the `lint {}` block `https://developer.android.com/studio/write/lint` and `https://developer.android.com/reference/tools/gradle-api/9.4/com/android/build/api/dsl/Lint` (`warningsAsErrors`, `abortOnError`); Google's security lints `https://raw.githubusercontent.com/google/android-security-lints/main/README.md`, `https://dl.google.com/android/maven2/com/android/security/lint/lint/maven-metadata.xml`; Play policy `https://support.google.com/googleplay/android-developer/answer/9888379`; secrets: `https://developer.android.com/jetpack/androidx/releases/security`, `https://developer.android.com/privacy-and-security/keystore`, `https://developer.android.com/privacy-and-security/risks/hardcoded-cryptographic-secrets`, `https://developer.android.com/identity/data/autobackup`, `https://developer.android.com/studio/publish/app-signing`, `https://docs.cloud.google.com/docs/authentication/api-keys-best-practices`, `https://developers.google.com/maps/documentation/android-sdk/secrets-gradle-plugin`, `https://raw.githubusercontent.com/android/nowinandroid/main/.gitignore`; transport: `https://developer.android.com/privacy-and-security/security-config`
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
- Containers (2026-09-20): Google's `android` org via `https://api.github.com/search/repositories?q=org:android+docker` (0 results); third-party images: `https://hub.docker.com/v2/repositories/cimg/android/tags` (sizes, push dates), `https://github.com/CircleCI-Public/cimg-android`, `https://hub.docker.com/v2/repositories/mingc/android-build-box/tags`, `https://hub.docker.com/v2/repositories/thyrlian/android-sdk/tags`, `https://raw.githubusercontent.com/cirruslabs/docker-images-flutter/master/README.md` (the wind-down note); JDK: `https://raw.githubusercontent.com/docker-library/official-images/master/library/eclipse-temurin` (`17-jdk` → `17.0.20_8-jdk-resolute`), `https://raw.githubusercontent.com/adoptium/containers/main/17/jdk/ubuntu/resolute/Dockerfile`, `https://hub.docker.com/v2/repositories/library/eclipse-temurin/tags/17-jdk` (211 MB), `https://developer.android.com/build/jdks` (`JAVA_HOME`), `https://docs.gradle.org/9.6.0/userguide/compatibility.html` (JVM 17–26); SDK: `https://developer.android.com/studio` (the zip, 181.8 MB, and its SHA-256), `https://developer.android.com/tools/sdkmanager` (`latest`, `--licenses`, package syntax), `https://developer.android.com/tools/variables` (`ANDROID_HOME`), `https://developer.android.com/studio/projects/install-ndk` (auto-install, default CMake), `sdkmanager --list` and `du` on this machine's SDK 2026-09-20 (package names, on-disk sizes); emulator: `https://raw.githubusercontent.com/google/android-emulator-container-scripts/master/README.md` (KVM, `--device /dev/kvm`, experimental); Gradle cache: `https://docs.gradle.org/current/userguide/directory_layout.html` (`GRADLE_USER_HOME`), `https://raw.githubusercontent.com/dependency-check/dependency-check-gradle/main/src/main/groovy/org/owasp/dependencycheck/gradle/extension/DataExtension.groovy` (data directory convention), `https://services.gradle.org/distributions/gradle-9.6.0-bin.zip` (141 MB, `Content-Length`); the volume: `https://docs.docker.com/reference/compose-file/volumes/`, `https://github.com/containers/podman-compose/blob/v1.0.6/podman_compose.py` (`assert_volume`); detekt: `https://detekt.dev/docs/gettingstarted/cli` (the direct-download form), `https://api.github.com/repos/detekt/detekt/releases/latest` (v1.23.8, assets), SHA-256 of `detekt-cli-1.23.8.zip` computed on this machine 2026-09-20 (no checksum published)
