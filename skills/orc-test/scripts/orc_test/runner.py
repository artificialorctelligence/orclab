"""One place every external command goes through, so every one is printed before it runs — and,
for a containerised project (v23), the one place the `compose run` prefix is added."""

import shlex
import subprocess

from . import container

_ACTIVE = None


def use(c):
    """Every later run() goes through `c` (a container.Container), or the host when None."""
    global _ACTIVE
    _ACTIVE = c


def active():
    return _ACTIVE


def run(cmd, cwd, env=None, input=None):
    if _ACTIVE is not None:
        cmd, cwd = container.wrap(_ACTIVE, cmd, cwd), _ACTIVE.root   # compose reads compose.yaml from cwd
    return run_on_host(cmd, cwd, env=env, input=input)


def run_on_host(cmd, cwd, env=None, input=None):
    """Never wrapped: git, and anything else that is the host's business even when a container
    is active."""
    print("$ " + shlex.join(cmd), flush=True)
    try:
        return subprocess.run(cmd, check=False, cwd=str(cwd), env=env, input=input, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        return subprocess.CompletedProcess(cmd, 127, stdout=f"{cmd[0]}: not found\n", stderr="")
