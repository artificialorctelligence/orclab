from orc_todo.resources import RESOURCES, insert, render, scan_max

BACKLOG = RESOURCES["backlog"]
VERIFICATION = RESOURCES["verification"]


def test_scan_max_finds_the_highest_backlog_number_not_the_last():
    """Entries are not necessarily in order, and gaps are expected and correct - a deleted
    entry's number is never reused."""
    text = "# Backlog\n\n## #7: a thing\n\nprose\n\n## #22: another\n\nprose\n\n## #9: third\n"
    assert scan_max(text, BACKLOG) == 22


def test_scan_max_finds_the_highest_scenario_number():
    text = "# V\n\n## Scenario 3: a\n\n## Scenario 45: b\n\n## Recording the result\n"
    assert scan_max(text, VERIFICATION) == 45


def test_scan_max_is_zero_on_a_file_with_no_entries():
    assert scan_max("# Backlog\n\nheader prose only\n", BACKLOG) == 0


def test_scan_max_ignores_a_number_inside_prose():
    """"see #40 above" in an entry body must not become the high-water mark."""
    text = "## #7: a thing\n\nrelated to #40 and #99, neither of which is a heading\n"
    assert scan_max(text, BACKLOG) == 7


def test_scan_max_ignores_a_resolved_suffix():
    text = "## #12: a thing (RESOLVED 2026-09-07)\n\nprose\n"
    assert scan_max(text, BACKLOG) == 12


def test_render_produces_the_house_heading_for_each_file():
    assert render(BACKLOG, 26, "a title", "body prose").startswith("## #26: a title\n")
    assert render(VERIFICATION, 46, "a title", "1. step").startswith("## Scenario 46: a title\n")


def test_render_separates_heading_from_body_with_a_blank_line():
    out = render(BACKLOG, 26, "t", "body prose")
    assert out == "## #26: t\n\nbody prose\n"


def test_insert_appends_a_backlog_entry_at_the_end():
    text = "# Backlog\n\n## #1: first\n\nprose\n"
    out = insert(text, BACKLOG, "## #2: second\n\nmore\n")
    assert out.endswith("## #2: second\n\nmore\n")
    assert "## #1: first" in out


def test_insert_puts_a_scenario_before_the_recording_section_not_at_the_end():
    """VERIFICATION.md ends with '## Recording the result'. Appending would put a new scenario
    after the closing section, where nobody running the script would reach it."""
    text = "# V\n\n## Scenario 1: a\n\nsteps\n\n## Recording the result\n\nnote it.\n"
    out = insert(text, VERIFICATION, "## Scenario 2: b\n\nsteps\n")
    assert out.index("## Scenario 2: b") < out.index("## Recording the result")
    assert out.endswith("note it.\n")


def test_insert_falls_back_to_appending_when_the_anchor_is_missing():
    text = "# V\n\n## Scenario 1: a\n\nsteps\n"
    out = insert(text, VERIFICATION, "## Scenario 2: b\n\nsteps\n")
    assert out.endswith("## Scenario 2: b\n\nsteps\n")


def test_insert_leaves_exactly_one_blank_line_between_sections():
    text = "# Backlog\n\n## #1: first\n\nprose\n"
    out = insert(text, BACKLOG, "## #2: second\n\nmore\n")
    assert "prose\n\n## #2: second" in out
    assert "prose\n\n\n" not in out


def test_scan_max_ignores_a_heading_quoted_in_a_fenced_example():
    # A phantom high-water mark never reissues a number - it silently skips to 100.
    text = "## #7: real\n\n```\n## #99: an example of the format\n```\n"
    assert scan_max(text, BACKLOG) == 7
