# Dragonfire Strategist benchmark report

Date: 2026-10-01  
Client evidence: 26.9.56700 / version code 326

## Verdict

The Strategist does **not** currently reproduce the three supplied expert formations.
Across both complete blind runs it matched **0/3** exact formations. It passed **3/3**
benchmark-independent holdouts in both runs, so its progression gates, troop-cycle
logic, and uncertainty discipline are materially stronger than its full-roster ranking.

The appropriate interpretation is:

- **Sound for constrained mechanics analysis and conditional theorycraft.**
- **Not yet calibrated to claim that its full-roster winner reflects the current meta.**
- A mismatch can be a defensible alternative, but failing to retain any expert line as
  the strongest rejected alternative is a search/weighting problem.

## Blind results

| Case | Expert | Initial recommendation | Search-revision recommendation |
|---|---|---|---|
| High damage | Velar / Vhagar / Moondancer; Shieldbearers | Malachite / Vhagar / Moondancer; Shieldbearers | Tairax / Caraxes / Tessarion; Cavalry |
| Damage + survivability | Vermithor / Rhysarion / Venator; Spearmen | Malachite / Vhagar / Moondancer; Shieldbearers | Malachite / Moondancer / Vermithor; Shieldbearers |
| Counter to Velar / Vhagar / Moondancer | Malachite / Seasmoke / Kalspire; Cavalry | Malachite / Vermithor / Arulix; Cavalry | Tessarion / Malachite / Feskar; Cavalry |

The objective-specific search revision stopped the same generic hybrid from winning the
first two prompts, but it did not improve exact benchmark recall. It produced more
distinct theorycraft lines without solving the absence of outcome-calibrated weighting.

## Holdouts

All three passed in both complete runs:

- Five-Star Velar correctly lost Gales of Power while retaining the lower-Star
  Velar/Moondancer chain.
- Five-Star Vermithor correctly fell back to 30% Physical, 60% Tactical, and 30%
  Protect and lost Bronze Bulwark's mitigation.
- The Malachite/Seasmoke/Kalspire Cavalry line was correctly rejected as a default into
  low-buff Spearmen; Seasmoke's removal value was downgraded rather than overfit.

## Diagnoses

### High damage — weak search with defensible alternatives

The alternatives cite real damage schedules, amplification, affinity, and proc limits.
Without a damage formula or battle outcomes, the repository cannot prove that they are
worse. The defect is that the known expert line was not retained for the final pairwise
comparison, despite being a strong affinity-perfect producer/payoff formation.

The search-revision run also made one false affinity claim: it called Spearmen
affinity-perfect for Tairax/Caraxes/Tessarion even though Tairax lacks positive Spearmen
affinity. An exact three-way affinity-intersection guard was added. A targeted rerun
made valid affinity claims and preserved the troop holdout, but selected another
non-benchmark high-damage line: Starshower / Moondancer / Shadowrend with
Shieldbearers.

### Damage plus survivability — mixed weak search and weighting

The recommended formations contain genuine Recovery, mitigation, protection, and
damage. However, neither full run compared the explicit Vermithor Protect + Rhysarion
Recovery + Venator sustained-pressure package. The agent therefore cannot demonstrate
that its selected hybrid dominates the expert line on the requested objective.

### Counter — upstream disruption is underweighted

The counter answers inventory threats and exclusions carefully and choose valid Cavalry
lines. The search-revision answer explicitly admits that enemy Advantage remains
uncovered, yet still does not compare Seasmoke's repeated positive-effect removal and
Kalspire payoff. It favors direct mitigation of downstream damage over disrupting the
buff engine that supports several downstream effects.

## Implementation changes from the backtest

- Added executable blind cases, raw-response capture, hashing, parsing, grading, and
  Markdown/JSON reports.
- Added full-roster candidate ledgers by non-Siege troop type, all-lane comparison, and
  distinct high-damage, damage/survivability, and counter objective profiles.
- Added a cross-objective guard so a generic hybrid cannot win materially different
  prompts without explicit justification.
- Added an exact set-intersection rule before any affinity-perfect claim.
- Kept all changes formation-agnostic; no benchmark trio receives a name-based boost or
  exception.

## Remaining evidence need

The missing calibration signal is empirical. Even a small collection of matchup
outcomes comparing the expert lines with the Strategist's strongest alternatives would
help determine whether the gap is bad weighting or a defensible meta alternative.
Until then, the Strategist should treat close cross-archetype comparisons as uncertain
and avoid presenting repository-only theorycraft as a proven meta ranking.

Raw complete runs:

- `runs/2026-10-01-current/`
- `runs/2026-10-01-search-revision/`
- Targeted affinity regression: `runs/2026-10-01-affinity-guard/`

The Copilot CLI test host injected an unrelated Open Brain quick-reference preamble into
each raw answer. It is presentation noise from that host environment, not text in the
Dragonfire Strategist definition.
