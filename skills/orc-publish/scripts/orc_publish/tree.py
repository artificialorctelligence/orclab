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
