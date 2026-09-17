import { LANES, TROOPS, combatExplorerQuery, recommendFormations } from "./engine.mjs?v=counter-2";

let data;
const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const dragonLink = slug => `../encyclopedia/#/dragons/${encodeURIComponent(slug)}`;

async function init() {
  data = await fetch("data/encyclopedia.json").then(response => { if (!response.ok) throw new Error(`Dataset ${response.status}`); return response.json(); });
  const dragons = data.dragons.filter(item => item.lifecycle !== "staged").sort((a, b) => a.name.localeCompare(b.name));
  document.querySelector("#enemy-troop").innerHTML = TROOPS.map(item => `<option>${item}</option>`).join("");
  document.querySelector("#enemies").innerHTML = LANES.map((lane, index) => `<div class="slot"><span class="lane">${lane}</span><label>Dragon<select data-enemy="${index}">${dragons.map((dragon, dragonIndex) => `<option value="${esc(dragon.slug)}" ${dragonIndex === index ? "selected" : ""}>${esc(dragon.name)} · ${esc(dragon.breed)}</option>`).join("")}</select></label><label>Level<input data-level="${index}" type="number" min="1" max="50" value="50"></label><label>Stars<input data-stars="${index}" type="number" min="1" max="10" value="10"></label></div>`).join("");
  document.querySelector("#roster").innerHTML = dragons.map(dragon => `<label><input type="checkbox" value="${esc(dragon.slug)}" checked><span>${esc(dragon.name)}</span></label>`).join("");
  document.querySelectorAll("#roster input").forEach(input => input.addEventListener("change", rosterCount));
  document.querySelector("#all").addEventListener("click", () => setRoster(true));
  document.querySelector("#none").addEventListener("click", () => setRoster(false));
  document.querySelector("#recommend").addEventListener("click", render);
  document.querySelector("#tool-switcher").addEventListener("change", event => { if (event.target.value) location.href = event.target.value; });
  rosterCount(); render();
}

function setRoster(checked) { document.querySelectorAll("#roster input").forEach(input => { input.checked = checked; }); rosterCount(); }
function rosterCount() { const inputs = [...document.querySelectorAll("#roster input")]; document.querySelector("#roster-count").textContent = `${inputs.filter(item => item.checked).length} of ${inputs.length} available`; }
function enemySlots() { return LANES.map((lane, index) => ({ lane, dragon: document.querySelector(`[data-enemy="${index}"]`).value, level: Number(document.querySelector(`[data-level="${index}"]`).value), stars: Number(document.querySelector(`[data-stars="${index}"]`).value) })); }

function render() {
  const enemies = enemySlots();
  const owned = [...document.querySelectorAll("#roster input:checked")].map(item => item.value);
  const enemyTroop = document.querySelector("#enemy-troop").value;
  const result = recommendFormations(data, enemies, owned, enemyTroop, document.querySelector("#objective").value);
  document.querySelector("#summary").textContent = `${result.threats.length} explicit threats · ${owned.length} available dragons`;
  document.querySelector("#threats").innerHTML = result.threats.map(threat => `<span class="threat" title="${esc(threat.sources.map(item => `${item.dragon} · ${item.ability}`).join("; "))}">${esc(threat.name)} · ${esc([...new Set(threat.sources.map(item => item.dragon))].join(", "))}</span>`).join("");
  document.querySelector("#recommendations").innerHTML = result.recommendations.length ? result.recommendations.map((item, index) => recommendationCard(item, index, enemies)).join("") : `<p class="muted">Select at least three available dragons. If the roster is narrow, the assistant will report only formations it can legally assemble.</p>`;
}

function recommendationCard(item, index, enemies) {
  const covered = new Set(item.covered);
  const uncovered = item.threats.filter(threat => !covered.has(threat.id));
  const troopNotes = [item.troop.positive.length ? `positive affinity: ${item.troop.positive.join(", ")}` : "no positive affinities", item.troop.advantage ? "troop-cycle advantage" : "", item.troop.negative.length ? `negative affinity: ${item.troop.negative.join(", ")}` : "", item.troop.disadvantage ? "troop-cycle disadvantage" : ""].filter(Boolean).join(" · ");
  return `<article class="recommendation"><div class="rec-head"><div><p class="eyebrow">${index === 0 ? "BEST COVERAGE" : index === 1 ? "ALTERNATIVE" : "SECOND ALTERNATIVE"}</p><h2>${item.formation.map(pick => esc(pick.dragon.name)).join(" · ")}</h2></div><span class="coverage">${Math.round(item.coverage * 100)}% threat coverage</span></div><div class="formation">${item.formation.map(pick => `<div class="pick"><small>${esc(pick.lane)}</small><h3><a href="${dragonLink(pick.dragon.slug)}">${esc(pick.dragon.name)}</a></h3><span>${esc(pick.dragon.breed)} · ${esc(pick.dragon.rarity_tier)}</span>${pick.counters.length ? `<ul class="evidence">${pick.counters.map(entry => `<li><b>${esc(entry.reason)}</b> via ${esc(entry.ability)}<q>${esc(entry.exact_text)}</q></li>`).join("")}</ul>` : `<p class="muted">Adds formation depth and ${pick.controls.length ? `${esc(pick.controls.map(control => control.name).join("/"))} control pressure` : "shared-troop compatibility"}; no direct counter claim.</p>`}</div>`).join("")}</div><div class="troop"><b>Shared troop: ${esc(item.troop.troop)}</b> — ${esc(troopNotes)}${uncovered.length ? `<br><b>What can go wrong:</b> No explicit answer found for ${esc(uncovered.map(threat => threat.name).join(", "))}.` : `<br>Every extracted threat has at least one explicit answer in this formation.`}</div><div class="actions"><a href="../combat/?${combatExplorerQuery(item, enemies, item.troop.troop)}">Inspect in Combat Explorer ↗</a></div></article>`;
}

init().catch(error => { document.querySelector("#recommendations").innerHTML = `<p class="muted">Unable to load the normalized dataset: ${esc(error.message)}</p>`; });
