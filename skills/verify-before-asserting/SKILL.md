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
already has a "your human partner's Signals You're Doing It Wrong" list, and entries like
"'We're stuck?' (frustrated) - Your approach isn't working" and "Stop guessing" describe exactly
what a phrase like "take a step back" signals in different words. Any phrasing of that signal
means the same thing: STOP, return to Phase 1, verify rather than defend.

This skill also reinforces one specific technique that skill already contains but frames
narrowly: writing a test to *localize* where a bug's root cause lives is valid and valuable during
Phase 1's evidence-gathering — not only as the Phase 4 pre-fix formality that skill's own text
emphasizes. Writing tests progressively closer to the actual failure point is itself a
verification technique, not just a confirmation step for a fix you already believe is right.

**Distinct from superpowers' `verification-before-completion`**, which gates claims that work is
*done* (no completion claim without fresh verification evidence) — this skill governs what to do
when a claim you already made gets *challenged*, before completion is even in question. The two
are easy to confuse by name; they fire at different moments.

## What NOT to do

- Don't restate a challenged claim more firmly instead of checking it.
- Don't treat "I'm surprised this is wrong" as a reason to look for a way the original claim could
  still be right — treat it as a reason to check.
- Don't wait for repeated pushback before verifying — the first challenge is the signal, not the
  third.
