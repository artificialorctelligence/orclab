"""Parse a project's RELEASING.md into ordered steps.

RELEASING.md is the single definition of a release's steps - this module only reads it. The
prose conventions this parser extracts (preconditions, performed-by-hand, delegation,
irreversible) are all OPTIONAL: a document using none of them parses fine, with every marker
field left at its default. That backward compatibility is load-bearing, not incidental - real
documents predate the conventions.

`release-checklist` documents one further convention, `**One-time setup:**`, deliberately absent
from that list: its whole behaviour is that the runner reads the step's own prose and asks, so
there is no field for a parser to extract. Expect this list to be shorter than that document's.
"""

import hashlib
import re
from dataclasses import dataclass, field

# "## 3. Security check" - a numbered step. "## Overview" is not a step.
_STEP_HEADING = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$", re.MULTILINE)

# Preconditions can span multiple lines; capture until blank line or next **marker**
_PRECONDITION = re.compile(
    r"\*\*Preconditions?:\*\*\s*(.+?)(?=\n\s*\n|\*\*|$)",
    re.IGNORECASE | re.DOTALL
)
_MANUAL = re.compile(r"\*\*Performed by hand\.?\*\*", re.IGNORECASE)
_IRREVERSIBLE = re.compile(r"\*\*Irreversible\.?\*\*", re.IGNORECASE)
_DELEGATES = re.compile(r"\*\*Run:\*\*\s*(/[\w-]+)", re.IGNORECASE)

# Any heading for body boundary detection
_ANY_HEADING = re.compile(r"^##\s", re.MULTILINE)

# A fence only opens or closes at the start of a line (leading whitespace allowed).
_FENCE_LINE = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def _get_fenced_regions(text):
    """Return list of (start, end) tuples for fenced code blocks (``` or ~~~).

    Fences are anchored to line start (leading whitespace allowed), per CommonMark. Scanning
    for the delimiter at ANY offset is a real bug, not a nicety: a stray ``` used inline in
    ordinary prose opens a fence that swallows the rest of the document, so every following
    step disappears and the runner drives a release that silently skips its own gates.

    The opening fence's character and length are respected when matching the close.
    """
    return _scan_fences(text)[0]


def _scan_fences(text):
    """(regions, line number where an unterminated fence opened or None)."""
    regions = []
    open_start = None
    open_marker = None
    open_line = None
    pos = 0
    for lineno, line in enumerate(text.splitlines(keepends=True), start=1):
        m = _FENCE_LINE.match(line)
        if m:
            marker = m.group(1)
            if open_start is None:
                open_start, open_marker, open_line = pos, marker, lineno
            elif marker[0] == open_marker[0] and len(marker) >= len(open_marker):
                regions.append((open_start, pos + len(line)))
                open_start = None
        pos += len(line)
    if open_start is not None:
        # Unterminated fence: everything after it is code as far as markdown is concerned, so
        # every step below it disappears. unclosed_fence_warning() surfaces that to a human.
        regions.append((open_start, len(text)))
        return regions, open_line
    return regions, None


def unclosed_fence_warning(text):
    """Warn when the document ends inside a fence, or None when it doesn't.

    This is the direct symptom, and it catches what numbering_warning() cannot: a fence left
    open near the end swallows only the trailing steps, so what survives still looks contiguous
    while the release quietly loses its last gates.
    """
    line = _scan_fences(text)[1]
    if line is None:
        return None
    return (
        f"warning: a code fence opened at line {line} is never closed - every step below it is "
        f"being read as code and will not be run; RELEASING.md may be malformed"
    )


def numbering_warning(steps):
    """Warn when step numbers aren't contiguous from 1, or None when they are.

    Warns and never fails - a project may legitimately number oddly, and refusing would strand
    it with no way to run a release at all.
    """
    numbers = [s.number for s in steps]
    if not numbers or numbers == list(range(1, len(numbers) + 1)):
        return None
    return (
        f"warning: found steps {', '.join(str(n) for n in numbers)} - expected contiguous "
        f"numbering from 1; RELEASING.md may be malformed or a code fence may be unclosed"
    )


def _is_in_fenced_block(pos, fenced_regions):
    """Check if a position is inside any fenced block."""
    for start, end in fenced_regions:
        if start <= pos < end:
            return True
    return False


@dataclass
class Step:
    number: int
    title: str
    body: str
    preconditions: list = field(default_factory=list)
    is_manual: bool = False
    delegates_to: str = None
    is_irreversible: bool = False


def parse_steps(text):
    """Return the document's numbered steps, in document order.

    A step's body runs from just after its heading to just before the next heading of any
    kind, so an unnumbered '## Appendix' correctly ends the previous step rather than being
    swallowed into it. Code fences (``` and ~~~) are respected: ## lines inside fenced
    blocks are not treated as headings, and fenced content is preserved in step bodies.
    """
    fenced_regions = _get_fenced_regions(text)

    # Find all step headings that are not inside fenced blocks
    all_step_matches = list(_STEP_HEADING.finditer(text))
    step_matches = [m for m in all_step_matches if not _is_in_fenced_block(m.start(), fenced_regions)]

    steps = []
    for m in step_matches:
        body_start = m.end()
        # Find next ## heading that's not in a fenced block, or use end of text
        body_end = len(text)
        for heading_match in _ANY_HEADING.finditer(text, body_start):
            if not _is_in_fenced_block(heading_match.start(), fenced_regions):
                body_end = heading_match.start()
                break

        body = text[body_start:body_end].strip()

        # Extract preconditions and normalize multi-line text to single-space-joined
        preconditions = [' '.join(p.split()) for p in _PRECONDITION.findall(body)]

        steps.append(
            Step(
                number=int(m.group(1)),
                title=m.group(2).strip(),
                body=body,
                preconditions=preconditions,
                is_manual=bool(_MANUAL.search(body)),
                delegates_to=(_DELEGATES.search(body).group(1) if _DELEGATES.search(body) else None),
                is_irreversible=bool(_IRREVERSIBLE.search(body)),
            )
        )
    return steps


def doc_hash(text):
    """Stable content hash, used to detect a RELEASING.md edited mid-release."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
