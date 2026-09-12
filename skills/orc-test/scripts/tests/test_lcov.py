import pathlib

from orc_test import lcov

FIX = pathlib.Path(__file__).parent / "fixtures" / "coverage.lcov"


def test_parse_uses_lf_lh_and_falls_back_to_da_counts():
    cov = lcov.parse(FIX)
    assert cov.files == {"src/calc/__init__.py": (4, 6), "src/other.py": (2, 2)}
    assert (cov.covered, cov.total) == (6, 8)
    assert cov.percent == 75.0
    assert cov.under(80) == [("src/calc/__init__.py", 66.7)]
