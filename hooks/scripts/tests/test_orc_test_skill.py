import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills" / "orc-test" / "SKILL.md").read_text()


def test_frontmatter_is_default_invocable():
    fm = re.match(r"---\n(.*?)\n---\n", TEXT, re.DOTALL).group(1)
    assert "name: orc-test" in fm and "disable-model-invocation" not in fm
    assert "allowed-tools: Bash(python3 *)" in fm


def test_every_rule_the_spec_names_is_stated():
    for phrase in ["## generate", "analyze.json", "Nothing is deleted until", "Another round?",
                   "never starts a third round", "**offers**", "does not start it",
                   "test-discipline", "uncommitted", "## When something goes wrong",
                   "## Deferred", "`ci`", "characterization tests"]:
        assert phrase in TEXT, phrase


def test_containers_section_names_the_record_the_override_and_the_engine():
    s = TEXT[TEXT.index("## Containers"):]
    s = s[:s.index("\n## ", 1)]
    for phrase in ["compose.yaml", "`orclab`", "container: false", "runner:", "docker", "podman",
                   "confirmed live 2026-", "(in container)", "container runner not found",
                   "container build failed", "never the host"]:
        assert phrase in s, phrase
    never = TEXT[TEXT.index("## What it never does"):TEXT.index("## `run`")]
    assert "engine" in never


def test_a_missing_tool_is_an_offer_not_homework():
    """direflail, 2026-09-27: "i do want orclab to ask to install modules it needs to do its work".

    The script still installs nothing; what changed is that Claude offers. Pinned here because
    the old text said only that it "names the missing one and its install line".
    """
    text = " ".join((ROOT / "skills" / "orc-test" / "SKILL.md").read_text().split())
    for phrase in ["When a tool is missing, offer to install it",
                   "Ask once, for everything missing",
                   "Show the command the script printed, unedited",
                   "If they decline, stop asking",
                   "re-run the gate",
                   "Inside a container, do not offer"]:
        assert phrase in text, phrase
    assert "EXTERNALLY-MANAGED" in text, "say why the plain pip command is not offered"
