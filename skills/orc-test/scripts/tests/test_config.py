from orc_test import config


def test_defaults_without_file(tmp_path):
    assert config.load(tmp_path) == {"coverage": 80, "tce": 70, "languages": {}}


def test_file_overrides_thresholds_and_commands(tmp_path):
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text(
        "coverage: 90\nlanguages:\n  python:\n    test: make check\n")
    cfg = config.load(tmp_path)
    assert cfg["coverage"] == 90 and cfg["tce"] == 70
    assert cfg["languages"]["python"]["test"] == "make check"
