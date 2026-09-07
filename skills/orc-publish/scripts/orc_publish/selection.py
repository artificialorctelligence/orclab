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
