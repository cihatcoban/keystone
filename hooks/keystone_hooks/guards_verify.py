"""verify.stop — the turn ends with changes that /verify has not passed.

Cheap by design: the gate compares a fingerprint, it never runs the checks.
scripts/verify.py runs them and records the fingerprint it verified.
"""

from __future__ import annotations

from . import state
from .core import Finding
from .events import Event

STAMP = "verify.json"


def verify_command(ctx: dict) -> str:
    return f'python3 "{ctx["keystone_root"] / "scripts" / "verify.py"}"'


def stop_gate(event: Event, ctx: dict) -> list[Finding]:
    if not ctx.get("constraints_text") or not state.is_repository(event.root):
        return []  # no written bar to verify against, or nothing to fingerprint
    changed = state.changed_files(event.root)
    if not changed:
        return []
    stamp = state.read_json(event.root, STAMP)
    current = state.fingerprint(event.root)
    if stamp.get("fingerprint") == current and stamp.get("result") == "pass":
        return []
    sample = ", ".join(changed[:3]) + (
        f" (+{len(changed) - 3} more)" if len(changed) > 3 else ""
    )
    if stamp.get("fingerprint") == current:
        why = "the last /verify of exactly these changes failed"
    elif stamp:
        why = "the files changed after the last /verify"
    else:
        why = "/verify has not run on them"
    return [
        Finding(
            "verify.stop",
            f"{len(changed)} changed file(s) — {sample} — and {why}. Run /verify "
            f"({verify_command(ctx)}) and report its result before calling the work "
            "done (CLAUDE.md §1.1, §1.10).",
        )
    ]


GUARDS = {"verify.stop": stop_gate}
