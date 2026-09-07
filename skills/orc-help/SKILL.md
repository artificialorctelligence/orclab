---
name: orc-help
description: Use when the user explicitly asks to use orc-help, or types /orc-help, to see Orclab's own running version and a synopsis of its available commands.
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
  working copy, not an installed one, since no installed copy was found. The current working
  directory is the plugin root for Step 3 in this case. In project context with no match, say
  plainly that Orclab isn't installed as a plugin here and its version can't be determined, and
  **stop — do not proceed to Step 3**, since there is no discovered root to list commands from.

## Step 3: List available commands

(Skip this step entirely if Step 2 ended in the project-context/no-match case — it already told
you to stop.) In the plugin root established by Step 2 — the discovered installed root, or the
current working directory fallback in core context — enumerate every `skills/orc*/SKILL.md`.
Note the glob has **no hyphen**: `orc*` catches `skills/orc/SKILL.md` itself as well as every
`skills/orc-*`. Orclab's discipline skills (`backlog-discipline`, `secret-hygiene` and the rest)
carry no `orc` prefix, so the same glob correctly excludes them. Read each component's
description from its own `description` frontmatter field. There is no second source to merge:
every component is a skill, and `commands/` no longer exists. Present one line per command name,
in this shape:

```
Orclab vX.Y.Z (running in <core|project> context)

Commands:
  /orc-code     — <real description field from orc-code.md>
  /orc-version  — <real description field from orc-version.md>
  /orc-help     — <real description field from orc-help.md>
  /orc          — <real description field from orc.md>
  /orc-git      — <real description field from orc-git.md>
  /orc-publish  — <real description field from skills/orc-publish/SKILL.md's frontmatter>
```

Always read the REAL `description` field from each real command/skill file found in this step —
the example above shows the format, not literal text to reuse. If a future command or skill-only
component is added, it appears here automatically because this step lists whatever files actually
exist, rather than a hardcoded list.
