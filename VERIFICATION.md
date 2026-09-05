# Orclab v1 verification script

Run these three scenarios in a **fresh Claude Code session, in the Orcshot project directory**
(`~/projects/orcshot`), after installing Orclab per `README.md`. Orcshot already has a real
`BACKLOG.md` and (once the second scenario is run) a real `RELEASING.md` in exactly the shape
these skills model from, making it a better verification target than a throwaway project.

## Scenario 1: backlog-discipline

1. Note the highest `#N` currently in Orcshot's `BACKLOG.md`.
2. Ask Claude to investigate something small and genuinely inconclusive (or describe a real,
   deliberately-deferred finding) and confirm it gets logged to the backlog.
3. **Expected:** a new `## #<N+1>: ...` entry is added, with a real paragraph of context (not a
   one-line stub), and the file's existing entries are untouched.
4. Ask Claude to resolve that same entry, describing a plausible fix.
5. **Expected:** the title gains a `(RESOLVED YYYY-MM-DD)` suffix, a new paragraph is appended
   below the original text, and the original paragraph is still present, word-for-word.
6. Ask Claude to delete the entry, stating explicitly that it's no longer worth tracking.
7. **Expected:** the `## #<N+1>: ...` section is removed entirely; no other entry is renumbered;
   the number `<N+1>` is confirmed as never appearing again in any later entry added during this
   verification pass.

## Scenario 2: release-checklist

1. Confirm Orcshot already has a `RELEASING.md`. Ask Claude to add a new step to it (e.g. a
   fictional "check translation completeness" step) and specify roughly where it belongs in the
   dependency order.
2. **Expected:** the new step is inserted in the correct position (not appended to the end
   regardless of order), existing steps are renumbered correctly, and the new step includes both
   an exact command (if applicable) and a stated "why this exists" if the reason isn't obvious.
3. Revert this change afterward (`git checkout -- RELEASING.md`) — it's a verification probe, not
   a real change to keep.

## Scenario 3: environment-registry

1. Ask Claude, in the Orcshot project, about a real environment it already has registered (e.g.
   the Ubuntu 26.04 VM) and confirm it re-verifies the live roster (e.g. re-running a listing
   command) rather than only reciting the stored memory content.
2. Describe a new, fictional environment gotcha for verification purposes and ask Claude to
   register it.
3. **Expected:** the gotcha is written to a memory file (`project` type), not to any git-tracked
   file in the Orcshot repo — confirm with `git status` in Orcshot that nothing changed there.
4. **Expected throughout:** at no point does Claude ask for, display, or type an actual password
   — if any step would require one, it should stop and describe the prompt instead.

## Recording the result

Note the outcome of each scenario (pass/fail, with specifics) either back in this conversation or
as a new `BACKLOG.md` entry in Orclab itself if something needs fixing before v1 is considered
done.
