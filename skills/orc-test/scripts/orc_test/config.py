"""`.orclab/test.yaml` — optional, project-owned. Thresholds, per-language command overrides,
and the per-checkout container override (v23)."""

import pathlib

import yaml


class BadConfig(Exception):
    """`.orclab/test.yaml` exists but is malformed."""


def load(root):
    path = pathlib.Path(root) / ".orclab" / "test.yaml"
    cfg = {"coverage": 80, "tce": 70, "languages": {}, "container": True, "runner": None}
    if not path.exists():
        return cfg
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        raise BadConfig(f"{path}: invalid YAML ({e})")
    if not isinstance(data, dict):
        raise BadConfig(f"{path}: top level must be a mapping")
    for k in ("coverage", "tce"):
        if k not in data:
            continue
        try:
            cfg[k] = int(data[k])
        except (ValueError, TypeError):
            raise BadConfig(f"{path}: {k!r} must be an integer, got {data[k]!r}")
    cfg["languages"] = dict(data.get("languages") or {})
    cfg["container"] = data.get("container", True) is not False
    runner = data.get("runner")
    if runner is not None and runner not in ("docker", "podman"):
        raise BadConfig(f"{path}: runner must be docker or podman, got {runner!r}")
    cfg["runner"] = runner
    return cfg
