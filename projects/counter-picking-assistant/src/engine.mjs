export const LANES = ["Left Flank", "Vanguard", "Right Flank"];
export const TROOPS = ["Archers", "Cavalry", "Shieldbearers", "Spearmen", "Siege"];

const unique = values => [...new Set(values)];
const graphCache = new WeakMap();
const graphMap = (data, bucket) => {
  if (!graphCache.has(data)) graphCache.set(data, {});
  const cached = graphCache.get(data);
  if (!cached[bucket]) cached[bucket] = new Map((data.graph?.[bucket] || []).map(item => [item.id, item]));
  return cached[bucket];
};
const abilityRecords = (data, ability, bucket) => {
  const records = graphMap(data, bucket);
  return (ability.normalized?.[`${bucket.slice(0, -1)}_refs`] || []).map(id => records.get(id)).filter(Boolean);
};

export function abilityEligible(ability, slot) {
  const unlock = ability.unlock || {};
  if (unlock.star_rank && Number(slot.stars) < Number(unlock.star_rank)) return false;
  if (unlock.level && Number(slot.level) < Number(unlock.level)) return false;
  if (ability.kind === "vanguard" && slot.lane !== "Vanguard") return false;
  if (ability.kind === "habit" && slot.habit_levels?.[ability.client_key] === 0) return false;
  return true;
}

function recordEligible(record, progression) {
  const gate = record?.exact_context?.match(/At\s+(\d+)\+?\s+Stars/i);
  return !gate || Number(progression.stars) >= Number(gate[1]);
}

function expandRounds(records) {
  if (!records.length) return null;
  const rounds = [];
  for (const item of records) {
    if (item.recurrence === "each_round") rounds.push(...Array.from({ length: 10 }, (_, index) => index + 1));
    else if (item.parity === "odd") rounds.push(1, 3, 5, 7, 9);
    else if (item.parity === "even") rounds.push(2, 4, 6, 8, 10);
    else rounds.push(...(item.rounds || []));
  }
  return unique(rounds).sort((a, b) => a - b);
}

function scopedSchedules(data, ability, context = null, inline = null) {
  if (Array.isArray(inline)) return inline;
  const records = abilityRecords(data, ability, "schedules");
  return context ? records.filter(item => context.toLowerCase().includes(item.exact_text.toLowerCase())) : records;
}

function roundsFor(data, ability, context = null, inline = null) {
  return expandRounds(scopedSchedules(data, ability, context, inline));
}

function timingLabel(data, ability, context = null, inline = null) {
  const records = scopedSchedules(data, ability, context, inline);
  return records.length ? unique(records.map(item => item.exact_text)).join(" · ") : "Triggered or passive; exact round not stated";
}

function targetLabel(data, ability) {
  const records = abilityRecords(data, ability, "targeters");
  return records.length ? unique(records.map(item => item.exact_text)).join(" · ") : "Target scope not normalized";
}

function habitLevel(ability, progression) {
  return Number(progression.habit_levels?.[ability.client_key] || 0);
}

export function currentHabitValue(ability, progression) {
  const level = habitLevel(ability, progression);
  if (ability.kind !== "habit" || !level) return null;
  const value = ability.upgrade_levels?.[String(level)];
  return value == null ? null : Number(value);
}

function operationChance(ability, operation, progression) {
  if (ability.kind === "habit" && /chance/i.test(ability.value_unit || "")) {
    const upgraded = currentHabitValue(ability, progression);
    if (upgraded != null) return upgraded;
  }
  return operation.chance_percent == null ? null : Number(operation.chance_percent);
}

function operationRecords(data, ability, progression) {
  return abilityRecords(data, ability, "status_operations")
    .filter(item => recordEligible(item, progression))
    .map(item => ({ ...item, chance_percent: operationChance(ability, item, progression) }));
}

function conditionRecords(data, ability) {
  return abilityRecords(data, ability, "conditions").filter(item => item.type === "status_present");
}

function activeAbilities(data, dragon, progression, lane) {
  return dragon.abilities.filter(ability => abilityEligible(ability, { ...progression, lane }));
}

function threatSource(data, dragon, ability, detail = null) {
  const context = detail?.exact_context || ability.exact_text[0];
  const inline = detail && Object.hasOwn(detail, "schedules") ? detail.schedules : null;
  return {
    dragon: dragon.name,
    dragon_slug: dragon.slug,
    ability: ability.name,
    ability_id: ability.id,
    exact_text: context,
    chance_percent: detail?.chance_percent ?? null,
    rounds: roundsFor(data, ability, context, inline),
    timing: timingLabel(data, ability, context, inline),
    target: targetLabel(data, ability),
  };
}

export function extractThreats(data, enemySlots) {
  const effects = new Map(data.effects.map(item => [item.id, item]));
  const threats = new Map();
  for (const slot of enemySlots) {
    const dragon = data.dragons.find(item => item.slug === slot.dragon);
    if (!dragon) continue;
    for (const ability of activeAbilities(data, dragon, slot, slot.lane)) {
      const damageEvents = ability.normalized.damage_events?.length
        ? ability.normalized.damage_events
        : (ability.normalized.damage_types || []).map(damage_type => ({ damage_type, exact_context: ability.exact_text[0] }));
      for (const event of damageEvents) {
        addThreat(threats, { id: `damage:${event.damage_type}`, category: "damage", name: event.damage_type }, threatSource(data, dragon, ability, event));
      }
      for (const operation of operationRecords(data, ability, slot)) {
        const effect = effects.get(operation.effect_id);
        if (operation.operation !== "applies" || !effect) continue;
        if (effect.id === "effect:recovery") addThreat(threats, { id: "sustain:recovery", category: "sustain", name: "Recovery" }, threatSource(data, dragon, ability, operation));
        else if (effect.effect_on_target === "harmful") addThreat(threats, { id: `status:${effect.id}`, category: "status", effect_id: effect.id, name: effect.name }, threatSource(data, dragon, ability, operation));
      }
    }
  }
  return [...threats.values()];
}

function addThreat(map, base, source) {
  const current = map.get(base.id);
  if (current) current.sources.push(source);
  else map.set(base.id, { ...base, sources: [source] });
}

function timingAssessment(data, ability, threat, context = null) {
  const counterRounds = roundsFor(data, ability, context);
  const threatRounds = unique(threat.sources.flatMap(source => source.rounds || []));
  if (!counterRounds?.length || !threatRounds.length) return { state: "unknown", score: 0, note: "Exact timing alignment is not established." };
  const counterFirst = Math.min(...counterRounds);
  const threatFirst = Math.min(...threatRounds);
  if (counterFirst <= threatFirst) return { state: "aligned", score: 1, note: `Available by the first documented threat window (round ${threatFirst}).` };
  return { state: "delayed", score: -1, note: `Begins in round ${counterFirst}, after the threat first appears in round ${threatFirst}.` };
}

function evidenceReliability(data, ability, progression, relation = null) {
  if (ability.evidence && ability.evidence.confidence !== "confirmed") return { chance_percent: null, unresolved: true, label: "Conditional client-only evidence; activation values are unresolved" };
  const operations = operationRecords(data, ability, progression);
  const relevant = relation && relation.relationship !== "counters"
    ? operations.filter(item => item.effect_id === "effect:cleanse" || item.operation === "applies" && /cleanse/i.test(item.exact_context))
    : operations;
  const chances = relevant.map(item => item.chance_percent).filter(value => value != null);
  if (!chances.length) return { chance_percent: null, label: "Guaranteed when its stated trigger/condition is met" };
  const chance = Math.min(...chances);
  return { chance_percent: chance, label: `${chance}% activation at the saved Habit level or documented fixed rate` };
}

function laneEvidence(data, dragon, abilities, lane, enemySlots) {
  const notes = [];
  let score = 0;
  const enemyHere = enemySlots.find(item => item.lane === lane);
  for (const ability of abilities) {
    const targeters = abilityRecords(data, ability, "targeters");
    const prioritizers = abilityRecords(data, ability, "prioritizers");
    if (enemyHere && targeters.some(item => item.scope === "same_lane" && item.side !== "ally")) {
      notes.push(`${ability.name} applies matching-lane pressure to ${enemyHere.name || enemyHere.dragon} in ${lane}.`);
      score += 1;
    }
    for (const priority of prioritizers.filter(item => item.priority_type === "lane")) {
      const target = enemySlots.find(item => item.lane.toLowerCase() === priority.field.toLowerCase());
      if (target) {
        notes.push(`${ability.name} explicitly ${priority.exact_text.toLowerCase()} (${target.name || target.dragon}).`);
        score += 1.5;
      }
    }
    for (const priority of prioritizers.filter(item => item.priority_type === "breed")) {
      const breed = priority.field.replace(/s$/i, "");
      const targets = enemySlots.filter(item => item.breed?.toLowerCase() === breed.toLowerCase());
      if (targets.length) {
        notes.push(`${ability.name} prioritizes ${breed}s, matching ${targets.map(item => item.name || item.dragon).join(", ")}.`);
        score += 1.5;
      }
    }
    if (ability.kind === "vanguard") {
      for (const direction of targeters.filter(item => ["left_flank", "right_flank"].includes(item.scope))) {
        notes.push(`${ability.name} explicitly supports the ${direction.scope === "left_flank" ? "Left Flank" : "Right Flank"}; placement preserves that directional value.`);
        score += 1;
      }
    }
  }
  return { notes: unique(notes), score };
}

export function candidateEvidence(data, dragon, threats, progression = { stars: 10, level: 50, habit_levels: {} }, lane = "Vanguard", enemySlots = []) {
  const counters = [];
  const abilities = activeAbilities(data, dragon, progression, lane);
  const textAbilities = abilities.map(ability => ({ ability, text: ability.exact_text.join(" ") }));
  for (const threat of threats) {
    let match = null;
    let reason = null;
    let relation = null;
    if (threat.category === "damage") {
      const token = threat.name.replace(" Damage", "");
      match = textAbilities.find(item => new RegExp(`(?:reduce|decrease)[^.]{0,100}${token} Damage (?:Dealt|Received)`, "i").test(item.text));
      reason = match && `Mitigates ${threat.name}`;
    } else if (threat.category === "sustain") {
      match = textAbilities.find(item => /reduce[^.]{0,100}Recovery Received|Prey reduces Recovery Received/i.test(item.text));
      reason = match && "Pressures enemy Recovery";
    } else if (threat.effect_id) {
      const effect = data.effects.find(item => item.id === threat.effect_id);
      relation = [...(effect?.relationships?.counters || []), ...(effect?.relationships?.cleanses || [])]
        .find(item => item.dragon_id === dragon.id && item.lifecycle !== "staged" && abilities.some(ability => ability.id === item.ability_id));
      const ability = relation && abilities.find(item => item.id === relation.ability_id);
      match = ability && { ability, text: ability.exact_text.join(" ") };
      reason = relation && (relation.relationship === "counters" ? `Counters ${threat.name}` : `May cleanse ${threat.name} by category`);
    }
    if (!match) continue;
    const exactText = relation && relation.relationship !== "counters"
      ? match.ability.exact_text.find(line => /cleanse/i.test(line))
      : match.ability.exact_text.find(line => line.toLowerCase().includes(threat.name.toLowerCase().replace(" damage", "")));
    const selectedText = exactText || match.ability.exact_text[0];
    const reliability = evidenceReliability(data, match.ability, progression, relation);
    const timing = timingAssessment(data, match.ability, threat, selectedText);
    counters.push({
      threat_id: threat.id, threat_name: threat.name, reason, ability: match.ability.name, ability_id: match.ability.id,
      exact_text: selectedText,
      reliability, timing,
    });
  }
  const effects = new Map(data.effects.map(item => [item.id, item]));
  const controls = [];
  for (const ability of abilities) for (const operation of operationRecords(data, ability, progression)) {
    const effect = effects.get(operation.effect_id);
    if (operation.operation === "applies" && effect?.game_section === "Control Effects" && effect.effect_on_target === "harmful") {
      controls.push({ name: effect.name, ability: ability.name, ability_id: ability.id, exact_text: operation.exact_context, chance_percent: operation.chance_percent });
    }
  }
  const lanePlan = laneEvidence(data, dragon, abilities.filter(ability => ability.evidence?.confidence !== "limited"), lane, enemySlots);
  const confirmedCounters = counters.filter(item => !item.reliability.unresolved);
  const conditionalCounters = counters.filter(item => item.reliability.unresolved);
  return {
    dragon, progression, lane, abilities, counters, controls,
    covered: unique(confirmedCounters.map(item => item.threat_id)),
    conditionalCovered: unique(conditionalCounters.map(item => item.threat_id)),
    laneNotes: lanePlan.notes, laneScore: lanePlan.score,
  };
}

export function chooseTroop(data, trio, enemyTroop, objective = "pvp") {
  const rules = data.mechanics.troop_types;
  return TROOPS.map(troop => {
    const positive = trio.filter(item => item.troop_affinities.positive.includes(troop)).map(item => item.name);
    const negative = trio.filter(item => item.troop_affinities.negative.includes(troop)).map(item => item.name);
    const advantage = rules[troop]?.advantaged_against === enemyTroop;
    const disadvantage = rules[troop]?.disadvantaged_against === enemyTroop || (troop === "Siege" && objective !== "poi");
    const value = positive.length * 2 - negative.length * 3 + (advantage ? 3 : 0) - (disadvantage ? 3 : 0) + (objective === "poi" && troop === "Siege" ? 5 : 0);
    return { troop, positive, negative, advantage, disadvantage, value };
  }).sort((a, b) => b.value - a.value || a.troop.localeCompare(b.troop))[0];
}

function compatibleChain(effect, condition) {
  if (effect.effect_on_target === "harmful") return ["enemy", "target"].includes(condition.subject);
  if (effect.effect_on_target === "beneficial") return ["ally", "self", "target"].includes(condition.subject);
  return false;
}

export function formationSynergies(data, formation) {
  const effects = new Map(data.effects.map(item => [item.id, item]));
  const producers = [];
  const consumers = [];
  for (const pick of formation) for (const ability of pick.abilities.filter(item => item.evidence?.confidence !== "limited")) {
    for (const operation of operationRecords(data, ability, pick.progression)) if (operation.operation === "applies") producers.push({ pick, ability, operation });
    for (const condition of conditionRecords(data, ability)) consumers.push({ pick, ability, condition });
  }
  const chains = [];
  for (const producer of producers) for (const consumer of consumers) {
    if (producer.pick.dragon.id === consumer.pick.dragon.id || producer.operation.effect_id !== consumer.condition.status_id) continue;
    const effect = effects.get(producer.operation.effect_id);
    if (!effect || !compatibleChain(effect, consumer.condition)) continue;
    const chance = producer.operation.chance_percent;
    chains.push({
      effect: effect.name, producer: producer.pick.dragon.name, producerAbility: producer.ability.name,
      consumer: consumer.pick.dragon.name, consumerAbility: consumer.ability.name,
      chance_percent: chance, reliability: chance == null ? "Guaranteed when triggered" : `${chance}% producer activation`,
      prerequisite: consumer.condition.exact_text, score: chance == null ? 8 : Math.max(1, 8 * chance / 100),
    });
  }
  const best = new Map();
  for (const chain of chains) {
    const key = `${chain.effect}|${chain.producer}|${chain.consumer}|${chain.consumerAbility}`;
    if (!best.has(key) || best.get(key).score < chain.score) best.set(key, chain);
  }
  return [...best.values()].sort((a, b) => b.score - a.score || a.effect.localeCompare(b.effect)).slice(0, 6);
}

function habitReliability(data, formation) {
  const entries = [];
  for (const pick of formation) for (const ability of pick.abilities.filter(item => item.kind === "habit")) {
    const chances = operationRecords(data, ability, pick.progression).map(item => item.chance_percent).filter(value => value != null);
    if (!chances.length) continue;
    entries.push({ dragon: pick.dragon.name, ability: ability.name, level: habitLevel(ability, pick.progression), chance_percent: Math.max(...chances), value_unit: ability.value_unit });
  }
  return entries.sort((a, b) => b.chance_percent - a.chance_percent).slice(0, 6);
}

function combatHorizon(data, formation) {
  const scheduled = formation.flatMap(pick => pick.abilities.map(ability => ({ dragon: pick.dragon.name, ability: ability.name, rounds: roundsFor(data, ability) })).filter(item => item.rounds?.length));
  const opening = scheduled.filter(item => item.rounds.some(round => round >= 0 && round <= 3)).map(item => `${item.dragon}: ${item.ability}`);
  const late = scheduled.filter(item => item.rounds.some(round => round >= 7 && round <= 10)).map(item => `${item.dragon}: ${item.ability}`);
  return { opening: unique(opening).slice(0, 5), late: unique(late).slice(0, 5) };
}

function permutations(items) {
  return [
    [items[0], items[1], items[2]], [items[0], items[2], items[1]], [items[1], items[0], items[2]],
    [items[1], items[2], items[0]], [items[2], items[0], items[1]], [items[2], items[1], items[0]],
  ];
}

function scoreFormation(data, formation, threats, enemyTroop, objective) {
  const covered = unique(formation.flatMap(item => item.covered));
  const conditionalCovered = unique(formation.flatMap(item => item.conditionalCovered || []).filter(id => !covered.includes(id)));
  const counterEvidence = formation.flatMap(item => item.counters);
  const reliability = covered.reduce((sum, threatId) => {
    const evidence = counterEvidence.filter(item => item.threat_id === threatId);
    return sum + Math.max(...evidence.map(item => item.reliability.chance_percent == null ? 1 : item.reliability.chance_percent / 100));
  }, 0);
  const timing = counterEvidence.reduce((sum, item) => sum + item.timing.score, 0);
  const synergies = formationSynergies(data, formation);
  const synergy = synergies.reduce((sum, item) => sum + item.score, 0);
  const lanes = formation.reduce((sum, item) => sum + item.laneScore, 0);
  const controls = unique(formation.flatMap(item => item.controls.map(control => control.name))).length;
  const troop = chooseTroop(data, formation.map(item => item.dragon), enemyTroop, objective);
  const breakdown = {
    threat_coverage: covered.length * 100, conditional_evidence: conditionalCovered.length * 15, counter_reliability: Math.round(reliability * 20), timing_alignment: timing * 6,
    explicit_synergy: Math.round(synergy), lane_fit: Math.round(lanes * 4), control_options: controls * 2, troop_fit: troop.value * 4,
  };
  return {
    formation, troop, threats, covered, conditionalCovered, coverage: threats.length ? covered.length / threats.length : 0,
    synergies, laneNotes: unique(formation.flatMap(item => item.laneNotes)), habitReliability: habitReliability(data, formation),
    combatHorizon: combatHorizon(data, formation), breakdown, score: Object.values(breakdown).reduce((sum, value) => sum + value, 0),
  };
}

export function recommendFormations(data, enemySlots, ownedRoster, enemyTroop, objective = "pvp") {
  const enrichedEnemies = enemySlots.map(slot => {
    const dragon = data.dragons.find(item => item.slug === slot.dragon);
    return { ...slot, name: dragon?.name, breed: dragon?.breed };
  });
  const threats = extractThreats(data, enrichedEnemies);
  const roster = new Map((ownedRoster || []).map(item => typeof item === "string" ? [item, { slug: item, owned: true, level: 50, stars: 10, habit_levels: {} }] : [item.slug, item]));
  const pool = data.dragons.filter(item => item.lifecycle !== "staged" && roster.has(item.slug) && roster.get(item.slug)?.owned !== false);
  const confidence = recommendationConfidence(enrichedEnemies);
  if (pool.length < 3) return { threats, recommendations: [], confidence };
  const cache = new Map();
  const positioned = (dragon, lane) => {
    const key = `${dragon.slug}|${lane}`;
    if (!cache.has(key)) cache.set(key, candidateEvidence(data, dragon, threats, roster.get(dragon.slug), lane, enrichedEnemies));
    return cache.get(key);
  };
  const candidates = [];
  for (let i = 0; i < pool.length - 2; i += 1) for (let j = i + 1; j < pool.length - 1; j += 1) for (let k = j + 1; k < pool.length; k += 1) {
    const trio = [pool[i], pool[j], pool[k]];
    let best = null;
    for (const order of permutations(trio)) {
      const formation = order.map((dragon, index) => positioned(dragon, LANES[index]));
      const result = scoreFormation(data, formation, threats, enemyTroop, objective);
      if (!best || result.score > best.score) best = result;
    }
    candidates.push({ ...best, signature: trio.map(item => item.slug).sort().join("|") });
  }
  candidates.sort((a, b) => b.score - a.score || b.coverage - a.coverage || a.signature.localeCompare(b.signature));
  return { threats, recommendations: candidates.slice(0, 3), confidence };
}

export function recommendationConfidence(enemySlots) {
  const known = enemySlots.filter(slot => slot.dragon);
  const missing = [];
  if (known.length < 3) missing.push(`${3 - known.length} enemy lane${3 - known.length === 1 ? " is" : "s are"} unknown`);
  if (known.some(slot => slot.level == null || !Number.isFinite(Number(slot.level)))) missing.push("one or more enemy levels are unknown");
  if (known.some(slot => slot.stars == null || !Number.isFinite(Number(slot.stars)))) missing.push("one or more enemy Star Ranks are unknown");
  const level = known.length === 3 && !missing.length ? "high" : known.length >= 2 ? "medium" : "low";
  return {
    level,
    known_lanes: known.length,
    missing,
    note: level === "high" ? "All three enemy lanes and progression gates are present." : `Recommendations cover only the ${known.length} documented enemy lane${known.length === 1 ? "" : "s"}; unknown threats are not scored.`,
  };
}

export function compareRecommendations(left, right) {
  const leftDragons = new Set(left.formation.map(item => item.dragon.slug));
  const rightDragons = new Set(right.formation.map(item => item.dragon.slug));
  const leftCovered = new Set(left.covered);
  const rightCovered = new Set(right.covered);
  return {
    left_only_dragons: left.formation.filter(item => !rightDragons.has(item.dragon.slug)).map(item => item.dragon.name),
    right_only_dragons: right.formation.filter(item => !leftDragons.has(item.dragon.slug)).map(item => item.dragon.name),
    left_only_threats: left.threats.filter(item => leftCovered.has(item.id) && !rightCovered.has(item.id)).map(item => item.name),
    right_only_threats: right.threats.filter(item => rightCovered.has(item.id) && !leftCovered.has(item.id)).map(item => item.name),
    coverage_delta: left.coverage - right.coverage,
    synergy_delta: left.synergies.length - right.synergies.length,
    troop_change: left.troop.troop === right.troop.troop ? null : `${left.troop.troop} vs ${right.troop.troop}`,
    score_delta: left.score - right.score,
  };
}

export function combatExplorerQuery(recommendation, enemies, troop) {
  const params = new URLSearchParams();
  recommendation.formation.forEach((item, index) => { params.set(`a${index + 1}`, item.dragon.slug); params.set(`a${index + 1}s`, String(item.progression.stars)); params.set(`a${index + 1}l`, String(item.progression.level)); });
  enemies.forEach((item, index) => { params.set(`e${index + 1}`, item.dragon); params.set(`e${index + 1}s`, String(item.stars)); params.set(`e${index + 1}l`, String(item.level)); });
  params.set("troop", troop);
  return params.toString();
}
