# Ingredient: Flathub

Written 2026-09-11 from Orcshot's channel, before its first submission. The process below is from
Flathub's own documentation as read that day (submission and maintenance pages), the confirmation
API was exercised live (it 404s for an unsubmitted app, which is what makes it a usable check), and
the sandbox behaviour that shaped Orcshot's manifest was tested on a real GNOME 50 VM. Nothing here
has been through a Flathub review yet; where the ingredient says "verify at first submission", it
means exactly that, and the next project to apply it should correct it.

`/orc-package` asks for these before applying, and uses them everywhere below:

| Ask for | Example (Orcshot) | Used as |
|---|---|---|
| Application id (reverse-DNS) | `org.orcshot.Orcshot` | `__APP_ID__` |
| Manifest filename in the project | `org.orcshot.Orcshot.yaml` | `__MANIFEST__` |
| GitHub username that will own the submission | `artificialorctelligence` | `__GH_USER__` |
| Upstream repo the manifest builds from | `github.com/artificialorctelligence/orcshot` | `__UPSTREAM__` |
| `channels.yaml` path for the leaf | `desktop.python.linux.flatpak` | the leaf's parent |

## 1. What the channel is

The de-facto Flatpak app store. Flathub builds the app itself from a manifest kept in a repository
it owns (`github.com/flathub/__APP_ID__`); users install from the Software app on any distro with
Flathub enabled — Fedora, Linux Mint and most others ship it enabled; Ubuntu does not, and its
users add it by hand. That makes Flathub the channel for everything that is not Ubuntu-with-snaps.

Built on: nothing in particular — Flathub builds the app itself. The local lint and test build
need `flatpak` and `org.flatpak.Builder` on any Linux; the publish action needs only `git` and `gh`.

Takes: a manifest (`__MANIFEST__`), a metainfo file, a desktop file and an icon, all in the
project. Producing them is `/orc-code`'s territory; this ingredient checks the manifest exists and
that `flatpak-builder-lint` passes on both the manifest and the metainfo:

```bash
flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest __MANIFEST__
flatpak run --command=flatpak-builder-lint org.flatpak.Builder appstream <metainfo file>
```

**Permissions are the review.** Flathub's rule: "static permissions must be kept to an absolute
minimum; where a portal exists, using it is mandatory." Two findings from Orcshot worth carrying:

- A sandboxed app may **own** its own app-id bus name (`__APP_ID__`) with no `--own-name` line —
  Flatpak grants that automatically — and unconfined desktop components (GNOME Shell extensions,
  Cinnamon applets) can call methods on it and receive its `org.gtk.Actions.Changed` signals
  through the proxy. Tested live on a real Flatpak with its real permissions. So an app that needs
  a privileged desktop-side helper can have the helper call *in* rather than the app reaching
  *out*, and needs no extra grant for it.
- To get a GNOME Shell extension installed, do not grant `--filesystem=~/.local/share/gnome-shell/extensions`.
  Call `org.gnome.Shell.Extensions.InstallRemoteExtension(uuid)` and GNOME installs it from
  extensions.gnome.org with its own confirmation dialog — Extension Manager's Flathub manifest does
  exactly this with `--talk-name=org.gnome.Shell.Extensions` and no filesystem grant.

## 2. Registration — one-time, account-gated, never performed by Orclab

A GitHub account for `__GH_USER__` with **two-factor authentication enabled** — Flathub's write
invitation (section 5) cannot be accepted without it. Nothing else: there is no Flathub account.

**Check:** `gh auth status` exits 0 as `__GH_USER__`;
`gh api user --jq .two_factor_authentication` prints `true`.

**If missing:** `gh auth login` (interactive; the user's) and GitHub's security settings for 2FA.

## 3. Credentials

**GitHub account with write access to `flathub/__APP_ID__`.** That is the only credential; there
is no Flathub login.

- **Check:** `gh auth status` exits 0 as `__GH_USER__`, and
  `gh api repos/flathub/__APP_ID__/collaborators/__GH_USER__/permission --jq .permission` prints
  `write` or `admin`.
- **If missing:** the user logs in with `gh auth login` (interactive; never done by Orclab) and
  accepts the pending invitation on GitHub. Nothing is stored by this ingredient.

## 4. Machine-local config

**None.** A checkout of `flathub/__APP_ID__` is a working directory the action creates and may
delete, not config. `flatpak` and `org.flatpak.Builder` must be installed for the local lint and
test build (`flatpak install flathub org.flatpak.Builder`), which is tooling, not project state.

## 5. Per-app setup — once per app, before its first release

The first submission is a pull request, and it takes days: "reviewers are volunteers", "merges are
done in batches".

1. Fork `github.com/flathub/flathub` (uncheck "copy the master branch only"); clone with
   `--branch=new-pr`; branch from `new-pr`.
2. Add `__MANIFEST__` (and `flathub.json` if the app needs to restrict architectures) — the
   manifest must build from a **tag or commit** of `__UPSTREAM__`, never a branch.
3. Open the PR **against `new-pr`, not `master`**, titled `Add __APP_ID__`. Comment `bot, build` to
   get a test build; reviewers may ask for changes.
4. On merge, Flathub creates `github.com/flathub/__APP_ID__` and sends `__GH_USER__` a write-access
   invitation — accept within one week; **2FA must be enabled on the GitHub account** or the
   invitation cannot be accepted.

**Check:** `curl -sf https://flathub.org/api/v2/appstream/__APP_ID__ >/dev/null` — 200 once
published, 404 before (confirmed live for Orcshot on 2026-09-11: 404). Also
`gh repo view flathub/__APP_ID__` exists after the merge, before the first build has published.

**If missing:** say so, quote steps 1–4, write the recipe anyway. The per-release leaf in section 6
is meaningless until this is done and its `requirements:` say so.

## 6. The publish action

Flathub publishes by **merging a PR in the app's own repo**; the only inputs are the new upstream
tag and its commit. The leaf opens that PR. Merging is a separate, deliberate step in
`RELEASING.md` (section 8) because the test build must be looked at first.

```yaml
flatpak:
  # The tag must already exist on __UPSTREAM__ - this leaf runs after the release commit is
  # tagged and pushed, never before. It updates the manifest's source to the new tag+commit in a
  # fresh checkout of the Flathub repo and opens the PR; Flathub's bot then builds it.
  prepare: "git -C \"${TMPDIR:-/tmp}\" clone -q https://github.com/flathub/__APP_ID__ flathub-__APP_ID__ 2>/dev/null || git -C \"${TMPDIR:-/tmp}/flathub-__APP_ID__\" pull -q"
  action: >-
    V=$(git describe --tags --abbrev=0) && C=$(git rev-list -n1 "$V") &&
    cd "${TMPDIR:-/tmp}/flathub-__APP_ID__" && git checkout -q -B "update-$V" origin/master &&
    sed -i -E "s/^(\\s*tag:).*/\\1 $V/; s/^(\\s*commit:).*/\\1 $C/" __MANIFEST__ &&
    git commit -qam "Update to $V" && git push -q -u origin "update-$V" &&
    gh pr create --fill --base master --head "update-$V"
  confirm:
    url: "https://github.com/flathub/__APP_ID__/pulls"
  metrics: "curl -fsS https://flathub.org/api/v2/stats/__APP_ID__ | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d[\"id\"], \"-\", d[\"installs_total\"], \"installs total,\", d[\"installs_last_month\"], \"last month,\", d[\"installs_last_7_days\"], \"last 7 days\")'"
  requirements:
    - "Section 5 must be complete: `gh repo view flathub/__APP_ID__` succeeds and
       `gh api repos/flathub/__APP_ID__/collaborators/__GH_USER__/permission` says write."
    - "The manifest in flathub/__APP_ID__ must reference the upstream by `tag:` and `commit:`
       lines the sed above can find. If the first submission used a different shape (a
       `url:`+`sha256:` tarball, say), rewrite the sed to match it, once, and record it here."
    - "The release tag must already be pushed to __UPSTREAM__ - run this after the commit/tag/
       push step, never before."
  issues:
    - "Merging the PR is what publishes, and it is deliberately NOT in this action: the bot's
       test build comment must be read first. Publication follows the merge 'usually within 1-2
       hours unless it is held in moderation' - and any permission change or critical AppStream
       change holds the build for a human moderator. Dropping a permission counts as a change."
    - "flatpak-external-data-checker runs across Flathub every two hours and may open this same
       PR by itself if the manifest declares `x-checker-data`. Then the action's PR is a
       duplicate; close one."
```

`distro.yaml` entries: one per distro/session target the user names that installs from Flathub,
`channel: <parent>`. Ask; do not invent them.

## 7. Confirmation

`https://flathub.org/api/v2/appstream/__APP_ID__` — the JSON's release list carries the new
version once the merged build has published. `confirm.url` above points at the PR list because at
the moment the action finishes, "PR open, test build pending" is the honest status.

Metrics: the leaf's `metrics:` reads `https://flathub.org/api/v2/stats/__APP_ID__` and prints the
three totals. The field names (`installs_total`, `installs_last_month`, `installs_last_7_days`)
were confirmed live on 2026-09-10 against `org.gimp.GIMP` (`/orc-publish`'s table, BACKLOG #7); the
endpoint 404s for an unpublished id, which fails the leaf honestly. Fetches, not people — the
schema does not say whether updates are counted.

## 8. `RELEASING.md` steps

One step, inserted **after the commit/tag/push step** (the tag must exist) and **before** the
forge-release step, so the release announcement can point at a Flathub build that exists.

```markdown
## N. Update Flathub

**One-time setup:** the first Flathub submission, reviewed by volunteers over days:
fork `flathub/flathub`, branch from `new-pr`, add `__MANIFEST__`, open the PR against `new-pr`
titled `Add __APP_ID__`, comment `bot, build`, answer the reviewers. After the merge, accept the
write-access invitation to `flathub/__APP_ID__` within a week (2FA required on the account).
Check: `curl -sf https://flathub.org/api/v2/appstream/__APP_ID__ >/dev/null`.

**Preconditions:** the release tag is pushed to __UPSTREAM__; `gh auth status` is you.

**Run:** /orc-publish <parent>

Then, by hand: wait for the bot's test-build comment on the PR, install the test build it links
(`flatpak install --user <the link>`) on a real machine, run the app, and only then merge the PR.
Publication follows within 1-2 hours unless a permission or AppStream change held it for a
moderator. Confirm: the appstream API above lists the new version.
```

Renumber everything after the insertion point so the document's steps stay contiguous integers.

## 9. Script template

**None.** The action is `git` + `sed` + `gh`. If a project's manifest shape makes the `sed`
unreadable, write the project a `scripts/flathub-update.sh` and reference it from the leaf; that
script is the project's, not this ingredient's.

## Sources (live on 2026-09-11)

- New-app submission (`new-pr` branch, `bot, build`, write invitation, 2FA, one week):
  `https://docs.flathub.org/docs/for-app-authors/submission`
- Updates (protected branches, PR test build, publish in 1-2 h, moderation on permission change,
  external-data-checker every two hours): `https://docs.flathub.org/docs/for-app-authors/maintenance`
- Requirements ("static permissions kept to an absolute minimum; portals mandatory where they
  exist"): `https://docs.flathub.org/docs/for-app-authors/requirements`
- Appstream API used as the check: `https://flathub.org/api/v2/appstream/__APP_ID__` (404 for
  Orcshot on 2026-09-11, i.e. the check distinguishes unsubmitted from published)
- Extension Manager's manifest — `--talk-name=org.gnome.Shell.Extensions`, no filesystem grant:
  `https://github.com/flathub/com.mattjakeman.ExtensionManager`
- Sandbox D-Bus behaviour (own app-id name; unconfined callers in, `org.gtk.Actions.Changed`
  out): tested on Orcshot's CI-built 0.3.0 Flatpak on an Ubuntu 26.04 / GNOME 50.1 VM, 2026-09-11.
