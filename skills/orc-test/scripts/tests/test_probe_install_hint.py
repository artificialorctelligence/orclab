"""The install command Orclab prints has to be one the machine will actually accept.

`pip install X` is refused outright on Debian and Ubuntu (PEP 668), which is what Orclab's own
machine runs — so the hint it printed for pytest, mutmut and pip-audit was a command that could
not work, every time (BACKLOG #84).
"""

from __future__ import annotations

import sys

import pytest
from orc_test import probe


@pytest.fixture
def machine(monkeypatch, tmp_path):
    """Describe a machine: no container, a chosen prefix, and whether PEP 668 marks it."""

    def build(*, externally_managed=False, venv=False, container=False):
        monkeypatch.setattr(probe.runner, "active", lambda: object() if container else None)
        prefix = tmp_path / "prefix"
        lib = prefix / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"
        lib.mkdir(parents=True, exist_ok=True)
        if externally_managed:
            (lib / "EXTERNALLY-MANAGED").write_text("")
        monkeypatch.setattr(sys, "prefix", str(prefix))
        monkeypatch.setattr(sys, "base_prefix", str(tmp_path / "other") if venv else str(prefix))

    return build


def test_a_plain_system_python_gets_a_plain_pip_install(machine):
    machine()
    assert probe.pip_install("mutmut") == "pip install mutmut"


def test_a_virtualenv_gets_a_plain_pip_install_even_when_the_base_is_managed(machine):
    """Inside a venv pip may write freely — the marker on the base interpreter is irrelevant."""
    machine(externally_managed=True, venv=True)
    assert probe.pip_install("mutmut") == "pip install mutmut"


def test_an_externally_managed_python_never_gets_a_command_pip_would_refuse(machine):
    machine(externally_managed=True)
    hint = probe.pip_install("mutmut")
    assert "--break-system-packages" in hint and "--user" in hint
    assert "~/.local" in hint, "the flag's name frightens people; say what it really does"


def test_inside_a_container_it_says_the_image_not_a_pip_command(machine):
    """A pip install inside the run container is gone the moment the container is."""
    machine(container=True)
    hint = probe.pip_install("mutmut")
    assert "container image" in hint
    assert not hint.startswith("pip install")


@pytest.mark.parametrize(
    "hint",
    ["install a JDK (https://adoptium.net)", "install Node.js (https://nodejs.org) — npx ships with npm",
     "https://getcomposer.org/download/"],
    ids=["jdk", "node", "composer"],
)
def test_a_non_pip_hint_is_left_exactly_as_its_language_module_wrote_it(hint, machine):
    machine(externally_managed=True)
    assert probe.pip_install_hint(hint) == hint


def test_a_pip_hint_is_rewritten_for_this_machine(machine):
    machine(externally_managed=True)
    assert probe.pip_install_hint("pip install pytest-cov").startswith("pip install --user")


def test_the_rewrite_keeps_the_package_name(machine):
    machine()
    assert probe.pip_install_hint("pip install pip-audit") == "pip install pip-audit"
