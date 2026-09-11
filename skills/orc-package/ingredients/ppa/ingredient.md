# Ingredient: PPA (Launchpad personal package archive)

Written from Orcshot's channel, stood up 2026-09-06/07 — the only channel anyone here has
actually put a release through. Where this says "found live", it was.

`/orc-package` asks for these before applying, and uses them everywhere below:

| Ask for | Example (Orcshot) | Used as |
|---|---|---|
| Launchpad owner (person or team) | `artificialorctelligence` | `__OWNER__` |
| PPA name | `orcshot` | `__PPA__` |
| Debian source package name | `orcshot` | `__SOURCE__` |
| Series you upload to | `noble` | `__FROM_SERIES__` |
| Series you copy to, if any | `resolute` | `__TO_SERIES__` |
| GPG signing key fingerprint | `FAF7…280A` (40 hex chars) | `<KEY>` |
| `channels.yaml` path for the leaf | `desktop.python.linux.ppa` | the leaf's parent |

## 1. What the channel is

An apt repository hosted by Launchpad. It builds from a **source** upload: you sign and `dput` a
`_source.changes`, and Launchpad's build farm compiles or assembles the binary. Users add
`ppa:__OWNER__/__PPA__` and `apt install __SOURCE__`.

Takes: a Debian source package — a `debian/` directory in the project and a working
`dpkg-buildpackage -S`. Producing that is out of this ingredient's scope (it is the artifact,
`/orc-code`'s territory); this ingredient assumes `debian/` exists and checks that it does.

## 2. Registration — one-time, account-gated, never performed by Orclab

The PPA must exist on Launchpad under the owner's account. Orclab never creates it.

**Check:** `https://launchpad.net/~__OWNER__/+archive/ubuntu/__PPA__` returns a page, not a 404.
A shell form: `curl -sfI https://launchpad.net/~__OWNER__/+archive/ubuntu/__PPA__ >/dev/null`.

**If missing:** the user creates it at `https://launchpad.net/~__OWNER__/+activate-ppa` (a team's
PPA is created from the team's page). Say that, and stop until they have.

## 3. Credentials — two different mechanisms, because they are

**Signing key, for uploads.** `dput` never authenticates; Launchpad recognizes the GPG key that
signed the `.changes`. The key must be registered to the Launchpad account *and* present in this
machine's keyring.

- **Check (this machine):** `gpg --list-secret-keys <KEY>`
- **Check (Launchpad):** the key's fingerprint appears at `https://launchpad.net/~__OWNER__/+editpgpkeys`
- **If missing:** the user imports or generates it and registers it with Launchpad. Orclab never
  does either. Discovering this at `debsign` time leaves a built, unsigned package and a half-done
  step, which is why it is a `**One-time setup:**` block on the upload step.

**OAuth token, for the series copy** (only if `__TO_SERIES__` is set). Copying between series
modifies an existing archive, which needs a real authenticated identity that a signature cannot
supply. `scripts/ppa-copy-series.py` stores the token at
`~/.config/__SOURCE__/launchpad-credentials.txt`, `chmod 0600`.

- **Check:** `python3 scripts/ppa-copy-series.py --check`
- **If missing:** the user runs `python3 scripts/ppa-copy-series.py --version <X.Y.Z-1>` once and
  completes the browser authorization it opens. Orclab never runs that command on the user's
  behalf, and never reads, prints, or copies the file.

## 4. Machine-local config

**None.** `dput` resolves `ppa:__OWNER__/__PPA__` through the `[ppa]` stanza that ships in
`/etc/dput.cf`; a `~/.dput.cf` entry is not needed (Orcshot's release doc records that its
`[orcshot-ppa]` section was written and then found unnecessary). The OAuth token in section 3 is a
credential, not config, and is governed by that section.

## 5. The publish action

The `channels.yaml` leaf at `<parent>.__FROM_SERIES__`:

```yaml
__FROM_SERIES__:
  # Derives the exact .changes filename from debian/changelog via dpkg-parsechangelog,
  # rather than a glob or a hardcoded version. A glob (../*.changes) is actively WRONG,
  # found live 2026-09-06: the parent directory accumulates every past build's .changes
  # file, and a binary build's .changes sits beside the source build's for the same
  # version - a PPA rejects a binary upload.
  action: "dpkg-buildpackage -us -uc -S -sa && debsign -k<KEY> ../__SOURCE___$(dpkg-parsechangelog --show-field Version)_source.changes && dput ppa:__OWNER__/__PPA__ ../__SOURCE___$(dpkg-parsechangelog --show-field Version)_source.changes"
  metrics: "python3 $ORC_PUBLISH_SCRIPTS/metrics/launchpad_ppa.py __OWNER__/__PPA__ --package __SOURCE__ --series __FROM_SERIES__"
  requirements:
    - "The -k on debsign is load-bearing. Without it debsign derives the signing identity from
       debian/changelog's maintainer field; if that is not the registered key it fails with
       `gpg: skipped ...: No secret key`. Confirm the key is present before a real run:
       `gpg --list-secret-keys <KEY>`."
    - "Before confirming a real (non-dry-run) run: unlock gpg-agent yourself, in your own
       terminal, so it caches your passphrase - e.g. `echo test | gpg --clearsign > /dev/null`.
       debsign then signs against the warm agent instead of prompting from inside the subprocess."
  issues:
    - "debsign asks for a GPG passphrase interactively. Actions run under a timeout and in their
       own session with no controlling terminal, so an unwarmed agent fails fast as `failed`
       rather than hanging. Pre-warming per the requirement above is the fix."
```

If `__TO_SERIES__` is set, a second leaf at `<parent>.__TO_SERIES__`:

```yaml
__TO_SERIES__:
  # Not a second source upload: for a package that is Architecture: all with no
  # series-specific build-dependencies, the binary built for __FROM_SERIES__ is copied as-is.
  # Version comes from debian/changelog the same way the upload's does.
  action: "python3 scripts/ppa-copy-series.py --version $(dpkg-parsechangelog --show-field Version)"
  metrics: "python3 $ORC_PUBLISH_SCRIPTS/metrics/launchpad_ppa.py __OWNER__/__PPA__ --package __SOURCE__ --series __TO_SERIES__"
  confirm:
    url: "https://launchpad.net/~__OWNER__/+archive/ubuntu/__PPA__/+packages"
  requirements:
    - "One-time per machine: run `python3 scripts/ppa-copy-series.py --check`. If it reports no
       credentials, run the script once without --check - it opens a browser once to authorize,
       then stores an OAuth token at ~/.config/__SOURCE__/launchpad-credentials.txt (chmod 0600).
       Never cat that file."
  issues:
    - "Ordering, not optional: this cannot run until __FROM_SERIES__'s build has actually
       SUCCEEDED on Launchpad's build farm - not merely until the upload was accepted. The script
       refuses and exits non-zero if the source isn't Published with built binaries."
    - "The copy is asynchronous. Launchpad's own docs: files can take up to twenty minutes to
       appear. A green exit means the copy was accepted, not that it has landed."
```

**Only apply the copy leaf when the package is `Architecture: all`** (check `debian/control`) and
the user confirms it has no series-specific build-dependencies. A compiled package needs a second
source upload per series, not a copy; say so and apply only the upload leaf.

`distro.yaml` entries: for each distro/session target the user names that installs from
`__FROM_SERIES__`, `channel: <parent>.__FROM_SERIES__`; for targets on `__TO_SERIES__`,
`channel: <parent>.__TO_SERIES__`. Ask which targets the project supports; do not invent them.

## 6. Confirmation

The upload leaf needs no `confirm`: `dput` exits non-zero on rejection, and the build's success is
the *next* step's precondition, not this step's outcome. The copy leaf declares `confirm.url` (the
packages page) because Launchpad's copy is asynchronous — `accepted` is the honest status.

## 7. `RELEASING.md` steps

Two steps, inserted **after the artifact is built and linted** and **before** any install-test,
commit/tag/push, or forge-release step, in this order:

```markdown
## N. Upload to the PPA

`ppa:__OWNER__/__PPA__` on Launchpad. PPAs build from a *source* upload, not the binary `.deb` -
Launchpad's build farm assembles the package itself.

**One-time setup:** the signing key must exist in this machine's keyring. It cannot be derived
from the package.

Check whether it is already there: `gpg --list-secret-keys <KEY>`

If it is not, import or generate the key registered to the Launchpad account before going further.

**Run:** /orc-publish <parent>.__FROM_SERIES__

Check build status at `https://launchpad.net/~__OWNER__/+archive/ubuntu/__PPA__/+packages`. The
next step must not run until this build has **succeeded** — not merely been accepted.

## N+1. Copy the built package to __TO_SERIES__

**Preconditions:** the `__FROM_SERIES__` build has **succeeded** on Launchpad. The script also
refuses if it hasn't.

**One-time setup:** authorizing this machine against Launchpad's API, once per machine.

Check whether it is already done: `python3 scripts/ppa-copy-series.py --check`

If it is not, run `python3 scripts/ppa-copy-series.py --version <X.Y.Z-1>` once and complete the
browser authorization it opens.

**Run:** /orc-publish <parent>.__TO_SERIES__
```

Omit step N+1 entirely when there is no `__TO_SERIES__`. Renumber everything after the insertion
point so the document's steps stay contiguous integers.

## 8. Script template

`templates/ppa-copy-series.py` → the project's `scripts/ppa-copy-series.py`, with the five
`__PLACEHOLDERS__` substituted. Only when `__TO_SERIES__` is set. The project then needs
`launchpadlib` (Debian/Ubuntu: `python3-launchpadlib`) — add it to whatever the project uses to
record dev dependencies, and say so; `--help` and `--check` work before it is installed.
