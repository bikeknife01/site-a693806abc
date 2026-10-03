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

I’ll build the candidate ledger from canonical rules, roster evidence, and screenshot-audited dragon profiles only, explicitly excluding the strategist-evaluation tree.

The canonical roster contains 36 screenshot-audited default-eligible dragons; Meleys and Smoketail remain conditional-only because their current screenshots and resolved upgrade values are incomplete. I’m using the compact catalog to inspect all 36, then validating every retained high-damage line against exact profiles and Level-50 client curves.

The leading ledger line is an affinity-perfect Spearmen fire chain built around Caraxes’s documented First-Strike payoff. The remaining comparison is which eligible Spearmen support produces more Rank-6 damage than Tessarion, and whether a Cavalry/Archer producer-payoff line can outweigh that chain.

At Rank 6, Dawnseeker’s First-Strike Habit is locked, so it cannot anchor Caraxes; Syrax’s Command offers only a 20% chance. The stronger evidence-backed line is now the Shieldbearer Rising Tide core: Starshower supplies repeated Tactical-damage triggers, Moondancer converts them into multi-target Physical burst, and the third slot is being resolved between Shadowrend’s late-cycle team scaling and Malachite’s steadier trigger/Advantage support.

### Recommended Formation

**Formation troop type:** Shieldbearers

| Position | Dragon | Current Power | Star rank | Habit skill levels | Job |
|---|---|---:|---:|---|---|
| Left Flank | Starshower | Unknown | 6 | Unlocked Habits: 5/5/5 | High-frequency Tactical damage; Rising Tide producer |
| Vanguard | Moondancer | Unknown | 6 | Unlocked Habits: 5/5/5 | Multi-target Physical payoff |
| Right Flank | Shadowrend | Unknown | 6 | Unlocked Habits: 5/5/5 | Multi-target damage; late-cycle team amplification |

All three are assumed **Level 50**. This is the best-supported general-purpose high-damage formation under the stated equal-progression assumptions.

**Why it works:** Moondancer grants Crescent Blade to Starshower. Starshower’s scheduled Tactical attacks on Rounds 1, 3, 7, and 9—and its 50%-chance Solar Flare consumption—each provide opportunities for Crescent Blade’s 50%-chance Rising Tide trigger, capped at once per round. At Habit Level 5, Starshower’s Solar Flare hit has a **200% Tactical damage rate**. Moondancer independently has 50% Rising Tide chances on Rounds 1, 3, 5, 6, 8, and 10; its even-round attack hits two adjacent enemies at **120% Physical damage**, doubled after reaching four stacks. These stack gains are probabilistic, but the underlying scheduled attacks are guaranteed.

Shadowrend contributes Physical damage to two enemies on Rounds 4, 7, 9, and 10. More importantly, Midnight Aura raises all allies’ Strength and Instinct by **80% during Rounds 7–10**. Its 20%-chance Advantage trigger doubles to 40% during that window; if Moondancer receives Advantage, its specified Rising Tide chances double. Moondancer is the Vanguard because Warrior’s Zeal adds 16% to its high-volume Physical Command damage and gives Starshower, on the Left Flank, +20 Instinct and Initiative.

**Troop rationale:** Shieldbearers are affinity-perfect: all three have Positive Shieldbearer affinity. That maximizes affinity-derived stats for this trio without sacrificing its producer/payoff chain. The inherent caveat is that **Cavalry has troop advantage over Shieldbearers**.

**Gates and investment:** Rank 6 unlocks Starshower’s 200% Solar Flare damage, Moondancer’s Full Moon stack attempts and upgraded even-round damage, and Shadowrend’s Advantage support. Their 8- and 10-Star Habits receive no credit. The pivotal uncertainty is Rising Tide accumulation: four stacks are plausible but not guaranteed, so Moondancer’s doubled damage should be treated as upside rather than baseline.

**Combat horizon:** The formation already pressures early through Starshower on Rounds 1 and 3 and Moondancer on Rounds 2 and 4. It becomes substantially stronger from Round 7 onward when Midnight Aura boosts both Physical and Tactical attackers and Shadowrend’s Advantage chance doubles. The repository does not establish whether stacks and start-of-combat effects persist or reset across a Stalemate, so later 10-round cycles should not be modeled as guaranteed continuation of the first cycle’s stack state.

**Strongest credible alternative:** **Caraxes (Left Flank) / Syrax (Vanguard) / Tessarion (Right Flank), using Spearmen.** It is also affinity-perfect and offers steadier Fire pressure: Tessarion gives the prioritized Left Flank +20% Fire Damage, Syrax raises all allies’ Intelligence and Instinct by 13%, and Caraxes deals Fire damage to all three enemies on Rounds 3, 6, and 9. Syrax can grant First-Strike and +10% Fire Damage for two rounds, enabling Caraxes’s 1.5× Command payoff, but only at a 20% chance and with more than one Fire ally eligible for priority. This line becomes preferable if fights usually end before Shadowrend’s Rounds 7–10 scaling matters, or if Rising Tide repeatedly fails to reach four stacks.

**Risks:** Power is unknown, Rising Tide and Solar Flare consumption are chance-based, and Shadowrend is back-loaded. Starshower’s documented Tactical Breach UI conflict is irrelevant here because that Habit is locked until Rank 8. Meleys and Smoketail were not allowed to displace screenshot-audited candidates: they are user-confirmed available but remain conditional-only because exact current values and Habit upgrade tracks are incomplete.

**Evidence:** `data/dragons/moondancer.json -> command.verbatim, vanguard.verbatim, habits[0..2]`; `data/dragons/starshower.json -> command.verbatim, habits[2].upgrade_levels["5"]`; `data/dragons/shadowrend.json -> command.verbatim, habits[0].upgrade_levels["5"], habits[2]`; each dragon’s `troop_affinities.positive`; `data/game_mechanics.json -> troop_affinity, troop_types`; `data/installed_evidence.json -> observations[2026-10-01-season-3-availability]`.

