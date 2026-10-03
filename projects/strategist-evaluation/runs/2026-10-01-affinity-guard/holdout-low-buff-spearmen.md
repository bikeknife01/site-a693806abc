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

I’ll evaluate the trio only against canonical rules, mechanics, and dragon records, with the enemy constrained to Spearmen and no material positive-buff plan.

The decisive comparison is now troop-counter value versus the trio’s affinity-perfect Cavalry baseline; I’m checking the canonical counter catalog and caveats before finalizing that tradeoff.

**No.** Malachite Left / Seasmoke Vanguard / Kalspire Right with **Cavalry should not remain the default counter** under these assumptions. Spearmen have explicit troop advantage over Cavalry—dealing more damage while receiving less—and the opponent’s lack of material positive buffs removes much of Seasmoke’s counter-specific value.

### Better-supported configuration

**Formation troop type:** Archers

| Position | Dragon | Current Power | Star rank | Habit skill levels | Job |
|---|---|---:|---:|---|---|
| Left Flank | Malachite | Unknown | 6 | Unlocked Habits: 5/5/5 | Tactical damage, Recovery, support |
| Vanguard | Seasmoke | Unknown | 6 | Unlocked Habits: 5/5/5 | Scheduled hybrid damage, Panic payoff |
| Right Flank | Kalspire | Unknown | 6 | Unlocked Habits: 5/5/5 | Basic-Attack damage, Panic producer, stat suppression |

**Why it works:** Kalspire’s Level-5 Tactical Assault gives each Basic Attack a **30% chance** to apply Panic to its target and an adjacent enemy for two rounds. Seasmoke’s Round 3/6/9 Physical hit is doubled against affected targets, producing a legitimate but probabilistic producer/payoff chain. Kalspire also applies a Level-5, combat-long **-13% Strength and Intelligence** reduction to all three enemies. Malachite supplies scheduled Tactical damage and strong early Recovery, including its 6-Star increases on Rounds 1–2.

**Troop rationale:** Cavalry is the trio’s only affinity-perfect intersection, but it is explicitly disadvantaged against enemy Spearmen. Archers instead have troop advantage over Spearmen. Seasmoke has positive Archer affinity; Malachite and Kalspire do not receive positive Archer affinity, so this sacrifices two dragons’ affinity benefit for the direct formation-wide troop counter. Against known Spearmen, that is the stronger default assumption because troop advantage affects both damage dealt and received.

**Threat coverage and exclusions:** Seasmoke’s positive-effect Cleanse is not a meaningful counter if the enemy does not materially use positive buffs. Its Infectious Wrath stacks—and therefore its Recovery suppression—require successful enemy Cleanses, so that branch may contribute little or nothing here. The formation directly covers enemy Strength/Intelligence through Kalspire but cannot claim counters to any unspecified enemy Commands, damage schedules, control, Recovery, or targeting.

**Gates and investment:** At Rank 6, only each dragon’s 2-, 4-, and 6-Star Habits are active. Malachite lacks its 8-Star team Strength and 10-Star First-/Double-Strike support; Seasmoke lacks its 8-Star Fire support and 10-Star adaptive buff; Kalspire lacks its 8- and 10-Star personal mitigation. Consequently, this Rank-6 formation is less broadly defensive than its complete kit might suggest.

**Alternative check:** Cavalry would become preferable if affinity-derived performance outweighed the troop disadvantage—such as after changing away from an enemy Spearmen formation—or if the enemy’s actual dragons created a compelling Cavalry-specific mechanical answer. Neither condition is established here. Without the enemy dragons, this is a **troop-matchup adjustment, not a complete dragon-kit counter claim**.

**Evidence:** `data/game_mechanics.json -> troop_types`, `troop_combat.advantage`; `data/dragons/malachite.json -> troop_affinities`, `command.verbatim`, `habits[0..2]`; `data/dragons/seasmoke.json -> troop_affinities`, `command.verbatim`, `vanguard.verbatim`, `habits[2]`; `data/dragons/kalspire.json -> troop_affinities`, `command.verbatim`, `vanguard.verbatim`, `habits[1..2].upgrade_levels["5"]`.

