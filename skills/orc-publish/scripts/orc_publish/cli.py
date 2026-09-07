"""/orc-publish CLI: resolve a selection, execute it, and report results.

This module never prompts for confirmation itself - --dry-run resolves and prints only,
normal mode resolves, prints, and executes immediately. The conversational safety gate
("always dry-run first, get an explicit yes, then run for real") lives in SKILL.md, which
calls this script twice: once with --dry-run, once without, once the user has confirmed.
"""

import argparse
import subprocess
import sys

from .selection import SelectionError, resolve_selection, resolve_token
from .tree import load_tree


def render_filename(template, version):
    """Render a leaf's filename_template for a given version string, or None if unset."""
    return template.replace("<version>", version) if template else None


def build_plan(channel_root, tokens):
    """Resolve CLI selection tokens against the channel tree to a list of leaf Nodes."""
    return resolve_selection(channel_root, tokens)


def format_plan(leaves):
    lines = []
    for leaf in leaves:
        action = leaf.action or "(no action set)"
        lines.append(f"{leaf.dotted_path}: {action}")
    return "\n".join(lines)


def run_for(distro_root, distro_path):
    """--for: report which channel path a distro leaf points at, or that none is set."""
    node = resolve_token(distro_root, distro_path)
    if not node.is_leaf:
        raise SelectionError(f"'{distro_path}' is not a single distro target - select a leaf")
    channel = node.channel
    if channel:
        return f"{node.dotted_path} -> {channel}"
    return f"{node.dotted_path}: no channel set (known target, not yet actionable)"


def execute_plan(leaves):
    """Run each leaf's action. An independent failure doesn't stop the remaining leaves.

    Returns a list of (leaf, status, detail) - status is "success", "failed", or
    "not attempted"; detail is the real error text on failure, empty otherwise.
    """
    results = []
    for leaf in leaves:
        if not leaf.action:
            results.append((leaf, "not attempted", "no action set"))
            continue
        try:
            subprocess.run(
                leaf.action, shell=True, check=True, capture_output=True, text=True
            )
            results.append((leaf, "success", ""))
        except subprocess.CalledProcessError as e:
            detail = (e.stderr or "").strip() or str(e)
            results.append((leaf, "failed", detail))
    return results


def format_summary(results):
    lines = []
    for leaf, status, detail in results:
        line = f"{leaf.dotted_path}: {status}"
        if detail:
            line += f" ({detail})"
        lines.append(line)
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="orc-publish")
    parser.add_argument("selection", nargs="*")
    parser.add_argument("--for", dest="for_distro")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--channels", default=".orclab/publish/channels.yaml")
    parser.add_argument("--distro", default=".orclab/publish/distro.yaml")
    args = parser.parse_args(argv)

    if args.for_distro:
        try:
            distro_root = load_tree(args.distro)
            print(run_for(distro_root, args.for_distro))
        except SelectionError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        return 0

    channel_root = load_tree(args.channels)
    try:
        leaves = build_plan(channel_root, args.selection)
    except SelectionError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(format_plan(leaves))

    if args.dry_run:
        return 0

    results = execute_plan(leaves)
    print(format_summary(results))
    return 0 if all(status != "failed" for _, status, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
