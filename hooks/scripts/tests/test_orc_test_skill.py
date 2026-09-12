import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills" / "orc-test" / "SKILL.md").read_text()


def test_frontmatter_is_default_invocable():
    fm = re.match(r"---\n(.*?)\n---\n", TEXT, re.S).group(1)
    assert "name: orc-test" in fm and "disable-model-invocation" not in fm
    assert "allowed-tools: Bash(python3 *)" in fm


def test_every_rule_the_spec_names_is_stated():
    for phrase in ["## generate", "analyze.json", "Nothing is deleted until", "Another round?",
                   "never starts a third round", "**offers**", "does not start it",
                   "test-discipline", "uncommitted", "## When something goes wrong",
                   "## Deferred", "ci"]:
        assert phrase in TEXT, phrase
