# hooks/scripts/tests/test_docs.py
"""The user-facing pages under docs/commands/ (spec: 2026-09-13-orclab-v20-command-docs-design.md).
Shape and presence only; a page saying what its command does today is a discipline, not a test."""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
PAGES = sorted((ROOT / "docs" / "commands").glob("*.md"))
HEADINGS = [
    "## What it's for",
    "## What you type",
    "## What it will ask you",
    "## What it changes",
    "## What it will never do without asking",
]


def _headings(text):
    return [line.rstrip() for line in text.splitlines() if line.startswith("## ")]


def test_every_page_has_exactly_the_five_headings_in_order():
    for page in PAGES:
        assert _headings(page.read_text()) == HEADINGS, page.name


def test_every_page_is_a_command_that_exists():
    for page in PAGES:
        assert (ROOT / "skills" / page.stem / "SKILL.md").is_file(), page.name


def test_no_page_points_the_reader_at_the_workshop():
    for page in PAGES:
        text = page.read_text()
        for banned in ["CLAUDE.md", "BACKLOG.md", "SKILL.md", "docs/superpowers"]:
            assert banned not in text, f"{page.name} mentions {banned}"
