"""The Stryker mutation-report JSON (schema v2): StrykerJS, Stryker.NET and dart_mutant all
write it. Score is Stryker's own: killed+timeout over everything that was actually testable."""

import json
import pathlib

from .model import Mutation, Survivor

_KILLED = {"Killed", "Timeout"}
_ALIVE = {"Survived", "NoCoverage"}


def find(out):
    hits = []
    for p in pathlib.Path(out).rglob("*.json"):
        try:
            if "files" in json.loads(p.read_text()):
                hits.append(p)
        except (ValueError, OSError):
            pass
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def parse(path, root):
    data = json.loads(pathlib.Path(path).read_text())
    killed, total, survivors = 0, 0, []
    for file, entry in data.get("files", {}).items():
        for mut in entry.get("mutants", []):
            status = mut.get("status")
            if status in _KILLED:
                killed += 1
                total += 1
            elif status in _ALIVE:
                total += 1
                desc = f"{mut.get('mutatorName')} → {mut.get('replacement', '')}".strip()
                if status == "NoCoverage":
                    desc += " (no test reaches it)"
                survivors.append(Survivor(file, mut["location"]["start"]["line"], desc))
    return Mutation(killed, total, survivors)
