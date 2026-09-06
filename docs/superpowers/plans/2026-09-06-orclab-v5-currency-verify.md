# Orclab v5: currency-discipline and verify-before-asserting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two new core skills to Orclab — `currency-discipline` (verify a chosen technology/version/approach is actually current) and `verify-before-asserting` (verify a challenged claim instead of defending it) — and bump Orclab to 0.5.0 with a real `CHANGELOG.md` entry.

**Architecture:** Two new skill directories, each with a `SKILL.md` and a `references/` worked example, following the exact file shape of v1's three skills. No commands, no `.orclab/` interaction, no coupling to any existing skill's internals beyond `verify-before-asserting`'s explicit cross-reference to superpowers' `systematic-debugging`.

**Tech Stack:** Markdown (skill content), JSON (plugin manifests). No code, no test framework — same as v1-v4, this is natural-language instructions shaping Claude's own behavior.

**Spec:** `docs/superpowers/specs/2026-09-06-orclab-v5-currency-verify-design.md`

## Global Constraints

- `currency-discipline` must name real, concrete verification mechanisms per ecosystem (`npm view`, PyPI's JSON API, crates.io, Maven Central, `go list -m -versions`) — never just "check if it's current" without a real command or endpoint.
- `verify-before-asserting` must explicitly cross-reference superpowers' `systematic-debugging` skill (its "Signals You're Doing It Wrong" table and the Phase 1 vs. Phase 4 test-usage distinction) as reinforcement, not duplication — it must not restate that skill's four-phase process itself.
- Neither skill's real motivating case (the deprecated-library rework, the Wayland claim) should be sanitized into something generic — both should be stated plainly, matching how the spec itself states them.
- Neither `SKILL.md` may declare a `model:` frontmatter field.
- Version bumps to exactly `0.5.0` in both manifests, matching the `CHANGELOG.md` entry and README.
- Nothing in this plan touches the check-in-cadence point — that's explicitly out of scope, captured as a personal memory instead (already done, outside this plan).

---

## File Structure

```
orclab/
  skills/
    currency-discipline/
      SKILL.md              (new)
      references/example-check.md   (new)
    verify-before-asserting/
      SKILL.md              (new)
      references/example-verification.md   (new)
  .claude-plugin/
    plugin.json               (modified: version bump to 0.5.0)
    marketplace.json           (modified: version bump to 0.5.0)
  CHANGELOG.md                 (modified: new entry)
  README.md                    (modified: mention both new skills)
  VERIFICATION.md              (modified: new scenarios)
```

---

### Task 1: `currency-discipline` skill

**Files:**
- Create: `skills/currency-discipline/SKILL.md`
- Create: `skills/currency-discipline/references/example-check.md`

**Interfaces:**
- Consumes: nothing (first task of this plan).
- Produces: a complete, independently-reviewable skill. No other task depends on its internal content.

- [ ] **Step 1: Write `skills/currency-discipline/SKILL.md`**

```markdown
---
name: currency-discipline
description: Use when choosing a dependency, library version, framework, or technical approach, or when research surfaces an answer to a technical question. Checks against the real, currently-live source rather than assuming a remembered or found answer is still current.
---

# Currency Discipline

Technology moves. A library version, a "best practice," or a platform capability that was true
two years ago may not be true now. This skill exists because trusting a stale answer without
checking caused real, avoidable rework on a real project — extremely old, already-deprecated
library versions got used, which later forced refactoring that wouldn't have been needed with a
current choice from the start.

## When to apply

- Choosing a dependency, library version, framework, or technical approach for a project.
- When research (a search, documentation, or recalled/trained knowledge) surfaces an answer to a
  technical question you're about to rely on.

## Rules

- **Default to the current stable version** of any technology involved, unless explicitly told
  otherwise. Don't default to "whatever version a found example happens to use" or "whatever's
  remembered from training" without checking.
- **Follow current, modern standards and practices** for the relevant ecosystem — an idiom or
  pattern that was correct a few years ago may no longer be how the ecosystem actually does things
  now.
- **Check the age of research before trusting it.** An old or undated source is a real risk
  factor, not neutral information, especially in a fast-moving ecosystem.
- **Verify against the real, currently-live source** when unsure — never assume the first answer
  found represents current best practice just because it was easy to find.

## Concrete verification mechanisms

This is the actual "how," not just "check if it's current":

**Library/package version** — query the real package registry directly, not a search engine's
index (which can lag) or recalled/trained knowledge (which has a hard cutoff):
- npm: `npm view <package> version`
- Python: `pip index versions <package>`, or PyPI's JSON API at
  `https://pypi.org/pypi/<package>/json`
- Rust: crates.io's API, or `cargo search <package>`
- Java: Maven Central's search API
- Go: `go list -m -versions <module>`

If the relevant package manager isn't installed locally, fetch the registry's real API endpoint
directly instead — it works regardless of local tooling.

**Language/runtime "current stable" status** — check the language's own official release page
directly, cross-checked against a real, well-known lifecycle-tracking resource such as
endoflife.date. Verify the resource itself is still live and accurate at time of use — don't
assume from memory that a reference site's content is current.

**Evaluating whether a found answer is stale** — check the source's own stated date where visible;
treat an undated answer, or one that reads like it predates a known ecosystem shift, as
higher-risk and worth a second, live check rather than silently presented as current fact.

## Relationship to superpowers

This skill doesn't replace any existing superpowers skill — nothing in the generic
brainstorm → spec → plan → build → verify → merge cycle covers checking whether a chosen
technology or a found answer is actually current. This skill fills that specific gap.

## What NOT to do

- Don't cite a library version or best practice from memory without checking it's still current,
  when currency is easy to verify and materially affects the decision.
- Don't treat "this is what I remember" and "this is what's currently true" as the same thing.
- Don't skip verification because a found answer looks confident or well-written — confidence and
  currency are unrelated.
```

- [ ] **Step 2: Write `skills/currency-discipline/references/example-check.md`**

```markdown
# Worked example: checking currency before committing to a choice

Adapted from a real lesson: a project ended up on extremely old, already-deprecated library
versions, discovered only once those versions started blocking new feature work — forcing a
refactor that a current choice from the start would have avoided entirely.

## Bad: trusting a remembered or found version without checking

> "Let's use `some-framework` version 2.x — that's the version I've seen most often."

No check was made. If the ecosystem has since moved to 4.x with 2.x deprecated, this locks the
project onto a version that may already be unsupported before the first commit lands.

## Good: verifying against the real, current source

> "Checking the actual current version before committing: `npm view some-framework version`
> returns `4.2.1`. The docs I found describing the 2.x API are from three years ago and don't
> mention the 3.x/4.x migration — that's a real sign they're stale, not just old-but-still-true.
> Using 4.2.1, following its current migration guide instead of the outdated docs."

The difference isn't effort — it's one extra command, run before the decision instead of after
the rework becomes necessary.

## A platform-capability version of the same discipline

> "Assumed Wayland doesn't support `<capability>` based on general familiarity with the platform.
> Before building around that assumption, checking the current Wayland protocol docs and testing
> directly on a real, current Wayland session — capabilities change release to release, and a
> remembered limitation from an older version may no longer hold."
```

- [ ] **Step 3: Verify frontmatter and required sections**

```bash
python3 -c "
import re
text = open('skills/currency-discipline/SKILL.md').read()
m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
assert m, 'no frontmatter block found'
assert 'name: currency-discipline' in m.group(1)
assert 'description:' in m.group(1)
assert 'model:' not in m.group(1)
for section in ['## When to apply', '## Rules', '## Concrete verification mechanisms', '## Relationship to superpowers', '## What NOT to do']:
    assert section in text, f'missing section: {section}'
print('OK: currency-discipline SKILL.md frontmatter and all required sections present')
"
```
Expected: `OK: currency-discipline SKILL.md frontmatter and all required sections present`

- [ ] **Step 4: Self-review against the spec's rules**

Confirm each of these is explicitly present:
- [ ] States real, concrete verification commands per ecosystem (npm, pip/PyPI, cargo/crates.io, Maven Central, go list) — not just "check if current"
- [ ] States checking a language/runtime's own official release page plus a lifecycle-tracking resource
- [ ] States checking a found answer's age/date before trusting it
- [ ] States the real motivating case (deprecated library versions causing rework) plainly, not sanitized
- [ ] Includes the Wayland-style platform-capability example in the reference file

- [ ] **Step 5: Commit**

```bash
git add skills/currency-discipline
git commit -m "Add currency-discipline skill"
```

---

### Task 2: `verify-before-asserting` skill

**Files:**
- Create: `skills/verify-before-asserting/SKILL.md`
- Create: `skills/verify-before-asserting/references/example-verification.md`

**Interfaces:**
- Consumes: nothing new from Task 1 (independent skill).
- Produces: a complete, independently-reviewable skill.

- [ ] **Step 1: Write `skills/verify-before-asserting/SKILL.md`**

```markdown
---
name: verify-before-asserting
description: Use when a factual or technical claim you made gets challenged, or when something turns out surprising - a platform, tool, or library not behaving as assumed. Verifies the real, current behavior instead of restating or defending the original claim.
---

# Verify Before Asserting

The failure mode this skill exists to close off isn't being wrong once — it's treating an
unverified claim as settled, and then defending it against a correct challenge instead of
checking. That's a worse failure than the original mistake, because it actively resists
correction.

## When to apply

- A factual or technical claim you made gets challenged or questioned.
- Something turns out surprising — a platform, tool, or library doesn't behave the way you
  assumed it would.

## Rules

- **The correct response to a challenge is to verify it** — check current documentation, test the
  actual behavior live, or re-derive the answer — never to restate or argue the original position
  more firmly without checking.
- **Surprise at being wrong is itself a signal to verify**, not a feeling to reason away or
  explain around.
- **This applies with extra force to platform and ecosystem capabilities that genuinely shift over
  time** (what a windowing system, OS version, or library currently supports) — verify the real,
  current behavior before designing around a remembered or assumed capability.

## Relationship to superpowers' `systematic-debugging`

This skill reinforces that skill, it doesn't duplicate or replace it. `systematic-debugging`
already has a "your human partner's Signals You're Doing It Wrong" table, and entries like
"'We're stuck?' (frustrated) - Your approach isn't working" and "Stop guessing" describe exactly
what a phrase like "take a step back" signals in different words. Any phrasing of that signal
means the same thing: STOP, return to Phase 1, verify rather than defend.

This skill also reinforces one specific technique that skill already contains but frames
narrowly: writing a test to *localize* where a bug's root cause lives is valid and valuable during
Phase 1's evidence-gathering — not only as the Phase 4 pre-fix formality that skill's own text
emphasizes. Writing tests progressively closer to the actual failure point is itself a
verification technique, not just a confirmation step for a fix you already believe is right.

## What NOT to do

- Don't restate a challenged claim more firmly instead of checking it.
- Don't treat "I'm surprised this is wrong" as a reason to look for a way the original claim could
  still be right — treat it as a reason to check.
- Don't wait for repeated pushback before verifying — the first challenge is the signal, not the
  third.
```

- [ ] **Step 2: Write `skills/verify-before-asserting/references/example-verification.md`**

```markdown
# Worked example: verifying a challenged claim instead of defending it

Adapted from a real lesson: a claim about a platform's capabilities was asserted confidently, then
defended against a direct, correct challenge instead of checked — costing real time and trust that
a single verification step would have avoided.

## Bad: defending the original claim

> Claude: "Wayland doesn't support `<capability>` — that's a known platform limitation."
> User: "Are you sure? That seems surprising."
> Claude: "Yes, Wayland's compositor model doesn't allow that kind of access for security reasons.
> That's why we need to work around it."

No verification happened. The claim was restated with additional-sounding justification instead
of checked — surprise from the person raising it was treated as something to explain past, not a
reason to check.

## Good: verifying the challenged claim

> Claude: "Wayland doesn't support `<capability>` — that's a known platform limitation."
> User: "Are you sure? That seems surprising."
> Claude: "Let me actually check rather than go from memory — checking the current Wayland
> protocol docs and testing directly on a real session now."
> [checks, finds the capability is in fact supported via a specific protocol extension]
> Claude: "I was wrong — it is supported, via `<the real mechanism>`. Correcting course."

The second challenge from the user shouldn't be needed — the first one is the signal.

## The debugging version of the same discipline

> Direflail: "Take a step back. Figure out the point at which the problem presents itself, and
> write tests until you're able to determine the root cause."

This is the same "we're stuck" signal `systematic-debugging` already documents, just in different
words — the response is to return to Phase 1's evidence-gathering, using tests written at
successive points in the flow to narrow down exactly where the failure starts, rather than
attempting another fix without knowing why the previous ones didn't work.
```

- [ ] **Step 3: Verify frontmatter and required sections**

```bash
python3 -c "
import re
text = open('skills/verify-before-asserting/SKILL.md').read()
m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
assert m, 'no frontmatter block found'
assert 'name: verify-before-asserting' in m.group(1)
assert 'description:' in m.group(1)
assert 'model:' not in m.group(1)
for section in ['## When to apply', '## Rules', \"## Relationship to superpowers' \`systematic-debugging\`\", '## What NOT to do']:
    assert section in text, f'missing section: {section}'
print('OK: verify-before-asserting SKILL.md frontmatter and all required sections present')
"
```
Expected: `OK: verify-before-asserting SKILL.md frontmatter and all required sections present`

- [ ] **Step 4: Self-review against the spec's rules**

Confirm each of these is explicitly present:
- [ ] Explicitly cross-references `systematic-debugging`'s "Signals You're Doing It Wrong" table, not just debugging in general
- [ ] States the Phase 1 (localize) vs. Phase 4 (confirm) distinction for test usage
- [ ] Does NOT restate `systematic-debugging`'s own four-phase process
- [ ] States the real motivating case (the Wayland claim) plainly, not sanitized
- [ ] States surprise-at-being-wrong is a signal to verify, not explain away

- [ ] **Step 5: Commit**

```bash
git add skills/verify-before-asserting
git commit -m "Add verify-before-asserting skill"
```

---

### Task 3: Version bump and CHANGELOG

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `CHANGELOG.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: Tasks 1 and 2's completed skills (README references them by name; the changelog entry describes what they are).
- Produces: Orclab at version `0.5.0`. Task 4's verification scenarios reference this version.

- [ ] **Step 1: Update `.claude-plugin/plugin.json`**

Replace the entire file content with:

```json
{
  "name": "orclab",
  "description": "Project-discipline skills and commands distilled from real practice: backlog tracking, release checklists, live-environment registries, currency and verification discipline, a deterministic /orc-code entry point for new-project, existing-project, and refactor work, /orc-version for versioning the current project, and /orc-git for common git/GitHub shortcuts.",
  "version": "0.5.0",
  "author": {
    "name": "direflail"
  }
}
```

- [ ] **Step 2: Update `.claude-plugin/marketplace.json`**

Replace the entire file content with:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "orclab",
  "description": "Project-discipline skills and commands distilled from real practice: backlog tracking, release checklists, live-environment registries, currency and verification discipline, a deterministic /orc-code entry point for new-project, existing-project, and refactor work, /orc-version for versioning the current project, and /orc-git for common git/GitHub shortcuts.",
  "owner": {
    "name": "direflail"
  },
  "plugins": [
    {
      "name": "orclab",
      "description": "Project-discipline skills and commands distilled from real practice: backlog tracking, release checklists, live-environment registries, currency and verification discipline, a deterministic /orc-code entry point for new-project, existing-project, and refactor work, /orc-version for versioning the current project, and /orc-git for common git/GitHub shortcuts.",
      "version": "0.5.0",
      "source": "./"
    }
  ]
}
```

- [ ] **Step 3: Verify manifests**

```bash
python3 -c "
import json
p = json.load(open('.claude-plugin/plugin.json'))
m = json.load(open('.claude-plugin/marketplace.json'))
assert p['name'] == m['plugins'][0]['name'] == 'orclab'
assert p['version'] == m['plugins'][0]['version'] == '0.5.0'
assert m['plugins'][0]['source'] == './'
print('OK: plugin.json/marketplace.json valid, consistent, version 0.5.0')
"
```
Expected: `OK: plugin.json/marketplace.json valid, consistent, version 0.5.0`

- [ ] **Step 4: Update `CHANGELOG.md`**

Find:
```
# Changelog

All notable changes to this project are documented here, newest first.

## [0.4.0] - 2026-09-05
```

Replace with:
```
# Changelog

All notable changes to this project are documented here, newest first.

## [0.5.0] - 2026-09-06

### Added
- `currency-discipline` — checks that a chosen dependency, version, or technical approach is
  actually current, and that research relied on is checked for age, before trusting it. Names
  real verification mechanisms per ecosystem (registry APIs, official release pages), not just
  "check if it's current."
- `verify-before-asserting` — verifies a challenged factual/technical claim instead of defending
  it, and reinforces (without duplicating) superpowers' own `systematic-debugging` signal
  recognition and test-based root-cause localization.

## [0.4.0] - 2026-09-05
```

- [ ] **Step 5: Verify CHANGELOG.md**

```bash
grep -c "## \[0.5.0\]" CHANGELOG.md
grep -c "## \[0.4.0\]" CHANGELOG.md
```
Expected: `1` and `1`.

- [ ] **Step 6: Update `README.md`**

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
- **currency-discipline** — check that a chosen dependency, version, or technical approach is
  actually current before committing to it, with real, concrete per-ecosystem verification
  mechanisms.
- **verify-before-asserting** — verify a challenged factual/technical claim instead of defending
  it; reinforces superpowers' own `systematic-debugging` signal recognition.
```

Find:
```
## Status

v1 (process core) + v2 (`/orc-code`) + v3 (`/orc-version`, `/orc-help`/`/orc`) + v4 (`/orc-git`)
shipped. See `docs/superpowers/specs/` for the design history, `CHANGELOG.md` for what actually
changed release to release, and `BACKLOG.md` for what's deliberately deferred (real per-stack
defaults research is #4, `/orc-data` is #5, hook-based enforcement is #3, per-language manifest
version-sync is #6). See `VERIFICATION.md` for the dogfood script that confirms everything
actually works once installed in a real project.
```

Replace with:
```
## Status

v1 (process core) + v2 (`/orc-code`) + v3 (`/orc-version`, `/orc-help`/`/orc`) + v4 (`/orc-git`) +
v5 (`currency-discipline`, `verify-before-asserting`) shipped. See `docs/superpowers/specs/` for
the design history, `CHANGELOG.md` for what actually changed release to release, and `BACKLOG.md`
for what's deliberately deferred (real per-stack defaults research is #4, `/orc-data` is #5,
hook-based enforcement is #3, per-language manifest version-sync is #6, distribution-channel
metrics is #7). See `VERIFICATION.md` for the dogfood script that confirms everything actually
works once installed in a real project.
```

- [ ] **Step 7: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json CHANGELOG.md README.md
git commit -m "Bump version to 0.5.0"
```

---

### Task 4: Dogfood verification scenarios

**Files:**
- Modify: `VERIFICATION.md`

**Interfaces:**
- Consumes: the completed skills from Tasks 1-2.
- Produces: a complete verification script covering v1-v5. No later task depends on this.

- [ ] **Step 1: Add new scenarios to `VERIFICATION.md`**

Find:
```
## Recording the result
```

Replace with:
```
## Scenario 17: currency-discipline on a dependency choice

1. In any project, ask Claude to add a dependency it would need to pick a version for (e.g. "add
   a testing library to this Python project").
2. **Expected:** Claude checks the real current version (e.g. via PyPI's JSON API or `pip index
   versions`) rather than naming a version from memory, and states what it checked.

## Scenario 18: currency-discipline on a research-derived answer

1. Ask Claude a technical question where the answer plausibly depends on a specific, checkable
   fact (e.g. "does GitHub Actions support X feature").
2. **Expected:** if Claude's answer relies on documentation or a search result, it notes the
   source's age/currency rather than presenting it as unconditionally true.

## Scenario 19: verify-before-asserting on a challenged claim

1. During any real task, if Claude states a factual/technical claim, challenge it directly (e.g.
   "are you sure about that?").
2. **Expected:** Claude verifies (checks docs, tests live, re-derives) rather than restating the
   original claim with additional-sounding justification. If the claim turns out correct, it
   should say so with the verification evidence, not just repeat itself.

## Scenario 20: verify-before-asserting during a real debugging session

1. During a real bug investigation that's taking multiple rounds, say something like "take a step
   back" or express that you're stuck.
2. **Expected:** Claude treats this as the same "we're stuck" signal `systematic-debugging` already
   documents — returning to root-cause investigation (Phase 1) rather than attempting another
   guess-fix, and considers writing a test to localize where the failure starts if it hasn't
   already.

## Recording the result
```

- [ ] **Step 2: Commit**

```bash
git add VERIFICATION.md
git commit -m "Add currency-discipline and verify-before-asserting dogfood scenarios"
```

---

## Self-Review Notes (from writing this plan)

- **Spec coverage:** both skills' full content (triggers, rules, concrete mechanisms,
  relationship-to-superpowers sections, worked examples) covered in Tasks 1-2. Version bump and
  changelog covered in Task 3. Verification scenarios cover both skills' real trigger scenarios
  (dependency choice, research-answer currency, challenged claim, debugging signal recognition) in
  Task 4. The check-in-cadence point correctly does not appear anywhere in this plan — it's
  explicitly out of scope, already captured as a personal memory outside this plan's scope.
- **Placeholder scan:** no TBD/TODO; every content block is complete, not a stub.
- **Consistency check:** version `0.5.0` is consistent across `plugin.json`, `marketplace.json`,
  the `CHANGELOG.md` entry, and README's Status line. Both skills' names in their frontmatter
  match their directory names exactly. `verify-before-asserting`'s cross-reference to
  `systematic-debugging` uses the same "Signals You're Doing It Wrong" table language consistently
  across the SKILL.md, its reference file, and Task 4's Scenario 20.
