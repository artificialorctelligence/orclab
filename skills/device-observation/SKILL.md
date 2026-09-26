---
name: device-observation
description: Use when a project is developed against a real device the developer has to look at — a phone, a head unit, an emulator, a desktop app window — and every check currently costs a round trip through them. Claude drives and observes the device itself: screenshots, synthetic input, logs that outlive the platform's own, and long-running processes started in the developer's own terminal. Not a command; Claude reads it whenever a human is being used as a pair of eyes.
user-invocable: false
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

On X11 — check first, because the commands differ per session type:

```bash
echo "$XDG_SESSION_TYPE"                                    # x11 or wayland
wmctrl -l                                                   # window titles
import -window "$(xdotool search --name 'Window Title' | head -1)" shot.png
```

On Wayland, `import` and `xdotool` do not work; `grim` (wlroots) or the desktop's own portal is
needed, and it may not be scriptable at all. Establish which one this machine is once, and record
it with `environment-registry`.

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

Do not hand the developer a long command to paste. If Claude can run it, Claude runs it.

## What the platform will not give you, and what to build instead

**Device logs rotate far faster than anyone expects.** One real Pixel keeps about **seventy
seconds** of `logcat`: everything from a commute is gone hours before the cable goes in. Discovering
this *after* the interesting failure is the normal way to discover it.

So when a project is used away from the desk, the app should write its own log:

- To a location readable without root — on Android, `getExternalFilesDir`, which `adb pull` reaches
  even for a store-installed release build, where `run-as` does not work at all.
- **Flushed every line.** A buffered sink dies with the process and takes exactly the lines that
  would have explained the crash.
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
