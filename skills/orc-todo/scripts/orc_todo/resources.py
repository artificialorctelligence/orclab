"""The two numbered resources, described rather than special-cased.

One allocator serves both files. What differs between them is captured here as data - the
heading shape, how a number is recognised, and where a new section goes. A second
implementation for the second file would be the duplication BACKLOG #22 warns about in a
different costume.

RELEASING.md is deliberately absent. Its step numbers are positional, not identities:
release-checklist requires renumbering when a step is inserted mid-document, so there is no
"next number" to hand out. Its real gap - prose cross-references surviving a renumber - is a
check in orc_release/steps.py instead.
"""

import dataclasses
import re


@dataclasses.dataclass(frozen=True)
class Resource:
    key: str
    filename: str
    heading: str          # format string with {n} and {title}
    number_re: str        # must anchor at line start; group 1 is the number
    anchor: str | None    # insert before this line; None or absent means append
    canonical_text: bool  # write the text to the main checkout, or to the invoking one


RESOURCES = {
    "backlog": Resource(
        key="backlog",
        filename="BACKLOG.md",
        heading="## #{n}: {title}",
        number_re=r"^## #(\d+):",
        anchor=None,
        canonical_text=True,   # a finding is true the moment it is written
    ),
    "verification": Resource(
        key="verification",
        filename="VERIFICATION.md",
        heading="## Scenario {n}: {title}",
        number_re=r"^## Scenario (\d+):",
        anchor="## Recording the result",
        canonical_text=False,  # a scenario describes the branch it was written on (BACKLOG #30)
    ),
}


def _headings(pattern, text):
    """Matches of pattern that are real headings - not lines inside a ``` fenced block.

    This is a file about its own format, so it will quote a heading in an example sooner or
    later, and a quoted one is character-for-character identical to a real one. The fence is
    the only thing that tells them apart. Indentation is not enough: a fenced example is
    usually flush left, which is the point of showing it.
    """
    fenced, inside, pos = set(), False, 0
    for line in text.splitlines(keepends=True):
        if line.startswith("```"):
            inside = not inside
        elif inside:
            fenced.add(pos)
        pos += len(line)
    return [m for m in pattern.finditer(text) if m.start() not in fenced]

def scan_max(text, resource):
    """The highest number appearing as a real heading. 0 when there are none.

    Anchored at line start on purpose: an entry body citing "#40" must not become the
    high-water mark, and entries are not stored in numerical order - gaps are expected and
    correct, since a deleted entry's number is never reused.

    Fenced examples are excluded for the same reason cli._sections excludes them, but the cost
    of missing one differs: here a quoted "## #99:" never reissues a number, it silently jumps
    the next one to 100. A gap is supposed to be the record of a deleted entry - a phantom gap
    is that record lying.
    """
    numbers = [int(m.group(1)) for m in _headings(re.compile(resource.number_re, re.MULTILINE), text)]
    return max(numbers) if numbers else 0


def render(resource, number, title, body):
    """One section in the file's house format."""
    return resource.heading.format(n=number, title=title) + "\n\n" + body.rstrip("\n") + "\n"


def insert(text, resource, rendered):
    """Place a rendered section, at the resource's anchor or at the end of the file."""
    block = rendered.rstrip("\n") + "\n"
    if resource.anchor:
        at = text.find("\n" + resource.anchor)
        if at != -1:
            head = text[: at + 1].rstrip("\n") + "\n\n"
            return head + block + "\n" + text[at + 1 :]
    return text.rstrip("\n") + "\n\n" + block
