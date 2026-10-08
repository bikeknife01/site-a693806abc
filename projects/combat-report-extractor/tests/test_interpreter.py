from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "projects" / "combat-report-extractor" / "combat_report_interpreter.py"
SPEC = importlib.util.spec_from_file_location("combat_report_interpreter", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)
FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class CombatReportInterpreterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = fixture("interpreter_synthetic.json")
        self.rules = fixture("rules_valid.json")
        self.observations = fixture("observations_valid.json")

    def model(self):
        return MODULE.build_analysis_model(self.report, self.rules, self.observations, ROOT)

    def test_exact_match_event_link_and_source_preservation(self) -> None:
        original = copy.deepcopy(self.report)
        model = self.model()
        self.assertEqual(1, len(model["links"]))
        link = model["links"][0]
        self.assertEqual("rule.vhagar.eclipse-cover-advantage.v1", link["rule_id"])
        self.assertEqual(0, link["round_offset"])
        result = next(event for event in model["events"] if event["event_id"] == link["result_event_id"])
        self.assertEqual("corroborated", result["annotations"][0]["confidence"])
        self.assertEqual(original, model["source_report"])
        self.assertEqual(original["actions"], [event["source_action"] for event in model["events"]])

    def test_owner_and_round_offset_bounds(self) -> None:
        self.rules["rules"][0]["match"]["owner_scope"] = "opponent"
        self.assertEqual([], self.model()["links"])
        self.rules = fixture("rules_valid.json")
        self.rules["rules"][0]["match"]["round_offset"] = {"minimum": 1, "maximum": 1}
        self.assertEqual([], self.model()["links"])

    def test_more_specific_rule_suppresses_broad_rule(self) -> None:
        broad = copy.deepcopy(self.rules["rules"][0])
        broad["id"] = "rule.vhagar.broad-advantage.v1"
        broad["source"]["ability"] = None
        broad["source"]["ability_type"] = None
        self.rules["rules"].append(broad)
        model = self.model()
        annotation = next(event for event in model["events"] if event["annotations"])["annotations"][0]
        self.assertEqual("rule.vhagar.eclipse-cover-advantage.v1", annotation["rule_id"])
        self.assertEqual(["rule.vhagar.broad-advantage.v1"], annotation["suppressed_rule_ids"])

    def test_equally_specific_rules_are_ambiguous(self) -> None:
        second = copy.deepcopy(self.rules["rules"][0])
        second["id"] = "rule.vhagar.eclipse-cover-advantage-alternative.v1"
        self.rules["rules"].append(second)
        model = self.model()
        self.assertEqual([], model["links"])
        self.assertEqual(1, len(model["ambiguous_matches"]))
        self.assertFalse(any(event["annotations"] for event in model["events"]))

    def test_disputed_and_deprecated_rules_do_not_interpret(self) -> None:
        disputed = self.rules["rules"][0]
        disputed["status"] = "disputed"
        disputed["interpretation"]["confidence"] = "disputed"
        counter = copy.deepcopy(self.observations["observations"][0])
        counter["id"] = "observation.synthetic-report.002"
        counter["disposition"] = "contradicts"
        self.observations["observations"].append(counter)
        disputed["evidence"]["contradicts"] = [counter["id"]]
        self.assertEqual([], self.model()["links"])

        self.rules = fixture("rules_valid.json")
        deprecated = self.rules["rules"][0]
        deprecated["status"] = "deprecated"
        deprecated["review"]["rationale"] = "Synthetic retirement."
        self.assertEqual([], self.model()["links"])

    def test_unmatched_events_are_retained(self) -> None:
        model = self.model()
        event_ids = {event["event_id"] for event in model["events"]}
        self.assertTrue(set(model["unmatched_events"]) < event_ids)
        unresolved = next(event for event in model["events"] if event["source_action"]["ability"] == "Unresolved Pulse")
        self.assertIn(unresolved["event_id"], model["unmatched_events"])

    def test_repeated_output_is_byte_identical_and_markdown_agrees(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            report_path = FIXTURES / "interpreter_synthetic.json"
            rules_path = FIXTURES / "rules_valid.json"
            observations_path = FIXTURES / "observations_valid.json"
            first = MODULE.interpret_paths(report_path, Path(first_dir), rules_path, observations_path, ROOT)
            second = MODULE.interpret_paths(report_path, Path(second_dir), rules_path, observations_path, ROOT)
            for key in ("enriched", "analysis", "markdown", "candidates"):
                self.assertEqual(first[key].read_bytes(), second[key].read_bytes(), key)
            enriched = json.loads(first["enriched"].read_text(encoding="utf-8"))
            markdown = first["markdown"].read_text(encoding="utf-8")
            annotation = next(event for event in enriched["events"] if event["annotations"])["annotations"][0]
            self.assertIn(annotation["rule_id"], markdown)
            self.assertIn(annotation["confidence"], markdown)
            user_damage = enriched["insights"]["by_owner"]["user"]["visible_parsed_damage_total"]
            self.assertIn(f"{user_damage:,} visible parsed damage", markdown)

    def test_unsupported_report_major_is_actionable(self) -> None:
        self.report["schema_version"] = "2.0.0"
        with self.assertRaisesRegex(ValueError, "unsupported combat-report schema"):
            self.model()

    def test_candidate_counts_reports_and_formations_independently(self) -> None:
        first = self.model()
        repeated_same_report = MODULE.discover_candidates([first, first], self.rules, self.observations, ROOT)
        candidate = next(
            item for item in repeated_same_report["candidates"]
            if item["pattern"]["result_phrase"] == "Unresolved Pulse remains visible."
        )
        self.assertEqual(2, candidate["counts"]["occurrences"])
        self.assertEqual(1, candidate["counts"]["distinct_reports"])
        self.assertEqual(1, candidate["counts"]["distinct_formations"])
        self.assertEqual("timing_correlation", candidate["proposed_relationship"])

        second_report = copy.deepcopy(self.report)
        second_report["source"]["sha256"] = "synthetic-second-report"
        for action in second_report["actions"]:
            if action["owner"] == "enemy":
                action["actor"] = "Arrax"
        second = MODULE.build_analysis_model(second_report, self.rules, self.observations, ROOT)
        varied = MODULE.discover_candidates([first, second], self.rules, self.observations, ROOT)
        candidate = next(
            item for item in varied["candidates"]
            if item["pattern"]["result_phrase"] == "Unresolved Pulse remains visible."
        )
        self.assertEqual(2, candidate["counts"]["distinct_reports"])
        self.assertEqual(2, candidate["counts"]["distinct_formations"])

    def test_candidate_preserves_alternatives_and_stable_fingerprint(self) -> None:
        first = MODULE.discover_candidates([self.model()], self.rules, self.observations, ROOT)
        second = MODULE.discover_candidates([self.model()], self.rules, self.observations, ROOT)
        self.assertEqual(MODULE.canonical_bytes(first), MODULE.canonical_bytes(second))
        candidate = next(
            item for item in first["candidates"]
            if item["pattern"]["result_phrase"] == "Protect for 2 rounds."
        )
        abilities = {item["ability"] for item in candidate["known_alternative_sources"]}
        self.assertIn("Bronze Fury", abilities)
        self.assertIn("Noble Sacrifice", abilities)
        self.assertEqual("Protect", candidate["pattern"]["normalized_result"])
        self.assertEqual("unresolved", candidate["proposed_relationship"])

    def test_counterevidence_is_a_review_candidate(self) -> None:
        counter = copy.deepcopy(self.observations["observations"][0])
        counter["id"] = "observation.synthetic-report.002"
        counter["disposition"] = "contradicts"
        self.observations["observations"].append(counter)
        self.rules["rules"][0]["evidence"]["contradicts"] = [counter["id"]]
        candidates = MODULE.discover_candidates([self.model()], self.rules, self.observations, ROOT)
        contradiction = next(item for item in candidates["candidates"] if item["contradictions"])
        self.assertEqual("rule.vhagar.eclipse-cover-advantage.v1", contradiction["contradictions"][0]["rule_id"])
        self.assertEqual("unresolved", contradiction["proposed_relationship"])

    def test_interpret_does_not_modify_canonical_stores_and_propose_is_draft(self) -> None:
        canonical_rules = ROOT / "data" / "combat_report_rules.json"
        canonical_observations = ROOT / "data" / "combat_report_observations.json"
        before = (canonical_rules.read_bytes(), canonical_observations.read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            paths = MODULE.interpret_paths(
                FIXTURES / "interpreter_synthetic.json", Path(directory),
                FIXTURES / "rules_valid.json", FIXTURES / "observations_valid.json", ROOT,
            )
            candidate_store = json.loads(paths["candidates"].read_text(encoding="utf-8"))
            candidate = next(
                item for item in candidate_store["candidates"]
                if item["pattern"]["result_phrase"] == "Unresolved Pulse remains visible."
            )
            fragment = MODULE.draft_candidate_fragment(candidate_store, candidate["candidate_id"])
            self.assertTrue(fragment["review_required"])
            self.assertEqual("draft", fragment["draft_rule"]["status"])
            self.assertIn(fragment["draft_rule"]["relationship"], {"timing_correlation", "unresolved"})
        self.assertEqual(before, (canonical_rules.read_bytes(), canonical_observations.read_bytes()))


if __name__ == "__main__":
    unittest.main()
