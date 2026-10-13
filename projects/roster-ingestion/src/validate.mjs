import {
  CONFIDENCE_VALUES,
  PROVENANCE_VALUES,
  REVIEW_VALUES,
  ROSTER_SCHEMA_VERSION,
  calculateDragonsArmyProgression,
  canonicalHabits,
  displayStarsToRank,
  issue,
} from "./core.mjs";

export function validateSnapshot(snapshot, knowledge) {
  const errors = [];
  const warnings = [];
  if (!snapshot || typeof snapshot !== "object" || Array.isArray(snapshot)) return { valid: false, errors: [issue("error", "invalid_root", "Roster snapshot must be an object.")], warnings };
  if (snapshot.schema_version !== ROSTER_SCHEMA_VERSION) errors.push(issue("error", "schema_version", `Expected ${ROSTER_SCHEMA_VERSION}.`));
  if (!/^[a-z0-9][a-z0-9_-]{0,63}$/.test(snapshot.profile_id || "")) errors.push(issue("error", "profile_id", "profile_id is invalid."));
  if (!snapshot.observed_at || Number.isNaN(Date.parse(snapshot.observed_at))) errors.push(issue("error", "observed_at", "observed_at must be an ISO date-time."));
  const sources = new Set((snapshot.source?.inputs || []).map(item => item.id));
  if (sources.size !== (snapshot.source?.inputs || []).length) errors.push(issue("error", "duplicate_source", "Source IDs must be unique."));
  const entries = snapshot.profile?.dragons;
  validateDragonsArmy(snapshot.profile?.stronghold?.dragons_army, errors);
  if (!entries || typeof entries !== "object" || Array.isArray(entries)) errors.push(issue("error", "profile_dragons", "profile.dragons must be an object."));
  else for (const [slug, entry] of Object.entries(entries)) validateEntry(slug, entry, knowledge, errors, warnings);
  for (const [key, records] of Object.entries(snapshot.evidence || {})) {
    if (!Array.isArray(records) || !records.length) errors.push(issue("error", "empty_evidence", `${key}: evidence must be a non-empty array.`));
    for (const record of records || []) {
      if (!sources.has(record.source_id) && record.source_id !== "transcription") errors.push(issue("error", "evidence_source", `${key}: unknown evidence source ${record.source_id}.`));
      if (!PROVENANCE_VALUES.has(record.provenance)) errors.push(issue("error", "evidence_provenance", `${key}: invalid provenance ${record.provenance}.`));
      if (!CONFIDENCE_VALUES.has(record.confidence)) errors.push(issue("error", "evidence_confidence", `${key}: invalid confidence ${record.confidence}.`));
      if (!REVIEW_VALUES.has(record.review_status)) errors.push(issue("error", "evidence_review", `${key}: invalid review status ${record.review_status}.`));
    }
  }
  const observed = Object.values(entries || {}).filter(entry => entry.owned === true).length;
  if (snapshot.roster_preflight?.observed_dragons !== observed) errors.push(issue("error", "observed_count", `roster_preflight.observed_dragons must equal ${observed}.`));
  const expected = snapshot.roster_preflight?.expected_visible_dragons;
  if (expected != null && expected !== observed) {
    const target = snapshot.roster_preflight?.completeness === "complete" ? errors : warnings;
    target.push(issue(target === errors ? "error" : "warning", "expected_count", `Expected ${expected} visible dragons but normalized ${observed}.`));
  }
  if (snapshot.knowledge?.dataset_sha256 !== knowledge.metadata.dataset_sha256) warnings.push(issue("warning", "knowledge_changed", "Snapshot was generated against a different canonical dataset hash."));
  if (snapshot.knowledge?.game_mechanics_sha256 !== knowledge.metadata.game_mechanics_sha256) warnings.push(issue("warning", "mechanics_changed", "Snapshot was generated against different shared game-mechanics rules."));
  for (const recorded of snapshot.review?.errors || []) errors.push(issue("error", `recorded_${recorded.code}`, recorded.message));
  for (const recorded of (snapshot.review?.conflicts || []).filter(item => item.recommendation_critical !== false)) errors.push(issue("error", `recorded_${recorded.code}`, recorded.message));
  return { valid: errors.length === 0, errors, warnings };
}

function validateDragonsArmy(value, errors) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    errors.push(issue("error", "dragons_army", "profile.stronghold.dragons_army is required."));
    return;
  }
  let expected;
  try {
    expected = calculateDragonsArmyProgression({ skill: value.current_skill, level: value.current_level, basis: value.basis });
  } catch (error) {
    errors.push(issue("error", "dragons_army", error.message));
    return;
  }
  for (const [field, expectedValue] of Object.entries(expected)) {
    if (value[field] !== expectedValue) errors.push(issue("error", "dragons_army_calculation", `profile.stronghold.dragons_army.${field} must be ${JSON.stringify(expectedValue)}.`));
  }
}

function validateEntry(slug, entry, knowledge, errors, warnings) {
  const dragon = knowledge.bySlug.get(slug.toLowerCase());
  if (!dragon) {
    errors.push(issue("error", "unknown_slug", `Unknown canonical dragon slug ${slug}.`, { dragon: slug }));
    return;
  }
  for (const field of ["owned", "include_in_search"]) if (!(entry[field] == null || typeof entry[field] === "boolean")) errors.push(issue("error", `invalid_${field}`, `${dragon.name}: ${field} must be boolean or null.`, { dragon: slug }));
  integerRange(entry.level, 1, 50, `${dragon.name}: level`, errors, slug);
  integerRange(entry.stars, 1, 10, `${dragon.name}: stars`, errors, slug);
  positiveNullable(entry.power, `${dragon.name}: power`, errors, slug);
  positiveNullable(entry.troop_capacity, `${dragon.name}: troop_capacity`, errors, slug);
  if (entry.displayed_stars != null) {
    const rank = displayStarsToRank(entry.displayed_stars);
    if (rank == null) errors.push(issue("error", "invalid_displayed_stars", `${dragon.name}: displayed_stars is invalid.`, { dragon: slug }));
    else if (entry.stars != null && rank !== entry.stars) errors.push(issue("error", "displayed_star_mismatch", `${dragon.name}: displayed Stars resolve to ${rank}, not ${entry.stars}.`, { dragon: slug }));
  }
  const habits = new Map(canonicalHabits(dragon).map(habit => [habit.client_key, habit]));
  for (const [key, value] of Object.entries(entry.habit_levels || {})) {
    const habit = habits.get(key);
    if (!habit) {
      errors.push(issue("error", "unknown_habit_key", `${dragon.name}: unknown Habit key ${key}.`, { dragon: slug }));
      continue;
    }
    integerRange(value, 0, 5, `${dragon.name}: ${habit.name}`, errors, slug, true);
    const unlock = Number(habit.unlock?.star_rank || 0);
    if (entry.stars != null && entry.stars < unlock && value != null && value !== 0) errors.push(issue("error", "locked_habit_active", `${dragon.name}: ${habit.name} requires ${unlock} Stars but has level ${value}.`, { dragon: slug, habit: key }));
    if (entry.stars != null && entry.stars >= unlock && value === 0) warnings.push(issue("warning", "unlocked_habit_zero", `${dragon.name}: ${habit.name} is unlocked but recorded as unavailable (0).`, { dragon: slug, habit: key }));
  }
}

function integerRange(value, min, max, label, errors, slug, nullable = true) {
  if (value == null && nullable) return;
  if (!Number.isInteger(value) || value < min || value > max) errors.push(issue("error", "range", `${label} must be an integer from ${min} to ${max}, or null.`, { dragon: slug }));
}

function positiveNullable(value, label, errors, slug) {
  if (value == null) return;
  if (!Number.isFinite(value) || value <= 0) errors.push(issue("error", "positive_value", `${label} must be greater than zero, or null.`, { dragon: slug }));
}

