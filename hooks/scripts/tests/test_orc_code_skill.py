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
