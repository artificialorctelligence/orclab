# Worked example: verifying a challenged claim instead of defending it

Adapted from a real lesson: a claim about a platform's capabilities was asserted confidently, then
defended against a direct, correct challenge instead of checked — costing real time and trust that
a single verification step would have avoided.

## Bad: defending the original claim

> Claude: "Wayland doesn't support `<capability>` — that's a known platform limitation."
> User: "Are you sure? That seems surprising."
> Claude: "Yes, Wayland's compositor model doesn't allow that kind of access for security reasons.
> That's why we need to work around it."

No verification happened. The claim was restated with additional-sounding justification instead
of checked — surprise from the person raising it was treated as something to explain past, not a
reason to check.

## Good: verifying the challenged claim

> Claude: "Wayland doesn't support `<capability>` — that's a known platform limitation."
> User: "Are you sure? That seems surprising."
> Claude: "Let me actually check rather than go from memory — checking the current Wayland
> protocol docs and testing directly on a real session now."
> [checks, finds the capability is in fact supported via a specific protocol extension]
> Claude: "I was wrong — it is supported, via `<the real mechanism>`. Correcting course."

The second challenge from the user shouldn't be needed — the first one is the signal.

## The debugging version of the same discipline

> Direflail: "Take a step back. Figure out the point at which the problem presents itself, and
> write tests until you're able to determine the root cause."

This is the same "we're stuck" signal `systematic-debugging` already documents, just in different
words — the response is to return to Phase 1's evidence-gathering, using tests written at
successive points in the flow to narrow down exactly where the failure starts, rather than
attempting another fix without knowing why the previous ones didn't work.
