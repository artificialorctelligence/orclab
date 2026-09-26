---
name: device-observation
description: Use when a project is developed against a real device the developer has to look at — a phone, a head unit, an emulator, a desktop app window — and every check currently costs a round trip through them. Claude drives and observes the device itself: screenshots, synthetic input, logs that outlive the platform's own, and long-running processes started in the developer's own terminal. Not a command; Claude reads it whenever a human is being used as a pair of eyes.
user-invocable: false
allowed-tools: Bash(python3 *)
---

# Device observation — stop using the developer as a camera

A project with a real device in the loop develops at the speed of the round trip: Claude changes
something, the developer relaunches, looks, and describes what they saw. Every one of those costs a
minute of their attention and loses most of what was on screen. Worse, what comes back is a
*description* — "the map is off-centre", "it's very cyan" — when the pixels would have settled the
question.

Most of that loop is unnecessary. Claude has a shell on the developer's machine. The device is on
the end of a cable, the head unit is a window on the desktop, and both can be read directly.

**The rule: never ask the developer to look at something Claude can look at.** Ask them for
judgment — "does this read as ice?" — not for observation.

## What Claude can do without them

### Screenshot the device

```bash
adb exec-out screencap -p > shot.png        # Android, straight to a file
xcrun simctl io booted screenshot shot.png  # iOS simulator
```

Then read the image. This is the single highest-value habit in this skill: a screenshot answers
questions a description cannot, including questions nobody thought to ask. Real bugs have been
found in the background of a screenshot taken for something else entirely.

### Screenshot a desktop window (an emulator, a head unit, a desktop app)

**First ask whether the desktop is involved at all.** Anything the device itself renders, the
device can usually capture, and that path works the same on every machine: `adb shell screencap`
reaches an emulator and even a car screen the phone is projecting into a head unit
(`car-android-auto` has that case), and `xcrun simctl io booted screenshot` reaches the simulator.
Reach for desktop capture only for a window that is genuinely the desktop's own — it is the part
of this skill that varies most between machines, and the part most likely to be missing entirely.

When it really is a desktop window, find the session type first, because nothing below is
portable:

```bash
echo "$XDG_SESSION_TYPE"    # x11 or wayland
```

- **X11** — `wmctrl -l` for the exact title (a guessed one silently matches nothing), then
  `import -window "$(xdotool search --name 'Title' | head -1)" shot.png`. `maim -i <id>` or `xwd`
  do the same job where ImageMagick is absent. Confirmed live 2026-09-26.
- **Wayland is not one answer.** Wayland is the plumbing; what decides whether a window can be
  captured unattended is the desktop on top of it, read from `XDG_CURRENT_DESKTOP`. On wlroots
  compositors (sway, Hyprland), `grim` with geometry from `swaymsg` or `hyprctl`. On KDE Plasma,
  `spectacle -a -b -n -o shot.png`. On **GNOME, there is no non-interactive per-window capture at
  all** — its portal waits for a human to click, which is the thing this skill exists to avoid.
  Researched 2026-09-26, not verified live: the machine this was written on runs X11.

  **Do not pick a capture tool by what is installed.** A KDE tool on a GNOME desktop does not
  fail — it falls through to the portal and blocks, waiting for a click that no one is coming to
  make, which reads as a hang rather than an error. Branch on the desktop first, then on the
  tool. `scripts/screenshot.py` does this; it was written the other way round first, and that is
  the bug direflail's question turned up on 2026-09-26.
- **An X11 program under Wayland** — the DHU and the Android emulator both are — is reported to
  stay visible to the X11 tools through XWayland. Worth trying before concluding the session type
  rules them out. Not verified.

**Do not assume any of these are installed.** `wmctrl`, `xdotool`, ImageMagick and `grim` are all
optional packages, absent by default on several distributions. Probe with `command -v` and use
what is there. If nothing is, that is a fair thing to ask the developer for — one install, once,
recorded with `environment-registry` — which is very different from asking them to be the camera
every time.

### The desktop build of a mobile app

A Flutter, React Native or Compose Multiplatform app usually also runs on the desktop, and
rebuilding there takes seconds where a phone takes minutes. Most layout, state and logic work is
faster to check that way, and the screenshot is a desktop window like any other.

What it does **not** check is anything the phone or the car actually decides: real permissions,
real sensors, the car surface, the projected screen, how a layout behaves at the size and
brightness of the real thing. Use the desktop build to iterate and the device to confirm, and say
which one a screenshot came from — a screenshot with no device behind it, presented as if there
were, is worse than no screenshot.

Its console output is right there in the terminal it was started from, so the app's own log file
matters less here than on a phone. Start it in the developer's terminal all the same, for the
reasons below.

### A portable way to capture a window

There is no one command that screenshots a window on every desktop, so this skill ships one that
picks whatever the machine has:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/screenshot.py" --list
python3 "${CLAUDE_SKILL_DIR}/scripts/screenshot.py" --window 'Orcweather' shot.png
python3 "${CLAUDE_SKILL_DIR}/scripts/screenshot.py" shot.png          # the whole screen
```

Standard library only, no packages to install. It prints the path and the real dimensions of what
it wrote, because a capture tool that exits 0 over an empty file is the failure worth catching. On
a desktop with nothing usable it fails with the name of what to install rather than a stack trace,
and under GNOME on Wayland it says outright that no non-interactive per-window capture exists and
to run the app under X11 instead.

Confirmed live on Linux/X11 2026-09-26. The macOS, Windows and Wayland branches are written from
each tool's documented interface and have not been run; `scripts/tests/` covers which branch gets
chosen on each platform, which is the part that can be wrong on a machine nobody here has.

### Drive the device

```bash
adb shell input swipe 504 1400 504 1400 900   # a long press: same point, 900ms
adb shell input text "Testspot"
adb shell input tap 691 907
```

Coordinates come from a screenshot Claude has just taken, in that screenshot's own pixels. This
reproduces UI bugs without the developer touching anything — and it produces a *reproduction*
rather than a report, which is the difference between debugging and guessing.

**Never do this while the developer is holding the device.** Synthetic input arrives with no
warning and fights whatever they are doing: a dialog opens under their hands, their typing lands in
the wrong field, and the resulting mess looks exactly like a bug in the app. Say what is about to be
driven, or wait.

### Read what the device says

```bash
adb logcat -d -s flutter:V              # one tag
adb logcat -b crash -d                  # survives far longer than the main buffer
adb shell dumpsys dropbox               # app and native crashes, kept for days
adb shell dumpsys location | grep -A3 "last location"
adb shell dumpsys package <pkg> | grep -A2 PERMISSION
```

`adb shell` reads standard input, so inside a `while read` loop it swallows the remaining lines
and the loop runs once. Add `< /dev/null` to the `adb` call whenever looping over ids.

`dumpsys` is chronically under-used and settles questions logs cannot: whether a permission is
actually granted, whether the app is really requesting location, whether a position fix exists at
all. One session spent an hour on a "no GPS" bug that `dumpsys location` answered in one line — a
four-metre fix on file and zero locations delivered to us, which pointed straight at a dead
subscription rather than a dead sensor.

### Start long-running things in the developer's own terminal

A head unit, a dev server, an emulator or a log tail belongs in **their** interactive shell, not in
Claude's sandboxed one: it needs their desktop's OpenGL and their signed-in tooling, it must outlive
the turn, and they must be able to stop it. Where the harness offers a terminal tool, use it, and
then make the panel visible — opening a tab does not necessarily reveal it.

A harness terminal tool may refuse a working directory outside the project. Run the thing by its
absolute path, or put a `cd` in the command line — but check whether it actually needs a
particular directory before telling anyone that it does. A bundled binary usually finds its own
libraries through an `$ORIGIN` rpath and runs from anywhere; `readelf -d` settles it in one line.

Do not hand the developer a long command to paste. If Claude can run it, Claude runs it.

## What the platform will not give you, and what to build instead

**Device logs rotate far faster than anyone expects.** One real Pixel keeps about **seventy
seconds** of `logcat`: everything from a commute is gone hours before the cable goes in. Discovering
this *after* the interesting failure is the normal way to discover it.

So when a project is used away from the desk, the app should write its own log:

- To a location readable without root — on Android, `getExternalFilesDir`, which `adb pull` reaches
  even for a store-installed release build, where `run-as` does not work at all.
- **Written synchronously, never buffered.** A buffered sink dies with the process and takes
  exactly the lines that would have explained the crash — but "flush after every write" is the
  wrong cure and an expensive one to learn: Dart's `IOSink` makes it an error to write while a
  flush is in flight, so the next line threw, the catch disabled the log, and after the change
  *nothing* was recorded but the first marker. Verified broken and then fixed on 2026-09-26. Use
  the platform's plain synchronous append (`File.writeAsStringSync(mode: append)`); the bytes are
  with the operating system before the call returns, which is what actually survives a crash, and
  at a few lines a minute reopening the file costs nothing.
- With the platform's uncaught-error hooks routed into it, not only what someone thought to print.
- Marking every cold start, so a launch with no clean shutdown before it *is* the crash report.

A native crash still kills the process before any of this runs. The app's log then gives the run-up,
and the cause has to come from the operating system's own crash store.

## Fake the conditions you cannot wait for

Weather, routes, error states and seasonal hazards do not arrive on demand, and a feature nobody has
ever seen is not finished. Put canned data behind build-time flags, one per *independent* axis, so
any combination can be produced:

```
--dart-define FAKE_WEATHER=true --dart-define FAKE_ROADS=false --dart-define FAKE_ALERTS=false
```

One flag is rarely enough. A canned storm carrying alerts, road reports *and* freezing temperatures
could not show an ice estimate, because the reported roads and the alerts each outranked it — the
interesting state stayed unreachable until both could be silenced separately. Expect to discover
this the first time a feature refuses to appear on demand.

Check the fake's shape matches the real feed, too: an "empty" fixture of the wrong type throws where
the real empty response would not, and then the app reports a broken feed that is only a broken
test.

## The loop, when it is working

1. Change the code.
2. Build and install from Claude's shell.
3. Ask for exactly one thing: relaunch.
4. Screenshot the device *and* the head-unit window, read the app's own log, and judge.
5. Ask the developer only for taste, or for what happens at speed on a real road.

Steps 2 and 4 are Claude's. The developer appears twice, briefly, and is asked only for the thing
that genuinely needs them.
