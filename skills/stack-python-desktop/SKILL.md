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
| `pyproject.toml` | Name, **`version`** (single source — `/orc-version` bumps it), `dependencies = ["pyside6"]`, `[project.scripts]` entry point. |
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

- Python: `https://www.python.org/downloads/`; tkinter docs `https://docs.python.org/3/library/tkinter.html`; sqlite3 docs `https://docs.python.org/3/library/sqlite3.html`; What's New 3.13/3.14 `https://docs.python.org/3/whatsnew/3.13.html`, `.../3.14.html`; bundled Tk/SQLite `https://raw.githubusercontent.com/python/cpython/3.14/PCbuild/get_externals.bat`, `.../3.14/Mac/BuildScript/build-installer.py`; macOS notes `https://docs.python.org/3/using/mac.html`
- PySide6: `https://pypi.org/project/PySide6/` (+ `/pypi/PySide6/json` for wheel tags); getting started `https://doc.qt.io/qtforpython-6/gettingstarted.html`, FAQ `https://doc.qt.io/qtforpython-6/faq/whatisqt.html`; deployment `https://doc.qt.io/qtforpython-6/deployment/index.html`, `.../deployment-pyside6-deploy.html`, `.../deployment-pyinstaller.html`, `.../deployment-briefcase.html`; Qt 6.11 platforms `https://doc.qt.io/qt-6/supported-platforms.html`; `https://doc.qt.io/qt-6/qsystemtrayicon.html`; `https://doc.qt.io/qt-6/qstyle.html`; LGPL `https://doc.qt.io/qt-6/lgpl.html`, `https://www.qt.io/qt-licensing`
- GTK / PyGObject: `https://pypi.org/project/PyGObject/`; `https://pygobject.gnome.org/getting_started.html`; `https://www.gtk.org/docs/installations/windows/`, `.../macos/`, `https://www.gtk.org/docs/language-bindings/python/`; `https://docs.gtk.org/gtk4/` (4.23.4 docs; 4.24.0 tagged 2026-09-11 per GitLab releases API), `https://docs.gtk.org/gtk3/class.StatusIcon.html`, `https://docs.gtk.org/gtk4/migrating-3to4.html`; GTK licence `https://gitlab.gnome.org/GNOME/gtk/-/raw/main/COPYING`; AppIndicator libraries `https://github.com/AyatanaIndicators/libayatana-appindicator` (marked OBSOLETE), `https://github.com/AyatanaIndicators/libayatana-appindicator-glib`
- Tk licence: `https://raw.githubusercontent.com/tcltk/tk/main/license.terms`
- Packagers: `https://pypi.org/project/pyinstaller/`, `https://pyinstaller.org/en/stable/operating-mode.html`, `.../usage.html`, `https://github.com/pyinstaller/pyinstaller/wiki/Supported-Packages`, `https://raw.githubusercontent.com/pyinstaller/pyinstaller/develop/PyInstaller/hooks/hook-PySide6.py`; `https://pypi.org/project/briefcase/`, `https://briefcase.beeware.org/en/stable/reference/platforms/index.html`, `.../linux/system.html`; `https://pypi.org/project/Nuitka/`, `https://nuitka.net/user-documentation/user-manual.html`, `https://raw.githubusercontent.com/Nuitka/Nuitka/main/LICENSE-RUNTIME.txt`
- Layout and storage: `https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/`; `https://pypi.org/project/platformdirs/`, `https://platformdirs.readthedocs.io/en/latest/api.html`, `https://github.com/tox-dev/platformdirs`, `https://raw.githubusercontent.com/tox-dev/platformdirs/main/src/platformdirs/macos.py`, `https://raw.githubusercontent.com/tox-dev/platformdirs/main/src/platformdirs/windows.py`
- Other toolkits and tray packages (versions from `https://pypi.org/pypi/<name>/json`): rumps, pyobjc, pystray, Kivy, dearpygui, toga, wxPython, PyQt6
- Linux desktops: `https://ubuntu.com/about/release-cycle`, `https://ubuntu.com/download/desktop`, `https://documentation.ubuntu.com/release-notes/26.04/summary-for-lts-users/`, `.../changes-since-previous-interim/`; `https://packages.ubuntu.com/resolute/ubuntu-desktop`, `.../gnome-shell-ubuntu-extensions`, `.../gnome-shell-extension-appindicator`, `https://packages.ubuntu.com/noble/gnome-shell-extension-appindicator`; `https://linuxmint.com/download_all.php`, `https://linuxmint.com/rel_zena.php`, `https://linuxmint.com/rel_zena_cinnamon_whatsnew.php`; `https://fedoramagazine.org/announcing-fedora-linux-44/`, `https://packages.fedoraproject.org/pkgs/gnome-shell-extension-appindicator/gnome-shell-extension-appindicator/` (docs.fedoraproject.org and fedoraproject.org/wiki/Releases answered with an Anubis challenge page, not content); `https://extensions.gnome.org/extension/615/appindicator-support/`, `https://github.com/ubuntu/gnome-shell-extension-appindicator`; `https://github.com/linuxmint/xapp`, `.../blob/master/libxapp/xapp-status-icon.c`, `https://github.com/linuxmint/cinnamon/blob/master/files/usr/share/cinnamon/applets/xapp-status@cinnamon.org/metadata.json`, `https://raw.githubusercontent.com/linuxmint/xapp/master/debian/control`; live on this machine: `busctl --user list`, `dpkg -L libxapp1`, `cinnamon --version` (Mint 22.3, Cinnamon 6.6.9, X11 session)
- Orcshot's own tray choice, as the example only: `~/projects/orcshot/src/orcshot/ui/xapp_tray.py`
