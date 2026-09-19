# Python

Researched on: 2026-09-11 (versions read from PyPI that day). Last real run: 2026-09-15, on all
six of Orclab's suites (TCE: orc-publish 78.9%, orc-release 81.9%, orc-test 76.6%, orc-todo
81.4%, orc-package 84.0%, hooks 84.0%; whole-project coverage 92.9%) — the day each got its
`[tool.mutmut]`, and the day orc-package's and the hooks' tests moved in-process. Before that:
2026-09-12, on
Orclab itself — `python3 skills/orc-test/scripts/run.py analyze skills/orc-todo/scripts`:
coverage 91.6% (373/407 lines — re-measured the same day with `coverage skills/orc-todo/scripts`
after the test files were dropped from the denominator; the first run's 95.3% (816/856) had
counted `tests/` as covered source), TCE 68.6% (637 killed of 928; 291 survived, 1 suspicious),
lint 0 findings; 68 tests, 929 mutants, mutmut's run 29s, the whole command ~2 min (most of it
one `mutmut show` per survivor — gone since 2026-09-13, see Mutation). What had to change to get
there is in "Caveats" — every one was found by that run, none by the research.

## Detect
`pyproject.toml`, `setup.py` or `setup.cfg` at the root or up to two directories down.

## Run
`python3 -m pytest -q --ignore-glob=*mutants/* [path]`. A `[tool.pytest.ini_options]` section is
the project's own config and is honoured by pytest itself. The ignore is not optional: see
Caveats. The path is passed to pytest only when it contains test files (`test_*.py` or
`*_test.py`, or is one); a source-only path such as `src/` would make pytest collect nothing, so
the whole suite runs and the path narrows only what coverage *measures*.

PyPI had pytest 9.1.1 on 2026-09-11; the real run was on Ubuntu's pytest 7.4.4 and pytest-cov
4.1.0, and nothing here depends on the newer ones.

A repo with several `scripts/tests/` dirs and no `__init__.py` in them (Orclab) collides on
basenames (`test_cli.py` twice → "import file mismatch") when one pytest collects them all. The
fix is `addopts = "--import-mode=importlib"` plus a `pythonpath` listing each `scripts/` dir —
under importlib mode a `conftest.py` no longer puts its own dir on `sys.path`, so the imports
that used to work by accident have to be declared. Under that mode test modules cannot import
each other; shared helpers go in a non-test module.

This root config isn't scoped to a root-level run: pytest searches upward for it, so `cd
skills/x/scripts && pytest tests/` for any of the five suites other than orc-todo (which has its
own per-suite `pyproject.toml`, see Mutation below) also picks up the root's importlib mode and
its six-`scripts/`-dirs-wide `pythonpath` — a same-named top-level module in two of those
`scripts/` dirs would then shadow one silently.

## Coverage
pytest-cov: `--cov=<path> --cov-report=lcov:.orclab/test/python/coverage.lcov
--cov-report=html:.orclab/test/python/html`. `run.py` reads the lcov, drops the test files
themselves (`--cov=.` includes `tests/`, which would inflate the number — every test line runs)
and applies the 80% gate to what is left.

A file nothing imports reaches the lcov only if coverage.py finds it by walking down from a
`--cov` dir, and that walk stops at any subdirectory without an `__init__.py` (the dir named by
`--cov` itself is exempt). Orcshot's `src/` has none, so `--cov=.` silently left its 17 never-
imported GTK windows out of the denominator (BACKLOG #42, 2026-09-13). `run.py` now passes one
extra `--cov=<dir>` for every `__init__.py`-less directory on the way to a `.py` file (`src`,
`tests`, …); overlapping roots produce no duplicate records. coverage.py 7's
`include_namespace_packages` would do the same, but it lives only in a config file, and naming
one with `--cov-config` would replace the project's own.
For a project-side gate in CI, pytest-cov's own switch is `--cov-fail-under=80`.

## Mutation (TCE)
mutmut 3.7.0 (PyPI, 2026-07-31). Config in the `pyproject.toml` of the directory mutmut runs
from — **the current key names**, not the ones the 2026-09-11 research had (`paths_to_mutate`
and `tests_dir` still work but warn "deprecated"):
```toml
[tool.mutmut]
source_paths = ["orc_todo/"]
pytest_add_cli_args_test_selection = ["tests/"]
also_copy = ["tests/"]
```
`python3 -m mutmut run`, then `run.py` reads mutmut's own cache — `mutants/<file>.meta`, one
JSON per source file with every mutant's exit code — which is all `mutmut results` prints
(`--all true` needed there; mutmut 3.7 otherwise lists only the *non-killed* ones, reading as a
0% score) and what `mutmut show <key>` walks to find a key's file. Exit codes 1/3 are `killed`,
36/24/-24/152/255 `timeout`; both count as caught, 0 (`survived`) as a survivor; the rest are not
counted. Survivors' diffs come from one process, `orc_test/mutmut_diffs.py`, which calls the
function `mutmut show` calls with the file already known: on Orcshot (26k mutants) one `show`
subprocess per survivor was ~35 of analyze's ~45 minutes; on orc-todo's 164 survivors it is now
~1s in place of ~60s. That diff is of the *function* alone, so its `@@` line numbers start at 1
for every function — `run.py` finds the survivor's file line by looking the removed line's text
up inside the function's real span (`ast`), the function named by the key
(`module.x_func__mutmut_N`, or `module.xǁClassǁmethod__mutmut_N` for a method). All three found
by v19's first real quality run on Orcshot, BACKLOG #42. Incremental: mutmut caches per function hash
in `mutants/`; only changed functions re-run. **That hash covers the source only, not the tests**
— found 2026-09-13 when `generate`'s second `analyze` on orc-todo returned the before-number
(69.4%) verbatim after ten new tests; mutmut 3.7 has no `--force`. `mutation_cmd` now removes
`mutants/` outright when any `test_*.py` or `conftest.py` under the config's directory is newer
than the cached verdicts (`*.meta`) — the verdicts cannot go alone; without them beside the
copied sources mutmut reports 0 mutants. Alternative, not used: cosmic-ray 8.7.0.

**Where mutmut runs matters.** It copies `source_paths` into `mutants/`, then runs pytest
in-process from *inside* `mutants/` with `mutants/` (and `mutants/src`, `mutants/source`) put
first on `sys.path`, and names every mutant from the source file's path relative to its cwd.
A hit is only recorded when the tests import the code under that same name — so the package
must be importable by its top-level name from the directory mutmut runs in. A package that lives
at `skills/x/scripts/pkg/` therefore gets its own `pyproject.toml` in `skills/x/scripts/`, and
`run.py` runs mutmut from the nearest `pyproject.toml` with a `[tool.mutmut]` section at or
above the path given (`mutation_cwd` in `langs/python.py`). A path argument narrows only by
choosing which config runs; within one config it always mutates the whole `source_paths`.

## Test lint
No tool. ruff's `PT` rules (flake8-pytest-style) report nothing for an assertion-free test or a
bare `@pytest.mark.skip` — checked 2026-09-11 with ruff 0.16.7. `run.py` scans `test_*.py` and
`*_test.py` with the stdlib `ast` module for: no assertion (an `assert`, `pytest.raises`, or a
`.assert_*` call counts), `sleep` calls, `@pytest.mark.skip`/`skipif`, duplicate test names.

## Audit
pip-audit 2.10.1 (`pip install pip-audit`), confirmed live 2026-09-19 against its README:
`python3 -m pip_audit -f json --progress-spinner off .` audits the project's declared dependencies
from `pyproject.toml` — not the environment — and exits 1 when any has a known vulnerability
(*"pip-audit's exit code cannot be suppressed"*). `run.py` reads the JSON: one line per
vulnerable package with its advisory ids and the versions that fix it. First resolution can take
as long as a `pip install`. Last real run: none yet.

## Caveats
- **mutmut copies only `source_paths` and `also_copy` into `mutants/`; the tests are not copied
  unless `also_copy` names them.** Without it the inner pytest says "file or directory not
  found: tests/" and mutmut stops with `BadTestExecutionCommandsException`. With it, `mutants/`
  holds a second copy of the tests, so a later plain pytest collects both and fails with "import
  file mismatch". Every pytest here passes `--ignore-glob=*mutants/*` (a glob, because each
  sub-project's mutmut has its own nested `mutants/`; no leading `*/`, because pytest matches
  the glob against the full path and `*/mutants/*` misses a `mutants/` at the directory it runs
  from); a project should also add `mutants/` and `.coverage` to `.gitignore`.
- **A `pythonpath` in an enclosing pytest config defeats mutmut silently.** pytest resolves
  `pythonpath` relative to the config file, and if the config it finds is the repo root's, the
  *unmutated* package is first on `sys.path`: the tests pass, hit no mutant, and mutmut stops
  with "could not find any test case for any mutant" (or, with fewer tests, reports every mutant
  `no tests`). The per-directory `pyproject.toml` therefore carries an empty
  `[tool.pytest.ini_options]` so pytest stops there — the same config the suite's per-directory
  run has always effectively used. mutmut's own error text names this cause.
- **A mutant that drops a path argument sends the test at the real thing.** mutmut runs the
  suite from `<scripts>/mutants/`, inside the real repo, and among its mutations is every
  `cwd`/`path` argument replaced by `None` or removed. A test isolated only by the temp dir it
  passes in then runs against the process cwd: on 2026-09-12 orc-todo's suite overwrote the main
  checkout's BACKLOG.md, appended nine stub scenarios to VERIFICATION.md and left a corrupt lock
  in `.git/orclab/` (BACKLOG #34). Before the first `analyze` on a suite that touches files, git
  or the network, check that its tests pin the ambient state (`monkeypatch.chdir(tmp_path)`).
  `run.py` now takes `git status --porcelain` before and after the mutation run; if anything
  outside `.orclab/`, `mutants/` and `.coverage` changed, it names the paths, reports TCE as not
  measurable, and does not score the run.
- **A test that kills a process group can kill the harness.** mutmut runs pytest in-process, so
  a mutant that drops `start_new_session=True` from a `Popen` leaves the child in *mutmut's own*
  group, and a test that then proves the group kill (`os.killpg`) SIGKILLs pytest and mutmut
  together: `analyze` dies with exit 137 and no report, every mutant of that function left
  unrecorded in its `.meta` (orc-publish, 2026-09-15). The fix is an autouse fixture that
  refuses to `killpg` the test process's own group — `skills/orc-publish/scripts/tests/
  conftest.py` — so the mutant becomes a failing test. **It has to live in `tests/conftest.py`,
  not in the `conftest.py` beside the package**: mutmut's copy holds `source_paths` and
  `also_copy` only, and pytest never loads a conftest above the directory it runs from, so the
  package-level one is silently absent under mutation. The same placement rule applies to any
  fixture a suite needs *during* `analyze`.
- **Tests that drive the code as a subprocess measure nothing under mutmut.** The active mutant
  is chosen through an environment variable read by the trampoline *in the test process*, and
  which tests reach which function is recorded there too; a child Python process is invisible on
  both counts — worse, the mutated copy imports mutmut's config at load and exits 1 when the
  child's cwd is not the config's directory. Orclab's hook tests (`hooks/scripts/tests/`) are
  were entirely this shape until 2026-09-15, which is also why coverage reported the hooks at 0%.
  To count, a test has to import and call the function — `hooks/scripts/tests/conftest.py`'s
  `run_hook` drives a hook's `main()` with stdin, stdout, cwd and environment pinned in-process,
  and `skills/orc-package/scripts/tests/conftest.py` loads an ingredient template as a module
  the same way. One subprocess test per script for the stdin/stdout/exit-0 contract is kept; it
  scores nothing, and **it must run the real script, not the one beside the test**: under
  mutation the test file sits in `mutants/tests/`, and the script beside it is mutmut's
  rewritten copy, which imports mutmut's config at load and exits 1 from any other cwd. The
  same goes for a test that reads the source as text. Both test dirs resolve the real path by
  stepping over a parent named `mutants`.
- `debug = true` under `[tool.mutmut]` prints the inner pytest run and is the way to see why it
  failed; it also changed three verdicts (640/288 with it, 637/291 without, stable across two
  clean runs), so measure with it off.
- mutmut mutates every string literal three ways (`XX…XX`, upper-case, lower-case) and every
  keyword argument to `None` or dropped. Code that mostly builds messages (a CLI module) collects
  survivors that are not test weaknesses — `orc_todo.cli` held 172 of the 291. Read the
  survivors list for the branch, comparison and argument mutations first.
