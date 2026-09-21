# PHP

Researched on: 2026-09-20 (versions read from php.net, Packagist and PECL that day, in
`skills/stack-php/SKILL.md`'s `## Toolchain` and `## The stack decision`). Last real run:
2026-09-20, in a container — podman 4.9.3 / podman-compose 1.0.6, rootless, the v24check sample
project (Slim 4.15.3, PHPUnit 13.3.4 with PCOV 1.0.12, Infection 0.35.4, on PHP 8.5.10):
`python3 skills/orc-test/scripts/run.py --cwd <scratch>/v24check detect` → `detected: PHP (in
container)`; `run` → `PHP        ✓ passed (0.4s)`; `coverage` → `PHP        coverage 20.0%
(1/5 lines) ✗ (min 80)` with `0.0%  .../src/GreetAction.php` (untested) and the html-report
line; `analyze` → the same coverage block, then `TCE 20.0% ✗ (min 70)    lint: not run — no
test-specific lint exists for PHP (no PHPStan rule reports an assertion-free test)` (2 of 10
mutants killed, 8 uncovered, 0 escaped on the real, unweakened suite — `gates failed: coverage,
tce`); `audit` → `PHP        audit ✓ 0 vulnerable`. This is the first run of this module through
`compose run`; every fix below is what that run taught, not what the research alone found
(`skills/stack-php/SKILL.md`'s `## Containers`, Task 2).

## Detect
`composer.json` at the root or up to two directories down.

## Run
`vendor/bin/phpunit [target]`. Config is `phpunit.xml` at the project root, read by PHPUnit
itself; `run.py` passes no options of its own for a plain run. `target` is a PHPUnit path/filter
argument (a test file or directory), passed through as-is — there is no source-vs-test split to
resolve, unlike Python's `--ignore-glob=*mutants/*` dance, because PHP's tools have nothing
comparable to mutmut's `mutants/` copy sitting in the tree.

## Coverage
`vendor/bin/phpunit --coverage-clover .orclab/test/php/clover.xml --coverage-html
.orclab/test/php/html [target]`. `run.py` reads the Clover XML: one `<file name=>` per source
file, each with a `<metrics statements= coveredstatements=>`; the project total is the same pair
one level up, under `<project>`. `<file name=>` is the **absolute path inside the container**,
which under Orclab's `compose.yaml` (the project mounted at its own host path) is the same
absolute path the rest of `/orc-test` already works with — no translation needed. PHPUnit prints
`Runtime: PHP 8.5.10 with PCOV 1.0.12` when the coverage driver loaded; the same line without
`with PCOV` means no report will be written, and `coverage_parse` then returns `Coverage(0, 0)`.

## Mutation (TCE)
Infection 0.35.4: `vendor/bin/infection --no-interaction --no-progress --threads=max
--with-uncovered [--filter=<target>]`. Config is `infection.json5` at the project root (or
wherever the marker directory is); `mutation_unavailable` requires `infection/infection` in
`composer.json`'s `require-dev` and an `infection.json5`/`infection.json` present — Infection
writes the former on its own first interactive run. Since `mutation_cmd` passes no logger flag
(Infection has none), `mutation_unavailable` also refuses an `infection.json5` with no `logs.json`
key — without it a full run would end in `Mutation(0, 0)` with no way to find the real log.

**Infection has no `--logger-json` option.** Its command-line-options page (read 2026-09-20)
lists `--logger-text`, `--logger-html`, `--logger-summary-json` (stats only), `--logger-github`,
`--logger-gitlab` — nothing that names an arbitrary path for the full log. The full log's path
is instead `infection.json5`'s own `logs.json` key (`.orclab/test/php/infection.json` in the
sample); `mutation_parse` reads that key — resolved relative to the project root — and falls
back to `<out>/infection.json` when the file is absent, the key is absent, or the file is real
JSON5 (comments and trailing commas are legal there) beyond what a `//`-comment-stripping
fallback can parse: `_infection_log_path` never lets a config file it cannot fully read raise
out of `mutation_parse` — a hand-edited `infection.json5` with a trailing comma degrades to the
`<out>/infection.json` fallback rather than crashing `analyze`.

**`--with-uncovered` is deliberate, not optional.** Since Infection 0.31 the default mutates
covered code only (*"`--only-covered` … was removed in Infection 0.31.0, use `--with-uncovered`
instead"*); without the flag an entirely untested file is simply absent from the count — the
sample's untested route handler gave `2 mutants, MSI 100` without it, `10 mutants, 8 uncovered,
MSI 20` with it. Stryker's and PITest's parsers here already count an uncovered mutant as alive
(`NoCoverage`/`NO_COVERAGE`), so the flag is what makes PHP's TCE mean the same thing as every
other language's.

`mutation_parse` reads the log's `stats` block (`totalMutantsCount`, `killedCount`,
`timeOutCount`, `errorCount` — the last two count as killed, matching how a timeout or a harness
error is read elsewhere) and **both** the `escaped` and the `uncovered` lists for survivors —
`--with-uncovered` counts an uncovered mutant in the denominator too, so a survivor list built
from `escaped` alone would never tell `/orc-test generate` that a whole file is untested; the
same "alive but no test reaches it" case `stryker.py`/`pitest.py` already list and tag for their
own tools. Each entry's `mutator.originalFilePath` (absolute, made root-relative the same way
Clover's `file name=` is) and `mutator.originalStartLine` become the survivor's file and line;
the description is `mutator.mutatorName`, with `" (no test reaches it)"` appended for an
`uncovered` entry so the two cases read differently in the report.

## Test lint
No tool. PHPStan (2.2.14, `vendor/bin/phpstan analyse`) has no rule that reports an
assertion-free test — checked against its rule list 2026-09-20. The test smell PHP has instead
is structural: PHPUnit marks an assertion-free test *risky* and still exits 0, but **Infection's
own initial test run fails on a risky test and refuses to proceed** (*"Project tests must be in
a passing state before running Infection"*) — so an assertion-free test blocks mutation testing
outright rather than silently scoring 100%. `lint` always returns this explanatory string; there
is nothing to run.

## Audit
`composer audit --format=json --locked` (Composer 2.10.3). `--locked` reads `composer.lock`
directly, so it works before `composer install` and gives the same answer after it;
`audit_nothing` checks for `composer.lock` first and reports "nothing declared" (not a gate
failure) when it is absent, before `composer` itself is ever checked. Exit 0 clean, 1 with
findings. The JSON's top-level `advisories` key is **a dict keyed by package name when there are
findings, and a list (`[]`) when there are none** — PHP's `json_encode` turns an empty
associative array into a JSON array, not an object — so `audit_findings` accepts both shapes and
treats a non-dict as empty. Each advisory carries `advisoryId`, `affectedVersions`, `title`,
`cve` (a string in every advisory seen; not guaranteed by the docs) and `link`; `run.py` reports
`<package> <affectedVersions>: <cve or advisoryId> — <title>`. `run.py` merges stderr into
stdout, and Composer can print a "could not detect the root package version" line there ahead of
the JSON, so `audit_findings` finds the JSON from the first `{` rather than assuming the whole
capture is JSON, the same pattern `python.py`/`javascript.py` already use for their own tools'
stray stderr lines.

## Caveats
- **First real project (orcweather `server/`, 2026-09-20)** found two misreads, both fixed that
  day: its `infection.json5` carries a `//` comment at the *end* of a line, which the whole-line-only
  stripper could not read, so `run.py` fell back to `<out>/infection.json`, found nothing, and said
  "produced no mutants" beside a 407-mutant log (BACKLOG #72; end-of-line comments and trailing
  commas are now read, block comments still degrade); and its container mounts only `server/`, so
  `--coverage-clover <root>/.orclab/test/php/clover.xml` was written inside the container and lost —
  phpunit said "done" and `run.py` said "no coverage report found" (BACKLOG #70; reports now land
  beside the marker).
- **`vendor/bin/phpunit`, `infection` and `phpstan` are the project's own `require-dev`
  packages**, installed by `composer install` — the one thing the project runs itself, once, and
  again whenever `composer.json` changes.
- **Infection needs a coverage driver (PCOV or Xdebug) loaded in the PHP that runs it.** Without
  one, coverage-guided mutation cannot tell which tests reach which mutant. The sample's image
  builds PCOV 1.0.12 via `pecl install pcov-1.0.12 && docker-php-ext-enable pcov`; Infection
  passes PHP's `-d pcov.directory=<src>` itself, and PHPUnit 13 needs no extra flag or mode
  switch for PCOV.
- **`php:8.5-cli` has neither `unzip`/`7z` nor the `zip` extension**, and Composer's archives are
  zips — `composer install` fails outright without one of them. `unzip` (Composer's own
  introduction page names it among its decompression tools) is the fix used here; the `zip`
  extension route also works but loses executable-bit permissions on unpacked files, which
  Composer itself warns about.
- **`COPY --from=composer:2` fails on Podman** (*"no stage or image found with that name"*) —
  there is no `composer` short-name alias the way `php` has one, so the bare form has nowhere to
  resolve to on an engine without `unqualified-search-registries`. The fix is the fully-qualified
  `docker.io/library/composer:2`, which needs no alias on either engine.
- **`podman compose build` can exit 0 on a failed build** (podman-compose 1.0.6's own quirk,
  `skills/orc-test/SKILL.md`'s Containers section) — read the build output for `COMMIT`/
  `Successfully tagged` rather than trusting the exit code; `container.build_failed` already
  checks for the logged `exit code: N` line, so this is handled for every language, not just PHP.
- **Composer 2.10 refuses to lock a version a published advisory affects** by default
  (`policy.advisories.block`), so a real project's `composer.lock` reaches a `composer audit`
  finding only via an advisory published after the lock was written, or a deliberate
  `--no-blocking` update — not a routine `composer require`.
