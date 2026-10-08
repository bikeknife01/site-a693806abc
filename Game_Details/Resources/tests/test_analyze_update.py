import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path


RESOURCES = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESOURCES))
from analyze_update import analyze, logical_name, resource_impacts  # noqa: E402


class AnalyzeUpdateTests(unittest.TestCase):
    def test_logical_name_replaces_only_content_version(self):
        self.assertEqual(logical_name("dragonTable_merged.1789415363.pb"), "dragonTable_merged.VERSION.pb")
        self.assertEqual(logical_name("ordinary.pb"), "ordinary.pb")

    def test_impact_routing_maps_combat_and_localization_consumers(self):
        result = resource_impacts(["dragonHabitsTable_merged.VERSION.pb", "Deltas_enUS.VERSION.txt"])
        self.assertIn("dragon_combat", result["domains"])
        self.assertIn("localization", result["domains"])
        self.assertIn("projects/recommendation-planner", result["domains"]["dragon_combat"]["consumers"])

    def test_analysis_distinguishes_content_changes_and_version_only_renames(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old, new, output = root / "old", root / "new", root / "out"
            old.mkdir()
            new.mkdir()
            (old / "dragonHabitsTable_merged.1111111111.json").write_text("old", encoding="utf-8")
            (new / "dragonHabitsTable_merged.2222222222.json").write_text("new", encoding="utf-8")
            (old / "same.1111111111.json").write_text("same", encoding="utf-8")
            (new / "same.2222222222.json").write_text("same", encoding="utf-8")
            args = argparse.Namespace(
                old=str(old), new=str(new), output=str(output), snapshot_date="2026-10-03",
                old_client_version="old", new_client_version="new", old_version_code="1", new_version_code="2",
                capture_scope="test fixture", skip_decode=True,
            )
            result = analyze(args)
            self.assertEqual(len(result["manifest"]["changed"]), 1)
            self.assertEqual(len(result["manifest"]["version_only"]), 1)
            self.assertIn("dragon_combat", result["impacts"]["domains"])
            report = (output / "analysis" / "update_report.md").read_text(encoding="utf-8")
            self.assertIn("does not prove release status", report)
            saved = json.loads((output / "analysis" / "impact_report.json").read_text(encoding="utf-8"))
            self.assertIn("projects/recommendation-planner", saved["domains"]["dragon_combat"]["consumers"])


if __name__ == "__main__":
    unittest.main()

