# Cloud plugin-load test 2: SessionStart hook

**Session:** cloud (`CLAUDE_CODE_REMOTE=true`), container started 2026-09-23 ~23:50 UTC
**Checkout:** `/home/user/orclab`, detached HEAD at `55dcca5` ("Trial: install Orclab from a SessionStart hook for cloud sessions")

## Verdict: (b) — the hook DID run, and this session still cannot see the plugin's skills

`claude plugin list` reports `orclab@orclab` version 0.25.1, scope user, enabled. The marketplace
is registered by directory path `/home/user/orclab`. The plugin cache holds all 36 skill
directories, `orc-help` among them. File timestamps put the marketplace registration at
23:50:15.806 and the install at 23:50:16.920, 2.3 and 3.5 seconds after the repo checkout's own
mtime (23:50:13.469) — the hook fired, in order, immediately after checkout. Despite that, the
available-skills list this session was given at start contains no `orclab:` or `orc-` entry, and
the `Skill` tool rejects both `orclab:orc-help` and the bare `orc-help` with `Unknown skill`. So
the hook is doing its job at the filesystem level and the session's skill registry was assembled
either before the install finished or from a source that the install does not feed. This is the
same class of failure recorded in `CLAUDE.md` under "A freshly (re)installed plugin does not
become available mid-conversation" — except here the install happens at SessionStart, before the
first turn, and still misses.

---

## 1. Available-skills list at session start

**No entry starts with `orclab:` or `orc-`.** Nothing matched. Three verbatim lines from the list
this session actually has:

```
- session-start-hook: Creating and developing startup hooks for Claude Code on the web. Use when the user wants to set up a repository for Claude Code on the web, create a SessionStart hook to ensure their project can run tests and linters during web sessions.
- dataviz: Use this skill whenever you are about to create ANY chart, graph, plot, dashboard, or data visualization, in ANY output medium [...]
- anthropic-skills:skill-creator: Create new skills, modify and improve existing skills, and measure skill performance. [...]
```

The full list is: `session-start-hook`, `dataviz`, `artifact-design`, `artifact-diagramming`,
`artifact-capabilities`, `update-config`, `keybindings-help`, `code-review`, `simplify`,
`fewer-permission-prompts`, `loop`, `claude-api`, `workflow-authoring`, `run`, `init`,
`security-review`, and the `anthropic-skills:*` set (`docs`, `docx`, `import-memory`, `morning`,
`notepadpp-code-reader`, `pdf`, `pptx`, `skill-creator`, `xlsx`). Every one of these is
environment-provided; none comes from this repo.

## 2. `Skill` tool call

Namespaced form:

```
Skill(skill="orclab:orc-help")
→ Unknown skill: orclab:orc-help
```

Bare form, tried as a control:

```
Skill(skill="orc-help")
→ Unknown skill: orc-help
```

## 3. `claude plugin list` / `claude plugin marketplace list`

```
$ claude plugin list
Installed plugins:

  > orclab@orclab
    Version: 0.25.1
    Scope: user
    Status: √ enabled

$ claude plugin marketplace list
Configured marketplaces:

  > orclab
    Source: Directory (/home/user/orclab)
```

Both exited 0.

## 4. Config files

```
$ cat ~/.claude/settings.json
{
  "extraKnownMarketplaces": {
    "orclab": {
      "source": {
        "source": "directory",
        "path": "/home/user/orclab"
      }
    }
  },
  "enabledPlugins": {
    "orclab@orclab": true
  }
}
```

```
$ cat ~/.claude/plugins/installed_plugins.json
{
  "version": 2,
  "plugins": {
    "orclab@orclab": [
      {
        "scope": "user",
        "installPath": "/root/.claude/plugins/cache/orclab/orclab/0.25.1",
        "version": "0.25.1",
        "installedAt": "2026-09-23T23:50:16.920Z",
        "lastUpdated": "2026-09-23T23:50:16.920Z",
        "gitCommitSha": "55dcca5a8c5995a57f55b568c506152dbd825811"
      }
    ]
  }
}
```

Note the `gitCommitSha` matches this checkout's HEAD exactly — the install came from this working
tree, not from GitHub.

## 5. Evidence the hook fired

### Repo-side hook registration

```
$ cat .claude/settings.json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"
          }
        ]
      }
    ]
  }
}
```

The hook script guards on `CLAUDE_CODE_REMOTE != "true"` and exits early otherwise. In this
session `CLAUDE_CODE_REMOTE=true`, so the guard passed.

### Timestamps — the strongest evidence, since the hook itself logs nothing

```
2026-09-23 23:50:13.469005738 +0000 /home/user/orclab/.claude/hooks/session-start.sh
2026-09-23 23:50:15.809005877 +0000 /root/.claude/plugins/known_marketplaces.json
2026-09-23 23:50:16.737763441 +0000 /root/.claude/settings.json
2026-09-23 23:50:16.897005942 +0000 /root/.claude/plugins/cache/orclab/orclab/0.25.1
2026-09-23 23:50:16.921005943 +0000 /root/.claude/plugins/installed_plugins.json
```

Checkout, then marketplace add 2.3s later, then install 3.5s later — the hook's two commands in
their written order. `known_marketplaces.json` records `"lastUpdated": "2026-09-23T23:50:15.806Z"`
and an `installLocation` of `/home/user/orclab`, i.e. the directory-path registration the hook
performs, not a GitHub-sourced one.

### `~/.claude/` contents

```
$ ls -la ~/.claude/
total 96
drwxr-xr-x 10 root root  4096 Sep 23 23:50 .
drwx------ 15 root root  4096 Sep 23 23:50 ..
-rw-r--r--  1 root root    24 Sep 23 23:50 .last-cleanup
drwxr-xr-x  2 root root  4096 Sep 23 23:50 backups
drwxr-xr-x  2 root root  4096 Sep 23 23:50 environment-manager
-rw-------  1 root root   442 Sep 23 23:50 launcher-settings.json
drwxr-xr-x  5 root root  4096 Sep 23 23:50 plugins
-rw-------  1 root root   214 Sep 23 23:50 policy-limits.json
-rw-------  1 root root   223 Sep 23 23:50 policy-limits.json.stamp.json
drwx------  3 root root  4096 Sep 23 23:50 projects
-rw-------  1 root root     2 Sep 23 23:50 remote-settings.json
drwxr-xr-x  3 root root  4096 Sep 23 23:50 session-env
drwx------  2 root root  4096 Sep 23 23:50 sessions
-rw-r--r--  1 root root   206 Sep 23 23:50 settings.json
drwxr-xr-x  2 root root  4096 Sep 23 23:50 shell-snapshots
drwxr-xr-x  4 root root  4096 Sep 23 23:50 skills
-rwxr-xr-x  1 root root  6395 Sep 23 23:50 stop-hook-git-check.sh
-rwxr-xr-x  1 root root 17848 Sep 23 23:50 stop-hook-reply-gate.py
-rwxr-xr-x  1 root root  3630 Sep 23 23:50 user-prompt-submit-reply-reminder.py
```

`~/.claude/skills/` holds only `session-start-hook` and a `synced/` directory — the
environment-provided skills. Orclab's skills are not there; they live only in the plugin cache.

### `~/.claude/projects/`

```
/root/.claude/projects/-home-user-orclab:
drwx------ 2 root root   4096 Sep 23 23:50 d1881a67-cac2-5738-a0dd-52e654c7a238
-rw------- 1 root root 182907 Sep 23 23:50 d1881a67-cac2-5738-a0dd-52e654c7a238.jsonl
```

The session transcript contains no `hookEventName` records at all (`grep -o
'"hookEventName":"[^"]*"'` returned nothing), and every `session-start` string in it comes from
this task's own prompt and this session's own tool calls. **No hook-execution log exists** — the
hook script redirects both commands to `/dev/null` and the transcript does not record SessionStart
hook output. The timestamp chain above is therefore the evidence, and it is unambiguous.

### The plugin cache does contain the skills

```
$ ls ~/.claude/plugins/cache/orclab/orclab/0.25.1/skills
backlog-discipline        orc-package               stack-godot
car-android-auto          orc-publish               stack-ios-native
car-carplay               orc-release               stack-kotlin-multiplatform
code-discipline           orc-reload                stack-php
currency-discipline       orc-test                  stack-python-desktop
environment-registry      orc-todo                  stack-react-native
map-openstreetmap         orc-version               stack-unity
orc                       release-checklist         stack-web
orc-code                  secret-hygiene            test-discipline
orc-git                   security-discipline       verify-before-asserting
orc-help                  source-librewxr           whole-process-first
                          source-road-conditions
```

36 skill directories, `orc-help` present. The files are on disk and correct; the session's skill
registry simply never picked them up.

## What this rules in and out

- **Not (a).** The hook ran, both its commands succeeded, and their effects are on disk.
- **Not a marketplace-auth problem.** The directory-path registration sidestepped the GitHub API
  entirely, exactly as `CLAUDE.md`'s gotcha #2 prescribes, and it worked.
- **Not a stale-clone problem** (gotcha #3). `gitCommitSha` matches HEAD.
- **It is the load-timing boundary.** A cloud session's available-skills list is assembled from
  whatever plugins are installed at the moment the session's context is built, and SessionStart
  hook output does not reopen that list. Installing during SessionStart is still too late — the
  same wall `CLAUDE.md` records for mid-session installs, hit three seconds earlier.

The implication for the repo: a SessionStart hook cannot make Orclab's own skills available to the
session that runs it. Making them available in cloud sessions needs the install to happen before
the session exists — the cloud environment's setup script rather than a repo-side hook — or needs
the components reachable by plain file read rather than through the skill registry.
