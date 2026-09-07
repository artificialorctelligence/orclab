# Orclab v11: the three gaps snap/flatpak exposed — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the three framework gaps that block configuring a not-yet-onboarded distribution
channel — honest wording for an action-less channel leaf, a per-leaf timeout strategy for
`execute_plan`, and a `**One-time setup:**` marker whose setup only ever runs when the user asks.

**Architecture:** No new components. Two existing bundled-script modules
(`skills/orc-publish/scripts/orc_publish/{tree,cli}.py`) gain a `timeout` leaf key and new report
wording; two existing `SKILL.md` files (`release-checklist`, `orc-release`) gain one prose
convention and the rule for following it. Tasks 1-4 are TDD against the existing pytest suite;
tasks 5-6 are prose and release bookkeeping.

**Tech Stack:** Python 3.12 stdlib (`subprocess`, `argparse`), PyYAML, pytest. Markdown for the
skill prose.

## Global Constraints

- Source of truth: `docs/superpowers/specs/2026-09-07-orclab-v11-publish-pipeline-gaps-design.md`.
- **No consuming project's content is written and no consuming project's real action is executed.**
  Nothing under `~/projects/orcshot` is touched — not its `RELEASING.md`, not its
  `.orclab/publish/*.yaml`, not its BACKLOG. Orclab ships the mechanism only (`CLAUDE.md`'s
  dogfooding boundary).
- **No real onboarding is performed.** No `snapcraft register`, `snapcraft login`, or Flathub
  submission, at any point, for any reason.
- Default timeout is exactly `600` seconds.
- The timed-out status string is exactly `timed out`, distinct from `failed`.
- The action-less channel wording is exactly `known channel, not yet actionable`.
- Run the suite with `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`.
- Every commit message ends with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## File Structure

| File | Responsibility | Tasks |
|---|---|---|
| `skills/orc-publish/scripts/orc_publish/cli.py` | Report wording, timeout constants/helpers, `execute_plan`, `main` wiring | 1, 3, 4 |
| `skills/orc-publish/scripts/orc_publish/tree.py` | `timeout` as a leaf key and `Node.timeout` | 2 |
| `skills/orc-publish/scripts/tests/test_cli.py` | Tests for wording, timeout behaviour, flag, validation | 1, 3, 4 |
| `skills/orc-publish/scripts/tests/test_tree.py` | Tests for `Node.timeout` | 2 |
| `skills/orc-publish/SKILL.md` | Operator-facing note about timeouts and the new wording | 4 |
| `skills/release-checklist/SKILL.md` | The `**One-time setup:**` marker convention | 5 |
| `skills/orc-release/SKILL.md` | The check-then-ask rule for that marker | 5 |
| `VERIFICATION.md`, `CHANGELOG.md`, `BACKLOG.md`, `.claude-plugin/*.json` | Release bookkeeping | 6 |

---

### Task 1: Honest wording for an action-less channel leaf

Spec part B. A deliberately-empty channel leaf (`snap: {}`) currently reads as an omission
(`(no action set)`). It adopts the parallel of the distro tree's own existing wording.

**Files:**
- Modify: `skills/orc-publish/scripts/orc_publish/cli.py`
- Test: `skills/orc-publish/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: module constant `NOT_ACTIONABLE = "known channel, not yet actionable"` in
  `orc_publish.cli`, used by tasks 3 and 4.

- [ ] **Step 1: Write the failing tests**

Append to `skills/orc-publish/scripts/tests/test_cli.py`:

```python
def test_format_plan_reports_an_action_less_leaf_as_not_yet_actionable(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            desktop:
              python:
                linux:
                  snap: {}
            """,
        )
    )
    leaves = build_plan(root, [])
    text = format_plan(leaves)
    assert "desktop.python.linux.snap: (known channel, not yet actionable)" in text
    assert "no action set" not in text


def test_execute_plan_details_an_action_less_leaf_as_not_yet_actionable(tmp_path):
    root = load_tree(write_yaml(tmp_path, "channels.yaml", "placeholder: {}"))
    leaves = build_plan(root, [])
    results = execute_plan(leaves)
    leaf, status, detail = results[0]
    assert status == "not attempted"
    assert detail == "known channel, not yet actionable"


def test_format_plan_still_shows_a_real_action_unchanged(tmp_path):
    root = load_tree(write_yaml(tmp_path, "channels.yaml", 'a: { action: "echo real" }'))
    text = format_plan(build_plan(root, []))
    assert "a: echo real" in text
    assert "not yet actionable" not in text
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_cli.py -k not_yet_actionable -v`
Expected: FAIL — the assertions find `(no action set)` / `no action set` instead.

- [ ] **Step 3: Write the minimal implementation**

In `skills/orc-publish/scripts/orc_publish/cli.py`, add the constant just below the imports:

```python
NOT_ACTIONABLE = "known channel, not yet actionable"
```

In `format_plan`, replace this line:

```python
        action = leaf.action or "(no action set)"
        lines.append(f"{leaf.dotted_path}: {action}")
```

with:

```python
        action = leaf.action or f"({NOT_ACTIONABLE})"
        lines.append(f"{leaf.dotted_path}: {action}")
```

In `execute_plan`, replace this line:

```python
            results.append((leaf, "not attempted", "no action set"))
```

with:

```python
            results.append((leaf, "not attempted", NOT_ACTIONABLE))
```

Update `execute_plan`'s docstring: change `and "no action set" when not attempted` to
`and "known channel, not yet actionable" when not attempted`.

- [ ] **Step 4: Run the whole suite to verify it passes**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS, all tests, including the pre-existing
`test_execute_plan_reports_not_attempted_for_a_leaf_with_no_action` (it asserts only the status,
which is unchanged).

- [ ] **Step 5: Commit**

```bash
git add skills/orc-publish/scripts/orc_publish/cli.py skills/orc-publish/scripts/tests/test_cli.py
git commit -m "$(cat <<'EOF'
orc-publish: report a deliberately-empty channel leaf honestly

An action-less channel leaf read as "(no action set)", which makes a
deliberate placeholder look like an omission. It now uses the parallel of
the wording the distro tree already has for exactly this idea.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `timeout` as a leaf key

Spec part C, first half. The tree learns the key; nothing uses it yet.

**Files:**
- Modify: `skills/orc-publish/scripts/orc_publish/tree.py`
- Test: `skills/orc-publish/scripts/tests/test_tree.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `Node.timeout` — returns the leaf's raw `timeout:` value, or `None` when unset or
  when the node is a branch. **It does not validate or coerce**; validation lives in task 4.

- [ ] **Step 1: Write the failing tests**

Append to `skills/orc-publish/scripts/tests/test_tree.py`:

```python
def test_leaf_exposes_its_own_timeout():
    node = Node(path=("a",), data={"action": "echo hi", "timeout": 30})
    assert node.timeout == 30


def test_leaf_without_a_timeout_reports_none():
    node = Node(path=("a",), data={"action": "echo hi"})
    assert node.timeout is None


def test_a_node_holding_only_a_timeout_is_still_a_leaf():
    node = Node(path=("a",), data={"timeout": 30})
    assert node.is_leaf


def test_branch_reports_no_timeout():
    node = Node(path=(), data={"desktop": {"action": "echo hi"}})
    assert node.timeout is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_tree.py -k timeout -v`
Expected: FAIL with `AttributeError: 'Node' object has no attribute 'timeout'`.

- [ ] **Step 3: Write the minimal implementation**

In `skills/orc-publish/scripts/orc_publish/tree.py`, extend the key set:

```python
LEAF_KEYS = frozenset(
    {"action", "filename_template", "channel", "requirements", "issues", "timeout"}
)
```

Add the property immediately after the existing `channel` property:

```python
    @property
    def timeout(self):
        """The leaf's own timeout in seconds, or None when unset. Not validated here."""
        return self._data.get("timeout") if self.is_leaf else None
```

- [ ] **Step 4: Run the whole suite to verify it passes**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS, all tests.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-publish/scripts/orc_publish/tree.py skills/orc-publish/scripts/tests/test_tree.py
git commit -m "$(cat <<'EOF'
orc-publish: a leaf can carry its own timeout

Adds timeout to LEAF_KEYS and Node.timeout. Nothing reads it yet - the
execution side lands next.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `execute_plan` honours a timeout and reports `timed out`

Spec part C, second half. Closes the actual hang risk from BACKLOG #11.

**Files:**
- Modify: `skills/orc-publish/scripts/orc_publish/cli.py`
- Test: `skills/orc-publish/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: `NOT_ACTIONABLE` (task 1), `Node.timeout` (task 2).
- Produces:
  - `DEFAULT_TIMEOUT_SECONDS = 600`
  - `effective_timeout(leaf, default_timeout=DEFAULT_TIMEOUT_SECONDS) -> int`
  - `execute_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS)` — unchanged return shape,
    `list[(Node, str, str)]`, with `"timed out"` as a fourth possible status alongside
    `"success"`, `"failed"`, `"not attempted"`.

- [ ] **Step 1: Write the failing tests**

Append to `skills/orc-publish/scripts/tests/test_cli.py`. Note the import line at the top of the
file also needs `DEFAULT_TIMEOUT_SECONDS` and `effective_timeout` added to the
`from orc_publish.cli import (...)` block.

```python
def test_effective_timeout_prefers_the_leafs_own_value(tmp_path):
    root = load_tree(
        write_yaml(tmp_path, "channels.yaml", 'a: { action: "true", timeout: 45 }')
    )
    leaf = build_plan(root, [])[0]
    assert effective_timeout(leaf) == 45


def test_effective_timeout_falls_back_to_the_default(tmp_path):
    root = load_tree(write_yaml(tmp_path, "channels.yaml", 'a: { action: "true" }'))
    leaf = build_plan(root, [])[0]
    assert effective_timeout(leaf) == DEFAULT_TIMEOUT_SECONDS
    assert DEFAULT_TIMEOUT_SECONDS == 600


def test_execute_plan_reports_a_hanging_action_as_timed_out(tmp_path):
    root = load_tree(
        write_yaml(tmp_path, "channels.yaml", 'a: { action: "sleep 5", timeout: 1 }')
    )
    leaves = build_plan(root, [])
    results = execute_plan(leaves)
    leaf, status, detail = results[0]
    assert status == "timed out"
    assert "timed out after 1s" in detail
    assert "waiting on stdin" in detail


def test_execute_plan_continues_past_a_timed_out_leaf(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            a: { action: "sleep 5", timeout: 1 }
            b: { action: "true" }
            """,
        )
    )
    results = execute_plan(build_plan(root, []))
    statuses = {leaf.dotted_path: status for leaf, status, _ in results}
    assert statuses == {"a": "timed out", "b": "success"}


def test_main_exits_non_zero_when_a_leaf_times_out(tmp_path):
    path = write_yaml(
        tmp_path, "channels.yaml", 'a: { action: "sleep 5", timeout: 1 }'
    )
    assert main(["--channels", path]) == 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_cli.py -k "timed_out or effective_timeout" -v`
Expected: FAIL — `ImportError` for `effective_timeout`/`DEFAULT_TIMEOUT_SECONDS`.

- [ ] **Step 3: Write the minimal implementation**

In `skills/orc-publish/scripts/orc_publish/cli.py`, add below `NOT_ACTIONABLE`:

```python
# A "something is wrong" ceiling, not a performance budget. A genuinely slow-but-healthy
# upload sets its own `timeout:` on its leaf rather than raising this. See BACKLOG #11.
DEFAULT_TIMEOUT_SECONDS = 600
```

Add this helper just above `execute_plan`:

```python
def effective_timeout(leaf, default_timeout=DEFAULT_TIMEOUT_SECONDS):
    """The timeout a leaf really runs under: its own if set, otherwise the default."""
    return leaf.timeout if leaf.timeout is not None else default_timeout
```

Replace `execute_plan` entirely with:

```python
def execute_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS):
    """Run each leaf's action. An independent failure doesn't stop the remaining leaves.

    Returns a list of (leaf, status, detail) - status is "success", "failed", "timed out",
    or "not attempted". detail is the action's real stdout on success, the real error text on
    failure, and "known channel, not yet actionable" when not attempted - never silently
    empty on success, since this is the only evidence an operator gets that a real publish
    actually happened.
    """
    results = []
    for leaf in leaves:
        if not leaf.action:
            results.append((leaf, "not attempted", NOT_ACTIONABLE))
            continue
        limit = effective_timeout(leaf, default_timeout)
        try:
            result = subprocess.run(
                leaf.action,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                timeout=limit,
            )
            detail = (result.stdout or "").strip()
            results.append((leaf, "success", detail))
        except subprocess.TimeoutExpired:
            # capture_output=True is why an interactive prompt is invisible - say so, or the
            # operator has no reason to suspect stdin at all.
            results.append(
                (
                    leaf,
                    "timed out",
                    f"timed out after {limit}s - no output captured, "
                    "the action may be waiting on stdin",
                )
            )
        except subprocess.CalledProcessError as e:
            detail = (e.stderr or "").strip() or str(e)
            results.append((leaf, "failed", detail))
    return results
```

In `main`, replace the final return with one that treats a timeout as a failing verdict:

```python
    return 0 if all(status not in ("failed", "timed out") for _, status, _ in results) else 1
```

- [ ] **Step 4: Run the whole suite to verify it passes**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS, all tests.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-publish/scripts/orc_publish/cli.py skills/orc-publish/scripts/tests/test_cli.py
git commit -m "$(cat <<'EOF'
orc-publish: time out a hanging action instead of hanging forever

execute_plan ran every action with no timeout, so an action blocking on
stdin hung the whole run with its prompt swallowed by capture_output.
Each leaf now runs under its own timeout: or a 600s default, and a
timeout reports as its own status with the stdin cause named.

Closes BACKLOG #11.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: `--timeout` override, config validation, and the dry-run timeout line

Spec part C, remainder: the run-wide override that a leaf still beats, a clean error for a
nonsense `timeout:`, and making the effective limit visible before the user confirms.

**Files:**
- Modify: `skills/orc-publish/scripts/orc_publish/cli.py`
- Modify: `skills/orc-publish/SKILL.md`
- Test: `skills/orc-publish/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: `NOT_ACTIONABLE`, `DEFAULT_TIMEOUT_SECONDS`, `effective_timeout`, `execute_plan`.
- Produces:
  - `format_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS)` — second parameter is new and
    optional, so existing single-argument calls keep working.
  - `timeout_error(leaves) -> str | None` — the first bad-`timeout:` message, or `None`.

- [ ] **Step 1: Write the failing tests**

Append to `skills/orc-publish/scripts/tests/test_cli.py`, adding `timeout_error` to the
`from orc_publish.cli import (...)` block at the top of the file:

```python
def test_format_plan_shows_each_actionable_leafs_effective_timeout(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            a: { action: "true", timeout: 45 }
            b: { action: "true" }
            c: {}
            """,
        )
    )
    text = format_plan(build_plan(root, []))
    assert "  timeout: 45s" in text
    assert "  timeout: 600s" in text
    # An action-less leaf runs nothing, so it has no timeout to show.
    assert text.splitlines()[-1] == "c: (known channel, not yet actionable)"


def test_format_plan_reflects_a_run_wide_default_override(tmp_path):
    root = load_tree(write_yaml(tmp_path, "channels.yaml", 'b: { action: "true" }'))
    text = format_plan(build_plan(root, []), default_timeout=30)
    assert "  timeout: 30s" in text


def test_a_leafs_own_timeout_beats_a_run_wide_override(tmp_path):
    root = load_tree(
        write_yaml(tmp_path, "channels.yaml", 'a: { action: "true", timeout: 45 }')
    )
    leaf = build_plan(root, [])[0]
    assert effective_timeout(leaf, default_timeout=30) == 45


def test_timeout_error_rejects_a_non_integer_timeout(tmp_path):
    root = load_tree(
        write_yaml(tmp_path, "channels.yaml", 'a: { action: "true", timeout: "soon" }')
    )
    message = timeout_error(build_plan(root, []))
    assert message is not None
    assert "a: timeout must be a positive whole number of seconds" in message


def test_timeout_error_rejects_zero_and_booleans(tmp_path):
    zero = load_tree(
        write_yaml(tmp_path, "zero.yaml", 'a: { action: "true", timeout: 0 }')
    )
    assert timeout_error(build_plan(zero, [])) is not None
    boolean = load_tree(
        write_yaml(tmp_path, "bool.yaml", 'a: { action: "true", timeout: true }')
    )
    assert timeout_error(build_plan(boolean, [])) is not None


def test_timeout_error_accepts_a_valid_and_an_unset_timeout(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            a: { action: "true", timeout: 45 }
            b: { action: "true" }
            """,
        )
    )
    assert timeout_error(build_plan(root, [])) is None


def test_main_reports_a_bad_timeout_as_an_error_even_in_dry_run(tmp_path, capsys):
    path = write_yaml(
        tmp_path, "channels.yaml", 'a: { action: "true", timeout: "soon" }'
    )
    assert main(["--channels", path, "--dry-run"]) == 1
    assert "error:" in capsys.readouterr().err


def test_main_timeout_flag_changes_the_default(tmp_path):
    path = write_yaml(tmp_path, "channels.yaml", 'a: { action: "sleep 5" }')
    assert main(["--channels", path, "--timeout", "1"]) == 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_cli.py -k "timeout" -v`
Expected: FAIL — `ImportError` for `timeout_error`.

- [ ] **Step 3: Write the minimal implementation**

In `skills/orc-publish/scripts/orc_publish/cli.py`, replace `format_plan` entirely with:

```python
def format_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS):
    if not leaves:
        return "(no leaves selected)"
    lines = []
    for leaf in leaves:
        if leaf.action:
            lines.append(f"{leaf.dotted_path}: {leaf.action}")
            lines.append(f"  timeout: {effective_timeout(leaf, default_timeout)}s")
        else:
            lines.append(f"{leaf.dotted_path}: ({NOT_ACTIONABLE})")
        for req in leaf.requirements:
            lines.append(f"  requirement: {req}")
        for issue in leaf.issues:
            lines.append(f"  issue: {issue}")
    return "\n".join(lines)
```

Add this function just below `format_plan`:

```python
def timeout_error(leaves):
    """The first leaf-level `timeout:` that isn't usable, as a message - or None.

    YAML turns `timeout: true` into a bool, and bool is a subclass of int, so it has to be
    rejected explicitly rather than passing the isinstance check.
    """
    for leaf in leaves:
        value = leaf.timeout
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            return (
                f"{leaf.dotted_path}: timeout must be a positive whole number of seconds, "
                f"got {value!r}"
            )
    return None
```

In `main`, add the flag alongside the existing arguments:

```python
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
```

Then, in `main`, replace this block:

```python
    print(format_plan(leaves), flush=True)

    if args.dry_run:
        return 0

    results = execute_plan(leaves)
```

with:

```python
    bad_timeout = timeout_error(leaves)
    if bad_timeout:
        print(f"error: {bad_timeout}", file=sys.stderr, flush=True)
        return 1

    print(format_plan(leaves, default_timeout=args.timeout), flush=True)

    if args.dry_run:
        return 0

    results = execute_plan(leaves, default_timeout=args.timeout)
```

- [ ] **Step 4: Run the whole suite to verify it passes**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS, all tests.

- [ ] **Step 5: Document it in the skill**

In `skills/orc-publish/SKILL.md`, append two bullets to the `## Notes` section:

```markdown
- Every action runs under a timeout — a leaf's own `timeout:` (seconds) if it sets one, otherwise
  600 seconds. `--timeout <seconds>` changes that default for a whole run; a leaf's own value
  still wins over it. The dry-run plan prints each actionable leaf's effective timeout, so it is
  visible in the Step 2 list before you confirm anything.
- A leaf reported as `timed out` is distinct from one reported as `failed`, and the distinction is
  worth relaying exactly. Because actions run with their output captured, a command waiting on
  stdin for a passphrase produces no visible prompt at all — a timeout is often the only signal
  that something is waiting on input rather than working.
- A channel leaf with no `action:` reports as `(known channel, not yet actionable)` and is never
  attempted. That is a real, deliberate state — a target the project knows about but has no
  publish mechanism for yet — not a misconfiguration to fix.
```

- [ ] **Step 6: Run the suite once more and commit**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS, all tests.

```bash
git add skills/orc-publish/scripts/orc_publish/cli.py skills/orc-publish/scripts/tests/test_cli.py skills/orc-publish/SKILL.md
git commit -m "$(cat <<'EOF'
orc-publish: --timeout override, timeout validation, and a visible limit

--timeout moves the default for a whole run without overriding a leaf
that deliberately set a tighter one. A non-integer, zero, or boolean
timeout: reports as a clean error instead of a traceback, including in
dry-run. The dry-run plan now shows each actionable leaf's effective
timeout, so it sits in the same list the user confirms.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: The `**One-time setup:**` marker and its check-then-ask rule

Spec part A. Pure prose across two skills. No script, no test suite — verified by the scenarios in
task 6.

**Files:**
- Modify: `skills/release-checklist/SKILL.md`
- Modify: `skills/orc-release/SKILL.md`

**Interfaces:**
- Consumes: nothing.
- Produces: the `**One-time setup:**` convention, referenced by task 6's VERIFICATION scenario.

- [ ] **Step 1: Add the marker to `release-checklist`**

In `skills/release-checklist/SKILL.md`, under `### Optional markers a step can carry`, change the
opening sentence from:

```
Four optional prose markers. They are read by `/orc-release` when it drives the checklist, but
```

to:

```
Five optional prose markers. They are read by `/orc-release` when it drives the checklist, but
```

and change `**All four are optional; a document` to `**All five are optional; a document`.

Then add this bullet at the end of that marker list, after the `**Irreversible**` bullet:

```markdown
- **One-time setup** — `**One-time setup:** <what it is, and what it is scoped to — per machine,
  per account, per project>` for something done once and then never again: registering a store
  name, submitting an app for review, creating a signing key, adding a per-machine config file.
  Write it inside the step that needs it, not in a separate section of its own.

  A one-time-setup block **must state how to tell it is already in place** — a real command, or a
  real observation — held to the same standard as `**Preconditions:**` above: specific and
  checkable, not generic. Without that, a runner has nothing to test and is reduced to asking
  blind, and a reader coming back six months later can't tell whether they already did it.
  Follow the check with the setup commands themselves.
```

- [ ] **Step 2: Add the rule to `/orc-release`**

In `skills/orc-release/SKILL.md`, in `## Step 3: Walk the steps in order`, inside item 2's
(`**Carry it out:**`) bullet list, add this bullet immediately after the existing
`Marked **performed by hand**` bullet (note the runner's own wording is lowercase there):

```markdown
   - Carrying a **One-time setup:** block → run **only its check**, never its setup commands.
     See "One-time setup blocks" below.
```

Then insert this section immediately after item 5 of that numbered list (before the
`If any \`run.py\` command` paragraph):

```markdown
### One-time setup blocks

A step may carry a `**One-time setup:**` block — something done once and then never again:
registering a store name, submitting an app for review, creating a signing key, adding a
per-machine config file. It always states how to tell whether it is already in place.

1. **Run only that check.** It is read-only by construction. Never run the setup commands to find
   out whether they were needed.
2. **Check passes** → the setup is already there. Say so, and carry on with the rest of the step.
3. **Check fails** → **stop.** Name exactly what is missing, in the document's own words, and ask
   whether the user wants it set up now — asking whatever the setup itself needs (which account,
   which key, which store name). Only run the setup commands once they say yes.

**Never run a setup command unprompted, and never treat a failed check as a step failure you can
resolve on your own initiative. Standing up a distribution channel is always something the user
asks for directly.**

Two real reasons this is a hard rule and not a preference:
- A store-name registration succeeds exactly once. Running it blindly on the next release fails,
  and halts a release on a step that was already fine.
- A Flathub submission is a pull request other people review over days. It is not a command that
  completes inside a release, and it must never be opened as a side effect of one.

Setup state is deliberately **not** recorded in the release cursor. Setup is per-machine and
per-account; the cursor is per-release. A stored "setup done" flag would be confidently wrong the
first time a release is cut from somewhere else — which a check that reads the real world cannot
be.
```

- [ ] **Step 3: Verify the two documents agree**

Run: `grep -n "One-time setup" skills/release-checklist/SKILL.md skills/orc-release/SKILL.md`
Expected: the marker name appears in both files, spelled identically as `**One-time setup:**`.

Run: `grep -c "Five optional prose markers" skills/release-checklist/SKILL.md`
Expected: `1` — and no remaining `Four optional` or `All four are optional` anywhere:
`grep -n "Four optional\|All four" skills/release-checklist/SKILL.md` must print nothing.

- [ ] **Step 4: Commit**

```bash
git add skills/release-checklist/SKILL.md skills/orc-release/SKILL.md
git commit -m "$(cat <<'EOF'
release-checklist: a One-time setup marker; orc-release checks, never sets up

Nothing in Orclab modelled the one-time, account-gated step that has to
happen before a channel can be published to at all - registering a store
name, submitting an app for review, creating a signing key. Orcshot's own
RELEASING.md had already invented the convention twice, inconsistently,
which is the tell that it belonged in the skill.

The marker must carry a checkable "how to tell it's already in place".
/orc-release runs only that check: passing, it moves on; failing, it
stops and asks. Setup commands never run unprompted - standing up a
distribution channel is always something the user asks for directly.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Verification scenarios, backlog, changelog, version

Release bookkeeping. Ends the branch.

**Files:**
- Modify: `VERIFICATION.md` (append three scenarios before `## Recording the result`)
- Modify: `BACKLOG.md` (#11 resolution layered on; #12 note)
- Modify: `CHANGELOG.md` (new `0.11.0` section at the top, below the intro)
- Modify: `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` — **via `/orc-version`,
  never by hand** (see BACKLOG #13: every hand-edited bump so far has skipped the tag)

**Interfaces:**
- Consumes: everything from tasks 1-5.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Add the verification scenarios**

In `VERIFICATION.md`, insert immediately before `## Recording the result`:

````markdown
## Scenario 40: a one-time-setup check that passes is not re-run

1. In a throwaway scratch directory, create a synthetic `RELEASING.md`. Its commands are written
   inline rather than in fenced blocks, so the whole file stays a single, unambiguous fence-free
   document — `/orc-release` warns about unclosed fences for good reason.

   ```markdown
   # Cutting a test release

   ## 1. Set up the store

   **One-time setup:** registering the store name, once per account.

   Check whether it is already done: `test -f already-registered`

   If it is not, register it: `touch already-registered && echo REGISTERED-FOR-REAL`

   ## 2. Ship

   Run: `echo shipped`
   ```

   Add a `pyproject.toml` with `[project]`, a `name`, and `version = "0.1.0"`, then
   `touch already-registered`.
2. Run `/orc-release`, proceed past the working-tree report, target `0.2.0`, and let it reach
   step 1.
3. **Expected:** it runs only `test -f already-registered`, reports that the setup is already in
   place, and carries on. It must **not** run the register command — `REGISTERED-FOR-REAL` must
   never appear anywhere in the output.

## Scenario 41: a failing one-time-setup check stops and asks

1. Same scratch directory and `RELEASING.md` as Scenario 40, but `rm -f already-registered` first,
   and clear any release state so the run starts clean.
2. Run `/orc-release` and let it reach step 1.
3. **Expected:** the check fails and it **stops** — naming exactly what is missing, in the
   document's own words, and asking whether you want it set up now. It must not run the register
   command on its own initiative, and must not report the step as a failure it cannot recover
   from.
4. Say no.
5. **Expected:** it does not proceed to step 2, and `already-registered` still does not exist.
6. Re-run, and this time say yes.
7. **Expected:** only now does it run the register command, `REGISTERED-FOR-REAL` appears, and
   `already-registered` exists afterwards.

## Scenario 42: /orc-publish times out a hanging action and reports an un-onboarded channel honestly

1. In a throwaway scratch directory, create `.orclab/publish/channels.yaml`:

   ```yaml
   test:
     hangs:
       action: "sleep 30"
       timeout: 2
     snap: {}
   ```
2. Run `/orc-publish` and read the dry-run list.
3. **Expected:** `test.hangs` shows its action followed by a `timeout: 2s` line; `test.snap` shows
   `(known channel, not yet actionable)` and no timeout line at all.
4. Confirm, and let it run for real.
5. **Expected:** `test.hangs` reports `timed out` — not `failed` — with a detail naming the real
   2s limit and saying the action may be waiting on stdin. `test.snap` reports
   `not attempted (known channel, not yet actionable)`.
6. **Expected:** the run's exit code is non-zero. A timeout is a failing verdict even though its
   status string differs from `failed`.
````

- [ ] **Step 2: Layer the resolution onto BACKLOG #11 and note #12**

In `BACKLOG.md`, change the `## #11:` heading to end with ` (RESOLVED 2026-09-07)`, and append to
the end of that entry, **without altering a word of its existing text**:

```markdown
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
```

Then append to the end of the `## #12:` entry, again without altering its existing text:

```markdown
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
```

- [ ] **Step 3: Add the changelog entry**

In `CHANGELOG.md`, insert immediately below the `All notable changes...` line:

```markdown
## [0.11.0] - 2026-09-07

### Added
- `**One-time setup:**` — a fifth optional marker in `release-checklist`, for the step that
  happens once and then never again (registering a store name, submitting an app for review,
  creating a signing key, a per-machine config file). It must carry a checkable "how to tell it is
  already in place," to the same standard as `**Preconditions:**`.
- `/orc-release`'s rule for that marker: run **only** the check. Passing, say so and carry on;
  failing, stop, name what is missing, and ask whether the user wants it set up — asking whatever
  the setup itself needs. Setup commands never run unprompted. Standing up a distribution channel
  is always something the user asks for directly.
- A `timeout:` key on a `/orc-publish` channel leaf, a 600-second default, and a `--timeout`
  override for a whole run that a leaf's own value still beats. The dry-run plan prints each
  actionable leaf's effective timeout, so it appears in the list the user confirms.

### Changed
- A `/orc-publish` action that hangs now reports `timed out` — a status distinct from `failed` —
  with a detail naming the real limit and saying the action may be waiting on stdin. Because
  actions run with output captured, a passphrase prompt produces no visible prompt at all, so the
  timeout is often the only signal. Closes BACKLOG #11.
- A channel leaf with no `action:` reports as `(known channel, not yet actionable)` instead of
  `(no action set)`, matching the wording the distro tree already used for the same idea. A
  deliberate placeholder for a real but not-yet-onboarded channel no longer reads as an omission.
```

- [ ] **Step 4: Run the full suite and the plugin validator**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS, all tests.

Run: `claude plugin validate .`
Expected: `Validation passed with warnings` — the single known `CLAUDE.md` warning from BACKLOG
#14. Per `CLAUDE.md`, this is **not** evidence the frontmatter is well-formed; it checks manifest
and file layout only. Do not cite it as more than that.

- [ ] **Step 5: Bump the version through `/orc-version`, not by hand**

Invoke `/orc-version 0.11.0`. It updates `.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json`, commits, and tags.

**Do not hand-edit either JSON file.** BACKLOG #13 records that every release so far bypassed
`/orc-version` and that two of them (`v0.5.0`, `v0.7.0`) went untagged as the direct, mechanical
cost. If `/orc-version` fails or misses a file, that is a real finding worth a BACKLOG entry —
report it rather than working around it by hand.

- [ ] **Step 6: Commit the documentation**

```bash
git add VERIFICATION.md BACKLOG.md CHANGELOG.md
git commit -m "$(cat <<'EOF'
v11: verification scenarios, changelog, BACKLOG #11 resolved and #12 noted

Three scenarios: a passing one-time-setup check that must not re-run the
setup, a failing one that must stop and ask, and a /orc-publish run that
times out a hanging leaf while reporting an un-onboarded channel honestly.

#11 gets its resolution layered onto its existing text, answering the
three decisions it asked for by name. #12 gets a note recording that v8
already closed it - v11's own brainstorming pass nearly re-designed it.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

## What this plan deliberately does not do

- **It does not touch Orcshot**, or any other consuming project. No `RELEASING.md` step, no
  `channels.yaml` leaf, no setup guide. Orcshot's BACKLOG #197 stays Orcshot's, and belongs to a
  session centred on that project.
- **It performs no real onboarding.** `snapcraft register`, `snapcraft login`, and a Flathub
  submission are all account-gated and externally reviewed. Part A exists so they are never done
  blindly; running one here would be the exact thing it guards against.
- **It does not settle BACKLOG #14** (`plugin validate --strict` failing on Orclab's own
  `CLAUDE.md`). Step 4 above runs plain `validate`, as everything in this repo already does.
