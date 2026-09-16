"""Loads an ingredient template as a module, in this process, so a test can call its functions
and coverage and mutation testing both see it. The templates are copied into consuming projects
and never imported by Orclab itself, which is why nothing else here imports them by name.

The path is taken relative to this file: from the real tree that is the real template; under
`/orc-test analyze` (mutmut runs from skills/orc-package/ and copies scripts/tests/ next to its
mutated copy of ingredients/) the same arithmetic lands on the mutated copy. The module name is
what mutmut derives from that relative path, which is how its trampoline matches a mutant to
the module it was made from."""

import importlib.util
import pathlib
import sys
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]  # skills/orc-package, or its mutants/ copy


def _load(relative, fake_modules):
    path = ROOT / relative
    name = relative[: -len(".py")].replace("/", ".")
    for modname, fake in fake_modules.items():
        sys.modules[modname] = fake
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def load_template():
    """For a test that has to set the environment before the template's import-time code runs."""
    return lambda relative: _load(relative, {})


@pytest.fixture
def ppa_template(monkeypatch, tmp_path):
    """ppa-copy-series.py, with launchpadlib absent: its imports are inside the two login
    functions, and a test that reaches those installs its own fake first."""
    monkeypatch.setitem(sys.modules, "launchpadlib", None)  # ImportError if anything imports it
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    return _load("ingredients/ppa/templates/ppa-copy-series.py", {})


@pytest.fixture
def fake_jwt(monkeypatch):
    """Stands in for PyJWT: records what encode() was asked to sign and returns a token."""
    calls = []
    fake = types.ModuleType("jwt")

    def encode(payload, key, algorithm=None, headers=None):
        calls.append({"payload": payload, "key": key, "algorithm": algorithm, "headers": headers})
        return "signed.jwt.token"

    fake.encode = encode
    fake.calls = calls
    monkeypatch.setitem(sys.modules, "jwt", fake)
    return fake


@pytest.fixture
def appstore_template(fake_jwt, monkeypatch):
    """appstore-status.py, importing the fake jwt above rather than PyJWT."""
    return _load("ingredients/app-store/templates/appstore-status.py", {"jwt": fake_jwt})
