#!/usr/bin/env python3
"""PostToolUse: run the project's own linter on the file Claude just wrote, and say what it found.

`code-discipline` states seven rules for the shape of code; four of them (nesting depth, function
length, swallowed errors, warnings) are checkable, and each `stack-*` skill's "Lint - where
code-discipline lands" section puts them in that stack's linter config. A rule in a config file
holds only when the linter runs - in CI, at commit, or here: on every Edit/Write, whoever made
it, subagents included. Holzmann's rule 10 wants the checker run daily; this is per write
(BACKLOG #40, 2026-09-13).

**It runs the project's configured linter, never an opinion of its own.** A language is linted
only when both hold: the tool is on PATH, and the project has that tool's config file somewhere
between the written file and the repo root. No config, no run - a project that has not adopted
the rules is not nagged about them, and this hook has no rules to contribute; they are all in
the config. C# has no per-file linter that finishes in seconds (`dotnet build` is the analyzer),
so `.cs` is left to the build.

Contract: read the hook payload as JSON on stdin. Findings go to stderr with exit 2 - the one way
a PostToolUse hook's output reaches Claude (the docs: "exit 2 instead so Claude sees the stderr
even though the tool already ran"). A clean file, an unlinted language, or any failure of this
script itself exits 0 and says nothing: a hook that wedges every write is worse than a missed
warning.

v23: a containerised project (compose.yaml with an `orclab` service at the git root, per
skills/orc-test/scripts/orc_test/container.py) lints through `compose run` instead of the host -
same config-file gate, same tool, run one layer over. No engine on PATH means no lint, never a
silent fall-through to the host.
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

from orclab_shared import invoking_root

OFF = "ORCLAB_LINT_ON_WRITE_OFF"
TIMEOUT = 30
MAX_LINES = 40

# extension -> (config file that proves the project adopted the tool, tool on PATH, argv)
# ponytail: one linter per language, the fast per-file one; a project wanting a different tool
# sets it in .orclab/test.yaml when that override exists (BACKLOG #40)
LINTERS = {
    ".py": ("pyproject.toml", "ruff", ["ruff", "check", "--no-fix"]),
    ".ts": (".oxlintrc.json", "oxlint", ["oxlint"]),
    ".tsx": (".oxlintrc.json", "oxlint", ["oxlint"]),
    ".js": (".oxlintrc.json", "oxlint", ["oxlint"]),
    ".jsx": (".oxlintrc.json", "oxlint", ["oxlint"]),
    ".kt": ("config/detekt/detekt.yml", "detekt", ["detekt", "--config", "config/detekt/detekt.yml", "--input"]),
    ".swift": (".swiftlint.yml", "swiftlint", ["swiftlint", "lint", "--quiet"]),
    ".dart": ("analysis_options.yaml", "dart", ["dart", "analyze", "--fatal-infos"]),
    ".gd": ("project.godot", "gdlint", ["gdlint"]),
}
# ESLint projects (Expo) instead of oxlint ones: same rules, different config file and binary
ESLINT = ("eslint.config.js", "eslint", ["eslint"])
NODE_BIN = "node_modules/.bin"

# v23: a containerised project (compose.yaml with an `orclab` service at the git root) lints
# through the container. A deliberate copy of skills/orc-test/scripts/orc_test/container.py's
# detection, by the rule in orclab_shared.py's docstring; no PyYAML here, a regex is enough for
# the one shape Orclab itself writes.
SERVICE_RE = re.compile(r"^services:\s*$(?:\n(?!\S).*)*?^  orclab:\s*$", re.MULTILINE)
RUNNERS = ("docker", "podman")
# PyYAML's boolean spellings for false that skills/orc-test/scripts/orc_test/config.py's real
# `yaml.safe_load` would also accept here (`data.get("container", True) is not False`)
FALSE_WORDS = ("false", "no", "off")


def _override_value(text, key):
    """The value after `key:` on its own line in `.orclab/test.yaml`, comment and surrounding
    whitespace stripped - a hand-rolled stand-in for the one or two lines this hook cares about,
    since real YAML parsing needs PyYAML (config.py has it; this hook does not)."""
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith(key + ":"):
            return line[len(key) + 1:].strip()
    return None


def container_prefix(root):
    """[] on the host; the compose-run prefix when `root` (the git root) is containerised and
    this checkout has not opted out; None when it is containerised but no engine is on PATH -
    then lint nothing, never fall back to the host."""
    compose = pathlib.Path(root) / "compose.yaml"
    if not compose.is_file() or not SERVICE_RE.search(compose.read_text(errors="replace")):
        return []
    override = pathlib.Path(root) / ".orclab" / "test.yaml"
    text = override.read_text(errors="replace") if override.is_file() else ""
    if (_override_value(text, "container") or "").lower() in FALSE_WORDS:
        return []
    runner = _override_value(text, "runner")
    names = (runner,) if runner else RUNNERS
    engine = next((n for n in names if shutil.which(n)), None)
    if engine is None:
        return None
    return [engine, "compose", "run", "--rm", "-T", "--workdir", str(root), "orclab"]


def _config_dir(start, name, holds=lambda p: True):
    """The nearest ancestor of `start` holding `name` (and passing `holds`), up to the git root."""
    d = pathlib.Path(start).resolve()
    if d.is_file():
        d = d.parent
    for parent in (d, *d.parents):
        if (parent / name).exists() and holds(parent / name):
            return parent
        if (parent / ".git").exists():
            break
    return None


def _ruff_section(pyproject):
    # ruff's own discovery skips a pyproject.toml without [tool.ruff]; a sub-project's
    # mutmut-only pyproject must not stop the search short of the one that configures ruff
    return "[tool.ruff" in pyproject.read_text(errors="replace")


def command_for(path):
    """(cwd, argv, header) to lint `path`, or None when the project has not configured a linter
    for it, or its container status can't be established. `header` is the two tokens worth
    naming in the exit-2 message - the linter itself, never the container-engine prefix."""
    ext = pathlib.Path(path).suffix
    if ext not in LINTERS:
        return None
    config, tool, argv = LINTERS[ext]
    root = _config_dir(path, config, _ruff_section if ext == ".py" else lambda p: True)
    if root is None and ext == ".py":
        root = _config_dir(path, "ruff.toml")
    if root is None and ext in (".ts", ".tsx", ".js", ".jsx"):
        config, tool, argv = ESLINT
        root = _config_dir(path, config)
    if root is None:
        return None
    local = root / NODE_BIN / tool
    if local.exists():
        argv = [str(local)] + argv[1:]

    # container status is a property of the git root, not of `root` (which may be a nested
    # sub-project's own config dir) - and it can't be told apart from "not containerised"
    # without one, so no git root means no lint, same as no engine on PATH.
    git_root = invoking_root(root)
    if git_root is None:
        return None
    prefix = container_prefix(git_root)
    if prefix is None:
        return None
    if not prefix and not local.exists() and shutil.which(tool) is None:
        return None

    cwd = pathlib.Path(git_root) if prefix else root
    header = " ".join(argv[:2])
    return cwd, prefix + argv + [str(pathlib.Path(path).resolve())], header


def main():
    try:
        if os.environ.get(OFF):
            return 0
        payload = json.load(sys.stdin)
        if payload.get("tool_name") not in ("Edit", "Write", "MultiEdit"):
            return 0
        path = (payload.get("tool_input") or {}).get("file_path")
        if not path or not pathlib.Path(path).is_file():
            return 0
        found = command_for(path)
        if found is None:
            return 0
        root, argv, header = found
        cp = subprocess.run(argv, check=False, cwd=root, capture_output=True, text=True, timeout=TIMEOUT)
        if cp.returncode == 0:
            return 0
        lines = (cp.stdout + cp.stderr).strip().splitlines()
        report = "\n".join(lines[:MAX_LINES]) + (f"\n… {len(lines) - MAX_LINES} more lines" if len(lines) > MAX_LINES else "")
        print(f"orclab lint_on_write: `{header}` on {path} exited {cp.returncode} - "
              f"code-discipline's checkable rules, from the project's own config. Set {OFF}=1 to disable.\n"
              f"{report}", file=sys.stderr)
        return 2
    except Exception:  # noqa: BLE001 - fail open, always: a hook that wedges every write is worse than a missed warning
        return 0


if __name__ == "__main__":
    sys.exit(main())
