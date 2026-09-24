# Cloud plugin-load test 3: the setup script symlink

**Verdict: no.** The setup script did not make Orclab's skills available to this
session. My session-start skills list contains zero `orclab:` entries; the `Skill`
tool answers `Unknown skill: orclab:orc-help` (and `Unknown skill: orc-help` for
the bare form); all 36 skills are missing, not just the three with
`disable-model-invocation: true`; and `claude plugin list` reports `No plugins
installed.` The reason is visible on disk and is not subtle: **the symlink does
not exist.** This session runs as `root` with `HOME=/root`, so `~/.claude/skills`
resolves to `/root/.claude/skills`, and that directory holds only
`session-start-hook` and `synced/` — no `orclab` entry, symlink or otherwise.
`/home/user/.claude` does not exist either, so the link was not created under the
`user` home and missed by the `$HOME` difference; it is simply absent everywhere.
Either the setup script ran before the `/root/.claude` tree was created (and was
overwritten when it was — note every path under `/root/.claude` carries the same
`Sep 24 00:09` timestamp as the checkout itself, i.e. the harness laid that tree
down at session start), or it did not run at all. Nothing here distinguishes
those two, but the outcome is the same: the skills were not handed to me.

---

## 1. `orclab:` entries in the session-start available-skills list

**None.** The available-skills list the harness gave me at session start contains
no entry beginning with `orclab:`, and no entry matching any of the 36 skill
directory names in this repo. Count of matching lines: **0**.

Three verbatim lines from the list I do have, for reference:

```
- session-start-hook: Creating and developing startup hooks for Claude Code on the web. Use when the user wants to set up a repository for Claude Code on the web, create a SessionStart hook to ensure their project can run tests and linters during web sessions.
- dataviz: Use this skill whenever you are about to create ANY chart, graph, plot, dashboard, or data visualization, in ANY output medium — an HTML or React artifact, inline SVG, plotting code in any library (matplotlib, plotly, d3, Recharts, …), an image/PNG you will render and upload, or a chart shared into Slack. Read it BEFORE writing the first line of chart code, choosing chart colors, building a stat tile / meter / KPI row, or laying out a dashboard.
- artifact-design: Design guidance and fundamentals for Artifacts. - Load before writing any artifact, including a skill-instructed Markdown one - Markdown is never a shortcut past the design pass.
```

The full list is: `session-start-hook`, `dataviz`, `artifact-design`,
`artifact-diagramming`, `artifact-capabilities`, `update-config`,
`keybindings-help`, `code-review`, `simplify`, `fewer-permission-prompts`,
`loop`, `claude-api`, `workflow-authoring`, `run`, `anthropic-skills:docs`,
`anthropic-skills:import-memory`, `anthropic-skills:morning`,
`anthropic-skills:notepadpp-code-reader`, `anthropic-skills:skill-creator`,
`anthropic-skills:xlsx`, `anthropic-skills:pptx`, `anthropic-skills:pdf`,
`anthropic-skills:docx`, `init`, `security-review`. The only namespaced prefix
present is `anthropic-skills:`, which corresponds to
`/root/.claude/skills/synced/<bucket>/` on disk — so namespaced skills *can*
appear here; Orclab's simply are not among them.

## 2. `Skill` tool call

Called with skill `orclab:orc-help`:

```
<tool_use_error>Unknown skill: orclab:orc-help</tool_use_error>
```

Also tried the bare form, `orc-help`:

```
<tool_use_error>Unknown skill: orc-help</tool_use_error>
```

## 3. Which of the 36 are missing

**All 36.** This is not the `disable-model-invocation` filter — that hypothesis
predicts exactly three absences (`orc-package`, `orc-publish`, `orc-release`)
and 33 present. The observed count is 36 absent, 0 present, so the flag is not
in play at all; nothing from this repo was loaded.

Full set from `ls /home/user/orclab/skills/` (36 entries), every one of which is
missing from my ambient list:

```
backlog-discipline
car-android-auto
car-carplay
code-discipline
currency-discipline
environment-registry
map-openstreetmap
orc
orc-code
orc-git
orc-help
orc-package
orc-publish
orc-release
orc-reload
orc-test
orc-todo
orc-version
release-checklist
secret-hygiene
security-discipline
source-librewxr
source-road-conditions
stack-android-native
stack-flutter
stack-godot
stack-ios-native
stack-kotlin-multiplatform
stack-php
stack-python-desktop
stack-react-native
stack-unity
stack-web
test-discipline
verify-before-asserting
whole-process-first
```

## 4. Filesystem state

`echo "HOME=$HOME  USER=$(whoami)"`:

```
HOME=/root  USER=root
```

`ls -la ~/.claude/skills/` (i.e. `/root/.claude/skills/`):

```
total 16
drwxr-xr-x  4 root root 4096 Sep 24 00:09 .
drwxr-xr-x 10 root root 4096 Sep 24 00:09 ..
drwxr-xr-x  2 root root 4096 Sep 23 23:46 session-start-hook
drwxr-xr-x  3 root root 4096 Sep 24 00:09 synced
```

`ls ~/.claude/skills/orclab/`:

```
ls: cannot access '/root/.claude/skills/orclab/': No such file or directory
```

`stat -c '%y %n' /home/user/orclab ~/.claude/skills/orclab`:

```
2026-09-24 00:09:18.630267273 +0000 /home/user/orclab
stat: cannot statx '/root/.claude/skills/orclab': No such file or directory
```

There is no symlink, so there is no symlink timestamp to compare against the
checkout's. What the checkout's own timestamp does show: `/home/user/orclab`
was last modified at `00:09:18`, the same minute as every directory under
`/root/.claude`, including `skills/` itself (`00:09`) — while
`skills/session-start-hook`, which predates this session, carries `23:46` from
the previous day. In other words the harness created (or recreated) the
`~/.claude/skills` directory at session start at 00:09, and nothing named
`orclab` survived into it.

`ls -la /home/user/.claude/`:

```
ls: cannot access '/home/user/.claude/': No such file or directory
```

So the link was not created under the `user` home either — this is not a
`$HOME`-mismatch story where the file exists somewhere I did not look.

Full `find /root/.claude/skills -maxdepth 3` (no `orclab` anywhere):

```
/root/.claude/skills
/root/.claude/skills/session-start-hook
/root/.claude/skills/session-start-hook/SKILL.md
/root/.claude/skills/synced
/root/.claude/skills/synced/.bucket-b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/import-memory
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/notepadpp-code-reader
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/skill-creator
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/morning
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/manifest.json
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/docx
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/xlsx
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/docs
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/pptx
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/pdf
```

That `synced/` bucket is exactly the eight `anthropic-skills:*` entries in my
ambient list, which confirms the loader does read `~/.claude/skills/` — it read
that subtree and surfaced it. It just had no `orclab` to read.

## 5. `claude plugin list`

`which claude`:

```
/opt/node22/bin/claude
```

`claude plugin list`:

```
No plugins installed. Use `claude plugin install` to install a plugin.
```

`cat /root/.claude/plugins/installed_plugins.json`:

```json
{
  "version": 2,
  "plugins": {}
}
```

Expected — the setup script attempted a skills-directory symlink, not a plugin
install, so an empty plugin list does not by itself contradict the approach. It
is recorded because it rules out a stale install from an earlier test being the
thing that loaded (or failed to load) anything.

---

## What this rules in and out

- **Not the `disable-model-invocation` filter.** That predicts 3 absent / 33
  present. Observed: 36 absent.
- **Not a `$HOME` mismatch.** `/home/user/.claude` does not exist; the link is
  absent from both candidate homes.
- **Not the loader ignoring `~/.claude/skills/`.** It demonstrably read that
  directory — the eight `anthropic-skills:*` entries in my ambient list come
  from `synced/` underneath it.
- **Not a plugin-vs-skill namespacing problem.** A namespaced prefix
  (`anthropic-skills:`) does appear in my list, so the mechanism works; there
  was nothing to namespace.
- **Remaining live possibilities**, which this session cannot distinguish: the
  setup script did not run; or it ran and its `mkdir -p`/`ln -sfn` were
  subsequently clobbered when the harness laid down `/root/.claude` at 00:09
  (every path under it carries that timestamp). Separating these needs the
  setup script's own execution log, which is not on this container — I looked
  for one under `/tmp`, `/var/log`, and `/root/.claude/session-env` and found
  nothing.
