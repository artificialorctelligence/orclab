---
name: test-discipline
description: Background rules for any test Claude is about to write or change, in any language - inside /orc-code, inside a subagent executing a plan, inside a bug fix. Know the code and the scenarios first, TDD, realistic data, mock everything that leaves the process, prove the test can fail, 80% line coverage on what the change touches. Not a command; Claude reads it whenever a test is about to be written.
user-invocable: false
---

# Test Discipline

The failure this exists to close: a test that calls the code and asserts nothing scores 100% on
lines and catches nothing. Every rule here is a way of making sure a test written under Orclab is
*proven* to catch something, not assumed to.

Applies whenever a test is about to be written or changed — a new feature, a bug fix, a refactor,
a subagent's task — whatever the language. The rules are in the order the work happens.

## 1. Know what you are testing before you write

- The code under test is open in front of you, not remembered.
- The project's framework and runner are known. `skills/orc-test/languages/<lang>.md` says which
  for each language `/orc-test` supports; a project's own config wins over that file.
- The scenarios that matter are listed *before* any test exists: empty and null inputs, a large
  input, the async path, the error path, the boundary the code's own `if` names.

## 2. TDD — one law, not two

State the expected behaviour in one plain sentence, write the test, watch it fail, then write the
code. That is `superpowers:test-driven-development`, which every session already loads; this
rule points at it and adds nothing. If you did not watch the test fail, you do not know it tests
the right thing.

## 3. Realistic data

Test data that looks like production, including the edge cases the code's shape alone would not
suggest — a name with a quote in it, a date at a month boundary, a list of ten thousand, a
zero-length file. Not `foo`, `bar`, `1`, `2`.

## 4. Isolation

Anything that leaves the process — a database, an HTTP call, the clock, the filesystem, an
environment variable — is mocked or replaced with a fake, so the test never fails because of the
network, the time of day, or state a previous test left behind. A test that needs the real thing
is an integration test and is named as one.

## 5. Prove the test can fail

After writing it, break the code on purpose once, run the test, confirm it goes red, and revert.
This is a step with an output, not advice:

> Changed `clamp`'s `<` to `<=`; `test_clamp_low_boundary` failed with `assert 0 == 1`; reverted.

It doubles the cost of every test and is the rule most tempting to skip. A test that cannot fail
is the worst kind of debt: it is green forever and means nothing. `/orc-test analyze` does this
at scale later (mutation testing plants the defects for you); this rule is the one-defect version
you run by hand while the code is in front of you.

## 6. 80% line coverage on what the change touches

Before saying "done", `/orc-test coverage <path to what you changed>`. Under 80% on a file you
touched means the work is not finished. The number is per file, not per repo, so a well-tested
neighbour cannot cover for the file you actually changed.

## What this is not

- Not a coverage target for the whole repo — that is `/orc-test coverage` with no path.
- Not the place that says how a language's tools are invoked — that is `languages/<lang>.md`.
- Not a substitute for reading the code. The ladder shortens the solution, never the reading.
