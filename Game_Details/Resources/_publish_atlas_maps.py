#!/usr/bin/env python3
"""Assemble versioned Atlas maps and the season selector for static hosting."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTRACTED = ROOT / "Game_Details" / "Resources" / "_extracted"
SELECTOR = ROOT / "projects" / "strategic-atlas-overlays" / "src" / "map-selector.html"
ASSETS = ("worldmap_background.jpg", "region_color_overlay.png", "mountain_overlay.png")
MAPS = (
    ("season1", EXTRACTED / "seasons" / "season1", "interactive_map.html"),
    ("season2", EXTRACTED, "interactive_map.html"),
    ("season3", EXTRACTED / "seasons" / "season3", "interactive_map.html"),
)


def _replace_once(content: str, old: str, new: str, description: str) -> str:
    count = content.count(old)
    if count != 1:
        raise ValueError(f"expected one {description}, found {count}")
    return content.replace(old, new, 1)


def _map_html(slug: str, source: Path) -> str:
    content = source.read_text(encoding="utf-8")
    for asset in ASSETS:
        content = _replace_once(
            content,
            f'href="{asset}"',
            f'href="assets/{slug}/{asset}"',
            f"{asset} image reference",
        )

    if slug != "season2":
        # The encyclopedia currently contains Bravo placement IDs only. Avoid
        # presenting another season's row indexes as exact Bravo records.
        content = _replace_once(
            content,
            "const recordHref = `../encyclopedia/#/map-nodes/${encodeURIComponent(d.sid.split(':')[1])}`;",
            "const recordHref = '../encyclopedia/#/map-nodes';",
            f"{slug} encyclopedia target",
        )
        content = _replace_once(
            content,
            "nav.innerHTML = 'View selected node in encyclopedia &#8599;';",
            "nav.innerHTML = 'Browse encyclopedia map records &#8599;';",
            f"{slug} encyclopedia navigation label",
        )
        content = _replace_once(
            content,
            "Open encyclopedia record &#8599;",
            "Browse encyclopedia map records &#8599;",
            f"{slug} encyclopedia detail label",
        )
    if slug == "season3":
        manifest = json.loads((source.parent / "source_manifest.json").read_text(encoding="utf-8"))
        count = manifest["poi_count"]
        content = _replace_once(
            content,
            "Explore territories, inspect map nodes, and evaluate routes around mountain barriers.",
            f"Season 3 · Campaign Charlie · {count:,} static POIs. Routes are estimates: "
            "terrain coverage is partial. Ruin levels may scale in game.",
            "Charlie map description",
        )
    return content


def publish(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SELECTOR, output / "index.html")
    for slug, source_dir, html_name in MAPS:
        source_html = source_dir / html_name
        (output / f"{slug}.html").write_text(_map_html(slug, source_html), encoding="utf-8")
        asset_dir = output / "assets" / slug
        asset_dir.mkdir(parents=True, exist_ok=True)
        for asset in ASSETS:
            shutil.copy2(source_dir / asset, asset_dir / asset)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    publish(args.output_dir.resolve())
    print(f"assembled Atlas seasons 1, 2 and 3 in {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
