import json
import textwrap

import pytest

from orc_release.versionfiles import (
    detect,
    read_version,
    verify_consistency,
    write_version,
)


def write(tmp_path, relpath, content):
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip())
    return p


PYPROJECT = """
    [build-system]
    requires = ["setuptools"]

    [project]
    name = "orcshot"
    version = "0.2.0"
    dependencies = []
    """


def test_detect_finds_nothing_in_an_empty_project(tmp_path):
    assert detect(str(tmp_path)) == []


def test_detect_finds_pyproject(tmp_path):
    write(tmp_path, "pyproject.toml", PYPROJECT)
    assert detect(str(tmp_path)) == ["pyproject.toml"]


def test_detect_finds_plugin_manifests(tmp_path):
    write(tmp_path, ".claude-plugin/plugin.json", '{"name": "x", "version": "0.1.0"}')
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        '{"name": "x", "plugins": [{"name": "x", "version": "0.1.0"}]}',
    )
    assert sorted(detect(str(tmp_path))) == [
        ".claude-plugin/marketplace.json",
        ".claude-plugin/plugin.json",
    ]


def test_read_pyproject_version(tmp_path):
    write(tmp_path, "pyproject.toml", PYPROJECT)
    assert read_version(str(tmp_path), "pyproject.toml") == "0.2.0"


def test_write_pyproject_version_preserves_everything_else(tmp_path):
    p = write(tmp_path, "pyproject.toml", PYPROJECT)
    write_version(str(tmp_path), "pyproject.toml", "0.3.0")
    text = p.read_text()
    assert 'version = "0.3.0"' in text
    assert 'name = "orcshot"' in text
    assert "[build-system]" in text
    assert 'requires = ["setuptools"]' in text


def test_write_pyproject_does_not_touch_a_dependency_version_field(tmp_path):
    p = write(
        tmp_path,
        "pyproject.toml",
        """
        [project]
        name = "x"
        version = "0.2.0"

        [tool.other]
        version = "9.9.9"
        """,
    )
    write_version(str(tmp_path), "pyproject.toml", "0.3.0")
    text = p.read_text()
    assert 'version = "0.3.0"' in text
    assert 'version = "9.9.9"' in text


def test_read_and_write_plugin_json(tmp_path):
    write(tmp_path, ".claude-plugin/plugin.json", '{\n  "name": "x",\n  "version": "0.1.0"\n}\n')
    assert read_version(str(tmp_path), ".claude-plugin/plugin.json") == "0.1.0"
    write_version(str(tmp_path), ".claude-plugin/plugin.json", "0.2.0")
    data = json.loads((tmp_path / ".claude-plugin/plugin.json").read_text())
    assert data["version"] == "0.2.0"
    assert data["name"] == "x"


def test_read_and_write_marketplace_json_nested_version(tmp_path):
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        '{\n  "name": "x",\n  "plugins": [{"name": "x", "version": "0.1.0"}]\n}\n',
    )
    assert read_version(str(tmp_path), ".claude-plugin/marketplace.json") == "0.1.0"
    write_version(str(tmp_path), ".claude-plugin/marketplace.json", "0.2.0")
    data = json.loads((tmp_path / ".claude-plugin/marketplace.json").read_text())
    assert data["plugins"][0]["version"] == "0.2.0"


def test_write_marketplace_adds_a_missing_version_field(tmp_path):
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        '{\n  "name": "x",\n  "plugins": [{"name": "x"}]\n}\n',
    )
    write_version(str(tmp_path), ".claude-plugin/marketplace.json", "0.2.0")
    data = json.loads((tmp_path / ".claude-plugin/marketplace.json").read_text())
    assert data["plugins"][0]["version"] == "0.2.0"


def test_verify_consistency_passes_when_all_files_agree(tmp_path):
    write(tmp_path, "pyproject.toml", PYPROJECT)
    write(tmp_path, ".claude-plugin/plugin.json", '{"name": "x", "version": "0.2.0"}')
    ok, versions = verify_consistency(str(tmp_path))
    assert ok is True
    assert set(versions.values()) == {"0.2.0"}


def test_verify_consistency_detects_a_real_mismatch(tmp_path):
    write(tmp_path, "pyproject.toml", PYPROJECT)
    write(tmp_path, ".claude-plugin/plugin.json", '{"name": "x", "version": "9.9.9"}')
    ok, versions = verify_consistency(str(tmp_path))
    assert ok is False
    assert versions["pyproject.toml"] == "0.2.0"
    assert versions[".claude-plugin/plugin.json"] == "9.9.9"


def test_verify_consistency_on_a_project_with_no_version_files(tmp_path):
    ok, versions = verify_consistency(str(tmp_path))
    assert ok is True
    assert versions == {}


def test_unknown_format_raises_rather_than_guessing(tmp_path):
    with pytest.raises(ValueError, match="unsupported"):
        read_version(str(tmp_path), "Cargo.toml")
