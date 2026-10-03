from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class StrategistContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rules = json.loads((ROOT / "data" / "recommendation_rules.json").read_text(encoding="utf-8"))
        cls.app = json.loads((ROOT / "data" / "dragon_application_knowledge.json").read_text(encoding="utf-8"))
        cls.installed = json.loads((ROOT / "data" / "installed_evidence.json").read_text(encoding="utf-8"))
        cls.vermithor = json.loads((ROOT / "data" / "dragons" / "vermithor.json").read_text(encoding="utf-8"))
        cls.starshower = json.loads((ROOT / "data" / "dragons" / "starshower.json").read_text(encoding="utf-8"))
        cls.agent = (ROOT / ".github" / "agents" / "dragonfire-strategist.agent.md").read_text(encoding="utf-8")

    def test_hard_formation_constraints(self) -> None:
        hard = self.rules["hard_constraints"]
        self.assertEqual(hard["dragon_count"], 3)
        self.assertEqual(hard["positions"], ["left_flank", "vanguard", "right_flank"])
        self.assertEqual(hard["shared_troop_types"], 1)
        self.assertEqual(hard["named_lane_alignment"], {
            "left_flank": "left_flank", "vanguard": "vanguard", "right_flank": "right_flank"
        })
        self.assertEqual(hard["habit_star_gates"], [2, 4, 6, 8, 10])
        self.assertFalse(hard["installed_unverified_default_eligible"])

    def test_agent_uses_canonical_contract_and_current_evidence(self) -> None:
        self.assertIn("data/recommendation_rules.json", self.agent)
        self.assertIn("data/installed_evidence.json", self.agent)
        self.assertNotIn("data/live_updates.json", self.agent)
        self.assertIn("Do not stop at\n\tthe first plausible trio", self.agent)
        self.assertIn("Power cannot create missing counter coverage", self.agent)
        self.assertIn("tools: [read, search, web, execute]", self.agent)
        self.assertIn("projects/strategist-simulator/simulate.mjs", self.agent)
        self.assertIn("Never select a formation from", self.agent)

    def test_backtest_runner_grants_only_the_simulator_shell_stem(self) -> None:
        runner = (ROOT / "projects" / "strategist-evaluation" / "backtest.py").read_text(encoding="utf-8")
        self.assertIn("shell(node projects/strategist-simulator/simulate.mjs:*)", runner)
        self.assertNotIn('"--allow-tool=shell"', runner)

    def test_full_roster_search_is_objective_specific_and_benchmark_agnostic(self) -> None:
        search = self.rules["candidate_search"]
        self.assertIn("each non-Siege troop type", search["full_roster_ledger"])
        self.assertIn("every retained trio", search["lane_permutations"])
        self.assertIn("materially different objectives", search["cross_objective_check"])
        self.assertIn("Never seed, boost, or exempt", search["benchmark_safety"])
        self.assertEqual(
            set(self.rules["objective_profiles"]),
            {"high_damage", "damage_and_survivability", "counter"},
        )
        self.assertIn("internal candidate\n\tledger", self.agent)
        self.assertIn("do not let a broadly competent hybrid win every prompt", self.agent)
        shared_troops = next(item for item in self.rules["decision_flow"] if item["id"] == "shared_troops")
        self.assertIn("exact intersection", shared_troops["rule"])
        self.assertIn("exact intersection of the three canonical Positive", self.agent)

    def test_season_three_dragons_preserve_availability_and_evidence_limits(self) -> None:
        by_name = {item["name"]: item for item in self.app["dragons"]}
        for name in ("Meleys", "Smoketail"):
            with self.subTest(name=name):
                self.assertEqual(by_name[name]["recommendation_status"], "client_discovered")
                self.assertEqual(by_name[name]["availability_status"], "user_confirmed_available")
                self.assertNotIn("Release and availability confirmation", by_name[name]["recommendation_evidence"]["missing_for_full_recommendations"])

    def test_vermithor_is_screenshot_audited_with_resolved_six_star_values(self) -> None:
        by_name = {item["name"]: item for item in self.app["dragons"]}
        record = by_name["Vermithor"]
        self.assertEqual(record["recommendation_status"], "screenshot_audited")
        self.assertEqual(record["availability_status"], "screenshot_observed")
        self.assertEqual(record["recommendation_evidence"]["missing_for_full_recommendations"], [])
        bronze_bulwark = next(item for item in self.vermithor["habits"] if item["name"] == "Bronze Bulwark")
        level_five = bronze_bulwark["upgrade_levels"]["5"]
        self.assertEqual(level_five["physical_damage_rate_percent"], 45)
        self.assertEqual(level_five["tactical_damage_rate_percent"], 90)
        self.assertEqual(level_five["protect_chance_percent"], 50)
        self.assertEqual(level_five["physical_fire_damage_received_percent"], -10)

    def test_starshower_is_screenshot_audited_with_resolved_progression(self) -> None:
        by_name = {item["name"]: item for item in self.app["dragons"]}
        record = by_name["Starshower"]
        self.assertEqual(record["recommendation_status"], "screenshot_audited")
        self.assertEqual(record["availability_status"], "screenshot_observed")
        self.assertEqual(record["recommendation_evidence"]["missing_for_full_recommendations"], [])
        by_habit = {item["name"]: item for item in self.starshower["habits"]}
        self.assertEqual(by_habit["Night Guardian"]["upgrade_levels"]["5"], 30)
        self.assertEqual(by_habit["Ill Portents"]["upgrade_levels"]["5"], 200)
        self.assertEqual(by_habit["Wishkeeper's Grace"]["upgrade_levels"]["5"], -15)
        self.assertTrue(any("Damage Dealt" in item for item in self.starshower["review"]))

    def test_curated_installed_evidence_has_explicit_usage(self) -> None:
        allowed_states = set(self.installed["evidence_states"])
        allowed_uses = {"conditional_only", "exclude", "corroboration_only"}
        ids = set()
        for item in self.installed["observations"]:
            self.assertNotIn(item["id"], ids)
            ids.add(item["id"])
            self.assertIn(item["evidence_state"], allowed_states)
            self.assertIn(item["recommendation_use"], allowed_uses)

    def test_benchmark_files_have_required_shape(self) -> None:
        benchmark_dir = ROOT / "projects" / "strategist-evaluation" / "benchmarks"
        records = []
        for path in benchmark_dir.glob("*.json") if benchmark_dir.exists() else []:
            record = json.loads(path.read_text(encoding="utf-8"))
            records.append(record)
            for field in ("benchmark_id", "objective", "our_formation", "opponent", "runs", "variations"):
                self.assertIn(field, record, f"{path}: {field}")
            self.assertEqual(set(record["our_formation"]), {"troop_type", "left_flank", "vanguard", "right_flank"})
            self.assertIn("baseline", record["runs"])
            self.assertTrue(record["variations"])
            for lane in ("left_flank", "vanguard", "right_flank"):
                self.assertEqual(record["our_formation"][lane]["star_rank"], 6)
                self.assertEqual(record["our_formation"][lane]["level"], 50)
                self.assertEqual(record["our_formation"][lane]["habit_levels"][:3], [5, 5, 5])
        self.assertEqual(
            {record["benchmark_id"] for record in records},
            {
                "velar-vhagar-moondancer-shieldbearers",
                "vermithor-rhysarion-venator-spearmen",
                "malachite-seasmoke-kalspire-cavalry-counter",
            },
        )


if __name__ == "__main__":
    unittest.main()
