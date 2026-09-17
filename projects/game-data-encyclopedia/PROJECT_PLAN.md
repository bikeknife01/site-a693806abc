# Game-Data Encyclopedia

## Project description

Build a searchable, cross-linked technical reference for Dragonfire. It should expose relationships hidden by the game UI while keeping exact source text, normalized interpretation, version history and confidence visible.

## Primary user questions

- Which dragons apply, consume or counter a status?
- What targets an ability and how is priority resolved?
- Which dragons share a trait, breed, troop affinity or damage type?
- What does a map POI, transit type, resource or encounter represent?
- Where can an item be obtained or spent?
- What changed between two client snapshots?

## Initial scope

- Dragons, commands, Vanguard abilities and Habits.
- Effects, statuses, labels, conditions, targeters and prioritizers.
- Traits, breeds, rarities, troop affinities and progression gates.
- Map POIs, regions, transit points, resources and encounters.
- Items, currencies, shops, chests and pity rules where resolved.
- Buildings/features such as Skirmish Grounds.
- Staged content included only behind an explicit filter and labeled prominently.

## Non-goals

- Reproducing story text as a primary feature.
- Presenting opaque decoded numbers without a label and caveat.
- Becoming a second independent source of normalized mechanics.
- Ranking dragons or purchases without scenario context.

## Existing related files

- `wiki/dragons/*.md`
- `wiki/Game-Mechanics.md`
- `wiki/Online-Sources.md`
- `data/dragons/*.json`
- `data/effects.json`
- `data/game_mechanics.json`
- `data/dragon_application_knowledge.json`
- `RECOMMENDATION_HANDOFF.md`
- Shared normalized outputs from `projects/shared-data-foundation`.

## Proposed project files

```text
projects/game-data-encyclopedia/
  PROJECT_PLAN.md
  src/
    pages/
    components/
    search/
    relationships/
    history/
  public/
  tests/
    search-fixtures/
    relationship-fixtures/
  README.md
```

## Information architecture

### Entity pages

Each page includes:

- Display name and stable logical ID.
- Exact localized or screenshot text.
- Normalized structured interpretation.
- Incoming and outgoing relationships.
- Evidence class, source, snapshot/build and uncertainty.
- Version history and relevant semantic changes.
- Links into Combat Explorer, Counter Picking, Atlas or Shop Evaluator.

### Relationship examples

- Dragon → command/habits/Vanguard/traits/affinities.
- Ability → conditions/effect groups/targets/rounds.
- Status → sources/consumers/counters/cleanses.
- Item → shops/chests/currencies/uses.
- POI → region/type/level/transit connections.
- Building → unlocks/modifiers/prerequisites.

### Search facets

- Entity type, live/staged state and evidence class.
- Damage type, status, target scope and round schedule.
- Dragon trait, breed, rarity and troop affinity.
- Map region, POI type, level, resource and encounter.
- Currency, shop, chest and event/campaign.

## Work plan

### Phase E1 — Content model

- [x] GDE-011 Define page types and required fields.
- [x] GDE-012 Define relationship vocabulary and reverse-link generation.
- [x] GDE-013 Define exact-text versus normalized-summary presentation.
- [x] GDE-014 Define staged/unknown visual treatments.
- [x] GDE-015 Define canonical URLs stable across display-name changes.

### Phase E2 — Data adapters

- [x] GDE-021 Consume normalized dragon and combat entities.
- [x] GDE-022 Consume map and POI entities.
- [ ] GDE-023 Consume economy entities.
- [x] GDE-024 Consume version/change manifests.
- [ ] GDE-025 Merge existing screenshot-audited wiki content without losing provenance.

### Phase E3 — Page generation

- [x] GDE-031 Generate dragon pages and ability subsections.
- [x] GDE-032 Generate effect/status pages with source and counter lists.
- [x] GDE-033 Generate map entity pages.
- [ ] GDE-034 Generate item/shop/chest/currency pages.
- [ ] GDE-035 Generate building/system pages.
- [x] GDE-036 Generate staged-content pages behind an explicit filter.

### Phase E4 — Search and navigation

- [x] GDE-041 Build client-side full-text index.
- [x] GDE-042 Add structured facets and multi-filter search.
- [x] GDE-043 Add bidirectional relationship navigation.
- [x] GDE-044 Add “related mechanics” and “used by” sections.
- [x] GDE-045 Add shareable query and entity URLs.

### Phase E5 — History and evidence

- [x] GDE-051 Display source snapshot/build and evidence class.
- [x] GDE-052 Display field-level uncertainty notes.
- [x] GDE-053 Display semantic changes between selected versions.
- [x] GDE-054 Distinguish live, staged, removed and superseded entities.
- [x] GDE-055 Link to raw decoded evidence only for local/developer builds, not public bulk assets.

### Phase E6 — Cross-tool integration

- [ ] GDE-061 Open a dragon/formation in Combat Explorer.
- [ ] GDE-062 Open a dragon in Counter Picking.
- [x] GDE-063 Open a POI on the Atlas.
- [ ] GDE-064 Open a shop/item in Shop Evaluator.
- [x] GDE-065 Provide stable link contracts for every other tool.

### Phase E7 — Validation and publication

- [x] GDE-071 Validate zero broken internal entity links.
- [x] GDE-072 Validate search recall for a fixed query suite.
- [x] GDE-073 Validate exact text against screenshot-audited fixtures.
- [ ] GDE-074 Test mobile/desktop readability and keyboard navigation.
- [ ] GDE-075 Publish as static GitHub Pages assets without exposing ignored snapshots.

### Phase E8 — Reference extensions

- [ ] GDE-081 Add item, currency, shop, chest, offer and pity-rule records once the economy schema is validated.
- [ ] GDE-082 Add building and game-system pages with prerequisites, unlocks and modifiers.
- [ ] GDE-083 Merge screenshot-audited wiki material with field-level provenance.
- [ ] GDE-084 Add side-by-side version comparison for selected releases and entities.
- [ ] GDE-085 Add optional local-only bookmarks and personal notes.
- [ ] GDE-086 Add printable dragon, matchup and alliance-operation reference sheets.

### Phase E9 — Portfolio navigation

- [x] GDE-091 Add a shared tool switcher linking the Encyclopedia, Atlas, Combat Explorer and Counter Picking Assistant.
- [ ] GDE-092 Preserve current entity or scenario context when another tool supports a compatible deep link.
- [x] GDE-093 Add the Encyclopedia to a shared player-tools landing page.

## MVP acceptance criteria

- Users can search dragons, abilities, statuses and core map/economy entities.
- Every entity has a stable link, evidence label and source version.
- Relationship pages show both sources and consumers where applicable.
- Staged Commander content is hidden by default and clearly labeled when enabled.
- Existing screenshot-confirmed wording remains distinguishable from client-decoded text.
- No raw ignored snapshot is required by the deployed page.

## Later extensions

- Saved personal notes and bookmarks stored locally.
- Side-by-side version comparison.
- Natural-language query layer constrained to cited encyclopedia records.
- Printable matchup, dragon and alliance-operation reference sheets.

## Implementation status — 2026-09-16

The first combat-reference vertical slice is implemented under this project with a
dependency-free static shell, generated compact dataset, stable hash routes, search,
facets, evidence/uncertainty display, staged-content opt-in, and local tests. Map,
economy, formal mobile QA, and an actual Pages deployment remain incomplete. The second
milestone adds first-class schedules, conditions, targeters,
prioritizers and status operations plus a deterministic baseline/change manifest and
history view. The Atlas integration now adds stable pages for all 7,912 placements,
map-specific search facets, inferred crossing relationships, and reciprocal deep links
that restore the exact selected Atlas node. Publication is wired into the existing Pages
workflow but has not been pushed or deployed. The chosen next sequence is Combat
Interaction Explorer, then Counter-Picking Assistant, followed by combined publication.
Economy/building coverage, richer version comparison, local bookmarks, printable
references and shared portfolio navigation are scheduled extensions rather than
blockers for the combat tools.
