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

## Coverage
Kover 0.9.9 (`org.jetbrains.kotlinx.kover` Gradle plugin): `./gradlew test koverXmlReport` →
`build/reports/kover/report.xml`, written in JaCoCo's own XML shape, so `jacoco.parse` reads it
unchanged (`jacoco.find` already checks this path). A project-side gate is `kover { reports {
verify { rule { minBound(80) } } } }` in the build file.

## Mutation (TCE)
Pitest 1.30.0 via the `info.solidsoft.pitest` Gradle plugin — same as Java's Gradle path, same
report location (`build/reports/pitest/mutations.xml`), read by the same `pitest.parse`. Plain
Pitest runs against Kotlin bytecode and reports mutants in compiler-generated code (null checks,
default-argument dispatchers) that no test could plausibly kill — junk, not real survivors.

**Arcmutate's Kotlin plugin** (`com.arcmutate:pitest-kotlin-plugin`, requires pitest ≥ 1.22.0)
filters those out. It is commercial, but free for open source — verified by an
`arcmutate-licence.txt` file at the project root, which `cli.py` does not check; instead
`licence.open_source(root)` reads the project's own `LICENSE`/`LICENCE`/`COPYING` file or its
`pyproject.toml`/`package.json` `license` field, the same declaration every other gate already
reads, never a new setting. The original `pitest-kotlin` open-source plugin is unmaintained —
don't reach for it.

## Test lint
detekt (no version pinned; run via its CLI). It has no test-specific rule set — an `@Disabled`
test or an assertion-free test body is not caught. The fallback there is a plain
`grep -rn '@Disabled'` (or eyeballing), not run automatically by `cli.py`.

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
