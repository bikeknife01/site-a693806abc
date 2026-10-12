"""Build the recommendation-facing installed-client dragon knowledge index.

The builder accepts a captured Resources directory so a dated snapshot can refresh
canonical knowledge without making runtime tools depend on the ignored snapshot.
It discovers versioned files by logical name and merges base plus delta localization.
NPC, test, balance, unresolved, and WIP rows remain excluded.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

from _parse_locale import parse_deltas
from _pbdump import dump_file


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "dragon_application_knowledge.json"


def one(value: Any) -> Any:
    if isinstance(value, list) and len(value) == 1:
        return value[0]
    return value


def key(node: Any) -> str | None:
    if isinstance(node, dict):
        value = node.get("2")
        return value if isinstance(value, str) else None
    return None


def as_text(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("1", "")
    return value.strip() if isinstance(value, str) else ""


def clean_text(value: Any) -> str:
    if not value:
        return ""
    value = html.unescape(str(value))
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", value).strip()


def progression_values(node: dict[str, Any]) -> list[Any]:
    body = one(node.get("2", {}))
    if not isinstance(body, dict):
        return []
    packed = one(body.get("1000", {}))
    if not isinstance(packed, dict):
        return []
    for field in ("1001", "1002", "1003"):
        values = one(packed.get(field, {}))
        if isinstance(values, dict) and "2" in values:
            raw_values = values["2"] if isinstance(values["2"], list) else [values["2"]]
            output = []
            for value in raw_values:
                if isinstance(value, dict) and "_fixed64_double" in value:
                    output.append(value["_fixed64_double"])
                elif isinstance(value, (int, float, str)):
                    output.append(value)
            return output
    return []


def discover(resources: Path, logical_name: str, suffix: str) -> Path:
    matches = sorted(resources.glob(f"{logical_name}.*.{suffix}"))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"expected one {logical_name}.VERSION.{suffix} in {resources}, found {len(matches)}"
        )
    return matches[0]


def version_from(path: Path) -> str:
    parts = path.name.split(".")
    return parts[-2] if len(parts) >= 3 else "unknown"


def load_locale(resources: Path) -> tuple[dict[str, str], list[Path]]:
    base_path = discover(resources, "enUS", "txt")
    delta_path = discover(resources, "Deltas_enUS", "txt")
    locale = parse_deltas(base_path)
    locale.update(parse_deltas(delta_path))
    return locale, [base_path, delta_path]


def indexed_rows(table: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row_key: row.get("2", {})
        for row in table.get("1", [])
        if (row_key := key(row.get("1", {})))
    }


def build(resources: Path, snapshot_manifest: Path | None = None) -> dict[str, Any]:
    table_names = (
        "dragonTable_merged",
        "dragonCommandsTable_merged",
        "dragonHabitsTable_merged",
        "dragonAffinityTable_merged",
        "progressionTable_merged",
    )
    table_paths = {name: discover(resources, name, "pb") for name in table_names}
    locale, locale_paths = load_locale(resources)
    tables = {name: dump_file(path) for name, path in table_paths.items()}

    progression_by_key: dict[str, list[Any]] = {}
    for row in tables["progressionTable_merged"].get("1", []):
        body = one(row.get("2", {}))
        row_key = key(body.get("1", {})) if isinstance(body, dict) else None
        if row_key:
            progression_by_key[row_key] = progression_values(row)

    commands_by_key = indexed_rows(tables["dragonCommandsTable_merged"])
    habits_by_key = indexed_rows(tables["dragonHabitsTable_merged"])
    affinities_by_key = indexed_rows(tables["dragonAffinityTable_merged"])
    dragons_by_key = indexed_rows(tables["dragonTable_merged"])

    documented: dict[str, dict[str, Any]] = {}
    for path in (ROOT / "data" / "dragons").glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        documented[record["name"]] = record

    client_only = {
        "Meleys": {
            "availability_status": "user_confirmed_available",
            "availability": "User confirmed Meleys as a Season 3 available dragon on 2026-10-01.",
            "missing": ["Exact numeric values", "Habit upgrade levels", "current screenshot verification"],
        },
        "Smoketail": {
            "availability_status": "user_confirmed_available",
            "availability": "User confirmed Smoketail as a Season 3 available dragon on 2026-10-01.",
            "missing": ["Exact numeric values", "Habit upgrade levels", "current screenshot verification"],
        },
    }

    roster = []
    for dragon_key, body in dragons_by_key.items():
        if not re.match(r"^dragon_(generic|iconic)_", dragon_key):
            continue
        name_key = as_text(body.get("1"))
        name = clean_text(locale.get(name_key, name_key))
        habit_refs = body.get("9", [])
        habit_refs = [habit_refs] if isinstance(habit_refs, dict) else habit_refs
        habit_keys = [key(item) for item in habit_refs]
        habit_rows = [habits_by_key.get(item or "", {}) for item in habit_keys]
        habit_names = [clean_text(locale.get(as_text(item.get("2")), as_text(item.get("2")))) for item in habit_rows]
        if name.startswith("WIP ") or len(habit_rows) != 6 or any("Work in Progress" in item for item in habit_names):
            continue
        if not name or name.endswith("_NAME"):
            continue

        stats = {}
        for field, label in (("15", "strength"), ("16", "intelligence"), ("17", "instinct"), ("18", "initiative"), ("19", "max_army_size")):
            progression_key = key(body.get(field, {}))
            stats[label] = {"progression_key": progression_key, "values_by_level": progression_by_key.get(progression_key or "", [])}
        star_scalars = {}
        for field, label in (("24", "strength"), ("25", "intelligence"), ("26", "instinct"), ("27", "initiative"), ("28", "max_army_size")):
            progression_key = key(body.get(field, {}))
            star_scalars[label] = {"progression_key": progression_key, "values_by_star": progression_by_key.get(progression_key or "", [])}

        command_key = key(body.get("8", {}))
        affinity_key = key(body.get("5", {}))
        affinity = affinities_by_key.get(affinity_key or "", {})
        troop_refs = affinity.get("4", [])
        troop_refs = [troop_refs] if isinstance(troop_refs, dict) else troop_refs
        affinity_values = affinity.get("5", [])
        affinity_values = affinity_values if isinstance(affinity_values, list) else [affinity_values]
        troop_names = {
            "Spear": "Spearmen",
            "Cavalry": "Cavalry",
            "Shield": "Shieldbearers",
            "Range": "Archers",
            "Siege": "Siege",
        }
        affinity_pairs = [
            (troop_names.get(key(troop) or "", key(troop) or ""), value)
            for troop, value in zip(troop_refs, affinity_values)
        ]
        command = commands_by_key.get(command_key or "", {})
        command_name_key = as_text(command.get("2"))
        command_detail_key = as_text(command.get("11")) or as_text(command.get("3"))
        habit_slots = []
        for index, (habit_key, habit, habit_name) in enumerate(zip(habit_keys, habit_rows, habit_names), start=1):
            habit_slots.append({
                "slot": index,
                "client_key": habit_key,
                "name": habit_name,
                "description_template": clean_text(locale.get(as_text(habit.get("3")), "")),
                "ability_key": key(habit.get("5", {})),
            })

        documented_record = documented.get(name)
        documented_evidence = (documented_record or {}).get("evidence", {})
        status = (
            documented_evidence.get("recommendation_status", "screenshot_audited")
            if documented_record
            else "client_discovered"
        )
        availability = ({
            "availability_status": documented_evidence.get("availability_status", "screenshot_observed"),
            "availability": (
                "Established by screenshot-audited record."
                if status == "screenshot_audited"
                else documented_evidence.get("basis", "Established by a reviewed canonical record.")
            ),
            "missing": [],
        } if documented_record else client_only.get(name, {
            "availability_status": "installed_unverified",
            "availability": "Present in the installed client; player availability is not established.",
            "missing": ["Release and availability confirmation", "Exact numeric values", "Habit upgrade levels", "current screenshot verification"],
        }))
        roster.append({
            "name": name,
            "client_key": dragon_key,
            "rarity_key": key(body.get("4", {})),
            "breed_key": key(body.get("6", {})),
            "troop_affinities": {
                "positive": [troop for troop, value in affinity_pairs if value == 2],
                "negative": [troop for troop, value in affinity_pairs if value == 1],
                "neutral": [troop for troop, value in affinity_pairs if value == 0],
                "source_key": affinity_key,
            },
            "recommendation_status": status,
            "availability_status": availability["availability_status"],
            "source_record": f"data/dragons/{name.lower()}.json" if documented_record else None,
            "level_model": {
                "max_level": body.get("23"),
                "vanguard_unlock_level": 16,
                "base_stats_by_level": stats,
                "star_scalars": star_scalars,
                "interpretation": "Use values_by_level at the player's reported dragon level. Star scaling is separate; do not compare raw base stats across different Star Ranks without applying the displayed star scalar.",
            },
            "client_ability_slots": {
                "command": {
                    "client_key": command_key,
                    "name": clean_text(locale.get(command_name_key, command_name_key)),
                    "description_template": clean_text(locale.get(command_detail_key, "")),
                    "ability_key": key(command.get("8", {})),
                },
                "habits_in_slot_order": habit_slots,
            },
            "recommendation_evidence": {
                "screenshot_record_is_primary": status == "screenshot_audited",
                "reviewed_canonical_record_is_primary": documented_record is not None,
                "client_templates_require_caution": status == "client_discovered",
                "availability": availability["availability"],
                "missing_for_full_recommendations": availability["missing"],
            },
        })

    snapshot = json.loads(snapshot_manifest.read_text(encoding="utf-8")) if snapshot_manifest else {}
    source_files = [*table_paths.values(), *locale_paths]
    return {
        "metadata": {
            "purpose": "Canonical client-derived roster, level progression, and ability-template index for formation recommendations.",
            "source": "Locally extracted installed application tables under Game_Details/Resources.",
            "snapshot_date": snapshot.get("snapshot_date"),
            "client_version": snapshot.get("version_name"),
            "version_code": snapshot.get("version_code"),
            "client_versions": {name: version_from(path) for name, path in table_paths.items()},
            "localization_versions": {path.name.split(".")[0]: version_from(path) for path in locale_paths},
            "source_files": [path.name for path in source_files],
            "comparison_baseline": "2026-09-16 client 26.9.56160" if snapshot.get("snapshot_date") == "2026-10-01" else None,
            "continuing_evidence_policy": "Unchanged logical resources in the captured installed build remain current installed-client evidence; a no-diff result does not make an older table irrelevant.",
            "scope": f"{len(roster)} production-named client rows; WIP, test, NPC, wild, balance-test, and unresolved rows are excluded.",
            "evidence_policy": "Reviewed canonical dragon records remain primary for exact current mechanics. Their evidence class distinguishes screenshot-audited records from explicitly approved cross-site verification. Client templates and level curves supplement them; client-only rows must be labeled client-discovered and their missing fields disclosed.",
        },
        "recommendation_contract": {
            "required_player_inputs": ["dragon name", "dragon level", "Star Rank", "Habit skill levels", "visible Power", "available dragons", "scenario", "enemy formation and troop type when applicable"],
            "level_rule": "Level affects base Strength, Intelligence, Instinct, Initiative, and Max Army Size through base_stats_by_level. Use the reported level rather than a screenshot's historical stat snapshot.",
            "do_not_infer": ["release status from client presence", "missing numeric ability values", "Habit skill levels for client-only rows", "hidden combat ordering or formulas"],
        },
        "dragons": sorted(roster, key=lambda item: item["name"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--resources",
        type=Path,
        required=True,
        help="captured Android Resources directory; required to avoid silently rebuilding from the historical working set",
    )
    parser.add_argument("--snapshot-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = build(args.resources, args.snapshot_manifest)
    if args.check:
        print(f"valid ({len(output['dragons'])} production-named dragon records)")
        return 0
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(output['dragons'])} production-named dragon records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
