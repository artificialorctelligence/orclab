# Orclab v22: `security-discipline` — the rules every project carries, and the extra set for one that strangers can reach

**Status:** design, approved section by section in conversation 2026-09-19. It began as "add PHP
to `/orc-code`" and became this first, by direflail's decision: *"it's really important that we
run this securely"*, and — asked whether the general security rule comes before or after the PHP
stack skill — *"B. it needs to happen before anything."* PHP is v23 and starts when this ships.

## The problem

direflail is putting an API on DreamHost, which serves PHP and nothing else. The security question
came up before the language question: *"if running this sans framework is going to make us
vulnerable, i need to know now. i haven't run php in literally 20 years."* Then, generalised:
*"security needs to be a part of every project. what that means may depend on the project itself
(something running locally like orcshot doesn't need the security of something sitting out on a
webhost where bad actors can detect it)."*

**What should already have covered it, and why it didn't** (`CLAUDE.md`, "Before building
anything"): searched every shipped `SKILL.md`, `CLAUDE.md`, `BACKLOG.md` and the bundled scripts.

- `code-discipline` — seven rules on the *shape* of code; not one is about trust, input, secrets
  or transport. Its own "What this is not" lists style and tests, not security, because nobody had
  asked.
- `test-discipline` — "know the scenarios first"; never names the hostile scenario.
- `secret-hygiene` — keeps a credential out of the *transcript*. It is the right skill for that and
  the wrong one for "never in the repo, never in the built artifact".
- `aikido:scan` — a real SAST plugin, installed on this machine, not part of Orclab; a consuming
  project cannot be assumed to have it.
- `code-modernization:security-auditor` / `modernize-harden` — a scanner for *existing* code with a
  reviewable patch. Right tool for the refactor case; nothing for a project being born.

Nothing in Orclab says "this project is reachable by people you did not invite, so these rules
apply." That is the gap, and it is a discipline skill, not a per-stack section alone, because the
question is the same for every stack.

## What is decided

### 1. The skill

`skills/security-discipline/SKILL.md`, `user-invocable: false`, sibling to `code-discipline` and
built the same way: a **small** set of rules, each traced to its source so the next reader can
judge it rather than take it on trust. The size ceiling is single digits — `code-discipline` has
seven and quotes Holzmann on why not seventy; a hundred-rule list is not read.

**Sources, researched live** the way BACKLOG #40 did for `code-discipline`: the current OWASP Top
10, OWASP ASVS, and the CWE Top 25 are the candidate list. The pass reads them, keeps what maps to
something a linter can check or a scaffold can build, and drops the rest. Every claim carries a
"confirmed live YYYY-MM-DD" stamp (`currency-discipline`). The exact rule text and count are the
research's output, not this spec's; what this spec fixes is the two tiers, the sourcing method and
the ceiling.

**Two tiers**, named in the opening, every rule tagged with its tier:

- **Every project.** Secrets never in the repo or the built artifact; dependencies audited against
  known vulnerabilities; anything downloaded or executed at runtime is verified before it runs;
  the app asks for the least permission it needs. Orcshot's tier.
- **Reachable by strangers.** All of the above, plus: every input that arrives over the network is
  hostile until validated; every route authenticates unless it is deliberately public and says so
  in the code; an error never reaches the client carrying internals (paths, queries, traces);
  transport is encrypted and plain HTTP refused; rate limits exist. The API's tier.

**How Claude knows the tier — both ways, because each covers a case the other cannot:**

- *From the code, whenever code exists.* Each rule is phrased by the situation it fires in
  ("code that accepts a request from the network…", "a value that came from a file or a user…").
  A route handler is visibly a route handler. This is how a refactor and a one-line fix in chat
  get the right rules without anyone having been asked anything.
- *From one question, when no code exists yet.* `/orc-code`'s New-Project Flow asks it (§2). The
  answer is **not recorded in a file**: what the scaffold produces — an auth layer, a public/private
  directory split, the security lint config — is the record, and from then on the code answers.
  direflail, on the alternatives: *"from the code itself is a given — IF the code exists. on a
  brand new project, we won't have that."*

Ends with **"What this is not"**: not `secret-hygiene` (that is the transcript; this is disk and
repo — it points there), not a penetration test, not runtime protection, and not enforced by this
file — §3 is.

### 2. Where it lands

**Every stack skill gets `## Security — where security-discipline lands`**, parallel to the
`## Lint — where code-discipline lands` section each carries. It maps each checkable rule to that
stack's tool and config:

- the static-analysis security ruleset and how it is switched on — Python: ruff's bandit-derived
  `S` rules; JS/TS: the ESLint security plugin; Kotlin, Swift, C#, Dart, GDScript, Unity: whatever
  the research finds, and **"none free" said plainly** where that is the answer, as the lint
  sections already say for Dart and GDScript;
- the dependency-audit command — candidates from memory, every one confirmed live before it is
  written: `pip-audit`, `npm audit`, `dotnet list package --vulnerable`, a Gradle plugin, and
  whatever Dart, Swift and Godot have or lack;
- where secrets live on that platform and the `.gitignore` entries that keep them out of the repo;
- for the exposed tier, what the scaffold builds (§2, `/orc-code`).

This makes Security the fourth facet every stack skill answers, after v18's Presence, UI and
Storage. All nine shipped stack skills get the section in this pass, researched and stamped; every one says
*"no project has been through this yet"* until one has. The PHP skill (v23) is born with one.

**`/orc-code` changes in three places** (`skills/orc-code/SKILL.md`, `docs/commands/orc-code.md`):

1. **New-Project Flow — the exposure question**, after platforms (step 3) and before starting
   point (step 4): *"Will anyone you didn't invite be able to reach this?"* The platforms ticked
   supply the proposed answer, so it is a confirmation, not a blank — web ticked: *"I'll assume
   yes — right?"*; desktop or mobile only: *"I'll assume no — right?"*. The answer picks the tier
   the scaffold builds to. Skipped, like every other question, when `$ARGUMENTS` already answered
   it.
2. **Scaffold** — beside the lint config it already writes from the stack skill's Lint section
   (step 5, the v19 wording), it writes the security lint config from the new Security section,
   and for the exposed tier scaffolds the pieces the rules need to exist from day one: the stack's
   auth layer, the public/private split, error handling that does not echo internals. *What* those
   pieces are per stack is the stack skill's section; `/orc-code` names no framework.
3. **Refactor, quality mode** — today brings an existing codebase up to `code-discipline`; it now
   brings it up to `security-discipline` too. `code-modernization:modernize-harden` already does
   an OWASP/CWE/dependency scan with a reviewable patch, so the mode **wraps it with an
   availability check**, the way `/orc-code` already wraps `feature-dev` and `code-modernization`
   — it grows no scanner of its own. Not installed: say so plainly, offer to help find it, and
   fall back to the skill's rules read against the code by hand.

**`test-discipline` gets one line**, not a section: at every trust boundary, one test that the
hostile case is refused — an unauthenticated request rejected, malformed input rejected. It already
says "know the scenarios first"; this names the scenario people forget.

### 3. Enforcement

Three mechanisms; two exist.

1. **On every write — `lint_on_write`, unchanged.** The hook runs the project's configured linter
   on each file Claude writes and *"carries no rules of its own"* (`hooks/scripts/lint_on_write.py`).
   With the security ruleset in the *same* linter config the Lint section already owns, every
   hostile-input or hardcoded-secret finding reports on write with no new hook. This is why §2
   puts the security rules in the linter config and not in a separate tool.
2. **Before anything leaves the machine — the dependency audit joins the v21 gate.** New
   `/orc-test audit`: runs each detected language's audit command, one line per language, ✓/✗,
   and — `/orc-test`'s standing rule — never installs a tool; names the missing one and its
   install line and skips that language. `/orc-git push` and `cp` run it beside `coverage`;
   `release` beside `analyze`. A known-vulnerable dependency is a red gate: the report is shown
   and nothing is pushed, no skip flag (v21, unchanged). It lives in `/orc-test` because that is
   where the per-language module and the `languages/<lang>.md` page already are — the audit
   command is one more entry in each, not a second registry. The audit is an every-project rule,
   so it runs on every project.
3. **On existing code** — the `modernize-harden` wrap from §2.

**Deliberately not built:** a runtime scanner; penetration testing; a secret-scan hook over git
history (the repo rule is prose plus the per-stack `.gitignore` entries; a hook, if ever wanted, is
a BACKLOG entry citing this spec).

### 4. What pins it, the docs, the records

**Tests, in the existing suites:**

- `hooks/scripts/tests/test_orc_code_skill.py` already asserts the phrase
  `## Lint — where code-discipline lands`; it gains the same assertion for
  `## Security — where security-discipline lands` across every `skills/stack-*/SKILL.md`, and one
  that `/orc-code`'s flow contains the exposure question. A stack skill added without the section
  fails.
- `/orc-test`'s suite gains `audit` tests per language module, with fixture output from each tool
  — captured from a real run or hand-built from the tool's documented format, and a README beside
  each saying which (the `mutation_test_junit.xml.README` precedent).
- `/orc-git`'s gate-pinning test from v21 widens to name `audit` beside `coverage`.

**Docs pages, same commit as the change** (`CLAUDE.md` checklist item 7): `docs/commands/orc-code.md`
(the question, what scaffold now writes, what refactor now does), `orc-test.md` (`audit`),
`orc-git.md` (the gate wording — which the v21 pinning test holds to what the tools really print).

**Records:** a BACKLOG entry for this spec; a deferred entry for the repo secret-scan hook; PHP as
v23. `security-discipline`'s rules and every stack section carry "confirmed live" stamps.

## Out of scope, by name

- **PHP** — v23, the next spec, starts when this ships. Its stack skill is born with the Security
  section this spec defines.
- **Shared-hosting publishing** (DreamHost as the confirmed-live example) — its own task; it is not
  PHP-specific and direflail wants it written from a real deployment, not before one.
- **Runtime protection, penetration testing, git-history secret scanning** — §3.
- **A `.orclab/` record of exposure** — rejected in §1; the code is the record.

## Verification

- `python3 -m pytest` green in `hooks/scripts`, `skills/orc-test/scripts`, and wherever the gate
  test lives, with the new assertions added red first.
- `/orc-test audit` run on Orclab itself (Python) and its line shown in the BACKLOG entry.
- The live check: `/orc-code` on a throwaway new project, web ticked, exposure confirmed "yes",
  and the scaffold's security config and pieces present; then `/orc-git push` on it showing the
  audit line in the gate. Recorded in the entry with the day's date.
