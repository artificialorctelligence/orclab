"""JaCoCo XML → Coverage. Kover (Kotlin) writes the same format."""

import pathlib
import xml.etree.ElementTree as ET

from .model import Coverage

_LOCATIONS = ["target/site/jacoco/jacoco.xml", "build/reports/jacoco/test/jacocoTestReport.xml",
              "build/reports/kover/report.xml"]


def find(root):
    hits = [p for loc in _LOCATIONS if (p := pathlib.Path(root) / loc).exists()]
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def parse(path):
    files = {}
    for pkg in ET.parse(path).getroot().iter("package"):
        for sf in pkg.iter("sourcefile"):
            c = next((c for c in sf.iter("counter") if c.get("type") == "LINE"), None)
            if c is not None:
                covered, missed = int(c.get("covered")), int(c.get("missed"))
                files[f"{pkg.get('name')}/{sf.get('name')}"] = (covered, covered + missed)
    return Coverage(sum(c for c, _ in files.values()), sum(t for _, t in files.values()), files)
