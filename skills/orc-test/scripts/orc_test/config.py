"""`.orclab/test.yaml` — optional, project-owned. Thresholds and per-language command overrides."""

import pathlib

import yaml


class BadConfig(Exception):
    """`.orclab/test.yaml` exists but is malformed."""


def load(root):
    path = pathlib.Path(root) / ".orclab" / "test.yaml"
    cfg = {"coverage": 80, "tce": 70, "languages": {}}
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError as e:
            raise BadConfig(f"{path}: invalid YAML ({e})")
        if not isinstance(data, dict):
            raise BadConfig(f"{path}: top level must be a mapping")
        for k in ("coverage", "tce"):
            if k in data:
                try:
                    cfg[k] = int(data[k])
                except (ValueError, TypeError):
                    raise BadConfig(f"{path}: {k!r} must be an integer, got {data[k]!r}")
        cfg["languages"] = dict(data.get("languages") or {})
    return cfg
