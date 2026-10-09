#!/usr/bin/env python3
"""Measure and aggregate local combat reports without turning correlation into causation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import validate_combat_report_rules as validator


TOOL_VERSION = "1.0.0"
SUPPORTED_SCHEMA_MAJOR = 1
SCHEMA_ROOT = SCRIPT_DIR / "schemas"


def repository_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def schema_major(value: Any, label: str) -> int:
    version = (
        value.get("analysis_schema_version") or value.get("schema_version")
        or (value.get("metadata") or {}).get("schema_version")
    )
    try:
        major = int(str(version).split(".", 1)[0])
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} has no valid schema version") from error
    if major != SUPPORTED_SCHEMA_MAJOR:
        raise ValueError(f"unsupported {label} schema: {version}")
    return major


def scheduled_rounds(trigger: dict[str, Any], battle_rounds: list[int]) -> list[int]:
    schedule = trigger["schedule"]
    if schedule == "each_round":
        return battle_rounds
    if schedule == "odd_rounds":
        return [round_number for round_number in battle_rounds if round_number % 2]
    if schedule == "even_rounds":
        return [round_number for round_number in battle_rounds if round_number % 2 == 0]
    configured = set(trigger.get("rounds", []))
    return [round_number for round_number in battle_rounds if round_number in configured]


def event_map(analysis: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {event["event_id"]: event for event in analysis.get("events", [])}


def action_time(event: dict[str, Any]) -> float:
    return float((event.get("source_action", {}).get("evidence") or {}).get("timestamp_seconds") or 0)


def activation_groups(
    analysis: dict[str, Any], definition: dict[str, Any], events: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    accepted_rules = set(definition["success_rule_ids"])
    grouped: dict[str, dict[str, Any]] = {}
    for link in analysis.get("links", []):
        if link.get("rule_id") not in accepted_rules:
            continue
        source_id = link["source_event_id"]
        source = events.get(source_id)
        result = events.get(link["result_event_id"])
        if source is None or result is None:
            continue
        action = source["source_action"]
        group = grouped.setdefault(source_id, {
            "source_event_id": source_id,
            "round": action.get("round"),
            "timestamp_seconds": action_time(source),
            "owner": action.get("owner"),
            "actor": action.get("actor"),
            "result_event_ids": set(),
            "rule_ids": set(),
        })
        group["result_event_ids"].add(result["event_id"])
        group["rule_ids"].add(link["rule_id"])
    ordered = sorted(grouped.values(), key=lambda item: (item["round"], item["timestamp_seconds"], item["source_event_id"]))
    stack_gain = definition["activation"].get("stack_gain")
    max_stacks = definition["activation"].get("max_stacks")
    stack = 0
    for item in ordered:
        item["result_event_ids"] = sorted(item["result_event_ids"])
        item["rule_ids"] = sorted(item["rule_ids"])
        if stack_gain:
            stack = stack + stack_gain
            if max_stacks is not None:
                stack = min(stack, max_stacks)
            item["inferred_stack_after"] = stack
        else:
            item["inferred_stack_after"] = None
    return ordered


def subject_keys(
    analysis: dict[str, Any], definition: dict[str, Any], activations: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    source = definition["source"]
    keys = {(item["owner"], item["actor"]) for item in activations if item.get("owner") and item.get("actor")}
    for event in analysis.get("events", []):
        action = event["source_action"]
        if action.get("actor") == source["dragon"] or action.get("ability") == source["ability"]:
            if action.get("owner") and action.get("actor"):
                keys.add((action["owner"], action["actor"]))
    return sorted(keys)


def duration_rounds(event: dict[str, Any]) -> int | None:
    detail = ((event.get("source_action") or {}).get("evidence") or {}).get("detail_text") or ""
    match = re.search(r"Lasts\s*for\s*([0-9]+)\s*round", detail, re.I)
    return int(match.group(1)) if match else None


def build_measurement(
    analysis: dict[str, Any], definitions: dict[str, Any], *, experiment_id: str | None = None,
    variant: str | None = None, question: str | None = None,
) -> dict[str, Any]:
    schema_major(analysis, "enriched combat report")
    schema_major(definitions, "trial definitions")
    events = event_map(analysis)
    battle_rounds = sorted(set(int(item) for item in analysis.get("coverage", {}).get("rounds_with_actions", [])))
    warnings = list(analysis.get("coverage", {}).get("warnings", []))
    rejected = int(analysis.get("coverage", {}).get("rejected_action_count", 0) or 0)
    trials: list[dict[str, Any]] = []
    exposures: list[dict[str, Any]] = []

    for definition in sorted(definitions.get("trials", []), key=lambda item: item["id"]):
        if definition["status"] != "accepted":
            continue
        activations = activation_groups(analysis, definition, events)
        rounds = scheduled_rounds(definition["trigger"], battle_rounds)
        for activation in activations:
            source_event = events[activation["source_event_id"]]
            duration = duration_rounds(source_event)
            if definition["activation"]["persists_until_end"]:
                end_round = battle_rounds[-1] if battle_rounds else activation["round"]
            elif duration is not None:
                end_round = activation["round"] + duration - 1
            else:
                end_round = None
            exposures.append({
                "trial_id": definition["id"], "owner": activation["owner"], "actor": activation["actor"],
                "source_event_id": activation["source_event_id"], "start_round": activation["round"],
                "start_timestamp_seconds": activation["timestamp_seconds"], "end_round": end_round,
                "duration_rounds": duration, "inferred_stack_after": activation["inferred_stack_after"],
                "provenance": "derived" if duration is not None else "inferred",
            })
        for owner, actor in subject_keys(analysis, definition, activations):
            present_rounds = sorted({
                int(event["source_action"]["round"])
                for event in analysis.get("events", [])
                if event["source_action"].get("owner") == owner
                and event["source_action"].get("actor") == actor
                and event["source_action"].get("round") in rounds
            })
            eligible = present_rounds if definition["opportunity"]["requires_actor_action_in_round"] else rounds
            unknown = sorted(set(rounds) - set(eligible))
            subject_activations = [
                item for item in activations if item["owner"] == owner and item["actor"] == actor
            ]
            complete = not warnings and not rejected
            reportable = complete and not unknown and bool(eligible)
            trials.append({
                "trial_id": definition["id"], "source": definition["source"], "owner": owner, "actor": actor,
                "scheduled_rounds": rounds, "eligible_opportunity_rounds": eligible,
                "unknown_opportunity_rounds": unknown, "activation_count": len(subject_activations),
                "activations": subject_activations,
                "observable_rate": round(len(subject_activations) / len(eligible), 6) if eligible else None,
                "rate_reportable": reportable,
                "rate_limitation": None if reportable else (
                    "Coverage warnings or rejected actions prevent a failure denominator." if not complete
                    else "At least one scheduled round lacks positive evidence that the source actor remained active."
                ),
                "advertised_chance_percent": definition["trigger"]["advertised_chance_percent"],
            })

    ordered_exposures = sorted(exposures, key=lambda item: (
        item["owner"], item["actor"], item["start_round"], item["start_timestamp_seconds"], item["trial_id"],
    ))
    outcomes: list[dict[str, Any]] = []
    for event in analysis.get("events", []):
        action = event["source_action"]
        if action.get("damage") is None and action.get("recovery") is None:
            continue
        timestamp = action_time(event)
        active: list[dict[str, Any]] = []
        for exposure in ordered_exposures:
            if exposure["end_round"] is None:
                continue
            if (exposure["owner"], exposure["actor"]) != (action.get("owner"), action.get("actor")):
                continue
            if action.get("round") < exposure["start_round"] or timestamp < exposure["start_timestamp_seconds"]:
                continue
            if exposure["end_round"] is not None and action.get("round") > exposure["end_round"]:
                continue
            active.append({"trial_id": exposure["trial_id"], "stack_count": exposure["inferred_stack_after"]})
        outcomes.append({
            "event_id": event["event_id"], "round": action.get("round"), "timestamp_seconds": timestamp,
            "owner": action.get("owner"), "actor": action.get("actor"), "ability": action.get("ability"),
            "target": action.get("target"), "damage": action.get("damage"), "recovery": action.get("recovery"),
            "active_exposures": active,
        })

    measurement = {
        "measurement_schema_version": "1.0.0", "tool_version": TOOL_VERSION,
        "input_report_hash": analysis["input_report_hash"], "rule_set_hash": analysis["rule_set_hash"],
        "trial_definition_hash": content_hash(definitions),
        "experiment": {"id": experiment_id, "variant": variant, "question": question},
        "coverage": {
            "rounds_with_actions": battle_rounds, "warnings": warnings,
            "rejected_action_count": rejected, "complete_for_failure_counting": not warnings and not rejected,
        },
        "trials": sorted(trials, key=lambda item: (item["trial_id"], item["owner"], item["actor"])),
        "exposures": ordered_exposures, "outcome_samples": outcomes,
        "limitations": [
            "Observable rates are per-report measurements, not universal proc probabilities.",
            "Missing text is never counted as a failed proc unless every scheduled opportunity is positively observable.",
            "Exposure-to-outcome association is correlation; it is not an isolated causal effect estimate."
        ],
    }
    errors = validator.validate_schema(measurement, load_json(SCHEMA_ROOT / "combat-measurement.schema.json"))
    if errors:
        raise ValueError("generated combat measurement failed schema validation:\n" + "\n".join(errors))
    return measurement


def wilson_interval(successes: int, opportunities: int) -> list[float] | None:
    if opportunities <= 0:
        return None
    z = 1.959963984540054
    proportion = successes / opportunities
    denominator = 1 + z * z / opportunities
    center = (proportion + z * z / (2 * opportunities)) / denominator
    margin = z * math.sqrt(proportion * (1 - proportion) / opportunities + z * z / (4 * opportunities * opportunities)) / denominator
    return [round(max(0.0, center - margin), 6), round(min(1.0, center + margin), 6)]


def aggregate_measurements(measurements: list[dict[str, Any]], experiment_id: str | None = None) -> dict[str, Any]:
    if not measurements:
        raise ValueError("at least one measurement is required")
    for measurement in measurements:
        schema_major({"schema_version": measurement.get("measurement_schema_version")}, "measurement")
    ids = {item.get("experiment", {}).get("id") for item in measurements if item.get("experiment", {}).get("id")}
    if experiment_id is None and len(ids) == 1:
        experiment_id = next(iter(ids))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for measurement in measurements:
        for trial in measurement.get("trials", []):
            grouped[trial["trial_id"]].append({"measurement": measurement, "trial": trial})
    trials: list[dict[str, Any]] = []
    for trial_id in sorted(grouped):
        rows = grouped[trial_id]
        eligible = sum(len(row["trial"]["eligible_opportunity_rounds"]) for row in rows)
        unknown = sum(len(row["trial"]["unknown_opportunity_rounds"]) for row in rows)
        successes = sum(row["trial"]["activation_count"] for row in rows)
        fully_reportable = all(row["trial"]["rate_reportable"] for row in rows)
        variants: dict[str, dict[str, int]] = defaultdict(lambda: {"reports": 0, "successes": 0, "opportunities": 0, "unknown": 0})
        for row in rows:
            variant = row["measurement"].get("experiment", {}).get("variant") or "unspecified"
            values = variants[variant]
            values["reports"] += 1
            values["successes"] += row["trial"]["activation_count"]
            values["opportunities"] += len(row["trial"]["eligible_opportunity_rounds"])
            values["unknown"] += len(row["trial"]["unknown_opportunity_rounds"])
        source = rows[0]["trial"]["source"]
        trials.append({
            "trial_id": trial_id, "source": source, "distinct_reports": len({row["measurement"]["input_report_hash"] for row in rows}),
            "subjects": len(rows), "activations": successes, "observable_opportunities": eligible,
            "unknown_opportunities": unknown, "observable_rate": round(successes / eligible, 6) if eligible else None,
            "interval_95": wilson_interval(successes, eligible), "rate_reportable": fully_reportable,
            "advertised_chance_percent": rows[0]["trial"]["advertised_chance_percent"],
            "variants": [{"name": name, **variants[name]} for name in sorted(variants)],
            "limitations": ([] if fully_reportable else [
                "At least one report has incomplete opportunity visibility; the observable rate must not be presented as a complete failure denominator."
            ]),
        })
    hashes = sorted({item["input_report_hash"] for item in measurements})
    model = {
        "experiment_schema_version": "1.0.0", "tool_version": TOOL_VERSION,
        "experiment_id": experiment_id, "measurement_hashes": sorted(content_hash(item) for item in measurements),
        "input_report_hashes": hashes,
        "rule_set_hashes": sorted({item["rule_set_hash"] for item in measurements}),
        "trial_definition_hashes": sorted({item["trial_definition_hash"] for item in measurements}),
        "trials": trials,
        "outcome_samples": [
            {"input_report_hash": measurement["input_report_hash"], "variant": measurement.get("experiment", {}).get("variant"), **sample}
            for measurement in sorted(measurements, key=lambda item: item["input_report_hash"])
            for sample in measurement.get("outcome_samples", [])
        ],
        "limitations": [
            "Pooled observations are descriptive until formation, progression, enemy, troop state, and overlapping effects are controlled.",
            "Wilson intervals quantify sampling uncertainty only; they do not repair coverage or eligibility uncertainty.",
        ],
    }
    model["aggregate_hash"] = content_hash(model)
    errors = validator.validate_schema(model, load_json(SCHEMA_ROOT / "combat-experiment.schema.json"))
    if errors:
        raise ValueError("generated combat experiment failed schema validation:\n" + "\n".join(errors))
    return model


def render_measurement(measurement: dict[str, Any]) -> str:
    lines = [
        "# Combat empirical measurement", "",
        f"- Input report SHA-256: `{measurement['input_report_hash']}`",
        f"- Rule store SHA-256: `{measurement['rule_set_hash']}`",
        f"- Trial definition SHA-256: `{measurement['trial_definition_hash']}`", "",
        "## RNG opportunities and activations", "",
    ]
    if not measurement["trials"]:
        lines.append("- No configured trial source was identifiable in this report.")
    for trial in measurement["trials"]:
        rate = f"{trial['activation_count']}/{len(trial['eligible_opportunity_rounds'])} observable"
        if trial["rate_reportable"]:
            rate += f" ({trial['observable_rate']:.1%})"
        else:
            rate += "; no complete proc-rate denominator"
        lines.append(f"- `{trial['trial_id']}` — {trial['actor']} ({trial['owner']}): {rate}.")
        if trial["unknown_opportunity_rounds"]:
            lines.append(f"  - Unknown scheduled rounds: {', '.join(map(str, trial['unknown_opportunity_rounds']))}.")
        if trial["rate_limitation"]:
            lines.append(f"  - Limitation: {trial['rate_limitation']}")
    lines.extend(["", "## Effect exposures and outcome samples", ""])
    lines.append(f"- Derived exposure records: {len(measurement['exposures'])}.")
    lines.append(f"- Damage/recovery samples with exposure context: {len(measurement['outcome_samples'])}.")
    lines.append("- Exposure correlation does not establish the isolated additive or diminishing effect of a buff or debuff.")
    return "\n".join(lines) + "\n"


def render_aggregate(model: dict[str, Any]) -> str:
    lines = [
        "# Combat experiment summary", "", f"- Experiment: `{model['experiment_id'] or 'unspecified'}`",
        f"- Aggregate SHA-256: `{model['aggregate_hash']}`",
        f"- Input report SHA-256 values: {', '.join(f'`{item}`' for item in model['input_report_hashes'])}",
        f"- Rule store SHA-256 values: {', '.join(f'`{item}`' for item in model['rule_set_hashes'])}",
        f"- Trial definition SHA-256 values: {', '.join(f'`{item}`' for item in model['trial_definition_hashes'])}",
        "", "## Aggregated trials", "",
    ]
    for trial in model["trials"]:
        rate = "n/a" if trial["observable_rate"] is None else f"{trial['observable_rate']:.1%}"
        qualifier = "complete denominator" if trial["rate_reportable"] else "partial observable denominator"
        lines.append(
            f"- `{trial['trial_id']}`: {trial['activations']}/{trial['observable_opportunities']} observable ({rate}); "
            f"{trial['distinct_reports']} distinct report(s); {qualifier}; {trial['unknown_opportunities']} unknown opportunity(ies)."
        )
        if trial["interval_95"]:
            lines.append(f"  - 95% Wilson interval over observable opportunities: {trial['interval_95'][0]:.1%}–{trial['interval_95'][1]:.1%}.")
        for variant in trial["variants"]:
            lines.append(
                f"  - Variant `{variant['name']}`: {variant['successes']}/{variant['opportunities']} observable; "
                f"{variant['unknown']} unknown across {variant['reports']} subject-report(s)."
            )
    lines.extend(["", "## Interpretation boundary", ""])
    lines.extend(f"- {item}" for item in model["limitations"])
    return "\n".join(lines) + "\n"


def draft_finding(aggregate: dict[str, Any], trial_id: str) -> dict[str, Any]:
    trial = next((item for item in aggregate["trials"] if item["trial_id"] == trial_id), None)
    if trial is None:
        raise ValueError(f"trial not found in aggregate: {trial_id}")
    slug = trial_id.removeprefix("trial.").rsplit(".v", 1)[0]
    source = trial["source"]
    return {
        "aggregate_hash": aggregate["aggregate_hash"], "review_required": True,
        "draft_finding": {
            "id": f"finding.{slug}.observed-proc-rate.v1", "status": "draft", "metric_type": "proc_rate",
            "source": {"dragon": source["dragon"], "ability": source["ability"], "trial_id": trial_id},
            "scope": {"battle_type": "unknown", "enemy": None, "formation_constraints": [], "progression_constraints": []},
            "estimate": {
                "numerator": trial["activations"], "denominator": trial["observable_opportunities"],
                "rate": trial["observable_rate"], "interval_95": trial["interval_95"], "unit": "activation per observable opportunity",
            },
            "evidence": {
                "report_hashes": aggregate["input_report_hashes"], "observation_ids": [],
                "contradicting_observation_ids": [], "distinct_reports": trial["distinct_reports"],
            },
            "interpretation": {
                "summary": "Draft descriptive proc-rate finding; review eligibility, coverage, formation comparability, and progression before acceptance.",
                "provenance": "derived", "confidence": "tentative",
            },
            "limitations": [
                "This is an observed sample rate, not a replacement for the canonical advertised chance.",
                *trial["limitations"],
            ],
            "recommendation": {"eligible": False, "use": "exclude", "rationale": "Draft empirical findings are not Strategist inputs."},
            "review": {"created": "YYYY-MM-DD", "last_reviewed": "YYYY-MM-DD", "strategist_gate": "not_requested"},
        },
    }


def build_finding_handoff(
    finding_id: str, findings: dict[str, Any], target_files: list[str], test_commands: list[str], confirmed: bool,
) -> dict[str, Any]:
    finding = next((item for item in findings.get("findings", []) if item["id"] == finding_id), None)
    if finding is None:
        raise ValueError(f"empirical finding not found: {finding_id}")
    if not confirmed:
        raise ValueError("Strategist handoff requires explicit empirical-finding confirmation")
    if finding["status"] != "accepted" or finding["interpretation"]["confidence"] != "corroborated":
        raise ValueError("Strategist handoff requires an accepted, corroborated empirical finding")
    if not finding["recommendation"]["eligible"] or finding["review"]["strategist_gate"] != "approved":
        raise ValueError("Strategist handoff requires an approved recommendation gate")
    if not target_files or not test_commands:
        raise ValueError("Strategist handoff requires receiving files and validation commands")
    for target in target_files:
        path = Path(target)
        if path.is_absolute() or ".." in path.parts or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", target):
            raise ValueError(f"handoff target must be repository-relative: {target}")
    return {
        "proposal_schema_version": "1.0.0", "proposal_type": "combat-empirical-to-strategist-review",
        "review_required": True, "automatic_changes": False, "finding_id": finding_id,
        "finding": finding,
        "receiving_changes": {"target_files": sorted(set(target_files)), "validation_commands": sorted(set(test_commands))},
        "excluded_inputs": ["local report files", "draft or disputed findings", "unreviewed candidates", "account identifiers"],
    }


def build_parser() -> argparse.ArgumentParser:
    root = repository_root_from_script()
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    measure = subparsers.add_parser("measure", help="Measure one enriched combat report")
    measure.add_argument("--analysis", type=Path, required=True)
    measure.add_argument("--definitions", type=Path, default=root / "data" / "combat_trial_definitions.json")
    measure.add_argument("--output", type=Path, required=True)
    measure.add_argument("--experiment")
    measure.add_argument("--variant")
    measure.add_argument("--question")
    aggregate = subparsers.add_parser("aggregate", help="Aggregate one or more combat measurements")
    aggregate.add_argument("--measurement", type=Path, action="append", required=True)
    aggregate.add_argument("--output", type=Path, required=True)
    aggregate.add_argument("--experiment")
    propose = subparsers.add_parser("propose", help="Create a draft empirical finding from an aggregate")
    propose.add_argument("--aggregate", type=Path, required=True)
    propose.add_argument("--trial", required=True)
    propose.add_argument("--output", type=Path, required=True)
    handoff = subparsers.add_parser("handoff", help="Create a gated Strategist proposal for an accepted empirical finding")
    handoff.add_argument("--findings", type=Path, default=root / "data" / "combat_empirical_findings.json")
    handoff.add_argument("--finding", required=True)
    handoff.add_argument("--target-file", action="append", required=True)
    handoff.add_argument("--test-command", action="append", required=True)
    handoff.add_argument("--confirm-reviewed-finding", action="store_true")
    handoff.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "measure":
        measurement = build_measurement(
            load_json(args.analysis), load_json(args.definitions), experiment_id=args.experiment,
            variant=args.variant, question=args.question,
        )
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=True)
        write_json(output / "combat-measurements.json", measurement)
        (output / "combat-measurements.md").write_text(render_measurement(measurement), encoding="utf-8")
        print(f"Combat measurements: {output / 'combat-measurements.json'}")
    elif args.command == "aggregate":
        model = aggregate_measurements([load_json(path) for path in args.measurement], args.experiment)
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=True)
        write_json(output / "combat-experiment.json", model)
        (output / "combat-experiment.md").write_text(render_aggregate(model), encoding="utf-8")
        print(f"Combat experiment: {output / 'combat-experiment.json'}")
    elif args.command == "propose":
        write_json(args.output.resolve(), draft_finding(load_json(args.aggregate), args.trial))
        print(f"Draft empirical finding: {args.output.resolve()}")
    elif args.command == "handoff":
        proposal = build_finding_handoff(
            args.finding, load_json(args.findings), args.target_file, args.test_command,
            args.confirm_reviewed_finding,
        )
        write_json(args.output.resolve(), proposal)
        print(f"Empirical Strategist proposal: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
