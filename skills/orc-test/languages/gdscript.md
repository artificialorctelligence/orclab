# GDScript

Researched on: 2026-09-11 (versions read from the Godot Asset Library and PyPI that day).
Last real run: none yet — the first project with this language corrects it.

## Detect
`project.godot` at the root or up to two directories down.

## Run
gdUnit4 6.2.1's own CLI runner: `./addons/gdUnit4/runtest.sh -a <path>` (default `test`), which
needs `GODOT_BIN` set to a Godot 4.x binary. It exits 0 on a green suite, **100 on test failures,
101 on warnings** — both are non-zero, so the pass/fail check needs no special case. It writes
JUnit XML to `reports/results.xml`. GUT 9.6.1 is a known alternative, not wired in here — a
project on GUT instead sets its own runner in `.orclab/test.yaml`'s `test:` override.

## Coverage
nano-coverage (github.com/IgorBayerl/nano-coverage-godot), **alpha, built from source** — it
hooks a gdUnit4 test session and writes `lcov.info` at the project root, read here with the
shared `lcov.py` reader. **No threshold flag of its own — `run.py` is the only gate.** Its addon
must be present at `addons/nano_coverage` before a run; `coverage_unavailable(root)` checks for
that and reports the reason in words instead of running anything when it is missing.

## Mutation (TCE)
**None exists.** No mutation-testing tool for GDScript was found as of this research.
`mutation_unavailable` always returns a reason; `mutation_cmd`/`mutation_parse` are dead code
kept only to satisfy the shared contract and are never called.

## Test lint
gdlint (gdtoolkit 4.5.0, `pip install gdtoolkit`) — style rules only (naming, indentation, max
line length); it has no assertion-free-test rule the way this project's own `run.py` scanners do
for other languages.

## Caveats
- gdUnit4 exits 100 on test failures and 101 on warnings — both non-zero, both read as "failed"
  here; no separate handling needed.
- nano-coverage is alpha and built from source; its lcov lands at the project root, not under
  `.orclab/test/gdscript/` like every other language's coverage output.
- Coverage is genuinely two-tier here: `coverage_unavailable` reports "not installed" in words
  when the addon is missing — that case alone does not fail the gate. Red tests still do
  ("tests failed; coverage not measured" fails the gate exactly like any other language).
