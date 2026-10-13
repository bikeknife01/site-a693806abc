# Player Roster Ingestion

## Goal

Produce one evidence-aware, versioned player-roster snapshot from either a
Dragonfire Formation Forge JSON export or a reviewed screenshot transcription.
Keep player observations separate from canonical dragon knowledge, preserve raw
source provenance, and emit a minimal profile accepted by the deterministic
recommendation planner.

## Status legend

- `[ ]` Not started
- `[-]` In progress
- `[x]` Complete

## Ordered work plan

### Phase 1 — Contract and schema

- [x] RST-001 Define the normalized snapshot contract and explicit unknown-value rules.
- [x] RST-002 Add a versioned JSON Schema covering metadata, profile data, field evidence, review state, and roster completeness.
- [x] RST-003 Define stable output layout and ISO-date naming conventions.

### Phase 2 — Canonical identity and enrichment

- [x] RST-011 Resolve dragon names and aliases to stable repository slugs.
- [x] RST-012 Map displayed Habit positions to canonical client ability keys.
- [x] RST-013 Record the canonical dataset version and source hashes without copying fixed dragon facts into the roster.

### Phase 3 — Formation Forge import

- [x] RST-021 Fingerprint and validate the supported site-export shape.
- [x] RST-022 Normalize level, Stars, Power, troop capacity, active/ownership semantics, and positional Habit levels.
- [x] RST-023 Validate duplicated fixed fields against canonical knowledge and report drift without importing community notes.
- [x] RST-024 Preserve an immutable source manifest and generate a field-treatment audit.

### Phase 4 — Screenshot transcription import

- [x] RST-031 Define a screenshot manifest and assisted-transcription input format.
- [x] RST-032 Normalize overview and detailed-panel observations into the same roster contract.
- [x] RST-033 Preserve displayed Stars, source image references, confidence, review state, and optional crop coordinates.
- [x] RST-034 Detect duplicate coverage, missing entries, unreadable values, and cross-screenshot conflicts without silently choosing a value.

### Phase 5 — Validation and review

- [x] RST-041 Validate schema shape, unique identity, ranges, Star conversion, Habit unlocks, and evidence references.
- [x] RST-042 Enforce observed, derived, canonical, assumed, and unknown provenance classes.
- [x] RST-043 Generate a concise Markdown review report with errors, warnings, conflicts, coverage, and source-field treatment.
- [x] RST-044 Make ingestion deterministic and fail closed on unresolved recommendation-critical conflicts.

### Phase 6 — Consumer outputs

- [x] RST-051 Emit an evidence-rich archival `roster.json`.
- [x] RST-052 Emit a minimal `planner-profile.json` using canonical slugs and keyed Habit levels.
- [x] RST-053 Dry-run planner-compatible output through the planner input validator.
- [x] RST-054 Keep fixed troop affinities canonical and keep scenario-level selectable troops outside the roster contract.

### Phase 7 — Snapshot lifecycle and interoperability

- [x] RST-061 Compare two normalized snapshots and emit machine-readable and Markdown progression deltas.
- [x] RST-062 Flag regressions and seasonal ambiguity instead of assuming all progression is monotonic.
- [x] RST-063 Add an explicit Formation Forge compatibility export that uses canonical fixed data and preserves unknown player values.

### Phase 8 — Verification and documentation

- [x] RST-071 Add fixtures for a site export, a screenshot transcription, conflicts, and invalid progression.
- [x] RST-072 Add unit and CLI integration tests for ingestion, validation, deterministic output, planner compatibility, and deltas.
- [x] RST-073 Document both ingestion paths, review workflow, privacy boundaries, directory layout, and commands.
- [x] RST-074 Run narrow tests, shared profile tests, planner tests, JSON parsing, and `git diff --check`.

### Phase 9 — Account-level army capacity

- [x] RST-081 Capture the highest unlocked Dragon's Army skill and current level once per account profile.
- [x] RST-082 Derive prerequisite, current-skill, per-dragon, and three-dragon formation bonuses deterministically.
- [x] RST-083 Record an explicit assumed zero when the user does not know the Stronghold detail.
- [x] RST-084 Carry the result into planner output, validation, review reports, and snapshot deltas.
- [x] RST-085 Add regression coverage for Dragon's Army III level 2 equaling 1,150 additional troops per dragon.

### Phase 10 — Recommendation determinism audit

- [x] RST-091 Gate producer/payoff conditions by the consumer ability's actual progression requirement.
- [x] RST-092 Surface the level-curve capacity proxy, including the Dragon's Army account bonus, without applying the unverified Star-scalar formula.
- [x] RST-093 Apply visible Power only when it is comparable across the complete eligible roster.
- [x] RST-094 Audit deterministic ordering, regression-test every corrected rule, and update the planner documentation.

## Acceptance criteria

- Both source paths produce the same normalized roster schema.
- Unknown values remain `null`; zero is never used as an unknown sentinel.
- Canonical dragon identity and Habit keys are stable and validated.
- Every observed or derived player value can be traced to source evidence.
- Conflicting recommendation-critical observations block planner-profile emission.
- Fixed dragon facts are validated or joined from canonical data rather than duplicated.
- Output is deterministic for identical inputs and knowledge data.
- Historical snapshots are never overwritten by the CLI.
- The planner-compatible output passes the recommendation planner's validation.

## Completion status — 2026-10-12

All planned phases are complete. The implementation includes both ingestion
paths, evidence-aware validation and review, planner output, compatibility
export, snapshot deltas, a deterministic recommendation audit, fixtures,
integration tests, and operator documentation. The audit gates inline
progression clauses before assigning synergy credit, de-duplicates a Habit
enhancement from its parent Command, compares the Dragon's Army-adjusted level-curve capacity proxy
for capacity-sensitive objectives, and uses Power only when the roster is
fully comparable. Manual end-to-end testing with real player inputs remains
the requested post-review step. In the normal workflow the user supplies a
JSON-file path or screenshot-folder path and the agent performs the ingestion
and review; the user is not expected to run commands. This is intentionally
not recorded as automated acceptance.

