# Game-Data Encyclopedia

A dependency-free static reference generated from the repository's canonical
normalized data. The first vertical slice covers dragons, Commands, Vanguard
abilities, Habits, effects/statuses, breed and rarity metadata, troop affinities,
Star/Habit gates, evidence, uncertainty, full-text search, structured filters, and
bidirectional relationship links.

The Atlas integration adds 7,912 stable map-placement records, searchable map entity
pages, inferred crossing relationships with explicit uncertainty, and reciprocal deep
links that preserve the exact selected Atlas node.

The second milestone adds first-class graph records for schedules, conditions,
targeters, prioritizers, and status operations, plus a semantic version-history view.

## Build, test, and preview

```powershell
python projects/game-data-encyclopedia/scripts/build.py --preview
python -m unittest discover -s projects/game-data-encyclopedia/tests -v
python -m http.server 8000 --directory projects/game-data-encyclopedia/preview
```

Then open `http://localhost:8000/encyclopedia/`. The preview mirrors the deployed
layout: `/` and `/map/` serve the Atlas, while `/encyclopedia/` serves this application.
Entity URLs use client logical keys or stable map
row IDs in hash routes, so display-name changes do not break links. Map records use
`#/map-nodes/000000`; Atlas links use `../map/?node=map-node%3A000000`.

`#/history` compares the generated dataset with
`public/data/version-baseline.json`. Normal builds never replace that baseline. After
reviewing and accepting a client update, explicitly advance it with:

```powershell
python projects/shared-data-foundation/src/normalize/build_encyclopedia_data.py --update-baseline
```

The generated `changes.json` records added, changed, and removed stable entities,
changed fields, and changed source hashes. Serialization formatting does not produce a
semantic change.

## Content model decisions (GDE-011 through GDE-015)

- **Page types:** the slice has dragon index/detail, effect/status index/detail, map-node index/detail, search,
  and progression-mechanics views. Each entity requires a stable ID, lifecycle,
  evidence object, source version, exact text, normalized fields, and relationships.
- **Relationship vocabulary:** `applies`, `consumes`, `counters`, and `mentions` are
  generated from explicit wording. Reverse status links group sources, consumers,
  counters, and category-based cleanses. A generic Cleanse is never presented as a
  guaranteed selection of a particular effect.
- **Exact versus normalized:** verbatim strings are displayed in bordered source
  blocks. Search tags, schedules, targets, damage types, and derived traits appear in a
  separately labeled normalized treatment and never overwrite source wording.
- **Staged and unknown:** staged records are excluded by default and require the
  explicit “Show staged” filter. They use a distinct evidence badge and retain all
  missing-evidence notes. Unknown values are text or `null`, never numeric zero.
- **Canonical URLs:** dragons use installed-client `client_key`; abilities combine the
  dragon client key with the ability client key; effects use a versioned normalized
  registry ID. Display names are presentation fields only.
- **Map identities:** map placements use the zero-based row position in
  `clean_map_nodes.csv`, padded in `map-node:000000` form. The row order is the same
  placement identity already used by crossing-chain data; repeating `instance_id`
  values are retained only as source metadata.
- **Structured combat graph:** text-derived schedules, conditions, targeters,
  prioritizers, and status operations are separate stable records referenced by each
  ability. They retain their exact supporting phrase and are labeled `derived` so they
  cannot silently replace the source text.

## Publication boundary

The built site depends only on tracked JSON/CSV generated from canonical data. It
does not read ignored snapshots, raw protobuf files, emulator data, or generated
diagnostic outputs. The existing strategic map remains available at `/map/` and
round-trips exact selections through the `node` query parameter.
