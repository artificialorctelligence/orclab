#!/usr/bin/env python3
"""Entry point for SKILL.md: puts the orc_todo package on sys.path, then runs its CLI."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orc_todo.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
