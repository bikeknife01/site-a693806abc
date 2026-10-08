# Dragonfire Combat Analyst — Technical Specification

Status: proposed implementation contract  
Owner: `projects/combat-report-extractor/`  
Last updated: 2026-10-08

## 1. Purpose

The Combat Analyst turns an extracted Dragonfire combat report into an auditable
explanation of what happened and what the report may teach us about combat mechanics.
It extends the existing local-only video extractor; it does not replace its OCR,
ownership classification, deduplication, or evidence-preservation responsibilities.

The system must support a growing body of rules that connect:

- a source dragon, Command, Vanguard ability, Habit, Basic Attack, or other action;
- the wording and values visible in a combat report;
- named or unnamed effects shown later in the report;
- the strength and provenance of the claimed relationship; and
- counterexamples or unresolved competing explanations.

The primary use case is learning from reports that show a result without repeating the
ability or Habit name responsible for it. The system should make these relationships
searchable and reusable without presenting temporal proximity as proven causality.

## 2. Goals

1. Enrich `combat-report.json` with established, evidence-backed interpretations.
2. Produce a round-by-round timeline and useful combat insights with citations to the
   original action record and frame.
3. Maintain a versioned, machine-readable rule base for explicit mappings, aliases,
   emitted effects, unnamed results, timing correlations, and unresolved hypotheses.
4. Preserve exact report and ability wording alongside normalized fields.
5. Record supporting and contradicting observations independently from the rules they
   evaluate.
6. Generate review candidates when a report exhibits a repeated but unconfirmed
   relationship; never promote those candidates automatically.
7. Give a dedicated Markdown agent a safe, repeatable workflow for explaining reports,
   evaluating hypotheses, and proposing rule updates.
8. Keep all capture and analysis activity outside the game process and emulator.

## 3. Non-goals

- Reading game memory, instrumenting the client, intercepting or decrypting traffic,
  modifying MuMu, or automating interaction with the game.
- Reconstructing server payloads or hidden server formulas.
- Claiming a report is complete when extractor coverage warnings remain.
- Inferring causality from a single adjacent action or effect.
- Treating missing report text as proof that an event did not occur.
- Automatically changing `data/dragons/*.json`, `data/effects.json`,
  `data/game_mechanics.json`, or Strategist rules.
- Predicting combat outcomes from incomplete formulas.
- Turning community claims or installed-client presence into live mechanics without the
  evidence treatment required by `AGENTS.md`.

## 4. Safety and operating boundary

The complete supported path is:

```text
user-supplied recording
  -> local frame/OCR extraction
  -> normalized visible action ledger
  -> deterministic rule interpretation
  -> human-reviewed hypotheses
  -> curated rules and observations
```

The analyst consumes files already on disk. It must not connect to ADB, MuMu, the game,
the network, or an external inference service. Recordings, frames, OCR manifests, and
generated runs remain ignored local artifacts. Only deliberately curated, non-account
specific observations and rules may be committed.

## 5. Evidence vocabulary

Every statement emitted by the analyst must use one of these provenance classes:

| Class | Meaning | Permitted wording |
| --- | --- | --- |
| `observed` | Directly visible in a cited report action, detail line, or retained frame. | “The report shows…” |
| `derived` | Deterministic calculation over observed values, such as a sum or ordering. | “The parsed visible total is…” |
| `inferred` | A supported interpretation that is not stated directly by this report. | “The evidence supports…” |
| `unknown` | The available evidence cannot resolve the source, meaning, or completeness. | “The source remains unresolved.” |

Confidence is categorical and separate from provenance:

- `tentative`: one observation or unresolved alternatives remain;
- `supported`: repeated consistent observations with no known contradiction;
- `corroborated`: repeated report evidence plus independent canonical ability/mechanic
  text, or another equally strong independent evidence type;
- `disputed`: at least one material counterexample has not been resolved.

These labels are not probabilities. They must not be converted into invented numeric
certainty.

## 6. Relationship types

Rules use one of the following relationship types:

| Type | Definition |
| --- | --- |
| `explicit` | The same report card directly names the source and result. |
| `ui_alias` | Two displayed phrases or names are evidenced as the same game concept. |
| `emitted_effect` | A named ability or action produces a separately reported effect. |
| `unnamed_result` | A separately reported result is attributed to a source whose name is not repeated on the result line. |
| `inferred_exclusive_mapping` | Controlled comparisons leave one supported source among the observed alternatives. |
| `timing_correlation` | Events repeatedly occur at a stable offset, but causality is not established. |
| `unresolved` | A useful pattern exists, but the responsible source or interpretation is not established. |

`timing_correlation` may not be rendered as “causes,” “triggers,” or “comes from.”
`inferred_exclusive_mapping` must list the alternatives excluded and the evidence used
to exclude them.

## 7. Architecture

### 7.1 Existing extractor

`combat_report_extractor.py` remains responsible for:

- local frame extraction and OCR;
- blue/user and red/enemy ownership classification;
- active round recognition;
- parsing visible action cards;
- canonicalizing known dragon and ability names;
- temporal deduplication;
- coverage warnings; and
- the raw visible-value summary.

Its current `combat-report.json` schema version is `1.0.0`. The interpreter must accept
that version. Any incompatible extractor change requires an explicit migration and new
fixtures.

### 7.2 Interpreter

The planned `combat_report_interpreter.py` consumes a normalized report plus canonical
rules and observations. It performs no OCR. It must:

1. validate input versions and rule data;
2. assign a stable event ID to every input action without deleting or rewriting the
   source action;
3. match rules using structured fields before considering normalized text patterns;
4. emit zero or more annotations per event;
5. connect related events only when the rule's constraints are satisfied;
6. calculate deterministic summaries over observed values;
7. surface unmatched and ambiguous patterns as review candidates; and
8. render JSON and Markdown from the same interpretation model.

### 7.3 Curated rule and observation stores

`data/combat_report_rules.json` is the canonical interpretation contract.
`data/combat_report_observations.json` holds compact, curated supporting or contradicting
evidence. Rules refer to observation IDs; they do not embed local absolute paths.

Local runs may generate `rule-candidates.json`, but candidates are not canonical and
must remain in ignored run folders until reviewed.

### 7.4 Markdown agent

`.github/agents/dragonfire-combat-analyst.agent.md` is a user-facing workflow and
reasoning contract. It must read the machine data and generated analysis rather than
containing a parallel prose rule base. The agent may propose patches, but it must not
silently promote candidates or edit Strategist data while merely analyzing a report.

### 7.5 Human documentation

`wiki/Combat-Report-Interpretation.md` explains established rules and open questions for
people. It is generated or checked from canonical machine data where practical. It must
clearly distinguish established interpretations from active hypotheses.

## 8. Canonical data contracts

Exact JSON Schemas are implementation deliverables. The following fields are the
minimum semantic contract.

### 8.1 Rule store

```json
{
  "metadata": {
    "schema_version": "1.0.0",
    "updated": "YYYY-MM-DD",
    "purpose": "Combat-report interpretation rules"
  },
  "rules": [
    {
      "id": "rule.<source-slug>.<result-slug>.v1",
      "status": "accepted",
      "relationship": "emitted_effect",
      "source": {
        "dragon": "Example Dragon",
        "ability": "Example Habit",
        "ability_type": "habit"
      },
      "match": {
        "event_kind": "activation",
        "owner_scope": "same",
        "result_event_kind": "effect",
        "round_offset": {"minimum": 0, "maximum": 1},
        "report_phrases": ["Exact displayed phrase"]
      },
      "interpretation": {
        "effect": "Canonical Effect",
        "summary": "Conservative human-readable interpretation",
        "provenance": "inferred",
        "confidence": "supported"
      },
      "evidence": {
        "supports": ["observation.example.001"],
        "contradicts": [],
        "canonical_sources": [
          "data/dragons/example.json -> habits[0].verbatim"
        ]
      },
      "limitations": ["What this rule does not establish"],
      "review": {
        "created": "YYYY-MM-DD",
        "last_reviewed": "YYYY-MM-DD"
      }
    }
  ]
}
```

Required rule properties:

- `id` is stable, unique, and never reused for a different meaning.
- `status` is `draft`, `accepted`, `disputed`, or `deprecated`.
- `relationship` uses the controlled vocabulary in section 6.
- `source` identifies only values established by the evidence; unknowns remain null.
- `match` is deterministic and bounded. Free-form regular expressions are permitted
  only when schemas constrain them and tests cover positive and negative cases.
- `interpretation.summary` may not claim more than `relationship` and evidence permit.
- `evidence.supports` and `evidence.contradicts` reference observation records.
- `limitations` is required for every inferred rule.
- `review` preserves review dates; deprecation preserves replacement IDs and rationale.

### 8.2 Observation store

```json
{
  "metadata": {"schema_version": "1.0.0", "updated": "YYYY-MM-DD"},
  "observations": [
    {
      "id": "observation.<report-slug>.<sequence>",
      "disposition": "supports",
      "report": {
        "report_id": "content-derived stable ID",
        "capture_date": "YYYY-MM-DD",
        "client_version": null,
        "extractor_schema_version": "1.0.0"
      },
      "location": {
        "round": 3,
        "timestamp_seconds": 82.0,
        "frame_basename": "frame-000002.jpg"
      },
      "verbatim": {
        "head_text": "Exact OCR/report wording",
        "detail_text": "Exact OCR/report wording"
      },
      "normalized": {
        "owner": "user",
        "actor": "Example Dragon",
        "ability": "Example Habit",
        "result": "Observed result"
      },
      "quality": {
        "visual_review": "confirmed",
        "coverage_warnings_relevant": false,
        "notes": []
      }
    }
  ]
}
```

Canonical observations must not contain account names, local absolute paths, or raw
video files. A frame basename is a locator within the private retained run, not a claim
that the evidence frame is committed. If visual review has not occurred, use
`visual_review: pending`; such an observation cannot by itself support `corroborated`.

### 8.3 Enriched output

`enriched-combat-report.json` retains the input report under `source_report` or through a
content-addressed reference and adds:

- `analysis_schema_version`;
- `rule_set_version` and content hash;
- stable `event_id` values;
- per-event `annotations` with rule and evidence IDs;
- `links` between source and result events;
- `unmatched_events` and `ambiguous_matches`;
- copied `coverage` plus analyst-specific warnings; and
- deterministic `insights`.

Every annotation includes `provenance`, `confidence`, `rule_id`, a plain-language
explanation, and source event IDs. An annotation must never overwrite the original OCR
or parser fields.

### 8.4 Review candidates

`rule-candidates.json` is local output containing:

- a stable candidate fingerprint;
- the recurring source/result pattern;
- report/event locators;
- count of distinct reports and occurrences;
- known alternative sources;
- contradictions;
- the most conservative proposed relationship type; and
- a checklist of evidence still needed.

A candidate is a queue item, not a rule. Candidate counts alone never establish
independence when all occurrences come from one report or identical formation.

## 9. Matching semantics

Rules are evaluated in this order:

1. exact structured identity: canonical actor, ability, action kind, owner, and round;
2. exact normalized report phrase;
3. constrained phrase pattern;
4. temporal and formation context.

Temporal context may narrow a match but cannot independently create a causal mapping.
Owner relations must be explicit: `same`, `opponent`, or `any`. Round offsets must be
bounded. Where several accepted rules match one result, the interpreter emits an
ambiguity instead of choosing by file order.

Rule precedence is permitted only when one rule explicitly supersedes another or has a
strictly more specific structured match. The explanation must identify the suppressed
rule and why it was not selected.

## 10. Insight products

The Markdown analysis should contain, when evidence permits:

1. coverage and reliability warnings;
2. formation/ownership facts visible in the report;
3. round-by-round action and effect timeline;
4. visible damage and recovery by side, dragon, ability, target, type, and round;
5. established effect attributions with rule citations;
6. activation-to-result timing observations;
7. observed proc/non-proc counts with denominator limitations;
8. unresolved or ambiguous effects;
9. candidate learnings worth targeted future observation; and
10. a concise tactical interpretation that does not exceed the data.

Use “visible parsed” for numeric totals unless completeness is positively established.
A proc rate may be described only when eligible trigger opportunities can be counted;
otherwise report occurrences without a percentage.

## 11. Rule lifecycle and promotion

1. **Discover:** interpreter writes a local candidate from unmatched recurring evidence.
2. **Review:** a person checks cited frames and exact report wording.
3. **Curate observations:** add minimal supporting and contradicting records.
4. **Draft rule:** add a deterministic match, conservative interpretation, limitations,
   and tests.
5. **Validate:** schemas, referential integrity, fixtures, and negative match tests pass.
6. **Accept:** status changes to `accepted` when evidence meets the chosen relationship
   and confidence threshold.
7. **Challenge:** new counterevidence changes confidence/status to `disputed`; it is not
   deleted.
8. **Revise/deprecate:** preserve the old ID, rationale, and replacement link.

Suggested minimum promotion policy:

- `explicit`: one visually confirmed direct statement may be accepted as `supported`.
- `ui_alias`: two contexts or independent canonical text are preferred.
- `emitted_effect` / `unnamed_result`: at least two distinct reports or formations plus
  compatible canonical ability text for `corroborated`.
- `inferred_exclusive_mapping`: controlled variation and recorded excluded alternatives
  are mandatory.
- `timing_correlation`: may be accepted as a correlation after repetition, but never
  promoted to causal wording without independent evidence.

## 12. Agent behavior contract

The Combat Analyst agent should:

- start from `combat-report.json` or `enriched-combat-report.json`;
- read coverage warnings before offering conclusions;
- cite report event/frame locators and rule IDs;
- use exact canonical ability wording where it matters;
- keep observation, calculation, and inference visibly separate;
- explain ambiguity and identify the best next recording comparison;
- propose data patches only after showing the evidence and promotion rationale; and
- hand recommendation-relevant, corroborated findings to a separate review step before
  they influence the Strategist.

It must not:

- hide rejected actions or coverage gaps;
- treat a candidate rule as established;
- edit canonical mechanics merely to make an interpretation fit;
- claim an unobserved trigger failed;
- use account-specific report results as universal balance values; or
- direct intrusive or concealed collection activity.

## 13. Compatibility and migrations

- All committed JSON stores declare semantic schema versions.
- Readers reject unsupported major versions with an actionable error.
- Minor additions are backward compatible and receive defaults only when the schema
  defines them.
- Rule IDs remain stable across wording refinements.
- Generated outputs include tool version, rule-store hash, and input report hash so an
  analysis can be reproduced.
- Migration scripts are required before removing or renaming committed fields.

## 14. Validation and acceptance criteria

The first production-ready release is complete when:

- JSON Schemas reject invalid enums, dangling observation IDs, duplicate IDs, unsafe
  absolute paths, and inferred rules without limitations;
- a validator checks cross-file references and canonical dragon/ability names;
- the interpreter deterministically enriches the existing OCR fixture;
- explicit, ambiguous, unmatched, contradicted, and deprecated-rule fixtures exist;
- Markdown and JSON agree on totals, provenance, confidence, and cited rules;
- running twice over the same inputs produces byte-identical JSON aside from no volatile
  timestamps being present;
- coverage warnings flow into every output;
- the agent definition and wiki read from or cite canonical data instead of duplicating
  rules; and
- all tests run without requiring MuMu, ADB, network access, recordings, or ignored
  snapshots.

