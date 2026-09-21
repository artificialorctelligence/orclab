"""/orc-test: run, measure and (via SKILL.md prose) repair a project's tests, per language."""

import argparse
import json
import os
import pathlib
import re
import shutil
import sys
import time

from . import config, container, detect, langs, runner
from .runner import run


class ContainerUnavailable(Exception):
    """The project is containerised and its image did not build; nothing runs on the host instead."""


_PYTEST_SUMMARY = re.compile(r"(\d+) passed|(\d+) failed|(\d+) error")
# What every mutation tool may legitimately touch, whatever the language. A language module adds
# its own leftovers via an optional top-level `SANDBOX: set[str]` (path prefixes), alongside the
# other optional module members: `CAVEATS_FOR(root)`, `coverage_unavailable(root)`,
# `mutation_cwd(root, target)`, `audit_nothing(root)` (a reason the project declares nothing to
# audit, e.g. a tool-only pyproject.toml — "not available", never red, checked before the tool
# is; BACKLOG #54). Anything a tracked file gains outside the union of the two is the
# suite writing to the real tree under a planted defect (test-discipline rule 4; BACKLOG #34).
_SANDBOX = {".orclab"}


def _target_under(m, d, root, path):
    """The user's root-relative path as `d`-relative, or None when it is not under `d`."""
    if path is None:
        return None
    target = os.path.relpath(root / path, d)
    if target.startswith(".."):
        print(f"{m.LABEL}: {path} is not under {d.relative_to(root)}/ — running on all of it")
        return None
    return target


def _resolve(args):
    """(project root, config, [(module, dir, target, container)]). `dir` is where the language's
    marker sits — every tool runs from there — while reports and `.orclab/test/` stay at the root;
    `container` is that language's own (None: the host), and `_each` makes it active per loop."""
    root = detect.project_root(args.cwd)
    cfg = config.load(root)
    mods = [m for m in langs.ALL if not args.lang or m.KEY == args.lang]
    found = detect.languages(root, mods)
    path = None
    if args.path:
        p = pathlib.Path(args.path)
        path = p.resolve().relative_to(root) if p.is_absolute() else p
    # One container per language, not per repository (BACKLOG #66): the compose.yaml beside the
    # marker, else the root's, else the host. Built once per distinct compose.yaml.
    per_lang = [(m, d, container.detect(d, cfg, root)) for m, d in found]
    print("detected: " + (", ".join(_name(m, d, root) + (" (in container)" if c else "") for m, d, c in per_lang)
                         or "no supported language"))
    built = set()
    usable = []
    for m, d, c in per_lang:
        runner.use(c)
        if c and c.runner is None:
            print(f"{m.LABEL}: container runner not found — install podman or docker — skipped")
            continue
        if c and c.root not in built:
            cp = runner.run_on_host(container.build_cmd(c), cwd=c.root)   # the engine itself is a host command
            if container.build_failed(cp):
                print(cp.stdout[-3000:])
                raise ContainerUnavailable
            built.add(c.root)
        gone = m.missing(d)
        for tool in gone:
            print(f"{m.LABEL}: missing {tool} — {m.TOOLS[tool]} — skipped")
        if gone:
            continue
        target = _target_under(m, d, root, path)
        usable.append((m, d, target, c))
    return root, cfg, usable


def _name(mod, d, root):
    return mod.LABEL if d == root else f"{mod.LABEL} ({d.relative_to(root)}/)"


def _each(usable):
    """Yield (module, dir, target) with that language's container made active first — every
    `run()` inside the loop body then goes through the right compose.yaml, or the host."""
    for m, d, target, c in usable:
        runner.use(c)
        yield m, d, target


def _out(root, mod, empty=True):
    out = pathlib.Path(root) / ".orclab" / "test" / mod.KEY
    if empty:
        shutil.rmtree(out, ignore_errors=True)
        out.mkdir(parents=True)
    return out


def _test_cmd(d, mod, target, cfg):
    return detect.declared_test_cmd(d, mod.KEY, cfg) or mod.test_cmd(d, target)


def _pytest_summary(root, cp):
    """(ran, counts) read from the runner's output, pytest's way — the default for a language module
    without its own `test_summary(root, cp)`. A runner that exits 0 with nothing to run (Gradle on a
    NO-SOURCE test task, BACKLOG #67) needs its own, or an empty suite passes."""
    counts = " ".join(m.group(0) for m in _PYTEST_SUMMARY.finditer(cp.stdout))
    return bool(counts) or not ("no tests ran" in cp.stdout or cp.returncode == 5), counts


def _run_tests(mod, d, target, cfg):
    """(ok, one-line summary). Prints the tool's output tail when it failed or gave no counts."""
    t0 = time.monotonic()
    cp = run(_test_cmd(d, mod, target, cfg), cwd=d)
    secs = time.monotonic() - t0
    ok = cp.returncode == 0
    ran, counts = getattr(mod, "test_summary", _pytest_summary)(d, cp)
    if not ok or not counts:
        print(cp.stdout[-3000:])
    if not ran:
        ok, counts = False, "0 tests"
    elif not counts:
        counts = "passed" if ok else "failed"
    return ok, f"{mod.LABEL:<10} {'✓' if ok else '✗'} {counts} ({secs:.1f}s)"


def cmd_detect(args):
    _root, cfg, usable = _resolve(args)
    for m, d, target in _each(usable):
        print(f"  {m.LABEL}: test command {' '.join(_test_cmd(d, m, target, cfg))}")
    return 0


def cmd_run(args):
    _root, cfg, usable = _resolve(args)
    failed = False
    lines = []
    for m, d, target in _each(usable):
        ok, line = _run_tests(m, d, target, cfg)
        failed |= not ok
        lines.append(line)
    print("\n" + "\n".join(lines) if lines else "nothing to run")
    return 1 if failed else 0


def _coverage(mod, d, target, out):
    why = getattr(mod, "coverage_unavailable", lambda r: None)(d)
    if why:
        return {"unavailable": why}
    cp = run(mod.coverage_cmd(d, target, out), cwd=d)
    if cp.returncode != 0:
        print(cp.stdout[-3000:])
        print(f"{mod.LABEL}: tests failed; coverage not measured")
        return None
    cov = mod.coverage_parse(d, out)
    if cov.total == 0:
        return {"unavailable": f"no coverage report found — see languages/{mod.KEY}.md"}
    return cov


def _coverage_block(mod, cov, threshold, out):
    ok = cov.percent >= threshold
    lines = [(f"{mod.LABEL:<10} coverage {cov.percent}% ({cov.covered}/{cov.total} lines) "
             f"{'✓' if ok else '✗ (min ' + str(threshold) + ')'}")]
    for path, pct in cov.under(threshold):
        lines.append(f"    {pct:5.1f}%  {path}")
    html = out / "html"
    if html.exists():
        lines.append(f"    html report: {html}")
    return "\n".join(lines)


def cmd_coverage(args):
    root, cfg, usable = _resolve(args)
    failed, blocks = False, []
    for m, d, target in _each(usable):
        cov = _coverage(m, d, target, _out(root, m))
        if cov is None:
            failed = True
            continue
        if isinstance(cov, dict):   # not measurable — not a gate failure
            blocks.append(f"{m.LABEL:<10} coverage not measurable — {cov['unavailable']}")
            continue
        failed |= cov.percent < cfg["coverage"]
        blocks.append(_coverage_block(m, cov, cfg["coverage"], _out(root, m, empty=False)))
    print("\n" + "\n\n".join(blocks) if blocks else "nothing measured")
    return 1 if failed else 0


def _audit_line(mod, d):
    """One language's audit line (plus indented findings), and whether it failed the gate."""
    if getattr(mod, "AUDIT_TOOL", None) is None:
        return f"{mod.LABEL:<10} audit not available — {mod.AUDIT_NONE}", False
    nothing = getattr(mod, "audit_nothing", lambda r: None)(d)
    if nothing:   # before the tool check: never "install X" for a tool that will then refuse the project
        return f"{mod.LABEL:<10} audit not available — {nothing}", False
    why = mod.audit_unavailable(d)
    if why:
        tool, install = mod.AUDIT_TOOL
        return f"{mod.LABEL}: missing {tool} — {install} — skipped", False
    cp = run(mod.audit_cmd(d), cwd=d)
    findings = mod.audit_findings(cp.stdout, cp.returncode)
    if findings == ["audit output not understood — see above"]:
        # Not a vulnerability count — an audit we could not read must not pass a push silently,
        # so this fails the gate too, just not as "N vulnerable" (it is not a finding).
        print(cp.stdout[-3000:])
        return f"{mod.LABEL}: audit output not understood — see above", True
    mark = "✗" if findings else "✓"
    lines = [f"{mod.LABEL:<10} audit {mark} {len(findings)} vulnerable"] + [f"    {f}" for f in findings]
    return "\n".join(lines), bool(findings)


def cmd_audit(args):
    _root, _cfg, usable = _resolve(args)
    failed, blocks = False, []
    for m, d, _target in _each(usable):
        block, bad = _audit_line(m, d)
        failed |= bad
        blocks.append(block)
    print("\n" + "\n".join(blocks) if blocks else "nothing audited")
    return 1 if failed else 0


def _source_count(d, mod, target):
    base = pathlib.Path(d) / (target or ".")
    skip = detect.SKIP_DIRS | getattr(mod, "SKIP_DIRS", set())   # the language's own vendored dirs
    return sum(1 for p in base.rglob(f"*{mod.SOURCE_EXT}") if not skip & set(p.relative_to(d).parts))


def _dirty(root, sandbox):
    """Tracked paths `git status --porcelain` reports changed, outside `sandbox`. Untracked (`??`)
    lines are never a defect signature here — a mutation tool's own scratch files it never
    committed are not "the suite writing to the real tree" (test-discipline rule 4; BACKLOG #34)."""
    cp = runner.run_on_host(["git", "status", "--porcelain"], cwd=root)   # git is the host's, container or not
    paths = (ln[3:] for ln in cp.stdout.splitlines() if not ln.startswith("??"))
    return {p for p in paths if not sandbox & set(pathlib.PurePath(p).parts)}


def _mutation(mod, root, d, target, out):
    why = mod.mutation_unavailable(d, target)
    if why:
        return {"unavailable": why}
    if not target:
        print(f"{mod.LABEL}: mutating {_source_count(d, mod, None)} files"
              " — a first run on the whole project takes a while; later runs are incremental"
              " where the tool supports it")
    where = getattr(mod, "mutation_cwd", lambda r, t: r)(d, target)   # a sub-project's own config
    sandbox = _SANDBOX | getattr(mod, "SANDBOX", set())   # the language's own legitimate scratch paths
    before = _dirty(root, sandbox)
    cp = run(mod.mutation_cmd(where, target, out), cwd=where)
    changed = sorted(_dirty(root, sandbox) - before)
    if changed:
        print(f"mutation run changed tracked files outside its sandbox: {' '.join(changed)} — the "
              "suite writes to the real tree under a planted defect (test-discipline rule 4; BACKLOG #34)")
        return {"unavailable": "mutation run modified the working tree — see above"}
    if cp.returncode not in (0, 1, 2):        # tools exit non-zero on survivors; a crash is higher
        print(cp.stdout[-3000:])
        return {"unavailable": f"mutation tool exited {cp.returncode}"}
    mut = mod.mutation_parse(where, out)
    if not mut.total:
        print(cp.stdout[-3000:])
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


def _analyze_one(m, root, d, target, cfg, no_mutation, failed_gates):
    """One language's coverage, TCE and lint: its analyze.json entry and its printed block.
    (None, None) when coverage could not be measured because the tests were red."""
    out = _out(root, m)
    sub = d.relative_to(root)
    cov = _coverage(m, d, target, out)
    if cov is None:
        return None, None
    tce = {"skipped": True} if no_mutation else _mutation(m, root, d, target, out)
    lint = m.lint(d, target, out)
    lint_note = lint if isinstance(lint, str) else None
    lint = [] if lint_note else lint
    if isinstance(cov, dict):   # not measurable — words, not a gate failure
        cov_result = cov
        cov_line = f"{m.LABEL:<10} coverage not measurable — {cov['unavailable']}"
    else:
        cov_result = {"percent": cov.percent, "under": cov.under(cfg["coverage"])}
        cov_line = _coverage_block(m, cov, cfg["coverage"], out)
        if cov.percent < cfg["coverage"]:
            failed_gates.add("coverage")
    if "score" in tce and tce["score"] < cfg["tce"]:
        failed_gates.add("tce")
    entry = {"coverage": cov_result, "tce": tce,
             "lint": [[str(sub / f.file), f.line, f.message] for f in lint], "lint_note": lint_note}
    lint_txt = f"not run — {lint_note}" if lint_note else f"{len(lint)} finding{'s' if len(lint) != 1 else ''}"
    lines = [cov_line, f"{'':<10} {_tce_line(tce, cfg['tce'])}    lint: {lint_txt}"]
    lines += [f"    survived  {s[0]}:{s[1]}  {s[2]}" for s in tce.get("survivors", [])]
    lines += [f"    lint      {sub / f.file}:{f.line}  {f.message}" for f in lint]
    lines += [f"    note: {c}" for c in (m.CAVEATS_FOR(d) if hasattr(m, "CAVEATS_FOR") else m.CAVEATS)]
    return entry, "\n".join(lines)


def cmd_analyze(args):
    result = {"when": int(time.time()), "target": args.path, "languages": {}}
    failed_gates, blocks = set(), []
    root, cfg, usable = _resolve(args)
    for m, d, target in _each(usable):
        ok, _ = _run_tests(m, d, target, cfg)
        if not ok:
            print(f"{m.LABEL}: tests failed; nothing measured")
            failed_gates.add("tests")
            continue
        entry, block = _analyze_one(m, root, d, target, cfg, args.no_mutation, failed_gates)
        if entry is None:
            failed_gates.add("tests")
            continue
        result["languages"][m.KEY] = entry
        blocks.append(block)
    if usable:
        out_path = pathlib.Path(root) / ".orclab" / "test" / "analyze.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=1))
    print("\n" + "\n\n".join(blocks) if blocks else "nothing measured")
    if failed_gates == {"tests"}:
        print("\ngates failed: tests — fix the failing tests first; generate cannot repair a red suite")
    elif failed_gates:
        print(f"\ngates failed: {', '.join(sorted(failed_gates))} — run `/orc-test generate` to repair")
    return 1 if failed_gates else 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="orc-test")
    p.add_argument("--cwd", default=".")
    p.add_argument("--lang", help="only this language KEY (python, javascript, ...)")
    p.set_defaults(fn=cmd_run, path=None, no_mutation=False)   # no subcommand means `run`
    sub = p.add_subparsers(dest="cmd")
    for name, fn in (("detect", cmd_detect), ("run", cmd_run), ("coverage", cmd_coverage),
                     ("audit", cmd_audit), ("analyze", cmd_analyze)):
        sp = sub.add_parser(name)
        sp.add_argument("path", nargs="?")
        sp.add_argument("--no-mutation", action="store_true")
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
    except ContainerUnavailable:
        print("container build failed — see above", file=sys.stderr)
        return 1
