# Orclab v2: /orc-code Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single working `/orc-code` slash command to the Orclab plugin — a deterministic entry point for new-project, add-to-existing-project, and refactor/migrate work, wrapping `feature-dev` and `code-modernization` where applicable.

**Architecture:** One new command file, `commands/orc-code.md`, at the plugin root (matching the real layout of every command-bearing plugin examined during design). It contains: routing logic (literal `refactor` subcommand or classified intent from `$ARGUMENTS`), three flows (new-project, add-to-existing, refactor), a shared plugin-discovery procedure, and a minimal defaults table. Plugin metadata (`plugin.json`/`marketplace.json`) and `README.md` get small updates to reflect the new command; `VERIFICATION.md` gains new dogfood scenarios.

**Tech Stack:** Markdown (command content), JSON (plugin manifests). No code, no test framework — same as v1, this is natural-language instructions shaping Claude's own behavior. Verification is mechanical content checks (frontmatter validity, presence of required sections) plus a written dogfood script, not unit tests.

**Spec:** `docs/superpowers/specs/2026-09-05-orclab-v2-orc-code-command-design.md`

## Global Constraints

- Exactly one command in this pass: `/orc-code`. No other `/orc-*` commands.
- Routing never uses filesystem heuristics (directory emptiness, git history, manifest presence) — classification comes only from `$ARGUMENTS`/explicit questions.
- The Add-to-Existing and Refactor flows must tell the user plainly when they're using `feature-dev`'s or `code-modernization`'s own workflow — no obscuring whose work is being used.
- If `feature-dev` or `code-modernization` isn't installed when needed, tell the user plainly and offer to help install — never silently attempt a worse job without it.
- The Defaults Table contains exactly one entry (Java desktop → Java + Spring + JavaFX) — do not add speculative entries for stacks that aren't confirmed (see BACKLOG #4 for the deferred research).
- The New-Project Flow must not report completion until its build/test verification command actually passes.
- Commands, like skills, must not declare a `model:` frontmatter field (confirmed absent from every real command file examined during design).

---

## File Structure

```
orclab/
  commands/
    orc-code.md          (new)
  .claude-plugin/
    plugin.json           (modified: version bump, description update)
    marketplace.json       (modified: description update, both occurrences)
  README.md               (modified: mention the new command)
  VERIFICATION.md          (modified: new /orc-code scenarios)
```

---

### Task 1: The `/orc-code` command

**Files:**
- Create: `commands/orc-code.md`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `README.md`

**Interfaces:**
- Consumes: nothing (first task of this plan).
- Produces: a complete, installable `/orc-code` command. Task 2 (verification) depends on this file's exact section headings (`## New-Project Flow`, `## Add-to-Existing Flow`, `## Refactor Flow`, `## Plugin-Discovery Procedure`, `## Defaults Table`) existing verbatim, since its scenarios reference this command's real behavior.

- [ ] **Step 1: Write `commands/orc-code.md`**

```markdown
---
description: Start new project work, add a feature to an existing project, or refactor/migrate existing code — one command routing to the right flow, wrapping feature-dev and code-modernization where they apply.
argument-hint: [refactor] <description of what to build, add, or change>
---

# /orc-code

You are helping with code work via the `/orc-code` command. Your first job is routing to the
right flow below — do this before anything else.

## Step 0: Route

1. If invoked as `/orc-code refactor ...`, OR if `$ARGUMENTS` itself clearly describes a
   language/version-migration intent (e.g. "change this Java project to do X," "migrate this to
   Kotlin," "upgrade from .NET Framework to .NET 8," "port this to Python") — go to **Refactor
   Flow** below. Recognize this from reading `$ARGUMENTS` the same way you'd recognize which skill
   applies to a request — don't require the literal word "refactor" if the intent is already
   clear.
2. Otherwise, if it isn't already obvious from `$ARGUMENTS` whether this is new work or existing
   work, ask exactly one question: "Starting something new, or working on an existing project?"
   - "New" → **New-Project Flow**
   - "Existing" → **Add-to-Existing Flow**

Never guess this from the filesystem (an empty directory, presence of a git history, manifest
files, etc.) — always resolve it from what was typed or by asking directly.

## New-Project Flow

Ask these questions **one at a time**, waiting for each answer before asking the next. Skip any
question `$ARGUMENTS` already answered.

1. **Language**: "What language would you like to use?"
2. **Project name**: "What would you like to name the project?"
3. **Project type/platform**: "What kind of project is this — desktop, web, mobile, CLI, or
   something else?" Once you have language + type, check the Defaults Table below:
   - If a default exists for this combination, propose it: "For a [type] [language] app, I'd
     default to [stack] — sound good, or would you like something different?" Use whatever they
     confirm or substitute.
   - If no default exists, don't propose one — just note there's no default yet and ask what
     stack/framework they want.
4. **Starting point**: "Would you like a minimal example, a basic scaffold with common features,
   or something specific — describe your use case."

Once all four are answered:

5. **Scaffold**: create the project directory (if it doesn't already exist), initialize the
   language's standard tooling (e.g. `npm init`, `cargo init`, a Maven/Gradle project layout,
   `python -m venv` + `pyproject.toml`, whatever is standard for the confirmed language), and
   write starter files reflecting the confirmed stack and starting point.
6. **Verify**: run the stack's standard build/test command (e.g. `mvn compile`, `npm run build`,
   `cargo build`, `python -m py_compile` or the project's own test command) and confirm it exits
   cleanly. If it fails, fix the issue before continuing — do not report this flow as complete
   until the verification command actually passes.
7. **Report**: tell the user what was created, the exact command to run it, and any relevant next
   steps.

## Add-to-Existing Flow

This flow wraps the `feature-dev` plugin's own real workflow rather than reimplementing it.

1. Run the **Plugin-Discovery Procedure** below, searching for a plugin named `feature-dev`.
2. **If not found**: tell the user plainly: "This needs the `feature-dev` plugin, which isn't
   currently installed." Offer to help — use the `SearchPlugins` tool with keywords like
   `["feature development", "guided implementation"]` if available, or point at the marketplace
   install flow (`/plugin marketplace add ...` / `/plugin install ...`) if you know where it's
   published. Stop here; do not attempt this flow without it.
3. **If found**: Read the `commands/feature-dev.md` file inside the located plugin's directory in
   full, and follow its instructions directly, exactly as if the user had invoked
   `/feature-dev $ARGUMENTS` themselves. Tell the user plainly that you're using feature-dev's own
   guided workflow for this — don't obscure that this is someone else's real, existing work.

## Refactor Flow

This flow wraps the `code-modernization` plugin's own real workflow rather than reimplementing it.

1. Run the **Plugin-Discovery Procedure** below, searching for a plugin named `code-modernization`.
2. **If not found**: same missing-dependency handling as the Add-to-Existing Flow above, naming
   `code-modernization` instead.
3. **If found**:
   - Check whether `commands/modernize-status.md` exists in the located plugin directory. If it
     does, read and follow it first to check whether prior modernization work already exists for
     this project.
   - If `modernize-status` reports existing progress, continue from whatever step it indicates.
   - If `modernize-status` reports no prior work, isn't available, or doesn't exist in this
     installed version, start from `commands/modernize-preflight.md` instead.
   - Read whichever command file applies in full, and follow its instructions directly, exactly as
     if the user had invoked that command themselves with the same `$ARGUMENTS`. Tell the user
     plainly that you're using code-modernization's own workflow for this.

## Plugin-Discovery Procedure

Given a plugin name to find (e.g. `feature-dev`, `code-modernization`):

1. Search for every `.claude-plugin/plugin.json` file under both of these roots:
   - `~/.claude/plugins/marketplaces/`
   - `~/.claude/plugins/cache/`
2. For each one found, read it and check its `"name"` field.
3. The first one whose `"name"` matches the target plugin exactly is the match — its containing
   directory (the directory holding that `.claude-plugin/` folder) is the plugin's root. Use that
   root to locate the plugin's `commands/*.md` files.
4. If no match is found under either root, the plugin is not installed.

Real install layouts you may encounter (all three have been directly observed): a versioned cache
path (`.../cache/<marketplace>/<plugin-name>/<version>/`), a nested marketplace path
(`.../marketplaces/<marketplace>/plugins/<plugin-name>/`), and a self-hosted single-plugin repo at
a marketplace's own root (`.../marketplaces/<plugin-name>/`). Search broadly enough to find all
three — don't assume only one shape.

## Defaults Table

| Language | Type    | Default stack              |
|----------|---------|-----------------------------|
| Java     | Desktop | Java + Spring + JavaFX      |

This table currently has exactly one entry. Do not invent additional defaults beyond what's listed
here — if a combination isn't in this table, ask directly in the New-Project Flow's step 3
instead of guessing. Add rows here only once a real, confirmed preference exists.
```

- [ ] **Step 2: Verify frontmatter and required sections**

```bash
python3 -c "
import re
text = open('commands/orc-code.md').read()
m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
assert m, 'no frontmatter block found'
assert 'description:' in m.group(1)
assert 'argument-hint:' in m.group(1)
assert 'model:' not in m.group(1)
for section in ['## Step 0: Route', '## New-Project Flow', '## Add-to-Existing Flow', '## Refactor Flow', '## Plugin-Discovery Procedure', '## Defaults Table']:
    assert section in text, f'missing section: {section}'
print('OK: commands/orc-code.md frontmatter and all required sections present')
"
```
Expected: `OK: commands/orc-code.md frontmatter and all required sections present`

- [ ] **Step 3: Self-review against the spec's rules**

Confirm each of these is explicitly present in the file just written:
- [ ] Routing recognizes refactor intent from `$ARGUMENTS` text, not just the literal `refactor` keyword
- [ ] Routing never mentions checking the filesystem to classify new-vs-existing
- [ ] New-Project Flow states it must not report completion until the verify step passes
- [ ] Add-to-Existing and Refactor flows both state they tell the user plainly which underlying plugin's workflow is being used
- [ ] Both wrapping flows state the missing-dependency handling (tell the user, offer to help install) if the target plugin isn't found
- [ ] Defaults Table has exactly one row

- [ ] **Step 4: Update `.claude-plugin/plugin.json`**

Replace the entire file content with:

```json
{
  "name": "orclab",
  "description": "Project-discipline skills and commands distilled from real practice: backlog tracking, release checklists, live-environment registries, and a deterministic /orc-code entry point for new-project, existing-project, and refactor work.",
  "version": "0.2.0",
  "author": {
    "name": "direflail"
  }
}
```

- [ ] **Step 5: Update `.claude-plugin/marketplace.json`**

Replace the entire file content with:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "orclab",
  "description": "Project-discipline skills and commands distilled from real practice: backlog tracking, release checklists, live-environment registries, and a deterministic /orc-code entry point for new-project, existing-project, and refactor work.",
  "owner": {
    "name": "direflail"
  },
  "plugins": [
    {
      "name": "orclab",
      "description": "Project-discipline skills and commands distilled from real practice: backlog tracking, release checklists, live-environment registries, and a deterministic /orc-code entry point for new-project, existing-project, and refactor work.",
      "source": "./"
    }
  ]
}
```

- [ ] **Step 6: Verify both manifest files are still valid JSON and consistent**

```bash
python3 -c "
import json
p = json.load(open('.claude-plugin/plugin.json'))
m = json.load(open('.claude-plugin/marketplace.json'))
assert p['name'] == m['plugins'][0]['name'] == 'orclab'
assert p['version'] == '0.2.0'
assert m['plugins'][0]['source'] == './'
print('OK: plugin.json/marketplace.json valid, version bumped, still consistent')
"
```
Expected: `OK: plugin.json/marketplace.json valid, version bumped, still consistent`

- [ ] **Step 7: Update `README.md`**

Find:
```
## Skills

- **backlog-discipline** — maintain a single flat `BACKLOG.md` of real, open findings, with
  permanent entry numbers and resolution history layered on top of (never replacing) the original
  diagnostic record.
- **release-checklist** — maintain a numbered, dependency-ordered `RELEASING.md`, cross-referenced
  against whatever CI already automates.
- **environment-registry** — register real, live test environments (VMs, containers, staging
  servers, devices) as Claude memory, never as a git-tracked file, never storing credentials.
```

Replace with:
```
## Skills

- **backlog-discipline** — maintain a single flat `BACKLOG.md` of real, open findings, with
  permanent entry numbers and resolution history layered on top of (never replacing) the original
  diagnostic record.
- **release-checklist** — maintain a numbered, dependency-ordered `RELEASING.md`, cross-referenced
  against whatever CI already automates.
- **environment-registry** — register real, live test environments (VMs, containers, staging
  servers, devices) as Claude memory, never as a git-tracked file, never storing credentials.

## Commands

- **/orc-code** — start a new project, add to an existing one, or refactor/migrate existing code.
  Routes deterministically to one of three flows, wrapping the `feature-dev` and
  `code-modernization` plugins where applicable rather than reimplementing their work.
```

Find:
```
## Status

v1 — process core. See `docs/superpowers/specs/` for the design history and `BACKLOG.md` for
what's deliberately deferred (a `/orc-*` command layer is tracked as #1). See `VERIFICATION.md`
for the dogfood script that confirms these skills actually work once installed in a real project.
```

Replace with:
```
## Status

v1 (process core) + v2 (`/orc-code`) shipped. See `docs/superpowers/specs/` for the design history
and `BACKLOG.md` for what's deliberately deferred (real per-stack defaults research is #4,
`/orc-data` is #5, hook-based enforcement is #3). See `VERIFICATION.md` for the dogfood script
that confirms everything actually works once installed in a real project.
```

- [ ] **Step 8: Commit**

```bash
git add commands/orc-code.md .claude-plugin/plugin.json .claude-plugin/marketplace.json README.md
git commit -m "Add /orc-code command: new-project, add-to-existing, and refactor flows"
```

---

### Task 2: Dogfood verification scenarios

**Files:**
- Modify: `VERIFICATION.md`

**Interfaces:**
- Consumes: the completed `commands/orc-code.md` from Task 1 (references its exact section names and behavior).
- Produces: a complete verification script covering both v1 and v2. No later task depends on this.

- [ ] **Step 1: Update `VERIFICATION.md`'s title and add new scenarios**

Find:
```
# Orclab v1 verification script

Run these scenarios in a **fresh Claude Code session, in the Orcshot project directory**
(`~/projects/orcshot`), after installing Orclab per `README.md`. Orcshot already has a real
`BACKLOG.md` and a real `RELEASING.md` in exactly the shape these skills model from, making it a
better verification target than a throwaway project.
```

Replace with:
```
# Orclab verification script

Run these scenarios in a **fresh Claude Code session** after installing/reinstalling Orclab per
`README.md`. Scenarios 1-4 (v1's skills) run in the Orcshot project directory (`~/projects/orcshot`)
— it already has a real `BACKLOG.md` and a real `RELEASING.md` in exactly the shape these skills
model from, making it a better verification target than a throwaway project. Scenarios 5-8
(`/orc-code`) specify their own target directory per scenario, since they cover different
situations (empty scratch dir, existing project, etc.).
```

Find:
```
## Recording the result
```

Replace with:
```
## Scenario 5: /orc-code new-project flow, no default exists

1. In a throwaway empty scratch directory, run `/orc-code` and say you want to start something
   new, in Python, as a CLI tool.
2. **Expected:** since no Python default exists in the Defaults Table, Claude asks directly what
   stack/framework you want rather than proposing anything.
3. Answer with a simple choice (e.g. plain stdlib, no framework) and let it scaffold.
4. **Expected:** a real project directory is created, and Claude runs a real verification command
   (e.g. `python -m py_compile` on the created file, or an equivalent check) and reports it passed
   before declaring the task done.

## Scenario 6: /orc-code new-project flow, a default exists

1. In a throwaway empty scratch directory, run `/orc-code` and say you want to start something
   new, in Java, as a desktop app.
2. **Expected:** Claude proposes "Java + Spring + JavaFX" specifically (the one confirmed Defaults
   Table entry), and lets you confirm or override it.
3. Override it with a different stack (e.g. plain Swing, no Spring) and confirm Claude proceeds
   with your override, not the proposed default.

## Scenario 7: /orc-code add-to-existing flow

1. In an existing project (e.g. Orcshot itself), run `/orc-code` and describe a small, real
   addition you'd want made, without saying "new" or "existing" explicitly if possible — see
   whether Claude asks the routing question or infers it correctly from context.
2. **Expected:** if the `feature-dev` plugin is installed, Claude states plainly that it's using
   feature-dev's own workflow, and that workflow's real behavior (codebase exploration, clarifying
   questions before implementation) is visible. If `feature-dev` is NOT installed, Claude states
   plainly that this flow needs it and offers to help install it, rather than attempting the
   feature ad hoc.

## Scenario 8: /orc-code refactor flow, both invocation forms

1. In an existing project with a clear single language (e.g. a small Java or Python file), run
   `/orc-code refactor` explicitly, describing a version/language migration.
2. **Expected:** Claude states plainly it's using `code-modernization`'s workflow (if installed) or
   states the missing-dependency message (if not).
3. Separately, run bare `/orc-code migrate this to a different language` (no literal "refactor"
   keyword) describing a similarly clear migration intent.
4. **Expected:** Claude routes to the same Refactor Flow without needing the literal keyword,
   demonstrating the intent-classification routing from Step 0 of `commands/orc-code.md`.

## Recording the result
```

- [ ] **Step 2: Commit**

```bash
git add VERIFICATION.md
git commit -m "Add /orc-code dogfood scenarios to verification script"
```

---

## Self-Review Notes (from writing this plan)

- **Spec coverage:** routing logic, all three flows, plugin-discovery procedure, defaults table,
  missing-dependency handling, and transparency requirements are all covered in Task 1's command
  content. Manifest/README updates covered. Verification scenarios cover both new-project branches
  (default exists / doesn't), both routing paths (question-asked / inferred-from-text), and both
  wrapping flows' installed/not-installed cases. Out-of-scope items (BACKLOG #3/#4/#5) correctly
  absent from this plan.
- **Placeholder scan:** no TBD/TODO; every content block is complete, not a stub.
- **Consistency check:** the command's own section headings match exactly what Task 2's scenarios
  and this plan's own Global Constraints reference (`## New-Project Flow`, `## Add-to-Existing
  Flow`, `## Refactor Flow`, `## Plugin-Discovery Procedure`, `## Defaults Table`). Plugin names
  (`feature-dev`, `code-modernization`) are spelled identically everywhere they appear. Version
  bump (`0.2.0`) is consistent between `plugin.json` and the verification step's assertion.
