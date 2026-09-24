# Cloud plugin-load test 4 — result

**Verdict: it works.** The SessionStart hook (`.claude/hooks/session-start.sh`) created
`~/.claude/skills/orclab -> /home/user/orclab` at **2026-09-24 00:12:39 UTC**, and the
available-skills list this session was handed at start **does** contain `orclab:` entries —
**33 of them**. Those 33 are exactly the 36 skills under `skills/` minus `orc-package`,
`orc-publish` and `orc-release`, which is precisely the expected set: those three and only
those three carry `disable-model-invocation: true`, so they are correctly withheld from
ambient matching while everything else loads. `Skill(orclab:orc-help)` resolved and launched,
reporting a base directory of `/root/.claude/skills/orclab/skills/orc-help` — i.e. the
symlinked path, resolving through the hook's link. The "interesting case" in item 4 (link
present but skills absent, meaning the hook ran too late) **did not occur**: the hook ran
early enough that the skill scan picked the link up. Plugin manifest version at test time:
**0.25.1**, commit `511cdb5`.

---

## 1. Does the available-skills list contain `orclab:` entries?

**Yes — 33 entries.** Several, quoted verbatim from the session-start listing:

```
- orclab:backlog-discipline: Use when a real finding, gap, or deferred decision surfaces that won't be fixed right now but is worth tracking — or when resolving, updating, or considering deletion of an existing BACKLOG.md entry. Maintains a single flat BACKLOG.md with permanent, non-reused entry numbers and layered (not overwritten) resolution history.
```

```
- orclab:orc-help: Use when the user explicitly asks to use orc-help, or types /orc-help, to see Orclab's own running version and a synopsis of its available commands.
```

```
- orclab:orc-code: Use when the user explicitly asks to use orc-code, or types /orc-code, to start a new project, add a feature to an existing project, or refactor/migrate existing code.
```

```
- orclab:orc-git: Use when the user explicitly asks to use orc-git, or types /orc-git, for git and GitHub shortcuts - connecting a repo, committing, pushing, branching, merging a finished branch, checking out a PR, or cutting a GitHub Release from an existing tag.
```

```
- orclab:stack-web: Background knowledge for any work in a web project - a React front end built with Vite in TypeScript, served together with its API by a FastAPI back end in Python, and choosing the framework, the test runner or the storage mechanism for it. Says what the current toolchain is, where things live in the project, and how it is deployed. Not a command; Claude reads it when a web app is in play.
```

```
- orclab:secret-hygiene: Use before running anything that could surface a credential OR bring a new one into existence - debugging auth, reading config/env/log files, dumping environment variables, inspecting keyrings or token stores, sharing command output, or generating a key, token or certificate. Keeps secrets out of the transcript, and gives the recovery procedure when one is exposed anyway.
```

Full list of the 33 `orclab:` names present:

`backlog-discipline`, `car-android-auto`, `car-carplay`, `code-discipline`,
`currency-discipline`, `environment-registry`, `map-openstreetmap`, `orc`, `orc-code`,
`orc-git`, `orc-help`, `orc-reload`, `orc-test`, `orc-todo`, `orc-version`,
`release-checklist`, `secret-hygiene`, `security-discipline`, `source-librewxr`,
`source-road-conditions`, `stack-android-native`, `stack-flutter`, `stack-godot`,
`stack-ios-native`, `stack-kotlin-multiplatform`, `stack-php`, `stack-python-desktop`,
`stack-react-native`, `stack-unity`, `stack-web`, `test-discipline`,
`verify-before-asserting`, `whole-process-first`.

## 2. `Skill` tool call with `orclab:orc-help`

Exact result — the call succeeded. The tool returned:

```
Launching skill: orclab:orc-help
```

and the skill body was delivered, headed with:

```
Base directory for this skill: /root/.claude/skills/orclab/skills/orc-help
```

followed by the real `/orc-help` instructions (Step 1 "Determine context" through Step 4
"Show one command's page, when a name was given"). No error. Note the base directory is the
symlinked path, not `/home/user/orclab/...` — the resolution went through the hook's link.

## 3. Filesystem state and timestamps

`ls -la ~/.claude/skills/`:

```
total 16
drwxr-xr-x  4 root root 4096 Sep 24 00:12 .
drwxr-xr-x 10 root root 4096 Sep 24 00:12 ..
lrwxrwxrwx  1 root root   17 Sep 24 00:12 orclab -> /home/user/orclab
drwxr-xr-x  2 root root 4096 Sep 23 23:46 session-start-hook
drwxr-xr-x  3 root root 4096 Sep 24 00:12 synced
```

`stat -c '%y %n' ~/.claude/skills/orclab`:

```
2026-09-24 00:12:39.179652899 +0000 /root/.claude/skills/orclab
```

`stat -c '%y %n' /home/user/orclab`:

```
2026-09-23 23:46:29.464936698 +0000 /home/user/orclab
```

**Yes, the hook created the link.** The checkout is timestamped 23:46:29 UTC (container
build / repo clone); the symlink is timestamped 00:12:39 UTC, i.e. **26 minutes 10 seconds
later** — at session start, which is when the SessionStart hook runs, not at checkout time.
For scale, the first tool call of this session ran at roughly 00:12:5x and `date -u` a few
calls later read `Thu Sep 24 00:13:04 UTC 2026`, so the link predates the session's first
command by seconds, not minutes.

## 4. The "hook ran too late" case

**Did not occur.** The link exists *and* the skills list contains the `orclab:` entries, so
the hook ran early enough for the skill scan to see it. Both timestamps, restated for the
record:

| thing | mtime (UTC) |
|---|---|
| checkout `/home/user/orclab` | 2026-09-23 23:46:29.464936698 +0000 |
| symlink `~/.claude/skills/orclab` | 2026-09-24 00:12:39.179652899 +0000 |

## 5. Which of the 36 skills are missing from the ambient list

`ls skills/` returns 36 directories. 33 appear as `orclab:` entries. The three missing are:

- `orc-package`
- `orc-publish`
- `orc-release`

**Exactly the expected three, and no others.** Confirmed against the source rather than
assumed — `grep -l 'disable-model-invocation: *true' skills/*/SKILL.md` returns:

```
skills/orc-package/SKILL.md
skills/orc-publish/SKILL.md
skills/orc-release/SKILL.md
```

Same three files, same three names. The withholding is the documented behaviour of that
frontmatter flag (CLAUDE.md, "`disable-model-invocation` and `user-invocable`": *"the skill
becomes invisible to Claude's own ambient judgment ... until explicitly invoked"*), so this
is a correct load, not a partial one. Per that same section the three remain reachable by
explicit invocation; this test did not exercise that path.

## Test conditions

- Repo: `artificialorctelligence/orclab` at `511cdb5` ("Trial: symlink the plugin into
  `~/.claude/skills` from SessionStart"), working tree clean before this file was written.
- Plugin manifest version `0.25.1`.
- Cloud session, `CLAUDE_CODE_REMOTE=true` (the hook's own guard — it exits 0 on a local
  checkout).
- Date of run: 2026-09-24.
