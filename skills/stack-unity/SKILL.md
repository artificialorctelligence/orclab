---
name: stack-unity
description: Background knowledge for any work in a Unity project (C#, Unity 6) - creating one, building for Android, iOS or desktop, configuring signing, versions or SDK levels, choosing a package, licensing questions, or preparing a Google Play or App Store release of a game. Says what the current toolchain is, where things live, and where each store rule lands. Not a command; Claude reads it when Unity is in play.
user-invocable: false
---

# Unity — cross-platform games, C#

**Checked against live sources on 2026-09-11.** Unity **6000.6.0f1** (2026-08-31). Unity ships a
minor every ~2 months and patches weekly; treat anything here older than one minor as suspect —
`orclab:currency-discipline` says re-check, and "Sources" says where.

**Nobody here has shipped a Unity game, and games are not in focus** (direflail, 2026-09-11).
This file is deliberately thinner than the mobile stacks: enough that a game session starts from
verified ground, not enough to pretend the game-specific questions (controls, a desktop sibling)
are answered. "Scope divergence" below says what the docs say about them; no game has tested it.

## When this is the stack

The **alternative** on every game row of `/orc-code`'s Defaults Table — Godot (`stack-godot`) is
the default for desktop, mobile, or both — chosen when the concern below applies (v18 spec §2,
2026-09-12). Unity is the larger ecosystem — more packages, more platform SDK integrations (ads,
IAP, analytics), more hiring — and is C#. Godot is smaller, open source, GDScript or C#. A game
that must ship on both stores is fine in either; the store ingredients apply to both unchanged.

**Licensing, because it is the question people have about Unity.** Unity Personal is free for
individuals and organisations under **US$200K** revenue or funding in the prior 12 months; Pro is
**$2,310 per seat per year** ($210 monthly). The 2023 Runtime Fee was **cancelled** (Unity's blog,
September 2024) before it ever applied, and the "Made with Unity" splash screen is **optional on
Personal from Unity 6**. Personal still requires a Unity account and Unity Hub to activate.

## Toolchain, as of 2026-09-11

| Thing | Current | Where it was read |
|---|---|---|
| Unity Editor | 6000.6.0f1 (Unity 6.6), via Unity Hub, which manages editor versions and platform modules | unity.com/releases/editor/whats-new |
| Language | C#, the .NET profile Unity bundles (not the system .NET SDK) | Unity manual |
| Editor on Linux | Supported (Ubuntu). **Android builds work from this machine.** The *iOS Build Support* module installs on Linux but produces only an Xcode project — the archive needs a Mac, same as every other stack here. Unity Build Automation is Unity's paid cloud Mac. | Unity manual "Getting started with iOS"; Hub module list |
| Android module | Hub installs OpenJDK, Android SDK and NDK matched to the editor — do not point Unity at Android Studio's SDK unless you have to | Unity manual |
| Android API levels | Minimum API 23; Unity 6.x targets API 35 and 36 ("Target API Level" in Player Settings; *Automatic (highest installed)* is the default and picks what the Hub installed) | Unity manual "Android requirements and compatibility" |
| 16 KB page size | Supported in Unity 6 — "update to recent Unity patches"; **native plugins are the risk** and must be rebuilt aligned. Unity's own note: Firebase ≥ 12.10, Burst ≥ 1.8.21 | Unity manual; Unity discussions |
| Privacy manifest (iOS) | The engine **declares its own** required-reason APIs since 2021.3.35 / 2022.3.18 / 2023.2.7 (file timestamp, user defaults, system boot time, disk space); the *app's* manifest is yours, placed at `Assets/Plugins/PrivacyInfo.xcprivacy`; each third-party package ships its own | Unity manual "Apple's privacy manifest policy requirements" |
| Headless build | `Unity -batchmode -quit -projectPath <p> -buildTarget <Android\|iOS\|StandaloneLinux64> -executeMethod <Class.Method> -logFile <f>` where the static C# method calls `BuildPipeline.BuildPlayer` | Unity manual "Command line arguments" |

## Project layout — where things live

| Path | What |
|---|---|
| `Assets/` | Everything the game is made of: scenes, scripts, prefabs, art. `Assets/Plugins/` for native plugins and the iOS privacy manifest. |
| `Packages/manifest.json` | Package Manager dependencies (Unity registry, git URLs). The version pins. |
| `ProjectSettings/ProjectSettings.asset` | **Player Settings** — company/product name, `applicationIdentifier` (bundle id / package name, per platform), `bundleVersion` (version string), `AndroidBundleVersionCode`, iOS `buildNumber`, target API level, architectures, signing keystore path. Edited through *Edit → Project Settings → Player*; the asset is YAML and diffable. |
| `ProjectSettings/EditorBuildSettings.asset` | Scenes in the build. |
| `Library/`, `Temp/`, `Logs/`, `Build/` | Generated. Git-ignored (Unity's standard `.gitignore`). |
| Build Profiles (`File → Build Profiles`) | Per-platform build configuration; *Build App Bundle (Google Play)* lives here for Android. |

## Build

Android: Build Profiles → Android → *Build App Bundle (Google Play)* → Build, or the headless
form above. Output is wherever the build method says; `.aab` when the bundle option is on.
*Export Project* instead produces a Gradle project for Android Studio when the manifest or Gradle
needs hand-editing.

iOS: Build produces an **Xcode project**; from there the App Store ingredient's local shape
applies (`xcodebuild archive` / `-exportArchive`, or Xcode by hand). The Unity-generated project's
`Unity-iPhone` target is where signing and `PrivacyInfo.xcprivacy` end up.

Coverage, mutation testing and test lint for this language: `skills/orc-test/languages/csharp.md`
— `/orc-test` reads it.

## Lint — where code-discipline lands

C#'s switch is in the project file, and the four shape rules are SonarAnalyzer.CSharp's
(10.34.0, a NuGet analyzer package; the rules are parametrised and **off** in its default profile,
so each is enabled by hand) — confirmed 2026-09-13 in `sonar-dotnet`'s rule sources:

```xml
<!-- .csproj -->
<TreatWarningsAsErrors>true</TreatWarningsAsErrors>
<EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
<PackageReference Include="SonarAnalyzer.CSharp" Version="10.34.0.3385" PrivateAssets="all" />
<ItemGroup><AdditionalFiles Include="SonarLint.xml" /></ItemGroup>
```

```ini
# .editorconfig
dotnet_diagnostic.S134.severity = error    # control flow nested too deeply (default max 3)
dotnet_diagnostic.S138.severity = error    # functions should not have too many lines (default 80)
dotnet_diagnostic.S108.severity = error    # nested blocks of code should not be left empty
dotnet_diagnostic.S2486.severity = error   # generic exceptions should not be ignored
dotnet_diagnostic.CA1031.severity = warning  # do not catch general exception types (Roslyn, ships with the SDK)
```

The two thresholds are rule *parameters*, and `.editorconfig` cannot set those — the analyzer
reads them from a `SonarLint.xml` passed as an `AdditionalFiles` item
(`SonarAnalyzer.Core/Configuration/ParameterLoader.cs`):

```xml
<AnalysisInput><Rules>
  <Rule><Key>S134</Key><Parameters><Parameter><Key>maximumNestingLevel</Key><Value>2</Value></Parameter></Parameters></Rule>
  <Rule><Key>S138</Key><Parameters><Parameter><Key>max</Key><Value>60</Value></Parameter></Parameters></Rule>
</Rules></AnalysisInput>
```

Rules 2, 3 and 5 (`using`, `ArgumentException` over `Debug.Assert`, which is
`[Conditional("DEBUG")]`) are reviewed, not linted.

## Security — where security-discipline lands

`security-discipline`'s rules for this stack, confirmed live 2026-09-19;
no project has been through this yet, and the first one corrects it. A single-player game is the
*Every project* tier — it accepts no connections — so rules 1–4 apply in full, and of 5–9 only
rule 8's client half: whether the game checks the certificate of, and refuses plain HTTP to, the
server it talks to. The Android and iOS builds are that platform's app, so the platform halves —
the keystore, cleartext and the system trust store on Android; the signing identity and App
Transport Security on iOS — are `stack-android-native`'s and `stack-ios-native`'s Security
sections, read against the Gradle project *Export Project* writes and the Xcode project the iOS
build writes; nothing is re-derived here. This section covers only what Unity itself adds: how
an analyzer reaches its compiler, its Package Manager, `PlayerPrefs`, the Player Settings that
gate permissions and plain HTTP, and what a build contains.

### Static analysis

The Lint section's analyzer, SonarAnalyzer.CSharp 10.34.0.3385, is also this stack's security
linter, and its security rules are **on by default** — nothing to enable. From `sonar-dotnet`'s
sources (read live 2026-09-19): `DiagnosticDescriptorFactory.cs` creates every diagnostic with
`isEnabledByDefault ?? rule.SonarWay`, and `rspec/cs/Sonar_way_profile.json` (345 rules) holds
every rule below; each is `"type": "VULNERABILITY"` in its `rspec/cs/S<n>.json`, raised as a
Warning. By `security-discipline` rule:

- **Rule 1.** `S2068` *"Credentials should not be hard-coded"* (its `securityStandards` list
  CWE-798, the rule's own source) and `S6418` *"Secrets should not be hard-coded"* (Blocker).
- **Rule 3.** No Sonar rule — reviewed. The concrete form is
  `UnityWebRequestAssetBundle.GetAssetBundle(uri, version, crc)`: *"If nonzero, this number
  will be compared to the checksum of the downloaded asset bundle data. If the CRCs do not
  match, an error will be logged and the asset bundle will not be loaded. If set to zero, CRC
  checking will be skipped"* (Scripting API, read live 2026-09-19). A zero `crc` on a bundle
  fetched over the network is the finding; a checksum is the rule's floor, and the signature it
  calls the standard has no Unity API.
- **Rule 4.** `S2612` *"File permissions should not be set to world-accessible values"*; the
  manifest half is two Android Player Settings (that page, read live 2026-09-19): **Internet
  Access** — *"Auto: Only add the internet access permission if you are using a networking
  API"*, against *"Require: Always add the internet access permission"*, which is *"Set to
  Require by default for development builds"* — and **Write Permission** — *"Internal: Only
  grant write permission to internal storage"*. Both stay at `Auto` and `Internal`; a permission
  a package adds through its own manifest is reviewed, as the rule says.
- **Rule 8's client half.** `S4830` *"Server certificates should be verified during SSL/TLS
  connections"* (Critical) — its own example is a `ServerCertificateValidationCallback` that
  *"return true; // Noncompliant"*; Unity's `CertificateHandler.ValidateCertificate` — *"true
  if the certificate should be accepted, false if not"*; *"Override this to implement a custom
  certificate validation scheme"* (Scripting API, read live 2026-09-19) — is the same loosening
  the rule's text does not name, so an override that returns `true` is reviewed:
  `grep -rn CertificateHandler Assets/` prints nothing, or only a pinning override with the
  reason on the line; `S4423` *"Weak SSL/TLS protocols should not be used"*; `S5332`
  *"Clear-text protocols should not be used"*, an `http://` literal. And the Player Setting that
  makes the last one a runtime refusal: **Allow downloads over HTTP** — *"The default option is
  Not allowed due to the recommended protocol being HTTPS, which is more secure"*; the three
  values are *"Not Allowed: Never allow downloads over HTTP"*, *"Allowed in Development
  Builds"*, *"Always Allowed"* (the Android and iOS Player-settings pages both carry it; it is
  `PlayerSettings.insecureHttpOption`, *"Determines if plain text HTTP connections are
  allowed"*). It stays at *Not allowed*.
- Also on, and left on: `S2077` (SQL built from strings), `S5773` and `S5766` (deserialization),
  `S4036` (an OS command resolved through `PATH`) — rule 5's sinks, which a single-player game
  has no network input to reach — and `S2053`, `S3329`, `S4790`, `S5542` (salts, IVs, weak
  hashes, cipher modes), `S2245` (a PRNG where a secret is made), `S4507` *"Debugging features
  should not be enabled in production"*, `S5443`, `S6444`.

**How the analyzer reaches Unity's compiler is not the `.csproj`.** Unity *"automatically
creates and maintains a Visual Studio .sln and .csproj file"* (*IDE support*, read live
2026-09-19), regenerating them for the IDE, and its own note on its analyzers says why a
`PackageReference` there is not a build step: *"Due to differences in the way Unity and Visual
Studio compiles user code, Microsoft.Unity.Analyzers.dll isn't configured automatically in the
Unity Editor."* The documented path (*Install and use an existing analyzer or source
generator*, read live 2026-09-19) is the DLL itself: download the NuGet package, take
`analyzers/SonarAnalyzer.CSharp.dll` (the one DLL in `sonaranalyzer.csharp.10.34.0.3385.nupkg`,
listed live), *"Move these files into the Assets folder, or any folder nested inside of the
Assets folder"*, in the Plugin Inspector *"disable Any Platform"* and then *"disable Editor and
Standalone"*, and give it the asset label `RoslynAnalyzer` — *"This label must exactly match
the example and is case sensitive."* Then *"When you save the file, Unity recompiles the script
and runs any applicable analyzers on the script's code."* Severity is a ruleset: the
analyzer-scope page names only `.ruleset` files, no `.editorconfig` — *"you can promote
warnings to errors for a specific assembly"*, and *"The Default.ruleset applies to all
assemblies in the project"*. So, beside the Lint section's `.editorconfig` (which the .NET SDK
reads and Unity's docs do not mention), the one file Unity's docs say it reads, in the `Assets`
root:

```xml
<?xml version="1.0" encoding="utf-8"?>
<!-- Assets/Default.ruleset: security-discipline rules 1, 4 and 8, Warning promoted to Error -->
<RuleSet Name="Orclab security" Description="security-discipline in Unity" ToolsVersion="10.0">
  <Rules AnalyzerId="SonarAnalyzer.CSharp" RuleNamespace="SonarAnalyzer.CSharp">
    <Rule Id="S2068" Action="Error" />  <!-- rule 1: credentials hard-coded -->
    <Rule Id="S6418" Action="Error" />  <!-- rule 1: secrets hard-coded -->
    <Rule Id="S2612" Action="Error" />  <!-- rule 4: world-accessible file permissions -->
    <Rule Id="S4830" Action="Error" />  <!-- rule 8: certificate validation off -->
    <Rule Id="S4423" Action="Error" />  <!-- rule 8: weak TLS -->
    <Rule Id="S5332" Action="Error" />  <!-- rule 8: clear-text protocol -->
  </Rules>
</RuleSet>
```

None of this has been run against a Unity project — not run here; the first project records
it: whether Unity 6's compiler loads this Sonar DLL, whether a ruleset `Error` stops a
batch-mode build, and whether the Lint section's four shape rules and their `SonarLint.xml`
parameters reach the compiler by this path at all (Unity's docs name no `AdditionalFiles`
mechanism). If the `.csproj` form turns out to be IDE-only, the Lint section is corrected the
same day.

SecurityCodeScan, the other C# security analyzer, is not the answer: `SecurityCodeScan.VS2019`'s
last NuGet release is 5.6.7 on 2022-09-05, and its repository's last commit on the default
branch is 2022-11-11 (LGPL-3.0; nuget.org's registration index and the GitHub API, read live
2026-09-19) — four years without a release, and Sonar already covers its ground.

### Dependency audit

**None free for Unity packages, and the C# tool does not reach them.** `/orc-test audit`'s C#
check, `dotnet list package --vulnerable --include-transitive --format json`
(`skills/orc-test/languages/csharp.md`, `## Audit`), reads NuGet packages from a restored
project. A Unity project's dependencies are not NuGet packages — they are `Packages/manifest.json`
entries the Package Manager resolves from Unity's registry (the layout table), and the `.csproj`
is the IDE file above, with no NuGet restore in a Unity build — so against a Unity project the
command has nothing to audit; what it prints (an empty report, or a `problems` entry for the
missing assets file) was not run here, and the first project records it. What Unity's own docs
offer is a **Deprecated** state, not an advisory: *"Packages that reach their end of life are no
longer supported in Editors where they're marked Deprecated. Avoid using packages in a
Deprecated state because they might be nonfunctional or unsafe"* (*Package states and
lifecycle*, read live 2026-09-19) — a review item, by hand, against rule 2's time frame until a
tool exists. A NuGet package brought in by hand as a DLL under `Assets/Plugins/` is in no
manifest and is reviewed the same way.

### Secrets

Three kinds of secret, three places, none of them a C# file or `ProjectSettings.asset` (rule 1;
each claim confirmed live 2026-09-19 against the page named):

- **The upload keystore and its passwords.** Unity keeps the path (the store table's row) and
  not the passwords: *"Note: For security reasons, Unity doesn't save your Keystore or Project
  Key passwords"* (Android Player settings page) — they are typed per session, or set in the
  headless build's C# method from the environment through `PlayerSettings.Android.keystorePass`
  and `keyaliasPass` (*"the password for retrieving and updating the keys inside a particular
  keystore"*; the `useCustomKeystore` example on that page assigns string literals and then
  `Debug.Log`s them — do neither). `.gitignore`: the standard Unity template (github/gitignore's
  `Unity.gitignore`, read live) ignores `Library/`, `Temp/`, `Obj/`, `Build/`, `Logs/`,
  `UserSettings/` and `MemoryCaptures/` (*"could contain extremely sensitive data"*) and has no
  keystore line — add `*.keystore` and `*.jks`. The iOS signing identity never touches this
  machine (the toolchain table); `stack-ios-native`'s Secrets says the rest.
- **A token the game holds for its user.** Not `PlayerPrefs`: *"Unity stores PlayerPrefs in a
  local registry, without encryption. Don't use PlayerPrefs data to store sensitive data"*
  (Scripting API, read live) — and the page names nothing in its place; the manual has no
  keychain API of its own. What exists is each platform's store, reached from C# through a
  native plugin — the Android Keystore (`stack-android-native`'s Secrets: an AES key in
  `AndroidKeyStore`, the ciphertext under the no-backup directory) and the iOS Keychain
  (`stack-ios-native`'s) — and no plugin for it has been chosen or run here; the first project
  that holds a token picks one and records it, and until then the scaffold stores no token.
- **An API key for a service the game calls.** A build is public — the `_Data` folder the Linux
  build ships, the `.aab`, the `.ipa` — and Minify (*"make the code harder to disassemble"*,
  Android Player settings) changes the effort, not the fact — so a key in a `const`, a
  `ScriptableObject` or `Resources/` is a key everyone has, and `S2068`/`S6418` above are the
  two checks that see the literal. It lives on a server the game calls — the *Reachable by
  strangers* tier of whatever stack that is (the Android skill's API-key paragraph, with Google's
  *"The client should pass requests to the server, which can add the credential and issue the
  request"*) — or it is one designed to ship, the Android skill's Maps-key case.

Never in the built artifact: the keystore, a `.p12` or `.p8`, `.env`, `.git`, and any value that
was ever a literal in a C# file, which is there by construction; a *Development Build* (the
build profile's checkbox) is not a release. Nothing lints the build; the first project lists one
once (`unzip -l` on the `.aab`; the `_Data` folder on desktop) and records the answer here.

### Reachable by strangers

This stack does not accept connections: n/a — a single-player game has no route to
authenticate, no error to sanitise and no rate to limit; the service it talks to carries rules
5–9 in its own stack. What still applies is rule 8's client half, per platform as the native
skills say it — cleartext off and the system trust store on Android, App Transport Security on
iOS — plus Unity's own two above: *Allow downloads over HTTP* at *Not allowed*, and a
`CertificateHandler` override that returns `true`. And the API-key paragraph: the build is not a
secret store. **Multiplayer is out of scope here.** A game that *"hosts players locally or over a
network"* (the *Multiplayer* manual page, read live 2026-09-19, which sends the rest to the
Multiplayer Center) is the *Reachable by strangers* tier on its server, and no stack skill
covers a game server yet; no BACKLOG entry exists for it, and the first multiplayer game opens
one — `stack-godot`'s section quotes what Godot's own docs already say about it.

## Presence

Not researched; unlikely to be needed.

## UI

No project has been built with these facets yet; the first one corrects them. The UI is the menus,
HUD and dialogs the player reads and taps, as distinct from the game world. Unity has two runtime
systems and its own docs pick one: the *Comparison of UI systems in Unity* table for Unity 6.6 puts,
for Runtime, **Recommendation: uGUI (Unity UI)**, **Alternative: UI Toolkit** (confirmed live
2026-09-12; the 6.3 LTS page carries the same table). **Default: uGUI** — a Canvas of GameObjects,
laid out in the Scene view like everything else; *"uGUI is the recommended solution for the
following: Easy referencing from MonoBehaviours"*, and it alone has *"In-scene authoring"*,
*"Serialized events"* and *"Integration with Animation Clips and Timeline"* (that page's feature
table); the package is `com.unity.ugui` 2.6 (confirmed live 2026-09-12). **Alternative: UI
Toolkit**, only for its concern — *"UI Toolkit is an alternative to uGUI (Unity UI) if you create a
screen overlay UI that runs on a wide variety of screen resolutions"* or with *"a significant
amount of user interfaces"*; it is *"web-like"*, *"document-based"*, edited in the UI Builder, and
*"in active development"* where uGUI is *"established and production-proven"* and *"updated
infrequently"*. Both work with the Input System package (*"Input system support"*, both ticked).
BACKLOG #2's design system translates into the frameworks above.

## Storage

No project has been built with these facets yet; the first one corrects them. Storage is what the
game keeps on the device between runs: settings, and saved progress. **Files go under
`Application.persistentDataPath`** — *"a directory path where you can store data that you want to
retain between runs"*; on iOS and Android *"The files can only be erased by users directly and not
by any app updates"* (confirmed live 2026-09-12, that Scripting API page). Where it is, per OS, from
the same page: Windows *"%userprofile%\AppData\LocalLow\<companyname>\<productname>"*; macOS player
*"~/Library/Application Support/unity.company name.product name"* (the Editor uses
`.../company name/product name`; the player *"uses the Editor path if that directory already
exists"*); Linux
*"$XDG_CONFIG_HOME/unity3d/Company/ProjectName"*, so `~/.config/unity3d/...`; Android
*"/storage/emulated/<userid>/Android/data/<packagename>/files"*; iOS
*"/var/mobile/Containers/Data/Application/<guid>/Documents"*; Web *"a location in the browser's
IndexedDB file system"*. The location follows the identity in Player Settings — *"If you keep the
same Bundle Identifier in future versions, the application keeps accessing the same location on
every update"* — so settle company, product and identifier before the first release. Build the full
path with `Path.Combine(Application.persistentDataPath, ...)`: the page warns that relative paths
land in the project folder on desktop. Saved progress is a file there: `JsonUtility.ToJson` on a
plain C# class (*"such as when saving game state"*; it serialises fields only, per Unity's
serializer rules — confirmed live 2026-09-12) written with `System.IO.File`. External databases are
out of scope for this skill.

**Config: `PlayerPrefs`** — *"stores Player preferences between game sessions"*, three value types
only (*"string, float and integer"*), unencrypted (*"Don't use PlayerPrefs data to store sensitive
data"*), and the size caveat is the Web platform's: *"Unity stores up to 1MB of PlayerPrefs data"*
there (confirmed live 2026-09-12, `PlayerPrefs` page, which also lists where it lands per OS: the
Windows registry, a `.plist`, `~/.config/unity3d`, `shared_prefs`, `NSUserDefaults`) — settings, not
saves. **SQLite only via a package**, and only when there are rows to query: Unity's manual names
none (a live search of docs.unity3d.com finds SQLite only as Visual Scripting's internal
dependency), so the current one is **`com.gilzoide.sqlite-net`** — SQLite-net 1.9.172 on SQLite
3.50.1, installed by git URL in the Package Manager
(`https://github.com/gilzoide/unity-sqlite-net.git#1.3.2`) or OpenUPM; latest tag 1.3.2, repository
active 2026-04 (confirmed live 2026-09-12). Its concern: a native binary per platform, so the
Android one falls under the 16 KB row in the store table — 1.3.2's own changelog line is *"Warning
about Android libraries not being aligned to 16kb page size"* — and *"Android and WebGL platforms
don't support loading SQLite databases from Streaming Assets and will always load them in memory"*,
so a database that must be written lives under `persistentDataPath`.



## Where each store rule lands

The store ingredients (`skills/orc-package/ingredients/play`, `.../app-store`) state the rules.

| Rule | Where it lands in Unity | Check |
|---|---|---|
| Play: target API 36 | Player Settings → Android → *Target API Level*. *Automatic* targets the highest SDK the Hub installed — confirm that is 36. | `grep AndroidTargetSdkVersion ProjectSettings/ProjectSettings.asset` (0 = automatic) and the SDK the Hub installed |
| Play: 16 KB alignment | Unity 6's own libraries are aligned; **every native plugin in `Assets/Plugins/Android`** and every package with native code must be. | `bundletool dump config --bundle=<out>.aab \| grep alignment` → `PAGE_ALIGNMENT_16K`, on the real bundle |
| Play: upload-key signing | Player Settings → Android → Publishing Settings → keystore path, alias, passwords. Unity stores the *path* in `ProjectSettings.asset` and asks for passwords per session unless supplied via the headless build's environment. Never commit the keystore. | `git check-ignore <keystore>` |
| Play: package name; version code increases | `applicationIdentifier` (Android) and `AndroidBundleVersionCode` in `ProjectSettings.asset`; `bundleVersion` is the version string. `/orc-version` does not edit this file yet (its `versionfiles.py` handles `pyproject.toml`, `debian/changelog`, an AppStream metainfo file and the plugin manifests — BACKLOG #6); bump it by hand and check it before every upload. | Play refuses a reused code |
| Play: Data safety | Decided by packages — Unity Analytics, Ads, IAP, Firebase all send data off-device. Keep the list. | `Packages/manifest.json` |
| App Store: Xcode 26+ | The Mac's Xcode, against the exported project. | `xcodebuild -version` |
| App Store: privacy manifest | Engine reasons are automatic (versions above). The app's own `Assets/Plugins/PrivacyInfo.xcprivacy` for anything beyond them — C# `File.GetLastWriteTime` and friends count as file-timestamp API use — plus each package's own. | present in the exported Xcode project's target; Xcode → Product → *Generate Privacy Report* after archiving |
| App Store: bundle id, signing, build number | `applicationIdentifier` (iOS), Player Settings → iOS → *Signing Team ID* / automatic signing, `buildNumber`. | exported project's General tab |
| App Store: usage strings | Player Settings → iOS → *Camera Usage Description*, *Microphone Usage Description*, *Location Usage Description*. Unity writes them into the exported `Info.plist`. | `plutil -p <exported>/Info.plist \| grep Usage` |
| Both: privacy policy in-app, account deletion, login rules | Game code. | — |

## Scope divergence

No project has been built with these facets yet; the first one corrects them. Scope divergence is
what happens when one game ships on a phone and on a desktop: some differences the engine keeps
apart for you in a setting, and some you have to design differently — a thumb is not a mouse, a
portrait phone is not a 16:9 monitor, a phone GPU is not a desktop one. Which actions a game has,
and whether a desktop build ships at all, stays the game's decision; desktop distribution is Steam,
itch.io, or the Linux channels Orclab already knows. On the store side Play asks at creation —
*"Specify whether your application is an app or a game. You can change this later."* (confirmed
live 2026-09-12, Play Console Help, *Create and set up your app*).

**What the engine keeps per platform.** A **build profile** per platform — *"a set of
configuration settings you can use to build your application on a particular platform"*, saved
*"as an asset file that is ready for use with version control"*; *"settings saved under build
profiles aren't shared across all the platforms"*, and Quality (below) can be customised per
profile (confirmed live 2026-09-12, *Introduction to build profiles*; *Quality project settings
reference*). **Scripting symbols** for the code that must differ: `#if UNITY_ANDROID`, `UNITY_IOS`,
`UNITY_STANDALONE_WIN`, `UNITY_STANDALONE_OSX`, `UNITY_STANDALONE_LINUX`, `UNITY_STANDALONE` (*"any
standalone platform"*), `UNITY_EDITOR` — the code inside is *"omitted entirely"* from other
targets, unlike a runtime `if` (confirmed live 2026-09-12, *Conditional compilation in Unity*;
*Unity scripting symbol reference*).

**Input.** The **Input System** package (`com.unity.inputsystem` 1.20.0, *"intended to be a
replacement for Unity's classic Input Manager"*): **actions** *"separate the purpose of an input
from the device controls which perform that input"* — a `Move` action bound to *"the left gamepad
stick and the keyboard's arrow keys"* is the docs' own example — and code reads the action, never
the device; **control schemes** *"let you enable or disable different sets of bindings for your
actions for different types of devices"* (confirmed live 2026-09-12, package manual *Actions*,
*Control schemes*). Touch on mobile: **on-screen controls** — *"stick and button widgets on
touchscreens to emulate a joystick or gamepad"*; an On-Screen Button whose control path is
`<Gamepad>/buttonSouth` means the Input System *"creates both a Gamepad and a Keyboard"* as
needed, *"automatically when the components are enabled"* — so the same bindings serve phone and
desktop and the widgets are simply not enabled on desktop; they *"don't have a predefined visual
representation"*, the sprite is yours (confirmed live 2026-09-12, *Introduction to on-screen
controls*). Designing input as actions from day one is what makes a desktop sibling possible.

**UI scaling and aspect ratio.** uGUI: the **Canvas Scaler** on the root Canvas (added by default
with a new Canvas), **UI Scale Mode = Scale With Screen Size** with a **Reference Resolution** —
*"the Canvas will keep having only the resolution of the reference resolution, but will scale up in
order to fit the screen"* — **Match** 0.5 so portrait and landscape scale evenly, and **anchors**
tying each element to its corner; that walk-through is *Designing UI for Multiple Resolutions*, and
the default (no scaler, or Constant Pixel Size) keeps pixel sizes, so elements *"take up a larger
or smaller proportion of the screen"* (confirmed live 2026-09-12, uGUI 2.6 *Canvas Scaler* and that page). UI Toolkit: the same
three modes and Match on the **Panel Settings** asset (*"Set how the panel's UI scales when the
screen size changes"*), with layout in Flexbox, which the best-practice guide calls *"a necessary
feature for any game that is targeting multiple platforms with different screen resolutions and
ratios"* (confirmed live 2026-09-12, *Panel Settings properties reference*; *Layouts*).

**Performance: quality levels.** **Edit → Project Settings → Quality** is a matrix of quality
levels × platforms with a default per platform — *"It's best to use lower quality on mobile devices
and older platforms"* — and each level *"Sets the render pipeline asset to use at this quality
level"*, so a mobile level points at a leaner **URP asset** than the desktop one; switching at
runtime belongs in *"loading screens or on static menus"* (confirmed live 2026-09-12, *Quality
project settings reference*; *Change the active URP asset at runtime*). The mobile-specific page is
*Configure for better performance in URP* — a list of URP-asset switches for *"lower-end mobile
platforms"* (Store Actions, LOD Cross Fade, the Baked Lit / Simple Lit shaders, Depth Priming
*"Disabled for mobile platforms"*); the *"mobile-friendly"* post effects are Bloom, Chromatic
Aberration, Color Grading, Lens Distortion, Vignette (confirmed live 2026-09-12; *Introduction to
post-processing in URP*).

**Per-platform desktop differences** (each build page, confirmed live 2026-09-12). **macOS**: an
architecture — *"Apple silicon is the recommended target architecture for new macOS builds"*,
Intel and universal are *"Deprecated"* — then *"Code signing & notarization"*: unsigned, *"the
device warns the end user before they open the application"*; notarization is Apple's check of
*"Developer ID-signed applications"*, which *"Digital distribution services often require"*. **Windows**: an architecture (Intel 64-bit,
Intel 32-bit, ARM 64-bit); the build page says nothing about signing your executable —
`UnityPlayer.dll` is *"signed with the Unity Technologies certificate"*, yours is not. **Linux**:
one `ProjectName.x86_64`, `UnityPlayer.so`, a `_Data` folder, and Unity ships `libdecor-0.so.0` so
the window is decorated *"across various compositors"* under Wayland; no signing.

## Sources (live on 2026-09-11; facets 2026-09-12)

- Security — where security-discipline lands (2026-09-19): Sonar's default-on rule `https://raw.githubusercontent.com/SonarSource/sonar-dotnet/master/analyzers/src/SonarAnalyzer.Core/Analyzers/DiagnosticDescriptorFactory.cs`, `https://raw.githubusercontent.com/SonarSource/sonar-dotnet/master/analyzers/rspec/cs/Sonar_way_profile.json`, `.../rspec/cs/S{2068,6418,2612,2077,5773,5766,4036,4830,4423,5332,2053,3329,4790,5542,2245,4507,5443,6444}.json` and `S4830.html`; `https://api.nuget.org/v3-flatcontainer/sonaranalyzer.csharp/10.34.0.3385/sonaranalyzer.csharp.10.34.0.3385.nupkg` (one DLL, `analyzers/SonarAnalyzer.CSharp.dll`); SecurityCodeScan: `https://api.nuget.org/v3/registration5-gz-semver2/securitycodescan.vs2019/index.json` (5.6.7, 2022-09-05), `https://api.github.com/repos/security-code-scan/security-code-scan` and `.../commits?per_page=1` (default branch `vs2019`, last commit 2022-11-11); Unity analyzers: `https://docs.unity3d.com/6000.6/Documentation/Manual/roslyn-analyzers.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/install-existing-analyzer.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/analyzer-scope-and-diagnostics.html` (`.ruleset` only; no `.editorconfig` on the page), `https://docs.unity3d.com/6000.6/Documentation/Manual/scripting-ide-support.html` (generated `.csproj`; the `Microsoft.Unity.Analyzers` note), `https://docs.unity3d.com/Packages/com.unity.ide.visualstudio@2.0/manual/using-visual-studio-editor.html` (*Regenerate project files*); Player Settings: `https://docs.unity3d.com/6000.6/Documentation/Manual/class-PlayerSettingsAndroid.html` (*Allow downloads over HTTP*, *Internet Access*, *Write Permission*, *Minify*, the keystore-password note), `https://docs.unity3d.com/6000.6/Documentation/Manual/class-PlayerSettingsiOS.html` (*Allow downloads over HTTP*), `https://docs.unity3d.com/6000.6/Documentation/ScriptReference/PlayerSettings-insecureHttpOption.html`, `https://docs.unity3d.com/6000.6/Documentation/ScriptReference/PlayerSettings.Android-keystorePass.html`, `https://docs.unity3d.com/6000.6/Documentation/ScriptReference/PlayerSettings.Android-useCustomKeystore.html`; `https://docs.unity3d.com/6000.6/Documentation/ScriptReference/Networking.UnityWebRequestAssetBundle.GetAssetBundle.html` (`crc`), `https://docs.unity3d.com/6000.6/Documentation/ScriptReference/Networking.CertificateHandler.ValidateCertificate.html`; `https://docs.unity3d.com/6000.6/Documentation/ScriptReference/PlayerPrefs.html` (*without encryption*); `https://docs.unity3d.com/6000.6/Documentation/Manual/upm-lifecycle.html` (Deprecated state); `https://raw.githubusercontent.com/github/gitignore/main/Unity.gitignore`; `https://docs.unity3d.com/6000.6/Documentation/Manual/multiplayer.html`
- Lint — where code-discipline lands (2026-09-13): `https://raw.githubusercontent.com/SonarSource/sonar-dotnet/master/analyzers/rspec/cs/S{134,138,108,2486}.json`, `.../analyzers/src/SonarAnalyzer.Core/Rules/{FunctionNestingDepthBase,MethodsShouldNotHaveTooManyLinesBase}.cs` (defaults 3 and 80), `.../Configuration/ParameterLoader.cs` (parameters from `SonarLint.xml`), `https://api.nuget.org/v3-flatcontainer/sonaranalyzer.csharp/index.json`, `https://raw.githubusercontent.com/dotnet/docs/main/docs/fundamentals/code-analysis/quality-rules/ca1031.md`, `https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/errors-warnings`, `https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.debug.assert`
- Current editor: `https://unity.com/releases/editor/whats-new`
- Pricing and Personal threshold: `https://unity.com/pricing`; Runtime Fee cancellation:
  `https://unity.com/blog/unity-is-canceling-the-runtime-fee`
- Android build process: `https://docs.unity3d.com/Manual/android-BuildProcess.html`;
  requirements: `https://docs.unity3d.com/6000.2/Documentation/Manual/android-requirements-and-compatibility.html`
- iOS build process: `https://docs.unity3d.com/Manual/iphone-BuildProcess.html`
- Privacy manifest: `https://docs.unity3d.com/6000.2/Documentation/Manual/apple-privacy-manifest-policy.html`
- Command line: `https://docs.unity3d.com/6000.2/Documentation/Manual/EditorCommandLineArguments.html`
- Store rules themselves: the Play and App Store ingredients under `skills/orc-package/ingredients/`.
- Facets (2026-09-12) — UI: `https://docs.unity3d.com/6000.6/Documentation/Manual/UI-system-compare.html` (the unversioned `/Manual/` path is 6000.6 today; `6000.3` carries the same table), `https://docs.unity3d.com/Packages/com.unity.ugui@latest/` (resolves to 2.6)
- Facets — storage: `https://docs.unity3d.com/6000.6/Documentation/ScriptReference/Application-persistentDataPath.html`, `https://docs.unity3d.com/6000.6/Documentation/ScriptReference/PlayerPrefs.html`, `https://docs.unity3d.com/6000.6/Documentation/ScriptReference/JsonUtility.html`, `https://github.com/gilzoide/unity-sqlite-net` (README, CHANGELOG, tags; Unity's docs name no SQLite package — a `site:docs.unity3d.com sqlite` search returns only Visual Scripting's internal dependency)
- Scope divergence: `https://docs.unity3d.com/6000.6/Documentation/Manual/build-profiles.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/platform-dependent-compilation.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/scripting-symbol-reference.html`, `https://docs.unity3d.com/Packages/com.unity.inputsystem@1.20/manual/index.html` (`@latest` resolves here), `.../Actions.html`, `.../control-schemes.html`, `.../introduction-on-screen-controls.html`, `https://docs.unity3d.com/Packages/com.unity.ugui@2.6/manual/script-CanvasScaler.html`, `https://docs.unity3d.com/Packages/com.unity.ugui@2.6/manual/HOWTO-UIMultiResolution.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/UIE-Runtime-Panel-Settings.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/best-practice-guides/ui-toolkit-for-advanced-unity-developers/layouts.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/class-QualitySettings.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/urp/urp-quality-settings-landing.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/urp/quality/quality-settings-through-code.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/urp/configure-for-better-performance.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/urp/integration-with-post-processing.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/macos-building.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/WindowsStandaloneBinaries.html`, `https://docs.unity3d.com/6000.6/Documentation/Manual/build-for-linux.html`, `https://support.google.com/googleplay/android-developer/answer/9859152`; read and found nothing to keep: `https://docs.unity3d.com/6000.6/Documentation/Manual/android-optimization.html` (a landing page — threads, startup, foldables), `https://docs.unity3d.com/6000.6/Documentation/Manual/Windows.html` (landing)
