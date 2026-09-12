import pytest

from orc_test import config


def test_defaults_without_file(tmp_path):
    assert config.load(tmp_path) == {"coverage": 80, "tce": 70, "languages": {}}


def test_load_returns_independent_languages_dict_each_call(tmp_path):
    first = config.load(tmp_path)
    first["languages"]["python"] = {"test": "pytest"}
    assert config.load(tmp_path)["languages"] == {}


def test_invalid_yaml_raises_bad_config(tmp_path):
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text("coverage: [unclosed")
    with pytest.raises(config.BadConfig):
        config.load(tmp_path)


def test_non_integer_threshold_raises_bad_config(tmp_path):
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text("coverage: many")
    with pytest.raises(config.BadConfig):
        config.load(tmp_path)


def test_non_mapping_top_level_raises_bad_config(tmp_path):
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text("- coverage\n- 80\n")
    with pytest.raises(config.BadConfig, match="top level must be a mapping"):
        config.load(tmp_path)


def test_file_overrides_thresholds_and_commands(tmp_path):
    (tmp_path / ".orclab").mkdir()
    (tmp_path / ".orclab" / "test.yaml").write_text(
        "coverage: 90\nlanguages:\n  python:\n    test: make check\n")
    cfg = config.load(tmp_path)
    assert cfg["coverage"] == 90 and cfg["tce"] == 70
    assert cfg["languages"]["python"]["test"] == "make check"
