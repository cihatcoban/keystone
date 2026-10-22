#!/bin/sh
# Launch the Keystone hook dispatcher with whatever Python is on PATH.
# With no Python the hook does nothing and says nothing: Keystone's hooks are
# stdlib Python by rule, and a missing interpreter must not turn into an error
# notice on every tool call. keystone_hook.py itself exits quietly below 3.9.
dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1; then
    exec "$py" "$dir/keystone_hook.py" "$@"
  fi
done
cat >/dev/null
exit 0
