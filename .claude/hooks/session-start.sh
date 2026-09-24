#!/bin/bash
# Loads Orclab as a real plugin in a Claude Code on the web session.
#
# A cloud container starts empty and keeps nothing, so installing never reaches
# it: `claude plugin install` writes under ~/.claude/plugins, which a cloud
# session never reads, and reports success having changed nothing (measured
# 2026-09-24 across four fresh sessions). ~/.claude/skills IS read, so this
# links the checkout there and Claude Code loads it as a plugin
# (orclab@skills-dir), namespaced (orclab:orc-help), with hooks/hooks.json
# registered.
#
# This is the whole mechanism. An earlier version sat alongside 36 committed
# symlinks under the repo's own .claude/skills/, which is the route Anthropic's
# docs name ("part of the clone"). That route carries skills ONLY - a skills
# directory does not read hooks/hooks.json, so secret_guard, backlog_guard,
# model_floor and lint_on_write never register. Cloud test 7 measured both live
# and settled it:
#
#   - the hook's namespaced skills are in the session-start list, so it lands
#     in time - the symlink is created ~2s after the clone, before the list is
#     built;
#   - `claude plugin list` reports ONE plugin, orclab@skills-dir, pathed at the
#     home symlink this hook creates - the committed symlinks never surfaced as
#     a plugin at all;
#   - lint_on_write resolved through ~/.claude/skills/orclab/hooks/scripts/ and
#     the runtime attributed it to "the orclab@skills-dir plugin".
#
# So this hook does everything the committed symlinks did and more, and running
# both loaded every skill twice - 66 list entries for 36 skills, ~4,364 to
# ~8,700 tokens of always-on context. Worse, the duplicate set cost that on a
# developer's own machine too, where it bought nothing at all: a local checkout
# has the plugin installed properly and already has both skills and hooks.
# The committed symlinks were dropped for that reason. If this undocumented
# route ever stops working, restoring them is one command - but restore them
# INSTEAD of this hook, not beside it, or the double-load comes back.
#
# Not needed and not wanted on a developer's own machine, where the plugin is
# installed properly - hence the guard below.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

mkdir -p "$HOME/.claude/skills"
ln -sfn "$CLAUDE_PROJECT_DIR" "$HOME/.claude/skills/orclab"

exit 0
