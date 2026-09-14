# Orclab v20: a page per command, written for the person who types it, and a README that is a front page

**Status:** design, approved in conversation 2026-09-13 (direflail: "looks right, write the
spec"). Resolves BACKLOG #32.

## The problem

Orclab has eleven `/orc-*` commands and nothing written for the person who will type them.
What exists, checked against the repo on 2026-09-13:

- `README.md`'s "Commands" section is one paragraph per command, written from the builder's
  side — "an allocator holding a lock over one canonical file", "applying an *ingredient*", "a
  position cursor" — and four entries end with "Ships as a skill only — see `CLAUDE.md` for
  why", which sends a user to Orclab's internal workshop notes. It is also describing an Orclab
  from a week ago: it lists ten commands (`/orc-test`, v17, is absent), five discipline skills
  of nine and five stacks of nine, a "Status" line that stops at v9 (the plugin is 0.19.0), a
  claim that every command "also ships as a matching skill, a thin pointer" (that layout went
  in v0.10.0), and a pointer to a "Known gap, now fixed" section that does not exist.
- Each `skills/<name>/SKILL.md` is the instruction Claude follows. It is addressed to Claude,
  and a user sees it only by opening the plugin cache.
- `docs/` holds `docs/superpowers/` — design records — and nothing for a user.

The consequence: someone who installs Orclab, runs `/orc-help`, and wants to know "what does
this actually do, what will it ask me, what will it never do on its own" has nowhere to read
it in their own vocabulary. The properties that make a command trustworthy — `/orc-git` asks
first when pushing was Claude's idea, `/orc-todo add` never commits, `/orc-version` never pushes
— are all stated, in Claude's instructions, in the builder's words.

Orclab is going to be put up for download. The README is the first thing a stranger reads, and
today it is wrong before it is unclear.

## What is decided

### 1. One page per command, all the same shape

`docs/commands/<name>.md`, one for every `skills/orc*/SKILL.md` — eleven today: `orc`,
`orc-code`, `orc-git`, `orc-help`, `orc-package`, `orc-publish`, `orc-release`, `orc-reload`,
`orc-test`, `orc-todo`, `orc-version`. `orc`'s page is two lines: it is `/orc-help`'s alias,
and everything on `orc-help`'s page applies.

Every page has exactly these five headings, as `##`, in this order, and no others:

1. **What it's for** — one paragraph. The situation you are in when you reach for it.
2. **What you type** — the invocation, and for a command with subcommands or modes
   (`orc-git`, `orc-todo`, `orc-test`, `orc-code`, `orc-package`) a table, one row per
   subcommand: what you type, what it does, in a sentence each. The five headings apply to the
   command as a whole; the table is the only place subcommands are enumerated.
3. **What it will ask you** — the questions it puts to you before it acts, in the order it asks
   them, or "Nothing" if it asks nothing.
4. **What it changes** — which files it writes, which commands it runs that leave a mark
   (a commit, a tag, a file in `.orclab/`), and what it leaves alone.
5. **What it will never do without asking** — the command's own rules, quoted or restated
   from its `SKILL.md`. This is the section a user reads to decide whether to trust it.

Rules for the prose, which are `CLAUDE.md`'s "explain it again from the reader's side" applied:

- Plain words. A term Orclab coined — *lane*, *ingredient*, *channel*, *gate*, *TCE* — is
  explained in the sentence where it first appears on that page, every page, because a reader
  arrives at any page first.
- No pointer to `CLAUDE.md`, `BACKLOG.md`, a spec, or another `SKILL.md`. A page is complete on
  its own. It may link to another command's page.
- No implementation vocabulary — lock, allocator, cursor, frontmatter, `disable-model-invocation`
  — unless the sentence is about what the user sees because of it, and then the effect is
  named, not the mechanism.
- Names of files the command writes are given, because the user will see them in `git status`.
- Nothing is promised that the `SKILL.md` does not carry. A page is a claim about the command,
  and is written from that command's `SKILL.md` read in full on the day the page is written —
  not from memory of it, and not from the README paragraph it replaces. "What it will never do
  without asking" in particular restates the rule the skill actually states, in the skill's
  own terms of when it applies (for `/orc-git`: typed by the user, it runs; Claude's own idea,
  it asks).

### 2. The README is a front page

`README.md` is rewritten, top to bottom, as the page a stranger reads before installing.
Sections, in order:

1. **What Orclab is** — three sentences. What it is (a Claude Code plugin), what it gives you
   (commands for the work around code — versions, releases, publishing, tests, the backlog —
   and background knowledge Claude reads on its own), and where it came from (real practice on
   Orcshot, then Orclab itself).
2. **Installing** — the two commands, unchanged from today, and one sentence that a fresh
   session is where a new install shows up.
3. **Commands** — eleven lines, one per command, each the command name linked to its page and
   one sentence. This list is the index; there is no separate table of contents. The sentence
   is written for this list, not copied from the skill's `description` field (which is
   addressed to Claude's ambient matching, not to a reader).
4. **What Claude reads on its own** — the background skills, one line each, grouped: the
   discipline skills (`backlog-discipline`, `code-discipline`, `currency-discipline`,
   `environment-registry`, `release-checklist`, `secret-hygiene`, `test-discipline`,
   `verify-before-asserting`, `whole-process-first`) and the nine stack skills. One sentence
   each on when Claude reaches for it. No pages: a user never types these.
5. **Changing Orclab** — one short paragraph for people working on Orclab itself: `CLAUDE.md`
   is the workshop notes, `BACKLOG.md` the open findings, `CHANGELOG.md` what changed release to
   release, `docs/superpowers/` the design history, `VERIFICATION.md` the install check. Named
   honestly as for people changing Orclab, not for users.

Removed, not moved: the v1–v9 "Status" paragraph (`CHANGELOG.md` is that); "Each command below
also ships as a matching skill … thin pointer"; "see *Known gap, now fixed* below"; every "Ships
as a skill only — see `CLAUDE.md` for why"; the `commands/`-removal history in "Installing".

Every skill and stack that exists is listed; everything listed exists. The test in §4 holds the
commands half of that; the skills half is checked by hand at the review step in the plan.

### 3. `/orc-help <command>` shows the page inside Claude

`/orc-help` and `/orc` gain an argument. `/orc-help <name>` finds `docs/commands/<name>.md` in
the installed plugin root that `orc-help`'s Step 2 already establishes, reads it, and presents
it in chat in the page's own order — the five headings, the table if there is one — relayed
as Claude relays any document, not pasted as raw Markdown. `<name>` is accepted with or without
the leading `/` and the `orc-` prefix (`git`, `orc-git`, `/orc-git` all reach `orc-git.md`).
A name with no page: "There is no `/orc-<name>` command; `/orc-help` lists what exists." Bare
`/orc-help` keeps today's synopsis and adds one closing line: `for any command, /orc-help
<name>`.

One source, two renderings (direflail, 2026-09-13: "a"). The Markdown page is written once;
GitHub renders it; `/orc-help` reads the same file. There is no second, terminal-shaped copy —
a duplicate is where the next drift would begin.

The change is to `skills/orc-help/SKILL.md` (a Step 4, and the closing line in Step 3's format)
and nothing in `skills/orc/SKILL.md`, which already forwards `$ARGUMENTS` to `orc-help`.

### 4. Keeping it true

**A test, `hooks/scripts/test_docs.py`** — the root `pyproject.toml` already collects `hooks/`
and puts `hooks/scripts` on the path, so no configuration changes. It asserts, over the repo:

- every `skills/orc*/SKILL.md` has a `docs/commands/<name>.md`, and every page has a skill;
- every page's `##` headings are exactly the five of §1, in order, and nothing else;
- every page's name is linked from `README.md`'s Commands section (`docs/commands/<name>.md`
  appears as a link target).

Presence and shape, not content. Content staying true — a page saying what its command does
today — is a discipline, the same as `RELEASING.md` staying true to the release, and it gets
one line in `CLAUDE.md`'s "Checklist for designing a new `/orc-*` thing": a change to what a
command asks, changes, or refuses touches its page in the same commit, and a new command ships
with its page or the test fails.

**The reader's-side pass is a step, not a hope.** Each page's first draft is followed by a
second reading as someone who has never opened a `SKILL.md`, and a rewrite of every sentence
that reader would stumble on. The plan carries this as its own task per page, with the review
question written down: *could this reader say, in their own words, what the command does, what
it will ask, and what it will not do — from this page alone?*

### 5. Out of scope

- The `SKILL.md` bodies. They are Claude's instructions and correct as they are; if writing a
  page finds a skill's rule unclear, that is a BACKLOG entry, not an edit made in passing.
- `CLAUDE.md`, beyond the one checklist line in §4.
- Pages for the discipline and stack skills. They get a line in the README and nothing more.
- Any generated documentation, site, or tooling beyond the one test. Eleven Markdown files
  and a README are the deliverable.

## What changes, by file

| File | Change |
|---|---|
| `docs/commands/<name>.md` × 11 | New. §1's shape. |
| `README.md` | Rewritten. §2's sections; the stale claims listed there removed. |
| `skills/orc-help/SKILL.md` | Step 4: show a page; Step 3's format gains the closing line. |
| `hooks/scripts/test_docs.py` | New. §4's three assertions. |
| `CLAUDE.md` | One line in the design checklist: a command change touches its page. |
| `BACKLOG.md` | #32 resolved, with what was verified. |
| `CHANGELOG.md`, `.claude-plugin/*.json` | v0.20.0, via `/orc-version`. |

## How it is verified

1. `python3 -m pytest hooks/` — `test_docs.py` green: eleven pages, five headings each, all
   linked from the README.
2. For each page, the reader's-side review question in §4 answered yes by a reviewer who did
   not write the page and has not read the skill — in the plan, a separate subagent given the
   page alone.
3. Each page's "What it will never do without asking" checked against its `SKILL.md` by a
   reviewer with both open: every rule on the page is in the skill; every refusal the skill
   states is on the page.
4. `README.md`: every name in its skill and stack lists is a directory under `skills/`; every
   directory under `skills/` is in one of its lists or is a command with a page.
5. After `/orc-reload` and a fresh session: `/orc-help git` presents `orc-git.md`; `/orc-help`
   ends with the closing line; `/orc-help nonesuch` says there is no such command.
6. `VERIFICATION.md` Scenario 12 (`/orc-help` in core vs. project context) gains step 5.

## Sources

- `README.md`, `skills/*/SKILL.md`, `pyproject.toml`, `hooks/scripts/` — read 2026-09-13.
- BACKLOG #32 (2026-09-10) — the ask and the before-picture.
- `CLAUDE.md`, "Before explaining anything, explain it again from the reader's side" — the
  standard every page is held to.
