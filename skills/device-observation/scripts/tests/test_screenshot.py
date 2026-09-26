"""Which mechanism gets chosen, and what is said when none exists.

The capture itself needs a real screen, so these tests pin the part that can be wrong on a
machine nobody here can run: the branch taken per platform, and whether a missing tool produces
a message that names what to install.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import screenshot


@pytest.fixture
def tools(monkeypatch):
    """Control which tools exist, and record the commands that would have run."""
    present: set[str] = set()
    calls: list[list[str]] = []

    def fake_have(tool):
        return tool in present

    def fake_run(cmd, tolerate=()):
        calls.append(cmd)
        return ""

    monkeypatch.setattr(screenshot, "have", fake_have)
    monkeypatch.setattr(screenshot, "run", fake_run)
    return present, calls


def test_session_reads_the_environment(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert screenshot.session() == "wayland"

    monkeypatch.setenv("XDG_SESSION_TYPE", "X11")  # case is not guaranteed
    assert screenshot.session() == "x11"


def test_session_falls_back_to_the_display_variables(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")
    assert screenshot.session() == "x11"

    monkeypatch.delenv("DISPLAY")
    assert screenshot.session() == "unknown"


def test_headless_says_so_instead_of_picking_a_backend(monkeypatch, tmp_path):
    monkeypatch.setattr(screenshot, "session", lambda: "unknown")
    with pytest.raises(screenshot.CaptureError, match="no graphical session"):
        screenshot.capture(tmp_path / "out.png", None)


def test_x11_prefers_imagemagick_then_maim_then_scrot(tools, tmp_path):
    present, calls = tools
    present.update({"import", "maim", "scrot"})
    assert screenshot.capture_x11(tmp_path / "o.png", None) == "import"

    present.remove("import")
    calls.clear()
    assert screenshot.capture_x11(tmp_path / "o.png", None) == "maim"

    present.remove("maim")
    assert screenshot.capture_x11(tmp_path / "o.png", None) == "scrot"


def test_x11_with_no_capture_tool_names_all_three(tools, tmp_path):
    with pytest.raises(screenshot.CaptureError, match="ImageMagick, maim or scrot"):
        screenshot.capture_x11(tmp_path / "o.png", None)


def test_x11_window_capture_needs_xdotool_and_says_so(tools, tmp_path):
    present, _ = tools
    present.add("import")
    with pytest.raises(screenshot.CaptureError, match="install xdotool"):
        screenshot.capture_x11(tmp_path / "o.png", "Some Window")


def test_x11_window_id_is_passed_to_the_capture_tool(tools, tmp_path, monkeypatch):
    present, calls = tools
    present.update({"xdotool", "import"})
    monkeypatch.setattr(screenshot, "run", lambda cmd, tolerate=(): calls.append(cmd) or "12345\n")
    screenshot.capture_x11(tmp_path / "o.png", "Head Unit")
    assert calls[-1][:3] == ["import", "-window", "12345"]


def test_gnome_wayland_is_told_to_use_x11_rather_than_left_guessing(tools, tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    with pytest.raises(screenshot.CaptureError, match="waits for a human"):
        screenshot.capture_wayland(tmp_path / "o.png", "Anything")


def test_spectacle_is_not_used_on_gnome_even_when_it_is_installed(tools, tmp_path, monkeypatch):
    """A KDE tool on GNOME falls through to the portal and blocks. Fail clearly instead."""
    present, calls = tools
    present.add("spectacle")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "ubuntu:GNOME")
    with pytest.raises(screenshot.CaptureError, match="waits for a human"):
        screenshot.capture_wayland(tmp_path / "o.png", None)
    assert calls == [], "spectacle must not be invoked on GNOME"


def test_spectacle_is_used_on_kde(tools, tmp_path, monkeypatch):
    present, calls = tools
    present.add("spectacle")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    assert screenshot.capture_wayland(tmp_path / "o.png", None) == "spectacle"
    assert calls[-1][0] == "spectacle"


def test_an_unknown_wayland_desktop_names_both_real_options(tools, tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "something-nobody-has-heard-of")
    with pytest.raises(screenshot.CaptureError, match=r"install grim.*install spectacle"):
        screenshot.capture_wayland(tmp_path / "o.png", None)


def test_desktop_prefers_the_standard_variable(monkeypatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    monkeypatch.setenv("DESKTOP_SESSION", "plasmawayland")
    assert screenshot.desktop() == "kde"

    monkeypatch.delenv("XDG_CURRENT_DESKTOP")
    monkeypatch.delenv("XDG_SESSION_DESKTOP", raising=False)
    assert screenshot.desktop() == "plasmawayland"


def test_windows_refuses_a_window_instead_of_capturing_the_wrong_thing(tools, tmp_path):
    present, _ = tools
    present.add("powershell")
    with pytest.raises(screenshot.CaptureError, match="not implemented on Windows"):
        screenshot.capture_windows(tmp_path / "o.png", "Some Window")


def test_png_size_reads_the_header(tmp_path):
    png = tmp_path / "real.png"
    png.write_bytes(
        screenshot.PNG_SIGNATURE + b"\x00\x00\x00\rIHDR" + struct.pack(">II", 800, 480)
    )
    assert screenshot.png_size(png) == (800, 480)


@pytest.mark.parametrize(
    "content", [b"", b"not a png at all", screenshot.PNG_SIGNATURE], ids=["empty", "junk", "truncated"]
)
def test_png_size_rejects_anything_that_is_not_a_whole_png(tmp_path, content):
    bad = tmp_path / "bad.png"
    bad.write_bytes(content)
    with pytest.raises(screenshot.CaptureError, match="not a PNG"):
        screenshot.png_size(bad)


def test_png_size_rejects_a_file_that_was_never_written(tmp_path):
    with pytest.raises(screenshot.CaptureError, match="not a PNG"):
        screenshot.png_size(tmp_path / "missing.png")


def test_run_tolerates_the_exit_codes_it_is_given():
    assert screenshot.run([sys.executable, "-c", "raise SystemExit(1)"], tolerate=(1,)) == ""
    with pytest.raises(screenshot.CaptureError, match="exited 1"):
        screenshot.run([sys.executable, "-c", "raise SystemExit(1)"])
