# Python

Researched on: 2026-09-11 (versions read from PyPI that day). Last real run: none yet — the
first is Task 19 of the v17 plan, on Orclab itself.

## Detect
`pyproject.toml`, `setup.py` or `setup.cfg` at the root or up to two directories down.

## Run
`python3 -m pytest -q --ignore=mutants [path]` — pytest 9.1.1. A `[tool.pytest.ini_options]`
section is the project's own config and is honoured by pytest itself. `--ignore=mutants` is not
optional: see Caveats.

## Coverage
pytest-cov 7.1.0: `--cov=<path> --cov-report=lcov:.orclab/test/python/coverage.lcov
--cov-report=html:.orclab/test/python/html`. `run.py` reads the lcov and applies the 80% gate.
For a project-side gate in CI, pytest-cov's own switch is `--cov-fail-under=80`.

## Mutation (TCE)
mutmut 3.7.0 (PyPI, 2026-07-31). Config in `pyproject.toml`:
```toml
[tool.mutmut]
paths_to_mutate = ["src/"]
tests_dir = ["tests/"]
```
`python3 -m mutmut run`, then `run.py` reads `python3 -m mutmut results` (one line per mutant:
`<key>: killed|survived|timeout|suspicious|skipped|no tests`) and `python3 -m mutmut show <key>`
for each survivor's diff. `killed` and `timeout` count as caught, `survived` as a survivor;
`suspicious`, `skipped` and `no tests` are not counted. Incremental: mutmut caches per function
hash in `mutants/`; only changed functions re-run. A path argument does not narrow mutmut — it
mutates `paths_to_mutate`. Alternative, not used: cosmic-ray 8.7.0 (more configurable, longer
setup).

## Test lint
No tool. ruff's `PT` rules (flake8-pytest-style) report nothing for an assertion-free test or a
bare `@pytest.mark.skip` — checked 2026-09-11 with ruff 0.16.7. `run.py` scans `test_*.py` with
the stdlib `ast` module for: no assertion (an `assert`, `pytest.raises`, or a `.assert_*` call
counts), `sleep` calls, `@pytest.mark.skip`/`skipif`, duplicate test names.

## Caveats
- **mutmut 3 copies the tests into `mutants/`.** A later plain `pytest` collects both copies and
  fails with "import file mismatch". Every pytest here passes `--ignore=mutants`; a project should
  also add `mutants/` to `.gitignore`.
- mutmut needs the tests to import the code under test the way the project runs — `pythonpath`
  in `[tool.pytest.ini_options]` or an installed package — or every mutant reports `no tests`.
