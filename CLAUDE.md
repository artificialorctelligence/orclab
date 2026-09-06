# Developing Orclab

This is guidance for whoever (human or Claude) designs Orclab's *own* future skills and
commands — not something Orclab ships to consuming projects. It's "project" category under
Orclab's own taxonomy: real, verified facts about how Claude Code's command/skill system
actually works, learned the hard way while building `/orc-code` through `/orc-git`, so the next
component gets designed right the first time instead of rediscovering the same gaps.

Every claim below was actually checked — against the real, current official docs, or against
live, direct behavior observed in a real session — not assumed from memory. Where something is
inference rather than a confirmed fact, it's labeled as such.

## Commands and Skills are different things, not merged

A `commands/*.md` file and a `skills/<name>/SKILL.md` file are distinct component types. An
early research pass this project did wrongly concluded they'd been "merged into the same
interface" — that came from a blog aggregation, not the primary docs, and doesn't hold up:
Anthropic's own plugins reference describes them as separate ("commands are simple markdown
files; skills are directories with `SKILL.md`").

**Real, confirmed bug, not theoretical**: the Claude Desktop client does not register plugin
`commands/*.md` files as slash commands at all. Confirmed live — `/orclab:orc` and `/orclab`
both returned "Unknown command" in that client, on an install that worked correctly via the CLI.
Skills, by contrast, invoke correctly there (confirmed via `ponytail`'s real `/ponytail`).

**What this means for every future `/orc-*` command**: if it needs to work in Desktop (which is
the actual daily-driver surface, not the CLI), it needs a thin wrapper Skill too — the same
"point at the real content, don't duplicate it" pattern `orc.md` already uses to reach
`orc-help.md`. `commands/*.md` stays for CLI use; the wrapper Skill is additive, not a
replacement.

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

1. Does it need to work in Desktop? If yes, it needs a wrapper Skill, not just a `commands/*.md`
   file.
2. Is it conversational/workflow-starting, or one-shot/side-effecting? The former stays default
   (natural-language triggerable); the latter gets `disable-model-invocation: true`.
3. Does its description reference its own real name explicitly, to give ambient matching the
   strongest possible cue?
4. Does it need to orchestrate a sub-component that should never fire on its own? Give that
   sub-component `disable-model-invocation: true` and invoke it explicitly by name.
5. Does the capability already exist as a real skill (built-in, or from another plugin)? Wrap it
   — with an availability check — rather than rebuilding it.
