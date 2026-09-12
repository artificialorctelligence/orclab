"""Swift: swift test (SPM, any OS) or xcodebuild (Mac only); xccov for coverage; Muter for TCE."""

import json
import pathlib
import platform
import shutil

from ..detect import SKIP_DIRS
from ..model import Coverage, Finding, Mutation, Survivor
from ..runner import run

KEY = "swift"
LABEL = "Swift"
SOURCE_EXT = ".swift"
MARKERS = ["Package.swift", "*.xcodeproj/project.pbxproj"]
TOOLS = {"swift": "install Swift (https://swift.org/install) — Xcode on a Mac",
         "xcodebuild": "install Xcode on a Mac (xcodebuild ships with it); a .xcodeproj cannot "
                        "be built or tested from Linux"}
CAVEATS = ["Muter has two open bugs (muter#307, #310, 2026) where SPM projects score 0%; treat "
           "a 0% TCE on an SPM package as the bug until a real run says otherwise.",
           "Muter's per-mutant detail is not parsed yet — survivors are listed per file."]


def _xcodeproj(root):
    """First .xcodeproj bundle at root, one, or two directories down (skipping SKIP_DIRS)."""
    root = pathlib.Path(root)
    for pattern in ("*.xcodeproj", "*/*.xcodeproj", "*/*/*.xcodeproj"):
        for p in sorted(root.glob(pattern)):
            if not (SKIP_DIRS & set(p.relative_to(root).parts)):
                return p
    return None


def missing(root):
    if _xcodeproj(root) and (platform.system() != "Darwin" or shutil.which("xcodebuild") is None):
        return ["xcodebuild"]
    return [] if shutil.which("swift") else ["swift"]


def _scheme(root):
    return _xcodeproj(root).stem


def test_cmd(root, target):
    if (proj := _xcodeproj(root)):
        rel = str(proj.relative_to(root))
        return ["xcodebuild", "test", "-project", rel, "-scheme", _scheme(root),
                "-destination", "platform=macOS"] + ([f"-only-testing:{target}"] if target else [])
    return ["swift", "test"] + (["--filter", target] if target else [])


def coverage_cmd(root, target, out):
    if (proj := _xcodeproj(root)):
        rel = str(proj.relative_to(root))
        return ["xcodebuild", "test", "-project", rel, "-scheme", _scheme(root),
                "-destination", "platform=macOS", "-enableCodeCoverage", "YES",
                "-resultBundlePath", str(pathlib.Path(out) / "result.xcresult")]
    return ["swift", "test", "--enable-code-coverage"]


def coverage_parse(root, out):
    out = pathlib.Path(out)
    if _xcodeproj(root):
        cp = run(["xcrun", "xccov", "view", "--report", "--json", str(out / "result.xcresult")], cwd=root)
        (out / "xccov.json").write_text(cp.stdout)
        report = out / "xccov.json"
    else:
        cp = run(["swift", "test", "--show-codecov-path"], cwd=root)
        report = pathlib.Path(cp.stdout.strip()) if cp.stdout.strip() else None
    if report is None or not report.exists():
        return Coverage(0, 0)
    try:
        return _parse_xccov(report, root)
    except ValueError:            # xccov printed something that is not its JSON report
        return Coverage(0, 0)


def _relativise(p, root):
    return str(pathlib.Path(p).relative_to(root)) if str(p).startswith(str(root)) else p


def _parse_xccov(path, root):
    data = json.loads(pathlib.Path(path).read_text())
    files = {}
    if "data" in data:   # SPM's `swift test --show-codecov-path`: llvm-cov export JSON, not xccov
        for f in data["data"][0].get("files", []):
            lines = f["summary"]["lines"]
            files[_relativise(f["filename"], root)] = (int(lines["covered"]), int(lines["count"]))
    else:                # xcodebuild + `xcrun xccov view --report --json`
        for target in data.get("targets", [data]):
            for f in target.get("files", []):
                files[_relativise(f["path"], root)] = (int(f["coveredLines"]), int(f["executableLines"]))
    return Coverage(sum(c for c, _ in files.values()), sum(t for _, t in files.values()), files)


def mutation_unavailable(root, target=None):
    if shutil.which("muter") is None:
        return "Muter not installed — brew install muter-mutation-testing/formulae/muter"
    if not (pathlib.Path(root) / "muter.conf.yml").exists():
        return "no muter.conf.yml — run `muter init` once in the project"
    return None


def mutation_cmd(root, target, out):
    cmd = ["muter", "run", "--format", "json", "--output", str(pathlib.Path(out) / "muter.json")]
    if target:
        cmd += ["--files-to-mutate", f"{target}/**/*.swift"]
    return cmd


def mutation_parse(root, out):
    report = pathlib.Path(out) / "muter.json"
    return _parse_muter(report) if report.exists() else Mutation(0, 0)


def _parse_muter(path):
    data = json.loads(pathlib.Path(path).read_text())
    survivors = [Survivor(f["fileName"], 0, f"file mutation score {f['mutationScore']}%")
                 for f in data.get("fileReports", []) if f.get("mutationScore", 100) < 100]
    return Mutation(int(data.get("numberOfKilledMutants", 0)),
                    int(data.get("totalAppliedMutationOperators", 0)), survivors)


def lint(root, target, out):
    if shutil.which("swiftlint") is None:
        return "SwiftLint not installed — brew install swiftlint"
    cp = run(["swiftlint", "lint", "--reporter", "json", "--quiet", target or "."], cwd=root)
    try:
        data = json.loads(cp.stdout[cp.stdout.index("["):])
    except ValueError:
        return f"swiftlint produced no JSON (exit {cp.returncode})"
    return [Finding(str(pathlib.Path(v["file"]).relative_to(root)), v["line"], f"{v['rule_id']}: {v['reason']}")
            for v in data if _is_test_file(v["file"])]


def _is_test_file(path):
    p = pathlib.PurePath(path)
    if p.name.endswith(("Tests.swift", "Test.swift")):
        return True
    return any(part in ("Tests", "tests", "Test", "test") for part in p.parts)
