# /orc-version

## What it's for

You're ready to record a new version of the project you're working in — maybe you've just
finished some changes and want to bump the version, or you just want to know whether what's
happened since the last version looks like a small fix, a new feature, or a breaking change.
`/orc-version` works out the current version first — from the small file a Claude Code plugin
carries that names it and its version (`.claude-plugin/plugin.json`), if the project has one (most
projects don't), or otherwise from the most recent version tag in git; if the two disagree, the
git tag always wins, since a hand-edited manifest shouldn't quietly become the source of truth.
It fetches the tags before looking, and if your copy of the project still has none it checks
whether any exist where the project is hosted — because a copy that simply never downloaded the
tags looks exactly like a project that was never tagged, and they need opposite answers. If tags
exist somewhere but not here, it tells you the newest one by name instead of calling the project
untagged.
A version number has three parts — major.minor.point (point is also sometimes called "patch") —
where a major change means something that used to work no longer does, minor means something was
added, and point means only fixes or cleanup. From the current version, `/orc-version` works out
(or takes) the next one, drafts the changelog entry for it (the running, dated list of what
changed in each version), updates the files that record the version number, and makes a local
commit and a local tag.

## What you type

| You type | What it does |
|---|---|
| `/orc-version` | Reports the current version. If anything has happened since the last one, proposes a new version and shows the changelog entry it would get, then asks before doing anything. If the project has no version yet, it just lists the forms below instead of proposing anything. |
| `/orc-version <major>.<minor>` or `/orc-version <major>.<minor>.<point>` | Sets the version to exactly the number you typed (a missing point number is treated as `0`). |
| `/orc-version increment major` | Bumps the first number by one and resets the other two to `0`. |
| `/orc-version increment minor` | Bumps the second number by one and resets the third to `0`. |
| `/orc-version increment point` | Bumps the third number by one and leaves the rest alone. If there's no version yet, `increment` starts counting up from `0.0.0`. |

Add `--no-commit` after the version number or the `increment` word — for example
`/orc-version 1.2.0 --no-commit` or `/orc-version increment minor --no-commit` — to update the
version files without committing or tagging anything. It only applies to these two forms, not the
bare `/orc-version` on its own.

`/orc-version release` no longer exists. That job now lives at [`/orc-git release`](orc-git.md),
since it pushes and publishes a release publicly, and nothing in this command does either.

## What it will ask you

- **Bare `/orc-version`, when there's something to propose:** in one message, it shows you the
  version it suggests, the reasoning behind it (which commits pushed it toward a bigger or smaller
  bump), and the changelog entry that version would get — then asks whether to apply that, edit
  the entry, or pick a different version instead. Saying yes writes everything from that one
  answer; it does not ask a second time.
- **Setting an exact version, or using `increment`:** before writing anything, it shows you the
  changelog entry it drafted from the project's commit history and asks whether you want to add or
  change anything before it's written.

Nothing else is asked — whether you add `--no-commit` is your own choice, made by how you typed
the command.

## What it changes

- **`CHANGELOG.md`** — created (with a standard header) if it doesn't exist yet, then the new entry
  is added to the top, above everything already there.
- **The project's version files** — it looks for whichever of these already exist in the project
  and updates only those; you don't choose which ones: `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, `pyproject.toml`, `pubspec.yaml`, `debian/changelog`, or a
  `*.metainfo.xml`/`*.appdata.xml` file at the project's root. A project with none of these still
  gets the changelog entry and the tag, just no version file edit — it says so plainly rather than
  creating a file you don't already use.
- **A Flutter project's build number, bumped for you.** `pubspec.yaml` holds two numbers on one
  line — `version: 1.0.0+6`. The left half is the version you asked for; the `+6` is the build
  number, and the App Store and Google Play both refuse an upload carrying one they have already
  seen. So this command always increases it, even when the version itself doesn't change: a build
  that came back rejected is re-uploaded under the same version and still needs a number the store
  has never seen. Nothing else in the file is touched — comments, dependencies and a pinned
  package's own `version:` all stay exactly as they were.
- **A commit** — `Bump version to X.Y.Z`, containing the changelog and whichever version files
  exist and were changed. Skipped entirely if you added `--no-commit`.
- **A local tag** — `vX.Y.Z`. Skipped if you added `--no-commit`. Either way, nothing this command
  does is ever pushed anywhere — the tag and the commit stay on your machine until you push them
  yourself or hand the tag to [`/orc-git release`](orc-git.md) — the separate command that pushes
  the tag and makes the public release.

## What it will never do without asking

- It will never write a changelog entry, or change any version number, without first showing you
  that entry and letting you change it — whether that showing happens as its own question, or as
  part of the single combined question the bare invocation asks.
- It will never treat a bare `/orc-version`'s suggestion as decided on its own — it only proposes a
  version and a changelog entry; nothing gets written unless you say yes, edit the entry, or choose
  a different version.
- It will never commit or tag anything once you've added `--no-commit` to the version-setting
  forms — it stops right after updating the version files and tells you what it changed.
- It will never push anything, anywhere, under any form of the command — the commit and the tag it
  makes are local only.
- It will never create or publish a public release of the version it just set — that has moved to
  [`/orc-git release`](orc-git.md), and typing `/orc-version release` does not run that for you; it
  only tells you where the command moved.
- It will never invent a version file for a project that doesn't already use one of the formats it
  knows — it says plainly that there's nothing to update instead of adding a new one.
