from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "projects" / "combat-report-extractor" / "validate_combat_report_rules.py"
SPEC = importlib.util.spec_from_file_location("validate_combat_report_rules", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)
FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class CombatReportRuleValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rules = fixture("rules_valid.json")
        self.observations = fixture("observations_valid.json")

    def validate(self):
        return MODULE.validate_stores(self.rules, self.observations, ROOT)

    def test_valid_minimal_stores(self) -> None:
        self.assertEqual([], self.validate())
        self.assertEqual([], MODULE.validate_stores(
            {"metadata": {"schema_version": "1.0.0", "updated": "2026-10-08", "purpose": "Empty"}, "rules": []},
            {"metadata": {"schema_version": "1.0.0", "updated": "2026-10-08"}, "observations": []}, ROOT,
        ))

    def test_controlled_enums_are_rejected(self) -> None:
        paths = [
            ("status", "invalid"), ("relationship", "causal"),
        ]
        for key, value in paths:
            with self.subTest(key=key):
                rules = copy.deepcopy(self.rules)
                rules["rules"][0][key] = value
                errors = MODULE.validate_stores(rules, self.observations, ROOT)
                self.assertTrue(any("invalid enum value" in error for error in errors), errors)
        for section, key, value in [
            ("source", "ability_type", "spell"), ("match", "owner_scope", "nearby"),
            ("interpretation", "provenance", "guessed"), ("interpretation", "confidence", "likely"),
        ]:
            with self.subTest(key=key):
                rules = copy.deepcopy(self.rules)
                rules["rules"][0][section][key] = value
                errors = MODULE.validate_stores(rules, self.observations, ROOT)
                self.assertTrue(any("invalid enum value" in error for error in errors), errors)
        observations = copy.deepcopy(self.observations)
        observations["observations"][0]["quality"]["visual_review"] = "maybe"
        self.assertTrue(any("invalid enum value" in error for error in MODULE.validate_stores(self.rules, observations, ROOT)))

    def test_duplicate_and_dangling_ids(self) -> None:
        self.rules["rules"].append(copy.deepcopy(self.rules["rules"][0]))
        self.assertIn("duplicate rule ID", "\n".join(self.validate()))
        self.rules = fixture("rules_valid.json")
        self.rules["rules"][0]["evidence"]["supports"] = ["observation.missing.001"]
        self.assertIn("dangling supports observation", "\n".join(self.validate()))

    def test_invalid_canonical_names(self) -> None:
        self.rules["rules"][0]["source"]["dragon"] = "Not A Dragon"
        self.assertIn("unknown canonical dragon", "\n".join(self.validate()))
        self.rules = fixture("rules_valid.json")
        self.rules["rules"][0]["source"]["ability"] = "Not An Ability"
        self.assertIn("unknown canonical ability", "\n".join(self.validate()))

    def test_inferred_rule_requires_limitations(self) -> None:
        self.rules["rules"][0]["limitations"] = []
        self.assertIn("requires at least one limitation", "\n".join(self.validate()))

    def test_unsafe_evidence_path_and_account_identifier(self) -> None:
        self.observations["observations"][0]["location"]["frame_basename"] = "C:\\private\\frame.jpg"
        self.assertIn("absolute local path", "\n".join(self.validate()))
        self.observations = fixture("observations_valid.json")
        self.observations["observations"][0]["quality"]["notes"] = ["player_id=123"]
        self.assertIn("account identifier", "\n".join(self.validate()))

    def test_disputed_rule_requires_counterevidence(self) -> None:
        rule = self.rules["rules"][0]
        rule["status"] = "disputed"
        rule["interpretation"]["confidence"] = "disputed"
        self.assertIn("disputed rule requires counterevidence", "\n".join(self.validate()))

    def test_timing_correlation_rejects_causal_wording(self) -> None:
        rule = self.rules["rules"][0]
        rule["relationship"] = "timing_correlation"
        rule["interpretation"]["summary"] = "Eclipse Cover causes Advantage."
        self.assertIn("uses causal wording", "\n".join(self.validate()))


if __name__ == "__main__":
    unittest.main()
