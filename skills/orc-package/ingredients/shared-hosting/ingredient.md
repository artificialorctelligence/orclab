# Ingredient: shared hosting (DreamHost the confirmed-live example)

Written from orcweather's API, deployed to DreamHost shared hosting on 2026-09-20 — the only
shared-hosting deployment anyone here has actually done. Every line marked "2026-09-20" was run
that day; the project's own record is `server/RELEASING.md` in the orcweather repository, and
Orclab's BACKLOG #64 is the entry this closed. Where the host is not DreamHost, the *shape*
holds (an SSH account, a per-domain document root, no Composer on the box) and the panel paths do
not — the first project on another host corrects them here.

**What this channel is not.** Not a PHP thing: a static `web/dist` from `stack-web` lands on the
same host by the same rsync, with no `vendor/` step. Not a store: nothing is reviewed, nothing is
listed, and the publish is a file copy that is live the moment it finishes.

`/orc-package` asks for these before applying, and uses them everywhere below:

| Ask for | Example (orcweather) | Used as |
|---|---|---|
| The domain the host serves | `api.orcweather.orcshot.org` | `__DOMAIN__` |
| SSH alias for the hosting account (from `~/.ssh/config`) | `orcweather-api` | `__SSH__` |
| Project directory on the host | `~/__DOMAIN__` (DreamHost's convention) | `__REMOTE__` |
| Directory the web server may serve, relative to the project | `public` | `__WEBROOT__` |
| What is uploaded — the directories and files, space-separated | `public src vendor composer.json composer.lock` | `__UPLOAD__` |
| Runtime state the host owns and a deploy must not delete | `var/` | `__STATE__` |
| Container engine, if the project has a `compose.yaml` | `podman` | `__ENGINE__` |
| `channels.yaml` path for the leaf | `server.php.linux` | the leaf's parent (the leaf is `dreamhost`) |

## 1. What the channel is

A shared web host: an account with SSH, Apache serving PHP for one or more domains, a control
panel for the per-domain settings, `rsync` and `cron` on the box — and nothing else. No
Composer, no daemon you can start, no CI, no root. What ships is ordinary files; the host's own
PHP runs them.

Built on: any machine with `rsync` and an SSH key the account accepts. `vendor/` is built where
Composer is — the dev container, or a machine with Composer — never on the host.

Takes: a project whose only web-reachable directory is `__WEBROOT__` (`stack-php`'s Layout:
`public/` with `index.php` and `.htaccess`; everything else beside it). Producing that is
`/orc-code`'s territory; this ingredient assumes it and checks that `__WEBROOT__/index.php`
exists.

**Confirmed live 2026-09-20 (DreamHost):** PHP 8.5.5 on the host (the container had 8.5.10 —
same branch, `vendor/` built on the newer ran on the older), extensions `curl json mbstring
openssl pdo_sqlite sqlite3 zlib`; `rsync` present; system Python 3.12 present with `pip install
--user` refused (PEP 668) — a venv works; HTTPS already on and `http://` already 301s.

## 2. Registration — one-time, account-gated, never performed by Orclab

The hosting account, the domain, and the domain's DNS all exist before this ingredient is
applied. Orclab never creates any of them — they are billed, and they are the user's.

**Check:** `ssh __SSH__ true` exits 0, and `curl -sfI https://__DOMAIN__/ >/dev/null` gets a
response (any status — the domain resolves and the host answers TLS).

**If missing:** the user adds the domain in the panel (DreamHost: *Manage Websites → Add
Website*) and the SSH alias to `~/.ssh/config`. Say that; the recipe is written regardless, and
the release halts at this step until they have.

## 3. Credentials — one mechanism

**SSH key**, already accepted by the account — it is what `rsync` and every `ssh __SSH__` line
below authenticate with. Nothing is stored by Orclab, nothing is a token.

- **Check:** `ssh -o BatchMode=yes __SSH__ true` — exit 0 means the key is loaded and accepted;
  BatchMode makes a password prompt fail instead of hang.
- **If missing:** the user adds their public key to the account (DreamHost: the panel's *Manage
  Users → Edit → SSH keys*, or `ssh-copy-id`). Orclab never generates or copies a key on the
  user's behalf.

**The project's own secrets** are not this ingredient's credentials, but the deploy has to know
where they live: a `.env` created **on the host by hand**, beside `composer.json` in
`__REMOTE__`, above `__WEBROOT__` where no URL reaches it, git-ignored locally and **never in
`__UPLOAD__`**. `secret-hygiene` governs its contents. (orcweather, 2026-09-20: no secret existed
yet, so none was written — its place is recorded so the first one goes there.)

## 4. Machine-local config

**`~/.ssh/config`** holds the `__SSH__` alias (host, user, key). That is the whole of it; there
is no config file for the host itself and no CLI to log in to.

## 5. Per-app setup — once per domain, before the first upload

Three panel settings, all *Performed by hand*, all per domain. The order matters: **the document
root is set before anything is uploaded**, so `src/`, `vendor/` and `composer.json` are never
web-visible even for a minute.

1. **PHP version.** DreamHost: *Manage Websites → __DOMAIN__ → Manage → Settings → Website
   Settings → PHP → Manage* → choose the version the project was built for (8.5 on 2026-09-20).
   The box's CLI default (8.2 there) is not what Apache runs; only the domain's setting is.
   - **Check:** `ssh __SSH__ '/usr/local/php85/bin/php -v'` prints the expected major.minor
     (DreamHost's per-version binaries live under `/usr/local/phpNN/bin/`); the panel is the
     authority for the web side, and a `GET /` after the first deploy is the proof.
2. **Document root.** DreamHost: *… → Website Settings → Directories → Modify → Web directory*
   → `__DOMAIN__/__WEBROOT__`. Allow a few minutes to apply. The panel creates the directory
   itself (with empty favicons) when the field changes — expected, harmless, overwritten by the
   first upload. Slim's documented `.htaccess`-in-the-web-root recipe is for a host without this
   field; on one that has it, the rewrite lives in `__WEBROOT__/.htaccess` only.
   - **Check (before any upload):** the panel field reads `__DOMAIN__/__WEBROOT__` (the user
     confirms; Orclab cannot read the panel). **Check (after):** `curl -s -o /dev/null -w
     '%{http_code}' https://__DOMAIN__/composer.json` is `404`.
3. **Errors.** PHP must have `display_errors = Off`, `log_errors = On` for the web SAPI. DreamHost's
   PHP 8.5 default already is (2026-09-20: a 404 and a 500 both rendered the framework's generic
   page), so nothing was written. If a host's default differs, the override is a `phprc` file —
   DreamHost: `~/.php/8.5/phprc` with those two lines (its php.ini page: *"A php.ini (phprc)
   file lets you override DreamHost's default PHP settings"*).
   - **Check:** `curl -si https://__DOMAIN__/no-such-path | head -1` is a `404` with a generic
     body — no file path, no trace.

HTTPS was already on for the domain with `http://` redirecting (DreamHost does this by default);
`__WEBROOT__/.htaccess` adds HSTS. Nothing to set up.

## 6. The publish action

The `channels.yaml` leaf at `<parent>`. Three commands: build the deploy `vendor/`, upload,
restore the dev tools. The build is `prepare:`, not folded into `action:` — the same split the
PPA ingredient explains — so the upload is one reversible-by-re-running command on its own.

The deploy `vendor/` is built without dev packages (7.9 MB, 12 packages on 2026-09-20 — the
dev set is several times that and includes the mutation tester); `--optimize-autoloader` is
Composer's documented production flag. Then the same `composer install` without `--no-dev`
puts the dev tools back, or `vendor/bin/phpunit` is gone until the next `/orc-test`.

`--delete` keeps the host an exact copy of what was uploaded; `--exclude '__STATE__'` is what
stops it deleting the host's own cache, counters and data files, which are never in the repo.
The whole first upload took **1.6 s** (2026-09-20).

For a project *with* a container (`compose.yaml` with an `orclab` service — `stack-php`'s
default), the Composer lines are prefixed with `__ENGINE__ compose run --rm -T --workdir "$PWD"
orclab`; for one without, they run bare. `rsync` always runs on this machine.

```yaml
dreamhost:
  # Build the production vendor/ where Composer is (the dev container); the host has none.
  prepare: "__ENGINE__ compose run --rm -T --workdir \"$PWD\" orclab composer install --no-dev --optimize-autoloader --no-interaction"
  # Upload exactly the listed paths; --delete mirrors removals, --exclude keeps the host's own state.
  action: "rsync -az --delete --exclude '__STATE__' __UPLOAD__ __SSH__:__REMOTE__/ && __ENGINE__ compose run --rm -T --workdir \"$PWD\" orclab composer install --no-interaction"
  confirm:
    command: "curl -sf https://__DOMAIN__/ && curl -s -o /dev/null -w '%{http_code}' https://__DOMAIN__/composer.json | grep -qx 404"
  requirements:
    - "Section 5's document root must read __DOMAIN__/__WEBROOT__ in the panel BEFORE the first
       run of this leaf. Uploading first and pointing the root second leaves src/ and vendor/
       reachable by URL until the panel change applies."
    - ".env is never in __UPLOAD__ and never in the repository. It is created on the host by
       hand, in __REMOTE__ beside composer.json, the day the first secret exists."
  issues:
    - "The second composer install in action: is what restores vendor/bin/phpunit and the rest
       of the dev tools locally. If the action is interrupted between rsync and that install,
       run it by hand; nothing on the host is affected."
    - "There is no preflight: — the no-vcs / no-tool-state rules inspect an archive, and this
       channel uploads a tree. The equivalent guard is __UPLOAD__ itself: it names directories
       explicitly, so .git, .orclab and tests/ are never sent because they are never listed."
```

`distro.yaml`: none. Nothing installs from this channel; a phone app or a browser calls
`https://__DOMAIN__/` directly.

**A cron job on the same host** is a second thing this channel ships, when the project has one
(orcweather's poller). It is installed once, by hand, not by the leaf — `## 8` has the step.
Two facts from 2026-09-20 that cost time: DreamHost's cron fires **about 40 s past the minute**,
not on it, so "within the last minute" checks need slack; and the crontab is edited either
with `crontab` over SSH **or** from the panel's Cron Jobs page, **never both** — a panel edit
overwrites the file (DreamHost's own warning).

## 7. Confirmation

Synchronous in effect — the files are live the moment `rsync` returns — but the leaf declares
`confirm.command` anyway, because the thing worth knowing is not "did rsync exit 0" but "is the
new build answering, and is nothing above `__WEBROOT__` reachable". The command above checks
both: `GET /` answers (the project's `/` route returns its name and `composer.json` version, which
is how a deploy is told apart from the one before it), and `/composer.json` is `404`. A project
adds its own routes to that line as they exist.

## 8. `RELEASING.md` steps

Inserted **after the test gate and the version bump**, **before** any commit/tag step that
records the release as done. The panel steps are one-time and sit first; the upload is every
release. Renumber everything after the insertion point so the document's steps stay contiguous.

```markdown
## N. Select the PHP version for __DOMAIN__ in the panel

**Performed by hand.** **One-time setup:** per domain. Already in place when the panel shows
the project's PHP version for the domain and `ssh __SSH__ '/usr/local/php85/bin/php -v'`
agrees (the box's CLI default is a different version; the domain's setting is what Apache
runs).

DreamHost: *Manage Websites → __DOMAIN__ → Manage → Settings → Website Settings → PHP →
Manage*.

## N+1. Point the domain's web directory at __WEBROOT__

**Performed by hand.** **One-time setup:** per domain. Already in place when the panel's
*Directories* field reads `__DOMAIN__/__WEBROOT__`.

Only `__WEBROOT__` may be reachable by URL; `src/`, `vendor/`, `composer.json` and `.env` sit
beside it in `__REMOTE__`. **Do this before the first upload, never after.**

DreamHost: *Manage Websites → __DOMAIN__ → Manage → Settings → Website Settings → Directories →
Modify → Web directory* → `__DOMAIN__/__WEBROOT__`. Allow a few minutes to apply.

## N+2. Build the deploy vendor/ and upload

**Preconditions:** N+1 is applied — once anything has been deployed,
`curl -s -o /dev/null -w '%{http_code}' https://__DOMAIN__/composer.json` is `404`.
Composer is not on the host and does not need to be: `vendor/` is built here without dev
packages and uploaded.

**Run:** /orc-publish <parent>.dreamhost

`--exclude '__STATE__'` keeps the host's own cache and data across deploys. `.env` is never
uploaded; it is created on the host by hand, in `__REMOTE__` beside `composer.json`, the day
the first secret exists.

## N+3. Smoke-check from outside

```bash
curl -si https://__DOMAIN__/ | grep -E '^HTTP|^strict|^\{'
curl -s -o /dev/null -w '%{http_code}\n' https://__DOMAIN__/composer.json
```

Done means: `HTTP/2 200`, the `strict-transport-security` header, the version you bumped in
the body, and **404** for the second line.
```

If the project has a cron job on the host, one more step after N+3 — one-time, by hand, over
SSH — whose text is the project's own (which script, which venv, which schedule). The two
DreamHost facts to carry into it: fires ~40 s past the minute; `crontab` over SSH or the panel,
never both. orcweather's `server/RELEASING.md` step 7 is the worked example, with a
`## Tearing it down` section that undoes every step above in reverse.

## 9. Script template

**None.** Every command in this ingredient is a one-liner already on the machine (`rsync`,
`ssh`, `curl`, the project's own Composer), and `RELEASING.md` carries them verbatim. A
`templates/` directory appears here the day a host needs more than that.

## Sources (live on 2026-09-20)

- `help.dreamhost.com/hc/en-us/articles/360041534491` — changing a domain's web directory
  (the *Directories → Modify → Web directory* field).
- `help.dreamhost.com/hc/en-us/articles/214200688-php-ini-overview` — *"A php.ini (phprc) file
  lets you override DreamHost's default PHP settings"*; `~/.php/<version>/phprc`.
- `help.dreamhost.com/hc/en-us/articles/115003505112-Force-your-site-to-redirect-to-HTTPS-SSL`
  — *"DreamHost automatically redirects … from HTTP to HTTPS"*.
- DreamHost's cron article — panel edits overwrite the crontab file (the "don't mix" warning).
- `www.slimframework.com/docs/v4/deployment/deployment.html` — "Deploying to a shared server":
  the `.htaccess`-in-the-web-root recipe this host does not need.
- The run itself: orcweather `server/RELEASING.md` and `docs/orclab-php-findings.md`,
  2026-09-20 — every timing, size and version above.
