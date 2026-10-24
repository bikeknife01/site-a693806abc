#!/usr/bin/env python3
"""Generate the encyclopedia dataset and assemble a static dist directory."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
DIST = PROJECT / "dist"
PREVIEW = PROJECT / "preview"
NORMALIZER = ROOT / "projects" / "shared-data-foundation" / "src" / "normalize" / "build_encyclopedia_data.py"
ATLAS_PUBLISHER = ROOT / "Game_Details" / "Resources" / "_publish_atlas_maps.py"
COMBAT_DIST = ROOT / "projects" / "combat-interaction-explorer" / "dist"
COUNTER_DIST = ROOT / "projects" / "counter-picking-assistant" / "dist"
LANDING_DIST = ROOT / "projects" / "player-tools-index" / "dist"


def assemble_preview() -> None:
    """Mirror the GitHub Pages layout for local cross-tool testing."""
    if PREVIEW.exists():
        shutil.rmtree(PREVIEW)
    PREVIEW.mkdir(parents=True)
    (PREVIEW / "map").mkdir(parents=True)
    if LANDING_DIST.exists():
        shutil.copytree(LANDING_DIST, PREVIEW, dirs_exist_ok=True)
    shutil.copytree(DIST, PREVIEW / "encyclopedia")
    if COMBAT_DIST.exists():
        shutil.copytree(COMBAT_DIST, PREVIEW / "combat")
    if COUNTER_DIST.exists():
        shutil.copytree(COUNTER_DIST, PREVIEW / "counter")
    subprocess.run(
        [sys.executable, str(ATLAS_PUBLISHER), "--output-dir", str(PREVIEW / "map")],
        cwd=ROOT,
        check=True,
    )
    (PREVIEW / ".nojekyll").touch()
    print(f"assembled local preview {PREVIEW}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="also assemble the deployed /map and /encyclopedia layout")
    args = parser.parse_args()
    subprocess.run([sys.executable, str(NORMALIZER)], cwd=ROOT, check=True)
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(PROJECT / "src", DIST)
    shutil.copytree(PROJECT / "public", DIST, dirs_exist_ok=True)
    (DIST / ".nojekyll").touch()
    print(f"built {DIST}")
    if args.preview:
        assemble_preview()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
