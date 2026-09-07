import json

import pytest

from orc_release.state import (
    STATE_PATH,
    clear_state,
    completed_numbers,
    irreversible_completed,
    is_in_progress,
    load_state,
    mark_complete,
    mark_skipped,
    next_step_number,
    save_state,
    start_release,
)


def test_no_state_means_not_in_progress(tmp_path):
    assert is_in_progress(str(tmp_path)) is False
    assert load_state(str(tmp_path)) is None


def test_start_release_writes_state_that_loads_back(tmp_path):
    start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc123")
    assert is_in_progress(str(tmp_path)) is True
    state = load_state(str(tmp_path))
    assert state["version"] == "0.3.0"
    assert state["previous_version"] == "0.2.0"
    assert state["doc_path"] == "RELEASING.md"
    assert state["doc_hash"] == "abc123"
    assert state["completed"] == []
    assert state["skipped"] == []
    assert state["started_at"]


def test_state_lands_at_the_documented_path(tmp_path):
    start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    assert (tmp_path / STATE_PATH).exists()
    assert STATE_PATH == ".orclab/release/state.json"


def test_mark_complete_records_number_and_title(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_complete(state, 1, "Pick a version")
    save_state(str(tmp_path), state)
    reloaded = load_state(str(tmp_path))
    assert reloaded["completed"] == [
        {"number": 1, "title": "Pick a version", "irreversible": False}
    ]


def test_mark_complete_records_irreversibility(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_complete(state, 6, "Upload to the PPA", irreversible=True)
    assert irreversible_completed(state) == [
        {"number": 6, "title": "Upload to the PPA", "irreversible": True}
    ]


def test_mark_complete_is_idempotent_for_the_same_step(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_complete(state, 1, "Pick a version")
    state = mark_complete(state, 1, "Pick a version")
    assert completed_numbers(state) == [1]


def test_mark_skipped_requires_and_records_a_reason(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_skipped(state, 3, "Security check", "semgrep not set up on this machine")
    assert state["skipped"] == [
        {
            "number": 3,
            "title": "Security check",
            "reason": "semgrep not set up on this machine",
        }
    ]


def test_mark_skipped_rejects_an_empty_reason(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    with pytest.raises(ValueError, match="reason"):
        mark_skipped(state, 3, "Security check", "   ")


def test_a_skipped_step_counts_as_passed_for_advancing(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_skipped(state, 1, "Pick a version", "already done by hand")
    assert completed_numbers(state) == [1]


def test_next_step_number_returns_the_first_unfinished_step(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_complete(state, 1, "One")
    state = mark_complete(state, 2, "Two")
    assert next_step_number(state, [1, 2, 3, 4]) == 3


def test_next_step_number_is_none_when_everything_is_done(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    for n in (1, 2, 3):
        state = mark_complete(state, n, f"Step {n}")
    assert next_step_number(state, [1, 2, 3]) is None


def test_clear_state_removes_it(tmp_path):
    start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    clear_state(str(tmp_path))
    assert is_in_progress(str(tmp_path)) is False


def test_clear_state_on_absent_state_is_not_an_error(tmp_path):
    clear_state(str(tmp_path))


def test_state_file_is_valid_readable_json(tmp_path):
    start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    json.loads((tmp_path / STATE_PATH).read_text())


def test_skip_then_complete_raises_and_leaves_state_unchanged(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_skipped(state, 6, "Upload to the PPA", "thought it wasn't needed yet")
    original_state = json.dumps(state, sort_keys=True)
    with pytest.raises(ValueError, match="6"):
        mark_complete(state, 6, "Upload to the PPA", irreversible=True)
    assert json.dumps(state, sort_keys=True) == original_state
    assert irreversible_completed(state) == []


def test_complete_then_skip_raises_and_leaves_state_unchanged(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_complete(state, 1, "Step one")
    original_state = json.dumps(state, sort_keys=True)
    with pytest.raises(ValueError, match="1"):
        mark_skipped(state, 1, "Step one", "skipped after complete")
    assert json.dumps(state, sort_keys=True) == original_state


def test_complete_twice_is_still_idempotent_not_an_error(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_complete(state, 1, "Step one")
    # Second complete on same number should be a silent no-op, not a ValueError
    state = mark_complete(state, 1, "Step one")
    assert completed_numbers(state) == [1]
    assert len(state["completed"]) == 1


def test_irreversible_tracking_after_guard_is_correct(tmp_path):
    state = start_release(str(tmp_path), "0.3.0", "0.2.0", "RELEASING.md", "abc")
    state = mark_complete(state, 6, "Upload to the PPA", irreversible=True)
    assert irreversible_completed(state) == [
        {"number": 6, "title": "Upload to the PPA", "irreversible": True}
    ]
