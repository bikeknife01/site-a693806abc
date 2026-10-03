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

I’ll reconstruct the enemy’s Rank 6 threat instances, then compare full-roster counter lines under the canonical decision contract while excluding the evaluation project entirely.

The enemy threat mix spans Basic Attacks, non-Basic Physical damage, Tactical/Recovery-driven Rising Tide, buffs, debuffs, and likely lane-specific pressure. I’m narrowing only after checking the complete canonical catalog, then I’ll verify exact text for the enemy and retained finalists.

The full-roster catalog points to a Cavalry counter shell because it gains troop advantage over Shieldbearers and includes explicit answers to both Warriors’ non-Basic Physical pressure. The deciding comparison is between broader guaranteed/conditional mitigation and more aggressive control or buff-removal coverage.

A broader catalog check surfaced one potentially stronger specialist than the initial Cavalry-perfect shell: Arrax has explicit team Tactical mitigation, which may cover Velar’s formation-wide Tactical hits more reliably than Malachite’s proc-based protection. I’m resolving that specialist against the sustain line before finalizing.

### Recommended Formation

**Best-supported counter:** Cavalry, exploiting troop advantage over enemy Shieldbearers.

| Position | Dragon | Current Power | Star rank | Habit skill levels | Job |
|---|---|---:|---:|---|---|
| Left Flank | Tessarion | Unknown | 6 | Unlocked Habits: 5 | Physical suppression, anti-Physical mitigation |
| Vanguard | Malachite | Unknown | 6 | Unlocked Habits: 5 | Recovery, Tactical mitigation, Fire support |
| Right Flank | Feskar | Unknown | 6 | Unlocked Habits: 5 | Non-Basic Physical mitigation, Physical-dealer punishment |

**Why it works:** This is an affinity-perfect Cavalry trio, so every dragon receives positive affinity while Cavalry also deals increased damage to Shieldbearers and receives reduced damage from them. Malachite’s Vanguard grants enhanced Recovery and supports Tessarion’s Fire damage; Tessarion prioritizes enemies dealing non-Basic Physical damage, while Feskar both mitigates and attacks that exact category. All three Commands are Active, so Vhagar’s Taunt redirects their Basic Attacks but does not prevent these Commands or Habits.

The matchup’s central danger is Moondancer’s Rising Tide engine: Velar supplies Tactical actions and possible Advantage, Vhagar buffs Moondancer’s non-Basic Physical damage, and Moondancer can double Crescent Blade after four stacks. This formation attacks that engine indirectly by reducing Physical output, mitigating its damage, sustaining through the opening, and applying troop advantage—not by assuming Rising Tide can be removed.

**Threat coverage and exclusions:**

| Enemy threat | Coverage | Response |
|---|---|---|
| Shieldbearer formation-wide combat modifier | **Direct** | Cavalry has troop advantage: increased damage dealt and reduced damage received. |
| Vhagar’s and Moondancer’s non-Basic Physical Commands | **Direct but target-limited** | Feskar begins combat with a Level-5 Resilient Bond reducing non-Basic Physical damage received by 13% for itself and one adjacent ally. It does not protect all three dragons. |
| Enemies that deal non-Basic Physical damage | **Direct offensive pressure** | Feskar deals Fire damage to all such enemies on Rounds 3, 5, 8, and 10; at Habit level 5, Emerald Inferno’s recorded rate is 80%. This explicitly includes Vhagar and Moondancer. |
| Physical damage against Malachite and Feskar | **Probabilistic** | Tessarion has a 50% chance at the start of each odd round to reduce Physical Damage Received for two other allies for two rounds. It does not protect Tessarion herself. |
| Velar’s formation-wide Tactical hits | **Probabilistic and partial** | Malachite has a 35% chance each round to reduce Tactical Damage Received by 16% for two other allies for two rounds. Malachite is excluded from her own effect. |
| Enemy Physical Damage Dealt | **Probabilistic and target-limited** | Tessarion’s Rounds 1/4/7 attack prioritizes a non-Basic Physical dealer and has a 50% chance to reduce its Damage Dealt by 20% for two rounds. Feskar separately has a 20% chance each round to reduce the highest-Strength enemy’s non-Basic Physical output by 12%; the repository does not establish whether that target is Vhagar or Moondancer. |
| Opening attrition | **Direct sustain** | Malachite applies Recovery to two adjacent allies on Rounds 1, 2, 5, and 8, with the Rank-6 enhancement affecting the opening Rounds 1–2. |
| Vhagar’s Taunt | **Partially neutralized, not removed** | Taunt still redirects Basic Attacks, but it does not suppress the trio’s Active Commands or Habits. No dragon here Cleanses Taunt. |
| Velar/Vhagar Advantage feeding Moondancer | **Uncovered** | The formation does not reliably remove Advantage. Velar’s Command and Vhagar’s Eclipse Cover can accelerate Moondancer’s stack chances. |
| Rising Tide and Crescent Blade | **Partially covered** | Physical mitigation and damage-output reductions apply to Crescent Blade where their target and proc conditions are met. Rising Tide itself is neither removed nor prevented. |
| Velar’s First-Strike/Slow, Vhagar’s Weakened, and enemy opening mitigation | **Uncovered** | No reliable Cleanse, Resistance, or enemy-buff removal is available from these dragons at Rank 6. |
| Ordinary Basic Attacks | **Partial** | Troop advantage applies formation-wide. Tessarion’s broad Physical mitigation has no Basic-Attack exclusion, but Feskar’s Resilient Bond and Physical-output debuff explicitly exclude Basic Attacks. |

**Combat horizon:** The recommendation is strongest in the first cycle because Malachite’s enhanced opening Recovery overlaps Tessarion’s early Physical suppression and Vhagar’s own defensive opening. The danger rises around Round 4 and later as Moondancer gets more opportunities to reach four Rising Tide stacks. In a fight continuing through one or two Stalemates, Malachite’s sustain is the principal reason this line ranks above the more aggressive alternative. Exact status/stack persistence across Stalemates is not documented, so no reset is assumed.

**Strongest credible alternative:** **Tessarion Left Flank / Arulix Vanguard / Feskar Right Flank**, also using Cavalry. Arulix gives the entire enemy formation a guaranteed 8% Strength and Intelligence reduction and repeatedly attacks both non-Basic Physical dealers. Its 25% scheduled Overwhelm can suppress Commands and Habits, while its 25% Stagger prioritizes Physical dealers. However, Stagger does **not** stop Vhagar’s or Moondancer’s Active Commands—it only stops Basic Attacks and Attack Modifier Commands—and Overwhelm’s target is uncertain because no enemy deals Fire damage. This alternative therefore offers better offensive pressure and probabilistic disruption but loses Malachite’s Recovery and Tactical protection. It becomes preferable if Arulix has materially higher actual Power, or if ending the fight quickly matters more than surviving Velar’s repeated formation-wide Tactical damage.

**Risks:** Visible Power and account modifiers are unknown. Meleys and Smoketail were considered part of the known production roster but were not selected: their screenshot-complete Rank gates, resolved values, and Habit upgrade tracks remain incomplete, so installed-client mechanics cannot receive decisive default-counter credit.

**Evidence:**

- `data/dragons/tessarion.json -> command.verbatim`, `habits[2].verbatim`, `habits[2].upgrade_levels["5"]`, `troop_affinities`
- `data/dragons/malachite.json -> command.verbatim`, `vanguard.verbatim`, `habits[0].verbatim`, `habits[0].upgrade_levels["5"]`, `troop_affinities`
- `data/dragons/feskar.json -> command.verbatim`, `habits[0].verbatim`, `habits[0].upgrade_levels["5"]`, `habits[2].upgrade_levels["5"]`, `troop_affinities`
- `data/dragons/velar.json -> command.verbatim`, `habits[0:3]`
- `data/dragons/vhagar.json -> command.verbatim`, `vanguard.verbatim`, `habits[0:3]`
- `data/dragons/moondancer.json -> command.verbatim`, `habits[0:3]`
- `data/game_mechanics.json -> troop_types.Cavalry`, `troop_affinity`, `abilities.basic_attack`
- `data/effects.json -> Taunt`, `Stagger`, `Overwhelm`

