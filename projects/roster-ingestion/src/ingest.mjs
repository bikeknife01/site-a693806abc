import fs from "node:fs";
import path from "node:path";
import {
  CONFIDENCE_VALUES,
  REVIEW_VALUES,
  TRANSCRIPTION_SCHEMA_VERSION,
  addEvidence,
  calculateDragonsArmyProgression,
  canonicalHabits,
  createSnapshotBase,
  derivedEvidence,
  displayStarsToRank,
  emptyProfileEntry,
  finalizeReview,
  issue,
  normalizeNullableNumber,
  observedEvidence,
  rankToDisplayedStars,
  readJson,
  resolveDragon,
  sha256File,
  sourceRecord,
  stableJson,
} from "./core.mjs";

const TROOP_FIELDS = {
  cavalry: "Cavalry",
  shieldbearers: "Shieldbearers",
  archers: "Archers",
  spearmen: "Spearmen",
  siege: "Siege",
};

const SITE_TREATMENT = [
  ["id", "Preserved only in raw source; canonical slug is used as identity."],
  ["active", "Mapped using the explicit active-semantics option and preserved as evidence."],
  ["name", "Resolved to a canonical repository slug."],
  ["reignLevel", "Imported as level."],
  ["starRank", "Imported as stars; displayed Stars remain unknown."],
  ["power", "Imported when greater than zero; zero becomes unknown."],
  ["troopCapacity", "Imported when greater than zero; zero becomes unknown."],
  ["habitLevels", "Mapped from displayed slot order to canonical Habit client keys; locked slots become 0."],
  ["rarity/breed/affinity", "Validated against canonical knowledge but not stored in the player profile."],
  ["role/damageType/tags/isNew", "Ignored as duplicated or source-specific classification."],
  ["notes", "Preserved only in the immutable raw source; never promoted to canonical evidence."],
  ["Dragon's Army", "Not present in the export; captured separately from a user declaration or explicitly assumed to be zero."],
].map(([source_field, treatment]) => ({ source_field, treatment }));

function normalizeObservedAt(value) {
  const raw = String(value || "");
  const expanded = /^\d{4}-\d{2}-\d{2}$/.test(raw) ? `${raw}T00:00:00Z` : raw;
  if (!expanded || Number.isNaN(Date.parse(expanded))) throw new Error("observed_at must be an ISO date or date-time.");
  return expanded;
}

function validateProfileId(value) {
  const result = String(value || "").toLowerCase();
  if (!/^[a-z0-9][a-z0-9_-]{0,63}$/.test(result)) throw new Error("profile_id must use 1-64 lowercase letters, digits, underscores, or hyphens.");
  return result;
}

function siteAffinityValue(dragon, troop) {
  if (dragon.troop_affinities?.positive?.includes(troop)) return "+";
  if (dragon.troop_affinities?.negative?.includes(troop)) return "-";
  return "0";
}

function validateFixedSiteFields(snapshot, raw, dragon) {
  if (raw.rarity != null && String(raw.rarity).toLowerCase() !== String(dragon.rarity_tier).toLowerCase()) {
    snapshot.review.warnings.push(issue("warning", "canonical_rarity_mismatch", `${dragon.name}: export rarity ${raw.rarity} differs from canonical ${dragon.rarity_tier}.`, { dragon: dragon.slug }));
  }
  if (raw.breed != null && String(raw.breed).toLowerCase() !== String(dragon.breed).toLowerCase()) {
    snapshot.review.warnings.push(issue("warning", "canonical_breed_mismatch", `${dragon.name}: export breed ${raw.breed} differs from canonical ${dragon.breed}.`, { dragon: dragon.slug }));
  }
  for (const [field, troop] of Object.entries(TROOP_FIELDS)) {
    if (raw.affinity?.[field] == null) continue;
    const actual = String(raw.affinity[field]);
    const expected = siteAffinityValue(dragon, troop);
    if (actual !== expected) snapshot.review.warnings.push(issue("warning", "canonical_affinity_mismatch", `${dragon.name}: export ${troop} affinity ${actual} differs from canonical ${expected}.`, { dragon: dragon.slug, troop }));
  }
}

function siteHabitLevels(snapshot, raw, dragon, sourceId) {
  const habits = canonicalHabits(dragon);
  const values = raw.habitLevels;
  const result = {};
  if (values == null) {
    for (const habit of habits) result[habit.client_key] = raw.active === false ? null : null;
    return result;
  }
  if (!Array.isArray(values)) {
    snapshot.review.errors.push(issue("error", "invalid_site_habits", `${dragon.name}: habitLevels must be an array.`, { dragon: dragon.slug }));
    return result;
  }
  if (values.length !== habits.length) snapshot.review.warnings.push(issue("warning", "site_habit_count", `${dragon.name}: export has ${values.length} Habit values; canonical data has ${habits.length}.`, { dragon: dragon.slug }));
  habits.forEach((habit, index) => {
    const rawLevel = values[index];
    let level = rawLevel == null ? null : Number(rawLevel);
    if (level != null && (!Number.isInteger(level) || level < 0 || level > 5)) {
      snapshot.review.errors.push(issue("error", "invalid_habit_level", `${dragon.name}: Habit ${habit.name} has invalid level ${rawLevel}.`, { dragon: dragon.slug, habit: habit.client_key }));
      level = null;
    }
    const unlock = Number(habit.unlock?.star_rank || 0);
    if (level != null && raw.starRank != null && Number(raw.starRank) < unlock && level !== 0) {
      snapshot.review.warnings.push(issue("warning", "locked_habit_normalized", `${dragon.name}: locked Habit ${habit.name} exported as ${level}; normalized to 0.`, { dragon: dragon.slug, habit: habit.client_key, unlock_stars: unlock }));
      level = 0;
    }
    result[habit.client_key] = level;
    addEvidence(snapshot, dragon.slug, `habit_levels.${habit.client_key}`, observedEvidence({ sourceId, field: `habit_levels.${habit.client_key}`, rawValue: rawLevel, normalizedValue: level }));
  });
  return result;
}

export function ingestFormationForge({ inputPath, profileId, observedAt, knowledge, activeMeans = "owned", completeness = "complete", dragonsArmy = null }) {
  if (!(["owned", "include"].includes(activeMeans))) throw new Error("activeMeans must be owned or include.");
  const raw = readJson(inputPath);
  if (!Array.isArray(raw) || !raw.length) throw new Error("Formation Forge input must be a non-empty JSON array.");
  const requiredFingerprint = ["name", "active", "starRank", "reignLevel", "habitLevels"];
  if (!raw.some(entry => requiredFingerprint.every(field => Object.hasOwn(entry, field)))) throw new Error("Input does not match the supported Formation Forge export shape.");
  const snapshot = createSnapshotBase({
    profileId: validateProfileId(profileId),
    observedAt: normalizeObservedAt(observedAt),
    sourceKind: "formation_forge_export",
    completeness,
    expectedVisibleDragons: completeness === "complete" ? (activeMeans === "owned" ? raw.filter(entry => Boolean(entry.active)).length : raw.length) : null,
    knowledge,
  });
  const sourceId = "formation-forge-export";
  snapshot.source.inputs.push(sourceRecord(inputPath, sourceId, "json_export"));
  snapshot.source.field_treatment = SITE_TREATMENT;
  snapshot.profile.stronghold.dragons_army = calculateDragonsArmyProgression(dragonsArmy || undefined);
  const seen = new Set();
  for (const [index, rawEntry] of raw.entries()) {
    const dragon = resolveDragon(knowledge, rawEntry.name);
    if (!dragon) {
      snapshot.review.errors.push(issue("error", "unknown_dragon", `Export entry ${index + 1} has unknown dragon ${rawEntry.name || "(missing)"}.`, { source_index: index }));
      continue;
    }
    if (seen.has(dragon.slug)) {
      snapshot.review.errors.push(issue("error", "duplicate_dragon", `Export contains duplicate dragon ${dragon.name}.`, { dragon: dragon.slug }));
      continue;
    }
    seen.add(dragon.slug);
    validateFixedSiteFields(snapshot, rawEntry, dragon);
    const entry = emptyProfileEntry();
    const active = Boolean(rawEntry.active);
    entry.owned = activeMeans === "owned" ? active : true;
    entry.include_in_search = active;
    entry.level = normalizeNullableNumber(rawEntry.reignLevel);
    entry.stars = normalizeNullableNumber(rawEntry.starRank);
    entry.power = normalizeNullableNumber(rawEntry.power, { zeroIsUnknown: true });
    entry.troop_capacity = normalizeNullableNumber(rawEntry.troopCapacity, { zeroIsUnknown: true });
    entry.habit_levels = siteHabitLevels(snapshot, rawEntry, dragon, sourceId);
    snapshot.profile.dragons[dragon.slug] = entry;
    for (const [field, rawValue, normalizedValue] of [
      ["owned", rawEntry.active, entry.owned],
      ["include_in_search", rawEntry.active, entry.include_in_search],
      ["level", rawEntry.reignLevel, entry.level],
      ["stars", rawEntry.starRank, entry.stars],
      ["power", rawEntry.power, entry.power],
      ["troop_capacity", rawEntry.troopCapacity, entry.troop_capacity],
    ]) addEvidence(snapshot, dragon.slug, field, observedEvidence({ sourceId, field, rawValue, normalizedValue, note: field === "owned" || field === "include_in_search" ? `Mapped using activeMeans=${activeMeans}.` : null }));
    if (rawEntry.power === 0) snapshot.review.warnings.push(issue("warning", "zero_power_unknown", `${dragon.name}: Power 0 was treated as unknown.`, { dragon: dragon.slug }));
    if (rawEntry.troopCapacity === 0) snapshot.review.warnings.push(issue("warning", "zero_capacity_unknown", `${dragon.name}: troop capacity 0 was treated as unknown.`, { dragon: dragon.slug }));
  }
  return finalizeReview(snapshot);
}

function normalizeObservedField(snapshot, dragon, field, observed, sourceId) {
  if (!observed || typeof observed !== "object" || !("value" in observed)) {
    snapshot.review.errors.push(issue("error", "invalid_observed_field", `${dragon.name}: ${field} must contain value, confidence, and review_status.`, { dragon: dragon.slug, field }));
    return null;
  }
  const confidence = String(observed.confidence || "");
  const reviewStatus = String(observed.review_status || "");
  if (!CONFIDENCE_VALUES.has(confidence) || !REVIEW_VALUES.has(reviewStatus)) {
    snapshot.review.errors.push(issue("error", "invalid_evidence_state", `${dragon.name}: ${field} has invalid confidence or review status.`, { dragon: dragon.slug, field }));
  }
  if (["machine_read", "unreadable", "conflicting"].includes(reviewStatus)) {
    snapshot.review.warnings.push(issue("warning", "field_needs_review", `${dragon.name}: ${field} is ${reviewStatus}.`, { dragon: dragon.slug, field, source_id: sourceId }));
  }
  let value = observed.value;
  if (["level", "stars"].includes(field)) value = normalizeNullableNumber(value);
  if (["power", "troop_capacity"].includes(field)) value = normalizeNullableNumber(value, { zeroIsUnknown: true });
  if (["owned", "include_in_search"].includes(field) && value != null && typeof value !== "boolean") {
    snapshot.review.errors.push(issue("error", "invalid_boolean", `${dragon.name}: ${field} must be a boolean or null.`, { dragon: dragon.slug, field, source_id: sourceId }));
    value = null;
  }
  if (field === "displayed_stars" && value != null) value = { color: String(value.color || "").toLowerCase(), count: Number(value.count) };
  if (reviewStatus === "unreadable" || reviewStatus === "conflicting" || (reviewStatus === "machine_read" && !["high", "confirmed"].includes(confidence))) value = null;
  if (reviewStatus === "conflicting") snapshot.review.conflicts.push(issue("error", "declared_field_conflict", `${dragon.name}: ${field} was explicitly marked conflicting.`, { dragon: dragon.slug, field, source_id: sourceId, recommendation_critical: true }));
  addEvidence(snapshot, dragon.slug, field, observedEvidence({
    sourceId,
    field,
    rawValue: observed.value,
    normalizedValue: value,
    confidence,
    reviewStatus,
    crop: observed.crop || null,
    note: observed.note || null,
  }));
  return value;
}

function normalizeTranscribedHabits(snapshot, dragon, observed, sourceId) {
  const habits = canonicalHabits(dragon);
  const raw = observed.value;
  if (!CONFIDENCE_VALUES.has(String(observed.confidence || "")) || !REVIEW_VALUES.has(String(observed.review_status || ""))) {
    snapshot.review.errors.push(issue("error", "invalid_evidence_state", `${dragon.name}: habit_levels has invalid confidence or review status.`, { dragon: dragon.slug, field: "habit_levels" }));
  }
  if (observed.review_status === "unreadable" || observed.review_status === "conflicting" || (observed.review_status === "machine_read" && !["high", "confirmed"].includes(observed.confidence))) {
    if (observed.review_status === "conflicting") snapshot.review.conflicts.push(issue("error", "declared_field_conflict", `${dragon.name}: habit_levels was explicitly marked conflicting.`, { dragon: dragon.slug, field: "habit_levels", source_id: sourceId, recommendation_critical: true }));
    for (const habit of habits) addEvidence(snapshot, dragon.slug, `habit_levels.${habit.client_key}`, observedEvidence({ sourceId, field: `habit_levels.${habit.client_key}`, rawValue: raw, normalizedValue: null, confidence: observed.confidence, reviewStatus: observed.review_status, crop: observed.crop || null, note: observed.note || null }));
    return Object.fromEntries(canonicalHabits(dragon).map(habit => [habit.client_key, null]));
  }
  const keyed = {};
  if (Array.isArray(raw)) habits.forEach((habit, index) => { keyed[habit.client_key] = raw[index] ?? null; });
  else if (raw && typeof raw === "object") Object.assign(keyed, raw);
  else {
    snapshot.review.errors.push(issue("error", "invalid_transcribed_habits", `${dragon.name}: habit_levels must be an array or keyed object.`, { dragon: dragon.slug }));
    return {};
  }
  const known = new Set(habits.map(habit => habit.client_key));
  for (const key of Object.keys(keyed)) {
    if (!known.has(key)) snapshot.review.errors.push(issue("error", "unknown_habit_key", `${dragon.name}: unknown Habit key ${key}.`, { dragon: dragon.slug, habit: key }));
    const rawLevel = keyed[key];
    const level = rawLevel == null ? null : Number(rawLevel);
    keyed[key] = level;
    addEvidence(snapshot, dragon.slug, `habit_levels.${key}`, observedEvidence({ sourceId, field: `habit_levels.${key}`, rawValue: rawLevel, normalizedValue: level, confidence: observed.confidence, reviewStatus: observed.review_status, crop: observed.crop || null, note: observed.note || null }));
  }
  return keyed;
}

function setNestedEntry(entry, field, value) {
  if (field.startsWith("habit_levels.")) entry.habit_levels[field.slice("habit_levels.".length)] = value;
  else entry[field] = value;
}

export function ingestScreenshotTranscription({ inputPath, knowledge, dragonsArmy = null }) {
  const input = readJson(inputPath);
  if (input?.schema_version !== TRANSCRIPTION_SCHEMA_VERSION) throw new Error(`Screenshot transcription must use ${TRANSCRIPTION_SCHEMA_VERSION}.`);
  if (!Array.isArray(input.sources) || !Array.isArray(input.observations)) throw new Error("Screenshot transcription requires sources and observations arrays.");
  const snapshot = createSnapshotBase({
    profileId: validateProfileId(input.profile_id),
    observedAt: normalizeObservedAt(input.observed_at),
    sourceKind: "screenshot_transcription",
    completeness: input.roster_preflight?.completeness || "declared_subset",
    expectedVisibleDragons: input.roster_preflight?.expected_visible_dragons ?? null,
    knowledge,
  });
  snapshot.source.field_treatment = [
    { source_field: "visible player progression", treatment: "Imported as observed player data with per-field evidence." },
    { source_field: "displayed_stars", treatment: "Preserved verbatim and converted to numeric Stars as a derived value." },
    { source_field: "dragon name", treatment: "Resolved to a canonical slug; fixed dragon facts are joined at consumption time." },
    { source_field: "unreadable or absent values", treatment: "Stored as null; never guessed from canonical knowledge." },
    { source_field: "Dragon's Army", treatment: "Captured once at account level from the transcription or user declaration; otherwise explicitly assumed to be zero." },
  ];
  const transcribedArmy = input.stronghold?.dragons_army;
  snapshot.profile.stronghold.dragons_army = calculateDragonsArmyProgression(
    dragonsArmy || (transcribedArmy ? { skill: transcribedArmy.current_skill, level: transcribedArmy.current_level, basis: "screenshot_transcription" } : undefined),
  );
  const inputDir = path.dirname(path.resolve(inputPath));
  const sources = new Map();
  for (const source of input.sources) {
    if (!source.id || sources.has(source.id)) {
      snapshot.review.errors.push(issue("error", "duplicate_source_id", `Screenshot source ID is missing or duplicated: ${source.id || "(missing)"}.`));
      continue;
    }
    const resolved = path.resolve(inputDir, source.path);
    if (!fs.existsSync(resolved)) {
      snapshot.review.errors.push(issue("error", "missing_source_file", `Screenshot source does not exist: ${source.path}.`, { source_id: source.id }));
      continue;
    }
    const record = sourceRecord(resolved, source.id, source.kind || "other");
    if (source.sha256 && source.sha256 !== record.sha256) snapshot.review.errors.push(issue("error", "source_hash_mismatch", `Screenshot hash does not match for ${source.id}.`, { source_id: source.id }));
    snapshot.source.inputs.push(record);
    sources.set(source.id, record);
  }
  const candidates = new Map();
  for (const [index, observation] of input.observations.entries()) {
    const dragon = resolveDragon(knowledge, observation.dragon);
    if (!dragon) {
      snapshot.review.errors.push(issue("error", "unknown_dragon", `Observation ${index + 1} has unknown dragon ${observation.dragon || "(missing)"}.`, { source_index: index }));
      continue;
    }
    if (!sources.has(observation.source_id)) {
      snapshot.review.errors.push(issue("error", "unknown_source_reference", `${dragon.name}: unknown screenshot source ${observation.source_id}.`, { dragon: dragon.slug }));
      continue;
    }
    if (!candidates.has(dragon.slug)) candidates.set(dragon.slug, new Map());
    const fields = candidates.get(dragon.slug);
    const incoming = observation.fields || {};
    for (const [field, observed] of Object.entries(incoming)) {
      if (field === "habit_levels") {
        const habits = normalizeTranscribedHabits(snapshot, dragon, observed, observation.source_id);
        for (const [key, value] of Object.entries(habits)) {
          const flat = `habit_levels.${key}`;
          if (!fields.has(flat)) fields.set(flat, []);
          fields.get(flat).push({ value, source_id: observation.source_id });
        }
        continue;
      }
      if (!(["owned", "include_in_search", "level", "stars", "displayed_stars", "power", "troop_capacity"].includes(field))) {
        snapshot.review.warnings.push(issue("warning", "ignored_transcription_field", `${dragon.name}: ignored unsupported field ${field}.`, { dragon: dragon.slug, field }));
        continue;
      }
      const value = normalizeObservedField(snapshot, dragon, field, observed, observation.source_id);
      if (!fields.has(field)) fields.set(field, []);
      fields.get(field).push({ value, source_id: observation.source_id });
    }
  }
  for (const [slug, fields] of candidates) {
    const dragon = knowledge.bySlug.get(slug.toLowerCase());
    const entry = emptyProfileEntry();
    for (const [field, values] of fields) {
      const distinct = new Map(values.map(item => [stableJson(item.value), item.value]));
      if (distinct.size > 1) {
        snapshot.review.conflicts.push(issue("error", "observation_conflict", `${dragon.name}: conflicting observations for ${field}.`, { dragon: slug, field, values, recommendation_critical: true }));
        setNestedEntry(entry, field, null);
      } else {
        setNestedEntry(entry, field, distinct.values().next().value);
        if (values.length > 1) snapshot.review.warnings.push(issue("warning", "duplicate_coverage", `${dragon.name}: ${field} appears in ${values.length} screenshots with the same value.`, { dragon: slug, field }));
      }
    }
    if (entry.owned == null && !fields.has("owned")) {
      entry.owned = true;
      addEvidence(snapshot, slug, "owned", derivedEvidence({ sourceId: valuesSource(fields), field: "owned", rawValue: dragon.name, normalizedValue: true, note: "Derived from the dragon being visibly present in the submitted roster evidence." }));
    }
    if (entry.include_in_search == null && !fields.has("include_in_search")) entry.include_in_search = entry.owned;
    if (entry.displayed_stars != null) {
      const derivedRank = displayStarsToRank(entry.displayed_stars);
      if (derivedRank == null) snapshot.review.errors.push(issue("error", "invalid_displayed_stars", `${dragon.name}: displayed Stars are invalid.`, { dragon: slug }));
      else if (entry.stars == null) {
        entry.stars = derivedRank;
        addEvidence(snapshot, slug, "stars", derivedEvidence({ sourceId: valuesSource(fields, "displayed_stars"), field: "stars", rawValue: entry.displayed_stars, normalizedValue: derivedRank, note: "Red Stars map to ranks 6-10; yellow Stars map to ranks 1-5." }));
      } else if (entry.stars !== derivedRank) snapshot.review.errors.push(issue("error", "displayed_star_mismatch", `${dragon.name}: displayed Stars resolve to ${derivedRank}, not ${entry.stars}.`, { dragon: slug }));
    }
    for (const habit of canonicalHabits(dragon)) {
      if (!(habit.client_key in entry.habit_levels)) entry.habit_levels[habit.client_key] = null;
    }
    snapshot.profile.dragons[slug] = entry;
  }
  return finalizeReview(snapshot);
}

function valuesSource(fields, field = null) {
  const selected = field ? fields.get(field) : [...fields.values()][0];
  return selected?.[0]?.source_id || "transcription";
}

