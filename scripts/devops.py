#!/usr/bin/env python3
# Copyright (c) Giovanni Pellicciotta
"""Runs the typical operations of this project through its virtual environment.

Run `python scripts/bootstrap-dev-environment.py` first to create the virtual environment.

Usage:
  python scripts/devops.py lint | format | build | check | clean
  python scripts/devops.py test [SELECTION...] [-- PYTEST-OPTIONS...]
  python scripts/devops.py versions
  python scripts/devops.py release [--dry-run] [--skip-checks] [--yes]
  python scripts/devops.py help [--verbose] | version
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from support_python.devops import DevopsCli, PythonProject  # noqa: E402
from support_python.tools import TOOLS_COPYRIGHT  # noqa: E402

if __name__ == "__main__":
    sys.exit(DevopsCli(PythonProject(REPO_ROOT), copyright=TOOLS_COPYRIGHT).run())
