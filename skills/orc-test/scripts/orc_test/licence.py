"""Is this project open source? Read from what the project already declares — never a new
setting. Arcmutate's Kotlin plugin is free only for open source; the day a project closes, its
LICENSE file is what changes, and the next run notices."""

import json
import pathlib
import re

_PATTERNS = [
    ("Apache-2.0", r"Apache License"), ("AGPL", r"AFFERO GENERAL PUBLIC LICENSE"),
    ("LGPL", r"LESSER GENERAL PUBLIC LICENSE"), ("GPL", r"GNU GENERAL PUBLIC LICENSE"),
    ("MPL-2.0", r"Mozilla Public License"), ("MIT", r"\bMIT License\b"),
    ("BSD", r"BSD \d-Clause|Redistribution and use in source and binary forms"),
    ("ISC", r"\bISC License\b"), ("Unlicense", r"This is free and unencumbered software"),
]
_FIELD = re.compile(r"^(Apache-2\.0|AGPL|LGPL|GPL|MPL-2\.0|MIT|BSD|ISC|Unlicense)", re.I)


def open_source(root):
    root = pathlib.Path(root)
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "LICENCE.md", "COPYING"):
        p = root / name
        if p.exists():
            text = p.read_text(errors="replace")
            for label, pat in _PATTERNS:
                if re.search(pat, text, re.I):
                    return label
    pkg = root / "package.json"
    if pkg.exists():
        field = json.loads(pkg.read_text()).get("license", "")
        if (m := _FIELD.match(str(field))):
            return m.group(1)
    py = root / "pyproject.toml"
    if py.exists():
        m = re.search(r'^license\s*=\s*"([^"]+)"', py.read_text(), re.M)
        if m and (f := _FIELD.match(m.group(1))):
            return f.group(1)
    return None
