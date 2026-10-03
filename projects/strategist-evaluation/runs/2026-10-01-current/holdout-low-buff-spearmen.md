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

I’ll evaluate the trio strictly from canonical mechanics and screenshot-audited dragon records, without accessing the excluded evaluation project.

### Evaluation

**No.** Malachite Left Flank, Seasmoke Vanguard, and Kalspire Right Flank **with Cavalry should not remain the default counter** against a Spearmen opponent that does not materially rely on positive buffs.

| Position | Dragon | Power | Star rank | Unlocked Habits | Job |
|---|---|---:|---:|---|---|
| Left Flank | Malachite | Unknown | 6 | First three, Level 5 | Recovery, Tactical damage, team support |
| Vanguard | Seasmoke | Unknown | 6 | First three, Level 5 | Fire damage, conditional cleansing, Panic payoff |
| Right Flank | Kalspire | Unknown | 6 | First three, Level 5 | Basic-Attack damage, Panic, enemy stat reduction |

**Formation troop type:** Prefer **Archers**, not Cavalry, for this matchup.

**Why Cavalry loses default status:** Cavalry is affinity-perfect for this trio, but Spearmen have direct troop advantage over Cavalry: they deal more damage and receive less in return. Archers instead counter Spearmen. Malachite and Kalspire have no recorded Archer penalty, while Seasmoke has positive Archer affinity. Therefore, the matchup advantage of Archers is the better-supported counter choice despite surrendering Malachite’s and Kalspire’s positive Cavalry affinity. Exact modifier sizes are unpublished, so the net margin cannot be quantified.

**Why the trio itself is less compelling:** Seasmoke’s counter value is substantially reduced when the enemy does not depend on positive effects. Infectious Wrath stacks—and their Level-5 **−30% Recovery Received per stack**—require Seasmoke actually to Cleanse an enemy. With few relevant buffs available, that counter chain may not operate. Seasmoke still contributes scheduled Fire damage, team Initiative, Vanguard mitigation for Kalspire, and a Panic payoff, but it is no longer a broadly applicable anti-buff counter.

Kalspire provides the remaining explicit synergy: at Habit Level 5, each Basic Attack adds Tactical damage, **50% Physical damage** to an adjacent enemy, and has a **30% chance** to afflict Panic on the target and an adjacent enemy. Seasmoke’s scheduled Physical damage on Rounds 3, 6, and 9 is doubled against targets afflicted with Panic. That chain is useful but probabilistic; it does not override Cavalry’s unfavorable troop matchup.

**Placement:** The stated lanes remain defensible. Seasmoke and Kalspire have the same Vanguard ability, and Seasmoke Vanguard grants Kalspire on the Right Flank **−8% Damage Received** while increasing Seasmoke’s own Strength, Intelligence, and Instinct. Malachite’s Vanguard instead benefits a Fire-damage Left Flank ally, which this arrangement does not provide.

**Combat horizon:** Malachite supplies strong opening Recovery on Round 2 and enhanced Tactical damage on Rounds 1–2 at 6 Stars. Kalspire pressures every round through Basic Attacks, while Seasmoke’s direct attacks occur on Rounds 3, 6, and 9. These schedules repeat in later combat cycles, but running Cavalry into Spearmen remains a persistent formation-wide liability throughout the fight.

**Verdict:** Retain this exact trio only as a **conditional mechanics line**, preferably using **Archers** against Spearmen. Do not retain the **Cavalry version** as the default counter, and do not describe Seasmoke as a hard counter when the opponent supplies few positive effects. Unknown Power is the largest unresolved viability input; materially different player-specific Power could justify using the trio, but it would not change Cavalry’s unfavorable troop-cycle relationship.

**Evidence:** `data/game_mechanics.json -> troop_types`, `troop_combat.advantage`; `data/dragons/malachite.json -> troop_affinities`, `command.verbatim`, `habits[2]`; `data/dragons/seasmoke.json -> command.verbatim`, `vanguard.verbatim`, `habits[2].upgrade_levels["5"]`; `data/dragons/kalspire.json -> command.verbatim`, `habits[2].upgrade_levels["5"]`. All three dragon records have empty `review` arrays.

