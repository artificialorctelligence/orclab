"""/orc-test: run, measure and (via SKILL.md prose) repair a project's tests, per language."""

import argparse
import pathlib
import re
import shutil
import sys
import time

from . import config, detect, langs
from .runner import run

_PYTEST_SUMMARY = re.compile(r"(\d+) passed|(\d+) failed|(\d+) error")


def _each_language(args):
    root = detect.project_root(args.cwd)
    cfg = config.load(root)
    mods = [m for m in langs.ALL if not args.lang or m.KEY == args.lang]
    found = detect.languages(root, mods)
    target = None
    if args.path:
        target = str(pathlib.Path(args.path).resolve().relative_to(root)) if pathlib.Path(args.path).is_absolute() else args.path
    print("detected: " + (", ".join(m.LABEL for m in found) or "no supported language"))
    usable = []
    for m in found:
        gone = m.missing(root)
        if gone:
            for tool in gone:
                print(f"{m.LABEL}: missing {tool} — {m.TOOLS[tool]} — skipped")
            continue
        usable.append((m, root, target, cfg))
    return usable


def _out(root, mod):
    out = pathlib.Path(root) / ".orclab" / "test" / mod.KEY
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    return out


def _test_cmd(root, mod, target, cfg):
    return detect.declared_test_cmd(root, mod.KEY, cfg) or mod.test_cmd(root, target)


def _run_tests(mod, root, target, cfg):
    """(ok, one-line summary). Prints the tool's output tail."""
    t0 = time.monotonic()
    cp = run(_test_cmd(root, mod, target, cfg), cwd=root)
    secs = time.monotonic() - t0
    ok = cp.returncode == 0
    print(cp.stdout[-3000:])
    counts = " ".join(m.group(0) for m in _PYTEST_SUMMARY.finditer(cp.stdout)) or (
        "passed" if ok else "failed")
    return ok, f"{mod.LABEL:<10} {'✓' if ok else '✗'} {counts} ({secs:.1f}s)"


def cmd_detect(args):
    for m, root, target, cfg in _each_language(args):
        print(f"  {m.LABEL}: test command {' '.join(_test_cmd(root, m, target, cfg))}")
    return 0


def cmd_run(args):
    failed = False
    lines = []
    for m, root, target, cfg in _each_language(args):
        ok, line = _run_tests(m, root, target, cfg)
        failed |= not ok
        lines.append(line)
    print("\n" + "\n".join(lines) if lines else "nothing to run")
    return 1 if failed else 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="orc-test")
    p.add_argument("--cwd", default=".")
    p.add_argument("--lang", help="only this language KEY (python, javascript, ...)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("detect", cmd_detect), ("run", cmd_run)):
        sp = sub.add_parser(name)
        sp.add_argument("path", nargs="?")
        sp.set_defaults(fn=fn)
    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except detect.NotAProject as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except config.BadConfig as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
