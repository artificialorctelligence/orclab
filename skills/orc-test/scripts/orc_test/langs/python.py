"""Python: pytest, pytest-cov (lcov), mutmut 3, and a stdlib ast scan for test smells.

mutmut 3 keeps a copy of the tests under mutants/ (via also_copy) for its own runs; a later plain
pytest collects both copies and dies with "import file mismatch". Every command here passes
--ignore-glob=*mutants/* — a glob because each sub-project's mutmut has its own mutants/, and
no leading */ because pytest matches the glob against the full path, so */mutants/* would miss
a mutants/ at the directory pytest runs from.
"""

import ast
import importlib.util
import os
import pathlib
import re
import tomllib

from .. import lcov
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
    "mutmut runs from the nearest pyproject.toml with [tool.mutmut] at or above the path and"
    " mutates that file's source_paths; a path narrows only by picking which config runs.",
]
SANDBOX = {"mutants", ".coverage", "__pycache__", ".pytest_cache"}   # mutmut/pytest-cov's own scratch

_IGNORE = "--ignore-glob=*mutants/*"        # root and nested: each suite's mutmut has its own mutants/
_RESULT = re.compile(r"^\s*(\S+): (.+)$")
_HUNK = re.compile(r"^@@ -(\d+)")


def missing(root):
    return [t for t in TOOLS if importlib.util.find_spec(t) is None]


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


def coverage_cmd(root, target, out):
    src = target or "."
    return ["python3", "-m", "pytest", "-q", _IGNORE, f"--cov={src}",
            f"--cov-report=lcov:{out / 'coverage.lcov'}", f"--cov-report=html:{out / 'html'}"]


def coverage_parse(root, out):
    cov = lcov.parse(out / "coverage.lcov")
    files = {p: v for p, v in cov.files.items() if not _is_test_file(p)}   # --cov=. pulls tests/ in
    return Coverage(sum(c for c, _ in files.values()), sum(t for _, t in files.values()), files)


def mutation_unavailable(root, target=None):
    if importlib.util.find_spec("mutmut") is None:
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


def mutation_cmd(root, target, out):
    # mutmut takes its paths from pyproject.toml (see CAVEATS); `root` here is mutation_cwd().
    return ["python3", "-m", "mutmut", "run"]


def _show(root, key):
    return run(["python3", "-m", "mutmut", "show", key], cwd=root).stdout


def _results(root):
    # mutmut 3.7 lists only the non-killed mutants unless asked for all; "--all" takes a value
    return run(["python3", "-m", "mutmut", "results", "--all", "true"], cwd=root).stdout


def mutation_parse(root, out):
    text = _results(root)
    killed, total, survivors = 0, 0, []
    for line in text.splitlines():
        m = _RESULT.match(line)
        if not m:
            continue
        status = m.group(2)
        if status in ("killed", "timeout"):        # timeout: the mutant hung the suite — a catch
            killed += 1
            total += 1
        elif status == "survived":
            total += 1
            survivors.append(_survivor(root, m.group(1)))
        # else: suspicious, skipped, "no tests" — not a verdict on the mutant, don't count it
    return Mutation(killed, total, survivors)


def _survivor(root, key):
    """File, line and replacement text of one surviving mutant, from `mutmut show`'s diff.
    The mutated line is the hunk's start plus the context lines before the first `-` line."""
    diff = _show(root, key)
    file, line, context, change = "?", 0, 0, ""
    for raw in diff.splitlines():
        if raw.startswith("--- "):
            file = raw[4:].strip()
        elif (h := _HUNK.match(raw)):
            line, context = int(h.group(1)), 0
        elif raw.startswith("-") and not raw.startswith("---"):
            if context is not None:   # first removed line only; a multi-line statement has several
                line += context
                context = None        # frozen: the mutated line is found
        elif raw.startswith("+") and not raw.startswith("+++"):
            change = raw[1:].strip()
            break
        elif raw.startswith(" ") and context is not None:
            context += 1
    return Survivor(file, line, change)


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
        for n in body:
            if isinstance(n, ast.Call) and _dotted(n.func).endswith("sleep"):
                out.append(Finding(str(rel), n.lineno, f"sleep in {node.name}"))
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
