import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { planBatchRecommendations, planRecommendations, renderBatchMarkdown, validatePlannerInput } from "../recommend.mjs";

const data = JSON.parse(fs.readFileSync(new URL("../../game-data-encyclopedia/public/data/encyclopedia.json", import.meta.url), "utf8"));
const common = JSON.parse(fs.readFileSync(new URL("../../../data/common_formations.json", import.meta.url), "utf8"));

function entry(name, overrides = {}) {
  const dragon = data.dragons.find(item => item.name === name);
  return {
    dragon: name,
    owned: true,
    level: 50,
    stars: 6,
    power: 100000,
    habit_levels: Object.fromEntries(dragon.abilities.filter(ability => ability.kind === "habit").map(ability => [ability.client_key, 5])),
    ...overrides,
  };
}

const baselineRoster = ["Velar", "Vhagar", "Moondancer", "Vermithor", "Rhysarion", "Venator", "Malachite", "Seasmoke", "Kalspire"].map(name => entry(name));

test("validates mixed per-dragon progression without replacing unknown Habit levels", () => {
  const input = validatePlannerInput(data, {
    roster: [entry("Velar", { level: 41, stars: 4, habit_levels: {} }), entry("Vhagar", { level: 50, stars: 6 }), entry("Moondancer", { level: 37, stars: 3 })],
  });
  assert.equal(input.roster[0].level, 41);
  assert.equal(input.roster[0].stars, 4);
  assert.deepEqual(input.roster[0].habit_levels, {});
});

test("rejects missing progression instead of silently assuming it", () => {
  assert.throws(() => validatePlannerInput(data, { roster: [{ dragon: "Velar" }, entry("Vhagar"), entry("Moondancer")] }), /level must be/);
});

test("retains all common baselines in the mandatory ledger", () => {
  const result = planRecommendations(data, common, {
    roster: baselineRoster,
    available_troops: ["Cavalry", "Shieldbearers", "Spearmen"],
    objective: "pvp",
    max_finalists: 6,
  });
  assert.equal(result.common_baselines.length, 3);
  assert.ok(result.common_baselines.every(item => item.status === "evaluated"));
  assert.equal(result.candidate_ledger.filter(item => item.category === "common_baseline").length, 3);
  assert.ok(result.primary_candidate);
});

test("a common baseline can itself be the primary recommendation", () => {
  const customBaseline = {
    formations: [{
      id: "best-order-baseline",
      name: "Velar / Moondancer / Vhagar",
      formation: { troop_type: "Shieldbearers", left_flank: "Velar", vanguard: "Moondancer", right_flank: "Vhagar" },
      applicability: { objectives: ["general_purpose"], counter_targets: [] },
      strategic_basis: "Test fixture matching the mechanically preferred order.",
    }],
  };
  const result = planRecommendations(data, customBaseline, {
    roster: [entry("Velar"), entry("Vhagar"), entry("Moondancer")],
    available_troops: ["Shieldbearers"],
  });
  assert.equal(result.common_baselines[0].status, "evaluated");
  assert.equal(result.primary_candidate.id, result.common_baselines[0].candidate.id);
});

test("reports unowned common formations as illegal with reasons", () => {
  const result = planRecommendations(data, common, {
    roster: [entry("Velar"), entry("Vhagar"), entry("Moondancer")],
    available_troops: ["Shieldbearers"],
  });
  assert.equal(result.common_baselines[0].status, "evaluated");
  assert.equal(result.common_baselines[1].status, "illegal");
  assert.match(result.common_baselines[1].reasons.join(" "), /Not owned/);
});

test("emits Pareto finalists, timing windows, and canonical evidence locators", () => {
  const result = planRecommendations(data, common, {
    roster: [entry("Malachite"), entry("Seasmoke"), entry("Kalspire"), entry("Velar")],
    available_troops: ["Cavalry"],
    enemy: {
      troop_type: "Shieldbearers",
      formation: [entry("Velar", { lane: "Left Flank" }), entry("Vhagar", { lane: "Vanguard" }), entry("Moondancer", { lane: "Right Flank" })],
    },
  });
  assert.ok(result.pareto_finalists.length > 0);
  assert.equal(typeof result.primary_candidate.metrics.objective_fit, "number");
  assert.ok(result.primary_candidate.timeline.by_round.length > 0);
  assert.ok(result.primary_candidate.evidence.every(item => item.canonical_source && item.encyclopedia_pointer));
  assert.ok(result.candidate_ledger.some(item => item.category === "counter_specific"));
});

test("normalizes displayed red stars and rejects a conflicting declared rank", () => {
  const input = validatePlannerInput(data, {
    roster: [entry("Velar", { stars: 7, displayed_stars: { color: "red", count: 2 } }), entry("Vhagar"), entry("Moondancer")],
  });
  assert.equal(input.roster[0].displayed_stars.count, 2);
  assert.throws(() => validatePlannerInput(data, {
    roster: [entry("Velar", { stars: 6, displayed_stars: { color: "red", count: 2 } }), entry("Vhagar"), entry("Moondancer")],
  }), /resolves to Rank 7/);
});

test("batch planner consolidates all three common enemy formations into an auditable report", () => {
  const result = planBatchRecommendations(data, common, {
    objective: "counter",
    available_troops: ["Cavalry", "Shieldbearers", "Spearmen"],
    roster: baselineRoster,
    roster_preflight: { completeness: "complete", expected_visible_dragons: baselineRoster.length },
    request_mode: "one_per_matchup",
    reuse_policy: "independent_matchups",
    scenarios: common.formations.map(item => ({ id: item.id, common_formation_id: item.id })),
  });
  assert.equal(result.scenarios.length, 3);
  assert.equal(result.validation.valid, true);
  assert.equal(result.roster_preflight.verified_complete, true);
  for (const scenario of result.scenarios) {
    assert.equal(scenario.selected_candidates.length, 1);
    assert.equal(scenario.selection_attestation.selected_candidate_id, scenario.selection_attestation.planner_primary_id);
    assert.ok(scenario.coverage_matrix.length > 0);
    assert.ok(scenario.gate_report.length > 0);
    assert.ok(scenario.decision_evidence.length > 0);
    assert.equal(scenario.common_baselines.length, 3);
  }
  const markdown = renderBatchMarkdown(result);
  assert.match(markdown, /Threat coverage/);
  assert.match(markdown, /Common-baseline check/);
  assert.match(markdown, /Left Flank/);
});

test("batch planner fails closed when a referenced common formation is unknown", () => {
  assert.throws(() => planBatchRecommendations(data, common, {
    roster: baselineRoster,
    scenarios: [{ id: "missing", common_formation_id: "not-a-formation" }],
  }), /Unknown common_formation_id/);
});

test("batch top-n output keeps roster-scope uncertainty explicit", () => {
  const result = planBatchRecommendations(data, common, {
    roster: baselineRoster,
    request_mode: "top_n_per_matchup",
    top_n: 2,
    scenarios: [{ id: "velar", common_formation_id: "velar-vhagar-moondancer-shieldbearers" }],
  });
  assert.equal(result.roster_preflight.completeness, "declared_subset");
  assert.ok(result.scenarios[0].selected_candidates.length >= 1);
  assert.ok(result.scenarios[0].selected_candidates.length <= 2);
  assert.ok(result.scenarios[0].risks.some(item => item.type === "roster_scope"));
});

test("counter coverage does not call chance or target limited effects direct", () => {
  const roster = ["Starshower", "Zivern", "Seasmoke", "Arulix"].map(name => entry(name, { stars: 10 }));
  const result = planBatchRecommendations(data, common, {
    roster,
    scenarios: [
      { id: "shieldbearers", common_formation_id: common.formations[0].id },
      { id: "cavalry", common_formation_id: common.formations[2].id },
    ],
  });
  const shieldbearers = result.scenarios[0];
  const cleanse = shieldbearers.coverage_matrix.find(row => row.threat === "Advantage");
  assert.equal(cleanse.state, "partial");
  assert.ok(cleanse.responses.some(response => response.qualifiers.some(note => note.includes("20%"))));
  const shroud = shieldbearers.coverage_matrix.find(row => row.threat === "Physical Damage");
  assert.equal(shroud.state, "partial");
  assert.match(shroud.remaining_gap, /Basic Attacks are excluded/);
  const cavalry = result.scenarios[1];
  const fire = cavalry.coverage_matrix.find(row => row.threat === "Fire Damage");
  assert.equal(fire.state, "partial");
  assert.equal(fire.responses.find(response => response.ability === "Gleaming Spiral").chance_percent, 25);
  assert.match(fire.remaining_gap, /25% activation chance/);
  assert.equal(cavalry.selected_candidates[0].metrics.covered_threat_count, cavalry.coverage_matrix.filter(row => row.state === "direct").length);
  const report = renderBatchMarkdown(result);
  assert.match(report, /planner_default_assumption/);
  assert.match(report, /reference assumptions/);
  assert.match(report, /Source instances/);
  assert.match(report, /validation.valid: true/);
});

