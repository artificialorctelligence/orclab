# C#

Researched on: 2026-09-11 (versions read from NuGet that day). Last real run: none yet — the
first is Task 19 of the v17 plan, on Orclab itself.

## Detect
`*.csproj` or `*.sln` at the root or up to two directories down.

## Run
`dotnet test [path]` — runs xUnit or NUnit tests, whichever a project references. A project's
own `*.runsettings` is honoured by `dotnet test` itself.

## Coverage
coverlet.collector 10.0.1, built into `dotnet test`: `dotnet test [path] --collect:"XPlat Code
Coverage" --results-directory=<out> -- DataCollectionRunSettings.DataCollectors.DataCollector
.Configuration.Format=lcov`. Coverlet writes `<out>/<guid>/coverage.info`; `run.py` takes the
newest `coverage.info` (or `*.lcov`) found anywhere under `<out>` and reads it with the shared
`lcov.py` reader. Alternative, not used here: `Microsoft.Testing.Extensions.CodeCoverage` 18.11.2,
for projects on Microsoft.Testing.Platform rather than VSTest. For a project-side gate in CI,
`coverlet.msbuild`'s own switches are `/p:Threshold=80 /p:ThresholdType=line`.

## Mutation (TCE)
Stryker.NET 5.0.0 (released 2026-09-11, targets .NET 10; pin 4.16.0 on an older SDK — see
Caveats): `dotnet stryker --reporter json --reporter progress --with-baseline --output
.orclab/stryker-net`. It writes the same Stryker JSON schema (v2) as StrykerJS and dart_mutant;
`run.py` reads it through the shared `stryker.py` reader, which takes the newest `*.json` under
`.orclab/stryker-net` whose top level has a `"files"` key. A path argument becomes `--mutate
<path>/**/*.cs`. Incremental: as of 5.0 the baseline (incremental) state is stored under the
output path itself, not a separate file — which is why the output is *not* `.orclab/test/csharp/`
(emptied at the start of every run) but `.orclab/stryker-net/` beside it, which `run.py` never
deletes, so the baseline is preserved from one run to the next. For a project-side gate in CI,
Stryker's own switch is `--break-at 70`.

## Test lint
`xunit.analyzers` 2.0.0 runs as part of `dotnet build` itself — no separate invocation. `run.py`
runs `dotnet build --no-incremental -warnaserror- [path]` and parses `xUnit####` warnings from its
output: `xUnit1004` (test skipped), `xUnit2013` (`Assert.Equal` used to check a collection size),
`xUnit1013` (public method not marked as a test), among others. NUnit projects instead get
`NUnit.Analyzers` warnings, reported as `NUnit####` — not yet parsed here, a known gap.

## Caveats
- **Stryker.NET 5.0.0 targets .NET 10.** On an older SDK, pin the 4.16.0 global tool instead:
  `dotnet tool install -g dotnet-stryker --version 4.16.0`.
- `dotnet-stryker` is installed as a global .NET tool and found on `PATH` as `dotnet-stryker`,
  even though it's invoked as `dotnet stryker`.
- Test lint only parses `xUnit####` codes; an NUnit project's `NUnit####` warnings pass through
  `dotnet build`'s output unreported for now.
