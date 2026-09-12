"""Which languages a project contains, and whether it already says how to run its tests."""

import json
import os
import pathlib
import re
import shlex
import subprocess

SKIP_DIRS = {"node_modules", ".git", "venv", ".venv", "mutants", "build", "dist", "__pycache__"}
MAX_DEPTH = 2


class NotAProject(Exception):
    pass


def project_root(cwd):
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(cwd), text=True,
                             capture_output=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise NotAProject(f"{cwd} is not inside a git repository")
    return pathlib.Path(out).resolve()


def _candidates(root):
    """Files up to MAX_DEPTH directories below root, never descending into SKIP_DIRS at all."""
    root = pathlib.Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        depth = len(pathlib.Path(dirpath).relative_to(root).parts)  # 0 == root itself
        for name in filenames:
            yield pathlib.Path(dirpath) / name
        if depth >= MAX_DEPTH:
            dirnames[:] = []  # already MAX_DEPTH directories down; don't descend further


def languages(root, modules):
    """[(module, dir)] — dir is where the module's first marker sits (root when it is at root),
    shallowest first, so a root build file wins over a module's. Everything that language's tools
    do runs from dir; the marker two directories down is a real sub-project, not a root one."""
    root = pathlib.Path(root)
    files = sorted(_candidates(root), key=lambda f: (len(f.relative_to(root).parts), str(f)))
    found = []
    for m in modules:
        hit = next((f for f in files if any(f.match(pat) for pat in m.MARKERS)), None)
        if hit is not None:
            depth = max(len(pathlib.PurePath(pat).parts) for pat in m.MARKERS if hit.match(pat))
            found.append((m, hit.parents[depth - 1]))   # *.xcodeproj/project.pbxproj → its parent
    dirs = {m.KEY: d for m, d in found}
    if "kotlin" in dirs and "java" in dirs:
        kot = next(m for m, _ in found if m.KEY == "kotlin")
        drop = "java" if kot.claims(dirs["kotlin"]) else "kotlin"
        found = [(m, d) for m, d in found if m.KEY != drop]
    return found


def declared_test_cmd(root, key, cfg):
    root = pathlib.Path(root)
    override = (cfg.get("languages") or {}).get(key, {}).get("test")
    if override:
        return shlex.split(override)
    pkg = root / "package.json"
    if key == "javascript" and pkg.exists():
        try:
            data = json.loads(pkg.read_text())
        except json.JSONDecodeError:
            data = {}
        if (data.get("scripts") or {}).get("test"):
            return ["npm", "test"]
    mk = root / "Makefile"
    if mk.exists() and re.search(r"^test\s*:", mk.read_text(), re.M):
        return ["make", "test"]
    return None
