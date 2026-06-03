#!/usr/bin/env python3
"""Compatibility wrapper for the packaged CLI."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from todoist_obsidian_bridge.cli import main  # noqa: E402


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv or argv[0].startswith("-"):
        argv = ["run", *argv]
    raise SystemExit(main(argv))
