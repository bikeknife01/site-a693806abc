"""Build a compact, auditable terrain-category layer for Atlas navigation.

The output is a palette PNG aligned to the Atlas background: 0 means that the
captured client has no terrain evidence for the cell, 1 is Default, 2 Coast,
3 Mountain, 4 Water, and 5 Error.  The interactive-map builder uses known
Default cells as walkable and known non-Default terrain as blocked; code 0
falls back to the older region/mountain/river evidence.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from PIL import Image

import _build_terrain_data as terrain_data


BASE = Path(__file__).resolve().parent
EXT = BASE / "_extracted"
CODES = {"Default": 1, "Coast": 2, "Mountain": 3, "Water": 4, "Error": 5}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--resource-dir",
        default=str(BASE),
        help="directory containing TerrainDataTable and Westeros terrain chunks",
    )
    parser.add_argument(
        "--source-label",
        default="repository resource set",
        help="portable provenance label recorded beside the generated layer",
    )
    args = parser.parse_args()

    resource_dir = Path(args.resource_dir).resolve()
    terrain_data.BASE = str(resource_dir)
    categories = terrain_data.load_terrain_category_names()
    chunks = terrain_data.load_terrain_tiles(categories)

    with Image.open(EXT / "worldmap_background.jpg") as background:
        width, height = background.size
    raw = bytearray(width * height)
    for x0, y0, chunk_width, chunk_height, grid in chunks:
        for local_y, row in enumerate(grid):
            world_y = y0 + local_y
            if not 0 <= world_y < height:
                continue
            offset = world_y * width
            for local_x, category in enumerate(row):
                world_x = x0 + local_x
                if 0 <= world_x < width:
                    raw[offset + world_x] = CODES.get(category, 0)

    # Atlas images use north-up screen coordinates; decoded chunks use game Y.
    flipped = bytearray(len(raw))
    for y in range(height):
        source = y * width
        destination = (height - 1 - y) * width
        flipped[destination : destination + width] = raw[source : source + width]

    output = Image.frombytes("P", (width, height), bytes(flipped))
    palette = [0, 0, 0, 78, 160, 94, 214, 174, 93, 91, 70, 54, 44, 96, 150, 255, 0, 255]
    palette.extend([0] * (768 - len(palette)))
    output.putpalette(palette)
    output.save(EXT / "terrain_navigation.png", optimize=True)

    counts = Counter(raw)
    manifest = {
        "schema": "atlas-terrain-navigation-1.0.0",
        "source": args.source_label,
        "dimensions": [width, height],
        "terrain_chunks": len(chunks),
        "codes": {"unknown": 0, **{key.lower(): value for key, value in CODES.items()}},
        "cell_counts": {
            "unknown": counts[0],
            **{key.lower(): counts[value] for key, value in CODES.items()},
        },
    }
    (EXT / "terrain_navigation.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"decoded {len(chunks):,} terrain chunks from {args.source_label}")
    print(f"wrote {EXT / 'terrain_navigation.png'}")
    print(f"wrote {EXT / 'terrain_navigation.json'}")


if __name__ == "__main__":
    main()
