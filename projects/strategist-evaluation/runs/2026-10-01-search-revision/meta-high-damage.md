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

I’ll apply the canonical decision contract, build the Level 50/Rank 6 candidate ledger from eligible live roster data, and compare all legal lane orders and shared troop choices without accessing the evaluation project.

The eligibility boundary is clear: the 36 screenshot-audited canonical profiles are default-eligible; Meleys and Smoketail remain conditional-only because their resolved values and Habit tracks are incomplete. I’m now comparing every audited profile at Rank 6, including Level-5 values for the first three Habits.

The leading comparison has narrowed to an affinity-perfect Spearmen/Cavalry fire-control line built around Caraxes and Tairax, versus an affinity-perfect Archers Panic line built around Zivern, Daemoros, and Seasmoke. The deciding check is whether Syrax’s Rank-6 support and First-Strike chain outweigh a third independent damage dealer, and which lane order preserves the most reliable opening and sustained output.

### Recommended Formation

**Best-supported under the stated assumptions:** **Tairax / Caraxes / Tessarion**  
**Formation troop type:** **Cavalry**

| Position | Dragon | Current Power | Star rank | Habit skill levels | Job |
|---|---|---:|---:|---|---|
| Left Flank | Tairax | Unknown | 6 | 5 / 5 / 5 | Control producer, recurring Fire payoff |
| Vanguard | Caraxes | Unknown | 6 | 5 / 5 / 5 | Multi-target Fire burst |
| Right Flank | Tessarion | Unknown | 6 | 5 / 5 / 5 | Hybrid damage, guaranteed Fire support |

**Why it works:** This lane order activates two guaranteed offensive boosts. Caraxes gains **+16% Fire Damage Dealt** from Vanguard, while Tessarion gives the Left Flank Tairax **+20% Fire Damage Dealt for the entire combat**. Caraxes also gives right-flank Tessarion +20 Strength and Initiative. At Habit 5, Caraxes carries a permanent **+25% self Fire boost**; Tairax has a **50% Stagger check on every odd round**, increases controlled enemies’ Damage Received by **+15%**, and deals **40% Fire damage each round** to every controlled enemy. These are explicit mechanics, although the Stagger chain remains probabilistic.

The damage schedule is unusually dense: Tessarion attacks on rounds **1/3/4/6/7/9**, Tairax’s primary Fire strike occurs on **2/5/8** with a 50% Burn chance, Caraxes hits all three enemies on **3/6/9**, and Tairax can add its control-payoff damage every round. Tessarion also has a 50% odd-round chance to raise its own Fire damage while mitigating allied non-Basic Physical damage.

**Troop rationale:** All three have Positive Cavalry affinity, making this affinity-perfect. **Spearmen are also affinity-perfect for exactly this trio**, so Cavalry is a declared general-purpose default rather than intrinsically superior. Cavalry pressures Shieldbearers but is disadvantaged against Spearmen; switch the shared troop type to Spearmen if Cavalry opposition is expected, accepting disadvantage against Archers.

**Gates and investment:** Rank 6 is pivotal. It unlocks Caraxes’s multi-target Slow/Burn Habit at **20% per effect per target**, Tairax’s **50% Stagger plus 40% control-payoff damage**, and Tessarion’s 50% odd-round Molten Armor trigger. All Vanguards are active at Level 50. Caraxes’s First-Strike multiplier is not credited because this formation does not provide First-Strike.

**Combat horizon:** Opening pressure starts with Tessarion’s permanent buff to Tairax, Caraxes’s permanent +25% self Fire bonus, Tairax’s same-lane Strength/Initiative reduction, and the first Stagger check. Round 6 is especially strong: Caraxes and Tessarion both attack, while Tairax begins its +32% Intelligence/Initiative phase. The recurring 10-round schedules remain valuable in prolonged combat, but the repository does not establish whether “Start of Combat” effects reapply or stacks reset after each Stalemate, so no such reset is assumed.

### Strongest Credible Alternative

**Archers — Left Flank Zivern / Vanguard Daemoros / Right Flank Seasmoke**

This is the strongest explicit alternative engine. Zivern has a **60% odd-round chance** to afflict all enemies with Panic, while Daemoros has a **50% each-round Panic trigger** against one target. Seasmoke then doubles its scheduled Physical component against enemies with Panic, alongside its 190% same-lane Fire strike. Daemoros’s Vanguard grants its own Physical damage +16% and gives left-flank Zivern Instinct and Initiative, directly supporting Zivern’s Tactical output. All three have Positive Archer affinity.

It ranks slightly lower because its best payoff depends on Panic being present on Seasmoke’s scheduled rounds, whereas the recommended formation has stronger guaranteed full-combat Fire boosts and broader scheduled damage before its probabilistic Stagger payoff is counted. The alternative becomes preferable if Panic consistently lands before Seasmoke’s rounds 3/6/9 attacks or if the opponent uses Spearmen, which Archers counter while Cavalry does not.

**Risks:** Visible Power, account modifiers, enemy troop type, and the hidden damage formula are unknown. Those inputs could reverse a close result. Meleys and Smoketail were not default-eligible: their availability is confirmed, but their screenshot-complete values and Habit upgrade tracks remain incomplete.

**Evidence:**

- `data/dragons/caraxes.json -> command.verbatim`, `vanguard.verbatim`, `habits[1].upgrade_levels["5"]`, `habits[2].upgrade_levels["5"]`
- `data/dragons/tairax.json -> command.verbatim`, `habits[1].upgrade_levels["5"]`, `habits[2].upgrade_levels["5"]`
- `data/dragons/tessarion.json -> command.verbatim`, `habits[1].upgrade_levels["5"]`, `habits[2].upgrade_levels["5"]`
- `data/dragons/zivern.json -> command.verbatim`, `habits[2].upgrade_levels["5"]`
- `data/dragons/daemoros.json -> command.verbatim`, `vanguard.verbatim`, `habits[0].upgrade_levels["5"]`
- `data/dragons/seasmoke.json -> command.verbatim`, `habits[2].upgrade_levels["5"]`
- `data/game_mechanics.json -> troop_affinity`, `troop_types`, `combat_lifecycle`
- `data/installed_evidence.json -> observations[2026-10-01-season-3-availability]`

