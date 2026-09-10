---
name: orc-todo
description: Use when the user explicitly asks to use orc-todo, or types /orc-todo, to see or change the backlog - listing open entries, reading one in full, adding or removing an entry, and creating or reordering the lanes that say which work runs in what order.
allowed-tools: Bash(python3 *)
---

# orc-todo

The command surface over the backlog and the lanes. Everything the lock and the allocator do
underneath stays invisible from here — this is the only part of v16 with a user in front of it.

Run every command as:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py <args>
```

`--cwd <path>` is a top-level option, before the subcommand, when the project is not the current
directory. It finds the project root the same way the rest of Orclab does; outside a git
repository, or in a project with no `BACKLOG.md`, it says so plainly and never creates one.

## Commands

| Command | What it does |
|---|---|
| `list` | Open entries, one line each, then lanes if any exist |
| `show <n>` | One entry in full |
| `add <resource> <title>` | Body is read from stdin; prints the allocated number |
| `remove <n>` | Delete a backlog entry; never renumbers |
| `lane list` | Every lane and what each is working on |
| `lane create <name> <items>` | `items` is comma-separated, e.g. `v13,v14` |
| `lane modify <name> <items>` | Replace a lane's item list — reorder, add, or drop |
| `lane delete <name>` | Remove a lane |
| `lane current <name> <item\|->` | Mark what a lane is working on; `-` clears it |
| `lock status` | Who holds the lock, if anyone |
| `lock clear` | Release the lock |

`<resource>` for `add` is `backlog` or `verification` — which file the entry belongs in.

## `add` takes its body on stdin, never as an argument

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py add backlog "a real finding" <<'EOF'
A genuine paragraph of context — why this matters, not just what it is.
EOF
```

A real entry is paragraphs, and shell quoting for multi-paragraph prose is how a stub gets
written instead of the real thing. An empty or whitespace-only body is refused outright.

This command is a front door to `backlog-discipline`'s rules, not a way around them. What
actually belongs in an entry — a genuine finding, not a placeholder, with the reasoning that
makes it worth keeping — is `backlog-discipline`'s call, not this skill's. When in doubt about
whether something is worth an entry, defer to that skill before writing one.

## `remove` never renumbers

Deleting an entry removes its section and nothing else. No other entry's number shifts, and the
deleted number is never reissued — the allocator's counter only ever moves forward. If a gap in
the numbering looks wrong, it isn't; it's the record of something that was once here.

## A lane item must have a real spec or plan

`lane create` and `lane modify` refuse an item with no matching file under
`docs/superpowers/specs` or `docs/superpowers/plans` (matched by name, e.g. `v13`) — the command
reports exactly which item is unspecced. An unspecced item is genuinely ambiguous: there is
nothing concrete yet to run.

When this happens: offer to write the spec first, then come back and ask which lane it belongs
in. Never invent a placeholder spec, and never drop the item from the lane request silently.

## Entries are written uncommitted, on purpose

`add` writes directly into the canonical `BACKLOG.md` (or `VERIFICATION.md`) and stops there —
it never runs `git commit`. Every agent reads the same canonical file, so the entry is visible
the moment it's written; nothing about correctness needs a commit. Committing here would also
mean running git in a checkout this command doesn't own, sweeping in whatever else is
uncommitted in that file as if it were part of the entry. Committing the entry is a separate,
deliberate step the user takes themselves.

## `lock clear` is for a lock you've decided is stale — never a reflex

`lock status` reports who holds it, its age, and whether that process is even still running.
Only clear a lock after actually looking at that and deciding it's stale — a dead PID, an
implausible age. A lock found when none was expected is a signal something is actually in
progress or crashed mid-write, and that's worth investigating before clearing it, not clearing on
sight because it's in the way.
