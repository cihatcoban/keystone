#!/usr/bin/env python3
"""Keystone hook entry point. Every harness manifest calls this file.

    keystone_hook.py --harness <claude-code|codex|gemini> --trigger <trigger>

Reads the harness's hook input on stdin and prints the harness's own decision
format on stdout. It always exits 0 and fails open: a guard that crashes is
skipped, never turned into a block. See docs/hooks.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info < (3, 9):  # python2 or an old python3: do nothing, quietly
    sys.exit(0)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from keystone_hooks.dispatch import main  # noqa: E402 — needs the sys.path insert above; hooks/ is not installed as a package

if __name__ == "__main__":
    sys.exit(main())
