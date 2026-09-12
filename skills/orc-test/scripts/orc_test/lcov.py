"""lcov → Coverage. The one reader for every tool that emits lcov: pytest-cov, vitest/jest,
coverlet, dart, nano-coverage."""

import pathlib

from .model import Coverage


def parse(path):
    files, cur, lf, lh, da_hit, da_all = {}, None, None, None, 0, 0
    for raw in pathlib.Path(path).read_text().splitlines():
        line = raw.strip()
        if line.startswith("SF:"):
            cur, lf, lh, da_hit, da_all = line[3:], None, None, 0, 0
        elif line.startswith("DA:"):
            da_all += 1
            da_hit += int(line[3:].split(",")[1]) > 0
        elif line.startswith("LF:"):
            lf = int(line[3:])
        elif line.startswith("LH:"):
            lh = int(line[3:])
        elif line == "end_of_record" and cur is not None:
            files[cur] = (lh, lf) if lf is not None and lh is not None else (da_hit, da_all)
            cur = None
    return Coverage(sum(c for c, _ in files.values()), sum(t for _, t in files.values()), files)
