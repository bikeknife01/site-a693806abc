import test from "node:test";
import assert from "node:assert/strict";
import { abilityEligible, applyStatus, buildTimeline, evaluateCondition, expireStatuses, isTrackableStatus, projectStatusTimeline, resolveTargeter, scheduleMatches, scenarioFromQuery, scenarioToQuery } from "../src/engine.mjs";

test("round schedules match explicit and recurring rounds", () => {
  assert.equal(scheduleMatches({ recurrence: "each_round", rounds: [] }, 7), true);
  assert.equal(scheduleMatches({ recurrence: null, rounds: [3, 6, 9] }, 6), true);
  assert.equal(scheduleMatches({ recurrence: null, rounds: [3, 6, 9] }, 7), false);
});

test("eligibility enforces star, level and Vanguard gates", () => {
  assert.equal(abilityEligible({ kind: "habit", unlock: { star_rank: 6 } }, { stars: 5, level: 50, lane: "Left Flank" }), false);
  assert.equal(abilityEligible({ kind: "vanguard", unlock: { level: 16 } }, { stars: 10, level: 16, lane: "Vanguard" }), true);
  assert.equal(abilityEligible({ kind: "vanguard", unlock: { level: 16 } }, { stars: 10, level: 16, lane: "Right Flank" }), false);
});

test("scenario links round trip", () => {
  const dragons = Array.from({ length: 6 }, (_, index) => ({ slug: `dragon-${index}` }));
  const scenario = scenarioFromQuery("", dragons);
  const restored = scenarioFromQuery(scenarioToQuery(scenario), dragons);
  assert.deepEqual(restored, scenario);
});

test("multiple matching clauses consolidate into one ability event", () => {
  const ability = { id: "ability:one", kind: "command", unlock: {}, exact_text: ["Each Round: first.", "Round 1: second."], normalized: { schedule_refs: ["s1", "s2"], target_hints: [] }, evidence: {} };
  const data = { dragons: [{ id: "dragon:one", slug: "one", name: "One", abilities: [ability] }], graph: { schedules: [{ id: "s1", exact_text: "Each Round", recurrence: "each_round", rounds: [] }, { id: "s2", exact_text: "Round 1", recurrence: null, rounds: [1] }] } };
  const slot = { lane: "Vanguard", dragon: "one", level: 50, stars: 10 };
  const timeline = buildTimeline(data, { allies: [slot], enemies: [], troop: "Archers" });
  assert.equal(timeline[1].items.length, 1);
  assert.equal(timeline[1].items[0].exact_text.length, 2);
});

test("adjacency targeting returns lane-aware enemy candidates", () => {
  const actor = { dragon: "ally-v", lane: "Vanguard", side: "Allied" };
  const slots = [actor, { dragon: "enemy-l", lane: "Left Flank", side: "Enemy" }, { dragon: "enemy-v", lane: "Vanguard", side: "Enemy" }, { dragon: "enemy-r", lane: "Right Flank", side: "Enemy" }];
  const result = resolveTargeter({ side: "enemy", scope: "adjacency", count: 1, exact_text: "within adjacency" }, actor, slots);
  assert.deepEqual(result.candidates.map(item => item.dragon), ["enemy-l", "enemy-v", "enemy-r"]);
  assert.equal(result.resolution, "selection_required");
});

test("same-lane targeting can resolve a sole candidate", () => {
  const actor = { dragon: "ally-l", lane: "Left Flank", side: "Allied" };
  const slots = [actor, { dragon: "enemy-l", lane: "Left Flank", side: "Enemy" }, { dragon: "enemy-v", lane: "Vanguard", side: "Enemy" }];
  const result = resolveTargeter({ side: "enemy", scope: "same_lane", count: 1, exact_text: "same lane" }, actor, slots);
  assert.equal(result.candidates[0].dragon, "enemy-l");
  assert.equal(result.resolution, "all_candidates");
});

test("star conditions are evaluated while stateful conditions remain unresolved", () => {
  assert.equal(evaluateCondition({ type: "star_rank", operator: "at_least", value: 6 }, { stars: 8 }).state, "met");
  assert.equal(evaluateCondition({ type: "status_present", status_id: "effect:slow" }, { stars: 8 }).state, "unresolved");
});

test("status instances stack to their cap and expire on the duration boundary", () => {
  const state = new Map();
  const operation = { effect_id: "effect:laceration", effect_name: "Laceration", duration_rounds: 2, max_stacks: 2 };
  applyStatus(state, "target", operation, 1);
  applyStatus(state, "target", operation, 1);
  applyStatus(state, "target", operation, 1);
  assert.equal(state.get("target")[0].stacks, 2);
  expireStatuses(state, 2);
  assert.equal(state.get("target").length, 1);
  expireStatuses(state, 3);
  assert.equal(state.get("target").length, 0);
});

test("chance applications branch without mutating guaranteed state", () => {
  const event = { dragon_slug: "actor", exact_text: ["50% chance to afflict Stun."], target_groups: [{ resolution: "all_candidates", candidates: [{ dragon: "target" }] }], status_operations: [{ operation: "applies", effect_id: "effect:stun", effect_name: "Stun", chance_percent: 50, duration_rounds: 2 }] };
  const timeline = projectStatusTimeline([{ round: 1, items: [event] }]);
  assert.equal(event.status_projection[0].state, "probability_branch");
  assert.deepEqual(timeline[0].status_after, {});
});

test("Recovery resolves as an interaction without entering active status state", () => {
  const event = { dragon_slug: "healer", exact_text: ["Apply Recovery to yourself."], target_groups: [{ resolution: "all_candidates", candidates: [{ dragon: "healer" }] }], status_operations: [{ operation: "applies", effect_id: "effect:recovery", effect_name: "Recovery", chance_percent: null, duration_rounds: null }] };
  const timeline = projectStatusTimeline([{ round: 1, items: [event] }]);
  assert.equal(isTrackableStatus(event.status_operations[0]), false);
  assert.equal(event.status_projection[0].state, "instant_resolution");
  assert.deepEqual(timeline[0].status_after, {});
});

test("guaranteed resolved applications persist and flag next-round suppression", () => {
  const applyEvent = { dragon_slug: "actor", exact_text: ["Afflict Stun."], target_groups: [{ resolution: "all_candidates", candidates: [{ dragon: "target" }] }], status_operations: [{ operation: "applies", effect_id: "effect:stun", effect_name: "Stun", chance_percent: null, duration_rounds: 2 }] };
  const targetEvent = { dragon_slug: "target", exact_text: [], target_groups: [], status_operations: [] };
  projectStatusTimeline([{ round: 1, items: [applyEvent] }, { round: 2, items: [targetEvent] }]);
  assert.equal(applyEvent.status_projection[0].state, "guaranteed");
  assert.equal(targetEvent.suppression[0].effect_name, "Stun");
});
