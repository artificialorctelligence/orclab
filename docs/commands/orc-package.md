# /orc-package

## What it's for

You've built something and now need to set your project up to actually ship it somewhere real —
a Launchpad PPA (a package archive Ubuntu and Debian users can add and install from), an app
store, or a package registry like npm. Doing that right the first time usually means researching
that destination's own rules from scratch. `/orc-package` skips the research: it applies a
ready-made, written-down set of instructions for one such destination — called an **ingredient**
— to your own project. A destination you can publish to is called a **channel**; the instructions
for setting one up are its ingredient. If no ingredient exists yet for the channel you name, it
offers to interview you about setting it up for real and write down what you did as a brand-new
ingredient — this is called **capturing** one — so the next project doesn't have to redo the
research either.

Because standing up a whole distribution channel is a real, one-time, consequential step, this
command only ever runs because you typed it — it never starts on its own just because a request
sounded related.

## What you type

| You type | What it does |
|---|---|
| `/orc-package` | Lists every channel it currently knows how to set up, and whether each one's instructions are Orclab's own or ones you wrote yourself |
| `/orc-package ppa` | Sets up a Launchpad PPA |
| `/orc-package snap` | Sets up the Snap Store |
| `/orc-package flatpak` | Sets up Flathub |
| `/orc-package play` | Sets up Google Play |
| `/orc-package app-store` | Sets up the Apple App Store |
| `/orc-package <other channel name>` | If no ready-made instructions exist for that name, offers to interview you and write new ones |

Of those five ready-made channels, only the Launchpad PPA one has actually been carried through a
real release so far. The Snap Store and Flathub ones have had real registration and real checks
run against them, but no real upload yet. The Google Play and Apple App Store ones are written
from each store's own published rules but have not been tried against a real release at all.
Whichever is true for a given channel is stated up front in that channel's own instructions, so
you always know how much to trust it before relying on it.

If you (or someone on your team) already wrote your own version of a channel's setup
instructions — saved on your own machine rather than shipped with Orclab — that version is used
instead of Orclab's built-in one for that channel name, and `/orc-package` always tells you which
one it used.

## What it will ask you

For `/orc-package` on its own: nothing. It just lists what it knows and stops.

For `/orc-package <channel>`, when instructions for that channel already exist:
- It asks you for every piece of information those instructions need — things like an account
  name, a package name, a signing key, or which release series to use. It never guesses any of
  these; if you don't supply one, it stops and asks rather than filling in a plausible-looking
  value.
- It asks where in your project's own channel list this new channel belongs, since that list can
  be organized in more than one way and you know your project's shape better than it does.

For `/orc-package <channel>`, when no instructions exist for that name yet:
- It asks whether you want to walk through setting the channel up together and have the result
  written down for reuse. If you say no, nothing happens.
- If you say yes, it interviews you section by section about how the channel works, and for the
  parts about registering an account, handling credentials, and any one-time-per-app setup, it
  insists on a real, repeatable way to check each one — an instruction nobody can ever verify
  isn't worth writing down.

## What it changes

- **`.orclab/publish/channels.yaml`**: adds the entry for the channel you're setting up, at the
  spot you named. This file is organized as a tree of paths (for example, a desktop app's Linux
  PPA might live at `desktop.python.linux.ppa`); one entry at the end of such a path is called a
  **leaf**. If a leaf at that exact path already exists, it's left completely alone and reported
  as untouched — `/orc-package` only ever adds a missing leaf, never replaces an existing one.
- **`.orclab/publish/distro.yaml`**: adds entries for the specific things you name (an app or
  package to publish), the same way — existing entries are never replaced.
- **`RELEASING.md`** (your project's own written release checklist): adds the steps that channel
  needs, at the point they belong, renumbering surrounding steps so the numbering stays in
  order. If your project doesn't have a `RELEASING.md` yet, it says so and stops before writing
  anything here — that file gets created as a separate, earlier step in setting up a project's
  release process, and this command doesn't substitute for it.
- **Files under `scripts/`**: for channels that need a helper script, adds one from a template
  — but only if a file of that name doesn't already exist there.
- **A small settings file that lives outside your project, on your own machine** (not part of
  the project's own files, so it never shows up in `git status`): some channels need one, for
  something like a local reference to a signing key. When one is needed, three rules always
  apply: it only ever gets a missing piece added to it — an existing one is never rewritten from
  scratch; the exact content is always shown to you before it's written, and running the command
  again afterward changes nothing; and it is never used to hold an actual secret — no password,
  key, or passphrase is ever written into it, or printed anywhere, by this command.
- If you go through the interview to **capture** a brand-new channel, the result is written as a
  new ingredient into a folder on your own machine (not inside the project itself), so it's
  automatically available to every other project on that same machine too — not just this one.
- Everything above only gets written after it's shown to you first.

## What it will never do without asking

- It never guesses a value it needs from you — an account name, a package name, a key, a series.
  If you haven't given it one, it stops and asks instead of filling in something plausible.
- It never does the actual account-side setup itself — creating the PPA, registering a signing
  key, authorizing access, claiming a store listing name. Every one of those stays yours to do by
  hand. `/orc-package` only checks whether each one is already done, and if it isn't, it writes
  that check into `RELEASING.md` as a step your project's release process re-checks every time,
  rather than trying to do the step for you.
- It never overwrites anything already there — an existing `channels.yaml` leaf, an existing
  `distro.yaml` entry, an existing script file, or an existing `RELEASING.md` step is always left
  exactly as it is; only what's missing gets added.
- It never writes, or prints, an actual credential — a password, a key, or a passphrase — into
  any file it touches, including the machine-local settings file above.
- When no instructions exist yet for a channel you name, it never fails silently and never
  invents a made-up procedure to fill the gap. It says plainly that nothing exists for that name
  and offers to build real instructions with you instead.
- It never produces the thing being shipped itself — the installer package, the signed app,
  whatever the store actually expects. Building that is [`/orc-code`](orc-code.md)'s job; this
  command only sets up where a finished one gets sent.
- It never runs an actual release. Carrying out an upload or submission using the instructions
  this command wrote is [`/orc-release`](orc-release.md)'s job.
- It never writes into any project other than the one you ran it in.
- It never starts any of this on its own initiative. Standing up a distribution channel always
  has to be something you type yourself, even if a project looks ready for one.
