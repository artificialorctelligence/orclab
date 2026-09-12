# skills/orc-test/scripts/tests/test_model.py
from orc_test.model import Coverage, Mutation, Survivor


def test_coverage_percent_and_under_sorted_worst_first():
    cov = Coverage(covered=7, total=10, files={
        "src/a.py": (9, 10), "src/b.py": (1, 4), "src/c.py": (3, 6)})
    assert cov.percent == 70.0
    assert cov.under(80) == [("src/b.py", 25.0), ("src/c.py", 50.0)]


def test_coverage_empty_is_zero_not_error():
    assert Coverage(0, 0, {}).percent == 0.0
    assert Coverage(0, 0, {}).under(80) == []


def test_mutation_score():
    m = Mutation(killed=7, total=10, survivors=[Survivor("src/a.py", 3, "< -> <=")])
    assert m.score == 70.0
    assert Mutation(0, 0, []).score == 0.0
