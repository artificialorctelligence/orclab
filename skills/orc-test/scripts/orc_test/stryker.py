"""The Stryker mutation-report JSON (schema v2): StrykerJS, Stryker.NET and dart_mutant all
write it. Score is Stryker's own: killed+timeout over everything that was actually testable."""

import json
import pathlib

from .model import Mutation, Survivor

_KILLED = {"Killed", "Timeout"}
_ALIVE = {"Survived", "NoCoverage"}


def find(out):
    hits = [p for p in pathlib.Path(out).rglob("*.json") if _is_report(p)]
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def _is_report(p):
    try:
        return "files" in json.loads(p.read_text())
    except (ValueError, OSError):
        return False


def parse(path, root):
    data = json.loads(pathlib.Path(path).read_text())
    killed, total, survivors = 0, 0, []
    mutants = ((file, mut) for file, entry in data.get("files", {}).items() for mut in entry.get("mutants", []))
    for file, mut in mutants:
        status = mut.get("status")
        if status in _KILLED:
            killed += 1
            total += 1
        elif status in _ALIVE:
            total += 1
            desc = f"{mut.get('mutatorName')} → {mut.get('replacement', '')}".strip()
            desc += " (no test reaches it)" if status == "NoCoverage" else ""
            survivors.append(Survivor(file, mut["location"]["start"]["line"], desc))
    return Mutation(killed, total, survivors)
