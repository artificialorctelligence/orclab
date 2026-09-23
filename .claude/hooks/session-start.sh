#!/bin/bash
# Makes this repo's own Orclab plugin available to Claude Code on the web.
#
# A cloud session starts in a fresh container with no plugins installed, and the
# repo's own `extraKnownMarketplaces`/`enabledPlugins` settings are not acted on
# there (confirmed live 2026-09-23 — see CLAUDE.md). Installing from this
# checkout in a SessionStart hook is the repo-side equivalent of the cloud
# environment's setup script.
set -euo pipefail

# Local checkouts manage their own install; only the disposable cloud container
# needs this.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Idempotent: both commands fail harmlessly if already registered/installed.
claude plugin marketplace add "$CLAUDE_PROJECT_DIR" >/dev/null 2>&1 || true
claude plugin install orclab@orclab -y >/dev/null 2>&1 || true

exit 0
