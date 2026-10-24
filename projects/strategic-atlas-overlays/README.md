# Strategic Atlas

The Atlas offers Season 1 / Alpha, Season 2 / Bravo, and Season 3 / Charlie.
Plain visits open Charlie. Select another campaign from **Map version**, or link
with `?season=season1`, `?season=season2`, or `?season=season3`.

## Charlie source and scope

The October 23, 2026 read-only installed-client capture contains
`Westeros_Charlie_3_ScalingRuins`, including the POI R-tree, map description,
region-index texture, backgrounds, and cached terrain chunks. The user reported
playing campaign Charlie. Client version is `26.10.57632`, package version code
`337`. Only downloaded Resources and `Application.current-version` were copied;
the running game was left running and the capture ADB endpoint was disconnected.

All **8,039 POI placements** resolve to template keys without ambiguity. Bravo has
7,912 placements. This is a different layout, not just 127 additions: matching
coordinates, template keys, and footprint dimensions finds 1,032 identical
placements, 7,007 Charlie-only entries, and 6,880 Bravo-only entries. These counts
do not identify movements of individual objects.

Named seats present in Charlie but absent from the Bravo placement list:

| Seat | X | Y |
| --- | ---: | ---: |
| Kingswood | 1520 | 927 |
| Tumbleton | 1194 | 1019 |
| Hayford | 1225 | 1136 |
| Antlers | 1485 | 1232 |

The generated season directory contains the CSV placements, region labels,
inferred crossing edges, browser assets, and `source_manifest.json`, which records
source and output SHA-256 hashes and builder versions. Raw captures remain ignored.
Static POIs do not establish current ownership, seat upgrades, or live scaling.
Ruin template levels range from 1 through 5; their live levels may differ.

There are 183 captured terrain chunks. Unknown terrain remains unknown and uses
the existing geographic routing fallback; it is never filled with Bravo terrain.
Routes are estimates and crossing connections are inferred from proximity.
The 2080×3312 region texture ends 57,428 pixels before its declared extent; those
trailing pixels remain zero/ocean. 997 POIs have no region label in the decoded
texture and remain unassigned rather than receiving guessed labels. The map
positions themselves come directly from the complete captured POI R-tree.

## Build and publication

`Game_Details/Resources/_build_atlas_season.py` runs the existing extraction
builders in a new isolated workspace, with an explicit map prefix and campaign
label. It uses one captured resource set, checks required spatial files, rejects
unresolved POI templates, and records source/output hashes. Existing output
directories are rejected to preserve previous builds. Example from the repo root:

```powershell
python Game_Details/Resources/_build_atlas_season.py `
  --resource-dir Game_Details/Resources/_snapshots/2026-10-23-charlie/android_data/com.wb.goog.hotd.socialstrategy/files/Resources `
  --work-dir .tmp-charlie-rebuild/work `
  --output-dir .tmp-charlie-rebuild/output `
  --map-prefix Westeros_Charlie_3_ScalingRuins --campaign Charlie `
  --source-label 'October 23, 2026 installed client 26.10.57632 (337)' `
  --snapshot-date 2026-10-23
```

After reviewing the build, copy its generated files together into
`Game_Details/Resources/_extracted/seasons/season3/`. Do not edit generated HTML or
CSV. Publish all three maps with:

```powershell
python Game_Details/Resources/_publish_atlas_maps.py --output-dir .tmp-atlas-preview/map
node --test projects/strategic-atlas-overlays/tests/selector.test.mjs
python -m unittest discover -s projects/strategic-atlas-overlays/tests -v
```

The publisher creates the selector, three HTML pages, and separate image assets.
GitHub Pages and the encyclopedia's local preview use this same publisher.

The encyclopedia catalog still contains Bravo placement IDs. Existing unscoped
`?node=` links therefore continue to open Bravo. Explicit season links take
precedence, and changing seasons clears the selected node. Alpha and Charlie
offer a link to the general encyclopedia map index rather than an unrelated Bravo
record. A Charlie link to Antlers is
`?season=season3&node=map-node%3A003832`.
