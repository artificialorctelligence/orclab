"""Inspect an archive before it is irreversibly published.

Separate from cli.py deliberately: reading archives and matching rules is its own
responsibility, and cli.py already carries the execution model. This module knows nothing
about leaves, channels or subprocesses - it takes a path and rule names, and reports.

Rules are named rather than expressed as raw glob lists in each project's config, because the
rules are the distilled knowledge. They are opt-in per leaf because they cannot be globalised:
a .snap is squashfs and legitimately contains .so files.
"""

import fnmatch
import tarfile
import zipfile

# 3,061 .git entries would bury a summary. Report the first few and state the real total.
MAX_REPORTED = 5

# "component" matches any full path segment; "name" fnmatches the final segment.
RULES = {
    "no-vcs": ("component", (".git", ".hg", ".svn", ".bzr", "CVS")),
    "no-tool-state": (
        "component",
        (
            ".claude", ".orclab", ".hypothesis", ".venv", "venv",
            "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules",
        ),
    ),
    "no-prebuilt-binaries": (
        "name",
        ("*.deb", "*.whl", "*.so", "*.so.*", "*.exe", "*.dll", "*.dylib", "*.pyd"),
    ),
}


class UnsupportedArchive(Exception):
    """The artifact is not in a format this inspector can read."""


class Finding:
    """One rule, and every archive entry that tripped it."""

    def __init__(self, rule, entries):
        self.rule = rule
        self.entries = entries

    def __eq__(self, other):
        return (
            isinstance(other, Finding)
            and self.rule == other.rule
            and self.entries == other.entries
        )

    def __repr__(self):
        return f"Finding({self.rule!r}, {self.entries!r})"


def unknown_rules(rule_names):
    """Rule names that are not real, so a typo in config is reported rather than ignored."""
    return [name for name in rule_names if name not in RULES]


def _archive_entries(path):
    """Every member name in the archive. Raises UnsupportedArchive for anything else."""
    if tarfile.is_tarfile(path):
        with tarfile.open(path) as tf:
            return tf.getnames()
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            return zf.namelist()
    raise UnsupportedArchive(str(path))


def _trips(entry, kind, patterns):
    if kind == "component":
        return any(part in patterns for part in entry.split("/"))
    name = entry.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def inspect_archive(path, rule_names):
    """Return a Finding per tripped rule. An empty list means the archive is clean."""
    entries = _archive_entries(path)
    findings = []
    for rule in rule_names:
        if rule not in RULES:
            continue
        kind, patterns = RULES[rule]
        matched = [e for e in entries if _trips(e, kind, patterns)]
        if matched:
            findings.append(Finding(rule, matched))
    return findings


def format_findings(findings):
    """One line per rule, naming it and the first few offenders with the real total."""
    lines = []
    for finding in findings:
        shown = finding.entries[:MAX_REPORTED]
        lines.append(
            f"{finding.rule}: {len(finding.entries)} entries, first {len(shown)}: "
            + ", ".join(shown)
        )
    return "; ".join(lines)
