"""Working-tree fingerprint and the files under .keystone/state/.

The fingerprint answers one question cheaply and the same way in every harness:
has anything changed since /verify last passed? It hashes HEAD, the diff
against HEAD and the content of untracked, unignored files. Keystone's own
files under .keystone/ are excluded, so writing a handoff note does not count
as a code change.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

EXCLUDE = ":(exclude).keystone"
UNTRACKED_LIMIT_BYTES = 2_000_000
UNTRACKED_LIMIT_FILES = 500
STATE_GITIGNORE = "# Keystone session state — local to this checkout.\n*\n"


def _git(root: Path, *args: str) -> tuple[int, bytes]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, timeout=20
        )
    except (OSError, subprocess.SubprocessError):
        return 1, b""
    return proc.returncode, proc.stdout


def is_repository(root: Path) -> bool:
    return _git(root, "rev-parse", "--git-dir")[0] == 0


def changed_files(root: Path) -> list[str]:
    """Paths with uncommitted changes or untracked and unignored, minus .keystone/."""
    code, out = _git(
        root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--",
        ".",
        EXCLUDE,
    )
    if code != 0:
        return []
    entries = [e for e in out.decode("utf-8", "replace").split("\0") if e]
    paths, skip = [], False
    for entry in entries:
        if skip:  # the source path that follows a rename entry
            skip = False
            continue
        status, path = entry[:2], entry[3:]
        if status[0] in "RC":
            skip = True
        paths.append(path)
    return paths


def fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    digest.update(_git(root, "rev-parse", "HEAD")[1])
    code, diff = _git(
        root, "diff", "HEAD", "--binary", "--no-color", "--", ".", EXCLUDE
    )
    if code != 0:  # no commits yet
        diff = _git(root, "diff", "--cached", "--binary", "--", ".", EXCLUDE)[1]
        diff += _git(root, "diff", "--binary", "--", ".", EXCLUDE)[1]
    digest.update(diff)
    _, untracked = _git(
        root, "ls-files", "--others", "--exclude-standard", "-z", "--", ".", EXCLUDE
    )
    for name in sorted(untracked.split(b"\0"))[:UNTRACKED_LIMIT_FILES]:
        if not name:
            continue
        digest.update(name)
        path = root / name.decode("utf-8", "replace")
        try:
            if path.is_file() and path.stat().st_size <= UNTRACKED_LIMIT_BYTES:
                digest.update(path.read_bytes())
        except OSError:
            pass
    return digest.hexdigest()


def state_dir(root: Path) -> Path:
    path = root / ".keystone" / "state"
    path.mkdir(parents=True, exist_ok=True)
    ignore = path / ".gitignore"
    if not ignore.exists():
        ignore.write_text(STATE_GITIGNORE, encoding="utf-8")
    return path


def read_json(root: Path, name: str) -> dict:
    path = root / ".keystone" / "state" / name
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(root: Path, name: str, data: dict) -> Path:
    path = state_dir(root) / name
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return path


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
