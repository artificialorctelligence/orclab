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


def test_a_scalar_preflight_is_read_as_one_rule_not_split_into_characters():
    """`preflight: no-vcs` instead of `preflight: [no-vcs]` is an easy YAML slip, and a bare
    list() over a string yields one "rule" per character - reported as
    `unknown preflight rule(s): n, o, -, v, c, s`, which names neither the real mistake nor
    anything the reader can act on."""
    node = Node(path=("a",), data={"action": "echo x", "preflight": "no-vcs"})
    assert node.preflight == ["no-vcs"]


def test_a_preflight_that_is_neither_string_nor_list_does_not_raise():
    """`preflight: 5` used to reach list(5) and raise TypeError out of the property itself -
    before any of the callers' own containment, so one malformed leaf killed the whole run and
    its healthy siblings never executed. Refusing that leaf is the caller's job; not crashing
    on the way there is this property's."""
    assert Node(path=("a",), data={"action": "echo x", "preflight": 5}).preflight == ["5"]


def test_a_preflight_list_containing_a_non_string_item_does_not_raise():
    """`preflight: [no-vcs, 5]` is a valid list, so it skipped the scalar-coercion branch
    above and returned list(value) verbatim - keeping the 5 as an int. Every caller that does
    ", ".join(leaf.preflight) (the dry-run plan line and a real refusal message alike) then
    raised TypeError on the first non-string item, ahead of its own per-leaf containment,
    aborting the whole run exactly like the bare-scalar case this property already guards."""
    node = Node(path=("a",), data={"action": "echo x", "preflight": ["no-vcs", 5]})
    assert node.preflight == ["no-vcs", "5"]


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
    leaf = load_tree(str(p)).find(("ppa", "noble"))
    assert leaf.is_leaf
    assert leaf.confirm_command == "python3 scripts/ppa-published.py"
    assert leaf.confirm_url == "https://launchpad.net/~x/+archive/ubuntu/y/+packages"


def test_confirm_may_declare_command_only(tmp_path):
    p = tmp_path / "channels.yaml"
    p.write_text("ppa:\n  noble:\n    action: dput x\n    confirm:\n      command: check.sh\n")
    leaf = load_tree(str(p)).find(("ppa", "noble"))
    assert leaf.confirm_command == "check.sh"
    assert leaf.confirm_url is None


def test_confirm_may_declare_url_only(tmp_path):
    p = tmp_path / "channels.yaml"
    p.write_text("ppa:\n  noble:\n    action: dput x\n    confirm:\n      url: https://example.test/q\n")
    leaf = load_tree(str(p)).find(("ppa", "noble"))
    assert leaf.confirm_command is None
    assert leaf.confirm_url == "https://example.test/q"


def test_a_leaf_without_confirm_reports_none(tmp_path):
    p = tmp_path / "channels.yaml"
    p.write_text("ppa:\n  noble:\n    action: dput x\n")
    leaf = load_tree(str(p)).find(("ppa", "noble"))
    assert leaf.confirm is None
    assert leaf.confirm_command is None
    assert leaf.confirm_url is None


def test_a_malformed_confirm_scalar_does_not_raise(tmp_path):
    # Same reasoning as `preflight`: refusing a malformed leaf is the caller's job. Raising in
    # the property aborts the whole run over one bad leaf, and its healthy siblings never run.
    p = tmp_path / "channels.yaml"
    p.write_text("ppa:\n  noble:\n    action: dput x\n    confirm: true\n")
    leaf = load_tree(str(p)).find(("ppa", "noble"))
    assert leaf.confirm is True
    assert leaf.confirm_command is None
    assert leaf.confirm_url is None
