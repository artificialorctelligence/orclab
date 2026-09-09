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
