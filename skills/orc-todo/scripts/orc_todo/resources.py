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


RESOURCES = {
    "backlog": Resource(
        key="backlog",
        filename="BACKLOG.md",
        heading="## #{n}: {title}",
        number_re=r"^## #(\d+):",
        anchor=None,
    ),
    "verification": Resource(
        key="verification",
        filename="VERIFICATION.md",
        heading="## Scenario {n}: {title}",
        number_re=r"^## Scenario (\d+):",
        anchor="## Recording the result",
    ),
}


def scan_max(text, resource):
    """The highest number appearing as a real heading. 0 when there are none.

    Anchored at line start on purpose: an entry body citing "#40" must not become the
    high-water mark, and entries are not stored in numerical order - gaps are expected and
    correct, since a deleted entry's number is never reused.
    """
    numbers = [int(m) for m in re.findall(resource.number_re, text, flags=re.MULTILINE)]
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
