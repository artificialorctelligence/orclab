# Orclab v12: artifact preflight — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop `/orc-publish` irreversibly publishing an artifact nobody looked at — a leaf declares what it publishes and which checks apply, the checks run after the artifact is built and before the irreversible step, and a failure means the publish never happens.

**Architecture:** A new `orc_publish/inspect.py` owns archive reading and rule matching, deliberately separate from `cli.py` which already carries the execution model. Three optional leaf fields (`prepare`, `artifact`, `preflight`) turn `execute_plan`'s single "run the action" into "prepare → inspect → act," and a new `refused` status reports a leaf that never ran because its artifact was wrong.

**Tech Stack:** Python 3.12 stdlib only — `tarfile`, `zipfile`, `fnmatch`, `subprocess`, `argparse`. PyYAML (already a dependency). pytest.

## Global Constraints

- Source of truth: `docs/superpowers/specs/2026-09-07-orclab-v12-artifact-preflight-design.md`.
- **No new dependency.** `tarfile` and `zipfile` are stdlib.
- **Every new leaf field is optional; no existing configuration changes behaviour.** A leaf declaring none of `prepare`/`artifact`/`preflight` behaves exactly as it does today.
- The refusal status string is exactly `refused`, distinct from `failed` and `timed out`.
- A refusal is a **non-zero exit** from `main`, like `failed` and `timed out`.
- `/orc-publish` **continues past** an independent leaf's refusal, exactly as it does for failure and timeout.
- Offending entries in a refusal detail are **capped at the first five, with a total count.**
- **Dry-run never runs `prepare`.**
- The action-shape check **warns, never refuses** — it is a regex over a shell string and will have false positives.
- The size-anomaly rule is **deliberately cut**; do not implement it.
- **Do not touch anything under `~/projects/orcshot`** — another session owns that repo. Build your own fixtures.
- Run the suite with `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`.
- Every commit message ends with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## File Structure

| File | Responsibility | Tasks |
|---|---|---|
| `skills/orc-publish/scripts/orc_publish/inspect.py` | **New.** Archive reading, rule matching, capped finding reports | 1 |
| `skills/orc-publish/scripts/tests/test_inspect.py` | **New.** Inspector tests against real archives built in `tmp_path` | 1 |
| `skills/orc-publish/scripts/orc_publish/tree.py` | Leaf keys and `Node` properties | 2 |
| `skills/orc-publish/scripts/orc_publish/cli.py` | Execution order, `refused`, dry-run behaviour, flags, action-shape warning | 2–5 |
| `skills/orc-publish/scripts/tests/{test_tree,test_cli}.py` | Tests for the above | 2–5 |
| `skills/orc-publish/SKILL.md` | Operator-facing notes | 6 |
| `skills/release-checklist/SKILL.md` | The lint-what-you-ship rule | 6 |
| `VERIFICATION.md`, `BACKLOG.md`, `.claude-plugin/*.json` | Close-out | 7 |

---

### Task 1: The archive inspector

A self-contained module. No CLI coupling, no knowledge of leaves — it takes a path and a list of rule names and returns findings.

**Files:**
- Create: `skills/orc-publish/scripts/orc_publish/inspect.py`
- Test: `skills/orc-publish/scripts/tests/test_inspect.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `RULES` — a dict mapping rule name to `(kind, patterns)`, `kind` being `"component"` or `"name"`
  - `MAX_REPORTED = 5`
  - `class UnsupportedArchive(Exception)`
  - `class Finding` with attributes `rule: str` and `entries: list[str]`
  - `inspect_archive(path, rule_names) -> list[Finding]`
  - `unknown_rules(rule_names) -> list[str]`
  - `format_findings(findings) -> str`

- [ ] **Step 1: Write the failing tests**

Create `skills/orc-publish/scripts/tests/test_inspect.py`:

```python
import tarfile
import zipfile

import pytest

from orc_publish.inspect import (
    Finding,
    MAX_REPORTED,
    UnsupportedArchive,
    format_findings,
    inspect_archive,
    unknown_rules,
)

ALL_RULES = ["no-vcs", "no-tool-state", "no-prebuilt-binaries"]


def make_tar(tmp_path, names, name="src.tar.gz"):
    """Build a real .tar.gz containing an empty file at each given path."""
    blank = tmp_path / "blank"
    blank.write_text("")
    path = tmp_path / name
    with tarfile.open(path, "w:gz") as tf:
        for n in names:
            tf.add(blank, arcname=n)
    return path


def make_zip(tmp_path, names, name="src.zip"):
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as zf:
        for n in names:
            zf.writestr(n, "")
    return path


def test_a_clean_archive_trips_nothing(tmp_path):
    archive = make_tar(tmp_path, ["pkg/setup.py", "pkg/src/main.py", "pkg/README.md"])
    assert inspect_archive(archive, ALL_RULES) == []


def test_vcs_directory_is_found(tmp_path):
    archive = make_tar(tmp_path, ["pkg/setup.py", "pkg/.git/config", "pkg/.git/HEAD"])
    findings = inspect_archive(archive, ["no-vcs"])
    assert [f.rule for f in findings] == ["no-vcs"]
    assert sorted(findings[0].entries) == ["pkg/.git/HEAD", "pkg/.git/config"]


def test_tool_state_is_found(tmp_path):
    archive = make_tar(tmp_path, ["pkg/main.py", "pkg/.venv/lib/x.py", "pkg/__pycache__/m.pyc"])
    findings = inspect_archive(archive, ["no-tool-state"])
    assert len(findings[0].entries) == 2


def test_prebuilt_binaries_are_found_by_name(tmp_path):
    archive = make_tar(tmp_path, ["pkg/main.py", "pkg/dist/thing.whl", "pkg/lib/libz.so.1"])
    findings = inspect_archive(archive, ["no-prebuilt-binaries"])
    assert sorted(findings[0].entries) == ["pkg/dist/thing.whl", "pkg/lib/libz.so.1"]


def test_a_component_rule_does_not_match_a_mere_substring(tmp_path):
    # "digital" contains "git" but is not a .git directory; ".gitignore" is a file, not the dir.
    archive = make_tar(tmp_path, ["pkg/digital/x.py", "pkg/.gitignore"])
    assert inspect_archive(archive, ["no-vcs"]) == []


def test_zip_archives_are_inspected_too(tmp_path):
    archive = make_zip(tmp_path, ["pkg/main.py", "pkg/.git/config"])
    findings = inspect_archive(archive, ["no-vcs"])
    assert findings[0].entries == ["pkg/.git/config"]


def test_each_requested_rule_reports_separately(tmp_path):
    archive = make_tar(tmp_path, ["pkg/.git/config", "pkg/dist/thing.whl"])
    findings = inspect_archive(archive, ALL_RULES)
    assert sorted(f.rule for f in findings) == ["no-prebuilt-binaries", "no-vcs"]


def test_an_unreadable_format_raises(tmp_path):
    path = tmp_path / "thing.snap"
    path.write_bytes(b"hsqs not really squashfs but definitely not tar or zip")
    with pytest.raises(UnsupportedArchive):
        inspect_archive(path, ["no-vcs"])


def test_unknown_rule_names_are_reported(tmp_path):
    assert unknown_rules(["no-vcs", "no-such-rule"]) == ["no-such-rule"]
    assert unknown_rules(ALL_RULES) == []


def test_findings_are_capped_but_the_total_is_stated():
    entries = [f"pkg/.git/obj{i}" for i in range(12)]
    text = format_findings([Finding("no-vcs", entries)])
    assert "12 entries" in text
    assert text.count("pkg/.git/obj") == MAX_REPORTED


def test_formatting_names_the_rule():
    assert "no-vcs" in format_findings([Finding("no-vcs", ["a/.git/x"])])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_inspect.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orc_publish.inspect'`.

- [ ] **Step 3: Write the implementation**

Create `skills/orc-publish/scripts/orc_publish/inspect.py`:

```python
"""Inspect an archive before it is irreversibly published.

Separate from cli.py deliberately: reading archives and matching rules is its own
responsibility, and cli.py already carries the execution model. This module knows nothing
about leaves, channels or subprocesses - it takes a path and rule names, and reports.

Rules are named rather than expressed as raw glob lists in each project's config, because the
rules are the distilled knowledge. They are opt-in per leaf because they cannot be globalised:
a .snap is squashfs and legitimately contains .so files.
"""

import fnmatch
import tarfile
import zipfile

# 3,061 .git entries would bury a summary. Report the first few and state the real total.
MAX_REPORTED = 5

# "component" matches any full path segment; "name" fnmatches the final segment.
RULES = {
    "no-vcs": ("component", (".git", ".hg", ".svn", ".bzr", "CVS")),
    "no-tool-state": (
        "component",
        (
            ".claude", ".orclab", ".hypothesis", ".venv", "venv",
            "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules",
        ),
    ),
    "no-prebuilt-binaries": (
        "name",
        ("*.deb", "*.whl", "*.so", "*.so.*", "*.exe", "*.dll", "*.dylib", "*.pyd"),
    ),
}


class UnsupportedArchive(Exception):
    """The artifact is not in a format this inspector can read."""


class Finding:
    """One rule, and every archive entry that tripped it."""

    def __init__(self, rule, entries):
        self.rule = rule
        self.entries = entries

    def __eq__(self, other):
        return (
            isinstance(other, Finding)
            and self.rule == other.rule
            and self.entries == other.entries
        )

    def __repr__(self):
        return f"Finding({self.rule!r}, {self.entries!r})"


def unknown_rules(rule_names):
    """Rule names that are not real, so a typo in config is reported rather than ignored."""
    return [name for name in rule_names if name not in RULES]


def _archive_entries(path):
    """Every member name in the archive. Raises UnsupportedArchive for anything else."""
    if tarfile.is_tarfile(path):
        with tarfile.open(path) as tf:
            return tf.getnames()
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            return zf.namelist()
    raise UnsupportedArchive(str(path))


def _trips(entry, kind, patterns):
    if kind == "component":
        return any(part in patterns for part in entry.split("/"))
    name = entry.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def inspect_archive(path, rule_names):
    """Return a Finding per tripped rule. An empty list means the archive is clean."""
    entries = _archive_entries(path)
    findings = []
    for rule in rule_names:
        if rule not in RULES:
            continue
        kind, patterns = RULES[rule]
        matched = [e for e in entries if _trips(e, kind, patterns)]
        if matched:
            findings.append(Finding(rule, matched))
    return findings


def format_findings(findings):
    """One line per rule, naming it and the first few offenders with the real total."""
    lines = []
    for finding in findings:
        shown = finding.entries[:MAX_REPORTED]
        lines.append(
            f"{finding.rule}: {len(finding.entries)} entries, first {len(shown)}: "
            + ", ".join(shown)
        )
    return "; ".join(lines)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS, all tests.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-publish/scripts/orc_publish/inspect.py skills/orc-publish/scripts/tests/test_inspect.py
git commit -m "$(cat <<'EOF'
orc-publish: an archive inspector with named rules

Reads tar and zip via stdlib and reports which named rules an archive
trips. Separate module because reading archives is its own responsibility
and cli.py already carries the execution model. Rules are named rather
than per-project glob lists because the rules are the distilled knowledge,
and opt-in because they cannot be globalised - a .snap legitimately
contains .so files.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Leaf fields, and removing the dead one

**Files:**
- Modify: `skills/orc-publish/scripts/orc_publish/tree.py`
- Modify: `skills/orc-publish/scripts/orc_publish/cli.py` (delete `render_filename`)
- Test: `skills/orc-publish/scripts/tests/test_tree.py`, `skills/orc-publish/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Node.prepare`, `Node.artifact`, `Node.preflight` — the first two return the raw string or `None`, `preflight` returns a list (empty when unset). `Node.filename_template` and `cli.render_filename` **cease to exist**.

- [ ] **Step 1: Write the failing tests**

Append to `skills/orc-publish/scripts/tests/test_tree.py`:

```python
def test_leaf_exposes_prepare_artifact_and_preflight():
    node = Node(
        path=("a",),
        data={
            "action": "echo publish",
            "prepare": "echo build",
            "artifact": "../thing.tar.xz",
            "preflight": ["no-vcs"],
        },
    )
    assert node.prepare == "echo build"
    assert node.artifact == "../thing.tar.xz"
    assert node.preflight == ["no-vcs"]


def test_the_new_fields_default_to_none_and_empty():
    node = Node(path=("a",), data={"action": "echo publish"})
    assert node.prepare is None
    assert node.artifact is None
    assert node.preflight == []


def test_a_node_holding_only_the_new_fields_is_still_a_leaf():
    assert Node(path=("a",), data={"artifact": "x.tar", "preflight": ["no-vcs"]}).is_leaf


def test_filename_template_is_gone():
    node = Node(path=("a",), data={"action": "echo hi"})
    assert not hasattr(node, "filename_template")
```

In `skills/orc-publish/scripts/tests/test_cli.py`, **delete** the two `render_filename` tests — `test_render_filename_substitutes_version` and `test_render_filename_handles_missing_template` — and remove `render_filename` from the `from orc_publish.cli import (...)` block. Those are the only two; confirm with `grep -n render_filename tests/test_cli.py` before and after.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_tree.py -k "prepare or filename_template or new_fields" -v`
Expected: FAIL — `AttributeError: 'Node' object has no attribute 'prepare'`, and `test_filename_template_is_gone` fails because the attribute still exists.

- [ ] **Step 3: Write the implementation**

In `skills/orc-publish/scripts/orc_publish/tree.py`, replace `LEAF_KEYS` with:

```python
LEAF_KEYS = frozenset(
    {
        "action", "channel", "requirements", "issues", "timeout",
        "prepare", "artifact", "preflight",
    }
)
```

Delete the `filename_template` property entirely and add, beside `timeout`:

```python
    @property
    def prepare(self):
        """A command run before the preflight gate - local, reversible work. None when unset."""
        return self._data.get("prepare") if self.is_leaf else None

    @property
    def artifact(self):
        """The archive path to inspect. Shell-expanded at execution, like `action`."""
        return self._data.get("artifact") if self.is_leaf else None

    @property
    def preflight(self):
        """Names of the rule sets that apply. Empty when unset - preflight is opt-in."""
        return list(self._data.get("preflight", [])) if self.is_leaf else []
```

In `skills/orc-publish/scripts/orc_publish/cli.py`, delete the `render_filename` function outright.

- [ ] **Step 4: Run the whole suite**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS. If anything still imports `render_filename`, the collection error names it.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-publish/scripts/orc_publish/tree.py skills/orc-publish/scripts/orc_publish/cli.py skills/orc-publish/scripts/tests/test_tree.py skills/orc-publish/scripts/tests/test_cli.py
git commit -m "$(cat <<'EOF'
orc-publish: prepare, artifact and preflight leaf fields

Adds the three optional fields preflight needs, all defaulting to
absent so no existing configuration changes behaviour.

Removes filename_template and render_filename, shipped dead in v7 - in
LEAF_KEYS, parsed, unit-tested, and never called from the main flow.
artifact: supersedes what it was for, and leaving a dead field that looks
like it names the published file beside a live one that does is a trap.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Execution order, the `refused` status, and the override

**Files:**
- Modify: `skills/orc-publish/scripts/orc_publish/cli.py`
- Test: `skills/orc-publish/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: `inspect_archive`, `unknown_rules`, `format_findings`, `UnsupportedArchive` (Task 1); `Node.prepare/artifact/preflight` (Task 2).
- Produces:
  - `_run(command, limit) -> (returncode, stdout, stderr)` — the single owner of the Popen /
    `start_new_session` / `killpg` block, called by both the `prepare` path and the action path
  - `expand_path(expr, timeout) -> str`
  - `preflight_refusal(leaf, default_timeout) -> str | None` — the refusal detail, or `None` when the leaf passes or declares no preflight
  - `execute_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS, allow_preflight_failure=False)` — unchanged return shape, with `"refused"` as a fifth possible status

- [ ] **Step 1: Write the failing tests**

Append to `skills/orc-publish/scripts/tests/test_cli.py`, adding `expand_path` and `preflight_refusal` to the `from orc_publish.cli import (...)` block:

```python
def _leaf_yaml(tmp_path, extra):
    return write_yaml(tmp_path, "channels.yaml", "a:\n" + extra)


def test_prepare_runs_before_the_action(tmp_path):
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            f'  prepare: "touch {tmp_path}/built"\n'
            f'  action: "test -f {tmp_path}/built && touch {tmp_path}/published"\n',
        )
    )
    results = execute_plan(build_plan(root, []))
    assert results[0][1] == "success"
    assert (tmp_path / "published").exists()


def test_a_failing_prepare_fails_the_leaf_and_the_action_never_runs(tmp_path):
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            '  prepare: "echo build-broke 1>&2; exit 1"\n'
            f'  action: "touch {tmp_path}/published"\n',
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "failed"
    assert "build-broke" in detail
    assert not (tmp_path / "published").exists()


def test_a_prepare_that_hangs_times_out_and_the_action_never_runs(tmp_path):
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            '  prepare: "sleep 30"\n'
            '  timeout: 1\n'
            f'  action: "touch {tmp_path}/published"\n',
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "timed out"
    assert "prepare" in detail
    assert not (tmp_path / "published").exists()


def test_a_dirty_artifact_refuses_and_the_action_never_runs(tmp_path):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    with tarfile.open(tmp_path / "src.tar.gz", "w:gz") as tf:
        tf.add(blank, arcname="pkg/.git/config")
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            f'  artifact: "{tmp_path}/src.tar.gz"\n'
            '  preflight: [no-vcs]\n'
            f'  action: "touch {tmp_path}/published"\n',
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "refused"
    assert "no-vcs" in detail
    assert not (tmp_path / "published").exists()


def test_a_clean_artifact_publishes(tmp_path):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    with tarfile.open(tmp_path / "src.tar.gz", "w:gz") as tf:
        tf.add(blank, arcname="pkg/main.py")
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            f'  artifact: "{tmp_path}/src.tar.gz"\n'
            '  preflight: [no-vcs]\n'
            f'  action: "touch {tmp_path}/published"\n',
        )
    )
    assert execute_plan(build_plan(root, []))[0][1] == "success"
    assert (tmp_path / "published").exists()


def test_a_missing_artifact_refuses(tmp_path):
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            f'  artifact: "{tmp_path}/never-built.tar.gz"\n'
            '  preflight: [no-vcs]\n'
            '  action: "true"\n',
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "refused"
    assert "not found" in detail


def test_an_unreadable_format_refuses_naming_the_format_not_a_rule(tmp_path):
    (tmp_path / "thing.snap").write_bytes(b"hsqs definitely not tar or zip")
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            f'  artifact: "{tmp_path}/thing.snap"\n'
            '  preflight: [no-vcs]\n'
            '  action: "true"\n',
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "refused"
    assert "unsupported" in detail.lower()
    assert "no-vcs" not in detail


def test_an_unknown_rule_name_refuses(tmp_path):
    root = load_tree(
        _leaf_yaml(
            tmp_path,
            f'  artifact: "{tmp_path}/anything.tar.gz"\n'
            '  preflight: [no-such-rule]\n'
            '  action: "true"\n',
        )
    )
    leaf, status, detail = execute_plan(build_plan(root, []))[0]
    assert status == "refused"
    assert "no-such-rule" in detail


def test_a_refused_leaf_does_not_stop_the_next_one(tmp_path):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    with tarfile.open(tmp_path / "src.tar.gz", "w:gz") as tf:
        tf.add(blank, arcname="pkg/.git/config")
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ artifact: "{tmp_path}/src.tar.gz", preflight: [no-vcs], action: "true" }}\n'
        'b: { action: "true" }\n',
    )
    results = execute_plan(build_plan(load_tree(path), []))
    assert {leaf.dotted_path: s for leaf, s, _ in results} == {"a": "refused", "b": "success"}


def test_main_exits_non_zero_on_a_refusal(tmp_path):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    with tarfile.open(tmp_path / "src.tar.gz", "w:gz") as tf:
        tf.add(blank, arcname="pkg/.git/config")
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ artifact: "{tmp_path}/src.tar.gz", preflight: [no-vcs], action: "true" }}\n',
    )
    assert main(["--channels", path]) == 1


def test_the_override_publishes_anyway_and_still_reports(tmp_path, capsys):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    with tarfile.open(tmp_path / "src.tar.gz", "w:gz") as tf:
        tf.add(blank, arcname="pkg/.git/config")
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ artifact: "{tmp_path}/src.tar.gz", preflight: [no-vcs], '
        f'action: "touch {tmp_path}/published" }}\n',
    )
    assert main(["--channels", path, "--allow-preflight-failure"]) == 0
    assert (tmp_path / "published").exists()
    assert "no-vcs" in capsys.readouterr().out


def test_expand_path_runs_command_substitution(tmp_path):
    assert expand_path("$(echo hello).tar.xz", 10) == "hello.tar.xz"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_cli.py -k "prepare or refus or artifact or expand_path or override" -v`
Expected: FAIL — `ImportError` for `expand_path`.

- [ ] **Step 3: Write the implementation**

In `skills/orc-publish/scripts/orc_publish/cli.py`, add to the imports:

```python
import pathlib

from .inspect import UnsupportedArchive, format_findings, inspect_archive, unknown_rules
```

Add these two functions just above `execute_plan`:

```python
def expand_path(expr, timeout):
    """Shell-expand an artifact path the same way an action is shell-expanded.

    Double-quoted so command substitution still runs but word splitting does not - a path
    with a space stays one path. Same trust boundary as `action`: it is the project's own
    config, not untrusted input.
    """
    result = subprocess.run(
        ["/bin/sh", "-c", f'printf %s "{expr}"'],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout.strip()


def preflight_refusal(leaf, default_timeout=DEFAULT_TIMEOUT_SECONDS):
    """Why this leaf must not publish, or None if it may.

    Returns None when the leaf declares no preflight - the check is opt-in, and a leaf that
    asks for nothing is not silently held to anything.
    """
    if not leaf.preflight:
        return None
    bad = unknown_rules(leaf.preflight)
    if bad:
        return f"unknown preflight rule(s): {', '.join(bad)}"
    if not leaf.artifact:
        return "preflight is declared but no artifact: is set - nothing to inspect"
    path = expand_path(leaf.artifact, effective_timeout(leaf, default_timeout))
    if not path or not pathlib.Path(path).is_file():
        return f"artifact not found: {path or leaf.artifact}"
    try:
        findings = inspect_archive(path, leaf.preflight)
    except UnsupportedArchive:
        return f"unsupported archive format, cannot inspect: {path}"
    if findings:
        return format_findings(findings)
    return None
```

Then, inside `execute_plan`'s loop, immediately after the `if not leaf.action:` block and before the `limit = ...` line, insert:

```python
        if leaf.prepare:
            try:
                rc, _out, err = _run(leaf.prepare, effective_timeout(leaf, default_timeout))
            except subprocess.TimeoutExpired:
                results.append(
                    (leaf, "timed out", f"prepare timed out after {effective_timeout(leaf, default_timeout)}s")
                )
                continue
            if rc != 0:
                results.append((leaf, "failed", (err or "").strip() or f"prepare exited {rc}"))
                continue

        refusal = preflight_refusal(leaf, default_timeout)
        if refusal and not allow_preflight_failure:
            results.append((leaf, "refused", refusal))
            continue
        if refusal:
            print(f"warning: {leaf.dotted_path}: {refusal}", flush=True)
```

Change `execute_plan`'s signature to:

```python
def execute_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS, allow_preflight_failure=False):
```

**Extract the existing process-group block into one helper rather than writing a second copy.**
`execute_plan` already contains `Popen(..., start_new_session=True)` with the
`except BaseException` / `killpg` / `wait` handler — code that needed two review rounds to get
right, so there must not be two of it. Move it into `_run`, and have **both** the `prepare` path
and the existing action path call it.

Add `_run` just above `preflight_refusal`:

```python
def _run(command, limit):
    """Run one command to completion under `limit` seconds.

    Returns (returncode, stdout, stderr). Raises subprocess.TimeoutExpired, which the caller
    turns into whatever it means in that context. The process starts in its own session and its
    whole group is killed on any exception - a compound shell command forks, so killing only the
    shell orphans the grandchild that is doing the real work. Interrupts take that path too, not
    just timeouts: start_new_session means a Ctrl-C no longer reaches the child by itself.
    """
    with subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, start_new_session=True,
    ) as proc:
        try:
            stdout, stderr = proc.communicate(timeout=limit)
        except BaseException:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            proc.wait()
            raise
        return proc.returncode, stdout, stderr
```

Then rewrite `execute_plan`'s existing action block to call it, so the Popen/killpg code exists
exactly once:

```python
        try:
            returncode, stdout, stderr = _run(leaf.action, limit)
            if returncode != 0:
                raise subprocess.CalledProcessError(
                    returncode, leaf.action, output=stdout, stderr=stderr
                )
            results.append((leaf, "success", (stdout or "").strip()))
        except subprocess.TimeoutExpired as e:
            ...unchanged timeout handling...
        except subprocess.CalledProcessError as e:
            ...unchanged failure handling...
```

**Do not change any of the existing timeout or failure behaviour while doing this** — the detail
strings, the `timed out` clause naming stdin, the partial-output decode, and the exit-code
treatment all stay byte-identical. Both the "output then hang" and "hang with no output" tests, and
both process-group tests, must pass unchanged. If any of them needs editing, stop and report it:
that means the refactor changed behaviour it was only supposed to relocate.

In `main`, add the flag and pass it through:

```python
    parser.add_argument("--allow-preflight-failure", action="store_true")
```

```python
    results = execute_plan(
        leaves,
        default_timeout=args.timeout,
        allow_preflight_failure=args.allow_preflight_failure,
    )
```

And extend the exit-code expression to treat a refusal as failing:

```python
    return 0 if all(
        status not in ("failed", "timed out", "refused") for _, status, _ in results
    ) else 1
```

- [ ] **Step 4: Run the whole suite**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS, all tests.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-publish/scripts/orc_publish/cli.py skills/orc-publish/scripts/tests/test_cli.py
git commit -m "$(cat <<'EOF'
orc-publish: prepare, inspect, then act - and refuse if the artifact is wrong

execute_plan's single "run the action" becomes prepare -> inspect -> act.
A tripped rule reports as `refused`, distinct from `failed` for the same
reason `timed out` is: nothing ran, because what was about to be published
is wrong, and the fix is different. Non-zero exit, and siblings continue.

--allow-preflight-failure downgrades a refusal to a warning for one run and
still prints every finding. It has to be typed; there is no config-level
opt-out, because an irreversible publish over a known-bad artifact should
cost a deliberate keystroke.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Dry-run behaviour

**Files:**
- Modify: `skills/orc-publish/scripts/orc_publish/cli.py`
- Test: `skills/orc-publish/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: `preflight_refusal`, `expand_path` (Task 3).
- Produces: `format_plan(leaves, default_timeout=DEFAULT_TIMEOUT_SECONDS)` gains preflight lines. No signature change.

- [ ] **Step 1: Write the failing tests**

```python
def test_dry_run_never_runs_prepare(tmp_path):
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ prepare: "touch {tmp_path}/built", action: "true" }}\n',
    )
    assert main(["--channels", path, "--dry-run"]) == 0
    assert not (tmp_path / "built").exists()


def test_dry_run_reports_findings_when_the_artifact_already_exists(tmp_path, capsys):
    import tarfile

    blank = tmp_path / "blank"
    blank.write_text("")
    with tarfile.open(tmp_path / "src.tar.gz", "w:gz") as tf:
        tf.add(blank, arcname="pkg/.git/config")
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ artifact: "{tmp_path}/src.tar.gz", preflight: [no-vcs], action: "true" }}\n',
    )
    assert main(["--channels", path, "--dry-run"]) == 0
    assert "no-vcs" in capsys.readouterr().out


def test_dry_run_says_inspection_is_deferred_when_the_artifact_is_not_built_yet(
    tmp_path, capsys
):
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ prepare: "true", artifact: "{tmp_path}/later.tar.gz", '
        'preflight: [no-vcs], action: "true" }\n',
    )
    assert main(["--channels", path, "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "will be inspected" in out
    assert "no-vcs" not in out


def test_dry_run_lists_the_preflight_rules_a_leaf_declares(tmp_path, capsys):
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        f'a: {{ artifact: "{tmp_path}/x.tar.gz", preflight: [no-vcs, no-tool-state], '
        'action: "true" }\n',
    )
    main(["--channels", path, "--dry-run"])
    assert "no-vcs, no-tool-state" in capsys.readouterr().out
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_cli.py -k dry_run -v`
Expected: FAIL — the new assertions find no preflight lines in the plan output.

- [ ] **Step 3: Write the implementation**

In `format_plan`, inside the `if leaf.action:` branch, after the `timeout:` line, add:

```python
            if leaf.preflight:
                lines.append(f"  preflight: {', '.join(leaf.preflight)}")
                if leaf.artifact:
                    path = expand_path(leaf.artifact, effective_timeout(leaf, default_timeout))
                    if path and pathlib.Path(path).is_file():
                        refusal = preflight_refusal(leaf, default_timeout)
                        lines.append(
                            f"  preflight result: {refusal}" if refusal
                            else "  preflight result: clean"
                        )
                    else:
                        lines.append(
                            "  preflight result: artifact not built yet - "
                            "will be inspected after prepare, at execution time"
                        )
```

**Nothing else changes.** `main` already returns before `execute_plan` when `--dry-run` is set, so `prepare` is never reached — the first test is a regression guard on that existing behaviour, not a new code path.

- [ ] **Step 4: Run the whole suite**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS, all tests.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-publish/scripts/orc_publish/cli.py skills/orc-publish/scripts/tests/test_cli.py
git commit -m "$(cat <<'EOF'
orc-publish: show preflight in the dry-run plan

The dry-run gate is where a user decides, so what preflight will do
belongs in the list they confirm. Inspects when the artifact already
exists and says inspection is deferred when it does not.

Dry-run still never runs prepare - it is a real command with real side
effects, and a dry run that builds is not a dry run. The test for that
guards existing behaviour rather than new code.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: The action-shape warning

**Files:**
- Modify: `skills/orc-publish/scripts/orc_publish/cli.py`
- Test: `skills/orc-publish/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `action_shape_warning(leaf) -> str | None`

- [ ] **Step 1: Write the failing tests**

Add `action_shape_warning` to the import block, then:

```python
def _one(tmp_path, action):
    root = load_tree(write_yaml(tmp_path, "c.yaml", f'a: {{ action: "{action}" }}'))
    return build_plan(root, [])[0]


def test_a_build_then_publish_action_warns(tmp_path):
    leaf = _one(tmp_path, "dpkg-buildpackage -S && dput ppa:x ../y.changes")
    warning = action_shape_warning(leaf)
    assert warning is not None
    assert "prepare" in warning


def test_a_bare_publish_action_does_not_warn(tmp_path):
    assert action_shape_warning(_one(tmp_path, "dput ppa:x ../y.changes")) is None


def test_a_bare_build_action_does_not_warn(tmp_path):
    assert action_shape_warning(_one(tmp_path, "dpkg-buildpackage -S")) is None


def test_publish_before_build_does_not_warn(tmp_path):
    # Order matters: only a build *preceding* an irreversible publish is the bad shape.
    assert action_shape_warning(_one(tmp_path, "dput ppa:x f.changes && dpkg-buildpackage -S")) is None


def test_an_action_less_leaf_does_not_warn(tmp_path):
    root = load_tree(write_yaml(tmp_path, "c.yaml", "a: {}"))
    assert action_shape_warning(build_plan(root, [])[0]) is None


def test_the_warning_appears_in_the_dry_run_plan(tmp_path, capsys):
    path = write_yaml(
        tmp_path, "channels.yaml", 'a: { action: "dpkg-buildpackage -S && dput ppa:x f.changes" }'
    )
    main(["--channels", path, "--dry-run"])
    assert "one command" in capsys.readouterr().out
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/test_cli.py -k action_shape -v`
Expected: FAIL — `ImportError` for `action_shape_warning`.

- [ ] **Step 3: Write the implementation**

Add near the other module constants in `cli.py`:

```python
# Heuristics over a shell string, so this warns and never refuses - unlike the content rules,
# which are deterministic checks of real bytes.
PUBLISH_VERBS = (
    "dput", "snapcraft upload", "twine upload", "npm publish",
    "gh release create", "cargo publish",
)
BUILD_VERBS = (
    "dpkg-buildpackage", "debuild", "python -m build", "flatpak-builder", "cargo build",
)
```

And the function, above `format_plan`:

```python
def action_shape_warning(leaf):
    """Warn when one action both builds and irreversibly publishes, so no gate can run between."""
    action = leaf.action or ""
    for publish in PUBLISH_VERBS:
        at = action.find(publish)
        if at == -1:
            continue
        for build in BUILD_VERBS:
            built = action.find(build)
            if built != -1 and built < at:
                return (
                    "action builds and irreversibly publishes in one command - no gate can run "
                    "between them. Split the build into prepare: to enable preflight."
                )
    return None
```

In `format_plan`, inside the `if leaf.action:` branch, after the preflight lines, add:

```python
            warning = action_shape_warning(leaf)
            if warning:
                lines.append(f"  warning: {warning}")
```

- [ ] **Step 4: Run the whole suite**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v`
Expected: PASS, all tests.

- [ ] **Step 5: Commit**

```bash
git add skills/orc-publish/scripts/orc_publish/cli.py skills/orc-publish/scripts/tests/test_cli.py
git commit -m "$(cat <<'EOF'
orc-publish: warn when one action builds and publishes together

An action containing an irreversible publish verb preceded by a build verb
admits no gate between them, which is the shape that made preflight look
impossible in the first place. Reported in the dry-run plan, and it fires
on configurations that have adopted no preflight at all.

Warns, never refuses: it is a regex over a shell string and will have
false positives, unlike the content rules which read real bytes.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Documentation

**Files:**
- Modify: `skills/orc-publish/SKILL.md`
- Modify: `skills/release-checklist/SKILL.md`

**Interfaces:**
- Consumes: everything from Tasks 1–5.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Add the operator notes to `/orc-publish`**

Append to `skills/orc-publish/SKILL.md`'s `## Notes` section:

```markdown
- A leaf may declare `prepare:` (a command run first), `artifact:` (the archive to inspect) and
  `preflight:` (which named rule sets apply). When it does, the order is **prepare → inspect →
  act**, and a tripped rule reports as `timed out`'s sibling status **`refused`**: nothing ran,
  because what was about to be published is wrong. That is a different thing from `failed`, which
  means a command you ran returned non-zero — relay the distinction rather than flattening it.
- `artifact:` must name the **archive itself**, not a manifest that references it. Inspecting a
  `.changes` file instead of the `.tar.xz` it lists would check the wrong thing while reporting
  success.
- The rules are `no-vcs`, `no-tool-state` and `no-prebuilt-binaries`, opt-in per leaf. They cannot
  be global: a `.snap` is squashfs and legitimately contains `.so` files.
- A `preflight:` declared on an archive format the inspector cannot read is **refused**, saying the
  format is unsupported. That is deliberate — a silent pass on an uninspectable artifact is exactly
  the failure preflight exists to prevent, wearing a green tick.
- `--allow-preflight-failure` downgrades refusals to warnings for one run and still prints every
  finding. Never pass it on the user's behalf; an irreversible publish over a known-bad artifact is
  their call to make explicitly.
- A dry-run inspects the artifact if it already exists and says so if it does not. It never runs
  `prepare` — a dry run that builds is not a dry run.
```

- [ ] **Step 2: Add the lint-what-you-ship rule to `release-checklist`**

In `skills/release-checklist/SKILL.md`, immediately after the `### Optional markers a step can carry` section ends and before `## Cross-referencing CI`, add:

```markdown
## Lint the thing you are shipping, not its sibling

A verification step must be pointed at **the artifact the release actually publishes**. This is not
a style preference — it is a real 2026-09-07 incident. A project ran `lintian` on its binary `.deb`
every release and passed clean every time, while the *source* package uploaded in the next step was
the broken one: it carried the repository's own `.git` directory, 1,415 entries in one published
release and 1,882 in the next, plus prebuilt binaries inside a source package.

A checklist that verifies one artifact and ships a different one has a blind spot by construction,
however good either check is. When writing a verification step, name the exact file the publish
step will upload, and check that one.
```

- [ ] **Step 3: Verify both documents read correctly**

Run: `grep -c "refused" skills/orc-publish/SKILL.md` — expect at least 2.
Run: `grep -n "Lint the thing you are shipping" skills/release-checklist/SKILL.md` — expect one match, at heading level `##`.
Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -q` — expect all passing; documentation changes must not have touched code.

- [ ] **Step 4: Commit**

```bash
git add skills/orc-publish/SKILL.md skills/release-checklist/SKILL.md
git commit -m "$(cat <<'EOF'
Document preflight, and the lint-what-you-ship rule

orc-publish gains operator notes for prepare/artifact/preflight, the
refused status and how it differs from failed, why the rules are opt-in,
and why an unreadable format refuses rather than passing.

release-checklist gains the structural half of the same finding: a
verification step must be pointed at the artifact the release actually
publishes. A project linted its .deb clean every release while the source
package it uploaded carried 1,415 then 1,882 .git entries into public
archives.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Verification scenario, backlog, version

**Files:**
- Modify: `VERIFICATION.md`
- Modify: `BACKLOG.md`
- Modify: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` — **via `/orc-version`, never by hand**

**Interfaces:**
- Consumes: everything.
- Produces: nothing.

- [ ] **Step 1: Add the verification scenario**

`VERIFICATION.md`'s scenarios currently run to 44. Insert immediately before `## Recording the result`:

````markdown
## Scenario 45: preflight refuses a dirty artifact before it can be published

Unit tests assert the refusal is produced. This checks the thing they cannot: that an operator
reading the summary understands what happened and why nothing was published.

1. In a throwaway scratch directory, build a deliberately dirty source archive:

   ```bash
   mkdir -p pkg/.git && touch pkg/main.py pkg/.git/config pkg/.git/HEAD
   tar czf dirty.tar.gz pkg
   ```
2. Create `.orclab/publish/channels.yaml`:

   ```yaml
   test:
     dirty:
       artifact: "dirty.tar.gz"
       preflight: [no-vcs]
       action: "touch PUBLISHED"
   ```
3. Run `/orc-publish` and read the dry-run list.
4. **Expected:** `test.dirty` shows its action, its `preflight: no-vcs` line, and a
   `preflight result:` naming `no-vcs`, the real entry count, and the first few offending paths —
   not a wall of every entry.
5. Confirm, and let it run for real.
6. **Expected:** the leaf reports **`refused`**, not `failed`. `PUBLISHED` does **not** exist — the
   action never ran. The run's exit code is non-zero.
7. Re-run with `--allow-preflight-failure`.
8. **Expected:** `PUBLISHED` now exists, the finding is still printed in full, and the exit code is
   zero. The override is loud, not silent.
9. Rebuild the archive without the `.git` directory (`rm -rf pkg/.git && tar czf dirty.tar.gz pkg`)
   and run again without the override.
10. **Expected:** the leaf publishes normally and the dry-run reports `preflight result: clean`.
````

- [ ] **Step 2: Resolve BACKLOG #21**

Add ` (RESOLVED 2026-09-08)` to `#21`'s title line, and append below its existing text:

```markdown
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
```

- [ ] **Step 3: Run everything**

Run: `cd skills/orc-publish/scripts && python3 -m pytest tests/ -v` — all passing.
Run: `cd skills/orc-release/scripts && python3 -m pytest tests/ -q` — all passing, untouched.
Run: `cd hooks/scripts && python3 -m pytest tests/ -q` — all passing, untouched.
Run: `claude plugin validate .claude-plugin/plugin.json` — expect `✔ Validation passed with warnings`, the one known `CLAUDE.md` warning. **Name the file**; the bare form validates the marketplace manifest and checks nothing about the plugin.

- [ ] **Step 4: Commit the documentation**

```bash
git add VERIFICATION.md BACKLOG.md
git commit -m "$(cat <<'EOF'
BACKLOG #21 resolved: preflight, and Scenario 45

Records that this entry's own first framing was wrong - a leaf whose
action builds what it publishes CAN be inspected, because only dput is
irreversible; the real constraint was that one opaque shell string admits
no gate, which prepare: fixes.

Scenario 45 covers what unit tests cannot: that a refusal reads to an
operator as "nothing was published, and here is why."

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: Bump the version through `/orc-version`, not by hand**

Invoke `/orc-version 0.12.0`. It updates both `.claude-plugin/*.json`, prepends the changelog entry, commits, and tags.

**Do not hand-edit either JSON file.** BACKLOG #13 records that every release before v0.11.0 bypassed `/orc-version`, and that two of them went untagged as the direct mechanical cost. If it fails or misses a file, that is a real finding worth an entry — report it rather than working around it.
