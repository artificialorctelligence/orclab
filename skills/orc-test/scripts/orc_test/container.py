"""A project that runs its toolchain in a container (v23). The record is compose.yaml at the
project root with a service named `orclab` — committed, so a clone keeps the opt-in; nothing
under .orclab/ can serve, that directory is git-ignored. Inside, the project is mounted at its
own host path, so every path in every report is valid on both sides and nothing is translated."""

import pathlib
import re
import shutil
from dataclasses import dataclass

import yaml

RUNNERS = ("podman", "docker")     # default order when .orclab/test.yaml names none — SKILL.md "Containers" says why
SERVICE = "orclab"


@dataclass(frozen=True)
class Container:
    root: pathlib.Path
    runner: str | None          # None: the engine is not on PATH — the caller says so, never runs on the host


def detect(root, cfg):
    """The project's Container, or None when it is not containerised or this checkout opted out."""
    root = pathlib.Path(root)
    if cfg.get("container") is False or not _has_service(root / "compose.yaml"):
        return None
    wanted = cfg.get("runner")
    names = (wanted,) if wanted else RUNNERS
    return Container(root, next((n for n in names if shutil.which(n)), None))


def _has_service(path):
    try:
        data = yaml.safe_load(path.read_text()) if path.is_file() else None
    except yaml.YAMLError:
        return False
    return isinstance(data, dict) and isinstance(data.get("services"), dict) and SERVICE in data["services"]


def wrap(c, cmd, cwd):
    # -T: no pseudo-tty (stdout is a pipe); --workdir: the same absolute path as on the host
    return [c.runner, "compose", "run", "--rm", "-T", "--workdir", str(cwd), SERVICE, *cmd]


def build_cmd(c):
    return [c.runner, "compose", "build", SERVICE]


# podman-compose 1.0.6 (Mint 22.3's apt) logs podman's own status as "exit code: N" and exits 0
# regardless — compose_build discards build_one's result; 1.6.0 returns it. Seen live
# 2026-09-20: FROM no-such-image:0 built "successfully" and the tests ran in the stale image.
_LOGGED_EXIT = re.compile(r"^exit code: (\d+)$", re.MULTILINE)


def build_failed(cp):
    """True when the build failed — by the engine's exit code, or by the status podman-compose
    1.0.6 logs and then throws away."""
    logged = _LOGGED_EXIT.findall(cp.stdout or "")
    return cp.returncode != 0 or any(int(n) != 0 for n in logged)
