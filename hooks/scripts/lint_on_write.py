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
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys

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


def _config_dir(start, name):
    """The nearest ancestor of `start` holding `name`, stopping at the git root (or /)."""
    d = pathlib.Path(start).resolve()
    if d.is_file():
        d = d.parent
    for parent in (d, *d.parents):
        if (parent / name).exists():
            return parent
        if (parent / ".git").exists():
            break
    return None


def _ruff_configured(root):
    return "[tool.ruff" in (root / "pyproject.toml").read_text(errors="replace") or (root / "ruff.toml").exists()


def command_for(path):
    """(cwd, argv) to lint `path`, or None when the project has not configured a linter for it."""
    ext = pathlib.Path(path).suffix
    if ext not in LINTERS:
        return None
    config, tool, argv = LINTERS[ext]
    root = _config_dir(path, config)
    if root is None and ext in (".ts", ".tsx", ".js", ".jsx"):
        config, tool, argv = ESLINT
        root = _config_dir(path, config)
    if root is None:
        return None
    if ext == ".py" and not _ruff_configured(root):
        return None
    local = root / NODE_BIN / tool
    if local.exists():
        argv = [str(local)] + argv[1:]
    elif shutil.which(tool) is None:
        return None
    return root, argv + [str(pathlib.Path(path).resolve())]


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
        root, argv = found
        cp = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=TIMEOUT)
        if cp.returncode == 0:
            return 0
        lines = (cp.stdout + cp.stderr).strip().splitlines()
        report = "\n".join(lines[:MAX_LINES]) + (f"\n… {len(lines) - MAX_LINES} more lines" if len(lines) > MAX_LINES else "")
        print(f"orclab lint_on_write: `{' '.join(argv[:2])}` on {path} exited {cp.returncode} - "
              f"code-discipline's checkable rules, from the project's own config. Set {OFF}=1 to disable.\n"
              f"{report}", file=sys.stderr)
        return 2
    except Exception:
        return 0  # fail open, always


if __name__ == "__main__":
    sys.exit(main())
