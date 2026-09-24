import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills" / "orc-help" / "SKILL.md").read_text()


def test_step_4_shows_a_command_page_and_the_synopsis_points_at_it():
    for phrase in ["## Step 4", "docs/commands/", "for any command, /orc-help <name>",
                   "There is no `/orc-", "with or without"]:
        assert phrase in TEXT, phrase


def test_step_2_defers_to_the_one_discovery_procedure():
    """Step 2 used to restate the search roots inline and drifted from /orc-code's copy,
    missing the root a cloud session loads from. One list, in one place."""
    step2 = TEXT[TEXT.index("## Step 2"):TEXT.index("## Step 3")]
    assert "Plugin-Discovery Procedure" in step2
    for stale in ["~/.claude/plugins/marketplaces/", "~/.claude/plugins/cache/"]:
        assert stale not in step2, f"{stale} is restated here; it belongs only in orc-code"
