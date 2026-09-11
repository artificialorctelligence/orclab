---
name: orc-package
description: Use when the user explicitly asks to use orc-package, or types /orc-package, to stand up a distribution channel for the current project - applying a shipped or captured ingredient (how to set up a PPA, a store, a registry) to the project's own channels.yaml, distro.yaml and RELEASING.md, or capturing a new ingredient for a channel Orclab does not ship yet.
disable-model-invocation: true
allowed-tools: Read, Bash(ls *), Bash(grep *), Bash(python3 *), Bash(gpg --list-secret-keys *), Bash(curl -sfI *)
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
2. Write `${ORCLAB_INGREDIENTS_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/orclab/ingredients/<channel>/ingredient.md`
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
