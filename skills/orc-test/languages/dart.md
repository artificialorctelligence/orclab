# Dart

Researched on: 2026-09-11 (versions read from pub.dev that day). Last real run: none yet — the first
project with this language corrects it.

## Detect
`pubspec.yaml` at the root or up to two directories down. Its own `dependencies:` block decides
Dart vs. Flutter: `sdk: flutter` present means every command below runs as `flutter test`
instead of `dart test`.

## Run
`dart test [path]` — `test` 1.32.0. A Flutter project runs `flutter test [path]` instead; both
tools recognise the same package layout and command shape.

## Coverage
Flutter writes `coverage/lcov.info` directly: `flutter test --coverage [path]`. Plain Dart has no
such switch on `dart test` itself — it needs a second step through `package:coverage` 1.15.1:

```bash
dart test --coverage=coverage [path] && \
dart run coverage:format_coverage --lcov --in=coverage --out=coverage/lcov.info \
  --packages=.dart_tool/package_config.json --report-on=lib
```

`run.py` runs this as one `bash -c` string (a `path` argument is `shlex.quote`d before it goes
in), then reads `coverage/lcov.info` with the shared `lcov.py` reader. **Neither tool has a
threshold flag — there is no project-side gate to delegate to; `run.py` is the only gate.**

## Mutation (TCE)
mutation_test 1.8.0 (pub.dev, 2026-02): `dart pub add --dev mutation_test`, then `dart run
mutation_test -f junit -o <out>`. It defaults to running `dart test` over `lib/` with no further
config. Its own gate is an XML config value, unused here. `run.py` takes the newest `*.xml` found
under `<out>` and reads it as junit: each mutant is a `<testcase>`, a `<failure>` child marks a
survivor, and the survivor's file/line/description are parsed from the testcase's `name`
attribute (`lib/clamp.dart:5:10 > replaced with >=`). Alternative, not used: dart_mutant
(github.com/Nimblesite/dart_mutant, MIT, Rust, Stryker JSON) — `run.py`'s existing `stryker.py`
reader would read its report unchanged, no new parser needed.

## Test lint
No tool. `dart analyze` runs as part of a normal Dart workflow but has no rule for an
assertion-free test, and nothing else on pub.dev fills that gap as of this research.

## Audit
`dart pub outdated --json` (or `flutter pub outdated --json` for a Flutter package; Dart SDK
3.13.3 here), confirmed live 2026-09-19 against
https://dart.dev/tools/pub/security-advisories, https://dart.dev/tools/pub/cmd/pub-outdated and
pub's source (dart-lang/pub `lib/src/command/outdated.dart`, `lib/src/solver/report.dart`). The
brief's candidate was `dart pub get`; it does surface advisories — *"The pub client surfaces
security advisories at dependency resolution"* — but only as prose, and `report.dart`'s
`reportAdvisories()` just logs, so it **exits 0** and prints nothing machine-readable. `pub
outdated --json` is the one pub command with the advisory in its JSON: a per-package
`isCurrentAffectedByAdvisory` boolean (from `outdated.dart`), alongside `current`, `upgradable`,
`resolvable` and `latest` versions. It also exits 0 either way, so the flag decides. What the
JSON lacks is the advisory's id and the version that fixes it, so the line reads
`http 0.13.0: security advisory (dart pub get prints the URL) — fix not reported by pub (latest
1.6.0)` — the same `— fix` token every language's audit line carries; `dart pub get`'s
footnote (`[^0]: https://github.com/advisories/GHSA-…`) names it, and `ignored_advisories` in
`pubspec.yaml` silences one the project has judged. Fixture captured from a real run with the
docs' own example pin (`http: 0.13.0`, GHSA-4rgh-jx4f-qfcq). Last real run: none yet.

## Caveats
- **mutation_test is young** (pub.dev 1.8.0, 2026-02) and its report is read here from junit XML
  rather than a purpose-built machine format; dart_mutant is the fallback if this proves
  unreliable in practice.
- **The `-f junit` name-format assumption is the first thing to check on a real run** — the
  fixture used to write `_parse_junit` is hand-built from mutation_test's documented schema, not
  captured from a real run (see `mutation_test_junit.xml.README`).
- No test-specific lint exists for Dart; `dart analyze` runs, but it cannot see an
  assertion-free test.
