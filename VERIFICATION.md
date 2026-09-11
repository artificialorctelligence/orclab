# Orclab verification script

Run these scenarios in a **fresh Claude Code session** after installing/reinstalling Orclab per
`README.md`. Scenarios 1-4 (v1's skills) run in the Orcshot project directory (`~/projects/orcshot`)
— it already has a real `BACKLOG.md` and a real `RELEASING.md` in exactly the shape these skills
model from, making it a better verification target than a throwaway project. Scenarios 5-8
(`/orc-code`) specify their own target directory per scenario, since they cover different
situations (empty scratch dir, existing project, etc.).

## Scenario 1: backlog-discipline

1. Ask Claude to investigate something small and genuinely inconclusive (or describe a real,
   deliberately-deferred finding) and confirm it gets logged to the backlog.
2. **Expected:** Claude asks the allocator for the number rather than scanning the file for the
   highest one — the number comes back from `/orc-todo add backlog`, which prints it. A new
   entry appears under that number, with a real paragraph of context (not a one-line stub), and
   the file's existing entries are untouched.
3. **Expected:** the entry is left **uncommitted**. The allocator writes and stops; committing
   would sweep whatever else is uncommitted in that file into a commit claiming to be a backlog
   entry. Confirm `git status` shows `BACKLOG.md` modified.
4. Ask Claude to resolve that same entry, describing a plausible fix.
5. **Expected:** the title gains a `(RESOLVED YYYY-MM-DD)` suffix, a new paragraph is appended
   below the original text, and the original paragraph is still present, word-for-word.
6. Ask Claude to delete the entry, stating explicitly that it's no longer worth tracking.
7. **Expected:** that entry's section is removed entirely; no other entry is renumbered; and the
   number is confirmed as never appearing again in any later entry added during this
   verification pass — the allocator's counter never goes backwards, so a deleted maximum
   cannot be reissued.

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
   demonstrating the intent-classification routing from Step 0 of `skills/orc-code/SKILL.md`.

## Scenario 9: /orc-version increment, local-only

1. In Orclab's own repo, run `/orc-version increment major`.
2. **Expected:** whatever `plugin.json` currently reports as the version, incrementing major
   resets minor and point to `0` (e.g. `0.5.0` → `1.0.0`) — both `plugin.json` and
   `marketplace.json`'s version fields update accordingly, a changelog entry is drafted from real
   git history since the current version's own git tag, you're asked whether to add/change
   anything before it's written, and a new commit + local tag for the new version are created.
3. **Expected throughout:** nothing is pushed anywhere, and no GitHub Release is created — confirm
   with `git log origin/main..HEAD` that the new commit hasn't reached the remote.
4. Revert this probe afterward — **confirm you're about to drop exactly the probe commit you just
   made** (`git log -1` should show the version-bump commit `/orc-version` just created), then find
   the tag it created with `git tag --list 'v*' --sort=-v:refname | head -1` (the newest tag —
   never assume it's `v1.0.0`; that's only correct while Orclab's major version is still `0`) and
   run `git tag -d <that tag> && git reset --hard HEAD~1`. Do not use a hardcoded version tag to
   revert to — the "current" version keeps changing release to release, and reverting to a stale
   tag would discard real, unrelated work made since that tag, not just this probe.

## Scenario 10: /orc-version bare invocation

1. In Orclab's own repo, run `/orc-version` with no arguments.
2. **Expected:** the current version (whatever `plugin.json` currently reports) is reported,
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
   all commands present as `skills/orc*/SKILL.md` at the time it's run (not a stale hardcoded
   list).
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

## Scenario 21: /orc-* wrapper skills work in Claude Desktop

1. In a **fresh** Desktop session started after the plugin is installed/updated (an existing chat
   thread will not pick up a mid-conversation reinstall — see `CLAUDE.md`'s gotcha #4), invoke
   each of the five skills at least once, either by its bare name or its plugin-qualified form if
   Desktop's autocomplete inserts one (`/orc-code` or `/orclab:orc-code` — confirmed live,
   2026-09-06): `/orc-code`, `/orc-version`, `/orc-help`, `/orc`, `/orc-git`.
2. **Expected:** each one succeeds — no "Unknown command" — and produces the same real behavior
   as its `skills/<name>/SKILL.md` (e.g. `/orc-help` reports the real version and command
   synopsis, `/orc-code` asks its real questions).
3. Separately, in the CLI, confirm the same `/orc-*` skills work there too — one component
   serves both surfaces, and since v0.10.0 there is no parallel `commands/` layer behind them.

## Scenario 22: /orc-* skills fire from a natural sentence, not just the literal slash

1. In a fresh session, say something like "I want to use orc-code to build a small CLI tool" —
   no literal slash.
2. **Expected:** the `orc-code` skill fires and follows its real structured flow (asking language,
   name, type, checking the Defaults Table) — not generic freelanced advice.
3. **Expected throughout:** none of the five skills fire ambiently on unrelated requests — e.g. a
   plain "help me commit this" (with no mention of `orc-git` by name) should not automatically
   trigger `orc-git`'s skill, since none of the five are meant to compete for attention outside an
   explicit or clearly-named request.

## Scenario 23: /orc-publish resolves and dry-runs a synthetic tree without executing anything

1. In a throwaway scratch directory (never Orclab's own repo, never a real project), create
   `.orclab/publish/channels.yaml`:
   ```yaml
   desktop:
     python:
       linux:
         snap: { action: "echo would-publish-snap" }
         flatpak: { action: "echo would-publish-flatpak" }
   ```
2. Run `/orc-publish --dry-run`.
3. **Expected:** both leaves and their real actions are printed; neither `echo` command actually
   runs (confirm no output beyond the printed plan itself).

## Scenario 24: /orc-publish executes after confirmation, with a real per-leaf summary

1. Using the same synthetic tree as Scenario 23, ask Claude to run `/orc-publish`.
2. **Expected:** Claude shows the dry-run plan first and asks for confirmation before running
   anything — it must not execute on the first pass.
3. Confirm.
4. **Expected:** both `echo` commands actually run, and Claude reports a summary showing both
   leaves as `success`.

## Scenario 25: /orc-publish continues past an independent failure and reports it honestly

1. Add a third leaf to the synthetic tree: `broken: { action: "exit 1" }`.
2. Run `/orc-publish` (or `/orc-publish desktop.python.linux broken` to include it explicitly)
   and confirm.
3. **Expected:** the working leaves still report `success`; `broken` reports `failed`; nothing is
   silently dropped from the summary, and the failure isn't paraphrased away.

## Scenario 26: /orc-publish --for reports an unset channel plainly, never as an error

1. Create `.orclab/publish/distro.yaml` in the same scratch directory:
   ```yaml
   mint-next:
     x11: {}
   ```
2. Run `/orc-publish --for mint-next.x11`.
3. **Expected:** reports "no channel set (known target, not yet actionable)" — a normal report,
   not an error, and nothing executes.

## Scenario 27: /orc-release refuses to invent a process

1. In a throwaway scratch directory with no `RELEASING.md`, run `/orc-release`.
2. **Expected:** it reports plainly that there's no `RELEASING.md` and stops, suggesting
   `release-checklist`. It must not propose or invent any steps.

## Scenario 28: /orc-release halts on a failed step

1. In a throwaway scratch directory, create a synthetic `RELEASING.md`:
   ```markdown
   # Cutting a test release

   ## 1. First

   Run: `echo one`

   ## 2. Fails

   Run: `exit 1`

   ## 3. Never reached

   Run: `echo three`
   ```
   Add a `pyproject.toml` with `[project]`, a `name`, and `version = "0.1.0"`.
2. Run `/orc-release`, proceed past the working-tree report, and let it run.
3. **Expected:** step 1 completes, step 2 fails and the run **stops there** — step 3 never runs.
   The real error output is reported, not paraphrased.

## Scenario 29: /orc-release resumes at the right step

1. Continuing from Scenario 28, fix step 2 (change `exit 1` to `echo two`) and run
   `/orc-release` again.
2. **Expected:** it resumes at step 2 — not step 1 — and warns that `RELEASING.md` changed since
   the release started.

## Scenario 30: /orc-release refuses to start a second release

1. With Scenario 28's release still in progress, ask to start a new release.
2. **Expected:** refused, with a plain statement that one is already in progress and that you must
   resume or abort it.

## Scenario 31: the entry working-tree report

1. In the scratch project, create a stray file (`touch scratch-file.txt`), abort any in-progress
   release, and start a fresh one.
2. **Expected:** the real `git status --short` output is shown, including `scratch-file.txt`, and
   you're asked whether to proceed. Answering yes continues normally — it must not block.
3. Stop mid-release and resume.
4. **Expected:** the working-tree report does **not** fire again on resume.

## Scenario 32: a skip is recorded with its reason

1. Mid-release, ask to skip a step, giving a reason.
2. **Expected:** it's recorded with that reason, and `/orc-release status` shows it. Asking to
   skip with no reason is refused.

## Scenario 33: abort is honest about what it can't undo

1. Create a synthetic `RELEASING.md` where step 2 carries `**Irreversible.**`, run the release
   through step 2, then abort.
2. **Expected:** version files are rolled back to the previous version, and step 2 is reported as
   irreversible, completed, and **standing** — not claimed as undone.
3. Repeat with a document carrying **no** markers at all.
4. **Expected:** abort states plainly that it **cannot determine** which completed steps had
   external effects, rather than guessing.

## Scenario 34: a human-performed step stops for the human

1. Create a synthetic `RELEASING.md` with a step marked `**Performed by hand.**`.
2. Run the release up to it.
3. **Expected:** it presents what to do and stops, waiting for your confirmation — it does not
   run anything for that step or mark it complete on its own.

## Scenario 35: a release that runs to completion is closed with `finish`

Every scenario above stops at a failure, a refusal, a skip, an abort, or a human handoff — none
reaches the end of a release. That gap is exactly why a completed release had no exit at all
until the v8 final review.

1. In a throwaway scratch directory, create a synthetic `RELEASING.md` whose steps are no-ops:
   ```markdown
   # Cutting a test release

   ## 1. First

   Run: `echo one`

   ## 2. Second

   Run: `echo two`
   ```
   Add a `pyproject.toml` with `[project]`, a `name`, and `version = "0.1.0"`.
2. Run `/orc-release`, proceed past the working-tree report, target `0.2.0`, and let both steps
   run to completion.
3. **Expected:** after the last step passes, it closes the release with `finish` — printing a
   summary naming the version, the completed steps, any skips and their reasons, and any
   irreversible steps that now stand. It must **not** use `abort`.
4. Check `pyproject.toml`.
5. **Expected:** still `0.2.0`. `finish` rolls back nothing.
6. Start another release (`0.3.0`).
7. **Expected:** it starts normally — the finished release does not block it.
8. Separately, mid-release (one step still outstanding), ask to finish.
9. **Expected:** refused, naming the outstanding step, with the release still in progress.

## Scenario 36: /orc-reload refuses outside a plugin project

1. In a throwaway scratch directory that is not a Claude Code plugin, run `/orc-reload`.
2. **Expected:** it reports plainly that this isn't a plugin project and stops. It must not go
   hunting for something to reinstall, and must not run any `claude plugin` command.

## Scenario 37: /orc-reload on a directory-sourced marketplace

1. In Orclab's own repo (registered by local path — confirm with
   `python3 -c "import json;print(json.load(open('$HOME/.claude/plugins/known_marketplaces.json'))['orclab']['source'])"`),
   run `/orc-reload`.
2. **Expected:** it reports the currently-installed version and the version `plugin.json` expects,
   notes there's no cached clone to refresh for a directory source, runs uninstall+install, then
   confirms the expected version is really present in
   `~/.claude/plugins/cache/orclab/orclab/` — quoting the real version, not assuming it.
3. **Expected:** it ends by stating that this session still has the old version loaded and a fresh
   session is required. That statement must appear every time, not only when something looked
   wrong.
4. If the working tree is dirty, **expected:** it says so, since a directory-sourced install picks
   up uncommitted changes.

## Scenario 38: /orc-reload does not silently reinstall from a stale clone

1. This one needs a `github`-sourced marketplace. If you have one registered whose cached clone at
   `~/.claude/plugins/marketplaces/<name>` is behind its remote, run `/orc-reload` in that
   project. (If you have none, note this scenario as untested rather than faking it.)
2. **Expected:** it detects the clone is behind, **stops**, and hands you the exact `git fetch`
   plus `reset --hard` command to run yourself.
3. **Expected:** it does **not** run `reset --hard` on your checkout, and does not proceed with a
   reinstall that would install the stale code while appearing to succeed.

## Scenario 39: /orc-reload reports a failed reinstall as failed

1. Temporarily make the reinstall unable to reach the expected version — e.g. bump
   `plugin.json`'s version without committing, in a project whose marketplace source is a git
   clone rather than the working tree, so the installed version can't match.
2. Run `/orc-reload`.
3. **Expected:** after the install commands exit cleanly, it checks the cache, finds the expected
   version absent, and says the reinstall did **not** work. It must not report success just
   because the commands returned zero.
4. Revert the probe.

## Scenario 40: a one-time-setup check that passes is not re-run

1. In a throwaway scratch directory, create a synthetic `RELEASING.md`. Its commands are written
   inline rather than in fenced blocks, so the whole file stays a single, unambiguous fence-free
   document — `/orc-release` warns about unclosed fences for good reason.

   ```markdown
   # Cutting a test release

   ## 1. Set up the store

   **One-time setup:** registering the store name, once per account.

   Check whether it is already done: `test -f already-registered`

   If it is not, register it: `touch already-registered && echo REGISTERED-FOR-REAL`

   ## 2. Ship

   Run: `echo shipped`
   ```

   Add a `pyproject.toml` with `[project]`, a `name`, and `version = "0.1.0"`, then
   `touch already-registered`.
2. Run `/orc-release`, proceed past the working-tree report, target `0.2.0`, and let it reach
   step 1.
3. **Expected:** it runs only `test -f already-registered`, reports that the setup is already in
   place, and carries on. It must **not** run the register command — `REGISTERED-FOR-REAL` must
   never appear anywhere in the output.

## Scenario 41: a failing one-time-setup check stops and asks

1. Same scratch directory and `RELEASING.md` as Scenario 40, but `rm -f already-registered` first,
   and clear any release state so the run starts clean.
2. Run `/orc-release` and let it reach step 1.
3. **Expected:** the check fails and it **stops** — naming exactly what is missing, in the
   document's own words, and asking whether you want it set up now. It must not run the register
   command on its own initiative, and must not report the step as a failure it cannot recover
   from.
4. Say no.
5. **Expected:** it does not proceed to step 2, and `already-registered` still does not exist.
6. Re-run, and this time say yes.
7. **Expected:** only now does it run the register command, `REGISTERED-FOR-REAL` appears, and
   `already-registered` exists afterwards.

## Scenario 42: /orc-publish times out a hanging action and reports an un-onboarded channel honestly

1. In a throwaway scratch directory, create `.orclab/publish/channels.yaml`:

   ```yaml
   test:
     hangs:
       action: "sleep 30"
       timeout: 2
     snap: {}
   ```
2. Run `/orc-publish` and read the dry-run list.
3. **Expected:** `test.hangs` shows its action followed by a `timeout: 2s` line; `test.snap` shows
   `(known channel, not yet actionable)` and no timeout line at all.
4. Confirm, and let it run for real.
5. **Expected:** `test.hangs` reports `timed out` — not `failed` — with a detail naming the real
   2s limit and saying the action may be waiting on stdin. `test.snap` reports
   `not attempted (known channel, not yet actionable)`.
6. **Expected:** the run's exit code is non-zero. A timeout is a failing verdict even though its
   status string differs from `failed`.

## Scenario 43: a timed-out compound action leaves nothing running behind it

1. In a throwaway scratch directory, create `.orclab/publish/channels.yaml`. The nested `sh -c`
   matters: inside a plain `(...)` subshell, `$$` expands to the *outer* shell's PID, and step 5
   would then check a process that was killed directly and pass without proving anything.

   ```yaml
   test:
     compound:
       action: "true && sh -c 'echo $$ > /tmp/orc-verify-43.pid; sleep 120'"
       timeout: 2
   ```
2. `rm -f /tmp/orc-verify-43.pid`, then run `/orc-publish`, confirm the dry-run list, and let it
   run for real.
3. **Expected:** `test.compound` reports `timed out` after about two seconds, and the run's exit
   code is non-zero.
4. Check the recorded grandchild: `kill -0 $(cat /tmp/orc-verify-43.pid)`.
5. **Expected:** it fails with "No such process". The grandchild — the part that would still have
   been uploading — is gone, not merely reparented and sleeping out its remaining 118 seconds. If
   it is still alive, the process-group kill is broken and the `timed out` report is a lie.
6. Change `timeout:` to `60`, `rm -f /tmp/orc-verify-43.pid`, run it again, and press Ctrl-C a few
   seconds in — while the action is underway, well before the timeout could fire.
7. **Expected:** step 4's check fails the same way. The grandchild is gone on interrupt too. An
   operator cancelling a real `dput` must not be left with it still uploading, because the retry
   then double-uploads to a public archive.

## Scenario 44: a timed-out leaf's captured output is readable, not buried

Added 2026-09-07. `/orc-publish`'s unit tests assert that the right words appear in a timed-out
leaf's detail, and they passed both before and after a real defect in it: the captured output was
placed mid-sentence, stranding "the action may be waiting on stdin" under the log's final line
where it read as part of the output. Substring assertions survive reordering. Only looking at the
real rendered output caught it, which is what this scenario is for.

1. In a throwaway scratch directory, create `.orclab/publish/channels.yaml`:

   ```yaml
   test:
     noisy:
       action: "for i in 1 2 3; do echo build-line-$i; done; sleep 30"
       timeout: 2
     silent:
       action: "sleep 30"
       timeout: 2
   ```
2. Run `/orc-publish`, confirm the dry-run list, and let it run for real.
3. **Expected**, for `test.noisy` — read the summary as an operator would, not as a substring
   search. The stdin sentence comes **first**, and the captured output **last**:

   ```
   test.noisy: timed out (timed out after 2s - the action may be waiting on stdin. Output captured before it hung:
   build-line-1
   build-line-2
   build-line-3)
   ```

   The real publish action this models is `dpkg-buildpackage && debsign && dput` — hundreds of
   lines of build log, then a hang. If the stdin hint appears *after* the output, it is below the
   fold on a real run and the operator never sees it.
4. **Expected**, for `test.silent`: `no output captured, the action may be waiting on stdin`. That
   is honest here and is its own distinct signal — the action hung before printing anything.

## Scenario 45: preflight refuses a dirty artifact before it can be published

Unit tests assert the refusal is produced. This checks the thing they cannot: that an operator
reading the summary understands what happened and why nothing was published.

1. In a throwaway scratch directory, build a deliberately dirty source archive:

   ```bash
   mkdir -p pkg/.git && touch pkg/main.py pkg/.git/config pkg/.git/HEAD
   tar czf dirty.tar.gz pkg
   ```
2. Create `.orclab/publish/channels.yaml`:

   ```yaml
   test:
     dirty:
       artifact: "dirty.tar.gz"
       preflight: [no-vcs]
       action: "touch PUBLISHED"
   ```
3. Run `/orc-publish` and read the dry-run list.
4. **Expected:** `test.dirty` shows its action, its `preflight: no-vcs` line, and a
   `preflight result:` naming `no-vcs`, the real entry count, and the first few offending paths —
   not a wall of every entry.
5. Confirm, and let it run for real.
6. **Expected:** the leaf reports **`refused`**, not `failed`. `PUBLISHED` does **not** exist — the
   action never ran. The run's exit code is non-zero.
7. Re-run with `--allow-preflight-failure`.
8. **Expected:** `PUBLISHED` now exists, the finding is still printed in full, and the exit code is
   zero. The override is loud, not silent.
9. Rebuild the archive without the `.git` directory (`rm -rf pkg/.git && tar czf dirty.tar.gz pkg`)
   and run again without the override.
10. **Expected:** the leaf publishes normally and the dry-run reports `preflight result: clean`.

## Scenario 46: concurrent allocation, lanes, and the guard

Unit tests cover the mechanism; this covers what they cannot see — whether a person can read the
output, and whether the two hooks actually fire in a real session rather than only in a
subprocess harness.

1. Run `/orc-todo list` in a project with a real `BACKLOG.md`.
2. **Expected:** open entries, one line each, resolved ones absent, partially-addressed ones
   marked `[partial]`. Judge it as a person: can you tell at a glance what is open? If lanes
   exist they follow; if none do, there is no lanes section at all.
3. Open two terminals in the same project — one in the main checkout, one in a worktree of it.
   Run `/orc-todo add backlog "<title>"` in both at the same time, piping a real paragraph into
   each.
4. **Expected:** two different numbers, two entries, both in the *main checkout's* file. Neither
   overwrote the other, and neither is committed. This is the 2026-09-08 failure, and it is the
   only step here that reproduces its real topology — two checkouts, one canonical file.
5. Create a lane and mark it in progress: `/orc-todo lane create A v13` then
   `/orc-todo lane current A v13`.
6. Start a genuinely new session in that project.
7. **Expected:** the session is told, unprompted, that lane A is working on v13 — plus any
   uncommitted entries from step 3. Nobody asked; that is the point. A session that has to
   remember to check is the one that built the same feature twice.
8. With an uncommitted entry still present, run `git reset --hard`.
9. **Expected:** refused, naming the entry that would be lost and offering the
   `# orclab:discard-entries` marker. Then commit the entries and run it again.
10. **Expected:** silent. A guard that fires when nothing is at risk is noise, and noise gets
    waved through — which is the failure it exists to prevent.
11. In the worktree from step 3, with the main checkout still holding an uncommitted entry, run
    `git reset --hard`.
12. **Expected:** silent. The worktree holds no uncommitted entry of its own, and the guard reads
    only the tree the command runs in; denying it over the main checkout's entry would advise
    committing something this tree does not contain. (Scenario 48 covers the worktree holding
    one of its own.)

## Scenario 47: an accepted publish reads as not-done to an operator

Covers what unit tests cannot: that an `accepted` summary line reads to a human as "this is not
finished," not as a synonym for success. #15 established that substring assertions pass on output
nobody can actually read - the same risk applies here, since a test can assert `"accepted" in out`
and still pass on a line an operator would misread as done.

1. In a throwaway scratch directory, create `.orclab/publish/channels.yaml` with a leaf declaring
   `confirm`, and an action that prints a wall of build output before exiting 0 (model a real
   `dpkg-buildpackage && debsign && dput`, not a bare `echo`).
2. Run `/orc-publish`, confirm the dry-run plan, and let it publish for real.
3. Read the real `accepted` line as an operator would - action output included, since a real one
   carries a wall of build log above the sentence that matters - and say what you would do next.
4. Expected: the operator reads it as "this is not finished yet," names what the leaf's `confirm`
   block says to do next (run `--confirm`, or check the URL), and does not mistake it for
   `success`.

## Scenario 48: a scenario written in a worktree stays on its branch

BACKLOG #30. During v13, `/orc-todo add verification` run from a worktree wrote the new scenario
into the main checkout's file, describing a field that existed only on the branch. Unit tests
cover the routing; this covers the two things they cannot: that the right file is the one a
person then sees in `git status`, and that the guard protects it there.

1. In a worktree of a project with a real `VERIFICATION.md`, run
   `/orc-todo add verification "<title>"` with a real paragraph on stdin.
2. **Expected:** the number printed is one higher than the highest scenario anywhere in the
   project, including the main checkout. `git status` in the worktree shows `VERIFICATION.md`
   modified; `git status` in the main checkout shows it clean. The scenario is on the branch.
3. In the same worktree, run `/orc-todo add backlog "<title>"` with a real paragraph.
4. **Expected:** the main checkout's `BACKLOG.md` is modified and the worktree's is not. The
   other file's behaviour did not change.
5. In the worktree, with the scenario from step 1 still uncommitted, run `git reset --hard`.
6. **Expected:** refused, naming that scenario. A discard reaches only the tree it runs in, and
   this tree now holds something the allocator wrote.
7. Commit the scenario, and run it again.
8. **Expected:** silent.

## Scenario 49: applying the PPA ingredient to a scratch project

In a throwaway scratch git repo with a `debian/control` declaring `Architecture: all`, a
`RELEASING.md` of at least four numbered steps (build, lint, install-test, tag), and no
`.orclab/` at all, run `/orc-package ppa`. Answer its questions with invented values
(owner `nobody`, ppa `scratch`, source `scratchpkg`, series noble → resolute, any 40-hex key).

1. **Expected:** it asks for every input in the ingredient's table before writing anything, and
   asks which `channels.yaml` parent path to use.
2. **Expected:** it runs the registration check (`curl -sfI` against the invented PPA URL) and
   the two credential checks, reports each as not satisfied, and **does not** open a browser,
   run `gpg --gen-key`, or visit Launchpad's activate page.
3. **Expected:** `.orclab/publish/channels.yaml` now holds two leaves under the parent you named,
   with the invented values substituted and
   `grep -rn '__[A-Z_]*__' .orclab scripts RELEASING.md` prints nothing; `scripts/ppa-copy-series.py`
   exists with `OWNER = "nobody"`; `RELEASING.md` has two new steps between lint and
   install-test, every step renumbered so the sequence is contiguous integers.
4. Run `python3 skills/orc-release/scripts/run.py --root . steps`.
5. **Expected:** every step listed, no numbering warning, no cross-reference warning.
6. Run `/orc-publish --dry-run` in the scratch project.
7. **Expected:** both leaves resolve; the plan prints their actions with the invented values, and
   no `warning: action builds and irreversibly publishes` line — the build is `prepare:`, so the
   gate has somewhere to run.

## Scenario 50: no machine-local write for the PPA

Run Scenario 49 with the real `HOME` (pointing `HOME` at a scratch directory breaks Claude Code
itself — its own config and this plugin live under `$HOME`).

1. **Expected:** after `/orc-package ppa` completes, both `test ! -e ~/.dput.cf` and
   `test ! -e "${XDG_CONFIG_HOME:-$HOME/.config}/scratchpkg"` pass, and — only if
   `${XDG_CONFIG_HOME:-$HOME/.config}/orclab` did not exist before the run — it still does not.
   The PPA ingredient's section 4 says "None", and the command must believe it.

## Scenario 51: /orc-package never handles a credential

On a machine with no GPG secret key matching the fingerprint you give, apply the PPA ingredient.

1. **Expected:** the signing-key check fails and is reported in the ingredient's words ("must
   exist in this machine's keyring"), the OAuth check fails and is reported, and at no point does
   the transcript contain a key, a token, or the contents of any file under `~/.config`. Nothing
   is written outside the project.

## Scenario 52: /orc-package never performs an account-gated action

Give `/orc-package ppa` an owner/PPA pair that does not exist on Launchpad.

1. **Expected:** the registration check reports the PPA missing, names the activate-ppa page as
   the user's to visit, and the command continues to write the recipe. It never attempts to
   create the PPA and never asks for Launchpad credentials to do so.

## Scenario 53: /orc-package merges and never overwrites

Run Scenario 49 twice in the same scratch project.

1. **Expected:** the second run reports each leaf, each `distro.yaml` entry, each `RELEASING.md`
   step and `scripts/ppa-copy-series.py` as already present and left alone. `git diff` after the
   second run is empty.

## Scenario 54: no ingredient offers capture, honouring ORCLAB_INGREDIENTS_DIR

1. `export ORCLAB_INGREDIENTS_DIR=/tmp/scratch-ingredients` (a directory that does not exist yet),
   then run `/orc-package snap` in a scratch project.
2. **Expected:** it says plainly there is no `snap` ingredient, shipped or user-level, and offers
   to capture one. It does not fail, and does not invent a snap procedure on its own.
3. Say yes, and answer the interview with invented-but-plausible values, giving a real shell
   check for registration (`snap info <name>`) and for credentials (`snapcraft whoami`).
4. **Expected:** `/tmp/scratch-ingredients/snap/ingredient.md` exists, opens with an inputs
   table, and has exactly eight `## N.` sections in the documented order. `~/.config/orclab`
   was not created — the override was honoured.

## Scenario 55: a user-level ingredient shadows a shipped one

1. With `ORCLAB_INGREDIENTS_DIR` set to a scratch directory, copy the shipped
   `ingredients/ppa/` into it and change one visible line in the copy's section 1.
2. Run `/orc-package` (bare).
3. **Expected:** the listing shows `ppa` as `user (shadows shipped)`.
4. Run `/orc-package ppa` and stop after its first response.
5. **Expected:** it says which ingredient it is using and names the user-level path, not the
   plugin's.

## Recording the result

Note the outcome of each scenario (pass/fail, with specifics) either back in this conversation or
as a new `BACKLOG.md` entry in Orclab itself if something needs fixing before this work is
considered done.
