# Cloud test 7 — result

Run 2026-09-24 in a Claude Code cloud session, on Orclab 0.25.1 at commit `a8e9ce8`, with both
mechanisms present: 36 committed symlinks under `.claude/skills/<name>`, and a SessionStart hook
that symlinks the checkout to `~/.claude/skills/orclab`.

## Verdict

**Q1 — the hooks fire. Yes.** `env | grep -i claude` was blocked before it ran, by Orclab's own
`secret_guard` PreToolUse hook, with a message naming secret-hygiene. No variable names or values
were printed, because the command never executed. Adding the home-directory symlink back is what
did it: a previous session proved the committed `.claude/skills/<name>` symlinks load the skills
but not the hooks, and on this run the hooks are loaded and enforcing.

**Q2 — the skills are present twice, 33 of each, and that is refuted only in the count, not the
shape.** The session-start list holds 33 bare-named Orclab skills (`orc-help`, `stack-flutter`, …)
and 33 namespaced ones (`orclab:orc-help`, `orclab:stack-flutter`, …) — 66 entries for 36 skills on
disk. The expectation of "roughly 33 each" is confirmed. The gap between 36 and 33 is not a loading
failure: the three absent from *both* lists are `orc-package`, `orc-publish` and `orc-release`,
which each carry `disable-model-invocation: true`, so by design their descriptions are withheld
from the ambient list until explicitly invoked.

**Q3 — nothing is broken by having both.** `claude plugin list` exits 0 and reports a single
plugin, `orclab@skills-dir` 0.25.1, status "loaded". No error, no warning, no duplicate-name
complaint anywhere in its output. `~/.claude/skills/orclab` exists as a symlink to
`/home/user/orclab`, created about two seconds after the checkout.

**Q4 — the hook set registered, not just one hook.** `lint_on_write` fired too, on a different
event (`PostToolUse` vs `secret_guard`'s `PreToolUse`), so this is the whole set loading rather
than a single lucky hook. It took two attempts to see it, and the first attempt is itself a
result: a file written to `/tmp` produced no reaction, which is the hook behaving correctly, not
failing — it lints only when the project has the tool's config file between the written file and
the repo root, and `/tmp` has none. Written inside the repo, where `pyproject.toml` and `ruff` both
exist, it blocked the write and reported both unused imports.

---

## Q1 — do the hooks fire now?

Command run:

    env | grep -i claude

What happened, verbatim:

    PreToolUse:Bash hook error: A bare `env`/`printenv` dumps every variable, including any
    credentials. For a comparison use keys only: env | sed -E 's/=.*//'. For one variable, test
    presence: [ -n "$VAR" ] && echo set. See secret-hygiene. If this is genuinely required,
    re-run with a trailing `# orclab:allow-secret`.

**Blocked by a hook, with a message mentioning secret-hygiene.** It did not run and printed
nothing — no variable names, no values. The hooks DID load.

The block was not re-attempted with the `# orclab:allow-secret` escape hatch: the point of the
test was whether the guard fires, and it did.

## Q2 — are the skills present twice?

Both sets are present. Counted from this session's available-skills list:

| | Count |
|---|---|
| Bare-named Orclab skills | 33 |
| Namespaced (`orclab:`) Orclab skills | 33 |
| Orclab skill directories on disk | 36 |
| Committed symlinks in `.claude/skills/` | 36 |

Bare-named, quoted from the list:

- `orc-help: Use when the user explicitly asks to use orc-help, or types /orc-help, to see
  Orclab's own running version and a synopsis of its available commands.`
- `secret-hygiene: Use before running anything that could surface a credential OR bring a new one
  into existence …`

Namespaced, quoted from the list:

- `orclab:orc-help: Use when the user explicitly asks to use orc-help, or types /orc-help, to see
  Orclab's own running version and a synopsis of its available commands.`
- `orclab:secret-hygiene: Use before running anything that could surface a credential OR bring a
  new one into existence …`

The two sets carry identical descriptions, one entry per skill per set.

**Why 33 and not 36.** `ls skills/` and `ls .claude/skills/` both return 36. The three that appear
in neither list are `orc-package`, `orc-publish` and `orc-release`. Those are exactly the three
side-effecting skills that carry `disable-model-invocation: true`, which by design keeps a skill's
description out of the ambient list until it is explicitly invoked. So the absence is the flag
working, not a loading failure, and it is symmetric across both sets — which is itself evidence
that both sets are loading through the same path and reading the same frontmatter.

## Q3 — anything broken by having both?

`claude plugin list`, exit code 0, complete output:

    Skills-directory plugins (.claude/skills/*):

      > orclab@skills-dir
        Version: 0.25.1
        Scope: user
        Path: ~/.claude/skills/orclab
        Status: √ loaded

**No error, no warning, no duplicate-name complaint.** Notably it reports one plugin, not two —
the two skill sets do not surface here as competing installs. The `Path` it names is the home
symlink, not the committed `.claude/skills/<name>` entries.

`ls -la ~/.claude/skills/`:

    total 16
    drwxr-xr-x  4 root root 4096 Sep 24 04:32 .
    drwxr-xr-x 10 root root 4096 Sep 24 04:32 ..
    lrwxrwxrwx  1 root root   17 Sep 24 04:32 orclab -> /home/user/orclab
    drwxr-xr-x  2 root root 4096 Sep 23 23:46 session-start-hook
    drwxr-xr-x  3 root root 4096 Sep 24 04:32 synced

`stat -c '%y %n' /home/user/orclab ~/.claude/skills/orclab`:

    2026-09-24 04:32:26.768472674 +0000 /home/user/orclab
    2026-09-24 04:32:28.813105669 +0000 /root/.claude/skills/orclab

The symlink is 2.04 seconds newer than the checkout — consistent with the SessionStart hook
creating it immediately after the repo was cloned. (`~` resolves to `/root` here.)

## Q4 — a second hook check

`lint_on_write` is registered as a `PostToolUse` hook matching `Edit|Write|MultiEdit` in
`hooks/hooks.json`, so it needs a real Write-tool call rather than a shell heredoc.

**First attempt — `/tmp/lintcheck.py`, two unused imports plus an unused local. Nothing reacted.**

That is the hook working as designed, and it is worth recording rather than scoring as a failure.
Its own docstring states the gate: *"A language is linted only when both hold: the tool is on
PATH, and the project has that tool's config file somewhere between the written file and the repo
root. No config, no run."* `/tmp` has no `pyproject.toml` above it, so the correct behaviour is to
exit 0 and say nothing. Reporting this as "the hook didn't fire" would have been wrong.

**Second attempt — the same content written to `lintcheck_tmp.py` at the repo root**, where
`pyproject.toml` sits and `ruff` is on PATH at `/root/.local/bin/ruff`. It reacted, blocking:

    PostToolUse:Write hook blocking error from command:
    "python3 "/root/.claude/skills/orclab/hooks/scripts/lint_on_write.py"":
    orclab lint_on_write: `ruff check` on /home/user/orclab/lintcheck_tmp.py exited 1 -
    code-discipline's checkable rules, from the project's own config.
    Set ORCLAB_LINT_ON_WRITE_OFF=1 to disable.
    error[F401][*]: `os` imported but unused
    error[F401][*]: `sys` imported but unused
    Found 2 errors.

    This hook comes from the orclab@skills-dir plugin.

Two things this settles beyond "one hook works":

1. **A different event class fired.** `secret_guard` is `PreToolUse`/`Bash`; `lint_on_write` is
   `PostToolUse`/`Write`. Two separate registrations from the same `hooks.json` both took effect,
   so the hook *set* registered, not one entry.
2. **The resolved path names the mechanism under test.** The hook ran from
   `/root/.claude/skills/orclab/hooks/scripts/lint_on_write.py` — through the home symlink the
   SessionStart hook created — and the runtime attributes it to `the orclab@skills-dir plugin`.
   That is direct evidence the home symlink, not the committed `.claude/skills/<name>` symlinks,
   is what carries the hooks.

Both throwaway files (`/tmp/lintcheck.py` and `lintcheck_tmp.py`) were deleted; `git status` is
clean apart from this result file.

## What this test establishes

Adding the SessionStart home symlink back **restores the plugin's hooks**, and does so without
breaking anything the committed symlinks were already providing. The cost is that every skill
appears twice in the available-skills list — 66 entries for 36 skills — which consumes context but
produced no error, no warning, and no name collision in `claude plugin list`.
