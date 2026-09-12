# Ingredient: Google Play

**Researched against Google's live pages on 2026-09-11; no release has gone through this yet.**
Every command below is documented by its vendor and none has been run by anyone here. The first
real release through it will find something this file has wrong — when it does, correct the file
(that is what capture is for, per `/orc-package`), and remove this paragraph only when a release
has actually landed.

`/orc-package` asks for these before applying, and uses them everywhere below:

| Ask for | Example | Used as |
|---|---|---|
| Application ID (the package name) | `org.orcshot.orcshot` | `__PACKAGE__` |
| Command that builds the release bundle | `flutter build appbundle --release` | `__BUILD__` |
| Path of the bundle that build writes | `build/app/outputs/bundle/release/app-release.aab` | `__AAB__` |
| Track to publish to | `internal` (start here), later `production` | `__TRACK__` |
| Where the service-account JSON lives (outside the repo) | `${XDG_CONFIG_HOME:-~/.config}/orcshot/play-service-account.json` | `__SA_JSON__` |
| Reporting bucket id, if metrics are wanted | `pubsite_prod_rev_01234567890987654321` | `__BUCKET__` |
| `channels.yaml` path for the leaf | `mobile.dart.android.play` | the leaf's parent |

Apply once per track wanted. `internal` first: it needs no review and is where a first upload
proves the credentials work.

## 1. What the channel is

Google's store for Android. Users install from the Play Store app; Google holds the app's real
signing key and re-signs what you upload (Play App Signing — mandatory for every app created since
August 2021).

Built on: **any machine** with the stack's toolchain (Android SDK; Flutter, Gradle, Unity or
Godot). No platform requirement — Linux is fine.

Takes: an **Android App Bundle** (`.aab`), signed with the project's *upload key*. Producing it —
the keystore, `build.gradle`/`key.properties`, the target SDK, 16 KB page alignment — is the
stack's job and out of this ingredient's scope; the stack skill (`stack-flutter`, and the natives
when written) says where each of the following store rules lands in the build. This ingredient
assumes `__BUILD__` produces `__AAB__` and checks that it does.

The rules the bundle has to meet, as of 2026-09-11, because a bundle that misses one is refused at
upload or blocked at review:

- **Target API level 36 (Android 16)** for new apps and updates, since 2026-08-31 (extension to
  2026-11-01 requestable in Play Console). Existing apps must target ≥35 to stay visible to new
  users. Google moves this every August; re-check the deadline page before trusting the number.
- **16 KB page-size support** for any app with native code targeting Android 15+, since
  2025-11-01; from **2027-02-01** no update ships without it. Flutter's engine, Unity and Godot are
  all native code. Check the built bundle, not the source:
  `bundletool dump config --bundle=__AAB__ | grep alignment` must print `PAGE_ALIGNMENT_16K`.
- **64-bit** native libraries (long-standing).
- The bundle is signed with the upload key the app record knows. A bundle signed with a different
  key is refused.

## 2. Registration — one-time, account-gated, never performed by Orclab

A Google Play developer account. **US$25 one-time.** Identity verification at signup: a government
ID and a card, both under the legal name; a personal account must also prove access to an Android
device through the Play Console mobile app. Two kinds:

- **Personal.** Gated before first production release — see section 5's closed-test rule.
- **Organization.** Exempt from that gate. Google's registration page does not say what it asks
  for instead (a D-U-N-S number is what Apple asks; Google's page does not mention one). Check at
  enrolment.

**Check:** `https://play.google.com/console/` signs in and shows a developer account. Orclab
cannot check this; the user does.

**A second, separate registration arriving now — Android developer verification.** Distinct from
the Play Console account: an identity check for anyone distributing apps to certified Android
devices at all, run through the *Android Developer Console*. Takes effect **2026-09-30** in Brazil,
Indonesia, Singapore and Thailand; global in 2027. Google's page says registration is
"recommended" for distribution exclusively outside Play and is not explicit about what a Play-only
developer must do. **Check at enrolment** rather than assume either way:
`https://support.google.com/android-developer-console/answer/16561738`.

## 3. Credentials — two mechanisms, because they are

**Upload keystore, for signing the bundle.** A Java keystore (`.jks`) holding the upload key. The
*build* uses it, not the publish action — so its path and passwords are the stack's configuration
(Flutter: `android/key.properties`, git-ignored). Google holds the real signing key; if the upload
key is lost, Play Console → Release → Setup → App signing → request an upload key reset. That is
recoverable, which is the reason Play App Signing exists.

- **Check:** the keystore file the stack's config names exists, and
  `keytool -list -keystore <path>` lists the alias (it prompts for the store password on the
  terminal — the user runs this, not Orclab).
- **If missing:** the user generates one (`keytool -genkey -v -keystore <path> -keyalg RSA
  -keysize 2048 -validity 10000 -alias upload`) *before* the app's first upload, because the first
  bundle's signature is what registers the upload key. Orclab never generates or reads it.

**Service account, for the Publishing API.** A Google Cloud service account whose JSON key file the
upload tool reads. Set up once:

1. Google Cloud console → IAM → Service Accounts → create one; create a JSON key; download it to
   `__SA_JSON__` and `chmod 0600` it.
2. Enable the *Google Play Android Developer API* on that Cloud project.
3. Play Console → Users and permissions → Invite new users → the service account's email address,
   with release permissions for the app. (Linking the Cloud project to the Play account is no
   longer required — Google's getting-started page says so explicitly.)

- **Check:** `test -s "__SA_JSON__"` — the file exists and is non-empty. Whether it is *accepted* is
  only proven by the first `validate_only` run in section 6.
- **If missing:** the user does the three steps above. Orclab never creates the account, never
  reads the file, never prints it.

## 4. Machine-local config

**None** beyond the two files above, each of which is a credential and governed by section 3. The
upload tool takes the JSON path on its command line.

## 5. Per-app setup — once per app, before its first release

Everything here is done in Play Console by the user, once per app, and none of it is a per-release
act. `/orc-release` re-checks each on every release through the `**One-time setup:**` markers in
section 8.

1. **The app record.** Play Console → Create app: name, default language, app or game, free or
   paid. The API cannot create an app; the record must exist before any upload.
   **Check:** the app appears at `https://play.google.com/console/` (user).
2. **Store listing** — title, descriptions, screenshots, icon, feature graphic, category, contact
   details. Required before any track beyond internal.
3. **App content declarations** (Play Console → Policy → App content):
   - **Data safety form** — mandatory for every app on closed, open or production tracks, *even
     one that collects nothing*. Requires a **privacy policy URL**, also mandatory regardless.
   - **Account deletion** — if the app lets people create an account, an in-app deletion path
     *and* a public web page to request deletion, both declared in the Data safety form.
   - **Content rating questionnaire** (IARC), ads declaration, target audience.
   **Check:** Play Console shows no outstanding "App content" tasks on the dashboard (user).
4. **The closed-test gate, personal accounts only.** A personal developer account created after
   2023-11-13 cannot publish to production until it has run a closed test with **at least 12
   testers, each opted in continuously for 14 days** (a tester who opts out and returns restarts
   their 14 days), then clicked *Apply for production* on the dashboard and answered its
   questionnaire. Google's stated review time is "within seven days or less." Organization
   accounts skip this entirely.
   **Check:** Play Console dashboard shows the Production track as available (user). Until it
   does, `__TRACK__` cannot be `production`.

## 6. The publish action

The `channels.yaml` leaf at `<parent>.__TRACK__`. The build is its own `prepare:` step, the same
split the PPA ingredient learned the hard way: the irreversible upload and the build that feeds it
must not be one `&&` command, so `/orc-publish`'s preflight has somewhere to run between them.

The upload tool is fastlane's `upload_to_play_store` (also called `supply`). It is the widely used,
vendor-documented way to drive the Publishing API from a shell, it works on Linux, and it has a real
dry run (`validate_only`). It needs Ruby and `gem install fastlane` on the machine. A project that
will not carry Ruby can drive the REST API directly — insert an edit, `POST` the bundle to
`https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications/__PACKAGE__/edits/{editId}/bundles`,
update the track, commit the edit — with scope `https://www.googleapis.com/auth/androidpublisher`;
that is a script the project would own, not this ingredient.

```yaml
__TRACK__:
  # The bundle is built by the stack, signed with the upload key from the stack's own
  # config. This leaf never touches the keystore.
  prepare: "__BUILD__"
  artifact: "__AAB__"
  preflight: [no-vcs, no-tool-state]
  action: "fastlane run upload_to_play_store package_name:__PACKAGE__ aab:__AAB__ json_key:__SA_JSON__ track:__TRACK__ release_status:completed"
  metrics: "gcloud storage cat gs://__BUCKET__/stats/installs/installs___PACKAGE___$(date -u +%Y%m)_overview.csv | iconv -f UTF-16 -t UTF-8 | python3 -c 'import csv,sys; r=list(csv.reader(sys.stdin)); print(\"; \".join(f\"{k}={v}\" for k,v in zip(r[0],r[-1])))'"
  confirm:
    url: "https://play.google.com/console/"
  timeout: 900
  requirements:
    - "Before the first real run on this machine, prove the credentials with the same command
       plus validate_only:true - it exercises the service account and the app record without
       publishing anything. A 401/403 here is a Play Console permission, not a build problem."
    - "A production release needs a completed store listing, Data safety form and content rating,
       and - on a personal account created after 2023-11-13 - the 12-testers-for-14-days closed
       test and an approved 'Apply for production'. None of that is checkable from here; see
       RELEASING.md's one-time setup blocks."
    - "The bundle must target API 36 and, if it carries native code targeting Android 15+, be 16 KB
       page-aligned: `bundletool dump config --bundle=__AAB__ | grep alignment` must say
       PAGE_ALIGNMENT_16K. Play refuses at upload otherwise."
  issues:
    - "release_status:completed publishes to __TRACK__ immediately on Google's side, subject to
       review. Use release_status:draft to stage a release and finish it in Play Console by hand."
    - "A production release is submitted for Google's review when the edit commits, and the
       Publishing API does not expose review state. Exit 0 means accepted, not live - the
       confirm URL is where a person looks."
    - "The metrics CSV lags 3-7 days and is UTF-16; the command converts it and prints the
       latest row. In the first week of a month the current month's file may not exist yet -
       substitute the previous month by hand. gsutil is Google's legacy CLI and leaves the
       Cloud CLI after March 2027 - hence gcloud storage. The bucket id is in Play Console ->
       Download reports."
```

`preflight:` does not include `no-prebuilt-binaries` — an `.aab` is *made of* prebuilt binaries
(`.so` files under `base/lib/`), so that rule would refuse every valid bundle. An `.aab` is a zip,
which `/orc-publish`'s inspector reads (`inspect.py` opens tar and zip), so `no-vcs` and
`no-tool-state` do apply — a stray `.git` or `.gradle` directory packed into a bundle is exactly
the kind of thing they exist to catch.

Omit `metrics:` when no `__BUCKET__` was given; the leaf then reports `(known channel, no metrics
source)`, which is the honest state.

`distro.yaml` entries: only if the project uses `distro.yaml` for device targets at all. Ask; do
not invent an Android-version target list.

## 7. Confirmation

`confirm.url` only. The Publishing API has no review-state endpoint — Google's tracks reference
documents `draft`/`inProgress`/`halted`/`completed` as *release* statuses, and none of them means
"passed review." So a Play publish is always `accepted`, and finding out it landed is a person
opening Play Console (Publishing overview shows "In review" / "Available on Google Play"). If
Google ever exposes review state, this becomes a `confirm.command` and the leaf stops needing a
human.

## 8. `RELEASING.md` steps

One step per applied track, inserted **after the bundle is built and any tests/lint pass** and
**before** the commit/tag/push and forge-release steps. The internal-track step, if the project
has one, precedes the production one.

```markdown
## N. Publish to Google Play (__TRACK__)

Uploads `__AAB__` to the `__TRACK__` track of `__PACKAGE__`. Google re-signs it with the app's
signing key; the bundle is signed with the upload key by the build.

**One-time setup:** the service-account JSON at `__SA_JSON__` (chmod 0600), created in Google
Cloud and invited into Play Console with release permissions.

Check whether it is already there: `test -s "__SA_JSON__"`

If it is not, create the service account, enable the Google Play Android Developer API on its
project, download the JSON key to that path, and invite its email address in Play Console →
Users and permissions.

**One-time setup:** the app's Play Console record, store listing, Data safety form (with privacy
policy URL) and content rating. Cannot be checked from here; open
`https://play.google.com/console/` and confirm the dashboard shows no outstanding App content
tasks.

**One-time setup (production, personal accounts only):** the closed test — 12 testers opted in
for 14 continuous days — and an approved *Apply for production*. Confirm the Production track is
available on the dashboard before running this step against `production`.

**Run:** /orc-publish <parent>.__TRACK__

Exit 0 means Google accepted the upload; a production release is then in review. Check
`https://play.google.com/console/` → the app → Publishing overview. Do not announce the release
until it shows as available on Google Play.
```

Renumber everything after the insertion point so the document's steps stay contiguous integers.

## 9. Script template

**None.** The upload is a documented fastlane invocation, and the metrics read is a one-line
pipeline; neither earns a project-side script. If a project drives the REST API instead of
fastlane, that script is the project's own, per the boundary `/orc-package` keeps — Orclab ships
the knowledge, the project ships its actions.

## Sources (live on 2026-09-11)

- Target API level: `https://developer.android.com/google/play/requirements/target-sdk` (page dated 2026-09-01)
- 16 KB pages: `https://developer.android.com/guide/practices/page-sizes`; Nov 2025 start:
  `https://android-developers.googleblog.com/2025/05/prepare-play-apps-for-devices-with-16kb-page-size.html`
- Account registration: `https://support.google.com/googleplay/android-developer/answer/6112435`
- Closed-test gate: `https://support.google.com/googleplay/android-developer/answer/14151465`
- Android developer verification: `https://support.google.com/android-developer-console/answer/16561738`
- Play App Signing / upload key: `https://developer.android.com/studio/publish/app-signing`
- Data safety: `https://support.google.com/googleplay/android-developer/answer/10787469`
- Account deletion: `https://support.google.com/googleplay/android-developer/answer/13327111`
- Publishing API setup: `https://developers.google.com/android-publisher/getting_started`;
  tracks and statuses: `https://developers.google.com/android-publisher/tracks`
- fastlane: `https://docs.fastlane.tools/actions/upload_to_play_store/`
- Stats bucket: `https://support.google.com/googleplay/android-developer/answer/6135870`;
  gsutil status: `https://docs.cloud.google.com/storage/docs/gsutil`
