# Strategic Atlas Overlays

## Project description

Extend the existing interactive Atlas with optional analytical overlays that answer operational questions about resources, encounters, accessibility, chokepoints, garrisons and POI reach. Preserve the existing coordinate search, POI filters and route calculator.

## Primary user questions

- Where are the highest concentrations of a selected resource or encounter?
- Which low-level crossings connect my start and destination?
- Which POIs or regions become isolated if a transit point is unavailable?
- What can be reached from a garrison or coordinate within a selected route budget?
- Where should an alliance stage armies to cover multiple objectives?
- Which route is fastest, safest, lowest-transit-level or least exposed?

## Player-profile decisions

- Building timers are irrelevant and excluded.
- March distance/time remains relevant because it affects reinforcement and coordination.
- Player/alliance ownership is optional user-entered or imported session data; it is not assumed to exist in static client files.
- Staged future-map records remain hidden unless explicitly enabled.

## Existing related files

- `Game_Details/Resources/_extracted/interactive_map.html`
- `Game_Details/Resources/_build_interactive_map.py`
- `Game_Details/Resources/_build_map_nodes.py`
- `Game_Details/Resources/_build_terrain_data.py`
- `Game_Details/Resources/_build_region_data.py`
- `Game_Details/Resources/_build_crossing_chains.py`
- `Game_Details/Resources/_stress_test_routes.py`
- `Game_Details/Resources/_extracted/clean_map_nodes.csv`
- `Game_Details/Resources/_extracted/crossing_chains.json`
- `Game_Details/Resources/_extracted/region_boundaries.json`
- `Game_Details/Resources/_extracted/region_fill_data.json`
- `Game_Details/Resources/_extracted/route_stress_report.json`
- Bravo POI R-tree, terrain, resource, region and obstruction chunks under `Game_Details/Resources/`

## Proposed project files

```text
projects/strategic-atlas-overlays/
  PROJECT_PLAN.md
  src/
    overlays/
      resources.*
      encounters.*
      reachability.*
      chokepoints.*
      garrison-coverage.*
      route-alternatives.*
    state/
    ui/
  tests/
    route-fixtures/
    overlay-fixtures/
  README.md
```

Implementation may ultimately remain in the existing Atlas builder; this folder owns specifications and tests even if production code is integrated into `Game_Details/Resources/_build_interactive_map.py`.

## Overlay catalog

### Resource density

- Select resource type and optional node level.
- Heatmap density within a selectable radius.
- Show nearest cluster and route distance, not just straight-line distance.

### Encounter and challenge

- Encounter-level distribution.
- Recommended dragon-level ranges where available.
- Defender/challenge-rating filter.
- Optional link to Counter Picking or Combat Explorer using an encounter template.

### Transit accessibility

- Crossing/tunnel/bridge/harbor level overlay.
- Reachable-area flood fill respecting the active transit-level filters.
- Highlight which restriction prevents a route.

### Chokepoint and isolation analysis

- Identify graph articulation points and high-betweenness transit nodes.
- Select a crossing/POI to show regions and objectives disconnected if removed.
- Distinguish topological importance from current political importance.

### Garrison and staging coverage

- User places garrison/army origins.
- Isochrone-style route-distance coverage.
- Compare candidate staging points by objectives covered and worst-case distance.

### Route alternatives

- Shortest legal route.
- Lowest maximum transit level.
- Fewest transit nodes.
- Optional safer/more concealed route when an exposure model is defined.
- Clear explanation when no route satisfies active constraints.

## Work plan

### Phase A1 — Data readiness

- [ ] SAO-011 Audit resource, encounter and defender information available per map tile/node.
- [ ] SAO-012 Confirm coordinate transformations across every map dataset.
- [ ] SAO-013 Add stable node/edge IDs and overlay metadata to generated map data.
- [ ] SAO-014 Separate map-generation changes from local cache completeness.
- [ ] SAO-015 Define session-only ownership/garrison input format.

### Phase A2 — Overlay framework

- [ ] SAO-021 Create a common overlay interface: visibility, legend, filters and opacity.
- [ ] SAO-022 Add independent collapsible controls and URL/session state.
- [ ] SAO-023 Ensure overlays are lazy-loaded and do not slow initial map display.
- [ ] SAO-024 Add hover/click inspection with source and confidence.
- [ ] SAO-025 Preserve route line, temporary coordinate marker and POI selection layering.

### Phase A3 — Resource and encounter overlays

- [ ] SAO-031 Generate resource-density tiles or compact point datasets.
- [ ] SAO-032 Implement resource-type and level filters.
- [ ] SAO-033 Implement encounter/challenge heatmap and range filters.
- [ ] SAO-034 Rank nearby candidates by legal route distance.
- [ ] SAO-035 Validate counts against extracted source records.

### Phase A4 — Reachability and route alternatives

- [ ] SAO-041 Implement reachable-area calculation using the same legal graph as routing.
- [ ] SAO-042 Implement lowest-maximum-transit-level path.
- [ ] SAO-043 Implement route alternatives and comparative metrics.
- [ ] SAO-044 Explain blocked routes by terrain/transit constraint.
- [ ] SAO-045 Extend stress tests across representative coordinate pairs and filter ranges.

### Phase A5 — Chokepoints and staging

- [ ] SAO-051 Compute articulation points and disconnected components.
- [ ] SAO-052 Compute transit centrality with documented assumptions.
- [ ] SAO-053 Implement removal-impact visualization.
- [ ] SAO-054 Implement user-defined garrison coverage.
- [ ] SAO-055 Compare candidate staging locations against selected objectives.

### Phase A6 — Integration and validation

- [ ] SAO-061 Add deep links to Encyclopedia records.
- [ ] SAO-062 Add encounter handoff to Counter Picking/Combat Explorer.
- [ ] SAO-063 Verify overlays at multiple zoom levels and panel widths.
- [ ] SAO-064 Regression-test existing search, filters, coordinate marker and routes.
- [ ] SAO-065 Publish through the existing GitHub Pages workflow.

## MVP acceptance criteria

- Resource and encounter overlays can be toggled independently.
- Reachability respects impassable terrain and configured transit levels.
- At least two legal route strategies can be compared where alternatives exist.
- Chokepoint results identify the affected graph components.
- Existing Atlas behavior and performance remain intact.
- Ownership/garrison data stays local unless the user explicitly exports it.
