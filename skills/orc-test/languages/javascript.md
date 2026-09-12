# JavaScript/TypeScript

Researched on: 2026-09-11 (versions read from the npm registry that day). Last real run: none
yet — the first is Task 19 of the v17 plan, on Orclab itself.

## Detect
`package.json` at the root or up to two directories down.

## Run
vitest 5.0.0 when `vitest` is in `package.json`'s dependencies (either section), else jest
30.5.1: `npx vitest run [path]` or `npx jest [path]`. A project's own `vitest.config.*` or
`jest.config.*` is honoured by the tool itself.

## Coverage
vitest, via `@vitest/coverage-v8` 5.0.0: `--coverage --coverage.reporter=lcov
--coverage.reporter=html --coverage.reportsDirectory=<out>`. jest: `--coverage
--coverageReporters=lcov --coverageReporters=html --coverageDirectory=<out>`. Either way `run.py`
reads `<out>/lcov.info` and applies the 80% gate itself. For a project-side gate in CI: vitest's
own `coverage.thresholds.lines: 80` in its config, jest's own `coverageThreshold.global.lines: 80`
in its config.

## Mutation (TCE)
StrykerJS 10.0.0 (`@stryker-mutator/core` plus `@stryker-mutator/vitest-runner` or
`@stryker-mutator/jest-runner`, whichever test runner is in use). `npx stryker run
--incremental --reporters json,progress --jsonReporter.fileName=<out>/mutation.json`; a path
argument becomes `--mutate <path>/**/*`. `run.py` reads the report through the shared `stryker.py`
reader (schema v2, also used by C# and Dart), which takes the newest `*.json` under `<out>` whose
top level has a `"files"` key — not a hardcoded `<out>/mutation.json` path. Incremental: Stryker
keeps its own state in `reports/stryker-incremental.json` between runs — see Caveats.

## Test lint
`@vitest/eslint-plugin` 1.6.27 or `eslint-plugin-jest` 29.16.6, run through the project's own
eslint config — not a separate tool invocation of our own. Rules watched for:
`vitest/expect-expect`, `vitest/no-disabled-tests`, `vitest/no-identical-title`, and the `jest/`
equivalents. When the plugin isn't in `package.json`'s dependencies (either section), lint is not
run and the report says so rather than reporting zero findings.

## Caveats
- **`eslint-plugin-vitest` (no `@vitest/` scope) is the abandoned 2024 package.** The maintained
  one is `@vitest/eslint-plugin` — do not install the unscoped name.
- Stryker's incremental diff (`reports/stryker-incremental.json`) only sees mutated and test
  files changing; commit the file or add it to `.gitignore`, either is fine, but do not delete it
  between runs or every run becomes a full run.
