#!/usr/bin/env python3
"""Deterministically interpret an extracted Dragonfire combat report."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ANALYSIS_SCHEMA_VERSION = "1.0.0"
TOOL_VERSION = "1.0.0"
SUPPORTED_REPORT_MAJOR = 1
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from validate_combat_report_rules import load_json, validate_schema, validate_stores  # noqa: E402


def repository_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip().casefold()


def major_version(value: Any, label: str) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise ValueError(f"{label} must be a semantic version, got {value!r}")
    return int(value.split(".", 1)[0])


def validate_inputs(
    report: dict[str, Any], rules: dict[str, Any], observations: dict[str, Any], repository_root: Path,
) -> None:
    if major_version(report.get("schema_version"), "report schema_version") != SUPPORTED_REPORT_MAJOR:
        raise ValueError(
            f"unsupported combat-report schema {report.get('schema_version')!r}; expected major version 1"
        )
    for key in ("actions", "coverage"):
        if key not in report:
            raise ValueError(f"combat report is missing required field {key!r}")
    errors = validate_stores(rules, observations, repository_root)
    if errors:
        raise ValueError("invalid rule data:\n" + "\n".join(f"- {error}" for error in errors))


def event_id(report_hash: str, position: int, action: dict[str, Any]) -> str:
    action_hash = content_hash(action)[:12]
    return f"event.{report_hash[:16]}.{position:06d}.{action_hash}"


def event_text(action: dict[str, Any]) -> list[str]:
    evidence = action.get("evidence") or {}
    return [
        value for value in (
            action.get("ability"), evidence.get("head_text"), evidence.get("detail_text")
        ) if isinstance(value, str) and value.strip()
    ]


def owner_matches(source_owner: str, result_owner: str, scope: str) -> bool:
    if scope == "same":
        return source_owner == result_owner
    if scope == "opponent":
        return {source_owner, result_owner} == {"user", "enemy"}
    return True


def source_matches(rule: dict[str, Any], action: dict[str, Any]) -> bool:
    source, match = rule["source"], rule["match"]
    return (
        (source["dragon"] is None or action.get("actor") == source["dragon"])
        and (source["ability"] is None or action.get("ability") == source["ability"])
        and (match["event_kind"] is None or action.get("kind") == match["event_kind"])
    )


def result_matches(
    rule: dict[str, Any], source_action: dict[str, Any], result_action: dict[str, Any],
) -> tuple[bool, str | None]:
    match = rule["match"]
    if not owner_matches(source_action.get("owner", "unknown"), result_action.get("owner", "unknown"), match["owner_scope"]):
        return False, None
    if match["result_event_kind"] is not None and result_action.get("kind") != match["result_event_kind"]:
        return False, None
    source_round, result_round = source_action.get("round"), result_action.get("round")
    if not isinstance(source_round, int) or not isinstance(result_round, int):
        return False, None
    offset = result_round - source_round
    if not match["round_offset"]["minimum"] <= offset <= match["round_offset"]["maximum"]:
        return False, None
    normalized_fields = {normalize_text(value) for value in event_text(result_action)}
    phrases = match["report_phrases"]
    if phrases:
        matching_phrase = next(
            (phrase for phrase in phrases if normalize_text(phrase) in normalized_fields), None,
        )
        if matching_phrase is None:
            return False, None
        return True, f"exact report phrase {matching_phrase!r}"
    patterns = match["report_patterns"]
    if patterns:
        matching_pattern = next(
            (pattern for pattern in patterns if any(re.search(pattern, value, re.I) for value in event_text(result_action))),
            None,
        )
        if matching_pattern is None:
            return False, None
        return True, f"constrained report pattern {matching_pattern!r}"
    effect = rule["interpretation"]["effect"]
    if effect is not None and result_action.get("ability") != effect:
        return False, None
    return True, "exact structured result identity"


def rule_specificity(rule: dict[str, Any]) -> tuple[int, int, int]:
    source, match = rule["source"], rule["match"]
    structured = sum(value is not None for value in (
        source["dragon"], source["ability"], source["ability_type"],
        match["event_kind"], match["result_event_kind"],
    ))
    phrase_weight = 2 if match["report_phrases"] else 1 if match["report_patterns"] else 0
    context = (1 if match["owner_scope"] != "any" else 0) - (
        match["round_offset"]["maximum"] - match["round_offset"]["minimum"]
    )
    return structured, phrase_weight, context


def build_events(report: dict[str, Any], report_hash: str) -> list[dict[str, Any]]:
    return [
        {
            "event_id": event_id(report_hash, position, action),
            "position": position,
            "source_action": copy.deepcopy(action),
            "annotations": [],
        }
        for position, action in enumerate(report["actions"])
    ]


def match_rules(
    events: list[dict[str, Any]], rules: dict[str, Any], observations: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    observation_ids = {item["id"] for item in observations["observations"]}
    accepted = [rule for rule in rules["rules"] if rule["status"] == "accepted"]
    proposed: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rule in sorted(accepted, key=lambda item: item["id"]):
        for source_event in events:
            source_action = source_event["source_action"]
            if not source_matches(rule, source_action):
                continue
            for result_event in events:
                if result_event is source_event and rule["relationship"] not in {"explicit", "ui_alias"}:
                    continue
                matched, basis = result_matches(rule, source_action, result_event["source_action"])
                if not matched:
                    continue
                proposed[result_event["event_id"]].append({
                    "rule": rule, "source_event_id": source_event["event_id"],
                    "basis": basis, "specificity": rule_specificity(rule),
                })

    links: list[dict[str, Any]] = []
    ambiguities: list[dict[str, Any]] = []
    involved: set[str] = set()
    events_by_id = {event["event_id"]: event for event in events}
    for result_id in sorted(proposed, key=lambda item: events_by_id[item]["position"]):
        matches = proposed[result_id]
        best_specificity = max(item["specificity"] for item in matches)
        winners = [item for item in matches if item["specificity"] == best_specificity]
        winner_rule_ids = sorted({item["rule"]["id"] for item in winners})
        if len(winner_rule_ids) > 1:
            ambiguities.append({
                "result_event_id": result_id,
                "candidate_rule_ids": winner_rule_ids,
                "source_event_ids": sorted({item["source_event_id"] for item in winners}),
                "explanation": "Equally specific accepted rules match; no attribution was selected.",
            })
            continue
        winner = min(winners, key=lambda item: item["source_event_id"])
        rule = winner["rule"]
        suppressed = sorted({
            item["rule"]["id"] for item in matches
            if item["rule"]["id"] != rule["id"] and item["specificity"] < best_specificity
        })
        annotation = {
            "rule_id": rule["id"],
            "relationship": rule["relationship"],
            "provenance": rule["interpretation"]["provenance"],
            "confidence": rule["interpretation"]["confidence"],
            "effect": rule["interpretation"]["effect"],
            "explanation": rule["interpretation"]["summary"],
            "source_event_ids": [winner["source_event_id"]],
            "evidence_ids": sorted(set(rule["evidence"]["supports"] + rule["evidence"]["contradicts"]) & observation_ids),
            "match_basis": winner["basis"],
            "suppressed_rule_ids": suppressed,
        }
        events_by_id[result_id]["annotations"].append(annotation)
        source_action = events_by_id[winner["source_event_id"]]["source_action"]
        result_action = events_by_id[result_id]["source_action"]
        links.append({
            "source_event_id": winner["source_event_id"], "result_event_id": result_id,
            "rule_id": rule["id"], "relationship": rule["relationship"],
            "round_offset": result_action["round"] - source_action["round"],
            "seconds_offset": round(
                float((result_action.get("evidence") or {}).get("timestamp_seconds") or 0)
                - float((source_action.get("evidence") or {}).get("timestamp_seconds") or 0), 3,
            ),
        })
        involved.update((winner["source_event_id"], result_id))
    links.sort(key=lambda item: (events_by_id[item["result_event_id"]]["position"], item["rule_id"], item["source_event_id"]))
    return links, ambiguities, involved


def _sorted_totals(values: dict[str, int]) -> dict[str, int]:
    return dict(sorted(values.items(), key=lambda item: (item[0])))


def derive_insights(events: list[dict[str, Any]], links: list[dict[str, Any]]) -> dict[str, Any]:
    owners: dict[str, dict[str, Any]] = {}
    rounds: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for owner in ("user", "enemy", "unknown"):
        damage_by_actor: dict[str, int] = defaultdict(int)
        damage_by_ability: dict[str, int] = defaultdict(int)
        damage_by_target: dict[str, int] = defaultdict(int)
        damage_by_type: dict[str, int] = defaultdict(int)
        action_count = recovery = damage_total = 0
        for event in events:
            action = event["source_action"]
            if action.get("owner") != owner:
                continue
            action_count += 1
            recovery += int(action.get("recovery") or 0)
            damage = action.get("damage")
            if damage:
                amount = int(damage["amount"])
                damage_total += amount
                damage_by_actor[action.get("actor") or "Unknown"] += amount
                damage_by_ability[action.get("ability") or "Unknown"] += amount
                damage_by_target[action.get("target") or "Unknown"] += amount
                damage_by_type[damage.get("type") or "Unknown"] += amount
                rounds[str(action.get("round"))][owner] += amount
        owners[owner] = {
            "parsed_actions": action_count,
            "visible_parsed_damage_total": damage_total,
            "visible_parsed_recovery_total": recovery,
            "damage_by_actor": _sorted_totals(damage_by_actor),
            "damage_by_ability": _sorted_totals(damage_by_ability),
            "damage_by_target": _sorted_totals(damage_by_target),
            "damage_by_type": _sorted_totals(damage_by_type),
        }
    effects: dict[str, int] = defaultdict(int)
    for event in events:
        for annotation in event["annotations"]:
            effects[annotation.get("effect") or "Unknown"] += 1
    return {
        "provenance": "derived",
        "numeric_scope": "visible parsed values only",
        "by_owner": owners,
        "visible_parsed_damage_by_round": {
            round_number: _sorted_totals(values) for round_number, values in sorted(rounds.items(), key=lambda item: int(item[0]))
        },
        "established_effect_counts": _sorted_totals(effects),
        "established_link_count": len(links),
    }


def build_analysis_model(
    report: dict[str, Any], rules: dict[str, Any], observations: dict[str, Any], repository_root: Path,
) -> dict[str, Any]:
    validate_inputs(report, rules, observations, repository_root)
    report_hash, rule_hash, observation_hash = content_hash(report), content_hash(rules), content_hash(observations)
    events = build_events(report, report_hash)
    links, ambiguities, involved = match_rules(events, rules, observations)
    unmatched = [event["event_id"] for event in events if event["event_id"] not in involved]
    coverage = copy.deepcopy(report["coverage"])
    coverage["analyst_warnings"] = []
    if ambiguities:
        coverage["analyst_warnings"].append(
            f"{len(ambiguities)} result event(s) have equally specific accepted rule matches."
        )
    if unmatched:
        coverage["analyst_warnings"].append(
            f"{len(unmatched)} event(s) have no established interpretation."
        )
    return {
        "analysis_schema_version": ANALYSIS_SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "input_report_hash": report_hash,
        "rule_set_version": rules["metadata"]["schema_version"],
        "rule_set_hash": rule_hash,
        "observation_set_hash": observation_hash,
        "source_report": copy.deepcopy(report),
        "events": events,
        "links": links,
        "unmatched_events": unmatched,
        "ambiguous_matches": ambiguities,
        "coverage": coverage,
        "insights": derive_insights(events, links),
    }


def analysis_summary(model: dict[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(model[key]) for key in (
            "analysis_schema_version", "tool_version", "input_report_hash", "rule_set_version",
            "rule_set_hash", "observation_set_hash", "coverage", "insights", "links",
            "unmatched_events", "ambiguous_matches",
        )
    } | {
        "timeline": [
            {
                "event_id": event["event_id"],
                "round": event["source_action"].get("round"),
                "owner": event["source_action"].get("owner"),
                "actor": event["source_action"].get("actor"),
                "ability": event["source_action"].get("ability"),
                "frame": (event["source_action"].get("evidence") or {}).get("frame"),
                "annotations": copy.deepcopy(event["annotations"]),
            }
            for event in model["events"]
        ]
    }


def load_effect_names(repository_root: Path) -> dict[str, str]:
    path = repository_root / "data" / "effects.json"
    if not path.exists():
        return {}
    return {
        normalize_text(item["name"]): item["name"]
        for item in load_json(path).get("effects", []) if isinstance(item.get("name"), str)
    }


def report_identity(model: dict[str, Any]) -> str:
    source = model["source_report"].get("source") or {}
    source_hash = source.get("sha256")
    return str(source_hash) if source_hash and source_hash != "fixture" else model["input_report_hash"][:24]


def formation_identity(model: dict[str, Any]) -> str:
    members: dict[str, set[str]] = defaultdict(set)
    for action in model["source_report"]["actions"]:
        if action.get("actor"):
            members[action.get("owner", "unknown")].add(action["actor"])
    formation = {owner: sorted(names) for owner, names in sorted(members.items())}
    return content_hash(formation)[:24]


def candidate_result_phrase(action: dict[str, Any]) -> str:
    evidence = action.get("evidence") or {}
    return (evidence.get("detail_text") or evidence.get("head_text") or action.get("ability") or "").strip()


def discover_candidates(
    models: list[dict[str, Any]], rules: dict[str, Any], observations: dict[str, Any],
    repository_root: Path,
) -> dict[str, Any]:
    """Build a conservative review queue; never return a canonical rule."""
    effect_names = load_effect_names(repository_root)
    groups: dict[str, dict[str, Any]] = {}
    for model in models:
        by_id = {event["event_id"]: event for event in model["events"]}
        report_id, formation_id = report_identity(model), formation_identity(model)
        unmatched = set(model["unmatched_events"])
        for result_event in model["events"]:
            if result_event["event_id"] not in unmatched:
                continue
            result_action = result_event["source_action"]
            if result_action.get("kind") not in {"affect", "self_effect", "recovery"}:
                continue
            phrase = candidate_result_phrase(result_action)
            if not phrase:
                continue
            alternatives: list[dict[str, Any]] = []
            for source_event in model["events"]:
                if source_event["position"] >= result_event["position"]:
                    continue
                source_action = source_event["source_action"]
                if source_action.get("owner") != result_action.get("owner"):
                    continue
                if not isinstance(source_action.get("round"), int) or not isinstance(result_action.get("round"), int):
                    continue
                offset = result_action["round"] - source_action["round"]
                if not 0 <= offset <= 1:
                    continue
                alternatives.append({
                    "actor": source_action.get("actor"), "ability": source_action.get("ability"),
                    "event_id": source_event["event_id"], "round_offset": offset,
                })
            alternatives.sort(key=lambda item: (item["round_offset"], item["actor"] or "", item["ability"] or "", item["event_id"]))
            source_signature = [
                [item["actor"], item["ability"], item["round_offset"]] for item in alternatives
            ]
            key_data = {"result_phrase": normalize_text(phrase), "source_window": source_signature}
            fingerprint = content_hash(key_data)
            group = groups.setdefault(fingerprint, {
                "fingerprint": fingerprint,
                "pattern": {
                    "result_phrase": phrase,
                    "normalized_result": None,
                    "source_window": source_signature,
                },
                "occurrences": [], "alternatives": {}, "reports": set(), "formations": set(),
                "contradictions": [],
            })
            normalized_ability = normalize_text(result_action.get("ability"))
            normalized_phrase = normalize_text(phrase)
            known_effect = effect_names.get(normalized_ability)
            if known_effect is None:
                known_effect = next(
                    (canonical for normalized, canonical in sorted(effect_names.items())
                     if re.search(rf"\b{re.escape(normalized)}\b", normalized_phrase)),
                    None,
                )
            group["pattern"]["normalized_result"] = known_effect
            group["occurrences"].append({
                "report_id": report_id, "formation_id": formation_id,
                "event_id": result_event["event_id"], "round": result_action.get("round"),
                "timestamp_seconds": (result_action.get("evidence") or {}).get("timestamp_seconds"),
                "frame_basename": (result_action.get("evidence") or {}).get("frame"),
                "verbatim": phrase,
            })
            group["reports"].add(report_id)
            group["formations"].add(formation_id)
            for item in alternatives:
                alternative_key = json.dumps(
                    [item["actor"], item["ability"], item["round_offset"]], ensure_ascii=False,
                )
                group["alternatives"][alternative_key] = {
                    "actor": item["actor"], "ability": item["ability"],
                    "round_offset": item["round_offset"],
                }

    candidates: list[dict[str, Any]] = []
    for fingerprint, group in groups.items():
        alternatives = [group["alternatives"][key] for key in sorted(group["alternatives"])]
        offsets = {item["round_offset"] for item in alternatives}
        repeated = len(group["occurrences"]) >= 2
        relationship = "timing_correlation" if repeated and alternatives and len(offsets) == 1 else "unresolved"
        candidates.append({
            "candidate_id": f"candidate.{fingerprint[:16]}",
            "fingerprint": fingerprint,
            "pattern": group["pattern"],
            "counts": {
                "occurrences": len(group["occurrences"]),
                "distinct_reports": len(group["reports"]),
                "distinct_formations": len(group["formations"]),
            },
            "occurrences": sorted(group["occurrences"], key=lambda item: (item["report_id"], item["event_id"])),
            "known_alternative_sources": alternatives,
            "contradictions": sorted(group["contradictions"], key=lambda item: json.dumps(item, sort_keys=True)),
            "proposed_relationship": relationship,
            "evidence_needed": [
                "Visually review every cited frame and exact wording.",
                "Repeat the pattern in a distinct report and formation.",
                "Vary or exclude the listed alternative sources.",
                "Check compatible canonical ability text before proposing causality.",
            ],
        })

    observation_by_id = {item["id"]: item for item in observations["observations"]}
    for rule in sorted(rules["rules"], key=lambda item: item["id"]):
        if rule["status"] != "accepted" or not rule["evidence"]["contradicts"]:
            continue
        contradiction_items = [
            {"rule_id": rule["id"], "observation_id": observation_id}
            for observation_id in rule["evidence"]["contradicts"] if observation_id in observation_by_id
        ]
        fingerprint = content_hash({"rule_id": rule["id"], "contradictions": contradiction_items})
        candidates.append({
            "candidate_id": f"candidate.{fingerprint[:16]}", "fingerprint": fingerprint,
            "pattern": {"result_phrase": None, "normalized_result": rule["interpretation"]["effect"], "source_window": []},
            "counts": {"occurrences": 0, "distinct_reports": 0, "distinct_formations": 0},
            "occurrences": [], "known_alternative_sources": [],
            "contradictions": contradiction_items, "proposed_relationship": "unresolved",
            "evidence_needed": ["Resolve the cited counterevidence before retaining or revising the accepted rule."],
        })
    candidates.sort(key=lambda item: (item["candidate_id"], item["fingerprint"]))
    return {
        "schema_version": "1.0.0", "tool_version": TOOL_VERSION,
        "input_report_hashes": sorted(model["input_report_hash"] for model in models),
        "rule_set_hash": content_hash(rules), "candidates": candidates,
    }


def draft_candidate_fragment(candidate_store: dict[str, Any], candidate_key: str) -> dict[str, Any]:
    candidate = next(
        (item for item in candidate_store.get("candidates", [])
         if candidate_key in {item.get("candidate_id"), item.get("fingerprint")}),
        None,
    )
    if candidate is None:
        raise ValueError(f"candidate not found: {candidate_key}")
    alternatives = candidate["known_alternative_sources"]
    unique_source = alternatives[0] if len(alternatives) == 1 else {}
    result = candidate["pattern"].get("normalized_result")
    slug_seed = normalize_text(result or candidate["candidate_id"]).replace(" ", "-")
    slug_seed = re.sub(r"[^a-z0-9-]+", "-", slug_seed).strip("-") or "unresolved"
    return {
        "candidate_fingerprint": candidate["fingerprint"],
        "review_required": True,
        "draft_rule": {
            "id": f"rule.review.{slug_seed}.v1",
            "status": "draft",
            "relationship": candidate["proposed_relationship"],
            "source": {
                "dragon": unique_source.get("actor"), "ability": unique_source.get("ability"),
                "ability_type": None,
            },
            "match": {
                "event_kind": None, "owner_scope": "same", "result_event_kind": None,
                "round_offset": {
                    "minimum": min((item["round_offset"] for item in alternatives), default=0),
                    "maximum": max((item["round_offset"] for item in alternatives), default=0),
                },
                "report_phrases": [candidate["pattern"]["result_phrase"]] if candidate["pattern"]["result_phrase"] else [],
                "report_patterns": [],
            },
            "interpretation": {
                "effect": result,
                "summary": "Review candidate only; the responsible source remains unresolved.",
                "provenance": "unknown", "confidence": "tentative",
            },
            "evidence": {"supports": [], "contradicts": [], "canonical_sources": []},
            "limitations": list(candidate["evidence_needed"]),
            "review": {"created": "YYYY-MM-DD", "last_reviewed": "YYYY-MM-DD"},
        },
        "observation_templates": candidate["occurrences"],
    }


def render_markdown(model: dict[str, Any]) -> str:
    coverage, insights = model["coverage"], model["insights"]
    lines = [
        "# Combat Analyst report", "",
        f"- Input report SHA-256: `{model['input_report_hash']}`",
        f"- Rule store SHA-256: `{model['rule_set_hash']}`",
        f"- Rule schema version: `{model['rule_set_version']}`", "",
        "## Coverage and reliability", "",
        f"- Parsed source actions: {coverage.get('action_count', len(model['events']))}",
        f"- Rounds with parsed actions: {', '.join(map(str, coverage.get('rounds_with_actions', []))) or 'none'}",
    ]
    for warning in coverage.get("warnings", []):
        lines.append(f"- Source warning: {warning}")
    for warning in coverage.get("analyst_warnings", []):
        lines.append(f"- Analyst warning: {warning}")
    lines.extend(["", "## Derived visible parsed totals", ""])
    for owner in ("user", "enemy", "unknown"):
        values = insights["by_owner"][owner]
        if values["parsed_actions"] or owner != "unknown":
            lines.append(
                f"- {owner}: {values['visible_parsed_damage_total']:,} visible parsed damage; "
                f"{values['visible_parsed_recovery_total']:,} visible parsed recovery; "
                f"{values['parsed_actions']} parsed action(s)."
            )
    lines.extend(["", "## Round-by-round observed timeline", ""])
    for event in model["events"]:
        action, event_key = event["source_action"], event["event_id"]
        evidence = action.get("evidence") or {}
        lines.append(
            f"- R{action.get('round')} {action.get('owner')}: {action.get('actor') or 'Unknown'} — "
            f"{action.get('ability') or action.get('kind')} → {action.get('target') or 'n/a'} "
            f"(`{event_key}`, frame `{evidence.get('frame') or 'unknown'}`)"
        )
        for annotation in event["annotations"]:
            lines.append(
                f"  - {annotation['provenance']}/{annotation['confidence']}: "
                f"{annotation['explanation']} (`{annotation['rule_id']}`; source "
                f"`{annotation['source_event_ids'][0]}`)"
            )
    lines.extend(["", "## Established interpretations", ""])
    if model["links"]:
        for link in model["links"]:
            lines.append(
                f"- `{link['rule_id']}` links `{link['source_event_id']}` to `{link['result_event_id']}` "
                f"at round offset {link['round_offset']} (timing is not independent proof of causality)."
            )
    else:
        lines.append("- None. No accepted rule produced a unique match.")
    lines.extend(["", "## Unknown or ambiguous", ""])
    for ambiguity in model["ambiguous_matches"]:
        lines.append(
            f"- Ambiguous `{ambiguity['result_event_id']}`: "
            + ", ".join(f"`{item}`" for item in ambiguity["candidate_rule_ids"])
            + "."
        )
    for event_key in model["unmatched_events"]:
        lines.append(f"- Unknown interpretation: `{event_key}`.")
    if not model["ambiguous_matches"] and not model["unmatched_events"]:
        lines.append("- None.")
    lines.extend(["", "## Tactical interpretation", ""])
    if coverage.get("warnings") or coverage.get("analyst_warnings"):
        lines.append("The visible parsed ledger is incomplete or partly unresolved; it does not support a complete combat-outcome claim.")
    else:
        lines.append("The parsed ledger has no recorded coverage warning, but values remain report-visible observations rather than server totals.")
    return "\n".join(lines) + "\n"


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def interpret_paths(
    report_path: Path, output: Path, rules_path: Path, observations_path: Path,
    repository_root: Path,
) -> dict[str, Path]:
    report, rules, observations = load_json(report_path), load_json(rules_path), load_json(observations_path)
    model = build_analysis_model(report, rules, observations, repository_root)
    schema = load_json(SCRIPT_DIR / "schemas" / "enriched-combat-report.schema.json")
    schema_errors = validate_schema(model, schema)
    if schema_errors:
        raise ValueError("generated enriched report failed schema validation:\n" + "\n".join(schema_errors))
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "enriched": output / "enriched-combat-report.json",
        "analysis": output / "combat-analysis.json",
        "markdown": output / "combat-insights.md",
        "candidates": output / "rule-candidates.json",
    }
    write_json(paths["enriched"], model)
    write_json(paths["analysis"], analysis_summary(model))
    paths["markdown"].write_text(render_markdown(model), encoding="utf-8")
    write_json(paths["candidates"], discover_candidates([model], rules, observations, repository_root))
    return paths


def add_common_inputs(parser: argparse.ArgumentParser, root: Path) -> None:
    parser.add_argument("--rules", type=Path, default=root / "data" / "combat_report_rules.json")
    parser.add_argument("--observations", type=Path, default=root / "data" / "combat_report_observations.json")
    parser.add_argument("--repository-root", type=Path, default=root)


def build_parser() -> argparse.ArgumentParser:
    root = repository_root_from_script()
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    interpret = subparsers.add_parser("interpret", help="Interpret a normalized combat-report.json")
    interpret.add_argument("--report", type=Path, required=True)
    interpret.add_argument("--output", type=Path, required=True)
    add_common_inputs(interpret, root)
    propose = subparsers.add_parser("propose", help="Write a reviewed candidate as a draft JSON fragment")
    propose.add_argument("--candidates", type=Path, required=True)
    propose.add_argument("--candidate", required=True, help="Candidate ID or full fingerprint")
    propose.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "interpret":
        paths = interpret_paths(
            args.report.resolve(), args.output.resolve(), args.rules.resolve(),
            args.observations.resolve(), args.repository_root.resolve(),
        )
        print(f"Enriched report: {paths['enriched']}")
        print(f"Analysis: {paths['analysis']}")
        print(f"Insights: {paths['markdown']}")
        print(f"Rule candidates: {paths['candidates']}")
    elif args.command == "propose":
        fragment = draft_candidate_fragment(load_json(args.candidates.resolve()), args.candidate)
        args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
        write_json(args.output.resolve(), fragment)
        print(f"Draft review fragment: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
