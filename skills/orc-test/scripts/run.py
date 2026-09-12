#!/usr/bin/env python3
# skills/orc-test/scripts/run.py
"""Entry point for SKILL.md: puts the orc_test package on sys.path, then runs its CLI."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orc_test.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
