import fs from "node:fs";
import path from "node:path";
import { validatePlannerInput } from "../../recommendation-planner/recommend.mjs";
import {
  canonicalHabits,
  rankToDisplayedStars,
  readJson,
  stableJson,
  writeJsonExclusive,
  writeTextExclusive,
} from "./core.mjs";
import { validateSnapshot } from "./validate.mjs";

export function plannerProfile(snapshot, knowledge, { requireReady = true } = {}) {
  const validation = validateSnapshot(snapshot, knowledge);
  const blocking = [
    ...validation.errors,
    ...(snapshot.review?.errors || []),
    ...(snapshot.review?.conflicts || []).filter(item => item.recommendation_critical !== false),
  ];
  const dragons = {};
  for (const [slug, entry] of Object.entries(snapshot.profile.dragons)) {
    const selected = entry.owned === true && entry.include_in_search !== false;
    if (selected && (entry.level == null || entry.stars == null)) blocking.push({ code: "missing_progression", message: `${slug}: selected dragons require known level and Stars.` });
    const habitLevels = Object.fromEntries(Object.entries(entry.habit_levels || {}).filter(([, value]) => value != null));
    dragons[slug] = {
      owned: selected,
      level: entry.level,
      stars: entry.stars,
      habit_levels: habitLevels,
      assumed: Boolean(entry.assumed),
    };
    if (entry.power != null) dragons[slug].power = entry.power;
    if (entry.displayed_stars != null) dragons[slug].displayed_stars = entry.displayed_stars;
  }
  if (requireReady && blocking.length) throw new Error(`Planner profile is blocked: ${blocking.map(item => item.message).join("; ")}`);
  const profile = { version: snapshot.profile.version, updated_at: snapshot.observed_at, stronghold: snapshot.profile.stronghold, dragons };
  if (requireReady) {
    validatePlannerInput(knowledge.data, {
      objective: "pvp",
      profile,
      roster_preflight: {
        completeness: snapshot.roster_preflight.completeness,
        expected_visible_dragons: snapshot.roster_preflight.expected_visible_dragons,
      },
    });
  }
  return profile;
}

export function renderReviewReport(snapshot, validation = { errors: [], warnings: [] }) {
  const counts = Object.values(snapshot.profile.dragons).reduce((result, entry) => {
    result.total += 1;
    if (entry.owned === true) result.owned += 1;
    if (entry.include_in_search === true) result.selected += 1;
    if (entry.power == null) result.unknownPower += 1;
    return result;
  }, { total: 0, owned: 0, selected: 0, unknownPower: 0 });
  const errors = [...(snapshot.review.errors || []), ...(validation.errors || [])];
  const warnings = [...(snapshot.review.warnings || []), ...(validation.warnings || [])];
  const lines = [
    `# Roster ingestion review — ${snapshot.profile_id}`,
    "",
    `- Observed at: ${snapshot.observed_at}`,
    `- Source path: ${snapshot.source.kind}`,
    `- Review status: **${snapshot.review.status}**`,
    `- Roster coverage: ${snapshot.roster_preflight.completeness}; ${counts.total} normalized dragons`,
    `- Owned: ${counts.owned}; included in search: ${counts.selected}`,
    `- Unknown Power: ${counts.unknownPower}`,
    `- Dragon's Army: ${snapshot.profile.stronghold.dragons_army.current_skill_name || "none"} level ${snapshot.profile.stronghold.dragons_army.current_level}; +${snapshot.profile.stronghold.dragons_army.additional_troops_per_dragon} troops per dragon (+${snapshot.profile.stronghold.dragons_army.additional_troops_per_three_dragon_formation} per three-dragon formation); ${snapshot.profile.stronghold.dragons_army.basis}`,
    `- Canonical dataset: ${snapshot.knowledge.dataset_id} schema ${snapshot.knowledge.dataset_schema_version}`,
    `- Canonical SHA-256: \`${snapshot.knowledge.dataset_sha256}\``,
    "",
    "## Validation",
    "",
    `Errors: ${errors.length}; conflicts: ${snapshot.review.conflicts.length}; warnings: ${warnings.length}.`,
  ];
  appendIssues(lines, "Errors", errors);
  appendIssues(lines, "Conflicts", snapshot.review.conflicts || []);
  appendIssues(lines, "Warnings", warnings);
  lines.push("", "## Source field treatment", "", "| Source field | Treatment |", "|---|---|");
  for (const row of snapshot.source.field_treatment || []) lines.push(`| ${escapeCell(row.source_field)} | ${escapeCell(row.treatment)} |`);
  lines.push("", "## Coverage", "", "| Dragon slug | Owned | Search | Level | Stars | Power | Habit coverage |", "|---|---:|---:|---:|---:|---:|---|");
  for (const [slug, entry] of Object.entries(snapshot.profile.dragons).sort(([a], [b]) => a.localeCompare(b))) {
    const habits = Object.values(entry.habit_levels || {});
    lines.push(`| ${slug} | ${display(entry.owned)} | ${display(entry.include_in_search)} | ${display(entry.level)} | ${display(entry.stars)} | ${display(entry.power)} | ${habits.filter(value => value != null).length}/${habits.length} known |`);
  }
  return `${lines.join("\n")}\n`;
}

function appendIssues(lines, heading, issues) {
  lines.push("", `### ${heading}`, "");
  if (!issues.length) lines.push("None.");
  else for (const item of issues) lines.push(`- \`${item.code}\`: ${item.message}`);
}

function display(value) {
  if (value == null) return "Unknown";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

function escapeCell(value) {
  return String(value).replace(/\|/g, "\\|").replace(/\r?\n/g, " ");
}

export function formationForgeExport(snapshot, knowledge, template = []) {
  const templateByName = new Map((Array.isArray(template) ? template : []).map(item => [String(item.name || "").toLowerCase(), item]));
  return Object.entries(snapshot.profile.dragons).sort(([a], [b]) => a.localeCompare(b)).map(([slug, entry], index) => {
    const dragon = knowledge.bySlug.get(slug.toLowerCase());
    const source = templateByName.get(dragon.name.toLowerCase()) || {};
    const habits = canonicalHabits(dragon);
    const affinity = {};
    for (const [field, troop] of Object.entries({ cavalry: "Cavalry", shieldbearers: "Shieldbearers", archers: "Archers", spearmen: "Spearmen", siege: "Siege" })) {
      affinity[field] = dragon.troop_affinities?.positive?.includes(troop) ? "+" : dragon.troop_affinities?.negative?.includes(troop) ? "-" : 0;
    }
    return {
      id: source.id || `dragonfire-${index}-${slug}`,
      active: entry.include_in_search ?? entry.owned ?? false,
      name: dragon.name,
      rarity: String(dragon.rarity_tier || "").toLowerCase(),
      breed: String(dragon.breed || "").toLowerCase(),
      role: source.role ?? null,
      damageType: source.damageType ?? null,
      power: entry.power,
      starRank: entry.stars,
      reignLevel: entry.level,
      troopCapacity: entry.troop_capacity,
      affinity,
      tags: Array.isArray(source.tags) ? source.tags : [],
      habitLevels: habits.map(habit => entry.habit_levels?.[habit.client_key] ?? null),
      notes: "",
    };
  });
}

export function diffSnapshots(before, after) {
  const changes = [];
  const regressions = [];
  const slugs = [...new Set([...Object.keys(before.profile.dragons), ...Object.keys(after.profile.dragons)])].sort();
  const oldArmy = before.profile.stronghold?.dragons_army;
  const newArmy = after.profile.stronghold?.dragons_army;
  for (const field of ["current_skill", "current_level", "additional_troops_per_dragon"]) {
    compareField(changes, regressions, "profile", `stronghold.dragons_army.${field}`, oldArmy?.[field] ?? null, newArmy?.[field] ?? null);
  }
  for (const slug of slugs) {
    const oldEntry = before.profile.dragons[slug];
    const newEntry = after.profile.dragons[slug];
    if (!oldEntry) {
      changes.push({ dragon: slug, field: "roster", before: null, after: "added", classification: "added" });
      continue;
    }
    if (!newEntry) {
      changes.push({ dragon: slug, field: "roster", before: "present", after: null, classification: "removed_or_unobserved" });
      continue;
    }
    for (const field of ["owned", "include_in_search", "level", "stars", "power", "troop_capacity"]) compareField(changes, regressions, slug, field, oldEntry[field], newEntry[field]);
    const habits = [...new Set([...Object.keys(oldEntry.habit_levels || {}), ...Object.keys(newEntry.habit_levels || {})])].sort();
    for (const habit of habits) compareField(changes, regressions, slug, `habit_levels.${habit}`, oldEntry.habit_levels?.[habit] ?? null, newEntry.habit_levels?.[habit] ?? null);
  }
  return {
    schema_version: "dragonfire.player-roster-diff.v1",
    profile_id: after.profile_id,
    before_observed_at: before.observed_at,
    after_observed_at: after.observed_at,
    seasonal_context_required: true,
    changes,
    regressions,
  };
}

function compareField(changes, regressions, dragon, field, before, after) {
  if (JSON.stringify(before) === JSON.stringify(after)) return;
  let classification = "changed";
  if (before == null && after != null) classification = "newly_observed";
  else if (before != null && after == null) classification = "became_unknown";
  else if (typeof before === "number" && typeof after === "number") classification = after > before ? "increase" : "decrease";
  const change = { dragon, field, before, after, classification };
  changes.push(change);
  if (classification === "decrease" && (["level", "stars", "power", "troop_capacity"].some(name => field === name || field.startsWith("habit_levels.")) || field.startsWith("stronghold.dragons_army."))) regressions.push({ ...change, warning: "Possible seasonal reset, stale evidence, or transcription error; review before interpreting." });
}

export function renderDiffReport(diff) {
  const lines = [
    `# Roster delta — ${diff.profile_id}`,
    "",
    `From ${diff.before_observed_at} to ${diff.after_observed_at}.`,
    "",
    "Progression decreases are review flags, not automatically errors; seasonal context may explain them.",
    "",
    "| Dragon | Field | Before | After | Classification |",
    "|---|---|---:|---:|---|",
  ];
  if (!diff.changes.length) lines.push("| — | — | — | — | No changes | ");
  else for (const row of diff.changes) lines.push(`| ${row.dragon} | ${row.field} | ${display(row.before)} | ${display(row.after)} | ${row.classification} |`);
  appendIssues(lines, "Regression review", diff.regressions.map(row => ({ code: row.field, message: `${row.dragon}: ${display(row.before)} → ${display(row.after)}. ${row.warning}` })));
  return `${lines.join("\n")}\n`;
}

export function writeIngestionBundle({ snapshot, knowledge, outputDir, rawInputPath, overwrite = false }) {
  const validation = validateSnapshot(snapshot, knowledge);
  if (validation.errors.length) snapshot.review.status = "blocked";
  const resolved = path.resolve(outputDir);
  fs.mkdirSync(resolved, { recursive: true });
  writeJsonExclusive(path.join(resolved, "roster.json"), snapshot, { overwrite });
  writeTextExclusive(path.join(resolved, "ingestion-report.md"), renderReviewReport(snapshot, validation), { overwrite });
  const rawDir = path.join(resolved, "source");
  fs.mkdirSync(rawDir, { recursive: true });
  const rawTarget = path.join(rawDir, path.basename(rawInputPath));
  fs.copyFileSync(path.resolve(rawInputPath), rawTarget, overwrite ? 0 : fs.constants.COPYFILE_EXCL);
  let planner = null;
  try {
    planner = plannerProfile(snapshot, knowledge);
    writeJsonExclusive(path.join(resolved, "planner-profile.json"), planner, { overwrite });
    const staleBlocked = path.join(resolved, "planner-profile.blocked.txt");
    if (overwrite && fs.existsSync(staleBlocked)) fs.rmSync(staleBlocked);
  } catch (error) {
    writeTextExclusive(path.join(resolved, "planner-profile.blocked.txt"), error.message, { overwrite });
    const stalePlanner = path.join(resolved, "planner-profile.json");
    if (overwrite && fs.existsSync(stalePlanner)) fs.rmSync(stalePlanner);
  }
  return { validation, planner, output_dir: resolved };
}

export function readSnapshot(filePath) {
  return readJson(filePath);
}

