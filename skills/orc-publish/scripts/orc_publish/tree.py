"""Load and walk Orclab's publish/distro trees.

Both trees share one generic recursive shape: a node is either a *leaf* (its keys are a
subset of LEAF_KEYS) or a *branch* (a map of child name -> child node). There is no fixed
schema beyond that distinction - depth follows whatever a real project actually needs.
"""

import yaml

LEAF_KEYS = frozenset(
    {
        "action", "metrics", "channel", "requirements", "issues", "timeout",
        "prepare", "artifact", "preflight",
    }
)


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
    def metrics(self):
        """A read-only command printing this channel's own published download numbers."""
        return self._data.get("metrics") if self.is_leaf else None

    def command(self, key):
        """The leaf's command under `key` ("action" or "metrics"), or None if unset."""
        return self._data.get(key) if self.is_leaf else None

    @property
    def channel(self):
        return self._data.get("channel") if self.is_leaf else None

    @property
    def timeout(self):
        """The leaf's own timeout in seconds, or None when unset. Not validated here."""
        return self._data.get("timeout") if self.is_leaf else None

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
        """Names of the rule sets that apply. Empty when unset - preflight is opt-in.

        A scalar is read as one rule, not iterated. `preflight: no-vcs` instead of
        `preflight: [no-vcs]` is an easy YAML slip, and a bare list() over a string turns it
        into one "rule" per character - `unknown preflight rule(s): n, o, -, v, c, s`, which
        names neither the mistake nor anything actionable. A non-string scalar (`preflight: 5`)
        raised TypeError out of this property, ahead of every caller's own containment, so one
        malformed leaf aborted the whole run and its healthy siblings never executed. Refusing
        such a leaf is the caller's job; getting there without crashing is this property's.

        The same applies one level down: a list can itself hold a non-string item
        (`preflight: [no-vcs, 5]`) - every element is coerced to str for the same reason a bare
        scalar is, since a caller that does `", ".join(leaf.preflight)` (both the dry-run plan
        and a real refusal message) raises TypeError on the first non-string item, and that
        raise happens ahead of the caller's own per-leaf containment too.
        """
        value = self._data.get("preflight", []) if self.is_leaf else []
        if value is None:
            return []
        if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple, set)):
            return [str(value)]
        return [str(item) for item in value]

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
