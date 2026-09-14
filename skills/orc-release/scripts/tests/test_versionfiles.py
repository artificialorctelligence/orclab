import json
import re
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


def test_detect_ignores_a_pyproject_with_no_project_table(tmp_path):
    write(tmp_path, "pyproject.toml", '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n')
    assert detect(str(tmp_path)) == []


def test_detect_finds_a_pyproject_with_a_project_table(tmp_path):
    write(tmp_path, "pyproject.toml", '[project]\nversion = "1.0.0"\n')
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


CHANGELOG = """
    orcshot (0.2.0-1) noble; urgency=medium

      * Adds internationalization.

     -- Orcshot <orc@example.com>  Wed, 26 Aug 2026 21:02:48 -0500

    orcshot (0.1.1-3) noble; urgency=medium

      * Fixes a debconf warning.

     -- Orcshot <orc@example.com>  Sun, 23 Aug 2026 14:45:00 -0500
    """


def test_read_changelog_returns_the_top_entry_version(tmp_path):
    write(tmp_path, "debian/changelog", CHANGELOG)
    assert read_version(str(tmp_path), "debian/changelog") == "0.2.0"


def test_detect_finds_debian_changelog(tmp_path):
    write(tmp_path, "debian/changelog", CHANGELOG)
    assert detect(str(tmp_path)) == ["debian/changelog"]


def test_write_changelog_prepends_a_new_entry(tmp_path):
    p = write(tmp_path, "debian/changelog", CHANGELOG)
    write_version(str(tmp_path), "debian/changelog", "0.3.0", body="* Adds Snap and Flatpak.")
    text = p.read_text()
    assert text.startswith("orcshot (0.3.0-1) noble; urgency=medium")
    assert "orcshot (0.2.0-1) noble; urgency=medium" in text
    assert "Adds Snap and Flatpak." in text


def test_write_changelog_inherits_series_and_maintainer_from_the_previous_entry(tmp_path):
    p = write(
        tmp_path,
        "debian/changelog",
        """
        orcshot (0.2.0-1) jammy; urgency=low

          * Older.

         -- Real Maintainer <real@example.com>  Wed, 26 Aug 2026 21:02:48 -0500
        """,
    )
    write_version(str(tmp_path), "debian/changelog", "0.3.0", body="* New.")
    text = p.read_text()
    assert "orcshot (0.3.0-1) jammy; urgency=low" in text
    assert "-- Real Maintainer <real@example.com>" in text


def test_write_changelog_is_idempotent_for_the_same_version(tmp_path):
    p = write(tmp_path, "debian/changelog", CHANGELOG)
    write_version(str(tmp_path), "debian/changelog", "0.3.0", body="* First.")
    write_version(str(tmp_path), "debian/changelog", "0.3.0", body="* Second.")
    text = p.read_text()
    assert text.count("orcshot (0.3.0-1)") == 1
    assert "Second." in text
    assert "First." not in text


def test_write_changelog_produces_a_parseable_signature_line(tmp_path):
    p = write(tmp_path, "debian/changelog", CHANGELOG)
    write_version(str(tmp_path), "debian/changelog", "0.3.0", body="* New.")
    sig = next(line for line in p.read_text().splitlines() if line.startswith(" -- "))
    # Exactly one leading space, then "-- name <email>", then TWO spaces, then the date.
    assert re.match(r"^ -- .+ <.+>  \w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} [+-]\d{4}$", sig)


def test_write_changelog_honours_an_explicit_debian_revision(tmp_path):
    p = write(tmp_path, "debian/changelog", CHANGELOG)
    write_version(
        str(tmp_path), "debian/changelog", "0.3.0", body="* New.", debian_revision="2"
    )
    assert "orcshot (0.3.0-2) noble" in p.read_text()


def test_write_changelog_requires_a_body(tmp_path):
    write(tmp_path, "debian/changelog", CHANGELOG)
    with pytest.raises(ValueError, match="body"):
        write_version(str(tmp_path), "debian/changelog", "0.3.0")


def test_write_changelog_preserves_the_source_package_name(tmp_path):
    p = write(
        tmp_path,
        "debian/changelog",
        "someotherpkg (1.0.0-1) noble; urgency=medium\n\n  * x\n\n"
        " -- M <m@e.com>  Wed, 26 Aug 2026 21:02:48 -0500\n",
    )
    write_version(str(tmp_path), "debian/changelog", "1.1.0", body="* y")
    assert p.read_text().startswith("someotherpkg (1.1.0-1) noble")


# --- AppStream metainfo -----------------------------------------------------

METAINFO = """
    <?xml version="1.0" encoding="UTF-8"?>
    <component type="desktop-application">
      <id>org.orcshot.Orcshot</id>
      <releases>
        <release version="0.2.0" date="2026-08-26">
          <description>
            <p>Initial Flathub-ready release.</p>
          </description>
        </release>
      </releases>
    </component>
    """


def test_detect_finds_a_metainfo_file_at_the_root(tmp_path):
    write(tmp_path, "org.orcshot.Orcshot.metainfo.xml", METAINFO)
    write(tmp_path, "other.appdata.xml", METAINFO)
    assert detect(str(tmp_path)) == ["org.orcshot.Orcshot.metainfo.xml", "other.appdata.xml"]


def test_read_metainfo_returns_the_newest_release_or_none(tmp_path):
    write(tmp_path, "org.orcshot.Orcshot.metainfo.xml", METAINFO)
    assert read_version(str(tmp_path), "org.orcshot.Orcshot.metainfo.xml") == "0.2.0"
    write(tmp_path, "empty.metainfo.xml", "<component>\n  <releases>\n  </releases>\n</component>\n")
    assert read_version(str(tmp_path), "empty.metainfo.xml") is None


def test_write_metainfo_prepends_a_dated_release_with_the_body_as_bullets(tmp_path):
    p = write(tmp_path, "org.orcshot.Orcshot.metainfo.xml", METAINFO)
    write_version(str(tmp_path), "org.orcshot.Orcshot.metainfo.xml", "0.4.0",
                  body="* Snap & Flatpak.\n* GNOME <Shell> extension.")
    text = p.read_text()
    assert re.search(r'  <releases>\n    <release version="0\.4\.0" date="\d{4}-\d{2}-\d{2}">\n'
                     r'      <description>\n        <ul>\n          <li>Snap &amp; Flatpak\.</li>\n'
                     r'          <li>GNOME &lt;Shell&gt; extension\.</li>\n        </ul>\n'
                     r'      </description>\n    </release>\n    <release version="0\.2\.0"', text)
    assert text.startswith('<?xml version="1.0"') and text.endswith("</component>\n")
    assert read_version(str(tmp_path), "org.orcshot.Orcshot.metainfo.xml") == "0.4.0"


def test_write_metainfo_without_a_body_is_a_bare_release(tmp_path):
    p = write(tmp_path, "org.orcshot.Orcshot.metainfo.xml", METAINFO)
    write_version(str(tmp_path), "org.orcshot.Orcshot.metainfo.xml", "0.4.0")
    assert re.search(r'  <releases>\n    <release version="0\.4\.0" date="[\d-]+"/>\n    <release version="0\.2\.0"',
                     p.read_text())


def test_write_metainfo_is_idempotent_for_the_same_version(tmp_path):
    p = write(tmp_path, "org.orcshot.Orcshot.metainfo.xml", METAINFO)
    write_version(str(tmp_path), "org.orcshot.Orcshot.metainfo.xml", "0.4.0", body="* First.")
    write_version(str(tmp_path), "org.orcshot.Orcshot.metainfo.xml", "0.4.0", body="* Second.")
    text = p.read_text()
    assert text.count('version="0.4.0"') == 1 and "Second." in text and "First." not in text
    assert text.count("<release ") == 2


def test_write_metainfo_into_an_empty_releases_block(tmp_path):
    p = write(tmp_path, "a.metainfo.xml", "<component>\n  <releases>\n  </releases>\n</component>\n")
    write_version(str(tmp_path), "a.metainfo.xml", "1.0.0")
    assert re.fullmatch(r'<component>\n  <releases>\n    <release version="1\.0\.0" date="[\d-]+"/>\n  </releases>\n</component>\n',
                        p.read_text())


def test_write_metainfo_requires_a_releases_block(tmp_path):
    write(tmp_path, "a.metainfo.xml", "<component>\n  <id>x</id>\n</component>\n")
    with pytest.raises(ValueError, match="<releases>"):
        write_version(str(tmp_path), "a.metainfo.xml", "1.0.0")


def test_verify_consistency_includes_the_metainfo(tmp_path):
    write(tmp_path, "pyproject.toml", PYPROJECT)
    write(tmp_path, "org.orcshot.Orcshot.metainfo.xml", METAINFO)
    assert verify_consistency(str(tmp_path))[0] is True
    write_version(str(tmp_path), "pyproject.toml", "0.3.0")
    ok, versions = verify_consistency(str(tmp_path))
    assert ok is False and versions["org.orcshot.Orcshot.metainfo.xml"] == "0.2.0"
