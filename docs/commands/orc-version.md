# /orc-version

## What it's for

You're ready to record a new version of the project you're working in — maybe you've just
finished some changes and want to bump the version, or you just want to know whether what's
happened since the last version looks like a small fix, a new feature, or a breaking change.
`/orc-version` works out the current version first — from the plugin manifest if the project has
one, or otherwise from the most recent version tag in git; if the two disagree, the git tag always
wins, since a hand-edited manifest shouldn't quietly become the source of truth. From there it
figures out (or takes) the next version, drafts the changelog entry for it, updates the files that
record the version number, and makes a local commit and a local tag.

## What you type

| You type | What it does |
|---|---|
| `/orc-version` | Reports the current version. If anything has happened since the last one, proposes a new version and shows the changelog entry it would get, then asks before doing anything. |
| `/orc-version <major>.<minor>` or `/orc-version <major>.<minor>.<point>` | Sets the version to exactly the number you typed (a missing point number is treated as `0`). |
| `/orc-version increment major` | Bumps the first number by one and resets the other two to `0`. |
| `/orc-version increment minor` | Bumps the second number by one and resets the third to `0`. |
| `/orc-version increment point` | Bumps the third number by one and leaves the rest alone. |
| Add `--no-commit` to any of the forms above | Updates the version files but stops before committing or tagging anything. |

`/orc-version release` no longer exists. That job now lives at `/orc-git release`, since it pushes
and publishes a release publicly, and nothing in this command does either.

## What it will ask you

- **Bare `/orc-version`, when there's something to propose:** in one message, it shows you the
  version it suggests, the reasoning behind it (which commits pushed it toward a bigger or smaller
  bump), and the changelog entry that version would get — then asks whether to apply that, edit
  the entry, or pick a different version instead. Saying yes writes everything from that one
  answer; it does not ask a second time.
- **Setting an exact version, or using `increment`:** before writing anything, it shows you the
  changelog entry it drafted from the project's commit history (a changelog is the running,
  dated list of what changed in each version) and asks whether you want to add or change anything
  before it's written.

Nothing else is asked — whether you add `--no-commit` is your own choice, made by how you typed
the command.

## What it changes

- **`CHANGELOG.md`** — created (with a standard header) if it doesn't exist yet, then the new entry
  is added to the top, above everything already there.
- **The project's version files** — whichever of these already exist in the project get their
  version number updated to match: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
  `pyproject.toml`, `debian/changelog`, or a `*.metainfo.xml`/`*.appdata.xml` file at the project's
  root. A project with none of these still gets the changelog entry and the tag, just no version
  file edit — it says so plainly rather than creating a file you don't already use.
- **A commit** — `Bump version to X.Y.Z`, containing the changelog and whichever version files
  exist and were changed. Skipped entirely if you added `--no-commit`.
- **A local tag** — `vX.Y.Z`. Skipped if you added `--no-commit`. Either way, nothing this command
  does is ever pushed anywhere — the tag and the commit stay on your machine until you push them
  yourself or hand the tag to `/orc-git release`.

## What it will never do without asking

- It will never write a changelog entry, or change any version number, without first showing you
  that entry and letting you change it — whether that showing happens as its own question, or as
  part of the single combined question the bare invocation asks.
- It will never treat a bare `/orc-version`'s suggestion as decided on its own — it only proposes a
  version and a changelog entry; nothing gets written unless you say yes, edit the entry, or choose
  a different version.
- It will never commit or tag anything once you've added `--no-commit` — it stops right after
  updating the version files and tells you what it changed.
- It will never push anything, anywhere, under any form of the command — the commit and the tag it
  makes are local only.
- It will never create or publish a public release of the version it just set — that has moved to
  `/orc-git release`, and typing `/orc-version release` does not run that for you; it only tells
  you where the command moved.
- It will never invent a version file for a project that doesn't already use one of the formats it
  knows — it says plainly that there's nothing to update instead of adding a new one.
