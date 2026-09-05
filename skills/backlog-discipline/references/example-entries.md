# Worked example: BACKLOG.md entries

Real, lightly-genericized entries adapted from Orcshot's own BACKLOG.md, showing the three states
an entry goes through.

## Open entry (not yet fixed)

## #142: Snap channel has no working audio feedback on capture

Found while adding Snap packaging (2026-08-30): the Snap manifest never granted access to any
audio-sink interface, so `capture_feedback.py`'s shutter-sound playback silently fails under
strict confinement — `play_capture_sound()` throws, caught by an existing broad exception handler
that was written for a different failure mode entirely, so capture itself still succeeds; only
the sound is missing. Confirmed live: a real strict-confinement build produces no audible sound
on capture, with no error surfaced anywhere the user would see it.

Not blocking the Snap channel's initial ship (silent capture already works, sound was always
best-effort) but a real, user-visible gap once anyone notices it's missing.

## Resolved entry (append, don't overwrite)

## #142: Snap channel has no working audio feedback on capture (RESOLVED 2026-09-01)

Found while adding Snap packaging (2026-08-30): the Snap manifest never granted access to any
audio-sink interface, so `capture_feedback.py`'s shutter-sound playback silently fails under
strict confinement — `play_capture_sound()` throws, caught by an existing broad exception handler
that was written for a different failure mode entirely, so capture itself still succeeds; only
the sound is missing. Confirmed live: a real strict-confinement build produces no audible sound
on capture, with no error surfaced anywhere the user would see it.

Not blocking the Snap channel's initial ship (silent capture already works, sound was always
best-effort) but a real, user-visible gap once anyone notices it's missing.

**Resolved for real, not just tracked**: added the `audio-playback` plug to `snapcraft.yaml` and
connected it in the manifest's default-connections. Verified live: real audible playback confirmed
on a real strict-confinement build, not just "the plug exists now."

## Deleted entry (not "marked resolved" — gone, number never reused)

Entry #96 existed, describing a migration-path concern for users upgrading from a version that,
it later turned out, was never actually published anywhere. Once that was confirmed (zero real
download counts on every channel), the entry's owner judged it couldn't affect any real user and
deleted it outright. The file simply jumps from `## #95: ...` to `## #97: ...` — that gap is the
correct, permanent record that #96 was considered and explicitly dropped, not lost track of.
