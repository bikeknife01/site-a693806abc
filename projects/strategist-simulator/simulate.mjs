#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  activeAbilities,
  candidateEvidence,
  extractThreats,
  operationRecords,
  roundsFor,
  scoreFormation,
} from "../counter-picking-assistant/src/engine.mjs";


const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../..");
const DATA_PATH = path.join(ROOT, "projects/game-data-encyclopedia/public/data/encyclopedia.json");
const LANES = ["Left Flank", "Vanguard", "Right Flank"];
const TROOPS = new Set(["Cavalry", "Shieldbearers", "Archers", "Spearmen", "Siege"]);

export function parseArgs(argv) {
  const result = { strawmen: [], candidates: [], level: 50, stars: 6, habitLevel: 5, objective: "pvp", pretty: false };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--strawman") result.strawmen.push(argv[++index]);
    else if (arg === "--candidate") result.candidates.push(argv[++index]);
    else if (arg === "--level") result.level = Number(argv[++index]);
    else if (arg === "--stars") result.stars = Number(argv[++index]);
    else if (arg === "--habit-level") result.habitLevel = Number(argv[++index]);
    else if (arg === "--objective") result.objective = argv[++index];
    else if (arg === "--pretty") result.pretty = true;
    else if (arg === "--help" || arg === "-h") result.help = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  return result;
}

function usage() {
  return [
    "Usage:",
    "  node projects/strategist-simulator/simulate.mjs \\",
    "    --strawman \"Velar,Vhagar,Moondancer|Shieldbearers\" \\",
    "    [--strawman \"Dragon,Dragon,Dragon|Troop\"] \\",
    "    --candidate \"Malachite,Seasmoke,Kalspire|Cavalry\" \\",
    "    [--candidate \"Dragon,Dragon,Dragon|Troop\"] [--stars 6] [--habit-level 5] [--pretty]",
    "",
    "Dragon order is Left Flank, Vanguard, Right Flank. One or two strawmen and one to eight candidates are allowed.",
  ].join("\n");
}

function lookupDragon(data, value) {
  const key = value.trim().toLowerCase();
  return data.dragons.find(item => item.name.toLowerCase() === key || item.slug.toLowerCase() === key);
}

export function parseFormationSpec(data, spec, label) {
  if (!spec || !spec.includes("|")) throw new Error(`${label} must use Dragon,Dragon,Dragon|Troop format.`);
  const [dragonPart, troopPart, ...extra] = spec.split("|");
  if (extra.length) throw new Error(`${label} contains too many | separators.`);
  const names = dragonPart.split(",").map(item => item.trim()).filter(Boolean);
  if (names.length !== 3) throw new Error(`${label} must contain exactly three dragons.`);
  const dragons = names.map(name => {
    const dragon = lookupDragon(data, name);
    if (!dragon) throw new Error(`${label} contains unknown dragon: ${name}`);
    return dragon;
  });
  if (new Set(dragons.map(item => item.slug)).size !== 3) throw new Error(`${label} must contain three distinct dragons.`);
  const troop = [...TROOPS].find(item => item.toLowerCase() === troopPart.trim().toLowerCase());
  if (!troop) throw new Error(`${label} contains unknown troop type: ${troopPart.trim()}`);
  return { dragons, troop };
}

function progression(dragon, options) {
  return {
    slug: dragon.slug,
    owned: true,
    level: options.level,
    stars: options.stars,
    habit_levels: Object.fromEntries(
      dragon.abilities.filter(ability => ability.kind === "habit").map(ability => [ability.client_key, options.habitLevel])
    ),
  };
}

function enemySlots(formation, options) {
  return formation.dragons.map((dragon, index) => ({
    dragon: dragon.slug,
    name: dragon.name,
    breed: dragon.breed,
    lane: LANES[index],
    ...progression(dragon, options),
  }));
}

function candidateFormation(data, formation, threats, enemies, options) {
  return formation.dragons.map((dragon, index) => candidateEvidence(
    data,
    dragon,
    threats,
    progression(dragon, options),
    LANES[index],
    enemies,
  ));
}

function roundNumberSet(result) {
  return [...new Set([
    ...result.combatHorizon.opening,
    ...result.combatHorizon.late,
  ])];
}

function branchOpportunityEstimates(data, candidate, options) {
  const estimates = [];
  candidate.dragons.forEach((dragon, index) => {
    const saved = progression(dragon, options);
    for (const ability of activeAbilities(data, dragon, saved, LANES[index])) {
      for (const operation of operationRecords(data, ability, saved)) {
        if (operation.chance_percent == null) continue;
        const rounds = roundsFor(data, ability, operation.exact_context, operation.schedules);
        const opportunities = Math.max(rounds?.length || 0, 1);
        const probability = Number(operation.chance_percent) / 100;
        estimates.push({
          dragon: dragon.name,
          ability: ability.name,
          effect_id: operation.effect_id,
          operation: operation.operation,
          chance_percent_per_opportunity: Number(operation.chance_percent),
          documented_rounds: rounds || [],
          opportunities_in_first_cycle: opportunities,
          expected_activations_if_independent_and_eligible: opportunities * probability,
          probability_at_least_once_if_independent_and_eligible: 1 - ((1 - probability) ** opportunities),
          caveat: "Assumes an eligible target/prerequisite at every opportunity and independent checks; not a predicted battle outcome.",
        });
      }
    }
  });
  return estimates;
}

function summarizeResult(data, candidate, result, options) {
  return {
    formation: {
      troop_type: candidate.troop,
      left_flank: candidate.dragons[0].name,
      vanguard: candidate.dragons[1].name,
      right_flank: candidate.dragons[2].name,
    },
    threat_count: result.threats.length,
    direct_coverage_count: result.covered.length,
    conditional_coverage_count: result.conditionalCovered.length,
    direct_coverage_ratio: result.coverage,
    covered_threats: result.threats.filter(item => result.covered.includes(item.id)).map(item => item.name),
    conditional_threats: result.threats.filter(item => result.conditionalCovered.includes(item.id)).map(item => item.name),
    uncovered_threats: result.threats.filter(item => !result.covered.includes(item.id) && !result.conditionalCovered.includes(item.id)).map(item => item.name),
    troop_matchup: result.troop,
    explicit_synergies: result.synergies,
    lane_evidence: result.laneNotes,
    pivotal_habit_reliability: result.habitReliability,
    branch_opportunity_estimates: branchOpportunityEstimates(data, candidate, options),
    combat_horizon: result.combatHorizon,
    diagnostic_breakdown: result.breakdown,
    diagnostic_proxy_score: result.score,
    scheduled_activity_summary: roundNumberSet(result),
  };
}

export function simulate(data, options) {
  if (options.strawmen.length < 1 || options.strawmen.length > 2) throw new Error("Supply one or two --strawman formations.");
  if (options.candidates.length < 1 || options.candidates.length > 8) throw new Error("Supply between one and eight --candidate formations.");
  if (!Number.isInteger(options.level) || options.level < 1) throw new Error("--level must be a positive integer.");
  if (!Number.isInteger(options.stars) || options.stars < 1 || options.stars > 10) throw new Error("--stars must be an integer from 1 to 10.");
  if (!Number.isInteger(options.habitLevel) || options.habitLevel < 1 || options.habitLevel > 5) throw new Error("--habit-level must be an integer from 1 to 5.");

  const strawmen = options.strawmen.map((spec, index) => parseFormationSpec(data, spec, `strawman ${index + 1}`));
  const candidates = options.candidates.map((spec, index) => parseFormationSpec(data, spec, `candidate ${index + 1}`));
  const scenarios = strawmen.map((strawman, index) => {
    const enemies = enemySlots(strawman, options);
    const threats = extractThreats(data, enemies);
    return {
      id: `strawman-${index + 1}`,
      formation: {
        troop_type: strawman.troop,
        left_flank: strawman.dragons[0].name,
        vanguard: strawman.dragons[1].name,
        right_flank: strawman.dragons[2].name,
      },
      threats: threats.map(item => ({ id: item.id, category: item.category, name: item.name, source_count: item.sources.length })),
      candidates: candidates.map(candidate => {
        const formation = candidateFormation(data, candidate, threats, enemies, options);
        return summarizeResult(data, candidate, scoreFormation(data, formation, threats, strawman.troop, options.objective, candidate.troop), options);
      }),
    };
  });

  const robustness = candidates.map(candidate => {
    const signature = `${candidate.dragons.map(item => item.name).join(" / ")} | ${candidate.troop}`;
    const results = scenarios.map(scenario => scenario.candidates.find(item => (
      item.formation.left_flank === candidate.dragons[0].name
      && item.formation.vanguard === candidate.dragons[1].name
      && item.formation.right_flank === candidate.dragons[2].name
      && item.formation.troop_type === candidate.troop
    )));
    const ratios = results.map(item => item.direct_coverage_ratio);
    const scores = results.map(item => item.diagnostic_proxy_score);
    return {
      candidate: signature,
      minimum_direct_coverage_ratio: Math.min(...ratios),
      mean_direct_coverage_ratio: ratios.reduce((sum, value) => sum + value, 0) / ratios.length,
      minimum_diagnostic_proxy_score: Math.min(...scores),
      mean_diagnostic_proxy_score: scores.reduce((sum, value) => sum + value, 0) / scores.length,
      has_troop_disadvantage: results.some(item => item.troop_matchup.disadvantage),
      unresolved_or_conditional_threats: [...new Set(results.flatMap(item => [...item.conditional_threats, ...item.uncovered_threats]))],
    };
  }).sort((left, right) => (
    right.minimum_direct_coverage_ratio - left.minimum_direct_coverage_ratio
    || right.mean_direct_coverage_ratio - left.mean_direct_coverage_ratio
    || right.minimum_diagnostic_proxy_score - left.minimum_diagnostic_proxy_score
    || left.candidate.localeCompare(right.candidate)
  ));

  return {
    metadata: {
      model: "mechanics_constrained_counter_comparison_v1",
      progression_assumption: { level: options.level, stars: options.stars, habit_level: options.habitLevel },
      objective: options.objective,
      evidence_source: path.relative(ROOT, DATA_PATH).replaceAll("\\", "/"),
    },
    limitations: [
      "This is a mechanics-coverage and timing comparison, not a battle-outcome or win-rate simulation.",
      "Diagnostic proxy scores are search aids, not universal formation strength values.",
      "No hidden damage, Recovery, troop-advantage, action-order, target-tiebreak, stacking, or Cleanse-priority formula is invented.",
      "Chance-based effects remain reliability evidence; the output does not claim that any proc occurs in a particular battle.",
      "At-least-once and expected-activation estimates assume independent checks and an eligible target/prerequisite at every documented opportunity.",
    ],
    scenarios,
    cross_strawman_robustness: robustness,
  };
}

function main() {
  try {
    const options = parseArgs(process.argv.slice(2));
    if (options.help) {
      process.stdout.write(`${usage()}\n`);
      return 0;
    }
    const data = JSON.parse(fs.readFileSync(DATA_PATH, "utf8"));
    const output = simulate(data, options);
    process.stdout.write(`${JSON.stringify(output, null, options.pretty ? 2 : 0)}\n`);
    return 0;
  } catch (error) {
    process.stderr.write(`strategist-simulator: ${error.message}\n\n${usage()}\n`);
    return 2;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exitCode = main();
