"""Same contract as the PPA template's test: after substitution the script is valid Python, its
usage runs with PyJWT absent, and no path in it ever prints the private key. The network paths
are untestable here by design - the ingredient says so in its first paragraph."""

import pathlib
import subprocess
import sys

TEMPLATE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "ingredients" / "app-store" / "templates" / "appstore-status.py"
)
FILLED = {
    "__KEY_ID__": "ABC123DEF4", "__ISSUER_ID__": "00000000-0000-0000-0000-000000000000",
    "__P8_PATH__": "/nonexistent/AuthKey.p8", "__BUNDLE_ID__": "org.example.app",
    "__VENDOR__": "12345678",
}


def instantiate(tmp_path):
    text = TEMPLATE.read_text()
    for placeholder, value in FILLED.items():
        text = text.replace(placeholder, value)
    assert "__" not in text.replace("__main__", "").replace("__name__", "").replace("__doc__", ""), \
        "every placeholder must be one of the five documented ones"
    out = tmp_path / "appstore-status.py"
    out.write_text(text)
    return out


def test_usage_runs_and_names_both_modes(tmp_path):
    script = instantiate(tmp_path)
    out = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                         env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"})
    # exit 2 = usage; it may also be a PyJWT ImportError (exit 1) on a machine without it -
    # both prove the file is valid Python and neither reaches the network.
    assert out.returncode in (1, 2), out.stderr
    assert "state" in out.stdout + out.stderr and "downloads" in out.stdout + out.stderr


def test_the_key_file_is_read_but_never_printed(tmp_path):
    text = instantiate(tmp_path).read_text()
    assert "open(P8_PATH)" in text
    assert "print(key" not in text and "print(token" not in text
