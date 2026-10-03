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

I’ll evaluate only the canonical rules, mechanics, and the three dragon profiles, with the Star-rank change traced ability by ability.

The key downgrade is isolated to Velar’s Rank-6 gate, but I’m checking the client progression record before calling it “only one Habit”: Star Rank also changes stats independently of unlocks, and the repository does not expose a complete final-stat formula.

### Recommended Formation

**Formation troop type:** Shieldbearers

| Position | Dragon | Current Power | Star rank | Habit skill levels | Job |
|---|---|---:|---:|---|---|
| Left Flank | Velar | Unknown | 5 | Strategic Leader 5; Quick Reflexes 5 | Tactical damage, Advantage support, Moondancer enabler |
| Vanguard | Vhagar | Unknown | 6 | Ancestral Shield 5; Battle Leader 5; Eclipse Cover 5 | Durable anchor, Taunt, mitigation, flank amplification |
| Right Flank | Moondancer | Unknown | 6 | New Moon 5; Reactive Instincts 5; Full Moon 5 | Scaling Physical damage, Rising Tide payoff |

**Verdict:** This remains a defensible general-purpose line, but it is materially less controlling than the six-Star Velar version. Its central Velar → Moondancer synergy and Vhagar’s placement benefits remain intact; what disappears is Velar’s entire First-Strike/Slow layer plus some Star-scaled stats.

**Why it works:** Vhagar is the correct Vanguard. Warrior’s Resilience gives Vhagar guaranteed `-8%` Damage Received and Velar, specifically in the Left Flank, `+16%` Tactical Damage Dealt. Vhagar’s Level-5 Battle Leader gives the Right Flank—Moondancer—`+25%` non-Basic Physical Damage Dealt until combat ends.

Velar is a Sentinel who deals Tactical Damage on Rounds 3, 5, 7, and 9. Crescent Blade therefore gives each of those attacks a 50% chance to add one Rising Tide stack to Moondancer, capped at one stack per round. At Habit Level 5, Moondancer also has a 50% Rising Tide chance on Rounds 1, 3, and 5, doubled to 100% when an ally has Advantage. Velar can provide Advantage to both other allies on Rounds 2, 4, 6, and 8, but only when Whirlwind’s fixed 20% trigger succeeds. Vhagar’s Level-5 Eclipse Cover supplies another possible Advantage source at 35% on Rounds 3–7, although it targets the ally with the most troops and therefore is not guaranteed to select Moondancer.

At six Stars and Habit Level 5, Moondancer’s Full Moon adds its late-round Rising Tide attempts at 50% on Rounds 6, 8, and 10—doubled by allied Advantage—and raises Crescent Blade’s Physical Damage rate to `+120%`, doubled to `+240%` at four or more Rising Tide stacks. This makes the formation strongest once Moondancer reaches that threshold.

**Exactly what changes from six-Star Velar:**

- **Gales of Power becomes locked.** The six-Star, Level-5 version independently checks every target on Rounds 2, 4, 6, and 8 for a 24% chance to grant each ally First-Strike and a separate 24% chance to afflict each enemy with Slow, each lasting two rounds. At five Stars, all of those checks disappear. This is the only ability unlock lost.
- **Velar’s Epic combat-stat scalar decreases:** Strength, Intelligence, Instinct, and Initiative move from the Rank-6 client scalar `0.75` to the Rank-5 scalar `0.60`. The repository does not establish the formula that converts those scalars into final displayed stats, so this cannot safely be described as a specific percentage reduction.
- **Velar’s maximum-army-size scalar does not change:** both Rank 5 and Rank 6 use `0.30`.
- **Nothing else changes mechanically:** Whirlwind retains its Advantage and Tactical-damage schedules; Strategic Leader remains Level 5 (`+20%` Tactical Damage to the prioritized Vanguard); Quick Reflexes remains Level 5 (`+32%` Instinct and Initiative); Velar remains a Sentinel for Crescent Blade; Vhagar’s Vanguard benefit still reaches Velar; and Shieldbearer affinity remains unchanged.
- **No Recovery or Cleanse was lost in this downgrade.** Those parts of Whirlwind require ten Stars, so neither the five- nor six-Star version has them.

**Troop rationale:** Shieldbearers are affinity-perfect: all three dragons have Positive Shieldbearer affinity and none has a negative affinity to it. That maximizes affinity-derived combat-stat benefit for this fixed trio. Shieldbearers have troop advantage over Archers but are disadvantaged against Cavalry, the line’s inherent general-purpose matchup caveat.

**Combat horizon:** The opening cycle has strong Vhagar durability—Level-5 Ancestral Shield reduces his Physical and Tactical Damage Received by `-24%` for Rounds 1–3, in addition to his Vanguard reduction—and persistent amplification for Moondancer. The formation scales as Rising Tide accumulates, especially from Round 6 onward. Compared with six-Star Velar, however, it has no First-Strike/Slow pressure during Rounds 2–9. It also has no Recovery or Cleanse, so sustained fights against damage-over-time, control, or dedicated sustain become less attractive.

**Risks:** Vhagar has no Burn supplier here, so Fiery Bonds remains a 25% Taunt chance rather than its doubled chance against Burned targets. Moondancer’s stack generation is chance-based and partly depends on Advantage or troop-count conditions. Power is unknown, so this is a kit-and-synergy judgment rather than proof that the trio is currently stronger than higher-Power alternatives.

**Bottom line:** Keep the formation if the goal is an affinity-perfect Shieldbearer hybrid with a durable Vanguard and Moondancer scaling. Five-Star Velar does not break its primary damage chain. The line is nevertheless a clear downgrade from the six-Star version because broad turn-order control goes from four scheduled sets of independent 24% checks to none. That loss makes it **defensible, not confidently optimal**, for general use.

**Evidence:** `data/dragons/velar.json -> command.verbatim, vanguard.verbatim, habits[0..2], troop_affinities`; `data/dragons/vhagar.json -> command.verbatim, vanguard.verbatim, habits[0..2].upgrade_levels["5"]`; `data/dragons/moondancer.json -> command.verbatim, habits[0..2].upgrade_levels["5"]`; `data/dragon_application_knowledge.json -> dragons[name=Velar].level_model.star_scalars`; `data/game_mechanics.json -> troop_affinity, troop_types, damage_types`.

