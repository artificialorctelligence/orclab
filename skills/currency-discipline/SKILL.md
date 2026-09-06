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

If the relevant package manager isn't installed locally, use `WebFetch` against the registry's
real API endpoint directly instead — it works regardless of local tooling.

**Language/runtime "current stable" status** — check the language's own official release page
directly via `WebFetch`, cross-checked against a real, well-known lifecycle-tracking resource such
as endoflife.date. Verify the resource itself is still live and accurate at time of use — don't
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
