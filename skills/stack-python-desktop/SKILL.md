---
name: stack-python-desktop
description: Background knowledge for any work in a Python desktop project - one Python codebase with PySide6 (Qt) windows, a tray icon and local storage, built for Linux, Windows and macOS, and choosing the toolkit, the packager or a tray, config or database mechanism for it. Says what the current toolchain is, where things live in the project, and where each store rule lands in the build. Not a command; Claude reads it when Python desktop is in play.
user-invocable: false
---

# Python — the desktop stack (Linux, Windows, macOS from one codebase)

No project has been built with this yet; the first one corrects it. Every version and default below
was read from the vendor's own page on the date shown; `orclab:currency-discipline` says re-check
anything older than a release cycle, and "Sources" says where.

## When this is the stack

The `/orc-code` Defaults Table row **App / one or more desktops, nothing else**: a windowed app for
any subset of Linux, Windows and macOS, from one Python codebase. Games are Godot or Unity. Anything
with a mobile future is not this: **Python has no real path to Android or iOS** (Briefcase lists
them, but with its own Toga toolkit, not with the toolkit chosen below) — if mobile is plausible
later, start from the multi-platform rows instead. This is a one-way door.

## Toolchain, as of 2026-09-12

| Thing | Current | Where it was read |
|---|---|---|
| Python | **3.14.7** (2026-08-05); 3.15 due October 2026 | python.org/downloads |
| PySide6 (Qt for Python) | **6.11.2** (2026-08-18); wheels for Python 3.10–3.14, `manylinux_2_34` x86_64 / `2_39` aarch64, `macosx_13_0` universal2, `win_amd64` / `win_arm64` — **not 3.15 yet** | pypi.org/project/PySide6 |
| Qt 6.11 platforms | Windows 10 (1809+) and 11 (6.12 is the last for Windows 10); macOS 13+ (incl. 26); Ubuntu 22.04/24.04, Debian 11/12, RHEL 9/10, openSUSE 15.6/16 | doc.qt.io supported platforms |
| pyside6-deploy (ships with PySide6) | wraps Nuitka **4.1.1** by default; Nuitka **4.2.1** on PyPI (2026-09-05), AGPL-3.0+ with a runtime exception for compiled output | Qt for Python deployment; pypi.org/project/Nuitka |
| PyInstaller (alternative packager) | **6.22.3** (2026-09-12); Python 3.8–3.15; Windows 8+, macOS 10.15+, glibc and musl Linux; has a `hook-PySide6.py` | pypi.org/project/pyinstaller |
| platformdirs | **4.11.8** (2026-09-08), MIT | pypi.org/project/platformdirs |
| SQLite | `sqlite3` is in the standard library; python.org's 3.14 builds bundle SQLite **3.50.4** | CPython 3.14 branch build scripts |

Install: `python3 -m venv .venv && . .venv/bin/activate && pip install pyside6`. Qt's own page:
*"No Qt installation is required … the Python packages (wheels) already include Qt binaries"*
(confirmed live 2026-09-12). That sentence is most of the toolkit decision.

## The toolkit decision

A desktop toolkit is the library that draws the windows, buttons and menus and talks to the
operating system for you. Three bind to Python and are candidates for one codebase on three
OSes; the default is the one whose *own* documentation gives one install command that works on
all three and includes a tray icon.

**Default: PySide6 — the Qt company's own Python binding for Qt 6.** `pip install pyside6` gives
Linux, Windows and macOS the same way, with Qt inside the wheel; the tray icon is a class in the
toolkit (`QSystemTrayIcon`, below); the packager is a command that ships with it
(`pyside6-deploy`). Widgets, not QML, for an app with ordinary controls: Qt's own FAQ says *"the
goal of Widgets is to respect the system style"* and that QML *"was originally motivated from
mobile applications development"* (confirmed live 2026-09-12). Licence: LGPL-3.0 (or GPL-2/3, or
commercial). A closed-source app is fine under LGPL-3 if Qt stays a shared library the user could
swap — Qt's own LGPL page: the user must be able to *"recombine or relink the Application with a
modified version of the Linked Version"* (confirmed live 2026-09-12); the wheels are shared
libraries, and pyside6-deploy/PyInstaller keep them so. PyQt6 is the same Qt under GPL-3 or a paid
licence — not the default for that reason.

**GTK 4 via PyGObject 3.58.0 (2026-08-28) — choose it only if the app is Linux-only and should
look native on GNOME.** The concern, confirmed live 2026-09-12 from PyGObject's own install page:
there is no pip wheel that brings GTK with it; on Windows the route is MSYS2 (`pacman -S
mingw-w64-ucrt-x86_64-gtk4 …` plus `PYGI_DLL_PATH`), on macOS it is Homebrew (`brew install
pygobject3 gtk4`), so the app ships a package manager's GTK, not its own. gtk.org's Windows page
says the built-in theme *"makes your app look like a Windows 7 app"*. And GTK 4 has no tray icon
at all (`GtkStatusIcon` was deprecated in 3.14 and is absent from GTK 4 — its class page 404s).
Licence LGPL-2.1+: same relinking obligation as Qt, satisfied by dynamic linking.

**Tkinter — choose it only for a one-window tool where zero dependencies matters more than
anything else.** It is in the standard library (the tkinter docs say the official binaries bundle
Tcl/Tk 8.6; CPython's 3.14 build scripts for the Windows and macOS installers actually name Tk
9.0.4 — the scripts win, and `tkinter.TkVersion` at runtime settles it), so nothing to install —
but it has no tray icon (the tkinter docs have none; `pystray` 0.19.5, last released 2023-09-17,
is the third-party answer) and no toolkit-blessed packager. Licence: Tcl/Tk's BSD-style terms —
keep the copyright notice, nothing else.

Also binding to Python, each with why it is not the default: **Kivy** 2.3.1 (2024-12-26) draws its
own non-native widgets, aimed at touch; **Dear PyGui** 2.3.1 (2026-05-01) is an immediate-mode
GPU UI for tools and dashboards, not native-looking; **Toga** 0.5.6 (2026-07-08) is Briefcase's
own native toolkit, still 0.x; **wxPython** 4.3.1 (2026-07-30) is native-widget and mature, but
has no equivalent of a toolkit-shipped packager. None is excluded for a project that wants it.

## Project layout — where things live

The Python Packaging guide's **src layout**: *"helps prevent accidental usage of the
in-development copy of the code"* (confirmed live 2026-09-12). pyside6-deploy's convention is
its own: it writes one file at the project root and reads it on every later run.

| Path | What |
|---|---|
| `pyproject.toml` | Name, **`version`** (single source — `/orc-version` bumps it), `dependencies = ["pyside6"]`, `[project.scripts]` entry point, and `[tool.pytest.ini_options]` with `pythonpath = ["src"]` so the tests import the package with no install (pytest's reference: *"Sets list of directories that should be added to the python search path"*; what a container run relies on — the Containers section below). |
| `src/<package>/__main__.py`, `main.py` | The app; `main.py` holds `if __name__ == "__main__":` because pyside6-deploy looks for it there by default. |
| `src/<package>/ui/` | Widgets, or `.ui` files from Qt Designer compiled by `pyside6-uic`. |
| `tests/` | pytest. |
| `pysidedeploy.spec` | **Written by the first `pyside6-deploy` run**, at the project root; controls every later build on every OS (Nuitka version, excluded Qt modules, icon). Commit it. |
| `.venv/`, `build/`, `dist/` | Outputs. Git-ignored. |
| `debian/`, `snap/snapcraft.yaml`, `<app-id>.yaml` (Flatpak) | Linux channel files, in the layout each ingredient specifies (below). |

## Build, run, test

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]'
python -m pytest                       # the check before any build
python -m <package>                    # run
pyside6-deploy src/<package>/main.py   # -> .bin (Linux) / .exe (Windows) / .app (macOS), and pysidedeploy.spec
```

**Each OS builds its own artifact** — pyside6-deploy compiles through Nuitka, which needs that
OS's C compiler (GCC/Clang on Linux, Xcode's Clang on macOS, Visual Studio 2022 or MinGW64 on
Windows), and PyInstaller's docs say the same of freezing in general: *"run PyInstaller on that
OS, under that version of Python"* (confirmed live 2026-09-12). No cross-compiling; a Windows or
macOS artifact means a Windows or macOS builder (CI runner or machine). On Linux the store
ingredients build from source and this step is skipped.

Concern lines for the packager: **PyInstaller** 6.22.3 when the C compile is the problem (no
compiler on the builder, or a build too slow) — `pyinstaller --windowed --name <App> src/<package>/main.py`
gives the same three outputs from a `.spec` of its own. **Briefcase** 0.4.5 when you want an
*installer* (`.dmg`, `.msi`, `.deb`/`.rpm`, Flatpak, AppImage) rather than a bare executable —
but its Qt 6 page still reads "As of March 2021, Qt 6 is not supported yet", so expect to prove
it first. Both are in the Qt for Python deployment table as cross-platform options.

Coverage, mutation testing and test lint for this language: `skills/orc-test/languages/python.md`
— `/orc-test` reads it.

## Lint — where code-discipline lands

`code-discipline`'s checkable rules — nesting, function length, swallowed errors, zero warnings —
in `pyproject.toml`, confirmed 2026-09-13 against ruff 0.16.7's and pyright 1.1.414's own docs:

```toml
[tool.ruff]
preview = true                      # PLR1702 has been a preview rule since 0.1.15
[tool.ruff.lint]
extend-select = ["PLR1702", "PLR0915", "E722", "S"]   # "S" is the security ruleset — see Security below
[tool.ruff.lint.pylint]
max-nested-blocks = 2               # ruff's default is 5
max-statements = 50                 # ruff's default; statements, not lines — about a printed page
[tool.pyright]
typeCheckingMode = "strict"         # default is "standard"
```

`PLR1702` too-many-nested-blocks, `PLR0915` too-many-statements, `E722` bare-except (on by
default), and inside `S`, `S110` try-except-pass (*"consider logging the exception"*) — the
rule this section needs; the rest of `S` is the Security section's. These sit on top of ruff's
own default set, which since 0.16 is **five whole categories** — *"correctness, suspicious,
complexity, performance, style"*, about 800 rules (its linter doc, confirmed live 2026-09-13) —
not the old `E4/E7/E9/F` handful; the first run on an existing codebase says so loudly (Orclab's
own: 190 findings, 146 of them from those defaults, all fixed the same day). Python has no compiler
warnings: ruff and pyright *are* the analyzer, both exit non-zero on a finding, and that is the
warnings-as-errors switch; `python -W error` in the test command promotes the runtime
`DeprecationWarning`s. Rules 2, 3 and 5 (loop exits, closing on the error path, checks that
survive release) have no linter — they are reviewed, not linted.

## Security — where security-discipline lands

`security-discipline`'s rules for this stack, confirmed live 2026-09-19;
no project has been through this yet, and the first one corrects it.

### Static analysis

ruff carries a port of bandit, Python's security linter, as its `S` category — 71 live rules
(73 listed, `S320` and `S410` marked removed), every code `security-discipline` cites among
them (rule 1: `S105`–`S107` hardcoded password; rule 5: `S608` SQL built from strings, `S602`
`shell=True`, `S301` pickle, `S506` unsafe `yaml.load`; rule 8: `S501` `verify=False`). Turn
the whole category on rather than those seven, so a rule the skill does not name (`S102`
`exec`, `S307` `eval`, `S324` MD5/SHA1, `S202` `tarfile.extractall`) is still caught, and the
skill and this config cannot drift: the skill's codes are a subset of `S`. The `"S"` in the
Lint section's `extend-select` line is this; two more lines go inside the `[tool.ruff.lint]`
table the Lint section already opens (ruff 0.16.8, 2026-09-16; confirmed live 2026-09-19
against its rule index and settings page, and run on 0.16.8 against a five-line fixture:
`S105` and `S607` fire, `S101` in `tests/` does not, `S403`/`S404` fire only when the `ignore`
line is removed):

```toml
ignore = ["S4"]                     # the 13 "suspicious import" rules: the call-site rules already cover them
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]               # assert is the test framework's own statement
```

What to leave off, and why. **`S101`** (*"Use of `assert` detected"*) is the one rule a
desktop app must not carry in `tests/` — pytest is built on `assert`. Its reason — assertions
*"are removed when Python is run with optimization requested (i.e., when the `-O` flag is
present)"* — is `code-discipline` rule 5's reason exactly, so it stays on for the app's own
code and the `per-file-ignores` entry above is the answer for tests; the rule page has no test
exemption of its own (checked). **`S401`–`S415`** flag an `import` (*"subprocess module is
possibly insecure"*, *"pickle, cPickle, dill, and shelve modules are possibly insecure"*)
rather than a call; they are preview rules, and the Lint section's `preview = true` would
switch them on — every module that imports `subprocess` would fail — while `S602`/`S603` and
`S301` already check the calls those imports lead to, so `ignore = ["S4"]`. **`S603`**
(*"subprocess call: check for execution of untrusted input"*) is the noisy one that stays: its
own page says *"Prone to false positives as it is difficult to determine whether the passed
arguments have been validated."* It fires when any argument is not a literal (the fixture:
`["ls"]` passes, `["ls", input()]` does not), so a desktop app that opens the user's file with
the OS's opener will hit it, and `S607` (*"Starting a process with a partial executable
path"*) alongside; the fix for `S607` is the full path, and `S603` gets a per-line
`# noqa: S603` naming why the argument is trusted — `code-discipline`'s named, commented
suppression — not a blanket ignore. **`S311`** (*"Checks for uses of cryptographically weak
pseudo-random number generators"*) flags a call into the `random` module without knowing what
the number is for; a shuffle or a retry delay is not cryptographic, and gets the same
per-line form with the reason. pyright has no security rules — its configuration
reference has none (read 2026-09-13 for the Lint section; nothing security-shaped in it).
Rules 3 and 4 (a download run without a check; a permission the code does not use) have no
linter in this stack — reviewed, not linted.

### Dependency audit

`/orc-test audit` runs pip-audit on `pyproject.toml`'s declared dependencies —
`skills/orc-test/languages/python.md`, `## Audit`; `pip install pip-audit` (rule 2).

### Secrets

A desktop app's secret is a token for a service the user signed into, and it belongs in the
operating system's own credential store, not in a config file under `platformdirs`' directory
and never in the source. **`keyring` 25.7.0** (2025-11-16, MIT, Python ≥ 3.9; confirmed live
2026-09-19 on PyPI and its README) is one call on every OS this stack targets —
`keyring.set_password("<app>", "<account>", token)` / `keyring.get_password(...)` — and its
README names the store behind it: *"macOS Keychain, Freedesktop Secret Service, KDE4 & KDE5
KWallet, and Windows Credential Locker"*. Its Linux dependencies (`SecretStorage`, `jeepney`)
are declared platform-conditionally on PyPI, so `pip install keyring` is the whole install.
On a Linux box with no desktop (CI, a
headless test) none of those stores is running; the README's answer is the `keyrings.alt`
package, and the app's answer is the same as the tray's — detect and degrade, never write the
token to a file instead.

In `.gitignore`, beyond the layout table's `.venv/`, `build/`, `dist/`: `.env` and `*.local`
now, and whatever signing file a Windows or macOS channel will one day ask for, the day its
ingredient names it. What must never be in the built artifact: any of those, and the `.git`
directory. Whether `pyside6-deploy`'s Nuitka build or PyInstaller ever picks one up was not
checked; the first project lists the artifact's contents once and records it here. A Linux
ingredient that builds from a source tarball is the other place to look (rule 1).

### Reachable by strangers

n/a: a desktop app accepts no connections. The client half of rule 8 still applies to the
app's own outbound calls: certificate validation stays on (`S501` above flags
`verify=False`), and a key baked into the artifact for a service it calls is not a secret —
anyone with the binary has it — so it is either fine to be public or it goes through
`keyring` after the user signs in.

## Containers

Runs in a container: **yes** — confirmed live 2026-09-20. The tests, every `/orc-test` step,
`lint_on_write` and the Linux build run inside; the app itself does not — a container has no
screen, so a window is shown on the host and tested headless inside.

The `Dockerfile` `/orc-code` writes when the user says yes to the container question — base
image and tag from the official `python` image's own tag list (`3.14` is `3.14.7` on Debian
trixie today, the same 3.14.7 the toolchain table names; `3.14.7` pins it), the toolchain
(PySide6), and every tool `skills/orc-test/languages/python.md` names (pytest, pytest-cov,
mutmut, pip-audit) plus ruff, which `lint_on_write` runs:

```dockerfile
FROM python:3.14
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 libegl1 libxkbcommon0 libfontconfig1 libfreetype6 libx11-6 libdbus-1-3 \
    && apt-get dist-clean
RUN pip install --no-cache-dir pyside6 pytest pytest-cov mutmut pip-audit ruff
ENV QT_QPA_PLATFORM=offscreen
```

Not run here — the first project records it. Why each line, so the next reader can check it:

- **`python:3.14`, not `-slim`.** The default tag is built on `buildpack-deps`, which the image's
  README recommends (*"we highly recommend using the default image of this repository"*) and
  whose trixie Dockerfile installs `gcc`, `g++` and `make` — the C compiler a `pyside6-deploy`
  build inside needs (Nuitka compiles). `pip` is in the image (`--with-ensurepip`), and the
  README's own example is `pip install --no-cache-dir`; `apt-get dist-clean` is the base
  image's own idiom.
- **The seven apt packages** are the system libraries the PySide6 6.11.2 wheel's Qt links and
  the base image does not carry — read with `objdump -p` off the `manylinux_2_34_x86_64` wheel,
  downloaded from PyPI on this machine: `libQt6Gui.so.6` needs `libEGL.so.1`, `libGL.so.1`,
  `libfontconfig.so.1`, `libfreetype.so.6`, `libX11.so.6` and `libxkbcommon.so.0`, and pulls in
  `libQt6DBus.so.6`, which needs `libdbus-1.so.3`; ICU is inside the wheel, glib and zlib are
  in the base image. Each `.so` was mapped to its trixie package on packages.debian.org. Not
  checked: whether a widget test wants a font package (`fonts-dejavu-core`) — the first
  project says.
- **One `pip install`** — each tool's own documented line (`pip install -U pytest`,
  `pip install pytest-cov`, `pip install mutmut`, `python -m pip install pip-audit`,
  `pip install ruff`), unpinned like the host's; PyPI today: pytest 9.1.1, pytest-cov 7.1.0,
  mutmut 3.8.0, pip-audit 2.10.1, ruff 0.16.8. **PySide6 is on the line because the image is
  where the project's dependencies live**: `compose run --rm` throws the container away after
  every command, so a `pip install` inside it is gone by the next one, and the host's `.venv/`
  is another Python. A dependency the project adds to `pyproject.toml` goes on this line too,
  then `<engine> compose build orclab` — the same rebuild picks up a new tool version, since
  the line is unpinned. The tests import `src/<package>` with no install: the layout table's
  `pythonpath = ["src"]` (its `pyproject.toml` row), which is why that row carries it.
- **`QT_QPA_PLATFORM=offscreen`** is what makes a `QApplication` start with no display. Qt's
  QPA page: *"The QT_QPA_PLATFORM environment variable and the -platform command line argument
  allow you to override this default"*; `QGuiApplication`'s reference lists `offscreen` among
  the platform plugin names, and the wheel ships it (`PySide6/Qt/plugins/platforms/
  libqoffscreen.so`, listed from the wheel). Set in the image so every test run, and every
  mutant's, inherits it; on the host the app picks `xcb` or `wayland` as before.

The `compose.yaml` is the one in `skills/orc-test/SKILL.md`'s Containers section, unchanged.
What cannot happen inside: showing a window or a tray icon (nothing draws it; the `Presence`
section's desktop-environment checks are host questions), the Windows and macOS artifacts
(`## Build, run, test`: each OS builds its own, and this image is Linux), and the Security
section's `keyring` stores, which do not run in a container. So `python -m <package>` runs on
the host, and the pyside6-deploy step is the Linux `.bin` only. The proposal `/orc-code` makes
for this stack's container question: **no**, because the toolchain is one venv — Python and
pip are on any dev machine, and Qt arrives inside the PySide6 wheel (*"No Qt installation is
required"*, above) — so the container saves nothing an install would cost; say yes when the
machine's Python is too old for the wheel (3.10–3.14 today), or to keep the Qt wheels (80 MB
downloaded for `PySide6_Essentials` alone) off it.

## Presence

The tray icon is how a desktop app stays visible and reachable when none of its windows is in
front: a small icon in the panel (Linux), the notification area (Windows) or the menu bar
(macOS), with a menu, that keeps the app alive in the background. In this stack it is one class,
`QSystemTrayIcon`, on every OS; what differs is whether the desktop shows it. Call
`QSystemTrayIcon.isSystemTrayAvailable()` first — Qt's own advice — and design so the app is
usable without one.

Qt's page (confirmed live 2026-09-12) names the platforms exactly: *"All supported versions of
Windows"*, *"All supported versions of macOS"*, *"All Linux desktop environments that implement
the D-Bus StatusNotifierItem specification, including KDE, Gnome, Xfce, LXQt, and DDE"*, and X11
trays implementing the XEmbed spec. StatusNotifierItem (SNI) is a D-Bus protocol, so it does not
care whether the session is X11 or Wayland — which is why the Linux answer below splits by
desktop environment, not by display layer.

### Linux

**GNOME has no tray of its own; a shell extension adds one.** "AppIndicator and
KStatusNotifierItem Support" (extensions.gnome.org #615, by 3v1n0; version 64 covers GNOME Shell
45–50, confirmed live 2026-09-12) is the SNI host. Without it a `QSystemTrayIcon` on GNOME is
simply not shown. **Cinnamon shows one natively**: Mint's `libxapp1` ships `xapp-sn-watcher`,
which owns `org.kde.StatusNotifierWatcher` on the session bus (checked live on this Mint 22.3 /
Cinnamon 6.6.9 machine, `busctl --user list`), so Qt's SNI path works with nothing installed.
Mint's own native mechanism is `XApp.StatusIcon` (libxapp, in Python via GObject Introspection,
`gi.require_version('XApp','1.0')`), hosted by Cinnamon's "XApp Status Applet" and falling back
to a `GtkStatusIcon` where no applet exists — that is what Orcshot chose, and it is the right
choice for a GTK app on Mint; for this stack `QSystemTrayIcon` reaches the same panel. **KDE
Plasma** is where SNI came from; native, nothing to add.

#### Ubuntu

Current: **26.04 LTS** (April 2026; 26.04.1 on the download page), GNOME **50**, and *"The Ubuntu
Desktop session now runs only on the Wayland back end, because GNOME Shell can no longer run as
an X.org session"* (release notes, confirmed live 2026-09-12); 24.04 LTS (GNOME 46) still
supported. The tray works out of the box on both: `ubuntu-desktop` depends on
`gnome-shell-ubuntu-extensions` (50.26.04.7ubuntu), which provides
`gnome-shell-extension-appindicator` (packages.ubuntu.com, resolute) — on 24.04 it is the package
of that name (57-2). No split by version, session or packaging: a snap or Flatpak talks the same
D-Bus, and the extension is the host's.

#### Mint

Current: **22.3 "Zena"** (Cinnamon 6.6, Ubuntu 24.04 base, supported to April 2029); 22.x and
21.x still supported (linuxmint.com, confirmed live 2026-09-12). X11 by default; the Wayland
session is offered at login and Mint's release notes still call it experimental. The tray works
with nothing installed via `xapp-sn-watcher` (above; checked on 22.3 only — the 21.x series was
not checked). No split by session found; the Wayland session was not tested here, so *verify the
tray there on the first project*.

#### Fedora

Current: **44** (2026-04-28; Fedora Magazine), Workstation on GNOME **50**, Wayland; same GNOME
answer as Ubuntu but **the extension is not preinstalled** — Fedora packages it as
`gnome-shell-extension-appindicator` 64-1.fc44 and its package page tells the user to run
`gnome-extensions enable appindicatorsupport@rgcjonas.gmail.com` (packages.fedoraproject.org,
confirmed live 2026-09-12; docs.fedoraproject.org itself refused the fetch, so the preinstall
claim rests on that page and on the extension's own README, which says the same). The app should
detect `isSystemTrayAvailable()` false and point at the extension, the way Orcshot's first-run
dialog points at its own GNOME extension. KDE
Plasma spin (Plasma 6.6): native. No split by version.

### Windows

`QSystemTrayIcon` covers it; nothing else needed. Nothing splits by version or display layer:
Qt 6.11 supports Windows 10 (1809+) and 11 alike, and Qt 6.12 is announced as the last to
support Windows 10 — a floor to raise later, not a fork today.

### macOS

`QSystemTrayIcon` becomes a menu-bar extra; nothing else needed. Nothing splits by version: the
PySide6 wheel is `macosx_13_0`, so macOS 13 is the floor and 26 is supported. `rumps` (0.4.0,
last released 2022-10-15) and `pyobjc` (12.2.2) reach the same menu bar and are the answer only
for an app that has no Qt — not this stack.

## UI

Bind to Python for desktop: **PySide6/Qt Widgets (the default), GTK 4 via PyGObject, Tkinter,
wxPython, Kivy, Dear PyGui, Toga** — each above with the concern that would pick it over the
default. Excluded: anything that reaches a screen only through a browser (a web framework is
the "web only" row) and PyQt6 (GPL-only or paid). Qt picks a style per platform on its own —
*"If no style is specified, Qt will choose the most appropriate style for the user's platform"*
(QStyle docs, confirmed live 2026-09-12) — so a widgets app looks at home on each OS without
theming work. BACKLOG #2's design system translates into the frameworks above.

## Storage

**Saved data: `sqlite3` from the standard library** — one file, no server, DB-API 2.0; python.org's
3.14 builds bundle SQLite 3.50.4 and a distro Python has its own (this machine: 3.45.1), so
`sqlite3.sqlite_version` at startup is the version that counts (confirmed live 2026-09-12).
**Where the file goes, and where config goes: `platformdirs` 4.11.8** resolves the per-OS
conventions; from its own source (`macos.py`, `windows.py` — confirmed live 2026-09-12): Linux
`~/.config/<app>` for config and `~/.local/share/<app>` for data (XDG); on macOS and Windows,
`user_config_dir` is defined as the same call as `user_data_dir` — macOS is
`~/Library/Application Support/<App>` for both; Windows is
`%USERPROFILE%\AppData\Local\<Author>\<App>` for both by default (`%APPDATA%\<Author>\<App>`,
i.e. Roaming, only when the caller passes `roaming=True`). Qt's `QSettings` is the alternative
when the config is only ever Qt's own window state. External databases are out of scope for this
skill.

## Where each store rule lands

Linux channels are already ingredients, each written from Orcshot's real channel and each with
its own sources — read the chosen one in full; this stack's own job is the `pyproject.toml` /
src layout they build from and the `version` they read:

| Channel | Ingredient | What this stack supplies |
|---|---|---|
| PPA (`.deb` via Launchpad) | `skills/orc-package/ingredients/ppa/ingredient.md` | `debian/` at the root; runtime deps are the distro's own PySide6 packages, not the wheel — name them from `apt-cache search pyside6` on the target series |
| Snap Store | `skills/orc-package/ingredients/snap/ingredient.md` | `snap/snapcraft.yaml`; the ingredient's `dbus`-slot review gate applies only if the app owns a bus name |
| Flathub | `skills/orc-package/ingredients/flatpak/ingredient.md` | `<app-id>.yaml`; whether to build on a runtime that carries Qt or vendor the wheel is decided at first submission |

**Windows:** no ingredient exists; the Microsoft Store (MSIX) would need one, fed by the
`pyside6-deploy` `.exe`. **macOS:** no ingredient exists; the Mac App Store (signed, notarized
`.app`, a Mac to build on — see the App Store ingredient's `local`/`cloud` choice) would need one.
Direct download of the `.exe`/`.app` is a channel with no store rules at all.

## Sources (live on 2026-09-12)

- Lint — where code-discipline lands (2026-09-13): `https://docs.astral.sh/ruff/rules/`, `https://docs.astral.sh/ruff/settings/`, `https://raw.githubusercontent.com/microsoft/pyright/main/docs/configuration.md`; versions from `https://pypi.org/pypi/<name>/json`
- Security — where security-discipline lands (2026-09-19): `https://docs.astral.sh/ruff/rules/` (the flake8-bandit table, 73 rows), `https://docs.astral.sh/ruff/rules/assert/`, `.../rules/subprocess-without-shell-equals-true/`, `.../rules/start-process-with-partial-path/`, `.../rules/hardcoded-password-string/`, `.../rules/suspicious-non-cryptographic-random-usage/`, `https://docs.astral.sh/ruff/settings/` (`lint.extend-select`, `lint.ignore`, `lint.per-file-ignores`); `https://pypi.org/pypi/ruff/json`, `https://pypi.org/pypi/keyring/json`, `https://raw.githubusercontent.com/jaraco/keyring/main/README.rst`; the fixture run: ruff 0.16.8 in a scratch venv on this machine
- Containers (2026-09-20): tags `https://raw.githubusercontent.com/docker-library/official-images/master/library/python`; `https://raw.githubusercontent.com/docker-library/docs/master/python/README.md` (image variants, `--no-cache-dir` example); `https://raw.githubusercontent.com/docker-library/python/master/3.14/trixie/Dockerfile` (`FROM buildpack-deps:trixie`, `--with-ensurepip`, `apt-get dist-clean`); `https://raw.githubusercontent.com/docker-library/buildpack-deps/master/debian/trixie/Dockerfile` (`gcc`, `g++`, `make`, `libglib2.0-dev`, `zlib1g-dev`); the wheel's own linkage: `pip download --no-deps --only-binary=:all: --python-version 3.14 --platform manylinux_2_34_x86_64 pyside6_essentials` and `objdump -p` on `libQt6Core/Gui/Widgets/DBus.so.6` and `plugins/platforms/libqoffscreen.so`, on this machine; package names `https://packages.debian.org/trixie/amd64/<pkg>/filelist` for `libgl1`, `libegl1`, `libxkbcommon0`, `libfontconfig1`, `libfreetype6`, `libx11-6`, `libdbus-1-3`; Qt `https://doc.qt.io/qt-6/qpa.html`, `https://doc.qt.io/qt-6/qguiapplication.html` (`platformName`, `-platform`); install lines `https://docs.pytest.org/en/stable/getting-started.html`, `https://raw.githubusercontent.com/pytest-dev/pytest-cov/master/README.rst`, `https://raw.githubusercontent.com/boxed/mutmut/main/README.rst`, `https://raw.githubusercontent.com/pypa/pip-audit/main/README.md`, `https://docs.astral.sh/ruff/installation/`; `https://docs.pytest.org/en/stable/reference/reference.html` (`pythonpath`); versions from `https://pypi.org/pypi/<name>/json`
- Python: `https://www.python.org/downloads/`; tkinter docs `https://docs.python.org/3/library/tkinter.html`; sqlite3 docs `https://docs.python.org/3/library/sqlite3.html`; What's New 3.13/3.14 `https://docs.python.org/3/whatsnew/3.13.html`, `.../3.14.html`; bundled Tk/SQLite `https://raw.githubusercontent.com/python/cpython/3.14/PCbuild/get_externals.bat`, `.../3.14/Mac/BuildScript/build-installer.py`; macOS notes `https://docs.python.org/3/using/mac.html`
- PySide6: `https://pypi.org/project/PySide6/` (+ `/pypi/PySide6/json` for wheel tags); getting started `https://doc.qt.io/qtforpython-6/gettingstarted.html`, FAQ `https://doc.qt.io/qtforpython-6/faq/whatisqt.html`; deployment `https://doc.qt.io/qtforpython-6/deployment/index.html`, `.../deployment-pyside6-deploy.html`, `.../deployment-pyinstaller.html`, `.../deployment-briefcase.html`; Qt 6.11 platforms `https://doc.qt.io/qt-6/supported-platforms.html`; `https://doc.qt.io/qt-6/qsystemtrayicon.html`; `https://doc.qt.io/qt-6/qstyle.html`; LGPL `https://doc.qt.io/qt-6/lgpl.html`, `https://www.qt.io/qt-licensing`
- GTK / PyGObject: `https://pypi.org/project/PyGObject/`; `https://pygobject.gnome.org/getting_started.html`; `https://www.gtk.org/docs/installations/windows/`, `.../macos/`, `https://www.gtk.org/docs/language-bindings/python/`; `https://docs.gtk.org/gtk4/` (4.23.4 docs; 4.24.0 tagged 2026-09-11 per GitLab releases API), `https://docs.gtk.org/gtk3/class.StatusIcon.html`, `https://docs.gtk.org/gtk4/migrating-3to4.html`; GTK licence `https://gitlab.gnome.org/GNOME/gtk/-/raw/main/COPYING`; AppIndicator libraries `https://github.com/AyatanaIndicators/libayatana-appindicator` (marked OBSOLETE), `https://github.com/AyatanaIndicators/libayatana-appindicator-glib`
- Tk licence: `https://raw.githubusercontent.com/tcltk/tk/main/license.terms`
- Packagers: `https://pypi.org/project/pyinstaller/`, `https://pyinstaller.org/en/stable/operating-mode.html`, `.../usage.html`, `https://github.com/pyinstaller/pyinstaller/wiki/Supported-Packages`, `https://raw.githubusercontent.com/pyinstaller/pyinstaller/develop/PyInstaller/hooks/hook-PySide6.py`; `https://pypi.org/project/briefcase/`, `https://briefcase.beeware.org/en/stable/reference/platforms/index.html`, `.../linux/system.html`; `https://pypi.org/project/Nuitka/`, `https://nuitka.net/user-documentation/user-manual.html`, `https://raw.githubusercontent.com/Nuitka/Nuitka/main/LICENSE-RUNTIME.txt`
- Layout and storage: `https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/`; `https://pypi.org/project/platformdirs/`, `https://platformdirs.readthedocs.io/en/latest/api.html`, `https://github.com/tox-dev/platformdirs`, `https://raw.githubusercontent.com/tox-dev/platformdirs/main/src/platformdirs/macos.py`, `https://raw.githubusercontent.com/tox-dev/platformdirs/main/src/platformdirs/windows.py`
- Other toolkits and tray packages (versions from `https://pypi.org/pypi/<name>/json`): rumps, pyobjc, pystray, Kivy, dearpygui, toga, wxPython, PyQt6
- Linux desktops: `https://ubuntu.com/about/release-cycle`, `https://ubuntu.com/download/desktop`, `https://documentation.ubuntu.com/release-notes/26.04/summary-for-lts-users/`, `.../changes-since-previous-interim/`; `https://packages.ubuntu.com/resolute/ubuntu-desktop`, `.../gnome-shell-ubuntu-extensions`, `.../gnome-shell-extension-appindicator`, `https://packages.ubuntu.com/noble/gnome-shell-extension-appindicator`; `https://linuxmint.com/download_all.php`, `https://linuxmint.com/rel_zena.php`, `https://linuxmint.com/rel_zena_cinnamon_whatsnew.php`; `https://fedoramagazine.org/announcing-fedora-linux-44/`, `https://packages.fedoraproject.org/pkgs/gnome-shell-extension-appindicator/gnome-shell-extension-appindicator/` (docs.fedoraproject.org and fedoraproject.org/wiki/Releases answered with an Anubis challenge page, not content); `https://extensions.gnome.org/extension/615/appindicator-support/`, `https://github.com/ubuntu/gnome-shell-extension-appindicator`; `https://github.com/linuxmint/xapp`, `.../blob/master/libxapp/xapp-status-icon.c`, `https://github.com/linuxmint/cinnamon/blob/master/files/usr/share/cinnamon/applets/xapp-status@cinnamon.org/metadata.json`, `https://raw.githubusercontent.com/linuxmint/xapp/master/debian/control`; live on this machine: `busctl --user list`, `dpkg -L libxapp1`, `cinnamon --version` (Mint 22.3, Cinnamon 6.6.9, X11 session)
- Orcshot's own tray choice, as the example only: `~/projects/orcshot/src/orcshot/ui/xapp_tray.py`
