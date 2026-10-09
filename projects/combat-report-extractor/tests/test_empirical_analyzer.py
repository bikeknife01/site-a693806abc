from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "projects" / "combat-report-extractor" / "combat_empirical_analyzer.py"
SPEC = importlib.util.spec_from_file_location("combat_empirical_analyzer", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)

VALIDATOR_PATH = ROOT / "projects" / "combat-report-extractor" / "validate_combat_report_rules.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("combat_validator_empirical", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)


def action(round_number: int, ability: str, timestamp: float, *, damage: int | None = None) -> dict:
    return {
        "round": round_number, "section": f"ROUND {round_number}", "owner": "user",
        "kind": "self_effect" if ability == "Skyward Titan" else "attack",
        "actor": "Vhagar", "ability": ability, "target": "Vhagar" if ability == "Skyward Titan" else "Enemy",
        "target_lane": "Vanguard", "damage": {"amount": damage, "type": "Physical"} if damage else None,
        "losses": damage, "remaining": None, "recovery": None, "modifiers": [],
        "evidence": {"timestamp_seconds": timestamp, "frame": f"synthetic-{timestamp}.jpg", "ocr_confidence": 1.0,
                     "head_text": f"[Vhagar] activates [{ability}].", "detail_text": "5% Strength."},
    }


class CombatEmpiricalAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analysis = {
            "analysis_schema_version": "1.0.0", "tool_version": "test",
            "input_report_hash": "a" * 64, "rule_set_hash": "b" * 64,
            "coverage": {"rounds_with_actions": [1, 2], "warnings": [], "rejected_action_count": 0},
            "events": [
                {"event_id": "event.1", "source_action": action(1, "Skyward Titan", 1.0), "annotations": []},
                {"event_id": "event.2", "source_action": action(1, "Skyward Titan", 1.1), "annotations": []},
                {"event_id": "event.3", "source_action": action(1, "Basic Attack", 2.0, damage=100), "annotations": []},
                {"event_id": "event.4", "source_action": action(2, "Basic Attack", 3.0, damage=120), "annotations": []},
            ],
            "links": [
                {"rule_id": "rule.strength", "source_event_id": "event.1", "result_event_id": "event.1"},
                {"rule_id": "rule.mitigation", "source_event_id": "event.1", "result_event_id": "event.2"},
            ],
        }
        self.definitions = {
            "metadata": {"schema_version": "1.0.0", "updated": "2026-10-08", "purpose": "test"},
            "trials": [{
                "id": "trial.vhagar.skyward.v1", "status": "accepted",
                "source": {"dragon": "Vhagar", "ability": "Skyward Titan", "ability_type": "habit"},
                "trigger": {"schedule": "each_round", "rounds": [], "advertised_chance_percent": 30,
                            "canonical_source": "data/dragons/vhagar.json -> habits[4].verbatim"},
                "success_rule_ids": ["rule.strength", "rule.mitigation"],
                "opportunity": {"requires_actor_action_in_round": True, "requires_complete_coverage": True},
                "activation": {"stack_gain": 1, "max_stacks": 5, "persists_until_end": True},
                "limitations": ["test limitation"],
            }],
        }

    def test_groups_multiple_effect_cards_into_one_activation(self) -> None:
        measurement = MODULE.build_measurement(
            self.analysis, self.definitions, experiment_id="iron-13", variant="baseline",
        )
        trial = measurement["trials"][0]
        self.assertEqual(1, trial["activation_count"])
        self.assertEqual([1, 2], trial["eligible_opportunity_rounds"])
        self.assertEqual([], trial["unknown_opportunity_rounds"])
        self.assertTrue(trial["rate_reportable"])
        self.assertEqual(0.5, trial["observable_rate"])
        self.assertEqual(1, measurement["exposures"][0]["inferred_stack_after"])
        self.assertEqual(
            [{"trial_id": "trial.vhagar.skyward.v1", "stack_count": 1}],
            measurement["outcome_samples"][0]["active_exposures"],
        )

    def test_withholds_complete_rate_when_opportunity_is_unknown(self) -> None:
        self.analysis["events"] = self.analysis["events"][:3]
        measurement = MODULE.build_measurement(self.analysis, self.definitions)
        trial = measurement["trials"][0]
        self.assertFalse(trial["rate_reportable"])
        self.assertEqual([2], trial["unknown_opportunity_rounds"])
        self.assertIn("source actor remained active", trial["rate_limitation"])

    def test_aggregate_and_draft_preserve_denominator_limits(self) -> None:
        first = MODULE.build_measurement(self.analysis, self.definitions, experiment_id="iron-13", variant="baseline")
        second_analysis = copy.deepcopy(self.analysis)
        second_analysis["input_report_hash"] = "c" * 64
        second = MODULE.build_measurement(second_analysis, self.definitions, experiment_id="iron-13", variant="swap")
        aggregate = MODULE.aggregate_measurements([first, second])
        trial = aggregate["trials"][0]
        self.assertEqual((2, 4), (trial["activations"], trial["observable_opportunities"]))
        self.assertEqual(2, trial["distinct_reports"])
        self.assertIsNotNone(trial["interval_95"])
        self.assertEqual(["b" * 64], aggregate["rule_set_hashes"])
        draft = MODULE.draft_finding(aggregate, trial["trial_id"])["draft_finding"]
        self.assertEqual("draft", draft["status"])
        self.assertFalse(draft["recommendation"]["eligible"])
        self.assertEqual(aggregate["input_report_hashes"], draft["evidence"]["report_hashes"])

    def test_strategist_handoff_requires_accepted_reviewed_finding(self) -> None:
        finding = {
            "id": "finding.vhagar.skyward.proc.v1", "status": "accepted", "metric_type": "proc_rate",
            "source": {"dragon": "Vhagar", "ability": "Skyward Titan", "trial_id": "trial.vhagar.skyward.v1"},
            "scope": {"battle_type": "pve", "enemy": "Level 13 Iron", "formation_constraints": [], "progression_constraints": []},
            "estimate": {"numerator": 9, "denominator": 24, "rate": 0.375, "interval_95": [0.2, 0.57], "unit": "activation per observable opportunity"},
            "evidence": {"report_hashes": ["a" * 64], "observation_ids": ["observation.test.001"],
                         "contradicting_observation_ids": [], "distinct_reports": 1},
            "interpretation": {"summary": "Reviewed sample.", "provenance": "derived", "confidence": "corroborated"},
            "limitations": ["PvE scope only."],
            "recommendation": {"eligible": True, "use": "reliability", "rationale": "Reviewed aggregate."},
            "review": {"created": "2026-10-08", "last_reviewed": "2026-10-08", "strategist_gate": "approved"},
        }
        store = {"metadata": {"schema_version": "1.0.0", "updated": "2026-10-08", "purpose": "test"}, "findings": [finding]}
        with self.assertRaisesRegex(ValueError, "explicit empirical-finding confirmation"):
            MODULE.build_finding_handoff(finding["id"], store, ["data/recommendation_rules.json"], ["python -m unittest"], False)
        proposal = MODULE.build_finding_handoff(
            finding["id"], store, ["data/recommendation_rules.json"], ["python -m unittest"], True,
        )
        self.assertFalse(proposal["automatic_changes"])
        self.assertIn("local report files", proposal["excluded_inputs"])

    def test_canonical_empirical_stores_validate(self) -> None:
        rules = json.loads((ROOT / "data" / "combat_report_rules.json").read_text(encoding="utf-8"))
        observations = json.loads((ROOT / "data" / "combat_report_observations.json").read_text(encoding="utf-8"))
        definitions = json.loads((ROOT / "data" / "combat_trial_definitions.json").read_text(encoding="utf-8"))
        findings = json.loads((ROOT / "data" / "combat_empirical_findings.json").read_text(encoding="utf-8"))
        self.assertEqual([], VALIDATOR.validate_empirical_stores(definitions, findings, rules, observations, ROOT))

        invalid = copy.deepcopy(definitions)
        invalid["trials"][0]["success_rule_ids"] = ["rule.missing.v1"]
        errors = VALIDATOR.validate_empirical_stores(invalid, findings, rules, observations, ROOT)
        self.assertIn("dangling success rule", "\n".join(errors))

        invalid = copy.deepcopy(definitions)
        invalid["trials"][0]["trigger"]["schedule"] = "whenever"
        errors = VALIDATOR.validate_empirical_stores(invalid, findings, rules, observations, ROOT)
        self.assertIn("invalid enum value", "\n".join(errors))

    def test_measurement_and_markdown_are_deterministic(self) -> None:
        first = MODULE.build_measurement(self.analysis, self.definitions)
        second = MODULE.build_measurement(self.analysis, self.definitions)
        self.assertEqual(MODULE.canonical_bytes(first), MODULE.canonical_bytes(second))
        self.assertIn(self.analysis["input_report_hash"], MODULE.render_measurement(first))


if __name__ == "__main__":
    unittest.main()
