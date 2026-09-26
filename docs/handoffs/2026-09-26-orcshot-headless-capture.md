# Handoff: unattended screen capture, for the Orcshot session

Written 2026-09-26 by a session working on Orclab. It is addressed to a session working on
Orcshot, and it is a question as much as a request — parts of it are probably wrong, and the
section that says so is the one worth reading first.

## Why Orclab is asking

Orclab ships a background skill called `device-observation`. Its rule is that Claude should never
ask a developer to look at something Claude could look at itself — ask a person for judgment, not
for observation. Screenshots are most of how that works.

On a phone or a simulator this is solved: the device photographs itself and the command is the
same on every operating system. On the desktop it falls apart. Every tool is optional, several
distributions ship none of them, and the answer differs per desktop environment rather than per
OS. Orclab's own helper
(`skills/device-observation/scripts/screenshot.py`) copes by probing for whatever is present.

There is one desktop where it finds nothing and cannot: **GNOME on Wayland.** There is no
non-interactive way to capture a window there. The desktop portal exists, and it waits for a human
to click, which is precisely the thing the skill exists to avoid.

A GNOME Shell extension is the exception, because it runs inside the compositor rather than
outside asking permission. Orcshot ships one. That is why this handoff is addressed to you and not
to anyone else.

## What Orclab would call, if it existed

The shape, not the implementation — how you do it is yours:

- **Invoked from a script**, with no human present and nobody watching the screen.
- **Names what to capture**: the whole screen, or one window identified by its title. A
  case-insensitive substring match is fine; that is what every other tool does.
- **Names where to put it**: an output path given by the caller.
- **Writes that file, prints the path, exits 0.**
- **On failure, exits non-zero** with one line on stderr saying why — "no window matching X", "the
  extension is not installed", "this desktop cannot".
- **Never prompts, never opens an editor or a destination menu, never takes focus** from the
  window being captured. Focus theft is not cosmetic here: it changes the picture.
- **Does not depend on a destination the user configured**, because the caller needs to know where
  the file went.

A way to **list window titles** non-interactively is just as valuable, and from what I read you
already have it. Claude needs to know what is on screen before it can ask for one window.

## What I read, and what I concluded

Cited so you can correct me quickly. All at the state of the tree on 2026-09-26.

1. **Five capture flags exist, and none of them takes a value.** `src/orcshot/app.py:177-195`
   registers `--capture-region`, `--capture-full-screen`, `--capture-active-window`,
   `--capture-window-picker` and `--capture-last-region`, every one as `GLib.OptionArg.NONE`.
   So there is no way to pass an output path or a window title today.
2. **The GNOME capture path ends by waiting for a human.**
   `src/orcshot/capture/gnome_capture_rect.py` describes its own wait as *"an open-ended,
   user-timed wait (however long picking a destination takes)"* via `pickDestinationAsync`.
3. **Your own CI says the same, more bluntly.** `scripts/ci-shell-roundtrip.py` explains that it
   tests window-listing because that call *"needs no user interaction, unlike every capture kind,
   which ends in the Shell-side destination menu waiting for a click."*
4. **Window enumeration already works and already carries titles.**
   `src/orcshot/resources/gnome-shell-extensions/orcshot@orcshot.org/windows.js:69,107,165` reads
   `title`, `wm_class`, `pid` and `id` per window.
5. **The app↔extension contract is inverted by design.** Per `src/orcshot/capture/shell_bridge.py`,
   the app never calls into the Shell; it changes the state of a `shell-request` action and the
   extension calls back with `GetRequest` / `Deliver` / `Hello`. Built that way so a confined snap
   can work. I read this as meaning there is no public capture API an outside process can call.

My conclusion from those five: the hard part — the compositor-privileged half — is built and
tested, and what is missing is a route through it that carries its destination in rather than
asking for one. That is a different change from adding a flag, which is what I first assumed.

## Where I am probably wrong

direflail's words: *"i think it does more than what you think it does."* Taking that seriously,
these are the specific things I could not establish, rather than a general disclaimer. Please
correct any of them rather than working around my description:

- **Is there already a non-interactive path I did not find?** A setting that fixes the destination
  and skips the picker, an undocumented flag, a D-Bus method, an environment variable.
- **Does any existing capture land somewhere predictable?** If a configured destination plus a
  deterministic filename already exists, a caller could read the file afterwards and no new
  capture mode is needed at all — only a way to know which file.
- **Does the app need to be running already?** If `orcshot --capture-full-screen` starts a fresh
  instance, does the job and leaves, that matters; if it requires a live tray instance, the
  calling script needs to know.
- **Can the extension capture a window that is not focused,** partly covered, minimised, or on
  another workspace? "Active window" is fragile when nobody is driving the desktop.
- **What happens on a locked or idle session?** Long unattended runs hit this.
- **Does any of this work outside GNOME?** I assumed the extension path is GNOME-only and
  everything else falls back, but I did not verify what Orcshot does on KDE, sway or X11.

## The open question neither of us should decide alone

Most machines already have *something*. On X11 Orclab's helper already works, confirmed live.
So there are two quite different jobs Orcshot could take, and it is your call which:

- **The narrow one: be the GNOME-on-Wayland answer.** Well-defined, small, and it closes the only
  hole that currently has no answer at all. Orclab would try grim, then Spectacle, then Orcshot,
  and on GNOME would go straight to Orcshot.
- **The broad one: be the preferred backend wherever installed.** Bigger, because it means being at
  least as good as `import` and `grim` at the things they already do well, and reliable enough to
  displace a tool that is already working. Worth it only if Orcshot's window targeting is
  genuinely better than "find the X11 window id and grab it".

direflail's framing: *"if they have a screenshot tool already installed, you might just need a
subset of its features."* That points at the narrow one. I have no stake in which — Orclab can
wire either, and the narrow one is strictly less work for you.

## What Orclab needs in order to wire it up

Whichever shape you choose, the calling side needs two things beyond the capture itself:

1. **A cheap way to ask "can you capture here, right now?"** — extension installed, extension
   enabled, this desktop supported. Orclab's helper picks a backend before it tries one, and a
   probe that costs a process start and no screen flash is what makes that possible. An exit code
   is enough; it does not need to be a pretty interface.
2. **A stable name on `PATH`.** `orcshot` is what Orclab would look for.

## Two notes that may save you time

- **You already have the test rig.** `scripts/ci-shell-roundtrip.py` drives the extension under a
  headless GNOME Shell and proves the contract end to end. Whatever gets built here can be tested
  the same way — which matters, because the people who need this feature are mostly not sitting at
  a GNOME machine.
- **Orclab's Wayland support is currently unverified.** Every Wayland branch in
  `screenshot.py` is written from documentation and has never been executed; only the X11 paths are
  confirmed live. If you build this, you are not slotting into something proven — you would be the
  first Wayland path anyone has actually run. Treat my Wayland claims accordingly.

## What Orclab is not asking for

Annotation, the editor, uploads, history, hotkeys, the tray, any UI at all. Bytes to a path and an
exit code. Everything else Orcshot does is for people, and this caller is not one.
