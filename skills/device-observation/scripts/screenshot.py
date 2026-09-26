#!/usr/bin/env python3
"""Capture a desktop window, or the whole screen, on whatever desktop this is.

A device photographs itself (`adb shell screencap`, `xcrun simctl io`), so this exists only for
windows that are genuinely the desktop's own - a Qt or Electron app, a desktop build of a mobile
app, an emulator's own chrome. There is no portable way to do that, so this picks whichever
mechanism the machine actually has and says plainly what to install when it has none.

    python3 screenshot.py out.png                    # the whole screen
    python3 screenshot.py --window 'Orcweather'      # one window, by title
    python3 screenshot.py --list                     # what windows are open

It always ends by reading back the file it wrote and printing the real dimensions, because a
backend that exits 0 and leaves a truncated or empty file is the failure worth catching.

Only the Linux/X11 backends have been run for real (2026-09-26). The macOS, Windows and Wayland
branches are written from each tool's own documented interface and have not been executed; the
backend-selection logic is what the test suite covers on every platform.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
TIMEOUT_SECONDS = 30


class CaptureError(Exception):
    """A backend was chosen and could not produce an image."""


def have(tool: str) -> bool:
    """True when `tool` is on PATH."""
    return shutil.which(tool) is not None


def run(cmd: list[str], tolerate: tuple[int, ...] = ()) -> str:
    """Run `cmd`, returning stdout. Raises CaptureError on failure.

    `tolerate` lists exit codes that mean "nothing found" rather than "broken" - xdotool
    exits 1 on an empty search, and that deserves this script's own message, not the tool's.
    """
    try:
        done = subprocess.run(
            cmd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CaptureError(f"{cmd[0]}: {exc}") from exc
    if done.returncode not in (0, *tolerate):
        detail = (done.stderr or done.stdout).strip().splitlines()
        raise CaptureError(f"{cmd[0]} exited {done.returncode}: {detail[-1] if detail else '?'}")
    return done.stdout


def session() -> str:
    """Which windowing system this is: 'x11', 'wayland', 'macos', 'windows' or 'unknown'."""
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("win"):
        return "windows"
    kind = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if kind in ("x11", "wayland"):
        return kind
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


# --- listing windows ---------------------------------------------------------------------


def list_windows() -> list[str]:
    """Titles of the open windows, best effort. Empty when the desktop will not say."""
    kind = session()
    if kind == "x11" and have("wmctrl"):
        return [line.split(None, 3)[-1] for line in run(["wmctrl", "-l"]).splitlines() if line]
    if kind == "wayland" and have("swaymsg"):

        def walk(node: dict) -> list[str]:
            found = [node["name"]] if node.get("name") and node.get("pid") else []
            for child in node.get("nodes", []) + node.get("floating_nodes", []):
                found += walk(child)
            return found

        return walk(json.loads(run(["swaymsg", "-t", "get_tree"])))
    if kind == "macos" and have("osascript"):
        script = 'tell application "System Events" to get name of every process whose visible is true'
        return [name.strip() for name in run(["osascript", "-e", script]).split(",") if name.strip()]
    return []


# --- capturing ---------------------------------------------------------------------------


def capture_x11(out: Path, title: str | None) -> str:
    """X11: ImageMagick, maim or scrot. Confirmed live 2026-09-26."""
    target = "root"
    if title is not None:
        if not have("xdotool"):
            raise CaptureError("a window title needs xdotool on X11; install xdotool")
        found = run(["xdotool", "search", "--name", title], tolerate=(1,)).split()
        if not found:
            raise CaptureError(f"no window matching {title!r}; try --list")
        target = found[0]
    if have("import"):
        run(["import", "-window", target, str(out)])
        return "import"
    if have("maim"):
        run(["maim", *(["-i", target] if title else []), str(out)])
        return "maim"
    if have("scrot") and title is None:
        run(["scrot", "-o", str(out)])
        return "scrot"
    raise CaptureError("no X11 capture tool; install ImageMagick, maim or scrot")


def desktop() -> str:
    """The desktop environment, lowercased - 'gnome', 'kde', 'sway', ... or '' if it won't say.

    Wayland is not one thing: whether a window can be captured unattended is decided by the
    compositor on top of it, not by Wayland. This is the discriminator for that.
    """
    for var in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION"):
        value = os.environ.get(var, "").strip().lower()
        if value:
            return value
    return ""


def capture_wayland(out: Path, title: str | None) -> str:
    """Wayland: grim on wlroots, Spectacle on KDE, nothing on GNOME. Not run for real."""
    where = desktop()
    if have("grim"):
        if title is None:
            run(["grim", str(out)])
            return "grim"
        if not have("swaymsg"):
            raise CaptureError("grim needs a compositor query for one window; install swaymsg")
        run(["grim", "-g", sway_geometry(title), str(out)])
        return "grim+swaymsg"
    # Spectacle on GNOME falls through to the portal and waits for a human to click. A clear
    # failure beats a capture that silently blocks, so it is only used on its own desktop.
    if have("spectacle") and "gnome" not in where:
        run(["spectacle", "-b", "-n", "-a" if title else "-f", "-o", str(out)])
        return "spectacle"
    if "gnome" in where:
        raise CaptureError(
            "GNOME on Wayland has no non-interactive window capture - its portal waits for a "
            "human to click. Run the app under X11, or capture from the device itself"
        )
    raise CaptureError(
        f"no Wayland capture tool for this desktop ({where or 'unknown'}). "
        "wlroots compositors (sway, Hyprland): install grim. KDE Plasma: install spectacle"
    )


def sway_geometry(title: str) -> str:
    """`x,y WxH` for the first sway window whose name contains `title`."""

    def walk(node: dict) -> dict | None:
        if title.lower() in (node.get("name") or "").lower() and node.get("pid"):
            return node["rect"]
        for child in node.get("nodes", []) + node.get("floating_nodes", []):
            hit = walk(child)
            if hit:
                return hit
        return None

    rect = walk(json.loads(run(["swaymsg", "-t", "get_tree"])))
    if rect is None:
        raise CaptureError(f"no window matching {title!r}; try --list")
    return f"{rect['x']},{rect['y']} {rect['width']}x{rect['height']}"


def capture_macos(out: Path, title: str | None) -> str:
    """macOS: the built-in screencapture. Not run for real."""
    if not have("screencapture"):
        raise CaptureError("screencapture is missing; this is not a normal macOS")
    if title is None:
        run(["screencapture", "-x", str(out)])
        return "screencapture"
    script = (
        f'tell application "System Events" to tell (first process whose name contains "{title}")'
        " to get {position, size} of front window"
    )
    numbers = [int(n) for n in run(["osascript", "-e", script]).replace(",", " ").split()]
    if len(numbers) != 4:
        raise CaptureError(f"could not read the bounds of {title!r}; grant Accessibility access")
    x, y, width, height = numbers
    run(["screencapture", "-x", "-R", f"{x},{y},{width},{height}", str(out)])
    return "screencapture -R"


POWERSHELL_FULL_SCREEN = """
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$b = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.X, $b.Y, 0, 0, $bmp.Size)
$bmp.Save('{out}', [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
"""


def capture_windows(out: Path, title: str | None) -> str:
    """Windows: PowerShell and System.Drawing, whole screen only. Not run for real."""
    shell = "powershell" if have("powershell") else "pwsh"
    if not have(shell):
        raise CaptureError("neither powershell nor pwsh is on PATH")
    if title is not None:
        raise CaptureError("per-window capture is not implemented on Windows; omit --window")
    run([shell, "-NoProfile", "-Command", POWERSHELL_FULL_SCREEN.format(out=out)])
    return "powershell"


BACKENDS = {
    "x11": capture_x11,
    "wayland": capture_wayland,
    "macos": capture_macos,
    "windows": capture_windows,
}


def capture(out: Path, title: str | None) -> str:
    """Capture to `out`, returning the name of the mechanism that did it."""
    kind = session()
    if kind not in BACKENDS:
        raise CaptureError(
            "no graphical session detected: XDG_SESSION_TYPE, WAYLAND_DISPLAY and DISPLAY are "
            "all unset. Over SSH, forward a display or capture on the machine with the screen"
        )
    return BACKENDS[kind](out, title)


def png_size(path: Path) -> tuple[int, int]:
    """Width and height of a PNG, from its header. Raises CaptureError if it is not one."""
    header = path.read_bytes()[:24] if path.exists() else b""
    if len(header) < 24 or not header.startswith(PNG_SIGNATURE):
        raise CaptureError(f"{path} is not a PNG ({path.stat().st_size if path.exists() else 0} bytes)")
    return struct.unpack(">II", header[16:24])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", nargs="?", default="screenshot.png", help="PNG to write")
    parser.add_argument("--window", help="capture one window whose title contains this")
    parser.add_argument("--list", action="store_true", help="list open window titles and exit")
    args = parser.parse_args(argv)

    if args.list:
        titles = list_windows()
        if not titles:
            print(f"this desktop ({session()}) will not list windows from a script", file=sys.stderr)
            return 1
        print("\n".join(titles))
        return 0

    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        mechanism = capture(out, args.window)
        width, height = png_size(out)
    except CaptureError as exc:
        print(f"screenshot failed: {exc}", file=sys.stderr)
        return 1
    print(f"{out}  {width}x{height}  via {mechanism}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
