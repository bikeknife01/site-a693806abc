# Dragonfire repository instructions

This repository is an evidence-based knowledge base for formation recommendations
in *Game of Thrones: Dragonfire*.

## Source authority

- Treat current in-game screenshots as authoritative for exact dragon ability text.
- Use official WB Games support and Dragonfire news pages for system-level rules.
- Treat fan sites, Reddit, videos, and tier lists as discovery sources unless their
  claims are independently verified.
- Never silently resolve conflicting or ambiguous evidence. Record it for review.
- Preserve exact transcribed wording in JSON `verbatim` fields.
- Treat displayed dragon stats in screenshots as incidental snapshots that are subject
  to change. They may be retained as potential reference points, but must not be relied
  upon as stable dragon characteristics, balance values, or comparative evidence.

## Knowledge routing

- Store screenshot-complete dragon facts in `data/dragons/<name>.json`.
- Store shared mechanics in `data/game_mechanics.json`.
- Store effect definitions in `data/effects.json`.
- Store incomplete official additions in `data/live_updates.json`.
- Store source audits in `wiki/Online-Sources.md`.
- Do not duplicate detailed mechanics in customization files.

## Recommendation integrity

- Distinguish transcribed facts from derived strategy.
- Never invent damage formulas, proc order, adjacency behavior, target selection,
  effect stacking, or other undocumented mechanics.
- Do not use player-specific Basics screenshot values as intrinsic dragon traits.
- Treat Star Rank and Habit upgrade level as separate progression dimensions.
- Normalize star displays correctly: yellow stars represent Ranks 1-5; one red star is
  Rank 6, two red stars is Rank 7, continuing through five red stars at Rank 10.
- Compare all three Vanguard abilities before assigning the Vanguard position.
- Treat opposing lanes as matching named positions rather than mirrored positions:
  Left Flank aligns with Left Flank, Vanguard with Vanguard, and Right Flank with
  Right Flank for default and same-lane targeting. Explicit ability scopes and
  redirection mechanics override this alignment when stated.
- Combat resolves automatically after an army enters an enemy-occupied tile. Do not
  invent manual mid-combat choices. After each 10-round cycle that leaves both armies
  fighting, a 60-second Stalemate/regrouping window allows recall to the army's previous
  tile. If neither army is defeated or leaves, another 10-round cycle begins. This
  repeats until defeat or retreat/recall; one Stalemate is common in PvP and two
  sometimes occur, but neither is a hard limit.
- Do not rank dragons by Stars alone. Legendary kits tend to be more advanced than
  Epic, followed by Rare, but rarity is not absolute; lower-rarity dragons may have
  exceptional output or unique formation value.
- Habits have skill levels 1-5 upgraded with Breedmarks and rarity-matched Cores. Use
  Habit level as a secondary reliability/effectiveness input, especially for activation
  chances, without letting it override explicit synergy or matchup fit by itself.
- Account for troop affinity and troop-type advantage separately.
- A three-dragon formation has one shared troop-type choice. Never recommend a
  different troop type for each dragon or lane; evaluate the shared type against all
  three dragons' affinities.
- Positive affinity boosts the matching dragon's combat stats and therefore its
  stat-dependent damage and effectiveness; troop-type advantage separately increases
  damage dealt and reduces damage received against the weak troop type.
- Treat Positive affinity across all three dragons as affinity-perfect and the best
  affinity-derived damage baseline for that fixed trio. Do not treat it as automatically
  optimal when stronger dragon synergies, control, sustain, timing, troop counters, or
  scenario mechanics outweigh the affinity benefit.
- For POI assaults, distinguish Defender-clearing armies from Siege armies.

## Editing and validation

- Preserve the existing JSON schema and exact in-game terminology.
- Add uncertainty to `review` rather than guessing.
- Parse every changed JSON file.
- Run `git diff --check`.
- Update matching wiki, handoff, status, and source-audit documentation when the
  underlying knowledge changes.