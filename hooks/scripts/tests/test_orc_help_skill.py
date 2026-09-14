import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
TEXT = (ROOT / "skills" / "orc-help" / "SKILL.md").read_text()


def test_step_4_shows_a_command_page_and_the_synopsis_points_at_it():
    for phrase in ["## Step 4", "docs/commands/", "for any command, /orc-help <name>",
                   "There is no `/orc-", "with or without"]:
        assert phrase in TEXT, phrase
