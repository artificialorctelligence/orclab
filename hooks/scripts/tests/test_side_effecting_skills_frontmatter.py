import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]

SIDE_EFFECTING_SKILLS = ["orc-publish", "orc-release", "orc-package"]


def _frontmatter(name):
    text = (ROOT / "skills" / name / "SKILL.md").read_text()
    return re.match(r"---\n(.*?)\n---\n", text, re.DOTALL).group(1)


def test_side_effecting_skills_disable_model_invocation():
    for name in SIDE_EFFECTING_SKILLS:
        fm = _frontmatter(name)
        assert "disable-model-invocation: true" in fm, name
