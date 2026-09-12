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
SwiftUI when a control is missing, not the starting point for a new app.

## The Mac requirement, stated once

**Every build, test run, archive and simulator needs macOS with Xcode.** Swift itself installs on
Linux (swift.org ships 6.3.3 for it), and that is enough to compile and test a pure-Swift
*package* — business logic, no UI — but there is no iOS SDK for Linux and never has been. From
this machine, an iOS project can be *edited* and its package layer *tested*; producing an `.ipa`
happens on a Mac at hand or a cloud Mac. The App Store ingredient
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
| Testing | **Swift Testing** (`import Testing`, `@Test`, `#expect`) for unit tests — Apple's current framework, integrated with SwiftPM; XCTest remains for UI tests (`XCUIApplication`) | developer.apple.com/documentation/testing |
| Dependencies | Swift Package Manager, in Xcode (File → Add Package Dependencies) or `Package.swift`. CocoaPods is not for new projects — its registry goes read-only 2026-12-02 | Flutter's SwiftPM page records the CocoaPods date; Apple docs for SwiftPM |
| Persistence | SwiftData (Apple's current, Swift-native layer over Core Data) when local persistence is needed; not a default, a choice | Apple docs |
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
| Build number increases every upload | `CURRENT_PROJECT_VERSION` (build) and `MARKETING_VERSION` (version) in target settings. `/orc-version` edits both and refuses a bump that leaves the build number unchanged. | App Store Connect refuses a reused build number for the same version |
| iPhone apps should run on iPad (2.4.1) | Target → General → *Supported Destinations*: iPhone and iPad both listed, and the layout tested on an iPad simulator. | `xcodebuild -showdestinations -scheme <App>` |
| Age rating, App Privacy answers, EU trader status | App Store Connect, not the project. App Privacy answers are decided by which packages you add — keep the list. | — |

## Choosing dependencies

Swift Package Manager only. Prefer Apple's frameworks first — they need no privacy manifest of
their own and never miss an SDK deadline. For a third-party package: does it ship a
`PrivacyInfo.xcprivacy` (look in its repo); is it maintained against the current Swift and Xcode;
what does it send off-device. `orclab:currency-discipline` applies to every version pin in
`Package.resolved`; Xcode's *Update to Latest Package Versions* is the tool.

**Deliberately not decided here**: networking beyond `URLSession`, persistence (SwiftData vs
plain files vs SQLite), backend, analytics. Project choices; no preference recorded until
direflail has one.

## Games

Not this stack. An iOS game is Unity or Godot, which produce their own Xcode project; the App
Store ingredient applies to it unchanged, including the privacy manifest and the Mac.

## Sources (live on 2026-09-11)

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
