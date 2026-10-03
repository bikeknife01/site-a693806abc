# Starshower

Sentinel · Age label: Elder · Rarity tier: Epic · Positive affinity: Shieldbearers

Starshower is a Tactical attacker and support dragon built around **Solar Flare** marks.
**Starfall** marks all three enemies, can consume a mark for a chance-based Tactical hit,
and deals scheduled same-lane Tactical damage. At 6 Stars, **Ill Portents** strengthens
the consuming hit and can refresh all marks once during rounds 6–10 when none remain.

Starshower also offers chance-based Cleanse/Evade, all-enemy Intelligence and Initiative
reduction, same-lane Tactical vulnerability, and 10-Star ally mitigation. Resistance
strengthens the mitigation; Advantage expands it from adjacent allies to all three.

Exact wording and all Habit upgrade tracks: [JSON](../../data/dragons/starshower.json).

## Recommendation-critical source coverage

- **Command — Starfall:** Marks 3 Enemies with Solar Flare at combat start. Each round has a 50% chance to consume a mark for Tactical Damage; rounds 1, 3, 7, and 9 also deal same-lane Tactical Damage. Six- and ten-Star clauses add stronger mark consumption, one conditional mark refresh, and ally mitigation.
- **Vanguard — Sentinel's Wit:** At Level 16+ in Vanguard, Starshower gains +16% Tactical Damage Dealt; the Left Flank Ally gains +20 Instinct and Initiative.
- **2 Stars — Night Guardian:** Each round has a chance to Cleanse one Negative effect from 2 other Allies and grant them 10% Evade for one round.
- **4 Stars — Battle Subversion:** Reduces the Intelligence and Initiative of all 3 Enemies until combat ends.
- **6 Stars — Ill Portents:** Raises Solar Flare consumption damage and permits one mark refresh during rounds 6–10 if no Enemy remains marked.
- **8 Stars — Tactical Breach:** Increases Tactical Damage Received by one same-lane Enemy until combat ends. Its upgrade-row label says `Damage Dealt`, conflicting with the explicit `Damage Received` sentence; see the JSON review item.
- **10 Stars — Wishkeeper's Grace:** Consuming Solar Flare mitigates allied Damage Received for one round, strengthened by Resistance and expanded to all Allies by Advantage.
