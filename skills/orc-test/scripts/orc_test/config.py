"""`.orclab/test.yaml` — optional, project-owned. Thresholds and per-language command overrides."""

import pathlib

import yaml

DEFAULTS = {"coverage": 80, "tce": 70, "languages": {}}


def load(root):
    path = pathlib.Path(root) / ".orclab" / "test.yaml"
    cfg = dict(DEFAULTS)
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}
        for k in ("coverage", "tce"):
            if k in data:
                cfg[k] = int(data[k])
        cfg["languages"] = dict(data.get("languages") or {})
    return cfg
