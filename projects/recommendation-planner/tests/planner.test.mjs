import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { globalDisjointPortfolio, parseArgs, planBatchRecommendations, planFormationPortfolio, planRecommendations, renderBatchMarkdown, renderPortfolioMarkdown, validatePlannerInput } from "../recommend.mjs";

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

test("CLI accepts saved input files and rejects the removed inline-JSON path", () => {
  assert.equal(parseArgs(["--input", "scenario.json"]).input, "scenario.json");
  assert.throws(() => parseArgs(["--input-json", "{}"]), /Unknown argument/);
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

test("uses a normalized Dragon's Army record in modeled capacity without trusting a mismatched total", () => {
  const profile = {
    dragons: Object.fromEntries(["Velar", "Vhagar", "Moondancer"].map(name => {
      const value = entry(name, { stars: 1, power: null });
      return [data.dragons.find(item => item.name === name).slug, value];
    })),
    stronghold: {
      dragons_army: {
        current_skill: "III",
        current_level: 2,
        additional_troops_per_dragon: 1150,
        basis: "user_declaration",
        provenance: "observed",
      },
    },
  };
  const result = planRecommendations(data, { formations: [] }, { objective: "highest_tile", profile, available_troops: ["Shieldbearers"] });
  assert.equal(result.input_summary.dragons_army.additional_troops_per_dragon, 1150);
  assert.equal(result.primary_candidate.metrics.dragons_army_bonus_per_dragon, 1150);
  assert.equal(result.primary_candidate.metrics.modeled_team_capacity, 18450);
  assert.match(result.metadata.selection_policy, /level-curve capacity proxy/);
  assert.ok(result.primary_candidate.metrics.modeled_capacity_by_dragon.every(item => item.star_scalar_applied === false));
  assert.throws(() => validatePlannerInput(data, {
    profile: {
      ...profile,
      stronghold: { dragons_army: { ...profile.stronghold.dragons_army, additional_troops_per_dragon: 999 } },
    },
  }), /must be 1150/);
});

test("highest-tile ordering prioritizes the largest legal modeled capacity after hard troop safety", () => {
  const result = planRecommendations(data, { formations: [] }, {
    objective: "highest_tile",
    roster: [
      entry("Vhagar", { level: 50, stars: 1, power: null }),
      entry("Velar", { level: 40, stars: 1, power: null }),
      entry("Moondancer", { level: 30, stars: 1, power: null }),
      entry("Vermithor", { level: 20, stars: 1, power: null }),
    ],
  });
  assert.equal(result.primary_candidate.metrics.modeled_team_capacity, 12000);
  assert.deepEqual(result.primary_candidate.progression.map(item => item.dragon).sort(), ["Moondancer", "Velar", "Vhagar"]);
});

test("does not compare partial visible Power as though unknown dragons had zero Power", () => {
  const result = planRecommendations(data, { formations: [] }, {
    roster: [entry("Velar", { power: 200000 }), entry("Vhagar", { power: null }), entry("Moondancer", { power: 100000 }), entry("Vermithor", { power: 300000 })],
    available_troops: ["Shieldbearers"],
  });
  assert.equal(result.input_summary.power_comparable, false);
  assert.ok(result.pareto_finalists.every(candidate => candidate.metrics.known_team_power === null));
});

test("troop-preservation objective scores active sustain within the documented policy", () => {
  const result = planRecommendations(data, { formations: [] }, {
    objective: "troop_preservation",
    roster: [
      entry("Velar", { level: 50, stars: 10, power: null }),
      entry("Rhysarion", { level: 50, stars: 2, power: null }),
      entry("Vermithor", { level: 50, stars: 4, power: null }),
      entry("Caraxes", { level: 50, stars: 1, power: null, habit_levels: {} }),
      entry("Feskar", { level: 50, stars: 1, power: null, habit_levels: {} }),
      entry("Tairax", { level: 50, stars: 1, power: null, habit_levels: {} }),
    ],
  });
  assert.ok(result.primary_candidate.metrics.troop_preservation.score > 0);
  assert.ok(result.primary_candidate.metrics.troop_preservation.components.some(item => item.effect_id === "effect:recovery" || item.effect_id === "effect:protect"));
  assert.equal(result.primary_candidate.metrics.modeled_team_capacity, 15000);
});

test("capacity proxy reports Star scalars without applying an unverified formula", () => {
  const result = planRecommendations(data, { formations: [] }, {
    objective: "highest_tile",
    roster: [entry("Velar", { level: 40, stars: 10 }), entry("Vhagar", { level: 40, stars: 1 }), entry("Moondancer", { level: 40, stars: 6 })],
  });
  assert.equal(result.primary_candidate.metrics.modeled_team_capacity, 12000);
  assert.ok(result.primary_candidate.metrics.modeled_capacity_by_dragon.every(item => item.modeled_max_army_size === 4000));
  assert.ok(result.primary_candidate.metrics.modeled_capacity_by_dragon.every(item => item.capacity_formula_status.includes("star_formula_unverified")));
});

test("global disjoint allocator can beat greedy first-choice removal", () => {
  const candidate = (id, slugs) => ({ id, result: { formation: slugs.map(slug => ({ dragon: { slug } })) } });
  const ranked = [
    candidate("abc", ["a", "b", "c"]),
    candidate("ade", ["a", "d", "e"]),
    candidate("bfg", ["b", "f", "g"]),
    candidate("chi", ["c", "h", "i"]),
    candidate("jkl", ["j", "k", "l"]),
    candidate("mno", ["m", "n", "o"]),
  ];
  const result = globalDisjointPortfolio(ranked, 3);
  assert.equal(result.primary.rankCost, 6);
  assert.deepEqual(result.primary.selected.map(item => item.candidate.id), ["ade", "bfg", "chi"]);
});

test("formation portfolios default to globally selected non-overlapping armies", () => {
  const result = planFormationPortfolio(data, common, {
    formation_count: 2,
    objective: "troop_preservation",
    roster: baselineRoster,
    roster_preflight: { completeness: "complete", expected_visible_dragons: baselineRoster.length },
  });
  assert.equal(result.request_interpretation.reuse_policy, "disjoint_armies");
  assert.equal(result.selected_formations.length, 2);
  const selected = result.selected_formations.flatMap(item => item.candidate.progression.map(dragon => dragon.slug));
  assert.equal(new Set(selected).size, 6);
  assert.equal(result.allocation_attestation.greedy_selection_used, false);
  assert.equal(result.search_summary.allocation_scope.includes("not a truncated"), true);
  const report = renderPortfolioMarkdown(result);
  assert.match(report, /validation.valid: true/);
  for (const formation of result.selected_formations) assert.ok(report.includes(formation.candidate.id));
});

test("unknown-Power endgame portfolios conservatively select the complete expert formation set", () => {
  const roster = baselineRoster.map(dragon => ({ ...dragon, power: null }));
  const result = planFormationPortfolio(data, common, {
    formation_count: 3,
    objective: "damage_and_survivability",
    roster,
    roster_preflight: { completeness: "complete", expected_visible_dragons: roster.length },
  });
  assert.equal(result.input_summary.competitive_context.resolved, "endgame");
  assert.equal(result.allocation_attestation.selection_basis, "expert_prior_default");
  assert.equal(result.strategic_qualification.status, "qualified_with_expert_prior");
  assert.equal(result.strategic_qualification.qualified, true);
  assert.deepEqual(new Set(result.selected_formations.map(item => item.candidate.expert_prior?.formation_id)), new Set(common.formations.map(item => item.id)));
  assert.ok(result.selected_formations.every(item => item.candidate.metrics.competitive_viability.qualified));
  assert.ok(result.selected_formations.every(item => item.global_candidate_rank > 0));
  assert.ok(result.allocation_attestation.strongest_alternative);
  const report = renderPortfolioMarkdown(result);
  assert.match(report, /Strategic qualification/);
  assert.match(report, /qualified_with_expert_prior/);
});

test("endgame ordinary-combat policy fails strategically closed on unsupported Rare dragons", () => {
  const roster = ["Bevlorin", "Shimmer", "Arrax"].map(name => entry(name));
  const result = planFormationPortfolio(data, { formations: [] }, {
    formation_count: 1,
    objective: "damage_and_survivability",
    competitive_context: "endgame",
    roster,
    roster_preflight: { completeness: "complete", expected_visible_dragons: roster.length },
  });
  assert.equal(result.validation.valid, true);
  assert.equal(typeof result.strategic_qualification.qualified, "boolean");
  assert.equal(result.strategic_qualification.qualified, false);
  assert.deepEqual(result.strategic_qualification.unsupported_rare_dragons.sort(), ["Arrax", "Bevlorin", "Shimmer"]);
});

test("reviewed Rare exceptions remain qualified in endgame ordinary combat", () => {
  const roster = ["Thunderstrike", "Shadowrend", "Velar"].map(name => entry(name));
  const result = planFormationPortfolio(data, { formations: [] }, {
    formation_count: 1,
    objective: "damage_and_survivability",
    competitive_context: "endgame",
    roster,
    roster_preflight: { completeness: "complete", expected_visible_dragons: roster.length },
  });
  assert.equal(result.strategic_qualification.qualified, true);
  assert.deepEqual(result.selected_formations[0].candidate.metrics.competitive_viability.reviewed_rare_exceptions.sort(), ["Shadowrend", "Thunderstrike"]);
});

test("explicit Rare override and Siege scope are audited exceptions rather than universal rarity scoring", () => {
  const roster = ["Bevlorin", "Shimmer", "Arrax"].map(name => entry(name));
  const overridden = planFormationPortfolio(data, { formations: [] }, {
    formation_count: 1,
    objective: "damage_and_survivability",
    competitive_context: "endgame",
    allow_unproven_rare: true,
    roster,
    roster_preflight: { completeness: "complete", expected_visible_dragons: roster.length },
  });
  assert.equal(overridden.strategic_qualification.qualified, true);
  assert.equal(overridden.selected_formations[0].candidate.metrics.competitive_viability.allow_unproven_rare, true);

  const siege = planFormationPortfolio(data, { formations: [] }, {
    formation_count: 1,
    objective: "siege",
    competitive_context: "endgame",
    available_troops: ["Siege"],
    roster,
    roster_preflight: { completeness: "complete", expected_visible_dragons: roster.length },
  });
  assert.equal(siege.strategic_qualification.qualified, true);
  assert.equal(siege.selected_formations[0].candidate.metrics.competitive_viability.siege_exception_applied, true);
});

test("known comparable Power permits mechanics-ranked displacement of the expert prior", () => {
  const result = planFormationPortfolio(data, common, {
    formation_count: 3,
    objective: "damage_and_survivability",
    competitive_context: "endgame",
    roster: baselineRoster,
    roster_preflight: { completeness: "complete", expected_visible_dragons: baselineRoster.length },
  });
  assert.equal(result.input_summary.power_comparable, true);
  assert.equal(result.allocation_attestation.selection_basis, "globally_ranked_qualified");
  assert.equal(result.strategic_qualification.qualified, true);
});

test("materially underdeveloped expert line does not receive the unknown-Power endgame default", () => {
  const roster = baselineRoster.map(dragon => ({ ...dragon, power: null }));
  roster.find(dragon => dragon.dragon === "Velar").level = 44;
  const result = planFormationPortfolio(data, common, {
    formation_count: 3,
    objective: "damage_and_survivability",
    competitive_context: "endgame",
    roster,
    roster_preflight: { completeness: "complete", expected_visible_dragons: roster.length },
  });
  assert.notEqual(result.allocation_attestation.selection_basis, "expert_prior_default");
  assert.equal(result.allocation_attestation.expert_baseline_portfolio, null);
  assert.equal(result.strategic_qualification.qualified, false);
});

test("hybrid objective uses de-duplicated magnitude-aware ordinal components", () => {
  const result = planRecommendations(data, { formations: [] }, {
    roster: [entry("Velar"), entry("Vermithor"), entry("Rhysarion")],
    objective: "damage_and_survivability",
  });
  const assessment = result.primary_candidate.metrics.objective_assessment;
  assert.equal(assessment.method, "deduplicated_magnitude_reliability_aware_ordinal_v1");
  assert.ok(assessment.damage_quality > 0);
  const keys = assessment.components.map(item => `${item.dragon}|${item.exact_text}`);
  assert.equal(new Set(keys).size, keys.length);
});

test("formation portfolios fail closed on a screenshot roster-count mismatch", () => {
  assert.throws(() => planFormationPortfolio(data, common, {
    formation_count: 2,
    roster: baselineRoster,
    roster_preflight: { completeness: "complete", expected_visible_dragons: baselineRoster.length + 1 },
  }), /expected 10 owned dragons but received 9/);
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
  assert.equal(typeof result.strategic_qualification.qualified, "boolean");
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
  assert.match(markdown, /Expert\/common-baseline check/);
  assert.match(markdown, /Strategic qualification/);
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
    ],
  });
  const shieldbearers = result.scenarios[0];
  const cleanse = shieldbearers.coverage_matrix.find(row => row.threat === "Advantage");
  assert.equal(cleanse.state, "partial");
  assert.ok(cleanse.responses.some(response => response.qualifiers.some(note => note.includes("20%"))));
  const shroud = shieldbearers.coverage_matrix.find(row => row.threat === "Physical Damage");
  assert.equal(shroud.state, "partial");
  assert.match(shroud.remaining_gap, /Basic Attacks are excluded/);
  const cavalryResult = planBatchRecommendations(data, common, {
    roster: ["Starshower", "Zivern", "Arulix"].map(name => entry(name, { stars: 10 })),
    scenarios: [{ id: "cavalry", common_formation_id: common.formations[2].id }],
  });
  const cavalry = cavalryResult.scenarios[0];
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

