"""The template is copied into a consuming project, never imported by Orclab. What Orclab can
prove about it: after placeholder substitution it is valid Python, its --help runs, and its
--check answers the one-time-setup question without launchpadlib installed and without ever
creating a credential."""

import pathlib
import subprocess
import sys

TEMPLATE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "ingredients" / "ppa" / "templates" / "ppa-copy-series.py"
)
FILLED = {
    "__OWNER__": "someone", "__PPA__": "theirppa", "__SOURCE__": "theirpkg",
    "__FROM_SERIES__": "noble", "__TO_SERIES__": "resolute",
}


def instantiate(tmp_path):
    text = TEMPLATE.read_text()
    for placeholder, value in FILLED.items():
        text = text.replace(placeholder, value)
    assert "__" not in text.replace("__main__", "").replace("__name__", ""), \
        "every placeholder must be one of the five documented ones"
    out = tmp_path / "ppa-copy-series.py"
    out.write_text(text)
    return out


def run(script, *args, home, extra_env=None):
    # PYTHONPATH cleared and a fake HOME: launchpadlib must not be needed for these paths,
    # and nothing may be written into the real home directory.
    env = {"HOME": str(home), "PATH": "/usr/bin:/bin"}
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, "-S", str(script), *args],
        capture_output=True, text=True, env=env,
    )


def test_help_runs_without_launchpadlib(tmp_path):
    script = instantiate(tmp_path)
    out = run(script, "--help", home=tmp_path)
    assert out.returncode == 0, out.stderr
    assert "--check" in out.stdout and "--dry-run" in out.stdout


def test_check_reports_no_credentials_and_creates_nothing(tmp_path):
    script = instantiate(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    out = run(script, "--check", home=home)
    assert out.returncode == 1
    assert "no launchpad credentials" in out.stderr
    assert not list(home.rglob("*")), "--check must never create a file, let alone a credential"


def test_check_passes_when_a_credential_file_exists(tmp_path):
    script = instantiate(tmp_path)
    creds = tmp_path / "creds.txt"
    creds.write_text("not-a-real-token")
    out = run(script, "--check", "--credentials", str(creds), home=tmp_path)
    assert out.returncode == 0
    assert "credentials present" in out.stdout
    assert "not-a-real-token" not in out.stdout + out.stderr, "never print the credential"


def test_the_default_credentials_path_is_per_project_under_xdg_config(tmp_path):
    script = instantiate(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    out = run(script, "--check", home=home)
    assert str(home / ".config" / "theirpkg" / "launchpad-credentials.txt") in out.stderr

    xdg = tmp_path / "xdg"
    out = run(script, "--check", home=home, extra_env={"XDG_CONFIG_HOME": str(xdg)})
    assert str(xdg / "theirpkg" / "launchpad-credentials.txt") in out.stderr
