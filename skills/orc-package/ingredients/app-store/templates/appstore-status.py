#!/usr/bin/env python3
"""Read-only App Store Connect queries for __BUNDLE_ID__.

  appstore-status.py state       exit 0 iff the latest iOS version is READY_FOR_SALE;
                                 otherwise prints the state and exits 1 (/orc-publish --confirm)
  appstore-status.py downloads   yesterday's Sales and Trends units for this app (/orc-publish --metrics)

Needs PyJWT with its crypto extra (`pip install 'PyJWT[crypto]'`). Never prints the key.
Written from Apple's live API docs 2026-09-11 and never run against a real account - correct
it on first use.
"""
import gzip
import io
import csv
import datetime as dt
import json
import sys
import time
import urllib.parse
import urllib.request

import jwt  # PyJWT

KEY_ID = "__KEY_ID__"
ISSUER_ID = "__ISSUER_ID__"
P8_PATH = "__P8_PATH__"
BUNDLE_ID = "__BUNDLE_ID__"
VENDOR = "__VENDOR__"
API = "https://api.appstoreconnect.apple.com/v1"


def token():
    with open(P8_PATH) as f:
        key = f.read()
    now = int(time.time())
    # Apple: ES256, exp at most 20 minutes out, aud fixed.
    return jwt.encode({"iss": ISSUER_ID, "iat": now, "exp": now + 600, "aud": "appstoreconnect-v1"},
                      key, algorithm="ES256", headers={"kid": KEY_ID})


def get(path, params=None, raw=False):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token()})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    return body if raw else json.loads(body)


def state():
    apps = get("/apps", {"filter[bundleId]": BUNDLE_ID})["data"]
    if not apps:
        print(f"no app with bundle id {BUNDLE_ID} on this team")
        return 1
    versions = get(f"/apps/{apps[0]['id']}/appStoreVersions",
                   {"filter[platform]": "IOS", "limit": 1})["data"]
    if not versions:
        print("no App Store version exists yet")
        return 1
    a = versions[0]["attributes"]
    s = a.get("appVersionState") or a.get("appStoreState")
    print(f"{a.get('versionString')}: {s}")
    return 0 if s == "READY_FOR_SALE" else 1


def downloads():
    day = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    body = get("/salesReports", {"filter[frequency]": "DAILY", "filter[reportDate]": day,
                                 "filter[reportSubType]": "SUMMARY", "filter[reportType]": "SALES",
                                 "filter[vendorNumber]": VENDOR, "filter[version]": "1_0"}, raw=True)
    rows = list(csv.DictReader(io.StringIO(gzip.decompress(body).decode()), delimiter="\t"))
    # The report covers every app under the vendor number and has no bundle-id column, so
    # rows are grouped by Title. Apple's Sales and Trends guide: product types 1/1F/1T are
    # app downloads, 7/7F/7T are updates - printed as-is so the mapping is checkable on the
    # first real run rather than assumed here.
    units = {}
    for r in rows:
        k = (r.get("Title", "?"), r.get("Product Type Identifier", "?"))
        units[k] = units.get(k, 0) + int(r.get("Units") or 0)
    if not units:
        print(f"{day}: no rows (a day with no downloads returns an empty report)")
        return 0
    for (title, ptype), n in sorted(units.items()):
        print(f"{day}: {title} type {ptype} = {n} units")
    print("(units are Apple's count of downloads and updates, not people)")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("state", "downloads"):
        print(__doc__)
        sys.exit(2)
    sys.exit(state() if cmd == "state" else downloads())
