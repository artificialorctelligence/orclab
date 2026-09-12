import pathlib

from orc_test import jacoco, pitest

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_jacoco_per_sourcefile_line_counters():
    cov = jacoco.parse(FIX / "jacoco.xml")
    assert cov.files == {"com/example/Clamp.java": (4, 6), "com/example/Other.java": (3, 3)}
    assert (cov.covered, cov.total) == (7, 9)


def test_pitest_statuses():
    m = pitest.parse(FIX / "mutations.xml")
    assert (m.killed, m.total) == (1, 3)
    assert [(s.file, s.line) for s in m.survivors] == [("com/example/Clamp.java", 6), ("com/example/Other.java", 9)]
    assert m.survivors[0].description == "changed conditional boundary"
    assert "(no test reaches it)" in m.survivors[1].description


def test_find_maven_and_gradle_locations(tmp_path):
    (tmp_path / "target" / "site" / "jacoco").mkdir(parents=True)
    (tmp_path / "target" / "site" / "jacoco" / "jacoco.xml").write_text("<report/>")
    assert jacoco.find(tmp_path) == tmp_path / "target" / "site" / "jacoco" / "jacoco.xml"
    g = tmp_path / "build" / "reports" / "jacoco" / "test"
    g.mkdir(parents=True)
    (g / "jacocoTestReport.xml").write_text("<report/>")
    assert jacoco.find(tmp_path) == g / "jacocoTestReport.xml"       # newest wins
    (tmp_path / "target" / "pit-reports" / "202609111200").mkdir(parents=True)
    (tmp_path / "target" / "pit-reports" / "202609111200" / "mutations.xml").write_text("<mutations/>")
    assert pitest.find(tmp_path).name == "mutations.xml"


def test_find_returns_none_when_absent(tmp_path):
    assert jacoco.find(tmp_path) is None
    assert pitest.find(tmp_path) is None
