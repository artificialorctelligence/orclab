---
name: stack-ios-native
description: Background knowledge for any work in a native iOS project (Swift, SwiftUI, Xcode) - creating one, building and archiving, configuring signing, versions, capabilities or usage strings, choosing a package, or preparing an App Store release. Says what the current toolchain is, where things live in the project, that a Mac is required and what that means from Linux, and where each App Store rule lands in the build. Not a command; Claude reads it when native iOS is in play.
user-invocable: false
---

# iOS native — Swift + SwiftUI

**Checked against live sources on 2026-09-11.** Xcode **27 RC** (2026-09-09; Swift 6.4; SDKs for
iOS 27; requires macOS Tahoe 26), with Xcode **26** (Swift 6.2, macOS 15) the **App Store
minimum** since 2026-04-28. Apple ships a major Xcode every September and raises the App Store
minimum every April; treat anything here older than one of those as suspect —
`orclab:currency-discipline` says re-check, and "Sources" says where.

**Nobody here has shipped a native iOS app yet.** Researched knowledge in BACKLOG #33's sense:
verified against Apple's current docs, not against a release. The first real app corrects it.

## When this is the stack

direflail's choice for **native iOS** (BACKLOG #4, 2026-09-11) — wanted *alongside* Flutter, not
instead of it. Right when the app is Apple-only, or needs what Flutter's plugins do not reach
(a new system framework, widgets, App Intents, watchOS/visionOS). Apple's own words: *"SwiftUI
helps you build great-looking apps across all Apple platforms with the power of Swift"* and it
*"is designed to work alongside UIKit and AppKit"* — UIKit is the older toolkit, reached from
SwiftUI when a control is missing, not the starting point for a new app. Swift has no Android
path. If Android is plausible later, start from the Android + iOS row instead — moving to it later
is a rewrite, not a port.

## The Mac requirement, stated once

**Every build, test run, archive and simulator needs macOS with Xcode.** Swift itself installs on
Linux (swift.org ships 6.3.3 for it), and that is enough to compile and test a pure-Swift
*package* — business logic, no UI — but there is no iOS SDK for Linux and never has been. From
this machine, an iOS project can be *edited* and its package layer *tested*; producing an `.ipa`
happens on a Mac at hand or a cloud Mac (named under "Building without a Mac" below). The App
Store ingredient
(`skills/orc-package/ingredients/app-store`) carries that choice as its `local` / `cloud`
question; this skill does not repeat it.

## Toolchain, as of 2026-09-11

| Thing | Current | Where it was read |
|---|---|---|
| Xcode | 27 RC (27A266a), Swift 6.4, iOS 27 SDK; runs on macOS 26 | developer.apple.com/news/releases; Xcode 27 release notes |
| App Store minimum | Xcode 26 / iOS 26 SDK since 2026-04-28 | developer.apple.com/news/upcoming-requirements |
| Swift | 6.4 in Xcode 27; 6.2 in Xcode 26; Swift 6 language mode has strict concurrency checking on — new projects should adopt it rather than stay in 5 mode | Xcode release notes |
| UI | SwiftUI; state via the `Observation` framework (`@Observable`) and SwiftUI property wrappers; navigation via `NavigationStack` | developer.apple.com/swiftui |
| Concurrency | Swift concurrency — `async`/`await`, actors, `@MainActor` for UI | Swift 6 language |
| Testing | **Swift Testing** (`import Testing`, `@Test`, `#expect`) for unit tests — Apple's current framework, integrated with SwiftPM; XCTest remains for UI tests (`XCUIApplication`). Coverage, mutation testing and test lint for this language: `skills/orc-test/languages/swift.md` — `/orc-test` reads it. | developer.apple.com/documentation/testing |
| Dependencies | Swift Package Manager, in Xcode (File → Add Package Dependencies) or `Package.swift`. CocoaPods is not for new projects — its registry goes read-only 2026-12-02 | Flutter's SwiftPM page records the CocoaPods date; Apple docs for SwiftPM |
| Persistence | SwiftData (Apple's current, Swift-native layer over Core Data) — the default under *Storage* below | developer.apple.com/documentation/swiftdata |
| Signing | Xcode's *Automatically manage signing* with the team selected; Xcode uses cloud-managed certificates | Xcode distribution docs |

Install (on the Mac): Xcode from the Mac App Store, then `xcode-select --install`, then
`xcodebuild -downloadPlatform iOS` for the simulator runtime. `xcodebuild -version` is the check.

## Project layout — where things live

Xcode's iOS App template (SwiftUI, Swift Testing) makes `<App>.xcodeproj` and:

| Path | What |
|---|---|
| `<App>/<App>App.swift` | The `@main` `App` struct — the entry point. |
| `<App>/ContentView.swift`, further `.swift` | Views and everything else. Group by feature, not by type; the template does not dictate. |
| `<App>/Assets.xcassets` | App icon (`AppIcon`), colours, images. The icon set must be complete for App Store upload. |
| `<App>/Info.plist` — often **absent** | Modern templates **generate** Info.plist from build settings (`GENERATE_INFOPLIST_FILE = YES`); values like `INFOPLIST_KEY_NSCameraUsageDescription` live in the target's *Info* tab / `project.pbxproj`. A project can opt back into a real file. Either way, the *Info* tab in Xcode is where to look. |
| `<App>/PrivacyInfo.xcprivacy` — **absent from the template** | Added by hand: File → New File → Resource → *App Privacy*, target = the app. Required for upload (see the table below). |
| `<App>/<App>.entitlements` | Capabilities (push, Sign in with Apple, iCloud) — added from *Signing & Capabilities*; each also has to be enabled on the bundle id on the developer site. |
| `<App>Tests/` | Swift Testing unit tests. `<App>UITests/` — XCTest UI tests. |
| `<App>.xcodeproj/project.pbxproj` | Where `PRODUCT_BUNDLE_IDENTIFIER`, `MARKETING_VERSION`, `CURRENT_PROJECT_VERSION`, `IPHONEOS_DEPLOYMENT_TARGET`, `DEVELOPMENT_TEAM` actually live. Edit through Xcode's target settings, not by hand. |
| `ExportOptions.plist` (project root, by convention) | Export method and signing for `xcodebuild -exportArchive`; Xcode writes one the first time you *Distribute App* by hand. Commit it. |
| `Package.swift` (optional) | A local package for the app's non-UI logic — the part that also compiles and tests on Linux. |

## Build, run, test (on the Mac)

```bash
xcodebuild -scheme <App> -destination 'platform=iOS Simulator,name=iPhone 17' test      # the check before any build
xcodebuild -scheme <App> -configuration Release -archivePath build/<App>.xcarchive archive
xcodebuild -exportArchive -archivePath build/<App>.xcarchive -exportOptionsPlist ExportOptions.plist -exportPath build/ipa   # -> build/ipa/<App>.ipa
```

`ExportOptions.plist` with `method = app-store-connect` exports an `.ipa` for the App Store
ingredient's action to upload; adding `destination = upload` makes `-exportArchive` upload it
itself (then the ingredient's `action:` is this command and there is no separate `.ipa`). The
older method name `app-store` still works but is deprecated. Confirm the exported filename with
`ls` after the first run rather than trusting this file. `swift test` at the root of a local
package runs its Swift Testing suite on any platform, Linux included.

### Building without a Mac

Apple's toolchain runs only on macOS, and this project *is* Xcode — there is no `xcodebuild` for
Linux and never has been. From this machine the Swift package layer can be edited and tested, but
the archive and the `.ipa` have to be produced on a Mac somewhere, so a Linux developer rents one
by the minute from a build service. Every service needs the same two things from you: a paid
Apple Developer Program membership, and an **App Store Connect API key** (App Store Connect →
Users and Access → Integrations) so it can talk to Apple on your behalf. They differ in whether
they generate the distribution certificate and provisioning profile, or expect you to supply them.

**Default: Codemagic** (confirmed live 2026-09-12) — the same default as `stack-flutter`, for the
same reasons. Its native-iOS quick-start: *"This guide will illustrate all of the necessary steps
to successfully build and publish a native iOS app with Codemagic. It will cover the basic steps
such as build versioning, code signing and publishing."* The build step is Codemagic's
`xcode-project build-ipa --workspace "$CM_BUILD_DIR/$XCODE_WORKSPACE" --scheme "$XCODE_SCHEME"`
(a wrapper over the `archive` + `-exportArchive` pair above) on `instance_type: mac_mini_m2`, with
Xcode 26.6 the default and 27.0 available as `edge` (its machine-spec pages, confirmed live
2026-09-12). Signing: add the API key in Team settings and
*"you can also generate a new Apple Development or Apple Distribution certificate"* there — the
private key never touches this machine — then `ios_signing: distribution_type: app_store` +
`bundle_identifier:` in `codemagic.yaml` fetches the matching profile, and
`xcode-project use-profiles` applies it before the build. Upload: `publishing: app_store_connect:`
with the same key. Cost: *"500 free minutes per month on macOS M2 machines on a personal
account"*, reset on the 1st; beyond that **$0.095/minute** on M2, $0.114 on M4 (no free minutes
on a Team). The App Store ingredient's `cloud` shape is written for this.

Alternatives (each confirmed live 2026-09-12), with the one thing that would make you reach for it:

- **Apple Xcode Cloud** — Apple's own, 25 compute hours/month included with the membership, and
  the natural home for a pure Xcode project. Concern: *"To get started, configure a workflow in
  Xcode"* — the first setup happens inside Xcode, so it needs a Mac once; with one at hand, even
  borrowed, prefer it over Codemagic for this stack.
- **GitHub Actions macOS runner** — already there if the repo is on GitHub; `macos-latest` is
  macOS 26 arm64 with Xcode 26.6 default and 27 on the `xcode-27` preview label. Concern:
  **signing is yours to script** — GitHub's guide has you export the certificate (`.p12`) and
  profile, base64 them into secrets and import into the runner's keychain; nothing is generated
  for you. Cost: **$0.062/minute** against $0.006 for Linux. GitHub's pages once documented a 10x
  multiplier on included minutes for macOS; the current pages give only the rate table, so
  whether the 2,000 free minutes deplete at the macOS rate is not stated (checked 2026-09-12,
  public repos are free either way).
- **EAS Build (Expo)** — not an option: its prerequisite is *"A React Native Android or iOS
  project"* and its pipeline runs `npm install` and `fastlane gym` in `ios/`; a plain Xcode
  project has no seat there.

## Lint — where code-discipline lands

SwiftLint 0.65.1 (`brew install swiftlint`; a build phase in Xcode or `swiftlint lint` in CI).
Its defaults are close already, confirmed 2026-09-13 in its rule sources:

```yaml
# .swiftlint.yml
nesting:
  function_level: { warning: 2, error: 2 }         # default is warning-only at 2, no error level
function_body_length: { warning: 60, error: 60 }   # default warning 50 / error 100
custom_rules:
  empty_catch:               # SwiftLint has no built-in empty-catch rule
    regex: 'catch\s*\{\s*\}'
    message: "an empty catch swallows the error — handle it, or name and comment the suppression"
    severity: error
  manual_server_trust:       # SwiftLint has no security rule either — see Security below
    regex: 'URLCredential\(trust:'
    message: "manual server trust — pinning is fine, accepting a certificate the system rejects is not; name and comment the suppression"
    severity: error
```

Warnings-as-errors is the compiler's: `-warnings-as-errors` (`swiftc`'s `Options.td`), set in
Xcode as `SWIFT_TREAT_WARNINGS_AS_ERRORS = YES` in the build settings (default `NO` — Apple's
`Swift.xcspec` in swift-build, confirmed 2026-09-13). Rules 2, 3 and 5 (`defer`, `precondition`
over `assert` — the Assert.swift docs say *"To check for invalid usage in Release builds, see
precondition"*) are reviewed, not linted.

## Security — where security-discipline lands

`security-discipline`'s rules for this stack, confirmed live 2026-09-19;
no project has been through this yet, and the first one corrects it. A phone app is the
*Every project* tier — it accepts no connections — so rules 1–4 apply in full, and of 5–9 only
what a client owes: rule 8's own client half (whether it checks the certificate of the server it
talks to — which on iOS the platform does, unless the app opts out), and rule 5's *shape* —
untrusted input reaching the point where it is used — extended here to a URL another app handed
it, which the rule's text does not name. The server it talks to carries 5–9 in its own stack.
`stack-kotlin-multiplatform`'s Security section reads this one for `iosApp/`.

### Static analysis

**SwiftLint has no security rule — none free.** Its rule directory for 0.65.1 (read live
2026-09-19) lists 256 rules — 102 default, 149 opt-in, 5 analyzer — and none is about a
credential, a certificate, HTTP, cryptography or injection; the one whose name suggests it,
`legacy_random`, is style: *"Prefer using type.random(in:) over legacy functions"*. What iOS has
instead is the platform: App Transport Security refuses a plain-HTTP connection at runtime (the
last subsection), and the App Store rejects an upload without a privacy manifest (the store
table). So this section adds one rule of Orclab's own, the same shape as the Lint section's
`empty_catch` — a regex custom rule — for the one client-side rule with a signature in Swift
code:

- **Rule 8's client half: `manual_server_trust`**, the entry in the Lint section's
  `.swiftlint.yml` above. Apple's *Performing manual server trust authentication* (read live
  2026-09-19): in `URLSession`, app code that wants to *"accept server credentials that would
  otherwise be rejected by the system"* — its example is *"a development server that uses a
  self-signed certificate"* — implements `urlSession(_:didReceive:completionHandler:)` and
  answers with `URLCredential(trust: serverTrust)` and `.useCredential`, the page's own listing.
  Certificate pinning — *"reject credentials that would otherwise be accepted"* — goes through
  the same call and is tightening, not a finding. So every `URLCredential(trust:` is one or the
  other; the rule fires on both, and pinning code names and comments the suppression
  (`// swiftlint:disable:next manual_server_trust`), which is `code-discipline`'s form. The
  loosening case does not even work while ATS covers the domain — *"You cannot loosen server
  trust requirements for an ATS-protected domain, but you can tighten them"* — so in
  `URLSession` it only works alongside an Info.plist exception, and the archive check in the
  last subsection is the other half of the same rule. Below `URLSession` nothing lints: *"ATS doesn't apply to
  calls your app makes to lower-level networking interfaces like the Network framework or
  CFNetwork"* — a project on those is reviewed.
- **Rules 1, 3, 4 and 5's shape: reviewed, not linted.** SwiftLint reads Swift files only, and
  there is no linter for the plist or the entitlements. Rule 1 (a token typed into a Swift
  file); rule 3 (a download run without a check — on iOS also a review rule: 2.5.2, *"Apps should
  be self-contained in their bundles ... nor may they download, install, or execute code which
  introduces or changes features or functionality of the app"*, read live 2026-09-19); rule 4,
  which the template scaffolds — no `.entitlements` file until a capability is added in
  *Signing & Capabilities*, no usage string until an `INFOPLIST_KEY_NS*UsageDescription` is set
  (the layout table), so each is a diff someone can see — and whether the code uses what was
  granted is reviewed; rule 5's shape (a URL from another app, the last subsection).

### Dependency audit

None free: SwiftPM has no advisory check — `skills/orc-test/languages/swift.md`, `## Audit`,
says what was checked, and `/orc-test audit` prints `audit not available` with that sentence
(rule 2). Re-read 2026-09-19: swiftlang/swift-package-manager's `main` is still `39b373a`, the
commit that page names, and `Sources/Commands/PackageCommands/` still holds the same subcommands
— nothing new. The store table's privacy-manifest row is the nearest thing this stack has to a
supply-chain check: each package with native code ships its own, and the upload is rejected
when one is missing.

### Secrets

Three kinds of secret, three places, none of them a source file (rule 1; every quotation below
confirmed live 2026-09-19 on developer.apple.com unless said otherwise):

- **The signing identity and the upload key.** With the toolchain row's *Automatically manage
  signing*, the distribution certificate is cloud-managed — *"associated with your Apple
  Developer Program membership and managed remotely"* (Developer Account Help), and *"Xcode
  automatically creates and shares cloud-managed certificates among your team, so you don't need
  to manually export cloud-managed certificates"* (Xcode's *Synchronizing code signing
  identities* page) — so there is no private key on disk to leak. A manually managed identity
  sits in the Mac's login keychain, and its export is a password-protected `.p12`: *"Anybody
  who gets access to the exported signing identity and learns (or guesses) the password can
  distribute signed software that appears to users and the operating system to come from your
  Apple Developer account."* That `.p12`, and the App Store Connect API key's `.p8` —
  downloadable *"a single time"*, *"Apple doesn't keep a copy of the private key"*, and *"Don't
  share your keys, store keys in a code repository, or include keys in client-side code"* (App
  Store Connect API, *Creating API Keys*) — go into the build service's secret store, which is
  where the Building-without-a-Mac section already puts them (Codemagic's Team settings;
  GitHub's guide base64s the `.p12` and the profile into Actions secrets), never into the
  working tree. `ExportOptions.plist`, which the layout table says to commit, holds the team id
  and the export method, not a key.
- **A token the app holds for its user** (a session, a refresh token): the **Keychain**, through
  `SecItemAdd` with `kSecClassGenericPassword` — *"an encrypted database called a keychain"*,
  and on iOS *"An app can access only its own keychain items, or those shared with a group to
  which the app belongs"* (*Keychain services*; *Keychains*). `Security` is a system framework;
  nothing to install. Not `UserDefaults` — the Storage section quotes Apple's *"Don't store
  personal or sensitive information as settings"*. Set `kSecAttrAccessible` on purpose: the
  default is `kSecAttrAccessibleWhenUnlocked`, and *"A device without a passcode is considered
  to always be unlocked"*; `kSecAttrAccessibleAfterFirstUnlock` is for a token a background
  fetch needs; a `ThisDeviceOnly` variant when the token must not follow a backup to a new
  phone — *"it isn't migrated when restoring another device's backup data"*; and
  `kSecAttrAccessibleAlways` *"isn't recommended"*. *"Always use the most restrictive option
  that makes sense for your app"* (*Restricting keychain item accessibility*).
- **An API key for a service the app calls.** The bundle is public — anyone with the `.ipa` can
  unpack it — so a key in it is a key everyone has. Google's API-key page
  (docs.cloud.google.com, dated 2026-09-16, platform-neutral): *"Don't include API keys in
  client code or commit them to code repositories"*; *"The client should pass requests to the
  server, which can add the credential and issue the request."* Apple's own line for its API
  key above says the same. That server is the *Reachable by strangers* tier of whatever stack
  it is in. Unlike Android there is no vendor-blessed key that ships in the bundle here — none
  found, and the first project that needs one records it.

`.gitignore`: `*.p12`, `*.p8`, and `.netrc` — the last is where `swift package-registry login`
stores a registry credential when the macOS keychain is not used (*"SwiftPM will save the
credentials to the operating system's credential store (e.g., Keychain in macOS) or netrc
file"*, its registry usage doc), and `swift package init`'s own `.gitignore` already lists it
alongside `xcuserdata/` and `DerivedData/` (`InitPackage.swift` on `main`, read live
2026-09-19). Whether Xcode's app template writes a `.gitignore` at all was not checked from
Linux; the first project on a Mac records it. Never in the built `.ipa`: a `.p12`, a `.p8`, a
`.netrc`, `.git`, `xcuserdata/`. Nothing lints the archive; the first project lists it once
(`unzip -l build/ipa/<App>.ipa`) and records the answer here.

### Reachable by strangers

This stack does not accept connections: n/a — a phone app has no route to authenticate, no
error to sanitise and no rate to limit; the service it talks to carries rules 5–9 in its own
stack. What still applies is rule 8's client half, which iOS enforces by default: App Transport
Security is on for every app linked against the iOS 9 SDK or later, *"requires that all HTTP
connections made with the URL Loading System — typically using the URLSession class — use
HTTPS"*, demands TLS 1.2 or later, SHA-256 and forward secrecy on top of the certificate
checks, and *"blocks connections that fail to meet minimum security specifications"* (the
`NSAppTransportSecurity` key page and *Preventing Insecure Network Connections*, read live
2026-09-19). A plain `http://` URL fails at runtime with *"App Transport Security has blocked a
cleartext HTTP (http://) resource load since it is insecure."* Loosening it is an
`NSAppTransportSecurity` dictionary in the target's Info tab — where the layout table says every
Info.plist value lives — and every loosening key is a finding in a release build:
`NSAllowsArbitraryLoads` (*"You must supply a justification during App Store review if you set
the key's value to YES"*) and the four others on Apple's justification list —
`NSAllowsArbitraryLoadsForMedia`, `NSAllowsArbitraryLoadsInWebContent`, a per-domain
`NSExceptionAllowsInsecureHTTPLoads`, a per-domain `NSExceptionMinimumTLSVersion` — which
*"might trigger additional App Store review for your app"*. The App Review Guidelines
themselves do not name ATS (read live 2026-09-19; the nearest is 1.6, *"Apps should implement
appropriate security measures"*): the cost is the justification Apple asks for at submission,
not a numbered rule. A development server: `NSAllowsLocalNetworking` — *"unqualified domains,
`.local` domains, and IP addresses"* — is the one exception not on that list, and its page says
that since iOS 17 a bare IP address needs an `NSExceptionDomains` entry, so run the dev server
under a `.local` name or over HTTPS rather than carrying an HTTP exception into the archive.
Pinning (`NSPinnedDomains`, or the delegate `manual_server_trust` watches) tightens and is never
a finding. The check, on the archived product, beside the store table's usage-string check:

```bash
plutil -p build/<App>.xcarchive/Products/Applications/<App>.app/Info.plist | grep -A8 NSAppTransportSecurity   # nothing, or only NSAllowsLocalNetworking / NSPinnedDomains
```

Rule 5's shape, for the one input a phone app does take from a stranger: a URL another app or a
web page handed it — a custom scheme or a universal link, arriving in SwiftUI through
`onOpenURL(perform:)`. Apple: *"URL schemes offer a potential attack vector into your app, so
make sure to validate all URL parameters and discard any malformed URLs"*, and *"don't allow
other apps to directly delete content or access sensitive information about the user"*
(*Defining a custom URL scheme for your app*, read live 2026-09-19) — parse with
`URLComponents`, match against the few paths the app defines, refuse the rest. And the API-key
paragraph above: the bundle is not a secret store.

## Containers

Runs in a container: **no** — confirmed live 2026-09-20. Every build, test run, archive and
simulator needs macOS with Xcode ("The Mac requirement, stated once", above), and a container on
this machine is a Linux machine: there is no iOS SDK for Linux and never has been, so nothing in
`## Build, run, test` — `xcodebuild … test`, `archive`, `-exportArchive` — can run inside one, and
neither can `/orc-test`'s app-target path (`skills/orc-test/languages/swift.md`: `xcodebuild
test`, `xcrun xccov`, and Muter, whose README says it *"can run only on macOS 10.15 or higher"*,
read live 2026-09-20). What could run headless in a container is the one part that already runs
on Linux: a local `Package.swift` layer (the layout table's optional row), whose `swift test`
needs no Xcode. Its image is the official `swift` image on Docker Hub — `6.4-trixie` is Swift
6.4.0 on Debian trixie, pushed 2026-09-19, 1.41 GB compressed (`6.4-trixie-slim`, 118 MB, is the
runtime without the compiler, so not for tests) — and SwiftLint 0.65.1's release assets include
`swiftlint_linux_amd64.zip` (67 MB), so a package's tests and its lint could run inside; no
Dockerfile is written for it, because a package layer without the app it serves is not this
stack, and nothing measures its mutation score off a Mac. The container-shaped answer that
exists for the app itself is the cloud Mac: "Building without a Mac" above rents one by the
minute (Codemagic's `mac_mini_m2` by default), which is a machine somewhere else, not a container
here. `/orc-code` skips the container question for this stack.

## Presence

No project has been built with these facets yet; the first one corrects them. Presence is how
the app stays visible and reachable when it is not in front. **iOS has no app-owned status-bar
icon.** The strip at the top of the screen is the system's: the Human Interface Guidelines say it
*"displays information about the device's current state, like the time, cellular carrier, and
battery level"*, and the developer documentation it points to is `UIStatusBarStyle` and
`preferredStatusBarStyle` — an app can restyle or hide the bar, never put anything in it
(confirmed live 2026-09-12). So an iOS app is present in two ways: a notification the user acts
on, and — for something ongoing — a Live Activity.

**Notifications: the `UserNotifications` framework.** Apple: notifications *"communicate important
information to users of your app, regardless of whether your app is running"*; each one *"can
display an alert, play a sound, or badge the app's icon"*, generated *"locally from your app or
remotely from a server that you manage"* through APNs (confirmed live 2026-09-12). The HIG names
the shapes: *"A banner or view on a Lock Screen, Home Screen"*, *"A badge on an app icon"*, *"An
item in Notification Center"*. Nothing shows until the user agrees: call
`UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge])`, in
context rather than at first launch — *"Subsequent authorization requests don't prompt the
person"*, so the first answer stands; the `.provisional` option delivers quietly to Notification
Center only, on trial, with Keep / Turn Off buttons (confirmed live 2026-09-12). A local
notification is `UNMutableNotificationContent` plus a time, calendar or location trigger in a
`UNNotificationRequest`; delivery *"isn't guaranteed"*.

What the user can do without opening the app — **actions via categories** (confirmed live
2026-09-12, *Declaring your actionable notification types*): *"Actionable notifications let the
user respond to a delivered notification without launching the corresponding app. Other
notifications display information in a notification interface, but the user's only course of
action is to launch the app."* Register `UNNotificationCategory` objects at launch with
`setNotificationCategories`, each holding `UNNotificationAction` buttons; put the category's
identifier in the content's `categoryIdentifier` (or the `category` key of a push payload). A
`UNTextInputNotificationAction` shows *"an editable text field"* — reply without opening the app.
Tapping a button *"forwards the selected action to your app, without bringing the app to the
foreground"*, handled in `UNUserNotificationCenterDelegate` (*Handling notifications and
notification-related actions*, confirmed live 2026-09-12). Remote (push) notifications add the
*APS Environment* entitlement, listed on the framework page; local ones need nothing beyond the
permission.

**The nearest persistent presence: a Live Activity (`ActivityKit`, iOS 16.1+).** The framework
page (confirmed live 2026-09-12): Live Activities are *"a rich, interactive, and highly glanceable
way for people to keep track of an event or activity over several hours"*; on iPhone and iPad one
*"appears on the Lock Screen, in the Dynamic Island, and on the Home Screen"*, and also on a paired
Apple Watch's Smart Stack, a paired Mac's menu bar and CarPlay; *"visionOS doesn't support Live
Activities."* Its *Displaying live data with Live Activities* article (confirmed live 2026-09-12)
does not name which iPhones have a Dynamic Island — on *"devices that don't support the Dynamic
Island"* the Lock Screen presentation appears as a banner instead. The UI is
SwiftUI inside a widget extension (`ActivityConfiguration`, a Lock Screen view plus compact,
minimal and expanded Dynamic Island views — all required); the app starts, updates and ends it
with `Activity`, or a server does by ActivityKit push; `NSSupportsLiveActivities = YES` in the
target's Info. Buttons and toggles let people *"perform essential functionality without launching
your app"*. Limits: *"active for up to eight hours"*, at most 12 on the Lock Screen; its own
sandbox, *"can't access the network or receive location updates"*; 4 KB of data. Reach for it only
when there is a real ongoing thing to track — a timer, an order, a game; otherwise a notification.

## UI

No project has been built with these facets yet; the first one corrects them. The UI is what the
user sees and touches; on iOS the choice is which of Apple's two toolkits draws it. **Default:
SwiftUI** — the toolchain row above; *"Declare the user interface and behavior for your app on
every platform"*, actively updated (its updates page's latest section is June 2026, Liquid Glass)
(confirmed live 2026-09-12 on `developer.apple.com/documentation/swiftui`). **Alternative: UIKit**
— also current (its own June 2026 updates section; iOS 2.0+, not deprecated) — only for an
existing UIKit codebase being extended rather than rewritten, or a specific control SwiftUI lacks.
The two mix per view, never per project: Apple's UIKit page says *"you can place UIKit views and
view controllers inside SwiftUI views, and vice versa"* — `UIViewRepresentable` wraps a `UIView`
into SwiftUI (*"a wrapper for a UIKit view that you use to integrate that view into your SwiftUI
view hierarchy"*), `UIViewControllerRepresentable` a view controller, and `UIHostingController`
goes the other way (confirmed live 2026-09-12). BACKLOG #2's design system translates into the
frameworks above.

## Storage

No project has been built with these facets yet; the first one corrects them. Storage is what the
app keeps on the device between launches: records the user creates (a database) and settings
(config). Everything below lives inside the app's own sandboxed data container — Apple's (archived,
still the only page naming the layout) file-system guide: *"an iOS app's interactions with the file
system are limited to the directories inside the app's sandbox directory"*, with `Documents/` for
user-visible files, `Library/Application Support` and `Library/Caches` for the app's own, `tmp/`
for scratch; the current backup page confirms `/tmp` and `/Library/Caches` are purged and excluded
from iCloud Backup and anything else *"may"* be included (confirmed live 2026-09-12). External
databases are out of scope for this skill.

**Saved data: SwiftData (`import SwiftData`, iOS 17+).** Apple: *"Combining Core Data's proven
persistence technology and Swift's modern concurrency features, SwiftData enables you to add
persistence to your app quickly, with minimal code and no external dependencies"* — `@Model` on a
class, `ModelContainer` via `.modelContainer(for:)` at the top of the view tree, `ModelContext` to
insert and delete, `@Query` in a view; still moving (June 2026: `sectionBy` queries, `Codable`
attributes, `ResultsObserver`) (confirmed live 2026-09-12). Where the file sits: the docs give
`ModelConfiguration.url` — *"the on-disk location of the schema's persistent storage"* — but do not
name the default path; assume the app container and pass a `url` when it matters. **Alternative:
Core Data** — the layer SwiftData sits on, iOS 3.0+, not deprecated — only for an existing Core
Data model being extended, Objective-C sources, or a UIKit screen that wants Core Data's *"data
sources for table and collection views"*; the SwiftData framework page lists *Adopting SwiftData
for a Core Data app* for the move (confirmed live 2026-09-12).

**Config: `UserDefaults`** (Foundation; SwiftUI's `@AppStorage` *"reflects a value from
`UserDefaults`"* into a view). Apple: *"a persistent store for app-specific and system-wide
settings"* — property-list types only; *"stores defaults
locally on the current device"*, *"in an unencrypted format"*, included in device backups;
*"Don't store personal or sensitive information as settings"* — that is the Keychain; and *"Don't
access the files of the defaults database directly"* (confirmed live 2026-09-12). Two hooks into
the store table below: reading `UserDefaults` is a required-reason API, so
`NSPrivacyAccessedAPITypes` in `PrivacyInfo.xcprivacy` must list it with a reason; and it is
device-local — cross-device settings are `NSUbiquitousKeyValueStore`, not decided here. Neither is
for records: a settings screen's toggles go here, anything with rows goes to SwiftData.

## Where each App Store rule lands

The App Store ingredient states the rules and owns them. This table is the other half.

| Rule (App Store ingredient) | Where it lands | Check |
|---|---|---|
| Built with Xcode 26 / iOS 26 SDK or newer (since 2026-04-28) | The Mac's Xcode. Nothing in the project pins it; `IPHONEOS_DEPLOYMENT_TARGET` is the *minimum* OS the app runs on, a separate choice (Apple's template defaults to the current major minus a little; older lowers reach, raises maintenance). | `xcodebuild -version` on the build Mac ≥ 26 |
| **Privacy manifest** (rejected at upload if wrong) | `PrivacyInfo.xcprivacy` in the app target — **not in Xcode's template, add it**. Declares `NSPrivacyCollectedDataTypes`, `NSPrivacyAccessedAPITypes` with reason codes for every required-reason API the app *and its packages* call (UserDefaults, file timestamps, system boot time, disk space, active keyboards), and `NSPrivacyTracking`/tracking domains. Each Swift package with native code ships its own; App Store Connect's rejection email (ITMS-91061 / 91053) names the offender. | `ls <App>/PrivacyInfo.xcprivacy`; after archiving, Xcode → Product → *Generate Privacy Report* shows the merged declaration |
| Public APIs only, currently shipping OS (2.5.1) | Apple's frameworks by construction; a third-party package is the risk. | — |
| Bundle identifier | `PRODUCT_BUNDLE_IDENTIFIER` in target settings; set at project creation from the organisation identifier. Must match the identifier registered on the developer site and the ingredient's `__BUNDLE_ID__`. | Xcode → target → General → Identity |
| Signing (distribution certificate + App Store profile) | *Signing & Capabilities* → *Automatically manage signing*, team selected; `ExportOptions.plist` `method = app-store-connect`, `signingStyle = automatic`. | an archive that exports without a signing error |
| Permission usage strings | `INFOPLIST_KEY_NS*UsageDescription` build settings (or `Info.plist` keys) for every capability the app touches — camera, photos, location, microphone, contacts, Bluetooth, local network, tracking. Missing one is a crash on first use and a rejection. | Xcode → target → Info; or `plutil -p build/<App>.xcarchive/Products/Applications/<App>.app/Info.plist \| grep UsageDescription` on the archived product |
| Privacy policy reachable in-app (5.1.1(i)) | A view with a link — settings or about. | — |
| Account deletion in-app (5.1.1(v)); private login alongside any social login (4.8) | App code. Sign in with Apple = the *Sign in with Apple* capability on the target and the bundle id, plus `AuthenticationServices`. | *Signing & Capabilities* lists it |
| Build number increases every upload | `CURRENT_PROJECT_VERSION` (build) and `MARKETING_VERSION` (version) in target settings. `/orc-version` does not edit this file yet (its `versionfiles.py` handles `pyproject.toml`, `pubspec.yaml`, `debian/changelog`, an AppStream metainfo file and the plugin manifests — BACKLOG #6); bump it by hand and check it before every upload. A handler must edit both and refuse a bump that leaves the build number unchanged. | App Store Connect refuses a reused build number for the same version |
| iPhone apps should run on iPad (2.4.1) | Target → General → *Supported Destinations*: iPhone and iPad both listed, and the layout tested on an iPad simulator. | `xcodebuild -showdestinations -scheme <App>` |
| Age rating, App Privacy answers, EU trader status | App Store Connect, not the project. App Privacy answers are decided by which packages you add — keep the list. | — |

## Choosing dependencies

Swift Package Manager only. Prefer Apple's frameworks first — they need no privacy manifest of
their own and never miss an SDK deadline. For a third-party package: does it ship a
`PrivacyInfo.xcprivacy` (look in its repo); is it maintained against the current Swift and Xcode;
what does it send off-device. `orclab:currency-discipline` applies to every version pin in
`Package.resolved`; Xcode's *Update to Latest Package Versions* is the tool.

**Deliberately not decided here**: networking beyond `URLSession`, backend, analytics. Project
choices; no preference recorded until direflail has one. (Persistence moved to *Storage* above,
2026-09-12.)

## Games

Not this stack. An iOS game is Unity or Godot, which produce their own Xcode project; the App
Store ingredient applies to it unchanged, including the privacy manifest and the Mac.

## Sources (live on 2026-09-11; facets and no-Mac builds 2026-09-12)

- Containers (2026-09-20): the official `swift` image's tags
  `https://hub.docker.com/v2/repositories/library/swift/tags/?name=6.4` (`6.4-trixie`,
  `6.4-trixie-slim`, pushed 2026-09-19); SwiftLint's release assets
  `https://api.github.com/repos/realm/SwiftLint/releases/tags/0.65.1`
  (`swiftlint_linux_amd64.zip`); Muter's README
  `https://raw.githubusercontent.com/muter-mutation-testing/muter/master/README.md` (macOS only)
- Security — where security-discipline lands (2026-09-19; Apple documentation pages read through
  their JSON form, as for the facets) — SwiftLint: `https://realm.github.io/SwiftLint/rule-directory.html`
  (0.65.1; 102 default, 149 opt-in, 5 analyzer rules, no security rule),
  `https://realm.github.io/SwiftLint/legacy_random.html`,
  `https://raw.githubusercontent.com/realm/SwiftLint/main/README.md` (regex custom rules;
  `swiftlint:disable:next`); Apple — `https://developer.apple.com/documentation/security/keychain-services`,
  `.../security/keychain-items`, `.../security/keychains`,
  `.../security/adding-a-password-to-the-keychain`,
  `.../security/restricting-keychain-item-accessibility`,
  `.../security/item-attribute-keys-and-values` (the seven accessibility values),
  `.../security/preventing-insecure-network-connections`,
  `https://developer.apple.com/documentation/bundleresources/information-property-list/nsapptransportsecurity`,
  `.../nsapptransportsecurity/nsallowsarbitraryloads`, `.../nsapptransportsecurity/nsallowslocalnetworking`,
  `https://developer.apple.com/documentation/foundation/performing-manual-server-trust-authentication`,
  `https://developer.apple.com/documentation/xcode/sharing-your-teams-signing-certificates`,
  `https://developer.apple.com/help/account/create-certificates/cloud-managed-certificates`,
  `https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api`,
  `https://developer.apple.com/documentation/xcode/defining-a-custom-url-scheme-for-your-app`,
  `https://developer.apple.com/documentation/swiftui/view/onopenurl(perform:)`,
  `https://developer.apple.com/app-store/review/guidelines/` (2.5.2 and 1.6; no mention of ATS,
  HTTPS or keychain anywhere on the page); API keys, platform-neutral:
  `https://docs.cloud.google.com/docs/authentication/api-keys-best-practices`; SwiftPM —
  `https://github.com/swiftlang/swift-package-manager` (`main` at 39b373a, the commit
  `skills/orc-test/languages/swift.md` names; `Sources/Commands/PackageCommands/` listed again),
  `https://raw.githubusercontent.com/swiftlang/swift-package-manager/main/Sources/Workspace/InitPackage.swift`
  (the `.gitignore` `swift package init` writes),
  `https://raw.githubusercontent.com/swiftlang/swift-package-manager/main/Documentation/PackageRegistry/PackageRegistryUsage.md`
  (keychain or `.netrc` for registry credentials)
- Lint — where code-discipline lands (2026-09-13): `https://raw.githubusercontent.com/realm/SwiftLint/main/Source/SwiftLintBuiltInRules/Rules/{Metrics/NestingRule,RuleConfigurations/NestingConfiguration,Metrics/FunctionBodyLengthRule}.swift`, `.../Models/BuiltInRules.swift` (no empty-catch rule), `https://raw.githubusercontent.com/swiftlang/swift/main/include/swift/Option/Options.td` (`-warnings-as-errors`), `https://raw.githubusercontent.com/swiftlang/swift-build/main/Sources/SWBUniversalPlatform/Specs/Swift.xcspec`, `https://raw.githubusercontent.com/swiftlang/swift/main/stdlib/public/core/Assert.swift`
- Current releases: `https://developer.apple.com/news/releases/`; Xcode 27 and 26 release notes
  under `https://developer.apple.com/documentation/xcode-release-notes/`
- App Store minimum Xcode: `https://developer.apple.com/news/upcoming-requirements/`
- SwiftUI: `https://developer.apple.com/swiftui/`
- Swift Testing: `https://developer.apple.com/documentation/testing`
- Swift on Linux: `https://www.swift.org/install/`
- Privacy manifests: `https://developer.apple.com/documentation/bundleresources/adding-a-privacy-manifest-to-your-app-or-third-party-sdk`
  (and that Xcode's app template does not include one — Apple's own steps are "File → New File
  → App Privacy", which is only needed because it is absent)
- Distribution: `https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases`;
  `-exportArchive` with `destination = upload`: Apple's *Archive export files* help page
- Store rules themselves: the App Store ingredient under `skills/orc-package/ingredients/app-store`, with its own sources.
- Facets (2026-09-12; every `developer.apple.com/documentation/...` and `/design/human-interface-guidelines/...` page was read through its JSON form, `/tutorials/data/` + `.json`, because the HTML is script-rendered) — presence: `https://developer.apple.com/design/human-interface-guidelines/status-bars`, `https://developer.apple.com/design/human-interface-guidelines/notifications`, `https://developer.apple.com/design/human-interface-guidelines/live-activities`, `https://developer.apple.com/documentation/usernotifications`, `.../usernotifications/asking-permission-to-use-notifications`, `.../usernotifications/declaring-your-actionable-notification-types`, `.../usernotifications/handling-notifications-and-notification-related-actions`, `https://developer.apple.com/documentation/activitykit`, `.../activitykit/displaying-live-data-with-live-activities`, `https://developer.apple.com/documentation/updates/activitykit`, `.../updates/usernotifications`
- Facets — UI: `https://developer.apple.com/documentation/swiftui`, `https://developer.apple.com/documentation/uikit`, `.../updates/swiftui`, `.../updates/uikit`, `.../swiftui/uiviewrepresentable`, `.../swiftui/uiviewcontrollerrepresentable`, `.../swiftui/uihostingcontroller`, `.../uikit/uistatusbarstyle`
- Building without a Mac (2026-09-12) — Codemagic: `https://docs.codemagic.io/yaml-quick-start/building-a-native-ios-app/`, `https://docs.codemagic.io/yaml-code-signing/signing-ios/`, `https://docs.codemagic.io/yaml-publishing/app-store-connect/`, `https://docs.codemagic.io/billing/pricing/`, `https://docs.codemagic.io/specs-macos/xcode-26-6/`, `https://docs.codemagic.io/specs-macos/xcode-27-0/`; Xcode Cloud: `https://developer.apple.com/xcode-cloud/`; GitHub Actions: `https://docs.github.com/en/actions/reference/runners/github-hosted-runners`, `https://docs.github.com/en/billing/managing-billing-for-your-products/about-billing-for-github-actions`, `https://docs.github.com/en/billing/reference/actions-runner-pricing`, `https://docs.github.com/en/actions/how-tos/deploy/deploy-to-third-party-platforms/sign-xcode-applications`, image contents `https://github.com/actions/runner-images/blob/main/images/macos/macos-26-arm64-Readme.md` and `https://github.com/actions/runner-images/blob/main/README.md`; EAS (why it is not an option): `https://docs.expo.dev/build/setup/`, `https://docs.expo.dev/build/introduction/`, `https://docs.expo.dev/build-reference/limitations/`, `https://docs.expo.dev/build-reference/ios-builds/`
- Facets — storage: `https://developer.apple.com/documentation/swiftdata`, `.../swiftdata/preserving-your-apps-model-data-across-launches`, `.../swiftdata/modelconfiguration`, `.../swiftdata/modelconfiguration/url`, `.../updates/swiftdata`, `https://developer.apple.com/documentation/coredata`, `https://developer.apple.com/documentation/foundation/userdefaults`, `.../swiftui/appstorage`, `https://developer.apple.com/documentation/foundation/optimizing-your-app-s-data-for-icloud-backup`, and the archived `https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html` for the container layout
