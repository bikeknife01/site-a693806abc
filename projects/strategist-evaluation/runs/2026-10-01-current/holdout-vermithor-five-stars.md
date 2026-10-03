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

I’ll compare the stated Rank 5/6/6 line against the all-Rank-6 version using only canonical rules, exact dragon text, affinity, unlock gates, and Level-5 Habit values.

The comparison turns on Vermithor’s Rank-6 gate, not the other two dragons: I’m checking the formation-level timing and catalog notes now so the verdict distinguishes lost mechanics from unchanged synergies.

### Recommended Formation

**Formation troop type:** Spearmen

| Position | Dragon | Current Power | Star rank | Habit skill levels | Job |
|---|---|---:|---:|---|---|
| Left Flank | Vermithor | Unknown | 5 | Noble Sacrifice 5; Nimble Resilience 5 | Mixed damage, early suppression, probabilistic Protect |
| Vanguard | Rhysarion | Unknown | 6 | Ebbing Fury 5; Sharp Resolve 5; Echoing Melody 5 | Recovery, opening suppression, Right-Flank amplification |
| Right Flank | Venator | Unknown | 6 | Hunter’s Bane 5; Dragon’s Might 5; Feral Precision 5 | Primary Physical pressure and least-troops finishing |

**Verdict:** The Rank-5 Vermithor version remains defensible as a general-purpose formation, but it is materially weaker than the all-Rank-6 version. It retains excellent Spearmen affinity, sustain, enemy suppression, and a coherent Rhysarion-to-Venator Vanguard link. It loses a substantial portion of Vermithor’s damage, Protect reliability, and self-mitigation, so this is no longer the fully realized version of the line.

**Exactly what changes from six Stars:** Only Vermithor’s eligible kit changes; Rhysarion and Venator remain unchanged.

| Vermithor mechanic | Rank 6, Habit 5 | Rank 5 | Difference |
|---|---:|---:|---:|
| Bronze Fury Physical rate on Rounds 2/4/6/8 | +45% | +30% | −15 percentage points; Rank 5 retains two-thirds of the Rank-6 rate |
| Bronze Fury Tactical rate on Rounds 2/4/6/8 | +90% | +60% | −30 percentage points; Rank 5 retains two-thirds of the Rank-6 rate |
| Protect chance on odd rounds | 50% | 30% | −20 percentage points, a 40% relative reliability reduction |
| Physical/Fire Damage Received after applying Protect | −10% for 2 rounds | None | Entire self-mitigation clause is lost |
| Bronze Bulwark | Unlocked at Habit 5 | Locked | All Rank-6 upgrades above are unavailable |
| Star-derived stats | Higher | Lower | Direction is established, but the final-stat formula does not support a precise numerical comparison |

Protect itself remains available at Rank 5: Bronze Fury still has a 30% chance on odd rounds to Protect the adjacent other ally with the least troops for two rounds. Protect splits **Command and Habit damage** between that ally and Vermithor; it does not cover Basic Attacks. Exact adjacency geometry is undocumented, so Venator must not be assumed to be a valid Protect target from the opposite flank.

**Why it works:** Rhysarion’s Vanguard ability gives Venator +8% Damage Dealt while improving Rhysarion’s own Recovery Dealt and Initiative. Venator then supplies reliable Basic-Attack-linked Physical pressure, two additional separately targeted +20% Physical instances after every Basic Attack, a guaranteed +40% least-troops hit after each Basic Attack at six Stars, and 50% Double-Strike opportunities on Rounds 4, 6, and 8. Rhysarion supplies +120% Recovery to two other allies on Rounds 2, 5, and 8, plus +50% team Recovery at the start of Round 4.

The opening is defensive: Rhysarion reduces **all allied and enemy Damage Dealt by 55% for Rounds 1–3**, while Vermithor reduces one enemy’s Physical Damage Dealt and one enemy’s Fire Damage Dealt by 15% for five rounds. Vermithor’s Noble Sacrifice is fully invested, so its nominal early Tactical-damage vulnerability is 0%. The formation then transitions toward Venator’s stronger Round-4/6/8 pressure.

A notable weakness is that the trio has no unlocked internal Control source. Rhysarion’s Fire damage therefore does not receive its 1.5× Control-target bonus under ordinary conditions. Venator’s Overwhelm is locked until Rank 10.

**Troop rationale:** Spearmen are Positive affinity for all three dragons, making this affinity-perfect and maximizing affinity-derived combat-stat benefits for this fixed trio. Spearmen also counter Cavalry but are disadvantaged against Archers. An Archer opponent is therefore the line’s inherent general-purpose troop-cycle weakness.

**Combat horizon:** Rank-5 Vermithor most noticeably weakens the even-round offense and odd-round protection during the opening ten rounds. Rhysarion’s Recovery and Venator’s later-round Attack Modifier pressure still give the formation a credible sustained profile if combat continues through a Stalemate. Compared with the six-Star version, however, Vermithor is less able to absorb Command/Habit damage redirected by Protect, because the −10% Physical/Fire mitigation following a successful Protect is gone.

**Risks:** Power is unknown, so current account viability cannot be compared against replacement dragons. The line also lacks Cleanse, guaranteed control, and internally enabled Control payoff. Vermithor’s Protect is only a 30% proc and does not cover Basic Attacks; its exact reachable targets depend on undocumented adjacency geometry.

**Alternative check:** Against the otherwise identical all-Rank-6 formation, the six-Star version is clearly superior: nothing is traded away, and Vermithor gains stronger mixed damage, 20 percentage points more Protect reliability, self-mitigation after successful Protect, and higher Star progression. Rank 5 remains defensible because Rhysarion and Venator still carry the formation’s sustain and focused offense, but upgrading Vermithor to Rank 6 is the most important improvement to this exact line.

**Evidence:** `data/dragons/vermithor.json -> command.verbatim`, `habits[0..2]`, `troop_affinities`, and `review`; `data/dragons/rhysarion.json -> command.verbatim`, `vanguard.verbatim`, `habits[0..2]`, and `troop_affinities`; `data/dragons/venator.json -> command.verbatim`, `habits[0..2]`, and `troop_affinities`; `data/effects.json -> Protect`; `data/game_mechanics.json -> troop_affinity`, `troop_types`, and `progression.star_rank`.

