"""Which mechanism gets chosen, and what is said when none exists.

The capture itself needs a real screen, so these tests pin the part that can be wrong on a
machine nobody here can run: the branch taken per platform, and whether a missing tool produces
a message that names what to install.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import screenshot

WINDOW_RECT = {"x": 10, "y": 20, "width": 800, "height": 480}


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


# --- listing windows, per desktop ---------------------------------------------------------


def test_list_windows_on_x11_takes_the_title_after_wmctrls_three_columns(tools, monkeypatch):
    present, _ = tools
    present.add("wmctrl")
    monkeypatch.setattr(screenshot, "session", lambda: "x11")
    monkeypatch.setattr(
        screenshot,
        "run",
        lambda cmd, tolerate=(): "0x03400004  0 Matrix Firefox\n0x0300000f  0 Matrix Head Unit\n",
    )
    assert screenshot.list_windows() == ["Firefox", "Head Unit"]


SWAY_TREE = {
    "name": "root",
    "nodes": [
        {"name": "workspace", "nodes": [{"name": "Orcweather", "pid": 42, "rect": WINDOW_RECT}]},
        {"name": "scratch", "floating_nodes": [{"name": "Notes", "pid": 43, "rect": WINDOW_RECT}]},
    ],
}


def test_list_windows_on_sway_walks_tiled_and_floating_windows(tools, monkeypatch):
    present, _ = tools
    present.add("swaymsg")
    monkeypatch.setattr(screenshot, "session", lambda: "wayland")
    monkeypatch.setattr(screenshot, "run", lambda cmd, tolerate=(): json.dumps(SWAY_TREE))
    # "workspace" and "root" have no pid, so they are containers rather than windows.
    assert screenshot.list_windows() == ["Orcweather", "Notes"]


def test_list_windows_on_macos_splits_the_osascript_list(tools, monkeypatch):
    present, _ = tools
    present.add("osascript")
    monkeypatch.setattr(screenshot, "session", lambda: "macos")
    monkeypatch.setattr(screenshot, "run", lambda cmd, tolerate=(): "Finder, Safari , Xcode")
    assert screenshot.list_windows() == ["Finder", "Safari", "Xcode"]


def test_list_windows_is_empty_when_the_desktop_offers_no_way_to_ask(tools, monkeypatch):
    monkeypatch.setattr(screenshot, "session", lambda: "wayland")
    assert screenshot.list_windows() == []


# --- wayland capture ----------------------------------------------------------------------


def test_grim_captures_the_whole_screen_without_a_compositor_query(tools, tmp_path, monkeypatch):
    present, calls = tools
    present.add("grim")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "sway")
    assert screenshot.capture_wayland(tmp_path / "o.png", None) == "grim"
    assert calls[-1][0] == "grim" and "-g" not in calls[-1]


def test_grim_needs_swaymsg_to_find_one_window(tools, tmp_path, monkeypatch):
    present, _ = tools
    present.add("grim")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "sway")
    with pytest.raises(screenshot.CaptureError, match="install swaymsg"):
        screenshot.capture_wayland(tmp_path / "o.png", "Orcweather")


def test_grim_is_given_the_geometry_swaymsg_reports(tools, tmp_path, monkeypatch):
    present, calls = tools
    present.update({"grim", "swaymsg"})
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "sway")
    monkeypatch.setattr(
        screenshot,
        "run",
        lambda cmd, tolerate=(): calls.append(cmd) or json.dumps(SWAY_TREE),
    )
    assert screenshot.capture_wayland(tmp_path / "o.png", "orcweather") == "grim+swaymsg"
    assert calls[-1][:3] == ["grim", "-g", "10,20 800x480"]


def test_sway_geometry_says_which_title_it_could_not_find(tools, monkeypatch):
    monkeypatch.setattr(screenshot, "run", lambda cmd, tolerate=(): json.dumps(SWAY_TREE))
    with pytest.raises(screenshot.CaptureError, match="no window matching 'Nothing'"):
        screenshot.sway_geometry("Nothing")


# --- macOS --------------------------------------------------------------------------------


def test_macos_without_screencapture_is_not_a_normal_macos(tools, tmp_path):
    with pytest.raises(screenshot.CaptureError, match="not a normal macOS"):
        screenshot.capture_macos(tmp_path / "o.png", None)


def test_macos_full_screen_suppresses_the_shutter(tools, tmp_path):
    present, calls = tools
    present.add("screencapture")
    assert screenshot.capture_macos(tmp_path / "o.png", None) == "screencapture"
    assert "-x" in calls[-1], "a capture nobody is watching should not make a noise"


def test_macos_window_capture_crops_to_the_bounds_osascript_reports(tools, tmp_path, monkeypatch):
    present, calls = tools
    present.update({"screencapture", "osascript"})
    monkeypatch.setattr(
        screenshot, "run", lambda cmd, tolerate=(): calls.append(cmd) or "10, 20, 800, 480"
    )
    assert screenshot.capture_macos(tmp_path / "o.png", "Orcweather") == "screencapture -R"
    assert calls[-1][:4] == ["screencapture", "-x", "-R", "10,20,800,480"]


def test_macos_names_the_permission_when_the_bounds_come_back_wrong(tools, tmp_path, monkeypatch):
    """An app without Accessibility access returns nothing useful, which is not a crash."""
    present, _ = tools
    present.update({"screencapture", "osascript"})
    monkeypatch.setattr(screenshot, "run", lambda cmd, tolerate=(): "")
    with pytest.raises(screenshot.CaptureError, match="Accessibility"):
        screenshot.capture_macos(tmp_path / "o.png", "Orcweather")


# --- Windows ------------------------------------------------------------------------------


def test_windows_uses_powershell_and_falls_back_to_pwsh(tools, tmp_path):
    present, calls = tools
    present.add("powershell")
    assert screenshot.capture_windows(tmp_path / "o.png", None) == "powershell"
    assert calls[-1][0] == "powershell"

    present.remove("powershell")
    present.add("pwsh")
    screenshot.capture_windows(tmp_path / "o.png", None)
    assert calls[-1][0] == "pwsh"


def test_windows_with_no_shell_at_all_says_which_two_it_looked_for(tools, tmp_path):
    with pytest.raises(screenshot.CaptureError, match="neither powershell nor pwsh"):
        screenshot.capture_windows(tmp_path / "o.png", None)


# --- dispatch and the command line ----------------------------------------------------------


@pytest.mark.parametrize("kind", ["x11", "wayland", "macos", "windows"])
def test_capture_dispatches_to_the_backend_for_this_session(kind, tmp_path, monkeypatch):
    """BACKENDS binds the functions at import, so the dict is what a test must patch."""
    monkeypatch.setattr(screenshot, "session", lambda: kind)
    monkeypatch.setitem(screenshot.BACKENDS, kind, lambda out, title: f"{kind}-was-called")
    assert screenshot.capture(tmp_path / "o.png", None) == f"{kind}-was-called"


def test_main_prints_the_path_and_the_real_size(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(screenshot, "capture", lambda out, title: "import")
    monkeypatch.setattr(screenshot, "png_size", lambda path: (800, 480))
    out = tmp_path / "shot.png"
    assert screenshot.main([str(out)]) == 0
    printed = capsys.readouterr().out
    assert "800x480" in printed and "via import" in printed and str(out) in printed


def test_main_creates_the_output_directory_rather_than_failing_on_it(tmp_path, monkeypatch):
    monkeypatch.setattr(screenshot, "capture", lambda out, title: "import")
    monkeypatch.setattr(screenshot, "png_size", lambda path: (1, 1))
    nested = tmp_path / "a" / "b" / "shot.png"
    assert screenshot.main([str(nested)]) == 0
    assert nested.parent.is_dir()


def test_main_passes_the_window_title_through(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(
        screenshot, "capture", lambda out, title: seen.update(title=title) or "import"
    )
    monkeypatch.setattr(screenshot, "png_size", lambda path: (1, 1))
    screenshot.main(["--window", "Head Unit", str(tmp_path / "o.png")])
    assert seen["title"] == "Head Unit"


def test_main_reports_a_failure_on_stderr_and_exits_nonzero(tmp_path, monkeypatch, capsys):
    def boom(out, title):
        raise screenshot.CaptureError("no window matching 'X'; try --list")

    monkeypatch.setattr(screenshot, "capture", boom)
    assert screenshot.main([str(tmp_path / "o.png")]) == 1
    captured = capsys.readouterr()
    assert "screenshot failed: no window matching" in captured.err
    assert captured.out == "", "a failure must not also print a path"


def test_main_list_prints_one_title_per_line(monkeypatch, capsys):
    monkeypatch.setattr(screenshot, "list_windows", lambda: ["Firefox", "Head Unit"])
    assert screenshot.main(["--list"]) == 0
    assert capsys.readouterr().out == "Firefox\nHead Unit\n"


def test_main_list_on_a_desktop_that_will_not_say_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr(screenshot, "list_windows", list)
    monkeypatch.setattr(screenshot, "session", lambda: "wayland")
    assert screenshot.main(["--list"]) == 1
    assert "will not list windows" in capsys.readouterr().err


def test_run_turns_a_missing_binary_into_a_capture_error():
    with pytest.raises(screenshot.CaptureError, match="definitely-not-a-real-binary"):
        screenshot.run(["definitely-not-a-real-binary-xyzzy"])
