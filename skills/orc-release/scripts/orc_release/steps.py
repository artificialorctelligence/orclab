"""Parse a project's RELEASING.md into ordered steps.

RELEASING.md is the single definition of a release's steps - this module only reads it. The
four prose conventions (preconditions, performed-by-hand, delegation, irreversible) are all
OPTIONAL: a document using none of them parses fine, with every marker field left at its
default. That backward compatibility is load-bearing, not incidental - real documents predate
the conventions.
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


def _get_fenced_regions(text):
    """Return list of (start, end) tuples for fenced code blocks (``` or ~~~).

    Respects opening fence's character and length for matching closing fence.
    """
    regions = []
    i = 0
    while i < len(text):
        # Check for fence start
        if i + 2 < len(text) and text[i:i+3] in ('```', '~~~'):
            fence_char = text[i]
            fence_len = 1
            while i + fence_len < len(text) and text[i + fence_len] == fence_char:
                fence_len += 1

            fence_start = i
            i += fence_len
            # Skip to end of line
            while i < len(text) and text[i] != '\n':
                i += 1
            if i < len(text):
                i += 1  # skip newline

            # Look for closing fence with same character and sufficient length
            found_close = False
            while i < len(text):
                if i + 2 < len(text) and text[i:i+3] in ('```', '~~~'):
                    close_char = text[i]
                    if close_char == fence_char:
                        close_len = 0
                        while i + close_len < len(text) and text[i + close_len] == close_char:
                            close_len += 1
                        if close_len >= fence_len:
                            # Found closing fence
                            regions.append((fence_start, i + close_len))
                            i = i + close_len
                            found_close = True
                            break
                i += 1

            if not found_close:
                # No closing fence found, treat to end of text
                regions.append((fence_start, len(text)))
                i = len(text)
        else:
            i += 1

    return regions


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
