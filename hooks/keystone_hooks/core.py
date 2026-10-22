"""Configuration, findings and the per-harness output dialects."""

from __future__ import annotations

import fnmatch
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
KEYSTONE_ROOT = HOOKS_DIR.parent
REGISTRY_PATH = HOOKS_DIR / "registry.json"

HARNESSES = ("claude-code", "codex", "gemini")
TRIGGERS = ("shell", "edit", "stop", "pre-compact", "session-start")
PROFILES = ("off", "warn", "strict")
DEFAULT_PROFILE = "warn"
SEVERITY = {"info": 0, "context": 0, "warn": 1, "ask": 2, "block": 3}
DEFAULT_PROTECTED_BRANCHES = [
    "main",
    "master",
    "trunk",
    "develop",
    "production",
    "prod",
    "release/*",
    "release-*",
]


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class Config:
    profile: str = DEFAULT_PROFILE
    disabled: list[str] = field(default_factory=list)
    protected_branches: list[str] = field(
        default_factory=lambda: list(DEFAULT_PROTECTED_BRANCHES)
    )
    protected_paths: list[str] = field(default_factory=list)
    commit_convention: str = "auto"
    notes: list[str] = field(default_factory=list)

    def is_disabled(self, hook_id: str) -> bool:
        """Match an exact ID, its family ('secret'), a rule's parent
        ('rules.project' for 'rules.project/no-x') or a glob ('bar.*')."""
        base = hook_id.split("/", 1)[0]
        family = base.split(".", 1)[0]
        for pattern in self.disabled:
            if pattern in (hook_id, base, family) or fnmatch.fnmatchcase(
                hook_id, pattern
            ):
                return True
        return False


def _split_list(value: str) -> list[str]:
    return [p for p in value.replace(",", " ").split() if p]


def load_config(root: Path, env: dict[str, str] | None = None) -> Config:
    """Project file `.keystone/config.json`, overridden by environment variables."""
    env = os.environ if env is None else env
    cfg = Config()
    path = root / ".keystone" / "config.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            data = {}
            cfg.notes.append(f".keystone/config.json ignored: {exc}")
        if isinstance(data, dict):
            cfg.profile = str(data.get("profile", cfg.profile))
            cfg.disabled = [str(x) for x in data.get("disabled_hooks", [])]
            cfg.protected_branches = [
                str(x) for x in data.get("protected_branches", cfg.protected_branches)
            ]
            cfg.protected_paths = [str(x) for x in data.get("protected_paths", [])]
            cfg.commit_convention = str(
                data.get("commit_convention", cfg.commit_convention)
            )
    if env.get("KEYSTONE_HOOK_PROFILE"):
        cfg.profile = env["KEYSTONE_HOOK_PROFILE"].strip().lower()
    if env.get("KEYSTONE_DISABLED_HOOKS"):
        cfg.disabled += _split_list(env["KEYSTONE_DISABLED_HOOKS"])
    if cfg.profile not in PROFILES:
        cfg.notes.append(
            f"unknown hook profile '{cfg.profile}', using '{DEFAULT_PROFILE}'"
        )
        cfg.profile = DEFAULT_PROFILE
    return cfg


def find_root(cwd: Path) -> Path:
    """The repository root above `cwd`, or `cwd` itself outside a repository."""
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists():
            return candidate
    return cwd


@dataclass
class Finding:
    hook_id: str
    message: str
    action: str = ""  # resolved from the registry and profile unless a rule sets it


def resolve_action(entry: dict, profile: str, finding: Finding) -> str:
    """The action a finding takes under the active profile."""
    configured = entry.get(profile, "warn")
    if configured == "rule":
        # A project rule is the team's own explicit choice, not a default, so
        # its action holds in every profile except `off`.
        return finding.action or "warn"
    return configured


def adapt_to_harness(action: str, harness: str, profile: str) -> str:
    """Codex rejects `ask` as invalid output; degrade it by profile."""
    if action == "ask" and harness == "codex":
        return "block" if profile == "strict" else "warn"
    return action


def format_message(items: list[tuple[str, str]]) -> str:
    lines = [f"Keystone [{hook_id}]: {message}" for hook_id, message in items]
    ids = ",".join(sorted({hook_id.split("/", 1)[0] for hook_id, _ in items}))
    lines.append(f"(to switch off: KEYSTONE_DISABLED_HOOKS={ids} — see docs/hooks.md)")
    return "\n".join(lines)


def render(
    harness: str, trigger: str, action: str, message: str, context: str = ""
) -> dict:
    """The JSON object a harness expects on stdout. Empty dict: say nothing."""
    if trigger == "session-start":
        if not context:
            return {}
        return {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }
    if not message or action in ("", "info", "context"):
        return {}
    if trigger in ("shell", "edit"):
        if harness == "gemini":
            if action in ("block", "ask"):
                return {
                    "decision": "deny" if action == "block" else "ask",
                    "reason": message,
                }
            return {"systemMessage": message}
        if action in ("block", "ask"):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny" if action == "block" else "ask",
                    "permissionDecisionReason": message,
                }
            }
        return {
            "systemMessage": message,
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": message,
            },
        }
    if trigger == "stop":
        if action == "block":
            decision = "deny" if harness == "gemini" else "block"
            return {"decision": decision, "reason": message}
        return {"systemMessage": message}
    return {"systemMessage": message} if trigger == "pre-compact" else {}
