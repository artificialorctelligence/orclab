# Worked example: BACKLOG.md entries

Real, lightly-genericized entries adapted from Orcshot's own BACKLOG.md, showing the three states
an entry goes through.

## Open entry (not yet fixed)

```markdown
## #142: Snap channel has no working audio feedback on capture

Found while adding Snap packaging (2026-08-30): the Snap manifest never granted access to any
audio-sink interface, so `capture_feedback.py`'s shutter-sound playback silently fails under
strict confinement — `play_capture_sound()` throws, caught by an existing broad exception handler
that was written for a different failure mode entirely, so capture itself still succeeds; only
the sound is missing. Confirmed live: a real strict-confinement build produces no audible sound
on capture, with no error surfaced anywhere the user would see it.

Not blocking the Snap channel's initial ship (silent capture already works, sound was always
best-effort) but a real, user-visible gap once anyone notices it's missing.
```

## Resolved entry (append, don't overwrite)

```markdown
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
```

## Deleted entry (not "marked resolved" — gone, number never reused)

Entry #96 existed, describing a migration-path concern for users upgrading from a version that,
it later turned out, was never actually published anywhere. Once that was confirmed (zero real
download counts on every channel), the entry's owner judged it couldn't affect any real user and
deleted it outright. The file simply jumps from `## #95: ...` to `## #97: ...` — that gap is the
correct, permanent record that #96 was considered and explicitly dropped, not lost track of.

## Deleting the highest-numbered entry (the numbering exception)

If the entry being deleted happens to be the current maximum (say `#150`, with nothing higher),
deleting it drops the file's own visible maximum back to `#149`. Scanning the file alone would
then let a future entry claim `#150` again — reusing a number that's supposed to be permanent.
This is the one case where the file alone isn't enough: check history (`git log -S'## #' --
BACKLOG.md` or equivalent) for the true historical maximum before numbering the next entry.
