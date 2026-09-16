"""appstore-status.py is copied into a consuming project, where /orc-publish runs it as the
--confirm check (`state`) and the --metrics source (`downloads`) against App Store Connect. The
network is one function, get(); the JWT is one, token(). Both are driven here against fakes that
record the request, and state()/downloads() against canned API responses - including the gzipped
tab-separated sales report Apple actually sends. One subprocess test keeps the shell contract:
the substituted file is valid Python and prints its usage."""

import datetime as dt
import gzip
import io
import json
import pathlib
import subprocess
import sys
import urllib.request

import pytest

# The real template, for the tests that read it as text or run it from a shell - under
# /orc-test analyze this file runs from mutmut's mutants/ copy, whose templates are rewritten.
_ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMPLATE = (
    (_ROOT.parent if _ROOT.name == "mutants" else _ROOT)
    / "ingredients" / "app-store" / "templates" / "appstore-status.py"
)
FILLED = {
    "__KEY_ID__": "ABC123DEF4", "__ISSUER_ID__": "00000000-0000-0000-0000-000000000000",
    "__P8_PATH__": "/nonexistent/AuthKey.p8", "__BUNDLE_ID__": "org.example.app",
    "__VENDOR__": "12345678",
}


def instantiate(tmp_path):
    text = TEMPLATE.read_text()
    for placeholder, value in FILLED.items():
        text = text.replace(placeholder, value)
    assert "__" not in text.replace("__main__", "").replace("__name__", "").replace("__doc__", ""), \
        "every placeholder must be one of the five documented ones"
    out = tmp_path / "appstore-status.py"
    out.write_text(text)
    return out


def test_usage_runs_and_names_both_modes(tmp_path):
    script = instantiate(tmp_path)
    out = subprocess.run([sys.executable, str(script)], check=False, capture_output=True, text=True,
                         env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"})
    # exit 2 = usage; it may also be a PyJWT ImportError (exit 1) on a machine without it -
    # both prove the file is valid Python and neither reaches the network.
    assert out.returncode in (1, 2), out.stderr
    assert "state" in out.stdout + out.stderr and "downloads" in out.stdout + out.stderr


# --- token(): what gets signed, and with what ----------------------------------------------------

@pytest.fixture
def key_file(appstore_template, tmp_path, monkeypatch):
    p8 = tmp_path / "AuthKey_ABC.p8"
    p8.write_text("-----BEGIN PRIVATE KEY-----\nMIGT…not-a-real-key…\n-----END PRIVATE KEY-----\n")
    monkeypatch.setattr(appstore_template, "P8_PATH", str(p8))
    return p8


def test_token_is_es256_over_the_issuer_with_a_ten_minute_life_and_the_key_id_header(appstore_template, fake_jwt, key_file, monkeypatch):
    monkeypatch.setattr(appstore_template.time, "time", lambda: 1_800_000_000.7)
    assert appstore_template.token() == "signed.jwt.token"
    [call] = fake_jwt.calls
    assert call["payload"] == {"iss": "__ISSUER_ID__", "iat": 1_800_000_000,
                              "exp": 1_800_000_600, "aud": "appstoreconnect-v1"}
    assert call["key"] == key_file.read_text()
    assert call["algorithm"] == "ES256"
    assert call["headers"] == {"kid": "__KEY_ID__"}


def test_the_key_is_read_from_the_file_but_never_printed(appstore_template, fake_jwt, key_file, capsys):
    appstore_template.token()
    assert "PRIVATE KEY" not in capsys.readouterr().out
    assert "print(key" not in TEMPLATE.read_text() and "print(token" not in TEMPLATE.read_text()


# --- get(): the one request shape ----------------------------------------------------------------

class FakeResponse:
    def __init__(self, body):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def api(appstore_template, monkeypatch):
    """Answers get() from a dict of path → body (JSON-encodable, or raw bytes) and records
    every Request made."""
    monkeypatch.setattr(appstore_template, "token", lambda: "signed.jwt.token")
    requests = []
    answers = {}

    def urlopen(req, timeout=None):
        requests.append((req, timeout))
        path = req.full_url[len(appstore_template.API):].split("?", 1)[0]
        body = answers[path]
        return FakeResponse(body if isinstance(body, bytes) else json.dumps(body).encode())

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    answers["requests"] = requests
    return answers


def test_get_sends_a_bearer_token_with_the_query_and_a_sixty_second_timeout(appstore_template, api):
    api["/apps"] = {"data": [{"id": "1"}]}
    assert appstore_template.get("/apps", {"filter[bundleId]": "org.example.app"}) == {"data": [{"id": "1"}]}
    [(req, timeout)] = api["requests"]
    assert req.full_url == "https://api.appstoreconnect.apple.com/v1/apps?filter%5BbundleId%5D=org.example.app"
    assert req.get_header("Authorization") == "Bearer signed.jwt.token"
    assert timeout == 60


def test_get_without_params_has_no_query_and_raw_returns_the_bytes(appstore_template, api):
    api["/salesReports"] = b"\x1f\x8b not json"
    assert appstore_template.get("/salesReports", raw=True) == b"\x1f\x8b not json"
    [(req, _)] = api["requests"]
    assert req.full_url == "https://api.appstoreconnect.apple.com/v1/salesReports"


# --- state(): exit 0 iff READY_FOR_SALE ----------------------------------------------------------

def versions(state_field, state_value, version="2.1.0"):
    return {"data": [{"attributes": {"versionString": version, state_field: state_value}}]}


def test_state_is_0_and_prints_the_version_when_ready_for_sale(appstore_template, api, capsys):
    api["/apps"] = {"data": [{"id": "6449"}]}
    api["/apps/6449/appStoreVersions"] = versions("appVersionState", "READY_FOR_SALE")
    assert appstore_template.state() == 0
    assert capsys.readouterr().out == "2.1.0: READY_FOR_SALE\n"


def test_state_asks_for_this_bundle_id_and_the_latest_ios_version_only(appstore_template, api):
    api["/apps"] = {"data": [{"id": "6449"}]}
    api["/apps/6449/appStoreVersions"] = versions("appVersionState", "READY_FOR_SALE")
    appstore_template.state()
    urls = [req.full_url for req, _ in api["requests"]]
    assert urls == [
        "https://api.appstoreconnect.apple.com/v1/apps?filter%5BbundleId%5D=__BUNDLE_ID__",
        "https://api.appstoreconnect.apple.com/v1/apps/6449/appStoreVersions?filter%5Bplatform%5D=IOS&limit=1",
    ]


@pytest.mark.parametrize("state_value", ["WAITING_FOR_REVIEW", "IN_REVIEW", "PENDING_DEVELOPER_RELEASE", "REJECTED"])
def test_state_is_1_and_names_any_other_state(appstore_template, api, capsys, state_value):
    api["/apps"] = {"data": [{"id": "6449"}]}
    api["/apps/6449/appStoreVersions"] = versions("appVersionState", state_value)
    assert appstore_template.state() == 1
    assert capsys.readouterr().out == f"2.1.0: {state_value}\n"


def test_state_falls_back_to_the_older_app_store_state_field(appstore_template, api, capsys):
    api["/apps"] = {"data": [{"id": "6449"}]}
    api["/apps/6449/appStoreVersions"] = versions("appStoreState", "READY_FOR_SALE", version="1.0")
    assert appstore_template.state() == 0
    assert capsys.readouterr().out == "1.0: READY_FOR_SALE\n"


def test_state_prefers_app_version_state_when_both_are_present(appstore_template, api, capsys):
    api["/apps"] = {"data": [{"id": "6449"}]}
    api["/apps/6449/appStoreVersions"] = {"data": [{"attributes": {
        "versionString": "3.0", "appVersionState": "IN_REVIEW", "appStoreState": "READY_FOR_SALE"}}]}
    assert appstore_template.state() == 1
    assert capsys.readouterr().out == "3.0: IN_REVIEW\n"


def test_state_is_1_when_no_app_has_this_bundle_id(appstore_template, api, capsys):
    api["/apps"] = {"data": []}
    assert appstore_template.state() == 1
    assert capsys.readouterr().out == "no app with bundle id __BUNDLE_ID__ on this team\n"
    assert len(api["requests"]) == 1


def test_state_is_1_when_the_app_has_no_version_yet(appstore_template, api, capsys):
    api["/apps"] = {"data": [{"id": "6449"}]}
    api["/apps/6449/appStoreVersions"] = {"data": []}
    assert appstore_template.state() == 1
    assert capsys.readouterr().out == "no App Store version exists yet\n"


# --- downloads(): yesterday's Sales and Trends report --------------------------------------------

def report(rows):
    """Apple's daily summary: a gzipped, tab-separated file with a header row."""
    cols = ["Provider", "Title", "Product Type Identifier", "Units", "Country Code"]
    text = "\t".join(cols) + "\n" + "".join("\t".join(r) + "\n" for r in rows)
    return gzip.compress(text.encode())


@pytest.fixture
def yesterday(appstore_template, monkeypatch):
    class Today(dt.date):
        @classmethod
        def today(cls):
            return cls(2026, 3, 1)      # the day after a 28-day February

    monkeypatch.setattr(appstore_template.dt, "date", Today)
    return "2026-02-28"


def test_downloads_asks_for_yesterdays_daily_summary_sales_report_for_this_vendor(appstore_template, api, yesterday):
    api["/salesReports"] = report([])
    appstore_template.downloads()
    [(req, _)] = api["requests"]
    assert req.full_url == (
        "https://api.appstoreconnect.apple.com/v1/salesReports?filter%5Bfrequency%5D=DAILY"
        "&filter%5BreportDate%5D=2026-02-28&filter%5BreportSubType%5D=SUMMARY"
        "&filter%5BreportType%5D=SALES&filter%5BvendorNumber%5D=__VENDOR__&filter%5Bversion%5D=1_0"
    )


def test_downloads_sums_units_per_title_and_product_type_sorted(appstore_template, api, yesterday, capsys):
    api["/salesReports"] = report([
        ["1", "Orcshot", "1", "3", "US"],
        ["1", "Orcshot", "1", "2", "DE"],       # same title and type: summed
        ["1", "Orcshot", "7", "11", "US"],      # an update, kept separate
        ["1", "Another App", "1", "1", "US"],   # sorts before Orcshot
        ["1", "Orcshot", "1F", "", "FR"],       # blank Units counts as 0, not a crash
    ])
    assert appstore_template.downloads() == 0
    assert capsys.readouterr().out == (
        "2026-02-28: Another App type 1 = 1 units\n"
        "2026-02-28: Orcshot type 1 = 5 units\n"
        "2026-02-28: Orcshot type 1F = 0 units\n"
        "2026-02-28: Orcshot type 7 = 11 units\n"
        "(units are Apple's count of downloads and updates, not people)\n"
    )


def test_downloads_reports_an_empty_day_as_no_rows_and_still_exits_0(appstore_template, api, yesterday, capsys):
    api["/salesReports"] = report([])
    assert appstore_template.downloads() == 0
    assert capsys.readouterr().out == "2026-02-28: no rows (a day with no downloads returns an empty report)\n"


def test_downloads_reads_apples_tab_separated_columns_not_commas(appstore_template, api, yesterday, capsys):
    # A title with a comma in it must stay one column.
    api["/salesReports"] = report([["1", "Notes, Lists & More", "1", "4", "GB"]])
    appstore_template.downloads()
    assert "Notes, Lists & More type 1 = 4 units" in capsys.readouterr().out
