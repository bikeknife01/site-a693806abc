from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "projects" / "combat-report-extractor" / "ingest_combat_report.py"
SPEC = importlib.util.spec_from_file_location("ingest_combat_report", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class CombatReportIngestTests(unittest.TestCase):
    def test_output_directory_is_deterministic_and_ignored(self) -> None:
        output = MODULE.output_directory(
            ROOT, Path("GOT Dragonfire (4).mp4"), "abcdef0123456789", date(2026, 10, 8),
        )
        self.assertEqual(
            ROOT / "Game_Details" / "Resources" / "_snapshots" / "2026-10-08"
            / "analysis" / "combat-report-got-dragonfire-4-abcdef01" / "extractor-run",
            output,
        )

    def test_retained_ocr_must_match_exact_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "ocr_frames.json"
            manifest.write_text(json.dumps({"source": {"sha256": "expected"}}), encoding="utf-8")
            self.assertTrue(MODULE.retained_ocr_matches(manifest, "expected"))
            self.assertFalse(MODULE.retained_ocr_matches(manifest, "different"))

    def test_finds_existing_manual_run_by_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = (
                root / "Game_Details" / "Resources" / "_snapshots" / "2026-10-08"
                / "analysis" / "manual-name" / "extractor-run-v3"
            )
            run.mkdir(parents=True)
            manifest = run / "ocr_frames.json"
            manifest.write_text(json.dumps({"source": {"sha256": "expected"}}), encoding="utf-8")
            self.assertEqual(
                manifest, MODULE.find_retained_ocr(root, "expected"),
            )
            self.assertIsNone(MODULE.find_retained_ocr(root, "different"))

    def test_root_powershell_entry_point_exists(self) -> None:
        script = ROOT / "ingest-combat-report.ps1"
        self.assertTrue(script.is_file())
        self.assertIn("ingest_combat_report.py", script.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
