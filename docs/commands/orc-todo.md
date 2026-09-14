# /orc-todo

## What it's for

You want to see what's still open on the project's backlog — its running list of things to do,
each one a numbered entry — read one of those entries in full, add a new one, remove one, or
manage its lanes: named, ordered lists that say which entries get worked on, and in what order.
`/orc-todo` does all of that for you, without you having to open and hand-edit the backlog file
yourself.

## What you type

| You type | What it does |
|---|---|
| `/orc-todo list` | Lists every open entry, one line each, then any lanes that exist |
| `/orc-todo show <n>` | Shows entry number `<n>` in full |
| `/orc-todo add <resource> <title>` | Adds a new entry titled `<title>`. `<resource>` is `backlog` for a genuine finding, or `verification` for a scenario describing something to check by hand later, once the work exists to check it against. You don't type the entry's full text as part of the command — you feed it in separately — and the command prints back the number it gave the new entry. |
| `/orc-todo remove <n>` | Deletes entry number `<n>` |
| `/orc-todo lane list` | Lists every lane — a named, ordered list of work items to go through, one at a time — and what each one is currently working on |
| `/orc-todo lane create <name> <items>` | Creates a lane named `<name>`, ordered by `<items>` — a comma-separated list of item names, e.g. `v13,v14` |
| `/orc-todo lane modify <name> <items>` | Replaces a lane's item list — use it to reorder, add, or drop items |
| `/orc-todo lane delete <name>` | Removes a lane |
| `/orc-todo lane current <name> <item>` (or `-`) | Marks which item a lane is currently working on; use `-` instead of an item to clear it |
| `/orc-todo lock status` | Shows whether the backlog is currently locked — held by another session, so two people don't write to it at the same time — and if so, who's holding it, for how long, and whether that session is even still running |
| `/orc-todo lock clear` | Releases that lock |

Add `--cwd <path>` before any of these to run the command against a different project than the
one you're currently in.

## What it will ask you

Nothing, for almost everything — every command above runs the instant you type it, and prints its
result straight back to you.

The one exception: if you ask `lane create` or `lane modify` to include an item that has no real
spec (a written description of what that piece of work should do) or plan (a written,
step-by-step plan for doing it) behind it yet, it won't add it and move on. It offers to write
that spec first, and then comes back and asks which lane the finished item belongs in.

## What it changes

- `add`: writes the new entry into one of two files, depending on `<resource>`. A **backlog**
  entry always lands in the project's `BACKLOG.md` — specifically the copy belonging to the
  project's main checkout (its primary, permanent copy), even if you run the command from a
  worktree (a separate, temporary working copy of the same project, checked out for one piece of
  work in isolation). That way a genuine finding is visible right away, in the one file everyone
  actually reads. A **verification** entry lands in `VERIFICATION.md`, but in whichever checkout
  you actually ran the command from — since it usually describes something that only exists on
  the branch you're currently working on, and shouldn't appear on the project's main line until
  that branch does. If you're already running the command from the main checkout, both kinds of
  entry land in the same place, so there's nothing to think about. Either way, the entry's number
  comes from one counter shared by every checkout, so two entries added at the same time from two
  different places never collide.
- `remove <n>`: deletes that entry's own section from the backlog, and nothing else.
- `lane create` / `lane modify` / `lane delete` / `lane current`: change the saved list of lanes,
  and, for `current`, which item a lane is presently working on.
- `lock clear`: releases the lock, so it stops blocking anyone else from writing to the backlog.
- `list`, `show`, and `lock status` only read information back to you — none of them change
  anything.

## What it will never do without asking

- It will never create a backlog file on its own. Outside a git project, or in a project that
  doesn't have one yet, it says so plainly and creates nothing.
- It will never accept a blank entry. If the body you give `add` is empty, or only blank lines,
  it refuses outright rather than writing a stub.
- It will never commit the entry it just wrote. Writing an entry and committing it to git are two
  separate steps — committing is something you do yourself afterward, for example with
  [`/orc-git commit`](orc-git.md).
- It will never renumber the remaining entries when one is removed, and it will never reissue the
  number that was freed up. If you later see a gap in the numbering, that's the record of
  something that used to be there, not a mistake to fix.
- It will never add an item to a lane unless a real spec or plan already exists for it. If one
  doesn't, it refuses and tells you exactly which item is missing one — it never invents a
  placeholder to fill the gap, and never quietly drops that item from the request instead.
- It will never treat `lock clear` as routine housekeeping. Only run it after you've checked
  `lock status` and judged the lock genuinely stale — its holder's process no longer running, or
  its age clearly implausible. Finding the backlog locked when you didn't expect it usually means
  something is genuinely in progress, or something crashed partway through writing — worth
  looking into before clearing it, not cleared on reflex just because it's in the way.
