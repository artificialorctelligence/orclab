"""v23: every stack skill says whether it runs in a container (spec §3)."""

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
HEADING = "## Containers"
EXPECTED = {"stack-python-desktop", "stack-web"}   # each stack task adds its skill's directory name here


@pytest.mark.parametrize("stack", sorted(EXPECTED))
def test_stack_skill_has_the_containers_section(stack):
    text = (ROOT / "skills" / stack / "SKILL.md").read_text()
    assert HEADING in text, stack
    body = text[text.index(HEADING):].split("\n## ", 1)[0]
    assert re.search(r"Runs in a container: \*\*(yes|no)\*\*", body), stack
    assert re.search(r"confirmed live 2026-\d\d-\d\d", body), stack
    if "**yes**" in body:
        assert "```dockerfile" in body and "FROM " in body, stack
    assert "container question" in body, stack


@pytest.mark.xfail(strict=True, reason="until Task 7 lands the ninth section; Task 7 removes this marker")
def test_every_stack_skill_is_expected():
    stacks = {p.parent.name for p in (ROOT / "skills").glob("stack-*/SKILL.md")}
    assert stacks == EXPECTED
