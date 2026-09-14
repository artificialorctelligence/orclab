"""Read and write a project's version across every file that holds it.

Deliberately per-format, not a generic "detect any manifest" abstraction: each format carries
real syntax whose sloppy write breaks a real build. Formats are added when a real project needs
one. Supported today: pyproject.toml, .claude-plugin/plugin.json, .claude-plugin/marketplace.json,
debian/changelog and an AppStream metainfo file (see the two sections below).

This module is the single owner of version-setting - /orc-release uses it directly, and
/orc-version delegates to it rather than carrying a second implementation.
"""

import datetime
import json
import os
import re
import xml.sax.saxutils

import tomllib

PYPROJECT = "pyproject.toml"
PLUGIN_JSON = ".claude-plugin/plugin.json"
MARKETPLACE_JSON = ".claude-plugin/marketplace.json"
DEBIAN_CHANGELOG = "debian/changelog"

METAINFO_SUFFIXES = (".metainfo.xml", ".appdata.xml")   # AppStream: <id>.metainfo.xml, older .appdata.xml

KNOWN_FORMATS = [PYPROJECT, PLUGIN_JSON, MARKETPLACE_JSON, DEBIAN_CHANGELOG]


def detect(root):
    """Repo-relative paths of every known version-holding file that actually exists.

    pyproject.toml only counts if it has a [project] table — one that's only e.g.
    [tool.pytest.ini_options] holds no version, and write_version would raise on it.
    """
    found = []
    for rel in KNOWN_FORMATS:
        if not os.path.exists(os.path.join(root, rel)):
            continue
        if rel == PYPROJECT and "project" not in tomllib.loads(_read_text(root, rel)):
            continue
        found.append(rel)
    # ponytail: root only, where Orcshot keeps its metainfo; walk data/ too when a project puts it there
    found += sorted(f for f in os.listdir(root) if f.endswith(METAINFO_SUFFIXES))
    return found


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
    if relpath.endswith(METAINFO_SUFFIXES):
        m = _MI_RELEASE.search(_read_text(root, relpath))
        return m.group("version") if m else None
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
    if relpath.endswith(METAINFO_SUFFIXES):
        return _write_metainfo(root, relpath, version, **kwargs)
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


# --- debian/changelog -------------------------------------------------------
#
# Structurally unlike every other format here: a log to prepend to, not a field to overwrite.
# Three things this must get right, each a real failure mode rather than a hypothetical:
#   1. Idempotence. Prepending twice for one version leaves two entries for it; a re-run or a
#      resumed release would do exactly that. Guarded by replacing a matching top entry.
#   2. The target series is inherited from the previous entry, never guessed - Launchpad
#      rejects an upload whose series is not one the PPA supports.
#   3. The maintainer is inherited from the previous entry, not read from `git config` - the
#      previous entry is definitionally what the package uses, while git config is whoever
#      happens to be running the command.

import email.utils

_CL_HEADER = re.compile(
    r"^(?P<source>\S+) \((?P<version>[^)]+)\) (?P<series>\S+); urgency=(?P<urgency>\S+)\s*$",
    re.MULTILINE,
)
_CL_SIGNATURE = re.compile(r"^ -- (?P<maintainer>.+?)  (?P<date>.+?)\s*$", re.MULTILINE)


def _changelog_current_version(text):
    """Upstream version of the top entry (the Debian revision suffix stripped)."""
    m = _CL_HEADER.search(text)
    if not m:
        return None
    return m.group("version").rsplit("-", 1)[0]


def _write_changelog(root, relpath, version, body=None, debian_revision="1", **_ignored):
    if not body or not body.strip():
        raise ValueError("a debian/changelog entry requires a body")

    text = _read_text(root, relpath)
    top = _CL_HEADER.search(text)
    if not top:
        raise ValueError(f"{relpath} has no parseable top entry to inherit from")

    source = top.group("source")
    series = top.group("series")
    urgency = top.group("urgency")

    sig = _CL_SIGNATURE.search(text)
    if not sig:
        raise ValueError(f"{relpath} has no parseable signature line to inherit from")
    maintainer = sig.group("maintainer")

    # Idempotence guard: if the top entry is already this version, replace it rather than
    # stacking a duplicate (a resumed or re-run release hits this for real).
    if _changelog_current_version(text) == version:
        next_header = _CL_HEADER.search(text, top.end())
        rest = text[next_header.start() :] if next_header else ""
    else:
        rest = text

    indented = "\n".join(
        ("  " + line.strip()) if line.strip() else "" for line in body.strip().splitlines()
    )
    entry = (
        f"{source} ({version}-{debian_revision}) {series}; urgency={urgency}\n"
        f"\n{indented}\n\n"
        f" -- {maintainer}  {email.utils.formatdate(localtime=True)}\n"
    )
    _write_text(root, relpath, entry + ("\n" + rest.lstrip("\n") if rest.strip() else ""))


# --- AppStream metainfo -----------------------------------------------------
#
# The same shape as debian/changelog - a log to prepend to, newest first - and the same two
# hazards: a re-run must not stack a second entry for one version, and the entry's own date is
# part of the record. Why it matters: Flathub's linter fails a metainfo whose newest <release>
# is not the built version, and Orcshot's RELEASING.md added the entry by hand and missed 0.3.0
# (BACKLOG #6, 2026-09-13). Edited as text, not through an XML parser: a parser rewrites the
# whole file's formatting and drops its comments on the way out.

_MI_RELEASES_OPEN = re.compile(r"^(?P<indent>[ \t]*)<releases>[ \t]*\n", re.MULTILINE)
_MI_RELEASE = re.compile(
    r"^(?P<indent>[ \t]*)<release\b[^>]*?\bversion=\"(?P<version>[^\"]+)\"[^>]*?(?:/>|>.*?</release>)[ \t]*\n?",
    re.MULTILINE | re.DOTALL,
)


def _write_metainfo(root, relpath, version, body=None, **_ignored):
    text = _read_text(root, relpath)
    opened = _MI_RELEASES_OPEN.search(text)
    if not opened:
        raise ValueError(f"{relpath} has no <releases> block to add a release to")
    top = _MI_RELEASE.search(text, opened.end())
    indent = top.group("indent") if top else opened.group("indent") + "  "
    if top and top.group("version") == version:       # idempotence: replace, never stack
        text = text[: top.start()] + text[top.end():]
    date = datetime.date.today().isoformat()
    bullets = [line.strip().lstrip("*-").strip() for line in (body or "").splitlines() if line.strip()]
    if bullets:
        items = "".join(f"{indent}      <li>{xml.sax.saxutils.escape(b)}</li>\n" for b in bullets)
        entry = (f'{indent}<release version="{version}" date="{date}">\n'
                 f"{indent}  <description>\n{indent}    <ul>\n{items}{indent}    </ul>\n"
                 f"{indent}  </description>\n{indent}</release>\n")
    else:
        entry = f'{indent}<release version="{version}" date="{date}"/>\n'
    _write_text(root, relpath, text[: opened.end()] + entry + text[opened.end():])
