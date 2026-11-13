(() => {
  "use strict";

  const content = document.querySelector("#content");
  const searchForm = document.querySelector("#global-search");
  const searchInput = document.querySelector("#search-input");
  const version = document.querySelector("#dataset-version");
  const toolSwitcher = document.querySelector("#tool-switcher");
  let data;
  let changesData;
  let changesError;
  let commandersData;
  let commanderAudit;
  let stagedPoiData;
  let documents = [];
  const repositoryBase = "https://github.com/bikeknife01/site-a693806abc/blob/main/";

  const escapeHtml = (value = "") => String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const label = value => value ? String(value).replaceAll("_", " ").replace(/\b\w/g, char => char.toUpperCase()) : "";
  const normalize = value => String(value || "").normalize("NFKD").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  const stem = token => ({ cleanses: "cleanse", cleaned: "cleanse", targets: "target", effects: "effect", rounds: "round" }[token]
    || (token.length > 4 && token.endsWith("s") ? token.slice(0, -1) : token));
  const tokens = value => normalize(value).split(/\s+/).filter(Boolean).map(stem);
  const matchesQuery = (haystack, query) => {
    const hayTokens = tokens(haystack);
    const queryTokens = tokens(query);
    if (queryTokens.filter(token => /^\d+$/.test(token)).length >= 2) {
      return hayTokens.join(" ").includes(queryTokens.join(" "));
    }
    const hay = new Set(hayTokens);
    return queryTokens.every(token => hay.has(token) || [...hay].some(item => item.startsWith(token)));
  };

  const evidenceChip = evidence => `<span class="evidence-chip ${escapeHtml(evidence.class.replaceAll("_", "-"))}">${escapeHtml(label(evidence.class))}</span>`;
  const lifecycleChip = lifecycle => lifecycle === "live" ? "" : `<span class="life-chip ${escapeHtml(lifecycle)}">${escapeHtml(label(lifecycle))}</span>`;
  const linkFor = item => item.entity_type === "dragon"
    ? `#/dragons/${encodeURIComponent(item.slug)}`
    : item.entity_type === "commander" ? `#/commanders/${encodeURIComponent(item.slug)}`
    : item.entity_type === "poi_reference" ? `#/poi-references/${encodeURIComponent(item.slug)}`
    : item.entity_type === "map_node"
      ? `#/map-nodes/${encodeURIComponent(item.slug)}`
      : `#/statuses/${encodeURIComponent(item.slug)}`;

  function buildDocuments() {
    const dragonDocs = data.dragons.map(dragon => {
      const abilityText = dragon.abilities.flatMap(ability => [
        ability.name,
        ...ability.exact_text,
        ...ability.normalized.damage_types,
        ...ability.normalized.schedules,
        ...ability.normalized.target_hints,
      ]);
      const affinities = (dragon.troop_affinities.positive || []).flatMap(item => [item, `${item} affinity`]);
      return {
        item: dragon,
        text: [dragon.name, dragon.breed, dragon.rarity_label, dragon.rarity_tier, ...dragon.traits, ...affinities, ...abilityText].join(" "),
      };
    });
    const effectDocs = data.effects.map(effect => ({
      item: effect,
      text: [effect.name, effect.game_section, effect.effect_on_target, effect.exact_text, effect.scope_note,
        ...Object.values(effect.relationships).flat().filter(ref => ref.lifecycle !== "staged").flatMap(ref => [ref.dragon_name, ref.ability_name])].join(" "),
    }));
    const mapDocs = data.map_nodes.map(node => ({
      item: node,
      text: [node.name, node.type, node.region, node.template_key, node.instance_id,
        node.coordinates.x, node.coordinates.y, node.level ? `level ${node.level}` : ""].join(" "),
    }));
    const commanderDocs = (commandersData?.commanders || []).map(commander => ({
      item: { ...commander, entity_type: "commander", lifecycle: "reference", evidence: { class: "official" } },
      text: [commander.name, "commander", ...commander.traits, commander.acquisition, ...commander.talents.flatMap(t => [t.name, t.exact_client_text])].join(" "),
    }));
    const poiDocs = (stagedPoiData?.references || []).map(poi => ({
      item: { ...poi, entity_type: "poi_reference", evidence: { class: "staged" } },
      text: [poi.name, poi.category, poi.region_key, poi.poi_key, ...poi.bonuses.map(bonus => bonus.name)].join(" "),
    }));
    documents = [...dragonDocs, ...effectDocs, ...mapDocs, ...commanderDocs, ...poiDocs];
  }

  function parseRoute() {
    const raw = location.hash.slice(1) || "/dragons";
    const [path, query = ""] = raw.split("?");
    return { parts: path.split("/").filter(Boolean), params: new URLSearchParams(query) };
  }

  function setActiveNav(section) {
    document.querySelectorAll("[data-nav]").forEach(link => link.classList.toggle("active", link.dataset.nav === section));
  }

  function relationshipSummary(ability) {
    const normalized = ability.normalized;
    const rows = [];
    if (normalized.damage_types.length) rows.push(["Damage", normalized.damage_types.join(", ")]);
    if (normalized.effect_relations.length) {
      rows.push(["Effects", normalized.effect_relations.map(rel => {
        const effect = data.effects.find(item => item.id === rel.effect_id);
        return `<a href="#/statuses/${encodeURIComponent(effect.slug)}">${escapeHtml(effect.name)}</a> <small>(${escapeHtml(rel.type)})</small>`;
      }).join(" · ")]);
    }
    const summary = rows.length ? `<dl>${rows.map(([term, value]) => `<div><dt>${term}</dt><dd>${value}</dd></div>`).join("")}</dl>` : "";
    const recordsFor = (field, graphType) => normalized[field].map(id => data.graph[graphType].find(item => item.id === id)).filter(Boolean);
    const scheduleRecords = recordsFor("schedule_refs", "schedules");
    const conditionRecords = recordsFor("condition_refs", "conditions");
    const targeterRecords = recordsFor("targeter_refs", "targeters");
    const prioritizerRecords = recordsFor("prioritizer_refs", "prioritizers");
    const operationRecords = recordsFor("status_operation_refs", "status_operations");
    const graphCards = [];
    if (scheduleRecords.length) graphCards.push(`<div class="graph-card"><strong>Timing</strong>${scheduleRecords.map(item => {
      const detail = item.rounds.length ? `Rounds ${item.rounds.join(", ")}` : item.parity ? `${label(item.parity)} rounds` : label(item.recurrence);
      return `<span>${escapeHtml(detail)} <small>${escapeHtml(label(item.phase))}</small></span>`;
    }).join("")}</div>`);
    if (conditionRecords.length) graphCards.push(`<div class="graph-card"><strong>Conditions</strong>${conditionRecords.map(item => {
      const effect = item.status_id ? data.effects.find(effectItem => effectItem.id === item.status_id) : null;
      const detail = effect ? `${effect.name} ${label(item.operator)}` : `${label(item.type)} ${item.operator ? label(item.operator) : ""} ${item.value ?? ""}`;
      return `<span>${escapeHtml(detail.trim())}</span>`;
    }).join("")}</div>`);
    if (targeterRecords.length) graphCards.push(`<div class="graph-card"><strong>Targeting</strong>${targeterRecords.map(item => `<span>${escapeHtml(item.count ?? "Unspecified")} ${escapeHtml(label(item.side))} · ${escapeHtml(label(item.scope))}</span>`).join("")}</div>`);
    if (prioritizerRecords.length) graphCards.push(`<div class="graph-card"><strong>Priority</strong>${prioritizerRecords.map(item => `<span>${escapeHtml(label(item.direction))} ${escapeHtml(item.field)} <small>${escapeHtml(label(item.priority_type))}</small></span>`).join("")}</div>`);
    if (operationRecords.length) graphCards.push(`<div class="graph-card"><strong>Status operations</strong>${operationRecords.map(item => {
      const effect = data.effects.find(effectItem => effectItem.id === item.effect_id);
      const metrics = [item.chance_percent != null ? `${item.chance_percent}%` : "", item.duration_rounds != null ? `${item.duration_rounds} rounds` : "", item.max_stacks != null ? `max ${item.max_stacks}` : ""].filter(Boolean).join(" · ");
      return `<span><a href="#/statuses/${encodeURIComponent(effect.slug)}">${escapeHtml(effect.name)}</a> · ${escapeHtml(label(item.operation))}${metrics ? ` <small>${escapeHtml(metrics)}</small>` : ""}</span>`;
    }).join("")}</div>`);
    if (!summary && !graphCards.length) return `<p>No structured interpretation beyond the exact wording is asserted.</p>`;
    return `${summary}${graphCards.length ? `<div class="graph-grid">${graphCards.join("")}</div>` : ""}`;
  }

  function filtersHtml(filters, section) {
    const options = (items, selected) => items.map(item => `<option value="${escapeHtml(item)}" ${item === selected ? "selected" : ""}>${escapeHtml(item)}</option>`).join("");
    if (section === "map-nodes") return `<form class="filters map-filters" id="filters">
      <label>Location type<select name="node_type"><option value="">All types</option>${options(data.facets.map_types, filters.nodeType)}</select></label>
      <label>Region<select name="region"><option value="">All regions</option>${options(data.facets.map_regions, filters.region)}</select></label>
      <label>Level<select name="level"><option value="">All levels</option>${options(data.facets.map_levels.map(String), filters.level)}</select></label>
      <label>Evidence<select name="evidence"><option value="">All evidence</option>${data.facets.evidence_classes.map(item => `<option value="${escapeHtml(item)}" ${item === filters.evidence ? "selected" : ""}>${escapeHtml(label(item))}</option>`).join("")}</select></label>
      <input type="hidden" name="type" value="map_node"><input type="hidden" name="section" value="map-nodes">
    </form>`;
    return `<form class="filters" id="filters">
      <label>Type<select name="type"><option value="all">All entities</option><option value="dragon" ${filters.type === "dragon" ? "selected" : ""}>Dragons</option><option value="commander" ${filters.type === "commander" ? "selected" : ""}>Commanders</option><option value="status" ${filters.type === "status" ? "selected" : ""}>Effects &amp; statuses</option><option value="map_node" ${filters.type === "map_node" ? "selected" : ""}>Atlas locations</option></select></label>
      <label>Breed<select name="breed"><option value="">All breeds</option>${options(data.facets.breeds, filters.breed)}</select></label>
      <label>Rarity<select name="rarity"><option value="">All rarities</option>${options(data.facets.rarities, filters.rarity)}</select></label>
      <label>Troop affinity<select name="affinity"><option value="">All affinities</option>${options(data.facets.troop_affinities, filters.affinity)}</select></label>
      <label>Evidence<select name="evidence"><option value="">All evidence</option>${data.facets.evidence_classes.map(item => `<option value="${escapeHtml(item)}" ${item === filters.evidence ? "selected" : ""}>${escapeHtml(label(item))}</option>`).join("")}</select></label>
      <label class="toggle"><input name="staged" type="checkbox" ${filters.staged ? "checked" : ""}> Show staged</label>
      <input type="hidden" name="section" value="${escapeHtml(section)}">
    </form>`;
  }

  function entityCard(item) {
    if (item.entity_type === "poi_reference") return `<a class="entity-card" href="${linkFor(item)}"><div class="card-meta"><span class="life-chip staged">Staged</span></div><h2>${escapeHtml(item.name)}</h2><p>Alpha Seat of Power reference · location unverified</p><div class="card-footer"><span>Regional bonuses</span><span>View reference →</span></div></a>`;
    if (item.entity_type === "commander") return `<a class="entity-card" href="${linkFor(item)}"><div class="card-meta"><span class="chip">Official guide · client text</span></div><h2>${escapeHtml(item.name)}</h2><p>${escapeHtml(item.traits.join(" · "))}</p><div class="card-footer"><span>3 talent descriptions</span><span>View guide →</span></div></a>`;
    if (item.entity_type === "dragon") {
      const abilityNames = item.abilities.slice(0, 3).map(ability => ability.name).join(" · ");
      return `<a class="entity-card" href="${linkFor(item)}">
        <div class="card-meta">${evidenceChip(item.evidence)}${lifecycleChip(item.lifecycle)}</div>
        <h2>${escapeHtml(item.name)}</h2>
        <div class="chips"><span class="chip">${escapeHtml(item.breed)}</span><span class="chip">${escapeHtml(item.rarity_tier || item.rarity_label || "Unknown rarity")}</span></div>
        <p>${escapeHtml(abilityNames)}</p>
        <div class="card-footer"><span>${item.abilities.length} abilities</span><span>View record →</span></div>
      </a>`;
    }
    if (item.entity_type === "map_node") {
      return `<a class="entity-card" href="${linkFor(item)}">
        <div class="card-meta">${evidenceChip(item.evidence)}<span class="chip">${escapeHtml(item.type)}</span></div>
        <h2>${escapeHtml(item.name)}</h2>
        <div class="chips"><span class="chip">${item.coordinates.x}, ${item.coordinates.y}</span>${item.level ? `<span class="chip">Level ${item.level}</span>` : ""}</div>
        <p>${escapeHtml(item.region || "Outside mapped regions")}</p>
        <div class="card-footer"><span>${item.crossing_connections.length} inferred links</span><span>View record →</span></div>
      </a>`;
    }
    const relCount = Object.values(item.relationships).flat().length;
    return `<a class="entity-card" href="${linkFor(item)}">
      <div class="card-meta">${evidenceChip(item.evidence)}${lifecycleChip(item.lifecycle)}</div>
      <h2>${escapeHtml(item.name)}</h2>
      <div class="chips"><span class="chip ${escapeHtml(item.effect_on_target)}">${escapeHtml(label(item.effect_on_target))}</span><span class="chip">${escapeHtml(item.game_section)}</span></div>
      <p>${escapeHtml(item.exact_text)}</p>
      <div class="card-footer"><span>${relCount} linked uses</span><span>View record →</span></div>
    </a>`;
  }

  function readFilters(route, section) {
    return {
      type: route.params.get("type") || (section === "search" ? "all" : section === "dragons" ? "dragon" : section === "map-nodes" ? "map_node" : "status"),
      breed: route.params.get("breed") || "",
      rarity: route.params.get("rarity") || "",
      affinity: route.params.get("affinity") || "",
      evidence: route.params.get("evidence") || "",
      staged: route.params.get("staged") === "1",
      nodeType: route.params.get("node_type") || "",
      region: route.params.get("region") || "",
      level: route.params.get("level") || "",
    };
  }

  function renderIndex(section, route) {
    setActiveNav(section === "statuses" ? "statuses" : "dragons");
    const query = route.params.get("q") || "";
    searchInput.value = query;
    const filters = readFilters(route, section);
    let results = documents.filter(document => !query || matchesQuery(document.text, query)).map(document => document.item);
    results = results.filter(item => filters.staged || item.lifecycle !== "staged");
    if (filters.type !== "all") results = results.filter(item => item.entity_type === filters.type);
    if (filters.breed) results = results.filter(item => item.breed === filters.breed);
    if (filters.rarity) results = results.filter(item => item.rarity_tier === filters.rarity);
    if (filters.affinity) results = results.filter(item => (item.troop_affinities?.positive || []).includes(filters.affinity));
    if (filters.evidence) results = results.filter(item => item.evidence.class === filters.evidence);
    if (filters.nodeType) results = results.filter(item => item.entity_type === "map_node" && item.type === filters.nodeType);
    if (filters.region) results = results.filter(item => item.entity_type === "map_node" && item.region === filters.region);
    if (filters.level) results = results.filter(item => item.entity_type === "map_node" && String(item.level) === filters.level);
    results.sort((a, b) => a.name.localeCompare(b.name));

    const title = query ? `Search: “${escapeHtml(query)}”` : section === "statuses" ? "Effects & statuses" : section === "map-nodes" ? "Atlas locations" : "Dragons";
    const description = query
      ? "Results match exact wording, normalized tags, relationships, traits, map types, regions, templates, IDs, and coordinates."
      : section === "statuses"
        ? "Definitions, sources, consumers, counters, and category-based cleanses in one relationship view."
        : section === "map-nodes"
          ? "Captured Bravo placements and inferred crossings. POI locations and values are server- and season-specific and stay fixed for that season; verify them on your server."
        : "Commands, Vanguard abilities, Habits, affinities, traits, progression gates, and source evidence.";
    const visibleResults = section === "map-nodes" && !query ? results.slice(0, 200) : results;
    content.innerHTML = `<section>
      <div class="page-heading"><div><p class="eyebrow">Combat reference</p><h1>${title}</h1><p>${description}</p></div><div class="count">${results.length} records</div></div>
      ${filtersHtml(filters, section)}
      ${section === "map-nodes" && results.length > visibleResults.length ? `<p class="panel-note">Showing the first ${visibleResults.length} records. Use search to locate a name, type, template, instance ID, or coordinate pair.</p>` : ""}
      ${section === "map-nodes" && !query && stagedPoiData ? `<section class="panel"><h2>Staged POI references</h2><p class="panel-note">Client definitions only; no verified coordinates or live availability.</p><div class="entity-grid">${stagedPoiData.references.map(item => entityCard({...item, entity_type: "poi_reference"})).join("")}</div></section>` : ""}
      <div class="entity-grid">${visibleResults.map(entityCard).join("") || `<div class="empty">No records match these filters.</div>`}</div>
    </section>`;
    bindFilters(section, query);
  }

  function bindFilters(section, query) {
    const form = document.querySelector("#filters");
    form.addEventListener("change", () => {
      const formData = new FormData(form);
      const params = new URLSearchParams();
      if (query) params.set("q", query);
      for (const key of ["type", "breed", "rarity", "affinity", "evidence", "node_type", "region", "level"]) {
        const value = formData.get(key);
        const defaultType = section === "dragons" ? "dragon" : section === "statuses" ? "status" : section === "map-nodes" ? "map_node" : "all";
        if (value && !(key === "type" && value === defaultType)) params.set(key, value);
      }
      if (formData.get("staged")) params.set("staged", "1");
      const base = query || section === "search" ? "/search" : `/${section}`;
      location.hash = `${base}${params.toString() ? `?${params}` : ""}`;
    });
  }

  function uncertaintyPanel(evidence) {
    if (!evidence.uncertainty?.length) return "";
    return `<section class="panel uncertainty"><h2>Uncertainty</h2><ul>${evidence.uncertainty.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul></section>`;
  }

  function evidencePanel(evidence) {
    const sourceUrl = evidence.source.startsWith("http") ? evidence.source : `${repositoryBase}${evidence.source.split("/").map(encodeURIComponent).join("/")}`;
    return `<section class="panel"><h2>Evidence</h2><dl class="facts">
      <div><dt>Class</dt><dd>${evidenceChip(evidence)}</dd></div>
      <div><dt>Confidence</dt><dd>${escapeHtml(label(evidence.confidence))}</dd></div>
      <div><dt>Source</dt><dd class="source-path"><a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">${escapeHtml(evidence.source)} ↗</a></dd></div>
      <div><dt>Version</dt><dd>${escapeHtml(evidence.source_version)}</dd></div>
    </dl></section>`;
  }

  function renderAbility(ability) {
    const unlock = ability.unlock.level ? `Level ${ability.unlock.level}` : ability.unlock.star_rank ? `${ability.unlock.star_rank} Stars` : "Core ability";
    return `<article class="ability" id="${escapeHtml(ability.id)}">
      <div class="ability-header"><div><span class="ability-kind">${escapeHtml(label(ability.kind))}</span><h3>${escapeHtml(ability.name)}</h3></div><span class="chip">${escapeHtml(unlock)}</span></div>
      ${ability.exact_text.map(text => `<div class="exact-block"><span class="exact-label">Exact source wording</span><p>${escapeHtml(text)}</p></div>`).join("")}
      <div class="normalized"><span class="normalized-label">Normalized interpretation</span>${relationshipSummary(ability)}</div>
      ${ability.evidence.uncertainty.length ? `<p class="panel-note">Client template contains unresolved values; see record uncertainty.</p>` : ""}
    </article>`;
  }

  function renderDragon(slugValue) {
    setActiveNav("dragons");
    const dragon = data.dragons.find(item => item.slug === decodeURIComponent(slugValue || ""));
    if (!dragon) return renderNotFound();
    searchInput.value = "";
    const affinity = dragon.troop_affinities.unknown
      ? "Not established"
      : (dragon.troop_affinities.positive || []).join(", ") || "None recorded";
    content.innerHTML = `<div class="breadcrumbs"><a href="#/dragons">Dragons</a><span>/</span><span>${escapeHtml(dragon.name)}</span></div>
      <header class="detail-heading"><div><p class="eyebrow">Dragon record</p><h1>${escapeHtml(dragon.name)}</h1><div class="chips">${evidenceChip(dragon.evidence)}${lifecycleChip(dragon.lifecycle)}<span class="chip">${escapeHtml(dragon.breed)}</span><span class="chip">${escapeHtml(dragon.rarity_tier || "Unknown rarity")}</span></div></div><div class="stable-id">${escapeHtml(dragon.id)}</div></header>
      <div class="detail-layout"><div class="stack">
        <section class="panel"><h2>Abilities</h2><p class="panel-note">Source wording is preserved verbatim. Structured tags below it are retrieval aids, not replacements.</p>${dragon.abilities.map(renderAbility).join("")}</section>
      </div><aside class="stack detail-aside">
        <section class="panel"><h2>Classification</h2><dl class="facts">
          <div><dt>Breed</dt><dd>${escapeHtml(dragon.breed)}</dd></div>
          <div><dt>Rarity tier</dt><dd>${escapeHtml(dragon.rarity_tier || "Unknown")}</dd></div>
          <div><dt>Display label</dt><dd>${escapeHtml(dragon.rarity_label || "Not recorded")}</dd></div>
          <div><dt>Positive affinity</dt><dd>${escapeHtml(affinity)}</dd></div>
          <div><dt>Negative affinity</dt><dd>${escapeHtml((dragon.troop_affinities.negative || []).join(", ") || "None displayed")}</dd></div>
        </dl></section>
        ${dragon.traits.length ? `<section class="panel"><h2>Derived traits</h2><div class="chips">${dragon.traits.map(item => `<span class="chip">${escapeHtml(item)}</span>`).join("")}</div><p class="panel-note">Derived from explicit kit evidence; these are not in-game classifications.</p></section>` : ""}
        ${evidencePanel(dragon.evidence)}${uncertaintyPanel(dragon.evidence)}
      </aside></div>`;
  }

  function relationshipGroup(title, refs) {
    const visible = refs.filter(ref => ref.lifecycle !== "staged");
    if (!visible.length) return "";
    return `<div class="relationship-group"><h3>${escapeHtml(title)}</h3><div class="relationship-list">${visible.map(ref => {
      const dragon = data.dragons.find(item => item.id === ref.dragon_id);
      return `<a class="relationship-link" href="#/dragons/${encodeURIComponent(dragon.slug)}"><span><strong>${escapeHtml(ref.ability_name)}</strong><small>${escapeHtml(ref.dragon_name)} · ${escapeHtml(label(ref.ability_kind))}</small></span><span>→</span></a>`;
    }).join("")}</div></div>`;
  }

  function renderStatus(slugValue) {
    setActiveNav("statuses");
    const effect = data.effects.find(item => item.slug === decodeURIComponent(slugValue || ""));
    if (!effect) return renderNotFound();
    searchInput.value = "";
    const rel = effect.relationships;
    content.innerHTML = `<div class="breadcrumbs"><a href="#/statuses">Effects &amp; statuses</a><span>/</span><span>${escapeHtml(effect.name)}</span></div>
      <header class="detail-heading"><div><p class="eyebrow">Effect / status</p><h1>${escapeHtml(effect.name)}</h1><div class="chips">${evidenceChip(effect.evidence)}${lifecycleChip(effect.lifecycle)}<span class="chip ${escapeHtml(effect.effect_on_target)}">${escapeHtml(label(effect.effect_on_target))}</span></div></div><div class="stable-id">${escapeHtml(effect.id)}</div></header>
      <div class="detail-layout"><div class="stack">
        <section class="panel"><h2>Definition</h2><div class="exact-block"><span class="exact-label">Exact repository wording</span><p>${escapeHtml(effect.exact_text)}</p></div>${effect.scope_note ? `<div class="normalized"><span class="normalized-label">Scope boundary</span>${escapeHtml(effect.scope_note)}</div>` : ""}</section>
        <section class="panel"><h2>Relationship graph</h2><p class="panel-note">Reverse links are generated from exact ability wording. Category cleanses are shown as possible cleanses, not guaranteed target selection.</p>
          ${relationshipGroup("Sources / appliers", rel.sources)}
          ${relationshipGroup("Consumers / conditional payoffs", rel.consumers)}
          ${relationshipGroup("Counters / immunity", rel.counters)}
          ${relationshipGroup("May cleanse by category", rel.cleanses)}
          ${relationshipGroup("Other explicit mentions", rel.mentions)}
          ${![...rel.sources, ...rel.consumers, ...rel.counters, ...rel.cleanses, ...rel.mentions].some(ref => ref.lifecycle !== "staged") ? `<div class="empty">No live linked abilities in this slice.</div>` : ""}
        </section>
      </div><aside class="stack detail-aside">
        <section class="panel"><h2>Classification</h2><dl class="facts"><div><dt>Game section</dt><dd>${escapeHtml(effect.game_section)}</dd></div><div><dt>Effect on target</dt><dd>${escapeHtml(label(effect.effect_on_target))}</dd></div><div><dt>Review required</dt><dd>${effect.review_required ? "Yes" : "No"}</dd></div></dl></section>
        ${evidencePanel(effect.evidence)}${uncertaintyPanel(effect.evidence)}
      </aside></div>`;
  }

  function renderMapNode(slugValue) {
    setActiveNav("map-nodes");
    const node = data.map_nodes.find(item => item.slug === decodeURIComponent(slugValue || ""));
    if (!node) return renderNotFound();
    searchInput.value = "";
    const atlasUrl = `../map/?node=${encodeURIComponent(node.id)}`;
    const connections = node.crossing_connections.map(id => data.map_nodes.find(item => item.id === id)).filter(Boolean);
    content.innerHTML = `<div class="breadcrumbs"><a href="#/map-nodes">Atlas locations</a><span>/</span><span>${escapeHtml(node.name)}</span></div>
      <header class="detail-heading"><div><p class="eyebrow">Atlas location</p><h1>${escapeHtml(node.name)}</h1><div class="chips">${evidenceChip(node.evidence)}<span class="chip">${escapeHtml(node.type)}</span>${node.level ? `<span class="chip">Level ${node.level}</span>` : ""}</div></div><div class="stable-id">${escapeHtml(node.id)}</div></header>
      <div class="detail-layout"><div class="stack">
        <section class="panel"><h2>Map placement</h2><p class="panel-note">Captured Bravo record: POI locations and values are server- and season-specific and stay fixed for that season. Verify this location on your server.</p><dl class="facts"><div><dt>Coordinates</dt><dd>${node.coordinates.x}, ${node.coordinates.y}</dd></div><div><dt>Region</dt><dd>${escapeHtml(node.region || "Outside mapped regions")}</dd></div><div><dt>Footprint</dt><dd>${node.footprint.width} × ${node.footprint.height}</dd></div><div><dt>Own place name</dt><dd>${node.has_own_name ? "Yes" : "No — display name falls back to its region"}</dd></div></dl><p><a class="action-link" href="${escapeHtml(atlasUrl)}">Open this location on the Atlas ↗</a></p></section>
        <section class="panel"><h2>Crossing connections</h2><p class="panel-note">These links are derived from spatial proximity because the client data has no explicit adjacency field.</p>${connections.length ? `<div class="relationship-list">${connections.map(item => `<a class="relationship-link" href="${linkFor(item)}"><span><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.type)} · ${item.coordinates.x}, ${item.coordinates.y}</small></span><span>→</span></a>`).join("")}</div>` : `<div class="empty">This location is not part of an inferred crossing chain.</div>`}</section>
      </div><aside class="stack detail-aside"><section class="panel"><h2>Source identifiers</h2><dl class="facts"><div><dt>Template</dt><dd class="source-path">${escapeHtml(node.template_key)}</dd></div><div><dt>Instance ID</dt><dd class="source-path">${escapeHtml(node.instance_id)}</dd></div><div><dt>Variant</dt><dd>${escapeHtml(node.variant || "Not recorded")}</dd></div><div><dt>Type code</dt><dd>${escapeHtml(node.type_code)}</dd></div></dl></section>${evidencePanel(node.evidence)}${uncertaintyPanel(node.evidence)}</aside></div>`;
  }

  function renderMechanics() {
    setActiveNav("mechanics");
    searchInput.value = "";
    const stars = data.facets.star_gates;
    const breedCards = Object.entries(data.mechanics.breeds).map(([name, value]) => `<section class="panel"><p class="eyebrow">${escapeHtml(value.role)}</p><h2>${escapeHtml(name)}</h2><p>${escapeHtml(value.summary)}</p><div class="chips"><span class="chip">${escapeHtml(value.damage_profile)}</span><span class="chip">${escapeHtml(value.primary_stat)}</span></div></section>`).join("");
    content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Progression reference</p><h1>Star &amp; Habit gates</h1><p>Star Rank unlocks Habits. Habit skill level is a separate permanent upgrade track; neither should be inferred from the other.</p></div></div>
      <div class="mechanics-grid"><section class="panel"><h2>Habit unlock schedule</h2>${stars.map((star, index) => `<div class="gate-row"><span class="gate-number">${star}</span><div><strong>Habit ${index + 1}</strong><p>Unlocks at Star Rank ${star}. Its separate skill level can then be upgraded from 1 through 5.</p></div></div>`).join("")}</section>
      <section class="panel"><h2>Star display normalization</h2><dl class="facts">${Object.entries(data.mechanics.star_display).map(([key, value]) => `<div><dt>${escapeHtml(label(key))}</dt><dd>${escapeHtml(value)}</dd></div>`).join("")}</dl></section></div>
      <div class="page-heading" style="margin-top:2rem"><div><p class="eyebrow">Reference taxonomy</p><h1>Breeds</h1></div></div><div class="mechanics-grid">${breedCards}</div>
      <section class="panel" style="margin-top:1rem"><h2>Known mechanics limits</h2><dl class="facts">${Object.entries(data.mechanics.unresolved_public_rules).map(([key, value]) => `<div><dt>${escapeHtml(label(key))}</dt><dd>${escapeHtml(value)}</dd></div>`).join("")}</dl></section>`;
  }

  function renderHistory() {
    setActiveNav("history");
    searchInput.value = "";
    if (!changesData) {
      content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Validated data history</p><h1>History manifest unavailable</h1><p>The core encyclopedia is still available. Rebuild the static output to regenerate <code>data/changes.json</code>, then refresh this page.</p></div></div><div class="error"><strong>History data could not be loaded.</strong><p>${escapeHtml(changesError?.message || "The optional history manifest was not returned.")}</p><p><a href="#/dragons">Continue to the dragon index</a></p></div>`;
      return;
    }
    const summary = changesData.summary;
    const baseline = changesData.baseline;
    const current = changesData.current;
    const versionText = versions => Object.values(versions || {}).join("/") || "Unknown";
    const inventoryRows = Object.keys(current.inventory).map(key => `<div><dt>${escapeHtml(label(key))}</dt><dd><span>${escapeHtml(baseline.inventory[key] ?? 0)}</span><span aria-hidden="true">→</span><strong>${escapeHtml(current.inventory[key] ?? 0)}</strong></dd></div>`).join("");
    const changeLink = change => {
      if (change.entity_type === "dragon") {
        const dragon = data.dragons.find(item => item.id === change.entity_id);
        return dragon ? `#/dragons/${encodeURIComponent(dragon.slug)}` : "#/history";
      }
      if (change.entity_type === "status") {
        const effect = data.effects.find(item => item.id === change.entity_id);
        return effect ? `#/statuses/${encodeURIComponent(effect.slug)}` : "#/history";
      }
      const parent = data.dragons.find(item => item.id === change.parent_id);
      return parent ? `#/dragons/${encodeURIComponent(parent.slug)}` : "#/history";
    };
    const changeRows = changesData.changes.map(change => `<a class="change-row" href="${changeLink(change)}"><span class="change-kind ${escapeHtml(change.change_type)}">${escapeHtml(label(change.change_type))}</span><span><strong>${escapeHtml(change.name)}</strong><small>${escapeHtml(label(change.entity_type))}${change.changed_fields.length ? ` · ${escapeHtml(change.changed_fields.map(label).join(", "))}` : ""}</small></span><span>→</span></a>`).join("");
    content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Validated data history</p><h1>Version history</h1><p>Semantic changes compare stable entity records, exact wording, structured mechanics, evidence, and lifecycle—not filenames or serialization noise.</p></div><div class="count">${changesData.comparison_state === "unchanged" ? "Baseline matches" : "Review required"}</div></div>
      <div class="version-summary">
        <section class="version-card"><span>Baseline</span><h2>${escapeHtml(baseline.label)}</h2><p>Schema ${escapeHtml(baseline.dataset_schema_version)} · client ${escapeHtml(versionText(baseline.client_versions))}</p></section>
        <div class="version-arrow" aria-hidden="true">→</div>
        <section class="version-card current"><span>Current</span><h2>${escapeHtml(current.label)}</h2><p>Schema ${escapeHtml(current.dataset_schema_version)} · client ${escapeHtml(versionText(current.client_versions))}</p></section>
      </div>
      <div class="change-metrics"><div><strong>${summary.added}</strong><span>Added</span></div><div><strong>${summary.changed}</strong><span>Changed</span></div><div><strong>${summary.removed}</strong><span>Removed</span></div><div><strong>${summary.source_files_changed}</strong><span>Source files</span></div></div>
      <div class="detail-layout"><section class="panel"><h2>Semantic changes</h2><p class="panel-note">A changed record lists the fields requiring review before publication.</p>${changeRows || `<div class="history-empty"><strong>No semantic drift detected.</strong><p>The generated dataset matches the validated baseline. Future source updates will appear here by stable entity ID.</p></div>`}</section>
      <aside class="stack detail-aside"><section class="panel"><h2>Inventory comparison</h2><dl class="inventory-list">${inventoryRows}</dl></section>${changesData.source_changes.length ? `<section class="panel"><h2>Source changes</h2>${changesData.source_changes.map(item => `<div class="source-change"><span>${escapeHtml(label(item.change_type))}</span>${escapeHtml(item.path)}</div>`).join("")}</section>` : ""}</aside></div>`;
  }

  function renderPoiReference(slug) {
    setActiveNav("map-nodes");
    searchInput.value = "";
    const poi = stagedPoiData?.references.find(item => item.slug === decodeURIComponent(slug || ""));
    if (!poi) return renderNotFound();
    content.innerHTML = `<div class="breadcrumbs"><a href="#/map-nodes">Atlas locations</a><span>/</span><span>${escapeHtml(poi.name)}</span></div><header class="detail-heading"><div><p class="eyebrow">Installed-client reference · ${escapeHtml(stagedPoiData.snapshot_date)}</p><h1>${escapeHtml(poi.name)}</h1><div class="chips"><span class="life-chip staged">Staged</span><span class="chip">${escapeHtml(poi.campaign_reference)}</span><span class="chip">${escapeHtml(poi.category)}</span></div></div></header><div class="detail-layout"><div class="stack"><section class="panel"><h2>Regional bonus references</h2><p>These are associated client definitions, not established live bonuses.</p>${poi.bonuses.map(bonus => `<article class="ability-card"><h3>${escapeHtml(bonus.name)}</h3><p>${escapeHtml(bonus.evidence)}</p><p class="panel-note">${escapeHtml(bonus.property_key)}</p></article>`).join("")}</section><section class="panel"><h2>Known limitations</h2><ul>${poi.limitations.map(note => `<li>${escapeHtml(note)}</li>`).join("")}</ul><p>Client region description: <code>${escapeHtml(poi.region_description)}</code>.</p></section></div><aside class="stack detail-aside"><section class="panel"><h2>Client references</h2><dl class="facts"><div><dt>POI</dt><dd>${escapeHtml(poi.poi_key)}</dd></div><div><dt>Region</dt><dd>${escapeHtml(poi.region_key)}</dd></div><div><dt>Kingdom reference</dt><dd>${escapeHtml(poi.kingdom_client_reference)}</dd></div><div><dt>Shared template</dt><dd>${escapeHtml(poi.shared_template)}</dd></div><div><dt>Defender group</dt><dd>${escapeHtml(poi.defender_group)}</dd></div></dl><p class="panel-note">Client ${escapeHtml(stagedPoiData.client_version)} / ${escapeHtml(stagedPoiData.version_code)}; compared with ${escapeHtml(stagedPoiData.baseline)}.</p></section></aside></div>`;
  }

  function renderCommanders(slug, rank = 20) {
    setActiveNav("commanders");
    searchInput.value = "";
    if (!commandersData) {
      content.innerHTML = `<div class="error"><h1>Commander guide unavailable</h1><p>The Commander reference data could not be loaded. Rebuild the encyclopedia and refresh.</p></div>`;
      return;
    }
    const source = `<a href="${escapeHtml(commandersData.guide_url)}">Official Commander guide</a>`;
    if (slug) {
      const commander = commandersData.commanders.find(item => item.slug === decodeURIComponent(slug));
      if (!commander) return renderNotFound();
      const talentCards = commander.talents.map(talent => {
        const audit = commanderAudit?.talents.find(item => item.talent === talent.name && item.commander === commander.name);
        const values = (talent.reviewed_tracks || []).flatMap(row => {
          const track = audit?.tracks[row.progression_id];
          if (!track || ![1, 20].includes(track.length)) return [];
          const value = track.length === 1 ? track[0] : track[rank - 1];
          return [`<div><dt>${escapeHtml(row.label)}</dt><dd>${escapeHtml(Number((value * 100).toFixed(4)))}% <small>(${escapeHtml(row.progression_id)})</small></dd></div>`];
        }).join("");
        const evidence = audit ? `<details><summary>Inspect linked progression tracks</summary><p class="panel-note">Raw decimal tracks and reference chains; numeric field paths are schema-less evidence. Not every linked track has been assigned a player-facing meaning.</p><dl class="facts">${Object.entries(audit.tracks).filter(([key]) => key.includes("talent_")).map(([key, track]) => `<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(track.length === 1 ? track[0] : track[rank - 1])} <small>(${track.length === 1 ? "constant" : `rank ${rank}`}; raw decimal)</small></dd></div>`).join("")}</dl></details>` : "";
        const clientText = talent.exact_client_text.replace(/<[^>]*>/g, "");
        const displayedText = talent.name === "Hightower's Beacon" ? clientText.replace("until the end of Combat.", "until the end of Combat.*") : clientText;
        return `<article class="ability-card"><h3>${escapeHtml(talent.name)}</h3><p class="panel-note">Installed-client text · ${escapeHtml(commandersData.source_date)} · ${escapeHtml(talent.client_key)}. Formatting tags removed; placeholders in the text are unresolved.</p><p style="white-space:pre-wrap">${escapeHtml(displayedText)}</p>${talent.name === "Hightower's Beacon" ? `<p class="panel-note">* Damage bonus duration requires confirmation.</p>` : ""}${values ? `<h4>Traced values · rank ${rank}</h4><dl class="facts">${values}</dl><p class="panel-note">Signed values are changes, not multipliers. The snapshot's linked 20-entry tracks are interpreted as talent ranks. Refer to the talent text for timing, targets and gates. <a href="${escapeHtml(talent.comparison_source)}">Community comparison</a>; not every displayed rank was independently corroborated.</p>` : ""}${evidence}</article>`;
      }).join("");
      content.innerHTML = `<div class="breadcrumbs"><a href="#/commanders">Commanders</a><span>/</span><span>${escapeHtml(commander.name)}</span></div><header class="detail-heading"><div><p class="eyebrow">Commander reference</p><h1>${escapeHtml(commander.name)}</h1><div class="chips">${commander.traits.map(trait => `<span class="chip">${escapeHtml(trait)}</span>`).join("")}</div></div></header><div class="detail-layout"><div class="stack"><section class="panel"><h2>Talents</h2><p>Client definitions and progression tracks do not confirm availability, current values, or live combat behavior. Use the talent screen for your current rank. ${commander.slug === "corlys" ? `The publisher also describes these talents in its <a href="${escapeHtml(commandersData.corlys_url)}">Corlys guide</a>.` : ""}</p>${commanderAudit ? `<label>Talent rank <select id="commander-rank">${Array.from({length: 20}, (_, i) => `<option value="${i + 1}" ${rank === i + 1 ? "selected" : ""}>${i + 1}</option>`).join("")}</select></label>` : `<p class="panel-note">Progression audit unavailable; client text remains available.</p>`}${talentCards}</section></div><aside class="stack detail-aside"><section class="panel"><h2>Acquisition</h2><p>${escapeHtml(commander.acquisition)}</p><p class="panel-note">Published route; availability depends on your world and Reign. ${source}</p></section><section class="panel"><h2>Evidence and conflicts</h2><p>Westeros Command reports that descriptions and data were out of sync in earlier builds. Buffer Companion's viewed summary conflicts with this capture and the official Corlys description. Do not combine values across versions.</p><p><a href="../encyclopedia/data/commander_value_audit.json">Download reference chains and source hashes</a></p></section></aside></div>`;
      document.querySelector("#commander-rank")?.addEventListener("change", event => renderCommanders(slug, Number(event.target.value)));
      return;
    }
    content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Official guide and installed-client evidence</p><h1>Commanders</h1><p>Assign a Commander to an army to add talents that interact with its dragons and combat conditions.</p></div></div><div class="mechanics-grid"><section class="panel"><h2>Unlock and assign</h2><p>Unlock the Commander’s Seat through Stronghold Upgrades, then assign a Commander in the Army Builder. Manage them in the Commander Grove or Army Builder. If unavailable, the publisher says Commanders become available after your next Reign Transition.</p><p>${source} · Published November 10, 2026</p></section><section class="panel"><h2>Progression and persistence</h2><p>Collect Commander Medals, Commander Honors and Onyx Honors through quests, events and offers to upgrade talents. Commander rank is the sum of talent ranks; rarity progresses from Common through Legendary and some progression may increase Army Size. Commanders and their upgrades persist between Reigns.</p></section><section class="panel"><h2>Build around talents</h2><p>Check the talent’s required trait, lane, trigger, rank and whether it applies to player or non-player battles. A trait anywhere in an army and a trait required specifically in the Vanguard are different conditions. A chance is not a guarantee.</p><p>The formation planner does not model Commander effects or Commander Army Size bonuses.</p></section></div><div class="page-heading" style="margin-top:2rem"><div><h2>Commanders and traits</h2><p>Acquisition and traits are from the official guide; talent descriptions are captured client text.</p></div></div><div class="entity-grid">${commandersData.commanders.map(item => entityCard({...item, entity_type: "commander"})).join("")}</div><section class="panel" style="margin-top:1rem"><h2>Dragon traits</h2><p class="panel-note">Publisher examples; verify the current trait in the Dragon Pit or Army Builder. These are Commander traits, distinct from inferred ability tags.</p><dl class="facts">${Object.entries(commandersData.trait_examples).map(([trait, dragons]) => `<div><dt>${escapeHtml(trait)}</dt><dd>${escapeHtml(dragons.join(", "))}</dd></div>`).join("")}</dl></section>`;
  }

  function renderNotFound() {
    content.innerHTML = `<div class="error"><h1>Record not found</h1><p>The stable ID in this URL is not present in the current validated dataset.</p><p><a href="#/dragons">Return to the dragon index</a></p></div>`;
  }

  function render() {
    if (!data) return;
    const route = parseRoute();
    const [section = "dragons", id] = route.parts;
    if (section === "poi-references" && id) renderPoiReference(id);
    else if (section === "commanders") renderCommanders(id);
    else if (section === "dragons" && id) renderDragon(id);
    else if (section === "statuses" && id) renderStatus(id);
    else if (section === "map-nodes" && id) renderMapNode(id);
    else if (section === "dragons" || section === "statuses" || section === "map-nodes" || section === "search") renderIndex(section, route);
    else if (section === "mechanics") renderMechanics();
    else if (section === "history") renderHistory();
    else renderNotFound();
    content.focus({ preventScroll: true });
  }

  searchForm.addEventListener("submit", event => {
    event.preventDefault();
    const query = searchInput.value.trim();
    location.hash = query ? `/search?q=${encodeURIComponent(query)}` : "/dragons";
  });
  document.addEventListener("keydown", event => {
    if (event.key === "/" && !["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName)) {
      event.preventDefault();
      searchInput.focus();
    }
  });
  window.addEventListener("hashchange", render);
  toolSwitcher.addEventListener("change", event => { if (event.target.value) location.href = event.target.value; });

  const fetchJson = url => fetch(url, { cache: "no-store" }).then(response => {
    if (!response.ok) throw new Error(`${url} request failed: ${response.status}`);
    return response.json();
  });
  Promise.all([
    fetchJson("./data/encyclopedia.json"),
    fetchJson("./data/changes.json").catch(error => {
      changesError = error;
      return null;
    }),
    fetchJson("./data/commanders.json").catch(() => null),
    fetchJson("./data/commander_value_audit.json").catch(() => null),
    fetchJson("./data/staged_poi_references.json").catch(() => null),
  ])
    .then(([payload, changePayload, commanderPayload, auditPayload, poiPayload]) => {
      data = payload;
      changesData = changePayload;
      commandersData = commanderPayload;
      commanderAudit = auditPayload;
      stagedPoiData = poiPayload;
      buildDocuments();
      version.textContent = `Schema ${data.metadata.schema_version} · client ${Object.values(data.metadata.client_versions).join("/")}`;
      render();
    })
    .catch(error => {
      content.innerHTML = `<div class="error"><h1>Dataset unavailable</h1><p>${escapeHtml(error.message)}</p><p>Run the documented build command and serve the generated dist directory over HTTP.</p></div>`;
    });
})();
