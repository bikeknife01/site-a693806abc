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

I’ll derive the recommendation strictly from the canonical rules, roster evidence, and dragon profiles, excluding the evaluation project entirely.

The roster contains 36 screenshot-audited dragons plus two Season 3 dragons whose exact current values remain incomplete; I’ll rank the audited roster first and treat incomplete client-derived candidates only if their evidence can support the same comparison standard.

The leading archetypes are now clear: a Sentinel-fed Moondancer damage engine, a First-Strike/Caraxes burst line, a Panic-payoff fire line, and a Physical-vulnerability line. I’m checking their exact Rank-6 gates, level-50 stats, affinities, and Vanguard interactions before selecting one.

### Recommended Formation

**Best-supported general-purpose high-damage formation:** **Malachite / Vhagar / Moondancer**  
**Formation troop type:** **Shieldbearers** — affinity-perfect

| Position | Dragon | Current Power | Star rank | Habit skill levels | Job |
|---|---|---:|---:|---|---|
| Left Flank | Malachite | Unknown | 6 | 2★/4★/6★: Level 5 | Tactical burst, Recovery, Advantage and Physical support |
| Vanguard | Vhagar | Unknown | 6 | 2★/4★/6★: Level 5 | Durable control, Physical damage, formation amplifier |
| Right Flank | Moondancer | Unknown | 6 | 2★/4★/6★: Level 5 | Primary scaling Physical-damage carry |

**Why it works:** This is the strongest explicit producer-to-payoff chain at the stated progression. Moondancer guarantees **Crescent Blade** to Malachite—the formation’s only other Sentinel—so Malachite’s Tactical Damage and Recovery can attempt to generate Rising Tide without target ambiguity. At Habit Level 5, Moondancer independently has a 50% Rising Tide chance on Rounds 1/3/5 and 6/8/10; Advantage doubles those checks. Malachite supplies Advantage to both allies at a 20% activation chance each round, while Vhagar can supply Advantage to the ally with the most troops at 35% on Rounds 3–7.

The lane arrangement adds two direct, reliable damage links:

- Vhagar’s Level-5 **Battle Leader** gives the prioritized Right Flank—Moondancer—**+25% non-Basic Physical Damage for the entire combat**.
- Vhagar’s Vanguard ability gives Left-Flank Malachite **+16% Tactical Damage**, strengthening both Malachite’s output and the Tactical events that feed Moondancer.
- Malachite has a 35% chance each round to give both other dragons **+16% non-Basic Physical Damage** for two rounds.
- Moondancer’s Level-5 **Full Moon** raises its even-round Physical attack to **+120% against two adjacent enemies**, doubled with four Rising Tide stacks. Vhagar adds a +120% Physical hit on every even round, while Malachite supplies strong opening Tactical hits and Recovery.

These are sourced mechanics; judging this as the best overall trio is derived analysis.

**Troop rationale:** Shieldbearers have Positive affinity for all three dragons, making this affinity-perfect. They maximize affinity-derived combat stats for the fixed trio without sacrificing the core synergy. Shieldbearers have troop advantage over Archers but are disadvantaged against Cavalry, which is the formation’s principal generic troop-cycle weakness.

**Gates and investment:** All pivotal mechanics are active at Level 50 and Rank 6. The formation does not rely on any 8-Star or 10-Star Habit. The important Level-5 values are Moondancer’s 50% scheduled Rising Tide checks and +120% Full Moon damage, Malachite’s +16% Physical support and 20% Advantage chance, and Vhagar’s permanent +25% Right-Flank Physical support plus 35% Eclipse Cover chance. Advantage support is probabilistic; Crescent Blade’s Sentinel assignment and Vhagar’s Battle Leader are unconditional, while Rising Tide generation remains chance-based.

**Combat horizon:** Opening damage is immediate: Malachite receives the Vanguard Tactical bonus, Moondancer receives Vhagar’s permanent Physical bonus, and Malachite’s Rank-6 Command has its enhanced Rounds 1–2 burst. The line becomes more dangerous as Rising Tide accumulates; reaching four stacks doubles Moondancer’s recurring even-round damage. Malachite’s Recovery and Vhagar’s opening mitigation/Taunt pressure make that ramp more credible than a fragile all-offense line. Rising Tide lasts until combat ends, so sustained combat favors this formation, although the repository does not establish hidden proc order or guarantee when four stacks will be reached.

### Strongest Credible Alternative

**Malachite — Moondancer — Starshower**, using **Shieldbearers**:

| Position | Dragon | Star rank | Job |
|---|---|---:|---|
| Left Flank | Malachite | 6 | Tactical burst, Recovery, Advantage |
| Vanguard | Moondancer | 6 | Scaling Physical carry |
| Right Flank | Starshower | 6 | High-ceiling Tactical burst, Cleanse/Evade support |

This alternative is also affinity-perfect and has the higher Tactical burst ceiling. Starshower has a 50% per-round chance to consume Solar Flare for a **+200% Tactical hit**, plus guaranteed +80% same-lane hits on Rounds 1/3/7/9. Both Sentinels can feed Crescent Blade through Tactical Damage or Recovery, although Moondancer’s initial Sentinel recipient is no longer deterministic. It ranks slightly lower for general use because Starshower’s largest damage is proc- and mark-dependent, while the recommended line gives Moondancer a guaranteed permanent +25% Physical amplifier and adds Vhagar’s durability, Taunt, and Weakened pressure.

The choice reverses if Tactical burst and probabilistic Cleanse are more valuable than Vhagar’s reliable Moondancer amplification and frontline control—for example, against an opponent especially vulnerable to Tactical Damage.

**Risks:** Visible Power and account-wide Stronghold, Heirloom, Realm, and Campaign modifiers are unknown. Cavalry troops counter the selected Shieldbearers. Meleys and Smoketail were not allowed to displace screenshot-audited candidates: they are user-confirmed available, but their current mechanics, resolved numeric values, Star gates, and Habit upgrade tracks remain incomplete and are restricted to conditional use.

**Evidence:**

- `data/dragons/moondancer.json -> command.verbatim`, `vanguard.verbatim`, `habits[0..2].verbatim`, `habits[0..2].upgrade_levels["5"]`, `troop_affinities`
- `data/dragons/vhagar.json -> command.verbatim`, `vanguard.verbatim`, `habits[0..2].verbatim`, `habits[1..2].upgrade_levels["5"]`, `troop_affinities`
- `data/dragons/malachite.json -> command.verbatim`, `vanguard.verbatim`, `habits[0..2].verbatim`, `habits[0..2].upgrade_levels["5"]`, `troop_affinities`
- `data/dragons/starshower.json -> command.verbatim`, `habits[0..2]`, `troop_affinities`
- `data/game_mechanics.json -> troop_affinity`, `troop_types.Shieldbearers`, `combat_lifecycle`
- `data/installed_evidence.json -> observations[id=2026-10-01-season-3-availability]`

