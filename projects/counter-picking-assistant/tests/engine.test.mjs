import test from "node:test";
import assert from "node:assert/strict";
import { chooseTroop, combatExplorerQuery, extractThreats, recommendFormations } from "../src/engine.mjs";

const effect = (id, name, target = "harmful", section = "Negative Effects") => ({ id, name, effect_on_target: target, game_section: section, relationships: { counters: [], cleanses: [] } });
const ability = (id, name, damage, refs, text, kind = "command") => ({ id, name, kind, unlock: {}, exact_text: [text], normalized: { damage_types: damage, status_operation_refs: refs, effect_relations: [] } });
const dragon = (id, name, abilities, positive = ["Archers"]) => ({ id: `dragon:${id}`, slug: id, name, breed: "Champion", rarity_tier: "Rare", lifecycle: "live", abilities, troop_affinities: { positive, negative: [] } });
const data = {
  effects: [effect("effect:stun", "Stun", "harmful", "Control Effects"), effect("effect:recovery", "Recovery", "beneficial", "Positive Effects")],
  graph: { status_operations: [{ id: "op-stun", effect_id: "effect:stun", operation: "applies" }, { id: "op-recovery", effect_id: "effect:recovery", operation: "applies" }] },
  mechanics: { troop_types: { Archers: { advantaged_against: "Spearmen", disadvantaged_against: "Shieldbearers" }, Cavalry: { advantaged_against: "Shieldbearers", disadvantaged_against: "Spearmen" }, Shieldbearers: { advantaged_against: "Archers", disadvantaged_against: "Cavalry" }, Spearmen: { advantaged_against: "Cavalry", disadvantaged_against: "Archers" }, Siege: { advantaged_against: null, disadvantaged_against: "all_combat_troops" } } },
  dragons: []
};
const enemy = dragon("enemy", "Enemy", [ability("enemy-fire", "Flame", ["Fire Damage"], ["op-stun", "op-recovery"], "Deal Fire Damage, afflict Stun, and apply Recovery.")], ["Spearmen"]);
const antiFire = dragon("anti-fire", "Anti Fire", [ability("ward", "Ward", [], [], "Reduce Fire Damage Received by -20%.", "vanguard")], ["Cavalry"]);
const fillerA = dragon("a", "A", [], ["Cavalry"]);
const fillerB = dragon("b", "B", [], ["Cavalry"]);
data.dragons = [enemy, antiFire, fillerA, fillerB];

test("extracts damage, harmful status, and sustain threats", () => {
  const threats = extractThreats(data, [{ dragon: "enemy", lane: "Vanguard", stars: 10, level: 50 }]);
  assert.deepEqual(threats.map(item => item.id).sort(), ["damage:Fire Damage", "status:effect:stun", "sustain:recovery"]);
});

test("shared troop choice respects affinity and troop cycle", () => {
  assert.equal(chooseTroop(data, [antiFire, fillerA, fillerB], "Shieldbearers").troop, "Cavalry");
});

test("formation recommendation covers explicit Fire mitigation and exports scenario", () => {
  const enemies = [{ dragon: "enemy", lane: "Vanguard", stars: 10, level: 50 }];
  const result = recommendFormations(data, enemies, ["anti-fire", "a", "b"], "Shieldbearers");
  assert.ok(result.recommendations[0].covered.includes("damage:Fire Damage"));
  assert.match(combatExplorerQuery(result.recommendations[0], enemies, "Cavalry"), /a2=anti-fire|a1=anti-fire|a3=anti-fire/);
});

test("owned progression controls eligibility and is preserved in Combat export", () => {
  antiFire.abilities[0].unlock = { level: 30 };
  const enemies = [{ dragon: "enemy", lane: "Vanguard", stars: 10, level: 50 }];
  const low = recommendFormations(data, enemies, [{ slug: "anti-fire", owned: true, level: 20, stars: 4 }, { slug: "a", owned: true, level: 20, stars: 4 }, { slug: "b", owned: true, level: 20, stars: 4 }], "Shieldbearers");
  assert.equal(low.recommendations[0].covered.includes("damage:Fire Damage"), false);
  const ready = recommendFormations(data, enemies, [{ slug: "anti-fire", owned: true, level: 35, stars: 6 }, { slug: "a", owned: true, level: 20, stars: 4 }, { slug: "b", owned: true, level: 20, stars: 4 }], "Shieldbearers");
  const query = combatExplorerQuery(ready.recommendations[0], enemies, "Cavalry");
  assert.match(query, /a[123]l=35/);
  assert.match(query, /a[123]s=6/);
  antiFire.abilities[0].unlock = {};
});

test("an increased damage-received clause is never classified as mitigation", async () => {
  const risky = dragon("risky", "Risky", [ability("risk", "Risk", [], [], "Increase your Physical Damage Received by +10% and reduce your Instinct by -40%.")]);
  const local = { ...data, dragons: [...data.dragons, risky] };
  const threats = extractThreats(local, [{ dragon: "enemy", lane: "Vanguard", stars: 10, level: 50 }]);
  const { candidateEvidence } = await import("../src/engine.mjs");
  assert.equal(candidateEvidence(local, risky, threats).covered.includes("damage:Physical Damage"), false);
});
