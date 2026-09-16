"""The Launchpad reader, with no network.

Two different claims, kept apart. What Launchpad actually returns - the shape of a publication,
that getDownloadCount is a bare integer, the ~75-request fan-out - is verified live against a
real PPA (BACKLOG #7), and no fake here can stand in for that. What this file proves is the
reader's own logic around those calls: the URL it asks for, the --series filter, the shape of
the counts, the report, and the error path that once escaped as a traceback into a real
/orc-publish summary. get() is replaced with a fake that answers from a dict of URL -> body
and records every request."""

import importlib.util
import pathlib

import pytest

# Loaded under the name mutmut derives from its path (metrics/launchpad_ppa.py, from scripts/):
# under /orc-test analyze the trampoline matches a mutant to a module by that name, and until
# 2026-09-15 this loaded as plain "launchpad_ppa", so every one of the file's mutants scored
# "no tests" and it dropped out of the suite's TCE without a word.
_ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("metrics.launchpad_ppa", _ROOT / "metrics" / "launchpad_ppa.py")
lp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lp)

PPA = "https://api.launchpad.net/1.0/~artificialorctelligence/+archive/ubuntu/orcshot"


def entry(series, arch, version="0.1.1-3", package="orcshot", n=0):
    return {
        "self_link": f"{PPA}/+binarypub/{n}",
        "distro_arch_series_link": f"https://api.launchpad.net/1.0/ubuntu/{series}/{arch}",
        "binary_package_name": package,
        "binary_package_version": version,
    }


@pytest.fixture
def api(monkeypatch):
    """Answers get(url) from `api[url]` and records each URL asked, in order."""
    answers = {}
    asked = []

    def get(url):
        asked.append(url)
        return answers[url]

    monkeypatch.setattr(lp, "get", get)
    answers["asked"] = asked
    return answers


def listing(api, entries, query="ws.op=getPublishedBinaries"):
    api[f"{PPA}?{query}"] = {"entries": entries}
    for e in entries:
        api[f"{e['self_link']}?ws.op=getDownloadCount"] = 0
    return entries


# --- the pure parts ------------------------------------------------------------------------------

def test_series_and_arch_come_from_the_publication_link():
    """Launchpad puts neither on the publication itself - both are path segments of the
    distro_arch_series link, which is what --series filters on."""
    e = entry("noble", "amd64")
    assert lp.series_of(e) == "noble"
    assert lp.arch_of(e) == "amd64"


def test_a_missing_or_short_link_does_not_crash_the_run():
    assert lp.series_of({}) == "?"
    assert lp.arch_of({}) == "?"
    assert lp.series_of({"distro_arch_series_link": "amd64"}) == "?"
    e = {"distro_arch_series_link": "https://api.launchpad.net/1.0/ubuntu//amd64"}   # an empty segment
    assert lp.series_of(e) == "?" and lp.arch_of(e) == "amd64"


def test_report_sums_every_architecture_into_one_per_version_total():
    counts = {
        ("orcshot", "0.1.1-3", "noble", "amd64"): 4,
        ("orcshot", "0.1.1-3", "noble", "s390x"): 4,
        ("orcshot", "0.2.0-1", "noble", "amd64"): 0,
    }
    text = lp.report(counts)
    assert "  orcshot 0.1.1-3: 8\n  orcshot 0.2.0-1: 0\n" in text
    assert "total: 8 across 3 publications" in text


def test_report_always_carries_the_not_installs_caveat():
    """The caveat ships in the output, not the docs: a bare total reads as users, and the
    identical per-architecture counts on a real PPA show it is mostly not."""
    assert "not installs and not people" in lp.report({("orcshot", "1.0", "noble", "amd64"): 1})


def test_report_says_so_when_a_ppa_has_no_published_binaries():
    assert lp.report({}) == "no published binaries found"


# --- the calls: what is asked, and what is made of the answers -----------------------------------

def test_the_listing_is_the_ppas_published_binaries(api):
    listing(api, [entry("noble", "amd64")])
    assert lp.published_binaries("artificialorctelligence", "orcshot") == [entry("noble", "amd64")]
    assert api["asked"] == [f"{PPA}?ws.op=getPublishedBinaries"]


def test_a_package_filter_is_an_exact_match_in_the_query(api):
    query = "ws.op=getPublishedBinaries&binary_name=orcshot-doc&exact_match=true"
    listing(api, [], query=query)
    assert lp.published_binaries("artificialorctelligence", "orcshot", "orcshot-doc") == []
    assert api["asked"] == [f"{PPA}?{query}"]


def test_a_listing_without_entries_is_empty_not_an_error(api):
    api[f"{PPA}?ws.op=getPublishedBinaries"] = {}
    assert lp.published_binaries("artificialorctelligence", "orcshot") == []


def test_download_count_is_the_publications_own_integer(api):
    e = entry("noble", "amd64", n=7)
    api[f"{e['self_link']}?ws.op=getDownloadCount"] = 12
    assert lp.download_count(e) == 12
    assert api["asked"] == [f"{PPA}/+binarypub/7?ws.op=getDownloadCount"]


def test_collect_keys_every_count_by_package_version_series_and_arch(api):
    entries = listing(api, [entry("noble", "amd64", n=1), entry("noble", "s390x", n=2),
                            entry("jammy", "amd64", version="0.1.0-1", n=3)])
    api[f"{PPA}/+binarypub/1?ws.op=getDownloadCount"] = 4
    api[f"{PPA}/+binarypub/2?ws.op=getDownloadCount"] = 4
    api[f"{PPA}/+binarypub/3?ws.op=getDownloadCount"] = 9
    assert lp.collect(entries, workers=2) == {
        ("orcshot", "0.1.1-3", "noble", "amd64"): 4,
        ("orcshot", "0.1.1-3", "noble", "s390x"): 4,
        ("orcshot", "0.1.0-1", "jammy", "amd64"): 9,
    }
    assert sorted(api["asked"]) == sorted(f"{e['self_link']}?ws.op=getDownloadCount" for e in entries)


def test_collect_of_nothing_asks_nothing(api):
    assert lp.collect([]) == {}
    assert api["asked"] == []


# --- main(): the command /orc-publish's metrics: line runs ---------------------------------------

def test_main_prints_the_label_and_the_report(api, capsys):
    entries = listing(api, [entry("noble", "amd64", n=1), entry("noble", "arm64", n=2)])
    api[f"{PPA}/+binarypub/1?ws.op=getDownloadCount"] = 3
    api[f"{PPA}/+binarypub/2?ws.op=getDownloadCount"] = 1
    assert lp.main(["artificialorctelligence/orcshot"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("ppa:artificialorctelligence/orcshot\n  orcshot 0.1.1-3: 4\n")
    assert "total: 4 across 2 publications" in out
    assert "+binarypub" not in out and "amd64" not in out    # per-publication lines are opt-in


def test_main_series_filter_skips_other_series_before_the_fan_out(api, capsys):
    entries = listing(api, [entry("noble", "amd64", n=1), entry("jammy", "amd64", n=2)])
    api[f"{PPA}/+binarypub/1?ws.op=getDownloadCount"] = 5
    assert lp.main(["artificialorctelligence/orcshot", "--series", "noble"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("ppa:artificialorctelligence/orcshot (noble)\n")
    assert "total: 5 across 1 publications" in out
    assert f"{PPA}/+binarypub/2?ws.op=getDownloadCount" not in api["asked"], "jammy was never fetched"


def test_main_per_publication_lists_each_nonzero_publication(api, capsys):
    entries = listing(api, [entry("noble", "amd64", n=1), entry("noble", "s390x", n=2)])
    api[f"{PPA}/+binarypub/1?ws.op=getDownloadCount"] = 6
    assert lp.main(["artificialorctelligence/orcshot", "--per-publication"]) == 0
    out = capsys.readouterr().out
    assert "  orcshot 0.1.1-3 noble/amd64: 6\n" in out
    assert "s390x" not in out, "a zero count is not listed"


def test_main_passes_the_package_filter_through(api):
    query = "ws.op=getPublishedBinaries&binary_name=orcshot&exact_match=true"
    listing(api, [], query=query)
    assert lp.main(["artificialorctelligence/orcshot", "--package", "orcshot"]) == 0
    assert api["asked"] == [f"{PPA}?{query}"]


def test_main_rejects_a_ppa_that_is_not_owner_slash_name(capsys):
    assert lp.main(["orcshot"]) == 1
    assert capsys.readouterr().err == "error: ppa must be owner/ppa-name\n"


@pytest.mark.parametrize("exc", [
    TimeoutError("The read operation timed out"),   # the bare OSError that once escaped as a traceback
    OSError("[Errno -3] Temporary failure in name resolution"),
    ValueError("Expecting value: line 1 column 1 (char 0)"),
    KeyError("self_link"),
])
def test_main_turns_a_failed_read_into_one_error_line_and_exit_1(monkeypatch, capsys, exc):
    def get(url):
        raise exc
    monkeypatch.setattr(lp, "get", get)
    assert lp.main(["artificialorctelligence/orcshot"]) == 1
    err = capsys.readouterr().err
    assert err.startswith("error: Launchpad read failed for artificialorctelligence/orcshot: ")
    assert "Traceback" not in err


def test_get_asks_the_url_with_a_timeout_and_decodes_json(monkeypatch):
    seen = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b'{"entries": []}'

    def urlopen(url, timeout=None):
        seen.update(url=url, timeout=timeout)
        return Response()

    monkeypatch.setattr(lp.urllib.request, "urlopen", urlopen)
    assert lp.get("https://api.launchpad.net/1.0/x") == {"entries": []}
    assert seen == {"url": "https://api.launchpad.net/1.0/x", "timeout": 60}
