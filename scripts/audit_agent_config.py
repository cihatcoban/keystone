#!/usr/bin/env python3
"""Audit AI-agent configuration for risky permissions and supply-chain gaps.

Run it in any project — standard library only, no network, read-only:

    python3 /path/to/keystone/scripts/audit_agent_config.py            # ./
    python3 /path/to/keystone/scripts/audit_agent_config.py --user     # also ~/
    python3 /path/to/keystone/scripts/audit_agent_config.py --strict   # warnings fail

Reads, when present: .claude/settings*.json, .mcp.json, .gemini/settings.json,
.codex/config.toml, .codex/hooks.json, .cursor/mcp.json, .vscode/mcp.json, and
with --user their counterparts under the home directory.

Errors (exit 1):
  A1  approvals or sandbox switched off wholesale (bypass, yolo, full access)
  A3  a credential written into agent configuration
  A4  a hook or MCP command that pipes a downloaded script into a shell

Warnings (exit 0 unless --strict):
  A2  an MCP server launched from an unpinned package or image, or over http
  A5  a .env file exists and no agent config here denies reading it
  A6  a blanket allow rule for the shell or for every tool

Values are never printed: findings name the file, the setting and the type.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_env  # noqa: E402 — must follow the sys.path insert; scripts/ is not a package

try:  # tomllib is stdlib from Python 3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

PROJECT_FILES = (
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".mcp.json",
    ".gemini/settings.json",
    ".codex/config.toml",
    ".codex/hooks.json",
    ".cursor/mcp.json",
    ".vscode/mcp.json",
)
USER_FILES = (
    "~/.claude/settings.json",
    "~/.claude.json",
    "~/.gemini/settings.json",
    "~/.codex/config.toml",
    "~/.codex/hooks.json",
    "~/.cursor/mcp.json",
)
LAUNCHERS = {"npx", "bunx", "uvx", "pnpx"}
LAUNCHER_SUBCOMMANDS = {
    ("pnpm", "dlx"),
    ("pipx", "run"),
    ("yarn", "dlx"),
    ("npm", "exec"),
}
PINNED = re.compile(r"@\d[\w.+-]*$|==\d|@sha256:")
PIPE_TO_SHELL = re.compile(
    r"(curl|wget|iwr|invoke-webrequest)\b[^|;&]*\|\s*(sudo\s+)?(sh|bash|zsh|python3?|iex|pwsh)\b"
    r"|\beval\s+\"?\$\((curl|wget)",
    re.IGNORECASE,
)
BLANKET_ALLOW = re.compile(
    r"^(\*|Bash|Bash\(\*\)|Bash\(\*:\*\)|run_shell_command|shell)$"
)
ENV_DENY = re.compile(r"\.env")


@dataclass
class Finding:
    level: str  # ERROR | warn
    code: str
    where: str
    detail: str


def load(path: Path) -> tuple[object, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"unreadable ({exc})"
    try:
        if path.suffix == ".toml":
            if tomllib is None:
                return None, "needs Python 3.11+ to read TOML"
            return tomllib.loads(text), ""
        return json.loads(text), ""
    except ValueError as exc:
        return None, f"not valid {path.suffix[1:].upper()} ({exc})"


def walk(node: object, path: str = ""):
    """Yield (dotted path, value) for every scalar in a JSON/TOML tree."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from walk(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from walk(value, f"{path}[{i}]")
    else:
        yield path, node


def mcp_servers(data: dict) -> dict:
    servers: dict = {}
    for key in ("mcpServers", "mcp_servers", "servers"):
        if isinstance(data.get(key), dict):
            servers.update(data[key])
    for project in (data.get("projects") or {}).values():  # ~/.claude.json
        if isinstance(project, dict) and isinstance(project.get("mcpServers"), dict):
            servers.update(project["mcpServers"])
    return servers


def check_server(name: str, spec: dict, where: str) -> list[Finding]:
    out: list[Finding] = []
    command = str(spec.get("command", ""))
    args = [str(a) for a in spec.get("args", []) if not str(a).startswith("-")]
    program = Path(command).name
    package = ""
    if program in LAUNCHERS and args:
        package = args[0]
    elif args and (program, args[0]) in LAUNCHER_SUBCOMMANDS and len(args) > 1:
        package = args[1]
    elif program in ("docker", "podman") and "run" in args:
        rest = [a for a in args[args.index("run") + 1 :] if "=" not in a]
        package = rest[0] if rest else ""
        if package and ":" not in package.split("/")[-1] and "@sha256:" not in package:
            package += ":latest"
    if package and (
        not PINNED.search(package) or package.endswith((":latest", "@latest"))
    ):
        out.append(
            Finding(
                "warn",
                "A2",
                where,
                f"MCP server '{name}' runs '{package}' without a pinned version",
            )
        )
    url = str(spec.get("url") or spec.get("httpUrl") or spec.get("serverUrl") or "")
    if url.startswith("http://") and not re.match(
        r"http://(localhost|127\.0\.0\.1|\[::1\])", url
    ):
        out.append(
            Finding(
                "warn", "A2", where, f"MCP server '{name}' is reached over plain http"
            )
        )
    line = " ".join([command, *map(str, spec.get("args", []))])
    if PIPE_TO_SHELL.search(line):
        out.append(
            Finding(
                "ERROR",
                "A4",
                where,
                f"MCP server '{name}' pipes a download into a shell",
            )
        )
    return out


def looks_like_secret(value: str) -> bool:
    """A literal value, not a reference: no path, variable name or placeholder."""
    if len(value) < 12 or " " in value or check_env.PLACEHOLDER.match(value):
        return False
    if re.search(r"\$\{?\w+\}?|^env:|^\{env:", value):  # a variable reference, not a value
        return False
    if value.startswith(("/", "./", "~", "http")) or re.fullmatch(
        r"[A-Z][A-Z0-9_]*", value
    ):
        return False  # a path, a URL, or the *name* of an environment variable
    has_digit = any(c.isdigit() for c in value)
    return has_digit and any(c.isalpha() for c in value) and entropy(value) >= 3.5


def entropy(value: str) -> float:
    counts = {c: value.count(c) for c in set(value)}
    return -sum(n / len(value) * math.log2(n / len(value)) for n in counts.values())


def check_secrets(data: object, where: str) -> list[Finding]:
    out = []
    for key_path, value in walk(data):
        if not isinstance(value, str) or not value:
            continue
        leaf = re.split(r"[.\[]", key_path)[-1]
        typed = [
            label
            for label, pattern in check_env.CREDENTIAL_PATTERNS
            if pattern.search(value)
        ]
        named = check_env.SECRET_KEY_NAME.search(leaf) and looks_like_secret(value)
        if typed or named:
            kind = typed[0] if typed else "secret-named value"
            out.append(
                Finding(
                    "ERROR",
                    "A3",
                    where,
                    f"{key_path} holds a literal credential ({kind})",
                )
            )
    return out


def check_permissions(data: dict, where: str) -> list[Finding]:
    out = []
    perms = data.get("permissions") if isinstance(data.get("permissions"), dict) else {}
    if perms.get("defaultMode") == "bypassPermissions" or data.get(
        "skipDangerousModePermissionPrompt"
    ):
        out.append(
            Finding(
                "ERROR", "A1", where, "permission prompts are bypassed for every tool"
            )
        )
    for rule in perms.get("allow", []) if isinstance(perms.get("allow"), list) else []:
        if BLANKET_ALLOW.match(str(rule)):
            out.append(
                Finding(
                    "warn",
                    "A6",
                    where,
                    f"allow rule '{rule}' approves every shell command",
                )
            )
    tools = data.get("tools") if isinstance(data.get("tools"), dict) else {}
    if (
        data.get("autoAccept")
        or tools.get("autoAccept")
        or str(data.get("approvalMode", "")).lower() == "yolo"
    ):
        out.append(
            Finding("ERROR", "A1", where, "Gemini auto-accepts every tool call (yolo)")
        )
    for rule in (
        tools.get("allowed", []) if isinstance(tools.get("allowed"), list) else []
    ):
        if BLANKET_ALLOW.match(str(rule)):
            out.append(
                Finding(
                    "warn",
                    "A6",
                    where,
                    f"tools.allowed '{rule}' approves every shell command",
                )
            )
    if (
        data.get("approval_policy") == "never"
        and data.get("sandbox_mode") == "danger-full-access"
    ):
        out.append(
            Finding("ERROR", "A1", where, "Codex runs with no approvals and no sandbox")
        )
    return out


def check_hooks(data: dict, where: str) -> list[Finding]:
    hooks = data.get("hooks") if isinstance(data.get("hooks"), dict) else {}
    out = []
    for key_path, value in walk(hooks):
        if isinstance(value, str) and PIPE_TO_SHELL.search(value):
            out.append(
                Finding(
                    "ERROR",
                    "A4",
                    where,
                    f"hook hooks.{key_path} pipes a download into a shell",
                )
            )
    return out


def denies_env(data: object) -> bool:
    for key_path, value in walk(data):
        lowered = key_path.lower()
        if (
            isinstance(value, str)
            and ENV_DENY.search(value)
            and ("deny" in lowered or "exclude" in lowered)
        ):
            return True
    return False


def audit(root: Path, include_user: bool = False) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    scanned: list[str] = []
    env_denied = False
    candidates = [root / f for f in PROJECT_FILES]
    if include_user:
        candidates += [Path(f).expanduser() for f in USER_FILES]
    for path in candidates:
        if not path.is_file():
            continue
        where = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        data, problem = load(path)
        scanned.append(where)
        if problem:
            findings.append(Finding("warn", "A0", where, problem))
            continue
        if not isinstance(data, dict):
            continue
        findings += check_permissions(data, where)
        findings += check_hooks(data, where)
        findings += check_secrets(data, where)
        for name, spec in mcp_servers(data).items():
            if isinstance(spec, dict):
                findings += check_server(name, spec, where)
        env_denied = env_denied or denies_env(data)
    ignore = root / ".geminiignore"
    if ignore.is_file() and ENV_DENY.search(
        ignore.read_text(encoding="utf-8", errors="replace")
    ):
        env_denied = True
    if (root / ".env").exists() and not env_denied:
        findings.append(
            Finding(
                "warn",
                "A5",
                ".env",
                "exists, and no agent configuration here denies reading it "
                "(templates/agent-secret-guards.md)",
            )
        )
    return findings, scanned


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="project directory (default: .)")
    parser.add_argument(
        "--user", action="store_true", help="also audit configuration in ~/"
    )
    parser.add_argument("--strict", action="store_true", help="warnings fail too")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    findings, scanned = audit(root, args.user)
    for f in sorted(findings, key=lambda f: (f.level != "ERROR", f.code, f.where)):
        print(f"{f.level:5}  {f.code}  {f.where}: {f.detail}")
    errors = sum(f.level == "ERROR" for f in findings)
    warnings = len(findings) - errors
    print(
        f"\naudit_agent_config: {len(scanned)} file(s) · {errors} errors · {warnings} warnings"
    )
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
