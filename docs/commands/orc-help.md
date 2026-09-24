# /orc-help

## What it's for

You want to know which version of Orclab is actually running right now, and what commands it
currently gives you — or you already know the command you want and would rather read its own
page than hunt for it. `/orc-help` works the same in either of the two places Orclab can be used
from: inside Orclab's own project, where the point is developing Orclab itself (this page calls
that "core context"), and inside any other project that simply has Orclab installed as a plugin
to use its commands ("project context"). Either way, it looks at what's actually installed or
sitting in the folder right now rather than assuming — so what it reports always matches the
real, current commands, even right after an update.

## What you type

| You type | What it does |
|---|---|
| `/orc-help` | Reports the version of Orclab that's running, and lists every command it currently has, one line per command. |
| `/orc-help <name>` | Shows that one command's own page instead of the list. Works with or without the leading `/` and the `orc-` prefix, so `git`, `orc-git`, and `/orc-git` all reach the same page. |

`/orc` is a shorter way to type the same thing — see [`/orc`](orc.md).

## What it will ask you

Nothing. It works out the answer on its own and reports it. When it can't — Orclab isn't
installed as a plugin anywhere on this machine, or the name you gave doesn't match any real
command — it stops and says so plainly, rather than asking you a question and waiting for an
answer.

## What it changes

Nothing. It only reads: the installed plugin's own files, to work out the version and the list of
commands, and, when you name one, that command's own page under `docs/commands/`. It never writes
anything, anywhere.

## What it will never do without asking

- It looks in every place a plugin can actually live, including the one a Claude Code on the web
  session loads from. It used to look in only two of the three, which meant that in a cloud
  session it reported Orclab as not installed while running out of Orclab.
- It never reports a version it isn't sure of. If Orclab isn't installed as a plugin anywhere on
  this machine and you're in a project other than Orclab's own, it says so plainly and stops
  instead of guessing.
- If you're inside Orclab's own project and no installed copy can be found anywhere else, it
  still reports a version — the one sitting in this folder right now — but labels it plainly as
  the working copy rather than an installed one, so an in-progress copy is never mistaken for the
  real installed version.
- It never answers from memory. Whether it's listing every command or showing you one command's
  page, it opens the real, current file at that moment — never a recollection of what that
  command used to do.
- If you name a command that doesn't exist, it says so plainly — "There is no `/orc-<name>`
  command; `/orc-help` lists what exists." — and stops, rather than guessing at what you meant.
- Beyond reading those files and reporting what they say, it never does anything else — no file
  it writes, no command it runs on your behalf.
