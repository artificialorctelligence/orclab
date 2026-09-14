# /orc-release

## What it's for

Your project has its own `RELEASING.md` — the ordered checklist that says exactly what "a
release" means for this project: which tests must pass, which files get their version bumped,
what gets built, and in what order it all has to happen. `/orc-release` is what actually walks
that checklist for you, start to finish, carrying out each step in the document's own order,
asking you for a decision wherever the document calls for one, and stopping outright the moment a
step fails rather than pushing on past it. It also remembers exactly where a release stands, so
you can close the session partway through and pick up again later — even in a brand-new session —
right where you left off.

It never invents a release process of its own. Whatever `RELEASING.md` says is the whole and only
plan; `/orc-release` reads it, drives it, and does not add, skip, or reorder a single step on its
own idea of what a release should include. And Claude never starts one of its own accord: this
only ever runs because you typed `/orc-release` yourself.

## What you type

| You type | What it does |
|---|---|
| `/orc-release` | If nothing is already underway, begins a new release — after confirming the target version with you — and walks `RELEASING.md` from its first step. If a release is already in progress, picks it back up exactly where it stopped, including in a session that never saw it start. |
| `/orc-release status` | Reports where a release currently stands — which steps are done, which were skipped and why, what's next — and stops there. Nothing is changed by asking. |

Beyond that, `/orc-release` follows what you tell it to do mid-release: ask it to skip a step
(with your reason) and it records that instead of running the step; ask it to abandon the release
and it rolls back what it safely can. Neither of those ever happens on its own — only because you
asked.

## What it will ask you

- If your project has no `RELEASING.md` yet, it isn't a question: `/orc-release` says so plainly
  and stops, pointing you at the `release-checklist` skill to create one, rather than guessing at
  a process to run.
- **Starting a brand-new release (never on a resume):** before touching anything, it shows you
  your project's real, unfiltered list of uncommitted changes (`git status --short`) and asks
  whether to proceed. This is only a check, not a block — its purpose is making sure unrelated,
  in-progress work in your tree gets a chance to be noticed before a release runs on top of it. It
  then confirms the exact version number to release before starting.
- **Any step the document marks as done by hand:** it tells you exactly what you need to do, then
  stops and waits — it never decides for itself that a by-hand step is finished. It only records
  what you tell it you did.
- **A step whose one-time setup hasn't happened yet** — something that only ever needs doing once
  for the whole project, like registering a store listing name or creating a signing key: it names
  exactly what's missing, in the document's own words, and asks whether to set it up now, then
  asks whatever that setup itself needs (which account, which key, which name). It only runs the
  real setup once you say yes.
- Expect ordinary Claude Code permission prompts throughout a real release, more than one. Each of
  your project's own commands — running its tests, building its artifact, uploading it — asks
  separately, right before it runs, rather than all being approved as a block up front. That's
  deliberate: it puts a visible check immediately in front of each riskier step instead of
  removing it.

## What it changes

- **Its own record of where a release stands**, at `.orclab/release/state.json` — created when a
  release starts, updated as each step is completed or skipped, and cleared once the release
  finishes or is aborted. This is the only thing that makes "pick up where I left off in a new
  session" possible.
- **The project's version files** — never written by `/orc-release` itself. It reaches
  [`/orc-version`](orc-version.md)'s own logic to do that, and holds back the commit specifically:
  the version is set early, but nothing is committed until `RELEASING.md`'s own later step does
  it, once the built result has actually been checked — committing any earlier would leave a real
  commit behind for every release attempt that never actually shipped.
- **`CHANGELOG.md`** — gets the entry `/orc-version` drafts, as part of that same version-setting
  step.
- **Whatever `RELEASING.md`'s own steps do**, exactly as that document says — nothing more. A
  step's real commands run for real; `/orc-release` never widens one beyond what's written there.
- **When the last step passes**, the release closes itself automatically: a summary is printed
  (the version, which steps completed, which were skipped and why, and which completed steps are
  now permanently irreversible), and its own state record is cleared. Nothing is rolled back at
  that point — a release that reaches its last step stands as shipped.
- **If you abandon a release instead** (asking it to abort), it rolls back what it safely can: the
  project's version files go back to what they held before the release started. Two things are
  deliberately left behind rather than touched automatically: a `debian/changelog` entry already
  prepended for this release stays in place (rewriting a changelog file automatically isn't safe,
  so you remove it by hand), and any `CHANGELOG.md` entry `/orc-version` drafted for this release
  is left untouched too, for the same reason. Any step already completed that `RELEASING.md`
  itself marks irreversible is never undone — it stands exactly as it is. If the document doesn't
  mark any step irreversible at all, `/orc-release` says so plainly and tells you to check every
  completed step yourself rather than guessing which of them can still be walked back. Its own
  state record is cleared once the abort finishes either way.

## What it will never do without asking

- It never continues past a failed step. The moment one fails, it stops, reports the real error,
  and waits for you — it never retries on its own, never skips ahead, and never keeps going.
- It never runs a command that isn't either something `RELEASING.md` itself states, or one of
  `/orc-release`'s own bookkeeping calls (checking status, recording a step done). It never
  invents a command of its own, and never adds anything to a documented step's command beyond
  what's written.
- It never acts on a step without first reading the whole document — reading only the one step in
  front of it, and missing what a later step needs, is exactly the mistake this command exists to
  prevent.
- It never keeps walking a release once `RELEASING.md` has changed underneath it. A mid-release
  edit can shift which step is which, so it stops and tells you to re-read the document instead of
  guessing at the new numbering.
- It never marks a by-hand step complete on its own initiative — only you can say you actually did
  it, and it records exactly that, nothing more.
- It never runs a one-time setup's real commands just to find out whether they're needed — it only
  ever runs the check, and only runs the setup itself once you've said yes. Some of these
  (registering a store name) work exactly once; others (submitting something for review) open a
  real process other people act on over days. Neither may ever start as a side effect of a check.
- It never skips a step on its own initiative — only when you explicitly ask, and only with a
  reason you actually give it.
- It never uses abandoning a release (abort) to close one that actually shipped — that's what
  finishing a release is for. Using abort on a shipped release would roll version files back on a
  repository whose release commit and tag already exist, which is simply wrong; abort is only for
  walking away from a release that didn't ship.
- It never claims to have undone more than it actually did — telling you a release was cleaned up
  when something has already gone out publicly would be worse than saying nothing at all.
- It never writes a project's version files itself, under any circumstance — that always goes
  through [`/orc-version`](orc-version.md)'s own logic, and is never committed at the moment it's
  set.
- It never softens a failed step's real output into something gentler — it reports the actual
  error, in full, every time.
- When `RELEASING.md` uses none of its optional markers at all (no by-hand steps, no one-time
  setup blocks, no pointers to run another command), it never assumes that therefore makes a step
  safe to run unsupervised — it asks you rather than guessing.
- It never starts a release, or acts on one, on its own initiative — this only ever runs because
  you typed `/orc-release` yourself.
