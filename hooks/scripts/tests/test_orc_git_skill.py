"""The v21 gate (spec 2026-09-15-orclab-v21-push-gate-design.md): /orc-git runs /orc-test
before anything reaches GitHub. These pin the sentences in the skill Claude follows and the
page a user reads, so an edit that drops the gate fails here rather than in front of a user."""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = (ROOT / "skills" / "orc-git" / "SKILL.md").read_text()
PAGE = (ROOT / "docs" / "commands" / "orc-git.md").read_text()

RUN_PY = 'python3 "${CLAUDE_PLUGIN_ROOT}/skills/orc-test/scripts/run.py"'


def section(text, heading):
    """The body of one `## heading` up to the next `## `."""
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    assert m, heading
    return m.group(1)


def test_push_runs_coverage_after_the_nothing_to_push_check_and_before_the_push():
    body = section(SKILL, "push")
    gate_cmd = f'{RUN_PY} --cwd <repo root> coverage'
    assert gate_cmd in body
    gate = body.index(gate_cmd)
    assert body.index("nothing to push") < gate < body.index("git push -u origin")
    for phrase in ["exits non-zero", "nothing is pushed", "not measurable", "git status --porcelain",
                   "does not start `/orc-test generate`"]:
        assert phrase in body, phrase


def test_cp_says_the_gate_belongs_to_the_push_half():
    body = section(SKILL, "commit-push [text] / cp [text]")
    assert "committed" in body and "not pushed" in body
    assert "coverage" in body


def test_release_runs_analyze_after_the_tag_check_and_before_the_pushes():
    body = section(SKILL, "release [tag]")
    gate_cmd = f'{RUN_PY} --cwd <repo root> analyze'
    assert gate_cmd in body
    gate = body.index(gate_cmd)
    assert body.index("Confirm the tag exists locally") < gate < body.index("git push origin HEAD")
    assert "TCE" in body and "minutes" in body


def test_merge_still_runs_run_not_coverage():
    body = section(SKILL, "merge <branch>")
    assert f"{RUN_PY} --cwd <path to the branch's tree> run" in body
    assert " coverage" not in body


def test_the_bare_listing_names_the_gate_on_push_and_release():
    listing = section(SKILL, "Bare invocation (no arguments)")
    assert "push the current branch, after /orc-test coverage and audit pass" in listing
    assert "after /orc-test analyze and audit pass" in listing


def test_the_family_table_names_the_dependency_on_orc_test():
    body = section(SKILL, "Two families under one name")
    assert "/orc-test" in body and "Orclab's own" in body


def test_no_subcommand_offers_a_way_to_skip_the_gate():
    for flag in ["--no-test", "--skip-test", "--no-gate", "--force-push"]:
        assert flag not in SKILL, flag


def test_the_page_says_when_the_tests_run_and_what_stops_a_push():
    typed = section(PAGE, "What you type")
    assert "test" in typed.split("`/orc-git push`")[1].split("\n")[0].lower()
    assert "test" in typed.split("`/orc-git release [tag]`")[1].split("\n")[0].lower()
    changes = section(PAGE, "What it changes")
    assert "80%" in changes and "coverage" in changes
    assert "70%" in changes and "mutation" in changes and "minutes" in changes
    never = section(PAGE, "What it will never do without asking")
    assert "under 80%" in never and "under 70%" in never
    assert "never writes tests on its own" in never
    assert "can't measure" in never or "cannot measure" in never


def test_push_runs_audit_beside_coverage_and_a_vulnerable_dependency_stops_it():
    body = section(SKILL, "push")
    audit_cmd = f'{RUN_PY} --cwd <repo root> audit'
    assert audit_cmd in body
    assert body.index("nothing to push") < body.index(audit_cmd) < body.index("git push -u origin")
    for phrase in ["vulnerable", "not available", "nothing is pushed"]:
        assert phrase in body, phrase


def test_release_runs_audit_too():
    body = section(SKILL, "release [tag]")
    assert f'{RUN_PY} --cwd <repo root> audit' in body


def test_listing_and_page_name_the_audit():
    listing = section(SKILL, "Bare invocation (no arguments)")
    assert "after /orc-test coverage and audit pass" in listing
    changes = section(PAGE, "What it changes")
    assert "known vulnerabilit" in changes
    never = section(PAGE, "What it will never do without asking")
    assert "known vulnerabilit" in never
