# Orclab v27: one vocabulary for the recipe tree — `recipe-discipline`, and the two words `/orc-package` has backwards

**Status:** design, 2026-09-26. Item 1 of BACKLOG #80, which direflail re-scoped the same day:
*"the two commands disagree on names, and they work on the same tree. we need to codify this in
orclab and make it easier and more useful to interact with."* Items 2 and 3 of that entry are
deliberately out of scope here — see §6.

## The problem

`/orc-code` and `/orc-package` walk contiguous halves of one tree and neither says so, because
the one word they share names a different level in each.

A project's `channels.yaml` path is five levels deep. Orcshot's real file holds two components:

```
desktop:                gnome-shell-extension:
  python:                 js:
    linux:                  linux:
      ppa: snap: flatpak:     ego:
```

`/orc-code`'s Defaults Table (`skills/orc-code/SKILL.md:380`) is keyed by type plus the platforms
ticked and answers with the stack — which is levels 3 and 2 of that path being computed. Step
0.2's third bullet, routing "a new part of an existing project" to a subdirectory, is level 1.
`/orc-package` and `/orc-publish` own levels 4 and 5. So `/orc-code` decides the front of every
address in the file and `/orc-package` then asks the user to type the whole thing in from memory.

**The collision.** `skills/orc-package/SKILL.md:52` says *"the tree is
component/platform/os/channel/series (`desktop.python.linux.ppa`)"*. Map those labels onto that
example and it is calling `python` the **platform** and `linux` the **os**.
`skills/orc-code/SKILL.md:45` asks *"Which platforms? Tick any of: Linux, Windows, Mac, Android,
iOS, web."* The shared word *platform* means level 2 in one command and level 3 in the other, so
a reader who carries the sentence from one to the other lands on the wrong level and correctly
concludes there is no correspondence. That is what happened in orckeys on 2026-09-25, and again
in this repository's own first pass at the report on 2026-09-26 — twice, independently, which is
the evidence that the naming misleads rather than merely under-documents.

**"os" is also wrong on its own terms**, not only inconsistent: `web` is a legal value at level 3
(`/orc-code` step 3 offers it), and web is not an operating system.

**The model has no mechanical existence.** `skills/orc-publish/scripts/orc_publish/tree.py`:
*"There is no fixed schema beyond that distinction - depth follows whatever a real project
actually needs."* A node is a leaf when its keys are a subset of `LEAF_KEYS`, a branch otherwise.
None of the five names appear anywhere in `/orc-publish`'s code — its one `"component"` is an
unrelated path-segment matcher in the preflight rules. So there is nothing to discover by reading
the code, which is why a careful pass concluded the concept was absent from `/orc-code` rather
than differently named.

## What should already have covered it

Per `CLAUDE.md`, "Before building anything, name what should already have covered it". Searched
2026-09-26: every shipped `SKILL.md`, `docs/commands/` (all eleven pages), `CLAUDE.md`,
`BACKLOG.md`, `hooks/scripts/` and `skills/*/scripts/`.

- **Nothing states the model except `orc-package/SKILL.md:51-52`.** `grep -rn
  "recipe\|component/platform" docs/commands/` returns nothing; `grep -c recipe
  skills/orc-code/SKILL.md` returns 0.
- **The three discipline skills are the closest existing mechanism** — `code-discipline`,
  `test-discipline`, `security-discipline`, each `user-invocable: false`, each read when its
  subject is in play. None covers project shape or delivery. This is a real gap, not a rule that
  failed to fire.
- **The one rule that did fire, and was not enough:** `/orc-package`'s own step 1 asks the user
  for the parent path *"and the user knows their project's shape better than you do."* True, and
  it is why the file is correct today. It is also why the model never needed writing down
  anywhere else — the human was the record.

## What is decided

### §1 — Scope: the names and their home, nothing else

v27 settles what the five levels are called and puts one authoritative statement where a session
will actually meet it. It does **not** make `/orc-code` write the path (#80 item 2) and does not
add any way to view or edit the tree (#80 item 3). Those inherit these names, which is why this
goes first.

### §2 — The five names

| Level | What it holds | Orcshot's values |
|---|---|---|
| 1 `component` | which piece of the project is being delivered | `desktop`, `gnome-shell-extension` |
| 2 `stack` | the language and toolkit it is built with | `python`, `js` |
| 3 `platform` | where it runs | `linux` (also `windows`, `mac`, `android`, `ios`, `web`) |
| 4 `channel` | where it is delivered, and what that place requires | `ppa`, `snap`, `flatpak`, `ego` |
| 5 `series` | the channel's own subdivision, where it has one | `noble`, `resolute` |

Levels 2 and 3 are the change: `/orc-package` currently calls them *platform* and *os*. Both new
names are already in use elsewhere and are what the data says — `docs/commands/orc-code.md:43`
already reads *"it proposes a **stack** — the language and toolkit"*, and step 3 already calls
Linux/Android/web *platforms*. This is adopting `/orc-code`'s existing words, not inventing any.

Two properties of the model that must survive being written down, because both are true of real
projects today and a tidier-looking rule would break them:

- **A component is not a folder.** Orcshot's `gnome-shell-extension` has no top-level directory;
  its source is at `src/orcshot/resources/gnome-shell-extensions/<uuid>` and
  `scripts/pack-extension.sh` builds it. A component is a thing built and delivered separately,
  wherever its source lives.
- **The depth is not fixed.** `tree.py` accepts whatever a project needs, and a shipped
  ingredient already relies on it: `shared-hosting`'s parent is `server.php.linux` with the leaf
  at `dreamhost` — four levels, no series. These five names are a convention for reading and
  writing a tree, not a schema that rejects one.

**Levels 2 and 3 are confirmed by every real path in the repository**, not only by orcshot. The
six shipped ingredients each carry an example parent path in their opening table:
`desktop.python.linux.ppa`, `desktop.python.linux.snap`, `desktop.python.linux.flatpak`,
`mobile.dart.ios.app-store`, `mobile.dart.android.play`, `server.php.linux` (leaf `dreamhost`).
Level 2 across all of them is `python`, `dart`, `php`, `js` — languages, every one. Level 3 is
`linux`, `ios`, `android`. There is no reading of that data on which level 2 is a platform.

**Level 1 is the honest weak spot, and v27 does not tidy it.** Its real values in the wild are a
mix of three different ideas: platform families (`desktop`, `mobile`), a tier (`server`), and one
genuine component name (`gnome-shell-extension`). "Component" describes the intent — which piece
of the project is being delivered — and describes orcshot's second value exactly, but a project
with one deliverable currently names level 1 after wherever it runs, which then repeats at level
3 (`mobile.dart.ios`). Renaming those values is out of scope per §5, and inventing a rule for
them without a project to test it against is the mistake #33 records. So v27 defines level 1 by
its intent, records that practice is looser, and leaves the convention to #80 item 2, which is
where something first has to *write* a path rather than read one.

### §3 — The home: a `recipe-discipline` background skill

`skills/recipe-discipline/SKILL.md`, `user-invocable: false`, the shape the three existing
discipline skills use. It carries §2's table, orcshot's two components as the worked example, and
the two properties above.

Three options were weighed and the other two rejected for recorded reasons:

- **Correct the two words in place and cross-reference from `/orc-code`.** Removes the
  disagreement, but leaves the model inside one command's question list — the thing #80 is about.
  It would close item 1 while the root persists.
- **A shared page under `docs/`.** Rejected on two grounds. Structural: `docs/` holds exactly
  `commands/`, `superpowers/` and `handoffs/`, and `hooks/scripts/tests/test_docs.py`'s
  `test_every_page_is_a_command_that_exists` means a page under `commands/` must be a real
  command — so this would be the only loose page of its kind. Substantive: a doc page is not
  loaded into a session, so it would not have reached the orckeys session that was planning a
  three-deliverable split. That is #75's complaint, and a page does not answer it.
- **A background skill.** A skill's description sits in every session, so the model is present at
  the moment a decision needs it. Items 2 and 3 extend it rather than needing a home of their own,
  which avoids a second copy to keep in sync.

**The cost, stated plainly:** this is a 37th shipped skill and its description loads into every
session. The mitigation is the trigger. Its description says *more than one deliverable* — a
second component, stack, platform or channel entering the picture — not "any project", so it does
not compete with the stack skills on an ordinary single-target build.

Per `CLAUDE.md`'s checklist item 6, the name has no `orc` prefix, which is correct: `/orc-help`
enumerates `skills/orc*/SKILL.md`, and this is background knowledge, not a command. For the same
reason `test_docs.py`'s `test_every_command_has_a_page` does not require a `docs/commands/` page
for it, matching the three existing discipline skills.

### §4 — What changes

1. **`skills/recipe-discipline/SKILL.md`** — new. §2's table, the worked example, the two
   properties, and one paragraph naming which command owns which levels.
2. **`skills/orc-package/SKILL.md:51-52`** — `component/platform/os/channel/series` becomes
   `component/stack/platform/channel/series`, and the sentence points at `recipe-discipline`
   instead of carrying the definition itself. The "ask the user, never guess" instruction stays
   exactly as it is; v27 changes what the levels are called, not who is asked.
3. **`skills/orc-code/SKILL.md`** — the Defaults Table's preamble gains a sentence saying it
   answers levels 2 and 3 of the project's recipe tree, pointing at `recipe-discipline`. No
   question changes, nothing new is recorded, and the table itself is untouched.
4. **`skills/orc-publish/SKILL.md`** — line 41 calls the arguments "selection tokens (dotted
   paths, ...)" and never names what a segment is; it gains the names and the same pointer.
5. **`docs/commands/orc-package.md` and `docs/commands/orc-publish.md`** — `CLAUDE.md` checklist
   item 7: what `/orc-package` *asks* is being reworded, so its page gets the level names in the
   user's words. `orc-code.md` already says "platforms" and "stack" correctly and needs only the
   sentence connecting them to the path.

### §5 — What deliberately does not change

**No value in any real file changes.** `desktop.python.linux.ppa.noble` stays exactly that. Only
the *labels* for the positions move. This matters concretely: `distro.yaml` cites leaves by dotted
string (`channel: desktop.python.linux.ppa.noble`), and `/orc-publish`'s selection tokens are the
same strings, so renaming a value would break references that nothing would catch. Every
`channels.yaml`, every `distro.yaml`, every ingredient's example path and every `RELEASING.md`
`**Run:** /orc-publish <path>` line is untouched by v27.

The six shipped ingredients need no edit: each states its parent path as an opaque example in its
opening table (`| channels.yaml path for the leaf | desktop.python.linux.ppa | the leaf's parent |`)
and never names the levels.

### §6 — What v27 does not settle

Both remain open on #80, and both inherit §2's names:

- **Item 2 — stop discarding what `/orc-code` already knows.** It confirms component, stack and
  platform during the New-Project Flow and writes none of them down. This is where the
  single-component naming question from §2 has to be answered.
- **Item 3 — make the tree something you can look at and act on.** Today the only way to see a
  project's shape is to open `channels.yaml`; the view of which coordinates are still blank is as
  useful as the filled-in one.

Read **#75** before item 2: it is the same root from the platform-ceiling side and already names
`/orc-code`'s planning step as the likely home. Read **#65** before item 3: a cross-project
dependency is plausibly an address in this same tree.

### §7 — How it is checked

One test, in the shape of `hooks/scripts/tests/test_docs.py`: no shipped `SKILL.md` or
`docs/commands/` page contains the retired `component/platform/os` sequence, and
`recipe-discipline`'s own table is the only place the five names are defined. That is a real
check — it fails if someone reintroduces the old vocabulary, and it fails if a second definition
grows somewhere else, which is the specific failure the "two places to keep in sync" argument in
§3 is worried about.

Per `CLAUDE.md`, `claude plugin validate` is not part of this: it does not read frontmatter, so it
cannot confirm `user-invocable: false` is spelled correctly on the new skill. Nothing mechanical
checks that today; `hooks/scripts/tests/test_side_effecting_skills_frontmatter.py` is the existing
precedent for a frontmatter test if one is wanted, and it is not proposed here.
