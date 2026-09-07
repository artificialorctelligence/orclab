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

## Recording the result

Note the outcome of each scenario (pass/fail, with specifics) either back in this conversation or
as a new `BACKLOG.md` entry in Orclab itself if something needs fixing before this work is
considered done.
