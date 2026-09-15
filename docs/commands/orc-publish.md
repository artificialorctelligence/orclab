# /orc-publish

## What it's for

You've built something, and your project already knows where it's supposed to go — real
destinations like a Launchpad PPA, the Snap Store, Flathub, or npm, each one called a **channel**,
set up ahead of time (typically by [`/orc-package`](orc-package.md)) in your project's own
`.orclab/publish/channels.yaml`. `/orc-publish` is what actually sends a finished build to one or
more of those channels — or, separately, reads back the numbers a channel already publishes about
itself, or checks whether something you already sent has actually landed yet. Claude never reaches
for this on its own: it only runs because you typed it yourself, or because a project's own
[`/orc-release`](orc-release.md) process names it as one of its steps.

## What you type

| You type | What it does |
|---|---|
| `/orc-publish <selection>` | Shows you the exact plan — the **dry run** — for what would be published where, then, once you say yes to that plan, actually publishes it |
| `/orc-publish <selection> --dry-run` | Shows the same plan on its own and stops there; nothing is published |
| `/orc-publish <selection> --metrics` | Reads back each channel's own published download/install numbers; publishes nothing |
| `/orc-publish <selection> --confirm` | Checks whether a publish that came back **accepted** earlier — meaning the channel took it in but hadn't yet confirmed it had landed — has landed since, reporting one of four things: landed, not yet, needs a human (a URL to go check by eye), or nothing to confirm (the leaf was never asynchronous to begin with); publishes nothing |
| `/orc-publish --for <path>` | Looks up what's configured for one specific thing in `distro.yaml`; read-only |
| `/orc-publish <selection> --timeout <seconds>` | Changes how long a publish step is allowed to run before it counts as timed out (a channel can set its own limit that still wins) |
| `/orc-publish <selection> --allow-preflight-failure` | Publishes anyway over a failed **preflight check** — the automatic checks `/orc-publish` runs against a built artifact before sending it anywhere, like making sure it doesn't contain leftover version-control files — that would normally stop it; only when you explicitly ask for this |

`<selection>` names which channel(s) to act on. `channels.yaml` is organized as a tree of dotted
paths — a **tree file** — with each specific destination at the end of one path called a **leaf**;
`<selection>` is one or more of those paths (`!` in front of one excludes it instead). For example,
a project with a Linux PPA channel arranged the way the skill's own examples are (a leaf named
after the Ubuntu series it publishes to, like `noble`) might select just that one leaf with
`linux.ppa.noble` — the exact shape depends on how your project's own `channels.yaml` is laid out.
Leaving `<selection>` out acts on everything the tree file has actionable.

## What it will ask you

- For an actual publish (no `--metrics`, `--confirm`, or `--for`): it always shows you the dry-run
  plan first — every channel or leaf involved, its real action, its time limit, and anything it
  needs from you before you confirm (like unlocking a signing key) — and waits for a clear yes to
  *that specific plan* before doing anything. An earlier "sounds good" from somewhere else in the
  conversation doesn't count; it needs a fresh yes to this exact list.
- For `--for`, `--metrics`, and `--confirm`: nothing. All three are read-only and go straight to
  their answer.
- If it can't even get that far — PyYAML isn't installed, or your project has no
  `.orclab/publish/channels.yaml` yet (or, for `--for`, no `distro.yaml`) — it isn't a question:
  it tells you plainly and stops.

## What it changes

- It reads your project's own `.orclab/publish/channels.yaml`, and, for `--for`, its
  `distro.yaml` too — both written by [`/orc-package`](orc-package.md) — but never writes to
  either one itself, and never makes a commit.
- What actually changes happens on the far side, at each channel itself, doing whatever that
  channel's own configured action does: a package uploaded to a PPA, a new version pushed to a
  registry, a submission opened with a store. Some of that lands immediately; some is
  **asynchronous** — queued or opened for review rather than finished the moment the command
  returns — and `/orc-publish` reports those as accepted rather than done, with `--confirm` as how
  you check on one later.
- Every leaf's outcome is reported exactly as it happened, as one of six words, never smoothed
  over into a single "it worked" or "it's done":
  - **success** — it ran and worked, with whatever real output it produced
  - **accepted** — it went through, but hasn't been confirmed to have landed yet (see
    `--confirm` above)
  - **refused** — a check caught a problem before anything ran
  - **failed** — it ran and came back with a real error
  - **timed out** — it was still running when its time limit hit
  - **not attempted** — there was nothing configured to run for that leaf at all
- If a leaf's own setup step already ran and built something before a check caught a problem
  (reported as `refused`), `/orc-publish` doesn't undo that — the refusal stops the publish
  itself, not whatever building already happened.
- `--metrics` and `--confirm` change nothing anywhere; they only read something back. One caveat
  on `--metrics`: the ready-made Snap Store example Orclab ships for it has never actually been
  run for real — no Orclab-built project has a published snap yet — so treat any number it reports
  as unverified until someone has.

## What it will never do without asking

- It never skips straight to publishing — it always shows the dry-run plan and waits for a clear
  yes to that exact plan first, no matter how confident the request sounded ("just publish
  everything, ship it all" doesn't skip the gate).
- It never accepts an earlier "sounds good" as that yes — it needs a fresh confirmation of the
  specific resolved list every time.
- It never invents a publish configuration when none exists — it says so plainly and stops.
- It never guesses which channel you meant — if what you named doesn't match anything, or matches
  more than one thing, it reports the problem instead of picking one for you.
- It never attempts a channel that has no publish action configured yet — it reports that
  plainly instead of trying and failing.
- It never publishes anything if any leaf in the plan has an unusable configuration — a
  non-text `action:`, `metrics:`, or `prepare:` value, a `timeout:` that isn't a positive whole
  number of seconds, or a `confirm:` block it can't use — it names the leaf and the bad value and
  stops the entire run before anything is sent anywhere, rather than publishing the leaves that
  look fine and leaving the broken one for later.
- Once the run is actually underway, one leaf's action failing does not stop its siblings — each
  leaf still gets its own attempt and its own reported outcome.
- It never paraphrases a failure away, and never reports a leaf as done unless the run actually
  confirmed it — a publish that's only accepted (queued, not yet landed) is never called finished.
- It never adds tracking, analytics, or phone-home code to get a channel's own numbers —
  `--metrics` only relays counts a channel already publishes about itself, together with the
  honest caveat that these count fetches, not people.
- It never treats `--confirm` as a way to publish anything — it only runs each channel's own
  landed-yet check and reports an honest outcome; it also never silently drops `--dry-run` or
  `--metrics` if you combine either with `--confirm` — it refuses the combination outright instead.
- It never guarantees that a channel's own landed-yet check is completely safe to run blindly —
  that check is your project's own command, not something Orclab verifies is read-only.
- It never waves an artifact through a check it can't actually read — an unsupported archive
  format is refused, not passed with a false green tick.
- It never downgrades a failed check to a mere warning on your behalf — `--allow-preflight-failure`
  only applies when you explicitly ask for it; it's never assumed on your behalf just because a
  request sounded urgent.
- It never builds anything during a dry run — a dry run only looks at what's already built, or
  reports that the real run would need to build it first.
- It never runs on its own initiative — only because you typed `/orc-publish` yourself, or because
  a project's own [`/orc-release`](orc-release.md) process names it as one of its own steps.
