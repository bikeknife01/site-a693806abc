from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class CombatAnalystDocumentationTests(unittest.TestCase):
    def test_required_entry_points_exist(self) -> None:
        for relative in (
            ".github/agents/dragonfire-combat-analyst.agent.md",
            "wiki/Combat-Report-Interpretation.md",
            "data/combat_report_rules.json",
            "data/combat_report_observations.json",
            "projects/combat-report-extractor/docs/CANDIDATE_REVIEW.md",
            "projects/combat-report-extractor/docs/STRATEGIST_HANDOFF.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_agent_uses_machine_data_and_evidence_classes(self) -> None:
        text = (ROOT / ".github/agents/dragonfire-combat-analyst.agent.md").read_text(encoding="utf-8")
        self.assertIn("data/combat_report_rules.json", text)
        self.assertIn("data/combat_report_observations.json", text)
        for label in ("Observed", "Derived", "Inferred", "Unknown"):
            self.assertIn(label, text)
        self.assertIn("Never auto-promote", text)

    def test_wiki_does_not_invent_rule_ids(self) -> None:
        wiki = (ROOT / "wiki/Combat-Report-Interpretation.md").read_text(encoding="utf-8")
        rules = json.loads((ROOT / "data/combat_report_rules.json").read_text(encoding="utf-8"))
        documented = set(re.findall(r"`(rule\.[a-z0-9.-]+\.v\d+)`", wiki))
        canonical = {rule["id"] for rule in rules["rules"]}
        self.assertLessEqual(documented, canonical)


if __name__ == "__main__":
    unittest.main()
