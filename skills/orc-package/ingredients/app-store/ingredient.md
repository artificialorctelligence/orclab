# Ingredient: Apple App Store

**Researched against Apple's live pages on 2026-09-11 (GitHub's runner pricing 2026-09-12); no release has gone through this yet.**
Every command below is documented by its vendor and none has been run by anyone here — including
the bundled script, which was written from Apple's API reference and has never been pointed at a
real team. The first real release will find something wrong; correct the file (that is what
capture is for, per `/orc-package`), and remove this paragraph only once a release has landed.

`/orc-package` asks for these before applying, and uses them everywhere below:

| Ask for | Example | Used as |
|---|---|---|
| Bundle identifier | `org.orcshot.orcshot` | `__BUNDLE_ID__` |
| Is there a Mac to build on — this machine, or a cloud one? | `local` / `cloud` | picks the leaf shape in section 6 |
| *(local)* Command that builds the signed `.ipa` | `flutter build ipa --release --export-options-plist=ios/ExportOptions.plist` | `__BUILD__` |
| *(local)* Path of the `.ipa` that build writes | `build/ios/ipa/App.ipa` | `__IPA__` |
| *(cloud)* Command that starts the cloud build-and-upload | `gh workflow run ios-release.yml --ref "$(git branch --show-current)"` | `__TRIGGER__` |
| App Store Connect API Key ID | `2X9R4HXF34` | `__KEY_ID__` |
| App Store Connect Issuer ID | `57246542-96fe-1a63-e053-0824d011072a` | `__ISSUER_ID__` |
| Where the `.p8` private key lives (outside the repo) | `${XDG_CONFIG_HOME:-~/.config}/orcshot/AuthKey___KEY_ID__.p8` | `__P8_PATH__` |
| Vendor number, if metrics are wanted (App Store Connect → Payments and Financial Reports) | `88123456` | `__VENDOR__` |
| `channels.yaml` path for the leaf | `mobile.dart.ios.app-store` | the leaf's parent |

## 1. What the channel is

Apple's store for iPhone and iPad. Every version goes through Apple's human review before it is
visible; TestFlight is the pre-release track and also reviewed, more lightly.

Built on: **macOS only.** Producing an `.ipa` requires Xcode, and since **2026-04-28** uploads must
be built with **Xcode 26 and the iOS 26 SDK**. There is no Linux path for the build. The upload
and everything after it can happen from anywhere — the API is plain HTTPS — but the artifact
cannot. Without a Mac at hand, the real options are a cloud Mac: Codemagic (free tier; can generate
signing on your behalf), GitHub Actions macOS runners ($0.062/minute against $0.006 for Linux,
about 10.3×; the 10× multiplier on included minutes GitHub once documented is no longer on its
pages — confirmed live 2026-09-12), Bitrise, or Apple's Xcode Cloud. That choice is the `local` / `cloud` question in the table, and it changes the
leaf's shape in section 6. It does not change anything else here.

Takes: a signed **`.ipa`** — an Xcode archive exported for App Store distribution with a
distribution certificate and an App Store provisioning profile, both issued under the Apple
Developer Program account. Producing it — certificates, profiles, `ExportOptions.plist`, the
privacy manifest — is the stack's job (`stack-flutter`, `stack-ios-native` when written) and out
of this ingredient's scope.

The rules the build has to meet, as of 2026-09-11, because a build that misses one is refused at
upload or rejected in review:

- **Xcode 26 / iOS 26 SDK**, since 2026-04-28. Apple raises this every spring after WWDC;
  re-check `https://developer.apple.com/news/upcoming-requirements/` before trusting it.
- **A privacy manifest** (`PrivacyInfo.xcprivacy`) at the app bundle root, declaring collected
  data types and the *required-reason APIs* the app and its SDKs use. App Store Connect **rejects
  the upload** for a manifest with unexpected keys, and since 2025-02-12 certain listed third-party
  SDKs must ship their own. Flutter plugins are third-party SDKs in this sense.
- **Public APIs only**, running on the currently shipping OS (guideline 2.5.1).
- iPhone apps "should run on iPad whenever possible" (2.4.1) — a review expectation, not a hard
  refusal.

## 2. Registration — one-time, account-gated, never performed by Orclab

The Apple Developer Program. **"99 USD per membership year."** Two kinds:

- **Individual.** An Apple Account with two-factor authentication; legal name (it is displayed as
  the seller on the store); email, phone, and a non-P.O.-box address. Identity is verified.
- **Organization.** Additionally: a legal entity (no DBAs or trade names), a **D-U-N-S number**, a
  working public website on the organization's own domain, and an account holder with authority to
  bind the entity.

Enrolment can take days; Apple sometimes asks for more identity documents.

**Check:** `https://developer.apple.com/account` signs in and shows an active membership, and
`https://appstoreconnect.apple.com` opens. Orclab cannot check this; the user does.

## 3. Credentials — three mechanisms, because they are

**Signing certificate and provisioning profile, for building the `.ipa`.** A *distribution*
certificate issued under the account and an *App Store* provisioning profile for
`__BUNDLE_ID__`. Xcode's automatic signing manages both on a Mac; fastlane `match` or Codemagic's
automatic signing does it for cloud builds. These are consumed by `__BUILD__`, not by this
ingredient's action, so they are the stack's configuration.

- **Check (local Mac):** `security find-identity -v -p codesigning` lists an "Apple Distribution"
  identity.
- **Check (cloud):** the cloud service's signing configuration is set up — checkable only in its
  own UI. Say so.
- **If missing:** the user creates them in Xcode or at
  `https://developer.apple.com/account/resources/certificates`. Orclab never does.

**App Store Connect API key, for upload, status, and metrics.** A *team* key: App Store Connect →
Users and Access → Integrations → App Store Connect API → Team Keys → Generate. Choose a role —
**App Manager** covers uploads and version state; **Admin** or **Sales and Reports** is needed
for the downloads report. Apple shows the **Issuer ID** at the top of that page and the **Key ID**
in the table; the private key is a `.p8` file **downloadable exactly once** — Apple keeps no copy.
Tokens are ES256 JWTs valid at most 20 minutes, which the bundled script mints per request.

- **Check:** `test -s "__P8_PATH__"`. Whether it is *accepted* is proven by the first
  `scripts/appstore-status.py state` run.
- **If missing:** the user generates a key and downloads it to `__P8_PATH__`, `chmod 0600`. A lost
  `.p8` is revoked and re-created, never recovered. Orclab never reads or prints it.

**`altool`'s key location (local shape only).** `xcrun altool --apiKey` never takes the key's
path; it looks for a file named exactly `AuthKey___KEY_ID__.p8` in `./private_keys`,
`~/private_keys`, `~/.private_keys`, `~/.appstoreconnect/private_keys`, or the directory named by
the `API_PRIVATE_KEYS_DIR` environment variable (altool man page, confirmed 2026-09-11). The leaf
below sets that variable to `__P8_PATH__`'s directory, so the file must carry that exact name —
which is why the table's example path does.

- **Check:** `test -r "$(dirname "__P8_PATH__")/AuthKey___KEY_ID__.p8"`
- **If missing:** rename or move the downloaded `.p8` so it is. The user does it; it is a
  credential.

## 4. Machine-local config

**None** beyond the credential files above. The script carries its ids as constants substituted at
instantiation; the `.p8` path is the only thing outside the repo it reads.

## 5. Per-app setup — once per app, before its first release

All in App Store Connect or the developer site, by the user, once per app. `/orc-release` re-checks
each on every release through the `**One-time setup:**` markers in section 8.

1. **The bundle identifier**, registered under Certificates, Identifiers & Profiles with the
   capabilities the app uses (push, Sign in with Apple, …).
   **Check:** it appears at `https://developer.apple.com/account/resources/identifiers` (user).
2. **The app record.** App Store Connect → My Apps → New App: platform, name, primary language,
   bundle id, SKU. The API cannot create it.
   **Check:** `python3 scripts/appstore-status.py state` reports something other than "no app
   with bundle id" — after section 9 has instantiated the script.
3. **App information and the version's metadata** — description, keywords, screenshots per
   device class, support URL, **privacy policy URL** (guideline 5.1.1(i): required in the listing
   *and* reachable inside the app), category, **age rating** (the questionnaire changed; answers
   were due by 2026-01-31), **App Privacy** "nutrition label" answers, export-compliance answer
   (encryption), and — for EU availability — **trader status** under the Digital Services Act,
   without which the app is not shown in the EU.
4. **Rules that shape the app itself**, so they are known before the first build, not at first
   rejection:
   - Account creation in the app ⇒ **account deletion in the app** (5.1.1(v)).
   - Any third-party or social login ⇒ an equivalent private login must also be offered (4.8) —
     in practice Sign in with Apple.
   - No login wall unless the app is genuinely account-based (5.1.1(v)).
5. **TestFlight** — optional but the normal first destination: a build uploaded to App Store
   Connect is testable internally at once and externally after a light review.

**Check for 3–5:** none from here. App Store Connect's version page lists what is still missing
before *Add for Review* is enabled; the user reads it.

## 6. The publish action

The `channels.yaml` leaf at `<parent>.app-store` — one of two shapes, chosen by the `local` /
`cloud` answer. In both, **the action uploads a build; it does not submit it for review.**
Submitting is a per-version act in App Store Connect (select the build, *Add for Review*,
*Submit*) — or `reviewSubmissions` in the API, which fastlane's `deliver` wraps with
`submit_for_review:true`. It is left manual here because the first submission needs the metadata
in section 5 filled in by hand anyway; automate it once a release has gone through.

**Local shape** — a Mac is this machine. Same prepare/act split as every other ingredient:

```yaml
app-store:
  # Built and signed by the stack on this Mac; uploaded with Apple's own altool.
  prepare: "__BUILD__"
  artifact: "__IPA__"
  preflight: [no-vcs, no-tool-state]
  action: "API_PRIVATE_KEYS_DIR=\"$(dirname \"__P8_PATH__\")\" xcrun altool --upload-app -f __IPA__ -t ios --apiKey __KEY_ID__ --apiIssuer __ISSUER_ID__"
  metrics: "python3 scripts/appstore-status.py downloads"
  confirm:
    command: "python3 scripts/appstore-status.py state"
    url: "https://appstoreconnect.apple.com/apps"
  timeout: 1200
  requirements:
    - "Before the first real run: the same command as the action with --validate-app in place
       of --upload-app. It checks the archive, the signing and the API key without uploading."
    - "altool finds the key by name - AuthKey___KEY_ID__.p8 in API_PRIVATE_KEYS_DIR, which the
       action sets to __P8_PATH__'s directory. The key's path is never on the command line."
    - "Built with Xcode 26 / iOS 26 SDK (since 2026-04-28) and carrying a valid
       PrivacyInfo.xcprivacy. Either failing is a refusal at upload, with the reason in an email
       from App Store Connect rather than in altool's output."
  issues:
    - "Exit 0 means App Store Connect accepted the upload for processing. The build then takes
       minutes to hours to become selectable, and nothing is in review until a person submits
       the version. --confirm reports READY_FOR_SALE only after Apple's review has passed and the
       version is released; every state before that is `not confirmed`, which is correct."
    - "The confirm and metrics commands need PyJWT with its crypto extra
       (`pip install 'PyJWT[crypto]'`). The metrics key must have the Admin or Sales and Reports
       role; App Manager is enough for confirm."
```

**Cloud shape** — no Mac here; a CI service builds, signs and uploads. The action *starts* that
job; `prepare:`, `artifact:` and `preflight:` are absent because the artifact never exists on this
machine, and the honest status of the action is `accepted` — nothing is proven until the confirm
command sees a state change:

```yaml
app-store:
  # No .ipa is ever on this machine. The cloud job builds, signs and uploads; this leaf
  # only starts it and later asks App Store Connect what happened.
  action: "__TRIGGER__"
  metrics: "python3 scripts/appstore-status.py downloads"
  confirm:
    command: "python3 scripts/appstore-status.py state"
    url: "https://appstoreconnect.apple.com/apps"
  requirements:
    - "The cloud job holds the distribution certificate, provisioning profile and its own copy
       of the API key. Those are configured in the service's UI, not in this repo, and cannot
       be checked from here."
  issues:
    - "Exit 0 means the job was queued, nothing more. The upload happens minutes later inside
       the job; its own log is where an upload failure shows, and --confirm here only ever
       reports App Store Connect's view."
    - "/orc-publish's preflight cannot run: the artifact is built elsewhere. Whatever checks the
       project wants on the .ipa belong in the cloud job."
```

`distro.yaml` entries: only if the project uses `distro.yaml` for device targets at all. Ask; do
not invent an iOS-version target list.

## 7. Confirmation

`confirm.command` is real here, unlike Play: App Store Connect exposes the version's state
(`WAITING_FOR_REVIEW` → `IN_REVIEW` → `PENDING_DEVELOPER_RELEASE` or `READY_FOR_SALE`, or
`REJECTED` / `METADATA_REJECTED` / `INVALID_BINARY`). The script prints the version and state and
exits 0 only for `READY_FOR_SALE`, so `--confirm` says `confirmed` exactly when the app is live.
`confirm.url` is kept alongside because a rejection's *reason* is only in App Store Connect's
Resolution Center, and a person reads that.

## 8. `RELEASING.md` steps

Two steps, inserted **after the build's tests and lint pass** and **before** commit/tag/push and
forge-release, in this order. The second is manual on purpose (see section 6).

```markdown
## N. Upload the iOS build to App Store Connect

Uploads the signed `.ipa` for `__BUNDLE_ID__`. Requires a Mac with Xcode 26 (local shape) or a
configured cloud Mac (cloud shape).

**One-time setup:** the App Store Connect API key (`__KEY_ID__`) at `__P8_PATH__`, chmod 0600,
with the App Manager role or higher.

Check whether it is already there: `test -s "__P8_PATH__"`

If it is not, generate a team key at App Store Connect → Users and Access → Integrations, download
the `.p8` once, and put it there.

**One-time setup:** the app record, bundle id, version metadata, privacy policy URL, App Privacy
answers, age rating and (for the EU) trader status. Cannot be checked from here; open
`https://appstoreconnect.apple.com/apps` and confirm the version page shows nothing missing.

**Run:** /orc-publish <parent>.app-store

Exit 0 means Apple accepted the upload; the build appears under TestFlight once processed. Do not
continue until it is selectable.

## N+1. Submit the version for review

In App Store Connect, open the version, select the build uploaded in step N, click *Add for
Review*, then *Submit to App Review*. Apple's review is human and takes hours to days.

Check progress with: `/orc-publish <parent>.app-store --confirm` — `confirmed` means the version
is READY_FOR_SALE. A rejection's reason is in App Store Connect → Resolution Center.
```

Renumber everything after the insertion point so the document's steps stay contiguous integers.

## 9. Script template

`templates/appstore-status.py` → the project's `scripts/appstore-status.py`, with `__KEY_ID__`,
`__ISSUER_ID__`, `__P8_PATH__`, `__BUNDLE_ID__` and `__VENDOR__` substituted. Always instantiated —
both leaf shapes use it for `confirm` and `metrics`. `__VENDOR__` may be left as the placeholder if
no vendor number was given; `state` never reads it, and `downloads` then fails with Apple's own
error rather than a fabricated number. The project needs `PyJWT[crypto]` — add it to whatever the
project uses to record dev dependencies, and say so.

## Sources (live on 2026-09-11)

- Program and enrolment: `https://developer.apple.com/programs/enroll/`
- Upcoming/current requirements (Xcode 26, age rating, required-reason APIs, DSA):
  `https://developer.apple.com/news/upcoming-requirements/`
- Privacy manifests:
  `https://developer.apple.com/documentation/bundleresources/adding-a-privacy-manifest-to-your-app-or-third-party-sdk`
- Review guidelines 2.4.1, 2.5.1, 4.8, 5.1.1: `https://developer.apple.com/app-store/review/guidelines/`
- API keys and tokens:
  `https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api`,
  `https://developer.apple.com/documentation/appstoreconnectapi/generating-tokens-for-api-requests`
- Upload methods: `https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/`
- Version states: `https://developer.apple.com/documentation/appstoreconnectapi/appstoreversionstate`
- Sales reports: `https://developer.apple.com/documentation/appstoreconnectapi/get-v1-salesreports`;
  analytics reports (the "App Store Downloads" report, not used here because its first request
  takes 1–2 days to produce anything):
  `https://developer.apple.com/documentation/appstoreconnectapi/downloading-analytics-reports`
- No-Mac builds (vendor sources): `https://blog.codemagic.io/how-to-build-and-distribute-ios-apps-without-mac-with-flutter-codemagic/`
