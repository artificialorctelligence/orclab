---
name: orc-publish
description: Use when the user explicitly asks to use orc-publish, or types /orc-publish, to push a project's built artifacts to their real distribution destinations (a PPA, the Snap Store, Flathub, npm, etc.) as configured in the project's own .orclab/publish/channels.yaml and distro.yaml.
allowed-tools: Bash(python3 *)
---

# orc-publish

Publishes a project's built artifacts to whatever real destinations it has configured in its own
`.orclab/publish/channels.yaml` (and, for a distro-scoped query, `.orclab/publish/distro.yaml`).
Orclab itself ships no real channel/distro content for any project — only a project that has
populated these two files can actually publish anything.

## Step 0: Confirm the project is actually set up for this

Run:

```
python3 -c "import yaml" && ls .orclab/publish/channels.yaml
```

If `import yaml` fails, tell the user plainly that `PyYAML` isn't installed
(`pip install pyyaml`) and stop. If `channels.yaml` doesn't exist, tell the user this project has
no publish configuration yet and stop — never invent one.

## Step 1: Read `$ARGUMENTS`

- If `$ARGUMENTS` contains `--for <path>`, this is a read-only query — skip straight to running
  the script with `--for <path>` and report its output. Nothing to confirm; nothing executes.
- Otherwise, the rest of `$ARGUMENTS` are selection tokens (dotted paths, optionally
  `!`-prefixed to exclude). Pass them through to the script exactly as given.

## Step 2: Always resolve in dry-run mode first

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py <selection tokens> --dry-run
```

Show the user the exact list this prints — every leaf and its real action, verbatim, not
paraphrased. This is the safety gate. **Never skip straight to execution**, even if the request
sounded confident ("just publish everything," "ship it all").

## Step 3: Get an explicit go-ahead for that specific list

Ask the user to confirm the list from Step 2. A vague "sounds good" earlier in the conversation,
about something else, doesn't count — wait for a clear yes to *this* resolved list.

## Step 4: Execute for real

Once confirmed, run the identical command without `--dry-run`:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py <same selection tokens>
```

Report the exact summary it prints, per leaf: success, failed (with the real error text), or not
attempted. Never paraphrase a failure away, and never claim success for a leaf the summary
doesn't confirm succeeded.

## Notes

- `--for <distro-path>` reporting "no channel set" is normal, not an error — report it as "known
  target, no channel wired yet."
- A selection token that doesn't resolve, or resolves ambiguously, is reported by the script as an
  `error:` line on stderr with a non-zero exit — relay that message plainly rather than guessing
  what the user meant.
