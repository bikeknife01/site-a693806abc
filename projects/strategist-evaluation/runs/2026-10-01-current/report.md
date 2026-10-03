# Dragonfire Strategist backtest

- Benchmark formation matches: 0/3
- Expert-rationale passes: 3/6
- Holdout passes: 3/3
- Missing responses: 0
- Overall: REVIEW REQUIRED

| Case | Formation | Expert rationale | Result |
|---|---:|---:|---:|
| `meta-high-damage` | mismatch | fail | FAIL |
| `meta-damage-survivability` | mismatch | fail | FAIL |
| `meta-cavalry-counter` | mismatch | fail | FAIL |
| `holdout-velar-five-stars` | n/a | pass | PASS |
| `holdout-vermithor-five-stars` | n/a | pass | PASS |
| `holdout-low-buff-spearmen` | n/a | pass | PASS |

## meta-high-damage

Parsed formation: `{"troop_type": "Shieldbearers", "left_flank": "Malachite", "vanguard": "Vhagar", "right_flank": "Moondancer"}`

- [x] Identifies the trio's shared Shieldbearer affinity (critical)
- [x] Uses Vhagar's directional Vanguard support (critical)
- [ ] Traces the Velar-to-Moondancer Rising Tide chain (critical)
- [ ] Treats the six-Star proc package as chance-based
- [x] Discloses Cavalry as the troop-cycle risk (critical)

## meta-damage-survivability

Parsed formation: `{"troop_type": "Shieldbearers", "left_flank": "Malachite", "vanguard": "Vhagar", "right_flank": "Moondancer"}`

- [ ] Identifies the trio's shared Spearmen affinity (critical)
- [x] Uses Vermithor's screenshot-audited Protect reliability (critical)
- [ ] Connects Rhysarion Recovery with Vermithor mitigation (critical)
- [ ] Explains why Rhysarion is Vanguard and Venator is Right Flank (critical)
- [ ] Discloses Archers as the troop-cycle risk (critical)

## meta-cavalry-counter

Parsed formation: `{"troop_type": "Cavalry", "left_flank": "Malachite", "vanguard": "Vermithor", "right_flank": "Arulix"}`

- [x] Uses Cavalry's troop advantage against Shieldbearers (critical)
- [ ] Attributes Seasmoke's removal to Cleansing Wrath (critical)
- [x] Treats Seasmoke's Cleanse as probabilistic rather than blanket removal (critical)
- [ ] Identifies Malachite sustain and Kalspire pressure (critical)
- [x] Explains Seasmoke Vanguard support for the Right Flank (critical)

## holdout-velar-five-stars

- [x] Removes six-Star Gales of Power credit (critical)
- [x] Retains the lower-Star Velar/Moondancer interaction (critical)

## holdout-vermithor-five-stars

- [x] Falls back to Vermithor's base Command values (critical)
- [x] Removes six-Star Bronze Bulwark credit (critical)
- [x] Does not retain Bronze Bulwark's on-Protect mitigation (critical)

## holdout-low-buff-spearmen

- [x] Recognizes Cavalry's disadvantage against Spearmen (critical)
- [x] Downgrades Seasmoke when there are few removable buffs (critical)
- [x] Rejects the benchmark formation as a universal default (critical)
