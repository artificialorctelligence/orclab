import os
import signal
import subprocess
import textwrap
import time

import pytest

from orc_publish.tree import load_tree
from orc_publish.selection import SelectionError
from orc_publish.cli import (
    action_shape_warning,
    build_plan,
    DEFAULT_TIMEOUT_SECONDS,
    effective_timeout,
    execute_plan,
    expand_path,
    format_plan,
    format_summary,
    main,
    preflight_refusal,
    run_for,
    timeout_error,
)


def write_yaml(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(textwrap.dedent(content))
    return str(path)


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
    # "sleep 5" produces no output at all, so "no output captured" is honest here - it's a
    # real, different signal from the output-then-hang shape below. See BACKLOG #15.
    assert "no output captured" in detail
    assert "waiting on stdin" in detail


def test_execute_plan_surfaces_output_captured_before_a_timeout(tmp_path):
    # The flagship shape: a wall of build output, then a hang. The operator needs to see how
    # far it got, not be told nothing was captured. See BACKLOG #15.
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            'a: { action: "echo hello; sleep 5", timeout: 1 }',
        )
    )
    results = execute_plan(build_plan(root, []))
    leaf, status, detail = results[0]
    assert status == "timed out"
    assert "timed out after 1s" in detail
    assert "hello" in detail
    assert "no output captured" not in detail
    assert "waiting on stdin" in detail
    # Ordering is load-bearing, not cosmetic: with a real build log the capture runs to
    # hundreds of lines, and a stdin hint printed after it is buried and reads as part of
    # the output. Asserted so a future edit can't silently re-invert it.
    assert detail.index("waiting on stdin") < detail.index("hello")


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


def grandchild_action(pidfile, sleep_seconds=30):
    """A compound action whose real work runs in a grandchild that reports its own PID.

    A lone `sleep` execs into the same PID as the shell, so a child-only kill would still
    reach it - that proves nothing about a compound command. The nested `sh -c` is a genuine
    grandchild, which a child-only kill orphans. The `$$` has to be inside that nested shell:
    in a plain `(...)` subshell it expands to the *outer* shell's PID, which would silently
    turn the assertion into one about a process that was killed directly.
    """
    return f"true && sh -c 'echo $$ > {pidfile}; sleep {sleep_seconds}'"


# A ceiling on how long the two process-group tests may take. Their grandchild sleeps 30s, so
# without a real group kill `proc.wait()` blocks until that sleep runs out and the test still
# passes - just 50x slower. That slowdown was the ONLY signal separating a working kill from a
# wait-it-out pass (BACKLOG #16), and nothing asserted on it. This does. It sits far above the
# real ~1.2s and far below the 30s a wait-it-out takes, so it fails a regressed kill without
# being a timing race on a loaded machine.
KILL_CEILING_SECONDS = 10


def assert_returned_promptly(elapsed, what):
    """Fail unless `what` finished well inside the grandchild's own sleep.

    A pass that took the full sleep means nothing was killed - the call merely waited for the
    process tree to end on its own, and reported the same outcome a real kill produces.
    """
    assert elapsed < KILL_CEILING_SECONDS, (
        f"{what} took {elapsed:.1f}s, over the {KILL_CEILING_SECONDS}s ceiling - the process "
        "group was probably not killed, and this only finished because the grandchild's own "
        "sleep ran out"
    )


def assert_process_gone(pid, timeout=5):
    """Fail unless `pid` is gone - polled, since reaping a reparented process is asynchronous."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    os.kill(pid, signal.SIGKILL)
    pytest.fail(f"grandchild {pid} survived - its process group was not killed")


def test_execute_plan_kills_the_whole_process_group_on_timeout(tmp_path):
    # The grandchild writes its PID immediately and then sleeps far past the timeout, so this
    # asks "is it still there?" rather than racing a sentinel file against the check. A kill
    # that only reaches the shell leaves the grandchild alive for the full 30s.
    pidfile = tmp_path / "grandchild.pid"
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            f'a: {{ action: "{grandchild_action(pidfile)}", timeout: 1 }}',
        )
    )
    started = time.monotonic()
    results = execute_plan(build_plan(root, []))
    elapsed = time.monotonic() - started
    leaf, status, detail = results[0]
    assert status == "timed out"

    assert_process_gone(int(pidfile.read_text()))
    assert_returned_promptly(elapsed, "execute_plan")


def test_execute_plan_kills_the_whole_process_group_on_interrupt(tmp_path, monkeypatch):
    # start_new_session also means a Ctrl-C on this process no longer reaches the action, so
    # an interrupt orphans exactly what the timeout kill exists to catch - unless the group
    # kill is unconditional. KeyboardInterrupt stands in for the signal; it takes the same path.
    pidfile = tmp_path / "grandchild.pid"
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            f'a: {{ action: "{grandchild_action(pidfile)}", timeout: 30 }}',
        )
    )
    leaves = build_plan(root, [])

    def interrupt_once_the_grandchild_is_up(self, *args, **kwargs):
        deadline = time.monotonic() + 5
        while not pidfile.exists():
            if time.monotonic() > deadline:
                pytest.fail("grandchild never wrote its pidfile - the action may not have started")
            time.sleep(0.01)
        raise KeyboardInterrupt

    monkeypatch.setattr(
        subprocess.Popen, "communicate", interrupt_once_the_grandchild_is_up
    )
    started = time.monotonic()
    with pytest.raises(KeyboardInterrupt):
        execute_plan(leaves)
    elapsed = time.monotonic() - started
    monkeypatch.undo()

    assert_process_gone(int(pidfile.read_text()))
    assert_returned_promptly(elapsed, "the interrupted execute_plan")


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


@pytest.mark.parametrize("bad", ["0", "-5"])
def test_main_rejects_a_non_positive_timeout_flag(tmp_path, capsys, bad):
    # Held to the same rule as a leaf's own `timeout:`. Unvalidated, both `--timeout 0` and
    # `--timeout -5` would falsely report every leaf as `timed out` without running it -
    # measured directly (Python 3.12): a negative timeout is an endtime already in the past,
    # so subprocess.run/Popen.communicate raise TimeoutExpired immediately, in 0.00s, exactly
    # like 0. Neither ever runs with no timeout.
    path = write_yaml(tmp_path, "channels.yaml", 'a: { action: "true" }')
    assert main(["--channels", path, "--dry-run", "--timeout", bad]) == 1
    err = capsys.readouterr().err
    assert "error: --timeout must be a positive whole number of seconds" in err


def _leaf_yaml(tmp_path, extra):
    return write_yaml(tmp_path, "channels.yaml", "a:\n" + extra)


def test_prepare_runs_before_the_action(tmp_path):
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            f'  prepare: "touch {tmp_path}/built"\n'
            f'  action: "test -f {tmp_path}/built && touch {tmp_path}/published"\n',
        )
    )
    results = execute_plan(build_plan(root, []))
    assert results[0][1] == "success"
    assert (tmp_path / "published").exists()


def test_a_failing_prepare_fails_the_leaf_and_the_action_never_runs(tmp_path):
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            '  prepare: "echo build-broke 1>&2; exit 1"\n'
            f'  action: "touch {tmp_path}/published"\n',
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "failed"
    assert "build-broke" in detail
    assert not (tmp_path / "published").exists()


def test_a_prepare_that_hangs_times_out_and_the_action_never_runs(tmp_path):
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            '  prepare: "sleep 30"\n'
            '  timeout: 1\n'
            f'  action: "touch {tmp_path}/published"\n',
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "timed out"
    assert "prepare" in detail
    assert not (tmp_path / "published").exists()


def test_a_dirty_artifact_refuses_and_the_action_never_runs(tmp_path):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    with tarfile.open(tmp_path / "src.tar.gz", "w:gz") as tf:
        tf.add(blank, arcname="pkg/.git/config")
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            f'  artifact: "{tmp_path}/src.tar.gz"\n'
            '  preflight: [no-vcs]\n'
            f'  action: "touch {tmp_path}/published"\n',
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "refused"
    assert "no-vcs" in detail
    assert not (tmp_path / "published").exists()


def test_a_clean_artifact_publishes(tmp_path):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    with tarfile.open(tmp_path / "src.tar.gz", "w:gz") as tf:
        tf.add(blank, arcname="pkg/main.py")
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            f'  artifact: "{tmp_path}/src.tar.gz"\n'
            '  preflight: [no-vcs]\n'
            f'  action: "touch {tmp_path}/published"\n',
        )
    )
    assert execute_plan(build_plan(root, []))[0][1] == "success"
    assert (tmp_path / "published").exists()


def test_a_missing_artifact_refuses(tmp_path):
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            f'  artifact: "{tmp_path}/never-built.tar.gz"\n'
            '  preflight: [no-vcs]\n'
            '  action: "true"\n',
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "refused"
    assert "not found" in detail


def test_an_unreadable_format_refuses_naming_the_format_not_a_rule(tmp_path):
    (tmp_path / "thing.snap").write_bytes(b"hsqs definitely not tar or zip")
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            f'  artifact: "{tmp_path}/thing.snap"\n'
            '  preflight: [no-vcs]\n'
            '  action: "true"\n',
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "refused"
    assert "unsupported" in detail.lower()
    assert "no-vcs" not in detail


def test_an_unknown_rule_name_refuses(tmp_path):
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            f'  artifact: "{tmp_path}/anything.tar.gz"\n'
            '  preflight: [no-such-rule]\n'
            '  action: "true"\n',
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "refused"
    assert "no-such-rule" in detail


def test_preflight_with_no_artifact_refuses(tmp_path):
    root = load_tree(_leaf_yaml(tmp_path, '  preflight: [no-vcs]\n  action: "true"\n'))
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "refused"
    assert detail == "preflight is declared but no artifact: is set - nothing to inspect"


# The plan is what the operator says yes to, so for every refusal knowable without the artifact
# existing, the dry-run line and the real run's detail must be the same sentence - asserted
# against each other rather than each against its own hardcoded copy.
@pytest.mark.parametrize(
    "extra",
    [
        "  preflight: [no-vcs]\n",                                     # no artifact: at all
        '  artifact: "later.tar.gz"\n  preflight: [no-vcss]\n',        # typo'd rule name
        '  artifact: "typo-in-path.tar.gz"\n  preflight: [no-vcs]\n',  # no prepare: to build it
    ],
    ids=["no-artifact", "unknown-rule", "missing-artifact-no-prepare"],
)
def test_dry_run_reports_the_refusal_the_real_run_will_give(tmp_path, capsys, extra):
    path = write_yaml(tmp_path, "channels.yaml", "a:\n" + extra + '  action: "true"\n')
    assert main(["--channels", path, "--dry-run"]) == 0
    plan = capsys.readouterr().out
    assert "will be inspected" not in plan

    _leaf, status, detail = execute_plan(build_plan(load_tree(path), []))[0]
    assert status == "refused"
    assert f"preflight result: {detail}" in plan


def test_a_refused_leaf_does_not_stop_the_next_one(tmp_path):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    with tarfile.open(tmp_path / "src.tar.gz", "w:gz") as tf:
        tf.add(blank, arcname="pkg/.git/config")
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ artifact: "{tmp_path}/src.tar.gz", preflight: [no-vcs], action: "true" }}\n'
        'b: { action: "true" }\n',
    )
    results = execute_plan(build_plan(load_tree(path), []))
    assert {leaf.dotted_path: s for leaf, s, _ in results} == {"a": "refused", "b": "success"}


def test_main_exits_non_zero_on_a_refusal(tmp_path):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    with tarfile.open(tmp_path / "src.tar.gz", "w:gz") as tf:
        tf.add(blank, arcname="pkg/.git/config")
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ artifact: "{tmp_path}/src.tar.gz", preflight: [no-vcs], action: "true" }}\n',
    )
    assert main(["--channels", path]) == 1


def test_the_override_publishes_anyway_and_still_reports(tmp_path, capsys):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    with tarfile.open(tmp_path / "src.tar.gz", "w:gz") as tf:
        tf.add(blank, arcname="pkg/.git/config")
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ artifact: "{tmp_path}/src.tar.gz", preflight: [no-vcs], '
        f'action: "touch {tmp_path}/published" }}\n',
    )
    assert main(["--channels", path, "--allow-preflight-failure"]) == 0
    assert (tmp_path / "published").exists()
    assert "no-vcs" in capsys.readouterr().out


def test_expand_path_runs_command_substitution(tmp_path):
    assert expand_path("$(echo hello).tar.xz", 10) == "hello.tar.xz"


def test_expand_path_kills_the_whole_process_group_on_timeout(tmp_path):
    # Same shape as the action-side process-group tests above: the command substitution in
    # expand_path's `printf` forks too, so a kill that only reaches the outer shell orphans
    # the grandchild - the exact bug a bare subprocess.run had.
    pidfile = tmp_path / "grandchild.pid"
    expr = f"$({grandchild_action(pidfile)}; echo x).tar.gz"
    with pytest.raises(subprocess.TimeoutExpired):
        expand_path(expr, 1)
    assert_process_gone(int(pidfile.read_text()))


def test_a_corrupt_archive_refuses_and_does_not_stop_siblings(tmp_path):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    archive = tmp_path / "src.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(blank, arcname="pkg/main.py")
    archive.write_bytes(archive.read_bytes()[: archive.stat().st_size // 2])
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ artifact: "{archive}", preflight: [no-vcs], action: "true" }}\n'
        'b: { action: "true" }\n',
    )
    results = execute_plan(build_plan(load_tree(path), []))
    statuses = {leaf.dotted_path: s for leaf, s, _ in results}
    details = {leaf.dotted_path: d for leaf, s, d in results}
    assert statuses == {"a": "refused", "b": "success"}
    assert "unsupported" in details["a"].lower()


def test_main_does_not_crash_on_a_corrupt_artifact(tmp_path):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    archive = tmp_path / "src.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(blank, arcname="pkg/main.py")
    archive.write_bytes(archive.read_bytes()[: archive.stat().st_size // 2])
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ artifact: "{archive}", preflight: [no-vcs], action: "true" }}\n',
    )
    assert main(["--channels", path]) == 1


def test_a_malformed_preflight_list_refuses_and_does_not_stop_siblings(tmp_path):
    """`preflight: [no-vcs, 5]` used to raise TypeError out of `", ".join(leaf.preflight)` in
    format_plan - reached by both --dry-run and a real run, ahead of execute_plan's own
    per-leaf containment, so the whole process aborted with a traceback and `b` never ran."""
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        'a: { artifact: "nope.tar.gz", preflight: [no-vcs, 5], action: "true" }\n'
        'b: { action: "true" }\n',
    )
    results = execute_plan(build_plan(load_tree(path), []))
    statuses = {leaf.dotted_path: s for leaf, s, _ in results}
    details = {leaf.dotted_path: d for leaf, s, d in results}
    assert statuses == {"a": "refused", "b": "success"}
    assert details["a"] == "unknown preflight rule(s): 5"


def test_main_does_not_crash_on_a_malformed_preflight_list(tmp_path):
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        'a: { artifact: "nope.tar.gz", preflight: [no-vcs, 5], action: "true" }\n'
        'b: { action: "true" }\n',
    )
    assert main(["--channels", path]) == 1


def test_dry_run_does_not_crash_on_a_malformed_preflight_list(tmp_path, capsys):
    """The dry-run plan must survive the same malformed shape the real run does - it reports
    what the real run will do, so a crash here would hide the refusal instead of previewing
    it."""
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        'a: { artifact: "nope.tar.gz", preflight: [no-vcs, 5], action: "true" }\n'
        'b: { action: "true" }\n',
    )
    assert main(["--channels", path, "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "preflight result: unknown preflight rule(s): 5" in out


def test_a_hanging_artifact_expansion_refuses_and_does_not_stop_siblings(tmp_path):
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        'a: { artifact: "$(sleep 30; echo x).tar.gz", preflight: [no-vcs], timeout: 1, '
        'action: "true" }\n'
        'b: { action: "true" }\n',
    )
    results = execute_plan(build_plan(load_tree(path), []))
    statuses = {leaf.dotted_path: s for leaf, s, _ in results}
    details = {leaf.dotted_path: d for leaf, s, d in results}
    assert statuses == {"a": "refused", "b": "success"}
    assert "timed out" in details["a"]


def test_dry_run_never_runs_prepare(tmp_path):
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ prepare: "touch {tmp_path}/built", action: "true" }}\n',
    )
    assert main(["--channels", path, "--dry-run"]) == 0
    assert not (tmp_path / "built").exists()


def test_dry_run_reports_findings_when_the_artifact_already_exists(tmp_path, capsys):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    with tarfile.open(tmp_path / "src.tar.gz", "w:gz") as tf:
        tf.add(blank, arcname="pkg/.git/config")
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ artifact: "{tmp_path}/src.tar.gz", preflight: [no-vcs], action: "true" }}\n',
    )
    assert main(["--channels", path, "--dry-run"]) == 0
    out = capsys.readouterr().out
    # "no-vcs" alone appears unconditionally in the "preflight: no-vcs" declaration line
    # even when the artifact is never inspected - assert on the rendered inspection result
    # instead, which only an actual `inspect_archive` call over the real archive produces.
    assert "preflight result: no-vcs: 1 entries, first 1: pkg/.git/config" in out


def test_dry_run_says_inspection_is_deferred_when_the_artifact_is_not_built_yet(
    tmp_path, capsys
):
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ prepare: "true", artifact: "{tmp_path}/later.tar.gz", '
        'preflight: [no-vcs], action: "true" }\n',
    )
    assert main(["--channels", path, "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "will be inspected" in out
    # The declared rule name legitimately appears in the "preflight: no-vcs" line
    # (see test_dry_run_lists_the_preflight_rules_a_leaf_declares, which requires exactly
    # that for an equally-unbuilt artifact) - what must not happen is an actual inspection
    # result, since the artifact doesn't exist yet to inspect.
    assert "preflight result: clean" not in out
    assert "preflight result: unknown preflight rule" not in out


def test_dry_run_lists_the_preflight_rules_a_leaf_declares(tmp_path, capsys):
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ artifact: "{tmp_path}/x.tar.gz", preflight: [no-vcs, no-tool-state], '
        'action: "true" }\n',
    )
    main(["--channels", path, "--dry-run"])
    assert "no-vcs, no-tool-state" in capsys.readouterr().out


def test_dry_run_does_not_crash_on_a_hanging_artifact_expansion(tmp_path, capsys):
    # Before this fix, format_plan called expand_path directly and let
    # subprocess.TimeoutExpired propagate - a dry run, the safety gate the user reads before
    # confirming, must never crash instead of reporting.
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        'a: { artifact: "$(sleep 30; echo x).tar.gz", preflight: [no-vcs], timeout: 1, '
        'action: "true" }\n',
    )
    assert main(["--channels", path, "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "preflight result: artifact path expansion timed out after 1s" in out


def _one(tmp_path, action):
    root = load_tree(write_yaml(tmp_path, "c.yaml", f'a: {{ action: "{action}" }}'))
    return build_plan(root, [])[0]


def test_a_build_then_publish_action_warns(tmp_path):
    leaf = _one(tmp_path, "dpkg-buildpackage -S && dput ppa:x ../y.changes")
    warning = action_shape_warning(leaf)
    assert warning is not None
    assert "prepare" in warning


def test_a_bare_publish_action_does_not_warn(tmp_path):
    assert action_shape_warning(_one(tmp_path, "dput ppa:x ../y.changes")) is None


def test_a_bare_build_action_does_not_warn(tmp_path):
    assert action_shape_warning(_one(tmp_path, "dpkg-buildpackage -S")) is None


def test_publish_before_build_does_not_warn(tmp_path):
    # Order matters: only a build *preceding* an irreversible publish is the bad shape.
    assert action_shape_warning(_one(tmp_path, "dput ppa:x f.changes && dpkg-buildpackage -S")) is None


def test_a_publish_after_a_build_warns_even_when_a_publish_came_first(tmp_path):
    # A leading publish must not hide the build-then-publish shape that follows it.
    leaf = _one(tmp_path, "dput ppa:x a.changes && dpkg-buildpackage -S && dput ppa:x b.changes")
    assert action_shape_warning(leaf) is not None


def test_an_action_less_leaf_does_not_warn(tmp_path):
    root = load_tree(write_yaml(tmp_path, "c.yaml", "a: {}"))
    assert action_shape_warning(build_plan(root, [])[0]) is None


def test_the_warning_appears_in_the_dry_run_plan(tmp_path, capsys):
    path = write_yaml(
        tmp_path, "channels.yaml", 'a: { action: "dpkg-buildpackage -S && dput ppa:x f.changes" }'
    )
    main(["--channels", path, "--dry-run"])
    assert "one command" in capsys.readouterr().out


# --metrics: the same execution path, reading a different leaf key. See BACKLOG #7.


def metrics_tree(tmp_path):
    return load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            ppa:
              noble:
                action: "echo PUBLISHED"
                metrics: "echo 42 downloads"
              snap: {}
            """,
        )
    )


def test_metrics_runs_the_metrics_command_not_the_action(tmp_path):
    leaves = build_plan(metrics_tree(tmp_path), ["ppa.noble"])
    results = execute_plan(leaves, command_key="metrics")
    assert results[0][1] == "success"
    assert results[0][2] == "42 downloads"


def test_action_is_still_the_default_command_key(tmp_path):
    leaves = build_plan(metrics_tree(tmp_path), ["ppa.noble"])
    assert execute_plan(leaves)[0][2] == "PUBLISHED"


def test_format_plan_shows_the_metrics_command_under_metrics(tmp_path):
    leaves = build_plan(metrics_tree(tmp_path), ["ppa.noble"])
    assert "ppa.noble: echo 42 downloads" in format_plan(leaves, command_key="metrics")


def test_a_leaf_without_metrics_is_reported_as_having_no_metrics_source(tmp_path):
    """Distinct wording from an action-less leaf: 'not yet actionable' would be a lie about a
    channel that publishes fine and simply has no counter wired up."""
    leaves = build_plan(metrics_tree(tmp_path), ["ppa.snap"])
    assert "no metrics source" in format_plan(leaves, command_key="metrics")
    assert execute_plan(leaves, command_key="metrics")[0][2] == "known channel, no metrics source"


def test_main_with_metrics_runs_metrics_and_leaves_the_action_alone(tmp_path, capsys):
    marker = tmp_path / "published"
    channels = write_yaml(
        tmp_path,
        "channels.yaml",
        f"""
        ppa:
          noble:
            action: "touch {marker}"
            metrics: "echo 7"
        """,
    )
    assert main(["ppa.noble", "--metrics", "--channels", channels]) == 0
    assert "ppa.noble: success (7)" in capsys.readouterr().out
    assert not marker.exists(), "--metrics must never run a leaf's publish action"


def test_main_exports_the_scripts_dir_to_leaf_commands(tmp_path, capsys):
    """A project's channels.yaml calls Orclab's own bundled readers by $ORC_PUBLISH_SCRIPTS,
    because $CLAUDE_SKILL_DIR is not set in every context these commands really run in."""
    channels = write_yaml(
        tmp_path,
        "channels.yaml",
        'ppa: { noble: { metrics: "test -f $ORC_PUBLISH_SCRIPTS/metrics/launchpad_ppa.py" } }',
    )
    assert main(["ppa.noble", "--metrics", "--channels", channels]) == 0
    assert "ppa.noble: success" in capsys.readouterr().out


# The two features meeting: the preflight gate belongs to the action path only.


def test_metrics_ignores_prepare_and_preflight(tmp_path, capsys):
    """A metrics query publishes nothing, so there is nothing to gate. Running the project's
    build to answer a read-only download-count question would be wrong, and a leaf whose
    artifact does not exist yet must still be able to report its numbers."""
    prepared = tmp_path / "prepared"
    channels = write_yaml(
        tmp_path,
        "channels.yaml",
        f"""
        ppa:
          noble:
            action: "echo PUBLISHED"
            metrics: "echo 42 downloads"
            prepare: "touch {prepared}"
            artifact: "{tmp_path}/never-built.tar"
            preflight: ["no-vcs"]
        """,
    )
    assert main(["ppa.noble", "--metrics", "--channels", channels]) == 0
    out = capsys.readouterr().out
    assert "ppa.noble: success (42 downloads)" in out
    assert "refused" not in out
    assert "preflight" not in out, "a --metrics plan must not inspect an artifact"
    assert not prepared.exists(), "--metrics must never run a leaf's prepare:"


def test_the_action_path_still_refuses_that_same_leaf(tmp_path):
    """The negative control for the test above: the identical leaf, run as an action, does
    hit the gate - so the metrics pass is skipping the gate, not the gate being absent."""
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            f"""
            ppa:
              noble:
                action: "echo PUBLISHED"
                metrics: "echo 42 downloads"
                artifact: "{tmp_path}/never-built.tar"
                preflight: ["no-vcs"]
            """,
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, ["ppa.noble"]))[0]


def test_confirm_with_neither_command_nor_url_is_an_error(tmp_path, capsys):
    # Declaring confirm says "this publish is asynchronous" and then names no way to find out
    # whether it landed. There is no default that could stand in for the missing answer.
    channels = tmp_path / "channels.yaml"
    channels.write_text('ppa:\n  noble:\n    action: "true"\n    confirm: {}\n')
    assert main(["--channels", str(channels), "--dry-run", "ppa"]) == 1
    assert "confirm must declare" in capsys.readouterr().err


def test_a_non_mapping_confirm_is_an_error_naming_the_value(tmp_path, capsys):
    channels = tmp_path / "channels.yaml"
    channels.write_text('ppa:\n  noble:\n    action: "true"\n    confirm: true\n')
    assert main(["--channels", str(channels), "--dry-run", "ppa"]) == 1
    err = capsys.readouterr().err
    assert "confirm must be a mapping" in err
    assert "True" in err


def test_a_well_formed_confirm_is_not_an_error(tmp_path):
    channels = tmp_path / "channels.yaml"
    channels.write_text('ppa:\n  noble:\n    action: "true"\n    confirm:\n      url: https://e.test/q\n')
    assert main(["--channels", str(channels), "--dry-run", "ppa"]) == 0
