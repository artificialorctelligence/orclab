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

See `verify-before-asserting`'s own worked example for the other half of this same real story —
what happens when that assumption gets challenged and defended instead of checked.
