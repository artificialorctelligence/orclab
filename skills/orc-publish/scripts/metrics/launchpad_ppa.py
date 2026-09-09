#!/usr/bin/env python3
"""Read a Launchpad PPA's real published download counts.

The only distribution channel in Orclab's `metrics:` set that needs code rather than a
one-liner. Launchpad has no "total downloads for this PPA" endpoint: it counts per *binary
package publication* - one record per (package, version, series, architecture) - so getting a
number means listing every publication and asking each one, which is an N+1 fan-out over ~80
requests for even a small PPA. Confirmed live against ppa:artificialorctelligence/orcshot on
2026-09-08; see Orclab BACKLOG #7.

Anonymous and read-only: no credentials, no OAuth, no local state.

What the number is NOT: an install count, or a count of people. It counts fetches of the .deb,
mirrors and indexers included - see the caveat this prints, which is part of the output on
purpose rather than a docstring nobody reads.
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

API = "https://api.launchpad.net/1.0"


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def published_binaries(owner, ppa, package=None):
    """Every binary publication in the PPA, newest first, as Launchpad returns them."""
    params = {"ws.op": "getPublishedBinaries"}
    if package:
        params["binary_name"] = package
        params["exact_match"] = "true"
    url = f"{API}/~{owner}/+archive/ubuntu/{ppa}?" + urllib.parse.urlencode(params)
    return get(url).get("entries", [])


def _link_segment(entry, index):
    """A path segment of a publication's distro_arch_series_link, or "?" if it isn't there.

    That link is .../ubuntu/<series>/<arch>, and Launchpad returns neither field directly on
    the publication - the link is the only place they exist. Missing or short links yield "?"
    rather than raising: a PPA read is a report, and one odd publication should not take the
    other seventy-four down with it.
    """
    segments = entry.get("distro_arch_series_link", "").rstrip("/").split("/")
    if len(segments) < abs(index):
        return "?"
    return segments[index] or "?"


def series_of(entry):
    return _link_segment(entry, -2)


def arch_of(entry):
    return _link_segment(entry, -1)


def download_count(entry):
    return int(get(f"{entry['self_link']}?ws.op=getDownloadCount"))


def collect(entries, workers=8):
    """(package, version, series, arch) -> count, fetched concurrently.

    Concurrent because this is one HTTP round trip per publication and a real PPA has dozens;
    serially it is a minute of waiting for four numbers. Deliberately only 8 at a time: at 16,
    two leaves reading the same PPA back to back drew a read timeout out of Launchpad on
    2026-09-08. This is someone else's free API being asked ~75 questions to answer one.
    """
    with ThreadPoolExecutor(max_workers=workers) as pool:
        counts = list(pool.map(download_count, entries))
    return {
        (e["binary_package_name"], e["binary_package_version"], series_of(e), arch_of(e)): c
        for e, c in zip(entries, counts)
    }


def report(counts):
    """Per-version totals and a grand total, with the caveat that makes them readable."""
    if not counts:
        return "no published binaries found"
    by_version = defaultdict(int)
    for (package, version, _series, _arch), count in counts.items():
        by_version[(package, version)] += count
    lines = []
    for (package, version), total in sorted(by_version.items()):
        lines.append(f"  {package} {version}: {total}")
    lines.append(f"total: {sum(by_version.values())} across {len(counts)} publications")
    lines.append(
        "note: Launchpad counts .deb fetches per (version, series, architecture) publication, "
        "not installs and not people - mirrors and indexers are included, which is why "
        "architectures with no plausible users still report downloads."
    )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="launchpad_ppa")
    parser.add_argument("ppa", help="owner/ppa-name, e.g. artificialorctelligence/orcshot")
    parser.add_argument("--package", help="restrict to one binary package name")
    parser.add_argument("--series", help="restrict to one Ubuntu series, e.g. noble")
    parser.add_argument("--per-publication", action="store_true",
                        help="also list every (version, series, arch) publication separately")
    args = parser.parse_args(argv)

    if "/" not in args.ppa:
        print("error: ppa must be owner/ppa-name", file=sys.stderr)
        return 1
    owner, ppa = args.ppa.split("/", 1)

    try:
        entries = published_binaries(owner, ppa, args.package)
        if args.series:
            # Filtered here, not in the API call: getPublishedBinaries takes a
            # distro_arch_series link (one per architecture), not a series name, so asking
            # Launchpad to do it would mean one query per arch. The series is already on every
            # entry we have, and skipping the other series' entries is what saves the round
            # trips - the fan-out below is the expensive part, not this listing.
            entries = [e for e in entries if series_of(e) == args.series]
        counts = collect(entries)
    except (OSError, ValueError, KeyError) as e:
        # OSError, not urllib.error.URLError: a read that stalls mid-body raises a bare
        # TimeoutError, which is an OSError but not a URLError, and escaped as a full traceback
        # into the /orc-publish summary the first time this ran for real.
        print(f"error: Launchpad read failed for {args.ppa}: {e}", file=sys.stderr)
        return 1

    label = f"ppa:{args.ppa}" + (f" ({args.series})" if args.series else "")
    print(label)
    if args.per_publication:
        for key, count in sorted(counts.items()):
            if count:
                print("  {} {} {}/{}: {}".format(*key, count))
    print(report(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
