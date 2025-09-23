#!/usr/bin/env python3
"""Verify brains journal entry exists and has required sections."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERN = re.compile(r"^v\d+\.\d+\.\d+[a-z]__.+\.md$")
REQUIRED_HEADINGS = [
    "## Context",
    "## Changes",
    "## Decisions",
    "## Tests & Evidence",
    "## Regressions Prevented",
    "## Follow-ups",
    "## Checklist",
]


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    brains_dir = root / "brains"
    entries = sorted([path for path in brains_dir.glob("*.md") if PATTERN.match(path.name)])
    if not entries:
        print("No brains entries found")
        return 1
    latest = entries[-1]
    text = latest.read_text(encoding="utf-8")
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in text]
    if missing:
        print(f"Brains entry {latest.name} missing headings: {', '.join(missing)}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
