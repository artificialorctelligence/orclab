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
Flutter is the default (`stack-flutter`'s `### Building without a Mac`: EAS Build takes only React
Native projects, but Codemagic builds and signs Flutter for iOS, so iOS-from-Linux does not force
this stack). The concern that moves a project here: **the team already writes React, or the web
target is a real website** — *"React primitives
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
2026-09-03) builds in Expo's cloud with generated credentials — the keystore and distribution
certificate included: *"When you run `eas build`, you will be prompted to generate credentials if
you have not done so already … Where needed, they will be stored on EAS servers"*
(`docs.expo.dev/app-signing/managed-credentials`, confirmed live 2026-09-12); `eas submit` uploads
with the API key and *"works on macOS, Linux, and Windows"* (`/submit/ios`). Free plan: *"15
Android and 15 iOS builds"* a month, then a flat rate per build — iOS **$2** on a medium worker,
**$4** on a large one (`expo.dev/pricing`, confirmed live 2026-09-12). Concern that picks Codemagic
instead: a `codemagic.yaml` already in the repo — it has a React Native quick-start.

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

A cross-family project — phones plus a website, or phones plus a desktop — is choosing between
Flutter drawing the same screens on every one of them and React drawing a real website beside
native phone widgets. Both cross-family rows of `/orc-code`'s Defaults Table default to Flutter; the comparison
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

## Lint — where code-discipline lands

Expo's template lints with ESLint through `eslint-config-expo` (`npx expo lint`); the three
rules go in `eslint.config.js`, confirmed 2026-09-13 against ESLint 10.10.0's rule docs:

```js
rules: {
  "max-depth": ["error", 2],                                         // default 4
  "max-lines-per-function": ["error", { max: 60, skipBlankLines: true, skipComments: true }],  // default 50
  "no-empty": ["error", { allowEmptyCatch: false }],                 // a commented catch still passes
}
```

`no-empty` exempts a block that *"contains a comment"* — that is `code-discipline` rule 6's
"named, commented suppression"; `allowEmptyCatch: false` refuses only the bare one. Every rule at
`"error"`, and `eslint --max-warnings 0` for the CLI; typescript-eslint 8.70.0's
`strictTypeChecked` config is the type-level equivalent. Rules 2, 3 and 5 are reviewed, not linted.
The full `eslint.config.js`, with these three rules and five more, is written once in the
Security section below.

## Security — where security-discipline lands

`security-discipline`'s rules for this stack, confirmed live 2026-09-19;
no project has been through this yet, and the first one corrects it. A React Native app is an
Android app and an iOS app with JavaScript in the middle, so it is the *Every project* tier —
rules 1–4, rule 8's client half, and rule 5's shape extended to a URL another app handed it,
which the rule's text does not name — and each platform half is the native skill's:
`stack-android-native`'s Security section for what prebuild writes into `android/` (the
keystore, cleartext, the system trust store), `stack-ios-native`'s for `ios/` (the signing
identity, App Transport Security). Here those directories are generated, so the platform
settings arrive through `app.json`, and this section says which keys. It covers only what the
JavaScript layer adds: its linter, npm's audit, the module that wraps both platforms' secure
stores, and where a key must not go.

### Static analysis

**The plugin question is `stack-web`'s, already answered, and RN's own config does not change
it.** `eslint-plugin-security` 4.0.1 (2026-06-12, Apache-2.0; npm, read live 2026-09-19) is
fifteen rules, categorised in `stack-web`'s Security section against its README: eight Node-only,
one covered by an `eval` rule, six *"reviewed, not linted"* because the README's own verdict is
that it *"finds a lot of false positives which need triage by a human."* Neither config a React
Native project lints with depends on it — `eslint-config-expo` 57.0.2 (the template's, via
`npx expo lint`) pulls in `expo`, `react`, `react-hooks` and `import`; `@react-native/eslint-config`
0.87.1 (a bare project's) pulls in `react`, `react-hooks`, `react-native`, `jest`, `ft-flow`,
`eslint-comments` and typescript-eslint (both `package.json`s on npm, read live 2026-09-19). What
does change from `stack-web` is that this stack already runs ESLint, so the plugin is not a
second linter here: it *can* run beside either config as one `require` and one array entry
(its README's flat-config form, `pluginSecurity.configs.recommended`). It still does not,
because the six that could fire are the six that need a human, and the eight Node-only ones
would fire on `app.config.js` and `metro.config.js`, which the ESLint guide says *"are run in a
Node.js environment"*; a project that wants the hotspot list adds that one entry.

What the JavaScript layer owes on its own is what the browser half of `stack-web` owes — rule 5
at the point where a value is used — plus `eval`, and none of it is on in the template's config:
`eslint-config-expo/flat` spreads `pluginReact.configs.recommended.rules` (`utils/react.js` on
`sdk-57`, read live), and eslint-plugin-react's README marks `no-danger` and `jsx-no-script-url`
as in no preset — only `no-danger-with-children` is recommended; its `utils/core.js` sets
`eqeqeq`, `no-undef` and the like and no `eval` rule. So five entries go in the same `rules: {}`
object the Lint section opens — the generated file *"extends configuration from
`eslint-config-expo`"*, and every example in the ESLint guide (read live 2026-09-19) is a
`defineConfig([...])` holding `eslint-config-expo/flat` and a `dist/*` ignore, so the object
below is one more element of that array, written once with the Lint section's three plus these:

```js
// eslint.config.js
const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');

module.exports = defineConfig([
  expoConfig,
  { ignores: ['dist/*'] },
  {
    rules: {
      "max-depth": ["error", 2],                                         // default 4
      "max-lines-per-function": ["error", { max: 60, skipBlankLines: true, skipComments: true }],  // default 50
      "no-empty": ["error", { allowEmptyCatch: false }],                 // a commented catch still passes
      "react/no-danger": "error",                                        // dangerouslySetInnerHTML — the web half
      "react/jsx-no-script-url": "error",                                // javascript: in an href — the web half
      "no-eval": "error",                                                // eslint-plugin-security's one covered rule, as ESLint core
      "no-implied-eval": "error",                                        // setTimeout("…")
      "no-new-func": "error",                                            // new Function("…")
    },
  },
]);
```

`react/no-danger`: *"Dangerous properties in React are those whose behavior is known to be a
common source of application vulnerabilities"* — a `<View>` has no `dangerouslySetInnerHTML`,
but `react-native-web`'s DOM and any `.web.tsx` file do, and the rule reads the JSX. `no-eval`:
*"Using `eval()` on untrusted code can open a program up to several different injection
attacks"*; `no-implied-eval` is the string form of `setTimeout` and `setInterval`; `no-new-func`
the `Function` constructor (eslint's rule docs on `main`, read live 2026-09-19). None of the five
has been run against this template; the first project does, and records it. A web component
that must render HTML sanitises it first and suppresses `no-danger` on that one line with the
reason — `code-discipline`'s named, commented suppression; HTML handed to a WebView
(`react-native-webview`'s `source.html`, `injectedJavaScript`) is the same rule with no linter
reading it — reviewed. Rules 1, 3, 4, 5's shape and 8's client half
are otherwise **reviewed, not linted** in JavaScript: no ESLint rule reads `app.json`, and the
platform checks read directories that are generated and not in the repo. Whether Android Lint
runs on the generated `android/` at all — on EAS, or after a local prebuild — was not run here;
the first project records it. And the Android skill's `lint { warningsAsErrors = true }` block
lands in `app/build.gradle.kts`, which prebuild writes, so it has no route into a generated
`android/` until the first project finds one — a config plugin, or a committed `android/` (the
bare path), are the two candidates, neither confirmed.

### Dependency audit

One run, from `/orc-test audit`: `npm audit --json` on `package-lock.json` —
`skills/orc-test/languages/javascript.md`, `## Audit`; npm ships with Node, nothing to install
(rule 2). It reads the lock file and nothing under it: the Gradle and CocoaPods dependencies a
native module brings into the generated `android/` and `ios/` are not npm packages, so they are
not in the report — the Android skill's dependency-check plugin would have to be wired into a
generated directory, which no project has done; Swift packages and pods are none free
(`languages/swift.md`).

### Secrets

Three kinds of secret, three places, none of them a `.ts` file or `app.json` (rule 1; each
claim confirmed live 2026-09-19 against the page named):

- **The upload key and the signing identity.** On the `### Building without a Mac` default they
  are EAS's: *"Where needed, they will be stored on EAS servers"* (managed credentials, quoted
  there), so nothing is on disk here. The local alternative — the store table's row — is a
  keystore under `android/app/` with its passwords in `gradle.properties`, or EAS's
  `credentials.json` naming both; `.gitignore` gets `credentials.json`. The template's own
  `gitignore` (`expo-template-default` on `sdk-57`, read live) already ignores `*.jks`, `*.p8`,
  `*.p12`, `*.key`, `*.mobileprovision`, `*.pem`, `.env*.local` and the whole of `/android` and
  `/ios` — so a keystore left inside a generated directory is out of the repo by the directory's
  rule, and `credentials.json` and `.env` are the two lines it lacks.
- **A token the app holds for its user** (a session, a refresh token): **`expo-secure-store`**
  (57.0.4 on npm, MIT; SDK 57's page — `npx expo install expo-secure-store`; Android, iOS, tvOS),
  the module that wraps both platforms' stores, each the native skill's answer: on iOS *"values
  are stored using the keychain services as `kSecClassGenericPassword`"*, with *"the additional
  option of being able to set the value's `kSecAttrAccessible` attribute"* (`AFTER_FIRST_UNLOCK`
  and its `_THIS_DEVICE_ONLY` form are the page's own recommendations — the choice the iOS skill
  says to make on purpose); on Android *"values are stored in
  `SharedPreferences`, encrypted with Android's Keystore system"*. Three things its page makes
  the project know: *"Large payloads can be rejected by the underlying platform. Historically,
  some iOS releases refused values above roughly 2048 bytes"* — a token, not a document; on iOS
  the value *"will persist across app uninstallations when the app is reinstalled with the same
  bundle ID"*; and Android Auto Backup *"has to be configured to exclude `expo-secure-store`
  shared preferences entries, as it's impossible to decrypt them after restoring the backup"* —
  the Android skill's no-backup reasoning, arriving as an unreadable restore — which its config
  plugin does for you (*"If your app doesn't have any custom backup configuration,
  `expo-secure-store` will automatically configure the Auto Backup system to ignore the
  `expo-secure-store` data"*; a project with its own backup rules excludes `SecureStore` under
  `sharedpref` and sets `configureAndroidBackup` to `false`). reactnative.dev's security page
  names it (*"Some libraries to consider:
  expo-secure-store, react-native-keychain"*) and says what the Storage section's stores are
  not: Async Storage is *"an asynchronous, unencrypted, key-value store"*, and its *"Don't"*
  column is *"Token storage, Secrets"* — `expo-sqlite/kv-store` is its drop-in (the Storage
  section), and nothing on its page says encrypted.
- **An API key for a service the app calls.** reactnative.dev: *"Never store sensitive API keys
  in your app code. Anything included in your code could be accessed in plain text by anyone
  inspecting the app bundle"*, and the fix in its words: *"build an orchestration layer between
  your app and the resource ... which can forward the request with the required API key or
  secret."* That layer is the *Reachable by strangers* tier of whatever stack it is in — the
  Android skill's API-key paragraph, same answer. Expo's environment variables do not change
  it: *"Do not store sensitive info, such as private keys, in `EXPO_PUBLIC_` variables. These
  variables will be visible in plain-text in your compiled application"* — they are for a
  staging URL, and EAS Build inlines them from the `.env` files uploaded with the job. `extra`
  in `app.json` is *"accessible via `Constants.expoConfig.extra`"* — read by the app, so in the
  app.

Never in the built artifact: a keystore, `credentials.json`, a `.p8` or `.p12`, `.env`, `.git`
— and any `EXPO_PUBLIC_` value, which is there by construction. Nothing lints the bundle; the
first project lists it once (`unzip -l android/app/build/outputs/bundle/release/app-release.aab`
after a local build, or the EAS artifact) and records the answer here.

### Reachable by strangers

This stack does not accept connections: n/a — a phone app has no route to authenticate, no
error to sanitise and no rate to limit; the service it talks to carries rules 5–9 in its own
stack. What still applies is rule 8's client half, per platform as the native skills say it,
reached here through `app.json` because `android/` and `ios/` are generated: on Android
cleartext is off by default since API 28 (`stack-android-native`), and the `app.json` key that
turns it back on is `expo-build-properties`' `android.usesCleartextTraffic` — *"For Android 9
and above, the default platform-specific value is `false`"* (its SDK page, read live
2026-09-19) — so that key set to `true` is a finding, as is any config plugin that writes a
`network_security_config.xml`; on iOS App Transport Security refuses plain HTTP at runtime
(`stack-ios-native`), and a loosening lands as an `NSAppTransportSecurity` dictionary under
`ios.infoPlist` — *"No other validation is performed, so use this at your own risk of rejection
from the App Store"* (the app config reference) — so every loosening key there is the iOS
skill's finding, in `app.json` instead of Xcode, bar the dev-server exception that skill names
(`NSAllowsLocalNetworking`). reactnative.dev's own line:
*"Your APIs should always use SSL encryption"*; pinning (*"embedding (or pinning) a list of
trusted certificates to the client"*) tightens and is never a finding, with its page's own
warning that a pinned certificate expires with the server's. Rule 5's shape, the one input a
phone app takes from a stranger, in the page's words: *"Deep links are not secure and you should
never send any sensitive information in them"* — *"there is no centralized method of registering
URL schemes"*, so a URL that arrives through Expo Router or `Linking` is validated, matched
against the app's few paths and otherwise refused, the native skills' line; an OAuth redirect
needs PKCE for the same reason (the page's `react-native-app-auth`). And the API-key paragraph:
the bundle is not a secret store.

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
| Version code increases (Play) / build number increases (App Store) | `android.versionCode` (integer) and `ios.buildNumber` (string) in `app.json`; `version` is the user-facing one for both. EAS can own them (`appVersionSource: remote` + `autoIncrement`). `/orc-version` does not edit this file yet (its `versionfiles.py` handles `pyproject.toml`, `debian/changelog`, an AppStream metainfo file and the plugin manifests — BACKLOG #6); bump it by hand and check it before every upload. | Play and App Store Connect refuse a reused number |
| Permissions declared (Play) / usage strings (App Store) | `android.permissions` (added at prebuild; `android.blockedPermissions` removes a module's); `ios.infoPlist` for every `NS*UsageDescription`. Config plugins add their own. | merged `AndroidManifest.xml` under `android/app/build/intermediates/`; `plutil -p ios/<name>/Info.plist \| grep UsageDescription` |
| **Privacy manifest** (App Store; ITMS-91061 at upload) | `ios.privacyManifests` in `app.json` — `NSPrivacyAccessedAPITypes` with reasons — written into `PrivacyInfo.xcprivacy` at prebuild. Expo's guide (2026-07-29): *"All Expo SDK packages that use 'required reason' APIs file have a PrivacyInfo file included"*, but *"Apple does not correctly parse all the PrivacyInfo files included by static CocoaPods dependencies"*, so copy each dependency's reasons from `node_modules/<pkg>/ios/PrivacyInfo.xcprivacy` into `app.json`. | `ls ios/<name>/PrivacyInfo.xcprivacy` after prebuild; Xcode's Generate Privacy Report on the Mac or the EAS build log |
| Built with Xcode 26 (App Store); Data safety / App Privacy, account deletion, privacy policy link, age rating | The build service's image, not the project; the rest is decided by the dependency list and app code, as in `stack-flutter` — one list answers both stores. | build log; `npm ls --depth=0` |

## Sources (live on 2026-09-12)

- Security — where security-discipline lands (2026-09-19): `https://registry.npmjs.org/eslint-plugin-security` (+ `/latest`), its README `https://raw.githubusercontent.com/eslint-community/eslint-plugin-security/main/README.md`, and `stack-web`'s Security section for the fifteen-rule categorisation; `https://registry.npmjs.org/eslint-config-expo/latest`, `https://registry.npmjs.org/@react-native/eslint-config/latest`; `eslint-config-expo`'s flat config on `sdk-57`: `https://raw.githubusercontent.com/expo/expo/sdk-57/packages/eslint-config-expo/flat/{default.js,utils/core.js,utils/react.js}`; eslint-plugin-react's rule table `https://raw.githubusercontent.com/jsx-eslint/eslint-plugin-react/master/README.md` and `.../docs/rules/no-danger.md`; `https://raw.githubusercontent.com/eslint/eslint/main/docs/src/rules/{no-eval,no-implied-eval,no-new-func}.md`; `https://docs.expo.dev/guides/using-eslint.md` (the generated file, Node-environment files); audit: `skills/orc-test/languages/javascript.md`; `expo-secure-store`: `https://docs.expo.dev/versions/latest/sdk/securestore.md`, `https://registry.npmjs.org/expo-secure-store/latest`; `https://reactnative.dev/docs/security` (API keys, Async Storage, SSL, deep links, PKCE); `https://docs.expo.dev/guides/environment-variables.md` (`EXPO_PUBLIC_`); `https://docs.expo.dev/versions/latest/config/app.md` (`ios.infoPlist`, `extra`); `https://docs.expo.dev/versions/latest/sdk/build-properties.md` (`usesCleartextTraffic`); the template's `https://raw.githubusercontent.com/expo/expo/sdk-57/templates/expo-template-default/gitignore`; the platform halves and Google's API-key page: `stack-android-native`'s and `stack-ios-native`'s Security sections and their sources
- Lint — where code-discipline lands (2026-09-13): `https://raw.githubusercontent.com/eslint/eslint/main/docs/src/rules/{max-depth,max-lines-per-function,no-empty}.md`; versions from `https://registry.npmjs.org/<name>/latest`
- Versions: `https://registry.npmjs.org/<pkg>` for `react-native`, `expo`, `react-native-web`, `react-native-windows`, `react-native-macos`, `expo-notifications`, `expo-sqlite`, `expo-router`, `jest-expo`, `@react-native-async-storage/async-storage`; `https://nodejs.org/dist/index.json`; `https://raw.githubusercontent.com/expo/expo/sdk-57/packages/expo/bundledNativeModules.json`
- React Native: `https://reactnative.dev/` (front page), `/docs/environment-setup`, `/docs/getting-started-without-a-framework`, `/docs/intro-react-native-components`, `/docs/platform-specific-code`, `/docs/out-of-tree-platforms`, `/blog` (0.87 2026-08-11, 0.82 2025-10-08, 0.80 2025-06-12), `/blog/2026/08/11/react-native-0.87`, `/blog/2025/01/21/version-0.77` (16 KB); `https://raw.githubusercontent.com/facebook/react-native/0.86-stable/packages/react-native/gradle/libs.versions.toml` (and `0.87-stable`)
- Expo docs (each also read as `.md`): `https://docs.expo.dev/versions/latest`, `/guides/new-architecture`, `/get-started/create-a-project`, `/get-started/start-developing`, `/workflow/continuous-native-generation` (`/workflow/prebuild` is a 404), `/guides/local-app-development`, `/guides/local-app-production`, `/build-reference/apk`, `/build-reference/app-versions`, `/app-signing/local-credentials`, `/develop/unit-testing`, `/workflow/web`, `/guides/publishing-websites`, `/guides/dom-components`, `/guides/monorepos`, `/router/introduction`, `/versions/latest/sdk/notifications`, `/versions/latest/sdk/sqlite`, `/versions/latest/sdk/async-storage`, `/versions/latest/config/app`, `/guides/apple-privacy`, `/versions/latest/sdk/build-properties`; `https://expo.dev/changelog/sdk-57`
- Expo source on `sdk-57`: `templates/expo-template-default` (`app.json`, `gitignore`, `package.json`, `src/`), `templates/expo-template-bare-minimum/{ios/Podfile,android/app/build.gradle,android/gradle.properties}`, `packages/expo-modules-autolinking/.../ExpoRootProjectPlugin.kt`, `packages/expo-sqlite/{android/src/main/java/expo/modules/sqlite/SQLiteModule.kt,ios/SQLiteModule.swift}` — all under `https://raw.githubusercontent.com/expo/expo/sdk-57/`
- Desktop and web: `https://necolas.github.io/react-native-web/docs/`, `https://microsoft.github.io/react-native-windows/docs/getting-started`, `.../docs/rnw-dependencies`, `https://raw.githubusercontent.com/microsoft/react-native-macos/main/README.md`, `https://raw.githubusercontent.com/react-native-async-storage/async-storage/main/README.md`, `https://api.github.com/repos/react-native-skia/react-native-skia/commits`; Notifee: `https://notifee.app/react-native/docs/overview`, `.../docs/android/styles`, `https://registry.npmjs.org/@notifee/react-native`, `https://api.github.com/repos/invertase/notifee/commits`
- Against Flutter (2026-09-12): `https://docs.flutter.dev/platform-integration/web/faq`
- EAS: `https://docs.expo.dev/build/setup.md`, `/submit/ios.md`, `/app-signing/managed-credentials.md`, `https://expo.dev/pricing` (all 2026-09-12), and `stack-flutter`'s `### Building without a Mac`; store rules: the Play and App Store ingredients under `skills/orc-package/ingredients/`.
