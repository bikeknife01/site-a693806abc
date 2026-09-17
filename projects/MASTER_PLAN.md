# Dragonfire Player Tools — Master Plan

## Purpose

This portfolio turns locally copied Dragonfire client data into five player-facing tools:

1. Combat Interaction Explorer
2. Strategic Atlas Overlays
3. Counter-Picking Assistant
4. Shop and Currency Evaluator
5. Game-Data Encyclopedia

The tools should explain their conclusions, preserve source provenance, distinguish confirmed mechanics from decoded or inferred behavior, and remain maintainable as the client data changes.

## Player profile and product assumptions

- The primary user is a spender. Purchase efficiency, unlock acceleration, star breakpoints, exclusivity, pity, duplicate value, and opportunity cost matter more than purely free-to-play optimization.
- Build time is normally eliminated through autocomplete and is not a primary optimization constraint.
- Commanders are not currently live. Commander records may be cataloged as staged data, but no initial recommendation, score, or simulator result should depend on them.
- The game can override client data from the server. Every displayed fact needs a source and confidence classification.
- Game files are read and decoded only from local PC copies. Emulator files are never analyzed in place.

## Shared principles

### Evidence classes

Every normalized fact receives one of these labels:

- `screenshot_confirmed`: visible in supplied in-game screenshots.
- `client_confirmed`: directly decoded from installed client data.
- `observed`: measured from an actual game result or log.
- `derived`: calculated from confirmed inputs.
- `staged`: present in client data but not established as live.
- `unknown`: unresolved or schema interpretation is incomplete.

The UI must not silently promote `staged`, `derived`, or `unknown` information to a confirmed game rule.

### Versioning

- Every generated dataset records the source snapshot date, client build, resource version, extraction script version, and hash.
- Current normalized output and historical snapshot comparisons remain separate.
- Stable logical IDs are used internally; localized names are presentation fields.
- A new snapshot must pass validation before replacing current generated output.

### Shared foundation

All five tools should consume normalized JSON produced by `projects/shared-data-foundation`, not read schema-less protobuf dumps in the browser.

Core shared entities:

- Dragon, command, habit, ability, effect, effect group, condition, targeter, prioritizer, status, trait, breed, troop type, lane and round schedule.
- Map node, POI, region, terrain class, crossing, route edge, encounter, defender and challenge rating.
- Item, currency, shop, slot, stock entry, offer, chest, pull option, pity rule and event availability.
- Source record, evidence class, confidence note and version/change record.

## Portfolio status

Status values: `not started`, `investigating`, `ready`, `in progress`, `blocked`, `validation`, `complete`.

| ID | Project | Status | Primary dependency | MVP completion |
|---|---|---|---|---|
| FND | Shared Data Foundation | in progress | None | Versioned normalized schemas, provenance, validators and generated datasets used by one tool |
| CIE | Combat Interaction Explorer | in progress | FND combat graph | Explain a selected 3v3 formation through one ten-round combat cycle |
| SAO | Strategic Atlas Overlays | not started | Existing Atlas + FND map data | Toggle useful strategic overlays without degrading route/search behavior |
| CPA | Counter-Picking Assistant | in progress | CIE rules + FND | Rank explainable counters for a specified enemy formation and objective |
| SCE | Shop and Currency Evaluator | not started | FND economy graph | Compare entered/live offers for unlock and star-progression value |
| GDE | Game-Data Encyclopedia | in progress | FND | Search and cross-link core dragons, effects, statuses, map entities and economy entities |

## Recommended dependency order

This is a technical order, not a commitment to start a particular user-facing project.

1. Build the minimum Shared Data Foundation required by the chosen first tool.
2. Build the Game-Data Encyclopedia shell early because it is the fastest way to inspect and validate normalized records.
3. Build the Combat Interaction Explorer rules engine.
4. Build the Counter-Picking Assistant on the combat engine rather than creating a second rules implementation.
5. Build Strategic Atlas Overlays against the existing Atlas data products.
6. Build the Shop and Currency Evaluator once shop/stock/offer relationships and live-price gaps are understood.

The Atlas and shop work can proceed independently of the combat work after shared IDs, provenance, and build conventions are established.

## Chosen delivery sequence

1. Extend the validated Encyclopedia/Atlas data contracts as needed by combat tooling.
2. Build the Combat Interaction Explorer.
3. Build the Counter-Picking Assistant on the Explorer's scenario and rules engine.
4. Add a shared player-tools landing page and consistent tool switcher to every application.
5. Complete cross-device/accessibility validation and publish the combined static site.
6. Continue optional Encyclopedia reference extensions and economy tooling after publication.

## Portfolio milestones

### M0 — Scope and source audit

- [ ] FND-001 Inventory all relevant current and snapshot resource tables.
- [ ] FND-002 Record which tables decode reliably and which fields remain anonymous.
- [ ] FND-003 Define evidence/confidence rules in machine-readable form.
- [ ] FND-004 Define current-vs-staged content policy; Commanders default to staged/hidden.
- [ ] FND-005 Establish a test snapshot and immutable expected fixtures.

Exit gate: each selected MVP can name its required source tables and unresolved fields.

### M1 — Normalized shared datasets

- [ ] FND-101 Publish JSON schemas for combat, map, and economy entities.
- [ ] FND-102 Build stable-ID and localization resolution.
- [ ] FND-103 Build source provenance and version manifests.
- [ ] FND-104 Add schema, referential-integrity, duplicate-ID and missing-localization validation.
- [ ] FND-105 Add snapshot-to-snapshot semantic diff output.

Exit gate: normalized outputs reproduce known dragon/map facts without reading raw protobuf in the UI.

### M2 — First vertical slice

- [x] Choose one of CIE, SAO, CPA, SCE or GDE.
- [x] Implement one end-to-end user workflow using generated data.
- [x] Add tests, confidence display, source links and build instructions.
- [ ] Validate against screenshots and at least one real in-game observation where applicable.

Exit gate: a user can complete the selected project's primary task locally.

### M3 — Cross-tool integration

- [x] Open Encyclopedia records directly from combat, counter and map results; shop results remain future scope.
- [x] Send a formation from Counter Picking to Combat Explorer.
- [ ] Send a map node/encounter from Atlas to the appropriate combat context.
- [ ] Send a dragon or item from Shop Evaluator to Encyclopedia and roster/investment context.
- [x] Reuse one browser-local player-profile format across Combat Explorer and Counter Picking; extend it to map/shop tools when built.

### M4 — Update automation and publication

- [ ] Run extraction and semantic diff against a new local snapshot.
- [ ] Block publishing on validation failures or unresolved breaking schema changes.
- [ ] Generate a player-readable change report.
- [ ] Publish static assets through the repository's existing GitHub Pages workflow.
- [ ] Add a rollback path to the last validated generated dataset.

## Decision matrix

Scores are relative estimates: 1 is low, 5 is high.

| Project | Immediate utility | Data readiness | Engineering effort | Validation difficulty | Shared leverage |
|---|---:|---:|---:|---:|---:|
| Combat Interaction Explorer | 5 | 4 | 5 | 5 | 5 |
| Strategic Atlas Overlays | 5 | 5 | 3 | 3 | 3 |
| Counter-Picking Assistant | 5 | 4 | 4 | 5 | 4 |
| Shop and Currency Evaluator | 4 | 3 | 4 | 4 | 3 |
| Game-Data Encyclopedia | 4 | 5 | 3 | 2 | 5 |

### Sensible first-project choices

- **Fastest visible gain:** Strategic Atlas Overlays.
- **Best foundation and lowest rules risk:** Game-Data Encyclopedia.
- **Highest analytical payoff:** Combat Interaction Explorer.
- **Most direct competitive decision support:** Counter-Picking Assistant, after a minimal combat engine.
- **Most spender-specific value:** Shop and Currency Evaluator, after confirming which prices and stocks are server-only.

## Cross-project player profile

Create one optional local profile, never committed with personal/account data:

- Owned dragons, levels, stars and Habit levels.
- Preferred troop types and common formations.
- Typical PvP/PvE/siege objectives.
- Current map position, faction and known owned/garrisoned tiles when relevant.
- Spending preferences: desired dragon, target star, maximum spend, value preference, tolerance for random pulls and whether cosmetic/non-combat items count.
- Time preference defaults: building completion time ignored; march time and combat-cycle time retained because they affect operations.

## Definition of done for every project

- [ ] Project plan acceptance criteria are met.
- [ ] No production calculation depends on Commanders while they remain staged.
- [ ] Every result distinguishes source facts from derived recommendations.
- [ ] Unknown or server-only inputs are requested rather than invented.
- [ ] Automated tests cover at least one normal, boundary and missing-data case.
- [ ] Generated data passes schema and referential-integrity validation.
- [ ] UI is usable on desktop and does not break the existing Atlas publication.
- [ ] A fresh local snapshot can update the tool without hand-editing generated output.
- [ ] Documentation identifies source files, build command and limitations.

## Tracking log

Add dated entries when a project changes state.

| Date | Project | From | To | Evidence/decision |
|---|---|---|---|---|
| 2026-09-16 | Portfolio | — | not started | Initial plans created; no implementation selected |
| 2026-09-16 | GDE | not started | in progress | Selected as the first implementation project; first vertical slice covers dragons, abilities, effects/statuses, search, evidence and stable links. |
| 2026-09-16 | FND | not started | in progress | Minimum combat encyclopedia schemas, normalization adapter and validators started in support of GDE. |
| 2026-09-16 | GDE | in progress | in progress | Combat-reference vertical slice built and locally validated; map/economy/history scope and publication remain. |
| 2026-09-16 | FND | in progress | in progress | Stable combat IDs, evidence schema, compact adapter, source manifest and referential tests now serve GDE; broader foundation remains. |
| 2026-09-16 | GDE | in progress | in progress | Added structured ability graphs and a player-readable semantic version-history view; map/economy scope and publication remain. |
| 2026-09-16 | FND | in progress | in progress | Added deterministic schedules, conditions, targeters, prioritizers, status operations, compact baseline fingerprints and field-level semantic diffs. |
| 2026-09-16 | GDE | in progress | in progress | Scheduled economy/building records, wiki provenance merge, version comparison, bookmarks, printable references and shared portfolio navigation as later extensions. |
| 2026-09-16 | CIE | not started | in progress | Selected as the next tool; first slice provides formation editing and an evidence-linked ten-round schedule timeline. |
| 2026-09-16 | CPA | not started | not started | Scheduled directly after CIE so counter recommendations reuse the combat scenario and rules engine. |
| 2026-09-17 | CPA | not started | in progress | First evidence-first threat extraction, roster filtering, formation alternatives, troop selection and Combat Explorer export built and browser-validated. |
| 2026-09-17 | Portfolio | not started | in progress | Added a shared landing page and tool switcher across Atlas, Encyclopedia, Combat Explorer and Counter Picker; combined Pages workflow prepared. |
| 2026-09-17 | Portfolio | in progress | in progress | Added a shared browser-local roster/progression profile with JSON portability, verified level/Star eligibility, per-Habit context, and progression-preserving Counter-to-Combat export. |
