export const LANES = ["Left Flank", "Vanguard", "Right Flank"];
export const TROOPS = ["Archers", "Cavalry", "Shieldbearers", "Spearmen", "Siege"];

export function abilityEligible(ability, slot) {
  const unlock = ability.unlock || {};
  if (unlock.star_rank && Number(slot.stars) < Number(unlock.star_rank)) return false;
  if (unlock.level && Number(slot.level) < Number(unlock.level)) return false;
  if (ability.kind === "vanguard" && slot.lane !== "Vanguard") return false;
  return true;
}

export function extractThreats(data, enemySlots) {
  const effects = new Map(data.effects.map(item => [item.id, item]));
  const operations = new Map((data.graph.status_operations || []).map(item => [item.id, item]));
  const threats = new Map();
  for (const slot of enemySlots) {
    const dragon = data.dragons.find(item => item.slug === slot.dragon);
    if (!dragon) continue;
    for (const ability of dragon.abilities.filter(item => abilityEligible(item, slot))) {
      for (const type of ability.normalized.damage_types || []) {
        addThreat(threats, { id: `damage:${type}`, category: "damage", name: type, source: dragon.name, ability: ability.name, ability_id: ability.id, exact_text: ability.exact_text[0] });
      }
      for (const ref of ability.normalized.status_operation_refs || []) {
        const operation = operations.get(ref);
        const effect = operation && effects.get(operation.effect_id);
        if (!operation || operation.operation !== "applies" || !effect) continue;
        if (effect.id === "effect:recovery") addThreat(threats, { id: "sustain:recovery", category: "sustain", name: "Recovery", source: dragon.name, ability: ability.name, ability_id: ability.id, exact_text: ability.exact_text.find(line => /recovery|recover/i.test(line)) || ability.exact_text[0] });
        else if (effect.effect_on_target === "harmful") addThreat(threats, { id: `status:${effect.id}`, category: "status", effect_id: effect.id, name: effect.name, source: dragon.name, ability: ability.name, ability_id: ability.id, exact_text: ability.exact_text.find(line => line.toLowerCase().includes(effect.name.toLowerCase())) || ability.exact_text[0] });
      }
    }
  }
  return [...threats.values()];
}

function addThreat(map, threat) {
  const current = map.get(threat.id);
  if (current) current.sources.push({ dragon: threat.source, ability: threat.ability, ability_id: threat.ability_id, exact_text: threat.exact_text });
  else map.set(threat.id, { ...threat, sources: [{ dragon: threat.source, ability: threat.ability, ability_id: threat.ability_id, exact_text: threat.exact_text }] });
}

export function candidateEvidence(data, dragon, threats, progression = { stars: 10, level: 50 }) {
  const counters = [];
  const abilities = dragon.abilities.filter(ability => abilityEligible(ability, { ...progression, lane: ability.kind === "vanguard" ? "Vanguard" : "Left Flank" }));
  const textAbilities = abilities.map(ability => ({ ability, text: ability.exact_text.join(" ") }));
  for (const threat of threats) {
    if (threat.category === "damage") {
      const token = threat.name.replace(" Damage", "");
      const match = textAbilities.find(item => new RegExp(`(?:reduce|decrease)[^.]{0,100}${token} Damage (?:Dealt|Received)`, "i").test(item.text));
      if (match) counters.push(evidence(threat, match.ability, `Mitigates ${threat.name}`));
    } else if (threat.category === "sustain") {
      const match = textAbilities.find(item => /reduce[^.]{0,100}Recovery Received|Prey reduces Recovery Received/i.test(item.text));
      if (match) counters.push(evidence(threat, match.ability, "Pressures enemy Recovery"));
    } else if (threat.effect_id) {
      const effect = data.effects.find(item => item.id === threat.effect_id);
      const relation = [...(effect?.relationships?.counters || []), ...(effect?.relationships?.cleanses || [])].find(item => item.dragon_id === dragon.id && item.lifecycle !== "staged");
      const match = relation && abilities.find(ability => ability.id === relation.ability_id);
      if (match) {
        const reason = relation.relationship === "counters" ? `Counters ${threat.name}` : `May cleanse ${threat.name} by category`;
        const exactText = relation.relationship === "counters"
          ? match.exact_text.find(line => line.toLowerCase().includes(threat.name.toLowerCase()))
          : match.exact_text.find(line => /cleanse/i.test(line));
        counters.push(evidence(threat, match, reason, exactText));
      }
    }
  }
  const controls = [];
  for (const ability of abilities) {
    for (const relation of ability.normalized.effect_relations || []) {
      const effect = data.effects.find(item => item.id === relation.effect_id);
      if (relation.type === "applies" && effect?.game_section === "Control Effects" && effect.effect_on_target === "harmful") controls.push({ name: effect.name, ability: ability.name, ability_id: ability.id, exact_text: ability.exact_text.find(line => line.toLowerCase().includes(effect.name.toLowerCase())) || ability.exact_text[0] });
    }
  }
  return { dragon, counters, controls, covered: [...new Set(counters.map(item => item.threat_id))] };
}

function evidence(threat, ability, reason, exactText = null) {
  return { threat_id: threat.id, threat_name: threat.name, reason, ability: ability.name, ability_id: ability.id, exact_text: exactText || ability.exact_text.find(line => line.toLowerCase().includes(threat.name.toLowerCase().replace(" damage", ""))) || ability.exact_text[0] };
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

export function recommendFormations(data, enemySlots, ownedSlugs, enemyTroop, objective = "pvp") {
  const threats = extractThreats(data, enemySlots);
  const pool = data.dragons.filter(item => item.lifecycle !== "staged" && ownedSlugs.includes(item.slug)).map(dragon => candidateEvidence(data, dragon, threats));
  pool.sort((a, b) => b.covered.length - a.covered.length || b.controls.length - a.controls.length || a.dragon.name.localeCompare(b.dragon.name));
  const recommendations = [];
  const seeds = [...new Set([0, Math.min(3, pool.length - 1), Math.min(6, pool.length - 1)])].filter(index => index >= 0);
  for (const seed of seeds) {
    const selected = [pool[seed]];
    const covered = new Set();
    pool[seed].covered.forEach(id => covered.add(id));
    while (selected.length < 3) {
      const available = pool.filter(item => !selected.includes(item));
      available.sort((a, b) => newCoverage(b, covered) - newCoverage(a, covered) || b.covered.length - a.covered.length || b.controls.length - a.controls.length || a.dragon.name.localeCompare(b.dragon.name));
      const choice = available[0];
      if (!choice) break;
      selected.push(choice);
      choice.covered.forEach(id => covered.add(id));
    }
    if (selected.length < 3) continue;
    const signature = selected.map(item => item.dragon.slug).sort().join("|");
    if (recommendations.some(item => item.signature === signature)) continue;
    const vanguard = [...selected].sort((a, b) => Number(hasVanguardEvidence(b)) - Number(hasVanguardEvidence(a)) || b.covered.length - a.covered.length)[0];
    const flanks = selected.filter(item => item !== vanguard).sort((a, b) => a.dragon.name.localeCompare(b.dragon.name));
    const formation = [flanks[0], vanguard, flanks[1]].map((item, index) => ({ ...item, lane: LANES[index] }));
    const troop = chooseTroop(data, selected.map(item => item.dragon), enemyTroop, objective);
    recommendations.push({ signature, formation, troop, covered: [...covered], coverage: threats.length ? covered.size / threats.length : 0, threats });
  }
  return { threats, recommendations };
}

function newCoverage(candidate, covered) { return candidate.covered.filter(id => !covered.has(id)).length; }
function hasVanguardEvidence(candidate) { return candidate.dragon.abilities.some(ability => ability.kind === "vanguard" && abilityEligible(ability, { stars: 10, level: 50, lane: "Vanguard" })); }

export function combatExplorerQuery(recommendation, enemies, troop) {
  const params = new URLSearchParams();
  recommendation.formation.forEach((item, index) => { params.set(`a${index + 1}`, item.dragon.slug); params.set(`a${index + 1}s`, "10"); params.set(`a${index + 1}l`, "50"); });
  enemies.forEach((item, index) => { params.set(`e${index + 1}`, item.dragon); params.set(`e${index + 1}s`, String(item.stars)); params.set(`e${index + 1}l`, String(item.level)); });
  params.set("troop", troop);
  return params.toString();
}
