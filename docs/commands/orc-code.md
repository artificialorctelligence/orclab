# /orc-code

## What it's for

You want Claude to write code for you — starting a brand-new project from nothing, adding a
feature to a project that already exists, or taking existing code and either cleaning it up or
moving it to a different language, framework, or version. `/orc-code` figures out which of these
you mean and walks you through it. For the "existing project" and "different language" cases, it
doesn't reimplement that work itself: it hands off to two other **plugins** (separately installed
add-ons for Claude Code) that already do it — `feature-dev` for adding to an existing project,
`code-modernization` for moving code elsewhere — and tells you plainly if either one isn't
installed when it's needed.

## What you type

| You type | What it does |
|---|---|
| `/orc-code` | Asks whether you're starting something new or working on an existing project, then follows whichever flow below matches your answer |
| `/orc-code <description of what to build or change>` | Same as above, but skips any question your description already answers |
| `/orc-code refactor` | Improves existing code in place, without changing its language, framework, or version — this is **quality mode** |
| `/orc-code refactor <what to change it to>` | Names a different language, framework, or version, and it moves the code there instead — this is **migration mode** |

It never looks at your files to decide which of these you mean — an empty folder, an existing git
history, whatever's already there — it only goes by what you typed, or by asking. If a plain
`refactor` request could reasonably be either mode (something like "modernize this"), it asks you
to pick, explaining each option in a sentence, rather than guessing.

## What it will ask you

First, if it isn't already obvious from what you typed: are you starting something new, or
working on an existing project?

**Starting something new**, one question at a time, skipping any your description already
answered:
1. What would you like to name the project?
2. Is it an app or a game? (A CLI tool or a library counts as an app. If what you're building
   doesn't fit either, it says there's no default for that and asks directly what stack you
   want.)
3. Which platforms — any combination of Linux, Windows, Mac, Android, iOS, web?
4. Once it knows the type and platforms, it proposes a **stack** — the language and toolkit the
   project will actually be built with, for example "Python" or "Kotlin + Jetpack Compose" — and
   asks whether that sounds right, or whether you'd rather pick something else. If nothing's been
   worked out yet for the combination you picked, it says so plainly and asks what you want
   instead of proposing something unproven.
5. Whether anyone you didn't invite will be able to reach it — a public website or API, yes; an
   app that runs only on your own machine or phone, no. It guesses from the platforms you ticked
   and asks you to confirm, and the answer decides which security rules the new project is built
   to from the start.
6. Whether to run the project's tools inside a container, so nothing has to be installed on your
   machine — it proposes no unless the stack is one that's unusual to have installed, and skips
   the question for a stack that can't (iOS needs a Mac). The container is only where the tools
   live while you develop; what you ship is the ordinary project files.
7. Would you like a minimal example, a basic **scaffold** (a skeleton project with the standard
   files and folders for that stack already in place, but no real features yet) with common
   features, or something specific — describe your use case?

**Adding to an existing project**: whatever the `feature-dev` plugin itself asks — `/orc-code`
hands the request to it and follows its own guided process from there.

**Refactoring, quality mode**:
- Before it deletes a test, it shows you the full list of what it wants to remove and why, and
  waits for a yes.
- After a round of fixes, it shows you the numbers before and after (how much of the code the
  tests exercise, and how well they'd catch a real bug). If either is still short of where it
  needs to be, it asks "Another round?" and waits for your answer before trying again — unless
  the shortfall is in a file the test suite doesn't touch at all, in which case it says so
  instead: another round can't fix that, and whether that file gets a real, working test is left
  for you to decide, not something it takes on itself.

**Refactoring, migration mode**: the same two questions as quality mode above (the deletion list,
and whether to run another round), plus:
- The same type-and-platform questions as a new project, to settle what the code is moving *to*.
- A handful of upfront questions the `code-modernization` plugin itself asks before it starts —
  what's in scope, whether the project builds locally, any unusual build steps, whether a
  migration's been attempted before, and anything that's off-limits to touch.
- Before it commits to an overall plan, and again after converting one small piece as a trial run,
  it stops and shows you what it's found and what it intends to do next, and waits for you to say
  go ahead — it never approves its own plan on your behalf.

## What it changes

- **New project**: creates the project folder (if needed), sets up the language's normal tooling,
  and writes the starter files for the stack and starting point you chose. It runs the project's
  own build or test command before calling the job done, and won't report it as finished until
  that command actually passes. It also writes the project's lint and security-check settings,
  and — when you said strangers can reach it — the pieces those rules need from day one: a
  login layer, a public folder separate from the code, error pages that give nothing away — and,
  if you said yes to the container, a `Dockerfile` and a `compose.yaml` at the project root,
  committed, that the test command and the on-write linter then use.
- **Existing project**: whatever `feature-dev`'s own workflow changes — `/orc-code` doesn't touch
  anything beyond what that plugin does.
- **Quality mode**: if the project doesn't already have a lint configuration (settings for the
  tool that checks code style and flags likely mistakes) or a mutation-testing configuration
  (settings for the check that deliberately breaks the code in small ways to see whether the
  tests would notice — used by [`/orc-test`](orc-test.md)), it writes one and commits it on its
  own (the security-check settings are written the same way), separately from the code changes.
  It then fixes files one at a time — always with the project's tests passing after each one —
  committing each file or module's fix separately. It leaves architecture-level opinions
  (whether a module should exist at all, say) as a suggestion for you, not a change it makes.
  If the `code-modernization` plugin is installed, it also runs that plugin's security scan and
  applies what holds up; if not, it tells you and reviews the code against the security rules
  by hand.
- **Migration mode**: creates `.orclab/modernize/` — a scratch folder holding the migration
  plugin's own working files — and does the actual conversion inside an isolated copy of your
  project, so the work in progress can't disturb whatever you're already doing: either a
  **worktree** (a second, temporary checkout of your project on its own branch) or a separate
  scratch clone. Once the new code clears the two checks named under "What it will never do
  without asking" below (its own tests pass, and it matches or beats the original on both how
  much code the tests exercise and how well they'd catch a real bug), it copies that code back
  over the checkout, and copies the plugin's plan and its catalogs of rules and changes into
  `docs/` so they stay with the project.

## What it will never do without asking

- It never decides "new project" vs. "existing project" vs. "refactor" by inspecting your files —
  only from what you typed, or by asking you directly.
- It never proposes a stack for a platform combination nothing's been worked out for yet, and it
  never scaffolds a new project — or migrates one — into a stack it doesn't already have
  background knowledge of. In either case it does the research (or asks you what you want) first,
  rather than guessing at conventions on the spot.
- It never calls a new project finished until its build or test command has actually passed.
- If `feature-dev` isn't installed, it says so plainly and stops rather than trying to add the
  feature itself; if it is installed, it tells you plainly that it's handing the work to that
  plugin's own process, rather than quietly doing so.
- It never guesses whether an ambiguous refactor request means a cleanup or a move to something
  different — it asks.
- In quality mode, it never starts making changes while the project's own tests are already
  failing — that gets fixed by hand first, since fixing pre-existing failures isn't part of this
  mode. It also never starts making changes until its own first measurement (running the linter
  and a full [`/orc-test`](orc-test.md) `analyze`) has finished, even though that first run can
  take a while on a large project.
- In quality mode, it only ever applies a linter's *safe* automatic fixes — never one that risks
  changing what the code actually does — and it never adds an exception to skip a rule just to
  make a number look better; a rule is either fixed, or given one specific, explained exception at
  that exact spot.
- In quality mode, it never edits a lint or mutation-testing configuration the project already
  has — it only writes one if the project doesn't have one yet.
- In quality mode, for a file the test suite doesn't exercise at all, it never rewrites that
  file's actual logic — a passing suite can't prove such a change safe. The only fix it makes
  there is a mechanical, behavior-preserving move (pulling a block out into a named helper,
  unchanged, with its variables passed in as parameters).
- In quality or migration mode, it never deletes a test without showing you the full list first
  and getting a yes.
- In quality mode, it never says the code is "clean" without re-measuring the numbers after the
  fixes are in.
- In migration mode, if the `code-modernization` plugin isn't installed, it stops and gives you
  the install command rather than attempting the move without it.
- In migration mode, it never starts moving code before recording how well the current tests
  cover and catch bugs in it — if that suite isn't passing, or barely exists, that gets fixed or
  written first, so there's a fair baseline to compare against at the end.
- In migration mode, it never signs off on the migration tool's own checkpoints for you — it stops
  and shows you the plan, and later the trial conversion, before continuing either time.
- In migration mode, it never calls the move finished until the moved code's own tests pass and it
  exercises at least as much of the code, and would catch at least as many real bugs, as the
  original did. If either check falls short, it says which one instead of calling the job done.
