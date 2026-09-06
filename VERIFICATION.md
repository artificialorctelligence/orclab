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

## Scenario 9: /orc-version increment, local-only

1. In Orclab's own repo, run `/orc-version increment major`.
2. **Expected:** since the current version is `0.4.0`, the result is `1.0.0` — both `plugin.json`
   and `marketplace.json`'s version fields update to `"1.0.0"`, a changelog entry is drafted from
   real git history since the `v0.4.0` tag, you're asked whether to add/change anything before
   it's written, and a new commit + local tag `v1.0.0` are created.
3. **Expected throughout:** nothing is pushed anywhere, and no GitHub Release is created — confirm
   with `git log origin/main..HEAD` that the new commit hasn't reached the remote.
4. Revert this probe afterward — **confirm you're about to drop exactly the probe commit you just
   made** (`git log -1` should show the version-bump commit `/orc-version` just created), then run
   `git tag -d v1.0.0 && git reset --hard HEAD~1`. Do not use a hardcoded version tag to revert to
   — the "current" version keeps changing release to release, and reverting to a stale tag would
   discard real, unrelated work made since that tag, not just this probe.

## Scenario 10: /orc-version bare invocation

1. In Orclab's own repo, run `/orc-version` with no arguments.
2. **Expected:** the current version (`0.4.0`, or whatever it's been bumped to) is reported,
   followed by the increment/set menu — and nothing else happens; no files change.

## Scenario 11: /orc-version release

**Caution:** if Scenario 9's probe bump wasn't kept (i.e. you already ran the revert commands
above), don't run this scenario against that reverted state — only run it against a real bump you
actually intend to publish. This is the only scenario in this script that makes something public
and irreversible.

1. After running Scenario 9 (or any real bump) and deciding to keep it, run
   `/orc-version release`.
2. **Expected:** the commit and tag get pushed to `origin`, and a real GitHub Release is created
   at `https://github.com/artificialorctelligence/orclab/releases` — confirm by checking that URL
   or via `gh release list`.

## Scenario 12: /orc-help in core vs. project context

1. In Orclab's own repo, run `/orc-help`.
2. **Expected:** reports "core" context, the real current version, and a live-read synopsis of
   all commands present in `commands/*.md` at the time it's run (not a stale hardcoded list).
3. In a different project that has Orclab installed (e.g. Orcshot, once dogfooded there), run
   `/orc-help` again.
4. **Expected:** reports "project" context, the same Orclab version as step 1 (assuming no bump
   happened in between), and the same command synopsis.
5. Run `/orc` (bare) in either location.
6. **Expected:** identical output to `/orc-help` in the same location.

## Scenario 13: /orc-git repo, all three directory states

1. In a throwaway empty scratch directory, run `/orc-git repo <a real, small test repo URL>`.
   **Expected:** the repo is cloned directly into the (empty) directory.
2. In a different throwaway directory that's already a git repo with no `origin` set, run
   `/orc-git repo <some URL>`. **Expected:** `origin` is set to that URL, no confirmation asked
   (since nothing existing was being overwritten).
3. In that same directory, run `/orc-git repo <a different URL>`. **Expected:** Claude shows the
   currently-set URL and asks for confirmation before changing it — it does not silently overwrite.
4. **Expected throughout:** `.orclab/git-repo.json` is created with the connected URL, and
   `.gitignore` gains a `.orclab/` entry if it didn't already have one.

## Scenario 14: /orc-git commit, clean tree and real changes

1. In a project with no uncommitted changes, run `/orc-git commit`. **Expected:** Claude reports
   there's nothing to commit and stops — no empty commit is created.
2. Make a real, small change, then run `/orc-git commit`. **Expected:** a real commit message is
   drafted from the actual diff (not a generic placeholder) and committed immediately — no
   confirmation question asked first.
3. Make another change, then run `/orc-git commit this is extra context`. **Expected:** the
   drafted message includes "this is extra context" as an addition, not as a replacement of the
   drafted description.

## Scenario 15: /orc-git push, commit-push/cp, and branch/switch aliases

1. After Scenario 14 commits something, run `/orc-git push` on a branch that's never been pushed
   before. **Expected:** it pushes with `-u origin <branch>` (sets upstream), with no confirmation
   prompt.
2. Make another small change, run `/orc-git commit-push`, then separately (on a different real
   change) run `/orc-git cp`. **Expected:** both produce identical commit-then-push behavior.
3. Run `/orc-git branch a-test-branch-name` (a branch that doesn't exist yet), then run
   `/orc-git switch a-test-branch-name` again. **Expected:** the first call creates and switches to
   it; the second call just switches (branch already exists) — both subcommand names behave
   identically.

## Scenario 16: /orc-git pr

1. In a project with at least one real open (or closed) PR, run `/orc-git pr <a real PR number>`.
   **Expected:** `gh pr checkout <id>` runs and the PR's branch is checked out locally.

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

Note the outcome of each scenario (pass/fail, with specifics) either back in this conversation or
as a new `BACKLOG.md` entry in Orclab itself if something needs fixing before this work is
considered done.
