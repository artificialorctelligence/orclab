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
