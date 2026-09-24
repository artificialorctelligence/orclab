# Cloud test 6 result

**Verdict.** **Q1 — the skills load: YES.** This cloud session started with 33 of Orclab's
36 committed `.claude/skills/` entries present in its available-skills list, and they are
named **bare** (`orc-help`, `orc-code`, `stack-flutter`) — **not** namespaced
(`orclab:orc-help`). The three absent ones are exactly `orc-package`, `orc-publish` and
`orc-release`, the three that carry `disable-model-invocation: true`, so their absence from
the *ambient* list is the flag working as designed, not a loading failure. **Q2 — the hooks
do NOT load: NO, they did not.** `env | grep -i claude` ran normally and printed 52 variable
names; nothing blocked it, and no secret-hygiene message appeared. A negative control run in
the same session shows `secret_guard.py` itself is present and *would* have denied that exact
command — so the script works and was simply never invoked. A repo's `.claude/skills/`
directory carries skills only; `hooks/hooks.json` is plugin machinery and is not read from a
skills directory. **Q3 — the environment setup script did NOT take effect this time either.**
`~/.claude/skills/orclab` does not exist; `stat` reports `No such file or directory`. The
earlier session's finding reproduces.

---

## Q1 — Do Orclab's skills load?

### What's on disk

`.claude/skills/` holds 36 committed symlinks, each pointing at `../../skills/<name>`:

```
$ git ls-files .claude/skills | wc -l
36
$ git ls-files -s .claude/skills | head -3
120000 3ab555e7a966324e0086b2c6f2031e4fd3f2bd85 0	.claude/skills/backlog-discipline
120000 0c8825eed4d89762fdd1c9aab7485a4923799ef3 0	.claude/skills/car-android-auto
120000 b685f5ac1b490ba66af6df35df727241f1d11ff4 0	.claude/skills/car-carplay
```

(Mode `120000` = symlink, so they are committed as symlinks, not as copied directories.)

### What the session actually received

The session-start available-skills list contains Orclab's skills. Verbatim matching lines,
several of many:

```
- orc-help: Use when the user explicitly asks to use orc-help, or types /orc-help, to see
  Orclab's own running version and a synopsis of its available commands.
- orc-code: Use when the user explicitly asks to use orc-code, or types /orc-code, to start
  a new project, add a feature to an existing project, or refactor/migrate existing code.
- orc-git: Use when the user explicitly asks to use orc-git, or types /orc-git, for git and
  GitHub shortcuts - connecting a repo, committing, pushing, branching, merging a finished
  branch, checking out a PR, or cutting a GitHub Release from an existing tag.
- orc-version: Use when the user explicitly asks to use orc-version, or types /orc-version,
  to set or increment the current project's version, draft a changelog entry, and tag the
  commit locally - or, with no arguments, to be told what bump the commits since the last
  tag suggest and why.
- backlog-discipline: Use when a real finding, gap, or deferred decision surfaces that won't
  be fixed right now but is worth tracking ...
- secret-hygiene: Use before running anything that could surface a credential OR bring a new
  one into existence ...
- stack-flutter: Background knowledge for any work in a Flutter/Dart project ...
- test-discipline: Background rules for any test Claude is about to write or change ...
```

### NAMING — bare, not namespaced

**They are bare.** The list reads `orc-help`, not `orclab:orc-help`. Not one entry carries an
`orclab:` prefix. For contrast, the same list *does* show namespaced entries for genuine
plugin-provided skills from another source — `anthropic-skills:docs`, `anthropic-skills:pptx`,
`anthropic-skills:skill-creator`. So the namespacing distinction is live in this session, and
Orclab's skills land on the bare side of it: they are loading as **project directory skills**,
the same way a `.claude/skills/` folder of loose skills would, **not as a plugin**.

That is the substantive finding behind Q1. The skills arrived, but they arrived stripped of
plugin identity.

### Count

| | |
|---|---|
| Symlinks committed in `.claude/skills/` | 36 |
| Present in the session's available-skills list | **33** |
| Absent | **3** |

The three absent: `orc-package`, `orc-publish`, `orc-release`.

All three, and only these three, carry `disable-model-invocation: true`:

```
$ head -8 skills/orc-publish/SKILL.md
---
name: orc-publish
description: Use when the user explicitly asks to use orc-publish, or types /orc-publish, ...
disable-model-invocation: true
allowed-tools: Bash(python3 *)
---
```

`orc-package` and `orc-release` are identical in this respect. Per `CLAUDE.md`'s own table,
that flag means the skill's *description is not in context ambiently* until it is explicitly
invoked — so their absence from this list is the documented, intended behavior and is
**not** evidence of a loading gap. Effective load rate for Q1 purposes: 36 of 36.

---

## Q2 — Do the plugin's HOOKS load? (the important one)

### The command, run verbatim

```
$ env | grep -i claude
```

**It was NOT blocked. It ran normally and printed 52 environment variable names.** No hook
fired, no permission-deny message, no mention of secret hygiene. Names only, values omitted:

```
AI_AGENT                            CLAUDE_CODE_ENVIRONMENT_RUNNER_VERSION
CLAUDECODE                          CLAUDE_CODE_EXECPATH
CLAUDE_ADDITIONAL_DIRECTORIES       CLAUDE_CODE_GZIP_REQUEST_BODIES
CLAUDE_AFTER_LAST_COMPACT           CLAUDE_CODE_HOLD_UNANSWERED_PARKED_PERMISSION
CLAUDE_AUTOCOMPACT_PCT_OVERRIDE     CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH
CLAUDE_AUTO_BACKGROUND_TASKS        CLAUDE_CODE_MESSAGING_SOCKET
CLAUDE_CODE_ACCOUNT_UUID            CLAUDE_CODE_MESSAGING_TOKEN
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD
                                    CLAUDE_CODE_ORGANIZATION_UUID
CLAUDE_CODE_ARTIFACT_ASSETS         CLAUDE_CODE_POST_FOR_SESSION_INGRESS_V2
CLAUDE_CODE_ARTIFACT_DB             CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST
CLAUDE_CODE_ARTIFACT_MULTI_FILE     CLAUDE_CODE_PROXY_RESOLVES_HOSTS
CLAUDE_CODE_ARTIFACT_TYPES          CLAUDE_CODE_REMOTE
CLAUDE_CODE_ARTIFACT_TYPE_CATALOG   CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE
CLAUDE_CODE_ARTIFACT_TYPE_CLOUD_CREATE
                                    CLAUDE_CODE_REMOTE_HERMETIC_MODE
CLAUDE_CODE_BASE_REF                CLAUDE_CODE_REMOTE_SEND_KEEPALIVES
CLAUDE_CODE_BG_TASKS_REPORT_RUNNING CLAUDE_CODE_REMOTE_SESSION_ID
CLAUDE_CODE_CHILD_SESSION           CLAUDE_CODE_SESSION_ATTENDED
CLAUDE_CODE_CONTAINER_ID            CLAUDE_CODE_SESSION_ID
CLAUDE_CODE_DEBUG                   CLAUDE_CODE_SYNC_SESSION_REFS
CLAUDE_CODE_DIAGNOSTICS_FILE        CLAUDE_CODE_SYNC_SKILLS
CLAUDE_CODE_DISABLE_BUILTIN_ANTMCP  CLAUDE_CODE_TEE_SDK_STDOUT
CLAUDE_CODE_ENTRYPOINT              CLAUDE_CODE_USER_EMAIL
CLAUDE_CODE_USE_CCR_V2              CLAUDE_CODE_VERSION
CLAUDE_CODE_WORKER_EPOCH            CLAUDE_EFFORT
CLAUDE_ENABLE_STREAM_WATCHDOG       CLAUDE_PID
CLAUDE_SESSION_INGRESS_TOKEN_FILE   DOCUMENTS_MCP_SCRATCH_ROOT
```

**Plainly: the hooks did NOT load.** A `.claude/skills/` directory carries skills, and only
skills.

### Negative control — the guard is not broken, it was never called

Per `CLAUDE.md`'s own rule about negative controls, "it didn't block" is only evidence if the
blocker would otherwise have blocked. Feeding `secret_guard.py` the exact tool payload by hand,
in this same container:

```
$ echo '{"tool_name":"Bash","tool_input":{"command":"env | grep -i claude"}}' \
    | python3 hooks/scripts/secret_guard.py
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
 "permissionDecisionReason": "A bare `env`/`printenv` dumps every variable, including any
 credentials. For a comparison use keys only: env | sed -E 's/=.*//'. ... See secret-hygiene.
 If this is genuinely required, re-run with a trailing `# orclab:allow-secret`."}}
```

The script is present, executable, and returns `deny` for precisely this command. It was
simply never invoked. That isolates the failure to hook *registration*, not hook *code*.

### Why — the mechanism

Orclab declares all four hooks in `hooks/hooks.json`, and every command in it is written as
`python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/<name>.py"`:

- `SessionStart` → `lane_notice.py`
- `PreToolUse` on `Bash` → `secret_guard.py`, `backlog_guard.py`
- `PreToolUse` on `Agent|Task` → `model_floor.py`
- `PostToolUse` on `Edit|Write|MultiEdit` → `lint_on_write.py`

Two independent reasons none of that ran:

1. **Nothing in this repo points the harness at `hooks/hooks.json`.** That file is read from a
   plugin manifest. There is no `.claude/settings.json` in this repo at all
   (`cat: .claude/settings.json: No such file or directory`), and `.claude/` contains exactly
   one thing — `skills/`. So the hook declarations are never reached.
2. **Orclab is not installed as a plugin here**, so `${CLAUDE_PLUGIN_ROOT}` has no value in
   this session even if the file were read (see `claude plugin list` below).

This is consistent with Q1: the skills came in as *project skills*, stripped of plugin
identity — and hooks are exactly the part of plugin identity that a skills directory has no
way to carry.

---

## Q3 — Did the environment's setup script run this time?

The setup script was set to:

```
mkdir -p ~/.claude/skills && ln -sfn /home/user/orclab ~/.claude/skills/orclab
```

**It did not take effect. There is no `orclab` symlink.**

```
$ echo $HOME
/root
$ ls -la ~/.claude/skills/
total 16
drwxr-xr-x  4 root root 4096 Sep 24 04:18 .
drwxr-xr-x 10 root root 4096 Sep 24 04:18 ..
drwxr-xr-x  2 root root 4096 Sep 23 23:46 session-start-hook
drwxr-xr-x  3 root root 4096 Sep 24 04:18 synced

$ stat -c '%y %n' ~/.claude/skills/orclab 2>&1
stat: cannot statx '/root/.claude/skills/orclab': No such file or directory
```

**No timestamp to report — the path does not exist.** The earlier session's finding reproduces
exactly. The directory `~/.claude/skills/` itself exists, but it was created by the harness
(its two entries are `session-start-hook` and the harness's own `synced/` bucket), not by the
setup script's `mkdir -p`.

Note the `$HOME` value: this session runs as `root`, so `~` is `/root`, and the checked path is
`/root/.claude/skills/orclab`. If the setup script ran as a different user, its symlink would
have landed in that user's home instead — but either way, it is not visible to the session that
needs it, which is the outcome that matters.

---

## `claude plugin list`

```
$ claude plugin list
No plugins installed. Use `claude plugin install` to install a plugin.
```

Corroborated by the on-disk registry:

```
$ cat ~/.claude/plugins/installed_plugins.json
{
  "version": 2,
  "plugins": {}
}
```

Orclab is not installed as a plugin in this session, by any route.

---

## Summary table

| Question | Answer | Evidence |
|---|---|---|
| Q1 — skills load? | **Yes**, 33 listed of 36 committed; the 3 absent are the 3 with `disable-model-invocation: true` | available-skills list quoted above |
| Q1 — naming? | **Bare** (`orc-help`), **not** namespaced (`orclab:orc-help`) — they load as project skills, not as a plugin | contrast with `anthropic-skills:docs` in the same list |
| Q2 — hooks load? | **No** | `env \| grep -i claude` ran and printed 52 names, unblocked; `secret_guard.py` returns `deny` for the same input when called by hand |
| Q3 — setup script symlink? | **No** — `~/.claude/skills/orclab` does not exist | `stat` → `No such file or directory` |
| `claude plugin list` | `No plugins installed.` | also `installed_plugins.json` → `"plugins": {}` |

## What this establishes

Anthropic's documented `.claude/skills/` route works, and works for symlinks — a committed
symlink farm is enough to get 36 skills into a cloud session with no SessionStart hook and no
plugin install. But it delivers **skills only, and delivers them unnamespaced**. Orclab's four
hooks — `secret_guard`, `backlog_guard`, `model_floor`, `lint_on_write` — do not come with
them, and no amount of `.claude/skills/` content will bring them, because hooks are declared in
plugin machinery a skills directory does not read.

Repo state at the time of this test: `orclab` v0.25.1, at commit `02679eb`
("Ship Orclab's skills to cloud sessions the documented way").
