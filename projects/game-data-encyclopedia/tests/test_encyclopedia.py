from __future__ import annotations

import importlib.util
import json
import re
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BUILDER_PATH = ROOT / "projects" / "shared-data-foundation" / "src" / "normalize" / "build_encyclopedia_data.py"
SPEC = importlib.util.spec_from_file_location("build_encyclopedia_data", BUILDER_PATH)
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(BUILDER)


def normalize(value: str) -> list[str]:
    replacements = {"cleanses": "cleanse", "cleaned": "cleanse", "targets": "target", "effects": "effect", "rounds": "round"}
    words = re.sub(r"[^a-z0-9]+", " ", value.lower()).split()
    return [replacements.get(word, word[:-1] if len(word) > 4 and word.endswith("s") else word) for word in words]


def search_text(dragon: dict) -> str:
    affinities = [part for item in dragon["troop_affinities"].get("positive", []) for part in (item, f"{item} affinity")]
    abilities = [part for ability in dragon["abilities"] for part in [ability["name"], *ability["exact_text"], *ability["normalized"]["target_hints"]]]
    return " ".join([dragon["name"], dragon["breed"], dragon.get("rarity_tier") or "", *dragon["traits"], *affinities, *abilities])


def matches(haystack: str, query: str) -> bool:
    hay_tokens = normalize(haystack)
    query_tokens = normalize(query)
    if sum(token.isdigit() for token in query_tokens) >= 2:
        return " ".join(query_tokens) in " ".join(hay_tokens)
    hay = set(hay_tokens)
    return all(token in hay or any(item.startswith(token) for item in hay) for token in query_tokens)


class EncyclopediaDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = BUILDER.build_data(ROOT)

    def test_commander_reference_has_separate_sources_and_complete_talents(self) -> None:
        reference = json.loads((ROOT / "data/commanders.json").read_text(encoding="utf-8"))
        audit = json.loads((ROOT / "data/commander_value_audit.json").read_text(encoding="utf-8"))
        traces = {(item["commander"], item["talent"]): item for item in audit["talents"]}
        self.assertEqual(reference["source_date"], "2026-11-13")
        self.assertEqual(audit["snapshot_date"], reference["source_date"])
        self.assertTrue(reference["guide_url"].startswith("https://news.gotdragonfire.com/"))
        self.assertEqual(len(reference["commanders"]), 5)
        self.assertEqual(len(reference["trait_examples"]), 8)
        for commander in reference["commanders"]:
            self.assertEqual(len(commander["talents"]), 3)
            self.assertEqual(len(commander["traits"]), 2)
            self.assertTrue(set(commander["traits"]).issubset(reference["trait_examples"]))
            for talent in commander["talents"]:
                self.assertTrue(talent["client_key"].startswith("TALENT_"))
                self.assertTrue(talent["exact_client_text"])
                trace = traces[(commander["name"], talent["name"])]
                self.assertTrue(trace["edges"])
                for row in talent["reviewed_tracks"]:
                    track = trace["tracks"][row["progression_id"]]
                    self.assertIn(len(track), (1, 20))
                    self.assertTrue(any(edge["to"] == row["progression_id"] for edge in trace["edges"]))
        no_quarter = traces[("Daemon Targaryen", "No Quarter")]["tracks"]
        self.assertEqual([no_quarter["prog_talent_noquarter_pos_01"][i] for i in (0, 9, 19)], [0.0107, 0.064, 0.16])
        sea_snake = traces[("Corlys Velaryon", "The Sea Snake")]["tracks"]
        self.assertEqual(sea_snake["prog_talent_theseasnake_trig_02"][-1], 1.0)

    def test_staged_poi_references_are_not_placements(self) -> None:
        reference = json.loads((ROOT / "data/staged_poi_references.json").read_text(encoding="utf-8"))
        self.assertEqual({item["name"] for item in reference["references"]}, {"Coldmoat", "Standfast"})
        for item in reference["references"]:
            self.assertEqual(item["lifecycle"], "staged")
            self.assertEqual(item["campaign_reference"], "Alpha")
            self.assertNotIn("coordinates", item)
            self.assertEqual(item["region_description"], "PLACEHOLDER")
            self.assertEqual(len(item["bonuses"]), 2)
            self.assertTrue(all("unverified" in bonus["evidence"] for bonus in item["bonuses"]))

    def test_commander_reference_tracks_have_traceable_progressions(self) -> None:
        reference = json.loads((ROOT / "data/commanders.json").read_text(encoding="utf-8"))
        audit = json.loads((ROOT / "data/commander_value_audit.json").read_text(encoding="utf-8"))
        traces = {(item["commander"], item["talent"]): item for item in audit["talents"]}
        self.assertEqual(len(reference["commanders"]), 5)
        for commander in reference["commanders"]:
            self.assertEqual(len(commander["talents"]), 3)
            for talent in commander["talents"]:
                trace = traces[(commander["name"], talent["name"])]
                for row in talent["reviewed_tracks"]:
                    self.assertIn(len(trace["tracks"][row["progression_id"]]), (1, 20))
                    self.assertTrue(any(edge["to"] == row["progression_id"] for edge in trace["edges"]))

    def test_unique_and_present_stable_ids(self) -> None:
        self.assertEqual(len(self.data["dragons"]), 38)
        self.assertEqual(sum(dragon["evidence"]["class"] == "screenshot_confirmed" for dragon in self.data["dragons"]), 38)
        self.assertEqual(sum(dragon["evidence"]["class"] == "cross_site_confirmed" for dragon in self.data["dragons"]), 0)
        ids = [item["id"] for item in self.data["dragons"]]
        ids += [item["id"] for item in self.data["effects"]]
        ids += [ability["id"] for dragon in self.data["dragons"] for ability in dragon["abilities"]]
        self.assertTrue(all(ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_relationships_are_not_broken(self) -> None:
        self.assertEqual(BUILDER.validate(self.data), [])
        dragon_ids = {item["id"] for item in self.data["dragons"]}
        for effect in self.data["effects"]:
            for reference in sum(effect["relationships"].values(), []):
                self.assertIn(reference["dragon_id"], dragon_ids)

    def test_map_node_ids_coordinates_and_connections(self) -> None:
        nodes = self.data["map_nodes"]
        self.assertEqual(len(nodes), 7912)
        self.assertEqual(nodes[0]["id"], "map-node:000000")
        self.assertEqual(nodes[-1]["id"], f"map-node:{len(nodes) - 1:06d}")
        known_ids = {node["id"] for node in nodes}
        self.assertEqual(len(known_ids), len(nodes))
        for node in nodes:
            self.assertGreaterEqual(node["coordinates"]["x"], 0)
            self.assertLessEqual(node["coordinates"]["x"], 2080)
            self.assertGreaterEqual(node["coordinates"]["y"], 0)
            self.assertLessEqual(node["coordinates"]["y"], 3312)
            self.assertTrue(set(node["crossing_connections"]).issubset(known_ids))
        self.assertTrue(any(node["crossing_connections"] for node in nodes))

    def test_structured_graph_fixtures(self) -> None:
        by_name = {dragon["name"]: dragon for dragon in self.data["dragons"]}
        shadowsong = by_name["Shadowsong"]
        breath = next(ability for ability in shadowsong["abilities"] if ability["name"] == "Breath of Fire")
        schedules = [item for item in self.data["graph"]["schedules"] if item["ability_id"] == breath["id"]]
        self.assertIn([2, 5, 8], [item["rounds"] for item in schedules])
        conditions = [item for item in self.data["graph"]["conditions"] if item["ability_id"] == breath["id"]]
        self.assertTrue(any(item["status_id"] == "effect:panic" for item in conditions))

        meleys = by_name["Meleys"]
        scarlet = next(ability for ability in meleys["abilities"] if ability["name"] == "Scarlet Strike")
        priorities = [item for item in self.data["graph"]["prioritizers"] if item["ability_id"] == scarlet["id"]]
        self.assertTrue(any(item["field"] == "Initiative" and item["direction"] == "highest" for item in priorities))

        starshower = by_name["Starshower"]
        starfall = next(ability for ability in starshower["abilities"] if ability["name"] == "Starfall")
        operations = [item for item in self.data["graph"]["status_operations"] if item["ability_id"] == starfall["id"]]
        self.assertTrue(any(item["effect_id"] == "effect:solar-flare" and item["operation"] == "consumes" for item in operations))

    def test_status_prerequisites_are_not_consumed_or_applied(self) -> None:
        meleys = next(dragon for dragon in self.data["dragons"] if dragon["name"] == "Meleys")
        abilities = {ability["name"]: ability for ability in meleys["abilities"]}
        for name in ("Scarlet Strike", "Royal Rend"):
            operations = [item for item in self.data["graph"]["status_operations"] if item["ability_id"] == abilities[name]["id"]]
            self.assertFalse(any(item["effect_id"] in {"effect:bleed", "effect:vulnerable", "effect:laceration"} and item["operation"] == "consumes" for item in operations))
            self.assertTrue(any(item["effect_id"] == "effect:vulnerable" and item["operation"] == "applies" for item in operations))
        red_queen = [item for item in self.data["graph"]["status_operations"] if item["ability_id"] == abilities["The Red Queen"]["id"]]
        self.assertFalse(any(item["effect_id"] == "effect:bleed" and item["operation"] == "applies" for item in red_queen))
        self.assertTrue(any(item["effect_id"] == "effect:laceration" and item["operation"] == "applies" for item in red_queen))

    def test_semantic_diff_reports_field_changes(self) -> None:
        baseline = BUILDER.make_version_baseline(self.data)
        unchanged = BUILDER.semantic_changes(self.data, baseline)
        self.assertEqual(unchanged["comparison_state"], "unchanged")
        self.assertEqual(unchanged["changes"], [])

        changed_data = deepcopy(self.data)
        target = next(dragon for dragon in changed_data["dragons"] if dragon["name"] == "Shadowsong")
        target["abilities"][0]["exact_text"][0] += " Test-only change."
        changed = BUILDER.semantic_changes(changed_data, baseline)
        ability_change = next(item for item in changed["changes"] if item["entity_id"] == target["abilities"][0]["id"])
        self.assertEqual(ability_change["change_type"], "changed")
        self.assertIn("exact_text", ability_change["changed_fields"])

    def test_representative_search_recall(self) -> None:
        corpus = [(dragon["name"], search_text(dragon)) for dragon in self.data["dragons"]]
        effect_corpus = [(effect["name"], " ".join([effect["name"], effect["exact_text"]])) for effect in self.data["effects"]]
        all_docs = corpus + effect_corpus
        queries = [
            "Vulnerable",
            "Fire damage",
            "targets highest Initiative",
            "cleanses negative effects",
            "Nimble",
            "Shieldbearer affinity",
            "rounds 2 5 8",
        ]
        for query in queries:
            with self.subTest(query=query):
                self.assertTrue(any(matches(text, query) for _, text in all_docs), query)

    def test_screenshot_wording_is_preserved_exactly(self) -> None:
        by_name = {dragon["name"]: dragon for dragon in self.data["dragons"]}
        for path in sorted((ROOT / "data" / "dragons").glob("*.json")):
            source = json.loads(path.read_text(encoding="utf-8"))
            generated = by_name[source["name"]]
            self.assertEqual(generated["abilities"][0]["exact_text"], BUILDER.text_blocks(source["command"]["verbatim"]))
            self.assertEqual(generated["abilities"][1]["exact_text"], BUILDER.text_blocks(source["vanguard"]["verbatim"]))
            for index, habit in enumerate(source["habits"], start=2):
                self.assertEqual(generated["abilities"][index]["exact_text"], BUILDER.text_blocks(habit["verbatim"]))

    def test_staged_content_is_hidden_by_default(self) -> None:
        staged = [item for item in [*self.data["dragons"], *self.data["effects"]] if item["lifecycle"] == "staged"]
        visible = [item for item in [*self.data["dragons"], *self.data["effects"]] if item["lifecycle"] != "staged"]
        self.assertTrue(staged)
        self.assertTrue(all(item not in visible for item in staged))
        staged_dragons = {item["name"] for item in self.data["dragons"] if item["lifecycle"] == "staged"}
        self.assertNotIn("Meleys", staged_dragons)
        self.assertNotIn("Smoketail", staged_dragons)

    def test_current_installed_evidence_provenance_and_lifecycle(self) -> None:
        app = json.loads((ROOT / "data" / "dragon_application_knowledge.json").read_text(encoding="utf-8"))
        self.assertEqual(app["metadata"]["snapshot_date"], "2026-10-01")
        self.assertEqual(app["metadata"]["client_version"], "26.9.56700")
        self.assertEqual(app["metadata"]["version_code"], 326)
        self.assertIn("continuing_evidence_policy", app["metadata"])

        by_name = {dragon["name"]: dragon for dragon in app["dragons"]}
        self.assertEqual(by_name["Smoketail"]["recommendation_status"], "screenshot_audited")
        self.assertEqual(by_name["Smoketail"]["availability_status"], "user_confirmed_available")
        self.assertEqual(by_name["Smoketail"]["troop_affinities"]["positive"], ["Spearmen"])
        smoketail = json.loads((ROOT / "data" / "dragons" / "smoketail.json").read_text(encoding="utf-8"))
        unraveled = next(habit for habit in smoketail["habits"] if habit["name"] == "Unraveled")
        self.assertEqual([unraveled["upgrade_levels"][str(level)]["per_weakened_champion_percent"] for level in range(1, 6)], [-10.5, -13, -15, -18, -21])
        self.assertIn("Burn", by_name["Smoketail"]["client_ability_slots"]["habits_in_slot_order"][2]["description_template"])
        self.assertEqual(by_name["Meleys"]["availability_status"], "user_confirmed_available")
        self.assertEqual(by_name["Meleys"]["recommendation_status"], "screenshot_audited")
        self.assertEqual(by_name["Meleys"]["troop_affinities"]["positive"], ["Cavalry", "Archers"])
        self.assertEqual(by_name["Meleys"]["troop_affinities"]["negative"], ["Siege"])

        for path in sorted((ROOT / "data" / "dragons").glob("*.json")):
            audited = json.loads(path.read_text(encoding="utf-8"))
            installed = by_name[audited["name"]]["troop_affinities"]
            self.assertEqual(installed["positive"], audited["troop_affinities"].get("positive", []), audited["name"])
            self.assertEqual(installed["negative"], audited["troop_affinities"].get("negative", []), audited["name"])

        curated = json.loads((ROOT / "data" / "installed_evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(curated["metadata"]["client_version"], app["metadata"]["client_version"])
        excluded = {item["id"] for item in curated["observations"] if item["recommendation_use"] == "exclude"}
        self.assertIn("2026-10-01-commanders", excluded)


if __name__ == "__main__":
    unittest.main()
