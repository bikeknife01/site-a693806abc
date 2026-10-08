#!/usr/bin/env python3
"""Compare two installed-client resource roots and map changes to repository consumers.

This tool reports client evidence only. It never edits canonical data and never treats
resource presence as proof that staged content is live or server-active.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from _parse_locale import parse_deltas
from _pbdump import dump_file


ANALYZER_VERSION = "1.0.0"
VERSION_PATTERN = re.compile(r"\.\d{10}(?=\.)")


@dataclass(frozen=True)
class ImpactRule:
    pattern: re.Pattern[str]
    domain: str
    consumers: tuple[str, ...]
    review: str


IMPACT_RULES = (
    ImpactRule(
        re.compile(r"dragon(?:Table|Abilities|AbilityConditions|Affinity|Commands|EffectGroups|Effects|Habits|Progression|Targeter)|Dragon(?:AbilityLabels|Breed|Command|Power|Rarity|Settings|Shard|Stat|Status|TargetPrioritizers)", re.I),
        "dragon_combat",
        (
            "data/dragons/*.json",
            "data/effects.json",
            "data/game_mechanics.json",
            "data/dragon_application_knowledge.json",
            "RECOMMENDATION_HANDOFF.md",
            ".github/agents/dragonfire-strategist.agent.md",
            "projects/game-data-encyclopedia",
            "projects/combat-interaction-explorer",
            "projects/counter-picking-assistant",
            "projects/recommendation-planner",
        ),
        "Review row-level mechanics, lifecycle, unlock gates, normalized graph records, recommendation behavior, and all combat consumers.",
    ),
    ImpactRule(
        re.compile(r"Commander|commander", re.I),
        "commander",
        (
            "data/dragon_application_knowledge.json",
            "data/live_updates.json",
            "wiki",
            ".github/agents/dragonfire-strategist.agent.md",
            "projects/game-data-encyclopedia",
        ),
        "Review traits, talent gates, status interactions, and whether the content is live or merely staged.",
    ),
    ImpactRule(
        re.compile(r"(?:^|_)Westeros_|WorldMap|Biome|Footprint|Region|Poi|Crossing", re.I),
        "world_map",
        (
            "Game_Details/Resources/_extracted",
            "projects/game-data-encyclopedia",
            "wiki",
        ),
        "Distinguish changed logical map resources from newly completed cache chunks before claiming a map revision.",
    ),
    ImpactRule(
        re.compile(r"Quest|Task|Event|Campaign|Shop|Offer|Gacha|Ambition|Achievement", re.I),
        "campaign_or_economy",
        (
            "data/live_updates.json",
            "data/dragon_application_knowledge.json",
            "wiki",
            "projects/game-data-encyclopedia",
        ),
        "Treat additions as possible campaign staging until activation or player-availability evidence exists.",
    ),
    ImpactRule(
        re.compile(r"(?:Deltas_)?[a-z]{2}[A-Z]{2}\.VERSION\.txt$", re.I),
        "localization",
        (
            "data/dragons/*.json",
            "data/effects.json",
            "data/dragon_application_knowledge.json",
            "data/live_updates.json",
            "wiki",
            ".github/agents/dragonfire-strategist.agent.md",
        ),
        "Review added and modified strings as wording evidence; delta strings may be staged and do not prove activation.",
    ),
)


def logical_name(path: Path | str) -> str:
    """Normalize a ten-digit content version while preserving the logical extension."""
    return VERSION_PATTERN.sub(".VERSION", Path(path).name)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def index_resources(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        raise ValueError(f"Resource root does not exist: {root}")
    result: dict[str, Path] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        key = logical_name(path)
        if key in result:
            raise ValueError(f"Duplicate logical resource {key!r} under {root}")
        result[key] = path
    return result


def row_key(row: object, position: int) -> str:
    if isinstance(row, dict):
        ident = row.get("1")
        if isinstance(ident, dict):
            for field in ("2", "1"):
                value = ident.get(field)
                if isinstance(value, str) and value:
                    return value
                if value is not None:
                    return json.dumps(value, sort_keys=True, ensure_ascii=False)
        if isinstance(ident, str) and ident:
            return ident
    return f"__row_{position:06d}"


def rows_by_key(document: object) -> dict[str, object]:
    rows = document.get("1", []) if isinstance(document, dict) else []
    if not isinstance(rows, list):
        rows = [rows]
    result: dict[str, object] = {}
    for position, row in enumerate(rows):
        key = row_key(row, position)
        if key in result:
            key = f"{key}#{position}"
        result[key] = row
    return result


def changed_paths(old: object, new: object, limit: int = 80) -> list[dict[str, object]]:
    changes: list[dict[str, object]] = []

    def walk(left: object, right: object, pointer: str) -> None:
        if len(changes) >= limit:
            return
        if type(left) is not type(right):
            changes.append({"path": pointer, "old": left, "new": right})
        elif isinstance(left, dict) and isinstance(right, dict):
            for key in sorted(set(left) | set(right), key=str):
                child = f"{pointer}.{key}" if pointer else str(key)
                if key not in left:
                    changes.append({"path": child, "old": None, "new": right[key]})
                elif key not in right:
                    changes.append({"path": child, "old": left[key], "new": None})
                else:
                    walk(left[key], right[key], child)
                if len(changes) >= limit:
                    return
        elif isinstance(left, list) and isinstance(right, list):
            if left != right:
                changes.append({"path": pointer, "old": left, "new": right})
        elif left != right:
            changes.append({"path": pointer, "old": left, "new": right})

    walk(old, new, "")
    return changes


def resource_impacts(logical_names: list[str]) -> dict[str, object]:
    domains: dict[str, dict[str, Any]] = {}
    unmatched: list[str] = []
    for name in sorted(set(logical_names)):
        matching = [rule for rule in IMPACT_RULES if rule.pattern.search(name)]
        if not matching:
            unmatched.append(name)
            continue
        for rule in matching:
            entry = domains.setdefault(rule.domain, {"resources": [], "consumers": set(), "review_actions": set()})
            entry["resources"].append(name)
            entry["consumers"].update(rule.consumers)
            entry["review_actions"].add(rule.review)
    return {
        "policy": "Impacts are deterministic review routing only. They do not update canonical facts or establish that client content is live.",
        "domains": {
            domain: {
                "resources": sorted(entry["resources"]),
                "consumers": sorted(entry["consumers"]),
                "review_actions": sorted(entry["review_actions"]),
            }
            for domain, entry in sorted(domains.items())
        },
        "unmatched_resources": unmatched,
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def compare_resources(old_root: Path, new_root: Path) -> tuple[dict[str, object], list[tuple[str, Path, Path]]]:
    old_index = index_resources(old_root)
    new_index = index_resources(new_root)
    manifest: dict[str, Any] = {
        "old_root": str(old_root.resolve()),
        "new_root": str(new_root.resolve()),
        "old_files": len(old_index),
        "new_files": len(new_index),
        "added": sorted(set(new_index) - set(old_index)),
        "removed": sorted(set(old_index) - set(new_index)),
        "changed": [],
        "version_only": [],
    }
    content_changed: list[tuple[str, Path, Path]] = []
    for key in sorted(set(old_index) & set(new_index)):
        old_path, new_path = old_index[key], new_index[key]
        old_hash, new_hash = sha256(old_path), sha256(new_path)
        if old_hash == new_hash and old_path.name == new_path.name:
            continue
        item = {
            "logical_name": key,
            "old_name": old_path.name,
            "new_name": new_path.name,
            "old_bytes": old_path.stat().st_size,
            "new_bytes": new_path.stat().st_size,
            "old_sha256": old_hash,
            "new_sha256": new_hash,
        }
        if old_hash == new_hash:
            manifest["version_only"].append(item)
        else:
            manifest["changed"].append(item)
            content_changed.append((key, old_path, new_path))
    return manifest, content_changed


def decode_table_changes(changes: list[tuple[str, Path, Path]], output: Path) -> dict[str, object]:
    summary: dict[str, object] = {}
    for key, old_path, new_path in changes:
        if old_path.suffix.lower() != ".pb" or key.startswith("Westeros_"):
            continue
        old_doc, new_doc = dump_file(str(old_path)), dump_file(str(new_path))
        safe_name = key.replace(".VERSION", "")
        write_json(output / "decoded" / "old" / f"{safe_name}.json", old_doc)
        write_json(output / "decoded" / "new" / f"{safe_name}.json", new_doc)
        old_rows, new_rows = rows_by_key(old_doc), rows_by_key(new_doc)
        added = sorted(set(new_rows) - set(old_rows))
        removed = sorted(set(old_rows) - set(new_rows))
        modified = sorted(row for row in set(old_rows) & set(new_rows) if old_rows[row] != new_rows[row])
        summary[key] = {
            "old_rows": len(old_rows),
            "new_rows": len(new_rows),
            "added": added,
            "removed": removed,
            "modified": modified,
            "modified_details": {row: changed_paths(old_rows[row], new_rows[row]) for row in modified},
        }
    return summary


def compare_locales(old_root: Path, new_root: Path, output: Path) -> dict[str, object]:
    old_index, new_index = index_resources(old_root), index_resources(new_root)
    summary: dict[str, object] = {}
    for key in ("Deltas_enUS.VERSION.txt", "enUS.VERSION.txt"):
        if key not in old_index or key not in new_index:
            continue
        old_locale, new_locale = parse_deltas(str(old_index[key])), parse_deltas(str(new_index[key]))
        added, removed = sorted(set(new_locale) - set(old_locale)), sorted(set(old_locale) - set(new_locale))
        modified = sorted(item for item in set(old_locale) & set(new_locale) if old_locale[item] != new_locale[item])
        summary[key] = {
            "old_entries": len(old_locale),
            "new_entries": len(new_locale),
            "added": {item: new_locale[item] for item in added},
            "removed": {item: old_locale[item] for item in removed},
            "modified": {item: {"old": old_locale[item], "new": new_locale[item]} for item in modified},
        }
        write_json(output / "decoded" / "old" / f"{key}.json", old_locale)
        write_json(output / "decoded" / "new" / f"{key}.json", new_locale)
    return summary


def markdown_report(metadata: dict[str, object], manifest: dict[str, object], impacts: dict[str, object]) -> str:
    lines = [
        "# Installed-client update analysis",
        "",
        "> Client presence is evidence that data exists in the captured build. It does not prove release status, server activation, player availability, or final balance.",
        "",
        "## Capture and comparison",
        "",
        f"- Snapshot date: {metadata['snapshot_date']}",
        f"- Old client/build: {metadata.get('old_client_version') or 'not supplied'} / {metadata.get('old_version_code') or 'not supplied'}",
        f"- New client/build: {metadata.get('new_client_version') or 'not supplied'} / {metadata.get('new_version_code') or 'not supplied'}",
        f"- Analyzer: {metadata['analyzer']} {metadata['analyzer_version']}",
        f"- Added logical resources: {len(manifest['added'])}",
        f"- Removed logical resources: {len(manifest['removed'])}",
        f"- Content-changing resources: {len(manifest['changed'])}",
        f"- Version-only renames: {len(manifest['version_only'])}",
        "",
        "## Routed consumer review",
        "",
    ]
    domains = impacts["domains"]
    if not domains:
        lines.append("No changed logical resource matched a known consumer-impact rule.")
    for domain, detail in domains.items():
        lines.extend([f"### {domain}", "", f"Changed resources: {', '.join(detail['resources'])}", "", "Review consumers:", ""])
        lines.extend(f"- `{consumer}`" for consumer in detail["consumers"])
        lines.extend(["", "Review actions:", ""])
        lines.extend(f"- {action}" for action in detail["review_actions"])
        lines.append("")
    if impacts["unmatched_resources"]:
        lines.extend(["## Unmatched changed resources", "", *[f"- `{name}`" for name in impacts["unmatched_resources"]], ""])
    return "\n".join(lines).rstrip() + "\n"


def analyze(args: argparse.Namespace) -> dict[str, object]:
    old_root, new_root, output = Path(args.old), Path(args.new), Path(args.output)
    manifest, content_changed = compare_resources(old_root, new_root)
    table_summary = {} if args.skip_decode else decode_table_changes(content_changed, output)
    locale_summary = compare_locales(old_root, new_root, output)
    changed_names = [*manifest["added"], *manifest["removed"], *[item["logical_name"] for item in manifest["changed"]]]
    impacts = resource_impacts(changed_names)
    metadata = {
        "snapshot_date": args.snapshot_date,
        "old_client_version": args.old_client_version,
        "new_client_version": args.new_client_version,
        "old_version_code": args.old_version_code,
        "new_version_code": args.new_version_code,
        "capture_scope": args.capture_scope,
        "analyzer": "Game_Details/Resources/analyze_update.py",
        "analyzer_version": ANALYZER_VERSION,
        "old_root_sha256_manifest": {key: sha256(value) for key, value in sorted(index_resources(old_root).items())},
        "new_root_sha256_manifest": {key: sha256(value) for key, value in sorted(index_resources(new_root).items())},
    }
    write_json(output / "analysis" / "comparison_metadata.json", metadata)
    write_json(output / "analysis" / "resource_manifest.json", manifest)
    write_json(output / "analysis" / "table_diff_summary.json", table_summary)
    write_json(output / "analysis" / "localization_diff.json", locale_summary)
    write_json(output / "analysis" / "impact_report.json", impacts)
    report = markdown_report(metadata, manifest, impacts)
    (output / "analysis" / "update_report.md").write_text(report, encoding="utf-8")
    return {"metadata": metadata, "manifest": manifest, "tables": table_summary, "localization": locale_summary, "impacts": impacts}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--old", required=True, help="old Resources directory")
    result.add_argument("--new", required=True, help="new Resources directory")
    result.add_argument("--output", required=True, help="snapshot/output directory")
    result.add_argument("--snapshot-date", default=date.today().isoformat())
    result.add_argument("--old-client-version")
    result.add_argument("--new-client-version")
    result.add_argument("--old-version-code")
    result.add_argument("--new-version-code")
    result.add_argument("--capture-scope", default="Resources directories supplied by the operator; capture method not specified")
    result.add_argument("--skip-decode", action="store_true", help="skip schema-less protobuf row decoding")
    return result


def main() -> int:
    args = parser().parse_args()
    result = analyze(args)
    manifest = result["manifest"]
    print(
        f"resources old={manifest['old_files']} new={manifest['new_files']}; "
        f"added={len(manifest['added'])}; removed={len(manifest['removed'])}; "
        f"content_changed={len(manifest['changed'])}; version_only={len(manifest['version_only'])}; "
        f"impact_domains={len(result['impacts']['domains'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

