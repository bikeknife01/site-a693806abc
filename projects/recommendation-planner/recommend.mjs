#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  LANES,
  TROOPS,
  activeAbilities,
  abilityEligible,
  candidateEvidence,
  eligibleDamageEvents,
  eligibleExactText,
  extractThreats,
  operationRecords,
  roundsFor,
  scoreFormation,
} from "../counter-picking-assistant/src/engine.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../..");
const DATA_PATH = path.join(ROOT, "projects/game-data-encyclopedia/public/data/encyclopedia.json");
const BASELINES_PATH = path.join(ROOT, "data/common_formations.json");
const RECOMMENDATION_RULES_PATH = path.join(ROOT, "data/recommendation_rules.json");
const APPLICATION_KNOWLEDGE_PATH = path.join(ROOT, "data/dragon_application_knowledge.json");
const GAME_MECHANICS_PATH = path.join(ROOT, "data/game_mechanics.json");
const DEFAULT_MAX_FINALISTS = 12;
const COMBAT_TROOPS = TROOPS.filter(troop => troop !== "Siege");
const APPLICATION_DRAGONS = new Map(JSON.parse(fs.readFileSync(APPLICATION_KNOWLEDGE_PATH, "utf8")).dragons.map(dragon => [dragon.client_key, dragon]));
const DRAGONS_ARMY_UPGRADES = JSON.parse(fs.readFileSync(GAME_MECHANICS_PATH, "utf8")).progression?.dragon_army_capacity_upgrades?.upgrades || {};
const DRAGONS_ARMY_TIERS = ["I", "II", "III", "IV"];
const RECOMMENDATION_RULES = JSON.parse(fs.readFileSync(RECOMMENDATION_RULES_PATH, "utf8"));
const COMPETITIVE_POLICY = RECOMMENDATION_RULES.competitive_viability;
const REVIEWED_RARE_EXCEPTIONS = new Set(COMPETITIVE_POLICY.reviewed_rare_exceptions.map(item => item.dragon_slug));

const unique = values => [...new Set(values)];
const sum = values => values.reduce((total, value) => total + value, 0);
const round = value => Math.round(value * 10000) / 10000;

export function parseArgs(argv) {
  const options = { input: null, output: null, format: "json", pretty: false, maxFinalists: DEFAULT_MAX_FINALISTS };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--input") options.input = argv[++index];
    else if (arg === "--output") options.output = argv[++index];
    else if (arg === "--format") options.format = argv[++index];
    else if (arg === "--max-finalists") options.maxFinalists = Number(argv[++index]);
    else if (arg === "--pretty") options.pretty = true;
    else if (arg === "--help" || arg === "-h") options.help = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  return options;
}

function usage() {
  return [
    "Usage:",
    "  node projects/recommendation-planner/recommend.mjs --input scenario.json [--format json|markdown] [--output result] [--max-finalists 12] [--pretty]",
    "",
    "The scenario format is documented in projects/recommendation-planner/README.md.",
  ].join("\n");
}

function lookupDragon(data, value) {
  const key = String(value || "").trim().toLowerCase();
  return data.dragons.find(dragon => dragon.slug.toLowerCase() === key || dragon.name.toLowerCase() === key);
}

function normalizeHabitLevels(raw) {
  if (raw == null) return {};
  if (typeof raw !== "object" || Array.isArray(raw)) throw new Error("habit_levels must be an object keyed by client ability key.");
  const result = {};
  for (const [key, value] of Object.entries(raw)) {
    const level = Number(value);
    if (!Number.isInteger(level) || level < 0 || level > 5) throw new Error(`Habit level for ${key} must be an integer from 0 to 5.`);
    result[key] = level;
  }
  return result;
}

function normalizeProgression(data, raw, label, { requireOwned = true } = {}) {
  const dragon = lookupDragon(data, raw?.slug ?? raw?.dragon ?? raw?.name);
  if (!dragon) throw new Error(`${label} has an unknown dragon: ${raw?.slug ?? raw?.dragon ?? raw?.name ?? "(missing)"}`);
  const level = Number(raw.level);
  const stars = Number(raw.stars);
  if (!Number.isInteger(level) || level < 1 || level > 50) throw new Error(`${label} level must be an integer from 1 to 50.`);
  if (!Number.isInteger(stars) || stars < 1 || stars > 10) throw new Error(`${label} stars must be an integer from 1 to 10.`);
  const power = raw.power == null ? null : Number(raw.power);
  if (power != null && (!Number.isFinite(power) || power < 0)) throw new Error(`${label} power must be a non-negative number when supplied.`);
  const displayedStars = raw.displayed_stars == null ? null : raw.displayed_stars;
  if (displayedStars != null) {
    const color = String(displayedStars.color || "").toLowerCase();
    const count = Number(displayedStars.count);
    if (!(["yellow", "red"].includes(color)) || !Number.isInteger(count) || count < 1 || count > 5) throw new Error(`${label} displayed_stars must use yellow or red with a count from 1 to 5.`);
    const normalized = color === "red" ? 5 + count : count;
    if (normalized !== stars) throw new Error(`${label} displayed_stars resolves to Rank ${normalized}, not declared Rank ${stars}.`);
  }
  return {
    slug: dragon.slug,
    owned: requireOwned ? raw.owned !== false : undefined,
    level,
    stars,
    power,
    habit_levels: normalizeHabitLevels(raw.habit_levels),
    assumed: Boolean(raw.assumed),
    displayed_stars: displayedStars == null ? null : { color: String(displayedStars.color).toLowerCase(), count: Number(displayedStars.count) },
    progression_source: raw.progression_source || raw.source || "declared",
    progression_confidence: raw.progression_confidence || raw.confidence || "unspecified",
  };
}

function profileEntries(input) {
  if (Array.isArray(input.roster)) return input.roster;
  if (input.profile?.dragons && typeof input.profile.dragons === "object") {
    return Object.entries(input.profile.dragons).map(([slug, entry]) => ({ slug, ...entry }));
  }
  throw new Error("Supply roster as an array, or profile.dragons as a Dragonfire player-profile object.");
}

function normalizeDragonsArmySkill(value) {
  const normalized = String(value ?? "none").trim().toUpperCase().replace(/^DRAGON'?S\s+ARMY\s+/, "");
  if (["", "NONE", "0"].includes(normalized)) return "none";
  if (!DRAGONS_ARMY_TIERS.includes(normalized)) throw new Error("Dragon's Army current_skill must be none, I, II, III, or IV.");
  return normalized;
}

function dragonsArmyProfile(input) {
  const supplied = input.profile?.stronghold?.dragons_army ?? input.stronghold?.dragons_army;
  if (supplied != null && (typeof supplied !== "object" || Array.isArray(supplied))) throw new Error("stronghold.dragons_army must be an object when supplied.");
  const raw = supplied || {};
  const currentSkill = normalizeDragonsArmySkill(raw.current_skill ?? raw.skill);
  const currentLevel = Number(raw.current_level ?? raw.level ?? 0);
  if (!Number.isInteger(currentLevel) || currentLevel < 0 || currentLevel > 5) throw new Error("Dragon's Army current_level must be an integer from 0 to 5.");
  if (currentSkill === "none" && currentLevel !== 0) throw new Error("Dragon's Army current_level must be 0 when current_skill is none.");
  const perTier = tier => Number(DRAGONS_ARMY_UPGRADES[`Dragon Army ${tier}`]?.troops_per_level);
  if (DRAGONS_ARMY_TIERS.some(tier => !Number.isFinite(perTier(tier)))) throw new Error("Canonical Dragon's Army capacity rules are incomplete.");
  const tierIndex = DRAGONS_ARMY_TIERS.indexOf(currentSkill);
  const priorBonus = tierIndex < 0 ? 0 : DRAGONS_ARMY_TIERS.slice(0, tierIndex).reduce((total, tier) => total + perTier(tier) * 5, 0);
  const troopsPerLevel = currentSkill === "none" ? 0 : perTier(currentSkill);
  const currentBonus = troopsPerLevel * currentLevel;
  const additionalPerDragon = priorBonus + currentBonus;
  if (raw.additional_troops_per_dragon != null && Number(raw.additional_troops_per_dragon) !== additionalPerDragon) {
    throw new Error(`Dragon's Army additional_troops_per_dragon must be ${additionalPerDragon} for ${currentSkill} level ${currentLevel}.`);
  }
  return {
    current_skill: currentSkill,
    current_level: currentLevel,
    additional_troops_per_dragon: additionalPerDragon,
    additional_troops_per_three_dragon_formation: additionalPerDragon * 3,
    provenance: raw.provenance || (supplied ? "unspecified" : "assumed"),
    basis: raw.basis || (supplied ? "declared" : "planner_default_assumption"),
  };
}

function capacitySensitiveObjective(objective) {
  return ["highest_tile", "highest_tiles", "troop_preservation", "preserve_troops", "minimize_troop_loss", "minimise_troop_loss"].includes(String(objective).toLowerCase().replaceAll("-", "_").replaceAll(" ", "_"));
}

function troopPreservationObjective(objective) {
  return ["troop_preservation", "preserve_troops", "minimize_troop_loss", "minimise_troop_loss"].includes(String(objective).toLowerCase().replaceAll("-", "_").replaceAll(" ", "_"));
}

function competitiveContext(input, roster, objective) {
  const requested = String(input.competitive_context || COMPETITIVE_POLICY.default_context).toLowerCase();
  if (!["auto", "endgame", "unrestricted"].includes(requested)) throw new Error("competitive_context must be auto, endgame, or unrestricted.");
  const threshold = COMPETITIVE_POLICY.auto_endgame_threshold;
  const matureDragonCount = roster.filter(entry => entry.level >= threshold.minimum_level && entry.stars >= threshold.minimum_star_rank).length;
  const resolved = requested === "auto"
    ? matureDragonCount >= threshold.minimum_owned_dragons_at_or_above_threshold ? "endgame" : "unrestricted"
    : requested;
  return {
    requested,
    resolved,
    inference: requested === "auto" ? {
      mature_dragon_count: matureDragonCount,
      minimum_owned_dragons: threshold.minimum_owned_dragons_at_or_above_threshold,
      minimum_level: threshold.minimum_level,
      minimum_star_rank: threshold.minimum_star_rank,
    } : null,
    allow_unproven_rare: Boolean(input.allow_unproven_rare),
    siege_scoped: ["poi", "siege"].includes(String(objective).toLowerCase().replaceAll("-", "_").replaceAll(" ", "_")),
  };
}

export function validatePlannerInput(data, input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) throw new Error("Planner input must be a JSON object.");
  const objective = String(input.objective || "pvp");
  const availableTroops = input.available_troops == null
    ? (objective === "poi" ? [...TROOPS] : [...COMBAT_TROOPS])
    : unique(input.available_troops.map(value => TROOPS.find(troop => troop.toLowerCase() === String(value).toLowerCase()) || String(value)));
  const unknownTroops = availableTroops.filter(troop => !TROOPS.includes(troop));
  if (unknownTroops.length) throw new Error(`Unknown available troop type(s): ${unknownTroops.join(", ")}`);
  if (!availableTroops.length) throw new Error("available_troops must contain at least one troop type.");

  const roster = profileEntries(input).map((entry, index) => normalizeProgression(data, entry, `roster entry ${index + 1}`));
  const duplicateRoster = roster.find((entry, index) => roster.findIndex(other => other.slug === entry.slug) !== index);
  if (duplicateRoster) throw new Error(`Roster contains duplicate dragon: ${duplicateRoster.slug}`);
  const owned = roster.filter(entry => entry.owned !== false);
  if (owned.length < 3) throw new Error("At least three owned dragons are required.");

  const enemyInput = input.enemy || {};
  const enemyTroop = enemyInput.troop_type == null ? null : TROOPS.find(troop => troop.toLowerCase() === String(enemyInput.troop_type).toLowerCase());
  if (enemyInput.troop_type != null && !enemyTroop) throw new Error(`Unknown enemy troop type: ${enemyInput.troop_type}`);
  const enemyFormation = enemyInput.formation || [];
  if (!Array.isArray(enemyFormation) || enemyFormation.length > 3) throw new Error("enemy.formation must be an array containing at most three lanes.");
  const enemies = enemyFormation.map((entry, index) => {
    const progression = normalizeProgression(data, entry, `enemy entry ${index + 1}`, { requireOwned: false });
    const lane = LANES.find(value => value.toLowerCase() === String(entry.lane || LANES[index]).toLowerCase());
    if (!lane) throw new Error(`enemy entry ${index + 1} has an unknown lane: ${entry.lane}`);
    return { ...progression, dragon: progression.slug, lane };
  });
  if (new Set(enemies.map(entry => entry.lane)).size !== enemies.length) throw new Error("Enemy lanes must be distinct.");

  const maxFinalists = input.max_finalists == null ? DEFAULT_MAX_FINALISTS : Number(input.max_finalists);
  if (!Number.isInteger(maxFinalists) || maxFinalists < 1 || maxFinalists > 100) throw new Error("max_finalists must be an integer from 1 to 100.");
  const competitive = competitiveContext(input, owned, objective);
  return {
    objective,
    availableTroops,
    availableTroopsSource: input.available_troops == null ? "planner_default_assumption" : "explicit_request",
    roster: owned,
    enemies,
    enemyTroop,
    maxFinalists,
    dragonsArmy: dragonsArmyProfile(input),
    powerComparable: owned.every(entry => entry.power != null),
    capacitySensitive: capacitySensitiveObjective(objective),
    troopPreservation: troopPreservationObjective(objective),
    competitive,
  };
}

function permutations(items) {
  return [
    [items[0], items[1], items[2]], [items[0], items[2], items[1]], [items[1], items[0], items[2]],
    [items[1], items[2], items[0]], [items[2], items[0], items[1]], [items[2], items[1], items[0]],
  ];
}

function combinations(items) {
  const result = [];
  for (let i = 0; i < items.length - 2; i += 1) {
    for (let j = i + 1; j < items.length - 1; j += 1) {
      for (let k = j + 1; k < items.length; k += 1) result.push([items[i], items[j], items[k]]);
    }
  }
  return result;
}

function evidenceReference(data, ability) {
  const dragonIndex = data.dragons.findIndex(dragon => dragon.abilities.some(candidate => candidate.id === ability.id));
  const abilityIndex = dragonIndex < 0 ? -1 : data.dragons[dragonIndex].abilities.findIndex(candidate => candidate.id === ability.id);
  return {
    ability_id: ability.id,
    canonical_source: ability.evidence?.source || null,
    encyclopedia_pointer: dragonIndex < 0 || abilityIndex < 0 ? null : `/dragons/${dragonIndex}/abilities/${abilityIndex}`,
    evidence_class: ability.evidence?.class || null,
    confidence: ability.evidence?.confidence || null,
    source_version: ability.evidence?.source_version || null,
  };
}

function provenanceFor(data, result) {
  const abilities = new Map();
  const dragonProfiles = result.formation.map(pick => {
    const dragonIndex = data.dragons.findIndex(dragon => dragon.id === pick.dragon.id);
    const sourceAbility = pick.dragon.abilities.find(ability => ability.evidence?.source);
    return {
      entity_type: "dragon_profile",
      dragon_id: pick.dragon.id,
      canonical_source: sourceAbility?.evidence?.source || null,
      encyclopedia_pointer: dragonIndex < 0 ? null : `/dragons/${dragonIndex}`,
      evidence_class: sourceAbility?.evidence?.class || null,
      confidence: sourceAbility?.evidence?.confidence || null,
      source_version: sourceAbility?.evidence?.source_version || null,
    };
  });
  for (const pick of result.formation) {
    for (const counter of pick.counters) {
      const ability = pick.dragon.abilities.find(item => item.id === counter.ability_id);
      if (ability) abilities.set(ability.id, ability);
    }
  }
  for (const synergy of result.synergies) {
    for (const pick of result.formation) {
      for (const ability of pick.abilities) {
        if (ability.name === synergy.producerAbility || ability.name === synergy.consumerAbility) abilities.set(ability.id, ability);
      }
    }
  }
  return [...dragonProfiles, ...[...abilities.values()].map(ability => ({ entity_type: "ability", ...evidenceReference(data, ability) }))];
}

function eventTimeline(data, formation, horizon = 10) {
  const events = [];
  for (const pick of formation) {
    for (const ability of activeAbilities(data, pick.dragon, pick.progression, pick.lane)) {
      const abilityRounds = roundsFor(data, ability);
      const operations = operationRecords(data, ability, pick.progression);
      if (abilityRounds?.length) {
        events.push({
          dragon: pick.dragon.name,
          lane: pick.lane,
          ability: ability.name,
          kind: "ability_schedule",
          trigger_rounds: abilityRounds.filter(value => value <= horizon),
          duration_rounds: null,
          active_windows: [],
          chance_percent: null,
          evidence: evidenceReference(data, ability),
        });
      }
      for (const operation of operations) {
        const triggerRounds = (roundsFor(data, ability, operation.exact_context, operation.schedules) || abilityRounds || []).filter(value => value <= horizon);
        const duration = operation.duration_rounds == null ? null : Number(operation.duration_rounds);
        events.push({
          dragon: pick.dragon.name,
          lane: pick.lane,
          ability: ability.name,
          kind: `status_${operation.operation}`,
          effect_id: operation.effect_id,
          trigger_rounds: triggerRounds,
          duration_rounds: duration,
          active_windows: duration == null ? [] : triggerRounds.map(start => ({ start, end: Math.min(horizon, start + duration - 1) })),
          chance_percent: operation.chance_percent,
          opportunity_count: Math.max(triggerRounds.length, 1),
          expected_activations_if_independent_and_eligible: operation.chance_percent == null ? null : round(Math.max(triggerRounds.length, 1) * Number(operation.chance_percent) / 100),
          probability_at_least_once_if_independent_and_eligible: operation.chance_percent == null ? null : round(1 - ((1 - Number(operation.chance_percent) / 100) ** Math.max(triggerRounds.length, 1))),
          max_stacks: operation.max_stacks ?? null,
          exact_text: operation.exact_context,
          evidence: evidenceReference(data, ability),
        });
      }
    }
  }
  const byRound = Array.from({ length: horizon + 1 }, (_, roundNumber) => ({
    round: roundNumber,
    triggers: events.filter(event => event.trigger_rounds.includes(roundNumber)).map(event => `${event.dragon}: ${event.ability}`),
    active_effects: events.filter(event => event.active_windows.some(window => roundNumber >= window.start && roundNumber <= window.end)).map(event => `${event.dragon}: ${event.effect_id}`),
  })).filter(entry => entry.triggers.length || entry.active_effects.length);
  const effectIds = unique(events.map(event => event.effect_id).filter(Boolean));
  const overlapBounds = effectIds.map(effectId => {
    const effectEvents = events.filter(event => event.effect_id === effectId);
    const overlaps = Array.from({ length: horizon + 1 }, (_, roundNumber) => ({
      round: roundNumber,
      active_sources: effectEvents.filter(event => event.active_windows.some(window => roundNumber >= window.start && roundNumber <= window.end)).length,
    }));
    const peak = Math.max(...overlaps.map(item => item.active_sources));
    return {
      effect_id: effectId,
      peak_simultaneous_documented_windows: peak,
      peak_rounds: overlaps.filter(item => item.active_sources === peak && peak > 0).map(item => item.round),
      documented_stack_ceilings: unique(effectEvents.map(event => event.max_stacks).filter(value => value != null)),
      caveat: "Overlapping documented windows do not establish that effects stack; consult the listed stack ceilings and preserve unknown stacking rules.",
    };
  });
  return {
    horizon_rounds: horizon,
    events,
    by_round: byRound,
    overlap_bounds: overlapBounds,
    probability_caveat: "Expected and at-least-once values assume independent checks and an eligible target or prerequisite at every opportunity; they are not predicted battle outcomes.",
  };
}

function targetCoverageWeight(text) {
  if (/\b(?:all|3) (?:other )?Allies\b/i.test(text)) return 1;
  if (/\b2 (?:other )?Allies\b/i.test(text)) return 0.75;
  if (/\b(?:1|one) (?:other )?Ally\b/i.test(text)) return 0.4;
  if (/\b(?:yourself|your)\b/i.test(text)) return 0.35;
  return 0.5;
}

function enemyTargetWeight(text) {
  if (/\b(?:3|all) Enemies\b/i.test(text)) return 1;
  if (/\b2 Enemies\b/i.test(text)) return 0.75;
  if (/\b(?:1|one|the) Enemy\b/i.test(text)) return 0.5;
  return 0.5;
}

function percentageValues(text, pattern) {
  return [...String(text).matchAll(pattern)].map(match => Number(match[1])).filter(Number.isFinite);
}

function objectiveQualityAssessment(data, result) {
  const components = [];
  const seenDamage = new Set();
  const seenAmplification = new Set();
  let damage = 0;
  let amplification = 0;
  for (const pick of result.formation) for (const ability of pick.abilities) {
    for (const event of eligibleDamageEvents(ability, pick.progression)) {
      const text = event.exact_context || "";
      const key = `${pick.dragon.slug}|${text}`;
      if (seenDamage.has(key) || !/\bdeal\b[^.]{0,180}\bDamage\b/i.test(text) || /\b(?:reduce|received)\b/i.test(text)) continue;
      seenDamage.add(key);
      const rates = percentageValues(text, /Damage Rate:\s*\+(\d+(?:\.\d+)?)%/gi);
      if (!rates.length) continue;
      const chance = text.match(/(\d+(?:\.\d+)?)%\s+chance/i);
      const reliability = chance ? Number(chance[1]) / 100 : /\b(?:if|when)\b/i.test(text) ? 0.5 : 1;
      const magnitude = sum(rates);
      const score = round((magnitude / 25) * reliability * enemyTargetWeight(text));
      damage += score;
      components.push({ dragon: pick.dragon.name, ability: ability.name, kind: "damage", magnitude_percent: magnitude, reliability, score, exact_text: text });
    }
    for (const text of eligibleExactText(ability, pick.progression)) {
      const key = `${pick.dragon.slug}|${text}`;
      if (seenAmplification.has(key) || !/Increase[^.]{0,160}Damage Dealt by \+/i.test(text)) continue;
      seenAmplification.add(key);
      const values = percentageValues(text, /Damage Dealt by \+(\d+(?:\.\d+)?)%/gi);
      if (!values.length) continue;
      const chance = text.match(/(\d+(?:\.\d+)?)%\s+chance/i);
      const reliability = chance ? Number(chance[1]) / 100 : /\b(?:if|when)\b/i.test(text) ? 0.5 : 1;
      const magnitude = sum(values);
      const score = round((magnitude / 10) * reliability * targetCoverageWeight(text));
      amplification += score;
      components.push({ dragon: pick.dragon.name, ability: ability.name, kind: "damage_amplification", magnitude_percent: magnitude, reliability, score, exact_text: text });
    }
  }
  return { damage: round(damage), amplification: round(amplification), components };
}

function preservationAssessment(data, result) {
  const beneficial = new Set(["effect:recovery", "effect:protect", "effect:resistance", "effect:evade", "effect:cleanse"]);
  const weights = { "effect:recovery": 4, "effect:protect": 3, "effect:resistance": 3, "effect:evade": 2, "effect:cleanse": 2 };
  const components = [];
  let effectScore = 0;
  let mitigationScore = 0;
  let vulnerabilityPenalty = 0;
  let unknownHabitEffects = 0;
  const seenEffects = new Set();
  const seenText = new Set();
  for (const pick of result.formation) for (const ability of pick.abilities) {
    const habitLevel = ability.kind === "habit" ? pick.progression.habit_levels?.[ability.client_key] : null;
    const habitInvestmentKnown = ability.kind !== "habit" || Number.isInteger(Number(habitLevel)) && Number(habitLevel) > 0;
    for (const operation of operationRecords(data, ability, pick.progression)) {
      if (operation.operation !== "applies" || !beneficial.has(operation.effect_id)) continue;
      const effectKey = `${pick.dragon.slug}|${operation.effect_id}|${operation.exact_context}`;
      if (seenEffects.has(effectKey)) continue;
      seenEffects.add(effectKey);
      const reliability = operation.chance_known === false ? 0 : operation.chance_percent == null ? 1 : Number(operation.chance_percent) / 100;
      if (operation.chance_known === false) unknownHabitEffects += 1;
      const score = round((weights[operation.effect_id] || 0) * reliability * targetCoverageWeight(operation.exact_context || ""));
      effectScore += score;
      components.push({ dragon: pick.dragon.name, ability: ability.name, kind: "beneficial_effect", effect_id: operation.effect_id, score, chance_percent: operation.chance_percent, chance_known: operation.chance_known !== false, exact_text: operation.exact_context });
    }
    for (const text of eligibleExactText(ability, pick.progression)) {
      const textKey = `${pick.dragon.slug}|${text}`;
      if (seenText.has(textKey)) continue;
      seenText.add(textKey);
      const reducesReceived = /(?:reduce|decrease)[^.]{0,120}Damage Received/i.test(text);
      const reducesEnemyDealt = /(?:reduce|decrease)[^.]{0,120}(?:Enemy|Enemies)[^.]{0,120}Damage Dealt/i.test(text) || /(?:reduce|decrease)[^.]{0,120}(?:Physical|Tactical|Fire) Damage Dealt of [^.]{0,80}Enemy/i.test(text);
      if (reducesReceived || reducesEnemyDealt) {
        const magnitudes = percentageValues(text, /Damage (?:Received|Dealt)[^.]{0,80}(?:by\s+)?-(\d+(?:\.\d+)?)%/gi);
        const magnitudeWeight = magnitudes.length ? Math.max(...magnitudes) / 10 : 1;
        const score = round(Math.max(1, magnitudeWeight) * (habitInvestmentKnown ? 1 : 0.5));
        mitigationScore += score;
        if (!habitInvestmentKnown) unknownHabitEffects += 1;
        components.push({ dragon: pick.dragon.name, ability: ability.name, kind: "mitigation", score, habit_investment_known: habitInvestmentKnown, exact_text: text });
      }
      if (/Increase (?:your|the source[^.]*)?[^.]{0,80}Damage Received by \+/i.test(text)) {
        vulnerabilityPenalty += 2;
        components.push({ dragon: pick.dragon.name, ability: ability.name, kind: "self_vulnerability", score: -2, exact_text: text });
      }
    }
  }
  return {
    score: round(effectScore + mitigationScore - vulnerabilityPenalty),
    tier: effectScore + mitigationScore - vulnerabilityPenalty >= 6 ? 3 : effectScore + mitigationScore - vulnerabilityPenalty >= 3 ? 2 : effectScore + mitigationScore - vulnerabilityPenalty > 0 ? 1 : 0,
    tier_label: effectScore + mitigationScore - vulnerabilityPenalty >= 6 ? "strong" : effectScore + mitigationScore - vulnerabilityPenalty >= 3 ? "supported" : effectScore + mitigationScore - vulnerabilityPenalty > 0 ? "limited" : "none",
    beneficial_effect_score: round(effectScore),
    mitigation_score: mitigationScore,
    vulnerability_penalty: vulnerabilityPenalty,
    unknown_habit_effects: unknownHabitEffects,
    components,
  };
}

function objectiveAssessment(data, result, objective, coverageCounts = null, preservation = null) {
  const normalized = String(objective || "pvp").toLowerCase().replaceAll("-", "_").replaceAll(" ", "_");
  const quality = objectiveQualityAssessment(data, result);
  const openingPressure = result.combatHorizon.opening.length;
  const latePressure = result.combatHorizon.late.length;
  const preservationValue = preservation?.score ?? preservationAssessment(data, result).score;
  let score = 0;
  if (["high_damage", "attack", "damage"].includes(normalized)) {
    score = quality.damage + quality.amplification + result.synergies.length * 2 + openingPressure * 0.5 + latePressure * 0.25 + result.troop.positive.length;
  } else if (["damage_and_survivability", "defense", "survivability"].includes(normalized)) {
    const offense = quality.damage + quality.amplification;
    score = offense + preservationValue + Math.min(offense, preservationValue) + result.synergies.length + result.troop.positive.length;
  } else if (troopPreservationObjective(normalized)) score = preservationValue;
  else if (["counter", "counter_specific"].includes(normalized)) {
    const counts = coverageCounts || coverageSummary(result);
    score = counts.direct * 4 + counts.probabilistic * 2 + counts.partial + (result.troop.advantage ? 3 : 0) - (result.troop.disadvantage ? 3 : 0);
  } else if (["poi", "siege"].includes(normalized)) score = result.troop.troop === "Siege" ? 5 + result.troop.positive.length : 0;
  return {
    score: round(score),
    method: "deduplicated_magnitude_reliability_aware_ordinal_v1",
    damage_quality: quality.damage,
    amplification_quality: quality.amplification,
    preservation_quality: preservationValue,
    components: quality.components,
  };
}

function competitiveViability(result, context) {
  const rare = result.formation.filter(pick => pick.dragon.rarity_tier === "Rare");
  const reviewed = rare.filter(pick => REVIEWED_RARE_EXCEPTIONS.has(pick.dragon.slug));
  const unsupported = rare.filter(pick => !REVIEWED_RARE_EXCEPTIONS.has(pick.dragon.slug));
  const siegeException = context.competitive.siege_scoped || result.troop.troop === "Siege";
  const gateActive = context.competitive.resolved === "endgame" && !context.competitive.allow_unproven_rare && !siegeException;
  const qualified = !gateActive || unsupported.length === 0;
  return {
    qualified,
    context: context.competitive.resolved,
    requested_context: context.competitive.requested,
    gate_applied: gateActive,
    allow_unproven_rare: context.competitive.allow_unproven_rare,
    siege_exception_applied: siegeException && rare.length > 0,
    reviewed_rare_exceptions: reviewed.map(pick => pick.dragon.name),
    unsupported_rare_dragons: unsupported.map(pick => pick.dragon.name),
    reason: qualified ? unsupported.length ? "Rare use is permitted by the selected context or explicit override." : "No unsupported Rare dragon is used." : `Endgame ordinary-combat policy does not qualify: ${unsupported.map(pick => pick.dragon.name).join(", ")}.`,
  };
}

function modeledArmyCapacity(pick, dragonsArmy) {
  const model = APPLICATION_DRAGONS.get(pick.dragon.slug)?.level_model;
  const baseArmySize = model?.base_stats_by_level?.max_army_size?.values_by_level?.[Number(pick.progression.level) - 1];
  const starScalar = model?.star_scalars?.max_army_size?.values_by_star?.[Number(pick.progression.stars) - 1];
  if (!Number.isFinite(baseArmySize)) return null;
  return {
    dragon: pick.dragon.name,
    dragon_slug: pick.dragon.slug,
    level: pick.progression.level,
    stars: pick.progression.stars,
    base_max_army_size: Number(baseArmySize),
    star_scalar: Number.isFinite(starScalar) ? Number(starScalar) : null,
    star_scalar_applied: false,
    capacity_formula_status: "level_curve_plus_dragons_army_only_star_formula_unverified",
    dragons_army_bonus: dragonsArmy.additional_troops_per_dragon,
    modeled_max_army_size: Number(baseArmySize) + dragonsArmy.additional_troops_per_dragon,
  };
}

function metricsFor(data, result, objective, context) {
  const coverageCounts = coverageSummary(result);
  const reliability = sum(result.formation.flatMap(pick => pick.counters).map(counter => {
    const assessment = assessResponse(counter);
    const chance = assessment.chance_percent == null ? 1 : assessment.chance_percent / 100;
    return assessment.state === "direct" ? 1 : assessment.state === "probabilistic" ? chance : chance * 0.25;
  }));
  const knownPowers = result.formation.map(pick => pick.progression.power).filter(value => value != null);
  const capacities = result.formation.map(pick => modeledArmyCapacity(pick, context.dragonsArmy));
  const preservation = preservationAssessment(data, result);
  const objectiveEvaluation = objectiveAssessment(data, result, objective, coverageCounts, preservation);
  return {
    direct_threat_coverage: result.threats.length ? coverageCounts.direct / result.threats.length : 0,
    covered_threat_count: coverageCounts.direct,
    conditional_threat_count: coverageCounts.probabilistic + coverageCounts.partial,
    probabilistic_threat_count: coverageCounts.probabilistic,
    partial_threat_count: coverageCounts.partial,
    counter_reliability: round(reliability),
    timing_alignment: result.breakdown.timing_alignment,
    explicit_synergy: result.breakdown.explicit_synergy,
    lane_fit: result.breakdown.lane_fit,
    troop_fit: result.breakdown.troop_fit,
    affinity_count: result.troop.positive.length,
    affinity_penalty_count: result.troop.negative.length,
    troop_disadvantage: result.troop.disadvantage ? 1 : 0,
    objective_fit: objectiveEvaluation.score,
    objective_assessment: objectiveEvaluation,
    competitive_viability: competitiveViability(result, context),
    troop_preservation: preservation,
    known_team_power: context.powerComparable && knownPowers.length === 3 ? sum(knownPowers) : null,
    modeled_team_capacity: capacities.every(Boolean) ? sum(capacities.map(item => item.modeled_max_army_size)) : null,
    minimum_modeled_dragon_capacity: capacities.every(Boolean) ? Math.min(...capacities.map(item => item.modeled_max_army_size)) : null,
    modeled_capacity_by_dragon: capacities,
    dragons_army_bonus_per_dragon: context.dragonsArmy.additional_troops_per_dragon,
    dragons_army: context.dragonsArmy,
    diagnostic_proxy_score: result.score,
  };
}

const MAXIMIZE = ["direct_threat_coverage", "objective_fit", "counter_reliability", "timing_alignment", "explicit_synergy", "lane_fit", "troop_fit", "affinity_count"];
const MINIMIZE = ["affinity_penalty_count", "troop_disadvantage"];

function dominates(left, right, { includePower, includeCapacity, includeMinimumCapacity }) {
  const maximize = [...MAXIMIZE, ...(includePower ? ["known_team_power"] : []), ...(includeCapacity ? ["modeled_team_capacity"] : []), ...(includeMinimumCapacity ? ["minimum_modeled_dragon_capacity"] : [])];
  const noWorse = maximize.every(key => left.metrics[key] >= right.metrics[key]) && MINIMIZE.every(key => left.metrics[key] <= right.metrics[key]);
  const better = maximize.some(key => left.metrics[key] > right.metrics[key]) || MINIMIZE.some(key => left.metrics[key] < right.metrics[key]);
  return noWorse && better;
}

function paretoFront(candidates, { includeCapacity = false, troopPreservation = false } = {}) {
  const includePower = candidates.length > 0 && candidates.every(candidate => candidate.metrics.known_team_power != null);
  const dimensions = { includePower, includeCapacity, includeMinimumCapacity: troopPreservation };
  const frontier = [];
  for (const candidate of candidates) {
    if (frontier.some(other => dominates(other, candidate, dimensions))) continue;
    for (let index = frontier.length - 1; index >= 0; index -= 1) {
      if (dominates(candidate, frontier[index], dimensions)) frontier.splice(index, 1);
    }
    frontier.push(candidate);
  }
  return frontier;
}

function policyCompare(left, right, { includeCapacity = false, troopPreservation = false } = {}) {
  const affinityDifference = left.metrics.affinity_count - right.metrics.affinity_count;
  let affinityAndSynergy = 0;
  if (affinityDifference === 0) affinityAndSynergy = right.metrics.explicit_synergy - left.metrics.explicit_synergy;
  else {
    const higherAffinity = affinityDifference > 0 ? left : right;
    const lowerAffinity = affinityDifference > 0 ? right : left;
    const affinityGap = Math.abs(affinityDifference);
    const synergyAdvantage = lowerAffinity.metrics.explicit_synergy - higherAffinity.metrics.explicit_synergy;
    const lowerAffinityOutweighs = synergyAdvantage > affinityGap;
    affinityAndSynergy = lowerAffinityOutweighs
      ? (lowerAffinity === left ? -1 : 1)
      : (higherAffinity === left ? -1 : 1);
  }
  const objectiveAndCapacity = troopPreservation
    ? (right.metrics.minimum_modeled_dragon_capacity ?? -1) - (left.metrics.minimum_modeled_dragon_capacity ?? -1)
      || right.metrics.troop_preservation.tier - left.metrics.troop_preservation.tier
      || (right.metrics.modeled_team_capacity ?? -1) - (left.metrics.modeled_team_capacity ?? -1)
      || right.metrics.objective_fit - left.metrics.objective_fit
    : right.metrics.objective_fit - left.metrics.objective_fit
      || (includeCapacity ? (right.metrics.modeled_team_capacity ?? -1) - (left.metrics.modeled_team_capacity ?? -1) : 0);
  return (
    Number(right.metrics.competitive_viability.qualified) - Number(left.metrics.competitive_viability.qualified)
    || right.metrics.direct_threat_coverage - left.metrics.direct_threat_coverage
    || left.metrics.troop_disadvantage - right.metrics.troop_disadvantage
    || objectiveAndCapacity
    || affinityAndSynergy
    || right.metrics.counter_reliability - left.metrics.counter_reliability
    || right.metrics.troop_fit - left.metrics.troop_fit
    || right.metrics.lane_fit - left.metrics.lane_fit
    || (right.metrics.known_team_power ?? -1) - (left.metrics.known_team_power ?? -1)
    || right.metrics.diagnostic_proxy_score - left.metrics.diagnostic_proxy_score
    || left.id.localeCompare(right.id)
  );
}

function candidateId(result) {
  return `${result.formation.map(pick => pick.dragon.slug).join("/")}|${result.troop.troop}`;
}

function decorateCandidate(data, result, objective, context) {
  return { id: candidateId(result), result, metrics: metricsFor(data, result, objective, context), provenance: provenanceFor(data, result) };
}

function summarizeCandidate(data, candidate, { includeTimeline = true } = {}) {
  const { result } = candidate;
  const threatCoverage = coverageMatrix(data, result);
  return {
    id: candidate.id,
    expert_prior: candidate.expert_prior || null,
    formation: {
      troop_type: result.troop.troop,
      left_flank: result.formation[0].dragon.name,
      vanguard: result.formation[1].dragon.name,
      right_flank: result.formation[2].dragon.name,
    },
    progression: result.formation.map(pick => ({ dragon: pick.dragon.name, slug: pick.dragon.slug, lane: pick.lane, ...pick.progression })),
    metrics: candidate.metrics,
    affinity_policy: affinityPolicyAttestation(candidate, { preferences: { affinity_policy: "perfect_unless_explicit_synergy" } }),
    troop_matchup: result.troop,
    troop_mechanics_evidence: {
      canonical_source: "data/game_mechanics.json",
      canonical_pointer: `/troop_types/${result.troop.troop.replaceAll("~", "~0").replaceAll("/", "~1")}`,
      encyclopedia_pointer: `/mechanics/troop_types/${result.troop.troop.replaceAll("~", "~0").replaceAll("/", "~1")}`,
    },
    covered_threats: threatCoverage.filter(row => row.state === "direct").map(row => row.threat),
    conditional_threats: threatCoverage.filter(row => ["probabilistic", "partial"].includes(row.state)).map(row => row.threat),
    uncovered_threats: threatCoverage.filter(row => row.state === "none").map(row => row.threat),
    explicit_synergies: result.synergies,
    lane_evidence: result.laneNotes,
    pivotal_habit_reliability: result.habitReliability,
    combat_horizon: result.combatHorizon,
    threat_coverage: threatCoverage,
    gate_report: gateReport(data, result),
    decision_evidence: decisionEvidence(data, result),
    risks: riskRegister(data, result, threatCoverage, null, candidate.metrics.dragons_army),
    timeline: includeTimeline ? eventTimeline(data, result.formation) : undefined,
    evidence: candidate.provenance,
  };
}

function gateState(ability, progression, lane) {
  if (abilityEligible(ability, { ...progression, lane })) return { state: "active", reason: null };
  if (ability.kind === "vanguard" && lane !== "Vanguard") return { state: "inactive", reason: "Requires Vanguard placement." };
  if (ability.unlock?.level && progression.level < ability.unlock.level) return { state: "locked", reason: `Requires Level ${ability.unlock.level}.` };
  if (ability.unlock?.star_rank && progression.stars < ability.unlock.star_rank) return { state: "locked", reason: `Requires Star Rank ${ability.unlock.star_rank}.` };
  if (ability.kind === "habit" && progression.habit_levels?.[ability.client_key] === 0) return { state: "inactive", reason: "Explicitly marked unavailable at Habit level 0." };
  return { state: "inactive", reason: "Unavailable under supplied progression." };
}

function gateReport(data, result) {
  return result.formation.flatMap(pick => pick.dragon.abilities.map(ability => {
    const gate = gateState(ability, pick.progression, pick.lane);
    return {
      dragon: pick.dragon.name,
      lane: pick.lane,
      ability: ability.name,
      ability_id: ability.id,
      kind: ability.kind,
      unlock: ability.unlock || {},
      habit_skill_level: ability.kind === "habit" ? (pick.progression.habit_levels?.[ability.client_key] ?? null) : null,
      ...gate,
      exact_text: eligibleExactText(ability, pick.progression),
      evidence: evidenceReference(data, ability),
    };
  }));
}

function assessResponse(counter) {
  const text = String(counter.exact_text || "");
  const chanceMatch = text.match(/(\d+(?:\.\d+)?)%\s+chance/i);
  const chance = counter.reliability?.chance_percent ?? (chanceMatch ? Number(chanceMatch[1]) : null);
  const qualifiers = [];
  if (counter.reliability?.unresolved) qualifiers.push("Unresolved source evidence or activation value.");
  if (chance != null && chance < 100) qualifiers.push(/each instance has a separate/i.test(text) ? `${chance}% chance for each eligible instance.` : `${chance}% activation chance when eligible.`);
  if (/excluding Basic Attacks/i.test(text)) qualifiers.push("Basic Attacks are excluded.");
  if (/\byour\b[^.]{0,100}Damage Received/i.test(text)) qualifiers.push("The mitigation applies only to the source dragon.");
  if (/\b(?:\d+|one|two|three) other Allies\b/i.test(text)) qualifiers.push("The source excludes itself and protects only the stated other allies.");
  if (/\b(?:up to \d+|\d+ (?:Enemy|Enemies|Ally|Allies)|selects 1 Enemy)\b/i.test(text)) qualifiers.push("Only the stated number of targets or effect instances can be affected.");
  if (/\b(?:same lane|within adjacency|left flank|right flank)\b/i.test(text)) qualifiers.push("The named lane or adjacency limits target scope.");
  if (/\b(?:when|if)\b/i.test(text)) qualifiers.push("An additional stated condition must occur.");
  if (/\bfor \d+ rounds?\b/i.test(text)) qualifiers.push("The response has a limited documented duration.");
  if (/\bgains\b|\beach stack\b|target's/i.test(text)) qualifiers.push("This payoff depends on a separate effect or stack being applied first.");
  if (counter.timing?.state === "delayed") qualifiers.push(counter.timing.note || "Response begins after the first documented threat window.");
  const limited = qualifiers.some(note => !note.includes("activation chance") && !note.includes("chance for each eligible instance"));
  const state = limited ? "partial" : chance != null && chance < 100 ? "probabilistic" : "direct";
  return { state, chance_percent: chance, qualifiers };
}

function coverageSummary(result) {
  const counts = { direct: 0, probabilistic: 0, partial: 0, none: 0 };
  for (const threat of result.threats) {
    const states = result.formation.flatMap(pick => pick.counters.filter(counter => counter.threat_id === threat.id).map(counter => assessResponse(counter).state));
    const state = ["direct", "probabilistic", "partial"].find(value => states.includes(value)) || "none";
    counts[state] += 1;
  }
  return counts;
}

function coverageMatrix(data, result) {
  const responseEntries = result.formation.flatMap(pick => pick.counters.map(counter => {
    const ability = pick.dragon.abilities.find(item => item.id === counter.ability_id);
    const assessment = assessResponse(counter);
    return {
      threat_id: counter.threat_id,
      dragon: pick.dragon.name,
      lane: pick.lane,
      ability: counter.ability,
      ability_id: counter.ability_id,
      exact_text: counter.exact_text,
      reliability: counter.reliability,
      timing: counter.timing,
      state: assessment.state,
      chance_percent: assessment.chance_percent,
      qualifiers: assessment.qualifiers,
      evidence: ability ? evidenceReference(data, ability) : null,
    };
  }));
  return result.threats.map(threat => {
    const responses = responseEntries.filter(entry => entry.threat_id === threat.id);
    const state = ["direct", "probabilistic", "partial"].find(value => responses.some(entry => entry.state === value)) || "none";
    const limitations = unique(responses.flatMap(entry => entry.qualifiers));
    return {
      threat_id: threat.id,
      threat: threat.name,
      category: threat.category,
      enemy_sources: threat.sources,
      state,
      responses,
      remaining_gap: state === "none" ? "No documented applicable response in the selected formation." : state === "direct" ? null : limitations.join(" ") || "The response does not guarantee coverage of every threat instance.",
    };
  });
}

function decisionEvidence(data, result) {
  const evidence = [{
    claim_type: "formation_selection",
    formation: result.formation.map(pick => ({ dragon: pick.dragon.name, lane: pick.lane })),
    troop_type: result.troop.troop,
    evidence: provenanceFor(data, result),
  }];
  for (const row of coverageMatrix(data, result)) for (const response of row.responses) {
    evidence.push({
      claim_type: "threat_response",
      threat: row.threat,
      state: row.state,
      dragon: response.dragon,
      lane: response.lane,
      ability: response.ability,
      ability_id: response.ability_id,
      exact_text: response.exact_text,
      reliability: response.reliability,
      timing: response.timing,
      evidence: response.evidence,
    });
  }
  for (const synergy of result.synergies) {
    const producer = result.formation.find(pick => pick.dragon.name === synergy.producer)?.dragon.abilities.find(ability => ability.name === synergy.producerAbility);
    const consumer = result.formation.find(pick => pick.dragon.name === synergy.consumer)?.dragon.abilities.find(ability => ability.name === synergy.consumerAbility);
    evidence.push({
      claim_type: "producer_payoff",
      effect: synergy.effect,
      producer: { dragon: synergy.producer, ability: synergy.producerAbility, evidence: producer ? evidenceReference(data, producer) : null },
      consumer: { dragon: synergy.consumer, ability: synergy.consumerAbility, evidence: consumer ? evidenceReference(data, consumer) : null },
      prerequisite: synergy.prerequisite,
      reliability: synergy.reliability,
    });
  }
  return evidence;
}

function riskRegister(data, result, coverage, rosterPreflight = null, dragonsArmy = null) {
  const risks = [{ type: "commanders_not_modeled", detail: "Commander talents, trait synergies, assignment and Commander Army Size bonuses are not modeled; they may change formation comparisons and capacity." }];
  const noPower = result.formation.filter(pick => pick.progression.power == null).map(pick => pick.dragon.name);
  if (noPower.length) risks.push({ type: "unknown_power", detail: `Current Power is unknown for ${noPower.join(", ")}.` });
  if (dragonsArmy?.additional_troops_per_dragon === 0 && ["ingestion_default", "planner_default_assumption"].includes(dragonsArmy.basis)) {
    risks.push({ type: "assumed_dragons_army", detail: "Dragon's Army was not supplied; the level-curve capacity proxy uses the required assumed +0 troops per dragon." });
  }
  if (result.formation.some(pick => pick.abilities.some(ability => ability.kind === "habit" && !Object.hasOwn(pick.progression.habit_levels || {}, ability.client_key)))) {
    risks.push({ type: "unknown_habit_investment", detail: "One or more unlocked Habit levels are unknown; variable proc rates and upgrade magnitudes were not treated as known or guaranteed." });
  }
  risks.push({ type: "capacity_formula", detail: "Capacity is a level-curve plus Dragon's Army proxy. Recorded Star scalars are disclosed but not applied because the final-stat formula is unverified." });
  for (const row of coverage.filter(item => item.state !== "direct")) risks.push({ type: `coverage_${row.state}`, detail: `${row.threat}: ${row.remaining_gap || "not guaranteed."}` });
  for (const gate of gateReport(data, result).filter(item => item.state === "locked")) risks.push({ type: "locked_ability", detail: `${gate.dragon} ${gate.ability}: ${gate.reason}` });
  if (rosterPreflight && rosterPreflight.completeness !== "complete") risks.push({ type: "roster_scope", detail: "The submitted roster is not explicitly confirmed complete; exhaustive search applies only to declared dragons." });
  return risks;
}

function resultForOrder(data, dragons, troop, context, cache) {
  const formation = dragons.map((dragon, index) => cache.get(`${dragon.slug}|${LANES[index]}`));
  return scoreFormation(data, formation, context.threats, context.enemyTroop, context.objective, troop);
}

function exhaustiveCandidates(data, context) {
  const dragonBySlug = new Map(data.dragons.map(dragon => [dragon.slug, dragon]));
  const pool = context.roster.map(entry => dragonBySlug.get(entry.slug)).filter(dragon => dragon && dragon.lifecycle !== "staged");
  const progression = new Map(context.roster.map(entry => [entry.slug, entry]));
  const enrichedEnemies = context.enemies.map(slot => {
    const dragon = dragonBySlug.get(slot.dragon);
    return { ...slot, name: dragon?.name, breed: dragon?.breed };
  });
  const threats = extractThreats(data, enrichedEnemies);
  const scoringContext = { ...context, enemies: enrichedEnemies, threats };
  const cache = new Map();
  for (const dragon of pool) for (const lane of LANES) {
    cache.set(`${dragon.slug}|${lane}`, candidateEvidence(data, dragon, threats, progression.get(dragon.slug), lane, enrichedEnemies));
  }
  const candidates = [];
  let laneOrdersEvaluated = 0;
  for (const trio of combinations(pool)) {
    const bestByTroop = new Map();
    for (const order of permutations(trio)) {
      laneOrdersEvaluated += 1;
      for (const troop of context.availableTroops) {
        const result = resultForOrder(data, order, troop, scoringContext, cache);
        const evaluated = { id: candidateId(result), result, metrics: metricsFor(data, result, context.objective, context) };
        const current = bestByTroop.get(troop);
        if (!current || policyCompare(evaluated, current, { includeCapacity: context.capacitySensitive, troopPreservation: context.troopPreservation }) < 0) bestByTroop.set(troop, evaluated);
      }
    }
    for (const evaluated of bestByTroop.values()) candidates.push({ ...evaluated, provenance: provenanceFor(data, evaluated.result) });
  }
  return { candidates, pool, progression, cache, context: scoringContext, laneOrdersEvaluated };
}

function baselineCandidate(data, baseline, search) {
  const fields = ["left_flank", "vanguard", "right_flank"];
  const dragons = fields.map(field => lookupDragon(data, baseline.formation[field]));
  const missingCanonical = fields.filter((field, index) => !dragons[index]).map(field => baseline.formation[field]);
  const missingRoster = dragons.filter(Boolean).filter(dragon => !search.progression.has(dragon.slug)).map(dragon => dragon.name);
  const troop = TROOPS.find(value => value.toLowerCase() === baseline.formation.troop_type.toLowerCase());
  const reasons = [];
  if (missingCanonical.length) reasons.push(`Unknown canonical dragon(s): ${missingCanonical.join(", ")}`);
  if (missingRoster.length) reasons.push(`Not owned: ${missingRoster.join(", ")}`);
  if (!troop) reasons.push(`Unknown troop: ${baseline.formation.troop_type}`);
  else if (!search.context.availableTroops.includes(troop)) reasons.push(`Troop unavailable: ${troop}`);
  const invalidReasons = [...reasons];
  const inapplicableReasons = search.context.objective === "poi" && troop !== "Siege" ? ["Marked inapplicable to a Siege-only POI objective."] : [];
  if (invalidReasons.length || inapplicableReasons.length) return {
    id: baseline.id,
    name: baseline.name,
    status: invalidReasons.length ? "illegal" : "inapplicable",
    reasons: [...invalidReasons, ...inapplicableReasons],
    candidate: null,
  };
  const result = resultForOrder(data, dragons, troop, search.context, search.cache);
  const candidate = decorateCandidate(data, result, search.context.objective, search.context);
  candidate.expert_prior = {
    formation_id: baseline.id,
    evidence_state: baseline.evidence_state,
    recommendation_prior: baseline.recommendation_prior || null,
    applicability: baseline.applicability,
    strategic_basis: baseline.strategic_basis,
  };
  return {
    id: baseline.id,
    name: baseline.name,
    status: "evaluated",
    reasons: [],
    applicability: baseline.applicability,
    strategic_basis: baseline.strategic_basis,
    candidate,
  };
}

function baselineApplies(baseline, objective) {
  const normalized = String(objective || "pvp").toLowerCase().replaceAll("-", "_").replaceAll(" ", "_");
  const objectives = baseline.applicability?.objectives || [];
  return objectives.includes(normalized) || objectives.includes("general_purpose") || normalized === "pvp";
}

function expertPriorEligible(baseline, input) {
  if (!baseline.candidate?.metrics.competitive_viability.qualified || !baselineApplies(baseline, input.objective)) return false;
  if (baseline.candidate.metrics.troop_disadvantage) return false;
  const threshold = COMPETITIVE_POLICY.auto_endgame_threshold;
  return baseline.candidate.result.formation.every(pick => pick.progression.level >= threshold.minimum_level && pick.progression.stars >= threshold.minimum_star_rank);
}

function strategicQualification(selectedCandidates, input, selectionBasis) {
  const failures = [];
  const unsupported = unique(selectedCandidates.flatMap(candidate => candidate.metrics.competitive_viability.unsupported_rare_dragons));
  if (selectedCandidates.some(candidate => !candidate.metrics.competitive_viability.qualified)) failures.push(`Selected portfolio includes unsupported endgame Rare dragon(s): ${unsupported.join(", ")}.`);
  if (input.competitive.resolved === "endgame" && !input.powerComparable && selectionBasis !== "expert_prior_default") {
    failures.push("Endgame Power is not comparable and no complete expert-prior portfolio was used; the result is mechanics-ranked only.");
  }
  return {
    qualified: failures.length === 0,
    status: failures.length ? "not_strategically_qualified" : selectionBasis === "expert_prior_default" ? "qualified_with_expert_prior" : "qualified",
    selection_basis: selectionBasis,
    competitive_context: input.competitive,
    power_comparable: input.powerComparable,
    unsupported_rare_dragons: unsupported,
    failures,
    meaning: "Strategic qualification is separate from structural validation and does not claim a simulated win rate or globally optimal formation.",
  };
}

function best(candidates, predicate = () => true, comparison = {}) {
  return candidates.filter(predicate).sort((left, right) => policyCompare(left, right, comparison))[0] || null;
}

function ledger(data, candidates, baselines, availableTroops, hasEnemy, comparison = {}) {
  const entries = [];
  for (const baseline of baselines) {
    entries.push({
      category: "common_baseline",
      category_key: baseline.id,
      disposition: baseline.status,
      reasons: baseline.reasons,
      candidate: baseline.candidate ? summarizeCandidate(data, baseline.candidate) : null,
    });
  }
  for (const troop of availableTroops.filter(value => value !== "Siege")) {
    const candidate = best(candidates, item => item.result.troop.troop === troop && item.result.troop.positive.length === 3 && item.result.troop.negative.length === 0, comparison);
    entries.push({ category: "affinity_perfect", category_key: troop, disposition: candidate ? "evaluated" : "unavailable", reasons: candidate ? [] : ["No legal affinity-perfect trio was found for this available troop."], candidate: candidate ? summarizeCandidate(data, candidate) : null });
  }
  const synergy = best(candidates, item => item.result.synergies.length > 0, comparison);
  entries.push({ category: "producer_payoff", category_key: "strongest_explicit_chain", disposition: synergy ? "evaluated" : "unavailable", reasons: synergy ? [] : ["No active explicit cross-dragon producer/payoff chain was found."], candidate: synergy ? summarizeCandidate(data, synergy) : null });
  const objective = best(candidates, () => true, comparison);
  entries.push({ category: "objective_specific", category_key: "best_supported_search_result", disposition: objective ? "evaluated" : "unavailable", reasons: [], candidate: objective ? summarizeCandidate(data, objective) : null });
  if (hasEnemy) {
    const counter = best(candidates, item => item.metrics.covered_threat_count > 0, comparison);
    entries.push({ category: "counter_specific", category_key: "documented_enemy", disposition: counter ? "evaluated" : "unavailable", reasons: counter ? [] : ["No candidate directly covered a normalized enemy threat."], candidate: counter ? summarizeCandidate(data, counter) : null });
  }
  return entries;
}

function reversalConditions(primary, alternative, { includeCapacity = false } = {}) {
  if (!primary || !alternative) return [];
  const messages = [];
  const left = primary.metrics;
  const right = alternative.metrics;
  if (right.explicit_synergy > left.explicit_synergy) messages.push(`${alternative.id} becomes preferable when explicit producer/payoff synergy is weighted above direct coverage and troop safety.`);
  if (right.troop_fit > left.troop_fit) messages.push(`${alternative.id} becomes preferable when troop affinity and matchup are weighted more heavily.`);
  if ((right.known_team_power ?? -1) > (left.known_team_power ?? -1)) messages.push(`${alternative.id} becomes preferable if visible current Power outweighs its weaker documented mechanics coverage.`);
  if (includeCapacity && (right.modeled_team_capacity ?? -1) > (left.modeled_team_capacity ?? -1)) messages.push(`${alternative.id} becomes preferable when troop-preservation capacity is weighted above its weaker documented mechanics coverage.`);
  if (right.timing_alignment > left.timing_alignment) messages.push(`${alternative.id} becomes preferable when earlier documented timing is decisive.`);
  if (!messages.length) messages.push("The ordering reverses only if undocumented combat formulas or omitted scenario constraints materially change the comparison.");
  return messages;
}

export function planRecommendations(data, commonFormations, rawInput) {
  const input = validatePlannerInput(data, rawInput);
  const search = exhaustiveCandidates(data, input);
  const baselines = commonFormations.formations.map(baseline => baselineCandidate(data, baseline, search));
  const baselineCandidates = baselines.filter(item => item.candidate).map(item => item.candidate);
  const candidateMap = new Map(search.candidates.map(candidate => [candidate.id, candidate]));
  for (const candidate of baselineCandidates) {
    const existing = candidateMap.get(candidate.id);
    if (existing) {
      existing.expert_prior = candidate.expert_prior;
      for (const baseline of baselines.filter(item => item.candidate === candidate)) baseline.candidate = existing;
    }
    else candidateMap.set(candidate.id, candidate);
  }
  const allCandidates = [...candidateMap.values()];
  const affinityEligibleCandidates = applyAffinityPolicy(allCandidates);
  const comparison = { includeCapacity: input.capacitySensitive, troopPreservation: input.troopPreservation };
  const qualifiedCandidates = affinityEligibleCandidates.filter(candidate => candidate.metrics.competitive_viability.qualified);
  const selectionPool = qualifiedCandidates.length ? qualifiedCandidates : affinityEligibleCandidates;
  const pareto = paretoFront(selectionPool, comparison).sort((left, right) => policyCompare(left, right, comparison));
  const mechanicalPrimary = pareto[0] || null;
  const expertPrimary = !input.powerComparable && input.competitive.resolved === "endgame"
    ? baselines.filter(item => expertPriorEligible(item, input) && affinityEligibleCandidates.includes(item.candidate)).map(item => item.candidate).sort((left, right) => policyCompare(left, right, comparison))[0] || null
    : null;
  const primary = expertPrimary || mechanicalPrimary;
  const selectionBasis = expertPrimary ? "expert_prior_default" : qualifiedCandidates.length ? "mechanically_ranked_qualified" : "mechanically_ranked_fallback";
  const finalists = unique([primary, ...pareto].filter(Boolean).map(candidate => candidate.id)).slice(0, input.maxFinalists).map(id => [primary, ...pareto].find(candidate => candidate?.id === id));
  const alternative = finalists.find(candidate => candidate.id !== primary?.id) || null;
  const primaryCoverage = primary ? coverageMatrix(data, primary.result) : [];
  const primaryGates = primary ? gateReport(data, primary.result) : [];
  return {
    metadata: {
      model: "dragonfire_deterministic_recommendation_planner_v1",
      evidence_source: path.relative(ROOT, DATA_PATH).replaceAll("\\", "/"),
      common_baselines_source: path.relative(ROOT, BASELINES_PATH).replaceAll("\\", "/"),
      recommendation_rules_source: path.relative(ROOT, RECOMMENDATION_RULES_PATH).replaceAll("\\", "/"),
      objective: input.objective,
      selection_policy: `Require 3-of-3 shared affinity unless a documented explicit-synergy advantage exceeds the affinity gap; then Pareto filter and order by direct threat coverage, troop safety${input.troopPreservation ? ", weakest-lane level-curve capacity floor, documented preservation tier, total level-curve capacity proxy, exact preservation score" : `, documented objective fit${input.capacitySensitive ? ", level-curve capacity proxy" : ""}`}, affinity/synergy policy, counter reliability, troop fit, lane fit, comparable known team Power, and diagnostic proxy score.`,
    },
    limitations: [
      "Commander talents, trait synergies, assignment and Commander Army Size bonuses are not modeled; they may change formation comparisons and capacity.",
      "This planner enumerates documented mechanics; it is not a battle-outcome or win-rate simulator.",
      "Troop-preservation weights are ordinal planning policy, not estimated casualties or equivalent troop counts.",
      "Diagnostic proxy scores are search aids and are not treated as universal formation strength.",
      "Unknown Habit levels remain unknown and contribute no invented upgrade value.",
      "Recorded Star scalars are reported but are not applied to capacity because the installed data does not establish a complete final-stat formula.",
      "No hidden damage, Recovery, troop-advantage, action-order, target-tiebreak, stacking, or Cleanse-priority formula is invented.",
      "Client presence alone does not establish live availability; staged dragons are excluded.",
    ],
    input_summary: {
      owned_dragons: input.roster.length,
      assumed_progression_entries: input.roster.filter(entry => entry.assumed).map(entry => entry.slug),
      available_troops: input.availableTroops,
      available_troops_source: input.availableTroopsSource,
      dragons_army: input.dragonsArmy,
      power_comparable: input.powerComparable,
      competitive_context: input.competitive,
      capacity_sensitive_objective: input.capacitySensitive,
      troop_preservation_objective: input.troopPreservation,
      enemy_lanes: input.enemies.length,
      enemy_troop: input.enemyTroop,
    },
    threats: search.context.threats.map(threat => ({
      ...threat,
      sources: threat.sources.map(source => {
        const ability = data.dragons.flatMap(dragon => dragon.abilities).find(item => item.id === source.ability_id);
        return { ...source, evidence: ability ? evidenceReference(data, ability) : null };
      }),
    })),
    search_summary: {
      legal_dragons: search.pool.length,
      trios_evaluated: combinations(search.pool).length,
      lane_orders_evaluated: search.laneOrdersEvaluated,
      trio_troop_candidates: search.candidates.length,
      shared_affinity_policy_eligible_candidates: affinityEligibleCandidates.length,
      pareto_candidate_count: pareto.length,
      returned_finalists: finalists.length,
    },
    common_baselines: baselines.map(item => ({
      id: item.id,
      name: item.name,
      status: item.status,
      reasons: item.reasons,
      candidate: item.candidate ? summarizeCandidate(data, item.candidate) : null,
    })),
    candidate_ledger: ledger(data, search.candidates, baselines, input.availableTroops, input.enemies.length > 0, comparison),
    pareto_finalists: finalists.map(candidate => summarizeCandidate(data, candidate)),
    primary_candidate: primary ? summarizeCandidate(data, primary) : null,
    strongest_alternative: alternative ? summarizeCandidate(data, alternative) : null,
    reversal_conditions: reversalConditions(primary, alternative, comparison),
    decision_audit: primary ? {
      coverage_matrix: primaryCoverage,
      gate_report: primaryGates,
      evidence: decisionEvidence(data, primary.result),
      risks: riskRegister(data, primary.result, primaryCoverage, null, primary.metrics.dragons_army),
    } : null,
    strategic_qualification: strategicQualification(primary ? [primary] : [], input, selectionBasis),
  };
}

function portfolioCandidateKey(candidate) {
  return candidate.result.formation.map(pick => pick.dragon.slug).sort().join("/");
}

function allocationSignature(allocation) {
  return allocation.selected.map(item => item.candidate.id).sort().join("||");
}

function allocationCompare(left, right) {
  return left.rankCost - right.rankCost || allocationSignature(left).localeCompare(allocationSignature(right));
}

export function globalDisjointPortfolio(rankedCandidates, formationCount, fullRanks = null) {
  const fullRank = (candidate, index) => fullRanks?.get(candidate.id) ?? index;
  const best = [];
  const consider = selected => {
    const allocation = { selected, rankCost: sum(selected.map(item => item.rank)) };
    if (best.some(item => allocationSignature(item) === allocationSignature(allocation))) return;
    best.push(allocation);
    best.sort(allocationCompare);
    if (best.length > 2) best.length = 2;
  };
  const greedy = [];
  const greedyUsed = new Set();
  for (const [rank, candidate] of rankedCandidates.entries()) {
    const dragons = candidate.result.formation.map(pick => pick.dragon.slug);
    if (dragons.some(slug => greedyUsed.has(slug))) continue;
    dragons.forEach(slug => greedyUsed.add(slug));
    greedy.push({ candidate, rank: fullRank(candidate, rank) });
    if (greedy.length === formationCount) break;
  }
  if (greedy.length === formationCount) consider(greedy);

  function visit(start, used, selected, rankCost) {
    const needed = formationCount - selected.length;
    if (!needed) {
      consider(selected);
      return;
    }
    if (rankedCandidates.length - start < needed) return;
    const currentBound = best.length >= 2 ? best[1].rankCost : Number.POSITIVE_INFINITY;
    for (let index = start; index <= rankedCandidates.length - needed; index += 1) {
      const optimistic = rankCost + sum(rankedCandidates.slice(index, index + needed).map((candidate, offset) => fullRank(candidate, index + offset)));
      if (optimistic > currentBound) break;
      const candidate = rankedCandidates[index];
      const dragons = candidate.result.formation.map(pick => pick.dragon.slug);
      if (dragons.some(slug => used.has(slug))) continue;
      const rank = fullRank(candidate, index);
      visit(index + 1, new Set([...used, ...dragons]), [...selected, { candidate, rank }], rankCost + rank);
    }
  }
  visit(0, new Set(), [], 0);
  return { primary: best[0] || null, alternative: best[1] || null };
}

const PORTFOLIO_RARITIES = ["Rare", "Epic", "Legendary"];

function normalizePortfolioGroups(rawInput, formationCount) {
  if (rawInput.portfolio_groups == null) return [{
    id: "portfolio",
    label: "Portfolio",
    count: formationCount,
    objective: String(rawInput.objective || "pvp"),
    constraints: {},
    preferences: { rarity_order: [], affinity_policy: "perfect_unless_explicit_synergy" },
    explicit: false,
  }];
  if (!Array.isArray(rawInput.portfolio_groups) || !rawInput.portfolio_groups.length) throw new Error("portfolio_groups must be a non-empty array when supplied.");
  const seen = new Set();
  const groups = rawInput.portfolio_groups.map((raw, index) => {
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) throw new Error(`portfolio_groups[${index}] must be an object.`);
    const id = String(raw.id || `group_${index + 1}`).trim();
    if (!id || seen.has(id)) throw new Error(`portfolio_groups must use unique non-empty ids; duplicate: ${id || "(empty)"}.`);
    seen.add(id);
    const count = Number(raw.count);
    if (!Number.isInteger(count) || count < 1) throw new Error(`portfolio_groups[${index}].count must be a positive integer.`);
    const constraints = raw.constraints || {};
    if (typeof constraints !== "object" || Array.isArray(constraints)) throw new Error(`portfolio_groups[${index}].constraints must be an object.`);
    const unknownConstraints = Object.keys(constraints).filter(key => !["minimum_dragon_level", "minimum_positive_affinities"].includes(key));
    if (unknownConstraints.length) throw new Error(`portfolio_groups[${index}].constraints contains unsupported key(s): ${unknownConstraints.join(", ")}.`);
    const minimumDragonLevel = constraints.minimum_dragon_level == null ? null : Number(constraints.minimum_dragon_level);
    if (minimumDragonLevel != null && (!Number.isInteger(minimumDragonLevel) || minimumDragonLevel < 1 || minimumDragonLevel > 50)) throw new Error(`portfolio_groups[${index}].constraints.minimum_dragon_level must be an integer from 1 to 50.`);
    const minimumPositiveAffinities = constraints.minimum_positive_affinities == null ? null : Number(constraints.minimum_positive_affinities);
    if (minimumPositiveAffinities != null && (!Number.isInteger(minimumPositiveAffinities) || minimumPositiveAffinities < 0 || minimumPositiveAffinities > 3)) throw new Error(`portfolio_groups[${index}].constraints.minimum_positive_affinities must be an integer from 0 to 3.`);
    const preferences = raw.preferences || {};
    if (typeof preferences !== "object" || Array.isArray(preferences)) throw new Error(`portfolio_groups[${index}].preferences must be an object.`);
    const unknownPreferences = Object.keys(preferences).filter(key => !["rarity_order", "affinity_policy"].includes(key));
    if (unknownPreferences.length) throw new Error(`portfolio_groups[${index}].preferences contains unsupported key(s): ${unknownPreferences.join(", ")}.`);
    if (preferences.rarity_order != null && !Array.isArray(preferences.rarity_order)) throw new Error(`portfolio_groups[${index}].preferences.rarity_order must be an array.`);
    const rarityOrder = preferences.rarity_order == null ? [] : preferences.rarity_order.map(value => String(value));
    const unknownRarities = rarityOrder.filter(value => !PORTFOLIO_RARITIES.includes(value));
    if (unknownRarities.length || new Set(rarityOrder).size !== rarityOrder.length) throw new Error(`portfolio_groups[${index}].preferences.rarity_order must contain unique Rare, Epic, or Legendary values.`);
    const affinityPolicy = preferences.affinity_policy == null ? "perfect_unless_explicit_synergy" : String(preferences.affinity_policy);
    if (affinityPolicy !== "perfect_unless_explicit_synergy") throw new Error(`portfolio_groups[${index}].preferences.affinity_policy must be perfect_unless_explicit_synergy.`);
    return {
      id,
      label: String(raw.label || id),
      count,
      objective: String(raw.objective || rawInput.objective || "pvp"),
      constraints: {
        minimum_dragon_level: minimumDragonLevel,
        minimum_positive_affinities: minimumPositiveAffinities,
      },
      preferences: { rarity_order: rarityOrder, affinity_policy: affinityPolicy },
      explicit: true,
    };
  });
  const declaredCount = sum(groups.map(group => group.count));
  if (declaredCount !== formationCount) throw new Error(`portfolio_groups counts sum to ${declaredCount}, not formation_count ${formationCount}.`);
  return groups;
}

function candidateMeetsPortfolioGroup(candidate, group) {
  const levels = candidate.result.formation.map(pick => pick.progression.level);
  if (group.constraints.minimum_dragon_level != null && levels.some(level => level < group.constraints.minimum_dragon_level)) return false;
  if (group.constraints.minimum_positive_affinities != null && candidate.metrics.affinity_count < group.constraints.minimum_positive_affinities) return false;
  return true;
}

export function applyAffinityPolicy(candidates) {
  // Compare against the strongest documented synergy among eligible perfect-affinity
  // candidates of the same competitive qualification, not an absolute score.
  const perfectByQualification = new Map();
  for (const candidate of candidates.filter(item => item.metrics.affinity_count === 3)) {
    const key = candidate.metrics.competitive_viability.qualified;
    const best = perfectByQualification.get(key);
    if (!best || candidate.metrics.explicit_synergy > best.metrics.explicit_synergy || (candidate.metrics.explicit_synergy === best.metrics.explicit_synergy && candidate.id.localeCompare(best.id) < 0)) perfectByQualification.set(key, candidate);
  }
  for (const candidate of candidates) {
    const comparator = perfectByQualification.get(candidate.metrics.competitive_viability.qualified) || null;
    const gap = 3 - candidate.metrics.affinity_count;
    const advantage = comparator ? candidate.metrics.explicit_synergy - comparator.metrics.explicit_synergy : null;
    candidate.affinity_evaluation = { comparator_id: comparator?.id || null, comparator_synergy_score: comparator?.metrics.explicit_synergy ?? null, synergy_advantage: advantage, eligible: gap <= 0 || !comparator || advantage > gap };
  }
  return candidates.filter(candidate => candidate.affinity_evaluation.eligible);
}

function affinityPolicyAttestation(candidate, group) {
  const affinityCount = candidate.metrics.affinity_count;
  const affinityGap = 3 - affinityCount;
  const explicitSynergy = candidate.metrics.explicit_synergy;
  const evaluation = candidate.affinity_evaluation;
  if (affinityCount === 3) return {
    target_positive_affinities: 3,
    status: "affinity_perfect",
    explicit_synergy_score: explicitSynergy,
    override_applied: false,
    justification: "All three dragons have positive affinity for the shared troop.",
  };
  if (!evaluation) return {
    target_positive_affinities: 3, status: "not_evaluated", explicit_synergy_score: explicitSynergy,
    affinity_gap: affinityGap, override_applied: false,
    justification: "No eligible comparison pool was evaluated for this candidate.",
  };
  const overrideApplied = Boolean(evaluation?.comparator_id && evaluation.synergy_advantage > affinityGap);
  return {
    target_positive_affinities: 3,
    status: overrideApplied ? "documented_synergy_override" : !evaluation?.comparator_id ? "no_affinity_perfect_available" : "below_affinity_target",
    explicit_synergy_score: explicitSynergy,
    affinity_gap: affinityGap,
    override_applied: overrideApplied,
    comparator_id: evaluation?.comparator_id || null,
    comparator_synergy_score: evaluation?.comparator_synergy_score ?? null,
    synergy_advantage: evaluation?.synergy_advantage ?? null,
    justification: overrideApplied
      ? `Documented synergy advantage ${evaluation.synergy_advantage} over ${evaluation.comparator_id} exceeds the ${affinityGap}-point shared-affinity gap.`
      : !evaluation?.comparator_id ? "No eligible affinity-perfect formation exists in this comparison pool; no synergy override is claimed." : "No documented explicit-synergy advantage outweighs the missing shared affinity.",
    documented_synergies: candidate.result.synergies,
  };
}

function portfolioGroupCompare(left, right, group, comparison) {
  for (const rarity of group.preferences.rarity_order) {
    const count = candidate => candidate.result.formation.filter(pick => pick.dragon.rarity_tier === rarity).length;
    const rarityDifference = count(right) - count(left);
    if (rarityDifference) return rarityDifference;
  }
  return policyCompare(left, right, comparison);
}

export function rankPortfolioGroupCandidates(candidates, group, comparison = {}) {
  const eligible = applyAffinityPolicy(candidates.filter(candidate => candidateMeetsPortfolioGroup(candidate, group)));
  const bestByTrio = new Map();
  for (const candidate of eligible) {
    const key = candidate.expert_prior ? `expert:${candidate.id}` : portfolioCandidateKey(candidate);
    const current = bestByTrio.get(key);
    if (!current || portfolioGroupCompare(candidate, current, group, comparison) < 0) bestByTrio.set(key, candidate);
  }
  return [...bestByTrio.values()].sort((left, right) => portfolioGroupCompare(left, right, group, comparison));
}

function constrainedAllocationSignature(allocation) {
  return allocation.selected.map(item => `${item.group.id}:${item.slot_index}:${item.candidate.id}`).join("||");
}

function constrainedAllocationCompare(left, right) {
  return left.rankCost - right.rankCost || constrainedAllocationSignature(left).localeCompare(constrainedAllocationSignature(right));
}

export function globalConstrainedPortfolio(groupPools) {
  const slots = groupPools.flatMap(({ group, ranked, fullRanks }) => Array.from({ length: group.count }, (_, slotIndex) => ({ group, ranked, fullRanks, slotIndex })));
  const best = [];
  const consider = selected => {
    const allocation = { selected, rankCost: sum(selected.map(item => item.rank)) };
    if (best.some(item => constrainedAllocationSignature(item) === constrainedAllocationSignature(allocation))) return;
    best.push(allocation);
    best.sort(constrainedAllocationCompare);
    if (best.length > 2) best.length = 2;
  };
  const greedy = [];
  const greedyUsed = new Set();
  const greedyLastIndex = new Map();
  for (const slot of slots) {
    const minimumIndex = slot.slotIndex > 0 ? (greedyLastIndex.get(slot.group.id) ?? -1) + 1 : 0;
    let chosen = null;
    for (let index = minimumIndex; index < slot.ranked.length; index += 1) {
      const candidate = slot.ranked[index];
      const dragons = candidate.result.formation.map(pick => pick.dragon.slug);
      if (dragons.some(slug => greedyUsed.has(slug))) continue;
      chosen = { candidate, rank: slot.fullRanks.get(candidate.id), group: slot.group, slot_index: slot.slotIndex };
      dragons.forEach(slug => greedyUsed.add(slug));
      greedyLastIndex.set(slot.group.id, index);
      break;
    }
    if (!chosen) break;
    greedy.push(chosen);
  }
  if (greedy.length === slots.length) consider(greedy);

  function visit(slotIndex, used, selected, rankCost, lastIndexByGroup) {
    if (slotIndex === slots.length) {
      consider(selected);
      return;
    }
    const currentBound = best.length >= 2 ? best[1].rankCost : Number.POSITIVE_INFINITY;
    const slot = slots[slotIndex];
    const start = slot.slotIndex > 0 ? (lastIndexByGroup.get(slot.group.id) ?? -1) + 1 : 0;
    for (let index = start; index < slot.ranked.length; index += 1) {
      const candidate = slot.ranked[index];
      const rank = slot.fullRanks.get(candidate.id);
      if (rankCost + rank > currentBound) break;
      const dragons = candidate.result.formation.map(pick => pick.dragon.slug);
      if (dragons.some(slug => used.has(slug))) continue;
      const nextLast = new Map(lastIndexByGroup);
      nextLast.set(slot.group.id, index);
      visit(slotIndex + 1, new Set([...used, ...dragons]), [...selected, { candidate, rank, group: slot.group, slot_index: slot.slotIndex }], rankCost + rank, nextLast);
    }
  }
  visit(0, new Set(), [], 0, new Map());
  return { primary: best[0] || null, alternative: best[1] || null };
}

function validatePortfolioResult(result) {
  const failures = [];
  if (result.selected_formations.length !== result.request_interpretation.formation_count) failures.push("Selected formation count does not match the request.");
  if (result.request_interpretation.reuse_policy === "disjoint_armies") {
    const dragons = result.selected_formations.flatMap(item => item.candidate.progression.map(entry => entry.slug));
    if (new Set(dragons).size !== dragons.length) failures.push("The selected portfolio reuses a dragon.");
  }
  if (!result.roster_preflight.verified_complete) failures.push("Roster preflight is not verified complete.");
  if (result.selected_formations.some(item => !item.candidate.id || !item.candidate.evidence.length)) failures.push("A selected formation is missing its candidate ID or evidence.");
  if (result.selected_formations.some(item => item.constraint_attestation && !item.constraint_attestation.satisfied)) failures.push("A selected formation violates its portfolio-group constraints.");
  return { valid: failures.length === 0, failures };
}

function planGroupedFormationPortfolio(data, commonFormations, rawInput, formationCount, reusePolicy, preflight, groups) {
  if (reusePolicy !== "disjoint_armies") throw new Error("portfolio_groups currently require reuse_policy: disjoint_armies.");
  const groupPlans = groups.map(group => {
    const input = validatePlannerInput(data, { ...rawInput, objective: group.objective });
    const search = exhaustiveCandidates(data, input);
    const baselines = commonFormations.formations.map(baseline => baselineCandidate(data, baseline, search));
    const all = [...search.candidates];
    for (const baseline of baselines.filter(item => item.candidate)) {
      const expertCandidate = baseline.candidate;
      const existing = all.find(candidate => candidate.id === expertCandidate.id);
      if (existing) {
        existing.expert_prior = expertCandidate.expert_prior;
        baseline.candidate = existing;
      } else all.push(expertCandidate);
    }
    const comparison = { includeCapacity: input.capacitySensitive, troopPreservation: input.troopPreservation };
    const ranked = rankPortfolioGroupCandidates(all, group, comparison);
    if (ranked.length < group.count) throw new Error(`Portfolio group ${group.id} has only ${ranked.length} eligible formations for ${group.count} requested slots.`);
    const fullRanks = new Map(ranked.map((candidate, index) => [candidate.id, index]));
    const qualifiedRanked = ranked.filter(candidate => candidate.metrics.competitive_viability.qualified);
    const expertIds = new Set(baselines.filter(baseline => expertPriorEligible(baseline, input)).map(baseline => baseline.candidate.id));
    return { group, input, search, baselines, ranked, fullRanks, qualifiedRanked, expertRanked: qualifiedRanked.filter(candidate => expertIds.has(candidate.id)) };
  });
  const pools = field => groupPlans.map(plan => ({ group: plan.group, ranked: plan[field], fullRanks: plan.fullRanks }));
  const qualifiedSearch = globalConstrainedPortfolio(pools("qualifiedRanked"));
  const allSearch = qualifiedSearch.primary ? qualifiedSearch : globalConstrainedPortfolio(pools("ranked"));
  if (!allSearch.primary) throw new Error("No globally valid disjoint formation portfolio satisfies every portfolio-group constraint.");
  const expertSearch = globalConstrainedPortfolio(pools("expertRanked"));
  const useExpertPrior = groupPlans[0].input.competitive.resolved === "endgame" && !groupPlans[0].input.powerComparable && expertSearch.primary;
  const allocation = useExpertPrior || allSearch.primary;
  const alternative = useExpertPrior && constrainedAllocationSignature(useExpertPrior) !== constrainedAllocationSignature(allSearch.primary) ? allSearch.primary : allSearch.alternative;
  const qualifiedAllocationUsed = Boolean(qualifiedSearch.primary);
  const selectionBasis = useExpertPrior ? "expert_prior_default" : qualifiedAllocationUsed ? "globally_grouped_qualified" : "globally_grouped_fallback";
  const inputByGroup = new Map(groupPlans.map(plan => [plan.group.id, plan.input]));
  const selectedFormations = allocation.selected.map((item, index) => {
    const input = inputByGroup.get(item.group.id);
    const minimumLevel = Math.min(...item.candidate.result.formation.map(pick => pick.progression.level));
    const affinityCount = item.candidate.metrics.affinity_count;
    return {
      priority: index + 1,
      portfolio_group: {
        id: item.group.id,
        label: item.group.label,
        slot: item.slot_index + 1,
        objective: item.group.objective,
        constraints: item.group.constraints,
        preferences: item.group.preferences,
      },
      group_candidate_rank: item.rank + 1,
      candidate_rank_scope: "portfolio_group",
      constraint_attestation: {
        satisfied: candidateMeetsPortfolioGroup(item.candidate, item.group),
        minimum_dragon_level_observed: minimumLevel,
        positive_affinity_count_observed: affinityCount,
        affinity_policy: affinityPolicyAttestation(item.candidate, item.group),
        rarity_counts: Object.fromEntries(PORTFOLIO_RARITIES.map(rarity => [rarity, item.candidate.result.formation.filter(pick => pick.dragon.rarity_tier === rarity).length])),
      },
      candidate: summarizeCandidate(data, item.candidate),
      risks: riskRegister(data, item.candidate.result, coverageMatrix(data, item.candidate.result), preflight, input.dragonsArmy),
    };
  });
  const summarizeAllocation = value => value ? {
    total_rank_cost: value.rankCost,
    candidate_ids: value.selected.map(item => item.candidate.id),
    candidate_ranks: value.selected.map(item => item.rank + 1),
    portfolio_group_ids: value.selected.map(item => item.group.id),
  } : null;
  const primaryInput = groupPlans[0].input;
  const result = {
    metadata: {
      model: "dragonfire_grouped_formation_portfolio_v1",
      evidence_source: path.relative(ROOT, DATA_PATH).replaceAll("\\", "/"),
      common_baselines_source: path.relative(ROOT, BASELINES_PATH).replaceAll("\\", "/"),
      recommendation_rules_source: path.relative(ROOT, RECOMMENDATION_RULES_PATH).replaceAll("\\", "/"),
      objective: "heterogeneous_portfolio",
      selection_policy: "Apply each portfolio group's hard constraints and ordered preferences, then globally minimize the sum of group-local full-search candidate ranks while enforcing disjoint armies.",
    },
    limitations: [
      "Commander talents, trait synergies, assignment and Commander Army Size bonuses are not modeled; they may change formation comparisons and capacity.",
      "This planner enumerates documented mechanics; it is not a battle-outcome, win-rate, or casualty simulator.",
      "Group rarity preferences are explicit request priorities, not a universal rarity score.",
      "Troop-preservation weights are ordinal planning policy, not estimated casualties or equivalent troop counts.",
      "Unknown Habit levels and variable Habit proc rates remain unknown and receive no invented reliability value.",
      "Recorded Star scalars are reported but are not applied to capacity because the installed data does not establish a complete final-stat formula.",
    ],
    request_interpretation: {
      request_mode: "formation_portfolio",
      formation_count: formationCount,
      reuse_policy: reusePolicy,
      default_semantics: "Explicit ordered portfolio groups with non-overlapping armies.",
      portfolio_groups: groups,
    },
    roster_preflight: preflight,
    troop_preflight: {
      available_troops: primaryInput.availableTroops,
      source: primaryInput.availableTroopsSource,
      caveat: "A lineup screenshot establishes dragons and progression, not which formation troop types are selectable.",
    },
    input_summary: {
      owned_dragons: primaryInput.roster.length,
      objective: "heterogeneous_portfolio",
      portfolio_groups: groups,
      dragons_army: primaryInput.dragonsArmy,
      capacity_basis: "Level curve plus Dragon's Army only; recorded Star scalars are not applied.",
      power_comparable: primaryInput.powerComparable,
      competitive_context: primaryInput.competitive,
    },
    search_summary: {
      legal_dragons: primaryInput.roster.length,
      groups: groupPlans.map(plan => ({
        id: plan.group.id,
        objective: plan.group.objective,
        full_trio_troop_candidates: plan.search.candidates.length,
        constraint_eligible_ranked_trios: plan.ranked.length,
        competitively_qualified_ranked_trios: plan.qualifiedRanked.length,
      })),
      allocation_scope: "The disjoint search jointly assigns every ordered group slot from its complete constraint-eligible ranked pool.",
    },
    selected_formations: selectedFormations,
    allocation_attestation: {
      selected: summarizeAllocation(allocation),
      strongest_alternative: summarizeAllocation(alternative),
      expert_baseline_portfolio: summarizeAllocation(expertSearch.primary),
      selection_basis: selectionBasis,
      greedy_selection_used: false,
      exhaustive_candidate_pool_used: true,
      group_constraints_enforced: true,
    },
    common_baselines: groupPlans[0].baselines.map(item => ({ id: item.id, name: item.name, status: item.status, reasons: item.reasons, candidate: item.candidate ? summarizeCandidate(data, item.candidate) : null })),
    common_baselines_by_group: Object.fromEntries(groupPlans.map(plan => [plan.group.id, plan.baselines.map(item => ({ id: item.id, name: item.name, status: item.status, reasons: item.reasons, candidate: item.candidate ? summarizeCandidate(data, item.candidate) : null }))])),
  };
  result.validation = validatePortfolioResult(result);
  result.strategic_qualification = strategicQualification(allocation.selected.map(item => item.candidate), primaryInput, selectionBasis);
  if (!result.validation.valid) throw new Error(`Portfolio result failed output validation: ${result.validation.failures.join(" ")}`);
  return result;
}

export function planFormationPortfolio(data, commonFormations, rawInput) {
  const formationCount = Number(rawInput.formation_count);
  if (!Number.isInteger(formationCount) || formationCount < 1) throw new Error("formation_count must be a positive integer.");
  const reusePolicy = rawInput.reuse_policy || "disjoint_armies";
  if (!['disjoint_armies', 'allow_reuse'].includes(reusePolicy)) throw new Error("Portfolio reuse_policy must be disjoint_armies or allow_reuse.");
  const preflight = rosterPreflight(data, rawInput);
  const groups = normalizePortfolioGroups(rawInput, formationCount);
  if (groups.some(group => group.explicit)) return planGroupedFormationPortfolio(data, commonFormations, rawInput, formationCount, reusePolicy, preflight, groups);
  const input = validatePlannerInput(data, rawInput);
  if (formationCount * 3 > input.roster.length && reusePolicy === "disjoint_armies") throw new Error(`A ${formationCount}-formation disjoint portfolio requires at least ${formationCount * 3} owned dragons.`);
  const search = exhaustiveCandidates(data, input);
  const baselines = commonFormations.formations.map(baseline => baselineCandidate(data, baseline, search));
  const all = [...search.candidates];
  for (const baseline of baselines.filter(item => item.candidate)) {
    const expertCandidate = baseline.candidate;
    const existing = all.find(candidate => candidate.id === expertCandidate.id);
    if (existing) {
      existing.expert_prior = expertCandidate.expert_prior;
      baseline.candidate = existing;
    }
    else all.push(expertCandidate);
  }
  const comparison = { includeCapacity: input.capacitySensitive, troopPreservation: input.troopPreservation };
  const bestByTrio = new Map();
  for (const candidate of applyAffinityPolicy(all)) {
    const key = candidate.expert_prior ? `expert:${candidate.id}` : portfolioCandidateKey(candidate);
    const current = bestByTrio.get(key);
    if (!current || policyCompare(candidate, current, comparison) < 0) bestByTrio.set(key, candidate);
  }
  const ranked = [...bestByTrio.values()].sort((left, right) => policyCompare(left, right, comparison));
  const fullRanks = new Map(ranked.map((candidate, index) => [candidate.id, index]));
  const qualifiedRanked = ranked.filter(candidate => candidate.metrics.competitive_viability.qualified);
  let mechanicalAllocation;
  let alternative = null;
  let qualifiedAllocationUsed = false;
  if (reusePolicy === "allow_reuse") {
    const allocationPool = qualifiedRanked.length >= formationCount ? qualifiedRanked : ranked;
    if (allocationPool.length < formationCount) throw new Error("Not enough distinct candidate formations exist for the requested portfolio.");
    mechanicalAllocation = { selected: allocationPool.slice(0, formationCount).map(candidate => ({ candidate, rank: ranked.indexOf(candidate) })), rankCost: sum(allocationPool.slice(0, formationCount).map(candidate => ranked.indexOf(candidate))) };
    qualifiedAllocationUsed = allocationPool === qualifiedRanked;
  } else {
    let selected = globalDisjointPortfolio(qualifiedRanked, formationCount, fullRanks);
    qualifiedAllocationUsed = Boolean(selected.primary);
    if (!selected.primary) selected = globalDisjointPortfolio(ranked, formationCount, fullRanks);
    const remap = value => value ? {
      selected: value.selected.map(item => ({ candidate: item.candidate, rank: ranked.indexOf(item.candidate) })),
      rankCost: sum(value.selected.map(item => ranked.indexOf(item.candidate))),
    } : null;
    mechanicalAllocation = remap(selected.primary);
    alternative = remap(selected.alternative);
    if (!mechanicalAllocation) throw new Error("No globally valid disjoint formation portfolio exists for the supplied roster.");
  }
  const expertCandidates = baselines
    .filter(item => expertPriorEligible(item, input) && ranked.includes(item.candidate))
    .map(item => item.candidate)
    .sort((left, right) => policyCompare(left, right, comparison));
  const expertSearch = reusePolicy === "allow_reuse"
    ? expertCandidates.length >= formationCount ? { primary: { selected: expertCandidates.slice(0, formationCount).map(candidate => ({ candidate, rank: ranked.indexOf(candidate) })) } } : { primary: null }
    : globalDisjointPortfolio(expertCandidates, formationCount, fullRanks);
  const expertAllocation = expertSearch.primary ? {
    selected: expertSearch.primary.selected.map(item => ({ candidate: item.candidate, rank: ranked.indexOf(item.candidate) })),
    rankCost: sum(expertSearch.primary.selected.map(item => ranked.indexOf(item.candidate))),
  } : null;
  const useExpertPrior = input.competitive.resolved === "endgame" && !input.powerComparable && expertAllocation;
  const allocation = useExpertPrior ? expertAllocation : mechanicalAllocation;
  if (useExpertPrior && allocationSignature(mechanicalAllocation) !== allocationSignature(expertAllocation)) alternative = mechanicalAllocation;
  const selectionBasis = useExpertPrior ? "expert_prior_default" : qualifiedAllocationUsed ? "globally_ranked_qualified" : "globally_ranked_fallback";
  const selectedFormations = allocation.selected.map((item, index) => ({
    priority: index + 1,
    global_candidate_rank: item.rank + 1,
    candidate: summarizeCandidate(data, item.candidate),
    risks: riskRegister(data, item.candidate.result, coverageMatrix(data, item.candidate.result), preflight, input.dragonsArmy),
  }));
  const summarizeAllocation = value => value ? {
    total_rank_cost: value.rankCost,
    candidate_ids: value.selected.map(item => item.candidate.id),
    candidate_ranks: value.selected.map(item => item.rank + 1),
  } : null;
  const result = {
    metadata: {
      model: "dragonfire_global_formation_portfolio_v1",
      evidence_source: path.relative(ROOT, DATA_PATH).replaceAll("\\", "/"),
      common_baselines_source: path.relative(ROOT, BASELINES_PATH).replaceAll("\\", "/"),
      recommendation_rules_source: path.relative(ROOT, RECOMMENDATION_RULES_PATH).replaceAll("\\", "/"),
      objective: input.objective,
      selection_policy: "Apply competitive-viability gates, then globally minimize the sum of full-search candidate ranks subject to the requested dragon-reuse policy. When endgame Power is not comparable, a complete legal expert-recommended portfolio is the conservative default and the mechanically ranked portfolio is retained as an alternative.",
    },
    limitations: [
      "Commander talents, trait synergies, assignment and Commander Army Size bonuses are not modeled; they may change formation comparisons and capacity.",
      "This planner enumerates documented mechanics; it is not a battle-outcome, win-rate, or casualty simulator.",
      "Troop-preservation weights are ordinal planning policy, not estimated casualties or equivalent troop counts.",
      "Unknown Habit levels and variable Habit proc rates remain unknown and receive no invented reliability value.",
      "Recorded Star scalars are reported but are not applied to capacity because the installed data does not establish a complete final-stat formula.",
      "Competitive viability and expert status are reviewed policy evidence, not simulated win rates or universal rarity scores.",
    ],
    request_interpretation: {
      request_mode: "formation_portfolio",
      formation_count: formationCount,
      reuse_policy: reusePolicy,
      default_semantics: rawInput.reuse_policy ? "explicit" : "An unqualified request for multiple formations defaults to non-overlapping armies.",
    },
    roster_preflight: preflight,
    troop_preflight: {
      available_troops: input.availableTroops,
      source: input.availableTroopsSource,
      caveat: "A lineup screenshot establishes dragons and progression, not which formation troop types are selectable.",
    },
    input_summary: {
      owned_dragons: input.roster.length,
      objective: input.objective,
      dragons_army: input.dragonsArmy,
      capacity_basis: "Level curve plus Dragon's Army only; recorded Star scalars are not applied.",
      power_comparable: input.powerComparable,
      competitive_context: input.competitive,
    },
    search_summary: {
      legal_dragons: search.pool.length,
      trios_evaluated: combinations(search.pool).length,
      lane_orders_evaluated: search.laneOrdersEvaluated,
      full_trio_troop_candidates: search.candidates.length,
      globally_ranked_trios: ranked.length,
      competitively_qualified_ranked_trios: qualifiedRanked.length,
      allocation_scope: "The disjoint search uses every globally ranked legal trio, not a truncated Pareto-finalist list.",
    },
    selected_formations: selectedFormations,
    allocation_attestation: {
      selected: summarizeAllocation(allocation),
      strongest_alternative: summarizeAllocation(alternative),
      expert_baseline_portfolio: summarizeAllocation(expertAllocation),
      selection_basis: selectionBasis,
      greedy_selection_used: false,
      exhaustive_candidate_pool_used: true,
    },
    common_baselines: baselines.map(item => ({ id: item.id, name: item.name, status: item.status, reasons: item.reasons, candidate: item.candidate ? summarizeCandidate(data, item.candidate) : null })),
  };
  result.validation = validatePortfolioResult(result);
  result.strategic_qualification = strategicQualification(allocation.selected.map(item => item.candidate), input, selectionBasis);
  if (!result.validation.valid) throw new Error(`Portfolio result failed output validation: ${result.validation.failures.join(" ")}`);
  return result;
}

function isBatchInput(input) {
  return Array.isArray(input?.scenarios);
}

function isPortfolioInput(input) {
  return input?.request_mode === "formation_portfolio" || input?.formation_count != null;
}

function habitLevelsAtFive(dragon) {
  return Object.fromEntries(dragon.abilities.filter(ability => ability.kind === "habit").map(ability => [ability.client_key, 5]));
}

function enemyFromCommonFormation(data, commonFormations, id) {
  const baseline = commonFormations.formations.find(item => item.id === id);
  if (!baseline) throw new Error(`Unknown common_formation_id: ${id}`);
  const reference = baseline.reference_assumptions || {};
  const fields = [["left_flank", "Left Flank"], ["vanguard", "Vanguard"], ["right_flank", "Right Flank"]];
  return {
    common_formation_id: baseline.id,
    common_formation_name: baseline.name,
    troop_type: baseline.formation.troop_type,
    formation: fields.map(([field, lane]) => {
      const dragon = lookupDragon(data, baseline.formation[field]);
      if (!dragon) throw new Error(`Common formation ${baseline.id} refers to an unknown dragon: ${baseline.formation[field]}`);
      return {
        dragon: dragon.name,
        lane,
        level: Number(reference.level || 50),
        stars: Number(reference.star_rank || 6),
        habit_levels: Object.fromEntries(dragon.abilities.filter(ability => ability.kind === "habit").map(ability => [ability.client_key, Number(reference.unlocked_habit_level || 5)])),
        assumed: true,
        progression_source: `data/common_formations.json -> formations[id=${baseline.id}].reference_assumptions`,
        progression_confidence: "reference_assumption",
      };
    }),
  };
}

function rosterPreflight(data, raw) {
  const entries = profileEntries(raw);
  const normalized = entries.map((entry, index) => normalizeProgression(data, entry, `roster entry ${index + 1}`));
  const declared = raw.roster_preflight || {};
  const completeness = declared.completeness || "declared_subset";
  if (!["complete", "declared_subset"].includes(completeness)) throw new Error("roster_preflight.completeness must be complete or declared_subset.");
  const expected = declared.expected_visible_dragons == null ? null : Number(declared.expected_visible_dragons);
  if (expected != null && (!Number.isInteger(expected) || expected < 3)) throw new Error("roster_preflight.expected_visible_dragons must be an integer of at least 3.");
  const owned = normalized.filter(entry => entry.owned !== false);
  if (expected != null && owned.length !== expected) throw new Error(`Roster preflight expected ${expected} owned dragons but received ${owned.length}.`);
  return {
    completeness,
    expected_visible_dragons: expected,
    declared_owned_dragons: owned.length,
    verified_complete: completeness === "complete" && (expected == null || expected === owned.length),
    verification_scope: "The planner checks the declared count and entries; it cannot independently verify screenshot transcription or obscured dragons.",
    progression_entries: owned.map(entry => ({ slug: entry.slug, level: entry.level, stars: entry.stars, displayed_stars: entry.displayed_stars, power: entry.power, progression_source: entry.progression_source, progression_confidence: entry.progression_confidence })),
  };
}

function scenarioInput(data, commonFormations, raw, scenario, index) {
  if (!scenario || typeof scenario !== "object" || Array.isArray(scenario)) throw new Error(`scenarios[${index}] must be an object.`);
  const id = String(scenario.id || `scenario-${index + 1}`);
  const suppliedEnemy = scenario.enemy || {};
  const commonId = scenario.common_formation_id || suppliedEnemy.common_formation_id;
  const resolvedEnemy = commonId ? enemyFromCommonFormation(data, commonFormations, commonId) : suppliedEnemy;
  if (!commonId && (!Array.isArray(resolvedEnemy.formation) || !resolvedEnemy.formation.length)) throw new Error(`Scenario ${id} must supply enemy.formation or common_formation_id.`);
  const input = {
    ...raw,
    ...scenario,
    objective: scenario.objective || raw.objective || "counter",
    available_troops: scenario.available_troops || raw.available_troops,
    enemy: resolvedEnemy,
    max_finalists: scenario.max_finalists || raw.max_finalists,
  };
  delete input.scenarios;
  delete input.request_mode;
  delete input.reuse_policy;
  delete input.roster_preflight;
  delete input.top_n;
  return { id, label: scenario.label || resolvedEnemy.common_formation_name || id, input, resolvedEnemy };
}

function summaryDragonSlugs(candidate) {
  return candidate.progression.map(entry => entry.slug).sort();
}

function uniqueCandidateChoices(result) {
  const seen = new Set();
  return [result.primary_candidate, ...result.pareto_finalists].filter(candidate => {
    if (!candidate || seen.has(candidate.id)) return false;
    seen.add(candidate.id);
    return true;
  });
}

function disjointSelection(scenarios) {
  let bestAllocation = null;
  function visit(index, used, selected, rankCost) {
    if (index === scenarios.length) {
      if (!bestAllocation || rankCost < bestAllocation.rankCost) bestAllocation = { selected, rankCost };
      return;
    }
    for (const [rank, candidate] of uniqueCandidateChoices(scenarios[index].planner_result).entries()) {
      const dragons = summaryDragonSlugs(candidate);
      if (dragons.some(slug => used.has(slug))) continue;
      const nextUsed = new Set([...used, ...dragons]);
      visit(index + 1, nextUsed, [...selected, { candidate, rank }], rankCost + rank);
    }
  }
  visit(0, new Set(), [], 0);
  return bestAllocation;
}

function validateBatchResult(result) {
  const failures = [];
  if (!result.scenarios.length) failures.push("No scenarios were evaluated.");
  for (const scenario of result.scenarios) {
    if (!scenario.planner_result.primary_candidate) failures.push(`${scenario.scenario_id}: no primary candidate was produced.`);
    if (!scenario.selected_candidates.length) failures.push(`${scenario.scenario_id}: no selected candidate was produced.`);
    if (scenario.coverage_matrix.length !== scenario.planner_result.threats.length) failures.push(`${scenario.scenario_id}: threat coverage matrix does not match the threat inventory.`);
    if (!scenario.gate_report.length) failures.push(`${scenario.scenario_id}: progression gate report is missing.`);
    if (!scenario.decision_evidence.length) failures.push(`${scenario.scenario_id}: decision evidence is missing.`);
    if (scenario.selection_attestation.selected_candidate_id !== scenario.selected_candidates[0]?.id) failures.push(`${scenario.scenario_id}: selection attestation does not match the selected candidate.`);
    if (!scenario.planner_result.pareto_finalists.some(item => item.id === scenario.selected_candidates[0]?.id)) failures.push(`${scenario.scenario_id}: selected candidate is not a documented Pareto finalist.`);
    if (!scenario.planner_result.common_baselines.length) failures.push(`${scenario.scenario_id}: common baselines are missing.`);
  }
  if (result.request_interpretation.reuse_policy === "disjoint_armies") {
    const dragons = result.scenarios.flatMap(scenario => summaryDragonSlugs(scenario.selected_candidates[0] || { progression: [] }));
    if (new Set(dragons).size !== dragons.length) failures.push("disjoint_armies selection reuses a dragon.");
  }
  return { valid: failures.length === 0, failures };
}

export function planBatchRecommendations(data, commonFormations, raw) {
  if (!isBatchInput(raw)) throw new Error("Batch input requires a scenarios array.");
  if (!raw.scenarios.length) throw new Error("Batch input must contain at least one scenario.");
  const requestMode = raw.request_mode || "one_per_matchup";
  const reusePolicy = raw.reuse_policy || "independent_matchups";
  const topN = raw.top_n == null ? 3 : Number(raw.top_n);
  if (!["one_per_matchup", "top_n_per_matchup"].includes(requestMode)) throw new Error("request_mode must be one_per_matchup or top_n_per_matchup.");
  if (!["independent_matchups", "disjoint_armies"].includes(reusePolicy)) throw new Error("reuse_policy must be independent_matchups or disjoint_armies.");
  if (!Number.isInteger(topN) || topN < 1 || topN > 12) throw new Error("top_n must be an integer from 1 to 12.");
  if (reusePolicy === "disjoint_armies" && requestMode !== "one_per_matchup") throw new Error("disjoint_armies currently supports one_per_matchup only, so every selected army can be validated as distinct.");

  const preflight = rosterPreflight(data, raw);
  const prepared = raw.scenarios.map((scenario, index) => scenarioInput(data, commonFormations, raw, scenario, index));
  const duplicateScenario = prepared.find((item, index) => prepared.findIndex(other => other.id === item.id) !== index);
  if (duplicateScenario) throw new Error(`Scenario IDs must be unique; duplicate: ${duplicateScenario.id}`);
  const planned = prepared.map(item => ({ ...item, planner_result: planRecommendations(data, commonFormations, item.input) }));
  let selected = planned.map(item => ({ candidate: item.planner_result.primary_candidate, rank: 0 }));
  if (reusePolicy === "disjoint_armies") {
    const allocation = disjointSelection(planned);
    if (!allocation) throw new Error("No disjoint set of documented Pareto finalists exists for the supplied scenarios and roster.");
    selected = allocation.selected;
  }
  const result = {
    metadata: {
      model: "dragonfire_deterministic_batch_recommendation_planner_v1",
      planner_model: "dragonfire_deterministic_recommendation_planner_v1",
      evidence_source: path.relative(ROOT, DATA_PATH).replaceAll("\\", "/"),
      common_baselines_source: path.relative(ROOT, BASELINES_PATH).replaceAll("\\", "/"),
    },
    request_interpretation: {
      request_mode: requestMode,
      reuse_policy: reusePolicy,
      scenario_count: planned.length,
      semantics: requestMode === "one_per_matchup" ? "One counter formation is selected independently for each enemy scenario unless the explicit disjoint_armies policy is used." : `The top ${topN} Pareto finalists are returned for each enemy scenario; repeated dragons are allowed under independent_matchups.`,
    },
    roster_preflight: preflight,
    troop_preflight: {
      available_troops: planned.map(item => ({ scenario_id: item.id, troop_types: item.planner_result.input_summary.available_troops, source: item.planner_result.input_summary.available_troops_source })),
      caveat: "A lineup screenshot establishes dragons and progression, not which formation troop types the player can currently select.",
    },
    scenarios: planned.map((item, index) => {
      const primary = item.planner_result.primary_candidate;
      const chosen = selected[index].candidate;
      const selectionBasis = chosen.id === primary.id ? item.planner_result.strategic_qualification.selection_basis : "disjoint_pareto_override";
      const qualification = strategicQualification([chosen], validatePlannerInput(data, item.input), selectionBasis);
      const candidates = requestMode === "top_n_per_matchup" ? uniqueCandidateChoices(item.planner_result).slice(0, topN) : [chosen];
      const alternative = item.planner_result.pareto_finalists.find(candidate => candidate.id !== chosen.id) || null;
      return {
        scenario_id: item.id,
        label: item.label,
        enemy_assumption: {
          common_formation_id: item.resolvedEnemy.common_formation_id || null,
          common_formation_name: item.resolvedEnemy.common_formation_name || null,
          troop_type: item.resolvedEnemy.troop_type || null,
          formation: item.resolvedEnemy.formation,
          source: item.resolvedEnemy.common_formation_id ? "data/common_formations.json reference assumptions" : "explicit scenario input",
        },
        planner_result: item.planner_result,
        selected_candidates: candidates,
        selection_attestation: {
          selected_candidate_id: chosen.id,
          planner_primary_id: primary.id,
          selection: chosen.id === primary.id ? "planner_primary" : "pareto_override_for_disjoint_armies",
          pareto_rank: selected[index].rank + 1,
          selection_policy: reusePolicy === "disjoint_armies" ? "Lowest-total-rank allocation across documented Pareto finalists with no dragon reused between scenarios." : "Planner primary under the documented deterministic lexicographic policy.",
        },
        strategic_qualification: qualification,
        coverage_matrix: chosen.threat_coverage,
        gate_report: chosen.gate_report,
        decision_evidence: chosen.decision_evidence,
        risks: [...chosen.risks, ...(preflight.verified_complete ? [] : [{ type: "roster_scope", detail: "The roster was not explicitly verified complete; exhaustive search applies only to the submitted dragons." }])],
        common_baselines: item.planner_result.common_baselines,
        strongest_alternative: alternative,
        reversal_conditions: reversalConditions(chosen, alternative, { includeCapacity: item.planner_result.input_summary.capacity_sensitive_objective }),
      };
    }),
  };
  result.cross_scenario_summary = {
    selected_formations: result.scenarios.map(scenario => ({ scenario_id: scenario.scenario_id, candidate_id: scenario.selected_candidates[0].id, dragons: summaryDragonSlugs(scenario.selected_candidates[0]), troop_type: scenario.selected_candidates[0].formation.troop_type })),
    repeated_dragons: Object.entries(result.scenarios.flatMap(scenario => summaryDragonSlugs(scenario.selected_candidates[0])).reduce((counts, slug) => ({ ...counts, [slug]: (counts[slug] || 0) + 1 }), {})).filter(([, count]) => count > 1).map(([slug]) => slug),
  };
  result.strategic_qualification = {
    qualified: result.scenarios.every(scenario => scenario.strategic_qualification.qualified),
    status: result.scenarios.every(scenario => scenario.strategic_qualification.qualified) ? "qualified" : "not_strategically_qualified",
    failures: result.scenarios.flatMap(scenario => scenario.strategic_qualification.failures.map(failure => `${scenario.scenario_id}: ${failure}`)),
    meaning: "Aggregate strategic qualification covers each selected scenario and remains separate from structural validation.",
  };
  result.validation = validateBatchResult(result);
  if (!result.validation.valid) throw new Error(`Batch result failed output validation: ${result.validation.failures.join(" ")}`);
  return result;
}

function markdownCell(value) {
  return String(value ?? "Unknown").replaceAll("|", "\\|").replaceAll("\n", " ");
}

function formatFormationTable(candidate) {
  const labels = { "Left Flank": "Left Flank", Vanguard: "Vanguard", "Right Flank": "Right Flank" };
  const rows = candidate.progression.map(item => `| ${labels[item.lane] || item.lane} | ${markdownCell(item.dragon)} | ${markdownCell(item.level)} | ${markdownCell(item.stars)} | ${markdownCell(item.power)} | ${markdownCell(Object.entries(item.habit_levels || {}).map(([key, level]) => `${key}=${level}`).join(", ") || "Unknown")} |`);
  return ["| Position | Dragon | Level | Star rank | Current Power | Habit levels |", "|---|---|---:|---:|---:|---|", ...rows].join("\n");
}

function affinityPolicyLines(policy) {
  if (!policy) return [];
  const lines = [`Affinity policy: **${policy.status}**. ${policy.justification}`];
  if (policy.override_applied) {
    lines.push("", "Compensating documented synergy:");
    for (const synergy of policy.documented_synergies || []) lines.push(`- ${synergy.producer} **${synergy.producerAbility}** → ${synergy.consumer} **${synergy.consumerAbility}** through ${synergy.effect}; reliability: ${synergy.reliability}; prerequisite: ${synergy.prerequisite}.`);
  }
  return lines;
}

export function renderBatchMarkdown(result) {
  if (!result?.validation?.valid) throw new Error("Cannot render an unvalidated batch result.");
  const lines = [
    "# Dragonfire multi-matchup recommendation report",
    "",
    `Interpretation: **${result.request_interpretation.request_mode}**; dragon reuse policy: **${result.request_interpretation.reuse_policy}**.`,
    `Roster preflight: ${result.roster_preflight.verified_complete ? `declared complete (${result.roster_preflight.declared_owned_dragons} submitted dragons; count checked when supplied)` : "declared roster subset; conclusions are scoped to supplied dragons"}. The planner does not independently read the screenshot.`,
    `Troop availability: ${result.troop_preflight.available_troops.map(item => `${item.scenario_id}: ${item.troop_types.join(", ")} (${item.source})`).join("; ")}. The lineup screenshot does not establish selectable troop types.`,
    "",
    "| Scenario | Selected candidate | Troop | Selection |",
    "|---|---|---|---|",
    ...result.scenarios.map(scenario => `| ${markdownCell(scenario.label)} | ${markdownCell(scenario.selected_candidates[0].id)} | ${markdownCell(scenario.selected_candidates[0].formation.troop_type)} | ${markdownCell(scenario.selection_attestation.selection)} |`),
  ];
  for (const scenario of result.scenarios) {
    const candidate = scenario.selected_candidates[0];
    lines.push("", `## ${scenario.label}`, "", "### Recommended formation", "", `Shared troop: **${candidate.formation.troop_type}**`, "", formatFormationTable(candidate));
    lines.push("", ...affinityPolicyLines(candidate.affinity_policy));
    lines.push("", `Enemy progression: ${scenario.enemy_assumption.source}; ${scenario.enemy_assumption.formation.map(item => `${item.dragon} Level ${item.level}, Rank ${item.stars}, Habit levels ${Object.values(item.habit_levels || {}).length ? [...new Set(Object.values(item.habit_levels))].join("/") : "unknown"}`).join("; ")}.`);
    if (scenario.selected_candidates.length > 1) {
      lines.push("", "### Additional Pareto finalists", "", "| Rank | Candidate | Formation | Shared troop |", "|---:|---|---|---|");
      for (const [index, finalist] of scenario.selected_candidates.slice(1).entries()) lines.push(`| ${index + 2} | ${markdownCell(finalist.id)} | ${markdownCell([finalist.formation.left_flank, finalist.formation.vanguard, finalist.formation.right_flank].join(" / "))} | ${markdownCell(finalist.formation.troop_type)} |`);
    }
    lines.push("", "### Threat coverage", "", "Coverage labels describe documented applicability, not damage prevented or predicted battle outcomes.", "", "| Enemy threat | Source instances | Coverage | Documented response | Remaining gap |", "|---|---|---|---|---|");
    for (const row of scenario.coverage_matrix) {
      const sources = row.enemy_sources.map(source => `${source.dragon}: ${source.ability} (${source.timing || "timing unknown"})`).join("; ");
      lines.push(`| ${markdownCell(row.threat)} | ${markdownCell(sources)} | ${markdownCell(row.state)} | ${markdownCell(row.responses.map(response => `${response.dragon}: ${response.ability}`).join("; ") || "None")} | ${markdownCell(row.remaining_gap || "No identified limitation in documented applicability")} |`);
    }
    lines.push("", "### Gates and investment", "", "| Dragon | Ability | State | Requirement / reason |", "|---|---|---|---|");
    for (const gate of scenario.gate_report) lines.push(`| ${markdownCell(gate.dragon)} | ${markdownCell(gate.ability)} | ${markdownCell(gate.state)} | ${markdownCell(gate.reason || "Active under supplied progression")} |`);
    lines.push("", "### Expert/common-baseline check", "");
    lines.push("Evaluated under the supplied roster and troop options. Expert-recommended status is a disclosed positive prior, not an exemption from evidence or matchup gates.", "");
    for (const baseline of scenario.common_baselines) {
      const comparison = baseline.candidate ? ` Candidate \`${baseline.candidate.id}\`; direct threats ${baseline.candidate.metrics.covered_threat_count} versus selected ${candidate.metrics.covered_threat_count}; affinity matches ${baseline.candidate.metrics.affinity_count} versus selected ${candidate.metrics.affinity_count}.` : "";
      lines.push(`- ${baseline.name}: **${baseline.status}**${baseline.reasons.length ? ` — ${baseline.reasons.join(" ")}` : ""}.${comparison}`);
    }
    lines.push("", "### Alternative and reversal", "", `Strongest planner alternative: **${scenario.strongest_alternative?.id || "None"}**.`, ...scenario.reversal_conditions.map(item => `- ${item}`));
    if (scenario.risks.length) lines.push("", "### Risks", "", ...scenario.risks.map(item => `- ${item.detail}`));
    lines.push("", "### Evidence", "");
    for (const claim of scenario.decision_evidence) {
      if (claim.claim_type === "threat_response") lines.push(`- ${claim.threat}: ${claim.dragon} — ${claim.ability}; ${claim.evidence?.canonical_source || "unknown source"} → ${claim.evidence?.encyclopedia_pointer || "unknown pointer"}.`);
      if (claim.claim_type === "producer_payoff") lines.push(`- ${claim.effect}: ${claim.producer.dragon} ${claim.producer.ability} → ${claim.consumer.dragon} ${claim.consumer.ability}.`);
      if (claim.claim_type === "formation_selection") lines.push(`- Formation records: ${claim.evidence.map(item => `${item.canonical_source || "unknown source"} → ${item.encyclopedia_pointer || "unknown pointer"}`).join("; ")}.`);
    }
    lines.push("", "### Audit status", "", `Selected candidate: \`${scenario.selection_attestation.selected_candidate_id}\`; planner primary: \`${scenario.selection_attestation.planner_primary_id}\`; selection rule: ${scenario.selection_attestation.selection_policy}`, `Strategic qualification: **${scenario.strategic_qualification.status}** (${scenario.strategic_qualification.qualified}).`);
  }
  lines.push("", "## Structural validation", "", "`validation.valid: true`.", "", "## Strategic qualification", "", `Status: **${result.strategic_qualification.status}**; qualified: **${result.strategic_qualification.qualified}**.`);
  if (result.strategic_qualification.failures.length) lines.push("", ...result.strategic_qualification.failures.map(failure => `- ${failure}`));
  lines.push("", "This is a mechanics-constrained comparison, not a win-rate prediction.");
  return `${lines.join("\n")}\n`;
}

export function renderPortfolioMarkdown(result) {
  if (!result?.validation?.valid) throw new Error("Cannot render an unvalidated formation portfolio.");
  const grouped = Array.isArray(result.request_interpretation.portfolio_groups);
  const lines = [
    "# Dragonfire non-overlapping formation portfolio",
    "",
    `Objective: **${result.metadata.objective}**. Requested formations: **${result.request_interpretation.formation_count}**. Dragon reuse: **${result.request_interpretation.reuse_policy}**.`,
    `Interpretation: ${result.request_interpretation.default_semantics}`,
    `Roster preflight: verified complete with ${result.roster_preflight.declared_owned_dragons} owned dragons${result.roster_preflight.expected_visible_dragons == null ? "" : `; expected visible count ${result.roster_preflight.expected_visible_dragons}`}.`,
    `Troop availability: ${result.troop_preflight.available_troops.join(", ")} (${result.troop_preflight.source}).`,
    `Capacity basis: ${result.input_summary.capacity_basis}`,
    `Competitive context: requested **${result.input_summary.competitive_context.requested}**, resolved **${result.input_summary.competitive_context.resolved}**. Selection basis: **${result.allocation_attestation.selection_basis}**.`,
  ];
  if (grouped) {
    lines.push("", "## Ordered portfolio groups", "");
    for (const group of result.request_interpretation.portfolio_groups) {
      const constraints = [
        group.constraints.minimum_dragon_level == null ? null : `minimum dragon level ${group.constraints.minimum_dragon_level}`,
        group.constraints.minimum_positive_affinities == null ? null : `minimum ${group.constraints.minimum_positive_affinities} positive affinities for the shared troop`,
      ].filter(Boolean);
      const preference = group.preferences.rarity_order.length ? `; rarity preference ${group.preferences.rarity_order.join(" then ")}` : "";
      const affinityPolicy = group.preferences.affinity_policy === "perfect_unless_explicit_synergy" ? "; prefer 3/3 shared affinity; compare documented synergy against the strongest 3/3 candidate in this group, or disclose when none exists" : "";
      lines.push(`- **${group.label}** (${group.count}): objective **${group.objective}**; ${constraints.length ? constraints.join("; ") : "no additional hard constraints"}${preference}${affinityPolicy}.`);
    }
  }
  lines.push("", grouped
    ? "| Priority | Group | Candidate ID | Left Flank | Vanguard | Right Flank | Shared troop | Affinities | Minimum level | Viability | Capacity proxy | Group rank |"
    : "| Priority | Candidate ID | Left Flank | Vanguard | Right Flank | Shared troop | Viability | Evidence prior | Preservation | Capacity proxy | Global rank |",
  grouped
    ? "|---:|---|---|---|---|---|---|---:|---:|---|---:|---:|"
    : "|---:|---|---|---|---|---|---|---|---:|---:|---:|",
  ...result.selected_formations.map(item => {
    const candidate = item.candidate;
    if (grouped) return `| ${item.priority} | ${markdownCell(item.portfolio_group.label)} | ${markdownCell(candidate.id)} | ${markdownCell(candidate.formation.left_flank)} | ${markdownCell(candidate.formation.vanguard)} | ${markdownCell(candidate.formation.right_flank)} | ${markdownCell(candidate.formation.troop_type)} | ${item.constraint_attestation.positive_affinity_count_observed} | ${item.constraint_attestation.minimum_dragon_level_observed} | ${candidate.metrics.competitive_viability.qualified ? "Qualified" : "Not qualified"} | ${markdownCell(candidate.metrics.modeled_team_capacity)} | ${item.group_candidate_rank} |`;
    return `| ${item.priority} | ${markdownCell(candidate.id)} | ${markdownCell(candidate.formation.left_flank)} | ${markdownCell(candidate.formation.vanguard)} | ${markdownCell(candidate.formation.right_flank)} | ${markdownCell(candidate.formation.troop_type)} | ${candidate.metrics.competitive_viability.qualified ? "Qualified" : "Not qualified"} | ${candidate.expert_prior ? "Expert-recommended" : "Generated"} | ${markdownCell(candidate.metrics.troop_preservation.tier_label)} (${markdownCell(candidate.metrics.troop_preservation.score)}) | ${markdownCell(candidate.metrics.modeled_team_capacity)} | ${item.global_candidate_rank} |`;
  }), "", `Allocation audit: total rank cost **${result.allocation_attestation.selected.total_rank_cost}**; selection basis **${result.allocation_attestation.selection_basis}**; greedy selection used: **false**; exhaustive candidate pool used: **true**${grouped ? "; group constraints enforced: **true**" : ""}.`);
  for (const item of result.selected_formations) {
    const candidate = item.candidate;
    lines.push("", `## Priority ${item.priority}: ${candidate.id}`, "", `Shared troop: **${candidate.formation.troop_type}**`, "", formatFormationTable(candidate));
    if (grouped) {
      const affinityPolicy = item.constraint_attestation.affinity_policy;
      lines.push("", `Portfolio group: **${item.portfolio_group.label}**; objective **${item.portfolio_group.objective}**; group candidate rank **${item.group_candidate_rank}**.`, `Constraint check: minimum dragon level **${item.constraint_attestation.minimum_dragon_level_observed}**; positive affinities **${item.constraint_attestation.positive_affinity_count_observed}**; affinity policy **${affinityPolicy.status}**; satisfied: **${item.constraint_attestation.satisfied}**.`, ...affinityPolicyLines(affinityPolicy));
    } else lines.push("", ...affinityPolicyLines(candidate.affinity_policy));
    lines.push("", "### Troop-preservation evidence", "", "| Dragon | Ability | Evidence type | Contribution | Reliability |", "|---|---|---|---:|---|");
    const components = candidate.metrics.troop_preservation.components.filter(component => component.score !== 0);
    if (!components.length) lines.push("| — | — | No active documented preservation component | 0 | — |");
    else for (const component of components) lines.push(`| ${markdownCell(component.dragon)} | ${markdownCell(component.ability)} | ${markdownCell(component.effect_id || component.kind)} | ${markdownCell(component.score)} | ${component.chance_known === false ? "Unknown Habit reliability" : component.chance_percent == null ? "Guaranteed when its stated trigger/condition is met" : `${component.chance_percent}%`} |`);
    lines.push("", "### Capacity proxy", "", "Recorded Star scalars are disclosed but not applied because the final-stat formula is unverified.", "", "| Dragon | Level curve | Dragon's Army | Proxy capacity | Star scalar (not applied) |", "|---|---:|---:|---:|---:|");
    for (const capacity of candidate.metrics.modeled_capacity_by_dragon || []) lines.push(`| ${markdownCell(capacity.dragon)} | ${markdownCell(capacity.base_max_army_size)} | ${markdownCell(capacity.dragons_army_bonus)} | ${markdownCell(capacity.modeled_max_army_size)} | ${markdownCell(capacity.star_scalar)} |`);
    if (item.risks.length) lines.push("", "### Risks and unknowns", "", ...item.risks.map(risk => `- ${risk.detail}`));
    lines.push("", "### Evidence locators", "", ...candidate.evidence.map(entry => `- ${entry.canonical_source || "unknown source"} → ${entry.encyclopedia_pointer || "unknown pointer"}`));
  }
  lines.push("", "## Expert/common-baseline check", "", ...result.common_baselines.map(baseline => `- ${baseline.name}: **${baseline.status}**${baseline.reasons.length ? ` — ${baseline.reasons.join(" ")}` : baseline.candidate ? ` — candidate \`${baseline.candidate.id}\`${baseline.candidate.expert_prior ? "; expert-recommended prior retained" : ""}` : ""}.`));
  if (result.allocation_attestation.expert_baseline_portfolio) lines.push("", "## Expert portfolio benchmark", "", `Candidate IDs: ${result.allocation_attestation.expert_baseline_portfolio.candidate_ids.map(id => `\`${id}\``).join(", ")}; global rank cost ${result.allocation_attestation.expert_baseline_portfolio.total_rank_cost}.`);
  if (result.allocation_attestation.strongest_alternative) lines.push("", "## Strongest alternative portfolio", "", `Candidate IDs: ${result.allocation_attestation.strongest_alternative.candidate_ids.map(id => `\`${id}\``).join(", ")}; total rank cost ${result.allocation_attestation.strongest_alternative.total_rank_cost}.`);
  lines.push("", "## Limitations", "", ...result.limitations.map(limitation => `- ${limitation}`));
  lines.push("", "## Structural validation", "", "`validation.valid: true`. The count, non-overlap, roster preflight, candidate IDs, and evidence references are structurally valid.");
  lines.push("", "## Strategic qualification", "", `Status: **${result.strategic_qualification.status}**; qualified: **${result.strategic_qualification.qualified}**; selection basis: **${result.strategic_qualification.selection_basis}**.`);
  if (result.strategic_qualification.failures.length) lines.push("", ...result.strategic_qualification.failures.map(failure => `- ${failure}`));
  lines.push("", "This remains a documented-mechanics portfolio comparison, not a simulated win-rate or predicted casualty total.");
  return `${lines.join("\n")}\n`;
}

function main() {
  try {
    const options = parseArgs(process.argv.slice(2));
    if (options.help) {
      process.stdout.write(`${usage()}\n`);
      return 0;
    }
    if (!options.input) throw new Error("Supply --input with a saved JSON scenario or profile file.");
    if (!Number.isInteger(options.maxFinalists) || options.maxFinalists < 1 || options.maxFinalists > 100) throw new Error("--max-finalists must be an integer from 1 to 100.");
    if (!["json", "markdown"].includes(options.format)) throw new Error("--format must be json or markdown.");
    const data = JSON.parse(fs.readFileSync(DATA_PATH, "utf8"));
    const baselines = JSON.parse(fs.readFileSync(BASELINES_PATH, "utf8"));
    const input = JSON.parse(fs.readFileSync(path.resolve(options.input), "utf8"));
    input.max_finalists = options.maxFinalists;
    const result = isBatchInput(input) ? planBatchRecommendations(data, baselines, input) : isPortfolioInput(input) ? planFormationPortfolio(data, baselines, input) : planRecommendations(data, baselines, input);
    if (options.format === "markdown" && !isBatchInput(input) && !isPortfolioInput(input)) throw new Error("--format markdown requires a batch input with scenarios or a formation portfolio input.");
    const output = options.format === "markdown"
      ? isBatchInput(input) ? renderBatchMarkdown(result) : renderPortfolioMarkdown(result)
      : JSON.stringify(result, null, options.pretty || options.output ? 2 : 0);
    if (options.output) fs.writeFileSync(path.resolve(options.output), `${output}\n`, "utf8");
    else process.stdout.write(`${output}\n`);
    return 0;
  } catch (error) {
    process.stderr.write(`recommendation-planner: ${error.message}\n\n${usage()}\n`);
    return 2;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exitCode = main();

