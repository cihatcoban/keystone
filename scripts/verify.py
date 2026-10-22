#!/usr/bin/env python3
"""Run a project's verification commands from CONSTRAINTS.md, phase by phase.

    python3 verify.py                  # run the plan, record the result
    python3 verify.py --plan           # show what would run, run nothing
    python3 verify.py --inferred       # no explicit table: run commands found
                                       # in "Measured by" cells that exist here
    python3 verify.py --acknowledge "standalone threshold change, see PR #12"

Phases run in order: build, types, lint, test, security, then a diff phase
that scans uncommitted changes for the bar-protection triggers of CLAUDE.md §4.
Commands come from a "## Verification commands" table in CONSTRAINTS.md (see
templates/CONSTRAINTS.template.md). The result and a fingerprint of the
working tree are written to .keystone/state/verify.json; the verify.stop hook
reads it to tell whether the current changes were verified.

Exit codes: 0 pass, 1 fail or unacknowledged findings, 2 nothing to run.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hooks"))

from keystone_hooks import constraints, core, events, guards_bar, guards_secret, state  # noqa: E402 — must follow the sys.path insert; hooks/ is not a package

PHASE_ALIASES = {
    "compile": "build",
    "type": "types",
    "typecheck": "types",
    "types": "types",
    "format": "lint",
    "static": "lint",
    "static analysis": "lint",
    "tests": "test",
    "sec": "security",
    "secrets": "security",
}
SECTION_PHASES = {
    "correctness": "test",
    "static analysis": "lint",
    "security": "security",
}
TAIL_LINES = 25


@dataclass
class Step:
    phase: str
    command: str
    origin: str  # explicit | inferred


@dataclass
class Result:
    phase: str
    command: str
    status: str  # pass | fail | timeout | error
    seconds: float
    tail: str = ""


def phase_name(raw: str) -> str:
    name = raw.strip().lower()
    return PHASE_ALIASES.get(name, name)


def order(steps: list[Step]) -> list[Step]:
    rank = {p: i for i, p in enumerate(constraints.PHASES)}
    return sorted(steps, key=lambda s: rank.get(s.phase, len(rank)))


def runnable(root: Path, span: str) -> bool:
    """Does the command's program exist here? Discover, don't assume."""
    try:
        argv = shlex.split(span)
    except ValueError:
        return False
    if not argv or "@" in argv[0]:
        return False
    if argv[0] == "make":
        makefile = root / "Makefile"
        target = argv[1] if len(argv) > 1 else ""
        return makefile.is_file() and bool(
            re.search(
                rf"^{re.escape(target)}\s*:", makefile.read_text(errors="replace"), re.M
            )
        )
    if argv[0].startswith(("./", "../")):
        return (root / argv[0]).is_file()
    return shutil.which(argv[0]) is not None


def inferred_steps(root: Path, text: str) -> list[Step]:
    steps: list[Step] = []
    for section in re.split(r"^## ", text, flags=re.M)[1:]:
        heading = re.sub(r"^\d+\.\s*", "", section.splitlines()[0]).strip().lower()
        phase = SECTION_PHASES.get(heading)
        if not phase:
            continue
        for span in constraints.measured_by(section):
            if runnable(root, span) and all(s.command != span for s in steps):
                steps.append(Step(phase, span, "inferred"))
    return order(steps)


def plan(root: Path, text: str, inferred: bool) -> list[Step]:
    explicit = [
        Step(phase_name(phase), command, "explicit")
        for phase, command in constraints.verification_commands(text)
    ]
    if explicit:
        return order(explicit)
    return inferred_steps(root, text) if inferred else []


def run_step(step: Step, root: Path, timeout: float) -> Result:
    start = time.monotonic()
    try:
        proc = subprocess.run(
            step.command,
            shell=True,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return Result(
            step.phase, step.command, "timeout", round(time.monotonic() - start, 2)
        )
    except OSError as exc:
        return Result(step.phase, step.command, "error", 0.0, str(exc))
    seconds = round(time.monotonic() - start, 2)
    status = "pass" if proc.returncode == 0 else "fail"
    tail = (
        ""
        if status == "pass"
        else "\n".join((proc.stdout + proc.stderr).rstrip().splitlines()[-TAIL_LINES:])
    )
    return Result(step.phase, step.command, status, seconds, tail)


def diff_changes(root: Path) -> list[events.FileChange]:
    """Uncommitted changes as FileChanges: tracked diff hunks, untracked files whole."""
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff",
            "HEAD",
            "--unified=0",
            "--no-color",
            "--",
            ".",
            state.EXCLUDE,
        ],
        capture_output=True,
        text=True,
        errors="replace",
    )
    changes: list[events.FileChange] = []
    for block in re.split(r"^diff --git ", proc.stdout, flags=re.M)[1:]:
        header = block.splitlines()[0]
        path = header.split(" b/", 1)[-1]
        lines = block.splitlines()
        minus = [x[1:] for x in lines if x.startswith("-") and not x.startswith("---")]
        plus = [x[1:] for x in lines if x.startswith("+") and not x.startswith("+++")]
        deleted = "\ndeleted file mode" in block
        changes.append(
            events.FileChange(path, "\n".join(minus), "\n".join(plus), deleted=deleted)
        )
    untracked = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            ".",
            state.EXCLUDE,
        ],
        capture_output=True,
        text=True,
        errors="replace",
    ).stdout.splitlines()
    for path in untracked:
        changes.append(
            events.FileChange(path, "", events.read_text(root, path), whole_file=True)
        )
    return changes


def diff_findings(root: Path, text: str) -> list[str]:
    event = events.Event("verify", "edit", root, root, changes=diff_changes(root))
    ctx = {"config": core.load_config(root), "constraints_text": text}
    messages = []
    for guard in (
        guards_bar.constraints_lowered,
        guards_bar.suppression,
        guards_bar.test_weakened,
    ):
        messages += [f"[{f.hook_id}] {f.message}" for f in guard(event, ctx)]
    messages += [
        f"[{f.hook_id}] {f.message}" for f in guards_secret.secret_write(event, ctx)
    ]
    return messages


def report(
    steps: list[Step], results: list[Result], findings: list[str], outcome: str
) -> None:
    origin = (
        "inferred from 'Measured by'"
        if steps and steps[0].origin == "inferred"
        else "CONSTRAINTS.md"
    )
    phases = len({s.phase for s in steps})
    print(f"verify: {len(steps)} command(s) in {phases} phase(s), from {origin}")
    for r in results:
        print(f"  {r.status.upper():7} {r.phase:9} {r.command}  ({r.seconds}s)")
        for line in r.tail.splitlines():
            print(f"          | {line}")
    for s in steps[len(results) :]:
        print(f"  SKIPPED {s.phase:9} {s.command}  (--fail-fast)")
    if findings:
        print(
            f"  diff: {len(findings)} bar-protection finding(s) in uncommitted changes"
        )
        for f in findings:
            print(f"          - {f}")
    print(f"result: {outcome.upper()}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="project directory (default: .)")
    parser.add_argument("--plan", action="store_true", help="print the plan only")
    parser.add_argument(
        "--inferred",
        action="store_true",
        help="without an explicit table, run runnable 'Measured by' commands",
    )
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument(
        "--timeout", type=float, default=900, help="seconds per command"
    )
    parser.add_argument(
        "--acknowledge",
        metavar="REASON",
        help="accept the diff findings, with the reason recorded",
    )
    parser.add_argument("--no-record", action="store_true")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    root = core.find_root(Path(args.root).resolve())
    text = constraints.load(root)
    if not text:
        print(
            "verify: no CONSTRAINTS.md — create it from templates/CONSTRAINTS.template.md "
            "(CLAUDE.md §1.4); there is no written bar to verify against"
        )
        return 2
    steps = plan(root, text, args.inferred)
    if args.plan or not steps:
        candidates = steps or inferred_steps(root, text)
        if not steps:
            print(
                "verify: CONSTRAINTS.md has no '## Verification commands' table; add one"
            )
            print("(templates/CONSTRAINTS.template.md shows the shape).")
            if candidates:
                print("Runnable commands found in its 'Measured by' cells:")
        for s in candidates:
            print(f"  {s.phase:9} {s.command}  [{s.origin}]")
        if not steps and candidates:
            print("Check they are the right ones, then run them with --inferred.")
        return 0 if (args.plan and steps) else 2

    results: list[Result] = []
    for step in steps:
        results.append(run_step(step, root, args.timeout))
        if args.fail_fast and results[-1].status != "pass":
            break
    findings = diff_findings(root, text)
    failed = any(r.status != "pass" for r in results) or len(results) < len(steps)
    if failed:
        outcome = "fail"
    elif findings and not args.acknowledge:
        outcome = "review"
    else:
        outcome = "pass"

    if not args.no_record and state.is_repository(root):
        state.write_json(
            root,
            "verify.json",
            {
                "result": outcome,
                "at": state.now(),
                "fingerprint": state.fingerprint(root),
                "steps": [asdict(r) | {"tail": r.tail[-2000:]} for r in results],
                "diff_findings": findings,
                "acknowledged": args.acknowledge or "",
            },
        )
    if args.json:
        print(
            json.dumps(
                {
                    "result": outcome,
                    "results": [asdict(r) for r in results],
                    "diff_findings": findings,
                },
                indent=2,
            )
        )
    else:
        report(steps, results, findings, outcome)
        if outcome == "review":
            print(
                "Commands passed, but the diff needs a human decision. Fix the findings, "
                'or rerun with --acknowledge "<reason>" once a person has accepted them.'
            )
    return 0 if outcome == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
