# Kotlin

Researched on: 2026-09-11 (versions read from Maven Central/plugin portal that day).
Last real run: none yet — the first project with this language corrects it.

## Detect
`build.gradle` or `build.gradle.kts` at the root or up to two directories down — same markers as
Java. A Gradle project counts as Kotlin, not Java, when a `.kt` file exists under a `src/`
directory at the root or up to two directories down (so a module layout like
`app/src/main/kotlin/A.kt` alongside `app/build.gradle.kts` still counts); `detect.languages`
drops Java from the result for that project so the two never both run.

## Run
`./gradlew test` (or `gradle test` without the wrapper). JUnit 5.

**What zero tests looks like.** Gradle exits 0 on a test task with no sources — `> Task
:app:testDebugUnitTest NO-SOURCE`, then `BUILD SUCCESSFUL` — so the exit code cannot say whether
anything ran (BACKLOG #67). `run` reads the JUnit XML the test tasks write under each module's
`build/test-results/` instead: no XML anywhere under the project is `0 tests ✗`; otherwise the
line carries the real count. Gradle removes a test task's results when its sources go away
(confirmed live, Gradle 9.3.1), so a deleted suite cannot pass on last week's XML.

**Flutter's `android/` is a special case.** Its `settings.gradle.kts` includes every plugin from
`~/.pub-cache`, so a bare `gradlew test` runs those plugins' unit tests too (orcweather:
`shared_preferences_android` ran 12 and failed one that is not orcweather's). Their XML lands
in the pub cache, outside the project, so `run` never counts them — but their failure still
fails the build. Declare the app module's task in `.orclab/test.yaml` — both commands, because
`koverXmlReport` depends on `test` and drags the same plugin suites in with it — until BACKLOG
#68 makes that the default:

```yaml
languages:
  kotlin:
    test: ./gradlew :app:testDebugUnitTest
    coverage: ./gradlew :app:testDebugUnitTest :app:koverXmlReport
```

Flutter also relocates every module's build directory under the project root — note the shape,
because the module's name goes where `build` was: `<project>/build/app/`, not `android/app/build/`.
Two things live there. The JUnit XML `test_summary` reads is handled (it searches the repository and
keeps what this run wrote), but Kover's report lands in `<project>/build/app/reports/kover/` where
`jacoco.find` does not look. Name the file in
the build script rather than hoping the two agree:
`kover { reports { total { xml { xmlFile = file("${rootProject.projectDir}/build/reports/kover/report.xml") } } } }`.

## Coverage
Kover 0.9.9 (`org.jetbrains.kotlinx.kover` Gradle plugin; 0.9.1 and earlier cannot see AGP 9's
built-in Kotlin and fail at configuration time): `./gradlew test koverXmlReport` →
`build/reports/kover/report.xml`, written in JaCoCo's own XML shape, so `jacoco.parse` reads it
unchanged (`jacoco.find` already checks this path). A project-side gate is `kover { reports {
verify { rule { minBound(80) } } } }` in the build file. Override the whole command with
`languages.kotlin.coverage` in `.orclab/test.yaml` when the default runs the wrong module.

## Mutation (TCE)
Pitest, and on Android **without a Gradle plugin, because none works** — confirmed live 2026-09-27
(BACKLOG #88). `info.solidsoft.pitest`'s own FAQ: *"Short answer is: not directly"*, pointing at
Karol Wrótniak's Android fork; that fork (`pl.droidsonroids.gradle.pitest`) last shipped **0.2.12 in
November 2022** and on Gradle 9 fails to apply at all — *"Cannot mutate configuration container for
buildscript of project ':app'"*. Pitest itself is current (1.30.0, August 2026) and works fine; it
only needs a classpath. A plain `JavaExec` task named `pitest` in the app module is the whole thing,
and `mutation_unavailable` looks for that word in any of the project's build files:

```kotlin
val pitestTool: Configuration by configurations.creating
dependencies {
    pitestTool("org.pitest:pitest-command-line:1.30.0")
    pitestTool("org.apache.commons:commons-text:1.15.0")   // pitest's XML writer needs it
}

afterEvaluate {
    val unitTest = tasks.named<Test>("testDebugUnitTest")
    val mainClasses = layout.buildDirectory.dir("tmp/kotlin-classes/debug")
    tasks.register<JavaExec>("pitest") {
        dependsOn(unitTest)
        workingDir = projectDir
        mainClass.set("org.pitest.mutationtest.commandline.MutationCoverageReport")
        classpath(pitestTool, mainClasses, provider { unitTest.get().classpath })
        doFirst {
            val code = mainClasses.get().asFile.path
            args("--classPath", (listOf(code) + unitTest.get().classpath.files.map { it.path }).joinToString(":"),
                 "--mutableCodePaths", code,
                 "--targetClasses", "<your package>.*", "--targetTests", "<your package>.*",
                 "--sourceDirs", "src/main/kotlin",
                 "--reportDir", "${rootProject.projectDir}/build/reports/pitest",
                 "--outputFormats", "XML", "--threads", "4", "--timeoutConst", "15000")
        }
    }
}
```

Four things in there each cost a run to find:

- **`workingDir = projectDir`.** Robolectric reads the merged-resources APK by a path relative to the
  module. Run from the language's directory and it resolves outside the project: every Robolectric
  test dies with `Failed to open APK ... Error -2147483643` and pitest reports the build unsuitable.
- **The code under test on `classpath` as well as in `--classPath`.** With only pitest's own jars on
  the JVM classpath, its pre-scan finds nothing and it exits `No mutations found`, which reads
  exactly like a wrong filter.
- **`commons-text`.** `pitest-command-line` does not bring it, and without it the run completes and
  then dies writing the report: `ClassNotFoundException: org.apache.commons.text.StringEscapeUtils`.
- **`--timeoutConst 15000`.** Robolectric boots an Android runtime per test class; the default
  allowance is sized for plain JVM tests and scores most mutants as timeouts.
- **`--reportDir` named explicitly**, for the same reason Kover's is: Flutter relocates the build
  directory and `pitest.find` searches `<language dir>/build/reports/pitest`.

Last real run: orcweather, 2026-09-27 — 265 mutations, 130 killed, **49%**, 66 with no coverage,
48 seconds over 29 test classes on this machine.

## Test lint
detekt (no version pinned; run via its CLI). It has no test-specific rule set — an `@Disabled`
test or an assertion-free test body is not caught. The fallback there is a plain
`grep -rn '@Disabled'` (or eyeballing), not run automatically by `cli.py`.

## Audit
OWASP dependency-check 13.0.0's Gradle plugin, confirmed live 2026-09-19 against
https://dependency-check.github.io/DependencyCheck/dependency-check-gradle/configuration.html
and https://plugins.gradle.org/plugin/org.owasp.dependencycheck — the Gradle half of
`languages/java.md`'s Audit section, which `langs/kotlin.py` reuses outright (same
`audit_findings`). Installed means `build.gradle(.kts)` has
`id("org.owasp.dependencycheck") version "13.0.0"` **and** `dependencyCheck { formats =
listOf("JSON") }` — **in the root build file**, because `cli.py` reads the root's report; a
plugin applied only in `app/build.gradle.kts` writes `app/build/reports/…` and the audit fails
loud (log printed, "output not understood") rather than reading nothing as clean. A multi-module
build wants `dependencyCheckAggregate`, not wired here. Then `./gradlew dependencyCheckAnalyze`
writes `build/reports/dependency-check-report.json`, which `cli.py` removes beforehand, then
prints and reads (the build's own output goes to `build/reports/dependency-check.log`; a build
that fails before writing the report prints the log instead, never last run's report). Exit
code ignored: `failBuildOnCVSS`
defaults to 11 and *"the build will not fail by default"*. First run downloads the NVD (20+
minutes; get an API key — `nvd.apiKey` in the block, from an environment variable, not in the
file). Last real run: none yet.

## Caveats
- **The Arcmutate caveat printed by `/orc-test analyze` reads two things: the licence the
  project declares, and whether the Gradle build file mentions `arcmutate`.** With neither, "TCE
  is approximate" (junk mutants included) and the licence is named as the blocker. With a
  recognised open-source licence but no `arcmutate` in the build, still approximate — and the
  caveat says the plugin would be free and names the dependency to add
  (`com.arcmutate:pitest-kotlin-plugin`). With both, TCE is reported as via Arcmutate. It never
  runs Arcmutate itself or confirms the plugin resolved on the build's classpath.
- **A private repo carrying an MIT `LICENSE` file passes the licence check anyway.** Arcmutate's
  own free-for-open-source term means *publicly* available, not merely MIT-licensed source sitting
  in a private repository — `licence.open_source` only reads the file's declared licence, it has
  no way to see whether the repository itself is public. That distinction stays the project's own
  to keep straight.
