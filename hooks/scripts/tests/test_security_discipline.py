"""security-discipline (spec 2026-09-19-orclab-v22-security-discipline-design.md): the skill's
frontmatter and shape, and the Security section every stack skill carries (§2)."""

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "security-discipline" / "SKILL.md"
HEADING = "## Security — where security-discipline lands"
SUBHEADINGS = ["### Static analysis", "### Dependency audit", "### Secrets", "### Reachable by strangers"]
EXPECTED = {"stack-android-native", "stack-ios-native", "stack-kotlin-multiplatform", "stack-python-desktop", "stack-web"}   # each stack task adds its skill's directory name here


def _frontmatter():
    m = re.match(r"---\n(.*?)\n---\n", SKILL.read_text(), re.DOTALL)
    assert m, "SKILL.md must start with YAML frontmatter"
    return dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)


def test_is_background_only():
    fm = _frontmatter()
    assert fm["name"].strip() == "security-discipline"
    assert fm["user-invocable"].strip() == "false"
    assert "disable-model-invocation" not in fm


def test_two_tiers_named_and_every_rule_tagged():
    text = SKILL.read_text()
    rules = re.findall(r"^## (\d+)\. .*$", text, re.MULTILINE)
    assert 1 <= len(rules) <= 9, "single digits (spec §1)"
    assert [int(n) for n in rules] == list(range(1, len(rules) + 1))
    for n in rules:
        body = text.split(f"## {n}. ")[1].split("\n## ")[0]
        assert "*Every project*" in body or "*Reachable by strangers*" in body, f"rule {n} has no tier tag"
    assert "**Every project**" in text and "**Reachable by strangers**" in text


def test_every_rule_names_its_source():
    text = SKILL.read_text()
    assert "## Sources" in text
    assert re.search(r"confirmed live 2026-\d\d-\d\d", text)
    assert "owasp.org" in text and "cwe.mitre.org" in text


def test_what_this_is_not_points_at_secret_hygiene_and_the_stack_sections():
    text = SKILL.read_text()
    tail = text[text.index("## What this is not"):]
    for phrase in ["secret-hygiene", "penetration", "Not enforced by this file", HEADING, "lint_on_write", "/orc-test audit"]:
        assert phrase in tail, phrase


@pytest.mark.parametrize("stack", sorted(EXPECTED))
def test_stack_skill_has_the_security_section(stack):
    text = (ROOT / "skills" / stack / "SKILL.md").read_text()
    assert HEADING in text, stack
    body = text[text.index(HEADING):]
    body = body.split("\n## ", 1)[0]
    for sub in SUBHEADINGS:
        assert sub in body, f"{stack}: {sub}"
    assert "no project has been through this yet" in body, stack
    assert re.search(r"confirmed live 2026-\d\d-\d\d", body), stack


@pytest.mark.xfail(strict=True, reason="until Task 8 lands the ninth stack section; Task 8 removes this marker")
def test_every_stack_skill_is_expected():
    """A stack skill added later must be listed here, so it cannot ship without the section."""
    stacks = {p.parent.name for p in (ROOT / "skills").glob("stack-*/SKILL.md")}
    assert stacks == EXPECTED
