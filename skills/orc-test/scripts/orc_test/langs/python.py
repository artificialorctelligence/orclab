"""Python: pytest, pytest-cov (lcov), mutmut 3, and a stdlib ast scan for test smells.

mutmut 3 copies the tests into mutants/ for its own runs; a later plain pytest collects both
copies and dies with "import file mismatch". Every command here passes --ignore=mutants.
"""

import ast
import importlib.util
import pathlib
import re

from .. import lcov
from ..model import Finding, Mutation, Survivor
from ..runner import run

KEY = "python"
LABEL = "Python"
MARKERS = ["pyproject.toml", "setup.py", "setup.cfg"]
TOOLS = {"pytest": "pip install pytest", "pytest_cov": "pip install pytest-cov"}
CAVEATS = ["mutmut writes its cache and a copy of the tests to mutants/; add it to .gitignore."]

_IGNORE = "--ignore=mutants"
_RESULT = re.compile(r"^\s*(\S+): (.+)$")
_HUNK = re.compile(r"^@@ -(\d+)")


def missing(root):
    return [t for t in TOOLS if importlib.util.find_spec(t) is None]


def test_cmd(root, target):
    return ["python3", "-m", "pytest", "-q", _IGNORE] + ([target] if target else [])


def coverage_cmd(root, target, out):
    src = target or "."
    return ["python3", "-m", "pytest", "-q", _IGNORE, f"--cov={src}",
            f"--cov-report=lcov:{out / 'coverage.lcov'}", f"--cov-report=html:{out / 'html'}"]


def coverage_parse(root, out):
    return lcov.parse(out / "coverage.lcov")


def mutation_unavailable(root):
    if importlib.util.find_spec("mutmut") is None:
        return "mutmut not installed — pip install mutmut"
    return None


def mutation_cmd(root, target, out):
    # mutmut takes its paths from pyproject.toml; `target` narrows nothing here, and the
    # report says so. mutation_parse reads the `mutmut results` listing from out/results.txt,
    # written there by whoever runs this command (mirrors coverage_parse reading coverage.lcov).
    return ["python3", "-m", "mutmut", "run"]


def _show(root, key):
    return run(["python3", "-m", "mutmut", "show", key], cwd=root).stdout


def mutation_parse(root, out):
    text = (out / "results.txt").read_text()
    killed, total, survivors = 0, 0, []
    for line in text.splitlines():
        m = _RESULT.match(line)
        if not m or m.group(2) == "no tests":
            continue
        total += 1
        if m.group(2) == "killed":
            killed += 1
        elif m.group(2) == "survived":
            survivors.append(_survivor(root, m.group(1)))
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
            line += context
            context = None            # frozen: the mutated line is found
        elif raw.startswith("+") and not raw.startswith("+++"):
            change = raw[1:].strip()
            break
        elif raw.startswith(" ") and context is not None:
            context += 1
    return Survivor(file, line, change)


def lint(root, target, out):
    base = pathlib.Path(root) / (target or ".")
    findings = []
    for path in sorted(base.rglob("test_*.py")):
        if "mutants" in path.parts:
            continue
        findings += _scan(path, path.relative_to(root))
    return findings


def _scan(path, rel):
    tree = ast.parse(path.read_text())
    seen, out = set(), []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test"):
            continue
        if node.name in seen:
            out.append(Finding(str(rel), node.lineno, f"duplicate test name {node.name}"))
        seen.add(node.name)
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
    if isinstance(n, ast.Call):
        name = _dotted(n.func)
        return name.endswith("raises") or ".assert_" in name or name.startswith("assert")
    return isinstance(n, ast.With) and any(_is_assert_call(i.context_expr) for i in n.items)
