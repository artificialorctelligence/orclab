---
name: stack-react-native
description: Background knowledge for any work in a React Native project - creating one with Expo, building for Android or iOS (and reaching web, Windows or macOS with React), configuring versions, permissions or the privacy manifest in app.json, choosing an RN or Expo package, or preparing a Google Play or App Store release. Says what the current toolchain is, where things live in the project, and where each store rule lands in the build. Not a command; Claude reads it when React Native is in play.
user-invocable: false
---

# React Native (with Expo) — the React way to both phones

No project has been built with this yet; the first one corrects it.

**Checked against live sources on 2026-09-12.** RN ships a minor every ~2 months, Expo an SDK every ~2–3; anything older than one release is suspect — re-check (`## Sources`).

## When this is the stack

React Native is a way to write a phone app in JavaScript or TypeScript using React — the same
component model as a React website — where each `<View>` or `<Text>` becomes the phone's own native
widget rather than a drawing of one. It is the **alternative** on two rows of `/orc-code`'s Defaults
Table: *Android + iOS, nothing else* and *two or more of desktop / mobile / web, iOS ticked*, where
Flutter is the default (Task 8: EAS Build takes only React Native projects, but Codemagic builds and
signs Flutter for iOS, so iOS-from-Linux does not force this stack). The concern that moves a project
here: **the team already writes React, or the web target is a real website** — *"React primitives
render to native platform UI, meaning your app uses the same native platform APIs other apps do"*
(reactnative.dev front page, confirmed live 2026-09-12), and the web half is plain React DOM, where
Flutter paints its own canvas everywhere. Not this stack: games (Godot, Unity), anything native-only.

## Toolchain, as of 2026-09-12

| Thing | Current | Where it was read |
|---|---|---|
| React Native | **0.87.1** (2026-08-26; 0.88.0-rc.0 on `next`) | npm registry |
| Expo SDK | **57** (`expo` 57.0.22, 2026-09-11; SDK 58 in preview) — pins **React Native 0.86.3**, React 19.2.3, `react-native-web` ~0.21.0 — one RN minor behind today. | npm; `docs.expo.dev/versions/latest`; `bundledNativeModules.json` on the `sdk-57` branch |
| Node.js | LTS — **24.21.0 "Krypton"** (2026-09-07); SDK 57 needs ≥ 22.13, RN 0.87 says *"Node.js >= 22.13.0"* | nodejs.org release index; Expo versions table; RN 0.87 blog |
| Start with Expo | reactnative.dev: *"if you're building a new app with React Native, we recommend using a Framework"* and *"Expo is a production-grade React Native Framework"*; bare (*"You can use React Native without a Framework"*) only *"if your app has unusual constraints that are not served well by a Framework"* | `reactnative.dev/docs/environment-setup` |
| New Architecture | **The only architecture.** RN 0.82 (2025-10-08): *"the first React Native that runs entirely on the New Architecture"*; Expo: *"SDK 55 and later run entirely on the New Architecture. The New Architecture is always enabled and cannot be disabled."* The legacy one was frozen in 0.80 (2025-06-12). | RN blog; `docs.expo.dev/guides/new-architecture` (2026-09-03) |
| Android defaults (RN 0.86, what SDK 57 builds with) | `minSdk` 24 / `targetSdk` **36** / `compileSdk` 36, NDK 27.1.12297006, AGP 8.12, Kotlin 2.1.20; RN 0.87 moves `compileSdk` to 37 and AGP to 9 | `gradle/libs.versions.toml` on the `0.86-stable` and `0.87-stable` branches; Expo's `ExpoRootProjectPlugin.kt` reads the version catalog (fallback 35) |
| iOS | deployment target **16.4** by default (`ios.deploymentTarget` in `Podfile.properties.json`); CocoaPods, with Swift Package Manager *"experimental"* in RN 0.87 | `expo-template-bare-minimum/ios/Podfile` on `sdk-57`; RN 0.87 blog |

Install: `npx create-expo-app@latest <name>`; `npx expo-doctor` checks the rows above. Development
runs on *"macOS, Windows (Powershell and WSL 2), and Linux"* (`get-started/create-a-project`,
2026-09-07); Android needs Android Studio, iOS Xcode on a Mac — see "Building without a Mac" below.

## Project layout — where things live

`create-expo-app` makes an Expo project; the layout is its SDK 57 default template (confirmed live 2026-09-12):

| Path | What |
|---|---|
| `app.json` | The app config — name, `slug`, **`version`**, `ios.bundleIdentifier`, `android.package`, permissions, plugins. The single place versions and store identity live; `## Where each store rule lands` is mostly this file. |
| `package.json` | Dependencies pinned to the SDK (`expo ~57.0.22`, `react-native 0.86.3`). `npx expo install <pkg>` picks the SDK-matched version; plain `npm install` does not. |
| `src/app/`, `src/components/`, `src/hooks/`, `assets/` | The app, TypeScript (~6.0) by default. *"The file structure of the src/app directory determines the app's navigation"* — `index.tsx`, `explore.tsx`, `_layout.tsx` (Expo Router, `## UI`); icons, splash and fonts under `assets/`, referenced from `app.json`. |
| `android/`, `ios/` | **Not in the repo.** Generated by prebuild — *"This creates the android and ios directories for running your React code"* — and ignored by the template's `.gitignore` (`# generated native folders` / `/ios` / `/android`). `npx expo run:android` runs prebuild once if they are absent; after changing `app.json`, `npx expo prebuild --clean` regenerates them. A config plugin in `app.json` is how native files are changed without owning them. |

A **bare** project (`npx @react-native-community/cli@latest init <name>`) has `android/` and `ios/`
committed from day one, maintained by you. The concern that picks it: a native change no config plugin
can express. Expo's CNG page (2026-07-20): *"All Expo projects now use Continuous Native Generation."*

## Build, run, test

```bash
npx expo install <pkg>                        # SDK-matched add; never plain npm install for RN packages
npx expo lint && npx jest                     # the check before any build
npx expo start                                # Metro dev server; Expo Go or a development build on the device
npx expo run:android                          # prebuild if needed, compile, install; --variant release for an unsigned release build
npx expo export -p web                        # -> dist/ (web.output: single | static | server)
cd android && ./gradlew app:bundleRelease     # -> android/app/build/outputs/bundle/release/app-release.aab, signed once the upload keystore is configured (below)
```

`npx expo run:ios` is the same on a Mac. Tests are Jest — `npx expo install jest-expo jest @types/jest
--dev`, preset `jest-expo` 57.0.5, *"a Jest preset that mocks the native part of the Expo SDK"*
(2026-06-30); coverage, mutation and test lint: `skills/orc-test/languages/javascript.md`.

### Building without a Mac

The problem, and what every service needs (a paid Apple Developer Program membership, an App Store
Connect API key), are in `stack-flutter`'s `### Building without a Mac`. **Here the default is EAS
Build**, the one service that skill rules out for Flutter, for the same reason: its prerequisite is
*"A React Native Android or iOS project"* (that skill's finding, from `docs.expo.dev/build/setup`).
`npx eas-cli@latest login`, `build:configure`, then `eas build --platform ios` (the setup page,
2026-09-03) builds in Expo's cloud with generated credentials (*"EAS Build can generate and manage
Android keystores, iOS provisioning profiles and distribution certificates"* — Task 8's report);
`eas submit` uploads with the API key and *"works on macOS, Linux, and Windows"* (`/submit/ios`).
Free: 15 iOS and 15 Android builds a month, then $2–4 per iOS build (Task 8's report). Concern that
picks Codemagic instead: a `codemagic.yaml` already in the repo — it has a React Native quick-start.

## React web and desktop

The web half of a React Native app is ordinary React running in a browser; the only question is
whether the phone screens are reused there or a website is written beside them. **Default:
`react-native-web`** — *"a compatibility layer between React DOM and React Native"* (its docs;
**0.21.2**, 2025-10-16, React 18 or 19 — confirmed live 2026-09-12): `npx expo install react-dom
react-native-web @expo/metro-runtime`, then `npx expo export -p web` → `dist/`. Expo's web page
(2026-06-03): *"RNW is optional when developing for web since you can use React DOM directly, but we
often recommended it when building across platforms as it maximizes code reuse."* `web.output` in
`app.json` picks `single` (SPA, the default), `static` (a file per route, for SEO) or `server` (API
routes, needs Node). **Alternative: a separate React web app** in the same repo (Expo's monorepo
guide) sharing only non-UI code. The concern that picks it: the site needs the HTML/CSS ecosystem
as-is (an existing web framework, DOM-only libraries) and should not look like the phone app.
Concern with the default: `react-native-web`'s component set is React Native's, so a web-only
widget is a `.web.tsx` file.

**Windows and macOS** are Microsoft's out-of-tree platforms (reactnative.dev, *"From Partners"*):
**`react-native-windows` 0.84.0** (2026-06-18, pins RN 0.84.1) — *"Starting with React Native Windows
0.82, the legacy Paper architecture has been completely removed"*, and *"You can only develop React
Native for Windows app on Windows"* (its system requirements, confirmed live 2026-09-12);
**`react-native-macos` 0.81.9** (2026-07-13, pins RN 0.81.6; macOS 11+, built with Xcode — inferred,
docs 404'd). Both trail RN by three to six minors; Windows needs its own OS (above), and Expo's
prebuild *"currently supports Android and iOS"* — a desktop target is a bare RN project per OS beside
the Expo one. Concern that picks them anyway: the desktop app must be the same React code.
**Linux desktop: nothing maintained** — reactnative.dev's one entry (*"React Native Skia … Currently
supports Linux and macOS"*, the `react-native-skia` org, not Shopify's drawing library) had its last
commit on 2023-03-24 (confirmed live 2026-09-12). A Linux sibling is the web build, or the desktop
row's own stack.

### Against Flutter for a cross-family project

A cross-family project is choosing between one codebase that draws the same screens everywhere,
or native phone widgets beside a real website. A project that ticks phones plus a website, or
phones plus a desktop, is choosing between Flutter drawing the same screens on every one of them
and React drawing a real website beside native phone widgets. Both cross-family rows of `/orc-code`'s Defaults Table default to Flutter; the comparison
and the concern lines live in `stack-flutter`'s `## Beyond mobile — desktop and web`. The concern
from this side, in one line: **the web tick is a website, not a phone app in a browser** — Flutter's
own web FAQ (confirmed live 2026-09-12) says its output *"doesn't align with what search engines
need to properly index"* and tells you to write landing, marketing and help pages in HTML beside
the app, where this stack's web half is React DOM (`react-native-web` above, or the web-only row's
React + Vite), with the web-only row's own concern still applying: a content site that must render
on the server (SEO, first paint) moves from Vite to Next.js — see `stack-web`'s `## The stack
decision`. The honest desktop answer, restated: Windows
and macOS are a bare RN project per OS trailing RN by three to six minors, and **Linux desktop has
no maintained React Native target** — a Linux tick is served by the web build or not at all, which
is what keeps Flutter the default whenever Linux is ticked.

## Presence

Presence is how the app stays visible and reachable when it is not in front: on a phone a
notification — status-bar icon, a card in the tray to tap, expand or act on. In React Native that is
**`expo-notifications` 57.0.18** (2026-09-11; Android, iOS — confirmed live 2026-09-12): local
notifications, one-off or repeating, *"Get and set the application badge icon number"*, *"Listen to
interactions with notifications"*, actions via `setNotificationCategoryAsync`, Android channels, push
tokens for FCM and APNs (its SDK page); what each OS allows is the native skills' `## Presence`. From
the page: exact-time schedules need `SCHEDULE_EXACT_ALARM` in `android.permissions`; Android 13's
prompt *"will not appear until at least one notification channel is created"*; push needs a
development build — *"unavailable in Expo Go on Android from SDK 53."*
**Desktop tray: none** — the module lists Android and iOS only, and no Expo module draws a tray icon.
**Alternative: `@notifee/react-native` 9.1.8** — *"feature rich"* (its description; GitHub active
2026-04-07): richer Android styles and a foreground service, neither in `expo-notifications`.

## UI

The UI is React components; the question is which component set. **Default: React Native's core
components** — `<View>`, `<Text>`, `<Image>`, `<ScrollView>`, `<TextInput>` — for which *"at runtime,
React Native creates the corresponding Android and iOS views"* (`ViewGroup`/`UIView`,
`EditText`/`UITextField`, …; reactnative.dev, confirmed live 2026-09-12), so *"React Native apps look,
feel, and perform like any other apps."* Navigation is **Expo Router** (57.0.21): *"When a file is
added to the app directory, the file automatically becomes a route"* (2026-09-03). "Same UI on both"
holds for layout and logic, not look: each component is the platform's own view, so one `<Switch>`
draws Android's on Android and Apple's on iOS. The concern line — when one platform must look a
specific way, RN's page says *"you may want to implement separate visual components for Android and
iOS"*: `Platform.select` or `Button.ios.tsx` / `Button.android.tsx`, per component, by hand. BACKLOG
#2's design system translates into the frameworks above.

## Storage

Storage is what the app keeps between launches: records and settings. **Saved data: `expo-sqlite`
57.0.3** (2026-09-11; Android, iOS, macOS, tvOS, web — confirmed live 2026-09-12): SQLite, plain
SQL, one file under `SQLite.defaultDatabaseDirectory` — `<filesDir>/SQLite` on Android, the documents
directory's `SQLite/` on iOS (its `SQLiteModule.kt` / `.swift` on `sdk-57`; wasm on web). **Config:
`expo-sqlite/kv-store`** — the same package's `Storage`, *"a drop-in replacement for the
@react-native-async-storage/async-storage library"*: no second dependency. Alternative:
**`@react-native-async-storage/async-storage`** — npm-latest **3.1.1** (2026-05-29), but
SDK 57 pins **2.2.0** (`bundledNativeModules.json`), so `npx expo install` gives 2.2.0; its README
(confirmed live 2026-09-12): SQLite on Android, iOS and macOS, IndexedDB on web. The concern that picks
it: a library you are adding already depends on it. External databases are out of scope.

## Where each store rule lands

The two store ingredients (`skills/orc-package/ingredients/play`, `.../app-store`) state the rules
and own them; this table says where each lands here. Nearly everything is a field in `app.json`
(`docs.expo.dev/versions/latest/config/app`, confirmed live 2026-09-12) that prebuild writes into the
native project — so each check runs on the generated file, after `npx expo prebuild --clean`. The
`Check` column's commands are Orclab's own, not taken from any page.

| Rule | Where it lands | Check |
|---|---|---|
| Target API 36 (Play, since 2026-08-31) | RN 0.86's catalog: `targetSdk` 36 by default. Override only via `expo-build-properties` (`android.targetSdkVersion`). | `grep targetSdk android/build.gradle` after prebuild, or `npx expo-doctor` |
| 16 KB pages (Play) | RN *"is ready to fully support 16 KB page size"* since 0.77 (2025-01-21); third-party native modules are the risk. | `bundletool dump config --bundle=android/app/build/outputs/bundle/release/app-release.aab \| grep alignment` |
| Signed with the upload key (Play) | EAS: managed or `credentials.json` (git-ignored). Local: keystore in `android/app/`, passwords in `android/gradle.properties` or `~/.gradle/gradle.properties` — the template's release config signs with the **debug** keystore until you change it. | a release `.aab` not signed by `androiddebugkey` |
| Package name = `__PACKAGE__` (Play); bundle identifier = `__BUNDLE_ID__` (App Store) | `android.package` and `ios.bundleIdentifier` in `app.json` — *"needs to be unique on the Play Store"*, fixed once uploaded. | `grep applicationId android/app/build.gradle`; `grep -m1 PRODUCT_BUNDLE_IDENTIFIER ios/*.xcodeproj/project.pbxproj` |
| Version code increases (Play) / build number increases (App Store) | `android.versionCode` (integer) and `ios.buildNumber` (string) in `app.json`; `version` is the user-facing one for both. EAS can own them (`appVersionSource: remote` + `autoIncrement`). `/orc-version` should bump these. | Play and App Store Connect refuse a reused number |
| Permissions declared (Play) / usage strings (App Store) | `android.permissions` (added at prebuild; `android.blockedPermissions` removes a module's); `ios.infoPlist` for every `NS*UsageDescription`. Config plugins add their own. | merged `AndroidManifest.xml` under `android/app/build/intermediates/`; `plutil -p ios/<name>/Info.plist \| grep UsageDescription` |
| **Privacy manifest** (App Store; ITMS-91061 at upload) | `ios.privacyManifests` in `app.json` — `NSPrivacyAccessedAPITypes` with reasons — written into `PrivacyInfo.xcprivacy` at prebuild. Expo's guide (2026-07-29): *"All Expo SDK packages that use 'required reason' APIs file have a PrivacyInfo file included"*, but *"Apple does not correctly parse all the PrivacyInfo files included by static CocoaPods dependencies"*, so copy each dependency's reasons from `node_modules/<pkg>/ios/PrivacyInfo.xcprivacy` into `app.json`. | `ls ios/<name>/PrivacyInfo.xcprivacy` after prebuild; Xcode's Generate Privacy Report on the Mac or the EAS build log |
| Built with Xcode 26 (App Store); Data safety / App Privacy, account deletion, privacy policy link, age rating | The build service's image, not the project; the rest is decided by the dependency list and app code, as in `stack-flutter` — one list answers both stores. | build log; `npm ls --depth=0` |

## Sources (live on 2026-09-12)

- Versions: `https://registry.npmjs.org/<pkg>` for `react-native`, `expo`, `react-native-web`, `react-native-windows`, `react-native-macos`, `expo-notifications`, `expo-sqlite`, `expo-router`, `jest-expo`, `@react-native-async-storage/async-storage`; `https://nodejs.org/dist/index.json`; `https://raw.githubusercontent.com/expo/expo/sdk-57/packages/expo/bundledNativeModules.json`
- React Native: `https://reactnative.dev/` (front page), `/docs/environment-setup`, `/docs/getting-started-without-a-framework`, `/docs/intro-react-native-components`, `/docs/platform-specific-code`, `/docs/out-of-tree-platforms`, `/blog` (0.87 2026-08-11, 0.82 2025-10-08, 0.80 2025-06-12), `/blog/2026/08/11/react-native-0.87`, `/blog/2025/01/21/version-0.77` (16 KB); `https://raw.githubusercontent.com/facebook/react-native/0.86-stable/packages/react-native/gradle/libs.versions.toml` (and `0.87-stable`)
- Expo docs (each also read as `.md`): `https://docs.expo.dev/versions/latest`, `/guides/new-architecture`, `/get-started/create-a-project`, `/get-started/start-developing`, `/workflow/continuous-native-generation` (`/workflow/prebuild` is a 404), `/guides/local-app-development`, `/guides/local-app-production`, `/build-reference/apk`, `/build-reference/app-versions`, `/app-signing/local-credentials`, `/develop/unit-testing`, `/workflow/web`, `/guides/publishing-websites`, `/guides/dom-components`, `/guides/monorepos`, `/router/introduction`, `/versions/latest/sdk/notifications`, `/versions/latest/sdk/sqlite`, `/versions/latest/sdk/async-storage`, `/versions/latest/config/app`, `/guides/apple-privacy`, `/versions/latest/sdk/build-properties`; `https://expo.dev/changelog/sdk-57`
- Expo source on `sdk-57`: `templates/expo-template-default` (`app.json`, `gitignore`, `package.json`, `src/`), `templates/expo-template-bare-minimum/{ios/Podfile,android/app/build.gradle,android/gradle.properties}`, `packages/expo-modules-autolinking/.../ExpoRootProjectPlugin.kt`, `packages/expo-sqlite/{android/src/main/java/expo/modules/sqlite/SQLiteModule.kt,ios/SQLiteModule.swift}` — all under `https://raw.githubusercontent.com/expo/expo/sdk-57/`
- Desktop and web: `https://necolas.github.io/react-native-web/docs/`, `https://microsoft.github.io/react-native-windows/docs/getting-started`, `.../docs/rnw-dependencies`, `https://raw.githubusercontent.com/microsoft/react-native-macos/main/README.md`, `https://raw.githubusercontent.com/react-native-async-storage/async-storage/main/README.md`, `https://api.github.com/repos/react-native-skia/react-native-skia/commits`; Notifee: `https://notifee.app/react-native/docs/overview`, `.../docs/android/styles`, `https://registry.npmjs.org/@notifee/react-native`, `https://api.github.com/repos/invertase/notifee/commits`
- Against Flutter (2026-09-12): `https://docs.flutter.dev/platform-integration/web/faq`
- EAS: `https://docs.expo.dev/build/setup.md`, `/submit/ios.md`, and `stack-flutter`'s `### Building without a Mac` with Task 8's report (`/build/setup`, `/app-signing/managed-credentials`, `expo.dev/pricing`); store rules: the Play and App Store ingredients under `skills/orc-package/ingredients/`.
