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

I’ll derive this only from the canonical rules, handoff, mechanics, effects, lifecycle evidence, and dragon profiles; evaluation artifacts remain untouched.

The hard gates leave all screenshot-audited dragons eligible at Level 50/Rank 6 with Habits 1–3 active; Meleys and Smoketail remain conditional-only because their exact values and Habit upgrade tracks are incomplete. I’m now comparing complete trios, Level-50 stat fit, Rank-6 producer/payoff chains, Vanguard placement, and shared affinity rather than treating rarity or role labels as a ranking.

Two lines now separate from the rest: an **Archers affinity-perfect sustain line** (Syrax → Moondancer, with Vhagar protecting and amplifying them) and a **Shieldbearers affinity-perfect Protect line** (Malachite → Moondancer, with Vermithor). I’m checking the strongest fire/First-Strike line and exact Rank-6 timing before choosing between them.

### Recommended Formation

**Best-supported general-purpose formation:** **Malachite / Vhagar / Moondancer**  
**Formation troop type:** **Shieldbearers** — affinity-perfect for all three.

| Position | Dragon | Current Power | Star rank | Habit skill levels | Job |
|---|---|---:|---:|---|---|
| Left Flank | Malachite | Unknown | 6 | Unlocked Habits 1–3: Level 5 | Tactical damage, Recovery, Rising Tide/Advantage enabler |
| Vanguard | Vhagar | Unknown | 6 | Unlocked Habits 1–3: Level 5 | Taunting frontline, mitigation, physical amplification |
| Right Flank | Moondancer | Unknown | 6 | Unlocked Habits 1–3: Level 5 | Primary physical damage, scaling mitigation |

**Why it works:** Moondancer grants Crescent Blade to Malachite, the formation’s only other Sentinel. Malachite can then generate Rising Tide when dealing Tactical Damage on rounds 1, 2, 4, and 7 or applying Recovery on rounds 2, 5, and 8—seven documented round opportunities, limited to one stack per round and each requiring a 50% trigger. Rising Tide reduces Moondancer’s damage received by 2% per stack and, at four stacks, doubles her Rank-6 even-round Crescent Blade damage. At Habit Level 5, Full Moon also gives Moondancer 50% Rising Tide checks on rounds 6, 8, and 10, doubled when Advantage is active.

Vhagar supplies the frontline protection and damage bridge. In Vanguard she receives 8% less damage and gives Malachite 16% more Tactical Damage. Her Level-5 Battle Leader gives the Right Flank Moondancer **+25% non-Basic Physical Damage** for the entire combat. Vhagar also has a 25% per-round chance to Taunt three enemies for two rounds, opening three-round mitigation of 24%, and 30% increased Recovery Received from round 4 onward. Malachite supports both wings through Recovery, a 35%-chance two-ally package of **+16% non-Basic Physical Damage and −16% Tactical Damage Received**, and a 20% per-round chance to grant both other allies Advantage. These are chance-based rather than guaranteed, but all pivotal Habit values are maximized under the assumptions.

The Level-50 curves also fit the jobs: Vhagar and Moondancer have base Strength 163 and 158 respectively, while Malachite has base Instinct 166 and Initiative 149. Because all three are Legendary and Rank 6, their recorded rarity/star-scalar context is comparable, although the repository does not establish a complete final-stat formula.

**Troop rationale:** Shieldbearers give Positive affinity to all three, maximizing affinity-derived stats for this fixed trio. Shieldbearers beat Archers but are disadvantaged against Cavalry; without a known opponent, that Cavalry exposure is the formation’s inherent troop-cycle weakness. Siege is inappropriate for general combat and is explicitly negative for Malachite and Moondancer.

**Gates and investment:** Rank 6 is decisive. It activates Moondancer’s Full Moon and doubled four-stack damage payoff, Malachite’s improved opening Command and Thunderous Roar, and Vhagar’s Eclipse Cover. Malachite’s 8-Star teamwide Strength Habit and Moondancer’s 8-Star physical-damage/Bleed payoff are unavailable and receive no credit. There is no dependable Cleanse in this Rank-6 trio.

**Combat horizon:** The opening cycle combines Vhagar’s strongest mitigation with Malachite’s enhanced rounds 1–2 Tactical damage and Recovery. Moondancer may reach four Rising Tide stacks during the first cycle, but that is not guaranteed: her main Sentinel trigger is 50%, while Advantage depends on Malachite’s 20% proc or Vhagar’s 35% rounds-3–7 proc. Later cycles retain Malachite’s Recovery and full-combat buffs, Vhagar’s Taunt and enhanced Recovery Received, and Moondancer’s stack-based mitigation; this gives the formation better sustained value than a pure opening-burst line.

### Strongest Credible Alternative

**Syrax — Vhagar — Moondancer with Archers**, using Syrax on the Left Flank, Vhagar in Vanguard, and Moondancer on the Right Flank.

It preserves the affinity-perfect structure and the same Vhagar-to-Moondancer physical amplification. Syrax also gives Moondancer seven Tactical/Recovery opportunities to generate Rising Tide and provides stronger scheduled Recovery—Level-5 Strategic Revival has a 100% Recovery Rate on rounds 2, 5, and 8, plus a 50% chance to grant Resistance. Her permanent teamwide Intelligence, Instinct, and Initiative buffs further improve broad formation durability and tempo.

The alternative ranks slightly lower because Syrax’s Fire/First-Strike support has no strong recipient here, while Malachite directly amplifies both Moondancer’s Physical damage and the formation’s Tactical mitigation and can supply Advantage for Moondancer’s doubled Rising Tide checks. Choose the Syrax version instead if reliable scheduled Recovery and Resistance matter more than physical amplification and stack acceleration. Its Archers are disadvantaged against Shieldbearers rather than Cavalry.

**Risks:** Visible Power is unknown, no opponent or account modifiers were supplied, pivotal Taunt/Advantage/Rising Tide effects are probabilistic, and neither line has Rank-6 Cleanse. A material Power disparity, a known troop matchup, or control-heavy enemy could reverse the choice. Meleys and Smoketail were not used as defaults: they are available but remain client-derived and lack exact resolved values, complete Habit upgrade tracks, and current screenshot verification.

**Evidence:** `data/dragons/malachite.json -> command.verbatim, vanguard.verbatim, habits[0..2], troop_affinities`; `data/dragons/vhagar.json -> command.verbatim, vanguard.verbatim, habits[0..2], troop_affinities`; `data/dragons/moondancer.json -> command.verbatim, habits[0..2], troop_affinities`; `data/dragons/syrax.json -> command.verbatim, habits[0..2], troop_affinities`; `data/dragon_application_knowledge.json -> dragons[name=Malachite|Vhagar|Moondancer].level_model`; `data/game_mechanics.json -> troop_affinity, troop_types, damage_types`.

