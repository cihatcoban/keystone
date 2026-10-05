#!/usr/bin/env bash
# Optional: inject the router skill at session start.
#
# NOT wired by the plugin. Hosts with native skill routing (Claude Code, Codex)
# already select skills from their descriptions; running this on top adds a
# second router and wastes context. Use it only on hosts without that.
#
# Wire as a SessionStart hook. Output must be the standard envelope or hosts
# that validate hook output will reject it.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
ROUTER="$ROOT/skills/using-skills/SKILL.md"
CONTRACT="$ROOT/CLAUDE.md"

emit() {
  if command -v jq >/dev/null 2>&1; then
    jq -cn --arg c "$1" \
      '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
  else
    printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}\n' \
      "$(python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))' <<<"$1")"
  fi
}

if [[ -f "$ROUTER" && -f "$CONTRACT" ]]; then
  emit "Keystone loaded. Operating contract and skill router follow.

$(cat "$CONTRACT")

$(cat "$ROUTER")"
else
  emit "Keystone: expected files not found at $ROOT. Skills may still be available individually."
fi
