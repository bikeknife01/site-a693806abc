export const OBSERVATION_KEY = "dragonfire.matchObservations.v1";
export const OBSERVATION_VERSION = 1;
export const OUTCOMES = ["win", "loss", "retreat", "recalled", "unknown"];

const clamp = (value, min, max, fallback) => {
  const number = Number(value);
  return Number.isFinite(number) ? Math.min(max, Math.max(min, Math.round(number))) : fallback;
};

export function normalizeObservation(raw) {
  const source = raw && typeof raw === "object" ? raw : {};
  const outcome = OUTCOMES.includes(source.outcome) ? source.outcome : "unknown";
  return {
    version: OBSERVATION_VERSION,
    id: String(source.id || `observation-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`),
    observed_at: String(source.observed_at || new Date().toISOString()),
    objective: String(source.objective || "pvp"),
    enemy_troop: String(source.enemy_troop || "unknown"),
    enemy_formation: Array.isArray(source.enemy_formation) ? source.enemy_formation.slice(0, 3).map(slot => ({
      lane: String(slot.lane || "unknown"), dragon: String(slot.dragon || "unknown"),
      level: slot.level == null ? null : clamp(slot.level, 1, 50, null), stars: slot.stars == null ? null : clamp(slot.stars, 1, 10, null),
    })) : [],
    recommended_signature: String(source.recommended_signature || ""),
    recommended_formation: Array.isArray(source.recommended_formation) ? source.recommended_formation.slice(0, 3).map(slot => ({ lane: String(slot.lane), dragon: String(slot.dragon) })) : [],
    recommended_troop: String(source.recommended_troop || "unknown"),
    outcome,
    stalemates: clamp(source.stalemates, 0, 20, 0),
    notes: String(source.notes || "").slice(0, 1000),
    scoring_effect: "none",
  };
}

export function loadObservations(storage = globalThis.localStorage) {
  try {
    const parsed = JSON.parse(storage?.getItem(OBSERVATION_KEY) || "[]");
    return Array.isArray(parsed) ? parsed.map(normalizeObservation) : [];
  } catch { return []; }
}

export function saveObservation(observation, storage = globalThis.localStorage) {
  const observations = loadObservations(storage);
  const normalized = normalizeObservation(observation);
  observations.push(normalized);
  storage?.setItem(OBSERVATION_KEY, JSON.stringify(observations));
  return { observation: normalized, observations };
}

export function observationsJson(storage = globalThis.localStorage) {
  return JSON.stringify({ schema_version: OBSERVATION_VERSION, scoring_effect: "none", observations: loadObservations(storage) }, null, 2);
}
