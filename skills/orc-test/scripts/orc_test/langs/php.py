"""PHP: PHPUnit (clover for coverage), Infection for mutation, composer audit. Every tool lives
in the project's own vendor/bin — installed by `composer install`, which is the one thing the
project runs itself (languages/php.md).

Infection has no --logger-json option (its command-line-options page, read 2026-09-20); the full
JSON log lands where the project's own infection.json5 says (`logs.json`), so mutation_parse
reads that file to find it. infection.json5 is JSON5 (comments/trailing commas allowed); the
sample's is plain JSON, so json.loads with a fallback that strips `//` comment lines is enough —
see stack-php's `## Build, run, test` and the infection.json fixture's README.
"""

import json
import pathlib
import re
import xml.etree.ElementTree as ET

from .. import probe
from ..model import Coverage, Mutation, Survivor

KEY = "php"
LABEL = "PHP"
SOURCE_EXT = ".php"
MARKERS = ["composer.json"]
TOOLS = {"composer": "https://getcomposer.org/download/ — or run inside the stack-php container"}
CAVEATS = [("vendor/bin/phpunit, infection and phpstan are the project's own require-dev packages;"
            " `composer install` once, and again when composer.json changes."),
           "Infection needs a coverage driver (pcov or xdebug) loaded in the PHP that runs it."]
SANDBOX = {".phpunit.cache", "vendor"}   # PHPUnit's own cache and composer's installed packages, not mutation output

AUDIT_TOOL = ("composer", "https://getcomposer.org/download/")
_UNREADABLE = ["audit output not understood — see above"]
_JSON5_COMMENT = re.compile(r"^\s*//.*$", re.MULTILINE)


def _dev_deps(root):
    p = pathlib.Path(root) / "composer.json"
    try:
        return json.loads(p.read_text()).get("require-dev", {})
    except (OSError, ValueError):
        return {}


def missing(root):
    return [t for t in TOOLS if not probe.which(t)]


def test_cmd(root, target):
    return ["vendor/bin/phpunit"] + ([target] if target else [])


def coverage_cmd(root, target, out):
    out = pathlib.Path(out)
    return ["vendor/bin/phpunit", "--coverage-clover", str(out / "clover.xml"),
            "--coverage-html", str(out / "html")] + ([target] if target else [])


def coverage_parse(root, out):
    p = pathlib.Path(out) / "clover.xml"
    if not p.exists():
        return Coverage(0, 0)
    files = {}
    for f in ET.parse(p).getroot().iter("file"):
        m = f.find("metrics")
        if m is not None:
            files[f.get("name")] = (int(m.get("coveredstatements", 0)), int(m.get("statements", 0)))
    return Coverage(sum(c for c, _ in files.values()), sum(t for _, t in files.values()), files)


def mutation_unavailable(root, target=None):
    if "infection/infection" not in _dev_deps(root):
        return "Infection not installed — composer require --dev infection/infection"
    if not any((pathlib.Path(root) / n).exists() for n in ("infection.json5", "infection.json")):
        return "no infection.json5 — vendor/bin/infection writes one on first interactive run"
    return None


def mutation_cmd(root, target, out):
    # No --logger-json (Infection has none); the full log's path is infection.json5's own
    # logs.json key, read back by mutation_parse. --with-uncovered: since Infection 0.31 the
    # default mutates covered code only, which would score an untested file as 100%; with the
    # flag an uncovered mutant counts as alive, matching how Stryker/PIT are read here.
    cmd = ["vendor/bin/infection", "--no-interaction", "--no-progress", "--threads=max", "--with-uncovered"]
    if target:
        cmd.append(f"--filter={target}")
    return cmd


def _json5_load(text):
    try:
        return json.loads(text)
    except ValueError:
        return json.loads(_JSON5_COMMENT.sub("", text))


def _infection_log_path(root, out):
    """Where Infection wrote its JSON log: infection.json5's logs.json key, resolved relative to
    root, or <out>/infection.json when the file is absent, the key is absent, or the file is
    real JSON5 (trailing commas, block comments) beyond the //-line-comment fallback above —
    never raise on a config file this module cannot fully read."""
    p = pathlib.Path(root) / "infection.json5"
    if p.is_file():
        try:
            log = _json5_load(p.read_text()).get("logs", {}).get("json")
        except ValueError:
            log = None
        if log:
            return pathlib.Path(root) / log
    return pathlib.Path(out) / "infection.json"


def _survivor(root, entry, uncovered):
    # `escaped` and `uncovered` entries share the same mutator/diff shape (infection.json.README).
    # --with-uncovered counts an uncovered mutant in the denominator (mutation_cmd), so it has to
    # be reported as a survivor too, or `generate` never learns the file is untested — the same
    # "alive but no test reaches it" case stryker.py/pitest.py tag the same way.
    m = entry["mutator"]
    file = m["originalFilePath"]
    try:
        file = str(pathlib.Path(file).relative_to(root))
    except ValueError:
        pass
    desc = m["mutatorName"] + (" (no test reaches it)" if uncovered else "")
    return Survivor(file, m["originalStartLine"], desc)


def mutation_parse(root, out):
    p = _infection_log_path(root, out)
    if not p.exists():
        return Mutation(0, 0)
    data = json.loads(p.read_text())
    s = data["stats"]
    killed = s["killedCount"] + s["timeOutCount"] + s["errorCount"]
    survivors = [_survivor(root, e, False) for e in data.get("escaped", [])]
    survivors += [_survivor(root, e, True) for e in data.get("uncovered", [])]
    return Mutation(killed, s["totalMutantsCount"], survivors)


def lint(root, target, out):
    return "no test-specific lint exists for PHP (no PHPStan rule reports an assertion-free test)"


def audit_unavailable(root):
    return None if probe.which("composer") else "composer not installed"


def audit_nothing(root):
    # --locked audits composer.lock; a project that has never run `composer install` has none.
    return None if (pathlib.Path(root) / "composer.lock").exists() else \
        "nothing declared: no composer.lock — run composer install"


def audit_cmd(root):
    return ["composer", "audit", "--format=json", "--locked"]


def _advisory_line(name, a):
    ident = a.get("cve") or a.get("advisoryId")
    return f"{name} {a.get('affectedVersions', '')}: {ident} — {a.get('title', '')}".rstrip(" —")


def audit_findings(stdout, returncode):
    # `advisories` is a dict keyed by package name when there are findings, and PHP's own
    # json_encode turns an empty associative array into a list ([]) when there are none
    # (composer_audit_clean.json.README) — both shapes are handled.
    try:
        data, _ = json.JSONDecoder().raw_decode(stdout, stdout.index("{"))
        advisories = data.get("advisories") or {}
        items = advisories.items() if isinstance(advisories, dict) else []
        return [_advisory_line(name, a) for name, advs in items for a in advs]
    except (ValueError, KeyError, TypeError, AttributeError):
        return _UNREADABLE
