import json
import pathlib
import subprocess

from orc_test import langs
from orc_test.model import Mutation, Survivor
from tests.helpers import fake, make_repo, run


def test_analyze_lint_not_run_is_a_reason_not_a_count(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(9, 10, []), lint="eslint not configured")])
    _code, out = run(["analyze"], make_repo(tmp_path), capsys)
    assert "lint: not run — eslint not configured" in out


def test_analyze_all_gates_and_result_file(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(6, 10, [Survivor("src/a.py", 2, "x <= 1")]))])
    code, out = run(["analyze"], repo, capsys)
    assert code == 1
    assert "coverage 90.0%" in out and "TCE 60.0% ✗ (min 70)" in out and "lint: 1 finding" in out
    assert "src/a.py:2  x <= 1" in out and "a caveat" in out
    assert "gates failed: tce — run `/orc-test generate` to repair" in out
    data = json.loads((repo / ".orclab" / "test" / "analyze.json").read_text())
    assert data["languages"]["fake"]["tce"]["survivors"] == [["src/a.py", 2, "x <= 1"]]


def test_analyze_unavailable_mutation_is_words_not_a_number(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(unavailable="no mutation tool exists for Fake")])
    _code, out = run(["analyze"], make_repo(tmp_path), capsys)
    assert "TCE not measurable — no mutation tool exists for Fake" in out
    assert "TCE 0" not in out


def test_analyze_no_mutation_flag(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(9, 10, []))])
    _code, out = run(["analyze", "--no-mutation"], make_repo(tmp_path), capsys)
    assert "TCE skipped" in out and "$ true" in out


def test_analyze_announces_size_on_whole_repo(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    for i in range(3):
        (repo / f"m{i}.py").write_text("x = 1\n")
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(9, 10, []))])
    _code, out = run(["analyze"], repo, capsys)
    assert "mutating 4 files" in out    # 3 modules + tests/test_ok.py; first run, no cache yet


def test_analyze_no_mutants_is_words_not_a_fabricated_zero_and_shows_the_tool_output(tmp_path, capsys, monkeypatch):
    m = fake(Mutation(0, 0, []))
    m.mutation_cmd = lambda root, t, out: ["bash", "-c", "echo 'BadTestExecutionCommandsException: no tests'"]
    monkeypatch.setattr(langs, "ALL", [m])
    _code, out = run(["analyze"], make_repo(tmp_path), capsys)
    assert "TCE not measurable — mutation tool produced no mutants" in out
    assert "BadTestExecutionCommandsException" in out     # the tool's own error, not hidden
    assert "TCE 0" not in out


def test_analyze_red_suite_is_not_offered_generate(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(test_cmd=["false"])])
    code, out = run(["analyze"], make_repo(tmp_path), capsys)
    assert code == 1
    assert "gates failed: tests — fix the failing tests first; generate cannot repair a red suite" in out
    assert "generate` to repair" not in out


def test_analyze_absent_coverage_report_is_words_not_zero_percent(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(9, 10, []), cov=(0, 0))])
    code, out = run(["analyze"], make_repo(tmp_path), capsys)
    assert code == 0
    assert "coverage not measurable — no coverage report found — see languages/fake.md" in out
    assert "coverage 0.0%" not in out


def test_mutation_run_that_dirties_the_tree_is_reported_not_scored(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    (repo / "tracked.txt").write_text("x\n")
    subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], check=True)
    m = fake(Mutation(9, 10, []))
    m.mutation_cmd = lambda root, t, out: ["bash", "-c", "echo x >> tracked.txt; mkdir -p mutants; touch mutants/ok"]
    monkeypatch.setattr(langs, "ALL", [m])
    _code, out = run(["analyze"], repo, capsys)
    assert "$ git status --porcelain" in out
    assert "mutation run changed tracked files outside its sandbox: tracked.txt — the suite writes" in out
    assert "BACKLOG #34" in out
    assert "TCE not measurable — mutation run modified the working tree — see above" in out
    assert "mutants" not in out.split("outside its sandbox:")[1].split("—")[0]   # mutants/ is the tool's own


def test_mutation_run_that_only_writes_its_sandbox_is_scored(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], check=True)
    m = fake(Mutation(9, 10, []))
    m.mutation_cmd = lambda root, t, out: ["bash", "-c", "mkdir -p mutants; touch mutants/ok .coverage"]
    monkeypatch.setattr(langs, "ALL", [m])
    code, out = run(["analyze"], repo, capsys)
    assert code == 0 and "TCE 90.0% ✓" in out


def test_mutation_run_that_rewrites_a_committed_sandbox_file_is_scored(tmp_path, capsys, monkeypatch):
    # javascript.py's own caveat tells a user to commit reports/stryker-incremental.json; a
    # module's SANDBOX must cover that even though it's tracked (BACKLOG #34 follow-up).
    repo = make_repo(tmp_path)
    (repo / "reports").mkdir()
    (repo / "reports" / "stryker-incremental.json").write_text("{}\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], check=True)
    m = fake(Mutation(9, 10, []))
    m.mutation_cmd = lambda root, t, out: ["bash", "-c", "echo '{\"x\":1}' > reports/stryker-incremental.json"]
    m.SANDBOX = {"reports"}
    monkeypatch.setattr(langs, "ALL", [m])
    code, out = run(["analyze"], repo, capsys)
    assert code == 0 and "TCE 90.0% ✓" in out


def test_mutation_run_that_rewrites_a_committed_file_with_no_sandbox_is_not_measurable(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    (repo / "reports").mkdir()
    (repo / "reports" / "stryker-incremental.json").write_text("{}\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], check=True)
    m = fake(Mutation(9, 10, []))
    m.mutation_cmd = lambda root, t, out: ["bash", "-c", "echo '{\"x\":1}' > reports/stryker-incremental.json"]
    monkeypatch.setattr(langs, "ALL", [m])
    _code, out = run(["analyze"], repo, capsys)
    assert "mutation run changed tracked files outside its sandbox: reports/stryker-incremental.json" in out
    assert "TCE not measurable — mutation run modified the working tree — see above" in out


def test_mutation_run_that_creates_an_untracked_file_is_scored(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], check=True)
    m = fake(Mutation(9, 10, []))
    m.mutation_cmd = lambda root, t, out: ["bash", "-c", "echo x > newthing.log"]   # untracked, no SANDBOX
    monkeypatch.setattr(langs, "ALL", [m])
    code, out = run(["analyze"], repo, capsys)
    assert code == 0 and "TCE 90.0% ✓" in out


def test_analyze_writes_result_file_even_when_every_language_fails_tests(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    monkeypatch.setattr(langs, "ALL", [fake(test_cmd=["false"])])
    _code, _out = run(["analyze"], repo, capsys)
    data = json.loads((repo / ".orclab" / "test" / "analyze.json").read_text())
    assert data["languages"] == {}


def test_analyze_coverage_unavailable_is_words_not_a_failed_gate(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    monkeypatch.setattr(langs, "ALL", [fake(Mutation(9, 10, []), coverage_unavailable="no coverage tool for Fake")])
    code, out = run(["analyze"], repo, capsys)
    assert code == 0
    assert out.count("coverage not measurable — no coverage tool for Fake") == 1
    data = json.loads((repo / ".orclab" / "test" / "analyze.json").read_text())
    assert data["languages"]["fake"]["coverage"] == {"unavailable": "no coverage tool for Fake"}


def test_analyze_rebases_survivors_from_a_sub_project_to_the_root(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    m = fake(Mutation(9, 10, [Survivor("pkg/a.py", 2, "x <= 1")]))
    (repo / "skills" / "x" / "scripts").mkdir(parents=True)
    m.mutation_cwds = lambda root, target: [pathlib.Path(root) / "skills" / "x" / "scripts"]
    monkeypatch.setattr(langs, "ALL", [m])
    _code, out = run(["analyze"], repo, capsys)
    assert "skills/x/scripts/pkg/a.py:2  x <= 1" in out


def test_analyze_sums_tce_over_every_sub_project_config(tmp_path, capsys, monkeypatch):
    """Six packages with their own [tool.mutmut] and a root with none is one TCE line, not
    `not measurable` (v0.25.0 was released on that line, 2026-09-20)."""
    repo = make_repo(tmp_path)
    subs = [repo / "skills" / n / "scripts" for n in ("a", "b")]
    for d in subs:
        d.mkdir(parents=True)
    m = fake()
    m.mutation_cwds = lambda root, target: subs
    m.mutation_parse = lambda root, out: (Mutation(9, 10, [Survivor("pkg/a.py", 2, "x <= 1")])
                                          if root == subs[0] else Mutation(5, 10))
    monkeypatch.setattr(langs, "ALL", [m])
    _code, out = run(["analyze"], repo, capsys)
    assert "TCE 70.0% ✓" in out and "skills/a/scripts/pkg/a.py:2  x <= 1" in out
    result = json.loads((repo / ".orclab" / "test" / "analyze.json").read_text())
    assert result["languages"]["fake"]["tce"]["killed"] == 14


def test_analyze_reads_the_report_when_the_tool_exits_high(tmp_path, capsys, monkeypatch):
    # mutation_test 1.8.1 does `exit(-1)` (255) whenever a mutant survived, after writing a complete
    # junit report; orcweather's first Dart run was called "exited 255" beside a 662-mutant report
    # (BACKLOG #71). The report decides; the exit code speaks only when there is no report.
    m = fake(Mutation(407, 662, []))
    m.mutation_cmd = lambda root, t, out: ["bash", "-c", "exit 255"]
    monkeypatch.setattr(langs, "ALL", [m])
    _code, out = run(["analyze"], make_repo(tmp_path), capsys)
    assert "TCE 61.5%" in out
    assert "exited 255" not in out


def test_analyze_no_report_and_a_high_exit_code_names_the_exit_code(tmp_path, capsys, monkeypatch):
    m = fake(Mutation(0, 0, []))
    m.mutation_cmd = lambda root, t, out: ["bash", "-c", "echo segfault-ish; exit 139"]
    monkeypatch.setattr(langs, "ALL", [m])
    _code, out = run(["analyze"], make_repo(tmp_path), capsys)
    assert "TCE not measurable — mutation tool exited 139" in out
    assert "segfault-ish" in out


def test_analyze_reports_land_beside_a_sub_project_marker(tmp_path, capsys, monkeypatch):
    # A sub-project's container mounts only its own directory (`.:${PWD}` in server/compose.yaml),
    # so a report path at the repository root is written inside the container and lost with it —
    # orcweather's PHP coverage "not measurable" while phpunit said "done" (BACKLOG #70). The
    # report dir is beside the marker; analyze.json stays at the root.
    repo = make_repo(tmp_path)
    (repo / "pyproject.toml").unlink()
    (repo / "tests" / "test_ok.py").unlink()
    sub = repo / "server"
    (sub / "tests").mkdir(parents=True)
    (sub / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    (sub / "tests" / "test_ok.py").write_text("def test_ok():\n    assert 1\n")
    seen = {}
    m = fake(Mutation(9, 10, []))
    m.coverage_cmd = lambda root, t, out: seen.setdefault("out", pathlib.Path(out)) and ["true"]
    monkeypatch.setattr(langs, "ALL", [m])
    run(["analyze"], repo, capsys)
    assert seen["out"] == sub / ".orclab" / "test" / "fake"
    assert (repo / ".orclab" / "test" / "analyze.json").exists()
    assert not (repo / ".orclab" / "test" / "fake").exists()
