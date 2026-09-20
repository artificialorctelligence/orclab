"""Is a tool present where the project's commands run? On the host, the cheap checks; inside a
container (v23), a command through the same chokepoint the tools run through — "missing" then
means missing where it matters, not on the developer's machine."""

import importlib.util
import shutil

from . import runner


def which(tool):
    if runner.active() is None:
        return shutil.which(tool) is not None
    return runner.run(["sh", "-c", f"command -v {tool}"], cwd=runner.active().root).returncode == 0


def python_module(name):
    if runner.active() is None:
        return importlib.util.find_spec(name) is not None
    return runner.run(["python3", "-c", f"import {name}"], cwd=runner.active().root).returncode == 0
