"""One place every external command goes through, so every one is printed before it runs — and,
for a containerised project (v23), the one place the `compose run` prefix is added."""

import os
import re
import shlex
import subprocess
import sys
import time

from . import container

_ACTIVE = None


def use(c):
    """Every later run() goes through `c` (a container.Container), or the host when None."""
    global _ACTIVE
    _ACTIVE = c


def active():
    return _ACTIVE


def run(cmd, cwd, env=None, input=None, stream=False, progress=None):
    if _ACTIVE is not None:
        cmd, cwd = container.wrap(_ACTIVE, cmd, cwd), _ACTIVE.root   # compose reads compose.yaml from cwd
    return run_on_host(cmd, cwd, env=env, input=input, stream=stream, progress=progress)


def _eta(done, total, done0, t0, now):
    """`~2m 40s` from the rate seen since the first counter reading (done0 at t0) — not since the
    run started, because an incremental run opens on the cached count. "" until there is a rate.
    ponytail: whole-run average — mutmut runs its estimated-fastest mutants first, so the early
    figure reads low and climbs; a recent-window rate if that ever misleads someone."""
    if done <= done0 or total <= 0:
        return ""
    left = (total - done) * (now - t0) / (done - done0)
    m, s = divmod(round(left), 60)
    return f"~{m}m {s}s" if m else f"~{s}s"


def run_on_host(cmd, cwd, env=None, input=None, stream=False, progress=None):
    """Never wrapped: git, and anything else that is the host's business even when a container
    is active. `stream=True` also echoes the tool's output as it arrives — the mutation tools'
    own progress bars and ETAs (mutation_test's `Total [###  ] 34% ~2m 40s`, Infection's
    `.M.S..` line), which a captured run showed only minutes later, or never (BACKLOG #73);
    `cmd` must not read stdin, so `input` is not streamed. `progress` is a regex with `done`
    and `total` groups for a tool whose counter carries no ETA (mutmut's `⠋ 312/625 🎉 …`): the
    runner appends `~2m 40s` after each rewrite of that line, on the terminal only, never in
    the captured stdout."""
    print("$ " + shlex.join(cmd), flush=True)
    if _ACTIVE is not None:
        # compose.yaml's `${PWD}` is read from the environment, and `cwd=` does not rewrite the
        # inherited PWD (it is the shell's, wrong under --cwd): set it to the project root
        env = {**(env if env is not None else os.environ), "PWD": str(_ACTIVE.root)}
    try:
        if not stream:
            return subprocess.run(cmd, check=False, cwd=str(cwd), env=env, input=input, text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert input is None, "stream=True cannot feed stdin"
        with subprocess.Popen(cmd, cwd=str(cwd), env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT) as p:
            chunks, first, eta_len = [], None, 0
            # bytes as they come, not lines: a progress bar is one \r-rewritten line for minutes
            while chunk := os.read(p.stdout.fileno(), 4096):
                chunks.append(chunk)
                text = chunk.decode(errors="replace")
                sys.stdout.write(text)
                # the tool's latest counter is its last line: after the last \r (mutmut rewrites
                # one line) or \n (Infection prints one per fifty mutants)
                if progress and (m := progress.match(re.split(r"[\r\n]", text.rstrip("\r\n"))[-1])):
                    done, total, now = int(m["done"]), int(m["total"]), time.monotonic()
                    first = first or (done, now)
                    eta = _eta(done, total, *first, now)
                    sys.stdout.write(f" {eta}".ljust(eta_len) if eta else "")   # overwrite a longer, older one
                    eta_len = max(eta_len, len(eta) + 1)
                sys.stdout.flush()
        return subprocess.CompletedProcess(cmd, p.returncode, stdout=b"".join(chunks).decode(errors="replace"), stderr="")
    except FileNotFoundError:
        return subprocess.CompletedProcess(cmd, 127, stdout=f"{cmd[0]}: not found\n", stderr="")
