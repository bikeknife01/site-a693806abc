import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { candidateEvidence, chooseTroop, combatExplorerQuery, compareRecommendations, currentHabitValue, extractThreats, formationSynergies, recommendationConfidence, recommendFormations } from "../src/engine.mjs";
import { loadObservations, normalizeObservation, saveObservation } from "../src/observations.mjs";

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

test("Vanguard-only counter evidence controls the selected lane", () => {
  const enemies = [{ dragon: "enemy", lane: "Vanguard", stars: 10, level: 50 }];
  const result = recommendFormations(data, enemies, ["anti-fire", "a", "b"], "Shieldbearers");
  const pick = result.recommendations[0].formation.find(item => item.dragon.slug === "anti-fire");
  assert.equal(pick.lane, "Vanguard");
  assert.ok(pick.covered.includes("damage:Fire Damage"));
});

test("saved Habit level changes producer reliability in an explicit synergy chain", () => {
  const slow = effect("effect:slow", "Slow");
  const producerAbility = ability("slow-source", "Slow Source", [], ["op-slow"], "Each Round: chance to afflict Slow.", "habit");
  producerAbility.client_key = "slow-source";
  producerAbility.unlock = { star_rank: 2 };
  producerAbility.upgrade_levels = { "1": 10, "2": 20, "3": 35, "4": 50, "5": 70 };
  producerAbility.value_unit = "percent_chance";
  const consumerAbility = ability("slow-payoff", "Slow Payoff", ["Fire Damage"], [], "Deal more damage if an enemy is afflicted with Slow.", "habit");
  consumerAbility.client_key = "slow-payoff";
  consumerAbility.unlock = { star_rank: 4 };
  consumerAbility.normalized.condition_refs = ["cond-slow"];
  const producer = dragon("producer", "Producer", [producerAbility]);
  const consumer = dragon("consumer", "Consumer", [consumerAbility]);
  const support = dragon("support", "Support", []);
  const local = {
    ...data,
    effects: [...data.effects, slow],
    dragons: [producer, consumer, support],
    graph: {
      ...data.graph,
      status_operations: [...data.graph.status_operations, { id: "op-slow", ability_id: "slow-source", effect_id: "effect:slow", operation: "applies", chance_percent: 10, exact_context: "chance to afflict Slow" }],
      conditions: [{ id: "cond-slow", ability_id: "slow-payoff", type: "status_present", subject: "enemy", status_id: "effect:slow", exact_text: "if an enemy is afflicted with Slow" }],
    },
  };
  const lowProgression = { stars: 10, level: 50, habit_levels: { "slow-source": 1, "slow-payoff": 5 } };
  const highProgression = { ...lowProgression, habit_levels: { ...lowProgression.habit_levels, "slow-source": 4 } };
  assert.equal(currentHabitValue(producerAbility, highProgression), 50);
  const low = candidateEvidence(local, producer, [], lowProgression, "Left Flank");
  const high = candidateEvidence(local, producer, [], highProgression, "Left Flank");
  const payoff = candidateEvidence(local, consumer, [], lowProgression, "Vanguard");
  const filler = candidateEvidence(local, support, [], lowProgression, "Right Flank");
  assert.equal(formationSynergies(local, [low, payoff, filler])[0].chance_percent, 10);
  assert.equal(formationSynergies(local, [high, payoff, filler])[0].chance_percent, 50);
});

test("an allied beneficial effect does not satisfy an enemy-status prerequisite", () => {
  const sourceAbility = ability("recovery-source", "Recovery Source", [], ["op-recovery"], "Apply Recovery to an Ally.", "habit");
  sourceAbility.client_key = "recovery-source";
  const payoffAbility = ability("enemy-recovery-payoff", "Enemy Recovery Payoff", [], [], "If an Enemy receives Recovery, gain a bonus.", "habit");
  payoffAbility.client_key = "enemy-recovery-payoff";
  payoffAbility.normalized.condition_refs = ["cond-enemy-recovery"];
  const source = dragon("recovery-source", "Recovery Source", [sourceAbility]);
  const payoff = dragon("recovery-payoff", "Recovery Payoff", [payoffAbility]);
  const local = {
    ...data,
    dragons: [source, payoff, fillerA],
    graph: {
      ...data.graph,
      status_operations: [...data.graph.status_operations, { id: "op-recovery", ability_id: "recovery-source", effect_id: "effect:recovery", operation: "applies", chance_percent: null, exact_context: "Apply Recovery to an Ally" }],
      conditions: [{ id: "cond-enemy-recovery", ability_id: "enemy-recovery-payoff", type: "status_present", subject: "enemy", status_id: "effect:recovery", exact_text: "If an Enemy receives Recovery" }],
    },
  };
  const progression = { stars: 10, level: 50, habit_levels: { "recovery-source": 5, "enemy-recovery-payoff": 5 } };
  const formation = [
    candidateEvidence(local, source, [], progression, "Left Flank"),
    candidateEvidence(local, payoff, [], progression, "Vanguard"),
    candidateEvidence(local, fillerA, [], progression, "Right Flank"),
  ];
  assert.equal(formationSynergies(local, formation).length, 0);
});

test("repository matchup fixtures return legal, distinct, explainable formations", () => {
  const realData = JSON.parse(fs.readFileSync(new URL("../../game-data-encyclopedia/public/data/encyclopedia.json", import.meta.url), "utf8"));
  const fixtures = JSON.parse(fs.readFileSync(new URL("./matchup-fixtures/core-matchups.json", import.meta.url), "utf8"));
  const observedCategories = new Set();
  for (const fixture of fixtures) {
    const result = recommendFormations(realData, fixture.enemies, fixture.owned, fixture.enemyTroop, fixture.objective);
    result.threats.forEach(threat => observedCategories.add(threat.category));
    assert.equal(result.recommendations.length, 3, fixture.name);
    assert.equal(new Set(result.recommendations.map(item => item.signature)).size, 3, fixture.name);
    for (const recommendation of result.recommendations) {
      assert.deepEqual(recommendation.formation.map(item => item.lane), ["Left Flank", "Vanguard", "Right Flank"], fixture.name);
      assert.ok(recommendation.formation.every(item => fixture.owned.some(entry => entry.slug === item.dragon.slug)), fixture.name);
      assert.ok(recommendation.coverage >= 0 && recommendation.coverage <= 1, fixture.name);
      assert.ok(recommendation.breakdown && recommendation.combatHorizon, fixture.name);
    }
  }
  assert.deepEqual([...observedCategories].sort(), ["damage", "status", "sustain"]);
});

test("qualified Cleanse relationships do not claim unrelated negative effects", () => {
  const realData = JSON.parse(fs.readFileSync(new URL("../../game-data-encyclopedia/public/data/encyclopedia.json", import.meta.url), "utf8"));
  const sunfyre = realData.dragons.find(item => item.name === "Sunfyre");
  const vulnerable = realData.effects.find(item => item.name === "Vulnerable");
  const weakened = realData.effects.find(item => item.name === "Weakened");
  assert.ok(vulnerable.relationships.cleanses.some(item => item.dragon_id === sunfyre.id));
  assert.equal(weakened.relationships.cleanses.some(item => item.dragon_id === sunfyre.id), false);
});

test("unresolved client templates remain conditional instead of confirmed coverage", () => {
  const realData = JSON.parse(fs.readFileSync(new URL("../../game-data-encyclopedia/public/data/encyclopedia.json", import.meta.url), "utf8"));
  const starshower = realData.dragons.find(item => item.name === "Starshower");
  const threat = { id: "status:effect:vulnerable", category: "status", effect_id: "effect:vulnerable", name: "Vulnerable", sources: [] };
  const progression = { level: 50, stars: 10, habit_levels: Object.fromEntries(starshower.abilities.filter(item => item.kind === "habit").map(item => [item.client_key, 5])) };
  const evidence = candidateEvidence(realData, starshower, [threat], progression, "Vanguard");
  assert.equal(evidence.covered.includes(threat.id), false);
  assert.equal(evidence.conditionalCovered.includes(threat.id), true);
});

test("partial enemy formations lower confidence without inventing threats", () => {
  const confidence = recommendationConfidence([
    { dragon: "enemy", lane: "Left Flank", level: 50, stars: 10 },
    { dragon: "", lane: "Vanguard", level: null, stars: null },
    { dragon: "", lane: "Right Flank", level: null, stars: null },
  ]);
  assert.equal(confidence.level, "low");
  assert.equal(confidence.known_lanes, 1);
  assert.match(confidence.note, /only the 1 documented enemy lane/);
});

test("side-by-side comparison exposes material formation differences", () => {
  const enemies = [{ dragon: "enemy", lane: "Vanguard", stars: 10, level: 50 }];
  const local = { ...data, dragons: [...data.dragons, dragon("c", "C", [], ["Spearmen"])] };
  const result = recommendFormations(local, enemies, ["anti-fire", "a", "b", "c"], "Shieldbearers");
  const comparison = compareRecommendations(result.recommendations[0], result.recommendations[1]);
  assert.ok(comparison.left_only_dragons.length > 0);
  assert.equal(typeof comparison.score_delta, "number");
});

test("observed outcomes are normalized, stored locally, and never affect scoring", () => {
  const values = new Map();
  const storage = { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) };
  const normalized = normalizeObservation({ outcome: "win", stalemates: 99, notes: "x".repeat(1200) });
  assert.equal(normalized.stalemates, 20);
  assert.equal(normalized.notes.length, 1000);
  assert.equal(normalized.scoring_effect, "none");
  saveObservation(normalized, storage);
  assert.equal(loadObservations(storage).length, 1);
  assert.equal(loadObservations(storage)[0].scoring_effect, "none");
});

test("damage threat timing is attributed to its clause instead of the whole ability", () => {
  const realData = JSON.parse(fs.readFileSync(new URL("../../game-data-encyclopedia/public/data/encyclopedia.json", import.meta.url), "utf8"));
  const threats = extractThreats(realData, [{ dragon: "dragon_generic_antares", lane: "Left Flank", level: 50, stars: 10 }]);
  const fire = threats.find(item => item.id === "damage:Fire Damage");
  const scheduled = fire.sources.find(item => item.exact_text.includes("Rounds 3, 6, 9"));
  assert.deepEqual(scheduled.rounds, [3, 6, 9]);
});

test("conditional parsing keeps produced effects out of prerequisites", () => {
  const realData = JSON.parse(fs.readFileSync(new URL("../../game-data-encyclopedia/public/data/encyclopedia.json", import.meta.url), "utf8"));
  const sheepstealer = realData.dragons.find(item => item.name === "Sheepstealer");
  const conditionsFor = abilityName => {
    const ability = sheepstealer.abilities.find(item => item.name === abilityName);
    return ability.normalized.condition_refs.map(id => realData.graph.conditions.find(item => item.id === id));
  };
  const savageClaim = conditionsFor("Savage Claim");
  const recoveryConditions = savageClaim.filter(item => item.status_id === "effect:recovery");
  assert.equal(recoveryConditions.length, 1);
  assert.equal(recoveryConditions[0].subject, "enemy");
  assert.match(recoveryConditions[0].exact_text, /Prey received Recovery/);
  const baitedKill = conditionsFor("Baited Kill").find(item => item.status_id === "effect:recovery");
  assert.equal(baitedKill.subject, "enemy");
});
