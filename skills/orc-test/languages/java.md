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

## Audit
OWASP dependency-check 13.0.0 (released 2026-08-03; Maven Central's `maven-metadata.xml` and
the Gradle plugin portal both say 13.0.0 — the older jeremylong.github.io mirror of the docs
still shows 12.1.0, read the dependency-check.github.io one), confirmed live 2026-09-19 against
https://dependency-check.github.io/DependencyCheck/dependency-check-maven/check-mojo.html and
https://dependency-check.github.io/DependencyCheck/dependency-check-gradle/configuration.html.
Maven has no native audit (checked maven.apache.org the same day: the dependency plugin's
`analyze` is about unused declarations, not advisories). It is a build plugin, so "installed"
means the build file names it — `cli.py` never adds it:

- Maven: `org.owasp:dependency-check-maven` under `<plugins>` in `pom.xml`, then
  `mvn -q org.owasp:dependency-check-maven:check -Dformat=JSON`; the report is
  `target/dependency-check-report.json` (`outputDirectory` default
  `${project.build.directory}`, *"This generally maps to 'target'"*). `check` runs per module;
  a multi-module build wants `aggregate`, not wired here.
- Gradle: `id("org.owasp.dependencycheck") version "13.0.0"` **and**
  `dependencyCheck { formats = listOf("JSON") }` in `build.gradle(.kts)` — the format is
  build-file config with no command-line property, so the JSON has to be asked for there — then
  `./gradlew dependencyCheckAnalyze` (or `gradle`); the report is
  `build/reports/dependency-check-report.json` (`outputDirectory` default `${buildDir}/reports`).

Exit code: ignored. `failBuildOnCVSS` — *"The default is 11 which means since the CVSS scores
are 0-10, by default the build will never fail"* — and the report is written before that check
in any case, so `audit_findings` reads the report. Because `cli.py` only sees the command's
stdout, the command is a one-line `sh -c` that sends the build's own output to
`dependency-check.log` beside the report and then prints the report; when no report was written
the log is printed instead and lands on "output not understood" with the reason above it. One
line per (jar, advisory): `commons-io-2.6.jar: CVE-2021-29425 (MEDIUM) — fix not reported by
dependency-check` — it matches CPEs against the NVD and names no fixed version; one CVE listed
by two sources (NVD and OSS Index) for the same jar is one line. **The first run downloads the
NVD: *"it may take 20 minutes or more"*, and the docs recommend an NVD API key
(`nvdApiKeyEnvironmentVariable`, never `-DnvdApiKey=` — *"Maven debug logging could expose the
API Key"*).** Subsequent runs within seven days take seconds. Last real run: none yet.

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
