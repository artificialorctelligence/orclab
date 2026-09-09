"""The Launchpad reader's own logic, with no network.

Only the pure parts are tested: the series/arch parsing that --series filtering depends on,
and the aggregation that turns ~75 per-publication counts into a readable report. The HTTP
fan-out itself is verified live against a real PPA, not mocked - a fake API that returns what
we expect proves nothing about Launchpad. See BACKLOG #7.
"""

import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location(
    "launchpad_ppa", pathlib.Path(__file__).resolve().parent.parent / "metrics/launchpad_ppa.py"
)
lp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lp)


def entry(series, arch):
    return {
        "distro_arch_series_link": f"https://api.launchpad.net/1.0/ubuntu/{series}/{arch}",
        "binary_package_name": "orcshot",
        "binary_package_version": "0.1.1-3",
    }


def test_series_and_arch_come_from_the_publication_link():
    """Launchpad puts neither on the publication itself - both are path segments of the
    distro_arch_series link, which is what --series filters on."""
    e = entry("noble", "amd64")
    assert lp.series_of(e) == "noble"
    assert lp.arch_of(e) == "amd64"


def test_a_missing_link_does_not_crash_the_run():
    assert lp.series_of({}) == "?"
    assert lp.arch_of({}) == "?"


def test_report_sums_every_architecture_into_one_per_version_total():
    counts = {
        ("orcshot", "0.1.1-3", "noble", "amd64"): 4,
        ("orcshot", "0.1.1-3", "noble", "s390x"): 4,
        ("orcshot", "0.2.0-1", "noble", "amd64"): 0,
    }
    text = lp.report(counts)
    assert "orcshot 0.1.1-3: 8" in text
    assert "orcshot 0.2.0-1: 0" in text
    assert "total: 8 across 3 publications" in text


def test_report_always_carries_the_not_installs_caveat():
    """The caveat ships in the output, not the docs: a bare total reads as users, and the
    identical per-architecture counts on a real PPA show it is mostly not."""
    assert "not installs and not people" in lp.report({("orcshot", "1.0", "noble", "amd64"): 1})


def test_report_says_so_when_a_ppa_has_no_published_binaries():
    assert lp.report({}) == "no published binaries found"
