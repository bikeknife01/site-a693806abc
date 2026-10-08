from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "projects" / "combat-report-extractor" / "combat_report_extractor.py"
SPEC = importlib.util.spec_from_file_location("combat_report_extractor", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class CombatReportExtractorTests(unittest.TestCase):
    def test_parses_supported_action_shapes(self) -> None:
        attack = MODULE.parse_action_head("[Vhagar]uses[BasicAttack]to attack[Rhysarion](Vanguard).")
        self.assertEqual("attack", attack["kind"])
        self.assertEqual("BasicAttack", attack["ability"])
        self.assertEqual("Rhysarion", attack["target"])
        self.assertEqual("Vanguard", attack["lane"])
        effect = MODULE.parse_action_head("[Vhagar] activates [Eclipse Cover] affecting [Vermithor] (Left Flank).")
        self.assertEqual("affect", effect["kind"])
        self.assertEqual("EclipseCover", effect["ability"])
        self.assertIsNone(
            MODULE.parse_action_head(
                "[Vermithor] is under the effect of [Noble Sacrifice] from itself."
            )
        )

    def test_manifest_parser_normalizes_and_deduplicates(self) -> None:
        manifest = json.loads((Path(__file__).parent / "fixtures" / "ocr_frames.json").read_text(encoding="utf-8"))
        report = MODULE.parse_ocr_manifest(manifest, ROOT)
        self.assertEqual(2, report["coverage"]["action_count"])
        user = next(action for action in report["actions"] if action["owner"] == "user")
        enemy = next(action for action in report["actions"] if action["owner"] == "enemy")
        self.assertEqual("Basic Attack", user["ability"])
        self.assertEqual({"amount": 396, "type": "Physical"}, user["damage"])
        self.assertEqual(8842, user["remaining"])
        self.assertEqual("Vermithor", enemy["actor"])
        self.assertEqual(177, enemy["losses"])
        self.assertFalse(any(action["kind"] == "attack" and not action["damage"] for action in report["actions"]))

    def test_insights_separate_user_and_enemy(self) -> None:
        manifest = json.loads((Path(__file__).parent / "fixtures" / "ocr_frames.json").read_text(encoding="utf-8"))
        report = MODULE.parse_ocr_manifest(manifest, ROOT)
        insights = MODULE.aggregate_insights(report)
        self.assertEqual(396, insights["by_owner"]["user"]["visible_damage_total"])
        self.assertEqual(177, insights["by_owner"]["enemy"]["visible_damage_total"])
        rendered = MODULE.render_insights(report)
        self.assertIn("User / blue", rendered)
        self.assertIn("Enemy / red", rendered)
        self.assertIn("R3 user: Vhagar", rendered)
        self.assertIn("Parsed blue damage is", rendered)


if __name__ == "__main__":
    unittest.main()

