# Orclab v5: `currency-discipline` and `verify-before-asserting` — design

## Goal

Distill two real, hard-won lessons from Orcshot into reusable core skills: staying on current
tech instead of drifting onto stale/deprecated versions, and verifying a challenged claim instead
of defending it. Both are genuinely project-agnostic — the same category as v1's three skills —
not specific to Orcshot or to direflail's personal working style.

direflail's own framing (2026-09-06): Orcshot ended up on extremely old, already-deprecated
library versions, causing avoidable refactors later; separately, real technical claims (e.g. about
Wayland's capabilities) were asserted confidently, then defended against direct correction instead
of verified. "It is not the specifics that bother me here. It is the lack of research and care and
then sticking to whatever story you'd come up with to an absurd point that concerns me."

A third, related point from the same discussion — recognizing "take a step back" as a debugging
signal, and using tests to localize a bug during root-cause investigation rather than only as a
pre-fix formality — is folded into `verify-before-asserting` as a reinforcement of superpowers'
own `systematic-debugging` skill, not a separate skill, since it's the same underlying discipline
(verify by checking, not by re-asserting) applied to one specific situation.

A fourth point (direflail wants fewer mid-task check-in questions) is explicitly **not** part of
this spec — it's personal working-style feedback for this project, captured as a memory, not
something that belongs in guidance shipped to anyone else who installs Orclab.

## Scope

**In scope now:** two skills, `currency-discipline` and `verify-before-asserting`, each with a
`SKILL.md` and a `references/` worked example, following the exact file shape v1's three skills
already established.

**Explicitly out of scope:** any change to superpowers' own `systematic-debugging` or
`verification-before-completion` skills — `verify-before-asserting` reinforces and cross-references
them, it does not fork or duplicate their content.

## `currency-discipline`

**Trigger:** choosing a dependency, library version, framework, or technical approach; or when
research (a search, documentation, or recalled knowledge) surfaces an answer to a technical
question.

**Rules:**
- Default to the current stable version of any technology involved, unless explicitly told
  otherwise. Don't default to "whatever version a found example happens to use" or "whatever's
  remembered from training" without checking.
- Follow current, modern standards and practices for the relevant ecosystem — an idiom or pattern
  that was correct three years ago may no longer be how the ecosystem actually does things now.
- When research surfaces an answer to a technical question, check its age before trusting it. An
  old or undated source is a real risk factor, not neutral information, especially in a
  fast-moving ecosystem.
- If unsure whether something is still current, verify against the real, currently-live
  authoritative source — never assume the first answer found represents current best practice.

**Concrete verification mechanisms** (the actual "how," not just "check if it's current"):
- **Library/package version**: query the real package registry directly, not a search engine's
  index (which can lag) or recalled/trained knowledge (which has a hard cutoff). Real commands per
  ecosystem: `npm view <package> version` (npm); `pip index versions <package>` or PyPI's JSON API
  at `https://pypi.org/pypi/<package>/json` (Python); crates.io's API or `cargo search <package>`
  (Rust); Maven Central's search API (Java); `go list -m -versions <module>` (Go). If the relevant
  package manager isn't installed locally, `WebFetch` against the registry's real API endpoint
  works regardless of local tooling.
- **Language/runtime "current stable" status**: check the language's own official release page
  directly via `WebFetch`, cross-checked against a real, well-known lifecycle-tracking resource
  such as endoflife.date. Verify the resource itself is still live and accurate at time of use —
  don't assume from memory that a reference site's content is current.
- **Evaluating whether a found answer is stale**: check the source's own stated date where visible;
  treat an undated answer, or one that reads like it predates a known ecosystem shift, as
  higher-risk and worth a second, live check rather than silently presented as current fact.

**Real motivating case, stated plainly in the skill:** Orcshot ended up on extremely old,
already-deprecated library versions, which caused real, avoidable refactoring work later. This
skill exists specifically to close off that recurring failure mode.

## `verify-before-asserting`

**Trigger:** a factual or technical claim you made gets challenged, or something turns out
surprising (a platform, tool, or library doesn't behave as assumed).

**Rules:**
- The correct response to a challenge on a factual/technical claim is to verify it — check current
  documentation, test the actual behavior live, or re-derive the answer — never to restate or
  argue the original position more firmly without checking.
- Surprise at being wrong is itself a signal to verify, not a feeling to reason away or explain
  around.
- This applies with extra force to platform and ecosystem capabilities that genuinely shift over
  time (what a windowing system, OS version, or library currently supports) — verify the real,
  current behavior before designing around a remembered or assumed capability.

**Relationship to superpowers' `systematic-debugging`** (reinforcement, not duplication): that
skill already has a "your human partner's Signals You're Doing It Wrong" table whose entries —
"'We're stuck?' (frustrated) - Your approach isn't working," "Stop guessing" — describe exactly
the situation a phrase like "take a step back" signals. This skill states explicitly that such a
signal, in any phrasing, means the same thing: STOP, return to Phase 1, verify rather than defend.
It also reinforces one specific technique already present in that skill but framed narrowly there:
writing a test to *localize* where a bug's root cause lives is valid and valuable during Phase 1's
evidence-gathering, not only as the Phase 4 pre-fix formality the skill's own text emphasizes.

**Real motivating case, stated plainly in the skill:** asserting that Wayland didn't support a
particular capability, then arguing against a direct, correct challenge instead of checking —
treated as a real, costly failure mode this skill exists to close off, not a hypothetical one.

## File structure

```
orclab/
  skills/
    currency-discipline/
      SKILL.md
      references/example-check.md
    verify-before-asserting/
      SKILL.md
      references/example-verification.md
```

Same shape as every other Orclab skill: `SKILL.md` states the discipline, `references/` holds one
worked example. Both get a "Relationship to superpowers" section, matching the other three skills
— `currency-discipline` notes it doesn't replace any existing skill (nothing in superpowers covers
this specifically); `verify-before-asserting` explicitly cross-references `systematic-debugging` as
described above.

## Validation

Same dogfooding principle as v1-v4 — no automated test suite applies to skill content. Validation
is running real scenarios in a fresh session and confirming: a dependency-choice request triggers
a real registry check rather than an assumed version number; a challenged technical claim during a
real task triggers actual verification (a real command, a real fetch) rather than a restated
assertion. Not written up as `VERIFICATION.md` scenarios yet — an implementation-plan-level detail,
added the same way prior versions' were.

## Out of scope, tracked separately

Check-in cadence (direflail wants fewer mid-task pause-and-ask moments) is personal working-style
feedback, not core guidance — captured as a memory for this project, not a skill shipped to anyone
else who installs Orclab.
