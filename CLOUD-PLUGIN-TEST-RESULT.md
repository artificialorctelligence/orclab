# Cloud plugin-load test result

Session: Claude Code on the web (cloud container), repo `artificialorctelligence/orclab`,
working directory `/home/user/orclab`, date 2026-09-23.

## Verdict

**No.** The repo's own checked-in `.claude/settings.json` — which registers this directory as a
marketplace named `orclab` and sets `"enabledPlugins": {"orclab@orclab": true}` — did **not** make
the plugin's skills available to this session. At session start the harness handed me a
skills list containing zero entries beginning with `orclab:` or `orc-`; calling the `Skill` tool
with `orclab:orc-help` returned `Unknown skill: orclab:orc-help`; `claude plugin list` reports
`No plugins installed`; `claude plugin marketplace list` reports `No marketplaces configured`;
and `~/.claude/plugins/installed_plugins.json` is an empty registry (`{"version": 2, "plugins":
{}}`). The 36 skill directories are present on disk under `skills/` — the plugin source is
right there in the checkout — but nothing in this container loaded them. There is no visible
trust gate blocking it either: `~/.claude/settings.json` does not exist, `~/.claude.json` holds
only feature flags (no `hasTrustDialogAccepted` key at all — the grep returned nothing), and the
only `trust` string matches under `~/.claude*` are in unrelated synced Anthropic skills and my
own session transcript. So the failure is not "settings found but untrusted"; the
project-level `extraKnownMarketplaces` / `enabledPlugins` settings appear simply not to have been
acted on by this cloud session's startup at all.

---

## 1. Available-skills list at session start

**No entry begins with `orclab:` or `orc-`.** The list the harness gave me contains no Orclab
component — not `orc`, `orc-help`, `orc-version`, `orc-git`, `orc-code`, nor any of the
discipline or stack skills. Nothing namespaced `orclab:` appears either.

Three lines of the list I *do* have, verbatim:

```
- session-start-hook: Creating and developing startup hooks for Claude Code on the web. Use when the user wants to set up a repository for Claude Code on the web, create a SessionStart hook to ensure their project can run tests and linters during web sessions.
- update-config: Use this skill to configure the Claude Code harness via settings.json. Automated behaviors ("from now on when X", "each time X", "whenever X", "before/after X") require hooks configured in settings.json - the harness executes these, not Claude, so memory/preferences cannot fulfill them. ...
- anthropic-skills:skill-creator: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
```

The only namespaced prefix present anywhere in the list is `anthropic-skills:` (account-synced
skills, found on disk at `~/.claude/skills/synced/...`). The rest are unprefixed harness
built-ins (`dataviz`, `artifact-design`, `code-review`, `loop`, `run`, `init`, …).

For contrast, the plugin source **is** present in the checkout — `ls skills/` returns 36
directories:

```
backlog-discipline        orc-help                  stack-android-native
car-android-auto          orc-package               stack-flutter
car-carplay               orc-publish               stack-godot
code-discipline           orc-release               stack-ios-native
currency-discipline       orc-reload                stack-kotlin-multiplatform
environment-registry      orc-test                  stack-php
map-openstreetmap         orc-todo                  stack-python-desktop
orc                       orc-version               stack-react-native
orc-code                  release-checklist         stack-unity
orc-git                   secret-hygiene            stack-web
                          security-discipline       test-discipline
                          source-librewxr           verify-before-asserting
                          source-road-conditions    whole-process-first
```
(total: 36)

## 2. `Skill` tool call with `orclab:orc-help`

Exact result:

```
Unknown skill: orclab:orc-help
```

(returned as a tool_use_error.)

## 3. `claude plugin list` and `claude plugin marketplace list`

```
=== claude plugin list ===
No plugins installed. Use `claude plugin install` to install a plugin.
=== EXIT: 0 ===

=== claude plugin marketplace list ===
No marketplaces configured
=== EXIT: 0 ===
```

## 4. `cat .claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "orclab": {
      "source": {
        "source": "directory",
        "path": "."
      }
    }
  },
  "enabledPlugins": {
    "orclab@orclab": true
  }
}
```

## 5. User-level config and plugin state

```
=== cat ~/.claude/settings.json ===
cat: /root/.claude/settings.json: No such file or directory

=== ls -la ~/.claude/ ===
total 80
drwxr-xr-x 10 root root  4096 Sep 23 23:47 .
drwx------ 15 root root  4096 Sep 23 23:47 ..
-rw-r--r--  1 root root    24 Sep 23 23:47 .last-cleanup
drwxr-xr-x  2 root root  4096 Sep 23 23:46 backups
drwxr-xr-x  2 root root  4096 Sep 23 23:47 environment-manager
-rw-------  1 root root   442 Sep 23 23:47 launcher-settings.json
drwxr-xr-x  3 root root  4096 Sep 23 23:47 plugins
drwx------  3 root root  4096 Sep 23 23:47 projects
drwxr-xr-x  3 root root  4096 Sep 23 23:47 session-env
drwx------  2 root root  4096 Sep 23 23:47 sessions
drwxr-xr-x  2 root root  4096 Sep 23 23:47 shell-snapshots
drwxr-xr-x  4 root root  4096 Sep 23 23:47 skills
-rwxr-xr-x  1 root root  6395 Sep 23 23:47 stop-hook-git-check.sh
-rwxr-xr-x  1 root root 17848 Sep 23 23:47 stop-hook-reply-gate.py
-rwxr-xr-x  1 root root  3630 Sep 23 23:47 user-prompt-submit-reply-reminder.py

=== ls -la ~/.claude/plugins/ ===
total 16
drwxr-xr-x  3 root root 4096 Sep 23 23:47 .
drwxr-xr-x 10 root root 4096 Sep 23 23:47 ..
-rw-r--r--  1 root root   35 Sep 23 23:46 installed_plugins.json
drwxr-xr-x  3 root root 4096 Sep 23 23:47 synced

=== cat ~/.claude/plugins/installed_plugins.json ===
{
  "version": 2,
  "plugins": {}
}
```

Supplementary (not requested, recorded because it explains what `synced` holds — it is
account-synced Anthropic skills, not Orclab):

```
=== ls -la ~/.claude/plugins/synced ===
total 12
drwxr-xr-x 3 root root 4096 Sep 23 23:47 .
drwxr-xr-x 3 root root 4096 Sep 23 23:47 ..
-rw-r--r-- 1 root root    0 Sep 23 23:47 .bucket-b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac
drwxr-xr-x 2 root root 4096 Sep 23 23:47 b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac
```

Note the directory `~/.claude/plugins/` exists and carries an *empty* v2 registry, and there is
no `~/.claude/plugins/marketplaces/` directory at all — the clone-per-marketplace directory
that `CLAUDE.md`'s "Marketplace/install gotchas" section describes was never created here.

## 6. Trust gate

```
=== cat ~/.claude.json | head -40 ===
{
  "cachedGrowthBookFeatures": {
    "tengu_cork_lantern": false,
    "tengu_tussock_oriole": false,
    "tengu_teal_corbel": true,
    "tengu_loggia_carousel": false,
    "tengu-off-switch": {
      "activated": false
    },
    "tengu_juniper_vale": {
      "enabled": false,
      "maxChars": 500,
      "autoDismissAfterMs": 30000
    },
    "tengu_bridge_attestation_enforce_config": {
      "accept_level": "VERIFIED_KEYLESS_DEVICE",
      "accept_statuses": []
    },
    "tengu_ultraplan_config": {
      "enabled": false
    },
    "tengu_pewter_kite_ms": 0,
    "tengu_twinkling_globe": false,
    "tengu_brisk_meadow": false,
    "tengu_amber_sentinel": true,
    "tengu_bridge_repl_v2": true,
    "tengu_fennel_kite": false,
    "tengu_sprightly_lagoon": false,
    "tengu_velvet_ibis": {},
    "tengu_smooth_forest": true,
    "tengu_wild_tome": true,
    "tengu_ccr_classifier_keepalive_enabled": false,
    "tengu_umber_lattice": true,
    "tengu_sorrel_trellis_tenon": false,
    "tengu_frame_publish_context": true,
    "tengu_harbor_kite": true,
    "tengu_desktop_upsell": {
      "enable_shortcut_tip": true,
      "enable_startup_dialog": false
    },
```

```
=== grep -ril trust ~/.claude* | head ===
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/morning/SKILL.md
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/docx/SKILL.md
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/xlsx/SKILL.md
/root/.claude/skills/synced/b80c1955-eefc-44a4-bc1d-5778aacf0e75_7bb2cbbe-bcf8-4b78-a511-ebf0ca087fac/pptx/SKILL.md
/root/.claude/projects/-home-user-orclab/16cdb293-5d03-5034-ab14-e94081c1221f.jsonl
```

All five `trust` hits are incidental: four are Anthropic's own synced skills (prose containing
the word), and the fifth is this session's own transcript, which contains the word because the
task prompt asked me to grep for it. No trust-gate state file, no `hasTrustDialogAccepted`
key (a targeted `grep -o '"hasTrustDialogAccepted":[^,}]*' ~/.claude.json` returned nothing),
and no per-project trust record for `/home/user/orclab`.
