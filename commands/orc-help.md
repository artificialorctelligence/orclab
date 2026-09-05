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
field is exactly `orclab`. Its containing directory is Orclab's own installed root. Read that
file's `"version"` field.

If you're in core context (Step 1), this discovered location IS the current working directory —
report its version directly. If you're in project context, this discovered location is wherever
Orclab actually got installed from (which may differ from the current directory) — report its
version the same way.

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
