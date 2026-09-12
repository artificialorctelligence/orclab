# Swift

Researched on: 2026-09-11. Last real run: none yet — the first is Task 19 of the v17 plan, on
Orclab itself.

## Detect
`Package.swift` (Swift Package Manager, runs on any OS) or an `*.xcodeproj` bundle (Xcode app
target, Mac only) — detected by the `project.pbxproj` file inside it, since `*.xcodeproj` itself
is a directory and the detector only matches files — at the root or up to two directories down.
`*.xcworkspace` is not detected.

## Run
`swift test [--filter <target>]` for an SPM package — works on Linux or macOS, no Xcode needed.
An Xcode project instead runs `xcodebuild test -project <bundle path, relative to root> -scheme
<name> -destination "platform=macOS"` (plus `-only-testing:<target>` to narrow) — the bundle path
is relative so a nested bundle (`App/App.xcodeproj`) still resolves correctly. `stack-ios-native`
already establishes that a Mac is required for app targets; this is the same constraint showing
up in `orc-test`.

## Coverage
SPM: `swift test --enable-code-coverage`, then `swift test --show-codecov-path` prints the path to
a JSON report — this is `llvm-cov export` JSON, not xccov: `{"data": [{"files": [{"filename":
<abs>, "summary": {"lines": {"covered", "count"}}}]}]}`. Xcode: `xcodebuild test ...
-enableCodeCoverage YES -resultBundlePath <out>/result.xcresult`, then `xcrun xccov view --report
--json <out>/result.xcresult`, which writes xccov's own shape: `{"targets": [{"files": [{"path":
<abs>, "coveredLines", "executableLines"}]}]}`. One parser reads both, branching on whether the
top level has a `"data"` key, and relativises paths against the project root either way. **No
threshold flag on either path — `run.py` is the only gate.**

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
whose file is a test file — a path component equal to `Tests`/`tests`/`Test`/`test`, or a
filename ending in `Tests.swift`/`Test.swift`.

## Caveats
- **Muter has two open bugs (muter#307, #310, 2026) where an SPM project always scores 0%.**
  Treat a 0% TCE score on an SPM package as this bug, not a real result, until a real run says
  otherwise.
- **Muter's per-mutant detail is not parsed yet.** `appliedOperators`'s inner shape wasn't
  confirmed from source, so survivors are reported per file (line 0) rather than per mutant —
  the fixture is hand-built from the documented schema; see `muter.json.README`.
- **Both the xccov and llvm-cov export JSON shapes are hand-built from documented output**, not
  captured from a real run; see `xccov.json.README` and `llvmcov.json.README`.
- An Xcode app-target run (`xcodebuild`, `xcrun xccov`) needs a Mac — `missing()` reports
  `xcodebuild` as missing on any other OS, or on a Mac without Xcode's command-line tools
  installed.
