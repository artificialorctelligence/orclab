# Orclab v7: `/orc-publish` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/orc-publish` to Orclab — a generic command that resolves a project's own
`.orclab/publish/channels.yaml` and `distro.yaml` trees into a concrete list of publish actions,
shows that list before doing anything, executes it, and reports per-leaf results — and bump
Orclab to 0.7.0 with a real `CHANGELOG.md` entry.

**Architecture:** Unlike every prior `/orc-*` command, this ships as a **skill only** —
`skills/orc-publish/SKILL.md` plus a bundled `scripts/` directory — with no separate
`commands/orc-publish.md` file. The first five commands got a `commands/*.md` file because they
predated the Desktop-compatibility discovery (v6); now that we know skills work on both CLI and
Desktop and commands don't work on Desktop at all, a brand-new command has no reason to create a
file that needs a second wrapper just to work everywhere. The tree-walking logic (load YAML,
tell leaf from branch, resolve `shared` cascades, resolve a dotted-path/subtree/exclude selection)
is real Python, not prose — that logic has real bug surface (ambiguous short names, multi-level
cascade merging) that shouldn't be re-derived by an LLM reading YAML by eye each time. The
**confirmation gate is conversational, not code**: the script never blocks on stdin. It has two
modes only — `--dry-run` (resolve + print, never executes) and normal (resolve + print + execute
immediately). `SKILL.md`'s own prose is what enforces "always dry-run first, get an explicit yes
in chat, only then re-invoke for real" — the script is a deterministic tool Claude calls twice,
not an interactive CLI a human types into directly.

**Tech Stack:** Python 3 (stdlib `argparse`/`subprocess`, plus `PyYAML` for parsing — install
locally with `pip install pyyaml pytest` to run tests), pytest for the resolver's test suite,
Markdown for `SKILL.md`, JSON for the plugin manifests.

**Spec:** `docs/superpowers/specs/2026-09-06-orclab-v7-orc-publish-design.md`

## Global Constraints

- Command name: `/orc-publish`. No separate `/orc-distro` command — the distro-scoped query is
  the `--for` flag.
- Storage paths, exact: `.orclab/publish/channels.yaml`, `.orclab/publish/distro.yaml`. YAML, not
  JSON.
- Both trees are generic recursive structures (branch or leaf), no fixed depth, no fixed schema
  beyond the leaf/branch distinction itself. A leaf is any node whose keys are a subset of
  `{action, filename_template, channel, requirements, issues}` — including the empty dict (a
  valid, unset leaf). Anything else is a branch.
- The distro-tree `channel` field is optional — an unset channel is a valid, non-error state
  meaning "known target, not yet actionable," and must never be silently attempted.
- `requirements`/`issues` on any node are lists of links only — never inline content (the
  resolver just carries whatever strings are there; it has no opinion on their content).
- `shared` nodes cascade to descendants by tree position — no explicit `extends` field. A `shared`
  child is never itself walked as a real sibling/leaf.
- Selection language: dotted paths, subtree-select, and `!`-prefixed exclude are the only
  composition primitives. No numbered/positional selection anywhere.
- Short names auto-resolve only when the final path segment is unique across the whole tree;
  otherwise it's a reported ambiguity listing every match's full path, never a silent guess.
- On a mid-run leaf failure, remaining independent leaves still execute; a final per-leaf summary
  (succeeded/failed/not attempted) is always reported. A leaf with no `action` reports "not
  attempted," never silently vanishes from the summary.
- **Zero Orcshot-specific (or any other consuming-project-specific) content may exist in Orclab's
  own repo.** All test fixtures in this plan are synthetic and throwaway.
- Real automated tests are required for the resolver logic (tree loading, selection resolution,
  cascade merging); `VERIFICATION.md` scenarios (hand-run) cover the command's end-to-end
  behavior against a synthetic tree with no-op actions — never a real destination.
- `filename_template` is exposed as leaf data (rendered via a tested pure function) but is **not**
  auto-injected into a leaf's `action` at execution time in this version — there is no generic
  "current version" source in Orclab's own mechanism yet, and wiring one in speculatively would be
  building for a case that doesn't exist. A future leaf's own wrapped `action` is free to read the
  template itself however its own project needs to.

---

## File Structure

```
orclab/
  skills/
    orc-publish/
      SKILL.md                          (new)
      scripts/
        run.py                          (new — entry point, fixes sys.path then calls cli.main)
        orc_publish/
          __init__.py                   (new — empty)
          tree.py                       (new — Node, load_tree, leaf/branch, shared cascade)
          selection.py                  (new — resolve_token, resolve_selection, SelectionError)
          cli.py                        (new — argparse, build_plan, execute_plan, formatting, main)
        tests/
          test_tree.py                  (new)
          test_selection.py             (new)
          test_cli.py                   (new)
  .claude-plugin/
    plugin.json                         (modified: version bump to 0.7.0)
    marketplace.json                    (modified: version bump to 0.7.0)
  CHANGELOG.md                          (modified: new 0.7.0 entry)
  README.md                             (modified: mention /orc-publish)
  VERIFICATION.md                       (modified: new Scenarios 23-26, synthetic fixture tree)
```

---

### Task 1: Tree loading, leaf/branch distinction, `shared` cascade (`tree.py`)

**Files:**
- Create: `skills/orc-publish/scripts/orc_publish/__init__.py`
- Create: `skills/orc-publish/scripts/orc_publish/tree.py`
- Create: `skills/orc-publish/scripts/tests/test_tree.py`

**Interfaces:**
- Produces: `orc_publish.tree.Node` (attributes: `path` (tuple of str), `name` (str, property),
  `dotted_path` (str, property), `is_leaf` (bool), `action`/`filename_template`/`channel`
  (str-or-None, properties, leaf-only), `requirements`/`issues` (list of str, properties,
  cascade-merged), `children()` (generator of `(name, Node)`, skips `shared`), `leaves()`
  (generator of every leaf `Node` beneath and including this one, depth-first), `find(segments)`
  (returns the `Node` at that path beneath this node, or `None`)); `orc_publish.tree.load_tree(path)`
  (reads a YAML file, returns its root `Node`); `orc_publish.tree.LEAF_KEYS` (the frozenset of
  reserved leaf field names).
- Consumes: nothing from other tasks (this is the foundation).

- [ ] **Step 1: Create the package directory and empty `__init__.py`**

```bash
mkdir -p ~/projects/orclab/skills/orc-publish/scripts/orc_publish
mkdir -p ~/projects/orclab/skills/orc-publish/scripts/tests
touch ~/projects/orclab/skills/orc-publish/scripts/orc_publish/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Create `skills/orc-publish/scripts/tests/test_tree.py`:

```python
import textwrap

import pytest

from orc_publish.tree import Node, load_tree


def write_yaml(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(textwrap.dedent(content))
    return str(path)


def test_leaf_detection_by_reserved_keys():
    node = Node(path=("a",), data={"action": "echo hi"})
    assert node.is_leaf


def test_branch_detection_by_non_reserved_keys():
    node = Node(path=(), data={"desktop": {"action": "echo hi"}})
    assert not node.is_leaf


def test_empty_dict_is_a_leaf_with_no_channel():
    node = Node(path=("mint-next", "x11"), data={})
    assert node.is_leaf
    assert node.channel is None


def test_none_data_is_treated_as_empty_leaf():
    node = Node(path=("mint-next", "x11"), data=None)
    assert node.is_leaf
    assert node.channel is None


def test_load_tree_from_yaml_and_find_a_leaf(tmp_path):
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        """
        desktop:
          python:
            linux:
              snap: { action: "echo publish-snap" }
        """,
    )
    root = load_tree(path)
    leaf = root.find(("desktop", "python", "linux", "snap"))
    assert leaf is not None
    assert leaf.is_leaf
    assert leaf.action == "echo publish-snap"
    assert leaf.dotted_path == "desktop.python.linux.snap"


def test_find_returns_none_for_a_missing_path(tmp_path):
    path = write_yaml(tmp_path, "channels.yaml", "desktop: { snap: { action: 'x' } }")
    root = load_tree(path)
    assert root.find(("desktop", "does-not-exist")) is None


def test_leaves_walks_every_real_leaf_depth_first(tmp_path):
    path = write_yaml(
        tmp_path,
        "channels.yaml",
        """
        desktop:
          python:
            linux:
              ppa:
                noble: { action: "echo noble" }
                resolute: { action: "echo resolute" }
              snap: { action: "echo snap" }
        """,
    )
    root = load_tree(path)
    paths = sorted(leaf.dotted_path for leaf in root.leaves())
    assert paths == [
        "desktop.python.linux.ppa.noble",
        "desktop.python.linux.ppa.resolute",
        "desktop.python.linux.snap",
    ]


def test_shared_cascades_into_its_own_siblings_requirements(tmp_path):
    path = write_yaml(
        tmp_path,
        "distro.yaml",
        """
        mint:
          shared:
            requirements: ["cinnamon-desktop"]
          x11: { channel: "desktop.python.linux.ppa.noble" }
          wayland:
            channel: "desktop.python.linux.ppa.noble"
            issues: ["untested"]
        """,
    )
    root = load_tree(path)
    x11 = root.find(("mint", "x11"))
    wayland = root.find(("mint", "wayland"))
    assert x11.requirements == ["cinnamon-desktop"]
    assert wayland.requirements == ["cinnamon-desktop"]
    assert wayland.issues == ["untested"]


def test_shared_cascades_across_multiple_nested_levels(tmp_path):
    path = write_yaml(
        tmp_path,
        "distro.yaml",
        """
        shared:
          requirements: ["universal-baseline"]
        ubuntu:
          shared:
            requirements: ["ubuntu-family-baseline"]
          noble:
            channel: "desktop.python.linux.ppa.noble"
            requirements: ["noble-specific"]
        """,
    )
    root = load_tree(path)
    noble = root.find(("ubuntu", "noble"))
    assert noble.requirements == [
        "universal-baseline",
        "ubuntu-family-baseline",
        "noble-specific",
    ]


def test_shared_is_never_walked_as_a_real_child(tmp_path):
    path = write_yaml(
        tmp_path,
        "distro.yaml",
        """
        mint:
          shared:
            requirements: ["x"]
          x11: { channel: "a.b.c" }
        """,
    )
    root = load_tree(path)
    names = [name for name, _ in root.find(("mint",)).children()]
    assert names == ["x11"]


def test_unset_channel_leaf_has_no_channel(tmp_path):
    path = write_yaml(
        tmp_path,
        "distro.yaml",
        """
        mint-next:
          x11: {}
          wayland:
        """,
    )
    root = load_tree(path)
    assert root.find(("mint-next", "x11")).channel is None
    assert root.find(("mint-next", "wayland")).channel is None
```

- [ ] **Step 3: Run the tests to confirm they fail with an import error**

```bash
cd ~/projects/orclab/skills/orc-publish/scripts
pip install pyyaml pytest  # if not already available
python3 -m pytest tests/test_tree.py -v
```

Expected: `ModuleNotFoundError: No module named 'orc_publish.tree'` (or similar) — `tree.py`
doesn't exist yet.

- [ ] **Step 4: Implement `tree.py`**

Create `skills/orc-publish/scripts/orc_publish/tree.py`:

```python
"""Load and walk Orclab's publish/distro trees.

Both trees share one generic recursive shape: a node is either a *leaf* (its keys are a
subset of LEAF_KEYS) or a *branch* (a map of child name -> child node). There is no fixed
schema beyond that distinction - depth follows whatever a real project actually needs.
"""

import yaml

LEAF_KEYS = frozenset({"action", "filename_template", "channel", "requirements", "issues"})


class Node:
    """A single node in a channel or distro tree."""

    def __init__(self, path, data, shared_requirements=None, shared_issues=None):
        self.path = path
        self._data = data or {}
        self.is_leaf = isinstance(self._data, dict) and set(self._data.keys()) <= LEAF_KEYS
        self._shared_requirements = list(shared_requirements or [])
        self._shared_issues = list(shared_issues or [])

    @property
    def name(self):
        return self.path[-1] if self.path else ""

    @property
    def dotted_path(self):
        return ".".join(self.path)

    @property
    def action(self):
        return self._data.get("action") if self.is_leaf else None

    @property
    def filename_template(self):
        return self._data.get("filename_template") if self.is_leaf else None

    @property
    def channel(self):
        return self._data.get("channel") if self.is_leaf else None

    @property
    def requirements(self):
        own = self._data.get("requirements", []) if self.is_leaf else []
        return self._shared_requirements + list(own)

    @property
    def issues(self):
        own = self._data.get("issues", []) if self.is_leaf else []
        return self._shared_issues + list(own)

    def children(self):
        """Yield (name, Node) for each real child. A 'shared' child is merged into the
        requirements/issues each *other* child inherits, never yielded as a child itself."""
        if self.is_leaf:
            return
        shared_data = self._data.get("shared")
        shared_reqs = list(self._shared_requirements)
        shared_issues = list(self._shared_issues)
        if isinstance(shared_data, dict):
            shared_reqs = shared_reqs + list(shared_data.get("requirements", []))
            shared_issues = shared_issues + list(shared_data.get("issues", []))
        for key, value in self._data.items():
            if key == "shared":
                continue
            yield key, Node(self.path + (key,), value, shared_reqs, shared_issues)

    def leaves(self):
        """Yield every leaf Node reachable beneath (and including) this node, depth-first."""
        if self.is_leaf:
            yield self
            return
        for _, child in self.children():
            yield from child.leaves()

    def find(self, path_segments):
        """Return the Node at path_segments beneath this node, or None if it doesn't exist."""
        node = self
        for segment in path_segments:
            if node.is_leaf:
                return None
            match = None
            for name, child in node.children():
                if name == segment:
                    match = child
                    break
            if match is None:
                return None
            node = match
        return node


def load_tree(yaml_path):
    """Load a channel or distro tree from a YAML file and return its root Node."""
    with open(yaml_path) as f:
        data = yaml.safe_load(f) or {}
    return Node(path=(), data=data)
```

- [ ] **Step 5: Run the tests to confirm they pass**

```bash
cd ~/projects/orclab/skills/orc-publish/scripts
python3 -m pytest tests/test_tree.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
cd ~/projects/orclab
git add skills/orc-publish/scripts/orc_publish/__init__.py \
        skills/orc-publish/scripts/orc_publish/tree.py \
        skills/orc-publish/scripts/tests/test_tree.py
git commit -m "orc-publish: tree loading, leaf/branch distinction, shared cascade"
```

---

### Task 2: Selection resolution (`selection.py`)

**Files:**
- Create: `skills/orc-publish/scripts/orc_publish/selection.py`
- Create: `skills/orc-publish/scripts/tests/test_selection.py`

**Interfaces:**
- Consumes: `orc_publish.tree.Node` (`.path`, `.name`, `.dotted_path`, `.is_leaf`, `.find()`,
  `.leaves()`, `.children()`) and `orc_publish.tree.load_tree` from Task 1.
- Produces: `orc_publish.selection.SelectionError(Exception)`; `resolve_token(root, token)` →
  `Node` (raises `SelectionError` if not found or ambiguous); `resolve_selection(root, tokens)` →
  `list[Node]` sorted by `dotted_path`, the leaves selected by `tokens` (empty `tokens` means
  every leaf in the tree; a `!`-prefixed token excludes).

- [ ] **Step 1: Write the failing tests**

Create `skills/orc-publish/scripts/tests/test_selection.py`:

```python
import textwrap

import pytest

from orc_publish.tree import load_tree
from orc_publish.selection import SelectionError, resolve_selection, resolve_token


def write_yaml(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(textwrap.dedent(content))
    return str(path)


CHANNELS = """
desktop:
  python:
    linux:
      ppa:
        noble: { action: "echo noble" }
        resolute: { action: "echo resolute" }
      snap: { action: "echo snap" }
      flatpak: { action: "echo flatpak" }
"""


def load_channels(tmp_path):
    return load_tree(write_yaml(tmp_path, "channels.yaml", CHANNELS))


def test_no_selection_returns_every_leaf(tmp_path):
    root = load_channels(tmp_path)
    leaves = resolve_selection(root, [])
    assert [leaf.dotted_path for leaf in leaves] == sorted(
        [
            "desktop.python.linux.ppa.noble",
            "desktop.python.linux.ppa.resolute",
            "desktop.python.linux.snap",
            "desktop.python.linux.flatpak",
        ]
    )


def test_full_dotted_path_selects_exactly_one_leaf(tmp_path):
    root = load_channels(tmp_path)
    leaves = resolve_selection(root, ["desktop.python.linux.ppa.noble"])
    assert [leaf.dotted_path for leaf in leaves] == ["desktop.python.linux.ppa.noble"]


def test_subtree_selection_selects_every_leaf_beneath_it(tmp_path):
    root = load_channels(tmp_path)
    leaves = resolve_selection(root, ["desktop.python.linux.ppa"])
    assert sorted(leaf.dotted_path for leaf in leaves) == sorted(
        ["desktop.python.linux.ppa.noble", "desktop.python.linux.ppa.resolute"]
    )


def test_exclude_removes_a_leaf_from_a_broader_selection(tmp_path):
    root = load_channels(tmp_path)
    leaves = resolve_selection(
        root, ["desktop.python.linux", "!desktop.python.linux.snap"]
    )
    paths = sorted(leaf.dotted_path for leaf in leaves)
    assert "desktop.python.linux.snap" not in paths
    assert "desktop.python.linux.flatpak" in paths
    assert "desktop.python.linux.ppa.noble" in paths


def test_exclude_can_remove_a_whole_subtree(tmp_path):
    root = load_channels(tmp_path)
    leaves = resolve_selection(
        root, ["desktop.python.linux", "!desktop.python.linux.ppa"]
    )
    paths = sorted(leaf.dotted_path for leaf in leaves)
    assert paths == sorted(
        ["desktop.python.linux.snap", "desktop.python.linux.flatpak"]
    )


def test_short_name_resolves_when_unique_in_the_tree(tmp_path):
    root = load_channels(tmp_path)
    node = resolve_token(root, "snap")
    assert node.dotted_path == "desktop.python.linux.snap"


def test_short_name_raises_selection_error_when_ambiguous(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            desktop:
              python:
                linux:
                  noble: { action: "echo a" }
            mobile:
              java:
                android:
                  noble: { action: "echo b" }
            """,
        )
    )
    with pytest.raises(SelectionError, match="ambiguous"):
        resolve_token(root, "noble")


def test_unknown_token_raises_selection_error(tmp_path):
    root = load_channels(tmp_path)
    with pytest.raises(SelectionError, match="does not match"):
        resolve_token(root, "does-not-exist")


def test_resolve_selection_raises_for_an_unresolvable_token(tmp_path):
    root = load_channels(tmp_path)
    with pytest.raises(SelectionError):
        resolve_selection(root, ["does-not-exist"])
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd ~/projects/orclab/skills/orc-publish/scripts
python3 -m pytest tests/test_selection.py -v
```

Expected: `ModuleNotFoundError: No module named 'orc_publish.selection'`.

- [ ] **Step 3: Implement `selection.py`**

Create `skills/orc-publish/scripts/orc_publish/selection.py`:

```python
"""Resolve /orc-publish selection expressions (dotted paths, subtree-select, exclude)."""


class SelectionError(Exception):
    """Raised when a selection token can't be resolved, or resolves ambiguously."""


def _all_named_nodes(root):
    """Yield every real Node in the tree (branches and leaves), for short-name lookup."""
    yield root
    if not root.is_leaf:
        for _, child in root.children():
            yield from _all_named_nodes(child)


def resolve_token(root, token):
    """Resolve one dotted-path or short-name token to a Node.

    Raises SelectionError if the token matches nothing, or matches more than one node by
    short name (an exact match on the final path segment).
    """
    segments = tuple(token.split("."))
    node = root.find(segments)
    if node is not None:
        return node

    matches = [n for n in _all_named_nodes(root) if n.path and n.name == token]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        paths = ", ".join(n.dotted_path for n in matches)
        raise SelectionError(f"'{token}' is ambiguous - matches: {paths}")
    raise SelectionError(f"'{token}' does not match any node in the tree")


def resolve_selection(root, tokens):
    """Resolve a list of CLI tokens (some possibly '!'-prefixed) to a sorted list of leaves.

    No tokens means every leaf in the tree. A '!'-prefixed token subtracts every leaf beneath
    it from whatever the non-excluded tokens selected.
    """
    if not tokens:
        return sorted(root.leaves(), key=lambda n: n.dotted_path)

    included = {}
    excluded = {}
    for token in tokens:
        if token.startswith("!"):
            node = resolve_token(root, token[1:])
            for leaf in node.leaves():
                excluded[leaf.dotted_path] = leaf
        else:
            node = resolve_token(root, token)
            for leaf in node.leaves():
                included[leaf.dotted_path] = leaf

    result = {path: leaf for path, leaf in included.items() if path not in excluded}
    return sorted(result.values(), key=lambda n: n.dotted_path)
```

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
cd ~/projects/orclab/skills/orc-publish/scripts
python3 -m pytest tests/test_selection.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/orclab
git add skills/orc-publish/scripts/orc_publish/selection.py \
        skills/orc-publish/scripts/tests/test_selection.py
git commit -m "orc-publish: dotted-path selection with subtree-select and exclude"
```

---

### Task 3: CLI orchestration (`cli.py`, `run.py`)

**Files:**
- Create: `skills/orc-publish/scripts/orc_publish/cli.py`
- Create: `skills/orc-publish/scripts/run.py`
- Create: `skills/orc-publish/scripts/tests/test_cli.py`

**Interfaces:**
- Consumes: `orc_publish.tree.load_tree`, `orc_publish.tree.Node` (Task 1);
  `orc_publish.selection.resolve_selection`, `resolve_token`, `SelectionError` (Task 2).
- Produces: `orc_publish.cli.render_filename(template, version) -> str | None`;
  `build_plan(channel_root, tokens) -> list[Node]`; `format_plan(leaves) -> str`;
  `run_for(distro_root, distro_path) -> str` (raises `SelectionError` if the resolved node isn't
  a single leaf); `execute_plan(leaves) -> list[tuple[Node, str, str]]` (status is `"success"`,
  `"failed"`, or `"not attempted"`; third element is the detail string, empty on success);
  `format_summary(results) -> str`; `main(argv=None) -> int` (exit code).

- [ ] **Step 1: Write the failing tests**

Create `skills/orc-publish/scripts/tests/test_cli.py`:

```python
import textwrap

import pytest

from orc_publish.tree import load_tree
from orc_publish.selection import SelectionError
from orc_publish.cli import (
    build_plan,
    execute_plan,
    format_plan,
    format_summary,
    render_filename,
    run_for,
)


def write_yaml(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(textwrap.dedent(content))
    return str(path)


def test_render_filename_substitutes_version():
    assert render_filename("orcshot_<version>.zip", "1.2.3") == "orcshot_1.2.3.zip"


def test_render_filename_handles_missing_template():
    assert render_filename(None, "1.2.3") is None


def test_format_plan_lists_each_leaf_and_its_action(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            "desktop: { python: { linux: { snap: { action: 'echo publish-snap' } } } }",
        )
    )
    leaves = build_plan(root, [])
    text = format_plan(leaves)
    assert "desktop.python.linux.snap: echo publish-snap" in text


def test_build_plan_raises_selection_error_for_an_unknown_token(tmp_path):
    root = load_tree(write_yaml(tmp_path, "channels.yaml", "a: { action: 'true' }"))
    with pytest.raises(SelectionError):
        build_plan(root, ["does-not-exist"])


def test_execute_plan_continues_past_a_failure_and_reports_each_status(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            a: { action: "true" }
            b: { action: "false" }
            c: { action: "true" }
            """,
        )
    )
    leaves = build_plan(root, [])
    results = execute_plan(leaves)
    statuses = {leaf.dotted_path: status for leaf, status, _ in results}
    assert statuses == {"a": "success", "b": "failed", "c": "success"}


def test_execute_plan_reports_not_attempted_for_a_leaf_with_no_action(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            """
            real: { action: "true" }
            placeholder: {}
            """,
        )
    )
    leaves = build_plan(root, [])
    results = execute_plan(leaves)
    statuses = {leaf.dotted_path: status for leaf, status, _ in results}
    assert statuses["placeholder"] == "not attempted"


def test_format_summary_includes_the_real_failure_detail(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "channels.yaml",
            "b: { action: \"echo failing-thing 1>&2; exit 1\" }",
        )
    )
    leaves = build_plan(root, [])
    results = execute_plan(leaves)
    summary = format_summary(results)
    assert "b: failed" in summary
    assert "failing-thing" in summary


def test_run_for_reports_the_channel_when_set(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "distro.yaml",
            "mint: { x11: { channel: 'desktop.python.linux.ppa.noble' } }",
        )
    )
    assert run_for(root, "mint.x11") == "mint.x11 -> desktop.python.linux.ppa.noble"


def test_run_for_reports_no_channel_when_unset(tmp_path):
    root = load_tree(write_yaml(tmp_path, "distro.yaml", "mint-next: { x11: {} }"))
    result = run_for(root, "mint-next.x11")
    assert "no channel set" in result


def test_run_for_raises_when_the_target_is_a_branch_not_a_leaf(tmp_path):
    root = load_tree(
        write_yaml(
            tmp_path,
            "distro.yaml",
            "mint: { x11: { channel: 'a.b' }, wayland: { channel: 'a.b' } }",
        )
    )
    with pytest.raises(SelectionError):
        run_for(root, "mint")
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd ~/projects/orclab/skills/orc-publish/scripts
python3 -m pytest tests/test_cli.py -v
```

Expected: `ModuleNotFoundError: No module named 'orc_publish.cli'`.

- [ ] **Step 3: Implement `cli.py`**

Create `skills/orc-publish/scripts/orc_publish/cli.py`:

```python
"""/orc-publish CLI: resolve a selection, execute it, and report results.

This module never prompts for confirmation itself - --dry-run resolves and prints only,
normal mode resolves, prints, and executes immediately. The conversational safety gate
("always dry-run first, get an explicit yes, then run for real") lives in SKILL.md, which
calls this script twice: once with --dry-run, once without, once the user has confirmed.
"""

import argparse
import subprocess
import sys

from .selection import SelectionError, resolve_selection, resolve_token
from .tree import load_tree


def render_filename(template, version):
    """Render a leaf's filename_template for a given version string, or None if unset."""
    return template.replace("<version>", version) if template else None


def build_plan(channel_root, tokens):
    """Resolve CLI selection tokens against the channel tree to a list of leaf Nodes."""
    return resolve_selection(channel_root, tokens)


def format_plan(leaves):
    lines = []
    for leaf in leaves:
        action = leaf.action or "(no action set)"
        lines.append(f"{leaf.dotted_path}: {action}")
    return "\n".join(lines)


def run_for(distro_root, distro_path):
    """--for: report which channel path a distro leaf points at, or that none is set."""
    node = resolve_token(distro_root, distro_path)
    if not node.is_leaf:
        raise SelectionError(f"'{distro_path}' is not a single distro target - select a leaf")
    channel = node.channel
    if channel:
        return f"{node.dotted_path} -> {channel}"
    return f"{node.dotted_path}: no channel set (known target, not yet actionable)"


def execute_plan(leaves):
    """Run each leaf's action. An independent failure doesn't stop the remaining leaves.

    Returns a list of (leaf, status, detail) - status is "success", "failed", or
    "not attempted"; detail is the real error text on failure, empty otherwise.
    """
    results = []
    for leaf in leaves:
        if not leaf.action:
            results.append((leaf, "not attempted", "no action set"))
            continue
        try:
            subprocess.run(
                leaf.action, shell=True, check=True, capture_output=True, text=True
            )
            results.append((leaf, "success", ""))
        except subprocess.CalledProcessError as e:
            detail = (e.stderr or "").strip() or str(e)
            results.append((leaf, "failed", detail))
    return results


def format_summary(results):
    lines = []
    for leaf, status, detail in results:
        line = f"{leaf.dotted_path}: {status}"
        if detail:
            line += f" ({detail})"
        lines.append(line)
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="orc-publish")
    parser.add_argument("selection", nargs="*")
    parser.add_argument("--for", dest="for_distro")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--channels", default=".orclab/publish/channels.yaml")
    parser.add_argument("--distro", default=".orclab/publish/distro.yaml")
    args = parser.parse_args(argv)

    if args.for_distro:
        try:
            distro_root = load_tree(args.distro)
            print(run_for(distro_root, args.for_distro))
        except SelectionError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        return 0

    channel_root = load_tree(args.channels)
    try:
        leaves = build_plan(channel_root, args.selection)
    except SelectionError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(format_plan(leaves))

    if args.dry_run:
        return 0

    results = execute_plan(leaves)
    print(format_summary(results))
    return 0 if all(status != "failed" for _, status, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Create the entry-point script**

Create `skills/orc-publish/scripts/run.py`:

```python
#!/usr/bin/env python3
"""Entry point for SKILL.md: puts the orc_publish package on sys.path, then runs its CLI."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orc_publish.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the tests to confirm they pass**

```bash
cd ~/projects/orclab/skills/orc-publish/scripts
python3 -m pytest tests/test_cli.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Manually verify `run.py` works end to end**

```bash
cd /tmp && mkdir -p orc-publish-smoke/.orclab/publish && cd orc-publish-smoke
cat > .orclab/publish/channels.yaml <<'EOF'
desktop:
  python:
    linux:
      snap: { action: "echo would-publish-snap" }
      flatpak: { action: "echo would-publish-flatpak" }
EOF
python3 ~/projects/orclab/skills/orc-publish/scripts/run.py --dry-run
python3 ~/projects/orclab/skills/orc-publish/scripts/run.py
cd ~ && rm -rf /tmp/orc-publish-smoke
```

Expected: the `--dry-run` invocation prints both leaves and their actions and exits 0 without
running anything; the second invocation prints the same plan, then actually runs both `echo`
commands and prints a summary showing both as `success`.

- [ ] **Step 7: Commit**

```bash
cd ~/projects/orclab
git add skills/orc-publish/scripts/orc_publish/cli.py \
        skills/orc-publish/scripts/run.py \
        skills/orc-publish/scripts/tests/test_cli.py
git commit -m "orc-publish: CLI orchestration, execution with per-leaf continue-on-failure"
```

---

### Task 4: `SKILL.md`, version bump, docs, and `VERIFICATION.md` scenarios

**Files:**
- Create: `skills/orc-publish/SKILL.md`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `VERIFICATION.md`

**Interfaces:**
- Consumes: `skills/orc-publish/scripts/run.py` (Task 3) as the script `SKILL.md` instructs
  Claude to invoke via `${CLAUDE_SKILL_DIR}/scripts/run.py`.

- [ ] **Step 1: Write `SKILL.md`**

Create `skills/orc-publish/SKILL.md`:

```markdown
---
name: orc-publish
description: Use when the user explicitly asks to use orc-publish, or types /orc-publish, to push a project's built artifacts to their real distribution destinations (a PPA, the Snap Store, Flathub, npm, etc.) as configured in the project's own .orclab/publish/channels.yaml and distro.yaml.
allowed-tools: Bash(python3 *)
---

# orc-publish

Publishes a project's built artifacts to whatever real destinations it has configured in its own
`.orclab/publish/channels.yaml` (and, for a distro-scoped query, `.orclab/publish/distro.yaml`).
Orclab itself ships no real channel/distro content for any project — only a project that has
populated these two files can actually publish anything.

## Step 0: Confirm the project is actually set up for this

Run:

```
python3 -c "import yaml" && ls .orclab/publish/channels.yaml
```

If `import yaml` fails, tell the user plainly that `PyYAML` isn't installed
(`pip install pyyaml`) and stop. If `channels.yaml` doesn't exist, tell the user this project has
no publish configuration yet and stop — never invent one.

## Step 1: Read `$ARGUMENTS`

- If `$ARGUMENTS` contains `--for <path>`, this is a read-only query — skip straight to running
  the script with `--for <path>` and report its output. Nothing to confirm; nothing executes.
- Otherwise, the rest of `$ARGUMENTS` are selection tokens (dotted paths, optionally
  `!`-prefixed to exclude). Pass them through to the script exactly as given.

## Step 2: Always resolve in dry-run mode first

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py <selection tokens> --dry-run
```

Show the user the exact list this prints — every leaf and its real action, verbatim, not
paraphrased. This is the safety gate. **Never skip straight to execution**, even if the request
sounded confident ("just publish everything," "ship it all").

## Step 3: Get an explicit go-ahead for that specific list

Ask the user to confirm the list from Step 2. A vague "sounds good" earlier in the conversation,
about something else, doesn't count — wait for a clear yes to *this* resolved list.

## Step 4: Execute for real

Once confirmed, run the identical command without `--dry-run`:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/run.py <same selection tokens>
```

Report the exact summary it prints, per leaf: success, failed (with the real error text), or not
attempted. Never paraphrase a failure away, and never claim success for a leaf the summary
doesn't confirm succeeded.

## Notes

- `--for <distro-path>` reporting "no channel set" is normal, not an error — report it as "known
  target, no channel wired yet."
- A selection token that doesn't resolve, or resolves ambiguously, is reported by the script as an
  `error:` line on stderr with a non-zero exit — relay that message plainly rather than guessing
  what the user meant.
```

- [ ] **Step 2: Bump the version and update manifests**

In `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` (both occurrences in the
latter), change `"version": "0.6.0"` to `"version": "0.7.0"`, and append to the shared
description text: `" /orc-publish pushes a project's built artifacts to its own configured
distribution channels."`

- [ ] **Step 3: Add the `CHANGELOG.md` entry**

Add, above the existing `## [0.6.0]` entry:

```markdown
## [0.7.0] - 2026-09-06

### Added
- `/orc-publish` — resolves a project's own `.orclab/publish/channels.yaml` (and, for a
  distro-scoped query via `--for`, `distro.yaml`) into a concrete list of publish actions, shows
  it before doing anything, executes it, and reports per-leaf success/failure/not-attempted.
  Ships as a skill only (no separate `commands/orc-publish.md`) — the first `/orc-*` component
  designed knowing skills already work on both CLI and Desktop, so there's no reason to create a
  commands file that would need its own wrapper just to work everywhere. See
  `docs/superpowers/specs/2026-09-06-orclab-v7-orc-publish-design.md` for the full design,
  including why distro and channel are modeled as two separate trees rather than one.
- Orclab's own repo ships zero real channel/distro content for any project, Orcshot included —
  populating a real project's `.orclab/publish/` trees is a separate follow-on task.
```

- [ ] **Step 4: Update `README.md`**

Add a bullet to the Commands section (matching the existing style, e.g. after the `/orc-git`
bullet):

```markdown
- **/orc-publish** — push a project's built artifacts to its own configured distribution
  channels (PPA, Snap Store, Flathub, npm, etc.), resolved from `.orclab/publish/channels.yaml`
  and `distro.yaml`. Ships as a skill only — see `CLAUDE.md` for why.
```

Update the Status line to append `+ v7 (\`/orc-publish\`)` after the v6 mention.

- [ ] **Step 5: Add `VERIFICATION.md` scenarios**

Add after the existing Scenario 22:

```markdown
## Scenario 23: /orc-publish resolves and dry-runs a synthetic tree without executing anything

1. In a throwaway scratch directory (never Orclab's own repo, never a real project), create
   `.orclab/publish/channels.yaml`:
   ```yaml
   desktop:
     python:
       linux:
         snap: { action: "echo would-publish-snap" }
         flatpak: { action: "echo would-publish-flatpak" }
   ```
2. Run `/orc-publish --dry-run`.
3. **Expected:** both leaves and their real actions are printed; neither `echo` command actually
   runs (confirm no output beyond the printed plan itself).

## Scenario 24: /orc-publish executes after confirmation, with a real per-leaf summary

1. Using the same synthetic tree as Scenario 23, ask Claude to run `/orc-publish`.
2. **Expected:** Claude shows the dry-run plan first and asks for confirmation before running
   anything — it must not execute on the first pass.
3. Confirm.
4. **Expected:** both `echo` commands actually run, and Claude reports a summary showing both
   leaves as `success`.

## Scenario 25: /orc-publish continues past an independent failure and reports it honestly

1. Add a third leaf to the synthetic tree: `broken: { action: "exit 1" }`.
2. Run `/orc-publish` (or `/orc-publish desktop.python.linux broken` to include it explicitly)
   and confirm.
3. **Expected:** the working leaves still report `success`; `broken` reports `failed`; nothing is
   silently dropped from the summary, and the failure isn't paraphrased away.

## Scenario 26: /orc-publish --for reports an unset channel plainly, never as an error

1. Create `.orclab/publish/distro.yaml` in the same scratch directory:
   ```yaml
   mint-next:
     x11: {}
   ```
2. Run `/orc-publish --for mint-next.x11`.
3. **Expected:** reports "no channel set (known target, not yet actionable)" — a normal report,
   not an error, and nothing executes.
```

- [ ] **Step 6: Run the full resolver test suite one more time**

```bash
cd ~/projects/orclab/skills/orc-publish/scripts
python3 -m pytest tests/ -v
```

Expected: all tests across `test_tree.py`, `test_selection.py`, and `test_cli.py` PASS.

- [ ] **Step 7: Commit**

```bash
cd ~/projects/orclab
git add skills/orc-publish/SKILL.md \
        .claude-plugin/plugin.json .claude-plugin/marketplace.json \
        CHANGELOG.md README.md VERIFICATION.md
git commit -m "orc-publish: SKILL.md, bump to 0.7.0, CHANGELOG, README, VERIFICATION scenarios"
```
