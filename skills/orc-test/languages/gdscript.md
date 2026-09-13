# GDScript

Researched on: 2026-09-11 (versions read from the Godot Asset Library and PyPI that day);
mutation 2026-09-12. Last real run: 2026-09-12, `run` and `analyze` against gdmutant's own
`corpus/` sample project (gdUnit4 v6.1.3, Godot 4.7.2 headless, gdmutant 0.1.2) — see Caveats
for what it found.

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
gdmutant 0.1.2 (`pip install 'gdmutant==0.1.*'`, PyPI, MIT, github.com/kphutt/gdmutant; released
2026-08-07, one maintainer, checked live 2026-09-12): `gdmutant run <target> --project <root>
--exclude 'test/*' --json <out>/mutation-report.json --runner gdunit4 --godot $GODOT_BIN`. It
mutates every `.gd` under the target (never `addons/`), reruns the suite once per mutant, and
writes the Stryker JSON that the shared `stryker.py` already reads for JS, C# and Dart. It exits
0 whether or not mutants survived, 1 on a red baseline, 2 on a setup error. `mutation_unavailable`
reports "not installed" in words when `gdmutant` is not on PATH — a Godot project without it gets
the pre-2026-09-12 behaviour, TCE in words rather than a number. A project on GUT gets `--runner
gut --tests res://test/unit` (GUT's `-gdir` does not recurse, so the stock layout has to be
spelled out). Mutation is serial: gdmutant edits the source in place and restores it, so `run.py`'s
tracked-files guard is what proves it put everything back — it did, on the real run.

**The research premise was wrong for a month.** The 2026-09-11 search (GitHub, the Godot Asset
Library, awesome-mutation-testing) recorded "none exists"; gdmutant had been on PyPI since
2026-08-05 and was missed because it is tiny and lives only there. BACKLOG #36 has the record.

## Test lint
gdlint (gdtoolkit 4.5.0, `pip install gdtoolkit`) — style rules only (naming, indentation, max
line length); it has no assertion-free-test rule the way this project's own `run.py` scanners do
for other languages.

## Caveats
- **A fresh checkout needs one `$GODOT_BIN --headless --import` before anything else** (found
  2026-09-12): without the `.godot/` class cache, gdUnit4's own scripts fail to parse
  (`Identifier "GdUnitResult" not declared`) and the suite is red for no reason of its own. Godot
  also writes a `.uid` beside every script on that import — untracked files, ignored by the guard.
- On gdmutant's corpus the real score was 61.1% for `turn_order.gd` (11 killed, 7 survived —
  the README's own number) but 8.1% overall, because the corpus ships a `harness/run_tests.gd`
  no gdUnit4 test reaches. That is the fixture's shape, not a defect; on a real project a file
  like that is a coverage gap the survivors list names by line.
- gdUnit4 exits 100 on test failures and 101 on warnings — both non-zero, both read as "failed"
  here; no separate handling needed.
- nano-coverage is alpha and built from source; its lcov lands at the project root, not under
  `.orclab/test/gdscript/` like every other language's coverage output.
- Coverage is genuinely two-tier here: `coverage_unavailable` reports "not installed" in words
  when the addon is missing — that case alone does not fail the gate. Red tests still do
  ("tests failed; coverage not measured" fails the gate exactly like any other language).
