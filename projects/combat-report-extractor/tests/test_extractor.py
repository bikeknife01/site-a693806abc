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

    def test_owner_color_and_common_ocr_name_correction(self) -> None:
        self.assertEqual("enemy", MODULE.owner_from_bgr_pixels([[60, 50, 90], [65, 50, 95]]))
        self.assertEqual("user", MODULE.owner_from_bgr_pixels([[95, 50, 60], [90, 50, 65]]))
        self.assertEqual("unknown", MODULE.owner_from_bgr_pixels([[70, 50, 72], [72, 50, 70]]))
        self.assertEqual("Zivern", MODULE.canonicalize("Zivem", {"zivern": "Zivern"}))

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

    def test_deduplicates_a_card_revisited_later_in_the_same_round(self) -> None:
        manifest = json.loads((Path(__file__).parent / "fixtures" / "ocr_frames.json").read_text(encoding="utf-8"))
        manifest["frames"][1]["timestamp_seconds"] = 120.0
        report = MODULE.parse_ocr_manifest(manifest, ROOT)
        self.assertEqual(2, report["coverage"]["action_count"])

    def test_preserves_distinct_modifier_cards_from_the_same_ability(self) -> None:
        def line(text: str, y: int) -> dict[str, object]:
            return {
                "text": text,
                "confidence": 0.99,
                "box": [[600, y], [1600, y], [1600, y + 30], [600, y + 30]],
                "ownership": "user",
            }

        manifest = {
            "frames": [{
                "frame": "frame-000001.jpg",
                "timestamp_seconds": 1.5,
                "active_section": "ROUND 2",
                "lines": [
                    line("[Rhysarion] activates [Inspiring Melody] affecting [Vermithor] (Left Flank).", 100),
                    line("25.657% Initiative.", 140),
                    line("[Rhysarion] activates [Inspiring Melody] affecting [Vermithor] (Left Flank).", 260),
                    line("5% damage received.", 300),
                ],
            }],
        }
        report = MODULE.parse_ocr_manifest(manifest, ROOT)
        self.assertEqual(2, report["coverage"]["action_count"])
        self.assertEqual(
            [[{"percent": 25.657, "description": "Initiative"}],
             [{"percent": 5.0, "description": "damage received"}]],
            [action["modifiers"] for action in report["actions"]],
        )

    def test_attaches_mixed_color_detail_to_header_owner(self) -> None:
        manifest = {
            "frames": [{
                "frame": "frame-000001.jpg",
                "timestamp_seconds": 1.5,
                "active_section": "ROUND 4",
                "lines": [
                    {
                        "text": "[Commanding Champion] uses [Tactical Strike] to attack [Rhysarion] (Vanguard).",
                        "confidence": 0.99,
                        "box": [[600, 100], [1800, 100], [1800, 130], [600, 130]],
                        "ownership": "enemy",
                    },
                    {
                        "text": "Deals 15 Tactical Damage against [Rhysarion]. [Rhysarion] takes 15 losses (11734 remaining).",
                        "confidence": 0.99,
                        "box": [[600, 140], [1900, 140], [1900, 170], [600, 170]],
                        "ownership": "user",
                    },
                ],
            }],
        }
        report = MODULE.parse_ocr_manifest(manifest, ROOT)
        self.assertEqual(1, report["coverage"]["action_count"])
        self.assertEqual("enemy", report["actions"][0]["owner"])
        self.assertEqual({"amount": 15, "type": "Tactical"}, report["actions"][0]["damage"])

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

