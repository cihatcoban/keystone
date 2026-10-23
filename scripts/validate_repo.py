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
 11  backticked `references/…` and `templates/…` paths in skills, references,
     commands, agents, templates, docs and the contract exist
 12  hook layer: registry schema, a guard per hook ID, every invariant mapped
     to a hook or a stated review-only reason, docs/hooks.md lists exactly the
     registry's IDs, manifests wired, no hooks/hooks.json (ADR-001)
 13  skill counts stated in manifests, README and docs match the skills shipped

Exit code 1 on any error. Warnings never fail the build.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import validate_hooks

ROOT = Path(__file__).resolve().parent.parent
DESC_MIN, DESC_MAX = 80, 500
DESC_TARGET = 320  # every description is injected into every session; see CONTRIBUTING
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
                err(
                    f"{rel(f)}: description {len(desc)} chars, must be {DESC_MIN}-{DESC_MAX}"
                )
            elif len(desc) > DESC_TARGET:
                warn(
                    f"{rel(f)}: description {len(desc)} chars, over the target {DESC_TARGET}"
                )
            if "Triggers" not in desc:
                err(f"{rel(f)}: description must contain a 'Triggers - ...' section")
            if not desc[:1].isupper():
                warn(f"{rel(f)}: description should start with a capital letter")
            openings[desc.split(".")[0][:45].lower()].append(name)

        words = len(body.split())
        if strict and words < BODY_MIN:
            err(f"{rel(f)}: body {words} words, minimum {BODY_MIN}")
        if words > BODY_MAX:
            warn(
                f"{rel(f)}: body {words} words — consider moving detail to references/"
            )
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


POINTER = re.compile(r"`((?:references|templates)/[\w.-]+)`")
POINTER_SOURCES = (
    "skills/*/SKILL.md",
    "references/*.md",
    "commands/*.md",
    "agents/*.md",
    "templates/*.md",
    "docs/**/*.md",
    "CLAUDE.md",
)


def check_doc_pointers(root: Path) -> None:
    """A pointer an agent follows must lead somewhere; a dead one invites invention."""
    seen: set[Path] = set()
    for pattern in POINTER_SOURCES:
        for f in sorted(root.glob(pattern)):
            if f in seen or not f.is_file():
                continue
            seen.add(f)
            text = f.read_text(encoding="utf-8")
            for target in sorted(set(POINTER.findall(text))):
                if not (root / target).is_file():
                    err(f"{f.relative_to(root)}: points to missing file {target}")


COUNT_CLAIM = re.compile(r"\b(\d+) (?:[a-z-]+ )?skills\b")
COUNT_SOURCES = (
    "plugin.json",
    ".claude-plugin/*.json",
    ".agents/plugins/*.json",
    "gemini-extension.json",
    "README.md",
    "docs/*.md",
)
OTHER_PROJECT = re.compile(r"everything-claude-code|\bECC\b")


def check_count_claims(root: Path, count: int) -> None:
    """A listing that says 32 skills when 34 ship is the first fact a user checks."""
    for pattern in COUNT_SOURCES:
        for f in sorted(root.glob(pattern)):
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if OTHER_PROJECT.search(line):
                    continue
                for claim in COUNT_CLAIM.findall(line):
                    if int(claim) != count:
                        err(
                            f"{f.relative_to(root)}:{n}: says {claim} skills, "
                            f"{count} exist"
                        )


def check_contract_parity() -> None:
    c, a = ROOT / "CLAUDE.md", ROOT / "AGENTS.md"
    if not (c.exists() and a.exists()):
        err("CLAUDE.md or AGENTS.md missing")
        return
    marker = "## 1. Invariants"
    ct, at = c.read_text(encoding="utf-8"), a.read_text(encoding="utf-8")
    if marker not in ct or marker not in at:
        err("operating contract: '## 1. Invariants' section not found in both files")
    elif ct[ct.index(marker) :] != at[at.index(marker) :]:
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


AGENT_PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
AGENT_PLUGIN_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
# Codex drops every skill description when the catalog exceeds its budget
# (2% of the context window, 8,000 chars when the window is unknown). Keep
# well inside the 2%-of-200k-tokens line so other installed skills still fit.
CATALOG_WARN_TOKENS, CATALOG_MAX_TOKENS = 3_200, 3_800


def load_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        err(f"{rel(path)}: missing")
        return None
    except (OSError, json.JSONDecodeError) as e:
        err(f"{rel(path)}: unreadable ({e})")
        return None
    if not isinstance(data, dict):
        err(f"{rel(path)}: must contain a JSON object")
        return None
    return data


def check_manifests() -> None:
    """Every agent's manifest, in the shape that agent's loader accepts.

    Each rule here mirrors a check in the agent's own loader, so a manifest the
    agent would reject fails this build instead of failing on a user's machine.
    """
    versions: dict[str, str] = {}

    # Claude Code — .claude-plugin/plugin.json
    f = ROOT / ".claude-plugin" / "plugin.json"
    if (data := load_json(f)) is not None:
        if not data.get("name"):
            err(f"{rel(f)}: 'name' is required")
        for key in ("agents", "commands"):
            value = data.get(key)
            paths = [value] if isinstance(value, str) else (value or [])
            for path in paths:
                if not str(path).endswith(".md"):
                    err(
                        f"{rel(f)}: '{key}' must list .md files, got '{path}' — "
                        f"omit the field to auto-discover {key}/"
                    )
        versions[rel(f)] = data.get("version", "")

    f = ROOT / ".claude-plugin" / "marketplace.json"
    if (data := load_json(f)) is not None:
        for plugin in data.get("plugins", []):
            versions[f"{rel(f)}#{plugin.get('name')}"] = plugin.get("version", "")

    # Codex — root plugin.json as an Agent Plugins manifest
    f = ROOT / "plugin.json"
    if (data := load_json(f)) is not None:
        if data.get("$schema") != AGENT_PLUGIN_SCHEMA:
            err(
                f"{rel(f)}: '$schema' must be {AGENT_PLUGIN_SCHEMA} — without it Codex "
                "ignores this file and falls back to .claude-plugin/plugin.json"
            )
        name = str(data.get("name", ""))
        if (
            not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,63}", name)
            or "--" in name
            or ".." in name
        ):
            err(
                f"{rel(f)}: invalid Agent Plugins name '{name}' (lowercase, digits, dots, hyphens)"
            )
        for key in ("version", "description"):
            if not str(data.get(key, "")).strip():
                err(f"{rel(f)}: '{key}' is required and must be non-empty")
        for key in sorted(set(data) - AGENT_PLUGIN_FIELDS):
            warn(
                f"{rel(f)}: unknown Agent Plugins field '{key}' will be ignored by Codex"
            )
        versions[rel(f)] = data.get("version", "")

    f = ROOT / ".agents" / "plugins" / "marketplace.json"
    if (data := load_json(f)) is not None:
        for plugin in data.get("plugins", []):
            source = plugin.get("source", {})
            if source.get("source") != "local" or source.get("path") not in (".", "./"):
                err(f"{rel(f)}: plugin source must be local with path './' (repo root)")
            if not plugin.get("policy", {}).get("installation"):
                err(f"{rel(f)}: plugin entry needs policy.installation")
            versions[f"{rel(f)}#{plugin.get('name')}"] = plugin.get("version", "")

    # Gemini CLI — gemini-extension.json
    f = ROOT / "gemini-extension.json"
    if (data := load_json(f)) is not None:
        name = str(data.get("name", ""))
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
            err(f"{rel(f)}: name '{name}' must be lowercase letters, digits and dashes")
        if not data.get("version"):
            err(f"{rel(f)}: 'version' is required")
        context = data.get("contextFileName")
        for ctx in [context] if isinstance(context, str) else (context or []):
            if (
                Path(ctx).is_absolute()
                or ".." in Path(ctx).parts
                or not (ROOT / ctx).is_file()
            ):
                err(
                    f"{rel(f)}: contextFileName '{ctx}' must be an existing relative file"
                )
        versions[rel(f)] = data.get("version", "")

    # Gemini sub-agents use the same agents/*.md; names must be slugs there.
    for agent in sorted((ROOT / "agents").glob("*.md")):
        fm, _ = frontmatter(agent.read_text(encoding="utf-8"), agent)
        if fm.get("name") and not re.fullmatch(r"[a-z0-9_-]+", fm["name"]):
            err(
                f"{rel(agent)}: name '{fm['name']}' is not a valid Gemini sub-agent slug"
            )

    distinct = {v for v in versions.values()}
    if len(distinct) > 1:
        detail = ", ".join(f"{k}={v or '(none)'}" for k, v in sorted(versions.items()))
        err(f"manifest versions disagree: {detail}")


def check_adapters() -> None:
    """Generated Gemini commands must match their commands/*.md sources."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_adapters

    try:
        expected = build_adapters.expected_outputs()
    except build_adapters.SourceError as e:
        err(f"commands/: {e}")
        return
    existing = set(build_adapters.GEMINI_DIR.glob("*.toml"))
    for path, content in expected.items():
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            err(
                f"{rel(path)}: stale or missing generated adapter — run `make adapters`"
            )
    for path in sorted(existing - set(expected)):
        err(
            f"{rel(path)}: generated adapter has no commands/*.md source — run `make adapters`"
        )


def check_catalog_budget(skills: dict[str, str]) -> None:
    """Estimate the skill catalog an agent injects into every session."""
    chars = sum(
        len(f"- {name}: {desc} (file: ~/keystone/skills/{name}/SKILL.md)")
        for name, desc in skills.items()
    )
    tokens = chars // 4
    if tokens > CATALOG_MAX_TOKENS:
        err(
            f"skill catalog ≈ {tokens} tokens ({chars} chars) exceeds {CATALOG_MAX_TOKENS}: "
            "Codex removes all descriptions past its budget — shorten descriptions"
        )
    elif tokens > CATALOG_WARN_TOKENS:
        warn(
            f"skill catalog ≈ {tokens} tokens ({chars} chars), close to the "
            f"{CATALOG_MAX_TOKENS}-token limit"
        )


def main() -> int:
    check_manifests()
    check_adapters()
    validate_hooks.check(ROOT, err, load_json)
    skills = check_skills(ROOT)
    check_catalog_budget(skills)
    check_dir_frontmatter("commands", need_name=False)
    check_dir_frontmatter("agents", need_name=True)
    check_references(skills)
    check_doc_pointers(ROOT)
    check_count_claims(ROOT, len(skills))
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
