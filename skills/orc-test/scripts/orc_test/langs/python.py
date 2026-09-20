"""Python: pytest, pytest-cov (lcov), mutmut 3, and a stdlib ast scan for test smells.

mutmut 3 keeps a copy of the tests under mutants/ (via also_copy) for its own runs; a later plain
pytest collects both copies and dies with "import file mismatch". Every command here passes
--ignore-glob=*mutants/* — a glob because each sub-project's mutmut has its own mutants/, and
no leading */ because pytest matches the glob against the full path, so */mutants/* would miss
a mutants/ at the directory pytest runs from.
"""

import ast
import json
import os
import pathlib
import shutil

import tomllib

from .. import lcov, probe
from ..detect import SKIP_DIRS
from ..model import Coverage, Finding, Mutation, Survivor
from ..runner import run

KEY = "python"
LABEL = "Python"
SOURCE_EXT = ".py"
MARKERS = ["pyproject.toml", "setup.py", "setup.cfg"]
TOOLS = {"pytest": "pip install pytest", "pytest_cov": "pip install pytest-cov"}
CAVEATS = [
    "mutmut writes its cache and a copy of the tests to mutants/; add it to .gitignore.",
    ("mutmut runs from the nearest pyproject.toml with [tool.mutmut] at or above the path and"
    " mutates that file's source_paths; a path narrows only by picking which config runs."),
]
SANDBOX = {"mutants", ".coverage", "__pycache__", ".pytest_cache"}   # mutmut/pytest-cov's own scratch

AUDIT_TOOL = ("pip-audit", "pip install pip-audit")
_UNREADABLE = ["audit output not understood — see above"]


def audit_nothing(root):
    # audit_cmd's `.` reads the [project] table and nothing else — pip-audit refuses a pyproject
    # without one ("does not contain `project` section", seen live on Orclab 2026-09-19; BACKLOG
    # #54). requirements.txt is deliberately not consulted: `-r` would be a different audit_cmd.
    try:
        data = tomllib.loads((pathlib.Path(root) / "pyproject.toml").read_text())
    except (OSError, tomllib.TOMLDecodeError):
        data = {}
    return None if "project" in data else "nothing declared: pyproject.toml has no [project] table"


def audit_unavailable(root):
    return None if probe.python_module("pip_audit") else "pip-audit not installed"


def audit_cmd(root):
    # `.` audits the project's own declared dependencies (pyproject.toml), not whatever happens to
    # be in the environment; README: "audit a local Python project at the given path".
    return ["python3", "-m", "pip_audit", "-f", "json", "--progress-spinner", "off", "."]


def _vulns_of(dep, seen):
    for v in dep.get("vulns", []):
        key = (dep["name"], dep["version"], v.get("id", "?"))
        if key in seen:
            continue
        seen.add(key)
        ids = ", ".join([v.get("id", "?")] + v.get("aliases", []))
        fix = ", ".join(v.get("fix_versions", [])) or "none published"
        yield f"{dep['name']} {dep['version']}: {ids} — fix {fix}"


def audit_findings(stdout, returncode):
    # Valid-but-wrong-shape JSON (a dependency missing name/version, a top-level int, a vulns
    # entry that isn't a dict, ...) must land on the sentinel too, not crash the caller — "raises
    # nothing" per the interface. seen/dedupe: pip-audit lists the same advisory twice for one
    # package when it comes from more than one source (found in the real captured fixture); the
    # ✗ N count is a count of distinct vulnerabilities, not of records.
    try:
        # runner.run merges stderr, and pip-audit prints its one-line summary there before the
        # JSON ("No known vulnerabilities found" / "Found N known vulnerabilities in M packages",
        # seen live 2026-09-19); read from the first `{`, the way csharp.py does.
        data, _ = json.JSONDecoder().raw_decode(stdout, stdout.index("{"))
        seen = set()
        return [line for dep in data.get("dependencies", []) for line in _vulns_of(dep, seen)]
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError, ValueError):
        return _UNREADABLE


_IGNORE = "--ignore-glob=*mutants/*"        # root and nested: each suite's mutmut has its own mutants/
_KILLED = {1, 3, 36, 24, -24, 152, 255}     # mutmut's status_by_exit_code: "killed" and "timeout"
MUTMUT_DIFFS = pathlib.Path(__file__).parents[1] / "mutmut_diffs.py"


def missing(root):
    return [t for t in TOOLS if not probe.python_module(t)]


def _has_tests(base):
    return base.is_file() or any(base.rglob("test_*.py")) or any(base.rglob("*_test.py"))


def _is_test_file(path):
    p = pathlib.PurePath(path)
    return bool({"tests", "test"} & set(p.parts[:-1])) or p.name.startswith("test_") or p.name.endswith("_test.py")


def test_cmd(root, target):
    # A source-only path would make pytest collect 0 tests; then the whole suite runs and the
    # path narrows only what coverage measures (see languages/python.md).
    narrow = target and _has_tests(pathlib.Path(root) / target)
    return ["python3", "-m", "pytest", "-q", _IGNORE] + ([target] if narrow else [])


def _cov_roots(root, target):
    """One --cov=<dir> per directory coverage.py would otherwise never look inside. It lists a
    never-imported file only by walking down from a --cov dir through directories that have an
    __init__.py, so a src/ without one hid every unexecuted file beneath it (BACKLOG #42). The dir
    given as a root is exempt, so every init-less dir on the way to a .py file becomes one."""
    root = pathlib.Path(root)
    base = root / (target or ".")
    roots = set()
    for p in base.rglob("*.py"):
        if SKIP_DIRS & set(p.relative_to(root).parts):
            continue
        roots.update(d for d in p.parents if base in d.parents and not (d / "__init__.py").exists())
    return [target or "."] + sorted(os.path.relpath(d, root) for d in roots)


def coverage_cmd(root, target, out):
    return ["python3", "-m", "pytest", "-q", _IGNORE] + [f"--cov={d}" for d in _cov_roots(root, target)] + [
            f"--cov-report=lcov:{out / 'coverage.lcov'}", f"--cov-report=html:{out / 'html'}"]


def coverage_parse(root, out):
    cov = lcov.parse(out / "coverage.lcov")
    files = {p: v for p, v in cov.files.items() if not _is_test_file(p)}   # --cov=. pulls tests/ in
    return Coverage(sum(c for c, _ in files.values()), sum(t for _, t in files.values()), files)


def mutation_unavailable(root, target=None):
    if not probe.python_module("mutmut"):
        return "mutmut not installed — pip install mutmut"
    if _mutmut_config(root, target) is None:
        where = pathlib.Path(root) / (target or ".")
        return (f"no [tool.mutmut] found in any pyproject.toml at or above {where} — add [tool.mutmut]"
                " with source_paths = [...]; see languages/python.md")
    return None


def _mutmut_config(root, target):
    """The nearest dir from `target` up to `root` whose pyproject.toml has a [tool.mutmut]
    section, or None. A `target` whose ".." walks above `root` never searches above it."""
    root = pathlib.Path(root)
    here = root / (target or ".")
    normalized = pathlib.Path(os.path.normpath(here))
    if normalized != root and root not in normalized.parents:
        return None
    for d in [here, *here.parents]:
        pyproject = d / "pyproject.toml"
        text = pyproject.read_text() if pyproject.is_file() else ""
        if text and tomllib.loads(text).get("tool", {}).get("mutmut") is not None:
            return d
        if d == root:
            break
    return None


def mutation_cwd(root, target):
    """Where mutmut runs. mutmut names mutants from the file path relative to its cwd and must
    import the code by that same name, so a package under skills/x/scripts/ runs from there."""
    return _mutmut_config(root, target) or pathlib.Path(root)


def _drop_cache_if_tests_changed(cwd):
    """mutmut's cache (mutants/) is keyed by source-function hash only: a test written to kill a
    survivor changes nothing it hashes, so the next run reports the old verdicts and `generate`'s
    after-number equals its before-number (BACKLOG #35, 2026-09-13). If any test file is newer
    than the cache, the whole directory goes and the run is full — the verdicts (*.meta) cannot
    go alone; without them beside the copied sources mutmut finds 0 mutants."""
    mutants = pathlib.Path(cwd) / "mutants"
    metas = list(mutants.rglob("*.meta"))
    if not metas:
        return
    cached = min(m.stat().st_mtime for m in metas)
    tests = (p for p in pathlib.Path(cwd).rglob("*.py")
             if "mutants" not in p.parts and (p.name.startswith("test_") or p.name == "conftest.py"))
    # ponytail: any newer test file drops the whole cache; per-function invalidation via
    # mutmut-stats.json's tests_by_mangled_function_name if a full rerun ever hurts
    if any(p.stat().st_mtime > cached for p in tests):
        shutil.rmtree(mutants)


def mutation_cmd(root, target, out):
    # mutmut takes its paths from pyproject.toml (see CAVEATS); `root` here is mutation_cwd().
    _drop_cache_if_tests_changed(root)
    return ["python3", "-m", "mutmut", "run"]


def _diffs(root, alive):
    """{key: diff} for every survivor, from one process (mutmut_diffs.py) rather than one
    `mutmut show` each — that loop was ~75% of a real project's analyze (BACKLOG #42)."""
    if not alive:
        return {}
    stdin = "".join(f"{key} {file}\n" for key, file in alive)
    # the script's text, not its path: inside a container only the project dir is mounted, not
    # Orclab's own plugin directory where MUTMUT_DIFFS lives (v23)
    out = run(["python3", "-c", MUTMUT_DIFFS.read_text()], cwd=root, input=stdin).stdout
    blocks = (b.partition("\n") for b in ("\n" + out).split("\n# ")[1:])
    return {key: diff.rstrip("\n") for key, _, diff in blocks}


def mutation_parse(root, out):
    """Verdicts from mutmut's own cache: mutants/<file>.meta holds every mutant's exit code, which is
    all `mutmut results` prints and what `mutmut show` walks to find a key's file."""
    root = pathlib.Path(root)
    killed, total, alive = 0, 0, []
    for meta in sorted((root / "mutants").rglob("*.meta")):
        file = str(meta.relative_to(root / "mutants"))[:-len(".meta")]
        if not (root / file).is_file():
            continue                            # a stale cache entry; mutmut's results skips it too
        for key, code in json.loads(meta.read_text())["exit_code_by_key"].items():
            if code in _KILLED:                 # timeout: the mutant hung the suite — a catch
                killed += 1
                total += 1
            elif code == 0:
                total += 1
                alive.append((key, file))
            # else: suspicious, skipped, "no tests", not checked — not a verdict on the mutant, don't count it
    diffs = _diffs(root, alive)
    return Mutation(killed, total, [_survivor(root, key, file, diffs.get(key, "")) for key, file in alive])


def _survivor(root, key, file, diff):
    """File, line and replacement text of one surviving mutant. The diff is of the function alone,
    so its hunk numbers are function-relative (BACKLOG #42): the removed line is found by its
    text inside the function's real span in the file instead."""
    removed, change = "", ""
    for raw in diff.splitlines():
        if raw.startswith("-") and not raw.startswith("---") and not removed:
            removed = raw[1:]                   # first removed line only; a multi-line statement has several
        elif raw.startswith("+") and not raw.startswith("+++"):
            change = raw[1:].strip()
            break
    return Survivor(file, _line_of(pathlib.Path(root) / file, key, removed), change)


def _line_of(path, key, removed):
    """The file line holding `removed`, inside the function the key names — mutmut keys are
    module.x_func__mutmut_N, or module.xǁClassǁmethod__mutmut_N for a method: the def line when
    the text is not in it, 0 when the function is not in the file."""
    name = key.partition("__mutmut_")[0].rpartition(".")[2]
    cls, sep, func = name.rpartition("ǁ")
    cls, func = (cls[2:], func) if sep else (None, func[2:])
    try:
        text = path.read_text()
        body, lines = ast.parse(text).body, text.splitlines()
    except (OSError, SyntaxError):
        return 0
    if cls:
        body = next((n.body for n in body if isinstance(n, ast.ClassDef) and n.name == cls), [])
    fn = next((n for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == func), None)
    if fn is None:
        return 0
    # ponytail: first line in the function with that text; the diff's context lines would tell
    # apart a statement repeated inside one function
    span = range(fn.lineno, fn.end_lineno + 1)
    return next((i for i in span if lines[i - 1].strip() == removed.strip()), fn.lineno)


def lint(root, target, out):
    base = pathlib.Path(root) / (target or ".")
    paths = set(base.rglob("test_*.py")) | set(base.rglob("*_test.py"))
    findings = []
    for path in sorted(paths):
        if SKIP_DIRS & set(path.relative_to(root).parts):
            continue
        findings += _scan(path, path.relative_to(root))
    return findings


def _test_funcs(body, cls):
    """(enclosing class name or None, FunctionDef) for every test* def, one class level deep —
    duplicate-name scoping needs to know which class (if any) a function belongs to, which
    plain ast.walk doesn't track."""
    for node in body:
        if isinstance(node, ast.ClassDef):
            yield from _test_funcs(node.body, node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            yield cls, node


def _scan(path, rel):
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return []
    seen, out = set(), []
    for cls, node in _test_funcs(tree.body, None):
        key = (cls, node.name)
        if key in seen:
            out.append(Finding(str(rel), node.lineno, f"duplicate test name {node.name}"))
        seen.add(key)
        body = list(ast.walk(node))
        skip = next((d for d in node.decorator_list if _is_skip(d)), None)
        if skip is not None:
            out.append(Finding(str(rel), skip.lineno, f"skipped: {node.name}"))
        if not any(isinstance(n, ast.Assert) or _is_assert_call(n) for n in body):
            out.append(Finding(str(rel), node.lineno, f"no assertion in {node.name}"))
        out += [Finding(str(rel), n.lineno, f"sleep in {node.name}")
                for n in body if isinstance(n, ast.Call) and _dotted(n.func).endswith("sleep")]
    return out


def _dotted(func):
    parts = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if isinstance(func, ast.Name):
        parts.append(func.id)
    return ".".join(reversed(parts))


def _is_skip(dec):
    d = dec.func if isinstance(dec, ast.Call) else dec
    return _dotted(d).endswith(("mark.skip", "mark.skipif"))


def _is_assert_call(n):
    if not isinstance(n, ast.Call):
        return False
    name = _dotted(n.func)
    return name.endswith("raises") or ".assert_" in name or name.startswith("assert")
