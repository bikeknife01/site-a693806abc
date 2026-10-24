#!/usr/bin/env python3
"""Rebuild a season in an isolated workspace from one captured resource set.

The legacy builders own the generated HTML and images. Run unchanged copies,
except for their map-prefix setting and campaign labels, so an older season is never
overwritten or silently used to fill gaps in a newer campaign's evidence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
LEGACY_PREFIX = "MAP_PREFIX = 'Westeros_Bravo_4_L4Sanctums'"
STEPS = (
    "_harvest_ids.py", "_build_map_nodes.py", "_build_worldmap_bg.py",
    "_build_region_data.py", "_build_terrain_data.py",
    "_build_terrain_navigation.py", "_build_crossing_chains.py",
    "_build_interactive_map.py",
)
PUBLISHED = (
    "interactive_map.html", "worldmap_background.jpg", "region_color_overlay.png",
    "mountain_overlay.png", "clean_map_nodes.csv", "node_place_names.json",
    "crossing_chains.json", "terrain_navigation.json",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(args: argparse.Namespace) -> dict:
    resources = args.resource_dir.resolve()
    work = args.work_dir.resolve()
    output = args.output_dir.resolve()
    if not args.map_prefix.replace("_", "").isalnum():
        raise ValueError("map prefix must contain only letters, digits and underscores")
    if not resources.is_dir():
        raise ValueError("resource directory does not exist")
    if output.exists():
        raise ValueError("output must be a new directory; preserve earlier season builds")
    for suffix in ("Poi_Rtree_Client.*.pb", "Client.description.*.json",
                   "WorldMapRegionIndex_Bitmap.*.r8",
                   "WorldMap_DiffuseAndSmoothness_Bitmap.*.astc",
                   "WorldMap_NormalsAndShadow_Bitmap.*.astc"):
        matches = list(resources.glob(f"{args.map_prefix}_{suffix}"))
        if len(matches) != 1:
            raise ValueError(f"expected one {suffix}, found {len(matches)}")
    work.mkdir(parents=True, exist_ok=False)
    extracted = work / "_extracted"
    extracted.mkdir()
    sources = []
    for path in sorted(resources.iterdir()):
        # Static tables plus this campaign's spatial evidence only.
        if not path.is_file():
            continue
        if not (path.name.startswith(args.map_prefix + "_") or
                (path.suffix == ".pb" and not path.name.startswith("Westeros_"))):
            continue
        shutil.copy2(path, work / path.name)
        sources.append({"file": path.name, "bytes": path.stat().st_size, "sha256": digest(path)})
    scripts = []
    for name in (*STEPS, "_pbdump.py"):
        source = BASE / name
        code = source.read_text(encoding="utf-8")
        code = code.replace(LEGACY_PREFIX, f"MAP_PREFIX = {args.map_prefix!r}")
        if name == "_build_interactive_map.py":
            code = code.replace("Interactive world map · Bravo", f"Interactive world map · {args.campaign}")
            code = code.replace("Bravo campaign · Showing", f"{args.campaign} campaign · Showing")
        (work / name).write_text(code, encoding="utf-8")
        scripts.append({"file": name, "sha256": digest(source)})
    for name in STEPS:
        command = [sys.executable, str(work / name)]
        if name == "_build_terrain_navigation.py":
            command += ["--source-label", args.source_label]
        print(f"Running {name}", flush=True)
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        (work / f"{name}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"{name} failed; see {work / (name + '.log')}")
        if name == "_build_map_nodes.py":
            with (extracted / "clean_map_nodes.csv").open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            if not rows or any(not r["template_key"] or "unknown" in r["type_name"].lower() for r in rows):
                raise ValueError("unresolved POI templates; review before publishing")
    navigation = json.loads((extracted / "terrain_navigation.json").read_text(encoding="utf-8"))
    region_names = json.loads((extracted / "node_place_names.json").read_text(encoding="utf-8"))
    region_log = (work / "_build_region_data.py.log").read_text(encoding="utf-8")
    gap = re.search(r"leaving (\d+) trailing pixels zero", region_log)
    report = {
        "schema": "atlas-season-source-1.0.0", "source": args.source_label,
        "snapshot_date": args.snapshot_date, "map_prefix": args.map_prefix,
        "campaign": args.campaign,
        "poi_count": len(rows), "types": dict(sorted(Counter(r["type_name"] for r in rows).items())),
        "terrain_navigation": navigation,
        "region_layer": {
            "unassigned_pois": sum(not name for name in region_names),
            "trailing_zero_pixels": int(gap.group(1)) if gap else 0,
        },
        "limitations": [
            "POIs and template levels are installed static placements, not current ownership or upgraded levels.",
            "Terrain chunks are a partial client cache. Routes use geographic fallback where terrain is unknown.",
            "Crossing connections are inferred from placement proximity, not server adjacency.",
            "Unassigned region labels stay blank; trailing region-texture gaps render as zero/ocean.",
        ],
        "sources": sources, "builders": scripts,
        "generated": [{"file": name, "sha256": digest(extracted / name)} for name in PUBLISHED],
    }
    (extracted / "source_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    output.mkdir(parents=True)
    for name in (*PUBLISHED, "source_manifest.json"):
        shutil.copy2(extracted / name, output / name)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("resource-dir", "work-dir", "output-dir"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in ("map-prefix", "source-label", "snapshot-date"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--campaign", choices=("Alpha", "Bravo", "Charlie"), required=True)
    report = build(parser.parse_args())
    print(f"Built {report['poi_count']:,} POIs for {report['map_prefix']}")


if __name__ == "__main__":
    main()
