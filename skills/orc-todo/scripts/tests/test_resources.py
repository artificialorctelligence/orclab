from orc_todo.resources import RESOURCES, has_foreign_numbered_headings, insert, render, scan_max

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


def test_insert_is_exact_about_the_seam_and_keeps_the_bodys_own_trailing_spaces():
    text = "# V\n\n## Scenario 1: a\n\nsteps\n\n\n## Recording the result\n\nnote it.\n"
    out = insert(text, VERIFICATION, "## Scenario 2: b\n\nsteps  \n\n\n")
    assert out == ("# V\n\n## Scenario 1: a\n\nsteps\n\n## Scenario 2: b\n\nsteps  \n\n"
                   "## Recording the result\n\nnote it.\n")


def test_insert_goes_before_the_first_anchor_when_the_heading_repeats():
    text = "# V\n\n## Recording the result\n\nfirst\n\n## Recording the result\n\nsecond\n"
    out = insert(text, VERIFICATION, "## Scenario 1: a\n\nsteps\n")
    assert out.startswith("# V\n\n## Scenario 1: a\n\nsteps\n\n## Recording the result\n\nfirst\n")


def test_foreign_numbered_headings_spots_another_projects_format():
    assert has_foreign_numbered_headings("## Open\n\n### 17. a finding\n")
    assert has_foreign_numbered_headings("## 3) a finding\n")


def test_foreign_numbered_headings_ignores_prose_headings_and_fenced_examples():
    assert not has_foreign_numbered_headings("# Backlog\n\n## Open\n\n## Resolved\n")
    assert not has_foreign_numbered_headings("prose\n\n```\n### 1. an example\n```\n")


def test_heading_re_still_counts_an_entry_whose_title_is_empty():
    """The pattern grew a title group on 2026-09-26 so cli could stop keeping its own copy.
    Requiring a space after the colon would have dropped `## #22:` from the scan, and a
    heading the scan cannot see is a number the allocator hands out twice."""
    assert scan_max("## #22:\n\nprose\n", BACKLOG) == 22


def test_heading_re_captures_the_title_for_the_cli():
    import re
    from orc_todo.resources import RESOURCES
    m = re.search(RESOURCES["backlog"].heading_re, "## #7: a real title\n", re.MULTILINE)
    assert (int(m.group(1)), m.group(2).strip()) == (7, "a real title")
