import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { calculateDragonsArmyProgression, canonicalHabits, loadKnowledge, stableJson } from "../src/core.mjs";
import { ingestFormationForge, ingestScreenshotTranscription } from "../src/ingest.mjs";
import { diffSnapshots, formationForgeExport, plannerProfile } from "../src/outputs.mjs";
import { validateSnapshot } from "../src/validate.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FIXTURES = path.join(HERE, "fixtures");
const PROJECT = path.resolve(HERE, "..");
const knowledge = loadKnowledge();

function fixture(name) {
  return path.join(FIXTURES, name);
}

function siteSnapshot() {
  return ingestFormationForge({
    inputPath: fixture("formation-forge.json"),
    profileId: "fixture-player",
    observedAt: "2026-10-11",
    knowledge,
  });
}

test("Formation Forge import uses canonical identity and explicit unknowns", () => {
  const snapshot = siteSnapshot();
  const syrax = snapshot.profile.dragons.dragon_iconic_syrax;
  assert.equal(snapshot.schema_version, "dragonfire.player-roster.v1");
  assert.equal(snapshot.observed_at, "2026-10-11T00:00:00Z");
  assert.equal(Object.keys(snapshot.profile.dragons).length, 4);
  assert.equal(snapshot.roster_preflight.expected_visible_dragons, 3);
  assert.equal(snapshot.roster_preflight.observed_dragons, 3);
  assert.equal(snapshot.profile.dragons.dragon_iconic_arrax.owned, false);
  assert.equal(syrax.power, null);
  assert.equal(syrax.troop_capacity, null);
  const fifthHabit = canonicalHabits(knowledge.bySlug.get("dragon_iconic_syrax"))[4];
  assert.equal(syrax.habit_levels[fifthHabit.client_key], 0);
  assert.equal(snapshot.source.field_treatment.some(row => row.source_field === "notes"), true);
  assert.equal(snapshot.profile.stronghold.dragons_army.additional_troops_per_dragon, 0);
  assert.equal(snapshot.profile.stronghold.dragons_army.provenance, "assumed");
  assert.equal(validateSnapshot(snapshot, knowledge).valid, true);
});

test("Dragon's Army progression includes completed prerequisite skills", () => {
  assert.deepEqual(
    calculateDragonsArmyProgression({ skill: "III", level: 2, basis: "user_declaration" }),
    {
      current_skill: "III",
      current_skill_name: "Dragon's Army III",
      current_level: 2,
      troops_per_level: 200,
      completed_prior_skills_bonus_per_dragon: 750,
      current_skill_bonus_per_dragon: 400,
      additional_troops_per_dragon: 1150,
      additional_troops_per_three_dragon_formation: 3450,
      provenance: "observed",
      basis: "user_declaration",
    },
  );
  assert.equal(calculateDragonsArmyProgression({ skill: "I", level: 5 }).additional_troops_per_three_dragon_formation, 750);
  const maximum = calculateDragonsArmyProgression({ skill: "IV", level: 5 });
  assert.equal(maximum.current_skill_bonus_per_dragon, 1250);
  assert.equal(maximum.additional_troops_per_dragon, 3000);
});

test("validation rejects tampered Dragon's Army derived totals", () => {
  const snapshot = siteSnapshot();
  snapshot.profile.stronghold.dragons_army.additional_troops_per_dragon = 999;
  const validation = validateSnapshot(snapshot, knowledge);
  assert.equal(validation.valid, false);
  assert.equal(validation.errors.some(item => item.code === "dragons_army_calculation"), true);
});

test("screenshot transcription derives numeric Stars and preserves evidence", () => {
  const snapshot = ingestScreenshotTranscription({ inputPath: fixture("screenshot-transcription.json"), knowledge });
  const syrax = snapshot.profile.dragons.dragon_iconic_syrax;
  assert.equal(syrax.stars, 8);
  assert.deepEqual(syrax.displayed_stars, { color: "red", count: 3 });
  assert.equal(syrax.owned, true);
  assert.equal(snapshot.profile.stronghold.dragons_army.additional_troops_per_dragon, 1150);
  assert.equal(snapshot.profile.stronghold.dragons_army.basis, "screenshot_transcription");
  assert.equal(snapshot.evidence["dragon_iconic_syrax.stars"][0].provenance, "derived");
  assert.equal(validateSnapshot(snapshot, knowledge).valid, true);
});

test("conflicting screenshot observations fail closed", () => {
  const snapshot = ingestScreenshotTranscription({ inputPath: fixture("screenshot-conflict.json"), knowledge });
  assert.equal(snapshot.review.status, "blocked");
  assert.equal(snapshot.profile.dragons.dragon_iconic_syrax.level, null);
  assert.equal(validateSnapshot(snapshot, knowledge).valid, false);
  assert.throws(() => plannerProfile(snapshot, knowledge), /Planner profile is blocked/);
});

test("validation rejects Habit levels above the current Star unlock", () => {
  const snapshot = ingestScreenshotTranscription({ inputPath: fixture("screenshot-invalid-progression.json"), knowledge });
  const validation = validateSnapshot(snapshot, knowledge);
  assert.equal(validation.valid, false);
  assert.equal(validation.errors.some(item => item.code === "locked_habit_active"), true);
});

test("planner profile passes the deterministic planner validator", () => {
  const profile = plannerProfile(siteSnapshot(), knowledge);
  assert.equal(profile.version, 3);
  assert.equal(Object.values(profile.dragons).filter(entry => entry.owned).length, 3);
  assert.equal(profile.dragons.dragon_iconic_syrax.power, undefined);
  assert.equal(profile.stronghold.dragons_army.additional_troops_per_dragon, 0);
});

test("compatibility export joins canonical fixed fields without inventing unknown values", () => {
  const exported = formationForgeExport(siteSnapshot(), knowledge);
  const syrax = exported.find(item => item.name === "Syrax");
  assert.equal(syrax.rarity, "legendary");
  assert.equal(syrax.affinity.archers, "+");
  assert.equal(syrax.power, null);
  assert.equal(syrax.role, null);
  assert.equal(syrax.notes, "");
});

test("compatibility export can preserve required site classifications from an explicit template", () => {
  const template = JSON.parse(fs.readFileSync(fixture("formation-forge.json"), "utf8"));
  const exported = formationForgeExport(siteSnapshot(), knowledge, template);
  const syrax = exported.find(item => item.name === "Syrax");
  assert.equal(syrax.role, "healer");
  assert.equal(syrax.damageType, "tactical");
  assert.equal(syrax.notes, "");
});

test("snapshot diff reports progress and flags possible regressions", () => {
  const before = siteSnapshot();
  const after = structuredClone(before);
  after.observed_at = "2026-10-12T00:00:00Z";
  after.profile.dragons.dragon_iconic_syrax.stars = 9;
  after.profile.dragons.dragon_iconic_vhagar.level = 49;
  after.profile.stronghold.dragons_army = calculateDragonsArmyProgression({ skill: "III", level: 2, basis: "user_declaration" });
  const diff = diffSnapshots(before, after);
  assert.equal(diff.changes.some(item => item.field === "stars" && item.classification === "increase"), true);
  assert.equal(diff.regressions.some(item => item.dragon === "dragon_iconic_vhagar" && item.field === "level"), true);
  assert.equal(diff.changes.some(item => item.field === "stronghold.dragons_army.additional_troops_per_dragon" && item.after === 1150), true);
});

test("normalization is deterministic", () => {
  assert.equal(stableJson(siteSnapshot()), stableJson(siteSnapshot()));
});

test("CLI writes the archival record, review, raw source, and planner profile", () => {
  const output = fs.mkdtempSync(path.join(os.tmpdir(), "dragonfire-roster-test-"));
  try {
    const run = spawnSync(process.execPath, [
      path.join(PROJECT, "roster.mjs"),
      "ingest-site",
      "--input", fixture("formation-forge.json"),
      "--profile-id", "fixture-player",
      "--observed-at", "2026-10-11",
      "--output-dir", output,
    ], { encoding: "utf8" });
    assert.equal(run.status, 0, run.stderr);
    for (const relative of ["roster.json", "planner-profile.json", "ingestion-report.md", "source/formation-forge.json"]) assert.equal(fs.existsSync(path.join(output, relative)), true, relative);
    const roster = JSON.parse(fs.readFileSync(path.join(output, "roster.json"), "utf8"));
    assert.equal(roster.profile.stronghold.dragons_army.basis, "ingestion_default");
    const second = spawnSync(process.execPath, [
      path.join(PROJECT, "roster.mjs"),
      "ingest-site",
      "--input", fixture("formation-forge.json"),
      "--profile-id", "fixture-player",
      "--observed-at", "2026-10-11",
      "--output-dir", output,
    ], { encoding: "utf8" });
    assert.notEqual(second.status, 0);
    assert.match(second.stderr, /EEXIST|file already exists/i);
  } finally {
    const resolved = path.resolve(output);
    if (resolved.startsWith(path.resolve(os.tmpdir()))) fs.rmSync(resolved, { recursive: true, force: true });
  }
});

test("CLI records a declared Dragon's Army skill and level", () => {
  const output = fs.mkdtempSync(path.join(os.tmpdir(), "dragonfire-roster-army-test-"));
  try {
    const run = spawnSync(process.execPath, [
      path.join(PROJECT, "roster.mjs"),
      "ingest-site",
      "--input", fixture("formation-forge.json"),
      "--profile-id", "fixture-player",
      "--observed-at", "2026-10-11",
      "--output-dir", output,
      "--dragons-army-skill", "III",
      "--dragons-army-level", "2",
    ], { encoding: "utf8" });
    assert.equal(run.status, 0, run.stderr);
    const roster = JSON.parse(fs.readFileSync(path.join(output, "roster.json"), "utf8"));
    const planner = JSON.parse(fs.readFileSync(path.join(output, "planner-profile.json"), "utf8"));
    assert.equal(roster.profile.stronghold.dragons_army.additional_troops_per_dragon, 1150);
    assert.equal(planner.stronghold.dragons_army.additional_troops_per_three_dragon_formation, 3450);
  } finally {
    const resolved = path.resolve(output);
    if (resolved.startsWith(path.resolve(os.tmpdir()))) fs.rmSync(resolved, { recursive: true, force: true });
  }
});

test("overwrite regeneration removes a stale blocked-profile marker", () => {
  const output = fs.mkdtempSync(path.join(os.tmpdir(), "dragonfire-roster-overwrite-test-"));
  try {
    fs.writeFileSync(path.join(output, "planner-profile.blocked.txt"), "stale", "utf8");
    const run = spawnSync(process.execPath, [
      path.join(PROJECT, "roster.mjs"),
      "ingest-site",
      "--input", fixture("formation-forge.json"),
      "--profile-id", "fixture-player",
      "--observed-at", "2026-10-11",
      "--output-dir", output,
      "--overwrite",
    ], { encoding: "utf8" });
    assert.equal(run.status, 0, run.stderr);
    assert.equal(fs.existsSync(path.join(output, "planner-profile.json")), true);
    assert.equal(fs.existsSync(path.join(output, "planner-profile.blocked.txt")), false);
  } finally {
    const resolved = path.resolve(output);
    if (resolved.startsWith(path.resolve(os.tmpdir()))) fs.rmSync(resolved, { recursive: true, force: true });
  }
});

