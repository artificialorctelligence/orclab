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

## Step 0: Confirm PyYAML is available

Run:

```
python3 -c "import yaml"
```

If this fails, tell the user plainly that `PyYAML` isn't installed (`pip install pyyaml`) and
stop.

## Step 1: Read `$ARGUMENTS` and confirm the right tree file exists

- If `$ARGUMENTS` contains `--for <path>`, this is a read-only query against the **distro** tree
  only — it never needs `channels.yaml`. Confirm `.orclab/publish/distro.yaml` exists:
  ```
  python3 -c "import pathlib,sys; sys.exit(0 if pathlib.Path('.orclab/publish/distro.yaml').exists() else 1)"
  ```
  If it doesn't, tell the user this project has no distro configuration yet and stop. Otherwise
  skip straight to running the script with `--for <path>` and report its output — nothing to
  confirm, nothing executes.
- Otherwise, confirm `.orclab/publish/channels.yaml` exists:
  ```
  python3 -c "import pathlib,sys; sys.exit(0 if pathlib.Path('.orclab/publish/channels.yaml').exists() else 1)"
  ```
  If it doesn't, tell the user this project has no publish configuration yet and stop — never
  invent one. Otherwise, the rest of `$ARGUMENTS` are selection tokens (dotted paths, optionally
  `!`-prefixed to exclude). Pass them through to the script exactly as given.

## Step 2: Always resolve in dry-run mode first

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py <selection tokens> --dry-run
```

Show the user the exact list this prints — every leaf, its real action, and any
`requirement:`/`issue:` lines beneath it, verbatim, not paraphrased. A leaf's requirements/issues
often name something the user needs to do *before* confirming (e.g. unlocking a signing key) —
don't let those scroll by unread. This is the safety gate. **Never skip straight to execution**,
even if the request sounded confident ("just publish everything," "ship it all").

## Step 3: Get an explicit go-ahead for that specific list

Ask the user to confirm the list from Step 2. A vague "sounds good" earlier in the conversation,
about something else, doesn't count — wait for a clear yes to *this* resolved list.

## Step 4: Execute for real

Once confirmed, run the identical command without `--dry-run`:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py <same selection tokens>
```

Report the exact summary it prints, per leaf: success (with the real output, if any), failed
(with the real error text), or not attempted. Never paraphrase a failure away, and never claim
success for a leaf the summary doesn't confirm succeeded.

## Notes

- `--for <distro-path>` reporting "no channel set (known target, not yet actionable)" is normal,
  not an error — relay that exact string, don't paraphrase it.
- A selection token that doesn't resolve, or resolves ambiguously, is reported by the script as an
  `error:` line on stderr with a non-zero exit — relay that message plainly rather than guessing
  what the user meant.
- A missing or malformed `channels.yaml`/`distro.yaml` (past Step 1's existence check — e.g. bad
  YAML syntax) is reported the same way: an `error:` line on stderr. Relay it plainly.
