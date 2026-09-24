---
name: orc-reload
description: Use when the user explicitly asks to use orc-reload, or types /orc-reload, to reinstall the Claude Code plugin they are currently developing so a fresh session picks up their latest changes.
allowed-tools: Read, Bash(claude plugin *), Bash(ls *), Bash(git -C *), Bash(git status *), Bash(git status), Bash(git log *), Bash(git rev-parse *)
---

# orc-reload

Reinstalls the plugin in the current project so the next session runs your latest code. Built
because "I changed the plugin, why is it still running the old version" has a handful of genuinely
different causes that all present identically, and guessing between them wastes real time.

**One thing this cannot do, and no command can:** a reinstall never takes effect in a conversation
that is already running. Skills and commands load when a session starts. You will need a fresh
session afterward — say so plainly at the end, every time. Measured again in a cloud session on
2026-09-24: a marker appended to a loaded skill's body did not appear when that skill was invoked
seconds later, so the body is held from session start there too, not re-read from disk.

## Step 0: Find out whether there is anything to reinstall

Run `[ -n "$CLAUDE_CODE_REMOTE" ] && echo cloud`. If it prints `cloud`, **stop and use the cloud
path below instead of Steps 1-5.** Those steps navigate by `known_marketplaces.json`,
`installed_plugins.json` and a marketplace clone, and in Claude Code on the web none of those
exists or governs what loaded — measured across seven cloud sessions on 2026-09-23/24. Followed
there, Step 2 reports that the plugin "has never been registered as a marketplace on this machine"
and stops, while the plugin is loaded and running.

### The cloud path

Nothing is installed, so nothing can be reinstalled. A cloud session loads the plugin straight from
the checkout you are sitting in — through a SessionStart hook that links the checkout into the
container's own skills directory, or through a plugin enabled for the user's claude.ai account.
Say that plainly rather than reporting a failed reinstall.

Then answer the question they actually have, which is different here. A new cloud session is a
fresh clone **of the remote**, so what it runs is what has been *pushed* — not what is saved, and
not even what is committed. Locally, a directory-sourced install picks up an uncommitted working
tree; in the cloud that same work is invisible to the next session. Check both, and report both:

```
git status --short
git log --oneline @{u}..HEAD
```

- **Uncommitted changes** — name them, and say they will not be in the next session until committed
  and pushed.
- **Unpushed commits** — name how many and say the same.
- **Both clean** — say so, and that the next session will run exactly this commit.

Then tell them the remedy, which is not a reinstall: commit and push, then start a new cloud
session on this branch. If their changes were already pushed and a session still ran old code, that
is a real problem worth looking at rather than papering over with a reinstall — say so.

## Step 1: Confirm this is a plugin project

Read `.claude-plugin/plugin.json` in the current project. If it doesn't exist, tell the user this
project isn't a Claude Code plugin and stop — don't go looking for something to reinstall.

Note its `"name"` and `"version"`. That version is what a correct reinstall should land on.

## Step 2: Find how this plugin's marketplace is registered

Read `~/.claude/plugins/known_marketplaces.json`. Find the entry for this plugin's marketplace —
usually the one whose `installLocation` or `source.path` is this project's own directory. If
nothing there points at this project, say so plainly: the plugin has never been registered as a
marketplace on this machine, and the user needs to add it first
(`claude plugin marketplace add <path>`). Stop there rather than guessing a name.

Also read `~/.claude/plugins/installed_plugins.json` and note what version is currently installed,
so you can report the real before/after rather than assuming the reinstall changed anything.

The `source.source` field decides what happens next, and the two cases genuinely differ:

### `"directory"` — the source is the live working tree

Nothing to refresh. The marketplace reads the project directory directly, so whatever is committed
(or even uncommitted) there right now is what gets installed. Go straight to Step 3.

Worth telling the user if their working tree is dirty: a directory-sourced install picks up
uncommitted changes, which is usually what you want while developing, but it means "installed" and
"pushed" can quietly diverge.

### `"github"` — there is a cached clone, and it does NOT auto-refresh

This is the case that wastes an afternoon. The marketplace keeps its own clone under
`~/.claude/plugins/marketplaces/<name>`, and **uninstalling and reinstalling the plugin reuses that
clone as-is**. A stale clone silently caps the installed version at whatever commit it holds, and
every symptom points somewhere else.

Check whether the clone is behind:

```
git -C ~/.claude/plugins/marketplaces/<marketplace-name> fetch --quiet && git -C ~/.claude/plugins/marketplaces/<marketplace-name> status -sb
```

If it is behind, **stop and tell the user**, giving them the exact command to run themselves:

```
git -C ~/.claude/plugins/marketplaces/<marketplace-name> fetch && git -C ~/.claude/plugins/marketplaces/<marketplace-name> reset --hard origin/main
```

Do not run that yourself. `reset --hard` on a checkout is the user's call, not yours, and a
reinstall from a stale clone would look like it worked while installing the wrong code.

Also worth knowing for this case: a marketplace registered from a **private** GitHub repo cannot be
refreshed by `claude plugin marketplace update` at all — that path fetches through GitHub's API
with no credentials of its own and reports the manifest as missing rather than as inaccessible.
Registering by local path instead avoids the whole problem.

## Step 3: Reinstall

```
claude plugin uninstall <plugin-name>@<marketplace-name>
claude plugin install <plugin-name>@<marketplace-name>
```

Uninstall-then-install, not `update`: the Update path is unreliable here, and in Claude Desktop the
Update button is frequently greyed out entirely for a directory-sourced marketplace.

If the install fails with a schema complaint, read the error literally rather than assuming the
usual causes. One real example worth recognizing: `owner`/`author` in a manifest requires a `name`
string — dropping it in favour of `email` alone breaks every `marketplace add`/`update` call
afterward, and the downstream symptom ("plugin not found in marketplace") names neither the field
nor schema validation.

## Step 4: Verify it actually landed

```
ls ~/.claude/plugins/cache/<plugin-name>/<plugin-name>/
```

Confirm the version from Step 1 is now present. Report the real before-and-after versions. **If the
expected version isn't there, say the reinstall did not work** and stop — do not report success
because the commands exited cleanly. Older version directories sticking around alongside the new
one is normal and not a problem.

## Step 5: Tell them about the fresh session

End by stating plainly that this session is still running the old version and cannot see the new
one, and that they need to start a new session to use it. This is confirmed behavior on both the
CLI and Claude Desktop, not a precaution — a long-running session will keep reporting the old
version, or "Unknown command" for a newly added component, no matter how correct the install is.
