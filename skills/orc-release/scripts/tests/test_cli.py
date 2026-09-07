import json
import textwrap

from orc_release.cli import main
from orc_release.state import STATE_PATH, load_state


DOC = textwrap.dedent(
    """
    # Cutting a release

    ## 1. Pick a version

    Edit the files.

    ## 2. Upload

    **Irreversible.** Once uploaded it cannot be undone.

    ## 3. Verify

    **Performed by hand.** Check it works.
    """
)


def setup_project(tmp_path, doc=DOC):
    (tmp_path / "RELEASING.md").write_text(doc)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "0.1.0"\n'
    )
    return str(tmp_path)


DEBIAN_CHANGELOG_TEXT = (
    "orclab (0.1.0-1) noble; urgency=medium\n"
    "\n"
    "  * Initial.\n"
    "\n"
    " -- Orclab <orc@example.com>  Wed, 26 Aug 2026 21:02:48 -0500\n"
)


def add_debian_changelog(tmp_path):
    (tmp_path / "debian").mkdir()
    (tmp_path / "debian/changelog").write_text(DEBIAN_CHANGELOG_TEXT)


def test_steps_subcommand_emits_parseable_json(tmp_path, capsys):
    root = setup_project(tmp_path)
    assert main(["--root", root, "steps"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert [s["number"] for s in data] == [1, 2, 3]
    assert data[1]["is_irreversible"] is True
    assert data[2]["is_manual"] is True


def test_steps_reports_plainly_when_there_is_no_releasing_md(tmp_path, capsys):
    assert main(["--root", str(tmp_path), "steps"]) == 1
    assert "RELEASING.md" in capsys.readouterr().err


def test_status_with_no_release_says_so(tmp_path, capsys):
    root = setup_project(tmp_path)
    assert main(["--root", root, "status"]) == 0
    assert "no release in progress" in capsys.readouterr().out.lower()


def test_start_records_state_with_the_doc_hash(tmp_path):
    root = setup_project(tmp_path)
    assert main(["--root", root, "start", "0.2.0"]) == 0
    state = load_state(root)
    assert state["version"] == "0.2.0"
    assert state["previous_version"] == "0.1.0"
    assert state["doc_hash"]


def test_start_refuses_when_a_release_is_already_in_progress(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    assert main(["--root", root, "start", "0.3.0"]) == 1
    assert "already in progress" in capsys.readouterr().err


def test_status_reports_the_next_step(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "complete", "1"])
    main(["--root", root, "status"])
    assert "2" in capsys.readouterr().out


def test_complete_records_irreversibility_from_the_document(tmp_path):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "complete", "2"])
    entry = [c for c in load_state(root)["completed"] if c["number"] == 2][0]
    assert entry["irreversible"] is True


def test_skip_requires_a_reason(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    assert main(["--root", root, "skip", "1", "--reason", "  "]) == 1
    assert "reason" in capsys.readouterr().err


def test_skip_records_the_reason(tmp_path):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "skip", "1", "--reason", "done by hand earlier"])
    assert load_state(root)["skipped"][0]["reason"] == "done by hand earlier"


def test_status_warns_when_the_document_changed_mid_release(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    (tmp_path / "RELEASING.md").write_text(DOC + "\n## 4. A new step\n\nInserted later.\n")
    main(["--root", root, "status"])
    out = capsys.readouterr().out.lower()
    assert "changed" in out


def test_version_set_writes_and_verify_confirms(tmp_path, capsys):
    root = setup_project(tmp_path)
    assert main(["--root", root, "version-set", "0.2.0"]) == 0
    assert 'version = "0.2.0"' in (tmp_path / "pyproject.toml").read_text()
    assert main(["--root", root, "version-verify"]) == 0
    assert "consistent" in capsys.readouterr().out.lower()


def test_version_verify_fails_on_a_real_mismatch(tmp_path, capsys):
    root = setup_project(tmp_path)
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin/plugin.json").write_text('{"name": "x", "version": "9.9.9"}')
    assert main(["--root", root, "version-verify"]) == 1
    assert "9.9.9" in capsys.readouterr().err


def test_version_rollback_restores_the_previous_version(tmp_path):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "version-set", "0.2.0"])
    assert main(["--root", root, "version-rollback"]) == 0
    assert 'version = "0.1.0"' in (tmp_path / "pyproject.toml").read_text()


def test_abort_reports_a_completed_irreversible_step_as_standing(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "complete", "2"])
    assert main(["--root", root, "abort"]) == 0
    out = capsys.readouterr().out.lower()
    assert "cannot" in out or "not undone" in out
    assert "upload" in out
    assert load_state(root) is None


def test_abort_on_a_document_with_no_markers_says_it_cannot_determine(tmp_path, capsys):
    root = setup_project(
        tmp_path, doc="# R\n\n## 1. One\n\nDo it.\n\n## 2. Two\n\nDo it.\n"
    )
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "complete", "1"])
    main(["--root", root, "abort"])
    assert "cannot determine" in capsys.readouterr().out.lower()


def test_abort_with_no_release_in_progress_is_reported_not_crashed(tmp_path, capsys):
    root = setup_project(tmp_path)
    assert main(["--root", root, "abort"]) == 1
    assert "no release in progress" in capsys.readouterr().err.lower()


def test_complete_on_an_already_skipped_step_is_reported_not_crashed(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "skip", "1", "--reason", "done by hand earlier"])
    assert main(["--root", root, "complete", "1"]) == 1
    err = capsys.readouterr().err
    assert "skipped" in err.lower()


# --- Fix round 1 -------------------------------------------------------------


def test_version_set_is_atomic_when_changelog_body_is_missing(tmp_path, capsys):
    root = setup_project(tmp_path)
    add_debian_changelog(tmp_path)
    assert main(["--root", root, "version-set", "0.3.0"]) == 1
    assert "changelog-body" in capsys.readouterr().err
    # Nothing was written - not pyproject.toml (detected and validated before), not the
    # changelog either.
    assert 'version = "0.1.0"' in (tmp_path / "pyproject.toml").read_text()
    assert "orclab (0.1.0-1)" in (tmp_path / "debian/changelog").read_text()
    assert "0.3.0" not in (tmp_path / "debian/changelog").read_text()


def test_abort_reports_a_failed_rollback_as_not_rolled_back(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    # Corrupt the [project] section mid-release so write_version cannot find it to roll back.
    (tmp_path / "pyproject.toml").write_text('name = "x"\nversion = "0.1.0"\n')
    assert main(["--root", root, "abort"]) == 0
    out = capsys.readouterr().out
    assert "NOT rolled back" in out
    assert "pyproject.toml" in out
    assert "no [project] section" in out
    assert "Rolled back to" not in out
    # And the file provably still holds the corrupted content - no rollback actually happened.
    assert "[project]" not in (tmp_path / "pyproject.toml").read_text()


def test_abort_reports_a_successful_rollback(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "version-set", "0.2.0"])
    assert main(["--root", root, "abort"]) == 0
    out = capsys.readouterr().out
    assert "Rolled back to 0.1.0" in out
    assert "pyproject.toml" in out
    assert 'version = "0.1.0"' in (tmp_path / "pyproject.toml").read_text()


def test_abort_changelog_note_is_absent_when_this_release_never_wrote_it(tmp_path, capsys):
    root = setup_project(tmp_path)
    add_debian_changelog(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    assert main(["--root", root, "abort"]) == 0
    assert "left in place" not in capsys.readouterr().out


def test_abort_changelog_note_is_present_when_this_release_wrote_it(tmp_path, capsys):
    root = setup_project(tmp_path)
    add_debian_changelog(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "version-set", "0.2.0", "--changelog-body", "* Release."])
    assert main(["--root", root, "abort"]) == 0
    assert "left in place" in capsys.readouterr().out


def test_complete_warns_on_stderr_when_the_document_changed_but_still_succeeds(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    (tmp_path / "RELEASING.md").write_text(DOC + "\n## 4. A new step\n\nInserted later.\n")
    assert main(["--root", root, "complete", "1"]) == 0
    err = capsys.readouterr().err.lower()
    assert "warning" in err
    assert "shifted" in err


def test_skip_warns_on_stderr_when_the_document_changed_but_still_succeeds(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    (tmp_path / "RELEASING.md").write_text(DOC + "\n## 4. A new step\n\nInserted later.\n")
    assert main(["--root", root, "skip", "1", "--reason", "already done"]) == 0
    err = capsys.readouterr().err.lower()
    assert "warning" in err
    assert "shifted" in err
