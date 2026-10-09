# Dragonfire Combat Analyst — End-to-End Build Plan

This plan implements the contract in
[`COMBAT_ANALYST_SPEC.md`](COMBAT_ANALYST_SPEC.md). Each phase should leave the repository
usable and tested. Do not combine rule discovery with silent promotion into canonical
mechanics.

## Phase 0 — Baseline and contract lock

Deliverables:

- record the current extractor `1.0.0` input shape as a fixture;
- add one compact synthetic fixture containing an activation, a separately displayed
  effect/result, an ambiguous case, and an unmatched case;
- document stable event-ID construction and deterministic output ordering;
- confirm local recordings, frames, OCR, and generated runs remain ignored.

Checks:

```powershell
python -m unittest discover -s projects/combat-report-extractor/tests -v
git status --short
```

Exit criteria: existing extractor behavior is unchanged and fixtures express the new
interpreter boundary.

## Phase 1 — Schemas, seed data, and validation

Create:

- `projects/combat-report-extractor/schemas/combat-report-rules.schema.json`;
- `projects/combat-report-extractor/schemas/combat-report-observations.schema.json`;
- `projects/combat-report-extractor/schemas/enriched-combat-report.schema.json`;
- `data/combat_report_rules.json` with metadata and no speculative accepted rules;
- `data/combat_report_observations.json` with curated fixture observations only; and
- `projects/combat-report-extractor/validate_combat_report_rules.py`.

Validator responsibilities:

- JSON Schema validation;
- unique rule and observation IDs;
- no dangling support/contradiction references;
- canonical dragon and ability name checks against `data/dragons/*.json`;
- confidence/status/relationship consistency;
- limitations on every inferred rule;
- no account identifiers or absolute local paths in committed observations; and
- deterministic error ordering suitable for tests.

Tests:

- valid minimal stores;
- each controlled enum rejected when invalid;
- duplicate and dangling IDs;
- invalid canonical names;
- inferred rule without limitations;
- unsafe evidence path;
- disputed rule without counterevidence.

Exit criteria: seed stores validate and negative fixtures fail for the expected reason.

## Phase 2 — Deterministic interpretation engine

Create `combat_report_interpreter.py` with this CLI:

```powershell
python projects/combat-report-extractor/combat_report_interpreter.py interpret `
  --report '<run>\combat-report.json' `
  --output '<run>'
```

Optional explicit inputs:

```text
--rules data/combat_report_rules.json
--observations data/combat_report_observations.json
--repository-root <path>
```

Outputs:

- `enriched-combat-report.json`;
- `combat-analysis.json`;
- `combat-insights.md`; and
- `rule-candidates.json`.

Implementation order:

1. input/schema version checks;
2. stable event IDs derived from report hash plus event position/content;
3. exact structured matcher;
4. exact phrase matcher;
5. constrained pattern and context matcher;
6. ambiguity detection;
7. source/result links and annotations;
8. deterministic aggregations by round/source/ability/effect;
9. JSON rendering;
10. Markdown rendering from the same model.

Do not refactor OCR in this phase. Share only small pure helpers when duplication is
clear and fully covered by existing extractor tests.

Tests:

- exact match and event linking;
- owner and round-offset bounds;
- a broad and specific rule choose the specific rule with an explanation;
- equally specific matches produce ambiguity;
- disputed/deprecated rules do not produce established interpretations;
- unmatched input is retained;
- source OCR/evidence fields are unchanged;
- repeated executions are byte-identical;
- Markdown claims correspond to JSON annotations.

Exit criteria: the interpreter enriches fixtures without changing the extractor and
does not over-attribute ambiguous results.

## Phase 3 — Candidate discovery and curation workflow

Implement conservative candidate generation for:

- repeated unknown result phrases;
- consistent source/result round offsets;
- report phrases that normalize to a known canonical effect;
- source/result pairs repeated across distinct report IDs; and
- contradictions to accepted rules.

Candidate logic must count distinct reports and distinct formations separately. It must
list alternative sources active in the same window. It may propose only
`timing_correlation` or `unresolved` unless the result directly names its source.

Add a documented curation command that converts a selected candidate into a draft patch
or prints the JSON fragment. It must never edit canonical data without an explicit
operator command. Prefer a `propose` subcommand that writes to a caller-selected file
over an in-place updater.

Tests:

- repetition in one report does not masquerade as independent evidence;
- formation variation is reported;
- alternatives are preserved;
- a counterexample is surfaced;
- candidate ordering and fingerprints are stable;
- canonical stores remain unchanged after ordinary `interpret` runs.

Exit criteria: new reports produce actionable review items without automatic promotion.

## Phase 4 — Human-facing documentation and agent

Create:

- `.github/agents/dragonfire-combat-analyst.agent.md`;
- `wiki/Combat-Report-Interpretation.md`; and
- README/AGENTS links and operating instructions.

The agent definition must implement the behavior contract in the specification. It
should direct the agent to validate inputs, run the interpreter, inspect coverage and
cited frames when available, then answer with separate observed/derived/inferred/unknown
sections. It may draft rule updates only when the user requests repository changes.

The wiki should include:

- the evidence vocabulary and relationship types;
- established accepted rules rendered from canonical data or explicitly linked by ID;
- disputed rules and unresolved questions;
- instructions for contributing a reviewed observation; and
- examples that are clearly synthetic unless backed by committed evidence.

Exit criteria: a fresh session can operate the workflow by reading repository files
without relying on prior chat history.

## Phase 5 — Real-report calibration

Run the interpreter against the retained local extraction at:

```text
Game_Details/Resources/_snapshots/2026-10-08/analysis/
combat-report-video-3/extractor-run/combat-report.json
```

This path is local and ignored; code and tests must not depend on it. Review a small,
representative sample of candidate mappings against cited frames. Curate only evidence
that is visually confirmed and contains no account-specific identifiers.

Calibration questions:

- Which report result phrases recur without a source name?
- Do the same source/result pairings recur across rounds?
- Are there competing active abilities that prevent attribution?
- Can canonical Habit/Command wording independently corroborate the mapping?
- Do clipped actions or six known missing damage sentences affect the conclusion?

Exit criteria: at least one fully auditable example exercises the real workflow, even if
the correct outcome is an unresolved candidate rather than an accepted rule.

## Phase 6 — Strategist handoff gate

Add a one-way review path for corroborated findings that may improve recommendations.
Do not make the Strategist consume local reports or draft rules directly.

A finding is eligible for handoff only when:

- its rule is `accepted` and `corroborated`;
- exact canonical ability text is compatible;
- limitations and relevant counterexamples are recorded;
- it describes a durable mechanic rather than account-specific damage values; and
- the receiving canonical file and tests are identified.

The handoff should produce a reviewable proposal, not mutate
`data/game_mechanics.json`, `data/effects.json`, or dragon profiles automatically.

Exit criteria: Combat Analyst discoveries cannot silently influence formation advice.

## Phase 7 — Empirical measurement and recommendation handoff

Create reviewed trial definitions, per-report opportunity/activation/exposure
measurements, repeated-experiment aggregation, a canonical empirical-findings store,
and a proposal-only Strategist handoff. Multiple emitted result cards count as one
source activation. Unknown opportunities never become failed procs. Outcome samples
retain exposure context without causal wording.

Update one-command ingestion, both agent contracts, wiki guidance, schemas, validation,
and synthetic tests. Local measurement and experiment files remain ignored; only
explicitly reviewed portable findings may be committed.

Checks:

```powershell
python -m unittest discover -s projects/combat-report-extractor/tests -v
python projects/combat-report-extractor/validate_combat_report_rules.py
```

Exit criteria: one-command ingestion emits a deterministic measurement, repeated runs
aggregate without inflating multi-card activations, and no empirical value can reach
the Strategist without accepted/corroborated/approved canonical state.

## Phase 8 — Release validation and documentation audit

Run:

```powershell
python -m unittest discover -s projects/combat-report-extractor/tests -v
python projects/combat-report-extractor/validate_combat_report_rules.py
git status --short
```

Also run any shared consumer tests if canonical mechanics are deliberately changed.
Confirm:

- ignored captures remain untracked;
- generated outputs contain tool/rule/input hashes;
- examples do not contain personal or account-specific data;
- all doc links resolve;
- no agent prose duplicates a hidden rule not present in machine data; and
- existing extractor output remains backward compatible.

## Recommended commit sequence

1. `Define combat analyst schemas and seed stores`
2. `Add deterministic combat report interpreter`
3. `Add combat rule candidate review workflow`
4. `Add Dragonfire Combat Analyst agent and guidance`
5. `Calibrate combat interpretation against reviewed evidence`

Keep schema/engine commits separate from curated real-game findings so reviewers can
distinguish implementation correctness from evidentiary judgment.

## Principal risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Temporal adjacency is mistaken for causality | Relationship vocabulary, conservative candidate types, ambiguity output, independent corroboration. |
| OCR errors become canonical rules | Retain verbatim OCR and frame locators; require visual-review state. |
| One report is counted as many observations | Count distinct report IDs and formations separately. |
| Rules drift from dragon data | Validate canonical names and cite exact source fields. |
| Analyst and Strategist create circular evidence | One-way, reviewed handoff; no draft-rule consumption by Strategist. |
| Generated Markdown disagrees with JSON | Render both from one analysis model and test correspondence. |
| Local evidence paths leak into Git | Schemas reject absolute paths; committed observations use portable metadata. |
| A parser change invalidates historic results | Version checks, hashes, migrations, retained fixtures. |

