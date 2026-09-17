export const LANES = ["Left Flank", "Vanguard", "Right Flank"];

export function abilityEligible(ability, slot) {
  const unlock = ability.unlock || {};
  if (unlock.star_rank && Number(slot.stars) < Number(unlock.star_rank)) return false;
  if (unlock.level && Number(slot.level) < Number(unlock.level)) return false;
  if (ability.kind === "vanguard" && slot.lane !== "Vanguard") return false;
  return true;
}

export function scheduleMatches(schedule, round) {
  if (schedule.recurrence === "each_round") return round >= 1 && round <= 10;
  if (Array.isArray(schedule.rounds) && schedule.rounds.includes(round)) return true;
  if (schedule.parity === "odd") return round % 2 === 1;
  if (schedule.parity === "even") return round % 2 === 0;
  return false;
}

export function buildTimeline(data, scenario) {
  const schedules = new Map(data.graph.schedules.map(item => [item.id, item]));
  const dragons = new Map(data.dragons.map(item => [item.slug, item]));
  const targeters = new Map((data.graph.targeters || []).map(item => [item.id, item]));
  const prioritizers = new Map((data.graph.prioritizers || []).map(item => [item.id, item]));
  const conditions = new Map((data.graph.conditions || []).map(item => [item.id, item]));
  const statusOperations = new Map((data.graph.status_operations || []).map(item => [item.id, item]));
  const effects = new Map((data.effects || []).map(item => [item.id, item]));
  const events = [{ phase: "combat_start", round: 0, label: "Start of combat", items: [] }];
  const slots = [
    ...scenario.allies.map(slot => ({ ...slot, side: "Allied" })),
    ...scenario.enemies.map(slot => ({ ...slot, side: "Enemy" })),
  ];

  for (const slot of slots) {
    const dragon = dragons.get(slot.dragon);
    if (!dragon) continue;
    for (const ability of dragon.abilities.filter(item => abilityEligible(item, slot))) {
      const startsCombat = ability.exact_text.some(text => /start of combat/i.test(text));
      if (startsCombat) events[0].items.push(makeEvent(dragon, ability, slot, "Start of Combat", "combat_start", slots, { targeters, prioritizers, conditions, statusOperations, effects }));
    }
  }

  for (let round = 1; round <= 10; round += 1) {
    const group = { phase: "round", round, label: `Round ${round}`, items: [] };
    for (const slot of slots) {
      const dragon = dragons.get(slot.dragon);
      if (!dragon) continue;
      for (const ability of dragon.abilities.filter(item => abilityEligible(item, slot))) {
        const matched = (ability.normalized.schedule_refs || [])
          .map(id => schedules.get(id))
          .filter(Boolean)
          .filter(schedule => scheduleMatches(schedule, round));
        const byPhase = new Map();
        for (const schedule of matched) {
          const phase = schedule.phase || "round";
          byPhase.set(phase, [...(byPhase.get(phase) || []), schedule]);
        }
        for (const [phase, phaseSchedules] of byPhase) {
          group.items.push(makeEvent(dragon, ability, slot, phaseSchedules.map(schedule => schedule.exact_text).join(" · "), phase, slots, { targeters, prioritizers, conditions, statusOperations, effects }));
        }
      }
    }
    group.items.sort((left, right) => phaseRank(left.phase) - phaseRank(right.phase) || left.side.localeCompare(right.side) || left.lane.localeCompare(right.lane));
    events.push(group);
  }
  return projectStatusTimeline(events);
}

function makeEvent(dragon, ability, slot, trigger, phase, slots, graph) {
  const triggerParts = trigger.split(" · ").map(part => part.toLowerCase());
  const matchingLines = ability.exact_text.filter(text => triggerParts.some(part => text.toLowerCase().includes(part)));
  const abilityTargeters = (ability.normalized.targeter_refs || []).map(id => graph.targeters.get(id)).filter(Boolean);
  const abilityPrioritizers = (ability.normalized.prioritizer_refs || []).map(id => graph.prioritizers.get(id)).filter(Boolean);
  const abilityConditions = (ability.normalized.condition_refs || []).map(id => graph.conditions.get(id)).filter(Boolean);
  const abilityOperations = (ability.normalized.status_operation_refs || []).map(id => graph.statusOperations.get(id)).filter(Boolean);
  return {
    dragon_id: dragon.id,
    dragon_slug: dragon.slug,
    dragon_name: dragon.name,
    ability_id: ability.id,
    ability_name: ability.name,
    kind: ability.kind,
    side: slot.side,
    lane: slot.lane,
    trigger,
    phase,
    exact_text: matchingLines.length ? matchingLines : ability.exact_text,
    target_hints: ability.normalized.target_hints || [],
    target_groups: abilityTargeters.map(targeter => resolveTargeter(targeter, slot, slots)),
    priorities: abilityPrioritizers.map(item => ({ type: item.priority_type, field: item.field, direction: item.direction, exact_text: item.exact_text })),
    conditions: abilityConditions.map(item => evaluateCondition(item, slot, graph.effects)),
    status_operations: abilityOperations.map(item => ({
      operation: item.operation,
      effect_id: item.effect_id,
      effect_name: graph.effects.get(item.effect_id)?.name || item.effect_id.replace("effect:", ""),
      effect_section: graph.effects.get(item.effect_id)?.game_section || null,
      chance_percent: item.chance_percent,
      duration_rounds: item.duration_rounds,
      max_stacks: item.max_stacks,
      evidence_class: item.evidence_class,
    })),
    evidence: ability.evidence,
  };
}

function phaseRank(phase) {
  return ({ combat_start: 0, start_of_round: 1, round: 2, round_end: 3 })[phase] ?? 9;
}

export function resolveTargeter(targeter, actor, slots) {
  let pool;
  if (targeter.side === "self") pool = [actor];
  else if (targeter.side === "ally") pool = slots.filter(slot => slot.side === actor.side);
  else if (targeter.side === "enemy") pool = slots.filter(slot => slot.side !== actor.side);
  else return { scope: targeter.scope, side: targeter.side, count: targeter.count, exact_text: targeter.exact_text, candidates: [], resolution: "unresolved_side" };

  const laneIndex = lane => LANES.indexOf(lane);
  const filtered = pool.filter(candidate => {
    if (targeter.scope === "self") return candidate === actor;
    if (targeter.scope === "any_lane") return true;
    if (targeter.scope === "same_lane") return candidate.lane === actor.lane;
    if (targeter.scope === "adjacency") return Math.abs(laneIndex(candidate.lane) - laneIndex(actor.lane)) <= 1;
    if (targeter.scope === "left_flank") return candidate.lane === "Left Flank";
    if (targeter.scope === "right_flank") return candidate.lane === "Right Flank";
    if (targeter.scope === "vanguard") return candidate.lane === "Vanguard";
    return false;
  });
  const candidates = filtered.map(candidate => ({ dragon: candidate.dragon, lane: candidate.lane, side: candidate.side }));
  const requested = Number(targeter.count || candidates.length);
  const resolution = !candidates.length ? "no_candidates" : candidates.length <= requested ? "all_candidates" : "selection_required";
  return { scope: targeter.scope, side: targeter.side, count: targeter.count, exact_text: targeter.exact_text, candidates, resolution };
}

export function evaluateCondition(condition, actor, effects = new Map()) {
  if (condition.type === "star_rank" && condition.operator === "at_least") {
    const met = Number(actor.stars) >= Number(condition.value);
    return { ...condition, state: met ? "met" : "not_met", explanation: `${actor.stars} Stars ${met ? "meets" : "does not meet"} the ${condition.value}+ Star clause.` };
  }
  const effectName = condition.status_id ? (effects.get(condition.status_id)?.name || condition.status_id.replace("effect:", "")) : null;
  return { ...condition, state: "unresolved", explanation: effectName ? `Requires combat-state knowledge of ${effectName}.` : "Requires combat state that is not yet supplied." };
}

export function applyStatus(state, target, operation, round) {
  const current = state.get(target) || [];
  const existing = current.find(item => item.effect_id === operation.effect_id);
  const expiresBeforeRound = operation.duration_rounds == null ? null : round + Number(operation.duration_rounds);
  if (existing) {
    existing.stacks = Math.min(existing.stacks + 1, operation.max_stacks || existing.stacks + 1);
    if (expiresBeforeRound != null) existing.expires_before_round = Math.max(existing.expires_before_round || 0, expiresBeforeRound);
  } else {
    current.push({ effect_id: operation.effect_id, effect_name: operation.effect_name, stacks: 1, max_stacks: operation.max_stacks, applied_round: round, expires_before_round: expiresBeforeRound });
  }
  state.set(target, current);
}

export function expireStatuses(state, round) {
  for (const [target, statuses] of state) {
    state.set(target, statuses.filter(status => status.expires_before_round == null || status.expires_before_round > round));
  }
}

export function isTrackableStatus(operation) {
  // Recovery resolves troop restoration when the scheduled interaction fires. It
  // remains part of the event graph, but is not a persistent status instance.
  return operation.effect_id !== "effect:recovery";
}

export function projectStatusTimeline(timeline) {
  const state = new Map();
  const suppressors = new Set(["effect:stun", "effect:stagger", "effect:overwhelm"]);
  for (const group of timeline) {
    expireStatuses(state, group.round);
    const roundStart = new Map([...state].map(([target, statuses]) => [target, statuses.map(status => ({ ...status }))]));
    for (const event of group.items) {
      event.suppression = (roundStart.get(event.dragon_slug) || []).filter(status => suppressors.has(status.effect_id));
      event.status_projection = [];
      const relevantText = event.exact_text.join(" ").toLowerCase();
      const relevant = event.status_operations.filter(operation => relevantText.includes(operation.effect_name.toLowerCase()));
      const byEffect = new Map();
      for (const operation of relevant) byEffect.set(operation.effect_id, [...(byEffect.get(operation.effect_id) || []), operation]);
      for (const [effectId, operations] of byEffect) {
        const applies = operations.filter(operation => operation.operation === "applies");
        const otherOperations = operations.filter(operation => operation.operation !== "applies" && operation.operation !== "mentions");
        const operation = applies[0];
        if (!operation) continue;
        if (otherOperations.length || applies.length > 1) {
          event.status_projection.push({ effect_id: effectId, effect_name: operation.effect_name, state: "ambiguous", explanation: "Conflicting or duplicate normalized operations; review exact wording." });
          continue;
        }
        if (!isTrackableStatus(operation)) {
          event.status_projection.push({ effect_id: effectId, effect_name: operation.effect_name, state: "instant_resolution", explanation: "Resolves during this interaction and is not added to the active-status state." });
          continue;
        }
        if (operation.chance_percent != null && operation.chance_percent < 100) {
          event.status_projection.push({ effect_id: effectId, effect_name: operation.effect_name, state: "probability_branch", chance_percent: operation.chance_percent, explanation: "Possible branch; not added to guaranteed state." });
          continue;
        }
        const resolved = event.target_groups.filter(groupItem => groupItem.resolution === "all_candidates" && groupItem.candidates.length);
        if (resolved.length !== 1) {
          event.status_projection.push({ effect_id: effectId, effect_name: operation.effect_name, state: "unresolved_target", explanation: "Application is not projected because its target group is ambiguous." });
          continue;
        }
        for (const target of resolved[0].candidates) applyStatus(state, target.dragon, operation, group.round);
        event.status_projection.push({ effect_id: effectId, effect_name: operation.effect_name, state: "guaranteed", targets: resolved[0].candidates.map(target => target.dragon), explanation: "Added to guaranteed state from a deterministic, uniquely resolved application." });
      }
    }
    group.status_after = Object.fromEntries([...state].filter(([, statuses]) => statuses.length).map(([target, statuses]) => [target, statuses.map(status => ({ ...status }))]));
  }
  return timeline;
}

export function scenarioToQuery(scenario) {
  const params = new URLSearchParams();
  for (const side of ["allies", "enemies"]) {
    scenario[side].forEach((slot, index) => {
      params.set(`${side[0]}${index + 1}`, slot.dragon);
      params.set(`${side[0]}${index + 1}s`, slot.stars);
      params.set(`${side[0]}${index + 1}l`, slot.level);
    });
  }
  params.set("troop", scenario.troop);
  return params.toString();
}

export function scenarioFromQuery(search, dragons) {
  const params = new URLSearchParams(search);
  const fallback = dragons.slice(0, 6).map(item => item.slug);
  const side = (name, offset) => LANES.map((lane, index) => ({
    lane,
    dragon: params.get(`${name[0]}${index + 1}`) || fallback[offset + index] || dragons[0]?.slug || "",
    stars: Number(params.get(`${name[0]}${index + 1}s`) || 10),
    level: Number(params.get(`${name[0]}${index + 1}l`) || 50),
  }));
  return { allies: side("allies", 0), enemies: side("enemies", 3), troop: params.get("troop") || "Shieldbearers" };
}
