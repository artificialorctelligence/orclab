# skills/orc-test/scripts/tests/test_runner.py
import sys

from orc_test.runner import run


def test_run_prints_command_and_captures_output(capsys, tmp_path):
    cp = run([sys.executable, "-c", "print('hi'); raise SystemExit(3)"], cwd=tmp_path)
    assert cp.returncode == 3
    assert cp.stdout.strip() == "hi"
    assert capsys.readouterr().out.startswith("$ ")


def test_run_missing_binary_does_not_raise(tmp_path):
    cp = run(["definitely-not-a-real-binary-xyz"], cwd=tmp_path)
    assert cp.returncode == 127
    assert "not found" in cp.stdout
