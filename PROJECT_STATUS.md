# Project status

## Workflow

1. Extract game framework
2. Establish JSON and Markdown conventions
3. Extract each dragon
4. Validate screenshot coverage and JSON
5. Perform cross-dragon analysis
6. Create formation recommendation guidance
7. Run final completeness audit

## Dragon extraction

| Dragon | JSON | Wiki | Validated | Review issues | Status |
|---|---:|---:|---:|---:|---|
| Antares | Yes | Yes | Yes | 0 | Complete |
| Arrax | Yes | Yes | Yes | 0 | Complete |
| Arulix | Yes | Yes | Yes | 0 | Complete |
| Bevlorin | Yes | Yes | Yes | 0 | Complete |
| Caraxes | Yes | Yes | Yes | 0 | Complete |
| Crimson | Yes | Yes | Yes | 0 | Complete |
| Daemoros | Yes | Yes | Yes | 0 | Complete |
| Dawnseeker | Yes | Yes | Yes | 0 | Complete |
| Feskar | Yes | Yes | Yes | 0 | Complete |
| Jagadrix | Yes | Yes | Yes | 0 | Complete |
| Kalspire | Yes | Yes | Yes | 0 | Complete |
| Malachite | Yes | Yes | Yes | 0 | Complete |
| Moondancer | Yes | Yes | Yes | 0 | Complete |
| Nyrena | Yes | Yes | Yes | 0 | Complete |
| Rhysarion | Yes | Yes | Yes | 0 | Complete |
| Seasmoke | Yes | Yes | Yes | 0 | Complete |
| Shadowrend | Yes | Yes | Yes | 0 | Complete |
| Shadowsong | Yes | Yes | Yes | 0 | Complete |
| Sheepstealer | Yes | Yes | Yes | 0 | Complete |
| Shimmer | Yes | Yes | Yes | 0 | Complete |
| Solstryker | Yes | Yes | Yes | 0 | Complete |
| Sunfyre | Yes | Yes | Yes | 0 | Complete |
| Syrax | Yes | Yes | Yes | 0 | Complete |
| Tairax | Yes | Yes | Yes | 0 | Complete |
| Tashix | Yes | Yes | Yes | 0 | Complete |
| Tessarion | Yes | Yes | Yes | 0 | Complete |
| Thunderstrike | Yes | Yes | Yes | 0 | Complete |
| Vaeldra | Yes | Yes | Yes | 0 | Complete |
| Velar | Yes | Yes | Yes | 0 | Complete |
| Venator | Yes | Yes | Yes | 0 | Complete |
| Vermax | Yes | Yes | Yes | 0 | Complete |
| Vesper | Yes | Yes | Yes | 0 | Complete |
| Vhagar | Yes | Yes | Yes | 0 | Complete |
| Zivern | Yes | Yes | Yes | 0 | Complete |

Allowed statuses: `Pending`, `In Progress`, `Needs Review`, and `Complete`.

A dragon is Complete only when:

- Every source screenshot has been inspected.
- Command, Vanguard, and all five Habits are represented.
- Exact displayed values have been cross-checked.
- The JSON parses successfully.
- The Markdown page exists.
- All ambiguity is recorded in the review queue.

## Shared work

| Item | Status |
|---|---|
| Source inventory | Complete |
| Core game mechanics | Complete |
| Effect glossary | Complete; Sheepstealer confirms Prey reduces Recovery Received by 30% |
| Dragon schema | Provisional; validated against Antares |
| Cross-dragon role index | Complete in `RECOMMENDATION_HANDOFF.md` |
| Synergy index | Complete in `RECOMMENDATION_HANDOFF.md` |
| Formation recommendation model | Complete as evidence rules and formation guidance |
| Online mechanics/source audit | Complete as of 2026-08-05; official system rules added and public unknowns documented |
| PvP scenarios | Pending |
| PvE scenarios | Pending |
| Final completeness audit | Complete; no unresolved review issues |

## Open questions

See `review/README.md`.

## Full knowledge-base audit — 2026-08-04

- Screenshots inspected: all 286 PNG panels in all 34 `Dragon_Specs` folders, including 34 Basics panels, 34 Vanguard panels, 48 Command/continuation panels, and 170 Habit panels.
- Records corrected: added missing source wording and recommendation-critical conditions for all 85 Habits in 17 later JSON records; normalized `Shield` to `Shieldbearers`; expanded incomplete derived roles; recorded missing/cropped facts; and corrected Review issue counts.
- Wiki corrections: expanded the four incomplete pages for Shadowsong, Sheepstealer, Shimmer, and Solstryker; normalized Shieldbearer terminology; and disclosed source limitations on affected dragon pages.
- Unresolved ambiguities: none. User confirmation resolved Dawnseeker's 10-Star title as `First Light`, Malachite's Command as `Warden's Rally`, Sheepstealer's rarity as Legendary, Vermax's rarity as Epic, and Vhagar's 10-Star title as `Skyward Titan`.
- Recommendation readiness: ready for formation recommendations. `RECOMMENDATION_HANDOFF.md` defines the schema, glossary, placement/targeting rules, cross-dragon catalog, limitations, and mandatory evidence-citation policy.

## Handoff log

Add one short entry after each work session:

- Date
- Dragons processed
- Files created or changed
- Validation performed
- New review issues
- Suggested next batch

### 2026-08-04 — Arrax, Arulix, Bevlorin, Caraxes

- Completed: Arrax, Arulix, Bevlorin, and Caraxes.
- Created: `data/dragons/{arrax,arulix,bevlorin,caraxes}.json` and matching `wiki/dragons/` pages.
- Validation: inspected all 32 assigned screenshots (8 per dragon), cross-checked ability text and all five Habit levels, parsed every new JSON file, and ran `git diff --check`.
- New review issues: none.
- Shared schema/mechanics changes: none.
- Suggested next batch: Crimson, Daemoros, Dawnseeker, Feskar.

### 2026-08-04 — Crimson, Daemoros, Dawnseeker, Feskar

- Completed: Crimson, Daemoros, Dawnseeker, and Feskar.
- Created: four normalized JSON records and matching wiki pages.
- Validation: inspected all 34 assigned screenshots, cross-checked ability text and five-level Habit tracks, and parsed every new JSON file.
- New review issues: none. Shared schema/mechanics changes: none.
- Suggested next batch: Jagadrix, Kalspire, Malachite, Moondancer.

### 2026-08-04 — Jagadrix, Kalspire, Malachite, Moondancer

- Created: four normalized JSON records and matching wiki pages.
- Validation: inspected all 35 assigned screenshots, cross-checked Command, Vanguard, five Habits, and five displayed Habit values, then parsed every new JSON file.
- Review issue later resolved by user confirmation: Malachite's Command is `Warden's Rally`.
- Suggested next batch: Nyrena, Rhysarion, Seasmoke, Shadowrend.

### 2026-08-04 — Nyrena, Rhysarion, Seasmoke, Shadowrend

- Completed: Nyrena, Rhysarion, Seasmoke, and Shadowrend.
- Created: four normalized JSON records and matching wiki pages.
- Validation: inspected all 34 assigned screenshots, combined split command panels, captured every Habit upgrade track, and parsed all new JSON.
- New review issues: none. Shared schema/mechanics changes: none.
- Suggested next batch: Shadowsong, Sheepstealer, Shimmer, Solstryker.

### 2026-08-04 — Shadowsong, Sheepstealer, Shimmer, Solstryker

- Completed: Shadowsong, Sheepstealer, Shimmer, and Solstryker.
- Created: four normalized JSON records and matching wiki pages.
- Validation: inspected all 35 assigned screenshots, combined split command panels, captured five Habit tracks, and parsed all new JSON.
- Shared mechanics evidence: Sheepstealer confirms Prey reduces Recovery Received by -30%.
- Suggested next batch: Sunfyre, Syrax, Tairax, Tashix.

### 2026-08-04 — Sunfyre, Syrax, Tairax, Tashix

- Completed: Sunfyre, Syrax, Tairax, and Tashix.
- Created: four normalized JSON records and matching wiki pages.
- Validation: inspected all 34 assigned screenshots, combined split command panels, cross-checked five Habit tracks, and parsed all new JSON.
- New review issues: none. Shared schema/mechanics changes: none.
- Suggested next batch: Tessarion, Thunderstrike, Vaeldra, Velar.

### 2026-08-04 — Tessarion, Thunderstrike, Vaeldra, Velar

- Completed: Tessarion, Thunderstrike, Vaeldra, and Velar.
- Created: four normalized JSON records and matching wiki pages.
- Validation: inspected all 33 assigned screenshots, combined Velar's split command panels, cross-checked Habit tracks, and parsed all new JSON.
- New review issues: none. Shared schema/mechanics changes: none.
- Suggested next batch: Venator, Vermax, Vesper, Vhagar.

### 2026-08-04 — Venator, Vermax, Vesper, Vhagar

- Completed: Venator, Vermax, Vesper, and Vhagar.
- Created: four normalized JSON records and matching wiki pages.
- Validation: inspected all 33 assigned screenshots, combined Venator's split command panels, and captured five Habit tracks for each dragon.
- Review issue resolved: Vhagar's 4-Star Habit is confirmed as Battle Leader.
- Suggested next batch: Zivern.

### 2026-08-04 — Zivern

- Completed: Zivern, the final dragon in the source set.
- Created: normalized JSON record and matching wiki page.
- Validation: inspected all 8 assigned screenshots, captured all five Habit tracks, and parsed the JSON.
- New review issues: none.
- Suggested next phase: cross-dragon analysis and formation guidance.

### 2026-08-04 — Full screenshot and recommendation-readiness audit

- Processed: all 34 dragons and all 286 supplied screenshots.
- Corrected: 17 JSON records with missing Habit wording/conditions, troop-name normalization, derived role coverage, affected wiki pages, review tracking, and project status.
- Created: `RECOMMENDATION_HANDOFF.md` with schema, mechanics glossary, formation interpretation, 34-dragon role/synergy/counter/constraint catalog, and evidence rules.
- Validation: parsed every dragon JSON; confirmed one JSON and wiki page per source folder; confirmed five Habits at Stars 2/4/6/8/10 and five upgrade columns per Habit; ran `git diff --check`.
- Review issues: none after user confirmation of all five previously unresolved facts.
- Shared schema/mechanics changes: every Habit now includes source wording; `Shieldbearers` is the canonical troop label; Prey remains documented as -30% Recovery Received where Sheepstealer explicitly states it.
- Suggested next phase: use the handoff to generate scenario-specific PvP and PvE formations with field-level citations.

### 2026-08-04 — Review confirmations

- Resolved: Dawnseeker 10-Star Habit is `First Light`; Malachite's Command is `Warden's Rally`; Sheepstealer is Legendary; Vermax is Epic; Vhagar 10-Star Habit is `Skyward Titan`.
- Updated: five JSON records, five wiki pages, `RECOMMENDATION_HANDOFF.md`, `review/README.md`, and this tracker.
- Review issues remaining: none.

### 2026-08-05 — Official and community web audit

- Reviewed: official site, WB Games support guides, official news/profiles/dev log,
  Dragonfire Hub, Reddit search results, community videos surfaced by search, and an
  independent fan wiki.
- Added: system-level progression, troop, retreat, PvE, POI, campaign, Stronghold,
  Heirloom, source-quality, and unresolved-rule guidance.
- Live additions: Starshower and Vermithor tracked in `data/live_updates.json`; full
  screenshot extraction remains pending because public profiles omit exact values,
  Vanguard text, and Habit upgrade tracks.
- Validation: parsed all JSON, checked customization diagnostics, ran `git diff --check`,
  and behavior-tested the Dragonfire Strategist's updated evidence routing.
