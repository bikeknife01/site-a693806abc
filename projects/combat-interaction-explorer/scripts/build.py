#!/usr/bin/env python3
"""Assemble the static Combat Interaction Explorer."""

from __future__ import annotations

import shutil
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
DIST = PROJECT / "dist"
DATA = ROOT / "projects" / "game-data-encyclopedia" / "public" / "data" / "encyclopedia.json"


def main() -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(PROJECT / "src", DIST)
    (DIST / "data").mkdir()
    shutil.copy2(DATA, DIST / "data" / DATA.name)
    (DIST / ".nojekyll").touch()
    print(f"built {DIST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
