---
name: orc-test
description: Use when the user explicitly asks to use orc-test, or types /orc-test, or asks to run the tests, check coverage, measure test quality, or improve the tests - runs every test suite in the project across its languages, holds coverage to 80% and mutation score (TCE) to 70%, and repairs weak suites from what analyze found.
allowed-tools: Bash(python3 *)
---

# orc-test

Run every command as:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py [--cwd <project>] [--lang <key>] <subcommand> [path]
```

`--cwd` and `--lang` go **before** the subcommand. `path` narrows every subcommand to that part
of the project. Outside a git repository the command says so and stops.

| Subcommand | Question it answers | Writes |
|---|---|---|
| `run` (or nothing) | Does the code work? | nothing |
| `coverage` | How much of it do the tests exercise? (gate 80%) | `.orclab/test/<lang>/` |
| `analyze` | Would the tests notice a defect? (coverage + TCE at 70% + lint) | `.orclab/test/<lang>/`, `.orclab/test/analyze.json` |
| `generate` | Fix what `analyze` found | tests, uncommitted — see below |
| `detect` | Which languages, and which test command each | nothing |

Typing `/orc-test` with no subcommand means `run`.

## How it finds the languages

By marker file, at the project root or up to two directories down: `pyproject.toml`/`setup.py`
→ Python; `package.json` → JavaScript/TypeScript; `pom.xml`/`build.gradle` → Java (Kotlin if
`.kt` files exist); `*.csproj` → C#; `pubspec.yaml` → Dart; `Package.swift`/`*.xcodeproj` →
Swift; `project.godot` → GDScript. Every hit runs. The first line of every report is
`detected: …` so a wrong guess is visible. What each language's tools are, and their gotchas, is
in `languages/<lang>.md` beside this file — read the relevant one before interpreting a report.

A project's own declared test command wins: a `test` script in `package.json`, a `Makefile`
`test:` target, or `.orclab/test.yaml`:

```yaml
coverage: 80        # percent of lines, per language
tce: 70             # mutation score, per language
languages:
  python:
    test: make check
```

## What it never does

Install a tool (it names the missing one and its install line, and skips that language). Run
git. Guess a language it cannot see a marker for.
