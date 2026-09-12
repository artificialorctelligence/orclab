"""Pitest mutations.xml → Mutation. Java and Kotlin both."""

import pathlib
import xml.etree.ElementTree as ET

from .model import Mutation, Survivor

_KILLED = {"KILLED", "TIMED_OUT"}
_ALIVE = {"SURVIVED", "NO_COVERAGE"}


def find(root):
    hits = list(pathlib.Path(root).glob("target/pit-reports/**/mutations.xml")) + \
           list(pathlib.Path(root).glob("build/reports/pitest/**/mutations.xml"))
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def parse(path):
    killed, total, survivors = 0, 0, []
    for m in ET.parse(path).getroot().iter("mutation"):
        status = m.get("status")
        if status in _KILLED:
            killed += 1
            total += 1
        elif status in _ALIVE:
            total += 1
            pkg = m.findtext("mutatedClass", "").rsplit(".", 1)[0].replace(".", "/")
            desc = m.findtext("description", "")
            if status == "NO_COVERAGE":
                desc += " (no test reaches it)"
            survivors.append(Survivor(f"{pkg}/{m.findtext('sourceFile')}", int(m.findtext("lineNumber", "0")), desc))
    return Mutation(killed, total, survivors)
