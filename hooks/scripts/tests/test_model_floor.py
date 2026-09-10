import json
import pathlib
import subprocess
import sys

FLOOR = str(pathlib.Path(__file__).resolve().parent.parent / "model_floor.py")


def run(tool_input, tool_name="Agent", env=None):
    """The hook's stdout for one dispatch, parsed - or None when it said nothing."""
    out = subprocess.run(
        [sys.executable, FLOOR],
        input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
        capture_output=True, text=True, env=env,
    )
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout) if out.stdout.strip() else None


def test_a_sub_floor_model_is_raised(tmp_path):
    r = run({"model": "haiku", "prompt": "x", "subagent_type": "general-purpose"})
    assert r["hookSpecificOutput"]["updatedInput"]["model"] == "sonnet"


def test_the_rest_of_the_dispatch_survives_untouched(tmp_path):
    # updatedInput replaces the whole input, so dropping a field here would silently discard
    # the agent's prompt - the one failure mode that would be worse than the wrong model.
    r = run({"model": "haiku", "prompt": "the real task", "subagent_type": "Explore",
             "run_in_background": True})
    patched = r["hookSpecificOutput"]["updatedInput"]
    assert patched["prompt"] == "the real task"
    assert patched["subagent_type"] == "Explore"
    assert patched["run_in_background"] is True


def test_a_model_at_the_floor_is_left_alone(tmp_path):
    assert run({"model": "sonnet", "prompt": "x"}) is None


def test_a_model_above_the_floor_is_left_alone(tmp_path):
    assert run({"model": "opus", "prompt": "x"}) is None


def test_a_full_model_id_is_recognised(tmp_path):
    # A dispatch may name either form; matching only the bare alias would raise Opus to Sonnet.
    assert run({"model": "claude-opus-5", "prompt": "x"}) is None


def test_a_dispatch_naming_no_model_is_left_alone(tmp_path):
    # This is how an agent definition's own pinned model reaches the subagent.
    assert run({"prompt": "x"}) is None


def test_an_unrecognised_model_is_raised_not_trusted(tmp_path):
    # Allowlist, not denylist: a cheap tier released after this file was written must not pass
    # simply by being absent from a list.
    r = run({"model": "claude-tiny-7", "prompt": "x"})
    assert r["hookSpecificOutput"]["updatedInput"]["model"] == "sonnet"


def test_the_message_names_what_was_replaced(tmp_path):
    # The point is that the substitution is visible. A silent override is how someone comes to
    # believe they ran on a model they did not.
    r = run({"model": "haiku", "prompt": "x"})
    assert "haiku" in r["systemMessage"] and "sonnet" in r["systemMessage"]


def test_it_ignores_tools_that_are_not_agent_dispatches(tmp_path):
    assert run({"model": "haiku", "command": "ls"}, tool_name="Bash") is None


def test_the_task_alias_is_covered(tmp_path):
    r = run({"model": "haiku", "prompt": "x"}, tool_name="Task")
    assert r["hookSpecificOutput"]["updatedInput"]["model"] == "sonnet"


def test_the_off_switch_disables_it(tmp_path):
    import os
    env = dict(os.environ, ORCLAB_MODEL_FLOOR_OFF="1")
    assert run({"model": "haiku", "prompt": "x"}, env=env) is None


def test_malformed_input_fails_open_rather_than_wedging_every_subagent(tmp_path):
    out = subprocess.run([sys.executable, FLOOR], input="not json",
                         capture_output=True, text=True)
    assert out.returncode == 0
    assert out.stdout.strip() == ""
