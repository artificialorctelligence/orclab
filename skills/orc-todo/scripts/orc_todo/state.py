"""Shared state for concurrent Orclab agents: where it lives, and the lock that guards it.

Everything here hangs off `git rev-parse --git-common-dir`, which resolves to the SAME
directory from the main checkout and from every worktree. That is the whole design: on
2026-09-08 two sessions each held their own copy of BACKLOG.md, so a lock on "the file" would
have locked two different files and protected nothing. See BACKLOG #22 and #25.

The directory is outside every working tree, so nothing here appears in a diff, merges, or
conflicts.
"""

import contextlib
import datetime
import json
import os
import pathlib
import subprocess
import time


class NotAGitRepo(Exception):
    """Raised rather than guessing a location. Every caller degrades honestly instead."""


class LockUnavailable(Exception):
    """The lock could not be taken. `.info` describes who holds it, when it can be read."""

    def __init__(self, message, info=None):
        super().__init__(message)
        self.info = info


def git_common_dir(cwd=None):
    """The shared .git directory, absolute. Identical from a worktree and its main checkout."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise NotAGitRepo(f"not a git repository: {cwd or os.getcwd()}") from e
    if not out:
        raise NotAGitRepo(f"not a git repository: {cwd or os.getcwd()}")
    base = pathlib.Path(cwd) if cwd else pathlib.Path.cwd()
    return (base / out).resolve()


def shared_dir(cwd=None):
    """<git-common-dir>/orclab, created on demand."""
    d = git_common_dir(cwd) / "orclab"
    d.mkdir(parents=True, exist_ok=True)
    return d


def canonical_root(cwd=None):
    """The main checkout - the working tree that owns the .git directory."""
    return git_common_dir(cwd).parent


def lock_path(cwd=None):
    return shared_dir(cwd) / "lock"


def _counters_path(cwd=None):
    return shared_dir(cwd) / "counters.json"


def _pid_alive(pid):
    if pid is None:
        return True  # unreadable holder: assume live, never invent grounds to clear it
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def lock_info(cwd=None):
    """Who holds the lock, or None when it is free.

    A corrupt or half-written lock reports pid None and alive True. Reading "no lock" from a
    file that exists would be the one failure mode a lock cannot have.
    """
    path = lock_path(cwd)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (ValueError, OSError):
        data = {}
    pid = data.get("pid")
    started = data.get("started")
    age = None
    if started:
        try:
            age = (
                datetime.datetime.now().astimezone()
                - datetime.datetime.fromisoformat(started)
            ).total_seconds()
        except ValueError:
            age = None
    return {
        "pid": pid,
        "started": started,
        "description": data.get("description"),
        "alive": _pid_alive(pid),
        "age_seconds": age,
    }


@contextlib.contextmanager
def held(description, cwd=None, timeout=10.0, poll=0.2):
    """Hold the lock for the duration of the block.

    Acquisition is one atomic os.open(O_CREAT|O_EXCL). "Check whether it is locked, then lock"
    is a time-of-check-to-time-of-use race - two processes both observe it free and both
    proceed - and is the standard way this pattern is broken.

    A stale lock (dead PID) is reported in the raised error, never removed. An unexpected lock
    is a signal worth investigating, not litter to sweep.
    """
    path = lock_path(cwd)
    deadline = time.monotonic() + timeout
    payload = json.dumps({
        "pid": os.getpid(),
        "started": datetime.datetime.now().astimezone().isoformat(),
        "description": description,
    })
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            if time.monotonic() >= deadline:
                info = lock_info(cwd)
                stale = info and not info["alive"]
                raise LockUnavailable(
                    ("lock appears stale - held by a process that is gone. "
                     "Investigate before clearing: /orc-todo lock status"
                     if stale else "lock is held by a running process"),
                    info,
                )
            time.sleep(poll)
            continue
        try:
            os.write(fd, payload.encode())
        finally:
            os.close(fd)
        break
    try:
        yield
    finally:
        with contextlib.suppress(FileNotFoundError):
            path.unlink()


def clear_lock(cwd=None):
    """Remove the lock. Returns True if one was there. Only ever called by an explicit request."""
    path = lock_path(cwd)
    if not path.exists():
        return False
    path.unlink()
    return True


def read_counters(cwd=None):
    path = _counters_path(cwd)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError):
        return {}  # a corrupt counter is recoverable: the file scan is the real source


def write_counters(mapping, cwd=None):
    _counters_path(cwd).write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n")
