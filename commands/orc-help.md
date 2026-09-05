---
description: Show Orclab's own running version and a synopsis of its available commands, noting whether you're currently in Orclab's own repo or a project that has it installed.
---

# /orc-help

## Step 1: Determine context

Check whether the CURRENT WORKING DIRECTORY contains `.claude-plugin/plugin.json` with
`"name": "orclab"`. If it does, you're inside Orclab's own repo — this is **core** context
(developing Orclab itself). If it doesn't, you're in some other project that has Orclab installed
as a plugin — this is **project** context. This checks where you currently are, not where
Orclab's installed plugin files happen to live — those can be different places.

## Step 2: Find Orclab's own installed files and report its version

Run the same discovery approach `/orc-code` uses for finding other plugins, applied to find
Orclab itself: search for every `.claude-plugin/plugin.json` file under
`~/.claude/plugins/marketplaces/` and `~/.claude/plugins/cache/`, and find the one whose `"name"`
field is exactly `orclab`. Its containing directory is Orclab's own installed root.

- **If a match is found**: read that file's `"version"` field and report it as Orclab's running
  version.
- **If no match is found**: Orclab isn't currently registered as a marketplace or installed as a
  plugin anywhere on this machine. In core context (Step 1), fall back to the current working
  directory's own `.claude-plugin/plugin.json` (the same file Step 1 already read to determine
  context) and report its version as the working copy's version — note plainly that this is the
  working copy, not an installed one, since no installed copy was found. In project context with
  no match, say plainly that Orclab isn't installed as a plugin here and its version can't be
  determined.

## Step 3: List available commands

In the discovered plugin root from Step 2, list every file under `commands/*.md`. For each one,
read its `description` frontmatter field. Present a one-line synopsis per command, in this shape:

```
Orclab vX.Y.Z (running in <core|project> context)

Commands:
  /orc-code     — <real description field from orc-code.md>
  /orc-version  — <real description field from orc-version.md>
  /orc-help     — <real description field from orc-help.md>
  /orc          — <real description field from orc.md>
```

Always read the REAL `description` field from each real command file found in Step 3 — the
example above shows the format, not literal text to reuse. If a future command is added, it
appears here automatically because this step lists whatever `commands/*.md` files actually exist,
rather than a hardcoded list.
