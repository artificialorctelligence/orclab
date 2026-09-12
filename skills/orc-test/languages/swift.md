# Swift

Researched on: 2026-09-11. Last real run: none yet — the first is Task 19 of the v17 plan, on
Orclab itself.

## Detect
`Package.swift` (Swift Package Manager, runs on any OS) or a `*.xcodeproj`/`*.xcworkspace`
(Xcode app target, Mac only) at the root or up to two directories down.

## Run
`swift test [--filter <target>]` for an SPM package — works on Linux or macOS, no Xcode needed.
An Xcode project instead runs `xcodebuild test -project <name>.xcodeproj -scheme <name>
-destination "platform=macOS"` (plus `-only-testing:<target>` to narrow) — `stack-ios-native`
already establishes that a Mac is required for app targets; this is the same constraint showing
up in `orc-test`.

## Coverage
SPM: `swift test --enable-code-coverage`, then `swift test --show-codecov-path` prints the path
to a JSON report in the same shape read below. Xcode: `xcodebuild test ... -enableCodeCoverage
YES -resultBundlePath <out>/result.xcresult`, then `xcrun xccov view --report --json
<out>/result.xcresult` writes the same shape. Both are read by one parser: `{"targets":
[{"files": [{"path": <abs>, "coveredLines", "executableLines"}]}]}`, paths relativised against
the project root. **No threshold flag on either path — `run.py` is the only gate.**

## Mutation (TCE)
Muter (github.com/muter-mutation-testing/muter, `brew install
muter-mutation-testing/formulae/muter`; last pushed 2026-07-21, no tagged release since 16/2023).
`muter init` once writes `muter.conf.yml` (`executable` + `arguments` telling Muter how to run
the test suite). `muter run --format json --output <out>/muter.json`; `--files-to-mutate
<target>/**/*.swift` narrows. The JSON (`MuterTestReport`, read from source 2026-09-11):
`globalMutationScore`, `totalAppliedMutationOperators`, `numberOfKilledMutants`, `fileReports:
[{fileName, mutationScore, appliedOperators: [...]}]`. `run.py` reads only the file-level
numbers — `appliedOperators`'s inner shape isn't confirmed, so a file scoring under 100% becomes
one `Survivor` at line 0 describing its score, not a per-mutant one, until a real run supplies
the shape.

## Test lint
SwiftLint 0.65.1: `swiftlint lint --reporter json --quiet [path]`. No rule targets an
assertion-free test specifically; `run.py` runs it over the test path and keeps only findings
whose file looks like a test file.

## Caveats
- **Muter has two open bugs (muter#307, #310, 2026) where an SPM project always scores 0%.**
  Treat a 0% TCE score on an SPM package as this bug, not a real result, until a real run says
  otherwise.
- **Muter's per-mutant detail is not parsed yet.** `appliedOperators`'s inner shape wasn't
  confirmed from source, so survivors are reported per file (line 0) rather than per mutant —
  the fixture is hand-built from the documented schema; see `muter.json.README`.
- **The xccov JSON shape is hand-built from documented `xcrun xccov` output**, not captured from
  a real run; see `xccov.json.README`.
- An Xcode app-target run (`xcodebuild`, `xcrun xccov`) needs a Mac — `missing()` reports
  `xcodebuild` as missing on any other OS, or on a Mac without Xcode's command-line tools
  installed.
