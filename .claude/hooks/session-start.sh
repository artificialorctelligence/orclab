#!/bin/bash
# Loads Orclab as a real plugin in a Claude Code on the web session.
#
# This sits ALONGSIDE the symlinks in .claude/skills/, and the two are not
# redundant - they carry different things. Measured 2026-09-24 on fresh cloud
# sessions:
#
#   .claude/skills/  - the documented route ("part of the clone"). Loads the
#                      skills, bare-named (orc-help). Carries skills ONLY: a
#                      skills directory does not read hooks/hooks.json, so
#                      secret_guard, backlog_guard, model_floor and
#                      lint_on_write never fire. Confirmed by running a bare
#                      `env` dump in such a session: nothing blocked it,
#                      though secret_guard was present on disk and would
#                      have denied that exact command.
#
#   this hook        - symlinks the checkout into the container's own skills
#                      directory, where Claude Code loads it as a plugin
#                      (orclab@skills-dir), namespaced (orclab:orc-help), with
#                      its hooks registered.
#
# The cost of running both, measured rather than estimated: every skill is
# loaded and described twice, so the always-on context goes from ~4,364 to
# ~8,700 tokens. The hook alone would give skills and hooks with no
# duplication; the symlinks alone are the documented mechanism and survive if
# this undocumented one ever stops working. Keeping both is a deliberate
# trade of context for resilience, not an oversight.
#
# Not needed and not wanted on a developer's own machine, where the plugin is
# installed properly.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

mkdir -p "$HOME/.claude/skills"
ln -sfn "$CLAUDE_PROJECT_DIR" "$HOME/.claude/skills/orclab"

exit 0
