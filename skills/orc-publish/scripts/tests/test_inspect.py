import tarfile
import zipfile

import pytest

from orc_publish.inspect import (
    Finding,
    MAX_REPORTED,
    UnsupportedArchive,
    format_findings,
    inspect_archive,
    unknown_rules,
)

ALL_RULES = ["no-vcs", "no-tool-state", "no-prebuilt-binaries"]


def make_tar(tmp_path, names, name="src.tar.gz"):
    """Build a real .tar.gz containing an empty file at each given path."""
    blank = tmp_path / "blank"
    blank.write_text("")
    path = tmp_path / name
    with tarfile.open(path, "w:gz") as tf:
        for n in names:
            tf.add(blank, arcname=n)
    return path


def make_zip(tmp_path, names, name="src.zip"):
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as zf:
        for n in names:
            zf.writestr(n, "")
    return path


def test_a_clean_archive_trips_nothing(tmp_path):
    archive = make_tar(tmp_path, ["pkg/setup.py", "pkg/src/main.py", "pkg/README.md"])
    assert inspect_archive(archive, ALL_RULES) == []


def test_vcs_directory_is_found(tmp_path):
    archive = make_tar(tmp_path, ["pkg/setup.py", "pkg/.git/config", "pkg/.git/HEAD"])
    findings = inspect_archive(archive, ["no-vcs"])
    assert [f.rule for f in findings] == ["no-vcs"]
    assert sorted(findings[0].entries) == ["pkg/.git/HEAD", "pkg/.git/config"]


def test_tool_state_is_found(tmp_path):
    archive = make_tar(tmp_path, ["pkg/main.py", "pkg/.venv/lib/x.py", "pkg/__pycache__/m.pyc"])
    findings = inspect_archive(archive, ["no-tool-state"])
    assert len(findings[0].entries) == 2


def test_prebuilt_binaries_are_found_by_name(tmp_path):
    archive = make_tar(tmp_path, ["pkg/main.py", "pkg/dist/thing.whl", "pkg/lib/libz.so.1"])
    findings = inspect_archive(archive, ["no-prebuilt-binaries"])
    assert sorted(findings[0].entries) == ["pkg/dist/thing.whl", "pkg/lib/libz.so.1"]


def test_a_component_rule_does_not_match_a_mere_substring(tmp_path):
    # "digital" contains "git" but is not a .git directory; ".gitignore" is a file, not the dir.
    archive = make_tar(tmp_path, ["pkg/digital/x.py", "pkg/.gitignore"])
    assert inspect_archive(archive, ["no-vcs"]) == []


def test_zip_archives_are_inspected_too(tmp_path):
    archive = make_zip(tmp_path, ["pkg/main.py", "pkg/.git/config"])
    findings = inspect_archive(archive, ["no-vcs"])
    assert findings[0].entries == ["pkg/.git/config"]


def test_each_requested_rule_reports_separately(tmp_path):
    archive = make_tar(tmp_path, ["pkg/.git/config", "pkg/dist/thing.whl"])
    findings = inspect_archive(archive, ALL_RULES)
    assert sorted(f.rule for f in findings) == ["no-prebuilt-binaries", "no-vcs"]


def test_an_unreadable_format_raises(tmp_path):
    path = tmp_path / "thing.snap"
    path.write_bytes(b"hsqs not really squashfs but definitely not tar or zip")
    with pytest.raises(UnsupportedArchive):
        inspect_archive(path, ["no-vcs"])


def test_unknown_rule_names_are_reported(tmp_path):
    assert unknown_rules(["no-vcs", "no-such-rule"]) == ["no-such-rule"]
    assert unknown_rules(ALL_RULES) == []


def test_findings_are_capped_but_the_total_is_stated():
    entries = [f"pkg/.git/obj{i}" for i in range(12)]
    text = format_findings([Finding("no-vcs", entries)])
    assert "12 entries" in text
    assert text.count("pkg/.git/obj") == MAX_REPORTED


def test_formatting_names_the_rule():
    assert "no-vcs" in format_findings([Finding("no-vcs", ["a/.git/x"])])
