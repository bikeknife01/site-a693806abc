import { LANES, buildTimeline, scenarioFromQuery, scenarioToQuery } from "./engine.mjs";

const $ = selector => document.querySelector(selector);
const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
let data;
let scenario;

function dragonName(slug) {
  return data.dragons.find(dragon => dragon.slug === slug)?.name || slug;
}

function renderMechanics(event) {
  const targets = event.target_groups.map(group => {
    const candidates = group.candidates.map(candidate => `${dragonName(candidate.dragon)} (${candidate.lane})`).join(", ");
    const state = group.resolution === "all_candidates" ? "resolved" : group.resolution === "selection_required" ? "choice unresolved" : group.resolution.replaceAll("_", " ");
    return `<div class="mechanic"><strong>Targets · ${escapeHtml(group.exact_text)}</strong><span>${candidates ? escapeHtml(candidates) : "No reliable candidate list"}</span><small>${escapeHtml(state)}${group.count ? ` · selects ${group.count}` : ""}</small></div>`;
  }).join("");
  const priorities = event.priorities.length ? `<div class="mechanic"><strong>Priority rules</strong><span>${event.priorities.map(item => escapeHtml(item.exact_text)).join(" · ")}</span><small>Stat, breed, and troop-count priorities remain unresolved without live formation stats.</small></div>` : "";
  const conditions = event.conditions.length ? `<div class="mechanic"><strong>Conditions</strong>${event.conditions.map(item => `<span class="condition ${item.state}">${escapeHtml(item.exact_text)} · ${escapeHtml(item.explanation)}</span>`).join("")}</div>` : "";
  const operations = event.status_operations.length ? `<div class="mechanic"><strong>Status relationships</strong><span>${event.status_operations.map(item => `${escapeHtml(item.operation)} ${escapeHtml(item.effect_name)}${item.chance_percent != null ? ` · ${item.chance_percent}%` : ""}${item.duration_rounds != null ? ` · ${item.duration_rounds} rounds` : ""}`).join("<br>")}</span><small>Raw normalized relationships; the projection applies stricter certainty and targeting rules.</small></div>` : "";
  const projection = event.status_projection.length ? `<div class="mechanic projection"><strong>Status projection</strong>${event.status_projection.map(item => `<span class="projection-state ${item.state}">${escapeHtml(item.effect_name)} · ${escapeHtml(item.state.replaceAll("_", " "))}${item.chance_percent != null ? ` (${item.chance_percent}%)` : ""}</span><small>${escapeHtml(item.explanation)}</small>`).join("")}</div>` : "";
  const suppression = event.suppression.length ? `<div class="mechanic suppression"><strong>Action suppression</strong><span>${event.suppression.map(item => `${escapeHtml(item.effect_name)}${item.stacks > 1 ? ` ×${item.stacks}` : ""}`).join(", ")}</span><small>This status was guaranteed active at the start of the round. The event remains visible because exact suppression ordering still requires validation.</small></div>` : "";
  return targets || priorities || conditions || operations || projection || suppression ? `<div class="mechanics-grid">${targets}${priorities}${conditions}${operations}${projection}${suppression}</div>` : "";
}

function renderStatusState(group) {
  const entries = Object.entries(group.status_after || {});
  if (!entries.length) return '<div class="status-state empty-state">No guaranteed active statuses after this phase.</div>';
  return `<div class="status-state"><strong>Guaranteed state after ${escapeHtml(group.label)}</strong>${entries.map(([slug, statuses]) => `<span><b>${escapeHtml(dragonName(slug))}</b> · ${statuses.map(status => `${escapeHtml(status.effect_name)}${status.stacks > 1 ? ` ×${status.stacks}` : ""}${status.expires_before_round != null ? ` (expires before R${status.expires_before_round})` : ""}`).join(", ")}</span>`).join("")}</div>`;
}

function dragonOptions(selected) {
  return data.dragons.filter(dragon => dragon.lifecycle !== "staged").map(dragon => `<option value="${escapeHtml(dragon.slug)}" ${dragon.slug === selected ? "selected" : ""}>${escapeHtml(dragon.name)} · ${escapeHtml(dragon.breed)}</option>`).join("");
}

function renderFormation(side) {
  const root = $(`#${side}`);
  root.innerHTML = scenario[side].map((slot, index) => `<article class="slot" data-side="${side}" data-index="${index}"><div class="lane">${LANES[index]}</div><label>Dragon<select class="dragon">${dragonOptions(slot.dragon)}</select></label><div class="progression"><label>Level<input class="level" type="number" min="1" max="50" value="${slot.level}"></label><label>Stars<input class="stars" type="number" min="1" max="10" value="${slot.stars}"></label></div></article>`).join("");
}

function readScenario() {
  for (const side of ["allies", "enemies"]) {
    document.querySelectorAll(`#${side} .slot`).forEach((node, index) => {
      scenario[side][index] = { lane: LANES[index], dragon: node.querySelector(".dragon").value, level: Number(node.querySelector(".level").value), stars: Number(node.querySelector(".stars").value) };
    });
  }
  scenario.troop = $("#troop").value;
  history.replaceState(null, "", `?${scenarioToQuery(scenario)}`);
  return scenario;
}

function renderTimeline() {
  const timeline = buildTimeline(data, readScenario());
  const total = timeline.reduce((sum, group) => sum + group.items.length, 0);
  $("#summary").textContent = `${total} scheduled ability events · ${scenario.troop}`;
  $("#timeline").innerHTML = timeline.map(group => `<details class="round" ${group.round <= 1 ? "open" : ""}><summary><span>${escapeHtml(group.label)}</span><small>${group.items.length} event${group.items.length === 1 ? "" : "s"}</small></summary><div class="events">${group.items.length ? group.items.map(event => `<article class="event ${event.side.toLowerCase()}"><div class="event-meta"><span class="side ${event.side.toLowerCase()}">${escapeHtml(event.side)}</span><span>${escapeHtml(event.lane)}</span><span>${escapeHtml(event.phase.replaceAll("_", " "))}</span><span>${escapeHtml(event.trigger)}</span><span class="evidence">${escapeHtml(event.evidence.class.replaceAll("_", " "))}</span></div><h3>${escapeHtml(event.dragon_name)} · ${escapeHtml(event.ability_name)}</h3>${event.exact_text.map(text => `<p>${escapeHtml(text)}</p>`).join("")}${renderMechanics(event)}<footer><span>${event.target_hints.length ? `Normalized hints: ${escapeHtml(event.target_hints.join(", "))}` : "No normalized target hint"}</span><a href="../encyclopedia/#/dragons/${encodeURIComponent(event.dragon_slug)}">Evidence record ↗</a></footer></article>`).join("") : '<p class="empty">No scheduled abilities for this phase.</p>'}${renderStatusState(group)}</div></details>`).join("");
}

async function init() {
  const response = await fetch("data/encyclopedia.json");
  if (!response.ok) throw new Error(`Dataset request failed (${response.status})`);
  data = await response.json();
  scenario = scenarioFromQuery(location.search, data.dragons.filter(dragon => dragon.lifecycle !== "staged"));
  $("#troop").innerHTML = data.facets.troop_affinities.map(troop => `<option ${troop === scenario.troop ? "selected" : ""}>${escapeHtml(troop)}</option>`).join("");
  renderFormation("allies");
  renderFormation("enemies");
  renderTimeline();
}

$("#generate").addEventListener("click", renderTimeline);
$("#copy-link").addEventListener("click", async () => { readScenario(); await navigator.clipboard.writeText(location.href); $("#copy-link").textContent = "Copied"; setTimeout(() => $("#copy-link").textContent = "Copy scenario link", 1200); });
$("#tool-switcher").addEventListener("change", event => { location.href = event.target.value; });
init().catch(error => { $("#timeline").innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`; });
