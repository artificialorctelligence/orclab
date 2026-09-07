# Developing Orclab

This is guidance for whoever (human or Claude) designs Orclab's *own* future skills and
commands — not something Orclab ships to consuming projects. It's "project" category under
Orclab's own taxonomy: real, verified facts about how Claude Code's command/skill system
actually works, learned the hard way while building `/orc-code` through `/orc-git`, so the next
component gets designed right the first time instead of rediscovering the same gaps.

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
Nothing in the plugin can suppress the bare-form toast, so it is Anthropic's to fix; reported
upstream on `anthropics/claude-code`.

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
deploy because your code looks ready."* Real fit for Orclab: anything genuinely one-shot and
side-effecting the moment it runs — `/orc-version release` (pushes and publishes), `/orc-git
push`. Anything more conversational and workflow-starting (`/orc-code`'s ask-questions-then-
scaffold flow) should stay default, since the whole point there is natural-language
triggerability matching a `/cat-code`-style dual-invocation UX.

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

## Wrap real, existing skills — don't reinvent them

The same "wrap, don't reinvent" principle Orclab already applies to `feature-dev` and
`code-modernization` (in `orc-code.md`) extends to built-in/environment-provided skills too.
Example: a real `pptx` skill capable of generating real PowerPoint files, with real bundled
scripts and hard-won gotchas already documented, already exists in this environment — a future
`/orc-doc pptx ...`-style command should delegate to it, not rebuild PowerPoint generation from
scratch.

**One real caveat, not to skip**: some such skills are environment-provisioned rather than
universally present (the real `pptx` skill found here lives under a Desktop-specific config
path, suggesting it may not exist the same way in every client). Any component that delegates to
one needs the same "check it's actually available, tell the user plainly if not" guard
`orc-code.md`'s flows already use for `feature-dev`/`code-modernization` — never assume silently.

## Checklist for designing a new `/orc-*` thing

1. Build it as `skills/<name>/SKILL.md`. There is no `commands/` directory any more, and the
   docs tell plugin authors to use `skills/` for new work.
2. Is it conversational/workflow-starting, or one-shot/side-effecting? The former stays default
   (natural-language triggerable); the latter gets `disable-model-invocation: true`.
3. Does its description reference its own real name explicitly, to give ambient matching the
   strongest possible cue?
4. Does it need to orchestrate a sub-component that should never fire on its own? Give that
   sub-component `disable-model-invocation: true` and invoke it explicitly by name.
5. Does the capability already exist as a real skill (built-in, or from another plugin)? Wrap it
   — with an availability check — rather than rebuilding it.
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
