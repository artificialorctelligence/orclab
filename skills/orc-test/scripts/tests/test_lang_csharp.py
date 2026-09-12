from orc_test.langs import csharp as cs
from orc_test.model import Coverage, Mutation


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
