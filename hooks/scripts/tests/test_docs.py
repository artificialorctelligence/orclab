# hooks/scripts/tests/test_docs.py
"""The user-facing pages under docs/commands/ (spec: 2026-09-13-orclab-v20-command-docs-design.md).
Shape and presence only; a page saying what its command does today is a discipline, not a test."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
PAGES = sorted((ROOT / "docs" / "commands").glob("*.md"), key=lambda p: p.stem)
HEADINGS = [
    "## What it's for",
    "## What you type",
    "## What it will ask you",
    "## What it changes",
    "## What it will never do without asking",
]


def _headings(text):
    return [line.rstrip() for line in text.splitlines() if line.startswith("## ")]


def test_every_page_has_exactly_the_five_headings_in_order():
    for page in PAGES:
        assert _headings(page.read_text()) == HEADINGS, page.name


def test_every_page_is_a_command_that_exists():
    for page in PAGES:
        assert (ROOT / "skills" / page.stem / "SKILL.md").is_file(), page.name


def test_no_page_points_the_reader_at_the_workshop():
    for page in PAGES:
        text = page.read_text()
        # BACKLOG.md is not here: /orc-todo edits the user's own; pointing at Orclab's is the reviewer's call
        for banned in ["CLAUDE.md", "SKILL.md", "docs/superpowers"]:
            assert banned not in text, f"{page.name} mentions {banned}"


def test_every_command_has_a_page():
    commands = sorted(p.parent.name for p in (ROOT / "skills").glob("orc*/SKILL.md"))
    assert [p.stem for p in PAGES] == commands


def test_readme_links_every_page():
    readme = (ROOT / "README.md").read_text()
    for page in PAGES:
        assert f"docs/commands/{page.name}" in readme, page.name


def _cloud_hook():
    return (ROOT / ".claude" / "hooks" / "session-start.sh").read_text()


def test_cloud_session_gets_both_the_skills_and_the_plugin_hooks():
    """A repo's .claude/skills/ carries skills only - measured 2026-09-24, a bare
    `env` dump ran unblocked in such a session while secret_guard sat on disk. The
    SessionStart hook loads the checkout as a plugin so hooks/hooks.json registers.
    Dropping either one silently loses something."""
    skills = ROOT / ".claude" / "skills"
    linked = sorted(p.name for p in skills.iterdir())
    shipped = sorted(p.name for p in (ROOT / "skills").iterdir() if p.is_dir())
    assert linked == shipped, "every shipped skill needs a .claude/skills/ symlink"
    for p in skills.iterdir():
        assert p.is_symlink(), f"{p.name} must be a symlink, not a copy"

    settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
    cmd = settings["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert cmd.endswith(".claude/hooks/session-start.sh"), cmd
    assert "ln -sfn" in _cloud_hook() and "$HOME/.claude/skills" in _cloud_hook()


def test_cloud_hook_stays_out_of_the_way_on_a_developers_machine():
    """It exists only because a cloud container starts empty; a local checkout has
    the plugin installed properly and must not get a second copy."""
    assert 'CLAUDE_CODE_REMOTE:-}" != "true"' in _cloud_hook()


def test_orc_reload_checks_for_a_cloud_session_before_the_local_steps():
    """Steps 1-5 navigate by known_marketplaces.json, installed_plugins.json and a
    marketplace clone. None of those exists or governs loading in a cloud session, so
    followed there Step 2 declares a running plugin 'never registered' and stops."""
    s = (ROOT / "skills" / "orc-reload" / "SKILL.md").read_text()
    before_step_1 = s[:s.index("## Step 1")]
    assert "CLAUDE_CODE_REMOTE" in before_step_1, "the cloud check must come first"
    for phrase in ["Nothing is installed", "@{u}..HEAD", "pushed"]:
        assert phrase in before_step_1, phrase


def test_orc_reload_page_tells_a_cloud_user_the_remedy_is_push_not_reinstall():
    page = (ROOT / "docs" / "commands" / "orc-reload.md").read_text()
    assert "cloud session" in page and "commit and push" in page


def test_readme_does_not_offer_only_the_local_install():
    """The local steps report success and change nothing in a cloud session - measured
    2026-09-24. A README offering them alone sends a cloud user somewhere with no exit."""
    readme = (ROOT / "README.md").read_text()
    install = readme[readme.index("## Installing"):readme.index("## Commands")]
    for phrase in ["cloud session", "claude.ai account", ".claude/skills/",
                   "session-start.sh"]:
        assert phrase in install, phrase
    assert install.index("/plugin install orclab@orclab") < install.index("In a cloud session")
