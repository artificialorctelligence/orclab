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

_PRECONDITION = re.compile(r"\*\*Preconditions?:\*\*\s*(.+?)$", re.IGNORECASE | re.MULTILINE)
_MANUAL = re.compile(r"\*\*Performed by hand\.?\*\*", re.IGNORECASE)
_IRREVERSIBLE = re.compile(r"\*\*Irreversible\.?\*\*", re.IGNORECASE)
_DELEGATES = re.compile(r"\*\*Run:\*\*\s*(/[\w-]+)", re.IGNORECASE)


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
    swallowed into it.
    """
    matches = list(_STEP_HEADING.finditer(text))
    steps = []
    for i, m in enumerate(matches):
        body_start = m.end()
        next_heading = re.compile(r"^##\s", re.MULTILINE).search(text, body_start)
        body_end = next_heading.start() if next_heading else len(text)
        body = text[body_start:body_end].strip()
        steps.append(
            Step(
                number=int(m.group(1)),
                title=m.group(2).strip(),
                body=body,
                preconditions=[p.strip() for p in _PRECONDITION.findall(body)],
                is_manual=bool(_MANUAL.search(body)),
                delegates_to=(_DELEGATES.search(body).group(1) if _DELEGATES.search(body) else None),
                is_irreversible=bool(_IRREVERSIBLE.search(body)),
            )
        )
    return steps


def doc_hash(text):
    """Stable content hash, used to detect a RELEASING.md edited mid-release."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
