#!/usr/bin/env python3
"""Ensure version artifacts stay in sync."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VERSION_PATTERN = re.compile(r"^(?P<base>\d+\.\d+\.\d+)(?P<letter>[a-z])$")


def _load_version(root: Path) -> tuple[str, str]:
    payload = json.loads((root / "app" / "config" / "version.json").read_text())
    app_version = payload["app_version"]
    match = VERSION_PATTERN.match(app_version)
    if not match:
        raise ValueError(f"app_version {app_version!r} not in expected format")
    return match.group("base"), match.group("letter")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    try:
        base, letter = _load_version(root)
    except ValueError as exc:
        print(exc)
        return 1

    patch_name = root / "PATCH_NOTES" / f"PATCH_NOTES_v{base}({letter}).md"
    if not patch_name.exists():
        print(f"Patch notes missing: {patch_name.name}")
        return 1

    brains_matches = list(root.glob(f"brains/v{base}{letter}__*.md"))
    if not brains_matches:
        print("Brains entry for version missing")
        return 1

    handoff_matches = list(root.glob(f"handoffs/HANDOFF_v{base}({letter}).md"))
    if not handoff_matches:
        print("Handoff file missing")
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
