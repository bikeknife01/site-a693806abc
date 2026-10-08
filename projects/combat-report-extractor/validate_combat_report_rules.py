#!/usr/bin/env python3
"""Validate Combat Analyst schemas, canonical rules, and curated observations."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_SCHEMA_MAJOR = 1
INFERRED_RELATIONSHIPS = {
    "emitted_effect", "unnamed_result", "inferred_exclusive_mapping",
    "timing_correlation", "unresolved",
}
CAUSAL_WORDS = re.compile(r"\b(causes?|triggers?|comes? from|produces?)\b", re.I)
WINDOWS_ABSOLUTE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")
ACCOUNT_KEYS = {"account", "account_id", "account_name", "player", "player_id", "player_name"}


def repository_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }[expected]


def validate_schema(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Validate the JSON Schema features used by this repository's three contracts."""
    errors: list[str] = []
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: invalid enum value {instance!r}")
    expected = schema.get("type")
    if expected is not None:
        choices = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(instance, choice) for choice in choices):
            errors.append(f"{path}: expected type {' or '.join(choices)}")
            return errors
    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in sorted(set(instance) - set(properties)):
                errors.append(f"{path}.{key}: additional property is not allowed")
        for key in sorted(set(instance) & set(properties)):
            errors.extend(validate_schema(instance[key], properties[key], f"{path}.{key}"))
    elif isinstance(instance, list):
        if schema.get("uniqueItems"):
            seen: set[str] = set()
            for index, item in enumerate(instance):
                marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
                if marker in seen:
                    errors.append(f"{path}[{index}]: duplicate array item")
                seen.add(marker)
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path}: requires at least {schema['minItems']} item(s)")
        if "items" in schema:
            for index, item in enumerate(instance):
                errors.extend(validate_schema(item, schema["items"], f"{path}[{index}]"))
    elif isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: string is shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: value does not match {schema['pattern']!r}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: value is below minimum {schema['minimum']}")
    return errors


def load_canonical_vocabulary(repository_root: Path) -> dict[str, set[str]]:
    vocabulary: dict[str, set[str]] = {}
    for path in sorted((repository_root / "data" / "dragons").glob("*.json")):
        data = load_json(path)
        name = data.get("name")
        if not isinstance(name, str):
            continue
        abilities = {"Basic Attack"}
        for key in ("command", "vanguard"):
            ability = (data.get(key) or {}).get("name")
            if isinstance(ability, str):
                abilities.add(ability)
        abilities.update(
            habit["name"] for habit in data.get("habits", [])
            if isinstance(habit.get("name"), str)
        )
        vocabulary[name] = abilities
    return vocabulary


def _duplicates(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        (duplicates if value in seen else seen).add(value)
    return sorted(duplicates)


def _unsafe_observation_values(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in ACCOUNT_KEYS:
                errors.append(f"{path}.{key}: account identifier fields are not permitted")
            errors.extend(_unsafe_observation_values(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_unsafe_observation_values(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        if WINDOWS_ABSOLUTE.match(value) or value.startswith("/"):
            errors.append(f"{path}: absolute local path is not permitted")
        if re.search(r"\b(?:account|player)[ _-]?id\s*[:=]", value, re.I):
            errors.append(f"{path}: account identifier text is not permitted")
    return errors


def validate_stores(
    rules: dict[str, Any], observations: dict[str, Any], repository_root: Path,
    schema_root: Path | None = None,
) -> list[str]:
    schema_root = schema_root or repository_root / "projects" / "combat-report-extractor" / "schemas"
    errors = [
        f"rules {message}" for message in validate_schema(
            rules, load_json(schema_root / "combat-report-rules.schema.json")
        )
    ]
    errors.extend(
        f"observations {message}" for message in validate_schema(
            observations, load_json(schema_root / "combat-report-observations.schema.json")
        )
    )
    if errors:
        return sorted(errors)

    rule_ids = [rule["id"] for rule in rules["rules"]]
    observation_ids = [item["id"] for item in observations["observations"]]
    errors.extend(f"duplicate rule ID: {item}" for item in _duplicates(rule_ids))
    errors.extend(f"duplicate observation ID: {item}" for item in _duplicates(observation_ids))
    observation_by_id = {item["id"]: item for item in observations["observations"]}
    rule_id_set = set(rule_ids)
    vocabulary = load_canonical_vocabulary(repository_root)

    errors.extend(_unsafe_observation_values(observations, "observations"))
    for observation in observations["observations"]:
        frame = observation["location"]["frame_basename"]
        if frame and (Path(frame).name != frame or WINDOWS_ABSOLUTE.match(frame)):
            errors.append(f"{observation['id']}: frame_basename must be a basename")

    for rule in rules["rules"]:
        rule_id = rule["id"]
        source = rule["source"]
        dragon, ability = source["dragon"], source["ability"]
        if dragon is not None and dragon not in vocabulary:
            errors.append(f"{rule_id}: unknown canonical dragon {dragon!r}")
        if ability is not None:
            if dragon is None:
                errors.append(f"{rule_id}: ability {ability!r} requires a canonical source dragon")
            elif dragon in vocabulary and ability not in vocabulary[dragon]:
                errors.append(f"{rule_id}: unknown canonical ability {ability!r} for {dragon}")
        offset = rule["match"]["round_offset"]
        if offset["minimum"] > offset["maximum"]:
            errors.append(f"{rule_id}: round_offset minimum exceeds maximum")
        for relation in ("supports", "contradicts"):
            for observation_id in rule["evidence"][relation]:
                if observation_id not in observation_by_id:
                    errors.append(f"{rule_id}: dangling {relation} observation {observation_id}")
                elif relation == "supports" and observation_by_id[observation_id]["disposition"] == "contradicts":
                    errors.append(f"{rule_id}: supporting reference {observation_id} has contradicts disposition")
                elif relation == "contradicts" and observation_by_id[observation_id]["disposition"] == "supports":
                    errors.append(f"{rule_id}: contradicting reference {observation_id} has supports disposition")
        interpretation = rule["interpretation"]
        if interpretation["provenance"] == "inferred" and not rule["limitations"]:
            errors.append(f"{rule_id}: inferred rule requires at least one limitation")
        if rule["relationship"] in INFERRED_RELATIONSHIPS and not rule["limitations"]:
            errors.append(f"{rule_id}: {rule['relationship']} rule requires at least one limitation")
        if rule["relationship"] == "inferred_exclusive_mapping" and not rule.get("excluded_alternatives"):
            errors.append(f"{rule_id}: inferred_exclusive_mapping requires excluded_alternatives")
        if rule["relationship"] == "timing_correlation" and CAUSAL_WORDS.search(interpretation["summary"]):
            errors.append(f"{rule_id}: timing_correlation summary uses causal wording")
        if rule["status"] == "disputed" and not rule["evidence"]["contradicts"]:
            errors.append(f"{rule_id}: disputed rule requires counterevidence")
        if rule["status"] == "accepted" and interpretation["confidence"] in {"tentative", "disputed"}:
            errors.append(f"{rule_id}: accepted rule has inconsistent confidence {interpretation['confidence']}")
        if rule["status"] == "accepted" and not rule["evidence"]["supports"]:
            errors.append(f"{rule_id}: accepted rule requires supporting observations")
        if interpretation["confidence"] == "corroborated":
            confirmed_support = any(
                observation_by_id.get(observation_id, {}).get("quality", {}).get("visual_review") == "confirmed"
                for observation_id in rule["evidence"]["supports"]
            )
            if not confirmed_support or not rule["evidence"]["canonical_sources"]:
                errors.append(
                    f"{rule_id}: corroborated confidence requires confirmed support and an independent canonical source"
                )
        for pattern in rule["match"]["report_patterns"]:
            try:
                re.compile(pattern)
            except re.error as error:
                errors.append(f"{rule_id}: invalid report pattern {pattern!r}: {error}")
        if rule["status"] == "deprecated":
            review = rule["review"]
            if not review.get("rationale"):
                errors.append(f"{rule_id}: deprecated rule requires review.rationale")
            replacement = review.get("replacement_rule_id")
            if replacement and replacement not in rule_id_set:
                errors.append(f"{rule_id}: replacement rule does not exist: {replacement}")
        for superseded in rule.get("supersedes", []):
            if superseded not in rule_id_set:
                errors.append(f"{rule_id}: superseded rule does not exist: {superseded}")

    return sorted(set(errors))


def build_parser() -> argparse.ArgumentParser:
    root = repository_root_from_script()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=root)
    parser.add_argument("--rules", type=Path, default=root / "data" / "combat_report_rules.json")
    parser.add_argument("--observations", type=Path, default=root / "data" / "combat_report_observations.json")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors = validate_stores(load_json(args.rules), load_json(args.observations), args.repository_root.resolve())
    if errors:
        print("Combat report rule validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validated {args.rules} and {args.observations}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
