import json
import pathlib
import subprocess
import sys

import pytest
from model_floor import OFF, main

# The real script, for the one test that runs it as a process: under /orc-test analyze this
# file runs from mutmut's mutants/ copy, whose scripts are rewritten and not runnable alone.
_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent
FLOOR = str((_SCRIPTS.parent if _SCRIPTS.name == "mutants" else _SCRIPTS) / "model_floor.py")


@pytest.fixture
def run(run_hook, monkeypatch):
    """run(tool_input, tool_name="Agent") -> the hook's stdout for one dispatch, parsed - or
    None when it said nothing. The off-switch is unset unless a test sets it."""
    monkeypatch.delenv(OFF, raising=False)

    def dispatch(tool_input, tool_name="Agent"):
        code, out, err = run_hook(main, {"tool_name": tool_name, "tool_input": tool_input})
        assert code == 0, err
        return json.loads(out) if out.strip() else None
    return dispatch


def test_a_sub_floor_model_is_raised(run):
    r = run({"model": "haiku", "prompt": "x", "subagent_type": "general-purpose"})
    assert r["hookSpecificOutput"]["updatedInput"]["model"] == "sonnet"


def test_the_rest_of_the_dispatch_survives_untouched(run):
    # updatedInput replaces the whole input, so dropping a field here would silently discard
    # the agent's prompt - the one failure mode that would be worse than the wrong model.
    r = run({"model": "haiku", "prompt": "the real task", "subagent_type": "Explore",
             "run_in_background": True})
    patched = r["hookSpecificOutput"]["updatedInput"]
    assert patched["prompt"] == "the real task"
    assert patched["subagent_type"] == "Explore"
    assert patched["run_in_background"] is True


def test_a_model_at_the_floor_is_left_alone(run):
    assert run({"model": "sonnet", "prompt": "x"}) is None


def test_a_model_above_the_floor_is_left_alone(run):
    assert run({"model": "opus", "prompt": "x"}) is None


def test_a_full_model_id_is_recognised(run):
    # A dispatch may name either form; matching only the bare alias would raise Opus to Sonnet.
    assert run({"model": "claude-opus-5", "prompt": "x"}) is None


def test_a_dispatch_naming_no_model_is_left_alone(run):
    # This is how an agent definition's own pinned model reaches the subagent.
    assert run({"prompt": "x"}) is None


def test_an_unrecognised_model_is_raised_not_trusted(run):
    # Allowlist, not denylist: a cheap tier released after this file was written must not pass
    # simply by being absent from a list.
    r = run({"model": "claude-tiny-7", "prompt": "x"})
    assert r["hookSpecificOutput"]["updatedInput"]["model"] == "sonnet"


def test_the_message_names_what_was_replaced(run):
    # The point is that the substitution is visible. A silent override is how someone comes to
    # believe they ran on a model they did not.
    r = run({"model": "haiku", "prompt": "x"})
    assert "haiku" in r["systemMessage"] and "sonnet" in r["systemMessage"]


def test_it_ignores_tools_that_are_not_agent_dispatches(run):
    assert run({"model": "haiku", "command": "ls"}, tool_name="Bash") is None


def test_the_task_alias_is_covered(run):
    r = run({"model": "haiku", "prompt": "x"}, tool_name="Task")
    assert r["hookSpecificOutput"]["updatedInput"]["model"] == "sonnet"


def test_the_off_switch_disables_it(run, monkeypatch):
    monkeypatch.setenv(OFF, "1")
    assert run({"model": "haiku", "prompt": "x"}) is None


def test_malformed_input_fails_open_rather_than_wedging_every_subagent(run_hook, monkeypatch):
    monkeypatch.delenv(OFF, raising=False)
    code, out, _ = run_hook(main, "not json")
    assert code == 0 and out.strip() == ""


def test_as_a_process_it_exits_0_with_the_patched_input_on_stdout():
    """The contract Claude Code sees; the one test here that runs the script for real."""
    out = subprocess.run([sys.executable, FLOOR], check=False,
                         input=json.dumps({"tool_name": "Agent", "tool_input": {"model": "haiku", "prompt": "x"}}),
                         capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout)["hookSpecificOutput"]["updatedInput"]["model"] == "sonnet"
