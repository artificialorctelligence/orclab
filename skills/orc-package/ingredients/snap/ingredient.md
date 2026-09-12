# Ingredient: Snap Store

Written 2026-09-11 from Orcshot's channel while standing it up — the registration and login were
done for real that day (`snapcraft 9.0.1`), the store's own reviewer was run locally against the
CI-built snap, and every "found live" below was. What has *not* yet happened for Orcshot is a real
upload: the first upload is gated on a human review of the `dbus` slot (section 5), and on a code
change the project made first (BACKLOG #205 there). Where this ingredient says "verify at first
upload", it means exactly that.

`/orc-package` asks for these before applying, and uses them everywhere below:

| Ask for | Example (Orcshot) | Used as |
|---|---|---|
| Snap name (as registered in the store) | `orcshot` | `__SNAP__` |
| Store publisher username (from `snapcraft whoami`) | `artificialorctelligence` | `__PUBLISHER__` |
| First channel to release to | `beta` | `__CHANNEL__` |
| Architecture the CI builds | `amd64` | `__ARCH__` |
| `channels.yaml` path for the leaf | `desktop.python.linux.snap` | the leaf's parent |

## 1. What the channel is

Canonical's app store for strictly confined packages. You upload a built `.snap` and *release* it
to a channel (`edge`, `beta`, `candidate`, `stable`); users `snap install __SNAP__` (`--beta` for a
non-stable channel). Ubuntu preinstalls snapd; Fedora and Arch make it an opt-in install; Linux
Mint blocks it by default. Plan the audience accordingly.

Built on: Linux with `snapcraft` installed (`sudo snap install snapcraft --classic`); `snapcraft
pack` builds inside an LXD or Multipass container it sets up itself. No other platform requirement.

Takes: a built `.snap` from `snapcraft pack` — a working `snapcraft.yaml` is the artifact and is
`/orc-code`'s territory. This ingredient assumes it exists and checks that it does
(`test -f snapcraft.yaml || test -f snap/snapcraft.yaml`).

**Run the store's reviewer locally before the first upload — it is the store's verdict on paper.**
`sudo snap install review-tools` (Canonical's own, the same code the store runs), then
`review-tools.snap-review __SNAP___<version>___ARCH__.snap`. Found live: the snap must sit under
`~/snap/review-tools/common/` for the confined tool to read it. Every `human review required` line
it prints is a store hold that a forum request must clear before that revision can be released to
any channel. The two that matter for desktop apps:

- **A `dbus` slot** (owning a well-known name): `human review required due to 'deny-connection'
  constraint`. Routine for an app-owned session name — precedent: BusyMax asked 2026-06-23,
  granted 2026-06-25, later uploads passed automatically. One forum post, section 5.
- **`personal-files` / `system-files`**: `human review required due to 'allow-installation'
  constraint` — the snap cannot even be *installed* from the store until a declaration is granted,
  and write access to a directory another program loads code from (`~/.local/bin`,
  `~/.local/share/applications`, `gnome-shell/extensions`) was refused as "a trivial confinement
  escape" as recently as 2026-09-04, even for manual connect. Do not plan on it. Change the design
  instead (Orcshot's #205 is one worked example).

Hand-repacking a snap with `mksquashfs` to test a change prints two extra `squashfs-package-v2`
errors that a real `snapcraft pack` does not — ignore those two, and only those two.

## 2. Registration — one-time, account-gated, never performed by Orclab

An Ubuntu One account (free; `https://snapcraft.io/account` creates one), logged into the store
from this machine: `snapcraft login` — on snapcraft 9 this prompts for the Ubuntu One e-mail and
password in the terminal (older versions opened a browser). The credential lands in the system
keyring (file fallback if there is none) and expires one year out.

**Check:** `snapcraft whoami` prints `username: __PUBLISHER__`, a `permissions:` line containing
`package_push`, `package_release` and `package_register`, and an `expires:` date in the future.
Pipe it through `sed 's/\(email:\).*/\1 <redacted>/'` before it reaches a transcript.

**If missing:** the user runs `snapcraft login` in their own terminal. Never run it, never type
into it; carry on writing the recipe.

## 3. Credentials

**Store login (the keyring credential from section 2).** Used by `snapcraft upload`.

- **Check:** `snapcraft whoami` exits 0 (the redacted form above).
- **If missing/expired:** the user runs `snapcraft login` again. Orclab never types into it.

**Headless / CI credential — only if the action is ever run somewhere without the keyring.**
`snapcraft export-login <file>` (interactive, once) produces a token file;
`SNAPCRAFT_STORE_CREDENTIALS=$(cat <file>)` in the environment authenticates non-interactively.
Restrict it: `--snaps=__SNAP__ --channels=__CHANNEL__ --acls=package_push,package_release
--expires=<ISO date>`. The file is a credential: 0600, outside the repo, never printed, never
committed — `secret-hygiene`. Not needed for a publish run from the developer's own machine, and
not written by this ingredient.

## 4. Machine-local config

**None.** `snapcraft` needs nothing beyond the keyring login. `review-tools` is a snap you install
once; its input directory (`~/snap/review-tools/common/`) is created by installing it.

## 5. Per-app setup — once per snap, before its first release

1. **Name registration.** `snapcraft register __SNAP__` — claims the name, asks one "will most
   users expect this name to come from you?" question, done. Public by default. The user runs it.
   **Check:** `snapcraft names` lists `__SNAP__`. **Not** `snap info __SNAP__` — that answers
   "no snap found" until a revision has been *released*, so it is the confirmation test in
   section 7, not this one.
2. **The store's automated review, run locally** (section 1) — every `human review required`
   line is an item here. For a `dbus` slot: after the first upload is held, post in the forum's
   `store-requests` category — snap name, the bus name, one sentence on why the app owns it
   (single-instance, tray menu export). A reviewer grants a snap declaration; "the newer version
   of the snaps should pass the automated reviews", i.e. re-upload after the grant, the held
   revision is not released retroactively. Two days for BusyMax (2026-06-23 → 06-25).
   **Check:** `snap info __SNAP__` shows a channel map on any channel — the only proof a revision
   got past review.
3. **The store listing** — icon, screenshots, category, long description — is set in the
   snapcraft.io dashboard (`https://snapcraft.io/__SNAP__/listing`), not in `snapcraft.yaml`. It
   does not block a release; until it is done the store page is bare.
   **Check:** none from here; the user looks at `https://snapcraft.io/__SNAP__`.

## 6. The publish action

The `channels.yaml` leaf at `<parent>`:

```yaml
snap:
  # `snapcraft pack` builds in an LXD/Multipass container it manages itself; the first build on
  # a machine sets that up and takes minutes. The .snap lands in the project root.
  prepare: "snapcraft pack"
  artifact: "__SNAP___$(grep -m1 '^version' pyproject.toml | sed -E 's/^version *= *\"([^\"]+)\"/\\1/')___ARCH__.snap"
  preflight: [no-vcs, no-tool-state]
  # Upload and release in one command. The store runs its automated review on receipt; if it
  # passes, the revision is live on __CHANNEL__ immediately. If a human review is required the
  # command reports it and the revision waits - see requirements.
  action: "snapcraft upload --release=__CHANNEL__ __SNAP___$(grep -m1 '^version' pyproject.toml | sed -E 's/^version *= *\"([^\"]+)\"/\\1/')___ARCH__.snap"
  confirm:
    url: "https://snapcraft.io/__SNAP__"
  metrics: "snapcraft metrics __SNAP__ --format=json --name weekly_installed_base_by_operating_system"
  requirements:
    - "Run `review-tools.snap-review <the .snap>` first. Any `human review required` line is a
       store hold; a `dbus` slot hold needs the one-time forum request (RELEASING.md's one-time
       setup on this step) before any revision can be released."
    - "`snapcraft whoami` must succeed on this machine (login expires yearly)."
    - "First release goes to __CHANNEL__, never straight to stable: it exercises review and the
       pipeline without the public listing that search and reviews land on. Promote with
       `snapcraft release __SNAP__ <revision> stable` once one real `snap install --__CHANNEL__
       __SNAP__` on a clean machine has been confirmed."
  issues:
    - "The artifact expression reads the version from pyproject.toml; substitute the project's
       real single source of truth if it is elsewhere (debian/changelog, package.json). The
       snap's own `version:` must come from the same place or the filename will not match."
    - "Only the architecture CI builds gets published. An amd64-only snap is invisible to arm64
       users; that is a product fact to state, not a bug."
```

`distro.yaml` entries: one per distro/session target the user names that installs from the store,
`channel: <parent>`. Ask; do not invent them.

## 7. Confirmation

`confirm.url` is the store page. The mechanical check is `snap info __SNAP__` listing the channel
map with the new version on `__CHANNEL__` — this is also the only thing that distinguishes
"accepted and released" from "accepted and held for human review", which `snapcraft upload`'s exit
code does not.

Metrics: the leaf's `metrics:` uses `weekly_installed_base_by_operating_system`, one of the twelve
metric names checked against the live snapcraft reference on 2026-09-10 (`/orc-publish`'s own
table; `installed_base_by_channel` is another). It needs the store login — Snap metrics are
confidential to the publisher, so no one but the author can run it — and has never produced
output for any Orclab-adjacent snap. When it first does, correct `/orc-publish`'s "Never run" row.

## 8. `RELEASING.md` steps

One step, inserted **after the artifact is built and CI is green for that commit** and **before**
the forge-release step. The store listing note belongs in its one-time setup because nothing in
`snapcraft.yaml` produces it.

```markdown
## N. Upload the snap to the Snap Store (__CHANNEL__)

**One-time setup:** three things, once per snap, all yours to do:
- Store login and name registration: check with `snapcraft whoami` (redact the e-mail line) and
  `snapcraft names`. If missing: `snapcraft login`, then `snapcraft register __SNAP__`.
  Both were done for Orcshot on 2026-09-11; the login expires 2027-09-11.
- The `dbus` slot declaration, if the snap owns a bus name: the first upload is held with
  `human review required due to 'deny-connection' constraint`. Post in the snapcraft forum's
  `store-requests` category (snap name, bus name, one sentence on why); re-upload after the
  grant. Check: `snap info __SNAP__` shows a channel map.
- The store listing (icon, screenshots, category, description) is set in the snapcraft.io
  dashboard, not in `snapcraft.yaml`. Until it is done the store page is bare.

**Run:** review-tools.snap-review on the built .snap, then /orc-publish <parent>

Confirm with `snap info __SNAP__`: the new version is on `__CHANNEL__`. Promote to `stable`
only after one real install from `__CHANNEL__` on a clean machine.
```

Renumber everything after the insertion point so the document's steps stay contiguous integers.

## 9. Script template

**None.** Every action here is a first-party `snapcraft` command. If the project needs a
version-derivation script because its version lives somewhere `grep` cannot reach, that is the
project's script, not this ingredient's.

## Sources (live on 2026-09-11)

- Upload and release: `https://ubuntu.com/docs/snapcraft/stable/how-to/publishing/publish-a-snap/`
- Login, `export-login`, `SNAPCRAFT_STORE_CREDENTIALS`:
  `https://ubuntu.com/docs/snapcraft/stable/how-to/publishing/authenticate/`
- `personal-files` needs a declaration: `https://snapcraft.io/docs/reference/interfaces/personal-files-interface/`
- A write request refused as a confinement escape (2026-08-26 → 09-04):
  `https://forum.snapcraft.io/t/auto-connect-request-for-personal-files-interfaces-appimage-installer/52903`
- A `dbus` slot granted in two days: `https://forum.snapcraft.io/t/d-bus-slot-declaration-request-busymax/51941`
- Classic confinement is not available for desktop-shell extensions:
  `https://snapcraft.io/docs/reference/administration/reviewing-classic-confinement-snaps/`
- The `dbus` slot's AppArmor policy (receive from unconfined on the owned name/path, no send):
  `https://github.com/canonical/snapd/blob/master/interfaces/builtin/dbus.go`
- `review-tools` (snap, publisher canonical): `snap info review-tools`; run on Orcshot's 0.3.0
  CI build, 2026-09-11: exactly `personal-files` (`allow-installation`) and `dbus`
  (`deny-connection`); with the plug removed, `dbus` alone.
