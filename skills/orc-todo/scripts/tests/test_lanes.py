import subprocess

import pytest

from orc_todo import lanes


def make_repo(tmp_path, specs=("v13", "v14", "v15")):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    d = tmp_path / "docs" / "superpowers" / "specs"
    d.mkdir(parents=True)
    for s in specs:
        (d / f"2026-09-08-orclab-{s}-something-design.md").write_text("# spec\n")
    return tmp_path


def test_a_lane_holds_its_items_in_order(tmp_path):
    repo = make_repo(tmp_path)
    lane = lanes.create_lane("B", ["v14", "v15"], cwd=repo)
    assert lane["items"] == ["v14", "v15"]
    assert lanes.read_lanes(repo)["B"]["items"] == ["v14", "v15"]


def test_an_unspecced_item_is_refused_and_names_itself(tmp_path):
    """The refusal is load-bearing, not pedantry: #17 alone is ambiguous because speccing it
    could produce either v14 or v15."""
    repo = make_repo(tmp_path)
    with pytest.raises(lanes.UnspeccedItem) as e:
        lanes.create_lane("A", ["v13", "v99"], cwd=repo)
    assert e.value.item == "v99"
    assert "A" not in lanes.read_lanes(repo), "a refused lane must not be half-created"


def test_a_plan_counts_as_a_spec_for_lane_membership(tmp_path):
    repo = make_repo(tmp_path, specs=())
    d = repo / "docs" / "superpowers" / "plans"
    d.mkdir(parents=True)
    (d / "2026-09-08-orclab-v12-artifact-preflight.md").write_text("# plan\n")
    assert lanes.create_lane("A", ["v12"], cwd=repo)["items"] == ["v12"]


def test_modify_replaces_the_item_list_so_it_can_reorder_add_and_drop(tmp_path):
    repo = make_repo(tmp_path)
    lanes.create_lane("B", ["v14", "v15"], cwd=repo)
    assert lanes.modify_lane("B", ["v15", "v13"], cwd=repo)["items"] == ["v15", "v13"]


def test_modify_on_a_missing_lane_raises(tmp_path):
    repo = make_repo(tmp_path)
    with pytest.raises(lanes.LaneMissing):
        lanes.modify_lane("nope", ["v13"], cwd=repo)


def test_delete_removes_the_lane(tmp_path):
    repo = make_repo(tmp_path)
    lanes.create_lane("B", ["v14"], cwd=repo)
    lanes.delete_lane("B", cwd=repo)
    assert "B" not in lanes.read_lanes(repo)


def test_modify_keeps_current_when_it_survives_and_clears_it_when_it_does_not(tmp_path):
    repo = make_repo(tmp_path)
    lanes.create_lane("B", ["v14", "v15"], cwd=repo)
    lanes.set_current("B", "v14", cwd=repo)
    assert lanes.modify_lane("B", ["v14", "v13"], cwd=repo)["current"] == "v14"
    assert lanes.modify_lane("B", ["v13", "v15"], cwd=repo)["current"] is None


def test_in_progress_reports_only_lanes_with_a_current_item(tmp_path):
    repo = make_repo(tmp_path)
    lanes.create_lane("A", ["v13"], cwd=repo)
    lanes.create_lane("B", ["v14"], cwd=repo)
    lanes.set_current("A", "v13", cwd=repo)
    running = lanes.in_progress(repo)
    assert [r["lane"] for r in running] == ["A"]
    assert running[0]["item"] == "v13" and running[0]["started"]


def test_setting_current_to_an_item_not_in_the_lane_raises(tmp_path):
    repo = make_repo(tmp_path)
    lanes.create_lane("A", ["v13"], cwd=repo)
    with pytest.raises(lanes.LaneMissing):
        lanes.set_current("A", "v15", cwd=repo)


def test_read_lanes_is_empty_rather_than_failing_when_nothing_exists(tmp_path):
    repo = make_repo(tmp_path)
    assert lanes.read_lanes(repo) == {}
