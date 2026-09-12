"""C#: dotnet test, coverlet (lcov), Stryker.NET (Stryker JSON), xunit.analyzers via dotnet build."""

import pathlib
import re
import shutil

from .. import lcov, stryker
from ..model import Coverage, Finding, Mutation
from ..runner import run

KEY = "csharp"
LABEL = "C#"
SOURCE_EXT = ".cs"
MARKERS = ["*.csproj", "*.sln"]
TOOLS = {"dotnet": "install the .NET SDK (https://dotnet.microsoft.com/download)"}
CAVEATS = ["Stryker.NET 5.0.0 targets .NET 10; on an older SDK pin 4.16.0 "
           "(dotnet tool install -g dotnet-stryker --version 4.16.0)."]
SANDBOX = {".orclab", "StrykerOutput", "bin", "obj"}   # coverlet/Stryker.NET/dotnet build output

_COLLECT = "--collect:XPlat Code Coverage"
_WARN = re.compile(r"^(?P<file>[^(]+)\((?P<line>\d+),\d+\): warning (?P<code>xUnit\d+): (?P<msg>.*?) \[", re.M)


def missing(root):
    return [t for t in TOOLS if shutil.which(t) is None]


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
