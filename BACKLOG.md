# Backlog

Open items not yet scheduled into a task. Each entry keeps the context that led to it — not just
"what," but "why this matters" — so picking it up later doesn't require re-deriving the reasoning
from scratch.

## #1: `/orc-*` command namespace with parameter routing and stack defaults (RESOLVED 2026-09-05)

Raised by direflail while reviewing the Orclab v1 (process core) design (2026-09-04), explicitly
as spitballing to check whether it should change v1's scope. It shouldn't, and doesn't — v1 (see
`docs/superpowers/specs/2026-09-04-orclab-v1-process-core-design.md`) is three behavioral skills
(`backlog-discipline`, `release-checklist`, `environment-registry`); this idea is a different kind
of thing entirely: a command/intent layer for directing *new* project work, not a discipline for
tracking existing project state.

**The idea, as described:**
- A `/orc-` command base, e.g. `/orc-code` to signal "code needs to be written."
- Subcommand parameters that change behavior significantly — e.g. `/orc-code refactor` means the
  project is changing language or language version, which should trigger an extended
  question-asking phase to nail down scope before anything happens (echoes the brainstorming
  skill's own "classify, then ask" shape, but scoped specifically to refactor/migration work).
- Natural-language routing: a plain request like "I'd like to use /orc-code to write a hello world
  project in Java" should be recognized as the `/orc-code` path with `java` as the inferred
  language parameter, without requiring the literal command syntax.
- Defaults, per language and per project type — e.g. Java desktop apps default to
  Java + Spring + JavaFX — with version/specifics still confirmed via questions rather than
  silently assumed.

**Why this matters:** if useful, this becomes the primary way Orclab gets used day-to-day
(starting new work), which is a different value proposition than v1's "keep track of what's
already true about a project." Worth designing well, not bolted onto v1 as an afterthought.

**Implementation mechanism, confirmed live (2026-09-04, corrected from this entry's own first
draft, which wrongly guessed plugins couldn't do this):** Claude Code plugins register real slash
commands via a `commands/*.md` file per command, with an `argument-hint` frontmatter field and
`$ARGUMENTS`/`$1`/`$2`-style positional parsing in the body — a real installed example,
`code-modernization`'s `modernize-assess.md`, takes `<system-dir> [--show-secrets] | --portfolio
<parent-dir>` and branches on `$ARGUMENTS` directly. This directly supports the `/orc-code
refactor`-style subcommand-as-parameter idea with no new mechanism needed. Still open: how many
commands beyond `/orc-code` are needed (this entry only describes the one example given), how the
natural-language-routing case ("use /orc-code to write X" without the literal slash) gets
recognized without a literal invocation, and how per-language/per-stack defaults get
stored/overridden per project.

**Next step, when picked up:** a fresh `superpowers:brainstorming` pass (Architectural path,
given it's a new subsystem with its own command surface and inference logic), separate from v1's
spec and plan.

**Resolved for real, not just tracked**: shipped as `/orc-code` (Orclab v2, 2026-09-05) — see
`docs/superpowers/specs/2026-09-05-orclab-v2-orc-code-command-design.md` and its companion plan.
Both of this entry's own open questions got real answers: natural-language routing without a
literal invocation is handled by reading `$ARGUMENTS` for intent (the same read-and-classify
mechanism Claude Code's own skill matching already uses, not a separate classifier) rather than
requiring the literal keyword; per-language/stack defaults are baked directly into
`commands/orc-code.md`'s own Defaults Table, editable in place, currently holding exactly one
real, confirmed entry (see #4 for the much larger, still-open research behind which defaults
belong there). `/orc-code` covers new-project, add-to-existing, and refactor work by wrapping
`feature-dev` and `code-modernization` rather than reimplementing them. Whether more `/orc-*`
commands beyond `/orc-code` get built is now a separate, forward-looking question — `/orc-data` is
already tracked on its own as #5.

## #2: A base visual/design-system layer for apps Orclab helps build — a future sub-project, not v1

Raised by direflail (2026-09-04), separately from #1 and from v1's process-core scope: right now
Orclab has no opinion at all about how the apps it helps build actually *look* — how desktop apps,
mobile apps, and web apps are styled, scaled, and made to behave visually, across platforms. The
concrete comparison direflail gave: Caterpillar (their employer) has an internal framework called
"Blocks," built on React, that fills exactly this role there — but it's employer-owned and can't
be used outside work, so a real gap exists for personal/other-project work.

**What this is NOT**: not another web framework (React/Vue/Angular/Svelte) — those were already
ruled out as beside the point in this same conversation; direflail was explicit that the ask is
about the visual/design layer that sits *on top of* those, not the framework itself. Also not
CSS-utility libraries (Bootstrap, Semantic UI) or admin-panel generators (Refine, react-admin) —
those came up in initial research but don't match the "controls look/scale/behavior across
desktop and web platforms" framing once direflail clarified the actual ask.

**Real candidates surfaced by research (not yet evaluated hands-on, not yet decided)**, roughly in
three layers that would likely need to be picked in combination, not as a single choice:

- **Full design systems** (closest analogs to Caterpillar's Blocks — token-driven theming plus a
  complete component set plus cross-platform scaling rules): Material Design 3 (Google), Fluent UI
  (Microsoft — adaptive layouts scaling across Windows desktop/web/mobile), Carbon (IBM —
  framework-agnostic: React/Angular/Vue/Svelte/web components), Ant Design (strong for data-dense,
  desktop-style apps), GitHub Primer (developer-tool focused).
- **UI component libraries** (the practical implementation layer): shadcn/ui (copy-paste model on
  Radix primitives + Tailwind — you own the source directly, no vendored dependency to work
  around), Chakra UI, MUI (works for web and Electron desktop), Radix UI (unstyled, accessible
  primitives only — maximum control, bring your own visual design).
- **Design tokens** (the actual cross-platform-scaling mechanism underneath either of the above):
  Style Dictionary (Amazon — transforms tokens into CSS/iOS/Android/etc. — the current industry
  standard), Diez (compose tokens in TypeScript, compile to native iOS/Android/Web libraries), the
  W3C Design Tokens spec (stable v1 as of October 2025 — vendor-neutral token format).

No hands-on evaluation of any of these has happened yet — this is raw research, not a decision.
An initial framing (not a recommendation to commit to) leaned toward Fluent UI or Carbon as the
closest single-framework analogs to Blocks, versus shadcn/ui + Radix + Tailwind + a token system
as the more modern, full-code-ownership alternative — but this needs real comparison against
Orclab's actual target platforms (desktop apps, mobile apps, web apps specifically) before
choosing, not just a feature-list comparison.

**Why this matters:** without this, every app Orclab helps scaffold or build would need its visual
styling decided from scratch each time, with no consistent base — the same kind of repeated,
undistilled decision-making this whole framework project exists to avoid.

**Next step, when picked up:** a fresh `superpowers:brainstorming` pass (Architectural path — this
is a new subsystem, and the choice of base framework has wide-reaching downstream consequences for
anything built on it), separate from v1's spec/plan and from #1's command-layer work. Likely needs
its own research spike comparing 2-3 real candidates against Orclab's actual target platforms
before a design gets proposed, not a decision made from the comparison table alone.

## #3: Real enforcement for the discipline v1 only guides — not yet decided how (RESOLVED 2026-09-07)

Raised by direflail (2026-09-04) right after v1 shipped, once it became clear that v1's three
skills (`backlog-discipline`, `release-checklist`, `environment-registry`) are pure guidance: text
Claude reads and follows, with nothing that fails a commit or blocks an action if the discipline
is violated (wrong `BACKLOG.md` numbering, a `RELEASING.md` step silently duplicating CI, an
environment-registry entry that leaked into git instead of memory). direflail had been planning to
build enforcement via the `/orc-*` command idea (#1), but flagged this as possibly its own
consideration, separate from #1, worth discussing before deciding where it belongs.

**What "enforcement" would actually mean, concretely** (not yet built, not yet designed): a
Claude Code `hooks/` script that runs on a real event (e.g. before a commit, or after Claude edits
`BACKLOG.md`) and actually checks the discipline mechanically — re-parses `BACKLOG.md` for
duplicate or reused entry numbers, checks that a resolved entry's original text is still present
verbatim, or similar — rather than trusting that Claude read and correctly applied the SKILL.md
prose. This is a fundamentally different kind of thing than a skill: a skill shapes behavior by
being read; a hook (or a CI lint step) verifies an outcome regardless of how it was produced.

**Open question, explicitly not resolved here:** whether this belongs inside the `/orc-*`
command-layer sub-project (#1), as its own sub-project, or as small additions directly to v1's
existing three skills (each skill could ship its own optional lint script, without needing the
command layer at all). direflail asked to hold off deciding and talk it through first.

**Next step, when picked up:** a conversation (or a fresh `superpowers:brainstorming` pass, if it
turns out to be Architectural-sized) specifically about where enforcement fits relative to #1 and
to v1's existing skills — before any hook or lint script gets designed.

**Update (2026-09-07), from a real leak — enforcement now has a concrete highest-value target:**
A session diagnosing a `gh` auth banner printed a live OAuth token straight into the transcript by
running `gh auth token` as a throwaway diagnostic. That produced a new discipline skill,
`skills/secret-hygiene/SKILL.md` — which is guidance in exactly the sense this entry is about:
prose Claude reads, with nothing that mechanically stops the command from running next time.

It also sharpens this entry's open question rather than just adding to it. For `BACKLOG.md`
numbering, guidance-only is survivable — a wrong entry number is caught later and corrected. A
printed secret is not correctable at all: it lands in the model's context, every subsequent API
request, and the on-disk session JSONL simultaneously, and the only remedy is rotation, which is
the user's work. That asymmetry makes `secret-hygiene` the discipline with by far the strongest
case for real enforcement, and the natural first hook to build if this entry gets picked up —
ahead of the `BACKLOG.md` linting this entry originally imagined.

**Mechanism, confirmed live (2026-09-07):** a Claude Code plugin really can ship hooks, via a
`hooks/hooks.json` file at the plugin root alongside `.claude-plugin/plugin.json` — verified
against the real installed `gitkraken-hooks` plugin in this environment, which registers
`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `SessionStart`, `SessionEnd`,
`UserPromptSubmit` and `Notification`, each as `{matcher, hooks: [{type: "command", command}]}`.
Orclab ships no `hooks/` directory today. **Still unverified, and the thing to check first:** the
exact contract by which a `PreToolUse` hook *denies* a tool call rather than merely observing it —
do not design against a remembered answer, confirm it against the current docs (`currency-discipline`).


**RESOLVED 2026-09-07 — enforcement exists, scoped to the one discipline that most needed it.**
Shipped: `hooks/hooks.json` registering a `PreToolUse` hook matched to `Bash`, backed by
`hooks/scripts/secret_guard.py`. Run its suite with
`cd hooks/scripts && python3 -m pytest tests/ -v` (48 tests). It denies the narrow set of commands
whose entire stdout is a credential, and every denial names the safe alternative so a block
redirects the work instead of dead-ending it.

**The three-way open question above is answered by what shipped, and the answer is the third
option** — small additions alongside the existing skills, not inside #1's command layer and not
its own sub-project. Enforcement turned out to be per-discipline rather than a general mechanism:
this hook knows about secrets specifically, and a future `BACKLOG.md` linter would share the
`hooks/` directory with it and nothing else.

**Deliberate scope limits, not oversights:**
- Only `secret-hygiene` is enforced. The `BACKLOG.md` numbering and `RELEASING.md` step checks
  this entry opened with are still guidance-only, and stayed that way on purpose: those failures
  are correctable after the fact, while a printed secret never is. Raise a fresh entry if the
  numbering discipline actually starts drifting in practice — don't pre-build for it.
- The guard fails open on any internal error, and a `# orclab:allow-secret` marker bypasses it.
  Both are intentional. A hook that wedges every Bash call in every project Orclab is installed
  in would be a worse outcome than the leak it prevents, and a bypass that must be typed
  explicitly leaves the decision visible in the transcript.

**A real bug its own tests caught, worth remembering:** the first implementation read the trailing
`2>&1` of the motivating leak command as a stdout capture and allowed it straight through — the
guard would have missed the exact incident that produced it. Redirect detection now requires a
genuine stdout redirect (no fd digit before `>`, no `>&` form). Writing the regression test for
the real command first, rather than for a tidied-up version of it, is what surfaced that.


## #4: Real per-language/per-domain default stacks for /orc-code — mostly undecided, one confirmed

Raised by direflail (2026-09-05) while designing `/orc-code`'s defaults table (part of #1's work).
When asked for real personal stack preferences to bake in (replacing the original idea's
illustrative placeholder), only one came back genuinely settled; everything else surfaced is real
signal about direction but not yet a decision:

- **Confirmed**: Java desktop → Java + Spring + JavaFX.
- **Unsettled, named as real interests or open questions, not decisions**: Python desktop (unsure
  of the modern stack, guessed "close to what Orcshot uses" but not confirmed), .NET 8 + C# for
  possible Windows desktop work, Unity for game development (wants to explore), mobile (wants
  Android native, iOS native, AND something cross-platform, but hasn't picked any of the three),
  web (HTML5/CSS/JS/React/Python confirmed as the toolset, but not yet mapped into specific
  default combos), database strategy across all of the above ("we'll need to discuss what to use
  in which case" — explicitly not resolved), containerization (Docker — wants to explore),
  observability (Grafana/Prometheus/Loki — wants to explore).

**Why this matters:** `/orc-code`'s defaults table is meant to reflect direflail's real, settled
preferences so the tool proposes something genuinely useful — baking in a guess for a stack
that isn't actually decided would give false-confidence suggestions, working against the whole
"built for me" premise of this project.

**Scope boundary, decided for now:** `/orc-code` v1's defaults table contains only the one
confirmed entry (Java desktop). Every other case falls through to asking directly — which was
already the design's fallback behavior when no default exists, so this isn't a workaround, just
an accurate reflection of what's actually settled today.

**Next step, when picked up:** likely several separate conversations/research passes, not one —
these domains (desktop-per-language, mobile strategy, web-stack-to-default mapping, database
strategy, containerization, observability) are different enough from each other that treating them
as one research question would repeat the same "too much at once" problem this entry itself was
split out to avoid.

**Vocabulary from #17's design pass, 2026-09-08 — a language default is an *ingredient*.**
direflail's framing while scoping `/orc-package`: Orclab ships **ingredients** (reusable units of
knowledge — how to stand up a PPA channel, a default stack for a language), and each project
assembles the ones it needs into its own **recipe**, which is the project's real, existing config —
`channels.yaml`, `RELEASING.md`, and for `/orc-code`'s purposes whatever a scaffolded project ends
up with. Orclab is itself a project with its own recipe, drawing on the same core ingredients as
anyone else.

That reframes this entry usefully. The "defaults table" is really *the ingredients Orclab ships for
`/orc-code`*, and its documented fall-through — ask directly when no default exists — is "no
ingredient for this case yet," which is the same honest state `/orc-publish` reports for a known
but un-onboarded channel. The scope boundary above is not a workaround; it is an accurate
ingredient list with one entry in it.

**Deliberate caution, agreed when the framing was raised: take the vocabulary, not a shared
mechanism.** A channel ingredient (registration, credentials, publish action, confirmation) and a
language ingredient (framework choices, project layout, build tooling) may share nothing beyond the
metaphor. They are consumed by different commands and have different shapes. Unifying them into one
ingredient *system* on the strength of two examples — one of which does not exist yet — would be
exactly the speculative generality this repo keeps deleting. See **#17**, which takes the same
vocabulary and holds the same line.

**One question this raises and does not answer:** #17's design lets a user *capture* a channel
ingredient Orclab does not ship, stored user-level so it survives a plugin reinstall and works for
someone who will never touch Orclab's source. Whether a settled language stack should be capturable
the same way — direflail's real Java-desktop preference living somewhere reusable rather than only
in Orclab's own table — is a genuine question, and is not decided here.

## #5: `/orc-data` — a command for tracking legacy-system info during refactor work

Raised by direflail (2026-09-05) alongside `/orc-code`'s design, describing the real motivation
behind the whole Orclab project: direflail's day job involves bringing 20-year-old Java/C# systems
up to modern standards, and wants a dedicated way to store and organize information about the
system being refactored, to support actually moving it to the new one.

**Real overlap worth checking before designing anything new:** `code-modernization` (the same
plugin `/orc-code refactor` already wraps, per #1's design) ships `modernize-map` and
`modernize-extract-rules` commands — real, existing steps in its workflow that sound like they
may already cover exactly this need (mapping a legacy system's structure, extracting its rules).
Worth reading what those two commands actually do, concretely, before assuming `/orc-data` needs
to be built from scratch — the same "wrap, don't reinvent" instinct already applied to
`/orc-code refactor` itself.

**Scope boundary:** nothing decided yet — no data shape, no fields, no relationship to
`modernize-map`/`modernize-extract-rules` has been evaluated. Not part of #1's `/orc-code` work.

**Next step, when picked up:** read `code-modernization`'s `modernize-map.md` and
`modernize-extract-rules.md` in full first — if they already solve this, `/orc-data` might end up
being a thin wrapper (same shape as `/orc-code refactor`) rather than new logic. Then a fresh
`superpowers:brainstorming` pass for whatever gap remains.

## #6: Per-language manifest version detection/sync for /orc-version — deferred, same reasoning as #4 (PARTIALLY ADDRESSED 2026-09-07 — still open for the formats it names)

Raised by direflail (2026-09-05) while designing `/orc-version` (see
`docs/superpowers/specs/2026-09-05-orclab-v3-orc-version-orc-help-design.md`): when Orclab is
pointed at a project that already has an established version-holding file — Maven's `pom.xml`,
npm's `package.json`, Cargo's `Cargo.toml`, and others — `/orc-version` could detect it at
first-touch and suggest a starting version from what's already there, and/or keep that file's own
version field in sync on every future bump (or at minimum ask each time whether to).

**Why this is deferred, not built now:** real and valuable, but each format has its own real
syntax and its own real risk of a sloppy write breaking a build — this is genuinely a per-format
feature, not one generic mechanism. The same shape of problem as BACKLOG #4's stack-defaults
research: broad enough that folding it into `/orc-version`'s own v1 design would have let it
swallow everything else being decided there.

**Scope boundary, decided for now:** v1 of `/orc-version` only touches `.claude-plugin/plugin.json`
/ `marketplace.json` (when present) and falls back to `CHANGELOG.md` + a git tag otherwise. It does
not detect or write to any other language's version-holding file.

**Next step, when picked up:** likely one format at a time (Maven first, or whatever direflail
actually needs first for real work), each with its own real syntax handled correctly — not a
generic "detect any manifest" abstraction built speculatively ahead of a second real case.

**Partially addressed by v8 (2026-09-07), and deliberately NOT closed.** v8's `/orc-release`
work built the mechanism this entry describes — real per-format read/write handlers in
`skills/orc-release/scripts/orc_release/versionfiles.py`, detection of which version-holding
files a project actually has, consistency verification across all of them, and rollback — and it
followed this entry's own "one format at a time" reasoning exactly rather than overriding it.

**But none of the three formats this entry names shipped.** v8 implemented `pyproject.toml` and
`debian/changelog` (plus the pre-existing `.claude-plugin/plugin.json` / `marketplace.json`),
because those are the formats real projects here use today — Orcshot's release needed them. `#6`
was raised about `pom.xml`, `package.json` and `Cargo.toml`, and not one of those has a handler.
v8's own `CHANGELOG.md` entry originally claimed "Closes BACKLOG #6"; that claim was wrong and
has been corrected to say what actually shipped. Recording that here rather than quietly deleting
it: the mechanism landing is not the same as the ask landing.

**What remains open, concretely:** add a handler for `package.json`, `Cargo.toml`, or `pom.xml`
when a real project here needs one. The cost is now much lower than when this entry was written —
`versionfiles.py` is the single place that owns version-setting, so a new format is one
read/write pair plus its entry in `KNOWN_FORMATS`, not a new mechanism. The first-touch
"suggest a starting version from what's already there" half of the original ask is also still
unbuilt.

## #7: Distribution-channel download/install metrics — carried over from Orcshot #186, direflail wants Orclab to own this eventually (PARTIALLY ADDRESSED 2026-09-08 — Launchpad confirmed, Snap/Flathub still unverified)

Raised by direflail (2026-09-06), explicitly carrying over Orcshot's own `BACKLOG.md` #186 (raised
there 2026-08-28, still open, not resolved on that side) and widening it: direflail wants whatever
this becomes to live in Orclab, not as an Orcshot-specific script, since any project publishing to
multiple distribution channels would want the same thing. Not wanted yet — direflail's own words:
"it doesn't have to be done yet."

**The original ask, verbatim from Orcshot's #186:** "find out what metrics we can get about how
many downloads we get. i don't want anything but numbers to make myself feel good." An explicit
constraint, not just phrasing — this is about reading whatever numbers each distribution channel
already publishes on its own, never about adding tracking, telemetry, or analytics to a project
that doesn't already have it. No phone-home code, nothing that reports on real users.

**What Orcshot's #186 already confirmed real, carried over here rather than re-derived:**
GitHub Releases exposes a genuine per-asset download counter today — `gh release view <tag>
--json assets` returns a real `downloadCount` field per asset. Trivial to check for any project
with a real release.

**What Orcshot's #186 left unchecked, still genuinely open:** whether Launchpad exposes any public
download/install statistics for PPA packages at all — a known, long-standing gap/frustration in
the Launchpad community (unlike Debian's own opt-in popularity-contest mechanism), never confirmed
one way or the other. Also unchecked: whether a PPA `apt install` is even the kind of thing
Launchpad *could* count, since PPA downloads happen from Launchpad's own mirror infrastructure,
not a single trackable endpoint the way a GitHub Release asset is.

**Real widening beyond what #186 itself covers**, per direflail's own explicit framing today
(apt/Snap/Flatpak, not just apt/GitHub): Snap Store publishes real, documented install/metrics
data (`snapcraft metrics <snap-name>` and the Snap Store's own developer dashboard) — not yet
confirmed live for any real project, just known to exist as a real mechanism worth checking.
Flathub also publishes real public per-app download statistics (flathub.org/stats and a
documented API) — also not yet confirmed live, same status.

**Why this belongs in Orclab, not Orcshot:** the actual mechanism per channel (GitHub's API,
`snapcraft metrics`, Flathub's stats API, whatever Launchpad turns out to offer or not) is
identical for any project publishing through that channel — this is exactly the kind of "core"
guidance direflail's own taxonomy describes, not something specific to Orcshot's own packaging.

**Scope boundary:** nothing built, nothing even fully researched yet — Launchpad's real
availability is still unconfirmed, and Snap/Flatpak's mechanisms are named but not yet verified
live against a real project. Not assigned to a specific Orclab command yet either (could end up
inside `/orc-version`'s own territory, given its adjacency to release/versioning, or its own
command, or something else entirely) — that's an open design question for whenever this gets
picked up, not decided here.

**Next step, when picked up:** finish the real research first (confirm Launchpad's actual
capability one way or the other, verify `snapcraft metrics` and Flathub's stats API live against
a real published project) before any `superpowers:brainstorming` pass on what Orclab actually
builds from it.

**Launchpad's capability confirmed live, 2026-09-08 — it does count PPA downloads.** The entry
above framed this as a known Launchpad gap that might not exist at all. That framing was wrong,
and it is the reason this was left unresearched for two days. Launchpad's public API exposes a
real per-binary-publication download counter, anonymously, no auth and no credentials file:

```bash
curl -sS "https://api.launchpad.net/1.0/~<owner>/+archive/ubuntu/<ppa>?ws.op=getPublishedBinaries"
# then, per entry in that result:
curl -sS "<entry.self_link>?ws.op=getDownloadCount"
```

Run against the real `ppa:artificialorctelligence/orcshot`: 82 binary publications, **90 downloads
in total**, all of it on `0.1.1-2` and `0.1.1-3`; `0.2.0` and `0.3.0` were at zero. A
`getDailyDownloadTotals` operation exists on the same object and returned `{}` for a zero-count
publication — real, but not yet seen returning data.

**Two caveats that shape what the number means, both found in that same run**, and both worth
carrying into whatever gets built rather than presenting a bare total as if it were users:
- The count is **per binary publication** — one record per (package, version, series,
  architecture). That is not double counting: a 24.04 user really does fetch the `noble`
  publication and a 26.04 user the `resolute` one, so summing across series is correct. It does
  mean there is no single "downloads for this PPA" number to read; you have to list every
  publication and ask each one, ~75 HTTP round trips for a PPA this small.
- Every architecture within a series read **identically** — `0.1.1-3` is exactly 4 on `amd64`,
  and also 4 on `s390x`, `riscv64`, `i386`, `armhf`, `ppc64el`, `arm64`. Orcshot has no plausible
  s390x users, and a real user population does not distribute itself uniformly across seven
  architectures. That is something walking the archive index, not people. So the honest reading
  of "90" is closer to *a handful of automated passes over two versions* than to 90 anyone. The
  counter is real; what it counts is fetches of the `.deb`. This caveat is printed as part of the
  tool's own output rather than left in documentation, because a bare total invites exactly the
  misreading this bullet had to correct once already.

**Still genuinely unverified:** `snapcraft metrics` and Flathub's stats API. Not for lack of
trying — Orcshot has never been onboarded to either (its own `channels.yaml` records both as
action-less leaves, confirmed live 2026-09-07: `snap info orcshot` finds no such snap, and both
the Flathub API and `flathub/org.orcshot.Orcshot` 404). There is no real published project to
check them against yet, so these stay unverified until a real Snap Store or Flathub publish
exists — see Orcshot's own BACKLOG #198/#197.

**Design settled, same day, and built:** this became `--metrics` on `/orc-publish` rather than a
component of its own. The reasoning is in the "Why this belongs in Orclab" paragraph above, taken
one step further — the config that declares *where a project publishes* is the same config that
says where to go count, so the metrics read is a second command key (`metrics:`) on the same
`channels.yaml` leaf that already carries `action:`. No new tree, no new selection syntax, no new
config file. See **#18**, whose proposed `status:` key is the identical shape against the same
leaves; that entry stays open, but its mechanism is now a two-line change rather than a design.

## #8: Two stale version literals left in VERIFICATION.md, found during v5's own final review (RESOLVED 2026-09-06)

Found during the currency-discipline/verify-before-asserting (v5) final review's fix round
(2026-09-06). That review caught and fixed Scenario 9's version anchor (it hardcoded `0.4.0`/
`v0.4.0`, stale the moment the branch bumped Orclab past that version) — but two adjacent, real
instances of the same staleness pattern were spotted by the re-review as explicitly out of that
fix's scope, and parked here instead of looping further on an already-clean fix round.

**Instance 1 — Scenario 10's own hardcoded example:** `VERIFICATION.md`'s Scenario 10 still reads
"the current version (`0.4.0`, or whatever it's been bumped to)" — the hedge ("or whatever it's
been bumped to") makes the scenario still technically correct, but the literal `0.4.0` example is
now stale now that Orclab is at `0.5.0`. Same class of defect Scenario 9 just got fixed for, one
scenario left half-addressed.

**Instance 2 — Scenario 9's own revert command:** step 4's revert instruction hardcodes
`git tag -d v1.0.0 && git reset --hard HEAD~1`. This is only correct because Orclab's current
major version is `0` — any `increment major` from a `0.x.y` version lands on `1.0.0`, which is
what makes the literal tag name right today. The moment Orclab's own real version reaches `1.0.0`
and gets bumped again, this same probe (`increment major` from, say, `1.4.0`) would produce
`2.0.0`, and the hardcoded `v1.0.0` in the revert command would be wrong — deleting a tag that
was never created, and quietly reverting the wrong thing (or nothing at all) instead.

**Why this matters, concretely, not hypothetically:** `VERIFICATION.md` is the actual dogfood
script someone runs by hand — a stale literal here isn't cosmetic, it produces a confusing failure
or a silent no-op exactly when the script is supposed to be proving the real tool works.

**Scope boundary:** both instances are wording/literal fixes only — no change to `/orc-version`
itself, no design question open here. This is purely "make the verification script's own examples
stop hardcoding a version number that keeps changing."

**Next step, when picked up:** reword Scenario 10's example the same way Scenario 9's was just
fixed (reference "whatever `plugin.json` currently reports," not a literal number), and make
Scenario 9's revert instruction compute the expected new-major tag from the real current version
rather than assuming `v1.0.0` specifically — or, more simply, tell the reader to check
`git tag --list 'v*' --sort=-v:refname | head -1` right before deciding what to delete, rather
than hardcoding any literal tag name at all.

**Resolved for real, not just tracked:** both instances fixed exactly as described above. Scenario
10 now reads "the current version (whatever `plugin.json` currently reports)" with no literal
number. Scenario 9's revert step now finds the actual tag it just created via
`git tag --list 'v*' --sort=-v:refname | head -1` instead of assuming `v1.0.0`.

## #9: v5's plan never tagged its own release — caught only by tagging v0.6.0 and noticing v0.5.0 missing (RESOLVED 2026-09-06)

Found 2026-09-06 while tagging v0.6.0: `git tag --list 'v*'` showed `v0.3.0`, `v0.4.0`, `v0.6.0` —
no `v0.5.0`, despite the currency-discipline/verify-before-asserting release having been built,
merged, and pushed under that version number. Not a deleted or lost tag — `git log --oneline --all
| grep 0.5.0` confirmed the version-bump commit (`1eb34c7`) is real and on `main`; it was simply
never tagged. Checked against v3's and v4's own plans: both explicitly included a "create the git
tag" step in their versioning task. v5's plan, drafted the same way, dropped that step — a real
gap in the plan itself, not an execution slip.

**Fixed for real, not just tracked:** retroactively tagged `v0.5.0` at `1eb34c7` (2026-09-06,
local-only, matching the existing convention that tags stay local until an explicit release
action). All four version tags (`v0.3.0`–`v0.6.0`) now present and correct.

**Why this matters beyond the one missing tag:** every future `/orc-*`-command or version-bump
plan risks the same silent gap unless the versioning task template itself is checked against a
real prior example (v3/v4) before being reused, not just written from memory of "what a version
bump task looks like."

**Next step, when picked up:** none needed for this instance — closing it here as resolved. Worth
remembering during future plan-writing (`superpowers:writing-plans`) for any Orclab version-bump
task: copy the git-tag step from an existing plan (e.g. v4's) rather than re-deriving the task
from scratch.

## #10: Solidify /orc-publish's testing strategy beyond what the spec settles for v7 (RESOLVED 2026-09-07)

Raised by direflail (2026-09-06) during the `/orc-publish` design's testing section: the spec
settles for real unit tests on the tree-resolver script (path resolution, subtree-select+exclude,
shared-cascade merging, unset-channel skip) plus `VERIFICATION.md` scenarios run against a
synthetic throwaway tree with no-op leaf actions — deliberately never testing against a real
destination from Orclab's own repo. direflail wants this strategy solidified further, but was
explicit it doesn't need to happen before `/orc-publish` ships.

**What's already decided, not open for re-litigation here:** the two-layer split itself (real
automated tests for the resolver logic; hand-run dogfood scenarios for command behavior) and the
synthetic-tree-only rule for Orclab's own verification (real-destination testing is the separate
Orcshot dogfooding task's job, not this one).

**What's actually open:** unspecified — direflail flagged a general instinct that this needs more
rigor without naming the specific gap yet. Likely candidates worth raising when this is picked up:
whether the resolver's unit tests need to cover deeper trees than the two-to-three-level examples
seen during design (Orcshot's own real component/channel/distro trees, once dogfooded, would be a
real stress test), and whether the synthetic throwaway tree used in `VERIFICATION.md` should be
checked into the repo as a fixture (so its shape doesn't drift from what the scenarios assume) or
constructed inline by each scenario.

**Next step, when picked up:** ask direflail what specifically felt underspecified, rather than
guessing — this entry exists to hold the "come back to this" intent, not to pre-decide what's
missing.

**Resolved 2026-09-07.** Asked, as this entry's own next step required, rather than guessing.
direflail scoped it to the second of the two candidates above — the synthetic-tree fixture
question — and the first was already closed by events: the resolver's unit tests now assert on
`desktop.python.linux.ppa.noble`, five segments, which is exactly Orcshot's real tree depth.

**The fixture question resolves as "no change," and the reason is the interesting part: the
premise didn't hold.** The concern was three inline copies of a synthetic tree drifting apart.
Looking at them, they are not copies — they are deliberately different trees testing different
properties: Scenario 23/24's `desktop.python.linux.{snap,flatpak}` (resolution, the dry-run gate,
execution), Scenario 42's `test.{hangs,snap}` (timeout reporting and an action-less leaf), and
Scenario 43's `test.compound` (the process-group kill). There is no shared tree to extract.
Scenario 24 already reuses 23's by reference rather than copying it. A single fixture would mean
one tree serving all three, coupling unrelated scenarios so a change made for one silently alters
the others — and these are hand-run by a person reading the document, where the YAML sitting
beside its own expectation is the point rather than an accident.

**The audit did find a real gap in the same strategy, and it is the opposite shape from the one
this entry guessed at.** The gap is not tree management; it is that unit tests and hand-run
scenarios cover different failure classes, and one class had nothing. #15's fix passed every unit
test both before and after a real defect in it — the captured output was placed mid-sentence,
stranding the stdin hint under the log's last line — because the tests assert substrings and
substrings survive reordering. Only reading the real rendered output caught it. That is precisely
what a `VERIFICATION.md` scenario is for, and no scenario covered it. Added as **Scenario 44**,
which asks the reader to judge the summary as an operator would rather than search it for words.

**So the strategy's two layers hold, with the split sharpened:** unit tests for what is true,
hand-run scenarios for what is *readable* — and a behaviour whose failure mode is presentation
rather than logic needs the second, because the first will pass either way.

## #11: `/orc-publish`'s `execute_plan` has no subprocess timeout — a real hang risk, not yet fixed (RESOLVED 2026-09-07)

Found during the final whole-branch review of `/orc-publish` (v7, 2026-09-06). `execute_plan` in
`skills/orc-publish/scripts/orc_publish/cli.py` runs each leaf's `action` via `subprocess.run`
with no `timeout` argument. A leaf action that blocks on stdin hangs the entire `/orc-publish` run
indefinitely, with no way to know which leaf is stuck — `capture_output=True` means the process's
own prompt never even reaches the terminal, so it just looks like the command has frozen. This
isn't hypothetical: Orcshot's own real PPA publish step already uses `debsign`, which prompts
interactively for a GPG passphrase, and `debsign` is exactly the kind of action a real
`channels.yaml` leaf would wrap once Orcshot's own follow-on dogfooding task (populating real
`.orclab/publish/` content, per the design spec's explicit scope note) gets underway.

**Why this is deferred, not fixed now:** picking a correct timeout value is itself a real design
question, not something to guess at speculatively. Different real actions have legitimately
different normal durations — a `dput` upload and a local build script don't share a reasonable
timeout — so a single hardcoded number would either falsely abort a slow-but-healthy upload or
fail to catch a hang quickly enough. This needs its own real decision (a per-leaf configurable
timeout? a global default with an override? something else?), not a number picked to make this
finding go away.

**Scope boundary:** this is about the generic mechanism — `execute_plan` itself needing a timeout
strategy — not about routing around `debsign`'s own interactive-prompt behavior specifically (e.g.
via `--no-tty` or a pre-supplied passphrase). Those are separate, narrower questions that belong to
whoever actually wires up `debsign` as a real leaf action, not to this generic mechanism fix.

**Explicit flag for whoever picks up Orcshot's own follow-on dogfooding task:** know about this
risk before running `/orc-publish` against a real `debsign`-based action — you will hit it live,
with the run just appearing to hang, otherwise.

**Next step, when picked up:** design a timeout strategy for `execute_plan` (default value,
whether it's per-leaf configurable via the channel tree, what happens to the summary line for a
leaf that times out — presumably a new `"timed out"` status distinct from `"failed"`) before
implementing it.

**Fixed for real (2026-09-07, Orclab v11).** All three decisions this entry asked for before
implementation got real answers, in
`docs/superpowers/specs/2026-09-07-orclab-v11-publish-pipeline-gaps-design.md`:

- **Per-leaf, with a default.** `timeout` is a leaf key; `execute_plan` uses a leaf's own value
  when set, and `--timeout <seconds>` moves the default for a whole run without overriding a leaf
  that deliberately set a tighter one.
- **600 seconds.** Deliberately a "something is wrong" ceiling rather than a performance budget.
  This entry's own objection — that `dput` and a local build script don't share a reasonable
  timeout — is answered by the per-leaf override, not by the default.
- **A distinct `timed out` status**, as this entry anticipated, whose detail names the real limit
  *and* says the action may be waiting on stdin. That last clause exists because
  `capture_output=True` is precisely why a `debsign` prompt is invisible, which is the confusion
  this entry recorded ("it just looks like the command has frozen").

The scope boundary held: nothing here routes around `debsign`'s own interactive behaviour.

**The finding that mattered more than the timeout itself, recorded because the method is worth as
much as the fact.** The plan prescribed `subprocess.run(..., shell=True, timeout=N)`, and that is
not sufficient — mid-branch review caught it, and the human ruled the finding over the plan.
`subprocess.run`'s own timeout kills only the `/bin/sh -c` process it started. A compound action —
which is what a real publish leaf is, `dpkg-buildpackage && debsign && dput` — does its real work
in a *grandchild* of that shell, and killing the shell orphans it. The operator is told `timed
out` while `dput` goes on uploading, and a retry then double-uploads to a public archive. So
`execute_plan` uses `subprocess.Popen(..., start_new_session=True)` with `communicate(timeout=)`
and kills the whole process group, not just the shell.

**Two consequences of that deviation, both found in the final fix round rather than assumed.**
First, the group kill has to fire on *any* exit from `communicate`, not only `TimeoutExpired`: the
same `start_new_session` that makes the group killable also means a terminal Ctrl-C no longer
reaches the action, so a timeout-only handler recreated the identical orphan on interrupt.
Verified both ways under a real SIGINT — in the same process group the grandchild died with the
interrupt; in a new session with a timeout-only handler it survived. Second, with no controlling
terminal `/dev/tty` cannot be opened at all, so a gpg/pinentry passphrase prompt — the very case
this entry was written about — now fails in about a second with a real error rather than hanging
to the limit. That is an improvement, but it is a *behaviour change* this entry's own scope
boundary did not anticipate, so it is named here instead of left to be rediscovered.

## #12: `/orc-publish` models channel fan-out, but a real release is mostly an ordered pipeline — the framework can't yet drive Orcshot's own release (RESOLVED 2026-09-07)

Found 2026-09-06/07, dogfooding `/orc-publish` against Orcshot's real release for the first time.
direflail named the pattern directly, and it's the right diagnosis: "i feel like you're finding out
what to do one piece at a time and then finding out later and we're patching up the process to fix
it. do you understand the whole process we're trying to do, and then are we applying that to the
framework?"

**What actually happened:** Orcshot's `.orclab/publish/channels.yaml` was written against
`RELEASING.md` step 6 in isolation, before anyone had read the document end to end. Every problem
that followed was a consequence of that, not bad luck — a `../*.changes` glob that would have tried
to `dput` 33 accumulated past builds (see the fix in Orcshot's own history), a near-miss uploading
a version already live on Launchpad, a near-miss releasing on top of uncommitted in-progress work,
and repeated confusion about step ordering. Each was patched individually as it surfaced.

**The real structural finding, once the whole 11-step process was actually read:**

| Orcshot's real release process | What `/orc-publish` models |
|---|---|
| 11 ordered steps with real gates (tests before build, lint before upload, CI green before the GitHub Release) | Independent leaves, no ordering, and by explicit design *continues past a failure* |
| Real preconditions ("is this version already on Launchpad?", "is the tree clean?") | None — no notion of checking destination or local state before acting |
| Steps that are not shell commands at all: a Launchpad web-UI "Copy packages" click, install-testing on three real machines/VMs, clicking a menu item to verify the update checker | `action:` is a shell string; these steps are invisible to the model entirely |
| Most steps (1-5, 8-11) are release-wide, not per-channel | Only models the per-channel fan-out |

**The tell, concretely:** Orcshot's own `ppa.noble` leaf had to smuggle `dpkg-buildpackage -S` — a
*build* — into what is nominally a *publish* action, just to work at all. A leaf action that has to
build the thing it publishes is a sign the "publish an already-built artifact" abstraction doesn't
fit the real work.

**In fairness to the v7 spec, this is not a bug in it:** `/orc-publish` was deliberately scoped to
"push a project's built artifacts to their real distribution destinations," with artifact
generation explicitly out of scope. It is internally consistent and it does the fan-out part
genuinely well (the channel/distro split, the dotted-path selection, the dry-run gate all held up
under real use). The gap is that *"push built artifacts" turned out to be a far thinner slice of
"release this project" than assumed when it was scoped* — roughly one step out of eleven, and even
that one doesn't cleanly fit. Orcshot's real process is mostly pipeline; v7 built the fan-out.

**The open design question, deliberately not answered here:** does Orclab need a pipeline concept —
ordered steps, gates/preconditions, and a way to represent a step a *human* performs (a web-UI
click, a manual install-test) rather than a shell command — with `/orc-publish` becoming one stage
within it rather than the whole thing? Adjacent existing pieces that must be considered rather than
duplicated: `release-checklist` (v1) already maintains a numbered, dependency-ordered
`RELEASING.md`, which is *exactly* the artifact this would be automating against — so this may be
much more about giving that skill real teeth than about inventing a new structure. `/orc-version`
also already owns part of the spine (version bump, changelog, tag, GitHub Release) and BACKLOG #6
already tracks its per-language manifest gap, which Orcshot hit live (it can't bump
`pyproject.toml`/`debian/changelog`).

**Why this is not a patch:** the previous items found during this dogfooding pass (#11, and the
Orcshot-side config fixes) were real but local. This one changes what the framework is for. It
needs the same `superpowers:brainstorming` → spec → plan treatment `/orc-publish` itself got, not
another inline fix.

**Next step, when picked up:** a fresh brainstorming pass (Architectural), starting from a real,
complete read of Orcshot's `RELEASING.md` as the worked example — the whole document first, before
any design is proposed. Read `release-checklist`'s SKILL.md and `/orc-version`'s command file in
full at the same time, since the answer may be "make these two work together properly" rather than
"add a new component."

**Already closed by v8 (recorded 2026-09-07).** This entry's open design question — "does Orclab
need a pipeline concept — ordered steps, gates/preconditions, and a way to represent a step a
*human* performs — with `/orc-publish` becoming one stage within it" — was answered yes and built
as `/orc-release`. Ordered steps that halt on failure, `**Preconditions:**`, `**Performed by
hand.**`, `**Run:** /some-command` delegation, and a cross-session state cursor all shipped in
v0.8.0. This entry's own "next step" (a fresh brainstorming pass from a complete read of Orcshot's
`RELEASING.md`) is what produced that design.

It is recorded here rather than left ambiguous because v11's brainstorming pass initially treated
this entry as open and nearly re-designed something that already exists. What v11 *did* find was
narrower and genuinely uncovered by v8 — one-time onboarding, honest reporting of a not-yet-usable
channel, and #11's timeout — all three closed in v11.

## #13: v0.7.0 was never tagged either — the same gap as #9, and #9's own mitigation didn't hold (RESOLVED 2026-09-07)

Found 2026-09-07 while direflail challenged whether `/orc-version` was actually a good idea, which
prompted checking how version bumps have really been done rather than assuming. `git tag --list`
showed `v0.3.0` through `v0.6.0` — no `v0.7.0`, despite v7 having shipped, been reviewed, and been
pushed.

**This is the second occurrence of the exact pattern #9 recorded**, and it is worth being blunt
that #9's stated mitigation failed. #9's "next step" read: "Worth remembering during future
plan-writing for any Orclab version-bump task: copy the git-tag step from an existing plan (e.g.
v4's) rather than re-deriving the task from scratch." v7's plan was written after that entry
existed, by the same author, and still omitted the tag step. A note reminding a human (or Claude)
to remember something is not a mechanism.

**The wider finding this surfaced, which matters more than the missing tag:** `/orc-version` has
essentially never been used, including in its own home project. Its Apply flow commits with the
exact message `Bump version to X.Y.Z` and nothing else, and tags automatically as step 4. But the
real bump commits read `orc-publish: SKILL.md, bump to 0.7.0, CHANGELOG, README, VERIFICATION
scenarios` (`0470c26`), `Add Desktop-compatible skill wrappers..., bump to 0.6.0` (`cfbdaee`), and
`Add /orc-git command, bump version to 0.4.0` (`427c62b`) — implementation-plan tasks that edited
the manifests by hand alongside everything else. `1eb34c7`'s message matches `/orc-version`'s
format, but #9 already established that one was manual too (its plan omitted tagging, which
`/orc-version` would have done automatically).

So a component was designed, specced, reviewed and shipped in v3, and then every subsequent release
bypassed it. Both missing tags are the direct, mechanical cost of that.

**Fixed for real:** `v0.7.0` tagged at `ecad9d3` (2026-09-07, local-only per convention) — the
commit where v7's fix rounds completed and the work was declared done. Commits after that point
(`0217e59` onward, including `0ac9541`'s real change to `/orc-publish`'s dry-run output) are
unreleased work accumulating toward the next version, not part of 0.7.0.

**Why no further mitigation is being written here:** the real fix is already in flight. v8's design
(`docs/superpowers/specs/2026-09-07-orclab-v8-orc-release-design.md`) makes `/orc-version` the one
place that owns version-setting, with `/orc-release` delegating to it — so tagging stops being
something a plan author has to remember and becomes something the mechanism does. This entry exists
as the evidence for that decision, not as a request for another reminder-style note. If v8 ships
and a third version still goes untagged, that is a real signal the approach is wrong.

## #14: `claude plugin validate --strict` fails on Orclab's own CLAUDE.md — settle before writing a RELEASING.md (RESOLVED 2026-09-07)

Found 2026-09-07 while confirming that a `metadata:` marker in SKILL.md frontmatter is accepted
(it is — see `CLAUDE.md`). `claude plugin validate` emits exactly one warning against Orclab:

```
❯ root: CLAUDE.md at the plugin root is not loaded as project context. To ship context with your
  plugin, use a skill (skills/<name>/SKILL.md) instead.
```

Plain `validate` passes with the warning. `--strict` promotes warnings to errors and **fails,
exit 1, on that warning alone** — confirmed live.

**The warning is accurate, and the current layout is still correct.** Consumers who install
Orclab genuinely never see `CLAUDE.md`; it is not injected into their sessions. That is exactly
what `CLAUDE.md` says about itself ("not something Orclab ships to consuming projects"), and it
still does its real job — inside the orclab repo it is that project's own `CLAUDE.md` and loads
normally. This is a false positive against intent, not a defect to fix.

**Two ways it bites later, which is why it's tracked rather than ignored:**
- `plugin validate` appears nowhere in this repo today, and Orclab has no `RELEASING.md` of its
  own — despite shipping `/orc-release`, which drives other projects' release processes. The
  moment someone writes one and adds the obvious `claude plugin validate --strict` gate, Orclab
  fails its own release gate on a file that is deliberately, correctly there. A landmine planted
  ahead of the process that will step on it.
- The warning recommends the wrong remedy for this case. "Use a skill instead" would move
  Orclab's internal development guidance into a shipped skill, pushing it into every consuming
  project's context — precisely the boundary `CLAUDE.md` draws against. A future session with
  less context will read a helpful-sounding suggestion and do the wrong thing.

**Decision needed when picked up:** whether Orclab's eventual `RELEASING.md` runs `plugin
validate` without `--strict`, waives this one warning explicitly, or skips validate altogether.
Not urgent — nothing runs it today — but it has to be settled *before* the release process is
written, not after it fails.

**Correction, layered on 2026-09-07 (v11's final fix round): the bare command does not emit that
warning at all, and the reason makes this entry more urgent, not less.** This entry says "`claude
plugin validate` emits exactly one warning against Orclab." In this repo's dual-manifest layout
that is not what the bare command does. Reproduced independently, twice:

```
❯ claude plugin validate .
Validating marketplace manifest: .../.claude-plugin/marketplace.json
✔ Validation passed

❯ claude plugin validate .claude-plugin/plugin.json
Validating plugin manifest: .../.claude-plugin/plugin.json
Validating plugin: .../CLAUDE.md
⚠ Found 1 warning: ❯ root: CLAUDE.md at the plugin root is not loaded as project context...
✔ Validation passed with warnings
```

Given a directory holding both manifests, it validates the **marketplace** one and stops. The
warning this entry describes appears only when `plugin.json` is named explicitly.

**Why this belongs to `CLAUDE.md`'s negative-control argument, not just to accuracy.** A
`RELEASING.md` gate running the bare `claude plugin validate .` would check the marketplace
manifest's structure and *nothing whatsoever* about the plugin, its skills, or the frontmatter
that carries this project's load-bearing behaviour — and it would print `✔ Validation passed`
either way. That is precisely what `CLAUDE.md`'s own negative-control section rules out: a check
that passes for both the right and the wrong input is not a check. The landmine the two bullets
above describe is real, but the worse outcome is the opposite one — a green gate that never looked
at the plugin, and a release process that believes it verified something.

So the decision this entry defers now has a third input: whichever way `--strict` goes, the gate
has to name `.claude-plugin/plugin.json` explicitly, or it validates the wrong file.

**Resolved 2026-09-07 — the decision is made, and it is written where it will actually be found.**
direflail's call: the gate is `claude plugin validate .claude-plugin/plugin.json`, naming the file
explicitly, **without** `--strict`.

- **Name the file** because the bare form validates the marketplace manifest and stops. A gate
  that prints `✔ Validation passed` without ever looking at the plugin is green for the right
  input and the wrong one alike — this entry's own correction above, in live form.
- **No `--strict`** because it promotes to an error the single warning Orclab gets, on a layout
  that is deliberate and correct. Failing a release on `CLAUDE.md` doing exactly its job is the
  landmine the second bullet above predicted, and the warning's suggested remedy would push
  Orclab's internal guidance into every consuming project's context.

**The resolution is recorded in `CLAUDE.md`'s "`claude plugin validate` does not check skill
frontmatter" section, not only here.** A resolved BACKLOG entry is not where someone writing a
release process looks; that section is about this exact tool and is on the minimum search surface.
Leaving the decision only in the backlog would have reproduced the failure this entry is about —
a correct answer nobody finds at the moment it matters.

**What is not resolved, deliberately:** Orclab still has no `RELEASING.md`. This entry asked only
for the decision to be settled *before* one is written, and it now is. Writing that document is
separate work, and whoever does it inherits a decision instead of a landmine.


## #15: a timed-out `/orc-publish` leaf says "no output captured" when output was in fact captured (RESOLVED 2026-09-07)

Found 2026-09-07 during v11's final fix round, checking a code comment rather than trusting it. A
timed-out leaf reports:

```
<path>: timed out (timed out after 600s - no output captured, the action may be waiting on stdin)
```

`subprocess.TimeoutExpired` does carry whatever was captured before the timeout. Verified
directly: after `echo hello; sleep 5` timed out at 1s, `TimeoutExpired.stdout` was `b'hello\n'` —
present, and **undecoded bytes** despite `text=True`, because the exception is built from the raw
buffers before the text wrapper ever sees them.

**Why this matters more than a stray adjective.** The flagship action is
`dpkg-buildpackage && debsign && dput` — a wall of build output, and *then* a hang. That is
precisely the output-then-hang shape where the operator is told nothing was captured while the
build log that would say how far it got is discarded. The other half of the detail line ("may be
waiting on stdin") stays true and stays useful; it is only the "no output captured" clause that is
sometimes a lie.

**Deliberately deferred, not overlooked.** Surfacing partial output was explicitly ruled out of
v11's fix round by direflail. The in-code comment at the `except subprocess.TimeoutExpired` handler
in `skills/orc-publish/scripts/orc_publish/cli.py` was corrected to say what is actually true — the
output exists and is not surfaced yet — rather than the false claim that capture never completed.
`docs/superpowers/specs/2026-09-07-orclab-v11-publish-pipeline-gaps-design.md` carries the same
correction against its own hardcoded example.

**Next step, when picked up:** surface `e.stdout`/`e.stderr` in the timeout detail the same way the
`failed` branch surfaces `e.stderr`, and reword the clause so it is honest when there is genuinely
nothing (a leaf that hung before printing anything is a real and different signal). It needs a
`.decode()` — the bytes are not decoded for you on this path, and the `failed` branch's strings
are, so the two branches cannot share the same handling as written. One test per shape: output
then hang, and hang with no output.

**Resolved 2026-09-07.** The timeout detail now surfaces what was captured, decoded defensively
for both `bytes` and `str` and tolerating a `None` stream. Both shapes were checked against a real
run, not just against assertions:

```
a: timed out (timed out after 1s - the action may be waiting on stdin. Output captured before it hung:
build-line-1
build-line-2
build-line-3)

b: timed out (timed out after 1s - no output captured, the action may be waiting on stdin)
```

"no output captured" survives, correctly, as the honest report for the second shape — a leaf that
hung before printing anything is a real and different signal, exactly as this entry anticipated.

**One thing the entry did not anticipate, found only by looking at real output.** The first
implementation put the captured output in the middle of the sentence, leaving
`build-line-3, the action may be waiting on stdin` — the stdin hint stranded under the last line
of the log, reading as part of it, and with a real `dpkg-buildpackage` capture it would sit
hundreds of lines below the fold. The clause order is now inverted: the actionable sentence first,
the dump last. **Every test passed both before and after that fix**, because they assert
substrings and substrings survive reordering, so a test now asserts the ordering itself
(`detail.index("waiting on stdin") < detail.index("hello")`). Rendering is not covered by
asserting that the right words are present somewhere.


## #16: the process-group-kill tests can't tell "killed" from "waited out" — narrowed by two live controls, not closed (RESOLVED 2026-09-07)

Found 2026-09-07 reviewing the two tests written for BACKLOG #11's fix,
`test_execute_plan_kills_the_whole_process_group_on_timeout` and
`test_execute_plan_kills_the_whole_process_group_on_interrupt` in
`skills/orc-publish/scripts/tests/test_cli.py`, together with `grandchild_action` and
`assert_process_gone` that they share. The real gap: nothing bounds the wall clock of either test,
and the `except BaseException:` handler in `execute_plan` (`skills/orc-publish/scripts/orc_publish/cli.py`)
calls `proc.wait()` after the kill attempt — a call that blocks until the child tree actually
exits, kill or no kill. So a test that never kills anything can still pass, by blocking on
`proc.wait()` until the grandchild's own sleep runs out on its own, and reporting the same "timed
out" / `KeyboardInterrupt`-raised outcome the real fix produces.

**Both controls were actually run (2026-09-07), and the real results are the finding — not the
theory of what they'd probably show:**

- **Control A** — swap `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` for `proc.kill()`, i.e.
  the real pre-fix `subprocess.run` behavior, the actual regression these tests exist to catch:
  **both tests fail**, with `Failed: grandchild <pid> survived - its process group was not
  killed`, in `2 failed in 11.16s`.
- **Control B** — delete the kill line entirely, leaving only `proc.wait()`: **both tests pass**,
  but in `60.11s` instead of the usual ~1.2s — the outer shell waits on its own grandchild, and
  `proc.wait()` waits on the outer shell, so by the time `assert_process_gone` runs, the grandchild
  is already gone on its own.

**So the tests are not vacuous.** They genuinely catch the regression they were written for —
control A proves that plainly, and this matters more than the gap below, because a reader who only
sees the gap might reasonably conclude the tests should be deleted. They shouldn't. The real gap is
narrower: a 50x slowdown is the *only* signal separating a real kill (control A's failure mode
inverted, i.e. the fix working, ~1.2s) from a wait-it-out pass (control B, ~60s) — and nothing in
either test asserts on wall-clock time, so nothing currently fails if a future change quietly
regresses the kill back to a no-op that happens to still finish inside CI's patience.

**Scope boundary:** this is not a claim that the fix in BACKLOG #11 is broken — control A shows the
current code does perform the group kill. This is only about the tests' own ability to *notice* if
that ever stops being true.

**Two candidate fixes, not chosen between:** assert a wall-clock ceiling on `execute_plan`'s return
(it should come back at about the leaf's `timeout`, not at the grandchild's full 30s sleep — a
loose bound like "under 5s" would separate the two cases cleanly without being a flaky tight
bound); or lengthen the grandchild's sleep relative to `assert_process_gone`'s poll window (already
5s) enough that a wait-it-out pass becomes wall-clock-impractical for a test suite to tolerate,
forcing a real kill to be the only way to pass at all.

**How this was found is as much the point as what was found.** An implementer ran control B, saw
both tests pass, and reported that the tests do not detect a broken kill. That inference was wrong
on its own terms: deleting the kill line entirely is not the regression these tests exist to catch
— the real pre-fix behavior was a *child-only* kill (`subprocess.run`'s own timeout, which reaches
only the `/bin/sh -c` process), not *no* kill at all. Testing "no kill" tests a scenario no real
regression produces; only control A — swapping in the actual pre-fix kill call — tests the real
regression. Two earlier agents had separately claimed these tests were verified against negative
controls, and a third claimed the opposite (that they were vacuous); only actually running the
correct control resolved the disagreement. This repo's own `CLAUDE.md` already makes the point that
a check which passes for both the right and the wrong input is not a check (the `claude plugin
validate` frontmatter finding) — this is the same lesson from the other direction: **a negative
control that removes the wrong thing proves nothing either**, and can produce a confident, wrong
conclusion in exactly the shape this one did.

**Resolved 2026-09-07 — candidate one, the wall-clock ceiling.** direflail chose it over the
sleep-tuning alternative, on the reasoning that it asserts the actual property (the kill happened,
promptly) rather than tuning two sleeps into a gap a slow CI box could still close — the same
timing-race shape this file's own tests had just been cleaned of.

`KILL_CEILING_SECONDS = 10` and `assert_returned_promptly()` in
`skills/orc-publish/scripts/tests/test_cli.py`; both process-group tests now time `execute_plan`
and assert it returned inside that ceiling. Ten sits far above the real ~1.2s and far below the
30s a wait-it-out takes, so it is not a race on a loaded machine.

**Both controls were re-run against the new assertion, since a fix to a test is worthless unless
the test now fails where it used to pass:**

- **Control B** (delete the kill entirely, leave `proc.wait()`) — the one that previously passed in
  60s and proved nothing: now **fails**, `the interrupted execute_plan took 30.0s, over the 10s
  ceiling - the process group was probably not killed, and this only finished because the
  grandchild's own sleep ran out`. `2 failed in 60.14s`.
- **Control A** (child-only `proc.kill()`, the real pre-fix regression): still **fails**, `2 failed
  in 11.16s` — the existing survival assertion catches it first, as before.

So the tests now fail under both a real regression and the degenerate no-kill case, and the
message names the actual cause rather than leaving a reader to infer it from a slow run.

**Worth keeping from the same day, one entry over:** #15's fix passed every test both before and
after a real defect in it, because the tests asserted substrings and the defect was ordering. The
lesson generalises to this entry — asserting that the right things are *true* is not the same as
asserting they are true *for the right reason*, and a control that used to pass is the cheapest
way to tell the difference.

## #17: what belongs in a `/orc-package` component, and what belongs elsewhere — scope undecided

Raised by direflail 2026-09-07, immediately after automating Orcshot's Launchpad
noble→resolute copy: "this whole process is going to have to be done for any new project... i'm
thinking this should be part of the first-time setup stuff for ppa." Then, asked whether it should
be PPA-only: "it definitely needs to be broader (what if i make a mobile app? cross platform
windows/linux app?). but i'm not sure what belongs HERE versus elsewhere yet."

**Confirmed by search, not assumed:** nothing in Orclab covers standing up a distribution channel
today. Searched the minimum surface (`skills/*/SKILL.md`, `CLAUDE.md`, `BACKLOG.md`,
`hooks/scripts/`, `skills/*/scripts/`). The three hits for PPA/dput/Launchpad are all incidental —
`release-checklist` uses "already published to the PPA" as an example of a good precondition and
explicitly warns against assuming `dpkg-buildpackage`-style steps belong everywhere; `orc-publish`
mentions `debsign` in a timeout note; `orc-release` uses `dput` as its example of a risky command.
None of them tells you how to make a channel exist.

**"Packaging" is currently four different things wearing one word.** Naming them is most of the
scoping problem:

| | Thing | What it was for the PPA |
|---|---|---|
| 1 | Produce the artifact | `debian/` layout, `dpkg-buildpackage` |
| 2 | Stand up the destination | create the PPA on Launchpad |
| 3 | Credentials for it | GPG key registered to Launchpad, `~/.dput.cf`, the OAuth authorization |
| 4 | Wire it into Orclab | `channels.yaml`, `distro.yaml`, `RELEASING.md` steps |

The 2026-09-07 work did 2, 3 and 4. It never touched 1 — Orcshot's `debian/` already existed.

**The observation a design should start from: 2, 3 and 4 repeat across every channel; 1 does not.**
Every distribution channel has the same shape — a one-time registration, a credential mechanism, a
per-release publish action, and often an asynchronous review (see **#18**). The mechanisms differ
wildly between a PPA, the Snap Store, Flathub, npm, PyPI, the App Store, Play Console and winget;
the shape does not. That is why the `**One-time setup:**` marker shipped in v0.11.0 fitted the PPA
copy on its first real use without having been written for it. Producing the artifact is the
opposite: `debian/control`, an Android keystore and an `.msix` manifest share essentially nothing.

**A supporting argument already in the code:** `/orc-publish`'s tree is already channel-shaped —
`desktop.python.linux.ppa.noble` is component/platform/os/channel/series. A `/orc-package` scoped
to channels would *populate* that tree; `/orc-publish` executes it. A mobile app becomes
`mobile.<lang>.android.play`; a cross-platform desktop app grows `desktop.<lang>.windows.winget`
beside its Linux channels. Same tree, same fan-out, same `--for` queries, no new structure.

**A candidate cleave, explicitly not a decision:** `/orc-package` owns channels (2, 3, 4), not
build systems. Producing the artifact is closer to `/orc-code`'s territory, which already owns
per-language and per-stack defaults — **#4** is the open entry for exactly that. Running the
release stays `/orc-release`'s.

**What is genuinely unknown, and must not be assumed away:** that shape is proven for exactly one
channel. Snap and Flathub are researched but unbuilt (Orcshot **#198**). The App Store and Play
Console add binary signing and multi-day human review, and whether "one-time setup plus a
per-release action" survives contact with App Store Connect has not been checked at all.

**Next step, when picked up:** a `superpowers:brainstorming` pass (Architectural — new component,
new command surface, and a taxonomy question underneath it), using the 2026-09-07 PPA walkthrough
as the one worked example that actually exists.

**An open disagreement to settle in that pass, not before it.** The Orcshot 0.3.0 handover proposes
that Orclab own "the series-copy mechanism generalised from the existing script" — i.e. a Launchpad
API client living in the framework. The position taken while building that script was the opposite:
Orclab ships the mechanism, projects ship their actions, which is the same boundary that keeps
`dput` in Orcshot's own `channels.yaml` rather than in `/orc-publish`. Generalizing a
forge-specific client into Orclab would make the framework know about one particular hosting
provider. Both positions are defensible; the handover's is the stronger one if several projects
ever publish to Launchpad, and the weaker one if they do not. What is *not* in dispute is which
properties any implementation must keep, all proven live: a `--check` mode that answers "has the
one-time authorization happened" without triggering it, a `--dry-run` that authenticates
anonymously so preconditions are verifiable on an unconfigured machine, refusal to act when the
source is not `Published` or has no built binaries, and a credentials file at `chmod 0600` that is
never printed. Two questions were deliberately left unanswered
when this was raised: whether the component dispatches per channel (`/orc-package ppa`) or is
PPA-only, and whether it writes the config and `RELEASING.md` steps itself or only instructs.
Answer **#18** first or alongside — a channel that isn't finished when the command exits changes
what "set up a channel" even means.

## #18: a publish can be accepted without being done — nothing models the wait, or how to check

Raised by direflail 2026-09-07, while scoping **#17**: "we're probably waiting for multi-day
(probably) human review and be able to check status on where those are at (either via api or by
giving links to the pages we can check)."

**The gap:** `/orc-publish` reports a leaf as `success` when its action exits 0. For several real
channels, exit 0 means *accepted*, not *published* — and the difference is hours to days.

| Channel | What exit 0 actually means | How the real state is checkable |
|---|---|---|
| PPA upload (`dput`) | queued; Launchpad's build farm has not built it | Launchpad API — `getPublishedSources` / `getPublishedBinaries`, confirmed live 2026-09-07 |
| PPA series copy | requested; files can take up to 20 minutes to appear | same API |
| Flathub first submission | a pull request opened, reviewed by people over days | GitHub PR status |
| Snap Store | uploaded; some confinements need Canonical review | `snapcraft status` / the developer dashboard |
| App Store / Play | submitted for multi-day human review | App Store Connect / Play Console APIs |

**This is already being worked around by hand, which is the tell that it belongs in the
framework.** Orcshot's own `ppa.resolute` leaf carries this as a prose `issues:` note: *"The copy
is asynchronous... A green exit means the copy was accepted, not that it has landed."* That is the
same pattern the `**One-time setup:**` marker came from — Orcshot's `RELEASING.md` had invented it
inline twice, inconsistently, before it became a real convention. A per-project prose note is how a
missing mechanism announces itself.

**Two distinct forms a status check takes**, and a design has to allow both rather than assuming
the first: a **programmatic** check (a command or API call that returns the real state — the
Launchpad one is proven, and `scripts/ppa-copy-series.py`'s own precondition check is already
exactly this), and a **link** to a page a human reads when no API exists or none is worth wiring.
Both are legitimate; only the first can gate a later step automatically.

**Why this is not just an `/orc-publish` concern:** it interacts with `/orc-release`, where a step
may not be completable in the session that started it — Orcshot's real release already has this
shape, since the resolute copy cannot run until the noble build has *succeeded*, not merely been
accepted. `/orc-release`'s state cursor already survives across sessions, so the pieces may
largely exist; what is missing is a way for a channel to declare "here is how you find out whether
this actually landed."

**Scope boundary:** this is about *observing* an asynchronous publish, not about polling or waiting
on one. Nothing here proposes that Orclab block, retry, or sleep — inventing a polling loop for a
multi-day human review would be worse than the prose note it replaces.

**Next step, when picked up:** decide whether this is a new leaf field in `channels.yaml` (a
`status:` command and/or URL alongside `action:`), a `release-checklist` marker for a step that
completes later, or both. Answer it alongside **#17**, whose "stand up a channel" question is
incomplete without it.

**Corroborated independently, and with a live incident, 2026-09-07.** The session driving
Orcshot's `0.3.0` release reached the same finding from the other direction — not "how do I check
status" but "this step cannot be tracked honestly." Orcshot's step 6 was three operations with a
remote wait in the middle: `dpkg-buildpackage`/`debsign`/`dput` (local, seconds), **Launchpad's
build farm building the upload (remote, ~28 minutes on that release)**, then the copy to
`resolute`, valid only after the build succeeded. `/orc-release` has one completion state per step,
so `run.py complete 6` was called while the copy had not happened and *could not* for another half
hour. **The release was recorded as further along than it was**, and only a manual note to the user
kept the record straight.

That adds a third option, cheaper than either above and worth weighing first because it needs no
code at all: **a documented convention that "wait for X, then do Y" must be split into two numbered
steps.** Orcshot's own document already renumbered to do exactly that (upload is step 6, copy is
step 7), which is why the same release would now be trackable. A `release-checklist` rule would
generalize it.

Also worth recording from that release: `dput` printing `Successfully uploaded packages.` says
nothing about whether the package *built*. The build farm's result is a separate gate from the
upload's success, which is this entry's whole point stated in the most concrete possible form.

**The mechanism half of this got built for a different reason, 2026-09-08 (see #7).** `/orc-publish`
now takes `--metrics`, which runs a leaf's `metrics:` command instead of its `action:` — the same
selection, timeout, process-group kill and capture path, parameterized by which key holds the
command. That is exactly the shape this entry's "next step" proposes for `status:`: adding it is
now a two-line change (`tree.LEAF_KEYS`, and `cli.NOT_SET`, which is where the per-key wording for
an unset command lives), not a design.

What that does **not** settle is everything this entry is actually about: whether a `status:`
command is even the right answer versus a link a human reads, versus the no-code option of
splitting "wait for X, then do Y" into two numbered release steps. The cheap mechanism arriving
first is a reason to be more careful here, not less — it makes the wrong answer as easy to build
as the right one. Decide it alongside **#17** as this entry already says.

## #19: `/orc-release`'s `**Run:**` marker silently drops its arguments (RESOLVED 2026-09-08)

Found 2026-09-07 while considering whether Orcshot's `RELEASING.md` step 11 should delegate the
GitHub Release to a command. The delegation marker is parsed by
`skills/orc-release/scripts/orc_release/steps.py`:

```python
_DELEGATES = re.compile(r"\*\*Run:\*\*\s*(/[\w-]+)", re.IGNORECASE)
```

It captures the command name and nothing else. Checked directly rather than inferred from reading
the pattern:

```
'**Run:** /orc-publish desktop.python.linux.ppa.resolute' -> delegates_to = '/orc-publish'
'**Run:** /orc-version release'                           -> delegates_to = '/orc-version'
'**Run:** /orc-version release v0.3.0'                    -> delegates_to = '/orc-version'
```

**Two different severities hide in that, and the second is the real finding.** For `/orc-publish`
the lost argument is a *target*: "publish something" instead of "publish `resolute`". Bad, but the
command is still the right command. For `/orc-version` the lost word changes **what the command
does** — `/orc-version` sets a version number, `/orc-version release` pushes a tag and creates a
public GitHub Release. A structured field saying `/orc-version` for a step that cuts a release is
not merely incomplete, it names a different action.

**This already affects a real document.** Orcshot's step 7, written 2026-09-07, is
`**Run:** /orc-publish desktop.python.linux.ppa.resolute` — the channel is being dropped today.

**Why it probably hasn't bitten yet, and why that isn't reassuring.** `/orc-release`'s SKILL.md
has Claude read each step's full body, so the prose carries the argument even when the parsed
field doesn't. The behaviour is likely correct in practice. But a structured field that is
confidently wrong is worse than one that is absent — it is exactly the "check that passes for both
the right and the wrong input" shape `CLAUDE.md` argues against, and the same class of defect as
the heading/body divergence in #12 and the sub-numbered steps now covered in `release-checklist`.

**Fix shape:** widen the capture to take the rest of the line (`(/[\w-]+(?:\s+\S+)*)` or simply
capture to end-of-line and strip), expose it as the delegation's full invocation, and add tests
for a bare command, a command with one argument, and a command with several. Check whether
anything consumes `delegates_to` expecting a bare name before widening it.

**Blocks nothing outright, but see #20** — that entry's proposed step 11 delegation
(`**Run:** /orc-git release`) is the case where the dropped word is most misleading, so fixing
this first makes that change clean.

**Resolved 2026-09-08.** The capture is widened to the rest of the line and stripped:

```python
_DELEGATES = re.compile(r"\*\*Run:\*\*\s*(/[\w-]+.*)", re.IGNORECASE)
```

`.` does not match a newline without `re.DOTALL`, so this stays single-line by construction — which
matters, because `**Preconditions:**` deliberately spans lines and this marker must not start
behaving like it. Verified directly rather than assumed, against the three cases this entry named
plus two it did not:

```
bare         -> '/orc-publish'
one arg      -> '/orc-publish desktop.python.linux.ppa.resolute'
two args     -> '/orc-version release v0.3.0'
trailing ws  -> '/orc-git release'
prose on following lines -> not captured; the next step's own field stays None
```

**The pre-existing bare-command test passed unchanged**, which is the real regression check: it
proves the widening did not over-capture. Confirmed before changing the field's meaning that nothing
branches on `delegates_to` — it is declared on the `Step` dataclass, set once in the parser, and
otherwise only asserted in tests.

`skills/orc-release/SKILL.md` needed no change: its instruction is "Marked **Run: /some-command** →
invoke that command," which was already correct and is now actually served by the parsed field.
Suites green at 102 / 62 / 48.

## #20: where release-adjacent responsibilities live — `/orc-version release` is misplaced

Raised by direflail 2026-09-07, after asking what the difference between `/orc-version release`
and `/orc-release` actually is — a question the current naming does not answer. His own framing:
"that frees up `/orc-version` to JUST be in charge of the version, and `/orc-release` can focus on
the release, delegating to `/orc-version` as needed."

**The diagnosis, sharpened from naming to risk class.** Everything `/orc-version` does is local and
reversible: edit a manifest, write a changelog entry, commit, tag locally (tags stay local by this
project's own convention — see #13). `release` is the single subcommand that pushes to a remote
*and* creates a public artifact. A dangerous verb sheltering under a benign command name is the
part that matters, more than the fact that `/orc-version release` and `/orc-release` read alike.

**One correction that constrains any redesign: it must not move *into* `/orc-release`.** That
skill's first rule is that `RELEASING.md` is the single definition of the steps and it "never
invents a release process." A `/orc-release` that knew how to create GitHub Releases would be
doing something the project's own document never asked for — and would be wrong for every project
that releases to PyPI, an internal deploy, or a Debian archive and nowhere else.

**Proposed destination, agreed in principle but not built: `/orc-git release <tag>`.** `/orc-git`
already owns forge operations (`gh pr checkout`, connecting a repo); `gh release create` is the
same family. The earlier objection — that `/orc-git` has no confirmation gates — was against
bundling a release into `cp` as a chained side effect. As its own explicitly typed subcommand,
invoking it *is* the deliberate act, exactly as `push` already argues for itself.

**How `/orc-release` then reaches it, and why no new mechanism is needed.** direflail's instinct
was that the repository host is "another link in that tree" — the project decides it uses GitHub,
and that delegates to `/orc-git`. That mechanism already exists and it is `RELEASING.md` itself:

```markdown
## 11. Publish the GitHub Release
**Run:** /orc-git release
```

`/orc-release` stays forge-agnostic by construction, because it only follows the document. If a
project moves to GitLab or Codeberg, that line changes and nothing in `/orc-release` does — the
same way step 7 delegates a Launchpad copy to `/orc-publish` without `/orc-release` knowing what
Launchpad is. No `forge.yaml`, no new abstraction. (See **#19** — the delegation marker currently
drops the `release` argument, which is why that should be fixed first.)

**The insight generalizes past the Release step, which nobody had noticed.** Auditing Orcshot's
own process for forge coupling: step 9 (`git push`) is host-agnostic and works anywhere; step 10
is **three `gh run list` calls** and is just as GitHub-specific as step 11. Any real "delegate the
forge" design has to cover CI confirmation too, not only the Release.

**A hard constraint on any answer, confirmed live 2026-09-07:** Orclab itself has **no
`RELEASING.md`, 9 tags, and 0 GitHub Releases**. It is precisely the project that would be
stranded if this capability were reachable only through `/orc-release`, which refuses to run
without that document. Whatever is decided must leave a directly typable path for a project that
tags versions but has no written process.

**A latent problem to settle at the same time, not urgent:** `/orc-git` conflates two things.
`commit`, `push`, `branch` are universal git and work against any host; `repo`, `pr` — and
`release`, if it lands there — are `gh`, GitHub-only. The name says git; half the command is
GitHub. Harmless while GitHub is the only forge in use, and the thing that has to be untangled the
day it isn't.

**An adjacent feature direflail raised, worth building with this rather than after it:** when
`/orc-release` reaches its "pick a version" step, it should *propose* one rather than only asking —
reading the commits since the last tag and saying why ("no breaking changes, four features, so a
minor bump"). Today `/orc-version` takes a number you supply or an explicit `increment
major|minor|point`. The suggestion is a version decision and belongs in `/orc-version`; the
plumbing to reach it from a release already exists (`/orc-release` delegates version-setting with
`--no-commit`).

**Next step, when picked up:** a `superpowers:brainstorming` pass — this moves responsibilities
across three shipped commands and touches naming, so it is not an inline edit. Fix **#19** first
or alongside. Nothing here is urgent: `/orc-version release` works today, and the only real cost
of the status quo is that nobody can tell the two commands apart from their names.

## #21: nothing inspects an artifact before it is irreversibly published (RESOLVED 2026-09-08)

Raised 2026-09-07 from a handover written by the session that drove Orcshot's `0.3.0` release end
to end. Everything below was measured from real tarballs during that release, not reasoned about
afterwards.

**Two publicly-uploaded PPA source packages carried the repository's own `.git` directory.** The
third was caught only because someone looked:

| Tarball | `.git` entries | agent-state entries | Size |
|---|---|---|---|
| `0.1.1-3` (**uploaded, public**) | 1,415 | 0 | 10.8 MB |
| `0.2.0-1` (**uploaded, public**) | 1,882 | 3 | 14.8 MB |
| `0.3.0-1` (caught before upload) | 3,061 | 1,330 | 22.6 MB |

By `0.3.0` the payload included whole stale git worktrees carrying a built `.deb` and a `.whl` —
prebuilt binaries inside a *source* package, which is what lintian's `source-contains-prebuilt-*`
family exists to catch. After the fix the same tarball was **1.02 MB**.

**Why this is not recoverable after the fact:** a PPA will not accept a re-upload of an existing
version. There is no undo and no fixing it in place — a mistake costs a version number, and the bad
artifact stays public.

**The sharpest argument for inspecting the artifact rather than trusting the build config**, and
the reason a generic check would have caught this on the *first* release: the packaging config was
actively wrong about its own behaviour. `debian/source/options` listed `tar-ignore = "<pattern>"`
entries, and its own comment asserted the default VCS/backup exclusions were active. They never
were. Per `dpkg-source(1)`, quoted from the real man page rather than from memory:

> `-I` by itself adds default `--exclude` options that will filter out control files and
> directories of the most common revision control systems, backup and swap files and Libtool build
> output directories.

Those defaults apply **only** when `-I` appears with no pattern. So the config claimed an exclusion
set it had never enabled, and nothing downstream ever compared the claim to the output.
(Debian-specific coda, since it fails open and would otherwise be rediscovered: in
`debian/source/options` the defaults must be re-enabled with the long form and no value —
`tar-ignore` alone on a line. A bare `-I` there is rejected with
`dpkg-source: warning: short option not allowed in debian/source/options`, the warning scrolls
past, and the defaults stay off.)

**What Orclab should own — a preflight, as an `/orc-publish` responsibility.** It is the component
that knows both the artifact and the destination, and it already has the dry-run gate where such a
report belongs. A cheap check would list the archive and fail on `.git/`, on agent/tool state
directories, and on `*.deb`/`*.whl`/`*.so`/`*.exe`, and warn when the size is wildly out of line
with the previous release. Every one of those three uploads trips at least one of those rules.

**The second lesson is structural rather than a missing check, and it generalizes further:**

> Lint the thing you are shipping, not its sibling.

Orcshot's step 5 ran `lintian` on the binary `.deb` and passed clean every time, while the *source*
package — the artifact actually being uploaded in the next step — was the broken one. **A checklist
that lints one artifact and ships a different one has a blind spot by construction**, regardless of
how good either check is. That belongs in `release-checklist` as a rule about what a verification
step must be pointed at, not only in `/orc-publish`.

**Scope boundary:** this is about *inspecting* what is about to be published, not about producing
it correctly. Orcshot's own `debian/source/options` fix is already committed on its side and is not
Orclab's business; the generic capability is.

**Next step, when picked up:** decide the shape — always-on inspection in `/orc-publish` before any
irreversible action, an opt-in `preflight:` declaration on a channel leaf (patterns are
format-specific: a `.tar.xz`, a `.snap` and a `.flatpak` are not inspected the same way), or a
`release-checklist` convention that a build step must be followed by a check *of that artifact*.
Probably the last one plus one of the first two. Related: **#18** (a publish accepted but not
landed) and **#20** (where release-adjacent responsibilities live).

**Resolved 2026-09-08 (Orclab v12).** A leaf may declare `prepare:`, `artifact:` and `preflight:`;
`/orc-publish` runs prepare, inspects the artifact against the named rules, and reports `refused`
without running the action when a rule trips. Non-zero exit, siblings continue, offending entries
capped at five with the real total. `--allow-preflight-failure` downgrades a refusal for one run and
still prints every finding.

**The framing this entry started with was wrong, and the correction is the design.** The first pass
claimed a leaf whose action builds what it publishes could not be inspected at all. It can: the
tarball exists after the build, `debsign` is local and reversible, and only `dput` is irreversible.
The real constraint was narrower — one opaque shell string admits no gate between two of its
commands — which `prepare:` fixes without anyone restructuring a release. That also answers #12's
standing complaint that a publish action had to smuggle a build into itself.

The size-anomaly rule was cut deliberately: it needs persistent state Orclab does not keep and is
the most false-positive-prone of the four, and all three real incidents trip a content rule.
`filename_template` and `render_filename` were removed as part of this — shipped dead in v7 and
superseded by `artifact:`.

The structural half lives in `release-checklist` as **"lint the thing you are shipping, not its
sibling,"** which generalises past this design: a checklist that verifies one artifact and ships a
different one has a blind spot however good either check is.

## #22: concurrent Orclab agents can collide on numbered resources — a lock, an allocator, and ordered queues

Raised by direflail 2026-09-08, immediately after asking which of the four then-unimplemented specs
could run concurrently. The map came back mostly clean on files — v12 and v13 both rewrite
`execute_plan` and must be sequential; #19, v14 and v15 touch disjoint files — but every one of them
appends a numbered scenario to `VERIFICATION.md`, and two concurrent streams would both read "ends
at 44" and both write "Scenario 45."

**The problem is two different things wearing one name, and one half is already solved.**

*Filesystem concurrency* — two agents contending for `.git/index.lock`, one's `git add` landing in
the middle of another's commit — is real and was hit for real on 2026-09-07, when an Orclab-centred
session and an Orcshot-centred session were both operating in Orcshot's single working tree. **Git
worktrees already fix that**, and `subagent-driven-development` already creates one per plan, which
is exactly why all of that day's Orclab work had zero contention while the Orcshot work had all of
it. Nothing to build.

*Semantic collision* is what survives worktrees **if each agent reads its own checked-out copy of the
file**. Two agents in separate checkouts derive the same "next number," and both are correct given
what they can see; no lock helps, because they are not contending for a resource at all.

**That framing is avoidable, and direflail's design avoids it — recorded because an earlier draft of
this entry assumed otherwise.** If every agent instead reaches out to **one canonical `BACKLOG.md`**,
rather than to its own worktree's copy, there are no divergent copies and the collision is an
ordinary shared-resource contention that a lock handles exactly as locks are meant to. The choice of
*which file agents write* is therefore the load-bearing decision here, not the locking primitive —
get that wrong and no amount of locking helps; get it right and the locking is textbook.

**Why detection alone is not enough, which is a correction to this entry's own first framing.** The
initial argument here was that a duplicate costs five minutes to renumber, so a one-line
`grep … | sort | uniq -d` beats building anything. That is true for `VERIFICATION.md` and **false
for `BACKLOG.md`**, and framing the problem around the weaker case got the conclusion wrong:

- Backlog entry numbers are **permanent and never reused** — a stated, load-bearing rule. If two
  agents both take `#22` and both commit, each referencing `#22` in its commit message and inside
  the entry text, it cannot be fixed by renumbering, because renumbering is precisely what the rule
  forbids. The damage is durable.
- The collision is **sometimes silent**. If both agents append immediately before the same trailing
  section, git conflicts and someone notices. If they insert in different regions, git merges
  cleanly and two `#22`s exist with no complaint at all.
- direflail does not read these files unsolicited (they are working memory for agents, not a status
  report), so a silent duplicate sits undisturbed until something trips over it.

**This bug class hit three times on 2026-09-07 in purely single-agent work**, which is the argument
that it is real rather than theoretical: duplicate `BACKLOG` numbers taken by two branches, a
`RELEASING.md` step renumber that made two steps vanish from the parsed release, and this. Only the
middle one has a mechanical check today (`/orc-release`'s step parser warns on non-contiguous
numbering); the other two have none.

### The design direflail proposed

**A file lock**, described accurately: a process arrives, finds no lock, takes it, does whatever is
needed to be assigned a number and write the file, then releases. A second process finds the lock
held, waits a few seconds, retries, and errors out after a reasonable period. Works for any number
of processes. Stale locks need a check — and, direflail's own operational note, a lock found when
none is expected is worth investigating rather than clearing reflexively.

**One technical correction, because it is the standard way this pattern is broken:** "check whether
it is locked, then set the lock" is a time-of-check-to-time-of-use race — two processes can both
observe it free and both proceed. The check and the set must be a single atomic operation:
`os.open(path, os.O_CREAT | os.O_EXCL)`, or `mkdir`, both atomic on POSIX. Everything else in the
description is right as stated.

**One lock, not one per resource, and lane-agnostic** — confirmed with direflail 2026-09-08. Every
process queues the same way regardless of which lane it belongs to. The reason is stronger than
simplicity: per-resource locks would reintroduce deadlock, since a work item can legitimately need
two numbers at once (v12's own plan adds both a `BACKLOG.md` entry and a `VERIFICATION.md`
scenario), and two agents acquiring them in opposite orders is textbook AB-BA. With a single lock
that is structurally impossible. The parallelism forgone is worthless anyway at millisecond hold
times.

**The critical section is take-a-number, not do-the-work** — otherwise lanes fully serialize and the
concurrency is pointless. But it should extend through the **commit**, not stop at the file write:
if the shared file lives in a worktree, two agents committing it concurrently are back to
`.git/index.lock` contention, which is the thing worktrees were supposed to have solved. Read,
append, commit, release — still sub-second.

**A consequence to know rather than fix:** writing to a shared ledger means the entry is not part of
the agent's own branch commit. Branches then never touch `BACKLOG.md` and cannot conflict on merge,
which is a real benefit — but an entry survives even if the work that motivated it is abandoned.
Acceptable for a findings ledger; surprising if unexpected.

**On wait times:** a queue of lanes contending for a sub-second append is not time-critical. Even
unlucky timing across several lanes costs seconds, which is the correct trade for eliminating a
class of collision that cannot be cleaned up afterwards.

**The real cost is not the lock.** A lock protects a resource only if *every* writer takes it. Today
"add a backlog entry" is `backlog-discipline` prose instructing Claude to scan the file for the
highest `N` and edit it directly. An agent doing that without going through an allocator defeats the
lock completely and silently — it will not even know it should have. So the actual work is
converting a prose-driven edit into a tool-mediated one: the skill must say "get your number from
the allocator" rather than "scan for the maximum." That is a larger change than the locking, and it
is the part that needs deciding. It is also the direction several 2026-09-07 findings already
pointed: mechanically checkable beats "be careful."

### Ordered queues — and yes, it becomes a scheduler

direflail's follow-on, and the case that makes this more than a lock: *"what if i want to run 12
then 13 but also simultaneously 19 and 14?"*

That is two lanes, each internally ordered, running in parallel:

```
lane A:  v12 → v13
lane B:  #19 → v14
```

**"Arguably yes" it is a scheduler — but a deliberately small one.** It is N sequential lanes running
concurrently, not a dependency graph. Nothing needs to express "v13 requires v12 *and* #19"; every
real ordering constraint found so far is linear within a lane. Keeping it to lanes avoids a DAG
resolver, cycle detection, and partial-failure semantics, none of which any real case here has
needed.

**Exclusion and ordering are different mechanisms and should not merge.** The lock gives mutual
exclusion on a shared resource; the lane gives ordering between work items. Conflating them is how a
lock grows into a general scheduler nobody asked for. A lane needs no lock to be ordered, and a lock
needs no lane to be correct.

### Alternatives worth weighing before building

- **Deferred numbering.** Agents write a placeholder (`## Scenario NEXT`) and the number is assigned
  at merge. Lock-free, no shared state, and it works well for `VERIFICATION.md`. **It does not work
  for `BACKLOG.md`**, where the entry number is referenced in the commit message and inside the entry
  text *while the work is happening* — a commit saying "BACKLOG #NEXT" is not usable. The two
  resources have genuinely different constraints and may deserve different answers, which is worth
  settling before assuming one mechanism covers both.
- **Pre-assigned ranges per lane** (lane A takes scenarios 45–47, lane B 48–50). No lock, no
  allocator, trivially correct. Goes stale the moment scope shifts, and does nothing for `BACKLOG.md`
  where numbering is global and permanent.
- **Just serialize.** Costs wall-clock time and nothing else. Genuinely the right answer if
  concurrent runs stay rare — the collision rate to date is zero, because concurrent streams have
  never actually been run.

### Scope boundaries

- **Not cross-machine.** PID-liveness staleness checks work on one host and do not survive
  containers or a shared network filesystem. Every real case here is one machine.
- **Not a daemon.** No long-running coordinator; a lock file and a lane definition are enough.
- **Not a DAG.** See above.
- **Not for `.git/index.lock`.** Git already handles that, and worktrees avoid it.

### Next step, when picked up

A `superpowers:brainstorming` pass. It needs to settle: whether one mechanism covers both
`BACKLOG.md` and `VERIFICATION.md` or they get different treatments; whether the allocator is a
bundled script or a hook; how `backlog-discipline` changes from "scan for the maximum" to "ask the
allocator," and what happens when an agent ignores it; and what a lane definition actually looks
like given that `subagent-driven-development` already owns per-plan execution and may be the natural
home rather than a new component. Add to that list, from the 2026-09-08 refinement: **where the
canonical file actually lives** — the main worktree's checkout, or a path outside every worktree —
since that decision is what makes the lock meaningful or useless.

**Do not build ahead of a real concurrent run.** The honest state is that this is a well-understood
hazard with a zero incident rate under concurrency, because concurrency has not been used yet. The
right trigger is the first time two lanes are actually launched.

## #23: the action-shape warning misses a repeated publish verb

Found by a code review of v12's action-shape check (2026-09-08), verified live against the real
implementation.

`cli.action_shape_warning()` warns when a leaf's single `action:` both builds and irreversibly
publishes, because no gate can run between the two. It compares only the **leftmost** occurrence
of each verb - `action.find(publish)` against `action.find(build)` - rather than every pair. So an
action that publishes, builds, then publishes again:

```
dput ppa:x a.changes && dpkg-buildpackage -S && dput ppa:x b.changes
```

genuinely has the build-then-irreversible-publish shape the check exists to catch, and produces no
warning at all: the first `dput` precedes the build, so the ordering test fails and the second
`dput` is never considered.

**Scope boundary, and the reason this is small:** the check warns and never refuses. A miss costs
a warning, not a bad publish - the real gate is `preflight:`, which inspects the artifact itself
and is not a heuristic over a shell string. This is a gap in an advisory hint, not in the safety
mechanism.

**The fix, if it is ever worth taking:** compare every `build` occurrence against every `publish`
occurrence rather than only the first of each. Worth weighing against the opposite risk - the
check already has false positives by design (any substring match counts, so
`cargo build-tools-checked && dput ...` warns today), and widening the search widens those too.

**Provenance, added after the fact.** Two sessions independently executed the whole of the v12
artifact-preflight plan in parallel on separate branches, neither aware of the other (see #25).
This branch's own final review of the action-shape check noticed the same repeated-verb gap and
set it aside as minor without formally filing it; it was the parallel session's own, independent
review that actually filed this entry's finding. Worth recording for what it says about the
review process, not just about the code: the same diff got two genuinely separate passes, and
only one of them turned an observation into a tracked entry.

## #24: `--dry-run`'s exit code doesn't distinguish a resolvable plan from one already known broken

Raised by the final review of v12 artifact preflight (2026-09-08) and deliberately scoped out of
that work's own fix wave rather than smuggled into it.

`/orc-publish --dry-run` exits 0 whenever it manages to resolve a selection, even when the plan it
prints already names a problem the tool has diagnosed with certainty. Confirmed live: a leaf with
a typo'd rule name (`preflight: ["no-vcss"]`) prints
`preflight result: unknown preflight rule(s): no-vcss` and exits 0.

**The concrete consequence** is not a bad publish - at execution that leaf is `refused`, nothing
is published, and `main` exits non-zero. It is that `--dry-run` is the gate `orc-publish`'s own
`SKILL.md` Step 2 asks a human to read and approve, and anything scripting around that step - a CI
preflight, a `RELEASING.md` check - cannot tell "this plan is fine" from "this plan is already
broken and I am saying so in the output you are about to approve."

**Why this is a design decision rather than a one-line fix.** The typo is not the only dry-run
condition that reports a problem and exits 0: `preflight is declared but no artifact: is set`,
`artifact not found:`, `unsupported archive format`, and `artifact path expansion timed out` all
behave the same way. Making only the statically-detectable ones non-zero draws an arbitrary line
through the middle of one category; making all of them non-zero changes what `--dry-run`'s exit
code means to every existing caller. The real question is what the dry-run contract is - a report
that succeeded in being produced, or a verdict on the plan - and it should be answered in one
deliberate pass.

**Scope boundary:** this is about the exit code only. The messages are already printed and already
correct.

**Provenance, added after the fact.** This finding came from the parallel session's own,
independent review of the same v12 artifact-preflight plan (see #25) - a second, genuinely
separate pass over the same diff this branch had already reviewed and shipped. It is deferred
here, not decided, deliberately: whether exit 0 is defensible (the dry run's job is to resolve
and print, and it did) or a real gap (a wrapper doing `orc-publish --dry-run && orc-publish`
proceeds anyway) is a design question for whoever picks this up, not something to settle in the
act of filing it.

## #25: BACKLOG #22's collision happened - two agents built the same feature, neither could see the other

Not a prediction any more. On 2026-09-08 two concurrent sessions each implemented the whole of the
v12 artifact-preflight plan, in full, independently. One worked on `main` directly; the other in a
worktree branched from `origin/main` at `092a327`. Both produced a complete feature with a passing
suite (120 tests and 119 tests), both wrote their own `VERIFICATION.md` Scenario 45, both resolved
BACKLOG #21, and both allocated new BACKLOG numbers from the same `#22` high-water mark. The
duplication surfaced only at `git merge`, as an add/add conflict on `tests/test_inspect.py`.

**What made it invisible for the entire run, and this is the part worth keeping.** #22 frames the
hazard as two agents *taking the same number*. That happened here, but it was the cheap part - a
renumber. The expensive part was that the two agents never contended for any shared resource at
all until the very end: the worktree session branched from `origin/main` and pushed nothing, and
the `main` session committed locally and pushed nothing, so for the whole of both runs there was
no observable state either could have polled to discover the other. A lock around number
allocation - #22's proposed remedy - would not have fired once. Every guard in #22's design
protects a *write*; nothing announces an *intent to start*.

**The concrete cost:** roughly a full implementation's worth of agent time and tokens, spent
twice, plus the review passes on both. Not recoverable, and not detectable until the end.

**One real consolation worth recording**, because it argues against treating duplication as pure
waste: the two implementations were not identical, and each caught something the other missed.
`main`'s routed `expand_path` through `_run` (closing a process-group hole the worktree's version
left open and had filed as a backlog entry); the worktree's fixed a scalar `preflight:` being read
one character per rule, and a non-string one raising `TypeError` out of the property ahead of
every caller's containment - both of which `main`'s had. The surviving branch was `main`'s, with
the worktree's two fixes ported onto it as `596d970`. That is a real argument for deliberate
N-version work on a genuinely risky component - but as a decision someone makes, not as an
accident nobody noticed.

**Scope boundary:** this entry records the incident and what it disproves about #22's framing. It
does not propose the mechanism - that belongs in #22, whose design needs an "announce intent to
start" step that its current one-lock-around-allocation shape does not have.

**Correction, 2026-09-08, same day - the paragraph above claiming #22's lock "would not have fired
once" is wrong, and the error is worth more than the claim was.** It asserted that the two sessions
never contended for a shared resource. They did, twice. **Both allocated `VERIFICATION.md` Scenario
45** - the surviving one is from the `main` session's `5684150`, and the worktree session's Task 7
independently resolved the same number from the same "scenarios run to 44" scan. **Both also took
BACKLOG `#23` and `#24`** from the same `#22` high-water mark, with different content. That is
precisely the collision #22 describes, on precisely the two resources it names. An allocator asked
for a scenario number twice returns 45 and 46; asked for a backlog number twice returns 23 and 24.
It would have fired four times and prevented all four collisions.

**How the wrong conclusion was reached, since the reasoning error is the reusable part:** the
duplicate *implementation* and the numbered-resource *collision* were treated as one event. They are
not. #22 has never claimed to prevent two agents building the same feature - its scope is numbered
resources, and on that scope it was exactly right. Judging it by whether it would have prevented the
duplicate build measured it against a promise it never made, then generalised that to "the design is
wrong."

**The second error compounds the first:** an unbuilt mechanism was declared disproven by a run that
did not have it. The sessions allocated numbers by scanning a file for the maximum, because that is
what `backlog-discipline` says to do and no allocator exists. Observing that no lock was taken in a
run containing no lock is not evidence about the lock. It is evidence about the absence.

**What survives from this incident as real input to #22's design:** the collision rate is no longer
zero, so #22's own "do not build ahead of a real concurrent run" trigger has genuinely fired. And
one detail worth carrying in - neither session pushed until the end, so the canonical-file question
#22 already flags (the main checkout, or a path outside every worktree) is load-bearing rather than
incidental. A lock on a file inside each worktree would have protected nothing here.

## #26: Claude's designs and explanations are built inside-out — the user has to ask for facts Claude already had

Raised by direflail 2026-09-09, at the end of the session that produced v16's spec and plan, and
raised as a working-relationship problem rather than a defect: *"your plans are good, if you're an
AI... i just want us to work better together."*

**The pattern, stated more precisely than "be more user-centric":** Claude reasons from the
mechanism outward and explains from the conclusion backwards. Both are natural from inside a context
where every premise is already loaded, and both are invisible from there — nothing feels missing,
because for Claude nothing is. The user is the only party who can see the gap, so the user ends up
doing the work of finding it.

**Five real instances from that one session**, recorded concretely because a vague pattern is
unfixable:

1. **A design built outward from a lock.** Claude proposed an `/orc-lane` command whose surface was
   organised around the lock, the allocator and the lane record — three pieces of machinery, two of
   which a person can never interact with. direflail: *"what you're designing doesn't make sense to
   a user. there's no command i can call to do something to the file lock."* The reframe to
   `/orc-todo`, organised around the backlog a person actually looks at, came entirely from them.
2. **Designing against a file never shown.** Claude spent several exchanges arguing that
   `VERIFICATION.md` belonged in the allocator's scope without once showing what it contains.
   direflail had to ask outright: *"tell me what VERIFICATION.md stores and give me an example of
   format."* The answer took one command and immediately made the scope question decidable.
3. **A premise skipped entirely.** Claude reported that an allocated entry "lands on main's branch,
   not the feature branch" as though that followed obviously. It only follows if you already know
   `subagent-driven-development` creates a worktree per plan, so a repo holds N copies of
   `BACKLOG.md`. direflail: *"i don't understand what the repo has to do with any of this."*
4. **An assumption never stated, then mistaken for a proposal.** Because Claude never said lanes do
   not create branches, direflail reasonably asked whether they did — *"are you proposing that each
   lane creates its own branch and the merge is where the trouble here is?"* The answer was no on
   both counts, and neither had ever been written down.
5. **A four-day-old line cited as settled authority.** Claude quoted `backlog-discipline`'s "Don't
   turn this into a general task list" as a constraint on the design. direflail: *"IS BACKLOG.md a
   task list? ... and who wrote backlog-discipline and why does it say this"*. Checking took one
   `git log`: they wrote it on 2026-09-04, the commit body is empty, and ten of twelve open entries
   are things that need doing. The line was deleted.

A sixth, different in kind but the same root: Claude reopened the already-settled decision that all
agents write one canonical `BACKLOG.md`, and direflail had to say *"i thought we had resolved
that."* Settled context decayed silently rather than being tracked.

**What should already have covered this, and why none of it fired.** `verify-before-asserting`
covers a claim that gets challenged — it fires after the user pushes back, which is exactly one step
too late here. `whole-process-first` covers reading a document before acting on it, not showing it
to the person you are designing with. `superpowers:brainstorming` requires asking questions one at a
time and proposing trade-offs, and Claude did both; it says nothing about surfacing the artifacts a
person needs in order to answer those questions. `CLAUDE.md`'s "name what should already have
covered it" is about mechanisms, not explanations. **There is a genuine gap, and it is not a matter
of widening an existing trigger.**

**Why this is harder than it looks, and the reason it is an entry rather than a fix.** The obvious
remedy — a rule saying "explain more" or "show your sources" — is the weakest possible form, and
`CLAUDE.md` already says why: prose fires only if the skill was invoked, the section was read, and
the reader classified themselves into its trigger. Worse, this failure is *self-concealing*. Every
other rule in this repo fires on a situation Claude can observe. Here the situation is "the user
lacks a fact I have," which Claude by construction cannot see — the fact is present, so nothing
registers as absent. A trigger phrased around noticing the gap will never fire, because noticing is
the part that fails.

That points at cheap structural habits rather than judgment: showing the artifact under discussion
before arguing about it, stating premises about the environment before conclusions that rest on
them, checking the provenance of any in-repo rule before citing it as a constraint, and keeping
settled decisions somewhere they cannot quietly decay. All four are mechanical and none require
Claude to detect its own blind spot first. Whether they belong in a skill, in `CLAUDE.md`, or in the
brainstorming flow is undecided.

**Scope boundary:** this is about how Claude designs and explains, not about output length. Four of
the five instances above were Claude being *too brief on premises while being long on conclusions* —
more words would not have fixed any of them, and the fix for #2 and #5 was one shell command each.

**One incidental confirmation, recorded because it settles a live question:** direflail opened this
request with *"add one task to the backlog."* `backlog-discipline`'s "not a general task list" line
is being removed by v16 partly on the argument that the file is substantially a task list. Its owner
calling an entry a task, unprompted, is the strongest evidence available that the removal is right.

**Correction, same day, from direflail — this entry flattened a distinction that matters.** The ask
was *"think more user-centric"*, and it was written up above as *be* more user-centric. direflail's
own words: *"the former means you still think and act as yourself, but you spare some cycles to
think things through as if you were a human, particularly when it comes to user-facing stuff."* Not
a request to become a different kind of reasoner - a request to spend cycles simulating the other
side of the table.

**The reasoning error that produced the flattening, which is the part worth keeping.** The paragraph
above argues the failure is self-concealing, and concludes the fix must therefore be mechanical
habit *instead of* judgment. That conflates two different capacities:

- **Noticing** that the user lacks a fact - genuinely unavailable, for the reason given: the fact is
  present, so nothing registers as absent.
- **Simulating** a reader who has not seen what this context has seen - a check that can be run on
  purpose, needing no prior noticing at all.

Only the first is blocked. The argument slid from "I cannot perceive the gap" to "so do not try to,"
and those do not connect. The four habits remain right, but they are the floor rather than the
answer: a deliberate pass over any user-facing design, read as someone who has not been in this
conversation, is the thing actually being asked for.

**And the cost argument was under-weighted.** direflail: *"that's going to help keep us from going
in two different directions and having to go back and refactor."* This is not only about clarity in
the moment. `/orc-lane` was designed, argued for, and had questions built on top of it before the
reframe to `/orc-todo` arrived - all of which was thrown away. That is the same economics as **#25**:
work done twice because two views of the problem never met early enough. A simulated pass during
design is paid in a paragraph; skipping it is paid in a rewrite.
