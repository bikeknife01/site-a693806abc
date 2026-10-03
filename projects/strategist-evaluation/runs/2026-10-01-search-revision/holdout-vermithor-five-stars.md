🧠 Open Brain is active. Quick reference:

CAPTURE       "Remember that...", "Save this...", "Note that..."
              → capture_thought (auto-routes people, actions, interactions)

SEARCH        "What do I know about...", "Have I captured anything on..."
              → search_thoughts (semantic similarity search)

REVIEW        "Show recent thoughts", "What have I captured lately?"
              → list_thoughts / thought_stats

GRAPH         "How is X related to Y?", "What connects to..."
              → ob-graph tools (create_node, traverse, find_path)

SESSION END   "wrap up", "park this", "goodnight", "done for today"
              → auto-capture protocol (saves ACT NOW items + session summary)

I’ll assess only the canonical rules, mechanics, and the three audited dragon profiles, excluding the blind-evaluation directory entirely.

The decisive comparison is Vermithor’s Rank-5 gate: I’m checking the compact catalog and placement guidance to separate that loss from the unchanged Rank-6 Rhysarion/Venator mechanics.

### Recommended Formation

**Formation troop type:** Spearmen

| Position | Dragon | Current Power | Star rank | Habit skill levels | Job |
|---|---|---:|---:|---|---|
| Left Flank | Vermithor | Unknown | 5 | Noble Sacrifice 5; Nimble Resilience 5 | Early suppression, hybrid damage, probabilistic Protect |
| Vanguard | Rhysarion | Unknown | 6 | Ebbing Fury 5; Sharp Resolve 5; Echoing Melody 5 | Recovery, opening suppression, hybrid damage |
| Right Flank | Venator | Unknown | 6 | Hunter’s Bane 5; Dragon’s Might 5; Feral Precision 5 | Primary sustained Physical damage and finishing pressure |

**Verdict:** This remains a defensible general-purpose hybrid, but Vermithor’s drop from Rank 6 to Rank 5 is a material downgrade. It retains sustain, suppression, affinity-perfect Spearmen, and Venator’s damage engine, but loses much of the six-Star line’s protection reliability and Vermithor damage. With Power unknown, it is supportable rather than demonstrably optimal.

### Exactly What Changes from the Six-Star Version

Only Vermithor’s eligible kit changes; Rhysarion and Venator remain at Rank 6.

| Vermithor mechanic | Six Stars, Habit 5 | Five Stars | Loss |
|---|---:|---:|---:|
| Bronze Fury Physical rate on Rounds 2/4/6/8 | +45% | +30% | 15 percentage points; one-third lower |
| Bronze Fury Tactical rate on Rounds 2/4/6/8 | +90% | +60% | 30 percentage points; one-third lower |
| Protect chance on odd rounds | 50% | 30% | 20 percentage points |
| Self Physical/Fire mitigation after applying Protect | -10% for 2 rounds | None | Entire clause is lost |
| Bronze Bulwark Habit | Unlocked at skill 5 | Locked | All upgrades above are unavailable |
| Star-derived stats | Rank-6 scaling | Rank-5 scaling | Lower, but the final-stat difference cannot be quantified from canonical evidence |

The base Protect attempt remains: on odd rounds Vermithor has a 30% chance to Protect the eligible adjacent ally with the least troops for two rounds. Protect splits **Command and Habit damage** between the protected target and Vermithor; it does not cover Basic Attacks. Because repository mechanics do not formally define adjacency geometry, Venator’s eligibility from the opposite flank should not be assumed.

Vermithor’s first two Habits remain fully effective. Noble Sacrifice at skill 5 has **no Tactical-damage-received penalty**, while reducing one prioritized Physical dealer and one prioritized Fire dealer by 15% for Rounds 1–5. Nimble Resilience still gives Vermithor -12% Damage Received and +24% Initiative for the combat.

### Why It Still Works

- **Guaranteed opening suppression:** Rhysarion reduces all enemies’ and allies’ Damage Dealt by 55% for the first three rounds. Vermithor simultaneously suppresses a prioritized Physical and Fire dealer by 15% for five rounds.
- **Strong sustain:** Rhysarion recovers two other allies on Rounds 2, 5, and 8 at +120%, enhanced by Intelligence. At the start of Round 4, Ebbing Fury also applies +50% Recovery to all three allies.
- **Venator remains intact:** Every Basic Attack produces two separate +20% Physical-damage instances. At Rank 6 it also deals +40% Physical damage to the least-troop enemy after each Basic Attack, with a 50% Double-Strike chance on Rounds 4, 6, and 8.
- **Useful Vanguard placement:** Rhysarion gains +15% Recovery Dealt and +25 Initiative, while Venator receives +8% Damage Dealt in the Right Flank. That supports both halves of the formation’s sustain-and-damage plan.
- **Affinity-perfect troops:** All three have Positive Spearmen affinity, maximizing affinity-derived stats for this fixed trio.

The synergy is complementary rather than a complete producer/payoff chain. This formation has no Control source, so it cannot reliably activate Rhysarion’s 1.5× Fire-damage condition. That is its largest offensive gap.

### Combat Horizon

Rounds 1–3 are deliberately defensive: Rhysarion’s -55% Damage Dealt affects the formation too, depressing Vermithor’s Round-2 attack and the opening damage from Rhysarion and Venator. The line becomes substantially more dangerous from Round 4, when the suppression expires, Rhysarion supplies team Recovery, Vermithor and Rhysarion attack together, and Venator begins its 50% Double-Strike windows.

In later cycles, the scheduled Commands and Recovery repeat. Rank-5 Vermithor is less reliable in sustained fighting because Protect triggers only at 30% and no longer grants the accompanying Physical/Fire mitigation. The line therefore depends more heavily on Rhysarion’s Recovery than the six-Star version did.

### Risks

- Spearmen are disadvantaged against Archers, although they counter Cavalry.
- No Cleanse, Resistance, or reliable Control is present.
- Vermithor’s Protect is chance-based, adjacency-limited, and excludes Basic Attacks.
- The trio does not supply the Control needed for Rhysarion’s enhanced Fire hit.
- Unknown Power and account modifiers prevent a definitive comparison against other available formations.

For this balanced placement, Rank-5 Vermithor does **not** invalidate the line, but it changes Vermithor from a relatively dependable protector/damage contributor into a suppression tank with unreliable protection. If the objective becomes pure offense, Venator Vanguard is a credible lane-order alternative; if stronger protection is required, Vermithor Vanguard can give the Right Flank -8% Damage Received. Rhysarion Vanguard remains the best-supported general-purpose compromise because it improves both team sustain and Venator’s damage.

**Evidence:** `data/dragons/vermithor.json -> command.verbatim`, `habits[0-2]`, `vanguard.verbatim`; `data/dragons/rhysarion.json -> command.verbatim`, `habits[0-2]`, `vanguard.verbatim`; `data/dragons/venator.json -> command.verbatim`, `habits[0-2]`; `data/effects.json -> Protect`; `data/game_mechanics.json -> troop_affinity`, `troop_types`, and `combat_lifecycle`.

