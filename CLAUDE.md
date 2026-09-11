# Developing Orclab

This is guidance for whoever (human or Claude) designs Orclab's own skills — both the subset it
ships to consuming projects and the full set it uses to develop itself. The guidance in *this
file* is what stays behind: Orclab's own workshop notes, not content installed anywhere else.
It's "project" category under Orclab's own taxonomy: real, verified facts about how Claude Code's
command/skill system actually works, learned the hard way while building `/orc-code` through
`/orc-git`, so the next component gets designed right the first time instead of rediscovering the
same gaps.

Every claim below was actually checked — against the real, current official docs, or against
live, direct behavior observed in a real session — not assumed from memory. Where something is
inference rather than a confirmed fact, it's labeled as such.

## Commands are the legacy form of Skills — Orclab ships skills only

**Settled against the primary docs (2026-09-07).** The plugins reference and the plugin guide
both describe `commands/` in the same words: *"Skills as flat Markdown files. **Use `skills/` for
new plugins**."* They are not two component types with different capabilities — `commands/` is
the legacy flat layout of the same thing. That is why the precedence rule reads the way it does:
*"if a skill and a command share the same name, the skill takes precedence."*

Two consequences worth stating outright, because an earlier pass of this file got both wrong:
- Skills support a **superset** of command frontmatter. Commands ignore `name` and `paths`;
  everything else — `$ARGUMENTS`, positional `$1`/`$2`, the `arguments` field, `argument-hint`,
  `allowed-tools`, `disable-model-invocation` — behaves identically in a `SKILL.md`.
- A plugin skill's invocable name comes from its **directory name**, not its `name:` field. The
  skills doc says otherwise; the docs are wrong. Confirmed live against the installed `aikido`
  plugin, whose skill directory `issues` carries `name: aikido-issues` and yet loads as
  `aikido:issues`.

**As of v0.10.0 Orclab has no `commands/` directory.** All components are skills.

**Real, confirmed bug, not theoretical**: the Claude Desktop client does not register plugin
`commands/*.md` files as slash commands at all. Confirmed live — `/orclab:orc` and `/orclab`
both returned "Unknown command" in that client, on an install that worked correctly via the CLI.
Skills, by contrast, invoke correctly there (confirmed via `ponytail`'s real `/ponytail`).

**Refinement, confirmed live (2026-09-07) — Desktop doesn't fail, it warns falsely and then
works.** The "Unknown command" observation above predates v6's wrapper skills. Typing the bare
`/orc-version` in Desktop shows a toast — *"/orc-version isn't a recognized command here. Some
commands only work in the Claude Code terminal."* — and then resolves and runs correctly anyway.

**The trigger is solely whether the submitted text is namespaced.** Accepting the autocomplete
menu *rewrites the input* to `/orclab:orc-version`, which is silent. Pressing Escape to dismiss
the menu submits the bare `/orc-version`, which warns. Same command, same session, seconds apart
— reproducible on demand via the Escape key.

The toast comes from Desktop's own UI bundle (`resources/ion-dist`, i18n id `+9dhXtDFu6`), not
from `claude-code` and not from the agent. It is fired as a side effect inside a comma expression
whose actual branch condition is a different predicate, so it is advisory, not a rejection. The
predicate is an exact case-insensitive match of the submitted name against a loaded command
list's `name` or `aliases`; plugin skills appear there under their **namespaced** name only. The
menu shows the bare form as a secondary label (`orclab:orc-version (orc-version)`), but that
label is not an alias, which is why the bare submission misses.

**It has nothing to do with how Orclab is built.** It still occurs on v0.10.0, which ships no
`commands/` directory at all. Theories that fit the early evidence and are all wrong, recorded so
they don't get re-derived: that the bare name must share the plugin's name prefix; that a skill
and command sharing a name suppresses the bare alias; that it's a load-timing race. The Escape-key
reproduction ruled out every one of them.

**Workaround: accept the autocomplete rather than dismissing it**, or type the namespaced form.
Nothing in the plugin can suppress the bare-form toast, so it is Anthropic's to fix. Reported
upstream as [anthropics/claude-code#92738](https://github.com/anthropics/claude-code/issues/92738)
(2026-09-07) — check there before investigating this again.

**The practical trap:** do not debug a wrapper skill because of this toast. It fires on a
component that is working correctly, and the wrapper is the reason it works at all.

**What this means for every future `/orc-*` component: build it as a skill, full stop.** The
older guidance here said `commands/*.md` "stays for CLI use" and the wrapper skill was "additive,
not a replacement." That was wrong on its own terms — because the skill wins any name collision,
the wrapper shadowed its own command file in the CLI too, so those command files were never
serving the CLI. They had become content that the wrappers happened to `Read`. v0.10.0 folded
each body into its skill and deleted `commands/` outright.

## The determinism spectrum: explicit invocation vs. ambient matching

Two genuinely different mechanisms produce the same visible result, and it matters which one
you're relying on:

1. **Explicit invocation** — a message that *starts with* `/name` (confirmed: multiple
   consecutive skills can even be stacked at the very start of one message, e.g.
   `/write-tests /fix-issue 123`, with trailing text passed as `$ARGUMENTS` to each). This is
   intercepted by the harness before it ever reaches Claude as text. It is a **guarantee** — no
   judgment involved, no chance of misfire, regardless of how many other skills exist.
2. **Ambient/semantic matching** — anything else, including a full sentence that mentions a
   skill's name ("I want to use orc-code to build X"). This is Claude reading the message and
   comparing it, using its own judgment, against every currently-available skill's
   `name`+`description`. It is **reliable, not guaranteed** — a distinctive, literal name
   mentioned in the sentence makes the match very likely (Claude is reasoning from a strong,
   unambiguous cue), but it is still a judgment call in the moment, not a mechanical certainty.

**A slash character that isn't at the start of a message does nothing special.** Confirmed
directly from the docs: slash-command recognition only applies at the start of a message (or
immediately following another stacked skill invocation). "Use /orc-code to build X" typed as a
full sentence is read by Claude exactly the same way as "use orc-code to build X" — the stray
slash carries no meaning for the ambient-matching path.

**Practical rule**: when writing a new skill's `description`, reference its own real name
directly ("Use when the user explicitly asks to use orc-code, or types `/orc-code`...") — this
gives Claude's judgment the strongest, least ambiguous cue for the ambient path, on top of the
guaranteed explicit path already working via the literal `/name` form.

## `disable-model-invocation` and `user-invocable`

Both are real, documented Boolean frontmatter fields (accept `true`/`false`/`yes`/`no`/`on`/
`off`/`1`/`0`, case-insensitive).

| Frontmatter | You can invoke (`/name`) | Claude can invoke | Description in context ambiently |
|---|---|---|---|
| (default — omit both) | Yes | Yes | Always |
| `disable-model-invocation: true` | Yes | No | Not until you invoke it |
| `user-invocable: false` | No | Yes | Always |

**`disable-model-invocation: true`** — the skill becomes invisible to Claude's own ambient
judgment (its description isn't even sitting in context as a candidate) until explicitly
invoked. The official docs' own example is `/deploy`: *"You don't want Claude deciding to
deploy because your code looks ready."* Real fit for Orclab: a skill whose *whole purpose* is
one-shot and side-effecting — `/orc-publish`, `/orc-release`, `/orc-package`, which all carry
it. Anything more conversational and workflow-starting (`/orc-code`'s ask-questions-then-
scaffold flow) should stay default, since the whole point there is natural-language
triggerability matching a `/cat-code`-style dual-invocation UX.

**The flag is per-skill, so it cannot protect one subcommand.** An earlier version of this
paragraph — from `CLAUDE.md`'s first commit, 2026-09-06, four days before `/orc-git` held a
`release` — named `/orc-git release` and `/orc-git push` as the fit. It was an illustration of
what the flag is for that later read as a requirement, and it was never applied, because
applying it would hide `commit` and `branch` from "commit this for me" along with the two
dangerous subcommands. Found by v14's final review, tracked as BACKLOG #31, settled by direflail
the same day: a skill that mixes everyday and irreversible subcommands carries the rule *inside*
the irreversible ones instead — **if the user typed it, it runs; if it was Claude's idea, Claude
says what it is about to run and waits for a yes.** `/orc-git`'s "Whose idea was it" section is
the reference form. Claude always knows which case it is in, which is what makes this a rule it
can follow and the flag a rule it cannot apply.

**Critical, confirmed-live nuance**: `disable-model-invocation` blocks *ambient self-selection*
— Claude spontaneously reaching for the skill because some unrelated request superficially
matches. It does **not** block *deliberate, explicit* invocation, including an orchestrating
skill's own instructions directing Claude to invoke it by name. Verified directly in this
session: a real, already-installed skill with `disable-model-invocation: true` was invoked
successfully via the `Skill` tool the moment it was named explicitly — no refusal.

**`user-invocable: false`** — the mirror case: background knowledge Claude should reach for
when relevant, but that isn't a meaningful `/name` action for a user to type (the docs' own
example: a `legacy-system-context` skill explaining how an old system works).

## Sub-skill isolation: restricting a skill to "only this orchestrator can reach it"

Real, working pattern, built on the nuance above: give a sub-skill `disable-model-invocation:
true`, and have an orchestrating skill or command's own instructions explicitly invoke it by
name (either by telling Claude to use the `Skill` tool with that name, or — the simpler
approach already used by `orc.md`/`orc-code.md` — by telling Claude to directly read the
sub-component's real file and follow it, which is a plain file read, not the invocation
mechanism at all, and is unaffected by any invocation flag either way).

Result: the sub-skill becomes unreachable to Claude for anything *except* being explicitly named
by the one thing that's supposed to reach it — real encapsulation, not just a documentation
convention.

## Skills can bundle and run real scripts

Confirmed against the actual, real `pptx` skill already present in this environment (not just
docs): a skill can ship a `scripts/` subdirectory with real code (Python, in that example), and
its `SKILL.md` tells Claude to run it via the `Bash` tool, referencing the script's path with
`${CLAUDE_SKILL_DIR}` so it resolves correctly regardless of where the skill is actually
installed (personal, project, or plugin level). Pre-approve execution in frontmatter, e.g.
`allowed-tools: Bash(python3 *)`.

Directory shape:
```
my-skill/
├── SKILL.md
├── scripts/
│   └── helper.py
```

## Before any answer that says what to do next, show what it rests on

**The trigger is the situation, not the intent.** You are about to produce something that ranks,
sequences, chooses between options, names something, judges whether something is ready, or says
what to work on next — **whether or not anyone asked you a question.**

**Judge the claim, not the container.** A report that ends by proposing an order is covered by
that ending, even though the rest of it reports. The unit is the claim someone would act on, not
the document it arrives in — **including one phrased as a question.** A question carrying its own
answer is the answer.

**Not this:** reporting a fact, explaining why something broke, or carrying out work you were
asked to do — asked means the action, not the goal it serves: choosing where a new helper lives
is not "carrying out the refactor."

**There is no exemption for a small answer,** and "this turns on nothing" is a conclusion you may
only reach after looking. The minimum is the project's own record of the thing: for what to work
on next, `BACKLOG.md` and `docs/superpowers/`; for a change to code, the file it touches and its
callers, found by a search you show rather than one you assume; for a name or a setting, whatever
already reads it, or the nearest existing one of its
kind. Where none of those fits, it is whatever you would cite if challenged. This list is
Orclab's own, written against its current layout; if that layout changes the list should read as
obviously stale rather than quietly wrong.

**The pass.** Open what the answer turns on and **quote the exact text that decided it** — if your
answer would be different had that text read otherwise, that is what to quote; where what decided
it is an absence, show the search that establishes it. A description of what you read is a claim
about yourself, not evidence about the project. State the premises the answer rests on, and attach
each to the claim it supports.

**What it looks like when skipped.** 2026-09-09: asked what to work on next, Claude ranked three
backlog entries and argued the ordering across two turns before direflail decided on it — without
ever running `ls docs/superpowers/specs`. All three already had finished specs; the one called "a
brainstorming pass on an undecided taxonomy" was a 260-line written one. One command, never run.

Full record, five more worked examples, and why this is a section rather than a fixed defect:
**#26**.

## Before explaining anything, explain it again from the reader's side

**The trigger is that you are about to explain something to a person** — a change, a design, a
problem, a why — whether or not the explanation is also an answer, and whether or not the topic
is "user-facing." A change to a Python module is still explained to a person.

**The reader** directs this project and decides what happens next, but has not been in this
session, has not read the files you just read, does not hold the code in their head, and will
not go and read it. That is not a deficiency to route around; it is who the explanation is for.

**The pass.** Having worked out what to say, think it through a second time *as that reader*,
then write that version. What happened, in terms of what a person does and sees. Why. What
changes. Names of functions, flags, files and git commands come only after the reader could say
in their own words what the thing is — and often not at all. The section above asks whether the
answer is *checkable*; this one asks whether it is *readable*. Both passes run; this one runs
last, over the finished text, because evidence the reader cannot parse has not been shown.

**What it looks like, 2026-09-10.** Asked to fix #30, Claude explained the design in two
paragraphs built on `canonical_root`, `git rev-parse --show-toplevel`, `next_number`'s scan and
`in_canonical_checkout`, with the CLAUDE.md line it rested on quoted and the file:line cited.
Every clause of the section above was satisfied. direflail: *"i'll admit, i don't understand
what you're talking about."* The rewrite — two copies of the project, the command wrote a test
scenario into the wrong one, keep the shared number but write the text where you ran it, and the
safety net has to look at the same copy — was understood on first read and approved. Same design,
same facts, one extra pass. direflail, on the cost: *"it seems well worth it if it works."*

**A second instance, same day, different shape.** Asked about BACKLOG #31, Claude recommended
"option (a) with (c)'s reasoning" — labels that existed only inside the entry Claude had written
an hour earlier and direflail had never opened. *"you're saying option a and c and never told me
what those options are."* No jargon this time; a reference to something the reader has not seen.
The pass has to catch both: anything the reader could not have read, whether it is a function
name or a label from a file, gets restated in full.

**Why this is a section and not a rewording of the one above.** #26's own diagnosis separates
two capacities: *noticing* that the reader lacks a fact, which is unavailable from inside a
context where the fact is present, and *simulating* a reader who has not seen it, which needs no
noticing and can be run on purpose. The section above is the floor — mechanical habits that
work without simulation. This is the simulation itself, which #26 names as "the thing actually
being asked for," and which until today lived only in Claude's memory file and not here.

## Before building anything, name what should already have covered it

**Before proposing to build anything — a component, a script, a hook, a lint, a check — name the
rule, skill, or component that was supposed to handle this case, and say why it didn't fire.** If
one exists, the fix is almost always widening its trigger, not adding a second mechanism beside
it. A new thing policing a rule that already exists is the worst of both: more code, and two
places to keep in sync.

**This governs every build, not just new `/orc-*` components.** It is deliberately a section of
its own rather than an item in the design checklist below, because that checklist's heading —
"designing a new `/orc-*` thing" — is a category a builder can describe their own work out of.
That is exactly how this rule gets missed.

**Ask the backward question, not the forward one.** "What would catch this?" invents a mechanism
without ever passing through what already exists. "What was supposed to catch this, and why
didn't it?" lands on the existing rule immediately. Real case (2026-09-07): a ~60-line
`BACKLOG.md` linter was proposed to enforce that a resolved entry's heading matches its body — a
rule `backlog-discipline`'s own "Resolving an entry" step 1 has always stated. That skill had been
read *in full* earlier in the same session, to follow it while writing an entry. Reading a
document to execute a task and reading it to answer "does this already solve my problem" surface
different things; the first does not substitute for the second. The real fix was one paragraph
widening the existing rule's trigger, and no new code at all.

**If you genuinely can't name anything**, the rule still has to tell you what to do — a rule made
only of deflections is friction, not guidance:

1. **Prove it.** Name where you looked — which skills, which docs, which existing scripts. An
   unsearched "nothing" isn't an answer, it's a skipped question, and it is the answer that would
   have been given about the linter above by someone who had read the covering skill an hour
   earlier.

   Naming *a* place you looked satisfies the letter of this while doing none of the work, so there
   is a floor. **Orclab's minimum search surface: every shipped skill's `SKILL.md`, this file,
   `BACKLOG.md`, and the bundled scripts under `hooks/scripts/` and `skills/*/scripts/`.** The
   skills are the ones that matter most and are easiest to skip — a rule living inside a skill
   body is the least discoverable kind there is, and it is exactly where the linter's covering
   rule already was. This list is Orclab's own, written against its current layout; if that
   layout changes the list should read as obviously stale rather than quietly wrong.
2. **Ask whether the absence is itself the finding.** A real gap you aren't filling right now is a
   BACKLOG entry, not a build.
3. **If there is a real gap, and you are building the solution now:**
   - **Record the proven absence** — in the commit message or the entry, "searched X, Y, Z;
     nothing covered it." Whoever comes next asks this same question, and without that they redo
     the entire search from scratch.
   - **Phrase the new thing's trigger by the situation it applies to**, not by the intent you had
     while building it. You are now the answer to this question for the next person; if the only
     way to find it is already knowing it exists, they will build a third one. This is not the
     same as widening a missed trigger above — that is repair, this is getting it right at birth.
   - **Then follow the design checklist below** for what shape it should take. That checklist
     already answers the "how," and this section deliberately doesn't restate it.

**Why prose is the weakest place to put a rule — and what to do about it.** Per the determinism
spectrum above, a rule inside a skill's body fires only if the skill was invoked, *and* the right
section was read, *and* the reader recognised their own work in it. Three conditions, each able
to fail silently. Every guidance miss recorded here so far has been the third: a trigger
phrased as an *intent* ("when you resolve an entry", "when designing a new component") that the
reader described their own work out of. **Phrase a trigger by the situation it applies to, not by
the intent someone brings to it** — and when one is missed, widen that trigger rather than adding
a mechanism beside it.

### The specific case: wrapping real, existing skills

The same "wrap, don't reinvent" principle Orclab already applies to `feature-dev` and
`code-modernization` (in `skills/orc-code/SKILL.md`) extends to built-in/environment-provided
skills too.
Example: a real `pptx` skill capable of generating real PowerPoint files, with real bundled
scripts and hard-won gotchas already documented, already exists in this environment — a future
`/orc-doc pptx ...`-style command should delegate to it, not rebuild PowerPoint generation from
scratch.

**One real caveat, not to skip**: some such skills are environment-provisioned rather than
universally present (the real `pptx` skill found here lives under a Desktop-specific config
path, suggesting it may not exist the same way in every client). Any component that delegates to
one needs the same "check it's actually available, tell the user plainly if not" guard
`skills/orc-code/SKILL.md`'s flows already use for `feature-dev`/`code-modernization` — never assume silently.

## Checklist for designing a new `/orc-*` thing

1. Build it as `skills/<name>/SKILL.md`. There is no `commands/` directory any more, and the
   docs tell plugin authors to use `skills/` for new work.
2. Is it conversational/workflow-starting, or one-shot/side-effecting? The former stays default
   (natural-language triggerable); the latter gets `disable-model-invocation: true`.
3. Does its description reference its own real name explicitly, to give ambient matching the
   strongest possible cue?
4. Does it need to orchestrate a sub-component that should never fire on its own? Give that
   sub-component `disable-model-invocation: true` and invoke it explicitly by name.
5. Have you answered "Before building anything, name what should already have covered it" above?
   That rule binds every build, not only the ones that reach this checklist. Its specific case
   applies here: if the capability already exists as a real skill (built-in, or from another
   plugin), wrap it — with an availability check — rather than rebuilding it.
6. Is it named `orc-<something>` (or `orc` itself)? `/orc-help`'s Step 3 enumerates
   `skills/orc*/SKILL.md` — no hyphen, so `skills/orc` is caught too — and that prefix is the
   only thing separating Orclab's commands from its discipline skills. A component named without
   it silently vanishes from Orclab's own command listing. If the `orc` prefix is ever dropped,
   Step 3 needs a different discriminator; a `metadata:` key is the documented way (confirmed
   live to load without error), since unknown *top-level* frontmatter keys are not.

## Running the bundled-script test suites

Any skill bundling real Python (like `orc-publish`) keeps its tests in a `tests/` directory next
to its `scripts/`, with an empty `conftest.py` at the `scripts/` root so the suite runs correctly
from any working directory or invocation form. Run a given skill's suite with:

```bash
cd skills/<skill-name>/scripts && python3 -m pytest tests/ -v
```

## `claude plugin validate` does not check skill frontmatter

Confirmed live (2026-09-07) with a negative control, not assumed. Two copies of Orclab, identical
except for one line in `skills/orc-git/SKILL.md` — one with a custom key correctly nested under
`metadata:`, the other with the same key as an unsupported *top-level* frontmatter field, which
the skills docs say is a hard error when packaging a skill for upload — produced byte-identical
output: `✔ Validation passed with warnings`.

So `plugin validate` checks manifest/marketplace structure and file layout. It does not read
frontmatter contents. **"Validation passed" is not evidence that a skill's frontmatter is
well-formed**, and it must never be cited as one in a release checklist.

This matters more here than it first looks, because Orclab's frontmatter is load-bearing
behavior, not decoration. A misspelled `disable-model-invocation` would silently make a
side-effecting skill (`/orc-publish`, `/orc-release`) model-invocable again — the exact property
the design checklist's item 2 exists to decide — and validate would report a clean pass. If
frontmatter is ever to be checked mechanically, it needs Orclab's own lint, which is the same
shape as the `hooks/scripts/` work in BACKLOG #3.

**The method is worth as much as the fact:** without the negative control, that passing run would
have looked like proof the `metadata:` marker was safe. It proved nothing — a check that passes
for both the right and the wrong input isn't a check. Any future "I verified it with the official
tool" claim needs the same control before it counts.

**Worse, the bare command validates the wrong file here.** Given a directory holding both
manifests — which this repo is — `claude plugin validate .` validates the *marketplace* manifest
and stops, printing `✔ Validation passed` without ever looking at the plugin, its skills, or the
frontmatter above. Reproduced twice, 2026-09-07. The `CLAUDE.md` warning below appears only when
`plugin.json` is named explicitly.

**Settled 2026-09-07 (BACKLOG #14), for whoever writes Orclab's `RELEASING.md`:** the gate is

```bash
claude plugin validate .claude-plugin/plugin.json
```

**Name the file, and do not pass `--strict`.** Naming it is not optional polish — the bare form
checks the marketplace manifest and nothing else, so it is the negative-control failure above in
live form: green for the right input and the wrong one alike. `--strict` is left off because it
promotes to an error the one warning Orclab gets — that `CLAUDE.md` at the plugin root is not
loaded as project context — which is a deliberate, correct layout choice, not a defect. Failing a
release on it would block on the file doing exactly its job, and the warning's own suggested
remedy ("use a skill instead") would push Orclab's internal development guidance into every
consuming project's context, which is the boundary this very file exists to draw.

Expect `✔ Validation passed with warnings`, with that one warning. And per the paragraphs above, a
pass still says nothing about frontmatter — never write a release step that implies otherwise.

## Marketplace/install gotchas, found dogfooding v6 in Desktop (2026-09-06)

Three real, separate bugs stacked on top of each other while getting v6 actually working live —
worth naming individually so a future reinstall failure doesn't get misdiagnosed as any one of
them by pattern-matching on the symptom alone:

1. **`owner`/`author` requires a `name` string — email-only is invalid schema.** Dropping `name`
   entirely (to satisfy "no personal name in the byline") silently broke every
   `marketplace add`/`marketplace update` call after that commit, with a confusing downstream
   symptom ("Plugin not found in marketplace" / "marketplace.json no longer present") that has
   nothing to do with schema on its face. Fix: keep `name` (a non-personal value like the plugin's
   own name is fine), add `email` alongside it, never replace `name` outright.
2. **A `github`-sourced marketplace registration fetches `marketplace.json` via GitHub's API, not
   local git credentials.** For a private repo this comes back as if the file doesn't exist at
   all (not a permissions error) — confirmed live, `claude plugin marketplace update` reported
   "The marketplace.json file is no longer present in this repository" for a file that `gh api`
   confirmed was present on the default branch the whole time. A plain `git fetch`/`pull` in the
   same repo worked fine (inherits the user's own git credential helper) — it's specifically the
   marketplace-refresh code path that has no private-repo auth of its own. Fix, for a
   personal/local-only plugin: register the marketplace by local path
   (`claude plugin marketplace add ~/path/to/repo`) instead of by GitHub `owner/repo` — this
   avoids the GitHub API entirely and reads the working tree directly.
3. **A locally-registered marketplace clone does not auto-refresh on plugin reinstall.** Desktop
   (and the CLI) keep their own clone under `~/.claude/plugins/marketplaces/<name>` (shared state
   across CLI and Desktop on the same machine); uninstalling and reinstalling the *plugin* reuses
   that existing clone as-is rather than re-pulling it. A stale clone silently caps the installed
   version at whatever commit it was cloned from. Fix: `git -C
   ~/.claude/plugins/marketplaces/<name> fetch && git reset --hard origin/main`, or remove and
   re-add the marketplace registration outright, before assuming a reinstall picked up new code.
4. **A freshly (re)installed plugin does not become available mid-conversation — confirmed on
   both Desktop and the CLI.** Skills/commands load when a conversation starts; an existing chat
   thread in Desktop kept reporting "Unknown command" and ambient natural-language misses even
   after the plugin was correctly reinstalled with the right version and skill count. A
   brand-new chat picked it up immediately, both via explicit invocation (`/orclab:orc-code`) and
   ambient matching ("i want to use orc-code to make a java project" correctly inferred both the
   new-project path and the language). Separately confirmed live on the CLI (2026-09-06): after
   reinstalling Orclab mid-session via `claude plugin uninstall`/`install` (to pick up v7), the
   `Skill` tool reported `Unknown skill: orclab:orc-publish` in that same long-running session,
   even though `installed_plugins.json` and the plugin cache both correctly showed the new
   version. **Always test a fresh install/update in a genuinely new session — CLI or Desktop —
   not the one used to debug or trigger the install.**

## Dogfooding a real project: three different things, three different rules

Found dogfooding `/orc-publish` on Orcshot (2026-09-06): a session nearly ran Orcshot's own real
release process (a genuine `dpkg-buildpackage`/`debsign`/`dput` upload to a live PPA) as a side
effect of testing Orclab's publish mechanism — from a context that had no visibility into
Orcshot's own in-progress state (real, uncommitted tray-modernization work sitting in the working
tree). Three genuinely different things were tangled together in that near-miss, and they need
different rules, not one blanket "don't touch other projects":

- **Orclab's own framework source** (`skills/`, `commands/`, `scripts/`, `CLAUDE.md`, `docs/`, its
  own `BACKLOG.md`) is edited only as deliberate Orclab development — never as an incidental side
  effect of using the plugin somewhere else.
- **A consuming project's own `.orclab/` config** (e.g. `.orclab/publish/channels.yaml`) is that
  project's own data, not Orclab's. Any session working on that project can and should write it
  directly — including a real end user's own independent session with Orclab installed as a
  plugin, not just a session dogfooding Orclab itself. Requiring every consuming project's config
  to be populated from Orclab's own dev repo would defeat the point of shipping a reusable plugin.
- **A consuming project's own high-stakes real actions** (a real release, deploy, or publish) do
  not belong in a session centered on Orclab's own development, or in any session that doesn't
  actually have that project's real current state in view. They belong in a session genuinely
  centered on that project — real end user's or a dogfooding pass, doesn't matter which, only
  whether the session can actually see what's really going on there. Testing that such an action
  *would* work (a dry run, a plan resolution) is fine anywhere; actually executing it is not.
