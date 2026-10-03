# Dragonfire Strategist backtest

- Benchmark formation matches: 0/1
- Expert-rationale passes: 1/2
- Holdout passes: 1/1
- Missing responses: 0
- Overall: REVIEW REQUIRED

| Case | Formation | Expert rationale | Result |
|---|---:|---:|---:|
| `meta-high-damage` | mismatch | fail | FAIL |
| `holdout-low-buff-spearmen` | n/a | pass | PASS |

## meta-high-damage

Parsed formation: `{"troop_type": "Shieldbearers", "left_flank": "Starshower", "vanguard": "Moondancer", "right_flank": "Shadowrend"}`

- [x] Identifies the trio's shared Shieldbearer affinity (critical)
- [ ] Uses Vhagar's directional Vanguard support (critical)
- [ ] Traces the Velar-to-Moondancer Rising Tide chain (critical)
- [ ] Treats the six-Star proc package as chance-based
- [x] Discloses Cavalry as the troop-cycle risk (critical)

## holdout-low-buff-spearmen

- [x] Recognizes Cavalry's disadvantage against Spearmen (critical)
- [x] Downgrades Seasmoke when there are few removable buffs (critical)
- [x] Rejects the benchmark formation as a universal default (critical)
