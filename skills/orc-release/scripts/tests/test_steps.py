import textwrap

from orc_release.steps import Step, doc_hash, parse_steps


DOC_PLAIN = textwrap.dedent(
    """
    # Cutting a release

    Some preamble that is not a step.

    ## 1. Pick a version

    Edit the version files.

    ## 2. Full test suite

    Run: `pytest tests/ -q`

    Must be fully green.
    """
)


def test_parses_numbered_steps_in_order():
    steps = parse_steps(DOC_PLAIN)
    assert [(s.number, s.title) for s in steps] == [
        (1, "Pick a version"),
        (2, "Full test suite"),
    ]


def test_preamble_before_the_first_step_is_not_a_step():
    steps = parse_steps(DOC_PLAIN)
    assert all("preamble" not in s.body for s in steps)


def test_step_body_captures_everything_up_to_the_next_step():
    steps = parse_steps(DOC_PLAIN)
    assert "pytest tests/ -q" in steps[1].body
    assert "Must be fully green" in steps[1].body
    assert "Pick a version" not in steps[1].body


def test_a_document_using_none_of_the_conventions_still_parses():
    steps = parse_steps(DOC_PLAIN)
    for s in steps:
        assert s.preconditions == []
        assert s.is_manual is False
        assert s.delegates_to is None
        assert s.is_irreversible is False


def test_preconditions_are_extracted():
    steps = parse_steps(
        textwrap.dedent(
            """
            ## 6. Upload to the PPA

            **Preconditions:** this version is not already published; gpg-agent is unlocked.

            Run: `dput ...`
            """
        )
    )
    assert steps[0].preconditions == [
        "this version is not already published; gpg-agent is unlocked."
    ]


def test_performed_by_hand_is_detected():
    steps = parse_steps(
        textwrap.dedent(
            """
            ## 7. Install-test on every target

            **Performed by hand.** Copy the .deb to each VM and launch it.
            """
        )
    )
    assert steps[0].is_manual is True


def test_delegation_is_extracted():
    steps = parse_steps(
        textwrap.dedent(
            """
            ## 6. Publish to every channel

            **Run:** /orc-publish
            """
        )
    )
    assert steps[0].delegates_to == "/orc-publish"


def test_irreversible_is_detected():
    steps = parse_steps(
        textwrap.dedent(
            """
            ## 6. Upload to the PPA

            **Irreversible.** Once uploaded, the version number is consumed.
            """
        )
    )
    assert steps[0].is_irreversible is True


def test_markers_are_case_insensitive_and_survive_surrounding_prose():
    steps = parse_steps(
        textwrap.dedent(
            """
            ## 3. Ship it

            Some prose first.

            **performed by hand.** do the thing

            **irreversible.**
            """
        )
    )
    assert steps[0].is_manual is True
    assert steps[0].is_irreversible is True


def test_non_step_headings_are_ignored():
    steps = parse_steps(
        textwrap.dedent(
            """
            ## Overview

            Not a step.

            ## 1. Real step

            Body.

            ## Appendix

            Also not a step.
            """
        )
    )
    assert [s.number for s in steps] == [1]


def test_doc_hash_is_stable_and_changes_with_content():
    assert doc_hash("abc") == doc_hash("abc")
    assert doc_hash("abc") != doc_hash("abd")


def test_step_is_a_plain_dataclass_with_expected_fields():
    s = Step(number=1, title="x", body="y")
    assert s.preconditions == []
    assert s.is_manual is False
    assert s.delegates_to is None
    assert s.is_irreversible is False


def test_multiline_preconditions_are_captured_fully():
    """Preconditions that wrap to multiple lines are captured in full, not truncated."""
    steps = parse_steps(
        textwrap.dedent(
            """
            ## 6. Upload to the PPA

            **Preconditions:** this version is not already published; gpg-agent is
            unlocked and the signing key is loaded.

            Run: `dput ...`
            """
        )
    )
    assert steps[0].preconditions == [
        "this version is not already published; gpg-agent is unlocked and the signing key is loaded."
    ]


def test_fenced_block_containing_heading_marker_does_not_end_step():
    """A ## line inside a fenced code block does not falsely end the step body."""
    steps = parse_steps(
        textwrap.dedent(
            """
            ## 2. Run a command

            Here's how to run it:

            ```
            ## this looks like a heading but is inside a fence
            still code
            ```

            More prose after the fence.
            """
        )
    )
    assert len(steps) == 1
    assert "More prose after the fence" in steps[0].body
    assert "still code" in steps[0].body
