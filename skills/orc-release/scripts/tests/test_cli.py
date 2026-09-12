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
    # Corrupt mid-release: [project] stays (detect() still finds a real version-holding file)
    # but its version field is gone, so write_version has nowhere to write the rollback. (Not
    # dropping [project] itself: detect() now requires it, so that would just make the file
    # invisible to abort rather than exercise a failed rollback - see versionfiles.detect.)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
    assert main(["--root", root, "abort"]) == 0
    out = capsys.readouterr().out
    assert "NOT rolled back" in out
    assert "pyproject.toml" in out
    assert "no version field in [project]" in out
    assert "Rolled back to" not in out
    # And the file provably still holds the corrupted content - no rollback actually happened.
    assert "version" not in (tmp_path / "pyproject.toml").read_text()


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


# --- Fix round 2 -------------------------------------------------------------


def _finish_every_step(root):
    for n in (1, 2, 3):
        main(["--root", root, "complete", str(n)])


def test_finish_refuses_while_a_step_is_outstanding_and_names_it(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "complete", "1"])
    assert main(["--root", root, "finish"]) == 1
    err = capsys.readouterr().err
    assert "step 2" in err
    assert "Upload" in err
    assert load_state(root) is not None


def test_finish_closes_a_completed_release_and_lets_the_next_one_start(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    _finish_every_step(root)
    assert main(["--root", root, "finish"]) == 0
    out = capsys.readouterr().out
    assert "0.2.0" in out
    assert "Upload" in out  # the irreversible step is named in the summary
    assert load_state(root) is None
    assert not (tmp_path / STATE_PATH).exists()
    # The whole point: a shipped release no longer blocks the next one forever.
    assert main(["--root", root, "start", "0.3.0"]) == 0


def test_finish_reports_skipped_steps_with_their_reasons(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "complete", "1"])
    main(["--root", root, "complete", "2"])
    main(["--root", root, "skip", "3", "--reason", "verified during install-test"])
    assert main(["--root", root, "finish"]) == 0
    assert "verified during install-test" in capsys.readouterr().out


def test_finish_never_rolls_a_version_file_back(tmp_path):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "version-set", "0.2.0"])
    _finish_every_step(root)
    assert main(["--root", root, "finish"]) == 0
    assert 'version = "0.2.0"' in (tmp_path / "pyproject.toml").read_text()


def test_steps_warns_on_stderr_about_non_contiguous_numbering_but_still_returns_them(
    tmp_path, capsys
):
    root = setup_project(
        tmp_path, doc="# R\n\n## 1. One\n\nx\n\n## 2. Two\n\nx\n\n## 5. Five\n\nx\n"
    )
    assert main(["--root", root, "steps"]) == 0
    captured = capsys.readouterr()
    assert "1, 2, 5" in captured.err
    assert [s["number"] for s in json.loads(captured.out)] == [1, 2, 5]


def test_steps_warns_when_an_unclosed_fence_is_hiding_the_rest_of_the_release(tmp_path, capsys):
    root = setup_project(tmp_path, doc="# R\n\n## 1. One\n\n```\n\n## 2. Two\n\n## 3. Three\n")
    assert main(["--root", root, "steps"]) == 0
    captured = capsys.readouterr()
    assert "never closed" in captured.err
    assert [s["number"] for s in json.loads(captured.out)] == [1]


def test_status_surfaces_the_numbering_warning_too(tmp_path, capsys):
    root = setup_project(
        tmp_path, doc="# R\n\n## 1. One\n\nx\n\n## 3. Three\n\nx\n"
    )
    assert main(["--root", root, "status"]) == 0
    assert "contiguous" in capsys.readouterr().err


def test_an_inline_backtick_fence_does_not_hide_the_rest_of_the_steps(tmp_path, capsys):
    root = setup_project(
        tmp_path,
        doc=(
            "# R\n\n## 1. Bump\n\nUse the ``` fence marker in prose.\n\n"
            "## 2. Test\n\nx\n\n## 3. Upload\n\n**Irreversible.**\n"
        ),
    )
    assert main(["--root", root, "steps"]) == 0
    assert [s["number"] for s in json.loads(capsys.readouterr().out)] == [1, 2, 3]


def test_version_set_writes_nothing_when_a_detected_file_is_unparseable(tmp_path, capsys):
    root = setup_project(tmp_path)
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin/plugin.json").write_text('{"name": "x", "version":')
    assert main(["--root", root, "version-set", "0.2.0"]) == 1
    err = capsys.readouterr().err
    assert "plugin.json" in err
    assert "nothing was written" in err
    assert 'version = "0.1.0"' in (tmp_path / "pyproject.toml").read_text()


def test_version_verify_fails_when_the_files_agree_but_miss_the_release_target(tmp_path, capsys):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    # Every file consistent at 0.1.0 - what a bad merge looks like mid-release.
    assert main(["--root", root, "version-verify"]) == 1
    err = capsys.readouterr().err
    assert "0.1.0" in err
    assert "0.2.0" in err


def test_version_verify_passes_against_the_release_target_once_set(tmp_path):
    root = setup_project(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "version-set", "0.2.0"])
    assert main(["--root", root, "version-verify"]) == 0


def test_a_subcommand_run_from_a_subdirectory_still_finds_the_document(tmp_path, monkeypatch, capsys):
    root = setup_project(tmp_path)
    (tmp_path / ".git").mkdir()
    sub = tmp_path / "src" / "deep"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    assert main(["steps"]) == 0  # no --root: must walk up to the git root
    assert [s["number"] for s in json.loads(capsys.readouterr().out)] == [1, 2, 3]


def test_a_subproject_with_its_own_document_wins_over_the_enclosing_git_root(
    tmp_path, monkeypatch, capsys
):
    # A monorepo package (or a vendored subproject) carrying its own RELEASING.md is its own
    # release unit. Stopping at the enclosing .git would tell it its document doesn't exist.
    (tmp_path / ".git").mkdir()
    (tmp_path / "RELEASING-not-this-one.md").write_text("# enclosing repo, no release doc\n")
    pkg = tmp_path / "packages" / "foo"
    pkg.mkdir(parents=True)
    setup_project(pkg)
    monkeypatch.chdir(pkg)
    assert main(["steps"]) == 0
    assert [s["number"] for s in json.loads(capsys.readouterr().out)] == [1, 2, 3]


def test_a_subdirectory_of_a_subproject_still_finds_the_subproject(
    tmp_path, monkeypatch, capsys
):
    (tmp_path / ".git").mkdir()
    pkg = tmp_path / "packages" / "foo"
    pkg.mkdir(parents=True)
    setup_project(pkg)
    deep = pkg / "src" / "deep"
    deep.mkdir(parents=True)
    monkeypatch.chdir(deep)
    assert main(["steps"]) == 0
    assert [s["number"] for s in json.loads(capsys.readouterr().out)] == [1, 2, 3]


def test_abort_says_so_when_it_leaves_the_version_files_disagreeing(tmp_path, capsys):
    root = setup_project(tmp_path)
    add_debian_changelog(tmp_path)
    main(["--root", root, "start", "0.2.0"])
    main(["--root", root, "version-set", "0.2.0", "--changelog-body", "* Release."])
    assert main(["--root", root, "abort"]) == 0
    out = capsys.readouterr().out
    # pyproject.toml rolls back to 0.1.0; debian/changelog's entry is deliberately left at
    # 0.2.0 - abort must name that disagreement, not just the rollback.
    assert "DISAGREE" in out
    assert "pyproject.toml: 0.1.0" in out
    assert "debian/changelog: 0.2.0" in out


def test_abort_names_the_changelog_md_entry_it_does_not_touch(tmp_path, capsys):
    root = setup_project(tmp_path)
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n")
    main(["--root", root, "start", "0.2.0"])
    assert main(["--root", root, "abort"]) == 0
    assert "CHANGELOG.md" in capsys.readouterr().out
