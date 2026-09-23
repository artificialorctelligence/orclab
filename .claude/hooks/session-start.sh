#!/bin/bash
# Puts this repo's own Orclab plugin in place for Claude Code on the web.
#
# A cloud session starts in a fresh container with no plugins installed, and
# nothing the repo checks in enables one by itself. Two things were tried and
# measured (2026-09-23, CLI 2.1.281, both on real cloud sessions):
#
#   * `extraKnownMarketplaces` + `enabledPlugins` in this file's sibling
#     settings.json: ignored outright. The session reported no orclab skills,
#     `Unknown skill: orclab:orc-help`, `No plugins installed` and `No
#     marketplaces configured`, with no trust gate to explain it.
#
#   * this hook: runs, and installs correctly — 2.3s and 3.5s after checkout,
#     with installed_plugins.json recording this working tree's own commit —
#     but the session's skill list is assembled before that lands, so /orc-*
#     is still missing on the first turn.
#
# So the hook's job is only to have the plugin installed and enabled by the
# time a person can type. Activating it in the running session takes one more
# step, by hand: /reload-plugins. Note that doing so also activates Orclab's
# own hooks (secret_guard, backlog_guard, model_floor, lint_on_write).
set -euo pipefail

# Local checkouts manage their own install; only the disposable cloud
# container needs this.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Idempotent: both commands fail harmlessly if already registered/installed.
claude plugin marketplace add "$CLAUDE_PROJECT_DIR" >/dev/null 2>&1 || true
claude plugin install orclab@orclab -y >/dev/null 2>&1 || true

exit 0
