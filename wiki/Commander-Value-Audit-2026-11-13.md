# Commander talent value audit — 2026-11-13

The November 13 Bikeknife static capture is client 26.10.58019, versionCode 345. This review follows talent → ability → effect group → effect/source progression → progression table references. The decoder is schema-less; fields are not authoritative semantic names. Twenty-entry tracks are interpreted as talent ranks 1–20 based on the talent system and source references. Values are installed-client evidence, not proof of current server activation or combat behavior. Signed percentages below are changes, not multipliers. See `data/commander_value_audit.json` for complete tracks, links and source hashes, and `data/commanders.json` for descriptions.

## Cross-source comparison

- [Westeros Command, 26.10.58019](https://westeroscommand.com/patch-notes/26.10.58019): the captured rank-20 tracks match its stated Daemon No Quarter, Criston Kingmaker and Rhaenyra Realm’s Delight values; its No Quarter rank 1 and 10 figures also match. It describes a Charlie-world comparison, not our server state.
- [Westeros Command, 26.9.57184](https://westeroscommand.com/patch-notes/26.9.57184): Sea Snake, Blockade, Driftmark, Vanguard’s Challenge, Strike and Vanish, Rogue Prince, Cloaked in Gold and Swift Counsel have matching cited rank-20 examples. Later changes override earlier values.
- [Westeros Command, 24861](https://westeroscommand.com/patch-notes/24861): the Seven’s Grace immunity, Recovery and stat tracks, Steel Beneath Silk stat bonus, and Beacon First-Strike and damage tracks agree with the reported rank-20 figures. The article assigns Beacon’s damage bonus three rounds; the captured description says until end of combat, while its group has numeric field `3: 3`. Runtime duration is unresolved.
- [Buffer Companion](https://buffercompanion.com/en/commandants): the summary viewed during review describes older-seeming kits; its Corlys stack count and trait multipliers conflict with both this capture and the [official Corlys guide](https://news.gotdragonfire.com/corlys-velaryon-the-sea-snake/). Exclude that summary from recommendation calculations. Search-indexed variants differ; a cached result is not evidence of the current page.
- Community rank-20 agreement does not independently verify every intermediate rank, the source-index interpretation, all targets or live behavior. The cost table and Commander capacity progression remain unpromoted: currency identity, rank mapping or competing tables remain unresolved.

## Traced progression values

Selected clauses are mapped to referenced progression rows; conditions, targets, timing and rank-gated bonuses must be read in the corresponding talent descriptions. Not all talent fields have a confidently mapped value.

### Corlys Velaryon

#### The Sea Snake

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Base Vulnerable chance | 3.33% | 20% | 50% | `prog_talent_theseasnake_trig_01` |
| Chance with Relentless | 6.66% | 40% | 100% | `prog_talent_theseasnake_trig_02` |
| Tactical damage dealt reduction, Relentless bonus | -3% | -9% | -15% | `prog_talent_theseasnake_neg_02` |

#### Blockade

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Physical and Tactical damage received | -0.42% | -2.5% | -6.25% | `prog_talent_blockade_pos_01` |
| Physical and Tactical damage received with Cunning | -0.84% | -5% | -12.5% | `prog_talent_blockade_pos_02` |
| Physical damage dealt reduction, Cunning bonus | -3% | -9% | -15% | `prog_talent_blockade_neg_01` |

#### Driftmark's Snare

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Undertow application chance | 6.67% | 40% | 100% | `prog_talent_driftmarkssnare_wrxn_trig_01` |
| Damage dealt change per Undertow stack | -2% | -2% | -2% | `prog_talent_driftmarkssnare_wrxn_neg_01` |
| Enemy Recovery received bonus | -2.5% | -7.5% | -12.5% | `prog_talent_driftmarkssnare_neg_01` |

### Criston Cole

#### The Kingmaker

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Vanguard damage increase above 75% troops | 0.5% | 3% | 7.5% | `prog_talent_thekingmaker_pos_01` |
| Vanguard damage increase at 50–75% troops | 0.75% | 4.5% | 11.25% | `prog_talent_thekingmaker_pos_02` |
| Vanguard damage increase at or below 50% troops | 1% | 6% | 15% | `prog_talent_thekingmaker_pos_03` |
| Vanguard Strength, Intelligence and Instinct bonus | 3.5% | 10.5% | 17.5% | `prog_talent_thekingmaker_pos_04` |

#### Vanguard's Challenge

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Enemy Vanguard Initiative change | -1.33% | -8% | -20% | `prog_talent_vanguardschallenge_neg_01` |
| Allied Vanguard Physical and Fire damage received | -0.8% | -4.8% | -12% | `prog_talent_vanguardschallenge_pos_01` |
| Allied Vanguard damage received with Dominant | -1.6% | -9.6% | -24% | `prog_talent_vanguardschallenge_pos_02` |
| Enemy Vanguard damage received, Dominant Vanguard bonus | 2% | 6% | 10% | `prog_talent_vanguardschallenge_neg_02` |
| Enemy Vanguard damage dealt, Stalwart Vanguard bonus | -2% | -6% | -10% | `prog_talent_vanguardschallenge_neg_03` |

#### Strike and Vanish

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Advantage chance | 3.33% | 20% | 50% | `prog_talent_strikeandvanish_trig_01` |
| Advantage chance with Dominant | 6.66% | 40% | 100% | `prog_talent_strikeandvanish_trig_02` |
| Evade chance | 0.5% | 3% | 7.5% | `prog_talent_strikeandvanish_evde_01` |
| Evade chance with Stalwart | 1% | 6% | 15% | `prog_talent_strikeandvanish_evde_02` |
| Flank damage received, Stalwart bonus | -2.5% | -7.5% | -12.5% | `prog_talent_strikeandvanish_pos_02` |

### Daemon Targaryen

#### The Rogue Prince

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Fire damage rate | 12% | 72% | 180% | `prog_talent_therogueprince_wrxn_dmg_01` |
| Allied damage dealt bonus when attacking players | 1% | 3% | 5% | `prog_talent_therogueprince_pos_01` |

#### Cloaked in Gold

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Physical damage received | -1.33% | -8% | -20% | `prog_talent_cloakedingold_pos_01` |
| Damage dealt bonus when attacking players with Volatile | 1% | 3% | 5% | `prog_talent_cloakedingold_pos_02` |

#### No Quarter

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Right-flank Fire damage dealt increase | 1.07% | 6.4% | 16% | `prog_talent_noquarter_pos_01` |
| Enemy damage received increase with Ruthless | 0.5% | 3% | 7.5% | `prog_talent_noquarter_neg_01` |

### Young Alicent

#### The Seven's Grace

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Immunity chance | 3.33% | 20% | 50% | `prog_talent_thesevensgrace_trig_01` |
| Immunity chance with Willful | 6.66% | 40% | 100% | `prog_talent_thesevensgrace_trig_02` |
| Recovery rate | 10% | 60% | 150% | `prog_talent_thesevensgrace_rec_01` |
| Recovery rate with Willful | 20% | 120% | 300% | `prog_talent_thesevensgrace_rec_02` |
| Strength and Initiative bonus with Willful | 2.4% | 7.2% | 12% | `prog_talent_thesevensgrace_pos_01` |

#### Steel Beneath Silk

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Resistance chance | 6.67% | 40% | 100% | `prog_talent_steelbeneathsilk_trig_01` |
| Intelligence and Instinct bonus with Cunning | 2.4% | 7.2% | 12% | `prog_talent_steelbeneathsilk_pos_02` |

#### Hightower's Beacon

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| First-Strike chance | 4.67% | 28% | 70% | `prog_talent_hightowersbeacon_trig_01` |
| Allied damage dealt bonus | 1% | 3% | 5% | `prog_talent_hightowersbeacon_pos_01` |

### Young Rhaenyra

#### The Realm's Delight

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Damage received reduction against players | -0.5% | -3% | -7.5% | `prog_talent_therealmsdelight_pos_01` |
| Damage received reduction against non-player armies | -1% | -6% | -15% | `prog_talent_therealmsdelight_pos_02` |

#### Swift Counsel

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Initiative increase | 0.67% | 4% | 10% | `prog_talent_swiftcounsel_pos_01` |
| Initiative increase with Nimble or Stalwart | 1.34% | 8% | 20% | `prog_talent_swiftcounsel_pos_02` |
| Resistance chance | 2% | 12% | 30% | `prog_talent_swiftcounsel_trig_01` |
| Intelligence bonus with Nimble or Stalwart | 3% | 9% | 15% | `prog_talent_swiftcounsel_pos_04` |
| Post-combat tile durability damage bonus | 1% | 3% | 5% | `prog_talent_swiftcounsel_pos_05` |

#### Heir's Reckoning

| Clause | Rank 1 | Rank 10 | Rank 20 | Progression row |
|---|---:|---:|---:|---|
| Weakened effect group trigger chance | 2% | 12% | 30% | `prog_talent_heirsreckoning_trig_01` |
| Instinct bonus with Nimble or Stalwart | 3% | 9% | 15% | `prog_talent_heirsreckoning_pos_01` |
| Post-combat tile durability damage bonus | 1% | 3% | 5% | `prog_talent_heirsreckoning_pos_02` |

## Limits for application use

The encyclopedia exposes these values as client-data reference, with a rank selector and links to the audit. The planner, counter picker and combat explorer do not score or simulate Commander effects, assignment, troop-capacity bonuses or commander reuse. The values are not enough by themselves to establish complete targeting, source-index semantics, current availability, or a battle model. User screenshots and current in-game values take precedence over this captured reference.
