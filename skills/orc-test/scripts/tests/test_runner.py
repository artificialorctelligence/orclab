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


def test_run_feeds_input_to_stdin(tmp_path):
    cp = run([sys.executable, "-c", "import sys; print(sys.stdin.read().upper())"], cwd=tmp_path, input="hi")
    assert cp.stdout.strip() == "HI"


def test_run_stream_echoes_output_as_it_arrives_and_still_captures_it(capsys, tmp_path):
    # The mutation step streams so the tool's own progress bar (\r-rewritten, no newline for
    # minutes) reaches the terminal; the captured stdout is unchanged for the parsers (BACKLOG #73).
    cp = run([sys.executable, "-c",
              "import sys; sys.stdout.write('File [##  ] 40%\\r'); sys.stdout.flush(); print('done'); raise SystemExit(255)"],
             cwd=tmp_path, stream=True)
    assert cp.returncode == 255
    assert cp.stdout == "File [##  ] 40%\rdone\n"
    out = capsys.readouterr().out
    assert out.startswith("$ ") and out.endswith("File [##  ] 40%\rdone\n")


def test_run_stream_appends_eta_when_progress_regex_reads_done_of_total(capsys, tmp_path):
    # mutmut prints `N/total …` but never an ETA; the runner appends one from the rate it observes
    import re
    from orc_test import runner
    progress = re.compile(r"^\S+ (?P<done>\d+)/(?P<total>\d+) ")
    cp = run([sys.executable, "-c",
              "import sys,time; sys.stdout.write('\\r⠋ 1/4 x'); sys.stdout.flush(); time.sleep(0.3);"
              " sys.stdout.write('\\r⠙ 3/4 x'); sys.stdout.flush(); print()"],
             cwd=tmp_path, stream=True, progress=progress)
    assert cp.stdout == "\r⠋ 1/4 x\r⠙ 3/4 x\n"          # the capture stays the tool's own text
    assert re.search(r"3/4 x ~\d+s", capsys.readouterr().out)
    assert runner._eta(done=1, total=4, done0=1, t0=0.0, now=5.0) == ""      # no rate yet
    assert runner._eta(done=3, total=4, done0=1, t0=0.0, now=10.0) == "~5s"  # 2 in 10s, 1 left
    assert runner._eta(done=3, total=203, done0=1, t0=0.0, now=2.0) == "~3m 20s"


def test_mutation_progress_regexes_read_each_tool_s_real_line():
    from orc_test.langs import php, python
    m = python.MUTATION_PROGRESS.match("⠋ 312/625  🎉 280 🫥 0  ⏰ 1  🤔 0  🙁 31  🔇 0  🧙 0")
    assert (m["done"], m["total"]) == ("312", "625")
    m = php.MUTATION_PROGRESS.match("IIII............MM.U   ( 50 / 407)")
    assert (m["done"], m["total"]) == ("50", "407")
