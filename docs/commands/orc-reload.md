# /orc-reload

## What it's for

You're developing a Claude Code plugin — a package of skills and commands that adds abilities to
Claude Code, and Orclab itself is one example, though this works for any plugin, not just
Orclab — and you've just changed its code. Claude Code only loads a plugin's skills and commands
when a session starts, so the session you're using right now to develop the plugin is still
running whatever code was installed before your latest changes, no matter what you edit from
here. `/orc-reload` confirms the folder you're in really is a plugin project, works out how that
plugin is currently installed, reinstalls it, and checks that the version you expect actually
landed. **One thing it cannot do, and no command can:** make the session you're running it from
switch to the new version. A reinstall only takes effect in a session you start afterward — it
tells you that plainly, every time it finishes.

**In a cloud session it does something different, because there is nothing to reinstall.** A
session in Claude Code on the web runs the plugin straight out of the folder you're looking at,
without installing anything, so there is no installed copy to replace. What it checks instead is
the thing that actually decides what your next session runs: a new cloud session is a fresh copy
of your repository *as it exists on GitHub*. So work you've saved but not committed, or committed
but not pushed, simply won't be there. It tells you which of those is true of your project right
now, and the remedy is to commit and push and start a new session — not to reinstall anything.

## What you type

| You type | What it does |
|---|---|
| `/orc-reload` | Reinstalls the plugin belonging to the project you're currently in, reporting the version that was installed before and the version installed after. |

## What it will ask you

Nothing. It runs through on its own and reports what it found and did. When something's wrong —
the project isn't a plugin, the plugin's never been registered, or the reinstall didn't actually
take — it stops and tells you plainly, rather than asking a question and waiting on an answer.
The one place it hands a decision to you instead of making it itself: if the plugin's registered
from GitHub (see "What it changes" below) and its local copy is out of date, it stops and gives
you the exact command to bring that copy up to date yourself, rather than running that command
for you.

## What it changes

Nothing in your project — it only reads `.claude-plugin/plugin.json` there, to confirm it's a
plugin and note its name and current version. Everything it actually changes lives under
`~/.claude/plugins/`, the folder where Claude Code keeps every plugin it has installed:

- It looks up how your plugin is registered as a *marketplace* — the record that tells Claude
  Code where to install a plugin from — in `~/.claude/plugins/known_marketplaces.json`. A
  marketplace registered **by directory** points straight at your project folder, so there's
  nothing to refresh: whatever's on disk there right now, committed or not, is what gets
  installed. A marketplace registered **by GitHub** instead works from its own copy of the
  repository — a *cached clone* — kept under `~/.claude/plugins/marketplaces/<name>`, which does
  not update itself; `/orc-reload` checks whether that copy has fallen behind (by fetching from
  GitHub) but, as covered in "What it will never do without asking" below, never updates it
  itself.
- It reinstalls the plugin — uninstalling it, then installing it again — which installs a fresh
  copy under `~/.claude/plugins/cache/`. An older version's directory may still sit beside it
  afterward; that's normal and not a sign anything went wrong.
- It then reads that copy back to confirm the version you expected is the one actually installed.

## What it will never do without asking

- It will never treat a reinstall as visible in the conversation that ran it. A reinstall only
  shows up in a session you start after it finishes — this session goes on running the old
  version, and it says so plainly, every time, at the end.
- If your project has no `.claude-plugin/plugin.json`, it will never guess at what to reinstall —
  it tells you plainly that this isn't a Claude Code plugin project and stops there.
- If it can't find your plugin registered as a marketplace anywhere on this machine, it will
  never invent or guess a name for one — it says so plainly and stops, so you can register it
  yourself first (`claude plugin marketplace add <path>`). Registering a plugin this way is a
  normal one-time step every plugin gets on a given machine before it can be installed at all —
  hitting this case just means that step hasn't happened here yet, not that anything is wrong.
- If the plugin's registered from GitHub and its cached clone has fallen behind, it will never
  bring that clone up to date itself — doing so discards whatever the clone currently holds, and
  that's your call, not something to decide on your behalf. It stops and hands you the exact
  command to run yourself instead.
- It will never call a reinstall successful just because the install commands ran without an
  error. It checks the installed copy's real version afterward, and if the version you expected
  isn't there, it says the reinstall did not work rather than reporting success.
