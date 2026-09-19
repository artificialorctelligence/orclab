import pathlib

from orc_test.langs import csharp as cs
from orc_test.model import Coverage, Mutation

_FIX = pathlib.Path(__file__).parent / "fixtures"
_UNREADABLE = ["audit output not understood — see above"]


# --- audit: dotnet list package --vulnerable (fixtures/dotnet_list_vulnerable.json, hand-built) ---

def test_audit_tool_and_command(monkeypatch):
    assert cs.AUDIT_TOOL == ("dotnet", cs.TOOLS["dotnet"])
    assert cs.audit_cmd("/x") == ["dotnet", "list", "package", "--vulnerable", "--include-transitive", "--format", "json"]
    monkeypatch.setattr(cs.shutil, "which", lambda tool: None)
    assert "dotnet" in cs.audit_unavailable("/x")
    monkeypatch.setattr(cs.shutil, "which", lambda tool: "/usr/bin/dotnet")
    assert cs.audit_unavailable("/x") is None


def test_audit_findings_dedupes_across_target_frameworks():
    # The fixture repeats the same packages under net8.0 and net9.0: three lines, not six —
    # and dotnet exited 0, so the report alone decides.
    lines = cs.audit_findings((_FIX / "dotnet_list_vulnerable.json").read_text(), 0)
    assert lines == [
        "A 1.0.0: GHSA-g8j6-m4p7-5rfq (High) — fix not reported by NuGet",
        "A 1.0.0: GHSA-v76m-f5cx-8rg4 (Moderate) — fix not reported by NuGet",
        "D 1.1.0: GHSA-5c66-x4wm-rjfx (Critical) — fix not reported by NuGet",
    ]


def test_audit_findings_skips_restore_chatter_and_fails_on_a_reported_error():
    clean = 'Restore complete (0.6s)\n\n{"version": 1, "parameters": "--vulnerable", "projects": [{"path": "a.csproj", "frameworks": [{"framework": "net8.0", "topLevelPackages": []}]}]}\n'
    assert cs.audit_findings(clean, 0) == []
    # No assets file / unreachable source: a `problems` error is the one thing that exits 1 —
    # and an empty projects list beside it must not read as "0 vulnerable".
    err = '{"version": 1, "parameters": "--vulnerable", "problems": [{"level": "error", "text": "No assets file was found"}], "projects": []}'
    assert cs.audit_findings(err, 1) == _UNREADABLE
    warn = '{"version": 1, "parameters": "--vulnerable", "problems": [{"level": "warning", "text": "NU1905"}], "projects": []}'
    assert cs.audit_findings(warn, 0) == []
    unscored = '{"projects": [{"frameworks": [{"transitivePackages": [{"id": "X", "resolvedVersion": "1", "vulnerabilities": [{"severity": "", "advisoryurl": "https://a/GHSA-9"}]}]}]}]}'
    assert cs.audit_findings(unscored, 0) == ["X 1: GHSA-9 (unscored) — fix not reported by NuGet"]


def test_audit_unreadable():
    assert cs.audit_findings("error MSB1003: Specify a project or solution file", 1) == _UNREADABLE   # no brace
    assert cs.audit_findings('{"projects": [{"frameworks": [{"topLevelPackages": [{"vulnerabilities": [{}]}]}]}]}', 0) == _UNREADABLE
    assert cs.audit_findings("{", 0) == _UNREADABLE
    assert cs.audit_findings("", 0) == _UNREADABLE


def test_commands(tmp_path):
    (tmp_path / "App.sln").write_text("")
    assert cs.test_cmd(tmp_path, None) == ["dotnet", "test"]
    assert cs.test_cmd(tmp_path, "tests/App.Tests") == ["dotnet", "test", "tests/App.Tests"]
    out = tmp_path / "out"
    cmd = cs.coverage_cmd(tmp_path, None, out)
    assert cmd[:3] == ["dotnet", "test", "--collect:XPlat Code Coverage"]
    assert f"--results-directory={out}" in cmd
    assert "DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=lcov" in " ".join(cmd)

    cmd2 = cs.coverage_cmd(tmp_path, "tests/App.Tests", out)
    assert cmd2[2] == "tests/App.Tests"
    assert cmd2.index("--") > cmd2.index("tests/App.Tests")


def test_coverage_parse_finds_lcov_under_results(tmp_path):
    d = tmp_path / "guid-1"
    d.mkdir()
    (d / "coverage.info").write_text("SF:App/A.cs\nDA:1,1\nDA:2,0\nend_of_record\n")
    assert cs.coverage_parse(tmp_path, tmp_path).files == {"App/A.cs": (1, 2)}


def test_coverage_parse_no_report(tmp_path):
    assert cs.coverage_parse(tmp_path, tmp_path) == Coverage(0, 0)


def test_mutation_needs_stryker_tool(tmp_path, monkeypatch):
    monkeypatch.setattr(cs.shutil, "which", lambda name: None)
    assert "dotnet tool install -g dotnet-stryker" in cs.mutation_unavailable(tmp_path)
    monkeypatch.setattr(cs.shutil, "which", lambda name: "/usr/bin/dotnet-stryker")
    assert cs.mutation_unavailable(tmp_path) is None
    cmd = cs.mutation_cmd(tmp_path, "src/App", tmp_path / "out")
    assert cmd[:3] == ["dotnet", "stryker", "--reporter"] and "--with-baseline" in cmd
    assert "--mutate" in cmd and "src/App/**/*.cs" in cmd
    # the baseline lives under --output, and .orclab/test/csharp is emptied every run: keep it apart
    assert cmd[cmd.index("--output") + 1] == str(tmp_path / ".orclab" / "stryker-net")


def test_mutation_parse_no_report(tmp_path):
    assert cs.mutation_parse(tmp_path, tmp_path / "out") == Mutation(0, 0)


def test_mutation_parse_reads_the_stryker_net_home_not_the_wiped_out_dir(tmp_path):
    home = tmp_path / ".orclab" / "stryker-net" / "reports"
    home.mkdir(parents=True)
    (home / "mutation-report.json").write_text(
        '{"files": {"A.cs": {"mutants": [{"status": "Killed", "mutatorName": "x", "location": {"start": {"line": 1}}}]}}}')
    assert cs.mutation_parse(tmp_path, tmp_path / "out") == Mutation(1, 1)


def test_lint_parses_xunit_analyzer_warnings(tmp_path, monkeypatch):
    out = ("App.Tests/AT.cs(12,9): warning xUnit2013: Do not use Assert.Equal() to check for collection size. "
           "[/x/App.Tests/App.Tests.csproj]\n"
           "App.Tests/AT.cs(20,5): warning xUnit1004: Test methods should not be skipped. [/x/App.Tests/App.Tests.csproj]\n"
           "App.Tests/AT.cs(30,1): warning CS0168: unrelated [/x/App.Tests/App.Tests.csproj]\n")
    monkeypatch.setattr(cs, "run", lambda cmd, cwd: type("R", (), {"stdout": out, "returncode": 0})())
    findings = cs.lint(tmp_path, None, tmp_path)
    assert [(f.file, f.line) for f in findings] == [("App.Tests/AT.cs", 12), ("App.Tests/AT.cs", 20)]


def test_source_ext():
    assert cs.SOURCE_EXT == ".cs"
