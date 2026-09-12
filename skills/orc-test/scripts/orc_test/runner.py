"""One place every external command goes through, so every one is printed before it runs."""

import shlex
import subprocess


def run(cmd, cwd, env=None):
    print("$ " + shlex.join(cmd), flush=True)
    try:
        return subprocess.run(cmd, cwd=str(cwd), env=env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        return subprocess.CompletedProcess(cmd, 127, stdout=f"{cmd[0]}: not found\n", stderr="")
