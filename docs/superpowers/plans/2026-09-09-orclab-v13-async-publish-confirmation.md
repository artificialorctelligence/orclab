# Orclab v13: Confirming an Asynchronous Publish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop `/orc-publish` reporting `success` for a publish that was only *accepted*, and give a channel a way to declare how anyone finds out whether it actually landed.

**Architecture:** One additive leaf field, `confirm`, holding optional `command` and `url`. Declaring it is what marks a publish asynchronous — such a leaf reports `accepted` instead of `success`, and a new `--confirm` mode runs the check without publishing anything. All of it rides the execution path that already exists (`_run`, per-leaf timeout, process-group kill, output capture); nothing polls, waits, sleeps or retries.

**Tech Stack:** Python 3 stdlib + PyYAML (already a dependency). pytest for tests. No new dependency.

**Spec:** `docs/superpowers/specs/2026-09-07-orclab-v13-async-publish-confirmation-design.md`. Closes **BACKLOG #18**.

## Global Constraints

- **No new dependency.**
- **Every new field and status is additive** — no existing configuration changes behaviour. A leaf with no `confirm` behaves exactly as it does today.
- **No polling, waiting, retrying or sleeping.** This observes an asynchronous publish; it never blocks on one.
- `/orc-publish` **continues past an independent leaf's outcome**, as it already does for `failed`, `timed out` and `refused`.
- **Orclab ships the mechanism only.** No project's `channels.yaml` is written by this work. Orcshot adopting it is separate work, in a session centred on Orcshot.
- The `orc-` prefix holds; no component is renamed.
- Test command, from `skills/orc-publish/scripts`: `python3 -m pytest tests/ -v`. Baseline before this plan: **127 passed**.

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `skills/orc-publish/scripts/orc_publish/tree.py` | Leaf schema and accessors | Add `confirm` to `LEAF_KEYS`; three properties |
| `skills/orc-publish/scripts/orc_publish/cli.py` | Validation, execution, formatting, argparse | `confirm_error`, `_accepted_detail`, `accepted` in `execute_plan`, `confirm_plan`, `format_confirm_plan`, `--confirm` wiring |
| `skills/orc-publish/scripts/tests/test_tree.py` | Schema tests | Task 1 |
| `skills/orc-publish/scripts/tests/test_cli.py` | Everything else | Tasks 2–4 |
| `skills/orc-publish/SKILL.md` | The user-facing surface | Task 5 |
| `skills/release-checklist/SKILL.md` | Two prose rules | Task 5 |
| `VERIFICATION.md` | The scenario unit tests cannot cover | Task 5 |

**Why `confirm` is not shaped like `metrics`.** `cli.py:38` predicts this entry and proposes the `metrics` shape — one more key in `NOT_SET`, sharing `command_key`. That prediction is wrong for what the spec actually chose: `confirm` is a *mapping* of two optional sub-fields, not a bare command string, and `--confirm` reports four statuses of its own rather than reusing `success`/`failed`. So it gets its own small path. Delete that stale sentence in Task 4 rather than leaving a comment that points the next reader at the wrong design.

## Two decisions this plan makes that the spec does not state

Both are flagged so review can overrule them without archaeology.

1. **`--confirm` exit code.** Only `not confirmed` exits 1. `confirmed`, `needs a human` and `no confirm declared` exit 0. Rationale: the spec makes `--confirm` a `/orc-release` **Preconditions:** command, so a met precondition must exit 0 and an unmet one non-zero — but the spec also says a `url`-only leaf makes `/orc-release` "stop and ask, the same shape as a step marked **Performed by hand.**", i.e. the human is already the gate there. Exit 1 must mean "the check ran and answered no."
2. **`--confirm` also rejects `--metrics`, not just `--dry-run`.** The spec names only `--dry-run`, but its stated reason — "silently dropping a flag the operator typed is how someone comes to believe a dry run happened when it did not" — applies identically to two flags that both select which command runs.

---

### Task 1: `confirm` in the leaf schema

**Files:**
- Modify: `skills/orc-publish/scripts/orc_publish/tree.py:10-15` (`LEAF_KEYS`), and add properties after `preflight`
- Test: `skills/orc-publish/scripts/tests/test_tree.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Node.confirm` -> the raw value (`dict`, or whatever YAML gave, or `None`); `Node.confirm_command` -> `str | None`; `Node.confirm_url` -> `str | None`.

**Why this task is first and matters more than it looks:** `Node.is_leaf` is `set(self._data.keys()) <= LEAF_KEYS`. Until `confirm` is in that set, a leaf declaring it stops being a leaf and is parsed as a *branch* — the tree silently changes shape. Every later task depends on this.

- [ ] **Step 1: Write the failing tests**

Append to `skills/orc-publish/scripts/tests/test_tree.py`:

```python
def test_a_leaf_declaring_confirm_is_still_a_leaf(tmp_path):
    # is_leaf is a subset test against LEAF_KEYS: an unknown key turns the leaf into a branch
    # and the tree silently changes shape, so this is the load-bearing assertion of the field.
    p = tmp_path / "channels.yaml"
    p.write_text(
        "ppa:\n"
        "  noble:\n"
        "    action: dput ppa:x a.changes\n"
        "    confirm:\n"
        "      command: python3 scripts/ppa-published.py\n"
        "      url: https://launchpad.net/~x/+archive/ubuntu/y/+packages\n"
    )
    leaf = load_tree(str(p)).child("ppa").child("noble")
    assert leaf.is_leaf
    assert leaf.confirm_command == "python3 scripts/ppa-published.py"
    assert leaf.confirm_url == "https://launchpad.net/~x/+archive/ubuntu/y/+packages"


def test_confirm_may_declare_command_only(tmp_path):
    p = tmp_path / "channels.yaml"
    p.write_text("ppa:\n  noble:\n    action: dput x\n    confirm:\n      command: check.sh\n")
    leaf = load_tree(str(p)).child("ppa").child("noble")
    assert leaf.confirm_command == "check.sh"
    assert leaf.confirm_url is None


def test_confirm_may_declare_url_only(tmp_path):
    p = tmp_path / "channels.yaml"
    p.write_text("ppa:\n  noble:\n    action: dput x\n    confirm:\n      url: https://example.test/q\n")
    leaf = load_tree(str(p)).child("ppa").child("noble")
    assert leaf.confirm_command is None
    assert leaf.confirm_url == "https://example.test/q"


def test_a_leaf_without_confirm_reports_none(tmp_path):
    p = tmp_path / "channels.yaml"
    p.write_text("ppa:\n  noble:\n    action: dput x\n")
    leaf = load_tree(str(p)).child("ppa").child("noble")
    assert leaf.confirm is None
    assert leaf.confirm_command is None
    assert leaf.confirm_url is None


def test_a_malformed_confirm_scalar_does_not_raise(tmp_path):
    # Same reasoning as `preflight`: refusing a malformed leaf is the caller's job. Raising in
    # the property aborts the whole run over one bad leaf, and its healthy siblings never run.
    p = tmp_path / "channels.yaml"
    p.write_text("ppa:\n  noble:\n    action: dput x\n    confirm: true\n")
    leaf = load_tree(str(p)).child("ppa").child("noble")
    assert leaf.confirm is True
    assert leaf.confirm_command is None
    assert leaf.confirm_url is None
```

**Note for the implementer:** check how the existing tests in this file build a tree and reach a node — if they use a helper rather than `load_tree(...).child(...)`, use that helper instead and keep the assertions identical. Do not introduce a second idiom in the same file.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_tree.py -v -k confirm`
Expected: FAIL. `test_a_leaf_declaring_confirm_is_still_a_leaf` fails on `assert leaf.is_leaf`; the rest fail with `AttributeError: 'Node' object has no attribute 'confirm_command'`.

- [ ] **Step 3: Add the key and the properties**

In `orc_publish/tree.py`, extend `LEAF_KEYS`:

```python
LEAF_KEYS = frozenset(
    {
        "action", "metrics", "channel", "requirements", "issues", "timeout",
        "prepare", "artifact", "preflight", "confirm",
    }
)
```

And add these three properties immediately after the `preflight` property:

```python
    @property
    def confirm(self):
        """How anyone finds out whether this publish actually landed. None when unset.

        A mapping of two optional sub-fields, `command` and `url`. Declaring it is what marks
        the publish asynchronous - there is deliberately no separate `async:` flag, because one
        flag could then disagree with the other.

        A non-mapping value (`confirm: true`) is returned as-is rather than coerced or raised
        on, for the same reason `preflight` tolerates a bad scalar: one malformed leaf must not
        abort a run whose other leaves are healthy. Refusing it is `confirm_error`'s job.
        """
        return self._data.get("confirm") if self.is_leaf else None

    @property
    def confirm_command(self):
        """The check to run, or None when unset or when `confirm` is not a mapping."""
        value = self.confirm
        return value.get("command") if isinstance(value, dict) else None

    @property
    def confirm_url(self):
        """The page a human reads, or None when unset or when `confirm` is not a mapping."""
        value = self.confirm
        return value.get("url") if isinstance(value, dict) else None
```

- [ ] **Step 4: Run the whole suite**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS — 132 passed (127 baseline + 5 new). No existing test changes behaviour; the field is purely additive.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-publish/scripts/orc_publish/tree.py skills/orc-publish/scripts/tests/test_tree.py
git commit -m "v13: add the confirm leaf field to the channel schema

confirm holds two optional sub-fields, command and url. Declaring it is what
marks a publish asynchronous - no separate async flag, so nothing can disagree.

Adding it to LEAF_KEYS is the load-bearing part: is_leaf is a subset test, so
until confirm is in that set a leaf declaring it parses as a branch and the
tree silently changes shape.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Refuse a `confirm` that declares nothing

**Files:**
- Modify: `skills/orc-publish/scripts/orc_publish/cli.py` — add `confirm_error` after `timeout_error` (ends at :161); wire it into `main` after the `bad_timeout` check
- Test: `skills/orc-publish/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: `Node.confirm`, `Node.confirm_command`, `Node.confirm_url` (Task 1).
- Produces: `confirm_error(leaves) -> str | None` — the first unusable `confirm:` as a message.

**Why:** the spec requires "a leaf with neither sub-field is a configuration error reported as an `error:` line, not silently ignored." Such a leaf declares the publish asynchronous and then gives nobody any way to find out whether it landed — there is no sensible default to fall back to.

- [ ] **Step 1: Write the failing tests**

Append to `skills/orc-publish/scripts/tests/test_cli.py`:

```python
def test_confirm_with_neither_command_nor_url_is_an_error(tmp_path, capsys):
    # Declaring confirm says "this publish is asynchronous" and then names no way to find out
    # whether it landed. There is no default that could stand in for the missing answer.
    channels = tmp_path / "channels.yaml"
    channels.write_text("ppa:\n  noble:\n    action: true\n    confirm: {}\n")
    assert main(["--channels", str(channels), "--dry-run", "ppa"]) == 1
    assert "confirm must declare" in capsys.readouterr().err


def test_a_non_mapping_confirm_is_an_error_naming_the_value(tmp_path, capsys):
    channels = tmp_path / "channels.yaml"
    channels.write_text("ppa:\n  noble:\n    action: true\n    confirm: true\n")
    assert main(["--channels", str(channels), "--dry-run", "ppa"]) == 1
    err = capsys.readouterr().err
    assert "confirm must be a mapping" in err
    assert "True" in err


def test_a_well_formed_confirm_is_not_an_error(tmp_path):
    channels = tmp_path / "channels.yaml"
    channels.write_text("ppa:\n  noble:\n    action: true\n    confirm:\n      url: https://e.test/q\n")
    assert main(["--channels", str(channels), "--dry-run", "ppa"]) == 0
```

**Note for the implementer:** match however the existing `test_cli.py` tests construct a channels file and call `main` — several already do exactly this for `timeout:`. Reuse that idiom rather than adding a new one.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_cli.py -v -k confirm`
Expected: FAIL — both error tests return 0 instead of 1, because nothing validates the field yet.

- [ ] **Step 3: Add `confirm_error` and wire it in**

In `orc_publish/cli.py`, immediately after `timeout_error`:

```python
def confirm_error(leaves):
    """The first unusable `confirm:` block, as a message - or None.

    Same treatment as a bad `timeout:`, and for the same reason: the value is a declaration
    the operator made, it cannot do what it claims, and guessing a default would be inventing
    an answer to "did this land" that nobody supplied.
    """
    for leaf in leaves:
        value = leaf.confirm
        if value is None:
            continue
        if not isinstance(value, dict):
            return (
                f"{leaf.dotted_path}: confirm must be a mapping with `command` and/or `url`, "
                f"got {value!r}"
            )
        if not leaf.confirm_command and not leaf.confirm_url:
            return f"{leaf.dotted_path}: confirm must declare `command`, `url`, or both"
    return None
```

In `main`, immediately after the existing `bad_timeout` block:

```python
    bad_confirm = confirm_error(leaves)
    if bad_confirm:
        print(f"error: {bad_confirm}", file=sys.stderr, flush=True)
        return 1
```

- [ ] **Step 4: Run the whole suite**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS — 135 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-publish/scripts/orc_publish/cli.py skills/orc-publish/scripts/tests/test_cli.py
git commit -m "v13: refuse a confirm block that declares neither command nor url

Such a leaf says its publish is asynchronous and then names no way to find out
whether it landed. Reported as an error line before anything runs, the same
treatment a bad timeout gets, because there is no default to fall back to.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: `accepted` instead of `success`

**Files:**
- Modify: `skills/orc-publish/scripts/orc_publish/cli.py` — `execute_plan` (:300-386), and a new `_accepted_detail` helper above it
- Test: `skills/orc-publish/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: `Node.confirm`, `Node.confirm_command`, `Node.confirm_url` (Task 1); `GATED_COMMAND_KEY` (`cli.py:44`).
- Produces: a fifth status string, `"accepted"`, in `execute_plan`'s return tuples; `_accepted_detail(leaf, output) -> str`.

**Two properties that need no code change, and must be tested rather than assumed:**
- **Exit code stays 0.** `main`'s final expression is `all(status not in ("failed", "timed out", "refused") ...)`. `accepted` is not in that tuple, so it already exits 0. Making a healthy async publish exit non-zero would conflate "still in flight" with "something broke" in the one signal automation reads.
- **`refused` never becomes `accepted`.** The preflight gate `continue`s before the action runs, so no confirmation state can exist for a refused leaf.

- [ ] **Step 1: Write the failing tests**

Append to `skills/orc-publish/scripts/tests/test_cli.py`:

```python
def test_a_leaf_declaring_confirm_reports_accepted_not_success(tmp_path, capsys):
    channels = tmp_path / "channels.yaml"
    channels.write_text(
        "ppa:\n  noble:\n    action: echo uploaded\n"
        "    confirm:\n      command: true\n      url: https://e.test/q\n"
    )
    assert main(["--channels", str(channels), "ppa"]) == 0
    out = capsys.readouterr().out
    assert "ppa.noble: accepted" in out
    assert "ppa.noble: success" not in out


def test_the_accepted_detail_says_it_is_not_done_and_how_to_find_out(tmp_path, capsys):
    # The word is doing the work here. #15 established that a substring assertion can pass on
    # output no operator can actually read, so assert the whole sentence a human sees.
    channels = tmp_path / "channels.yaml"
    channels.write_text(
        "ppa:\n  noble:\n    action: echo uploaded\n"
        "    confirm:\n      command: true\n      url: https://e.test/q\n"
    )
    main(["--channels", str(channels), "ppa"])
    out = capsys.readouterr().out
    assert "upload accepted; not yet confirmed - run --confirm, or see https://e.test/q" in out
    assert "uploaded" in out  # the action's own output is still the evidence it ran


def test_a_url_only_confirm_still_reports_accepted(tmp_path, capsys):
    channels = tmp_path / "channels.yaml"
    channels.write_text(
        "ppa:\n  noble:\n    action: echo uploaded\n    confirm:\n      url: https://e.test/q\n"
    )
    assert main(["--channels", str(channels), "ppa"]) == 0
    assert "no confirm command declared, or see https://e.test/q" in capsys.readouterr().out


def test_a_leaf_without_confirm_still_reports_success(tmp_path, capsys):
    channels = tmp_path / "channels.yaml"
    channels.write_text("ppa:\n  noble:\n    action: echo uploaded\n")
    assert main(["--channels", str(channels), "ppa"]) == 0
    assert "ppa.noble: success" in capsys.readouterr().out


def test_metrics_on_a_confirm_leaf_is_not_accepted(tmp_path, capsys):
    # --metrics reads back numbers a channel already publishes. Nothing was submitted, so
    # there is nothing pending to confirm.
    channels = tmp_path / "channels.yaml"
    channels.write_text(
        "ppa:\n  noble:\n    action: echo uploaded\n    metrics: echo 12 downloads\n"
        "    confirm:\n      command: true\n"
    )
    assert main(["--channels", str(channels), "--metrics", "ppa"]) == 0
    out = capsys.readouterr().out
    assert "ppa.noble: success" in out
    assert "accepted" not in out


def test_a_refused_leaf_never_reaches_accepted(tmp_path, capsys):
    # Composition with v12: refusal precedes the action, so no confirmation state can exist.
    channels = tmp_path / "channels.yaml"
    channels.write_text(
        "ppa:\n  noble:\n    action: echo uploaded\n    preflight: no-such-rule\n"
        "    confirm:\n      command: true\n"
    )
    assert main(["--channels", str(channels), "ppa"]) == 1
    out = capsys.readouterr().out
    assert "ppa.noble: refused" in out
    assert "accepted" not in out
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_cli.py -v -k "accepted or without_confirm or refused_leaf"`
Expected: FAIL — the leaves report `success`, not `accepted`. `test_a_leaf_without_confirm_still_reports_success` and `test_a_refused_leaf_never_reaches_accepted` should already PASS; that is intended, they are the regression guards.

- [ ] **Step 3: Add `_accepted_detail` and use it**

In `orc_publish/cli.py`, immediately above `execute_plan`:

```python
def _accepted_detail(leaf, output):
    """The `accepted` line's detail: what happened, what has not, and how to find out.

    The action's own output goes last, not first. A real publish's capture is a wall of log,
    and the sentence that tells an operator this is not finished has to survive being read
    above it - see BACKLOG #15, where a correct message was unreadable in exactly this way.
    """
    how = "run --confirm" if leaf.confirm_command else "no confirm command declared"
    if leaf.confirm_url:
        how += f", or see {leaf.confirm_url}"
    parts = [f"upload accepted; not yet confirmed - {how}"]
    if output:
        parts.append(output)
    return "\n".join(parts)
```

In `execute_plan`, replace the success branch:

```python
            detail = (stdout or "").strip()
            results.append((leaf, "success", detail))
```

with:

```python
            detail = (stdout or "").strip()
            if command_key == GATED_COMMAND_KEY and leaf.confirm:
                results.append((leaf, "accepted", _accepted_detail(leaf, detail)))
            else:
                results.append((leaf, "success", detail))
```

Then extend `execute_plan`'s docstring — its second paragraph currently enumerates the statuses:

```python
    Returns a list of (leaf, status, detail) - status is "success", "accepted", "failed",
    "timed out", "refused", or "not attempted". A leaf that declares `confirm` reports
    "accepted" rather than "success" on a zero-exit action: the upload genuinely succeeded
    and nothing went wrong, so the exit code stays 0, but it has not landed yet. detail is
    the command's real stdout on success, the real error text on failure, and the per-key
    "not set" wording when not attempted - never silently empty on success, since this is
    the only evidence an operator gets that a real publish actually happened.
```

- [ ] **Step 4: Run the whole suite**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS — 141 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-publish/scripts/orc_publish/cli.py skills/orc-publish/scripts/tests/test_cli.py
git commit -m "v13: a leaf declaring confirm reports accepted, not success

dput printing 'Successfully uploaded packages.' says nothing about whether the
package built. A leaf that knows how to check itself is exactly a leaf whose
publish does not settle when the action exits, so it now reports accepted.

Exit code stays 0 and needed no change - accepted is not in main's failure
tuple. Making a healthy async publish exit non-zero would conflate 'still in
flight' with 'something broke' in the one signal automation reads. Both that
and 'a refused leaf never reaches accepted' are covered by tests rather than
left as properties nobody checks.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: `--confirm`

**Files:**
- Modify: `skills/orc-publish/scripts/orc_publish/cli.py` — a `NO_CONFIRM` constant beside `NO_METRICS` (:32-33), the stale comment at :38, `format_confirm_plan` and `confirm_plan` after `format_summary`, and `main`'s argparse and dispatch
- Test: `skills/orc-publish/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: `Node.confirm_command`, `Node.confirm_url` (Task 1); `_run`, `_decode`, `effective_timeout`, `format_summary`, `DEFAULT_TIMEOUT_SECONDS` (all existing in `cli.py`).
- Produces: `confirm_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS) -> list[(Node, str, str)]` with status in `{"confirmed", "not confirmed", "needs a human", "no confirm declared"}`; `format_confirm_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS) -> str`.

- [ ] **Step 1: Write the failing tests**

Append to `skills/orc-publish/scripts/tests/test_cli.py`:

```python
def test_confirm_mode_publishes_nothing(tmp_path, capsys):
    # The sentinel is the whole test: if the action ran, the file exists.
    sentinel = tmp_path / "published.txt"
    channels = tmp_path / "channels.yaml"
    channels.write_text(
        f"ppa:\n  noble:\n    action: touch {sentinel}\n    confirm:\n      command: true\n"
    )
    assert main(["--channels", str(channels), "--confirm", "ppa"]) == 0
    assert not sentinel.exists()
    assert "ppa.noble: confirmed" in capsys.readouterr().out


def test_confirm_maps_a_nonzero_exit_to_not_confirmed_with_the_real_output(tmp_path, capsys):
    channels = tmp_path / "channels.yaml"
    channels.write_text(
        "ppa:\n  noble:\n    action: true\n"
        "    confirm:\n      command: sh -c 'echo still building >&2; exit 3'\n"
    )
    assert main(["--channels", str(channels), "--confirm", "ppa"]) == 1
    out = capsys.readouterr().out
    assert "ppa.noble: not confirmed" in out
    assert "still building" in out


def test_a_url_only_leaf_needs_a_human_and_prints_the_url(tmp_path, capsys):
    channels = tmp_path / "channels.yaml"
    channels.write_text(
        "ppa:\n  noble:\n    action: true\n    confirm:\n      url: https://e.test/packages\n"
    )
    assert main(["--channels", str(channels), "--confirm", "ppa"]) == 0
    out = capsys.readouterr().out
    assert "ppa.noble: needs a human" in out
    assert "https://e.test/packages" in out


def test_a_leaf_with_no_confirm_reports_no_confirm_declared(tmp_path, capsys):
    channels = tmp_path / "channels.yaml"
    channels.write_text("ppa:\n  noble:\n    action: true\n")
    assert main(["--channels", str(channels), "--confirm", "ppa"]) == 0
    assert "ppa.noble: no confirm declared" in capsys.readouterr().out


def test_a_not_confirmed_leaf_does_not_stop_the_next_one(tmp_path, capsys):
    channels = tmp_path / "channels.yaml"
    channels.write_text(
        "ppa:\n"
        "  noble:\n    action: true\n    confirm:\n      command: false\n"
        "  jammy:\n    action: true\n    confirm:\n      command: true\n"
    )
    assert main(["--channels", str(channels), "--confirm", "ppa"]) == 1
    out = capsys.readouterr().out
    assert "ppa.noble: not confirmed" in out
    assert "ppa.jammy: confirmed" in out


def test_confirm_rejects_dry_run_rather_than_ignoring_one_of_them(tmp_path, capsys):
    # Silently dropping a flag the operator typed is how someone comes to believe a dry run
    # happened when it did not.
    channels = tmp_path / "channels.yaml"
    channels.write_text("ppa:\n  noble:\n    action: true\n")
    assert main(["--channels", str(channels), "--confirm", "--dry-run", "ppa"]) == 1
    assert "--confirm cannot be combined with --dry-run" in capsys.readouterr().err


def test_confirm_rejects_metrics_for_the_same_reason(tmp_path, capsys):
    channels = tmp_path / "channels.yaml"
    channels.write_text("ppa:\n  noble:\n    action: true\n")
    assert main(["--channels", str(channels), "--confirm", "--metrics", "ppa"]) == 1
    assert "--confirm cannot be combined with --metrics" in capsys.readouterr().err


def test_a_confirm_command_that_hangs_is_not_confirmed_rather_than_hanging(tmp_path, capsys):
    channels = tmp_path / "channels.yaml"
    channels.write_text(
        "ppa:\n  noble:\n    action: true\n    timeout: 1\n"
        "    confirm:\n      command: sleep 30\n"
    )
    assert main(["--channels", str(channels), "--confirm", "ppa"]) == 1
    out = capsys.readouterr().out
    assert "ppa.noble: not confirmed" in out
    assert "timed out after 1s" in out
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_cli.py -v -k "confirm_mode or not_confirmed or needs_a_human or no_confirm_declared or rejects"`
Expected: FAIL — `error: unrecognized arguments: --confirm` (argparse exits 2 via SystemExit).

- [ ] **Step 3: Implement the mode**

In `orc_publish/cli.py`, add the constant beside `NO_METRICS`:

```python
NO_CONFIRM = "synchronous channel - its publish settles when the action exits"
```

Replace the stale prediction in the `NOT_SET` comment. The current final sentence reads:

```python
# BACKLOG #18's proposed `status:` is the same shape again: add it to tree.LEAF_KEYS and to
# NOT_SET below.
```

Replace it with:

```python
# BACKLOG #18 shipped as `confirm:` and is deliberately NOT this shape - it is a mapping of
# two optional sub-fields, not a bare command, and it reports four statuses of its own. It has
# its own small path (confirm_plan) rather than a fourth entry here.
```

Add both functions immediately after `format_summary`:

```python
def format_confirm_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS):
    """What `--confirm` will check, printed before it runs.

    Deliberately not `format_plan` with a third command key: `--confirm` publishes nothing, so
    there is no preflight or action-shape line to print, and half of what it reports is a URL
    rather than a command.
    """
    if not leaves:
        return "(no leaves selected)"
    lines = []
    for leaf in leaves:
        if leaf.confirm_command:
            lines.append(f"{leaf.dotted_path}: {leaf.confirm_command}")
            lines.append(f"  timeout: {effective_timeout(leaf, default_timeout)}s")
        elif leaf.confirm_url:
            lines.append(f"{leaf.dotted_path}: (needs a human) {leaf.confirm_url}")
        else:
            lines.append(f"{leaf.dotted_path}: ({NO_CONFIRM})")
    return "\n".join(lines)


def confirm_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS):
    """Check whether each selected leaf's accepted publish has actually landed.

    Publishes nothing. Returns (leaf, status, detail) with status "confirmed",
    "not confirmed", "needs a human", or "no confirm declared".

    Exit 0 from the command means confirmed and anything else means not confirmed - two
    states, not three. A three-state protocol distinguishing "not yet" from "the check itself
    broke" would have to be honoured by every project implementing `confirm`, and for gating
    purposes both answers mean do not advance. Which one it was belongs in the command's own
    output, which a human reads.

    A timeout is "not confirmed" for the same reason: it is not a positive answer, and this
    never waits on a remote publish by design.
    """
    results = []
    for leaf in leaves:
        command = leaf.confirm_command
        if not command:
            if leaf.confirm_url:
                results.append((leaf, "needs a human", leaf.confirm_url))
            else:
                results.append((leaf, "no confirm declared", NO_CONFIRM))
            continue

        limit = effective_timeout(leaf, default_timeout)
        try:
            returncode, stdout, stderr = _run(command, limit)
        except subprocess.TimeoutExpired as e:
            captured = "\n".join(filter(None, [_decode(e.stdout), _decode(e.stderr)]))
            detail = f"confirm timed out after {limit}s"
            if captured:
                detail += f"\n{captured}"
            results.append((leaf, "not confirmed", detail))
            continue

        detail = "\n".join(filter(None, [(stdout or "").strip(), (stderr or "").strip()]))
        if leaf.confirm_url:
            detail = "\n".join(filter(None, [detail, f"see {leaf.confirm_url}"]))
        results.append((leaf, "confirmed" if returncode == 0 else "not confirmed", detail))
    return results
```

In `main`, add the flag after `--metrics`:

```python
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="check whether each selected leaf's already-accepted publish has actually "
        "landed, by running its `confirm.command` - publishes nothing",
    )
```

Immediately after the `is_bad_timeout(args.timeout)` block, add the conflict check:

```python
    if args.confirm and (args.dry_run or args.metrics):
        other = "--dry-run" if args.dry_run else "--metrics"
        print(
            f"error: --confirm cannot be combined with {other} - --confirm is its own mode "
            "and publishes nothing. Run them separately.",
            file=sys.stderr,
            flush=True,
        )
        return 1
```

And insert the dispatch immediately **before** the existing `command_key = ...` line:

```python
    if args.confirm:
        print(format_confirm_plan(leaves, default_timeout=args.timeout), flush=True)
        results = confirm_plan(leaves, default_timeout=args.timeout)
        print(format_summary(results), flush=True)
        return 0 if all(status != "not confirmed" for _, status, _ in results) else 1
```

**Exit-code note for the reviewer:** only `not confirmed` exits 1. `needs a human` exits 0 because the spec makes `/orc-release` stop and ask on such a leaf — the human is the gate there, not the exit code. See "Two decisions this plan makes" at the top.

- [ ] **Step 4: Run the whole suite**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS — 149 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-publish/scripts/orc_publish/cli.py skills/orc-publish/scripts/tests/test_cli.py
git commit -m "v13: add --confirm, which checks a publish landed and publishes nothing

Resolves the selection exactly as a publish does, runs each leaf's
confirm.command, and reports confirmed / not confirmed / needs a human / no
confirm declared. Two states from the command, not three: every project would
have to honour a richer protocol and for gating both non-zero answers mean the
same thing.

Rejects --dry-run and --metrics rather than silently dropping one - that is how
someone comes to believe a dry run happened when it did not. The spec names
only --dry-run; --metrics is the same failure for the same reason.

Also corrects the NOT_SET comment, which predicted #18 would land as a
metrics-shaped 'status:' key. It did not.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: The prose — `SKILL.md`, two `release-checklist` rules, and the verification scenario

**Files:**
- Modify: `skills/orc-publish/SKILL.md` — document `confirm`, `accepted`, and `--confirm`
- Modify: `skills/release-checklist/SKILL.md` — two rules
- Modify: `VERIFICATION.md` — one scenario
- Modify: `BACKLOG.md` — resolve #18 per `backlog-discipline`

**Interfaces:**
- Consumes: everything from Tasks 1–4. No code.

**Read first:** `skills/orc-publish/SKILL.md` end to end before editing it, and `skills/release-checklist/SKILL.md`'s existing `**Preconditions:**` section. Both rules below *extend* wording that is already there; neither is a new marker.

- [ ] **Step 1: Document the field, the status and the mode in `orc-publish/SKILL.md`**

Match the file's existing voice and table style. It must cover: the `confirm` field with both sub-fields and that at least one is required; that declaring it is what marks a publish asynchronous; the `accepted` status and that it exits 0; `--confirm`'s four statuses; and that `--confirm` rejects `--dry-run` and `--metrics`. Include the spec's worked YAML:

```yaml
noble:
  action: "… && dput ppa:artificialorctelligence/orcshot …"
  confirm:
    command: "python3 scripts/ppa-published.py --version $(dpkg-parsechangelog --show-field Version)"
    url: "https://launchpad.net/~artificialorctelligence/+archive/ubuntu/orcshot/+packages"
```

Also carry across the spec's two honest limits, which belong in the user-facing document rather than only in the spec:
- Orclab cannot enforce that `confirm.command` is read-only. The field is documented as a check and every real example is a query, but the guarantee is the project's. Anyone auditing a `channels.yaml` should read its `confirm` commands with that in mind.
- A confirmed publish is confirmed *at that moment*. Nothing is cached and nothing is watched. Re-running `--confirm` is how you find out again.

- [ ] **Step 2: Add the two rules to `release-checklist/SKILL.md`**

**Rule 1 — a step that waits on external state must be two steps.** The local action is one step; whatever depends on the remote result is another, with a precondition. A single step cannot honestly represent "the first half is done and the second half cannot start yet", because `/orc-release` has one completion state per step, so marking it complete claims more than happened. Cite the real incident: Orcshot's `0.3.0` release had build/sign/upload, a ~28-minute Launchpad build, and the series copy all as step 6; `complete 6` was recorded while the copy was still half an hour away, and the release was recorded as further along than it was.

**Rule 2 — prefer a precondition that names a command over one that only describes a condition.** "This version is not already published to the PPA" is good prose; a command that answers it is a gate. This extends the marker's existing advice to prefer "the specific and checkable" by saying what checkable means when a check is actually available. Worked example:

```markdown
## 7. Copy the built package to 26.04

**Preconditions:** the `noble` build has succeeded on Launchpad — not merely been accepted.
Check with `/orc-publish --confirm desktop.python.linux.ppa.noble`.
```

- [ ] **Step 3: Add the `VERIFICATION.md` scenario**

Use `/orc-todo` so the scenario gets a real allocated number — do not hand-number it:

```bash
python3 <orclab>/skills/orc-todo/scripts/run.py add verification "an accepted publish reads as not-done to an operator"
```

The scenario covers what unit tests cannot: that an `accepted` summary line reads to a human as *"this is not finished"*. **#15 established that substring assertions pass on output nobody can actually read**, which is exactly why this is a scenario and not another `assert "accepted" in out`. It should have the operator read a real `accepted` line — action output included, since a real one carries a wall of build log above the sentence — and say what they would do next.

- [ ] **Step 4: Resolve BACKLOG #18**

Follow `backlog-discipline`'s "Resolving an entry" exactly — **both** steps, and never rewrite the original text:
1. Append `(RESOLVED YYYY-MM-DD)` to the `## #18:` title line.
2. Append a resolution paragraph below the existing text saying what shipped and how it was verified.

The resolution must address, because the entry raises them explicitly:
- The entry's three candidate answers were a `status:` field, a `release-checklist` marker, and the no-code option of splitting "wait for X, then do Y" into two steps. **The answer was two of the three** — the `confirm` field *and* rule 1 — and neither a new `/orc-release` marker nor a polling loop.
- The entry warned that the cheap mechanism arriving first (`--metrics`) "makes the wrong answer as easy to build as the right one." Record that `confirm` deliberately did **not** reuse that shape.
- **#17 note:** the entry says to decide this alongside #17. #17/v15 remains open and its ingredient shape depends on this field, which now exists. Say so, and do not mark #17 resolved.

- [ ] **Step 5: Run the whole suite one final time and commit**

```bash
cd skills/orc-publish/scripts && python3 -m pytest tests/ -v
```
Expected: PASS — 149 passed. (No code changed in this task; this confirms the prose edits touched nothing they shouldn't.)

```bash
git add skills/orc-publish/SKILL.md skills/release-checklist/SKILL.md VERIFICATION.md BACKLOG.md
git commit -m "v13: document confirm, and the two release-checklist rules it implies

A step that waits on external state must be two steps - the 0.3.0 release
recorded step 6 complete while the series copy was still half an hour away.
And a precondition that names a command is a gate, where one that only
describes a condition is prose.

Resolves BACKLOG #18. Two of its three candidate answers shipped: the confirm
field and the two-step rule. No new /orc-release marker, and no polling.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-review

**Spec coverage.** Every section maps to a task: the `confirm` field → 1; the "neither sub-field is an error" requirement → 2; `accepted`, its exit code, and the v12 composition → 3; `--confirm`, its four statuses, the timeout, continuing past a failure, and the flag rejection → 4; the two `release-checklist` rules, the `/orc-release` precondition example, the two honest limits, and the `VERIFICATION.md` scenario → 5. "No polling/waiting/retrying" is a Global Constraint and is satisfied by construction — nothing in `confirm_plan` loops or sleeps.

**Placeholders.** None. Every code step carries real code; every test step carries real assertions; the two spec-silent decisions are decided and flagged rather than deferred.

**Type consistency.** `confirm` / `confirm_command` / `confirm_url` are used under those exact names in Tasks 2, 3 and 4. `confirm_plan` and `format_confirm_plan` share the `(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS)` signature. `confirm_plan` returns the same `(leaf, status, detail)` triple `execute_plan` does, which is what lets Task 4 reuse `format_summary` unchanged.

**Known soft spot.** The expected test counts (132 / 135 / 141 / 149) assume the 127 baseline and that no listed test is dropped. If a count is off by one or two after an implementer merges a test into an existing parametrisation, that is fine — the suite passing is the gate, not the arithmetic.
