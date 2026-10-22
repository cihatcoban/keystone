#!/usr/bin/env python3
"""Measure whether skills are *followed*, not only selected — with a real agent CLI.

make triggers proves that each eval prompt shares vocabulary with the right
skill. It cannot prove that an agent, given the prompt, actually applies the
skill. This runner sends each positive prompt to a real CLI twice — as written
(implicit) and prefixed with "Use the <skill> skill" (explicit) — then asks the
same CLI to grade the answer against the skill's exit checklist.

    python3 scripts/evals_live.py --cli claude --skills git-workflow --limit 2
    python3 scripts/evals_live.py --cli gemini --out evals/live-gemini.json
    python3 scripts/evals_live.py --command 'my-agent --print {prompt}'

Optional and never part of CI: it calls a model, costs money and is not
deterministic. Read results as a trend across runs, not a single verdict.

Per skill it reports: the share of checklist items addressed (implicit and
explicit) and how often the grader judged the skill applied at all. A large
gap between explicit and implicit means the skill is not being picked up; a
low explicit score means the skill is picked up but not followed.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Non-interactive invocations. Each is an assumption about the installed CLI's
# flags; override with --command when your version differs.
CLI_COMMANDS = {
    "claude": "claude -p {prompt} --output-format json",
    "gemini": "gemini -p {prompt} --output-format json",
    "codex": "codex exec --skip-git-repo-check {prompt}",
}
RESPONSE_KEYS = ("result", "response", "text", "output", "content")
FRAME = (
    "You are working in an empty scratch project. Do not create, edit or delete "
    "files and do not run commands; answer with the plan and reasoning you would "
    "follow.\n\n"
)
GRADER = """You are grading an AI coding agent's answer against a checklist.
Return ONLY a JSON object, no prose:
{{"skill_applied": true|false, "items": [{{"item": "<checklist item>", "addressed": true|false}}]}}

"skill_applied" is true when the answer clearly follows the method of the
skill "{skill}", not merely mentions it. An item is "addressed" only when the
answer does or plans what the item states.

Checklist:
{checklist}

Answer to grade:
<<<
{answer}
>>>
"""


@dataclass
class Trial:
    skill: str
    prompt: str
    variant: str  # implicit | explicit
    addressed: int = 0
    total: int = 0
    skill_applied: bool = False
    error: str = ""


@dataclass
class Summary:
    skill: str
    implicit: float | None = None
    explicit: float | None = None
    applied_rate: float | None = None
    trials: list[Trial] = field(default_factory=list)


def checklist(skill: str) -> list[str]:
    text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    section = text.split("## Exit checklist", 1)[-1]
    return [m.strip() for m in re.findall(r"^- \[ \] (.+)$", section, re.M)]


def run_cli(template: str, prompt: str, timeout: float, cwd: Path) -> str:
    argv = [part.replace("{prompt}", prompt) for part in shlex.split(template)]
    proc = subprocess.run(
        argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, errors="replace"
    )
    if proc.returncode != 0:
        raise RuntimeError(f"exit {proc.returncode}: {proc.stderr.strip()[-300:]}")
    return extract_text(proc.stdout)


def extract_text(stdout: str) -> str:
    """The answer text from a CLI's JSON envelope, or stdout as it is."""
    try:
        data = json.loads(stdout)
    except ValueError:
        return stdout.strip()
    if isinstance(data, dict):
        for key in RESPONSE_KEYS:
            if isinstance(data.get(key), str):
                return data[key]
    return stdout.strip()


def parse_grade(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("grader returned no JSON object")
    grade = json.loads(match.group(0))
    if not isinstance(grade.get("items"), list):
        raise ValueError("grader JSON has no 'items' list")
    return grade


def trial(
    skill: str, prompt: str, variant: str, template: str, timeout: float, cwd: Path
) -> Trial:
    result = Trial(skill, prompt, variant)
    items = checklist(skill)
    asked = prompt if variant == "implicit" else f"Use the {skill} skill. {prompt}"
    try:
        answer = run_cli(template, FRAME + asked, timeout, cwd)
        grading = GRADER.format(
            skill=skill, checklist="\n".join(f"- {i}" for i in items), answer=answer
        )
        grade = parse_grade(run_cli(template, grading, timeout, cwd))
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        result.error = str(exc)[:300]
        return result
    result.total = len(items)
    result.addressed = min(
        len(items), sum(1 for i in grade["items"] if i.get("addressed") is True)
    )
    result.skill_applied = bool(grade.get("skill_applied"))
    return result


def summarize(skill: str, trials: list[Trial]) -> Summary:
    def rate(variant: str) -> float | None:
        done = [t for t in trials if t.variant == variant and not t.error and t.total]
        return (
            round(sum(t.addressed / t.total for t in done) / len(done), 2)
            if done
            else None
        )

    graded = [t for t in trials if not t.error]
    applied = (
        round(sum(t.skill_applied for t in graded) / len(graded), 2) if graded else None
    )
    return Summary(skill, rate("implicit"), rate("explicit"), applied, trials)


def cases(skills: list[str] | None, limit: int) -> dict[str, list[str]]:
    out = {}
    for path in sorted((ROOT / "evals" / "cases").glob("*.json")):
        if skills and path.stem not in skills:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        prompts = [p["prompt"] for p in data.get("trigger", {}).get("positive", [])]
        out[path.stem] = prompts[:limit] if limit else prompts
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--cli", choices=sorted(CLI_COMMANDS))
    source.add_argument("--command", help="custom template; {prompt} is replaced")
    parser.add_argument("--skills", help="comma-separated skill names (default: all)")
    parser.add_argument(
        "--limit", type=int, default=1, help="prompts per skill (0 = all)"
    )
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--out", help="write the full results as JSON here")
    args = parser.parse_args(argv)

    template = args.command or CLI_COMMANDS[args.cli]
    if "{prompt}" not in template:
        parser.error("the command template must contain {prompt}")
    selected = cases(args.skills.split(",") if args.skills else None, args.limit)
    if not selected:
        print("evals_live: no matching eval cases")
        return 2

    summaries = []
    with tempfile.TemporaryDirectory() as scratch:
        for skill, prompts in selected.items():
            trials = [
                trial(skill, prompt, variant, template, args.timeout, Path(scratch))
                for prompt in prompts
                for variant in ("implicit", "explicit")
            ]
            summary = summarize(skill, trials)
            summaries.append(summary)
            errors = sum(1 for t in trials if t.error)

            def pct(x):
                return "  n/a" if x is None else f"{x:5.0%}"

            print(
                f"{skill:36} implicit {pct(summary.implicit)}  explicit {pct(summary.explicit)}"
                f"  applied {pct(summary.applied_rate)}"
                + (f"  ({errors} errored)" if errors else "")
            )
    if args.out:
        Path(args.out).write_text(
            json.dumps([asdict(s) for s in summaries], indent=2) + "\n"
        )
    failed = all(t.error for s in summaries for t in s.trials)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
