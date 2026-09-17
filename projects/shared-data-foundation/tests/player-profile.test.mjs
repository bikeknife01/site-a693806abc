import test from "node:test";
import assert from "node:assert/strict";
import { habitSummary, loadProfile, normalizeProfile, rosterEntries, saveProfile } from "../src/profile/player-profile.mjs";

const dragons = [
  { slug: "alpha", lifecycle: "live", abilities: [{ kind: "command", client_key: "command" }, { kind: "habit", client_key: "habit-a" }] },
  { slug: "beta", lifecycle: "live", abilities: [{ kind: "vanguard", client_key: "habit-b" }] },
  { slug: "future", lifecycle: "staged", abilities: [] },
];

test("a missing profile starts with transparent maxed-roster assumptions", () => {
  const storage = { getItem: () => null };
  const profile = loadProfile(dragons, storage);
  assert.equal(rosterEntries(profile).length, 2);
  assert.equal(profile.dragons.alpha.assumed, true);
  assert.equal(habitSummary(dragons[0], profile.dragons.alpha), "5");
  assert.equal(profile.dragons.future, undefined);
});

test("profile normalization clamps progression and retains per-habit levels", () => {
  const profile = normalizeProfile({ dragons: { alpha: { owned: true, level: 99, stars: 0, habit_levels: { "habit-a": 3 } } } }, dragons);
  assert.equal(profile.dragons.alpha.level, 50);
  assert.equal(profile.dragons.alpha.stars, 1);
  assert.equal(profile.dragons.alpha.habit_levels["habit-a"], 3);
});

test("saving removes starter assumptions and writes the shared storage key", () => {
  let saved;
  const storage = { setItem: (key, value) => { saved = { key, value }; } };
  const profile = saveProfile(normalizeProfile(null, dragons), dragons, storage);
  assert.equal(profile.dragons.alpha.assumed, false);
  assert.equal(saved.key, "dragonfire.playerProfile.v1");
  assert.equal(JSON.parse(saved.value).version, 1);
});
