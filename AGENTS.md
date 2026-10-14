# Dragonfire Repository Instructions

This repository is an evidence-oriented knowledge base and tool suite for *Game of Thrones: Dragonfire*. Preserve exact source wording, separate observed facts from inference, and do not silently promote staged client content to live player-facing behavior.

## Repository Map

- `RECOMMENDATION_HANDOFF.md`: compact discovery and reasoning handoff for formation recommendations.
- `data/dragons/*.json`: canonical normalized dragon profiles.
- `data/game_mechanics.json` and `data/effects.json`: shared mechanics and status definitions.
- `data/dragon_application_knowledge.json`: installed-client roster, progression, ability templates, and evidence status.
- `data/live_updates.json`: first-party client discoveries that may not yet be screenshot-complete or live.
- `wiki/`: human-readable source-audited documentation.
- `.github/agents/dragonfire-strategist.agent.md`: the user-facing Strategist agent definition.
- `.github/agents/dragonfire-combat-analyst.agent.md`: the local report interpretation and evidence-review workflow.
- `data/combat_report_rules.json` and `data/combat_report_observations.json`: canonical reviewed report mappings and portable evidence.
- `data/community_simulation_reference.json`: reviewed public simulator constants,
  benchmarks, and formation hypotheses for sensitivity checks; not a live combat formula.
- `.agents/skills/add-dragon/`: screenshot-complete dragon ingestion workflow.
- `Game_Details/Resources/`: extraction scripts plus the historical working resource set.
- `Game_Details/Resources/_snapshots/`: ignored, local-only installed-client snapshots and their analyses.
- `projects/recommendation-planner/`: deterministic single-formation, portfolio, and
  multi-matchup planning with validated JSON and Markdown reports.
- `projects/roster-ingestion/`: evidence-aware Formation Forge and screenshot roster
  ingestion that emits planner-ready profiles.
- `projects/`: data foundation, encyclopedia, combat explorer, counter assistant, and related tools.

## Evidence Order

Use the following authority order for recommendation-critical claims:

1. Current user-supplied or repository screenshots showing exact in-game text.
2. Canonical screenshot-audited dragon JSON and mechanics files.
3. Curated installed-client evidence with an explicit snapshot/build date.
4. Official current web material.
5. Explicitly reviewed cross-site verification, usable only with its recorded source
   disclosure and always subordinate to contradictory current-client evidence.
6. Unreviewed community sources as discovery or strategy hypotheses only.

Client presence proves that data exists in an installed build. It does not by itself prove release status, server activation, player availability, final balance, or that a staged event is live. Preserve this distinction in data, documentation, and agent responses.

## Multi-Matchup Recommendations

For several enemy formations, follow the batch contract in
`projects/recommendation-planner/README.md` even when the caller has not selected the
custom Strategist agent. Transcribe the supplied roster, run
`projects/recommendation-planner/recommend.mjs` through its CLI, and use its validated
Markdown report as the answer. Keep the complete report and cite its selected and primary
candidate IDs. Do not replace the report's coverage or baseline tables with manually
authored ones. Preserve explicit distinctions between observed roster facts, assumed
selectable troops, and reference enemy progression.

Use `independent_matchups` only when the user explicitly wants separate hypothetical
answers that need not be deployed together. If the user asks for a numbered set of
formations to deploy—even against several enemies—the non-overlapping portfolio contract
below takes precedence.

## Multiple-Formation Recommendations

When the user asks for any number greater than one of formations, armies, marches, or
compositions, assume the dragons must be non-overlapping unless the user explicitly
allows reuse. For a general PvE, tile, or troop-preservation request, use one
`formation_portfolio` planner input with the requested `formation_count` and
`reuse_policy: disjoint_armies`. Do not choose one formation and repeatedly rerun after
removing its dragons. Use the validated generated Markdown report and preserve its
candidate IDs, global-allocation attestation, preservation evidence, capacity-proxy
disclosure, risks, and common-baseline dispositions.

Resolve `competitive_context` through `data/recommendation_rules.json`. Endgame ordinary
combat excludes unsupported Rare dragons from a qualified selection while retaining them
for audit; Thunderstrike and Shadowrend are reviewed exceptions, and Siege is separately
scoped. Do not enable `allow_unproven_rare` without an explicit user request. Treat the
formations in `data/common_formations.json` as expert-recommended priors, not neutral test
controls. When endgame Power is not comparable and a complete legal expert portfolio
exists, use it as the conservative default and retain the mechanics-ranked portfolio as
an alternative. `validation.valid` is structural only; a definitive recommendation also
requires `strategic_qualification.qualified`.

For screenshot rosters, the agent—not the user—performs the reviewed transcription through
`projects/roster-ingestion/roster.mjs`. Record and validate the visible-card count, retain
the ignored local profile/input/report together, and stop on a mismatch. Planner CLI work
uses saved input and output files; do not pass inline JSON through PowerShell.

## Local Client Capture

### Known environment

- Android emulator: MuMu Player, with CLI version `6.8.3.0` observed on 2026-10-10 (`6.8.0.0` was observed on 2026-10-01).
- MuMu tools directory: `C:\Program Files\Netease\MuMuPlayer\nx_main`
- CLI: `mumu-cli.exe`
- ADB client: `adb.exe`
- Existing main-account instance display name: `Bikeknife`.
- Dedicated throwaway research instance display name: `TrikePistol`.
- Emulator instance used by the 2026-10-01 local snapshots: VM index `0`, Android 15. Do not infer a current display name or reuse this index without discovery.
- Game package: `com.wb.goog.hotd.socialstrategy`

Do not hard-code the VM index, ADB port, or `/data/app/...` installation directory. MuMu can reorder instances or assign a different port, and Android changes the hashed package path after installs or updates. Discover all three on every capture.

### Instance identity and research boundary

- Treat MuMu display names as mandatory safety labels, not as assumptions about VM indexes. At the start of every emulator task, run `mumu-cli.exe info --vmindex all`, resolve the requested display name to exactly one VM index, and record the name, index, and reported ADB endpoint. Stop if the name is missing, duplicated, or ambiguous.
- `Bikeknife` is the user's main-account instance. It is restricted to the minimal-impact capture policy below. Never use it for root access, private app-data access, runtime instrumentation, memory inspection, traffic interception, client modification, or experimental security-setting changes.
- `TrikePistol` is the user-designated throwaway research instance. Repository work may launch the game there and, when relevant to a documented investigation, inspect the game's private files, use emulator-provided root or debugging access, attach runtime instrumentation to the game process, inspect the game's in-process state, and observe the game application's own network behavior.
- Authorization for `TrikePistol` does not extend to `Bikeknife`, the host's unrelated data, other applications, other accounts, other players, or publisher infrastructure. Do not collect Google or WB credentials, reusable authentication tokens, payment data, contacts, messages, or unrelated analytics identifiers. If such material appears incidentally, do not persist it and redact it from reports.
- Privacy separation is permitted; evasion is not. `TrikePistol` may use a separately created MuMu instance, distinct Google and game identities, separate host-side working directories and evidence stores, an explicit ADB-endpoint allowlist, and network segmentation such as a guest network or dedicated firewall profile. These controls may prevent accidental cross-instance access and reduce unnecessary linkage, but must not be represented as anonymity. Do not spoof device identity, rotate identifiers or network origins to defeat enforcement, hide instrumentation from the game, suppress security telemetry, or circumvent an account or device restriction.
- Research automation on `TrikePistol` is permitted when it reproduces ordinary client inputs for setup, navigation, evidence capture, or repeatable non-competitive experiments. Document the script, input sequence, rate, and expected server-visible effects. Do not automate competitive play, resource farming, matchmaking, ranking, purchases, rewards, or interactions that disadvantage another player or create an in-game advantage.
- Ordinary actions performed through the unmodified client may create expected server-side state on the throwaway account; this alone is not prohibited. Do not forge, tamper with, replay, or directly issue protocol requests to obtain unintended results; alter purchases, currency, inventory, rewards, match outcomes, or another user's data; exploit publisher infrastructure; or bypass server authorization or validation.
- Runtime instrumentation may observe the user's own `TrikePistol` client, but authorization does not include bypassing anti-cheat or other access controls. If a protection blocks an experiment, stop and record the limitation rather than concealing the tool, patching the protection, or changing fingerprints to evade detection.
- Prefer read-only collection and observation. Any change needed to enable research on `TrikePistol` must be limited to that instance, documented in the investigation notes, and reversible where practical. Preserve original APKs, libraries, metadata, and relevant configuration hashes before patching or transformation. Do not present behavior observed in a modified client as ordinary live-client behavior.
- Keep `TrikePistol` artifacts local and ignored by Git until they are reviewed and sanitized. Use a distinct snapshot name such as `Game_Details/Resources/_snapshots/YYYY-MM-DD-trikepistol/`, and record the client version, package version, instance display name, VM index, collection method, modifications, and source hashes. Never commit account identifiers, secrets, raw private databases, tokens, or unsanitized traffic captures.
- Never copy private app or Android identity state between instances. This includes `/data/data` or `/data/user` trees, app databases and shared preferences, AccountManager data, keystores, backups, authentication state, Android or Google service identifiers, advertising identifiers, and push-registration tokens. Public APKs and static game resources may be compared as evidence, but do not import TrikePistol state into Bikeknife or vice versa.
- Before an invasive step, re-check that the selected VM is `TrikePistol`. Afterward, disconnect only its ADB endpoint and restore only processes or settings changed for that investigation. Never stop, reset, snapshot, clone, or modify `Bikeknife` as cleanup for a `TrikePistol` task.

### Minimal-impact capture policy

- This is the default policy for routine static captures on either instance and the maximum permitted scope on `Bikeknife`. The explicitly authorized research activities above are exceptions for `TrikePistol` only.
- Use ordinary read-only ADB listing and pull operations.
- Do not launch the game solely to copy files. Starting the emulator is sufficient when the downloaded resources are already current.
- Under this default workflow, do not write into the emulator, modify the APKs, attach instrumentation, alter security settings, or attempt to conceal activity from monitoring or anti-cheat systems.
- Do not pull the complete package data directory by default. It contains logs, analytics queues, caches, temporary offer art, and potentially account-adjacent data that are unnecessary for static gameplay analysis.
- Capture only installed APKs, the downloaded `Resources` directory, `Application.current-version`, and IL2CPP metadata unless a documented investigation requires more.
- Copy into a new dated snapshot. Never overwrite an earlier baseline.
- Keep snapshots local and ignored by Git. Do not make runtime tools depend on an ignored snapshot.
- If an agent starts MuMu for a capture, disconnect ADB and shut down only the instance/process it started when finished.

### Discovery sequence

Use PowerShell and the installed MuMu tools. Inspect state before starting anything:

```powershell
$mumu = 'C:\Program Files\Netease\MuMuPlayer\nx_main\mumu-cli.exe'
$adb = 'C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe'

& $mumu info --vmindex all
& $adb devices -l
```

After resolving the requested display name to `$vmIndex`, start only that instance through the supported CLI if it is stopped. Some installations require `MuMuNxMain.exe` to be started once before `control launch` can connect.

```powershell
$vmIndex = <resolved-index-for-requested-display-name>
& $mumu main launch
& $mumu control --vmindex $vmIndex launch
& $mumu info --vmindex $vmIndex
```

If `control launch` returns `mainnx connect failed`, start the installed main process, then retry the same control command:

```powershell
$mumuMain = 'C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuNxMain.exe'
Start-Process -FilePath $mumuMain -WindowStyle Hidden
& $mumu control --vmindex $vmIndex launch
```

Do not repeatedly launch additional manager processes. Confirm the display name and player state again with `info --vmindex $vmIndex`; continue only when the name still matches and `is_android_started` and `is_process_started` are true.

Read `adb_host_ip` and `adb_port` from the final `info` output. Connect with the reported endpoint, then verify the package and build:

```powershell
$device = '127.0.0.1:<reported-port>'
$package = 'com.wb.goog.hotd.socialstrategy'

& $adb connect $device
& $adb -s $device shell pm path $package
& $adb -s $device shell dumpsys package $package |
    Select-String -Pattern 'versionName=|versionCode=|dataDir=|codePath='
```

`pm path` is the authoritative source for the current APK paths. The package currently uses `base.apk`, `split_EmbeddedAssets.apk`, and `split_config.arm64_v8a.apk`, but rediscover the list rather than assuming it remains unchanged.

### Static source paths

The useful external-data sources are:

```text
/sdcard/Android/data/com.wb.goog.hotd.socialstrategy/files/Resources
/sdcard/Android/data/com.wb.goog.hotd.socialstrategy/files/Application.current-version
/sdcard/Android/data/com.wb.goog.hotd.socialstrategy/files/il2cpp/Metadata/global-metadata.dat
```

The ARM64 split APK contains the native IL2CPP library when binary inspection is necessary. Retain the original APK and metadata hashes before extracting or analyzing them.

Before copying, inspect resource size and count:

```powershell
& $adb -s $device shell "du -sk /sdcard/Android/data/$package/files/Resources"
& $adb -s $device shell "find /sdcard/Android/data/$package/files/Resources -type f | wc -l"
```

Create a dated layout under `Game_Details/Resources/_snapshots/YYYY-MM-DD/`:

```text
apks/
android_data/com.wb.goog.hotd.socialstrategy/files/
  Application.current-version
  il2cpp/Metadata/global-metadata.dat
  Resources/
analysis/
decoded/old/
decoded/new/
```

Use `adb pull` for each discovered APK and for the three static sources above. Avoid the broader `/sdcard/Android/data/<package>` pull unless the user explicitly needs a non-static artifact and its privacy implications have been reviewed.

Finish by restoring the prior emulator state when applicable:

```powershell
& $adb disconnect $device
& $mumu control --vmindex $vmIndex shutdown
& $mumu main close
```

Do not shut down an emulator or manager that was already running for the user before the task.

## Resource Diff Method

Resource filenames commonly include a ten-digit content version, for example `dragonTable_merged.1789415363.pb`. Compare resources by logical name after replacing the version segment with `.VERSION`, then hash the content. This separates:

- added or removed logical resources;
- byte-changing updates;
- version-only renames with identical bytes.

Relevant local tools:

- `Game_Details/Resources/_pbdump.py`: schema-less protobuf decoder.
- `Game_Details/Resources/_parse_locale.py`: locale delta parser.
- `Game_Details/Resources/analyze_update.py`: reusable analyzer that hashes logical resources, decodes changed non-map protobufs, compares rows and localization, and routes changed resource domains to repository consumers without editing them.
- `Game_Details/Resources/_snapshots/2026-10-01/analyze_update.py`: historical snapshot-specific example retained for reproducibility.
- `Game_Details/Resources/_snapshots/2026-10-01/analysis/update_report.md`: human-readable example report.

The analyzer uses protobuf field `1` and its nested textual identifier where possible as a stable row key. Because this is schema-less decoding, numeric field paths are evidence of change but not authoritative semantic field names. Corroborate behavior with localization, cross-table references, known schemas, screenshots, or code inspection.

### Triage rules

- Start with `resource_manifest.json` to distinguish content changes from version bumps.
- Review changed gameplay protobufs before large `.unity3d` bundles.
- Compare both `Deltas_enUS.*.txt` and `enUS.*.txt`. The delta file often carries staged or newly delivered strings while the base locale remains unchanged.
- Treat added `Westeros_*` chunks cautiously. Additional files with no changed logical counterparts often mean the emulator cache became more complete, not that terrain or POIs changed.
- A table moving from `.pb` to `.json` is a format migration, not necessarily a feature removal. The 2026-10-01 snapshot did this for `DailyQuestTable`.
- Large quest, task, shop, or event additions may be campaign staging. Record them, but require activation evidence before calling them live.
- Record snapshot date, client version, package version code, capture scope, source hashes, comparison baseline, and analyzer version in every report.

## Combat Report Video Extraction

Use `projects/combat-report-extractor/combat_report_extractor.py` for user-supplied
combat-report recordings. Read its README before running it. The workflow is local-only:
it must not upload recordings or frames, connect to the game, attach instrumentation,
intercept TLS, inspect memory, or modify the emulator.

Treat the user's ownership convention as authoritative: blue action backgrounds and blue
dragon names are the user's side; red backgrounds and red names are the enemy side. Run
the extractor into a dated ignored snapshot under
`Game_Details/Resources/_snapshots/<date>/analysis/`. Preserve `ocr_frames.json`,
`combat-report.json`, `insights.md`, and their cited frames together for audit. Reparse
retained OCR instead of rerunning expensive video decoding when only parser logic changes.

The generated totals describe successfully parsed text visible in sampled frames. They
are not server totals. Read `coverage.warnings` and inspect cited frames before using a
claim. Never silently repair ambiguous OCR, infer a missing round, or assign an unknown
side. Unsupported records remain raw evidence or rejected actions until visually
corroborated. Keep recordings, extracted frames, OCR runs, local virtual environments,
and downloaded model/runtime files ignored by Git.

## Combat Report Interpretation

Use `projects/combat-report-extractor/combat_report_interpreter.py` only after a
`combat-report.json` exists. The interpreter is a local-file transform and must not
launch MuMu, connect ADB, inspect the game, capture traffic, use instrumentation, or
upload evidence. It accepts extractor schema `1.0.0`, preserves every source action,
and adds annotations with stable event IDs and input/rule hashes.

Validate `data/combat_report_rules.json` and `data/combat_report_observations.json` with
`projects/combat-report-extractor/validate_combat_report_rules.py`. Keep observed,
derived, inferred, and unknown claims distinct. Treat timing relationships as
correlations unless independent evidence establishes more. `rule-candidates.json` is an
ignored local review queue and must never be promoted automatically.

One-command ingestion also writes `combat-measurements.json` and
`combat-measurements.md`. These group multiple result cards under one activation, keep
observable and unknown RNG opportunities separate, and annotate later outcome samples
with effect exposure. Group repeated runs with `-Experiment`, `-Variant`, and
`-Question`, then aggregate their measurements with
`combat_empirical_analyzer.py aggregate`. Local measurements and aggregates are not
canonical evidence.

Committed observations must be portable and reviewed: no account identifiers, absolute
local paths, raw recordings, or unreviewed claims presented as established. Preserve all
supporting and contradicting observation references. The Strategist must not consume
draft/disputed rules or generated local reports. Only an accepted, corroborated,
canonical-text-compatible durable mechanic may enter the separate review proposal
described in `wiki/Combat-Report-Interpretation.md`; that proposal does not mutate
Strategist or canonical mechanic data automatically.

Reviewed cross-report metrics belong in `data/combat_empirical_findings.json`. The
Strategist may consume only accepted, corroborated findings with
`recommendation.eligible: true` and an approved Strategist gate. Missing report text is
never a failed proc, and exposure-correlated damage or Recovery is not an isolated
causal effect without a controlled comparison.

## Classified Local Findings

The 2026-10-01 local snapshot compares client `26.9.56700` (`versionCode` 326) with the 2026-09-16 snapshot of `26.9.56160`.

The following findings have already been classified and must not be reopened merely
because they originated in an installed snapshot:

- Meleys and Smoketail are user-confirmed available and their complete records are
  `cross_site_verified`; they are recommendation-eligible only with source disclosure.
- Meleys' Relentless/Physical DPS labels, Reflect limit, and related mechanics are recorded
  in her canonical profile and `data/installed_evidence.json` with that same provenance.
- Smoketail's Ember Snare naming its ongoing Fire damage as Burn is likewise
  cross-site-verified and canonicalized.
- Installed targeter and condition rows are `corroboration_only`; use them to support
  explicit ability wording, never to invent targeting semantics.
- Commander affinities and talent changes for Corlys, Criston, Daemon, young Alicent, and
  young Rhaenyra remain `staged` and `exclude` for recommendations.
- Alpha savage-dragon rows and the additional `Westeros_*` cache files remain discovery
  evidence, not proof of live activation or a map revision.

Consult `data/installed_evidence.json`, the local snapshot report, and machine-readable
manifests for exact IDs and row-level changes. New findings still require lifecycle and
recommendation-use classification before incorporation.

## Editing and Validation

- Keep exact in-game wording in verbatim fields. Normalize only in derived fields.
- Update canonical JSON, human-readable wiki material, handoff data, and generated project data together when a fact crosses those boundaries.
- Do not hand-edit generated files when a repository build script owns them.
- Run the narrowest relevant tests first, then shared-data and consumer tests when changing common schemas or mechanics.
- For encyclopedia data changes, run:

```powershell
python projects/game-data-encyclopedia/scripts/build.py
python -m unittest discover -s projects/game-data-encyclopedia/tests -v
```

- For Strategist, planner, engine, or roster-workflow changes, run the affected focused
  suites and the Strategist contract suite:

```powershell
node --test projects/recommendation-planner/tests/planner.test.mjs
node --test projects/counter-picking-assistant/tests/engine.test.mjs
node --test projects/roster-ingestion/tests/roster-ingestion.test.mjs
python -m unittest discover -s projects/strategist-evaluation/tests -v
python -m unittest discover -s projects/combat-report-extractor/tests -p test_documentation.py -v
```

- `data/recommendation_rules.json` is the machine-readable decision and portfolio
  contract. The planner README owns CLI and report schemas; `RECOMMENDATION_HANDOFF.md`
  owns mechanics discovery and field interpretation; the Strategist agent owns runtime
  routing and response behavior; this file owns repository-wide workflow and validation.
  Prefer references across these boundaries instead of copying detailed policy text.

- Check `git status --short` before and after work. Preserve unrelated user changes and confirm that local snapshots remain ignored.
