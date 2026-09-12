import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
LANG_DIR = ROOT / "skills" / "orc-test" / "languages"
REQUIRED = ["## Detect", "## Run", "## Coverage", "## Mutation (TCE)", "## Test lint",
            "## Caveats", "Researched on:", "Last real run:"]
EXPECTED = {"python", "javascript", "java", "kotlin"}   # each language task adds its key here


@pytest.mark.parametrize("key", sorted(EXPECTED))
def test_language_file_has_every_section(key):
    text = (LANG_DIR / f"{key}.md").read_text()
    for section in REQUIRED:
        assert section in text, f"{key}.md lacks {section!r}"
    assert re.search(r"Researched on: 2026-\d\d-\d\d", text)
