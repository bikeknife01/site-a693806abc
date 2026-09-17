"""Build the recommendation-facing Dragonfire client knowledge file.

This intentionally filters NPC, test, and WIP rows from the application roster.
It preserves the source keys and level curves so the agent can reason about a
player's actual dragon level without treating raw client presence as release proof.
"""
import csv
import html
import json
import os
import re
import sys

BASE = os.path.dirname(__file__)
ROOT = os.path.normpath(os.path.join(BASE, "..", ".."))
EXTRACTED = os.path.join(BASE, "_extracted")
sys.path.insert(0, BASE)
from _pbdump import dump_file


def one(value):
    if isinstance(value, list) and len(value) == 1:
        return value[0]
    return value


def key(node):
    if isinstance(node, dict):
        value = node.get("2")
        return value if isinstance(value, str) else None
    return None


def progression_values(node):
    body = node.get("2", {})
    body = one(body)
    if not isinstance(body, dict):
        return []
    packed = body.get("1000", {})
    packed = one(packed)
    if not isinstance(packed, dict):
        return []
    for field in ("1001", "1002", "1003"):
        values = packed.get(field, {})
        values = one(values)
        if isinstance(values, dict) and "2" in values:
            values = values.get("2", [])
            values = values if isinstance(values, list) else [values]
            out = []
            for value in values:
                if isinstance(value, dict) and "_fixed64_double" in value:
                    out.append(value["_fixed64_double"])
                elif isinstance(value, (int, float, str)):
                    out.append(value)
            return out
    return []


def clean_text(value):
    if not value:
        return ""
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", value).strip()


def client_key(node):
    return key(node.get("1", {})) if isinstance(node, dict) else None


locale = json.load(open(os.path.join(EXTRACTED, "locale_enUS.json"), encoding="utf-8"))
progression_table = dump_file(os.path.join(BASE, "progressionTable_merged.1787687231.pb"))
progression_by_key = {}
for row in progression_table.get("1", []):
    body = row.get("2", {})
    body = one(body)
    row_key = key(body.get("1", {})) if isinstance(body, dict) else None
    if row_key:
        progression_by_key[row_key] = progression_values(row)

commands_table = json.load(open(os.path.join(EXTRACTED, "dragonCommandsTable_merged.1787687230.json"), encoding="utf-8"))
commands_by_key = {client_key(row): row.get("2", {}) for row in commands_table.get("1", []) if client_key(row)}
habits_table = json.load(open(os.path.join(EXTRACTED, "dragonHabitsTable_merged.1787687230.json"), encoding="utf-8"))
habits_by_key = {client_key(row): row.get("2", {}) for row in habits_table.get("1", []) if client_key(row)}

documented = {}
for filename in os.listdir(os.path.join(ROOT, "data", "dragons")):
    if filename.endswith(".json"):
        record = json.load(open(os.path.join(ROOT, "data", "dragons", filename), encoding="utf-8"))
        documented[record["name"]] = record

client_only = {
    "Starshower": {
        "availability": "Shadow of the Greens campaign",
        "missing_for_full_recommendations": ["Most exact numeric values", "Habit upgrade levels", "current screenshot verification"]
    },
    "Vermithor": {
        "availability": "Shadow of the Greens campaign",
        "missing_for_full_recommendations": ["Exact numeric values", "Habit upgrade levels", "current screenshot verification"]
    },
    "Meleys": {
        "availability": "Present in installed-client data; current player availability was not established by this audit.",
        "missing_for_full_recommendations": ["Release and availability confirmation", "Exact numeric values", "Habit upgrade levels", "current screenshot verification"]
    }
}

roster = []
with open(os.path.join(EXTRACTED, "clean_dragons.csv"), newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        row = {name: value.strip() for name, value in row.items()}
        if not re.match(r"^dragon_(generic|iconic)_", row["key"]):
            continue
        if row["name"].startswith("WIP ") or "Work in Progress" in row["habit_slot_6_name"]:
            continue
        if not row["habit_slot_6_name"]:
            continue

        raw = json.load(open(os.path.join(EXTRACTED, "dragonTable_merged.1787687230.json"), encoding="utf-8"))
        break

raw_rows = {client_key(item): item.get("2", {}) for item in raw.get("1", []) if client_key(item)}
with open(os.path.join(EXTRACTED, "clean_dragons.csv"), newline="", encoding="utf-8") as handle:
    source_rows = list(csv.DictReader(handle))

for row in source_rows:
    row = {name: value.strip() for name, value in row.items()}
    if not re.match(r"^dragon_(generic|iconic)_", row["key"]):
        continue
    if row["name"].startswith("WIP ") or "Work in Progress" in row["habit_slot_6_name"] or not row["habit_slot_6_name"]:
        continue
    body = raw_rows[row["key"]]
    stats = {}
    for field, label in (("15", "strength"), ("16", "intelligence"), ("17", "instinct"), ("18", "initiative"), ("19", "max_army_size")):
        prog_key = key(body.get(field, {}))
        values = progression_by_key.get(prog_key, [])
        stats[label] = {"progression_key": prog_key, "values_by_level": values}
    star_scalars = {}
    for field, label in (("24", "strength"), ("25", "intelligence"), ("26", "instinct"), ("27", "initiative"), ("28", "max_army_size")):
        prog_key = key(body.get(field, {}))
        star_scalars[label] = {"progression_key": prog_key, "values_by_star": progression_by_key.get(prog_key, [])}

    command = commands_by_key.get(row["unique_command"], {})
    command_name_key = command.get("2")
    command_detail_key = command.get("11") or command.get("3")
    habit_slots = []
    for index in range(1, 7):
        habit_key = row[f"habit_slot_{index}_key"]
        habit = habits_by_key.get(habit_key, {})
        habit_slots.append({
            "slot": index,
            "client_key": habit_key,
            "name": row[f"habit_slot_{index}_name"],
            "description_template": clean_text(locale.get(habit.get("3"), "")),
            "ability_key": key(habit.get("5", {})),
        })
    status = "screenshot_audited" if row["name"] in documented else "client_discovered"
    entry = {
        "name": row["name"],
        "client_key": row["key"],
        "rarity_key": row["rarity"],
        "breed_key": row["breed"],
        "recommendation_status": status,
        "source_record": f"data/dragons/{row['name'].lower()}.json" if status == "screenshot_audited" else None,
        "level_model": {
            "max_level": body.get("23"),
            "vanguard_unlock_level": 16,
            "base_stats_by_level": stats,
            "star_scalars": star_scalars,
            "interpretation": "Use values_by_level at the player's reported dragon level. Star scaling is separate; do not compare raw base stats across different Star Ranks without applying the displayed star scalar."
        },
        "client_ability_slots": {
            "command": {
                "client_key": row["unique_command"],
                "name": clean_text(locale.get(command_name_key, command_name_key)),
                "description_template": clean_text(locale.get(command_detail_key, "")),
                "ability_key": key(command.get("8", {}))
            },
            "habits_in_slot_order": habit_slots
        },
        "recommendation_evidence": {
            "screenshot_record_is_primary": status == "screenshot_audited",
            "client_templates_require_caution": True,
            "availability": client_only.get(row["name"], {}).get("availability", "Established by screenshot-audited record."),
            "missing_for_full_recommendations": client_only.get(row["name"], {}).get("missing_for_full_recommendations", [])
        }
    }
    roster.append(entry)

out = {
    "metadata": {
        "purpose": "Canonical client-derived roster, level progression, and ability-template index for formation recommendations.",
        "source": "Locally extracted installed application tables under Game_Details/Resources.",
        "client_versions": {"dragon_and_ability": "1787687230", "progression": "1787687231"},
        "scope": "37 production-named client rows; WIP, test, NPC, wild, and balance-test rows are excluded.",
        "evidence_policy": "Screenshot-audited dragon records remain primary for exact current mechanics. Client templates and level curves supplement them; client-only rows must be labeled client-discovered and their missing fields disclosed."
    },
    "recommendation_contract": {
        "required_player_inputs": ["dragon name", "dragon level", "Star Rank", "unlocked Habit levels", "available dragons", "scenario", "enemy troop type or target"],
        "level_rule": "Level affects base Strength, Intelligence, Instinct, Initiative, and Max Army Size through base_stats_by_level. Use the reported level rather than a screenshot's historical stat snapshot.",
        "do_not_infer": ["release status from client presence", "missing numeric ability values", "Habit upgrade levels for client-only rows", "hidden combat ordering or formulas"]
    },
    "dragons": sorted(roster, key=lambda item: item["name"])
}
with open(os.path.join(ROOT, "data", "dragon_application_knowledge.json"), "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=2, ensure_ascii=False)
    handle.write("\n")
print(f"wrote {len(roster)} production-named dragon records")
