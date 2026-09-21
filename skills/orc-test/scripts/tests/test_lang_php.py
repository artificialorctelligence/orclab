import json
import pathlib

from orc_test import probe
from orc_test.langs import php
from orc_test.model import Coverage, Mutation

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_markers_and_source_ext():
    assert php.MARKERS == ["composer.json"]
    assert php.SOURCE_EXT == ".php"


def test_missing_wants_composer(tmp_path, monkeypatch):
    (tmp_path / "composer.json").write_text('{"require-dev": {"phpunit/phpunit": "^12"}}')
    monkeypatch.setattr(probe, "which", lambda n: False)
    assert php.missing(tmp_path) == ["composer"]
    monkeypatch.setattr(probe, "which", lambda n: True)
    assert php.missing(tmp_path) == []


def test_test_and_coverage_cmds(tmp_path):
    out = tmp_path / "out"
    assert php.test_cmd(tmp_path, None) == ["vendor/bin/phpunit"]
    assert php.test_cmd(tmp_path, "tests/Unit") == ["vendor/bin/phpunit", "tests/Unit"]
    cmd = php.coverage_cmd(tmp_path, None, out)
    assert cmd[:2] == ["vendor/bin/phpunit", "--coverage-clover"] and cmd[2] == str(out / "clover.xml")
    assert "--coverage-html" in cmd


def test_coverage_parse_reads_clover(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "clover.xml").write_bytes((FIX / "clover.xml").read_bytes())
    cov = php.coverage_parse(tmp_path, out)
    assert cov.total > 0 and cov.covered <= cov.total
    assert any(p.endswith("Greeting.php") for p in cov.files)


def test_coverage_parse_no_report(tmp_path):
    assert php.coverage_parse(tmp_path, tmp_path) == Coverage(0, 0)


def test_mutation_needs_infection_in_require_dev(tmp_path):
    (tmp_path / "composer.json").write_text('{"require-dev": {}}')
    assert "infection/infection" in php.mutation_unavailable(tmp_path)
    (tmp_path / "composer.json").write_text('{"require-dev": {"infection/infection": "^0.30"}}')
    (tmp_path / "infection.json5").write_text(json.dumps({"logs": {"json": "out/infection.json"}}))
    assert php.mutation_unavailable(tmp_path) is None


def test_mutation_needs_logs_json_key(tmp_path):
    # infection.json5 exists and infection/infection is required, but the config has no
    # logs.json key: mutation_cmd passes no logger flag (Infection has none), so a full run
    # would end in Mutation(0, 0) and cli.py would blame "produced no mutants" instead of the
    # real cause — this must be caught before the run, not diagnosed after it.
    (tmp_path / "composer.json").write_text('{"require-dev": {"infection/infection": "^0.30"}}')
    (tmp_path / "infection.json5").write_text(json.dumps({"source": {"directories": ["src"]}}))
    reason = php.mutation_unavailable(tmp_path)
    assert reason is not None and "logs.json" in reason
    (tmp_path / "infection.json5").write_text(json.dumps({"logs": {"json": "x.json"}}))
    assert php.mutation_unavailable(tmp_path) is None


def test_mutation_cmd_has_no_logger_json_option_and_uses_with_uncovered(tmp_path):
    # Corrections to the brief (Task 2, live): Infection has no --logger-json; --with-uncovered
    # is what makes an untested file count against the score instead of vanishing from it.
    out = tmp_path / "out"
    cmd = php.mutation_cmd(tmp_path, None, out)
    assert cmd == ["vendor/bin/infection", "--no-interaction", "--threads=max", "--with-uncovered"]
    assert "--no-progress" not in cmd    # the run is streamed; the progress line is wanted (BACKLOG #73)
    assert not any(c.startswith("--logger-json") for c in cmd)
    cmd = php.mutation_cmd(tmp_path, "src/Greeting.php", out)
    assert cmd[-1] == "--filter=src/Greeting.php"


def test_mutation_parse_reads_infection_log_named_by_json5(tmp_path):
    # The sample's real infection.json5: {"logs": {"json": ".orclab/test/php/infection.json"}}.
    out = tmp_path / "out"
    out.mkdir()
    log = tmp_path / ".orclab" / "test" / "php" / "infection.json"
    log.parent.mkdir(parents=True)
    log.write_bytes((FIX / "infection.json").read_bytes())
    (tmp_path / "infection.json5").write_text(
        json.dumps({"logs": {"json": ".orclab/test/php/infection.json"}}))
    data = json.loads((FIX / "infection.json").read_text())
    mut = php.mutation_parse(tmp_path, out)
    assert mut.total == data["stats"]["totalMutantsCount"]
    assert mut.killed == data["stats"]["killedCount"] + data["stats"]["timeOutCount"] + data["stats"]["errorCount"]
    # escaped + uncovered: --with-uncovered counts both as alive (see the dedicated test below)
    assert len(mut.survivors) == len(data["escaped"]) + len(data["uncovered"]) >= 1
    s = mut.survivors[0]
    assert s.file.endswith(".php") and s.line > 0 and s.description


def test_mutation_parse_survivors_include_uncovered_mutants(tmp_path):
    # --with-uncovered counts an uncovered mutant in the denominator too (mutation_cmd), so a
    # survivor list built from `escaped` alone would never tell `generate` that GreetAction.php
    # is untested. The log's `uncovered` array shares `escaped`'s mutator/diff shape
    # (infection.json.README); the siblings (stryker.py, pitest.py) both list these and tag them
    # " (no test reaches it)".
    out = tmp_path / "out"
    out.mkdir()
    (out / "infection.json").write_bytes((FIX / "infection.json").read_bytes())
    data = json.loads((FIX / "infection.json").read_text())
    mut = php.mutation_parse(tmp_path, out)
    assert len(mut.survivors) == len(data["escaped"]) + len(data["uncovered"]) == 9
    tagged = [s for s in mut.survivors if "no test reaches it" in s.description]
    assert tagged and any(s.file.endswith("GreetAction.php") for s in tagged)
    # the one escaped (covered but not killed) mutant is not tagged uncovered
    untagged = [s for s in mut.survivors if "no test reaches it" not in s.description]
    assert untagged and untagged[0].file.endswith("Greeting.php")


def test_mutation_parse_tolerates_json5_comments(tmp_path):
    # infection.json5 is JSON5 (comments, trailing commas allowed); a real project's file may
    # carry a // comment line even though the sample's own file (Task 2) happens to be plain JSON.
    out = tmp_path / "out"
    out.mkdir()
    (out / "infection.json").write_bytes((FIX / "infection.json").read_bytes())
    (tmp_path / "infection.json5").write_text(
        '{\n  // where the full log lands\n  "logs": {"json": "out/infection.json"}\n}')
    mut = php.mutation_parse(tmp_path, out)
    assert mut.total == 10


def test_mutation_parse_falls_back_on_json5_it_cannot_read(tmp_path):
    # Real JSON5 beyond the fallback (a /* block */ comment): mutation_parse must degrade to
    # <out>/infection.json, never raise.
    out = tmp_path / "out"
    out.mkdir()
    (out / "infection.json").write_bytes((FIX / "infection.json").read_bytes())
    (tmp_path / "infection.json5").write_text('{\n  /* the log */ "logs": {"json": "out/infection.json"}\n}')
    mut = php.mutation_parse(tmp_path, out)
    assert mut.total == 10


def test_mutation_parse_reads_trailing_comments_and_commas(tmp_path):
    # orcweather's server/infection.json5 (2026-09-20): a // comment at the END of a line, not on
    # its own. The whole-line-only stripper failed, fell back to <out>/infection.json, found
    # nothing, and analyze said "produced no mutants" beside a 407-mutant log (BACKLOG #72).
    # The comment text carries a comma, and the string a `//`, so the stripper must respect quotes.
    log = tmp_path / "elsewhere" / "infection.json"
    log.parent.mkdir()
    log.write_bytes((FIX / "infection.json").read_bytes())
    (tmp_path / "infection.json5").write_text(
        '{\n    "source": { "directories": ["src"], "excludes": ["Fetch.php"] }, // Fetch is the network edge, live-tested\n'
        '    "logs": { "json": "elsewhere/infection.json", "html": "http://x//y", },\n}')
    mut = php.mutation_parse(tmp_path, tmp_path / "out")
    assert mut.total == 10


def test_mutation_parse_falls_back_to_out_dir_without_json5(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "infection.json").write_bytes((FIX / "infection.json").read_bytes())
    mut = php.mutation_parse(tmp_path, out)
    assert mut.total == 10


def test_mutation_parse_no_report(tmp_path):
    assert php.mutation_parse(tmp_path, tmp_path) == Mutation(0, 0)


def test_audit_cmd_and_unavailable(tmp_path, monkeypatch):
    assert php.audit_cmd(tmp_path) == ["composer", "audit", "--format=json", "--locked"]
    monkeypatch.setattr(probe, "which", lambda n: False)
    assert php.audit_unavailable(tmp_path) == "composer not installed"


def test_audit_nothing_without_a_lock_file(tmp_path):
    assert "composer.lock" in php.audit_nothing(tmp_path)
    (tmp_path / "composer.lock").write_text("{}")
    assert php.audit_nothing(tmp_path) is None


def test_audit_findings_names_each_advisory():
    text = (FIX / "composer_audit.json").read_text()
    lines = php.audit_findings(text, 1)
    assert lines and all(": " in l for l in lines)
    assert any("guzzlehttp/guzzle" in l for l in lines)   # the package the README names


def test_audit_findings_clean():
    # composer_audit_clean.json's `advisories` is a list ([]), not a dict — PHP's json_encode
    # turns an empty associative array into [], while a finding-bearing capture keys it by
    # package name (composer_audit.json.README). Both shapes must be handled.
    text = (FIX / "composer_audit_clean.json").read_text()
    assert php.audit_findings(text, 0) == []


def test_audit_findings_unreadable():
    assert php.audit_findings("not json", 1) == ["audit output not understood — see above"]


def test_lint_says_no_tool(tmp_path):
    assert isinstance(php.lint(tmp_path, None, tmp_path), str)
