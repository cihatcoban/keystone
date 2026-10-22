"""Normalize each harness's hook input into one Event shape."""

from __future__ import annotations

import os
import re
import shlex
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

READ_LIMIT_BYTES = 1_000_000


@dataclass
class FileChange:
    path: str  # repository-relative when the file is inside the root
    before: str = ""  # text the change removes (old_string, prior file, '-' lines)
    after: str = ""  # text the change adds (new_string, new file, '+' lines)
    whole_file: bool = False  # `after` is the file's complete new content
    deleted: bool = False

    def added_lines(self) -> list[str]:
        return _subtract(self.after, self.before)

    def removed_lines(self) -> list[str]:
        return _subtract(self.before, self.after)


def _subtract(a: str, b: str) -> list[str]:
    """Lines of `a` not matched by a line of `b` (multiset difference)."""
    remaining = Counter(line.rstrip() for line in b.splitlines())
    out = []
    for line in a.splitlines():
        key = line.rstrip()
        if remaining[key] > 0:
            remaining[key] -= 1
        else:
            out.append(line)
    return out


@dataclass
class Event:
    harness: str
    trigger: str
    root: Path
    cwd: Path
    command: str = ""
    changes: list[FileChange] = field(default_factory=list)
    stop_hook_active: bool = False
    source: str = ""  # session-start: startup | resume | clear | compact
    raw: dict = field(default_factory=dict)


def relative(root: Path, cwd: Path, path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = cwd / p
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return p.as_posix()


def read_text(root: Path, rel_path: str) -> str:
    path = root / rel_path
    try:
        if path.is_file() and path.stat().st_size <= READ_LIMIT_BYTES:
            return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    return ""


def _shell_command(tool_input: dict) -> str:
    command = tool_input.get("command", tool_input.get("cmd", ""))
    if isinstance(command, list):
        parts = [str(x) for x in command]
        # Codex runs ["bash", "-lc", "<script>"]; the script is what matters.
        if len(parts) >= 3 and parts[1] in ("-c", "-lc") and "sh" in parts[0]:
            return parts[2]
        return shlex.join(parts)
    return str(command or "")


PATCH_FILE = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$")


def parse_apply_patch(text: str) -> list[tuple[str, str, str, str]]:
    """(kind, path, removed text, added text) for each file in a Codex patch."""
    files: list[tuple[str, str, list[str], list[str]]] = []
    for line in text.splitlines():
        match = PATCH_FILE.match(line)
        if match:
            files.append((match.group(1), match.group(2).strip(), [], []))
            continue
        if not files or line.startswith("*** "):
            if line.startswith("*** Move to: ") and files:
                kind, _, minus, plus = files[-1]
                files[-1] = (kind, line[len("*** Move to: ") :].strip(), minus, plus)
            continue
        if line.startswith("+"):
            files[-1][3].append(line[1:])
        elif line.startswith("-"):
            files[-1][2].append(line[1:])
    return [(k, p, "\n".join(m), "\n".join(a)) for k, p, m, a in files]


def _changes(
    harness: str, tool: str, ti: dict, root: Path, cwd: Path
) -> list[FileChange]:
    if harness == "codex":
        patch = _shell_command(ti)
        out = []
        for kind, path, minus, plus in parse_apply_patch(patch):
            rel = relative(root, cwd, path)
            if kind == "Add":
                out.append(FileChange(rel, read_text(root, rel), plus, whole_file=True))
            elif kind == "Delete":
                out.append(FileChange(rel, read_text(root, rel), "", deleted=True))
            else:
                out.append(FileChange(rel, minus, plus))
        return out

    path = str(ti.get("file_path") or ti.get("path") or "")
    if not path:
        return []
    rel = relative(root, cwd, path)
    if tool in ("Write", "write_file"):
        return [
            FileChange(
                rel, read_text(root, rel), str(ti.get("content", "")), whole_file=True
            )
        ]
    if tool == "MultiEdit":
        edits = ti.get("edits") or []
        return [
            FileChange(rel, str(e.get("old_string", "")), str(e.get("new_string", "")))
            for e in edits
            if isinstance(e, dict)
        ]
    return [
        FileChange(rel, str(ti.get("old_string", "")), str(ti.get("new_string", "")))
    ]


def normalize(harness: str, trigger: str, raw: dict, root: Path | None = None) -> Event:
    from .core import find_root

    cwd = Path(str(raw.get("cwd") or os.getcwd()))
    root = root or find_root(cwd)
    event = Event(harness=harness, trigger=trigger, root=root, cwd=cwd, raw=raw)
    tool = str(raw.get("tool_name", ""))
    ti = raw.get("tool_input") or {}
    if not isinstance(ti, dict):
        ti = {"command": ti}
    if trigger == "shell":
        event.command = _shell_command(ti)
    elif trigger == "edit":
        event.changes = _changes(harness, tool, ti, root, cwd)
    elif trigger == "stop":
        event.stop_hook_active = bool(raw.get("stop_hook_active"))
    elif trigger == "session-start":
        event.source = str(raw.get("source", ""))
    return event


# --- shell parsing -----------------------------------------------------------

WRAPPERS = {"sudo", "command", "env", "time", "nohup", "exec", "builtin", "doas"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


@dataclass
class Segment:
    argv: list[str]
    env: dict[str, str]
    text: str


OPERATOR = re.compile(r"^[;&|\n]+$")


def _tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|\n")
    lexer.whitespace = " \t\r"  # newline separates commands, so it is punctuation
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:  # unbalanced quotes: fall back to a rough split
        return re.split(r"[ \t\r]+", command.replace("\n", " ; "))


def segments(command: str) -> list[Segment]:
    """Split a shell command on ; && || | & and newlines, respecting quotes."""
    out: list[Segment] = []
    current: list[str] = []
    for token in [*_tokens(command), ";"]:
        if not OPERATOR.match(token):
            current.append(token)
            continue
        argv, current = current, []
        env: dict[str, str] = {}
        while argv and (ASSIGNMENT.match(argv[0]) or argv[0] in WRAPPERS):
            head = argv.pop(0)
            if ASSIGNMENT.match(head):
                key, value = head.split("=", 1)
                env[key] = value
        if argv:
            out.append(Segment(argv, env, shlex.join(argv)))
    return out


def git_args(segment: Segment) -> tuple[str, list[str], list[str]] | None:
    """(subcommand, arguments, `-c` settings) for a git invocation, else None."""
    argv = segment.argv
    if not argv or os.path.basename(argv[0]) != "git":
        return None
    settings: list[str] = []
    i = 1
    while i < len(argv):
        token = argv[i]
        if token in ("-c", "-C", "--git-dir", "--work-tree", "--namespace"):
            if token == "-c" and i + 1 < len(argv):
                settings.append(argv[i + 1])
            i += 2
            continue
        if token.startswith("--") and "=" in token:
            i += 1
            continue
        if token.startswith("-"):
            i += 1
            continue
        return token, argv[i + 1 :], settings
    return None
