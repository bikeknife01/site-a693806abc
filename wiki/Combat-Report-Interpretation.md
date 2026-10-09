# Combat report interpretation

The Combat Analyst adds auditable interpretations to the local extractor's visible
action ledger. The canonical sources of truth are
[`data/combat_report_rules.json`](../data/combat_report_rules.json) and
[`data/combat_report_observations.json`](../data/combat_report_observations.json). This
page describes the workflow; it does not duplicate their mappings.

## Evidence vocabulary

| Class | Meaning | Safe wording |
| --- | --- | --- |
| `observed` | Directly visible in a cited action, detail line, or retained frame. | “The report shows…” |
| `derived` | Deterministic calculation over observed values. | “The visible parsed total is…” |
| `inferred` | Supported interpretation not directly stated by this report. | “The evidence supports…” |
| `unknown` | Source, meaning, or completeness remains unresolved. | “The source remains unresolved.” |

Confidence is separate: `tentative`, `supported`, `corroborated`, or `disputed`. These
are review categories, not invented probabilities.

## Relationship types

- `explicit`: one report card directly names source and result.
- `ui_alias`: displayed phrases are evidenced as the same concept.
- `emitted_effect`: a named source produces a separately reported effect.
- `unnamed_result`: a separate result is attributed without repeating its source name.
- `inferred_exclusive_mapping`: controlled comparisons exclude recorded alternatives.
- `timing_correlation`: events recur at a stable offset without establishing causality.
- `unresolved`: a useful pattern exists but source or meaning remains open.

## Current rule state

Established and disputed rules are the entries with the corresponding `status` in
`data/combat_report_rules.json`. Accepted rules currently include directly displayed
results for Velar, Moondancer, Vhagar, Zivern, and Rhysarion; Vhagar's displayed
Bulwark Strength and mitigation cards; Moondancer's granted Crescent Blade to Rising
Tide mitigation chain; Crimson's Bloodscale Terror results; Rhysarion's Inspiring
Melody and Dawnsong results; and Seasmoke's Cleansing Wrath and Infectious Wrath
results. Their exact IDs, match bounds,
limitations, and portable supporting and contradicting observation references remain
in the machine data. Use the validator and generated analysis to enumerate current IDs;
do not infer an additional rule from this summary.

## Run and review

Before recording new evidence, follow the
[`Combat Report Capture Guide`](Combat-Report-Capture-Guide.md), especially its
single-dragon-swap protocol and local capture-note template.

```powershell
python projects/combat-report-extractor/validate_combat_report_rules.py
python projects/combat-report-extractor/combat_report_interpreter.py interpret `
  --report '<run>\combat-report.json' `
  --output '<run>'
```

Review `combat-insights.md`, then inspect `enriched-combat-report.json` for preserved
actions and annotations. Coverage warnings flow through both. `rule-candidates.json`
is a local queue and may remain unresolved. Its formation contexts and canonical source
clues correlate displayed abilities on both sides with exact dragon ability and Habit
wording. A uniquely owned ability can identify a canonical dragon behind a PvE role
label, but the correlation remains a clue until the displayed result and relationship
meet the review policy. The candidate proposal workflow is in
[`projects/combat-report-extractor/docs/CANDIDATE_REVIEW.md`](../projects/combat-report-extractor/docs/CANDIDATE_REVIEW.md).

## Contribute a reviewed observation

1. Inspect the cited retained frame and exact OCR/report wording.
2. Remove account identifiers and use only a frame basename, never an absolute path.
3. Record report ID, capture date, extractor schema, round, timestamp, verbatim text,
   normalized fields, visual-review state, and coverage relevance.
4. Mark the observation `supports`, `contradicts`, or `context`. Counterevidence is
   retained even if a rule is later revised.
5. Reference the observation from a draft rule with a bounded deterministic match,
   conservative summary, limitations, and canonical ability citation.
6. Add positive and negative fixtures, run the full local tests, then explicitly change
   status only when the promotion policy in the specification is met.

Synthetic fixture examples under `projects/combat-report-extractor/tests/fixtures/` are
clearly marked and establish no live mechanic.

## Strategist handoff gate

Combat findings do not flow directly into formation recommendations. A proposal is
eligible for separate review only when the rule is `accepted` and `corroborated`, exact
canonical ability wording is compatible, limitations and counterexamples are retained,
the finding is a durable mechanic rather than an account-specific numeric outcome, and
the intended receiving file and tests are named. The handoff is a proposal; it never
automatically edits mechanics, effects, dragon profiles, recommendation data, or the
Strategist agent. Draft/disputed rules and local generated reports are ineligible. See
[`projects/combat-report-extractor/docs/STRATEGIST_HANDOFF.md`](../projects/combat-report-extractor/docs/STRATEGIST_HANDOFF.md)
for the proposal command and its explicit eligibility checks.
