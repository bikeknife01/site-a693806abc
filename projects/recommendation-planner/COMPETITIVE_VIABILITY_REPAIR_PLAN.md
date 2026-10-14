# Competitive viability repair plan

This checklist tracks the 2026-10-13 repair prompted by a structurally valid but
strategically implausible endgame portfolio. Keep it until the implementation,
tests, documentation, and final repository review are complete.

- [x] Define a canonical endgame-viability policy without turning rarity into a
  universal strength score.
- [x] Record the reviewed Rare-dragon exceptions (Thunderstrike, Shadowrend, and
  Siege-scoped use) and an explicit caller override.
- [x] Promote the three user-confirmed expert formations from neutral comparison
  controls to evidence-bearing recommendation priors.
- [x] Infer or accept competitive context and retain strategically ineligible
  candidates for audit without selecting them when a qualified portfolio exists.
- [x] Compare a complete legal expert portfolio and use it as the conservative
  default when endgame Power is not comparable.
- [x] Replace raw ability-count objective scoring with de-duplicated,
  magnitude/reliability-aware ordinal components.
- [x] Separate structural output validation from strategic qualification in JSON
  and Markdown.
- [x] Update the Strategist, planner, handoff, and repository contracts.
- [x] Add regression and holdout coverage for endgame Rare use, exceptions,
  expert-prior selection, explicit overrides, and known-Power displacement.
- [x] Run focused and shared validation suites, inspect the generated retained
  roster result locally, review the diff, and commit the completed repair.
