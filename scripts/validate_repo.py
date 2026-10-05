#!/usr/bin/env python3
"""Keystone repository validator.

Checks
  1  every skills/<dir>/SKILL.md parses and has name + description
  2  frontmatter name == directory name
  3  description length within bounds and contains a trigger section
  4  body word count within bounds; has an H1; has an exit checklist
  5  relative links inside skills resolve to real files
  6  commands/ and agents/ files carry the required frontmatter
  7  every skill referenced from a command or agent exists
  8  CLAUDE.md and AGENTS.md bodies are identical
  9  every skill has an eval case with positive and negative prompts
 10  no duplicate description opening clause (routing collision smell)
 11  templates and references referenced from skills exist

Exit code 1 on any error. Warnings never fail the build.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESC_MIN, DESC_MAX = 80, 500
BODY_MIN, BODY_MAX = 350, 1600

errors: list[str] = []
warnings: list[str] = []


def err(m: str) -> None:
    errors.append(m)


def warn(m: str) -> None:
    warnings.append(m)


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def frontmatter(text: str, path: Path) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        err(f"{rel(path)}: missing frontmatter")
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        err(f"{rel(path)}: unterminated frontmatter")
        return {}, text
    data: dict[str, str] = {}
    key = None
    for line in text[4:end].split("\n"):
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            data[key] = m.group(2).strip()
        elif key and line[:1] in (" ", "\t"):
            data[key] += " " + line.strip()
    return data, text[end + 5 :]


def check_skills(base: Path, strict: bool = True) -> dict[str, str]:
    found: dict[str, str] = {}
    sdir = base / "skills"
    if not sdir.is_dir():
        err(f"{rel(sdir)}: missing")
        return found
    openings: dict[str, list[str]] = defaultdict(list)

    for d in sorted(p for p in sdir.iterdir() if p.is_dir()):
        f = d / "SKILL.md"
        if not f.exists():
            err(f"{rel(d)}: no SKILL.md")
            continue
        fm, body = frontmatter(f.read_text(encoding="utf-8"), f)
        name, desc = fm.get("name", ""), fm.get("description", "")

        if not name:
            err(f"{rel(f)}: frontmatter 'name' missing")
        elif name != d.name:
            err(f"{rel(f)}: name '{name}' != directory '{d.name}'")
        else:
            found[name] = desc

        if not desc:
            err(f"{rel(f)}: frontmatter 'description' missing")
        else:
            if not DESC_MIN <= len(desc) <= DESC_MAX:
                err(f"{rel(f)}: description {len(desc)} chars, must be {DESC_MIN}-{DESC_MAX}")
            if "Triggers" not in desc:
                err(f"{rel(f)}: description must contain a 'Triggers - ...' section")
            if not desc[:1].isupper():
                warn(f"{rel(f)}: description should start with a capital letter")
            openings[desc.split(".")[0][:45].lower()].append(name)

        words = len(body.split())
        if strict and words < BODY_MIN:
            err(f"{rel(f)}: body {words} words, minimum {BODY_MIN}")
        if words > BODY_MAX:
            warn(f"{rel(f)}: body {words} words — consider moving detail to references/")
        if not re.search(r"^# .+", body, re.M):
            err(f"{rel(f)}: body has no H1 heading")
        if strict and "Exit checklist" not in body:
            err(f"{rel(f)}: body has no 'Exit checklist' section")
        if re.search(r"^- \[ \]", body, re.M) is None and strict:
            warn(f"{rel(f)}: exit checklist has no checkbox items")

        for link in re.findall(r"\]\((?!https?://|mailto:|#)([^)]+)\)", body):
            target = link.split("#")[0]
            if not target:
                continue
            if not ((d / target).exists() or (ROOT / target).exists()):
                err(f"{rel(f)}: broken link -> {target}")

    for opening, names in openings.items():
        if len(names) > 1:
            warn(f"descriptions start alike ({', '.join(names)}) — routing may collide")
    return found


def check_dir_frontmatter(sub: str, need_name: bool) -> list[Path]:
    out: list[Path] = []
    d = ROOT / sub
    if not d.is_dir():
        err(f"{sub}/: missing")
        return out
    for f in sorted(d.glob("*.md")):
        fm, _ = frontmatter(f.read_text(encoding="utf-8"), f)
        if need_name and not fm.get("name"):
            err(f"{rel(f)}: frontmatter 'name' missing")
        if not fm.get("description"):
            err(f"{rel(f)}: frontmatter 'description' missing")
        out.append(f)
    if not out:
        err(f"{sub}/: contains no markdown files")
    return out


def check_references(skills: dict[str, str]) -> None:
    pattern = re.compile(r"`skills/([a-z0-9-]+)")
    backtick = re.compile(r"`([a-z][a-z0-9-]{4,})`\s+skill")
    for sub in ("commands", "agents"):
        for f in (ROOT / sub).glob("*.md"):
            text = f.read_text(encoding="utf-8")
            for ref in set(pattern.findall(text)) | set(backtick.findall(text)):
                if ref not in skills:
                    err(f"{rel(f)}: references unknown skill '{ref}'")
            for ref in set(re.findall(r"`references/([\w.-]+)`", text)):
                if not (ROOT / "references" / ref).exists():
                    err(f"{rel(f)}: references missing file references/{ref}")


def check_contract_parity() -> None:
    c, a = ROOT / "CLAUDE.md", ROOT / "AGENTS.md"
    if not (c.exists() and a.exists()):
        err("CLAUDE.md or AGENTS.md missing")
        return
    marker = "## 1. Invariants"
    ct, at = c.read_text(encoding="utf-8"), a.read_text(encoding="utf-8")
    if marker not in ct or marker not in at:
        err("operating contract: '## 1. Invariants' section not found in both files")
    elif ct[ct.index(marker):] != at[at.index(marker):]:
        err("CLAUDE.md and AGENTS.md bodies differ — update both together")


def check_evals(skills: dict[str, str]) -> None:
    cdir = ROOT / "evals" / "cases"
    for name in sorted(skills):
        f = cdir / f"{name}.json"
        if not f.exists():
            err(f"evals/cases/{name}.json: missing")
            continue
        try:
            case = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err(f"{rel(f)}: invalid JSON ({e})")
            continue
        if case.get("skill_name") != name:
            err(f"{rel(f)}: skill_name mismatch")
        pos = case.get("trigger", {}).get("positive", [])
        neg = case.get("trigger", {}).get("negative", [])
        if len(pos) < 3:
            err(f"{rel(f)}: needs at least 3 positive prompts, has {len(pos)}")
        if len(neg) < 2:
            err(f"{rel(f)}: needs at least 2 negative prompts, has {len(neg)}")
    for f in sorted(cdir.glob("*.json")):
        if f.stem not in skills:
            warn(f"{rel(f)}: eval case for unknown skill")


def main() -> int:
    skills = check_skills(ROOT)
    check_dir_frontmatter("commands", need_name=False)
    check_dir_frontmatter("agents", need_name=True)
    check_references(skills)
    check_contract_parity()
    check_evals(skills)

    example = ROOT / "examples" / "domain-pack"
    if example.is_dir():
        check_skills(example, strict=False)

    for w in warnings:
        print(f"warn   {w}")
    for e in errors:
        print(f"ERROR  {e}")
    print(f"\n{len(skills)} skills · {len(errors)} errors · {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
