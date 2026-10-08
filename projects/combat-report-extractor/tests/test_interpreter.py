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

    def test_candidate_correlates_actor_alias_to_canonical_formation_ability(self) -> None:
        report = copy.deepcopy(self.report)
        report["source"]["sha256"] = "synthetic-canonical-clue"
        report["actions"] = [{
            "round": 1, "section": "ROUND 1", "owner": "enemy", "kind": "affect",
            "actor": "Persistent Hunter", "ability": "Bloodscale Terror", "target": "Vhagar",
            "target_lane": "Vanguard", "damage": None, "losses": None, "remaining": None,
            "recovery": None, "modifiers": [],
            "evidence": {
                "timestamp_seconds": 1.0, "frame": "synthetic-clue.jpg", "ocr_confidence": 1.0,
                "head_text": "[Persistent Hunter] activates [Bloodscale Terror] affecting [Vhagar].",
                "detail_text": "Stun applied. Lasts for 2 rounds.",
            },
        }]
        report["coverage"].update({"rounds_with_actions": [1], "action_count": 1})
        model = MODULE.build_analysis_model(report, self.rules, self.observations, ROOT)
        candidates = MODULE.discover_candidates([model], self.rules, self.observations, ROOT)
        clue = candidates["candidates"][0]["canonical_source_clues"][0]
        self.assertEqual(("Persistent Hunter", "Crimson", "Bloodscale Terror"), (
            clue["report_actor"], clue["canonical_dragon"], clue["canonical_ability"],
        ))
        self.assertTrue(any("Stun" in text for item in clue["canonical_text"] for text in item["verbatim"]))
        enemy = candidates["formation_contexts"][0]["owners"]["enemy"][0]
        self.assertEqual(["Crimson"], enemy["canonical_dragon_clues"])

    def test_unique_canonical_ability_owner_can_match_an_actor_alias(self) -> None:
        rule = copy.deepcopy(self.rules["rules"][0])
        rule["source"] = {"dragon": "Crimson", "ability": "Bloodscale Terror", "ability_type": "command"}
        action = {"actor": "Persistent Hunter", "ability": "Bloodscale Terror", "kind": "affect"}
        owners = MODULE.canonical_ability_owners(MODULE.load_canonical_ability_catalog(ROOT))
        self.assertTrue(MODULE.source_matches(rule, action, owners))
        action["ability"] = "Basic Attack"
        self.assertFalse(MODULE.source_matches(rule, action, owners))

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

    def test_canonical_explicit_rule_links_one_card_to_itself(self) -> None:
        report = {
            "schema_version": "1.0.0",
            "source": {"path": "synthetic.mp4", "sha256": "synthetic-explicit"},
            "ownership_rule": {"blue": "user", "red": "enemy", "authority": "user-supplied"},
            "coverage": {"rounds_with_actions": [6], "action_count": 1, "rejected_action_count": 0, "warnings": []},
            "actions": [{
                "round": 6, "section": "ROUND 6", "owner": "user", "kind": "affect",
                "actor": "Velar", "ability": "Gales of Power", "target": "Moondancer", "target_lane": "Right Flank",
                "damage": None, "losses": None, "remaining": None, "recovery": None, "modifiers": [],
                "evidence": {"timestamp_seconds": 12.0, "frame": "synthetic.jpg", "ocr_confidence": 1.0,
                             "head_text": "[Velar] activates [Gales of Power] affecting [Moondancer].",
                             "detail_text": "First-Strikestatus applied."},
            }],
            "rejected_actions": [],
        }
        rules = json.loads((ROOT / "data" / "combat_report_rules.json").read_text(encoding="utf-8"))
        observations = json.loads((ROOT / "data" / "combat_report_observations.json").read_text(encoding="utf-8"))
        model = MODULE.build_analysis_model(report, rules, observations, ROOT)
        self.assertEqual(1, len(model["links"]))
        self.assertEqual(model["links"][0]["source_event_id"], model["links"][0]["result_event_id"])
        annotation = model["events"][0]["annotations"][0]
        self.assertEqual("observed", annotation["provenance"])
        self.assertEqual("corroborated", annotation["confidence"])

        empty_rules = {"metadata": {"schema_version": "1.0.0", "updated": "2026-10-08", "purpose": "Test"}, "rules": []}
        empty_observations = {"metadata": {"schema_version": "1.0.0", "updated": "2026-10-08"}, "observations": []}
        unmatched = MODULE.build_analysis_model(report, empty_rules, empty_observations, ROOT)
        candidate = MODULE.discover_candidates([unmatched], empty_rules, empty_observations, ROOT)["candidates"][0]
        self.assertEqual("First-Strike", candidate["pattern"]["normalized_result"])

    def test_every_accepted_rule_matches_reviewed_evidence_and_rejects_changed_result(self) -> None:
        rules = json.loads((ROOT / "data" / "combat_report_rules.json").read_text(encoding="utf-8"))
        observations = json.loads(
            (ROOT / "data" / "combat_report_observations.json").read_text(encoding="utf-8")
        )
        observations_by_id = {item["id"]: item for item in observations["observations"]}

        for rule in (item for item in rules["rules"] if item["status"] == "accepted"):
            with self.subTest(rule=rule["id"]):
                observation = observations_by_id[rule["evidence"]["supports"][0]]
                action = {
                    "round": observation["location"]["round"],
                    "section": f"ROUND {observation['location']['round']}",
                    "owner": observation["normalized"]["owner"],
                    "kind": rule["match"]["event_kind"],
                    "actor": observation["normalized"]["actor"],
                    "ability": observation["normalized"]["ability"],
                    "target": None,
                    "target_lane": None,
                    "damage": None,
                    "losses": None,
                    "remaining": None,
                    "recovery": None,
                    "modifiers": [],
                    "evidence": {
                        "timestamp_seconds": observation["location"]["timestamp_seconds"],
                        "frame": observation["location"]["frame_basename"],
                        "ocr_confidence": 1.0,
                        "head_text": observation["verbatim"]["head_text"],
                        "detail_text": observation["verbatim"]["detail_text"],
                    },
                }
                report = {
                    "schema_version": "1.0.0",
                    "source": {"path": "synthetic.mp4", "sha256": f"synthetic-{rule['id']}"},
                    "ownership_rule": {"blue": "user", "red": "enemy", "authority": "user-supplied"},
                    "coverage": {
                        "rounds_with_actions": [action["round"]], "action_count": 1,
                        "rejected_action_count": 0, "warnings": [],
                    },
                    "actions": [action],
                    "rejected_actions": [],
                }
                if rule["relationship"] not in {"explicit", "ui_alias"}:
                    source_action = copy.deepcopy(action)
                    source_action["round"] = max(1, action["round"] - rule["match"]["round_offset"]["maximum"])
                    source_action["section"] = f"ROUND {source_action['round']}"
                    source_action["actor"] = rule["source"]["dragon"]
                    source_action["ability"] = rule["source"]["ability"]
                    source_action["evidence"]["head_text"] = (
                        f"[{rule['source']['dragon']}] activates [{rule['source']['ability']}]."
                    )
                    source_action["evidence"]["detail_text"] = ""
                    report["actions"] = [source_action, action]
                    report["coverage"]["rounds_with_actions"] = sorted({source_action["round"], action["round"]})
                    report["coverage"]["action_count"] = 2
                model = MODULE.build_analysis_model(report, rules, observations, ROOT)
                self.assertEqual([rule["id"]], [item["rule_id"] for item in model["links"]])

                changed = copy.deepcopy(report)
                changed["actions"][-1]["evidence"]["detail_text"] = "Different result wording."
                changed_model = MODULE.build_analysis_model(changed, rules, observations, ROOT)
                self.assertNotIn(rule["id"], [item["rule_id"] for item in changed_model["links"]])

    def test_strategist_handoff_is_proposal_only_and_gated(self) -> None:
        rules = json.loads((ROOT / "data" / "combat_report_rules.json").read_text(encoding="utf-8"))
        observations = json.loads((ROOT / "data" / "combat_report_observations.json").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "durable-mechanic confirmation"):
            MODULE.build_strategist_handoff(
                "rule.velar.gales-of-power.first-strike.v1", rules, observations, ROOT,
                ["data/effects.json"], ["python -m unittest"], False,
            )
        with self.assertRaisesRegex(ValueError, "repository-relative"):
            MODULE.build_strategist_handoff(
                "rule.velar.gales-of-power.first-strike.v1", rules, observations, ROOT,
                ["C:\\private\\effects.json"], ["python -m unittest"], True,
            )
        proposal = MODULE.build_strategist_handoff(
            "rule.velar.gales-of-power.first-strike.v1", rules, observations, ROOT,
            ["data/effects.json"],
            ["python -m unittest discover -s projects/combat-report-extractor/tests -v"], True,
        )
        self.assertTrue(proposal["review_required"])
        self.assertFalse(proposal["automatic_changes"])
        self.assertEqual("habits[2].verbatim", proposal["finding"]["canonical_ability"]["field"])
        self.assertIn("generated local report results", proposal["excluded_inputs"])
        self.assertEqual(2, len(proposal["evidence"]["supports"]))

        draft_rules = copy.deepcopy(rules)
        draft_rules["rules"][0]["status"] = "draft"
        with self.assertRaisesRegex(ValueError, "accepted, corroborated"):
            MODULE.build_strategist_handoff(
                "rule.velar.gales-of-power.first-strike.v1", draft_rules, observations, ROOT,
                ["data/effects.json"], ["python -m unittest"], True,
            )


if __name__ == "__main__":
    unittest.main()
