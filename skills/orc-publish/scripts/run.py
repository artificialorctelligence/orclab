#!/usr/bin/env python3
"""Entry point for SKILL.md: puts the orc_publish package on sys.path, then runs its CLI."""

import os
import sys

_NO_YAML = """Orclab needs PyYAML, which is not installed here.

    pip install --user PyYAML

If pip refuses with "externally-managed-environment", add --break-system-packages - it only
permits writing to your own ~/.local and does not touch system packages, despite the name. On
Debian and Ubuntu, `sudo apt install python3-yaml` is the other way.

Orclab reads its .orclab/*.yaml config with PyYAML; nothing else needs it. A plugin manifest has
no way to declare a Python dependency, so this cannot be installed for you (BACKLOG #84)."""

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from orc_publish.cli import main
except ModuleNotFoundError as missing:      # a bare traceback here helps nobody
    if missing.name != "yaml":
        raise
    sys.exit(_NO_YAML)

if __name__ == "__main__":
    sys.exit(main())
