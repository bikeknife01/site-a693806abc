# Shared Data Foundation

## Project description

Create a repeatable extraction, normalization, validation and versioning layer used by all planned player tools. This is infrastructure, not a separate player-facing product. It prevents the Combat Explorer, Atlas, Counter Assistant, Shop Evaluator and Encyclopedia from interpreting the same protobuf structures differently.

## Goals

- Convert locally copied client resources into stable, documented JSON.
- Join hashed references to logical IDs and localization text.
- Preserve raw values, normalized interpretations and evidence provenance separately.
- Provide semantic diffs across client snapshots.
- Detect schema drift before generated data is published.

## Non-goals

- Reading or modifying files in the emulator.
- Treating anonymous protobuf field numbers as understood without corroboration.
- Storing account secrets or personal purchase history in Git.
- Making Commanders part of live recommendations before they appear in game.

## Existing related files

- `Game_Details/Resources/_pbdump.py`
- `Game_Details/Resources/_parse_locale.py`
- `Game_Details/Resources/_build_clean_data.py`
- `Game_Details/Resources/_build_map_nodes.py`
- `Game_Details/Resources/_build_terrain_data.py`
- `Game_Details/Resources/_build_region_data.py`
- `Game_Details/Resources/_snapshots/<version>/analysis/*`
- `data/dragons/*.json`
- `data/effects.json`
- `data/game_mechanics.json`
- `data/dragon_application_knowledge.json`
- `RECOMMENDATION_HANDOFF.md`

## Proposed project files

```text
projects/shared-data-foundation/
  PROJECT_PLAN.md
  schemas/
    evidence.schema.json
    combat.schema.json
    map.schema.json
    economy.schema.json
    player-profile.schema.json
  src/
    extract/
    normalize/
    validate/
    diff/
  tests/
    fixtures/
  generated/                 # ignored; reproducible output
  README.md                  # commands and data contract, added during implementation
```

## Work plan

### Phase F1 — Source inventory

- [ ] FND-011 Catalog tables used by each planned tool.
- [ ] FND-012 Record logical key, localized fields and reference fields for each table.
- [ ] FND-013 Classify fields as understood, probable, opaque or server-dependent.
- [ ] FND-014 Identify duplicate/current resource versions and deterministic selection rules.
- [ ] FND-015 Document snapshot provenance and local-copy-only handling.

### Phase F2 — Schemas and identity

- [x] FND-021 Define stable canonical IDs and display-name resolution.
- [x] FND-022 Define source/evidence/confidence objects.
- [ ] FND-023 Define combat, map, economy and player-profile schemas.
- [x] FND-024 Define staged-content flags and default filtering.
- [x] FND-025 Define unknown-value representation; never use zero as “unknown.”

### Phase F3 — Normalization

- [x] FND-031 Normalize dragon/ability/effect/condition/targeter graphs.
- [ ] FND-032 Normalize map/POI/region/terrain/crossing graphs.
- [ ] FND-033 Normalize item/shop/stock/offer/gacha/pity graphs.
- [ ] FND-034 Resolve localization with fallback to logical ID.
- [ ] FND-035 Generate compact browser datasets and full diagnostic datasets.

### Phase F4 — Validation

- [ ] FND-041 Validate schemas and unique IDs.
- [x] FND-042 Validate all references and report dangling IDs.
- [x] FND-043 Validate dragon counts and known screenshot-confirmed fixtures.
- [ ] FND-044 Validate map node counts, coordinate bounds and crossing connectivity.
- [ ] FND-045 Validate economy quantities, currencies and impossible negative values.
- [ ] FND-046 Fail safely when a client update changes an expected structure.

### Phase F5 — Version diff

- [ ] FND-051 Normalize filenames independently of resource-version numbers.
- [x] FND-052 Produce row/field semantic diffs.
- [x] FND-053 Separate content changes from cache additions and serialization churn.
- [x] FND-054 Generate a machine-readable change manifest for downstream tools.
- [x] FND-055 Generate a concise human review report before publication.

## Acceptance criteria

- One command can build normalized data from a specified local snapshot.
- Output is deterministic for the same input hashes.
- Every normalized record links to source resource, snapshot and evidence class.
- A broken or unknown reference is reported, not silently discarded.
- Commanders are emitted as staged and excluded by default from live tools.
- At least one downstream tool consumes generated output successfully.

## Implementation status — 2026-09-16

The minimum GDE combat slice is implemented: stable client-key identity, evidence
objects, staged policy, deterministic source hashing, first-class combat graph records,
a compact browser adapter, semantic baseline/diff manifests, and referential/exact-text
tests. The broader foundation remains in progress because map, economy, raw snapshot
selection, complete schema-validation automation, and full diagnostic output are not
yet implemented.
