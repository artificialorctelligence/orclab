# Orclab v12: artifact preflight — design

## Goal

Stop `/orc-publish` from irreversibly publishing an artifact nobody looked at. A leaf may declare
what it publishes and which checks apply; the checks run **after the artifact is built and before
the irreversible step**, and a failure means the publish never happens.

Closes **BACKLOG #21**.

## Why this exists

Measured from real tarballs while releasing Orcshot `0.3.0`, not reasoned about afterwards:

| Tarball | `.git` entries | agent-state entries | Size |
|---|---|---|---|
| `0.1.1-3` (**uploaded, public**) | 1,415 | 0 | 10.8 MB |
| `0.2.0-1` (**uploaded, public**) | 1,882 | 3 | 14.8 MB |
| `0.3.0-1` (caught before upload) | 3,061 | 1,330 | 22.6 MB |

By `0.3.0` the payload carried whole stale git worktrees containing a built `.deb` and a `.whl` —
prebuilt binaries inside a *source* package. After the fix the same tarball was 1.02 MB.

**There is no undo.** A PPA will not accept a re-upload of an existing version; a mistake costs a
version number permanently and the bad artifact stays public.

**The argument for inspecting the artifact rather than trusting the build config** is that the
config was actively wrong about itself. `debian/source/options` listed `tar-ignore` patterns and
its own comment claimed the default VCS/backup exclusions were active. They never were — per
`dpkg-source(1)`, those defaults apply only when `-I` appears with no pattern. The config asserted
an exclusion set it had never enabled, and nothing downstream ever compared the claim to the
output. A check that reads the produced artifact would have caught this on the *first* release.

## Scope

**In scope:**
- Three additive leaf fields: `prepare`, `artifact`, `preflight`.
- An artifact inspector over tar and zip archives, with three named rule sets.
- A new `refused` result status, distinct from `failed`.
- A heuristic warning for an action that builds and irreversibly publishes in one shell string.
- One `release-checklist` prose rule.

**Explicitly out of scope:**
- **Producing artifacts correctly.** That is the project's packaging config. Orcshot's own
  `debian/source/options` fix is already committed on its side.
- **Post-publish verification** — "did it land, and is it what I meant?" That is **#18**, and this
  spec deliberately does not absorb it. #21 is "don't ship the wrong thing"; #18 is "know whether
  it arrived."
- **A size-anomaly rule.** See "Deliberately cut" below.
- **Any change to `/orc-release`.** Preflight is reached through `/orc-publish` as it already is.

## The ordering problem, and why it is not what it first looks like

Orcshot's `ppa.noble` action is one string:

```
dpkg-buildpackage -us -uc -S -sa && debsign -k… && dput ppa:… 
```

The first framing of this design claimed such a leaf "cannot adopt preflight, because the action
creates the artifact it publishes." **That was wrong**, and direflail rejected it correctly: the
tarball exists after the first command, `debsign` is local and reversible, and only `dput` is
irreversible. There is a perfectly good inspection point inside that chain.

The real constraint is narrower: `/orc-publish` hands the whole string to `sh -c`, so it cannot
inject a gate *between two commands inside one opaque string*. That is a limitation of how actions
are modelled, not of when artifacts exist. So the fix is not "restructure your release" — it is
"give the leaf a way to say where the gate goes."

This also answers **#12**'s standing complaint that `ppa.noble` "had to smuggle a build into what
is nominally a publish action." `prepare:` gives the build a declared home and the smuggling stops
being necessary.

## Design

### Leaf fields

```yaml
noble:
  prepare:   "dpkg-buildpackage -us -uc -S -sa"
  artifact:  "../orcshot_<version>.tar.xz"
  preflight: [no-vcs, no-tool-state, no-prebuilt-binaries]
  action:    "debsign -k… && dput ppa:… "
```

- **`prepare`** — an optional command run before the gate. Local, reversible work: building the
  artifact. Runs under the leaf's own timeout, exactly as `action` does.
- **`artifact`** — the path to inspect, relative to the working directory. **It must name the
  archive itself.** Orcshot's existing `filename_template` names the `.changes` file, which is a
  manifest, not an archive — inspecting that would be the lint-the-sibling bug in miniature.

  **The path is shell-expanded, exactly as `action` already is**, so a project derives the version
  the same way it already does in its action:
  `../orcshot_$(dpkg-parsechangelog --show-field Version).tar.xz`. The first draft of this spec
  instead specified a `<version>` placeholder, copying the dormant `filename_template` field — but
  that field's helper, `render_filename(template, version)`, has never had a caller, so nothing in
  `/orc-publish` knows a version at all. Inventing version plumbing to fill a placeholder would be
  building a mechanism the project already has. Same trust boundary as `action`: it is the
  project's own config.
- **`preflight`** — the rule sets that apply, by name. Opt-in per leaf, never global.

All three are optional. A leaf declaring none behaves exactly as it does today, so no existing
configuration changes behaviour, and Orcshot's leaf adopts this by moving one command across a
line.

**Remove `filename_template` and `render_filename` as part of this.** The field is in `LEAF_KEYS`,
`Node.filename_template` parses it, `render_filename` is implemented and unit-tested, and nothing
in the main flow has ever called any of it — shipped dead in v7. `artifact:` supersedes what it was
for. Leaving a dead field that looks like it names the published file, beside a live one that
actually does, is a trap for the next reader. Orcshot's config sets it and will need it dropped
when it adopts `artifact:`.

**Why named rules rather than a per-leaf glob list:** the rules are the distilled knowledge, which
is Orclab's actual product. A raw pattern list would make every project retype what this incident
taught. Opt-in matters because the rules are format-specific in a way that cannot be globalised —
a `.snap` is squashfs and legitimately *contains* `.so` files.

### Execution order

For each selected leaf, in order:

1. If `prepare` is set, run it. A non-zero exit fails the leaf; `action` never runs.
2. If `preflight` is set, resolve `artifact` and inspect it. Any rule tripping refuses the leaf;
   `action` never runs.
3. Run `action` as today.

`prepare` failing is a `failed` leaf, with its real stderr, exactly as an action failure is.

**Dry-run never runs `prepare`.** It is a real command with real side effects, and dry-run resolves
and prints only. So a dry-run inspects the artifact only if it already exists: if it does, the
findings are printed in the Step 2 plan; if it does not, the plan says the inspection will run
after `prepare` at execution time. Saying "will inspect later" is honest; running a build during a
dry-run is not.

### Refusal

A tripped rule produces a new status, **`refused`** — distinct from `failed` for the same reason
`timed out` is: the cause is materially different and the fix is different. `failed` means a
command you ran returned non-zero. `refused` means nothing ran, because what you were about to
publish is wrong.

Non-zero exit from `main`, like `failed` and `timed out`. Independent leaves continue, as always.

The detail names the rule and the offending entries, **capped at the first five with a total
count**. This is deliberate: 3,061 `.git` entries would bury the summary, and today's #15 fix
already taught that what the operator actually reads matters as much as what is true.

### Override

`--allow-preflight-failure` downgrades every refusal to a warning for that run. It must be typed;
there is no config-level opt-out, and every finding is still printed in full. An irreversible
publish over a known-bad artifact should require a deliberate keystroke.

### Rules

| Rule | Rejects any path component or name matching |
|---|---|
| `no-vcs` | `.git`, `.hg`, `.svn`, `.bzr`, `CVS` |
| `no-tool-state` | `.claude`, `.orclab`, `.hypothesis`, `.venv`, `venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `node_modules` |
| `no-prebuilt-binaries` | `*.deb`, `*.whl`, `*.so`, `*.so.*`, `*.exe`, `*.dll`, `*.dylib`, `*.pyd` |

Every one of the three real uploads trips at least one.

### Formats

`tarfile` and `zipfile` from the standard library — `.tar`, `.tar.gz`, `.tar.xz`, `.tar.bz2`,
`.zip`, `.whl`. Nothing else, and no new dependency.

A `preflight` declared on a format the inspector cannot read is **refused**, with a detail saying
the format is unsupported rather than naming a rule — the leaf is declining for a configuration
reason, not because the archive's contents are wrong. Never a silent pass. A silent pass on an uninspectable artifact is the exact failure this entry
exists to prevent, wearing a green tick.

### The action-shape warning

Separately from preflight, and applying to every leaf including those that declare nothing:
inspect the `action` string statically at dry-run time. If it contains an irreversible publish verb
(`dput`, `snapcraft upload`, `twine upload`, `npm publish`, `gh release create`, `cargo publish`)
preceded in the same string by a build verb (`dpkg-buildpackage`, `debuild`, `python -m build`,
`flatpak-builder`, `cargo build`), report it:

> `desktop.python.linux.ppa.noble: action builds and irreversibly publishes in one command — no
> gate can run between them. Split the build into prepare: to enable preflight.`

**This warns, it does not refuse**, and the distinction is principled: the content rules are
deterministic checks of real bytes, while this is a regex over a shell string and will have false
positives. Refusing on a heuristic would be the wrong trade. Its value is that it catches the bad
shape on configurations that have not adopted preflight at all.

## Deliberately cut

**The size-anomaly rule** ("warn when the artifact is wildly out of line with the last release").
It needs a baseline, which means persistent state Orclab does not keep, and it is by far the most
false-positive-prone of the four — a release can legitimately triple. All three real incidents trip
a content rule, so cutting it costs nothing measurable and removes the only piece needing
persistence. Raise it as its own entry if a real case ever slips past the content rules.

## The other half: `release-checklist`, no code

One rule, from the same incident:

> **Lint the thing you are shipping, not its sibling.** A verification step must be pointed at the
> artifact the release actually publishes. Orcshot ran `lintian` on the binary `.deb` and passed
> clean every release, while the *source* package being uploaded in the next step was the broken
> one. A checklist that verifies one artifact and ships a different one has a blind spot by
> construction, however good either check is.

This generalises past Debian and past this design — it is worth stating even for projects that
never adopt preflight.

## Testing

Bundled-script tests in the existing suite, `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`:

- **Inspector**: synthetic tarballs and zips built in `tmp_path`, one per rule, plus a clean
  archive that trips nothing; entry reporting capped at five with a correct total.
- **Ordering**: `prepare` runs before inspection; a refused leaf never runs its `action` (assert via
  a sentinel file the action would create); a failing `prepare` also never reaches `action`.
- **Statuses**: `refused` is distinct from `failed`; `main` exits non-zero on a refusal; a refused
  leaf does not stop a following leaf.
- **Dry-run**: never runs `prepare` (sentinel again); reports findings when the artifact exists and
  says inspection is deferred when it does not.
- **Formats**: an unreadable format with `preflight` declared is refused, not passed.
- **Override**: `--allow-preflight-failure` runs the action and still prints every finding.
- **Action shape**: the warning fires on a build-then-publish string and not on a bare `dput`.

A `VERIFICATION.md` scenario covers what unit tests cannot: that a real refusal *reads* correctly
to an operator — the rule named, the entries capped, the reason legible without hunting. #15's
defect passed every substring assertion and was only visible in rendered output.

## Global constraints

- No new dependency; `tarfile` and `zipfile` are stdlib.
- Every new leaf field is optional and no existing configuration changes behaviour.
- `/orc-publish` continues past an independent leaf's refusal, as it does for failure and timeout.
- Orclab ships the mechanism; no project's content is written here. Orcshot adopting this is its
  own work, in a session centred on it.
