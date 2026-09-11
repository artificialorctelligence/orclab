# Orclab v15: `/orc-package` — ingredients and recipes

## Goal

Give Orclab a way to stand up a distribution channel for a project, so the work done once for
Orcshot's PPA does not have to be redone from scratch for the next project or the next channel.

Closes **BACKLOG #17**.

## Vocabulary — the decomposition this design rests on

direflail's framing, and it is load-bearing rather than decorative, because an earlier pass of this
design used one word for two things and the storage question became unanswerable as a result:

| Term | What it is | Where it lives |
|---|---|---|
| **Ingredient** | A reusable unit of knowledge — how to stand up a PPA channel, how to set up a language stack | **Core**: shipped in Orclab's repo. Or **user-level**, if captured for a channel Orclab does not ship yet. |
| **Recipe** | One project's actual assembly of ingredients | That project's own repo |

**A project's recipe already exists.** `channels.yaml`, `distro.yaml` and `RELEASING.md` *are*
Orcshot's recipe. `/orc-package` does not invent a new artifact type for projects — it applies an
ingredient by writing into the recipe that is already there.

**Orclab is itself a project with a recipe**, drawing on the same core ingredients as anyone else.
That framing immediately predicts something true and previously noticed only in isolation: Orclab
has **no `RELEASING.md`, 9 tags and 0 GitHub Releases** despite shipping `/orc-release`. It has not
written its own recipe. Not this spec's job to fix, but it is the same gap seen from a new angle.

## Scope

**In scope:**
- A new skill, `skills/orc-package/SKILL.md`, invoked as `/orc-package <channel>`.
- One shipped ingredient: **PPA**, written from the 2026-09-07 work, which is the only channel
  anyone here has actually stood up.
- The documented shape an ingredient must have.
- Capture: an interview that writes a new ingredient for a channel Orclab does not ship.
- User-level ingredient storage, and its precedence against shipped ingredients.

**Explicitly out of scope:**
- **Producing the artifact.** `debian/` layout, an Android keystore, an `.msix` manifest — these
  share essentially nothing with each other, unlike channel setup which repeats. That is
  `/orc-code`'s territory and **#4**'s entry.
- **Running the release.** `/orc-release` already owns that and is unchanged here.
- **Performing account-gated actions.** See "What it will not do."
- **A shared ingredient mechanism with `/orc-code`.** The vocabulary carries across (#4 records
  it); the machinery deliberately does not. A channel ingredient and a language ingredient may
  share nothing past the metaphor, and generalising on two examples — one unbuilt — is the
  speculative work this repo keeps deleting.
- **Ingredients for snap, Flathub, npm, App Store, Play, winget.** Nobody here has published to
  them. Writing recipes for stores we have not used would be inventing. Capture is how they arrive.

## What it does

`/orc-package <channel>` applies an ingredient to the current project's recipe. Three kinds of
work, and the boundary between them is the safety property:

### 1. Writes into the project's recipe

- The `channels.yaml` leaf, with its action, requirements, issues, and — where the ingredient says
  so — the `timeout`, `confirm` (v13) and `preflight` (v12) fields.
- The `distro.yaml` entries, where the channel serves specific targets.
- The `RELEASING.md` steps, **in correct integer dependency order**, with the right markers.
  Renumbering when inserting mid-document, per `release-checklist` — sub-numbered steps make steps
  vanish from the parsed release, which is a real incident, not a style rule.
- Any script the ingredient carries as a template, dropped into the project's `scripts/`.

### 2. Writes machine-local config, under three hard rules

Some setup is genuinely per-machine and belongs nowhere in a repo. `/orc-package` may write these,
bounded by:

- **Merge, never overwrite.** A per-user config file may already carry entries for other projects.
  Appending a missing section is allowed; rewriting the file is not.
- **Idempotent, and shown before writing.** A second run changes nothing, and the exact content is
  displayed before it is written.
- **Never a credential.** Orclab may create a *directory* for one, or a config file that contains
  none. The moment real secret material is involved, it checks and prompts. It never writes a
  token, a key, or a passphrase.

**Corrected 2026-09-10, before the plan was written: the shipped PPA ingredient has no
machine-local config, so these rules ship unexercised.** An earlier draft named `~/.dput.cf` as the
worked example. Checked against the machine the 2026-09-07 work ran on: the file does not exist
there, and Orcshot's own `RELEASING.md` says why — *"`dput` understands the `ppa:` shorthand
directly without needing the `[orcshot-ppa]` section at all"*; `/etc/dput.cf` ships a stock
`[ppa]` stanza. The PPA's only per-machine state is the Launchpad OAuth token, which is a
credential and falls under rule 3, not this one. The rules stay because a captured ingredient may
genuinely need them (a store CLI's config file, say); the PPA ingredient's own "machine-local
config" section says **none**, and nothing in the shipped work pretends otherwise.

### 3. Checks, and prompts, for everything account-gated

Creating the PPA on Launchpad, registering a store name, a GPG key, an OAuth authorization — these
are never performed. Each becomes a `**One-time setup:**` block in the project's `RELEASING.md`,
with the check the ingredient supplies, and `/orc-package` reports which are already satisfied.

This is not caution for its own sake; it is the rule v0.11.0 already shipped: **standing up a
distribution channel is always something the user asks for directly.**

## The shape of an ingredient

An ingredient is **prose in a markdown file**, like every other thing Orclab ships. No schema, no
registry, no code. `/orc-package` reads it and follows it, exactly as Claude reads any skill.

Derived from the one channel that actually exists, an ingredient states:

1. **What the channel is**, and what kind of artifact it takes.
2. **Registration** — the one-time, account-gated step, and **a checkable test for whether it is
   already done.** The check is what makes a `**One-time setup:**` block work rather than being a
   note nobody can act on.
3. **Credentials** — the mechanism, and its own check. GPG for a PPA, OAuth for Launchpad's API,
   a store login elsewhere. Named as different mechanisms, because they are.
4. **Machine-local config**, if any, and the exact content to merge.
5. **The publish action** for the `channels.yaml` leaf, with its real requirements and issues.
6. **Confirmation** — how anyone finds out whether the publish actually landed (v13's `confirm`).
   A channel with a remote build or a human review is the normal case, not the exception.
7. **The `RELEASING.md` steps** it needs, and where they belong in dependency order.
8. **Any script template** to instantiate into the project.

### Layout

Shipped ingredients live beside the skill that reads them, and carry their own templates:

```
skills/orc-package/
├── SKILL.md
└── ingredients/
    └── ppa/
        ├── ingredient.md            # the prose, in the shape above
        └── templates/
            └── ppa-copy-series.py   # instantiated into the project's scripts/
```

A user-level ingredient is the same shape one directory deeper in
`${XDG_CONFIG_HOME:-~/.config}/orclab/ingredients/<channel>/`, so a captured ingredient can carry
templates too and a contributed one is a directory move rather than a rewrite.

**The honest limit:** this shape is derived from exactly one channel, so it is PPA-shaped. The
first snap capture will probably reveal it needs changing. That is expected — it is derived from
real practice rather than invented, which is the same standard as everything else here — but v1 of
the shape is not the final shape, and whoever writes the second ingredient should feel free to
change it rather than contorting a real channel to fit.

## Capture — how a channel Orclab does not ship becomes an ingredient

For `/orc-package snap` today, the honest answer is that there is no ingredient. Refusing there and
stopping teaches nothing and leaves the next person where this session started.

Instead: `/orc-package` walks the user through standing the channel up, and **writes the result as
a new ingredient** in the shape above. Doing the work once produces the thing that makes it
unnecessary the second time.

**Where a captured ingredient lives, and why not the three obvious wrong places:**

```
${XDG_CONFIG_HOME:-~/.config}/orclab/ingredients/<channel>/
```

- **Not the project repo** — the entire point is the *next* project. An ingredient in Orcshot does
  nothing for the one after it.
- **Not the installed plugin cache** — a reinstall destroys it, and `CLAUDE.md` already records
  that the cache is refreshed from a marketplace clone.
- **Not Orclab's own repo** — a real end user installs Orclab as a plugin and neither can nor
  should write there.

Config rather than data: an ingredient is a declarative description the user authors and
hand-edits, which is what `~/.config` is for. `~/.local/share` reads as "the app put this here,
don't touch it," which is the opposite. **Honor `XDG_CONFIG_HOME`** rather than hardcoding
`~/.config`, and allow `ORCLAB_INGREDIENTS_DIR` as an explicit override — one line, and it is the
difference between working and not on a machine with an unusual layout.

**Precedence: a user ingredient of the same name wins over a shipped one**, and `/orc-package`
says which it used. That is how someone corrects a shipped ingredient that is wrong for them
without editing the plugin.

**A captured ingredient is contributable.** It is a markdown file in the documented shape; moving
it into Orclab's repo is how it stops being user-level and starts helping everyone. The spec does
not automate that — a pull request is not a thing Orclab should invent — but the format makes it a
copy rather than a rewrite.

**Deliberate risk, recorded:** capture is designed from zero worked examples *of capturing*. The
mitigation is that the shape it captures into is derived from a real channel, not an imagined one.
If the first real capture shows the interview asks the wrong questions, that is a finding to act
on, not a failure of the idea.

## The command surface

| Invocation | Does |
|---|---|
| `/orc-package` | Lists available ingredients — shipped and user-level, marked as which |
| `/orc-package <channel>` | Applies that ingredient to the current project's recipe |
| `/orc-package <channel>` (no ingredient) | Offers to capture one, and walks it through |

**Frontmatter: `disable-model-invocation: true`.** Per the design checklist's item 2, this is
one-shot and side-effecting — it writes files inside and outside the repo and stands up
distribution channels. Claude must never reach for it because a request superficially matched. The
`**One-time setup:**` rule already says standing up a channel is always something the user asks for
directly, and this is the same rule applied to the component itself.

**No unscoped `Bash` pre-approval**, for the reason `/orc-release` already gives: this writes files
outside the repository, and each such write should surface a permission prompt at the moment it
happens. Buying fewer prompts here would remove friction from precisely the operations that most
deserve it.

## This resolves #17's parked disagreement

The entry parks a dispute: should Orclab own a generalised Launchpad API client? The Orcshot 0.3.0
handover argues yes; the position taken while building `ppa-copy-series.py` was that Orclab ships
mechanism and projects ship actions.

**Ingredients answer it without either extreme.** Orclab ships the PPA ingredient, and that
ingredient *carries the copy script as a template* which `/orc-package` instantiates into the
project's `scripts/`. The project owns its copy and can edit it; Orclab is not carrying a live
Launchpad client in its own runtime. Neither "the framework knows about one hosting provider" nor
"every project reinvents it."

The properties that implementation must keep, all proven live 2026-09-07 and not in dispute, become
part of the ingredient: a `--check` mode answering "has the one-time authorization happened"
without triggering it, a `--dry-run` that authenticates anonymously so preconditions are verifiable
on an unconfigured machine, refusal when the source is not `Published` or has no built binaries,
and a credentials file at `chmod 0600` that is never printed.

## Interlocks

- **Orcshot #198** (build the real snap and Flathub publish mechanisms) produces the **second
  ingredient** as a by-product. That is the example this design most needs, and it is the honest
  test of whether the ingredient shape generalises past one channel.
- **v13 / #18** — `confirm` is part of an ingredient. A channel with a remote build or human review
  is the normal case.
- **v12 / #21** — an ingredient may declare `preflight` rules appropriate to its artifact format.
- **v14 / #20** — the seam is a GitHub Release, defensibly both a forge operation and a
  distribution channel. v14 defers: `/orc-git release` is the mechanism, and whether a project
  treats it as a channel is expressed in that project's recipe. **This spec agrees with that
  split**, which settles v14's open question in the direction it predicted.
- **#4** — same vocabulary, deliberately no shared mechanism.

## What is genuinely unproven

Stated so it is not assumed away later: the "one-time setup, credential mechanism, publish action,
confirmation" shape is proven for **exactly one channel**. Snap and Flathub are researched but
unbuilt. The App Store and Play Console add binary signing and multi-day human review, and whether
this shape survives contact with App Store Connect has not been checked at all. The design is built
so that finding out is cheap — capture an ingredient and see what does not fit — rather than
requiring the shape to be right in advance.

## Testing

`/orc-package` is a prose skill with no bundled script; the writes are file edits Claude performs,
matching `/orc-code` and `/orc-git`. So this is verified through `VERIFICATION.md` scenarios:

- **Applying the PPA ingredient** to a synthetic scratch project: the `channels.yaml` leaf,
  `distro.yaml` entries and `RELEASING.md` steps all appear, the steps are contiguous integers
  after insertion, and `/orc-release`'s parser reports no warning.
- **No machine-local write for the PPA**: applying the ingredient in a scratch `HOME` leaves
  `$HOME` untouched except for nothing — no `~/.dput.cf`, no config directory. (The merge rules
  above have no shipped ingredient to exercise them; the first captured ingredient that needs a
  per-user config file is where that scenario gets written, against a real file.)
- **Never a credential**: applying the ingredient on a machine with no GPG key reports the missing
  key and writes nothing secret.
- **Account-gated refusal**: it never creates a PPA, and says plainly that is the user's to do.
- **No ingredient**: `/orc-package snap` offers capture rather than failing.
- **Capture**: an interview writes a well-formed ingredient to the user-level directory, honoring
  `ORCLAB_INGREDIENTS_DIR`.
- **Precedence**: a user ingredient shadowing a shipped one is used, and `/orc-package` says so.

## Global constraints

- No new dependency.
- The `orc-` prefix holds, so `/orc-help` lists it.
- Orclab ships the mechanism and the ingredient. No consuming project's content is written from an
  Orclab-centred session; applying an ingredient to Orcshot happens in a session centred on Orcshot.
- Nothing here changes `/orc-publish`, `/orc-release` or `/orc-version` behaviour.
