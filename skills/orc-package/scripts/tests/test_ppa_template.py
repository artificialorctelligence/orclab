"""ppa-copy-series.py is copied into a consuming project and run there against a real PPA. What
a defect in it does is publish a source with no binaries into a real series - which is exactly
what its preconditions exist to refuse - so every branch of main() is driven here against a
fake Launchpad that records what it was asked. Only the two login functions touch launchpadlib,
and those are tested against a fake of that module too. Two subprocess tests keep the contract
a shell sees: the substituted file is valid Python and answers --help and --check with
launchpadlib absent."""

import pathlib
import subprocess
import sys
import types

import pytest

# The real template, for the tests that read it as text or run it from a shell - under
# /orc-test analyze this file runs from mutmut's mutants/ copy, whose templates are rewritten.
_ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMPLATE = (
    (_ROOT.parent if _ROOT.name == "mutants" else _ROOT)
    / "ingredients" / "ppa" / "templates" / "ppa-copy-series.py"
)
FILLED = {
    "__OWNER__": "someone", "__PPA__": "theirppa", "__SOURCE__": "theirpkg",
    "__FROM_SERIES__": "noble", "__TO_SERIES__": "resolute",
}


# --- the contract a shell sees: subprocess, launchpadlib absent ---------------------------------

def instantiate(tmp_path):
    text = TEMPLATE.read_text()
    for placeholder, value in FILLED.items():
        text = text.replace(placeholder, value)
    assert "__" not in text.replace("__main__", "").replace("__name__", ""), \
        "every placeholder must be one of the five documented ones"
    out = tmp_path / "ppa-copy-series.py"
    out.write_text(text)
    return out


def run(script, *args, home):
    # -S and a bare PATH: launchpadlib must not be needed for these paths, and nothing may be
    # written into the real home directory.
    return subprocess.run(
        [sys.executable, "-S", str(script), *args], check=False, capture_output=True, text=True,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
    )


def test_substituted_file_answers_help_without_launchpadlib(tmp_path):
    script = instantiate(tmp_path)
    out = run(script, "--help", home=tmp_path)
    assert out.returncode == 0, out.stderr
    assert "--check" in out.stdout and "--dry-run" in out.stdout


def test_check_from_a_shell_reports_no_credentials_and_creates_nothing(tmp_path):
    script = instantiate(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    out = run(script, "--check", home=home)
    assert out.returncode == 1
    assert str(home / ".config" / "theirpkg" / "launchpad-credentials.txt") in out.stderr
    assert not list(home.rglob("*")), "--check must never create a file, let alone a credential"


# --- a fake Launchpad ----------------------------------------------------------------------------

class FakeBinary:
    def __init__(self, name):
        self.binary_package_name = name


class FakeSource:
    def __init__(self, binaries):
        self._binaries = binaries

    def getPublishedBinaries(self):
        return [FakeBinary(n) for n in self._binaries]


class FakeDistribution:
    def getSeries(self, name_or_version):
        return f"<series {name_or_version}>"


class FakePPA:
    def __init__(self, sources):
        self.distribution = FakeDistribution()
        self._sources = sources          # what getPublishedSources returns
        self.queries = []
        self.copies = []

    def getPublishedSources(self, **kw):
        self.queries.append(kw)
        return list(self._sources)

    def copyPackage(self, **kw):
        self.copies.append(kw)


class FakePerson:
    def __init__(self, ppa):
        self._ppa = ppa
        self.asked = []

    def getPPAByName(self, name):
        self.asked.append(name)
        return self._ppa


class FakeLaunchpad:
    def __init__(self, owner, ppa):
        self.person = FakePerson(ppa)
        self.people = {owner: self.person}


@pytest.fixture
def launchpad(ppa_template, monkeypatch):
    """Wires main() to a fake Launchpad and records which login path it took. `sources` is
    what the PPA reports as published in the from-series."""
    state = types.SimpleNamespace(anonymous=0, logged_in=[], ppa=None, lp=None)

    def wire(sources, owner="__OWNER__"):
        state.ppa = FakePPA(sources)
        state.lp = FakeLaunchpad(owner, state.ppa)

        def anonymously():
            state.anonymous += 1
            return state.lp

        def log_in(path):
            state.logged_in.append(path)
            return state.lp

        monkeypatch.setattr(ppa_template, "log_in_anonymously", anonymously)
        monkeypatch.setattr(ppa_template, "log_in", log_in)
        return state

    return wire


PUBLISHED = FakeSource(["theirpkg", "theirpkg-doc", "theirpkg"])   # a duplicate, on purpose
NO_BINARIES_YET = FakeSource([])


# --- --check -------------------------------------------------------------------------------------

def test_check_without_a_credential_exits_1_names_the_path_and_creates_nothing(ppa_template, tmp_path, capsys):
    creds = tmp_path / "creds.txt"
    assert ppa_template.main(["--check", "--credentials", str(creds)]) == 1
    err = capsys.readouterr().err
    assert f"no launchpad credentials at {creds}" in err
    assert "opens a browser exactly once" in err
    assert not creds.exists()


def test_check_with_a_credential_exits_0_and_never_prints_it(ppa_template, tmp_path, capsys):
    creds = tmp_path / "creds.txt"
    creds.write_text("oauth_token=not-a-real-token")
    assert ppa_template.main(["--check", "--credentials", str(creds)]) == 0
    out = capsys.readouterr()
    assert f"launchpad credentials present: {creds}" in out.out
    assert "not-a-real-token" not in out.out + out.err


def test_an_empty_credential_file_does_not_count(ppa_template, tmp_path):
    creds = tmp_path / "creds.txt"
    creds.write_text("")
    assert ppa_template.has_credentials(creds) is False
    assert ppa_template.main(["--check", "--credentials", str(creds)]) == 1


def test_default_credential_path_is_per_project_under_xdg_config(ppa_template, tmp_path, monkeypatch):
    assert ppa_template.credentials_path(None) == (
        tmp_path / ".config" / ppa_template.SOURCE / "launchpad-credentials.txt"
    )
    assert ppa_template.credentials_path("/elsewhere/c.txt") == pathlib.Path("/elsewhere/c.txt")


def test_xdg_config_home_overrides_the_default_location(load_template, monkeypatch, tmp_path):
    # DEFAULT_CREDENTIALS is fixed at import, so this loads the template with the variable set.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    mod = load_template("ingredients/ppa/templates/ppa-copy-series.py")
    assert mod.DEFAULT_CREDENTIALS == tmp_path / "xdg" / mod.SOURCE / "launchpad-credentials.txt"


# --- --version is required past --check ----------------------------------------------------------

def test_version_is_required_unless_check(ppa_template, capsys):
    with pytest.raises(SystemExit) as e:
        ppa_template.main(["--dry-run"])
    assert e.value.code == 2
    assert "--version is required unless --check" in capsys.readouterr().err


# --- dry run: reads only, anonymous session, never copies ----------------------------------------

def test_dry_run_refuses_a_source_that_is_not_published(ppa_template, launchpad, capsys):
    lp = launchpad(sources=[])
    assert ppa_template.main(["--version", "0.3.0-1", "--dry-run"]) == 1
    err = capsys.readouterr().err
    assert "__SOURCE__ 0.3.0-1 is not Published in __FROM_SERIES__" in err
    assert "wait for the build to succeed" in err
    assert lp.anonymous == 1 and lp.logged_in == []
    assert lp.ppa.copies == []


def test_the_published_source_lookup_is_exact_and_in_the_from_series(ppa_template, launchpad):
    lp = launchpad(sources=[PUBLISHED])
    ppa_template.main(["--version", "0.3.0-1", "--dry-run"])
    assert lp.ppa.queries == [{
        "source_name": "__SOURCE__", "version": "0.3.0-1",
        "distro_series": "<series __FROM_SERIES__>", "status": "Published", "exact_match": True,
    }]
    assert lp.lp.person.asked == ["__PPA__"]


def test_dry_run_refuses_a_published_source_with_no_built_binaries(ppa_template, launchpad, capsys):
    lp = launchpad(sources=[NO_BINARIES_YET])
    assert ppa_template.main(["--version", "0.3.0-1", "--dry-run"]) == 1
    err = capsys.readouterr().err
    assert "published in __FROM_SERIES__ but has no built binaries yet" in err
    assert lp.ppa.copies == []


def test_dry_run_prints_the_plan_and_copies_nothing(ppa_template, launchpad, capsys):
    lp = launchpad(sources=[PUBLISHED])
    assert ppa_template.main(["--version", "0.3.0-1", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "source:   __SOURCE__ 0.3.0-1 (__FROM_SERIES__, Published)" in out
    assert "binaries: theirpkg, theirpkg-doc" in out       # sorted, deduplicated
    assert "copy to:  __TO_SERIES__ (Release pocket, binaries included)" in out
    assert out.rstrip().endswith("dry run - nothing copied")
    assert lp.ppa.copies == []
    assert lp.anonymous == 1 and lp.logged_in == []


# --- the real run: authenticated, and the copy request itself ------------------------------------

def test_real_run_copies_with_binaries_into_the_release_pocket(ppa_template, launchpad, tmp_path, capsys):
    lp = launchpad(sources=[PUBLISHED])
    creds = tmp_path / "creds.txt"
    creds.write_text("oauth_token=x")
    assert ppa_template.main(["--version", "0.3.0-1", "--credentials", str(creds)]) == 0
    assert lp.ppa.copies == [{
        "from_archive": lp.ppa, "source_name": "__SOURCE__", "version": "0.3.0-1",
        "from_series": "__FROM_SERIES__", "to_series": "__TO_SERIES__",
        "to_pocket": "Release", "include_binaries": True,
    }]
    assert lp.logged_in == [creds] and lp.anonymous == 0
    out = capsys.readouterr().out
    assert "copy requested: __SOURCE__ 0.3.0-1 __FROM_SERIES__ -> __TO_SERIES__" in out
    assert "https://launchpad.net/~__OWNER__/+archive/ubuntu/__PPA__/+packages" in out
    assert "browser will open" not in out


def test_real_run_warns_that_a_browser_will_open_when_no_credential_is_cached(ppa_template, launchpad, tmp_path, capsys):
    lp = launchpad(sources=[PUBLISHED])
    creds = tmp_path / "absent.txt"
    assert ppa_template.main(["--version", "0.3.0-1", "--credentials", str(creds)]) == 0
    assert f"no cached credential at {creds} - a browser will open once to authorize" in capsys.readouterr().out
    assert lp.logged_in == [creds]


def test_real_run_refuses_before_copying_when_preconditions_fail(ppa_template, launchpad, tmp_path):
    lp = launchpad(sources=[NO_BINARIES_YET])
    creds = tmp_path / "creds.txt"
    creds.write_text("oauth_token=x")
    assert ppa_template.main(["--version", "0.3.0-1", "--credentials", str(creds)]) == 1
    assert lp.ppa.copies == []


def test_owner_ppa_and_series_can_be_overridden_on_the_command_line(ppa_template, launchpad, tmp_path):
    lp = launchpad(sources=[PUBLISHED], owner="other-owner")
    creds = tmp_path / "creds.txt"
    creds.write_text("oauth_token=x")
    rc = ppa_template.main([
        "--version", "1.0-1", "--credentials", str(creds), "--owner", "other-owner",
        "--ppa", "other-ppa", "--source", "otherpkg", "--from-series", "jammy", "--to-series", "noble",
    ])
    assert rc == 0
    assert lp.lp.person.asked == ["other-ppa"]
    assert lp.ppa.queries[0]["source_name"] == "otherpkg"
    assert lp.ppa.queries[0]["distro_series"] == "<series jammy>"
    assert lp.ppa.copies[0]["from_series"] == "jammy" and lp.ppa.copies[0]["to_series"] == "noble"


# --- the two functions that touch launchpadlib, against a fake of it -----------------------------

@pytest.fixture
def fake_launchpadlib(monkeypatch):
    calls = []

    class Launchpad:
        @staticmethod
        def login_anonymously(app, service, version=None):
            calls.append(("anonymous", app, service, version))
            return "anon-session"

        @staticmethod
        def login_with(app, service, version=None, credentials_file=None):
            calls.append(("login", app, service, version, credentials_file))
            if credentials_file and getattr(Launchpad, "writes_credential", True):
                pathlib.Path(credentials_file).write_text("oauth_token=fresh")
            return "auth-session"

    pkg = types.ModuleType("launchpadlib")
    mod = types.ModuleType("launchpadlib.launchpad")
    mod.Launchpad = Launchpad
    pkg.launchpad = mod
    monkeypatch.setitem(sys.modules, "launchpadlib", pkg)
    monkeypatch.setitem(sys.modules, "launchpadlib.launchpad", mod)
    Launchpad.calls = calls
    return Launchpad


def test_anonymous_login_is_the_production_devel_api_under_the_projects_app_name(ppa_template, fake_launchpadlib):
    assert ppa_template.log_in_anonymously() == "anon-session"
    assert fake_launchpadlib.calls == [("anonymous", "__SOURCE__-release", "production", "devel")]


def test_login_creates_the_credential_directory_and_locks_the_file_down(ppa_template, fake_launchpadlib, tmp_path):
    creds = tmp_path / "deep" / "er" / "creds.txt"
    assert ppa_template.log_in(creds) == "auth-session"
    assert fake_launchpadlib.calls == [("login", "__SOURCE__-release", "production", "devel", str(creds))]
    assert creds.read_text() == "oauth_token=fresh"
    assert oct(creds.stat().st_mode & 0o777) == "0o600"


def test_login_tolerates_a_session_that_wrote_no_credential_file(ppa_template, fake_launchpadlib, tmp_path):
    fake_launchpadlib.writes_credential = False
    creds = tmp_path / "creds.txt"
    assert ppa_template.log_in(creds) == "auth-session"
    assert not creds.exists()


def test_find_published_source_returns_the_first_match_or_none(ppa_template):
    ppa = FakePPA([PUBLISHED, NO_BINARIES_YET])
    assert ppa_template.find_published_source(ppa, "p", "1.0-1", "noble") is PUBLISHED
    assert ppa_template.find_published_source(FakePPA([]), "p", "1.0-1", "noble") is None


def test_built_binaries_are_sorted_and_deduplicated(ppa_template):
    assert ppa_template.built_binaries(FakeSource(["z-tool", "a-lib", "z-tool", "m-doc"])) == ["a-lib", "m-doc", "z-tool"]
    assert ppa_template.built_binaries(NO_BINARIES_YET) == []
