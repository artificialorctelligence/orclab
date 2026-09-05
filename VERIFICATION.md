# Orclab verification script

Run these scenarios in a **fresh Claude Code session** after installing/reinstalling Orclab per
`README.md`. Scenarios 1-4 (v1's skills) run in the Orcshot project directory (`~/projects/orcshot`)
— it already has a real `BACKLOG.md` and a real `RELEASING.md` in exactly the shape these skills
model from, making it a better verification target than a throwaway project. Scenarios 5-8
(`/orc-code`) specify their own target directory per scenario, since they cover different
situations (empty scratch dir, existing project, etc.).

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

## Scenario 4: scaffolding on first use

1. In a throwaway empty scratch directory (not Orcshot — this specifically tests the no-file-yet
   path), ask Claude to log a real finding to the backlog.
2. **Expected:** `BACKLOG.md` is created first, with the exact standard header from
   `skills/backlog-discipline/SKILL.md`'s "If `BACKLOG.md` doesn't exist yet" section, and then
   the new entry is added below it as `#1`.

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

Note the outcome of each scenario (pass/fail, with specifics) either back in this conversation or
as a new `BACKLOG.md` entry in Orclab itself if something needs fixing before v1 is considered
done.
