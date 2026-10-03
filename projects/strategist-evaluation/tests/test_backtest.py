from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("strategist_backtest", PROJECT / "backtest.py")
assert SPEC and SPEC.loader
BACKTEST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BACKTEST)


class StrategistBacktestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = BACKTEST.load_cases()

    def test_suite_has_three_blind_benchmarks_and_holdouts(self) -> None:
        cases = self.payload["cases"]
        benchmarks = [case for case in cases if case["kind"] == "benchmark"]
        holdouts = [case for case in cases if case["kind"] == "holdout"]
        self.assertEqual(len(benchmarks), 3)
        self.assertGreaterEqual(len(holdouts), 3)
        self.assertTrue(all(case.get("expected_formation") for case in benchmarks))
        self.assertTrue(all(any(check["critical"] for check in case["reasoning_checks"]) for case in cases))

    def test_markdown_formation_parser(self) -> None:
        response = """
### Recommended Formation

**Formation troop type:** **Shieldbearers**

| Position | Dragon | Current Power | Star rank | Habit skill levels | Job |
|---|---|---:|---:|---|---|
| Left Flank | Velar | unknown | 6 | 5/5/5 | damage |
| Vanguard | Vhagar | unknown | 6 | 5/5/5 | support |
| Right Flank | Moondancer | unknown | 6 | 5/5/5 | payoff |

### Strongest Credible Alternative

| Left Flank | Malachite | unknown | 6 | 5/5/5 | damage |
| Vanguard | Moondancer | unknown | 6 | 5/5/5 | support |
| Right Flank | Starshower | unknown | 6 | 5/5/5 | payoff |
"""
        self.assertEqual(BACKTEST.parse_formation(response), {
            "troop_type": "Shieldbearers",
            "left_flank": "Velar",
            "vanguard": "Vhagar",
            "right_flank": "Moondancer",
        })

    def test_grader_separates_formation_and_reasoning(self) -> None:
        case = {
            "id": "sample",
            "kind": "benchmark",
            "benchmark_id": "sample",
            "expected_formation": {
                "troop_type": "Cavalry",
                "left_flank": "A",
                "vanguard": "B",
                "right_flank": "C",
            },
            "reasoning_checks": [{
                "id": "logic",
                "label": "Logic",
                "critical": True,
                "all_patterns": ["explicit mechanic"],
            }],
        }
        response = """
**Formation troop type:** Cavalry
| Left Flank | A | unknown |
| Vanguard | B | unknown |
| Right Flank | C | unknown |
No evidence is given.
"""
        result = BACKTEST.grade_case(case, response)
        self.assertTrue(result["exact_formation_match"])
        self.assertFalse(result["critical_reasoning_pass"])
        self.assertFalse(result["passed"])

    def test_counter_troop_fallback_parser(self) -> None:
        response = """
### Recommended Formation
**Best-supported counter:** Cavalry, exploiting troop advantage.
| Left Flank | Tessarion | unknown |
| Vanguard | Malachite | unknown |
| Right Flank | Feskar | unknown |
"""
        self.assertEqual(BACKTEST.parse_formation(response)["troop_type"], "Cavalry")

    def test_repository_run_paths_are_portable(self) -> None:
        with tempfile.TemporaryDirectory(dir=BACKTEST.ROOT) as directory:
            response_dir = Path(directory)
            report = BACKTEST.grade_run([], response_dir)
        self.assertEqual(
            report["response_dir"],
            response_dir.resolve().relative_to(BACKTEST.ROOT).as_posix(),
        )


if __name__ == "__main__":
    unittest.main()
