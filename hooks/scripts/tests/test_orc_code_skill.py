import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills" / "orc-code" / "SKILL.md").read_text()


def test_frontmatter_still_routes_refactor():
    fm = re.match(r"---\n(.*?)\n---\n", TEXT, re.DOTALL).group(1)
    assert "name: orc-code" in fm
    assert "refactor/migrate existing code" in fm
    assert "argument-hint: [refactor]" in fm


def test_refactor_flow_has_two_modes_and_asks_when_unsure():
    for phrase in ["### Which mode", "### Quality mode", "### Migration mode",
                   "changes neither the language nor its version",
                   "names a different language, framework or version",
                   "ask — one question", "Never guess"]:
        assert phrase in TEXT, phrase
    # the modes are introduced before either is described
    assert TEXT.index("### Which mode") < TEXT.index("### Quality mode") < TEXT.index("### Migration mode")


def test_quality_mode_is_the_dogfood_procedure_in_order():
    q = TEXT[TEXT.index("### Quality mode"):TEXT.index("### Migration mode")]
    for phrase in ["## Lint — where code-discipline lands", "a project's own settings win",
                   "/orc-test analyze", "before", "safe", "never `--unsafe-fixes`",
                   "one function at a time", "suite green after every file",
                   "/orc-test generate", "before → after", "Another round?"]:
        assert phrase in q, phrase
    for refused in ["`--unsafe-fixes`", "`ignore`"]:
        assert refused in q
    # order: config, baseline, autofix, by hand, generate, report
    marks = [q.index(p) for p in ("## Lint", "Baseline", "safe autofixes", "one function at a time",
                                   "/orc-test generate", "before → after")]
    assert marks == sorted(marks)


def test_quality_mode_keeps_what_the_orcshot_run_bought():
    q = TEXT[TEXT.index("### Quality mode"):TEXT.index("### Migration mode")]
    for phrase in ["0. **The checkout can run its own suite.**", "venv `bin` first on `PATH`",
                   "[tool.mutmut]", "For a file the suite never imports",
                   "a green suite proves nothing about the change",
                   "fixed by hand first", "When something goes wrong"]:
        assert phrase in q, phrase
    assert q.index("The checkout can run its own suite") < q.index("## Lint")


def test_migration_mode_adds_stack_tests_worktree_and_gate():
    m = TEXT[TEXT.index("### Migration mode"):TEXT.index("## Plugin-Discovery Procedure")]
    assert "Run once for real on 2026-09-13" in m and "see BACKLOG #41" in m
    for phrase in ["Defaults Table", "stack-*", "[target-stack]",
                   "characterization", "/orc-test analyze", "/orc-test generate",
                   "before any `modernize-", "legacy/", "analysis/", "modernized/",
                   "worktree", "/orc-test run", "no lower than", "modernize-status",
                   "modernize-preflight",
                   # the plugin sequence the first run learned: brief needs three inputs, and
                   # uplift's delta catalog comes before brief
                   "`brief` reads", "are not optional between `assess` and `brief`",
                   "`extract-rules`, `uplift` Step 3 (delta catalog), `brief`, `uplift`",
                   "fixed by hand first"]:
        assert phrase in m, phrase


def test_discovery_tells_available_from_installed():
    d = TEXT[TEXT.index("## Plugin-Discovery Procedure"):TEXT.index("## Defaults Table")]
    for phrase in ["installed_plugins.json", "available, not installed",
                   "claude plugin install code-modernization@claude-plugins-official",
                   "fresh session"]:
        assert phrase in d, phrase


def test_code_discipline_names_the_quality_mode():
    cd = (ROOT / "skills" / "code-discipline" / "SKILL.md").read_text()
    assert "`/orc-code refactor`'s quality mode" in cd


def test_new_project_flow_asks_exposure_after_platforms_and_before_starting_point():
    flow = TEXT[TEXT.index("## New-Project Flow"):TEXT.index("## Add-to-Existing Flow")]
    q = "Will anyone you didn't invite be able to reach this?"
    assert q in flow
    assert flow.index("Which platforms?") < flow.index(q) < flow.index("minimal example")
    for phrase in ["I'll assume yes", "I'll assume no", "security-discipline", "not recorded"]:
        assert phrase in flow, phrase


def test_scaffold_writes_the_security_config_and_the_exposed_tier_pieces():
    flow = TEXT[TEXT.index("## New-Project Flow"):TEXT.index("## Add-to-Existing Flow")]
    scaffold = flow[flow.index("**Scaffold**"):flow.index("**Verify**")]
    for phrase in ["## Security — where security-discipline lands", "### Reachable by strangers"]:
        assert phrase in scaffold, phrase


def test_quality_mode_writes_security_config_and_wraps_modernize_harden():
    q = TEXT[TEXT.index("### Quality mode"):TEXT.index("### Migration mode")]
    assert "## Security — where security-discipline lands" in q
    assert "modernize-harden" in q and "Plugin-Discovery Procedure" in q
    assert q.index("one function at a time") < q.index("modernize-harden") < q.index("/orc-test generate")
    assert "isn't currently installed" in q or "not installed" in q


def test_test_discipline_names_the_hostile_scenario():
    td = (ROOT / "skills" / "test-discipline" / "SKILL.md").read_text()
    r1 = td[td.index("## 1. "):td.index("## 2. ")]
    assert "trust boundary" in r1 and "unauthenticated" in r1


def test_new_project_flow_asks_container_after_exposure_and_before_starting_point():
    flow = TEXT[TEXT.index("## New-Project Flow"):TEXT.index("## Add-to-Existing Flow")]
    q = "Run this project's toolchain in a container, so nothing has to be installed on this machine?"
    assert q in flow
    assert flow.index("didn't invite") < flow.index(q) < flow.index("minimal example")
    for phrase in ["compose.yaml", "`orclab`", "Dockerfile", "## Containers", "skips the container question",
                   "not what ships", "Once all six are answered"]:
        assert phrase in flow, phrase


def test_scaffold_and_verify_run_through_the_container():
    flow = TEXT[TEXT.index("## New-Project Flow"):TEXT.index("## Add-to-Existing Flow")]
    scaffold = flow[flow.index("**Scaffold**"):flow.index("**Verify**")]
    verify = flow[flow.index("**Verify**"):flow.index("**Report**")]
    assert "Dockerfile" in scaffold and "compose.yaml" in scaffold
    assert "compose run" in verify or "through the container" in verify
