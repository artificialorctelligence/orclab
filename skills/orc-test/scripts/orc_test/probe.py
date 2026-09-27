"""Is a tool present where the project's commands run? On the host, the cheap checks; inside a
container (v23), a command through the same chokepoint the tools run through — "missing" then
means missing where it matters, not on the developer's machine."""

import importlib.util
import pathlib
import shlex
import shutil
import sys

from . import runner


def which(tool):
    if runner.active() is None:
        return shutil.which(tool) is not None
    return runner.run(["sh", "-c", f"command -v {shlex.quote(tool)}"], cwd=runner.active().root).returncode == 0


def python_module(name):
    if runner.active() is None:
        return importlib.util.find_spec(name) is not None
    return runner.run(["python3", "-c", f"import {name}"], cwd=runner.active().root).returncode == 0


def pip_install(package):
    """The install command that will actually work here, for `package`.

    `pip install X` is refused outright on Debian and Ubuntu since PEP 668: those ship
    /usr/lib/pythonX.Y/EXTERNALLY-MANAGED to stop pip breaking the system Python, and the error
    names no way forward that Orclab can predict. Printing a command the machine rejects is worse
    than printing nothing, so the marker is read rather than assumed (BACKLOG #84).

    pipx is deliberately not offered: Orclab invokes these as `python3 -m mutmut` and
    `python3 -m pip_audit`, and pipx puts an application on PATH without putting its module on
    the import path, so a pipx install would satisfy the human and not the caller.
    """
    if runner.active() is not None:
        return f"add {package} to the container image — a pip install inside it dies with the container"
    if sys.prefix != sys.base_prefix:
        return f"pip install {package}"            # a virtualenv: pip is free to write into it
    if pathlib.Path(sys.prefix, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}",
                    "EXTERNALLY-MANAGED").exists():
        return (f"pip install --user --break-system-packages {package}"
                " (--break-system-packages only permits writing to your own ~/.local; it does not"
                " touch system packages, despite the name)")
    return f"pip install {package}"


def pip_install_hint(hint):
    """A language module's install hint, corrected for this machine when it is a pip one.

    Language modules state their hint as a constant (`TOOLS`, `AUDIT_TOOL`), so they cannot ask
    the machine anything at import time. Every non-pip hint - a JDK, Node, composer - is returned
    untouched; only `pip install <pkg>` is re-rendered, because that is the only one that is
    outright refused on a PEP 668 system.
    """
    prefix = "pip install "
    return pip_install(hint[len(prefix):].strip()) if hint.startswith(prefix) else hint
