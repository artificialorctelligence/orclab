---
name: code-discipline
description: Background rules for any production code Claude is about to write or change, in any language - inside /orc-code, inside a subagent executing a plan, inside a bug fix in chat. Seven rules on the shape of code - linear control flow, bounded loops, resources closed on the error path, short functions, loud checks that survive release, no swallowed errors, zero warnings - with where each one comes from and what each stack's tooling enforces. Not a command; Claude reads it whenever code is about to be written.
user-invocable: false
---

# Code Discipline

`test-discipline` says how a test is written. This says how the code under it is written. Seven
rules, each traced to its source so the next reader can judge it rather than take it on trust;
five are from Holzmann's 2006 "Power of Ten" for JPL flight software, one from Martin's *Clean
Code*, one is the resource idiom every stack already has. Holzmann's own opening is the reason
there are seven and not seventy: *"most existing guidelines contain well over a hundred rules,
sometimes with questionable justification."* These are the ones that hold up, and each maps to
something a linter can check (BACKLOG #40, researched 2026-09-13).

Applies whenever code is about to be written or changed, whoever started it — a `/orc-code`
scaffold, a subagent's task, a one-line fix in chat. The rules are in the order they bite.

## 1. Control flow stays linear — no more than two levels of nesting

Handle the exceptional case and return early; the happy path reads top to bottom at one level.
Two levels is Martin's number (*"the indent level of a function should not be greater than one or
two"*); the Linux kernel allows three. Early returns are not a violation — Holzmann says so in
the rule that inspired this one: *"an early error return is the simpler solution."* Recursion is
fine; the flight-software ban on it exists for static call-graph proofs, not for readability.

## 2. Every loop has an exit you can name

`for x in items` is bounded by its source. The rule is for `while`: a counter, a deadline, or a
bounded source, written down — never "it can't spin forever". Reaching the ceiling is an error
the function reports, not a silent stop. Holzmann's rationale: *"prevents runaway code."* An event
loop that is *meant* to run until the process ends is the one exemption he names, and it says so
in a comment.

## 3. Close everything you open — on the error path too

A file, a socket, a lock, a transaction, a temp dir: opened inside the construct the language
provides for exactly this (`with`, `use`, `defer`, try-with-resources, `try`/`finally`), so the
error path releases it without anyone remembering to. The error path is the whole point; the
happy path would have closed it anyway.

## 4. One function, one job, about 60 lines

Holzmann: *"what can be printed on a single sheet of paper… no more than about 60 lines"*, because
a function is *"a logical unit… understandable and verifiable as a unit."* Sixty is the ceiling,
not the target — Linux says one or two screenfuls. A function that needs a section comment in the
middle is two functions.

## 5. Check what you did not produce, and fail loudly with a check that survives release

Holzmann's rule is two assertions per function — a *density*, against 60-line functions, and in
his C an assertion is a shipped runtime check: *"when an assertion fails, an explicit recovery
action must be taken."* Do not translate it as the `assert` keyword. In every language Orclab's
stacks use, `assert` is debug-only — Python (`-O` emits no code for it), Kotlin (needs `-ea`),
Swift (*"In -O builds, condition is not evaluated"*), Dart (*"In production code, assertions are
ignored"*), C# (`Debug.Assert` is `[Conditional("DEBUG")]`), GDScript (*"only executed in debug
builds"*). A check written with it vanishes from the shipped app, which is the opposite of the
rule. So: a function validates its inputs from outside itself — arguments from a caller it does
not own, a file, the network, a user — with `raise`, `require`/`check`, `precondition`, an
`ArgumentException`, `push_error` and a return; and the count is not kept. Holzmann's density was
a proxy for "will a defect be intercepted"; `/orc-test analyze` measures that directly, as TCE.

## 6. Never swallow an error

A bare `except: pass`, an empty `catch`, a `Result` dropped on the floor is not handling; it is
the defect moving somewhere it will be harder to find. PEP 8: a bare except *"can disguise other
problems."* Handling is one of three things: recover and say how; log the traceback and carry on;
or clean up and re-raise. A **narrow, named, commented** suppression — `suppress(FileNotFoundError)`
with the reason beside it — is handling; ESLint's `no-empty` draws the same line, allowing an empty
`catch` only when it *"contains a comment."*

## 7. Zero warnings from day one — not zero errors

Holzmann's rule 10: all warnings enabled at the most pedantic setting, *"from the first day of
development"*, and it *"applies even in cases where the compiler or the static analyzer gives an
erroneous warning… the code causing the confusion should be rewritten."* A warning left in on
day one is a hundred by week three, and the real one is invisible among them. The switch, per
stack, confirmed against each toolchain's docs 2026-09-13: Kotlin `allWarningsAsErrors = true`;
C# `<TreatWarningsAsErrors>`; Swift `-warnings-as-errors`; Dart `analysis_options.yaml` severity
overrides; GDScript `debug/gdscript/warnings/*` in `project.godot` (0 ignore, 1 warn, 2 error);
JS/TS ESLint rules at `error`; Python has no compiler warnings — ruff and pyright are the
analyzer, `-W error` for the runtime ones. Each `stack-*` skill's `## Lint — where code-discipline lands` section has the config: the
switch, plus the linter rules for nesting, function length and swallowed errors where that
language's tooling has them (Dart and GDScript have no free nesting/length rule — said there).

## What this is not

- Not a style guide — naming, formatting and import order are the formatter's job.
- Not `test-discipline` — that is the test; this is the code the test is written against.
- Not enforced by this file. A rule in prose fires only when it is read. The checkable ones
  (nesting, function length, empty catch, warnings) are linter configuration — each `stack-*`
  skill's `## Lint` section — and Orclab's `lint_on_write` hook runs the project's configured
  linter on every `Edit`/`Write`, whoever made it, and reports what it found. No config, no run:
  the hook carries no rules of its own. `ORCLAB_LINT_ON_WRITE_OFF=1` disables it.
