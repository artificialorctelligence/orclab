# Orclab v15: `/orc-package` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Orclab a `/orc-package <channel>` command that applies a shipped or user-captured *ingredient* — the reusable knowledge of how to stand up one distribution channel — to the current project's *recipe* (its `channels.yaml`, `distro.yaml`, `RELEASING.md`, `scripts/`), shipping the PPA ingredient written from the only channel anyone here has actually stood up.

**Architecture:** One prose skill, `skills/orc-package/SKILL.md`, that reads a markdown ingredient and follows it, the way Claude reads any skill. One shipped ingredient directory, `skills/orc-package/ingredients/ppa/`, holding the prose plus the Launchpad series-copy script as a template with five `__PLACEHOLDERS__`. User-level ingredients live under `${ORCLAB_INGREDIENTS_DIR:-${XDG_CONFIG_HOME:-~/.config}/orclab/ingredients}/<channel>/` in the same shape and win over shipped ones by name. No registry, no schema, no runtime code in Orclab — the only Python is the template, which is copied into the *project* and never imported by Orclab.

**Tech Stack:** Markdown. The template is Python 3.12 using `launchpadlib` (a dependency of the *consuming project*, stated in the ingredient; Orclab itself gains none). pytest for the one template check.

## Global Constraints

- Source of truth: `docs/superpowers/specs/2026-09-08-orclab-v15-orc-package-ingredients-design.md`, as corrected 2026-09-10 (the PPA ingredient has **no** machine-local config).
- **No new dependency for Orclab.** `launchpadlib` is required by the instantiated template inside a consuming project, and the ingredient says so; nothing under `skills/orc-package/` imports it at module top, so `--help` and `--check` work on a machine without it.
- **`disable-model-invocation: true`** on the skill — one-shot and side-effecting. **No unscoped `Bash` pre-approval** in `allowed-tools`; writes outside the repo must each surface a permission prompt.
- **Never a credential.** The skill and the ingredient never write a token, key, or passphrase, never print one, never `cat` the credentials file. `secret-hygiene` applies.
- **Never an account-gated action.** Creating a PPA, registering a key with Launchpad, and the OAuth authorization are described, checked, and prompted for — never performed.
- **Merge, never overwrite**, for every write into a project's recipe: an existing `channels.yaml` leaf, `distro.yaml` entry, or `RELEASING.md` step is left alone and reported, not replaced.
- **`RELEASING.md` steps are contiguous integers** after insertion. Renumber when inserting mid-document, per `release-checklist`; never sub-number (`6a`), which makes steps vanish from `/orc-release`'s parser.
- **The `orc-` prefix holds**, so `/orc-help`'s `skills/orc*/SKILL.md` glob lists it.
- **Do not touch `~/projects/orcshot`** or any real `$HOME`. Every check uses `tmp_path` and a scratch `HOME`. Applying the ingredient to Orcshot happens in a session centred on Orcshot, later.
- Run the template check with `cd skills/orc-package/scripts && python3 -m pytest tests/ -v`.
- Every commit message ends with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `skills/orc-package/ingredients/ppa/ingredient.md` | The PPA ingredient: the eight-part shape, written from Orcshot's real recipe | 1 |
| `skills/orc-package/ingredients/ppa/templates/ppa-copy-series.py` | The series-copy script with `__OWNER__`, `__PPA__`, `__SOURCE__`, `__FROM_SERIES__`, `__TO_SERIES__` placeholders; lazy `launchpadlib` import | 1 |
| `skills/orc-package/scripts/conftest.py` | Empty; makes the suite run from any cwd (repo convention) | 1 |
| `skills/orc-package/scripts/tests/test_ppa_template.py` | Instantiates the template into `tmp_path` and proves `--help` and `--check` work without `launchpadlib` and without a credential | 1 |
| `skills/orc-package/SKILL.md` | The command: list, apply, capture; ingredient resolution and precedence; the safety rules | 2 |
| `VERIFICATION.md` | Seven new scenarios from the spec's Testing section | 3 |
| `README.md` | One bullet in the command list | 3 |
| `BACKLOG.md` | `#17` resolved, layered | 3 |

---

### Task 1: The PPA ingredient and its template

**Files:**
- Create: `skills/orc-package/ingredients/ppa/ingredient.md`
- Create: `skills/orc-package/ingredients/ppa/templates/ppa-copy-series.py`
- Create: `skills/orc-package/scripts/conftest.py` (empty)
- Test: `skills/orc-package/scripts/tests/test_ppa_template.py`

**Interfaces:**
- Consumes: nothing in Orclab. Source material is Orcshot's real recipe, quoted below — do not open `~/projects/orcshot`; everything needed is in this task.
- Produces: the ingredient shape (eight numbered sections with these exact headings) that Task 2's SKILL.md tells Claude to read, and the five placeholder names Task 2's apply flow substitutes.

- [ ] **Step 1: Write the failing template test**

```python
# skills/orc-package/scripts/tests/test_ppa_template.py
"""The template is copied into a consuming project, never imported by Orclab. What Orclab can
prove about it: after placeholder substitution it is valid Python, its --help runs, and its
--check answers the one-time-setup question without launchpadlib installed and without ever
creating a credential."""

import pathlib
import subprocess
import sys

TEMPLATE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "ingredients" / "ppa" / "templates" / "ppa-copy-series.py"
)
FILLED = {
    "__OWNER__": "someone", "__PPA__": "theirppa", "__SOURCE__": "theirpkg",
    "__FROM_SERIES__": "noble", "__TO_SERIES__": "resolute",
}


def instantiate(tmp_path):
    text = TEMPLATE.read_text()
    for placeholder, value in FILLED.items():
        text = text.replace(placeholder, value)
    assert "__" not in text.replace("__main__", "").replace("__name__", ""), \
        "every placeholder must be one of the five documented ones"
    out = tmp_path / "ppa-copy-series.py"
    out.write_text(text)
    return out


def run(script, *args, home):
    # PYTHONPATH cleared and a fake HOME: launchpadlib must not be needed for these paths,
    # and nothing may be written into the real home directory.
    return subprocess.run(
        [sys.executable, "-S", str(script), *args],
        capture_output=True, text=True, env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
    )


def test_help_runs_without_launchpadlib(tmp_path):
    script = instantiate(tmp_path)
    out = run(script, "--help", home=tmp_path)
    assert out.returncode == 0, out.stderr
    assert "--check" in out.stdout and "--dry-run" in out.stdout


def test_check_reports_no_credentials_and_creates_nothing(tmp_path):
    script = instantiate(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    out = run(script, "--check", home=home)
    assert out.returncode == 1
    assert "no launchpad credentials" in out.stderr
    assert not list(home.rglob("*")), "--check must never create a file, let alone a credential"


def test_check_passes_when_a_credential_file_exists(tmp_path):
    script = instantiate(tmp_path)
    creds = tmp_path / "creds.txt"
    creds.write_text("not-a-real-token")
    out = run(script, "--check", "--credentials", str(creds), home=tmp_path)
    assert out.returncode == 0
    assert "credentials present" in out.stdout
    assert "not-a-real-token" not in out.stdout + out.stderr, "never print the credential"


def test_the_default_credentials_path_is_per_project_under_xdg_config(tmp_path):
    script = instantiate(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    out = run(script, "--check", home=home)
    assert str(home / ".config" / "theirpkg" / "launchpad-credentials.txt") in out.stderr
```

- [ ] **Step 2: Run it to verify it fails**

Run: `mkdir -p skills/orc-package/scripts/tests && touch skills/orc-package/scripts/conftest.py && cd skills/orc-package/scripts && python3 -m pytest tests/ -v`
Expected: 4 FAIL — `FileNotFoundError` on the template path.

- [ ] **Step 3: Write the template**

This is Orcshot's `scripts/ppa-copy-series.py` (its 2026-09-07 version) with three changes and nothing else: the five project-specific values become placeholders; `launchpadlib` is imported inside the two login functions so `--help` and `--check` run without it; the default credentials path is derived from `__SOURCE__`. Keep every docstring — they are the reasoning a project's maintainer will read.

```python
#!/usr/bin/env python3
"""Copy an already-built PPA source between Ubuntu series, via Launchpad's API.

Instantiated into this project by Orclab's `/orc-package ppa`. The project owns this copy and
may edit it; Orclab does not carry a live Launchpad client in its own runtime.

Why this exists as an API call rather than another `dput`: `dput` never authenticates to
Launchpad at all. It is an anonymous upload whose authorization is the GPG signature on the
`.changes` file - Launchpad recognizes the key, not a user. Copying between series modifies an
existing archive, which needs a real authenticated identity, and a GPG signature cannot supply
one. Hence OAuth, and hence the one-time authorization below.

Credentials are kept in a plain file rather than the GNOME keyring, deliberately: the file path
is checkable by a shell test, which is what `/orc-release`'s `**One-time setup:**` marker needs
in order to tell whether setup has already happened without running the setup itself.

The file is an OAuth token. It is chmod 0600 on save. Never cat it, never paste it into a
transcript - see Orclab's `secret-hygiene` skill.

Requires `launchpadlib` (Debian/Ubuntu: `python3-launchpadlib`; or `pip install launchpadlib`).
It is imported only when a Launchpad session is actually opened, so `--help` and `--check`
work on a machine that has not installed it yet.
"""

import argparse
import os
import pathlib
import sys

OWNER = "__OWNER__"
PPA = "__PPA__"
SOURCE = "__SOURCE__"
FROM_SERIES = "__FROM_SERIES__"
TO_SERIES = "__TO_SERIES__"

DEFAULT_CREDENTIALS = pathlib.Path.home() / ".config" / SOURCE / "launchpad-credentials.txt"
APPLICATION_NAME = f"{SOURCE}-release"


def credentials_path(override):
    return pathlib.Path(override) if override else DEFAULT_CREDENTIALS


def has_credentials(path):
    """True when a usable credential already exists - the one-time-setup check."""
    return path.is_file() and path.stat().st_size > 0


def log_in_anonymously():
    """Read-only session. Launchpad serves public PPA data with no credential at all.

    Every precondition check below is a read, so --dry-run needs no authorization: it can
    verify the copy would be valid on a machine that has never been set up.
    """
    from launchpadlib.launchpad import Launchpad

    return Launchpad.login_anonymously(APPLICATION_NAME, "production", version="devel")


def log_in(path):
    """Log in for writing, authorizing through a browser only if no credential is cached yet."""
    from launchpadlib.launchpad import Launchpad

    path.parent.mkdir(parents=True, exist_ok=True)
    launchpad = Launchpad.login_with(
        APPLICATION_NAME, "production", version="devel", credentials_file=str(path)
    )
    if path.is_file():
        # launchpadlib does not restrict the mode itself; this is an OAuth token.
        os.chmod(path, 0o600)
    return launchpad


def find_published_source(ppa, source_name, version, series_name):
    """Return the published source in `series_name`, or None.

    This is the precondition that makes the copy safe. Copying a source Launchpad has not
    finished building yet is the mistake this guards against - the copy would carry no binaries,
    silently producing a source-only publication in the target series.
    """
    distro_series = ppa.distribution.getSeries(name_or_version=series_name)
    for source in ppa.getPublishedSources(
        source_name=source_name,
        version=version,
        distro_series=distro_series,
        status="Published",
        exact_match=True,
    ):
        return source
    return None


def built_binaries(source):
    """The binary names already built for a published source, as a sorted list."""
    return sorted({b.binary_package_name for b in source.getPublishedBinaries()})


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ppa-copy-series",
        description="Copy an already-built PPA source from one Ubuntu series to another.",
    )
    parser.add_argument("--owner", default=OWNER)
    parser.add_argument("--ppa", default=PPA)
    parser.add_argument("--source", default=SOURCE)
    # Not argparse-required: --check is a setup probe that needs no version, and the
    # `**One-time setup:**` block in RELEASING.md has to be a clean one-liner.
    parser.add_argument("--version", help="e.g. 0.3.0-1; required unless --check")
    parser.add_argument("--from-series", default=FROM_SERIES)
    parser.add_argument("--to-series", default=TO_SERIES)
    parser.add_argument("--credentials", default=None, help="override the credentials file path")
    parser.add_argument(
        "--check",
        action="store_true",
        help="report whether the one-time Launchpad authorization has been done, and stop",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    creds = credentials_path(args.credentials)

    if args.check:
        if has_credentials(creds):
            print(f"launchpad credentials present: {creds}")
            return 0
        print(f"error: no launchpad credentials at {creds}", file=sys.stderr, flush=True)
        print(
            "  run this script once without --check to authorize; it opens a browser exactly "
            "once per machine",
            file=sys.stderr,
            flush=True,
        )
        return 1

    if not args.version:
        parser.error("--version is required unless --check is given")

    if args.dry_run:
        # Reads only, so no credential and no browser - a dry run works on a fresh machine.
        launchpad = log_in_anonymously()
    else:
        if not has_credentials(creds):
            print(
                f"no cached credential at {creds} - a browser will open once to authorize",
                flush=True,
            )
        launchpad = log_in(creds)
    ppa = launchpad.people[args.owner].getPPAByName(name=args.ppa)

    source = find_published_source(ppa, args.source, args.version, args.from_series)
    if source is None:
        print(
            f"error: {args.source} {args.version} is not Published in {args.from_series} - "
            "nothing to copy. If the upload just happened, Launchpad's build farm has not "
            "finished yet; wait for the build to succeed before copying.",
            file=sys.stderr,
            flush=True,
        )
        return 1

    binaries = built_binaries(source)
    if not binaries:
        print(
            f"error: {args.source} {args.version} is published in {args.from_series} but has no "
            "built binaries yet - copying now would publish a source with nothing installable. "
            "Wait for the build to finish.",
            file=sys.stderr,
            flush=True,
        )
        return 1

    print(f"source:   {args.source} {args.version} ({args.from_series}, Published)", flush=True)
    print(f"binaries: {', '.join(binaries)}", flush=True)
    print(f"copy to:  {args.to_series} (Release pocket, binaries included)", flush=True)

    if args.dry_run:
        print("dry run - nothing copied", flush=True)
        return 0

    ppa.copyPackage(
        from_archive=ppa,
        source_name=args.source,
        version=args.version,
        from_series=args.from_series,
        to_series=args.to_series,
        to_pocket="Release",
        include_binaries=True,
    )
    print(
        f"copy requested: {args.source} {args.version} {args.from_series} -> {args.to_series}.\n"
        "Launchpad copies asynchronously - the source appears in the archive listing right away, "
        "but the files can take up to twenty minutes to show up. Confirm at\n"
        f"  https://launchpad.net/~{args.owner}/+archive/ubuntu/{args.ppa}/+packages",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd skills/orc-package/scripts && python3 -m pytest tests/ -v`
Expected: 4 PASS. If `test_help_runs_without_launchpadlib` fails with `ModuleNotFoundError`, an import escaped to module top — move it back inside the login function.

- [ ] **Step 5: Write the ingredient**

Every fact below comes from Orcshot's real `channels.yaml`, `distro.yaml` and `RELEASING.md` as of 2026-09-07. The `<placeholders in angle brackets>` are what `/orc-package` asks the user for; the `__PLACEHOLDERS__` are what it substitutes into the template. Write this file exactly:

````markdown
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
````

- [ ] **Step 6: Check the ingredient's shape mechanically**

Run: `grep -c '^## [1-8]\. ' skills/orc-package/ingredients/ppa/ingredient.md`
Expected: `8`.

Run: `grep -o '__[A-Z_]*__' skills/orc-package/ingredients/ppa/ingredient.md skills/orc-package/ingredients/ppa/templates/ppa-copy-series.py | sort -u | cut -d: -f2 | sort -u`
Expected: exactly `__FROM_SERIES__`, `__OWNER__`, `__PPA__`, `__SOURCE__`, `__TO_SERIES__` — the ingredient and the template agree on the placeholder set.

- [ ] **Step 7: Commit**

```bash
git add skills/orc-package/
git commit -m "v15: the PPA ingredient, and the series-copy script as a template

Written from Orcshot's real recipe. The template is Orcshot's scripts/ppa-copy-series.py with
five placeholders and a lazy launchpadlib import, so --help and --check work before the
project installs it and the one-time-setup check never creates a credential.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: The `/orc-package` skill

**Files:**
- Create: `skills/orc-package/SKILL.md`

**Interfaces:**
- Consumes: the ingredient shape from Task 1 — eight `## N.` sections; the five `__PLACEHOLDERS__`; `templates/` beside `ingredient.md`.
- Produces: the three invocations the README and verification scenarios describe: `/orc-package` (list), `/orc-package <channel>` (apply, or offer capture).

- [ ] **Step 1: Write the skill**

````markdown
---
name: orc-package
description: Use when the user explicitly asks to use orc-package, or types /orc-package, to stand up a distribution channel for the current project - applying a shipped or captured ingredient (how to set up a PPA, a store, a registry) to the project's own channels.yaml, distro.yaml and RELEASING.md, or capturing a new ingredient for a channel Orclab does not ship yet.
disable-model-invocation: true
allowed-tools: Read, Bash(ls *), Bash(grep *), Bash(gpg --list-secret-keys *)
---

# orc-package

Applies an **ingredient** — the reusable knowledge of how to stand up one distribution channel —
to this project's **recipe**: its `.orclab/publish/channels.yaml`, `.orclab/publish/distro.yaml`,
`RELEASING.md`, and `scripts/`. A project's recipe already exists in those files; this command
writes into it, it does not invent a new artifact.

**This is one-shot and side-effecting, and it stands up channels.** It is never reached because a
request superficially matched; the user types it. Standing up a distribution channel is always
something the user asks for directly — the same rule `/orc-release`'s `**One-time setup:**`
blocks already enforce.

## Where ingredients live, and which one wins

Two places, checked in this order:

1. **User-level:** `${ORCLAB_INGREDIENTS_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/orclab/ingredients}/<channel>/ingredient.md`
2. **Shipped:** `${CLAUDE_SKILL_DIR}/ingredients/<channel>/ingredient.md`

A user-level ingredient of the same name **wins**, and you say which one you used every time.
That is how someone corrects a shipped ingredient that is wrong for them without editing the
plugin. Honour both environment variables exactly as written — a hardcoded `~/.config` is the
difference between working and not on a machine with an unusual layout.

An ingredient is a directory: `ingredient.md` in the shape below, and an optional `templates/`
beside it whose files are instantiated into the project's `scripts/`.

## Step 0: Route on `$ARGUMENTS`

| Invocation | Do |
|---|---|
| `/orc-package` | **List.** Enumerate both locations. Print each channel name and which location it came from (`shipped` / `user`, and `user (shadows shipped)` when both exist). Stop. |
| `/orc-package <channel>` and an ingredient exists | **Apply**, below. |
| `/orc-package <channel>` and none exists | **Offer capture**, below. Never fail silently and never invent one. |

## Apply

Read the ingredient in full first — `whole-process-first` — before writing anything. Then, in
this order:

### 1. Ask for the ingredient's inputs

The ingredient's opening table names what it needs (an owner, a package name, a key fingerprint,
a series). Ask for each. Ask which `channels.yaml` parent path the leaf belongs under — the
tree is component/platform/os/channel/series (`desktop.python.linux.ppa`), and the user knows
their project's shape better than you do. Never guess a value; an ingredient applied with a
guessed owner writes a wrong action into a real release process.

### 2. Run the ingredient's checks — and only its checks

For registration (section 2) and each credential mechanism (section 3), run **the check the
ingredient supplies**, read-only by construction. Report each as satisfied or not.

**Never perform the setup.** Creating the PPA, registering a key, authorizing OAuth, registering
a store name: each is the user's to do, and each becomes a `**One-time setup:**` block in
`RELEASING.md` so `/orc-release` re-checks it on every release. If a check fails, say exactly
what is missing in the ingredient's own words, and carry on applying — the recipe is correct
before the account work is done, and the release will halt at the right step until it is.

### 3. Write the recipe — merge, never overwrite

Show every write before making it. For each:

- **`channels.yaml` leaf(s)** from section 5, at the parent the user named, placeholders
  substituted. If a leaf with that path already exists, leave it exactly as it is and report
  that it was not touched. Create `.orclab/publish/channels.yaml` if the project has none.
- **`distro.yaml` entries**, only for targets the user names. Same rule: existing entries stay.
- **`RELEASING.md` steps** from section 7, at the position the ingredient describes, **renumbered
  so steps stay contiguous integers** — follow `release-checklist`; a sub-numbered step (`6a`)
  vanishes from `/orc-release`'s parser, which is a recorded incident. Keep the `**One-time
  setup:**` and `**Run:**` markers verbatim; `/orc-release` parses them. If the project has no
  `RELEASING.md`, say so and stop before this write: `release-checklist` sets one up, and this
  command does not stand in for it.
- **Templates** from section 8, into `scripts/`, placeholders substituted, only when the
  ingredient's conditions for them hold. An existing file of the same name is left alone.

After writing `RELEASING.md`, run `/orc-release`'s parser to prove the numbering:
`python3 <orc-release's scripts/run.py> --root . steps` prints the steps and any numbering or
cross-reference warning. A warning means the insertion was wrong; fix it before reporting done.

### 4. Machine-local config — the three rules

Some ingredients need a per-machine file outside the repo. When one does:

- **Merge, never overwrite.** Append a missing section; never rewrite the file.
- **Idempotent, and shown first.** Display the exact content, then write; a second run changes
  nothing.
- **Never a credential.** A directory for one, or a config file that contains none, is fine. The
  moment real secret material is involved, check and prompt. Never write a token, a key, or a
  passphrase, and never print one — `secret-hygiene` applies.

The shipped PPA ingredient has none of these. Its section 4 says so.

### 5. Report

What was written, what was left alone and why, which checks passed, and which
`**One-time setup:**` items remain the user's to do — each named in the ingredient's words.

## Offer capture

There is no ingredient for `<channel>`. Refusing teaches nothing. Instead, offer to walk through
standing the channel up **and write the result as a new ingredient**, so the second project gets
it for free. If the user says yes:

1. Interview for each of the eight sections below, in order. For sections 2 and 3, insist on a
   **checkable test** — an ingredient whose one-time setup cannot be checked is a note nobody
   can act on.
2. Write `${ORCLAB_INGREDIENTS_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/orclab/ingredients}/<channel>/ingredient.md`
   in the shape below. Create the directory. Show the file before writing it.
3. Then apply it, above.

The shape is derived from exactly one channel and is PPA-shaped. If it does not fit the channel
being captured, change the shape rather than contorting the channel to fit — and say that you did,
so the next person knows the shape moved.

## The shape of an ingredient

`ingredient.md` opens with a table of the inputs it asks for, then eight sections with these
headings:

1. `## 1. What the channel is` — and what kind of artifact it takes.
2. `## 2. Registration` — the one-time, account-gated step, **with a checkable test**.
3. `## 3. Credentials` — each mechanism named separately, each **with its own check**.
4. `## 4. Machine-local config` — the exact content to merge, or `None`.
5. `## 5. The publish action` — the `channels.yaml` leaf(s) with real requirements and issues.
6. `## 6. Confirmation` — how anyone finds out the publish landed (`confirm`, per `/orc-publish`).
7. `## 7. RELEASING.md steps` — the steps, and where they belong in dependency order.
8. `## 8. Script template` — what `templates/` holds and when to instantiate it.

Placeholders the command substitutes are written `__LIKE_THIS__` and every one must appear in
the opening table.

## What this never does

- Produce the artifact (`debian/`, a keystore, a manifest). That is `/orc-code`'s territory.
- Run a release. That is `/orc-release`'s.
- Perform an account-gated action, write or print a credential, or overwrite anything.
- Write into `~/projects/<some other project>`: it applies to the project it runs in.
````

- [ ] **Step 2: Check the frontmatter mechanically**

`claude plugin validate` does not read frontmatter (CLAUDE.md records the negative control), so check it directly:

Run: `sed -n '1,/^---$/p' skills/orc-package/SKILL.md | sed '1d;$d' | grep -c '^disable-model-invocation: true$'`
Expected: `1`.

Run: `grep -c 'Bash(\*)\|allowed-tools:.*Bash\b[^(]' skills/orc-package/SKILL.md`
Expected: `0` — no unscoped Bash.

Run: `ls skills/orc*/SKILL.md | grep -c orc-package`
Expected: `1` — `/orc-help`'s glob picks it up.

Run: `claude plugin validate .claude-plugin/plugin.json`
Expected: `✔ Validation passed with warnings`, with only the known `CLAUDE.md` warning.

- [ ] **Step 3: Commit**

```bash
git add skills/orc-package/SKILL.md
git commit -m "v15: /orc-package - list, apply, and capture ingredients

One prose skill. Ingredient resolution honours ORCLAB_INGREDIENTS_DIR and XDG_CONFIG_HOME
with user-level winning over shipped, and says which was used. Apply runs only the
ingredient's checks, never its setup; writes are merge-only and shown first; RELEASING.md
insertion is proved by orc-release's own parser. No ingredient offers capture into the
user-level directory rather than failing.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Verification scenarios, README, and closing #17

**Files:**
- Modify: `VERIFICATION.md` — insert before `## Recording the result`
- Modify: `README.md:43-46` — add a bullet after `/orc-todo`'s
- Modify: `BACKLOG.md` — `#17`'s heading and a layered resolution

**Interfaces:**
- Consumes: the invocations from Task 2, the ingredient's checks and placeholders from Task 1.
- Produces: nothing downstream; this is the close-out.

- [ ] **Step 1: Add the scenarios with `/orc-todo add verification`**

Seven scenarios, one `add` each, body on stdin from a file (shell quoting multi-paragraph prose is how stubs get written). The numbers come back from the allocator; use whatever it prints. Run from the worktree — since #30, a verification scenario lands in the checkout it was written from. Bodies:

**Scenario A — applying the PPA ingredient to a scratch project**

```
In a throwaway scratch git repo with a `debian/control` declaring `Architecture: all`, a
`RELEASING.md` of at least four numbered steps (build, lint, install-test, tag), and no
`.orclab/` at all, run `/orc-package ppa`. Answer its questions with invented values
(owner `nobody`, ppa `scratch`, source `scratchpkg`, series noble → resolute, any 40-hex key).

1. **Expected:** it asks for every input in the ingredient's table before writing anything, and
   asks which `channels.yaml` parent path to use.
2. **Expected:** it runs the registration check (`curl -sfI` against the invented PPA URL) and
   the two credential checks, reports each as not satisfied, and **does not** open a browser,
   run `gpg --gen-key`, or visit Launchpad's activate page.
3. **Expected:** `.orclab/publish/channels.yaml` now holds two leaves under the parent you named,
   with the invented values substituted and no `__PLACEHOLDER__` left; `scripts/ppa-copy-series.py`
   exists with `OWNER = "nobody"`; `RELEASING.md` has two new steps between lint and
   install-test, every step renumbered so the sequence is contiguous integers.
4. Run `python3 <orc-release scripts/run.py> --root . steps`.
5. **Expected:** every step listed, no numbering warning, no cross-reference warning.
6. Run `/orc-publish --dry-run` in the scratch project.
7. **Expected:** both leaves resolve; the plan prints their actions with the invented values.
```

**Scenario B — no machine-local write for the PPA**

```
Run Scenario A with `HOME` pointed at an empty scratch directory (`HOME=/tmp/scratch-home
claude ...`, or export it in the session before invoking).

1. **Expected:** after `/orc-package ppa` completes, `find $HOME -type f` prints nothing. No
   `~/.dput.cf`, no `~/.config/scratchpkg/`, nothing. The PPA ingredient's section 4 says
   "None", and the command must believe it.
```

**Scenario C — never a credential**

```
On a machine with no GPG secret key matching the fingerprint you give, apply the PPA ingredient.

1. **Expected:** the signing-key check fails and is reported in the ingredient's words ("must
   exist in this machine's keyring"), the OAuth check fails and is reported, and at no point does
   the transcript contain a key, a token, or the contents of any file under `~/.config`. Nothing
   is written outside the project.
```

**Scenario D — account-gated refusal**

```
Give `/orc-package ppa` an owner/PPA pair that does not exist on Launchpad.

1. **Expected:** the registration check reports the PPA missing, names the activate-ppa page as
   the user's to visit, and the command continues to write the recipe. It never attempts to
   create the PPA and never asks for Launchpad credentials to do so.
```

**Scenario E — merge, never overwrite**

```
Run Scenario A twice in the same scratch project.

1. **Expected:** the second run reports each leaf, each `distro.yaml` entry, each `RELEASING.md`
   step and `scripts/ppa-copy-series.py` as already present and left alone. `git diff` after the
   second run is empty.
```

**Scenario F — no ingredient offers capture, honouring the override**

```
1. `export ORCLAB_INGREDIENTS_DIR=/tmp/scratch-ingredients` (a directory that does not exist yet),
   then run `/orc-package snap` in any project.
2. **Expected:** it says plainly there is no `snap` ingredient, shipped or user-level, and offers
   to capture one. It does not fail, and does not invent a snap procedure on its own.
3. Say yes, and answer the interview with invented-but-plausible values, giving a real shell
   check for registration (`snap info <name>`) and for credentials (`snapcraft whoami`).
4. **Expected:** `/tmp/scratch-ingredients/snap/ingredient.md` exists, opens with an inputs
   table, and has exactly eight `## N.` sections in the documented order. `~/.config/orclab`
   was not created — the override was honoured.
```

**Scenario G — precedence**

```
1. With `ORCLAB_INGREDIENTS_DIR` set to a scratch directory, copy the shipped
   `ingredients/ppa/` into it and change one visible line in the copy's section 1.
2. Run `/orc-package` (bare).
3. **Expected:** the listing shows `ppa` as `user (shadows shipped)`.
4. Run `/orc-package ppa` and stop after its first response.
5. **Expected:** it says which ingredient it is using and names the user-level path, not the
   plugin's.
```

- [ ] **Step 2: Check the scenarios landed contiguously and parse**

Run: `grep -n '^## Scenario' VERIFICATION.md | tail -8`
Expected: seven new consecutive numbers, all before `## Recording the result`.

- [ ] **Step 3: README bullet**

Insert after the `/orc-todo` bullet (`README.md`, after the line ending `take the same one. Ships as a skill only.`):

```markdown
- **/orc-package** — stand up a distribution channel for this project by applying an
  *ingredient* (the reusable knowledge of how to set up a PPA, a store, a registry) to the
  project's own `channels.yaml`, `distro.yaml` and `RELEASING.md`. Ships the PPA ingredient;
  captures a new one, into your own config directory, for any channel it doesn't ship. Runs
  only an ingredient's checks, never its account-gated setup, and never writes a credential.
  Ships as a skill only.
```

- [ ] **Step 4: Resolve #17**

Change `BACKLOG.md`'s heading `## #17: what belongs in a \`/orc-package\` component, and what belongs elsewhere — scope undecided` to end ` (RESOLVED 2026-09-10)`, and append this paragraph to the entry's end, after its last existing paragraph:

```markdown
**Resolved 2026-09-10 — v15 shipped.** The cleave the entry called "a candidate, explicitly not a
decision" is the one taken: `/orc-package` owns standing up the channel (registration, credentials,
wiring into the recipe) and not producing the artifact, which stays with `/orc-code` and **#4**.
The four things wearing one word are now three places: the artifact is `/orc-code`'s, the channel
is an *ingredient* `/orc-package` applies, the release is `/orc-release`'s. The parked disagreement
about a Launchpad client is settled by the ingredient carrying the copy script as a *template*
instantiated into the project — Orclab ships the knowledge, the project owns the code.

One correction found while planning, recorded in the spec: the PPA has no machine-local config.
`~/.dput.cf` was named as the worked example and was never needed; `dput` resolves `ppa:` through
`/etc/dput.cf`. The shape is still proven for exactly one channel, and the first capture — snap,
per Orcshot #198 — is where it gets tested against a second.
```

- [ ] **Step 5: Commit**

```bash
git add VERIFICATION.md README.md BACKLOG.md
git commit -m "v15 close-out: seven verification scenarios, the README bullet, #17 resolved

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-review against the spec

- **Vocabulary / recipe already exists** → SKILL.md's opening and "Apply §3" write into the existing files. ✔
- **Scope: one shipped ingredient, the shape, capture, user-level storage and precedence** → Tasks 1, 2, 2, 2. ✔
- **Three kinds of work and the safety property** → Apply §3 (recipe), §4 (machine-local, three rules), §2 (checks only, never setup). ✔
- **Shape of an ingredient, eight parts, layout with `templates/`** → Task 1 file layout; SKILL.md "The shape". ✔
- **Capture: location, XDG + override, not the three wrong places, precedence, contributable** → SKILL.md "Where ingredients live" and "Offer capture"; Scenarios F and G. ✔
- **Command surface: three invocations, `disable-model-invocation`, no unscoped Bash** → SKILL.md Step 0 and frontmatter; Task 2 Step 2 checks it. ✔
- **Resolves the Launchpad-client disagreement; keeps `--check`, `--dry-run` anonymous, refusal on unpublished, 0600** → Task 1 template keeps all four; test covers `--check`. ✔
- **Testing section's seven scenarios** → Task 3 A–G, with the machine-local one replaced per the 2026-09-10 correction. ✔
- **Global constraints: no new dependency, `orc-` prefix, no consuming project written, no change to `/orc-publish`/`/orc-release`/`/orc-version`** → Global Constraints above; nothing in any task edits those three skills. ✔
- **Type/name consistency:** the five placeholder names are identical in Task 1's test, template, ingredient, and Task 2's SKILL.md; the eight section headings in Task 1's ingredient match the list in Task 2's "The shape". ✔
