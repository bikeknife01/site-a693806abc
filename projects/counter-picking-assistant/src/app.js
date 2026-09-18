import { LANES, TROOPS, combatExplorerQuery, compareRecommendations, recommendFormations } from "./engine.mjs?v=counter-5";
import { habitSummary, loadProfile, mountProfileManager, rosterEntries, saveProfile } from "./player-profile.mjs";
import { OUTCOMES, loadObservations, observationsJson, saveObservation } from "./observations.mjs";

let data;
let dragons;
let profile;
const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const dragonLink = slug => `../encyclopedia/#/dragons/${encodeURIComponent(slug)}`;

async function init() {
  data = await fetch("data/encyclopedia.json").then(response => { if (!response.ok) throw new Error(`Dataset ${response.status}`); return response.json(); });
  dragons = data.dragons.filter(item => item.lifecycle !== "staged").sort((a, b) => a.name.localeCompare(b.name));
  profile = loadProfile(dragons);
  document.querySelector("#enemy-troop").innerHTML = TROOPS.map(item => `<option>${item}</option>`).join("");
  document.querySelector("#enemies").innerHTML = LANES.map((lane, index) => `<div class="slot"><span class="lane">${lane}</span><label>Dragon<select data-enemy="${index}"><option value="">Unknown / empty lane</option>${dragons.map((dragon, dragonIndex) => `<option value="${esc(dragon.slug)}" ${dragonIndex === index ? "selected" : ""}>${esc(dragon.name)} · ${esc(dragon.breed)}</option>`).join("")}</select></label><label>Level<input data-level="${index}" type="number" min="1" max="50" value="50"></label><label>Stars<input data-stars="${index}" type="number" min="1" max="10" value="10"></label></div>`).join("");
  renderRoster();
  mountProfileManager({ dragons, getProfile: () => profile, setProfile: value => { profile = value; }, onSave: () => { renderRoster(); render(); } });
  document.querySelector("#all").addEventListener("click", () => setRoster(true));
  document.querySelector("#none").addEventListener("click", () => setRoster(false));
  document.querySelector("#recommend").addEventListener("click", render);
  document.querySelector("#tool-switcher").addEventListener("change", event => { if (event.target.value) location.href = event.target.value; });
  rosterCount(); render();
}

function renderRoster() {
  document.querySelector("#roster").innerHTML = dragons.map(dragon => { const entry = profile.dragons[dragon.slug]; return `<label title="Level ${entry.level} · ${entry.stars} Stars · Habits ${habitSummary(dragon, entry)}"><input type="checkbox" value="${esc(dragon.slug)}" ${entry.owned ? "checked" : ""}><span>${esc(dragon.name)}<small>L${entry.level} · ${entry.stars}★</small></span></label>`; }).join("");
  document.querySelectorAll("#roster input").forEach(input => input.addEventListener("change", event => { profile.dragons[event.target.value].owned = event.target.checked; profile = saveProfile(profile, dragons); rosterCount(); }));
  rosterCount();
}
function setRoster(checked) { Object.values(profile.dragons).forEach(entry => { entry.owned = checked; }); profile = saveProfile(profile, dragons); renderRoster(); }
function rosterCount() { const owned = rosterEntries(profile).length; document.querySelector("#roster-count").textContent = `${owned} of ${dragons.length} available`; }
function enemySlots() { return LANES.map((lane, index) => { const dragon = document.querySelector(`[data-enemy="${index}"]`).value; const level = document.querySelector(`[data-level="${index}"]`).value; const stars = document.querySelector(`[data-stars="${index}"]`).value; return { lane, dragon, level: dragon && level ? Number(level) : null, stars: dragon && stars ? Number(stars) : null }; }); }

function render() {
  const enemies = enemySlots();
  const owned = rosterEntries(profile);
  const enemyTroop = document.querySelector("#enemy-troop").value;
  const result = recommendFormations(data, enemies, owned, enemyTroop, document.querySelector("#objective").value);
  document.querySelector("#summary").textContent = `${result.threats.length} explicit threats · ${owned.length} owned dragons · ${result.confidence.level} input confidence`;
  document.querySelector("#confidence").innerHTML = `<strong>${esc(result.confidence.level.toUpperCase())} INPUT CONFIDENCE</strong><span>${esc(result.confidence.note)}${result.confidence.missing.length ? ` Missing: ${esc(result.confidence.missing.join("; "))}.` : ""}</span>`;
  document.querySelector("#threats").innerHTML = result.threats.map(threat => {
    const detail = threat.sources.map(item => `${item.dragon} · ${item.ability} · ${item.timing} · ${item.target}${item.chance_percent == null ? "" : ` · ${item.chance_percent}% chance`}`).join("; ");
    return `<span class="threat" title="${esc(detail)}">${esc(threat.name)} · ${esc([...new Set(threat.sources.map(item => item.dragon))].join(", "))}</span>`;
  }).join("");
  document.querySelector("#recommendations").innerHTML = result.recommendations.length ? result.recommendations.map((item, index) => recommendationCard(item, index, enemies)).join("") : `<p class="muted">Select at least three available dragons. If the roster is narrow, the assistant will report only formations it can legally assemble.</p>`;
  renderComparison(result);
  renderObservationLog(result, enemies, enemyTroop);
}

function renderComparison(result) {
  const host = document.querySelector("#comparison");
  if (result.recommendations.length < 2) { host.innerHTML = ""; return; }
  const options = result.recommendations.map((item, index) => `<option value="${index}">${index + 1}. ${esc(item.formation.map(pick => pick.dragon.name).join(" · "))}</option>`).join("");
  host.innerHTML = `<div class="section-title"><div><p class="eyebrow">SIDE-BY-SIDE</p><h2>Compare proposed counters</h2></div></div><div class="compare-controls"><label>Formation A<select data-compare="left">${options}</select></label><label>Formation B<select data-compare="right">${options}</select></label></div><div id="comparison-body"></div>`;
  host.querySelector('[data-compare="right"]').value = "1";
  const update = () => {
    const leftIndex = Number(host.querySelector('[data-compare="left"]').value);
    const rightIndex = Number(host.querySelector('[data-compare="right"]').value);
    const left = result.recommendations[leftIndex]; const right = result.recommendations[rightIndex];
    const comparison = compareRecommendations(left, right);
    const cell = (label, a, b) => `<div class="compare-row"><b>${esc(label)}</b><span>${esc(a)}</span><span>${esc(b)}</span></div>`;
    host.querySelector("#comparison-body").innerHTML = `<div class="compare-table">${cell("Formation", left.formation.map(item => item.dragon.name).join(" · "), right.formation.map(item => item.dragon.name).join(" · "))}${cell("Documented coverage", `${Math.round(left.coverage * 100)}%`, `${Math.round(right.coverage * 100)}%`)}${cell("Shared troop", left.troop.troop, right.troop.troop)}${cell("Verified chains", left.synergies.length, right.synergies.length)}${cell("Unique dragons", comparison.left_only_dragons.join(", ") || "None", comparison.right_only_dragons.join(", ") || "None")}${cell("Uniquely covered threats", comparison.left_only_threats.join(", ") || "None", comparison.right_only_threats.join(", ") || "None")}${cell("Transparent score", left.score, right.score)}</div><p class="muted">Score delta A−B: ${comparison.score_delta >= 0 ? "+" : ""}${comparison.score_delta}. Compare the evidence rows above; the score is not a win prediction.</p>`;
  };
  host.querySelectorAll("[data-compare]").forEach(select => select.addEventListener("change", update)); update();
}

function renderObservationLog(result, enemies, enemyTroop) {
  const host = document.querySelector("#observations");
  const observations = loadObservations();
  const options = result.recommendations.map((item, index) => `<option value="${index}">${index + 1}. ${esc(item.formation.map(pick => pick.dragon.name).join(" · "))}</option>`).join("");
  host.innerHTML = `<div class="section-title"><div><p class="eyebrow">OBSERVED VALIDATION</p><h2>Record the real outcome</h2></div><span>${observations.length} saved locally</span></div><p class="muted">Observations are stored only in this browser and have no scoring effect. Export them for later evidence review; the assistant never fits rules to a single anecdote.</p><div class="observation-form"><label>Formation used<select id="observed-formation">${options}</select></label><label>Outcome<select id="observed-outcome">${OUTCOMES.map(value => `<option value="${value}">${esc(value)}</option>`).join("")}</select></label><label>Stalemates<input id="observed-stalemates" type="number" min="0" max="20" value="0"></label><label>Notes<input id="observed-notes" maxlength="1000" placeholder="What happened, without guessing hidden mechanics"></label><button type="button" id="observed-save" ${result.recommendations.length ? "" : "disabled"}>Save observation</button><button type="button" id="observed-export" ${observations.length ? "" : "disabled"}>Export JSON</button></div><span id="observed-message" class="muted" aria-live="polite"></span>`;
  host.querySelector("#observed-save").addEventListener("click", () => {
    const recommendation = result.recommendations[Number(host.querySelector("#observed-formation").value)];
    const saved = saveObservation({
      objective: document.querySelector("#objective").value, enemy_troop: enemyTroop, enemy_formation: enemies,
      recommended_signature: recommendation.signature,
      recommended_formation: recommendation.formation.map(item => ({ lane: item.lane, dragon: item.dragon.slug })),
      recommended_troop: recommendation.troop.troop, outcome: host.querySelector("#observed-outcome").value,
      stalemates: host.querySelector("#observed-stalemates").value, notes: host.querySelector("#observed-notes").value,
    });
    host.querySelector("#observed-message").textContent = `Saved locally. ${saved.observations.length} observation${saved.observations.length === 1 ? "" : "s"} available.`;
    host.querySelector("#observed-export").disabled = false;
  });
  host.querySelector("#observed-export").addEventListener("click", () => {
    const blob = new Blob([observationsJson()], { type: "application/json" });
    const link = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: "dragonfire-observed-matches.json" });
    link.click(); URL.revokeObjectURL(link.href); host.querySelector("#observed-message").textContent = "Observation log exported.";
  });
}

function recommendationCard(item, index, enemies) {
  const covered = new Set(item.covered);
  const uncovered = item.threats.filter(threat => !covered.has(threat.id));
  const conditional = item.threats.filter(threat => item.conditionalCovered?.includes(threat.id));
  const troopNotes = [item.troop.positive.length ? `positive affinity: ${item.troop.positive.join(", ")}` : "no positive affinities", item.troop.advantage ? "troop-cycle advantage" : "", item.troop.negative.length ? `negative affinity: ${item.troop.negative.join(", ")}` : "", item.troop.disadvantage ? "troop-cycle disadvantage" : ""].filter(Boolean).join(" · ");
  const synergies = item.synergies.length ? item.synergies.map(chain => `<li><b>${esc(chain.effect)}:</b> ${esc(chain.producer)}’s ${esc(chain.producerAbility)} → ${esc(chain.consumer)}’s ${esc(chain.consumerAbility)} <small>${esc(chain.reliability)} · prerequisite: ${esc(chain.prerequisite)}</small></li>`).join("") : `<li>No cross-dragon producer/payoff chain was verified from explicit status conditions.</li>`;
  const laneNotes = item.laneNotes.length ? item.laneNotes.map(note => `<li>${esc(note)}</li>`).join("") : `<li>No explicit same-lane, lane-priority, breed-priority, or directional Vanguard edge was found.</li>`;
  const reliability = item.habitReliability.length ? item.habitReliability.map(entry => `<li><b>${esc(entry.dragon)} · ${esc(entry.ability)}</b>: ${entry.chance_percent}% at Habit level ${entry.level}</li>`).join("") : `<li>No unlocked chance-based Habit is carrying this recommendation.</li>`;
  const horizon = `<li><b>Opening (rounds 0–3):</b> ${esc(item.combatHorizon.opening.join(", ") || "No explicit scheduled ability")}</li><li><b>Late cycle (rounds 7–10):</b> ${esc(item.combatHorizon.late.join(", ") || "No explicit scheduled ability")}</li>`;
  const breakdown = Object.entries(item.breakdown).map(([key, value]) => `<span>${esc(key.replaceAll("_", " "))}<b>${value >= 0 ? "+" : ""}${value}</b></span>`).join("");
  return `<article class="recommendation"><div class="rec-head"><div><p class="eyebrow">${index === 0 ? "BEST-SUPPORTED" : index === 1 ? "ALTERNATIVE" : "SECOND ALTERNATIVE"}</p><h2>${item.formation.map(pick => esc(pick.dragon.name)).join(" · ")}</h2></div><span class="coverage">${Math.round(item.coverage * 100)}% confirmed threat coverage</span></div><div class="formation">${item.formation.map(pick => `<div class="pick"><small>${esc(pick.lane)}</small><h3><a href="${dragonLink(pick.dragon.slug)}">${esc(pick.dragon.name)}</a></h3><span>${esc(pick.dragon.breed)} · L${pick.progression.level} · ${pick.progression.stars}★ · Habits ${esc(habitSummary(pick.dragon, pick.progression))}</span>${pick.counters.length ? `<ul class="evidence">${pick.counters.map(entry => `<li><b>${esc(entry.reason)}</b> via ${esc(entry.ability)}<span class="certainty ${entry.reliability.unresolved ? "unresolved" : ""}">${esc(entry.reliability.label)} · ${esc(entry.timing.note)}</span><q>${esc(entry.exact_text)}</q></li>`).join("")}</ul>` : `<p class="muted">Adds formation depth and ${pick.controls.length ? `${esc(pick.controls.map(control => control.name).join("/"))} control pressure` : "shared-troop compatibility"}; no direct counter claim.</p>`}</div>`).join("")}</div><div class="troop"><b>Shared troop: ${esc(item.troop.troop)}</b> — ${esc(troopNotes)}${uncovered.length ? `<br><b>What can go wrong:</b> No confirmed answer found for ${esc(uncovered.map(threat => threat.name).join(", "))}.` : `<br>Every extracted threat has at least one confirmed answer in this formation.`}${conditional.length ? `<br><b>Conditional client evidence:</b> ${esc(conditional.map(threat => threat.name).join(", "))}; unresolved templates do not count as confirmed coverage.` : ""}</div><details class="analysis" ${index === 0 ? "open" : ""}><summary>Timing, lanes, synergies, and reliability</summary><div class="analysis-grid"><section><h3>Verified synergy chains</h3><ul>${synergies}</ul></section><section><h3>Lane plan</h3><ul>${laneNotes}</ul></section><section><h3>Habit reliability</h3><ul>${reliability}</ul></section><section><h3>Combat horizon</h3><ul>${horizon}</ul></section></div><div class="score-breakdown" aria-label="Transparent ranking contributions">${breakdown}</div><p class="muted caveat">Scores rank documented coverage and fit; they do not predict a win or supply unknown damage, proc-order, or adjacency formulas.</p></details><div class="actions"><a href="../combat/?${combatExplorerQuery(item, enemies, item.troop.troop)}">Inspect in Combat Explorer ↗</a></div></article>`;
}

init().catch(error => { document.querySelector("#recommendations").innerHTML = `<p class="muted">Unable to load the normalized dataset: ${esc(error.message)}</p>`; });
