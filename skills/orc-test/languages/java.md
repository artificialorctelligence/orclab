# Java

Researched on: 2026-09-11 (versions read from GitHub releases/Maven Central that day).
Last real run: none yet — the first project with this language corrects it.

## Detect
`pom.xml`, `build.gradle` or `build.gradle.kts` at the root or up to two directories down. A
`pom.xml` means Maven; otherwise Gradle, via `./gradlew` if the wrapper is present, else a
bare `gradle`.

## Run
Maven: `mvn -q test`, or `mvn -q test -Dtest=<pkg>.*` when the target narrows to a package under
`src/main/java/<pkg>`. Gradle: `./gradlew test` (or `gradle test`). JUnit 5 either way.

## Coverage
JaCoCo 0.8.15 (GitHub releases — **Maven Central's search API reported 0.8.13 that day; stale,
check GitHub**). Maven needs no pom change: `mvn -q org.jacoco:jacoco-maven-plugin:prepare-agent
test org.jacoco:jacoco-maven-plugin:report`, report at `target/site/jacoco/jacoco.xml`. Gradle
needs `plugins { jacoco }` and `jacocoTestReport { reports { xml.required = true } }` in the
build file, report at `build/reports/jacoco/test/jacocoTestReport.xml`. `run.py` reads that XML
(per-`<sourcefile>` `LINE` counters) and applies the 80% gate. For a project-side gate in CI,
JaCoCo's own switch is the `jacoco:check` goal with `minimum 0.80` on `LINE`. `jacoco.find` also
checks a third location, `build/reports/kover/report.xml` — Kotlin's Kover writes the same JaCoCo
XML shape there, so the same reader covers a Kotlin project sharing this language module.

## Mutation (TCE)
Pitest 1.30.0 (2026-08-27) + pitest-junit5-plugin 1.2.2. Maven:
`org.pitest:pitest-maven:mutationCoverage -DoutputFormats=XML,HTML -DwithHistory
-DtimestampedReports=false` → `target/pit-reports/mutations.xml`; incremental via
`-DwithHistory` (a history file under `target/`), and `scmMutationCoverage` narrows to
changed files only. Gradle needs the `info.solidsoft.pitest` plugin → report at
`build/reports/pitest/mutations.xml`. A target under `src/main/java/<pkg>` becomes
`-DtargetClasses=<pkg>.*` (Maven) — Gradle's plugin has no per-run equivalent, so a target there
doesn't narrow it. `KILLED`/`TIMED_OUT` count as caught, `SURVIVED`/`NO_COVERAGE` as survivors;
`NON_VIABLE`/`MEMORY_ERROR`/`RUN_ERROR` are not counted (the mutant itself was unusable, not a
verdict on the tests).

## Test lint
PMD 7's `category/java/bestpractices.xml` rules `UnitTestShouldIncludeAssert` and
`UnitTestContainsTooManyAsserts`, run as `pmd check -d src/test -f json` and read back as JSON.
PMD does not flag `@Disabled` tests — checked 2026-09-11 with PMD 7; the fallback there is a
plain `grep -rn @Disabled src/test`, not run automatically by `run.py`.

## Caveats
- **The JUnit 5 support for Pitest is a `<dependency>` nested inside the `pitest-maven` plugin's
  own `<plugin>` block, not a project dependency and not a CLI flag.** It does not go in the
  pom's top-level `<dependencies>`:
  ```xml
  <plugin>
    <artifactId>pitest-maven</artifactId>
    <dependencies>
      <dependency>
        <artifactId>pitest-junit5-plugin</artifactId>
      </dependency>
    </dependencies>
  </plugin>
  ```
  `mutation_unavailable` just checks for the string `pitest-junit5-plugin` anywhere in the pom
  (Maven) or for `pitest` in the build file (Gradle) before trying to run Pitest at all — it does
  not parse the XML structure, so it doesn't care which block the dependency sits in.
- **Pitest exits non-zero when the run falls below its own `mutationThreshold`.** Leave that
  setting unset in the project's pom/build file — `run.py` reads the XML report and applies the
  gate itself, the same rule as every other tool here (never the tool's own threshold).
