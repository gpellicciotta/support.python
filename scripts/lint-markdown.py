#!/usr/bin/env python3
# Copyright (c) Giovanni Pellicciotta
"""Standalone entry point for the Markdown linter."""

from __future__ import annotations

from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if SRC_DIR.is_dir() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from support_python.markdown_lint import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
