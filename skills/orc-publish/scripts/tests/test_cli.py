import textwrap

import pytest

from orc_publish.tree import load_tree
from orc_publish.selection import SelectionError
from orc_publish.cli import (
    build_plan,
    execute_plan,
    format_plan,
    format_summary,
    main,
    render_filename,
    run_for,
)


def write_yaml(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(textwrap.dedent(content))
    return str(path)


def test_render_filename_substitutes_version():
    assert render_filename("orcshot_<version>.zip", "1.2.3") == "orcshot_1.2.3.zip"


def test_render_filename_handles_missing_template():
    assert render_filename(None, "1.2.3") is None


def test_format_plan_lists_each_leaf_and_its_action(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            "desktop: { python: { linux: { snap: { action: 'echo publish-snap' } } } }",
        )
    )
    leaves = build_plan(root, [])
    text = format_plan(leaves)
    assert "desktop.python.linux.snap: echo publish-snap" in text


def test_format_plan_includes_a_leafs_requirements_and_issues(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            desktop:
              python:
                linux:
                  ppa:
                    noble:
                      action: "echo publish"
                      requirements: ["gpg key registered to the Launchpad account"]
                      issues: ["unlock gpg-agent before running for real"]
            """,
        )
    )
    leaves = build_plan(root, [])
    text = format_plan(leaves)
    assert "requirement: gpg key registered to the Launchpad account" in text
    assert "issue: unlock gpg-agent before running for real" in text


def test_build_plan_raises_selection_error_for_an_unknown_token(tmp_path):
    root = load_tree(write_yaml(tmp_path, "channels.yaml", "a: { action: 'true' }"))
    with pytest.raises(SelectionError):
        build_plan(root, ["does-not-exist"])


def test_execute_plan_continues_past_a_failure_and_reports_each_status(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            a: { action: "true" }
            b: { action: "false" }
            c: { action: "true" }
            """,
        )
    )
    leaves = build_plan(root, [])
    results = execute_plan(leaves)
    statuses = {leaf.dotted_path: status for leaf, status, _ in results}
    assert statuses == {"a": "success", "b": "failed", "c": "success"}


def test_execute_plan_reports_not_attempted_for_a_leaf_with_no_action(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            real: { action: "true" }
            placeholder: {}
            """,
        )
    )
    leaves = build_plan(root, [])
    results = execute_plan(leaves)
    statuses = {leaf.dotted_path: status for leaf, status, _ in results}
    assert statuses["placeholder"] == "not attempted"


def test_format_summary_includes_the_real_failure_detail(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            "b: { action: \"echo failing-thing 1>&2; exit 1\" }",
        )
    )
    leaves = build_plan(root, [])
    results = execute_plan(leaves)
    summary = format_summary(results)
    assert "b: failed" in summary
    assert "failing-thing" in summary


def test_run_for_reports_the_channel_when_set(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "distro.yaml",
            "mint: { x11: { channel: 'desktop.python.linux.ppa.noble' } }",
        )
    )
    assert run_for(root, "mint.x11") == "mint.x11 -> desktop.python.linux.ppa.noble"


def test_run_for_reports_no_channel_when_unset(tmp_path):
    root = load_tree(write_yaml(tmp_path, "distro.yaml", "mint-next: { x11: {} }"))
    result = run_for(root, "mint-next.x11")
    assert "no channel set" in result


def test_run_for_raises_when_the_target_is_a_branch_not_a_leaf(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "distro.yaml",
            "mint: { x11: { channel: 'a.b' }, wayland: { channel: 'a.b' } }",
        )
    )
    with pytest.raises(SelectionError):
        run_for(root, "mint")


def test_format_plan_reports_no_leaves_selected_when_empty():
    assert format_plan([]) == "(no leaves selected)"


def test_execute_plan_surfaces_successful_stdout_in_the_result(tmp_path):
    root = load_tree(
        write_yaml(tmp_path, "channels.yaml", 'a: { action: "echo hello-from-a" }')
    )
    leaves = build_plan(root, [])
    results = execute_plan(leaves)
    leaf, status, detail = results[0]
    assert status == "success"
    assert "hello-from-a" in detail


def test_main_dry_run_does_not_execute_any_action(tmp_path):
    path = write_yaml(
        tmp_path, "channels.yaml", f'a: {{ action: "touch {tmp_path}/sentinel" }}'
    )
    exit_code = main(["--channels", path, "--dry-run"])
    assert exit_code == 0
    assert not (tmp_path / "sentinel").exists()


def test_main_real_run_executes_the_action(tmp_path):
    path = write_yaml(
        tmp_path, "channels.yaml", f'a: {{ action: "touch {tmp_path}/sentinel" }}'
    )
    exit_code = main(["--channels", path])
    assert exit_code == 0
    assert (tmp_path / "sentinel").exists()


def test_main_reports_a_clean_error_for_a_missing_channels_file(tmp_path, capsys):
    exit_code = main(["--channels", str(tmp_path / "does-not-exist.yaml")])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err


def test_main_for_mode_notes_when_selection_tokens_are_ignored(tmp_path, capsys):
    path = write_yaml(tmp_path, "distro.yaml", "mint: { x11: { channel: 'a.b' } }")
    exit_code = main(["ignored-token", "--distro", path, "--for", "mint.x11"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "ignored" in captured.err
