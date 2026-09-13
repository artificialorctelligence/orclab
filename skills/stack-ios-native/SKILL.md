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
| Build number increases every upload | `CURRENT_PROJECT_VERSION` (build) and `MARKETING_VERSION` (version) in target settings. `/orc-version` edits both and refuses a bump that leaves the build number unchanged. | App Store Connect refuses a reused build number for the same version |
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

## Sources (live on 2026-09-11; facets 2026-09-12)

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
- Facets — storage: `https://developer.apple.com/documentation/swiftdata`, `.../swiftdata/preserving-your-apps-model-data-across-launches`, `.../swiftdata/modelconfiguration`, `.../swiftdata/modelconfiguration/url`, `.../updates/swiftdata`, `https://developer.apple.com/documentation/coredata`, `https://developer.apple.com/documentation/foundation/userdefaults`, `.../swiftui/appstorage`, `https://developer.apple.com/documentation/foundation/optimizing-your-app-s-data-for-icloud-backup`, and the archived `https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html` for the container layout
