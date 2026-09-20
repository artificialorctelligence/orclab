# Orclab v24: PHP as a web back end — `stack-php`, `/orc-test` learns PHP, and a handoff for the first project

**Status:** design, approved section by section in conversation 2026-09-20. It is the second
half of the request that became v22 ("add PHP to `/orc-code`", BACKLOG #50), deferred behind v23
so that its live check could run in a container rather than by installing PHP on this machine.

## The problem

direflail is putting an API on DreamHost, which serves PHP and nothing else. Orclab has no PHP
stack skill, `/orc-test` has no PHP module, `lint_on_write` has no `.php` row, and `/orc-code`'s
web row does not offer PHP. CLAUDE.md's stack rule ("Before the first project builds on a stack
… Orclab has never met") says the knowledge is written from live research before the first
project, and BACKLOG #50 adds that the live check runs in the container v23 built.

**What should already have covered it** (`CLAUDE.md`, "Before building anything"): searched every
shipped `SKILL.md`, `CLAUDE.md`, `BACKLOG.md`, `hooks/scripts/` and `skills/*/scripts/`. PHP
appears only in #48's and #50's history and in the v22/v23 specs as "the next one." No stack
skill, no language module, no linter row. The gap is the one #50 records.

## What is decided

### §1 — Scope: the skill *and* the machinery (direflail: "B")

Three options were offered: the stack skill and Defaults Table row only (A); A plus a `/orc-test`
language module and a `lint_on_write` row (B); B plus scaffolding the real DreamHost API through
`/orc-code` in this repo (C). **B**, by direflail's decision, with one addition: *"if there is
something valid you could lend to C as instructions, let's put that into a file so I can give it
to that session"* — §6. C stays out because CLAUDE.md's dogfooding section puts a consuming
project's real work in a session centered on that project.

Why not A: #50 says the Security section carries "a dependency-audit command for `/orc-test
audit`", and that is a claim about `/orc-test`, which only knows a language when
`skills/orc-test/scripts/orc_test/langs/` holds a module for it (eight today, no `php.py`).
A would ship a skill whose Security section cannot be exercised — what #33 records went wrong
with Orcshot.

What v24 ships, all in Orclab's repo:

1. `skills/stack-php/SKILL.md` — the tenth stack skill, `user-invocable: false`, the section
   set the other nine share.
2. `/orc-test`: `langs/php.py`, `languages/php.md`, captured fixtures with `.README`s,
   `tests/test_lang_php.py`, `ALL` in `langs/__init__.py`.
3. `hooks/scripts/lint_on_write.py`: one `.php` row in `LINTERS`, and its tests.
4. `skills/orc-code/SKILL.md`: the web row's Alternatives column gains PHP; the stack question
   names it; `docs/commands/orc-code.md` changes in the same commit (CLAUDE.md checklist item 7).
5. `docs/handoffs/<date>-php-first-project.md` (§6).
6. The listings that enumerate stacks and languages: `README.md`'s stack list,
   `hooks/scripts/tests/test_orc_test_languages.py`'s `EXPECTED`, `skills/orc-test/SKILL.md`'s
   marker sentence.
7. BACKLOG, through `/orc-todo` (§7).

### §2 — Prove first, then write (direflail: "A")

Order of work, by direflail's decision: build the image, run every tool inside it on a sample
project, keep the output as fixtures, *then* write the skill and the module from what ran. The
alternative orders — write from docs and fix afterwards, or prove only the module — were declined;
the fix-up pass is where Orcshot's two refactors came from, and the container is the reason #50
waited for v23.

The proof: a `Dockerfile` from the official `php` image plus Composer, a sample PHP project
(one endpoint, one test) mounted through the `compose.yaml` shape `skills/orc-test/SKILL.md`'s
Containers section defines, and each tool run through the real `compose run --rm orclab` path
`/orc-test` uses. Nothing PHP is installed on this machine; the image is removed when done.

**Candidates to confirm, each a research answer under `currency-discipline`, none decided here:**
PHP 8.5 (DreamHost's top selectable version, php.net supported until 2027-12-31 — both confirmed
live 2026-09-19 in #50; `php:8.5-cli` is the tag to check); Composer; PHPUnit for tests; a
coverage driver — PCOV or Xdebug — which must be compiled into the image and is the kind of
detail that only surfaces by running; Infection for mutation (PHP's one maintained mutation
tester; Humbug was retired into it); `composer audit` for the dependency audit; PHPStan or
Psalm for static analysis; the per-file linter `lint_on_write` runs. The framework — plain PHP,
Slim, Laravel, Symfony — is decided by the research, with three constraints: shared hosting
(weight), JSON first and HTML if wanted, and **a framework that produces an OpenAPI description
from the code is ahead of one that does not** (§3, the contract). One is picked; the runner-up is
stubbed with the concern that would pick it, as `stack-web` stubs Django.

**On what PHP is here.** The question "does PHP replace the back end or the whole web row" was
withdrawn: React is a front-end library, and a PHP server emits JSON for an API, JSON for a React
front end, or HTML — outputs of one server, not different stacks. The skill describes one PHP
server; the front end, if any, is `stack-web`'s React unchanged.

### §3 — The `stack-php` skill

Written after §2 has run, so every command in it was executed in the image. The shared section
set (When this is the stack, Toolchain, The stack decision, Project layout, Build/run/test,
Lint, Security, Containers, Presence, Storage, Deployment, Sources), and what each says beyond
the shape:

- **When this is the stack:** a web back end in PHP — an API alone, behind a React front end
  from `stack-web`, or serving HTML itself. The concern that picks it over the row's default:
  the host serves PHP and nothing else.
- **The stack decision:** §2's framework, with the runner-up stubbed.
- **Project layout:** `composer.json` at the root — the version file `/orc-version` does not yet
  write (`versionfiles.py`'s `KNOWN_FORMATS` holds `pyproject.toml`, the two plugin manifests and
  `debian/changelog`; BACKLOG #6). **The contract:** where the OpenAPI description lives and which
  tool produces it — the file a consuming app's client is written or generated against (§7's
  cross-project entry). Where a `web/` front end from `stack-web` sits if present.
- **Lint / Security:** the two sections `code-discipline` and `security-discipline` route to —
  the static-analysis ruleset, `composer audit` for `/orc-test audit`, where secrets live, what
  the exposed tier adds. From the tools having run, not from their READMEs.
- **Containers:** the `Dockerfile` from §2 verbatim, marked *run here* — the first of the ten
  Containers sections that says so. The proposal to `/orc-code`'s container question is **yes**:
  PHP is the unusual-on-a-dev-machine toolchain v23's §1 had in mind.
- **Deployment:** says plainly that shared-hosting publishing is not yet written, names the
  BACKLOG entry, and does not pretend to know DreamHost.

### §4 — `/orc-test` and `lint_on_write`

`php.py` follows the module contract the other eight export — `KEY`, `LABEL`, `SOURCE_EXT`,
`MARKERS = ["composer.json"]`, `TOOLS`, `CAVEATS`, `SANDBOX`, `AUDIT_TOOL`, and
`test_cmd` / `coverage_cmd` / `coverage_parse` / `mutation_unavailable` / `mutation_cmd` /
`mutation_parse` / `audit_nothing` / `audit_unavailable` / `audit_cmd` / `audit_findings` /
`lint` — and is registered in `ALL`. Its tests are fixture-driven like the others: the captured
coverage, Infection and `composer audit` output from §2, each with a `.README` saying how it was
made. `languages/php.md` has `python.md`'s headings (Detect, Run, Coverage, Mutation (TCE), Test
lint, Audit, Caveats) and a "Last real run" line with a date. Test-smell lint only if a real
tool exists; otherwise the doc says so, as Dart's does.

`lint_on_write` gets one tuple — `.php` → (the config file that proves the project adopted the
tool, the binary, argv) — found under the project's `vendor/bin` the way JS tools are found under
`node_modules/.bin`; in a containerised project it runs through the container like every other
row.

### §5 — `/orc-code`

The web row's Alternatives column gains PHP with the Knowledge column pointing at
`skills/stack-php/SKILL.md`; the New-Project Flow's stack confirmation names it among the row's
alternatives as it does Next.js and Django. No new question in the flow; the container question
already exists and `stack-php` proposes yes. `docs/commands/orc-code.md`'s "What it will ask you"
changes in the same commit.

### §6 — The handoff file for the first project

`docs/handoffs/<date>-php-first-project.md` — a new directory; nothing like it exists
(searched `docs/` and every skill for "handoff", "first project": the phrase appears only inside
stack skills as "the first project records it"). Written for a session that has Orclab installed
as a plugin and is centered on the API project: plain instructions, no Orclab internals.

- **Start:** `/orc-code`, yes to the container question, PHP when the web row's alternatives are
  offered; what toolchain to expect, so a surprise is recognised as one.
- **What v24 could not verify and this session must record:** the DreamHost side — selecting 8.5
  per domain, Composer on a shared account, what is uploaded and how, what a first deploy took.
  Each line is one the shared-hosting BACKLOG entry needs; the handoff says "record these in
  your own `RELEASING.md` (via `release-checklist`) and tell Orclab's entry N what you found."
- **The contract:** ship the OpenAPI file; say in the README where it is.
- **Report back:** anything in `stack-php` that was wrong or missing, by section — the first real
  use corrects the skill, as CLAUDE.md's stack rule expects.

### §7 — Records and tests

Through `/orc-todo`: #50 points at this spec and becomes v24's entry; #6 gains `composer.json`;
two new entries —

- **Shared-hosting publishing** (DreamHost the confirmed-live example): written from the first
  real deployment, not before one (#50's own words). Its input is §6's recorded lines.
- **Cross-project dependencies** — orcweather's Android/iOS stacks will call this PHP API.
  Searched the skills and command pages for any cross-project notion (other project, contract,
  OpenAPI, sibling repo): none; every `.orclab/` file is one project's own settings. What v24
  does: the API publishes its contract (§3), and the handoff asks the first project to say where
  it is. What is *not* built: a record in the consuming project ("calls that API, contract here,
  deployed there") — nothing in Orclab would read it. Trigger: *the first session that works on a
  project which calls another project's API* — the orcweather session that adds the client.
  Sequence: opened by v24; the API session writes the contract and the README sentence; the
  orcweather session either finds it (a sentence is the record; close) or stumbles (what it
  stumbled on is what the record must hold); built, if needed, by whichever command turns out to
  need the reader — `/orc-code`'s feature flow asking "does this change an API another project
  calls?", or `/orc-release` warning that an app depends on what is being released. Its own
  small spec then. Could be v25, could be never.

Tests that change or appear: `test_orc_test_languages.py`'s `EXPECTED` gains `php`;
`test_docs.py` already checks `orc-code.md`'s headings; `test_lang_php.py` against the fixtures;
`lint_on_write`'s tests gain the `.php` row; `test_side_effecting_skills_frontmatter.py` is
unaffected (`stack-php` is `user-invocable: false`, not `disable-model-invocation`).

## Out of scope, by name

- Scaffolding the real DreamHost API in this repo (C) — its own session, with §6 in hand.
- Shared-hosting publishing — its BACKLOG entry, written from the first deployment.
- A cross-project dependency record — its BACKLOG entry, evidenced by the orcweather session.
- `composer.json` in `/orc-version` — #6.
- A production PHP image — v23's deferred entry covers deploy-as-container for every stack.
- PHP rendering HTML pages as a *default*: the skill allows it, the research does not optimise
  for it.

## Verification

- §2's tools have each run once inside the image through `compose run --rm orclab`, and the
  fixture `.README`s say the command and date.
- `cd skills/orc-test/scripts && python3 -m pytest tests/ -q` green; `hooks/scripts/tests` green.
- `claude plugin validate .claude-plugin/plugin.json` — the one expected warning.
- `podman images` (or `docker images`) shows no PHP image left on the machine.
- `stack-php`'s every "confirmed live" carries a date, and its Deployment section says "not yet"
  with the entry number.
