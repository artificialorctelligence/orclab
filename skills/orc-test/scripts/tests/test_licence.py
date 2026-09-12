from orc_test import licence


def test_recognises_common_licences(tmp_path):
    (tmp_path / "LICENSE").write_text("MIT License\n\nCopyright (c) 2026 ...")
    assert licence.open_source(tmp_path) == "MIT"
    (tmp_path / "LICENSE").write_text("Apache License\nVersion 2.0, January 2004")
    assert licence.open_source(tmp_path) == "Apache-2.0"
    (tmp_path / "LICENSE").write_text("GNU GENERAL PUBLIC LICENSE\nVersion 3")
    assert licence.open_source(tmp_path) == "GPL"


def test_none_when_missing_or_proprietary(tmp_path):
    assert licence.open_source(tmp_path) is None
    (tmp_path / "LICENSE").write_text("All rights reserved. Proprietary.")
    assert licence.open_source(tmp_path) is None


def test_manifest_field(tmp_path):
    (tmp_path / "package.json").write_text('{"license": "ISC"}')
    assert licence.open_source(tmp_path) == "ISC"
