#!/usr/bin/env python3
"""Build the compact Game-Data Encyclopedia dataset from canonical repository JSON.

The adapter deliberately reads normalized repository files only. It never reads the
ignored snapshot directory and never interprets anonymous protobuf fields.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT = ROOT / "projects" / "game-data-encyclopedia" / "public" / "data" / "encyclopedia.json"
DEFAULT_BASELINE = ROOT / "projects" / "game-data-encyclopedia" / "public" / "data" / "version-baseline.json"
DEFAULT_CHANGES = ROOT / "projects" / "game-data-encyclopedia" / "public" / "data" / "changes.json"
STAR_GATES = (2, 4, 6, 8, 10)
EFFECT_ID_REGISTRY = {
    name: stable_id for name, stable_id in (
        ("Bleed", "bleed"), ("Panic", "panic"), ("Burn", "burn"),
        ("First-Strike", "first-strike"), ("Double-Strike", "double-strike"),
        ("Recovery", "recovery"), ("Advantage", "advantage"),
        ("Resistance", "resistance"), ("Slow", "slow"),
        ("Weakened", "weakened"), ("Vulnerable", "vulnerable"),
        ("Prey", "prey"), ("Evade", "evade"), ("Cleanse", "cleanse"),
        ("Taunt", "taunt"), ("Stun", "stun"), ("Overwhelm", "overwhelm"),
        ("Stagger", "stagger"), ("Confusion", "confusion"),
        ("Protect", "protect"), ("Solar Flare", "solar-flare"),
        ("Laceration", "laceration"), ("Reflect", "reflect"),
    )
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def effect_id(name: str) -> str:
    """Resolve a display name through the explicit stable effect ID registry."""
    return f"effect:{EFFECT_ID_REGISTRY.get(name, slug(name))}"


def text_blocks(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def humanize(value: str) -> str:
    return value.replace("_", " ").strip().title()


def word_pattern(value: str) -> str:
    parts = [re.escape(part) for part in re.split(r"[\s-]+", value) if part]
    return r"\b" + r"[-\s]+".join(parts) + r"\b"


def classify_effect_relations(text: str, effects: list[dict[str, Any]]) -> list[dict[str, str]]:
    relations: list[dict[str, str]] = []
    lowered = text.lower()
    for effect in effects:
        name = effect["name"]
        pattern = word_pattern(name)
        if not re.search(pattern, text, flags=re.IGNORECASE):
            continue
        kinds: list[str] = []
        if re.search(rf"\b(?:afflict|apply|grant|mark)\b[^.\n]{{0,120}}{pattern}", text, flags=re.IGNORECASE):
            kinds.append("applies")
        if re.search(rf"\b(?:consume|consuming)\b[^.\n]{{0,100}}{pattern}", text, flags=re.IGNORECASE):
            kinds.append("consumes")
        if re.search(rf"\b(?:if|when|while)\b[^.\n]{{0,140}}\b(?:has|have|with|afflicted)\b[^.\n]{{0,80}}{pattern}", text, flags=re.IGNORECASE):
            kinds.append("consumes")
        if re.search(rf"\bimmunity\b[^.\n]{{0,100}}{pattern}", text, flags=re.IGNORECASE):
            kinds.append("counters")
        if name.lower() == "cleanse" or "cleanse" in lowered and name.lower() == "cleanse":
            kinds.append("applies")
        if not kinds:
            kinds.append("mentions")
        for kind in dict.fromkeys(kinds):
            relations.append({"effect_id": effect_id(name), "type": kind})
    return relations


def schedules(text: str) -> list[str]:
    found: list[str] = []
    patterns = (
        r"Start of Combat",
        r"After Combat",
        r"Odd-numbered Rounds",
        r"Even-numbered Rounds",
        r"Each Round",
        r"Start of Each Round",
        r"Start of Round \d+",
        r"Rounds?\s+\d+(?:\s*[-,]\s*\d+)+",
        r"Rounds?\s+\d+",
    )
    for pattern in patterns:
        found.extend(match.group(0) for match in re.finditer(pattern, text, flags=re.IGNORECASE))
    unique = list(dict.fromkeys(found))
    return [item for item in unique if not any(item != other and item.lower() in other.lower() for other in unique)]


def damage_types(text: str) -> list[str]:
    return [name for name in ("Physical Damage", "Tactical Damage", "Fire Damage") if name.lower() in text.lower()]


def target_hints(text: str) -> list[str]:
    hints = []
    for phrase in (
        "same lane", "any lane", "within adjacency", "highest Initiative",
        "lowest Initiative", "highest Strength", "lowest Strength", "least troops",
        "Left Flank", "Right Flank", "Vanguard", "all Enemies", "all Allies",
    ):
        if phrase.lower() in text.lower():
            hints.append(phrase)
    return hints


def schedule_rules(text: str, ability_id: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    patterns = (
        (r"Start of Combat", {"phase": "start_of_combat", "rounds": [0]}),
        (r"After Combat", {"phase": "after_combat", "rounds": [11]}),
        (r"Odd-numbered Rounds", {"phase": "round", "parity": "odd"}),
        (r"Even-numbered Rounds", {"phase": "round", "parity": "even"}),
        (r"Start of Each Round", {"phase": "start_of_round", "recurrence": "each_round"}),
        (r"Each Round", {"phase": "round", "recurrence": "each_round"}),
        (r"Start of Round (?P<single>\d+)", {"phase": "start_of_round"}),
        (r"Rounds?\s+(?P<rounds>\d+(?:\s*,\s*\d+)+)", {"phase": "round"}),
        (r"Rounds?\s+(?P<start>\d+)\s*[-–]\s*(?P<end>\d+)", {"phase": "round"}),
    )
    occupied: list[tuple[int, int]] = []
    for pattern, defaults in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            if any(match.start() >= start and match.end() <= end for start, end in occupied):
                continue
            record: dict[str, Any] = {
                "exact_text": match.group(0),
                "phase": defaults["phase"],
                "rounds": list(defaults.get("rounds", [])),
                "parity": defaults.get("parity"),
                "recurrence": defaults.get("recurrence"),
            }
            if match.groupdict().get("single"):
                record["rounds"] = [int(match.group("single"))]
            elif match.groupdict().get("rounds"):
                record["rounds"] = [int(value) for value in re.findall(r"\d+", match.group("rounds"))]
            elif match.groupdict().get("start"):
                start, end = int(match.group("start")), int(match.group("end"))
                record["rounds"] = list(range(start, end + 1))
            candidates.append(record)
            occupied.append((match.start(), match.end()))
    unique: list[dict[str, Any]] = []
    for item in candidates:
        signature = json.dumps(item, sort_keys=True)
        if not any(json.dumps(existing, sort_keys=True) == signature for existing in unique):
            unique.append(item)
    for index, item in enumerate(unique, start=1):
        item["id"] = f"schedule:{ability_id.split(':', 1)[1]}:{index}"
        item["ability_id"] = ability_id
    return unique


def inline_schedule_rules(text: str, ability_id: str) -> list[dict[str, Any]]:
    """Return schedule facts scoped to one sentence/clause, without graph identity fields."""
    return [
        {key: value for key, value in item.items() if key not in {"id", "ability_id"}}
        for item in schedule_rules(text, ability_id)
    ]


def sentence_context(text: str, start: int, end: int) -> str:
    left = max(text.rfind(".", 0, start), text.rfind("\n", 0, start)) + 1
    right_candidates = [index for index in (text.find(".", end), text.find("\n", end)) if index >= 0]
    right = min(right_candidates) + 1 if right_candidates else len(text)
    return text[left:right].strip()


def damage_event_rules(text: str, ability_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for match in re.finditer(r"[^.\n]+(?:[.\n]|$)", text):
        context = match.group(0).strip()
        for damage_type in damage_types(context):
            events.append({
                "damage_type": damage_type,
                "exact_context": context,
                "schedules": inline_schedule_rules(context, ability_id),
                "target_hints": target_hints(context),
            })
    return events


def condition_rules(text: str, ability_id: str, effects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    # A status is a prerequisite only when it appears in the antecedent of the
    # condition. Stopping at the first clause delimiter prevents text such as
    # "If you have a Prey, ... apply Recovery" from treating Recovery as an
    # input to the ability rather than its result.
    for conditional in re.finditer(r"\b(?:if|when|while|against)\b", text, flags=re.IGNORECASE):
        clause_end = len(text)
        for delimiter in (",", ";", ":", ".", "\n"):
            position = text.find(delimiter, conditional.end())
            if position >= 0:
                clause_end = min(clause_end, position)
        clause_end = min(clause_end, conditional.start() + 180)
        phrase = text[conditional.start():clause_end].strip()
        if re.search(r"\bsuccessful(?:ly)?\s+removes?\b", phrase, re.IGNORECASE):
            continue
        for effect in effects:
            if not re.search(word_pattern(effect["name"]), phrase, flags=re.IGNORECASE):
                continue
            if re.search(r"\b(?:enem(?:y|ies)|prey)\b", phrase, re.IGNORECASE):
                subject = "enemy"
            elif re.search(r"\ball(?:y|ies)\b", phrase, re.IGNORECASE):
                subject = "ally"
            elif re.search(r"\btarget\b", phrase, re.IGNORECASE) and re.search(r"\bPrey\b", text, re.IGNORECASE):
                subject = "enemy"
            elif re.search(r"\b(?:you|yourself)\b", phrase, re.IGNORECASE):
                subject = "self"
            else:
                subject = "target"
            records.append({
                "type": "status_present",
                "subject": subject,
                "operator": "present",
                "status_id": effect_id(effect["name"]),
                "value": None,
                "exact_text": phrase,
            })
    for match in re.finditer(
        r"\b(?:if\s+)?(?:you\s+are\s+)?(?P<operator>below|above|at or below|at or above)\s+(?P<value>\d+)%\s+Max Troop Capacity",
        text,
        flags=re.IGNORECASE,
    ):
        records.append({
            "type": "troop_capacity_threshold",
            "subject": "self",
            "operator": match.group("operator").lower().replace(" ", "_"),
            "status_id": None,
            "value": int(match.group("value")),
            "exact_text": match.group(0),
        })
    for match in re.finditer(r"\bAt\s+(?P<stars>\d+)\+?\s+Stars\b", text, flags=re.IGNORECASE):
        records.append({
            "type": "star_rank",
            "subject": "self",
            "operator": "at_least",
            "status_id": None,
            "value": int(match.group("stars")),
            "exact_text": match.group(0),
        })
    unique: list[dict[str, Any]] = []
    for item in records:
        signature = json.dumps(item, sort_keys=True)
        if not any(json.dumps(existing, sort_keys=True) == signature for existing in unique):
            unique.append(item)
    for index, item in enumerate(unique, start=1):
        item["id"] = f"condition:{ability_id.split(':', 1)[1]}:{index}"
        item["ability_id"] = ability_id
        item["evidence_class"] = "derived"
    return unique


def targeter_rules(text: str, ability_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    scope_patterns = {
        "any_lane": r"any lane",
        "same_lane": r"same lane",
        "adjacency": r"within adjacency",
        "left_flank": r"Left Flank",
        "right_flank": r"Right Flank",
        "vanguard": r"Vanguard",
    }
    for scope, pattern in scope_patterns.items():
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            window = text[max(0, match.start() - 90):match.end()]
            count_match = re.search(r"\b(?P<count>\d+|one|two|three|all)\s+(?P<side>Enemy|Enemies|Ally|Allies|combatants?)\b", window, re.IGNORECASE)
            count: int | str | None = None
            side = "unknown"
            if count_match:
                raw_count = count_match.group("count").lower()
                count = {"one": 1, "two": 2, "three": 3}.get(raw_count, raw_count)
                if isinstance(count, str) and count.isdigit():
                    count = int(count)
                side = "enemy" if count_match.group("side").lower().startswith("enem") else "ally"
            records.append({
                "scope": scope,
                "side": side,
                "count": count,
                "exact_text": match.group(0),
            })
    if re.search(r"\b(?:yourself|your|self)\b", text, re.IGNORECASE):
        records.append({"scope": "self", "side": "self", "count": 1, "exact_text": "self"})
    unique: list[dict[str, Any]] = []
    for item in records:
        signature = json.dumps(item, sort_keys=True)
        if not any(json.dumps(existing, sort_keys=True) == signature for existing in unique):
            unique.append(item)
    for index, item in enumerate(unique, start=1):
        item["id"] = f"targeter:{ability_id.split(':', 1)[1]}:{index}"
        item["ability_id"] = ability_id
        item["evidence_class"] = "derived"
    return unique


def prioritizer_rules(text: str, ability_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for match in re.finditer(
        r"\b(?P<direction>highest|lowest|least)\s+(?P<field>Initiative|Strength|Instinct|Intelligence|troops|Max Troop Capacity)\b",
        text,
        flags=re.IGNORECASE,
    ):
        direction = match.group("direction").lower()
        records.append({
            "priority_type": "stat" if "troop" not in match.group("field").lower() else "troop_count",
            "field": match.group("field"),
            "direction": "lowest" if direction == "least" else direction,
            "exact_text": match.group(0),
        })
    for match in re.finditer(r"\bprioritiz(?:es|ing)\s+(?:the\s+)?(?P<value>Left Flank|Right Flank|Vanguard|Warriors?|Hunters?|Sentinels?|Champions?)\b", text, flags=re.IGNORECASE):
        value = match.group("value")
        records.append({
            "priority_type": "lane" if "Flank" in value or value.lower() == "vanguard" else "breed",
            "field": value,
            "direction": "preferred",
            "exact_text": match.group(0),
        })
    for index, item in enumerate(records, start=1):
        item["id"] = f"prioritizer:{ability_id.split(':', 1)[1]}:{index}"
        item["ability_id"] = ability_id
        item["evidence_class"] = "derived"
    return records


def status_operations(text: str, ability_id: str, effects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relation in classify_effect_relations(text, effects):
        effect_name = next(item["name"] for item in effects if effect_id(item["name"]) == relation["effect_id"])
        pattern = word_pattern(effect_name)
        match = re.search(pattern, text, flags=re.IGNORECASE)
        context = sentence_context(text, match.start(), match.end()) if match else text
        chance = re.search(r"(?P<chance>\d+(?:\.\d+)?)%\s+chance", context, flags=re.IGNORECASE)
        duration = re.search(r"for\s+(?P<rounds>\d+)\s+round", context, flags=re.IGNORECASE)
        stacks = re.search(r"Max\s+(?P<stacks>\d+)\s+stacks", context, flags=re.IGNORECASE)
        records.append({
            "effect_id": relation["effect_id"],
            "operation": relation["type"],
            "chance_percent": float(chance.group("chance")) if chance else None,
            "duration_rounds": int(duration.group("rounds")) if duration else None,
            "max_stacks": int(stacks.group("stacks")) if stacks else None,
            "exact_context": context.strip(),
            "schedules": inline_schedule_rules(context, ability_id),
        })
    for index, item in enumerate(records, start=1):
        item["id"] = f"status-operation:{ability_id.split(':', 1)[1]}:{index}"
        item["ability_id"] = ability_id
        item["evidence_class"] = "derived"
    return records


def cleanse_scope_matches(effect: dict[str, Any], text: str) -> bool:
    """Match broad Cleanse wording without discarding an explicit category qualifier."""
    lowered = text.lower()
    behavior = str(effect.get("behavior") or effect.get("exact_text") or "").lower()
    if effect["effect_on_target"] == "harmful" and "negative effect" in lowered:
        if re.search(r"negative effect[^.]{0,100}increases?[^.]{0,60}damage received", lowered):
            return "increases damage received" in behavior
        if re.search(r"negative effect[^.]{0,100}reduces?[^.]{0,60}damage dealt", lowered):
            return "reduces damage dealt" in behavior
        return True
    if effect["effect_on_target"] == "beneficial" and "positive effect" in lowered:
        if re.search(r"positive effect[^.]{0,100}increases?[^.]{0,60}damage dealt", lowered):
            return "increases damage dealt" in behavior
        if re.search(r"positive effect[^.]{0,100}reduces?[^.]{0,60}damage received", lowered):
            return "reduces damage received" in behavior
        return True
    return False


def source_entry(path: Path) -> dict[str, str]:
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": file_hash(path)}


def make_ability(
    *,
    dragon_id: str,
    client_key: str,
    name: str,
    kind: str,
    exact_text: Any,
    source: str,
    evidence_class: str,
    source_version: str,
    effects: list[dict[str, Any]],
    unlock: dict[str, int] | None = None,
    ability_type: str | None = None,
    upgrade_levels: dict[str, Any] | None = None,
    value_unit: str | None = None,
    uncertainty: list[str] | None = None,
) -> dict[str, Any]:
    blocks = text_blocks(exact_text)
    joined = " ".join(blocks)
    ability_id = f"ability:{dragon_id.split(':', 1)[1]}:{client_key}"
    structured_schedules = schedule_rules(joined, ability_id)
    structured_conditions = condition_rules(joined, ability_id, effects)
    structured_targeters = targeter_rules(joined, ability_id)
    structured_prioritizers = prioritizer_rules(joined, ability_id)
    structured_operations = status_operations(joined, ability_id, effects)
    return {
        "id": ability_id,
        "client_key": client_key,
        "name": name,
        "kind": kind,
        "ability_type": ability_type,
        "unlock": unlock or {},
        "upgrade_levels": upgrade_levels or {},
        "value_unit": value_unit,
        "exact_text": blocks,
        "normalized": {
            "damage_types": damage_types(joined),
            "damage_events": damage_event_rules(joined, ability_id),
            "schedules": schedules(joined),
            "target_hints": target_hints(joined),
            "effect_relations": classify_effect_relations(joined, effects),
            "schedule_refs": [item["id"] for item in structured_schedules],
            "condition_refs": [item["id"] for item in structured_conditions],
            "targeter_refs": [item["id"] for item in structured_targeters],
            "prioritizer_refs": [item["id"] for item in structured_prioritizers],
            "status_operation_refs": [item["id"] for item in structured_operations],
        },
        "graph_records": {
            "schedules": structured_schedules,
            "conditions": structured_conditions,
            "targeters": structured_targeters,
            "prioritizers": structured_prioritizers,
            "status_operations": structured_operations,
        },
        "evidence": {
            "class": evidence_class,
            "confidence": "confirmed" if evidence_class == "screenshot_confirmed" else "limited",
            "source": source,
            "source_version": source_version,
            "uncertainty": uncertainty or [],
        },
    }


def build_data(root: Path = ROOT) -> dict[str, Any]:
    effects_path = root / "data" / "effects.json"
    mechanics_path = root / "data" / "game_mechanics.json"
    app_path = root / "data" / "dragon_application_knowledge.json"
    map_nodes_path = root / "Game_Details" / "Resources" / "_extracted" / "clean_map_nodes.csv"
    map_regions_path = root / "Game_Details" / "Resources" / "_extracted" / "node_place_names.json"
    crossing_chains_path = root / "Game_Details" / "Resources" / "_extracted" / "crossing_chains.json"
    effects_source = read_json(effects_path)["effects"]
    mechanics = read_json(mechanics_path)
    app = read_json(app_path)
    app_by_name = {dragon["name"]: dragon for dragon in app["dragons"]}
    client_version = "/".join(app["metadata"]["client_versions"].values())

    with map_nodes_path.open("r", encoding="utf-8", newline="") as handle:
        map_rows = list(csv.DictReader(handle))
    map_regions = read_json(map_regions_path)
    crossing_edges = read_json(crossing_chains_path)
    if len(map_rows) != len(map_regions):
        raise ValueError("map node and containing-region records are not aligned")
    crossing_neighbors: dict[int, list[int]] = {}
    for left, right in crossing_edges:
        crossing_neighbors.setdefault(left, []).append(right)
        crossing_neighbors.setdefault(right, []).append(left)
    map_nodes = []
    for index, (row, region_name) in enumerate(zip(map_rows, map_regions)):
        stable_id = f"map-node:{index:06d}"
        own_name = row["place_name"].strip()
        display_name = own_name or region_name or row["type_name"]
        map_nodes.append({
            "id": stable_id,
            "slug": stable_id.split(":", 1)[1],
            "name": display_name,
            "entity_type": "map_node",
            "type": row["type_name"],
            "type_code": row["type_code"],
            "coordinates": {"x": int(row["x"]), "y": int(row["y"])},
            "footprint": {"width": int(row["bbox_w"] or 1), "height": int(row["bbox_h"] or 1)},
            "region": region_name,
            "has_own_name": bool(own_name),
            "level": int(row["level"]) if row["level"] else None,
            "variant": row["variant"],
            "instance_id": row["instance_id"],
            "template_key": row["template_key"],
            "crossing_connections": [f"map-node:{neighbor:06d}" for neighbor in sorted(crossing_neighbors.get(index, []))],
            "evidence": {
                "class": "observed",
                "confidence": "confirmed",
                "source": "Game_Details/Resources/_extracted/clean_map_nodes.csv",
                "source_version": client_version,
                "uncertainty": (["Crossing connections are derived from spatial proximity; the client data has no explicit adjacency field."]
                                if index in crossing_neighbors else []),
            },
        })

    effect_entities: list[dict[str, Any]] = []
    for item in effects_source:
        stable_effect_id = effect_id(item["name"])
        is_staged = item["name"] in {"Laceration", "Reflect"}
        source = item.get("source", "data/effects.json")
        evidence_class = "client_confirmed" if source.startswith("Game_Details/") else "screenshot_confirmed"
        if source.startswith("http"):
            evidence_class = "client_confirmed"
        effect_entities.append({
            "id": stable_effect_id,
            "slug": stable_effect_id.split(":", 1)[1],
            "name": item["name"],
            "entity_type": "status",
            "game_section": item["game_section"],
            "effect_on_target": item["effect_on_target"],
            "exact_text": item["behavior"],
            "scope_note": item.get("scope_note"),
            "review_required": item.get("review_required", False),
            "lifecycle": "staged" if is_staged else "live",
            "evidence": {
                "class": "staged" if is_staged else evidence_class,
                "confidence": "limited" if item.get("review_required") or is_staged else "confirmed",
                "source": source,
                "source_version": item.get("source_checked", client_version),
                "uncertainty": [item["scope_note"]] if item.get("scope_note") else [],
            },
            "relationships": {"sources": [], "consumers": [], "counters": [], "cleanses": [], "mentions": []},
        })
    effect_by_id = {item["id"]: item for item in effect_entities}

    dragons: list[dict[str, Any]] = []
    relationships: list[dict[str, str]] = []
    dragon_files = sorted((root / "data" / "dragons").glob("*.json"))
    audited_by_name = {read_json(path)["name"]: (path, read_json(path)) for path in dragon_files}

    for client in app["dragons"]:
        name = client["name"]
        dragon_id = f"dragon:{client['client_key']}"
        audited = audited_by_name.get(name)
        abilities: list[dict[str, Any]] = []
        if audited:
            path, record = audited
            relative_source = path.relative_to(root).as_posix()
            slots = client["client_ability_slots"]["habits_in_slot_order"]
            command_client = client["client_ability_slots"]["command"]
            abilities.append(make_ability(
                dragon_id=dragon_id,
                client_key=command_client["client_key"],
                name=record["command"]["name"],
                kind="command",
                ability_type=record["command"].get("type"),
                exact_text=record["command"]["verbatim"],
                source=relative_source,
                evidence_class="screenshot_confirmed",
                source_version=client_version,
                effects=effects_source,
            ))
            abilities.append(make_ability(
                dragon_id=dragon_id,
                client_key=slots[0]["client_key"],
                name=record["vanguard"]["name"],
                kind="vanguard",
                unlock={"level": int(record["vanguard"].get("unlock_level", 16))},
                exact_text=record["vanguard"]["verbatim"],
                source=relative_source,
                evidence_class="screenshot_confirmed",
                source_version=client_version,
                effects=effects_source,
            ))
            for index, habit in enumerate(record["habits"]):
                slot = slots[index + 1]
                abilities.append(make_ability(
                    dragon_id=dragon_id,
                    client_key=slot["client_key"],
                    name=habit["name"],
                    kind="habit",
                    unlock={"star_rank": int(habit["star_unlock"])},
                    upgrade_levels=habit.get("upgrade_levels"),
                    value_unit=habit.get("value_unit"),
                    exact_text=habit["verbatim"],
                    source=relative_source,
                    evidence_class="screenshot_confirmed",
                    source_version=client_version,
                    effects=effects_source,
                ))
            breed = record["breed"]
            rarity_label = record.get("rarity_label")
            rarity_tier = record.get("rarity_tier")
            affinities = record.get("troop_affinities", {"positive": [], "negative": []})
            traits = [humanize(role) for role in record.get("derived", {}).get("roles", [])]
            lifecycle = "live"
            evidence_class = "screenshot_confirmed"
            confidence = "confirmed"
            uncertainty = list(record.get("review", []))
            source = relative_source
        else:
            slots = client["client_ability_slots"]["habits_in_slot_order"]
            missing = list(client["recommendation_evidence"]["missing_for_full_recommendations"])
            command = client["client_ability_slots"]["command"]
            abilities.append(make_ability(
                dragon_id=dragon_id,
                client_key=command["client_key"],
                name=command["name"],
                kind="command",
                exact_text=command["description_template"],
                source="data/dragon_application_knowledge.json",
                evidence_class="client_confirmed",
                source_version=client_version,
                effects=effects_source,
                uncertainty=missing,
            ))
            for index, slot in enumerate(slots):
                abilities.append(make_ability(
                    dragon_id=dragon_id,
                    client_key=slot["client_key"],
                    name=slot["name"],
                    kind="vanguard" if index == 0 else "habit",
                    unlock={"level": 16} if index == 0 else {"star_rank": STAR_GATES[index - 1]},
                    exact_text=slot["description_template"],
                    source="data/dragon_application_knowledge.json",
                    evidence_class="client_confirmed",
                    source_version=client_version,
                    effects=effects_source,
                    uncertainty=missing,
                ))
            breed = humanize(client["breed_key"].removeprefix("breed_"))
            rarity_label = None
            rarity_tier = humanize(client["rarity_key"].removeprefix("rarity_dragon_"))
            affinities = {"positive": [], "negative": [], "unknown": True}
            traits = []
            lifecycle = "staged" if "not established" in client["recommendation_evidence"]["availability"].lower() else "live"
            evidence_class = "staged" if lifecycle == "staged" else "client_confirmed"
            confidence = "limited"
            uncertainty = missing
            source = "data/dragon_application_knowledge.json"

        dragon = {
            "id": dragon_id,
            "slug": client["client_key"],
            "name": name,
            "entity_type": "dragon",
            "breed": breed,
            "rarity_label": rarity_label,
            "rarity_tier": rarity_tier,
            "troop_affinities": affinities,
            "traits": traits,
            "lifecycle": lifecycle,
            "abilities": abilities,
            "evidence": {
                "class": evidence_class,
                "confidence": confidence,
                "source": source,
                "source_version": client_version,
                "uncertainty": uncertainty,
            },
        }
        dragons.append(dragon)

        for ability in abilities:
            for relation in ability["normalized"]["effect_relations"]:
                edge = {
                    "from": ability["id"],
                    "to": relation["effect_id"],
                    "type": relation["type"],
                    "dragon_id": dragon_id,
                }
                relationships.append(edge)

    ability_lookup = {
        ability["id"]: (dragon, ability)
        for dragon in dragons
        for ability in dragon["abilities"]
    }
    for edge in relationships:
        effect = effect_by_id[edge["to"]]
        dragon, ability = ability_lookup[edge["from"]]
        ref = {
            "dragon_id": dragon["id"],
            "dragon_name": dragon["name"],
            "ability_id": ability["id"],
            "ability_name": ability["name"],
            "ability_kind": ability["kind"],
            "relationship": edge["type"],
            "lifecycle": dragon["lifecycle"],
        }
        bucket = {
            "applies": "sources",
            "consumes": "consumers",
            "counters": "counters",
            "mentions": "mentions",
        }[edge["type"]]
        effect["relationships"][bucket].append(ref)

    cleanse_abilities = []
    for dragon in dragons:
        for ability in dragon["abilities"]:
            joined = " ".join(ability["exact_text"])
            if re.search(r"\bcleanse", joined, flags=re.IGNORECASE):
                cleanse_abilities.append((dragon, ability, joined))
    for effect in effect_entities:
        if effect["name"] == "Cleanse":
            continue
        for dragon, ability, text in cleanse_abilities:
            scope_matches = cleanse_scope_matches(effect, text)
            if scope_matches:
                effect["relationships"]["cleanses"].append({
                    "dragon_id": dragon["id"],
                    "dragon_name": dragon["name"],
                    "ability_id": ability["id"],
                    "ability_name": ability["name"],
                    "ability_kind": ability["kind"],
                    "relationship": "may_cleanse_by_category",
                    "lifecycle": dragon["lifecycle"],
                })

    graph = {"schedules": [], "conditions": [], "targeters": [], "prioritizers": [], "status_operations": []}
    for dragon in dragons:
        for ability in dragon["abilities"]:
            records = ability.pop("graph_records")
            for graph_type in graph:
                graph[graph_type].extend(records[graph_type])

    source_paths = [effects_path, mechanics_path, app_path, map_nodes_path, map_regions_path, crossing_chains_path, *dragon_files]
    return {
        "metadata": {
            "schema_version": "1.3.0",
            "dataset_id": "dragonfire-encyclopedia-combat-v1",
            "source_snapshot": "installed-client-local-copy",
            "client_versions": app["metadata"]["client_versions"],
            "last_web_audit": mechanics["metadata"]["last_web_audit"],
            "default_visibility": "live",
            "source_manifest": [source_entry(path) for path in source_paths],
        },
        "facets": {
            "breeds": sorted(mechanics["breeds"].keys()),
            "rarities": ["Rare", "Epic", "Legendary"],
            "troop_affinities": sorted(mechanics["troop_types"].keys()),
            "evidence_classes": ["screenshot_confirmed", "client_confirmed", "observed", "derived", "staged", "unknown"],
            "star_gates": list(STAR_GATES),
            "habit_levels": mechanics["progression"]["habit_upgrades"]["levels"],
            "map_regions": sorted({node["region"] for node in map_nodes if node["region"]}),
            "map_types": sorted({node["type"] for node in map_nodes}),
            "map_levels": sorted({node["level"] for node in map_nodes if node["level"] is not None}),
        },
        "mechanics": {
            "breeds": mechanics["breeds"],
            "damage_types": mechanics["damage_types"],
            "troop_types": mechanics["troop_types"],
            "star_display": mechanics["progression"]["star_display"],
            "habit_upgrades": mechanics["progression"]["habit_upgrades"],
            "unresolved_public_rules": mechanics["unresolved_public_rules"],
        },
        "dragons": dragons,
        "effects": effect_entities,
        "map_nodes": map_nodes,
        "relationships": relationships,
        "graph": graph,
    }


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ids: list[str] = []
    ids.extend(item["id"] for item in data["dragons"])
    ids.extend(item["id"] for item in data["effects"])
    ids.extend(item["id"] for item in data["map_nodes"])
    ids.extend(ability["id"] for dragon in data["dragons"] for ability in dragon["abilities"])
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    errors.extend(f"duplicate stable id: {item}" for item in duplicates)
    known_effects = {item["id"] for item in data["effects"]}
    known_dragons = {item["id"] for item in data["dragons"]}
    known_abilities = {ability["id"] for dragon in data["dragons"] for ability in dragon["abilities"]}
    known_map_nodes = {item["id"] for item in data["map_nodes"]}
    for node in data["map_nodes"]:
        x, y = node["coordinates"]["x"], node["coordinates"]["y"]
        if not (0 <= x <= 2080 and 0 <= y <= 3312):
            errors.append(f"map node coordinates out of bounds: {node['id']}")
        for target in node["crossing_connections"]:
            if target not in known_map_nodes:
                errors.append(f"unknown crossing connection: {node['id']} -> {target}")
    graph_ids = {graph_type: {item["id"] for item in records} for graph_type, records in data["graph"].items()}
    for graph_type, records in data["graph"].items():
        if len(graph_ids[graph_type]) != len(records):
            errors.append(f"duplicate graph id in {graph_type}")
        for record in records:
            if record["ability_id"] not in known_abilities:
                errors.append(f"unknown graph ability in {graph_type}: {record['ability_id']}")
            if record.get("status_id") and record["status_id"] not in known_effects:
                errors.append(f"unknown graph status in {graph_type}: {record['status_id']}")
            if record.get("effect_id") and record["effect_id"] not in known_effects:
                errors.append(f"unknown graph effect in {graph_type}: {record['effect_id']}")
    reference_map = {
        "schedule_refs": "schedules",
        "condition_refs": "conditions",
        "targeter_refs": "targeters",
        "prioritizer_refs": "prioritizers",
        "status_operation_refs": "status_operations",
    }
    for dragon in data["dragons"]:
        for ability in dragon["abilities"]:
            for field, graph_type in reference_map.items():
                for reference in ability["normalized"][field]:
                    if reference not in graph_ids[graph_type]:
                        errors.append(f"unknown {graph_type} reference: {reference}")
    for edge in data["relationships"]:
        if edge["to"] not in known_effects:
            errors.append(f"unknown relationship target: {edge['to']}")
        if edge["from"] not in known_abilities:
            errors.append(f"unknown relationship source: {edge['from']}")
        if edge["dragon_id"] not in known_dragons:
            errors.append(f"unknown relationship dragon: {edge['dragon_id']}")
    return errors


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def version_entities(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entities: dict[str, dict[str, Any]] = {}
    for dragon in data["dragons"]:
        payload = {
            "name": dragon["name"],
            "breed": dragon["breed"],
            "rarity_label": dragon["rarity_label"],
            "rarity_tier": dragon["rarity_tier"],
            "troop_affinities": dragon["troop_affinities"],
            "traits": dragon["traits"],
            "lifecycle": dragon["lifecycle"],
            "evidence": dragon["evidence"],
        }
        entities[dragon["id"]] = {
            "id": dragon["id"], "entity_type": "dragon", "name": dragon["name"],
            "parent_id": None, "fingerprint": canonical_hash(payload), "payload": payload,
        }
        for ability in dragon["abilities"]:
            ability_payload = {
                "name": ability["name"], "kind": ability["kind"], "ability_type": ability["ability_type"],
                "unlock": ability["unlock"], "exact_text": ability["exact_text"],
                "normalized": ability["normalized"], "evidence": ability["evidence"],
            }
            graph_records = {
                graph_type: [item for item in records if item["ability_id"] == ability["id"]]
                for graph_type, records in data["graph"].items()
            }
            ability_payload["graph"] = graph_records
            entities[ability["id"]] = {
                "id": ability["id"], "entity_type": "ability", "name": ability["name"],
                "parent_id": dragon["id"], "fingerprint": canonical_hash(ability_payload), "payload": ability_payload,
            }
    for effect in data["effects"]:
        payload = {
            "name": effect["name"], "game_section": effect["game_section"],
            "effect_on_target": effect["effect_on_target"], "exact_text": effect["exact_text"],
            "scope_note": effect["scope_note"], "review_required": effect["review_required"],
            "lifecycle": effect["lifecycle"], "evidence": effect["evidence"],
        }
        entities[effect["id"]] = {
            "id": effect["id"], "entity_type": "status", "name": effect["name"],
            "parent_id": None, "fingerprint": canonical_hash(payload), "payload": payload,
        }
    for node in data["map_nodes"]:
        payload = {
            "name": node["name"], "type": node["type"], "coordinates": node["coordinates"],
            "footprint": node["footprint"], "region": node["region"], "has_own_name": node["has_own_name"],
            "level": node["level"], "variant": node["variant"], "instance_id": node["instance_id"],
            "template_key": node["template_key"], "crossing_connections": node["crossing_connections"],
            "evidence": node["evidence"],
        }
        entities[node["id"]] = {
            "id": node["id"], "entity_type": "map_node", "name": node["name"],
            "parent_id": None, "fingerprint": canonical_hash(payload), "payload": payload,
        }
    return entities


def make_version_baseline(data: dict[str, Any]) -> dict[str, Any]:
    entities = version_entities(data)
    compact_entities = {
        entity_id: {
            "id": item["id"],
            "entity_type": item["entity_type"],
            "name": item["name"],
            "parent_id": item["parent_id"],
            "fingerprint": item["fingerprint"],
            "field_fingerprints": {key: canonical_hash(value) for key, value in item["payload"].items()},
        }
        for entity_id, item in entities.items()
    }
    inventory = {
        "dragons": len(data["dragons"]),
        "abilities": sum(len(dragon["abilities"]) for dragon in data["dragons"]),
        "statuses": len(data["effects"]),
        "map_nodes": len(data["map_nodes"]),
        **{graph_type: len(records) for graph_type, records in data["graph"].items()},
    }
    return {
        "schema_version": "1.0.0",
        "label": "Initial indexed combat release",
        "dataset_schema_version": data["metadata"]["schema_version"],
        "dataset_id": data["metadata"]["dataset_id"],
        "client_versions": data["metadata"]["client_versions"],
        "inventory": inventory,
        "sources": data["metadata"]["source_manifest"],
        "entities": compact_entities,
    }


def semantic_changes(data: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    current_entities = version_entities(data)
    baseline_entities = baseline.get("entities", {})
    changes: list[dict[str, Any]] = []
    for entity_id in sorted(set(current_entities) | set(baseline_entities)):
        current = current_entities.get(entity_id)
        previous = baseline_entities.get(entity_id)
        if previous is None:
            changes.append({
                "entity_id": entity_id, "entity_type": current["entity_type"], "name": current["name"],
                "parent_id": current["parent_id"], "change_type": "added", "changed_fields": [],
            })
        elif current is None:
            changes.append({
                "entity_id": entity_id, "entity_type": previous["entity_type"], "name": previous["name"],
                "parent_id": previous["parent_id"], "change_type": "removed", "changed_fields": [],
            })
        elif current["fingerprint"] != previous["fingerprint"]:
            current_fields = {key: canonical_hash(value) for key, value in current["payload"].items()}
            previous_fields = previous.get("field_fingerprints") or {
                key: canonical_hash(value) for key, value in previous.get("payload", {}).items()
            }
            fields = sorted(key for key in set(current_fields) | set(previous_fields) if current_fields.get(key) != previous_fields.get(key))
            changes.append({
                "entity_id": entity_id, "entity_type": current["entity_type"], "name": current["name"],
                "parent_id": current["parent_id"], "change_type": "changed", "changed_fields": fields,
            })
    baseline_sources = {item["path"]: item["sha256"] for item in baseline.get("sources", [])}
    current_sources = {item["path"]: item["sha256"] for item in data["metadata"]["source_manifest"]}
    source_changes = [
        {"path": path, "change_type": "added" if path not in baseline_sources else "removed" if path not in current_sources else "changed"}
        for path in sorted(set(baseline_sources) | set(current_sources))
        if baseline_sources.get(path) != current_sources.get(path)
    ]
    summary = {
        "added": sum(item["change_type"] == "added" for item in changes),
        "changed": sum(item["change_type"] == "changed" for item in changes),
        "removed": sum(item["change_type"] == "removed" for item in changes),
        "source_files_changed": len(source_changes),
    }
    return {
        "schema_version": "1.0.0",
        "baseline": {
            "label": baseline.get("label", "Previous validated release"),
            "dataset_schema_version": baseline.get("dataset_schema_version"),
            "client_versions": baseline.get("client_versions", {}),
            "inventory": baseline.get("inventory", {}),
        },
        "current": {
            "label": "Current generated release",
            "dataset_schema_version": data["metadata"]["schema_version"],
            "client_versions": data["metadata"]["client_versions"],
            "inventory": make_version_baseline(data)["inventory"],
        },
        "comparison_state": "unchanged" if not changes and not source_changes else "changes_detected",
        "summary": summary,
        "changes": changes,
        "source_changes": source_changes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--baseline-manifest", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--changes-output", type=Path, default=DEFAULT_CHANGES)
    parser.add_argument("--update-baseline", action="store_true", help="replace the validated comparison baseline")
    parser.add_argument("--check", action="store_true", help="validate without writing output")
    args = parser.parse_args()
    data = build_data(ROOT)
    errors = validate(data)
    if errors:
        raise SystemExit("\n".join(errors))
    if not args.check:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        current_baseline = make_version_baseline(data)
        if args.update_baseline or not args.baseline_manifest.exists():
            args.baseline_manifest.parent.mkdir(parents=True, exist_ok=True)
            args.baseline_manifest.write_text(json.dumps(current_baseline, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        baseline = read_json(args.baseline_manifest)
        changes = semantic_changes(data, baseline)
        args.changes_output.parent.mkdir(parents=True, exist_ok=True)
        args.changes_output.write_text(json.dumps(changes, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        print(
            f"wrote {args.output} ({len(data['dragons'])} dragons, {len(data['effects'])} effects, "
            f"{sum(len(items) for items in data['graph'].values())} graph records)"
        )
    else:
        print(f"valid ({len(data['dragons'])} dragons, {len(data['effects'])} effects)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
