"""C#: dotnet test, coverlet (lcov), Stryker.NET (Stryker JSON), xunit.analyzers via dotnet build."""

import json
import pathlib
import re
import shutil

from .. import lcov, probe, stryker
from ..model import Coverage, Finding, Mutation
from ..runner import run

KEY = "csharp"
LABEL = "C#"
SOURCE_EXT = ".cs"
MARKERS = ["*.csproj", "*.sln"]
TOOLS = {"dotnet": "install the .NET SDK (https://dotnet.microsoft.com/download)"}
CAVEATS = [("Stryker.NET 5.0.0 targets .NET 10; on an older SDK pin 4.16.0 "
           "(dotnet tool install -g dotnet-stryker --version 4.16.0).")]
SANDBOX = {".orclab", "StrykerOutput", "bin", "obj"}   # coverlet/Stryker.NET/dotnet build output

AUDIT_TOOL = ("dotnet", TOOLS["dotnet"])
_UNREADABLE = ["audit output not understood — see above"]


def audit_unavailable(root):
    return None if shutil.which("dotnet") else "dotnet not installed"


def audit_cmd(root):
    # Verb-first form: .NET 10 added `dotnet package list` as an alias and keeps this one, and
    # --format json needs SDK 7.0.200+. --include-transitive is passed because transitive
    # packages are not audited by default.
    return ["dotnet", "list", "package", "--vulnerable", "--include-transitive", "--format", "json"]


def _packages(data):
    """Every top-level and transitive package dict, across every project and target framework —
    one package is listed once per framework and per project, so the caller dedupes."""
    for proj in data["projects"]:
        for fw in proj.get("frameworks", []):
            yield from fw.get("topLevelPackages", []) + fw.get("transitivePackages", [])


def _vulns_of(pkg, seen):
    for v in pkg.get("vulnerabilities", []):
        key = (pkg["id"], pkg["resolvedVersion"], v["advisoryurl"])
        if key in seen:
            continue
        seen.add(key)
        yield (f"{pkg['id']} {pkg['resolvedVersion']}: {v['advisoryurl'].rpartition('/')[2]}"
               f" ({v.get('severity') or 'unscored'}) — fix not reported by NuGet")


def audit_findings(stdout, returncode):
    # dotnet exits 0 with vulnerable packages (NuGet/Home#11315, closed not-planned; the runner
    # fails only on a `problems` entry of level error) — so the report decides, and a reported
    # error (no restore, unreachable source) is the sentinel, not a clean pass. Restore chatter
    # may precede the JSON on .NET 10 (auto-restore), hence raw_decode from the first brace.
    try:
        data, _ = json.JSONDecoder().raw_decode(stdout, stdout.index("{"))
        if any(p["level"] == "error" for p in data.get("problems", [])):
            return _UNREADABLE
        seen = set()
        return [line for pkg in _packages(data) for line in _vulns_of(pkg, seen)]
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError, ValueError):
        return _UNREADABLE


_COLLECT = "--collect:XPlat Code Coverage"
_WARN = re.compile(r"^(?P<file>[^(]+)\((?P<line>\d+),\d+\): warning (?P<code>xUnit\d+): (?P<msg>.*?) \[", re.MULTILINE)


def missing(root):
    return [t for t in TOOLS if not probe.which(t)]


def test_cmd(root, target):
    return ["dotnet", "test"] + ([target] if target else [])


def coverage_cmd(root, target, out):
    return (["dotnet", "test"] + ([target] if target else []) +
            [_COLLECT, f"--results-directory={out}",
             "--", "DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=lcov"])


def coverage_parse(root, out):
    hits = list(pathlib.Path(out).rglob("coverage.info")) + list(pathlib.Path(out).rglob("*.lcov"))
    if not hits:
        return Coverage(0, 0)
    return lcov.parse(max(hits, key=lambda p: p.stat().st_mtime))


def mutation_unavailable(root, target=None):
    if shutil.which("dotnet-stryker") is None:
        return "Stryker.NET not installed — dotnet tool install -g dotnet-stryker"
    return None


def _stryker_out(root):
    # Stryker.NET keeps its baseline under --output; `.orclab/test/csharp/` is emptied every run,
    # so the report and baseline live beside it instead and survive from one run to the next.
    return pathlib.Path(root) / ".orclab" / "stryker-net"


def mutation_cmd(root, target, out):
    cmd = ["dotnet", "stryker", "--reporter", "json", "--reporter", "progress",
           "--with-baseline", "--output", str(_stryker_out(root))]
    if target:
        cmd += ["--mutate", f"{target}/**/*.cs"]
    return cmd


def mutation_parse(root, out):
    home = _stryker_out(root)
    p = stryker.find(home) if home.is_dir() else None
    return stryker.parse(p, root) if p else Mutation(0, 0)


def lint(root, target, out):
    cp = run(["dotnet", "build", "--no-incremental", "-warnaserror-"] + ([target] if target else []), cwd=root)
    return [Finding(m["file"], int(m["line"]), f"{m['code']}: {m['msg']}") for m in _WARN.finditer(cp.stdout)]
