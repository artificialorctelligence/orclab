# Worked example: a RELEASING.md excerpt

Adapted from a real project's release checklist, showing the pattern: numbered steps in
dependency order, commands given exactly, judgment calls stated plainly, and CI cross-referenced
rather than silently duplicated.

## 1. Pick a version

Decide the new version number (semver: `MAJOR.MINOR.PATCH`). Update it everywhere the project
records its own version — if there's more than one place, list them explicitly and note that they
must match, since a mismatch here is a real, silent failure mode later.

## 2. Full test suite

    pytest tests/ -q

Must be fully green before continuing. This step, and the build/lint steps below, now also run
automatically on every push and PR via `.github/workflows/ci.yml` — running them by hand here is
still the fastest local feedback loop, not a redundant step; see the final step for cross-checking
CI's own view before release.

## 3. Security check

Added after a real gap: an early release shipped without ever running a dependency/SAST scan.

    semgrep ci

Any new high/critical finding gets understood before continuing — not silently waved through, but
not automatically a blocker either; a finding can turn out to be a confirmed false positive.

## 4. Build

    <the project's real build command>

## 5. Tag and publish

    git tag vX.Y.Z && git push --tags
    <publish command for this project's real target(s)>

## 6. Confirm CI's own view

Check the CI dashboard for the tagged commit — a clean local run and a clean CI run are both
required; CI can catch environment differences a local run won't.
