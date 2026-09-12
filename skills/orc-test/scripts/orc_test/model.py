"""The three things every language reports in the same shape, whatever tool produced them."""

from dataclasses import dataclass, field


def _pct(part, whole):
    return round(100.0 * part / whole, 1) if whole else 0.0


@dataclass
class Coverage:
    covered: int
    total: int
    files: dict = field(default_factory=dict)   # path -> (covered, total)

    @property
    def percent(self):
        return _pct(self.covered, self.total)

    def under(self, threshold):
        """[(path, percent)] for files below threshold, worst first."""
        rows = [(p, _pct(c, t)) for p, (c, t) in self.files.items() if _pct(c, t) < threshold]
        return sorted(rows, key=lambda r: (r[1], r[0]))


@dataclass
class Survivor:
    file: str
    line: int
    description: str


@dataclass
class Mutation:
    killed: int
    total: int
    survivors: list = field(default_factory=list)

    @property
    def score(self):
        return _pct(self.killed, self.total)


@dataclass
class Finding:
    file: str
    line: int
    message: str
