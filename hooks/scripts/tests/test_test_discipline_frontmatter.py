# hooks/scripts/tests/test_test_discipline_frontmatter.py
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "test-discipline" / "SKILL.md"


def _frontmatter():
    text = SKILL.read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md must start with YAML frontmatter"
    return dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)


def test_is_background_only():
    fm = _frontmatter()
    assert fm["name"].strip() == "test-discipline"
    assert fm["user-invocable"].strip() == "false"
    assert "disable-model-invocation" not in fm


def test_six_rules_and_points_at_tdd():
    text = SKILL.read_text()
    for n in range(1, 7):
        assert re.search(rf"^## {n}\. ", text, re.M), f"rule {n} missing"
    assert "superpowers:test-driven-development" in text
    assert "/orc-test coverage" in text
