---
name: backlog-discipline
description: Use when a real finding, gap, or deferred decision surfaces that won't be fixed right now but is worth tracking — or when resolving, updating, or considering deletion of an existing BACKLOG.md entry. Maintains a single flat BACKLOG.md with permanent, non-reused entry numbers and layered (not overwritten) resolution history.
---

# Backlog Discipline

`BACKLOG.md` is a single flat file tracking real, open findings — not a task tracker, not a
wishlist. Each entry keeps the reasoning that led to it, not just a one-line title, so picking it
up later never requires re-deriving the "why" from scratch.

## When to add an entry

Add an entry when something real is found that:
- has a genuine consequence (not a hypothetical one), and
- isn't being fixed right now.

Don't add an entry for a task you're about to do in this same session — that's just work, not
backlog. Don't add an entry for speculative future-proofing with no concrete trigger.

## If `BACKLOG.md` doesn't exist yet

Create it first, with this exact header:

```markdown
# Backlog

Open items not yet scheduled into a task. Each entry keeps the context that
led to it - not just "what," but "why this matters" - so picking it up later
doesn't require re-deriving the reasoning from scratch.
```

Then add the first entry below it, numbered `#1`.

## Numbering

Scan the file for every `## #N:` heading and take the highest `N` seen. The new entry is `N + 1`.

**Exception — the highest-numbered entry itself was deleted:** scanning the file alone then finds
a lower maximum than history actually reached, which would silently reuse a number that's
supposed to be permanent (see Deletion below). Before numbering a new entry, check whether a
higher number ever existed — `git log -S'## #' -- BACKLOG.md` (or equivalent) — and take the true
historical maximum, not just the current file's. Every other deletion (anywhere but the current
maximum) leaves the file's own maximum unaffected, so scanning the file alone is sufficient there.

## Writing a new entry

```markdown
## #<N>: <short, specific title describing the real problem>

<Context: what was found, when/how, and why. State the real, concrete consequence explicitly —
not "this could theoretically cause X" but the actual thing that happens. If discovered during a
specific piece of work, name it, so a future reader knows the circumstances.>

<If the finding has a clear scope boundary — what it does NOT affect — say so explicitly, the
same way you'd state what it does affect. This prevents both under- and over-reacting to the
entry later.>
```

Keep it a real paragraph or few, not a checklist stub. The entry should let someone with zero
memory of this conversation understand the problem and its stakes.

## An entry that says another entry is needed

Sometimes writing one entry surfaces a second, genuinely separate finding. When that happens,
**create the second entry in the same session, and refer to it by its real number.**

Never write "this would need its own entry" and stop there. That is a promise the file cannot
keep: prose describing an entry that does not exist is invisible to anyone scanning headings, and
the work it names is tracked nowhere at all.

This is not hypothetical. Orcshot's #197 ended with "no existing entry tracks that yet - it would
need its own, separate from this one," describing the single largest piece of work in that
project's publishing effort. No entry was created. It stayed untracked in both repos until
someone happened to ask what was still open, a day later, and it became #198 only then.

Two consequences of doing it properly, both worth having:
- The reader of #197 can follow a number to real, written context instead of a description of
  context that was never written.
- A forward-reference that names a number is **mechanically checkable** - does that entry exist?
  A forward reference written in prose is not checkable by anything.

If the second finding genuinely doesn't warrant its own entry, say why in the first entry rather
than leaving a dangling promise. "Out of scope here, and not worth tracking separately because X"
is a complete thought; "this would need its own entry" is not.

## Resolving an entry

**Never delete or rewrite the original diagnostic text.** Append to it instead:

1. Add `(RESOLVED YYYY-MM-DD)` to the end of the entry's title line.
2. Add a new paragraph below the original text, starting with something like "**Resolved for
   real, not just tracked**:" or "**Resolved**:", explaining what actually fixed it and how you
   know (what was verified, not just what was changed).

The original entry stays intact above the resolution note. A reader should be able to see both
the original problem *and* how it was actually closed out, in one place.

**This applies whenever you record that an entry is closed — not only when you're the one closing
it.** Discovering that earlier work already resolved something is still resolving it, and gets
both steps: the heading marker and the paragraph. So does adding "a note" that an entry is no
longer open. If the body says an entry is closed and the title line doesn't, the entry is worse
than it was before — the heading is the only part anything scans, so it now advertises the
opposite of what it says.

Orclab's own #12 sat that way: its body recorded that v8 had already closed it, its title line
didn't, and a later session read the heading, concluded the design question was still open, and
came close to re-designing a component that had already shipped. The plan that produced it said
"#12 gets a note recording that v8 already closed it" — a note, never a resolution — so this
section was never consulted, and every downstream review faithfully checked the work against that
framing.

## Deleting an entry

Delete an entry outright — not "mark resolved," not archive it — only when the entry's owner
(ask, don't assume) explicitly judges it no longer worth tracking: e.g. the scenario it describes
can no longer affect any real user, or it was superseded by a different entry.

When deleting: remove the entire `## #N: ...` section. **Do not renumber any other entry, and do
not reuse `N` for a future entry.** A gap in the numbering (e.g. #187, #189, with no #188) is
expected and correct — it's a real signal that something was found and explicitly judged not
worth tracking, not a bug in the file.

## Relationship to superpowers

This skill covers backlog discipline only — tracking real findings in a single file. It doesn't
replace the surrounding brainstorm → spec → plan → build → verify → merge cycle; that's
`superpowers`' job (`superpowers:brainstorming`, `superpowers:writing-plans`,
`superpowers:subagent-driven-development`). This skill assumes that cycle is available for
everything outside backlog entries themselves, rather than reimplementing it.

## What NOT to do

- Don't turn this into a general task list — it's for findings, not routine planned work.
- Don't silently delete an entry because it looks stale to you — surface the judgment call.
- Don't compress or summarize an old entry's context to save space — the context is the point.
- Don't leave a dangling forward-reference. If an entry says another entry is needed, create it
  and name its number before the session ends.
