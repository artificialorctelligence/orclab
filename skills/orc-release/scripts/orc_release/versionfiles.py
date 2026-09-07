"""Read and write a project's version across every file that holds it.

Deliberately per-format, not a generic "detect any manifest" abstraction: each format carries
real syntax whose sloppy write breaks a real build. Formats are added when a real project needs
one. Supported today: pyproject.toml, .claude-plugin/plugin.json, .claude-plugin/marketplace.json,
and debian/changelog (see the changelog section below).

This module is the single owner of version-setting - /orc-release uses it directly, and
/orc-version delegates to it rather than carrying a second implementation.
"""

import json
import os
import re
import tomllib

PYPROJECT = "pyproject.toml"
PLUGIN_JSON = ".claude-plugin/plugin.json"
MARKETPLACE_JSON = ".claude-plugin/marketplace.json"
DEBIAN_CHANGELOG = "debian/changelog"

KNOWN_FORMATS = [PYPROJECT, PLUGIN_JSON, MARKETPLACE_JSON, DEBIAN_CHANGELOG]


def detect(root):
    """Repo-relative paths of every known version-holding file that actually exists."""
    return [rel for rel in KNOWN_FORMATS if os.path.exists(os.path.join(root, rel))]


def _read_text(root, relpath):
    with open(os.path.join(root, relpath)) as f:
        return f.read()


def _write_text(root, relpath, text):
    with open(os.path.join(root, relpath), "w") as f:
        f.write(text)


def read_version(root, relpath):
    """Current version in one file, or None if the file has no version to report."""
    if relpath == PYPROJECT:
        data = tomllib.loads(_read_text(root, relpath))
        return data.get("project", {}).get("version")
    if relpath == PLUGIN_JSON:
        return json.loads(_read_text(root, relpath)).get("version")
    if relpath == MARKETPLACE_JSON:
        plugins = json.loads(_read_text(root, relpath)).get("plugins", [])
        return plugins[0].get("version") if plugins else None
    if relpath == DEBIAN_CHANGELOG:
        return _changelog_current_version(_read_text(root, relpath))
    raise ValueError(f"unsupported version file format: {relpath}")


def write_version(root, relpath, version, **kwargs):
    """Set the version in one file, preserving everything else about it."""
    if relpath == PYPROJECT:
        return _write_pyproject(root, relpath, version)
    if relpath == PLUGIN_JSON:
        data = json.loads(_read_text(root, relpath))
        data["version"] = version
        return _write_text(root, relpath, json.dumps(data, indent=2) + "\n")
    if relpath == MARKETPLACE_JSON:
        data = json.loads(_read_text(root, relpath))
        for plugin in data.get("plugins", []):
            plugin["version"] = version
        return _write_text(root, relpath, json.dumps(data, indent=2) + "\n")
    if relpath == DEBIAN_CHANGELOG:
        return _write_changelog(root, relpath, version, **kwargs)
    raise ValueError(f"unsupported version file format: {relpath}")


def _write_pyproject(root, relpath, version):
    """Replace only [project]'s own version line.

    Targeted regex rather than a TOML round-trip: rewriting the parsed document would reformat
    the file and destroy comments, producing a noisy diff on every release.
    """
    text = _read_text(root, relpath)
    section = re.search(r"^\[project\]\s*$", text, re.MULTILINE)
    if not section:
        raise ValueError(f"{relpath} has no [project] section")
    next_section = re.compile(r"^\[", re.MULTILINE).search(text, section.end())
    end = next_section.start() if next_section else len(text)
    body = text[section.end() : end]
    new_body, count = re.subn(
        r'^(version\s*=\s*)"[^"]*"',
        lambda m: f'{m.group(1)}"{version}"',
        body,
        count=1,
        flags=re.MULTILINE,
    )
    if count == 0:
        raise ValueError(f"{relpath} has no version field in [project]")
    _write_text(root, relpath, text[: section.end()] + new_body + text[end:])


def verify_consistency(root):
    """Confirm every version-holding file agrees. Returns (ok, {relpath: version}).

    Orcshot's own RELEASING.md states why this matters: pyproject.toml and debian/changelog
    "must match, or the built .deb's own version won't line up with the source tree that
    produced it." Nothing verified that until now.
    """
    versions = {}
    for rel in detect(root):
        v = read_version(root, rel)
        if v is not None:
            versions[rel] = v
    return (len(set(versions.values())) <= 1, versions)
