import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { parseArgs, parseFormationSpec, simulate } from "../simulate.mjs";


const data = JSON.parse(fs.readFileSync(new URL("../../game-data-encyclopedia/public/data/encyclopedia.json", import.meta.url), "utf8"));

test("formation specs preserve lane order and one shared troop", () => {
  const formation = parseFormationSpec(data, "Malachite,Seasmoke,Kalspire|Cavalry", "candidate");
  assert.deepEqual(formation.dragons.map(item => item.name), ["Malachite", "Seasmoke", "Kalspire"]);
  assert.equal(formation.troop, "Cavalry");
});

test("one or two strawmen can compare fixed candidate formations", () => {
  const options = parseArgs([
    "--strawman", "Velar,Vhagar,Moondancer|Shieldbearers",
    "--strawman", "Vermithor,Rhysarion,Venator|Spearmen",
    "--candidate", "Malachite,Seasmoke,Kalspire|Cavalry",
    "--candidate", "Tessarion,Malachite,Feskar|Cavalry",
    "--stars", "6",
    "--habit-level", "5",
  ]);
  const result = simulate(data, options);
  assert.equal(result.scenarios.length, 2);
  assert.equal(result.cross_strawman_robustness.length, 2);
  assert.equal(result.scenarios[0].candidates[0].formation.troop_type, "Cavalry");
  assert.deepEqual(
    Object.keys(result.scenarios[0].candidates[0].formation),
    ["troop_type", "left_flank", "vanguard", "right_flank"],
  );
  assert.ok(result.scenarios.every(item => item.threats.length > 0));
  assert.equal(result.scenarios[0].threats.some(item => item.id === "sustain:recovery"), false);
  assert.ok(result.scenarios[0].threats.some(item => item.id === "enabler:effect:advantage"));
  assert.ok(result.scenarios[0].candidates[0].covered_threats.includes("Advantage"));
  assert.ok(result.scenarios[0].candidates[0].branch_opportunity_estimates.length > 0);
  const procRates = new Map(result.scenarios[0].candidates[0].pivotal_habit_reliability.map(item => [`${item.dragon}:${item.ability}`, item.chance_percent]));
  assert.equal(procRates.get("Malachite:Thunderous Roar"), 20);
  assert.equal(procRates.get("Kalspire:Tactical Assault"), 30);
  assert.ok(result.scenarios[0].candidates[0].branch_opportunity_estimates.every(item => (
    item.probability_at_least_once_if_independent_and_eligible >= 0
    && item.probability_at_least_once_if_independent_and_eligible <= 1
  )));
  assert.match(result.limitations[0], /not a battle-outcome or win-rate simulation/);
});

test("the simulator rejects more than two strawmen", () => {
  assert.throws(() => simulate(data, {
    strawmen: [
      "Velar,Vhagar,Moondancer|Shieldbearers",
      "Vermithor,Rhysarion,Venator|Spearmen",
      "Malachite,Seasmoke,Kalspire|Cavalry",
    ],
    candidates: ["Malachite,Seasmoke,Kalspire|Cavalry"],
    level: 50,
    stars: 6,
    habitLevel: 5,
    objective: "pvp",
  }), /one or two/);
});
