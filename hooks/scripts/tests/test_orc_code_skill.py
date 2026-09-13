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


def test_migration_mode_adds_stack_tests_worktree_and_gate():
    m = TEXT[TEXT.index("### Migration mode"):TEXT.index("## Plugin-Discovery Procedure")]
    assert "Run once for real on 2026-09-13" in m and "see BACKLOG #41" in m
    for phrase in ["Defaults Table", "stack-*", "[target-stack]",
                   "characterization", "/orc-test analyze", "/orc-test generate",
                   "before any `modernize-", "legacy/", "analysis/", "modernized/",
                   "worktree", "/orc-test run", "no lower than", "modernize-status",
                   "modernize-preflight"]:
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
