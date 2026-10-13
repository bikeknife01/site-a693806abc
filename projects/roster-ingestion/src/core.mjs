import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const TOOL_VERSION = "1.0.0";
export const ROSTER_SCHEMA_VERSION = "dragonfire.player-roster.v1";
export const TRANSCRIPTION_SCHEMA_VERSION = "dragonfire.screenshot-transcription.v1";
export const PROFILE_VERSION = 3;
export const CONFIDENCE_VALUES = new Set(["low", "medium", "high", "confirmed"]);
export const REVIEW_VALUES = new Set(["machine_read", "confirmed", "corrected", "conflicting", "unreadable"]);
export const PROVENANCE_VALUES = new Set(["observed", "derived", "assumed", "unknown"]);
export const CRITICAL_FIELDS = new Set(["owned", "level", "stars", "power", "habit_levels"]);

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const PROJECT_ROOT = path.resolve(HERE, "../../..");
export const DEFAULT_KNOWLEDGE_PATH = path.join(PROJECT_ROOT, "projects/game-data-encyclopedia/public/data/encyclopedia.json");
export const GAME_MECHANICS_PATH = path.join(PROJECT_ROOT, "data/game_mechanics.json");
const GAME_MECHANICS = JSON.parse(fs.readFileSync(GAME_MECHANICS_PATH, "utf8"));
const ARMY_UPGRADES = GAME_MECHANICS.progression?.dragon_army_capacity_upgrades?.upgrades || {};
export const DRAGONS_ARMY_SKILLS = Object.freeze({
  none: { name: null, troops_per_level: 0 },
  I: { name: "Dragon's Army I", troops_per_level: Number(ARMY_UPGRADES["Dragon Army I"]?.troops_per_level) },
  II: { name: "Dragon's Army II", troops_per_level: Number(ARMY_UPGRADES["Dragon Army II"]?.troops_per_level) },
  III: { name: "Dragon's Army III", troops_per_level: Number(ARMY_UPGRADES["Dragon Army III"]?.troops_per_level) },
  IV: { name: "Dragon's Army IV", troops_per_level: Number(ARMY_UPGRADES["Dragon Army IV"]?.troops_per_level) },
});
if (Object.values(DRAGONS_ARMY_SKILLS).some(item => !Number.isFinite(item.troops_per_level))) throw new Error("Canonical Dragon's Army capacity rules are incomplete.");

export function sha256Buffer(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

export function sha256File(filePath) {
  return sha256Buffer(fs.readFileSync(filePath));
}

export function stableValue(value) {
  if (Array.isArray(value)) return value.map(stableValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, stableValue(value[key])]));
  }
  return value;
}

export function stableJson(value) {
  return `${JSON.stringify(stableValue(value), null, 2)}\n`;
}

export function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

export function writeJsonExclusive(filePath, value, { overwrite = false } = {}) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, stableJson(value), { encoding: "utf8", flag: overwrite ? "w" : "wx" });
}

export function writeTextExclusive(filePath, value, { overwrite = false } = {}) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, value.endsWith("\n") ? value : `${value}\n`, { encoding: "utf8", flag: overwrite ? "w" : "wx" });
}

export function normalizeLookup(value) {
  return String(value || "").normalize("NFKD").replace(/[’']/g, "").replace(/[^a-zA-Z0-9]+/g, "").toLowerCase();
}

export function loadKnowledge(knowledgePath = DEFAULT_KNOWLEDGE_PATH) {
  const resolved = path.resolve(knowledgePath);
  const data = readJson(resolved);
  if (!data?.metadata?.schema_version || !Array.isArray(data.dragons)) throw new Error(`Unsupported encyclopedia dataset: ${resolved}`);
  const bySlug = new Map();
  const byName = new Map();
  for (const dragon of data.dragons) {
    bySlug.set(dragon.slug.toLowerCase(), dragon);
    const key = normalizeLookup(dragon.name);
    if (byName.has(key)) throw new Error(`Canonical dragon name is ambiguous: ${dragon.name}`);
    byName.set(key, dragon);
  }
  return {
    path: resolved,
    data,
    bySlug,
    byName,
    metadata: {
      dataset_id: data.metadata.dataset_id,
      dataset_schema_version: data.metadata.schema_version,
      dataset_sha256: sha256File(resolved),
      game_mechanics_sha256: sha256File(GAME_MECHANICS_PATH),
      client_versions: data.metadata.client_versions || {},
      source_manifest: data.metadata.source_manifest || [],
    },
  };
}

export function resolveDragon(knowledge, value) {
  const raw = String(value || "").trim();
  if (!raw) return null;
  return knowledge.bySlug.get(raw.toLowerCase()) || knowledge.byName.get(normalizeLookup(raw)) || null;
}

export function canonicalHabits(dragon) {
  return (dragon?.abilities || []).filter(ability => ability.kind === "habit").sort((a, b) => {
    const aRank = Number(a.unlock?.star_rank || 0);
    const bRank = Number(b.unlock?.star_rank || 0);
    return aRank - bRank || a.client_key.localeCompare(b.client_key);
  });
}

export function emptyProfileEntry() {
  return {
    owned: null,
    include_in_search: null,
    level: null,
    stars: null,
    displayed_stars: null,
    power: null,
    troop_capacity: null,
    habit_levels: {},
    assumed: false,
  };
}

export function issue(severity, code, message, context = {}) {
  return { severity, code, message, ...context };
}

export function observedEvidence({ sourceId, field, rawValue, normalizedValue, confidence = "confirmed", reviewStatus = "confirmed", crop = null, note = null }) {
  return {
    source_id: sourceId,
    field,
    provenance: "observed",
    raw_value: rawValue ?? null,
    normalized_value: normalizedValue ?? null,
    confidence,
    review_status: reviewStatus,
    crop,
    note,
  };
}

export function derivedEvidence({ sourceId, field, rawValue, normalizedValue, note }) {
  return {
    source_id: sourceId,
    field,
    provenance: "derived",
    raw_value: rawValue ?? null,
    normalized_value: normalizedValue ?? null,
    confidence: "confirmed",
    review_status: "confirmed",
    crop: null,
    note,
  };
}

export function displayStarsToRank(displayed) {
  if (!displayed || typeof displayed !== "object") return null;
  const color = String(displayed.color || "").toLowerCase();
  const count = Number(displayed.count);
  if (!(["yellow", "red"].includes(color)) || !Number.isInteger(count) || count < 1 || count > 5) return null;
  return color === "red" ? count + 5 : count;
}

export function rankToDisplayedStars(stars) {
  const value = Number(stars);
  if (!Number.isInteger(value) || value < 1 || value > 10) return null;
  return value <= 5 ? { color: "yellow", count: value } : { color: "red", count: value - 5 };
}

export function normalizeNullableNumber(value, { zeroIsUnknown = false } = {}) {
  if (value == null || value === "") return null;
  const number = Number(value);
  if (!Number.isFinite(number) || (zeroIsUnknown && number === 0)) return null;
  return number;
}

export function normalizeDragonsArmySkill(value) {
  const raw = String(value ?? "none").trim();
  if (!raw || /^(none|0|unknown)$/i.test(raw)) return "none";
  const compact = raw.replace(/[’']/g, "").replace(/dragons?/gi, "").replace(/army/gi, "").replace(/[^iv]/gi, "").toUpperCase();
  if (Object.hasOwn(DRAGONS_ARMY_SKILLS, compact) && compact !== "none") return compact;
  throw new Error(`Dragon's Army skill must be none, I, II, III, or IV; received ${value}.`);
}

export function calculateDragonsArmyProgression({ skill = "none", level = 0, basis = "ingestion_default" } = {}) {
  const currentSkill = normalizeDragonsArmySkill(skill);
  const currentLevel = Number(level);
  if (!Number.isInteger(currentLevel) || currentLevel < 0 || currentLevel > 5) throw new Error("Dragon's Army level must be an integer from 0 to 5.");
  if (currentSkill === "none" && currentLevel !== 0) throw new Error("Dragon's Army level must be 0 when no skill is selected.");
  if (!(new Set(["user_declaration", "screenshot_transcription", "ingestion_default"])).has(basis)) throw new Error(`Unsupported Dragon's Army basis: ${basis}.`);
  const tiers = ["I", "II", "III", "IV"];
  const tierIndex = tiers.indexOf(currentSkill);
  const completedPriorBonus = tierIndex < 0
    ? 0
    : tiers.slice(0, tierIndex).reduce((sum, tier) => sum + DRAGONS_ARMY_SKILLS[tier].troops_per_level * 5, 0);
  const troopsPerLevel = DRAGONS_ARMY_SKILLS[currentSkill].troops_per_level;
  const currentSkillBonus = troopsPerLevel * currentLevel;
  const additionalPerDragon = completedPriorBonus + currentSkillBonus;
  return {
    current_skill: currentSkill,
    current_skill_name: DRAGONS_ARMY_SKILLS[currentSkill].name,
    current_level: currentLevel,
    troops_per_level: troopsPerLevel,
    completed_prior_skills_bonus_per_dragon: completedPriorBonus,
    current_skill_bonus_per_dragon: currentSkillBonus,
    additional_troops_per_dragon: additionalPerDragon,
    additional_troops_per_three_dragon_formation: additionalPerDragon * 3,
    provenance: basis === "ingestion_default" ? "assumed" : "observed",
    basis,
  };
}

export function createSnapshotBase({ profileId, observedAt, sourceKind, completeness = "declared_subset", expectedVisibleDragons = null, knowledge }) {
  return {
    schema_version: ROSTER_SCHEMA_VERSION,
    profile_id: profileId,
    observed_at: observedAt,
    source: {
      kind: sourceKind,
      inputs: [],
      field_treatment: [],
    },
    roster_preflight: {
      completeness,
      expected_visible_dragons: expectedVisibleDragons,
      observed_dragons: 0,
    },
    knowledge: knowledge.metadata,
    ingestion: {
      tool: "projects/roster-ingestion",
      tool_version: TOOL_VERSION,
    },
    profile: {
      version: PROFILE_VERSION,
      updated_at: observedAt,
      stronghold: {
        dragons_army: calculateDragonsArmyProgression(),
      },
      dragons: {},
    },
    evidence: {},
    review: {
      status: "needs_review",
      errors: [],
      warnings: [],
      conflicts: [],
    },
  };
}

export function addEvidence(snapshot, slug, field, record) {
  const key = `${slug}.${field}`;
  if (!snapshot.evidence[key]) snapshot.evidence[key] = [];
  snapshot.evidence[key].push(record);
}

export function relativeSourceName(inputPath) {
  return path.basename(inputPath).replace(/\\/g, "/");
}

export function sourceRecord(inputPath, id, kind) {
  const resolved = path.resolve(inputPath);
  return {
    id,
    kind,
    name: relativeSourceName(resolved),
    sha256: sha256File(resolved),
    size_bytes: fs.statSync(resolved).size,
  };
}

export function finalizeReview(snapshot) {
  const criticalConflicts = snapshot.review.conflicts.filter(item => item.recommendation_critical !== false);
  snapshot.review.status = snapshot.review.errors.length || criticalConflicts.length
    ? "blocked"
    : snapshot.review.warnings.length
      ? "needs_review"
      : "ready";
  snapshot.roster_preflight.observed_dragons = Object.values(snapshot.profile.dragons).filter(entry => entry.owned === true).length;
  return snapshot;
}

