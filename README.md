# Orclab

Orclab is a Claude Code plugin. It gives you commands for the work around code — versions,
releases, publishing, tests, the backlog — plus background knowledge Claude reads on its own
while it works, without you asking for it. It comes from real practice: worked out on a real
project (Orcshot, a screenshot tool for Linux desktops) first, then turned back on Orclab's own
development.

## Installing

### On your own computer

Clone this repository, then register that checkout as a local plugin marketplace —
`~/projects/orclab` below is just an example path, use wherever you cloned it:

    /plugin marketplace add ~/projects/orclab
    /plugin install orclab@orclab

A new install shows up in a fresh session, not the one you ran the install from.

### In a cloud session

Claude Code can also run in the cloud, from your browser or phone, instead of on your machine.
Installing does not work there, and it fails quietly: the commands above report success and
change nothing, because a cloud session starts in a fresh container that keeps nothing from
before and never reads the folder an install writes to. Anthropic's own documentation says the
same of a plugin a repository turns on in its `.claude/settings.json` — a cloud session does not
install it.

So something has to put the plugin in place as the session starts. Two ways, and they carry
different things:

**Enable Orclab for your claude.ai account.** This is the route Anthropic documents, and the only
one that works in every repository rather than one you have prepared. A plugin enabled for your
account is downloaded into each cloud session before it starts, with its skills, hooks and
everything else. Adding it is done in your claude.ai settings rather than from Claude Code.

**Or carry it in a repository you control**, which is what this repository does for its own cloud
sessions — see `.claude/hooks/session-start.sh` here. It runs before the session starts and links
the checkout into the container's own skills directory, where Claude Code loads it as a real
plugin: skills *and* hooks, the `secret-hygiene` guard and the rest. The hook does nothing outside
a cloud container, so a developer's own machine is untouched by it.

Anthropic's docs name a second route — committing symlinks under the repository's own
`.claude/skills/`, which are part of the clone. That route is real but carries skills only, with
no hooks: measured in a cloud session on 2026-09-24, a command the `secret-hygiene` guard should
have blocked ran unimpeded. Since the hook above already carries the skills, adding it would only
load every skill a second time — 66 entries for 36 skills, roughly doubling always-on context — so
this repository does not use it. If you take that route instead of the hook, expect no hooks.

### What Orclab can and cannot do in the cloud

A cloud container is Linux, with no screen, no phone attached and no Mac. Most of Orclab is
unaffected — `/orc-test`, `/orc-git`, `/orc-todo` and `/orc-version` work normally, and
`/orc-code` works for anything that builds and runs headless. What cannot work there is anything
needing a device, a display or your own credentials: an iOS build, a desktop app you can actually
look at, and `/orc-publish`, `/orc-release` and `/orc-package`, which need the signing keys and
store logins that a cloud session is designed to keep out.

## Commands

- [/orc-code](docs/commands/orc-code.md) — start a new project, add a feature to one that already
  exists, or clean up/move existing code. Adding a feature hands off to Anthropic's own
  `feature-dev` plugin, and moving code to another language or version hands off to its
  `code-modernization` plugin; either way it says plainly if the one it needs isn't installed.
- [/orc-git](docs/commands/orc-git.md) — the everyday git and GitHub jobs: connect a repo, commit,
  push, switch branches, merge, check out a PR, cut a release.
- [/orc-help](docs/commands/orc-help.md) — see which version of Orclab is running and what
  commands it gives you, or read one command's own page; `/orc` is its short name
  ([orc.md](docs/commands/orc.md)).
- [/orc-package](docs/commands/orc-package.md) — set your project up to ship somewhere real (a
  PPA, an app store, a package registry) by applying a ready-made recipe (Orclab calls one an
  *ingredient*), or capturing a new one.
- [/orc-publish](docs/commands/orc-publish.md) — send a finished build to a channel your project
  already has set up, or read back that channel's own published numbers.
- [/orc-release](docs/commands/orc-release.md) — walk your project's own `RELEASING.md` end to
  end, stopping the moment a step fails, and remembering where you left off.
- [/orc-reload](docs/commands/orc-reload.md) — reinstall the plugin you're developing so a fresh
  session picks up your latest changes.
- [/orc-test](docs/commands/orc-test.md) — check whether your tests pass, how much they cover,
  whether they'd catch a real bug, and whether a dependency has a known vulnerability, then fix
  the weak ones.
- [/orc-todo](docs/commands/orc-todo.md) — see and change the project's backlog: list, read, add,
  remove, and order its lanes.
- [/orc-version](docs/commands/orc-version.md) — bump the project's version, draft its changelog
  entry, and tag the commit locally.

Inside Claude, `/orc-help <name>` shows any of these pages.

## What Claude reads on its own

A plugin is installed for your user, so everything below is present in every Claude Code session
on this machine once Orclab is installed, not only in one project (in a cloud session, in every
session that gets Orclab by one of the two routes above) — but each one only comes into play when
its own trigger fits what you're actually doing: a stack skill when that stack is in
play, `secret-hygiene` when a command could surface a credential. For example, when
`secret-hygiene` fires, it keeps secrets out of what gets shown or pasted, and gives the recovery
procedure if one gets exposed anyway. Uninstalling (`/plugin uninstall orclab@orclab`) removes
all of it.

Discipline:

- **backlog-discipline** — when a real finding or deferred decision surfaces, or an existing
  `BACKLOG.md` entry needs resolving, updating, or considering for deletion.
- **code-discipline** — whenever Claude is about to write or change production code, in any
  language.
- **currency-discipline** — when choosing a dependency, library version, framework, or technical
  approach, or when research turns up an answer to a technical question.
- **environment-registry** — when a real, live test environment is accessed or its access details
  are learned, so they don't need re-deriving later.
- **release-checklist** — when setting up a release process for a new project, or when an
  existing `RELEASING.md` needs a newly-learned step added.
- **secret-hygiene** — before running or pasting anything that could surface a credential.
- **security-discipline** — whenever Claude is about to write or change code, in any language;
  what every project owes and what one strangers can reach owes on top.
- **test-discipline** — whenever Claude is about to write or change a test, in any language.
- **verify-before-asserting** — when a claim Claude made gets challenged, or something turns out
  to behave surprisingly.
- **whole-process-first** — before acting on any one step of a documented multi-step process.

Stacks:

- **stack-android-native** — native Android work (Kotlin, Jetpack Compose, Gradle).
- **stack-flutter** — Flutter/Dart work.
- **stack-godot** — Godot game work (GDScript or C#).
- **stack-ios-native** — native iOS work (Swift, SwiftUI, Xcode).
- **stack-kotlin-multiplatform** — Kotlin Multiplatform work shared between native Android and
  iOS apps.
- **stack-php** — PHP web back-end work (an API alone or behind a React front end).
- **stack-python-desktop** — Python desktop work (PySide6/Qt, tray icon, local storage).
- **stack-react-native** — React Native work (Expo).
- **stack-unity** — Unity game work (C#).
- **stack-web** — web work (a Vite/TypeScript/React front end with a FastAPI back end).

Sources, maps and car surfaces:

- **source-librewxr** — weather radar, nowcast, storm cells and alerts from LibreWXR, and the
  point-weather companions (NWS, Open-Meteo) it does not cover.
- **source-road-conditions** — US road conditions: per-state 511 APIs, one paid aggregator, the
  free federal work-zone registry, or inference from weather data already in hand.
- **map-openstreetmap** — the OSM tile usage policy, `flutter_map`, a swappable base layer, and
  stacking a raster weather overlay on top.
- **car-android-auto** — Android Auto / Automotive OS through the Car App Library: the weather
  category, manifest lines, quality rules, and how a Flutter app reaches the car screen.
- **car-carplay** — Apple CarPlay: which categories exist (weather is not one), that only
  navigation apps draw the map, and the iOS 26 widget / Live Activity path with no entitlement.

## Changing Orclab

For people changing Orclab, not for people using it: `CLAUDE.md` is the workshop notes for how
Claude Code's command/skill system actually works, `BACKLOG.md` the open findings, `CHANGELOG.md`
what changed release to release, `docs/superpowers/` the design history behind each change, and
`VERIFICATION.md` the check that confirms everything actually works once installed.
