#!/bin/bash
# Makes this repo's own Orclab plugin available to Claude Code on the web.
#
# Three placements were measured on real cloud sessions (2026-09-23/24,
# CLI 2.1.281):
#
#   * `extraKnownMarketplaces`/`enabledPlugins` in .claude/settings.json:
#     ignored outright by the web harness, which reads only `hooks` there.
#   * `claude plugin install` from this hook: installs correctly, but into
#     ~/.claude/plugins/, which a cloud session never reads.
#   * a symlink into ~/.claude/skills/ made by hand mid-session: picked up,
#     all 36 skills, with the three `disable-model-invocation` ones correctly
#     withheld from ambient matching. That directory is re-scanned live.
#
# So this is the right target, and the only open question was when it has to
# exist. The environment setup script's attempt at the same symlink did not
# survive into a session; this hook runs inside the session instead.
set -euo pipefail

# Local checkouts manage their own install; only the disposable cloud
# container needs this.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

mkdir -p "$HOME/.claude/skills"
ln -sfn "$CLAUDE_PROJECT_DIR" "$HOME/.claude/skills/orclab"

exit 0
