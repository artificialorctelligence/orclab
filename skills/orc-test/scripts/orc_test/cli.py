"""/orc-test: run, measure and (via SKILL.md prose) repair a project's tests, per language."""

import argparse
import json
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
    counts = " ".join(m.group(0) for m in _PYTEST_SUMMARY.finditer(cp.stdout))
    if not counts:
        empty = "no tests ran" in cp.stdout or cp.returncode == 5
        counts = "0 tests" if empty else ("passed" if ok else "failed")
        ok = ok and not empty
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


def _coverage(mod, root, target, cfg, out):
    why = getattr(mod, "coverage_unavailable", lambda r: None)(root)
    if why:
        return {"unavailable": why}
    cp = run(mod.coverage_cmd(root, target, out), cwd=root)
    if cp.returncode != 0:
        print(cp.stdout[-3000:])
        print(f"{mod.LABEL}: tests failed; coverage not measured")
        return None
    return mod.coverage_parse(root, out)


def _coverage_block(mod, cov, threshold, out):
    ok = cov.percent >= threshold
    lines = [f"{mod.LABEL:<10} coverage {cov.percent}% ({cov.covered}/{cov.total} lines) "
             f"{'✓' if ok else '✗ (min ' + str(threshold) + ')'}"]
    for path, pct in cov.under(threshold):
        lines.append(f"    {pct:5.1f}%  {path}")
    html = out / "html"
    if html.exists():
        lines.append(f"    html report: {html}")
    return "\n".join(lines)


def cmd_coverage(args):
    failed, blocks = False, []
    for m, root, target, cfg in _each_language(args):
        cov = _coverage(m, root, target, cfg, _out(root, m))
        if cov is None:
            failed = True
            continue
        if isinstance(cov, dict):   # not measurable — not a gate failure
            blocks.append(f"{m.LABEL:<10} coverage not measurable — {cov['unavailable']}")
            continue
        failed |= cov.percent < cfg["coverage"]
        blocks.append(_coverage_block(m, cov, cfg["coverage"], _out_path(root, m)))
    print("\n" + "\n\n".join(blocks) if blocks else "nothing measured")
    return 1 if failed else 0


def _out_path(root, mod):
    return pathlib.Path(root) / ".orclab" / "test" / mod.KEY


def _source_count(root, mod, target):
    base = pathlib.Path(root) / (target or ".")
    return sum(1 for p in base.rglob(f"*{mod.SOURCE_EXT}")
               if not detect.SKIP_DIRS & set(p.relative_to(root).parts))


def _mutation(mod, root, target, cfg, out):
    why = mod.mutation_unavailable(root)
    if why:
        return {"unavailable": why}
    if not target:
        print(f"{mod.LABEL}: mutating {_source_count(root, mod, None)} files"
              " — a first run on the whole project takes a while; later runs are incremental"
              " where the tool supports it")
    where = getattr(mod, "mutation_cwd", lambda r, t: r)(root, target)   # a sub-project's own config
    cp = run(mod.mutation_cmd(where, target, out), cwd=where)
    if cp.returncode not in (0, 1, 2):        # tools exit non-zero on survivors; a crash is higher
        print(cp.stdout[-3000:])
        return {"unavailable": f"mutation tool exited {cp.returncode}"}
    mut = mod.mutation_parse(where, out)
    if not mut.total:
        return {"unavailable": "mutation tool produced no mutants — check its configuration"}
    sub = pathlib.Path(where).relative_to(root)
    return {"score": mut.score, "killed": mut.killed, "total": mut.total,
            "survivors": [[str(sub / s.file), s.line, s.description] for s in mut.survivors]}


def _tce_line(tce, threshold):
    if "unavailable" in tce:
        return f"TCE not measurable — {tce['unavailable']}"
    if tce.get("skipped"):
        return "TCE skipped"
    ok = tce["score"] >= threshold
    return f"TCE {tce['score']}% {'✓' if ok else '✗ (min ' + str(threshold) + ')'}"


def cmd_analyze(args):
    result = {"when": int(time.time()), "target": args.path, "languages": {}}
    failed_gates, blocks = set(), []
    langs_found = _each_language(args)
    project = langs_found[0][1] if langs_found else detect.project_root(args.cwd)
    for m, root, target, cfg in langs_found:
        out = _out(root, m)
        ok, _ = _run_tests(m, root, target, cfg)
        if not ok:
            print(f"{m.LABEL}: tests failed; nothing measured")
            failed_gates.add("tests")
            continue
        cov = _coverage(m, root, target, cfg, out)
        if cov is None:
            failed_gates.add("tests")
            continue
        tce = {"skipped": True} if args.no_mutation else _mutation(m, root, target, cfg, out)
        lint = m.lint(root, target, out)
        lint_note = lint if isinstance(lint, str) else None
        lint = [] if lint_note else lint
        if isinstance(cov, dict):   # not measurable — words, not a gate failure
            cov_result = cov
            cov_line = f"{m.LABEL:<10} coverage not measurable — {cov['unavailable']}"
        else:
            cov_result = {"percent": cov.percent, "under": cov.under(cfg["coverage"])}
            cov_line = _coverage_block(m, cov, cfg["coverage"], _out_path(root, m))
            if cov.percent < cfg["coverage"]:
                failed_gates.add("coverage")
        if "score" in tce and tce["score"] < cfg["tce"]:
            failed_gates.add("tce")
        result["languages"][m.KEY] = {
            "coverage": cov_result,
            "tce": tce, "lint": [[f.file, f.line, f.message] for f in lint], "lint_note": lint_note}
        lint_txt = f"not run — {lint_note}" if lint_note else f"{len(lint)} finding{'s' if len(lint) != 1 else ''}"
        lines = [cov_line, f"{'':<10} {_tce_line(tce, cfg['tce'])}    lint: {lint_txt}"]
        for s in tce.get("survivors", []):
            lines.append(f"    survived  {s[0]}:{s[1]}  {s[2]}")
        for f in lint:
            lines.append(f"    lint      {f.file}:{f.line}  {f.message}")
        for c in (m.CAVEATS_FOR(root) if hasattr(m, "CAVEATS_FOR") else m.CAVEATS):
            lines.append(f"    note: {c}")
        blocks.append("\n".join(lines))
    if langs_found:
        out_path = pathlib.Path(project) / ".orclab" / "test" / "analyze.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=1))
    print("\n" + "\n\n".join(blocks) if blocks else "nothing measured")
    if failed_gates:
        print(f"\ngates failed: {', '.join(sorted(failed_gates))} — run `/orc-test generate` to repair")
    return 1 if failed_gates else 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="orc-test")
    p.add_argument("--cwd", default=".")
    p.add_argument("--lang", help="only this language KEY (python, javascript, ...)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("detect", cmd_detect), ("run", cmd_run), ("coverage", cmd_coverage),
                     ("analyze", cmd_analyze)):
        sp = sub.add_parser(name)
        sp.add_argument("path", nargs="?")
        sp.add_argument("--no-mutation", action="store_true")
        sp.set_defaults(fn=fn, no_mutation=False)
    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except detect.NotAProject as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except config.BadConfig as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
