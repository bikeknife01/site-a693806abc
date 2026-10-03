# Strategist backtest assessment

## Outcome

The revised Strategist matched **0 of 3** expert formations exactly and passed **3 of
3** holdouts. The evidence does not support calling its full-roster ranking logic
meta-calibrated. It does support calling its gate, troop-cycle, uncertainty, and local
mechanics reasoning generally sound.

| Scenario | Expert formation | Strategist recommendation | Diagnosis |
|---|---|---|---|
| General high damage | Velar / Vhagar / Moondancer, Shieldbearers | Tairax / Caraxes / Tessarion, Cavalry | Weak search; defensible theorycraft alternative, but the expert line was not retained for the final comparison |
| Damage plus survivability | Vermithor / Rhysarion / Venator, Spearmen | Malachite / Moondancer / Vermithor, Shieldbearers | Mixed weak search and weighting; the selected line has real sustain/protection, but the explicit Rhysarion/Venator package was not compared |
| Counter to Velar / Vhagar / Moondancer | Malachite / Seasmoke / Kalspire, Cavalry | Tessarion / Malachite / Feskar, Cavalry | Bad weighting; the answer carefully covers damage but knowingly leaves the enemy Advantage enabler uncovered and does not compare Seasmoke's upstream removal line |

## What is working

- Exactly one shared troop type and three legal lanes were used.
- Star and Habit gates were applied correctly in both five-Star holdouts.
- Vermithor's six-Star values did not leak into the five-Star case.
- Cavalry was correctly rejected into Spearmen, and Seasmoke's value was downgraded
  when the opponent did not rely on positive buffs.
- Chance-based effects, targeting limits, Basic-Attack exclusions, unknown Power, and
  unpublished formulas were disclosed rather than treated as guarantees.
- The revised objective profiles stopped one generic hybrid from winning every prompt.

## What remains unsound or unresolved

- The agent can enumerate mechanically coherent alternatives, but no observed battle
  outcomes or published formulas calibrate the relative weight of their damage,
  mitigation, Recovery, control, or upstream disruption.
- A claimed full-roster comparison is not externally auditable from the final answer.
  None of the expert lines appeared as the strongest rejected alternative.
- The high-damage answer contains a concrete affinity error: it says Spearmen are also
  affinity-perfect for Tairax / Caraxes / Tessarion, but Tairax's canonical positive
  affinities are Cavalry, Shieldbearers, and Siege. Only Cavalry is affinity-perfect for
  that trio among the two troop types discussed.
- The counter search overweights direct damage mitigation relative to removing an
  upstream buff that enables several downstream payoffs.
- Every CLI response begins with an unrelated Open Brain quick-reference preamble. That
  text comes from the test host's Copilot/plugin environment rather than the Strategist
  definition, but it is still user-facing noise in this execution path.
- Exact-match evaluation should therefore remain separate from mechanical-validity
  evaluation. The mismatches are not proof that every alternative is bad, but they are
  evidence that the Strategist does not currently recover known meta reliably.

## Recommended next calibration step

Do not add formation-name exceptions. Add a small amount of matchup or battle-outcome
evidence when it becomes practical, then use pairwise comparisons to learn whether the
expert line consistently beats the theorycraft alternatives. Until then, the
Strategist should present close full-roster results as competing evidence-supported
lines rather than call one definitively best.

The raw answers, hashes, and machine grade are in this directory. The holdouts show
that the benchmark-independent rules survive changes to Star rank and troop matchup.
