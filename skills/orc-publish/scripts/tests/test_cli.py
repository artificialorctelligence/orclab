import textwrap
import time

import pytest

from orc_publish.tree import load_tree
from orc_publish.selection import SelectionError
from orc_publish.cli import (
    build_plan,
    DEFAULT_TIMEOUT_SECONDS,
    effective_timeout,
    execute_plan,
    format_plan,
    format_summary,
    main,
    render_filename,
    run_for,
    timeout_error,
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


def test_format_plan_reports_an_action_less_leaf_as_not_yet_actionable(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            desktop:
              python:
                linux:
                  snap: {}
            """,
        )
    )
    leaves = build_plan(root, [])
    text = format_plan(leaves)
    assert "desktop.python.linux.snap: (known channel, not yet actionable)" in text
    assert "no action set" not in text


def test_execute_plan_details_an_action_less_leaf_as_not_yet_actionable(tmp_path):
    root = load_tree(write_yaml(tmp_path, "channels.yaml", "placeholder: {}"))
    leaves = build_plan(root, [])
    results = execute_plan(leaves)
    leaf, status, detail = results[0]
    assert status == "not attempted"
    assert detail == "known channel, not yet actionable"


def test_format_plan_still_shows_a_real_action_unchanged(tmp_path):
    root = load_tree(write_yaml(tmp_path, "channels.yaml", 'a: { action: "echo real" }'))
    text = format_plan(build_plan(root, []))
    assert "a: echo real" in text
    assert "not yet actionable" not in text


def test_effective_timeout_prefers_the_leafs_own_value(tmp_path):
    root = load_tree(
        write_yaml(tmp_path, "channels.yaml", 'a: { action: "true", timeout: 45 }')
    )
    leaf = build_plan(root, [])[0]
    assert effective_timeout(leaf) == 45


def test_effective_timeout_falls_back_to_the_default(tmp_path):
    root = load_tree(write_yaml(tmp_path, "channels.yaml", 'a: { action: "true" }'))
    leaf = build_plan(root, [])[0]
    assert effective_timeout(leaf) == DEFAULT_TIMEOUT_SECONDS
    assert DEFAULT_TIMEOUT_SECONDS == 600


def test_execute_plan_reports_a_hanging_action_as_timed_out(tmp_path):
    root = load_tree(
        write_yaml(tmp_path, "channels.yaml", 'a: { action: "sleep 5", timeout: 1 }')
    )
    leaves = build_plan(root, [])
    results = execute_plan(leaves)
    leaf, status, detail = results[0]
    assert status == "timed out"
    assert "timed out after 1s" in detail
    assert "waiting on stdin" in detail


def test_execute_plan_continues_past_a_timed_out_leaf(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            a: { action: "sleep 5", timeout: 1 }
            b: { action: "true" }
            """,
        )
    )
    results = execute_plan(build_plan(root, []))
    statuses = {leaf.dotted_path: status for leaf, status, _ in results}
    assert statuses == {"a": "timed out", "b": "success"}


def test_main_exits_non_zero_when_a_leaf_times_out(tmp_path):
    path = write_yaml(
        tmp_path, "channels.yaml", 'a: { action: "sleep 5", timeout: 1 }'
    )
    assert main(["--channels", path]) == 1


def test_execute_plan_kills_the_whole_process_group_on_timeout(tmp_path):
    # A lone `sleep` execs into the same PID as the shell, so subprocess.run's own
    # child-only kill would still work on it - that proves nothing about a compound
    # command. This one forks a grandchild in a subshell, which subprocess.run orphans:
    # the "timed out" report fires at 1s while the grandchild is still alive, and it
    # would go on to create the sentinel file at ~3s if left running.
    sentinel = tmp_path / "orphan"
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            f'a: {{ action: "true && (sleep 3; touch {sentinel})", timeout: 1 }}',
        )
    )
    results = execute_plan(build_plan(root, []))
    leaf, status, detail = results[0]
    assert status == "timed out"

    time.sleep(3)
    assert not sentinel.exists()


def test_format_plan_shows_each_actionable_leafs_effective_timeout(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            a: { action: "true", timeout: 45 }
            b: { action: "true" }
            c: {}
            """,
        )
    )
    text = format_plan(build_plan(root, []))
    assert "  timeout: 45s" in text
    assert "  timeout: 600s" in text
    # An action-less leaf runs nothing, so it has no timeout to show.
    assert text.splitlines()[-1] == "c: (known channel, not yet actionable)"


def test_format_plan_reflects_a_run_wide_default_override(tmp_path):
    root = load_tree(write_yaml(tmp_path, "channels.yaml", 'b: { action: "true" }'))
    text = format_plan(build_plan(root, []), default_timeout=30)
    assert "  timeout: 30s" in text


def test_a_leafs_own_timeout_beats_a_run_wide_override(tmp_path):
    root = load_tree(
        write_yaml(tmp_path, "channels.yaml", 'a: { action: "true", timeout: 45 }')
    )
    leaf = build_plan(root, [])[0]
    assert effective_timeout(leaf, default_timeout=30) == 45


def test_timeout_error_rejects_a_non_integer_timeout(tmp_path):
    root = load_tree(
        write_yaml(tmp_path, "channels.yaml", 'a: { action: "true", timeout: "soon" }')
    )
    message = timeout_error(build_plan(root, []))
    assert message is not None
    assert "a: timeout must be a positive whole number of seconds" in message


def test_timeout_error_rejects_zero_and_booleans(tmp_path):
    zero = load_tree(
        write_yaml(tmp_path, "zero.yaml", 'a: { action: "true", timeout: 0 }')
    )
    assert timeout_error(build_plan(zero, [])) is not None
    boolean = load_tree(
        write_yaml(tmp_path, "bool.yaml", 'a: { action: "true", timeout: true }')
    )
    assert timeout_error(build_plan(boolean, [])) is not None


def test_timeout_error_accepts_a_valid_and_an_unset_timeout(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            a: { action: "true", timeout: 45 }
            b: { action: "true" }
            """,
        )
    )
    assert timeout_error(build_plan(root, [])) is None


def test_main_reports_a_bad_timeout_as_an_error_even_in_dry_run(tmp_path, capsys):
    path = write_yaml(
        tmp_path, "channels.yaml", 'a: { action: "true", timeout: "soon" }'
    )
    assert main(["--channels", path, "--dry-run"]) == 1
    assert "error:" in capsys.readouterr().err


def test_main_timeout_flag_changes_the_default(tmp_path):
    path = write_yaml(tmp_path, "channels.yaml", 'a: { action: "sleep 5" }')
    assert main(["--channels", path, "--timeout", "1"]) == 1
