"""Which languages a project contains, and whether it already says how to run its tests."""

import json
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
    root = pathlib.Path(root)
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if len(rel.parts) > MAX_DEPTH or SKIP_DIRS & set(rel.parts):
            continue
        yield p


def languages(root, modules):
    files = list(_candidates(root))
    found = []
    for m in modules:
        if any(f.match(pat) for pat in m.MARKERS for f in files):
            found.append(m)
    return found


def declared_test_cmd(root, key, cfg):
    root = pathlib.Path(root)
    override = (cfg.get("languages") or {}).get(key, {}).get("test")
    if override:
        return shlex.split(override)
    pkg = root / "package.json"
    if key == "javascript" and pkg.exists():
        if (json.loads(pkg.read_text()).get("scripts") or {}).get("test"):
            return ["npm", "test"]
    mk = root / "Makefile"
    if mk.exists() and re.search(r"^test\s*:", mk.read_text(), re.M):
        return ["make", "test"]
    return None
