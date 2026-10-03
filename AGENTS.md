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
- `.agents/skills/add-dragon/`: screenshot-complete dragon ingestion workflow.
- `Game_Details/Resources/`: extraction scripts plus the historical working resource set.
- `Game_Details/Resources/_snapshots/`: ignored, local-only installed-client snapshots and their analyses.
- `projects/`: data foundation, encyclopedia, combat explorer, counter assistant, and related tools.

## Evidence Order

Use the following authority order for recommendation-critical claims:

1. Current user-supplied or repository screenshots showing exact in-game text.
2. Canonical screenshot-audited dragon JSON and mechanics files.
3. Curated installed-client evidence with an explicit snapshot/build date.
4. Official current web material.
5. Community sources as discovery or strategy hypotheses only.

Client presence proves that data exists in an installed build. It does not by itself prove release status, server activation, player availability, final balance, or that a staged event is live. Preserve this distinction in data, documentation, and agent responses.

## Local Client Capture

### Known environment

- Android emulator: MuMu Player, with CLI version `6.8.0.0` observed on 2026-10-01.
- MuMu tools directory: `C:\Program Files\Netease\MuMuPlayer\nx_main`
- CLI: `mumu-cli.exe`
- ADB client: `adb.exe`
- Emulator instance used by the current local snapshots: VM index `0`, Android 15.
- Game package: `com.wb.goog.hotd.socialstrategy`

Do not hard-code the ADB port or `/data/app/...` installation directory. MuMu can assign a different port, and Android changes the hashed package path after installs or updates. Discover both on every capture.

### Minimal-impact capture policy

- Use ordinary read-only ADB listing and pull operations.
- Do not launch the game solely to copy files. Starting the emulator is sufficient when the downloaded resources are already current.
- Do not write into the emulator, modify the APKs, attach instrumentation, alter security settings, or attempt to conceal activity from monitoring or anti-cheat systems.
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

If VM `0` is stopped, start the existing MuMu manager and instance through the supported CLI. Some installations require `MuMuNxMain.exe` to be started once before `control launch` can connect.

```powershell
& $mumu main launch
& $mumu control --vmindex 0 launch
& $mumu info --vmindex 0
```

If `control launch` returns `mainnx connect failed`, start the installed main process, then retry the same control command:

```powershell
$mumuMain = 'C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuNxMain.exe'
Start-Process -FilePath $mumuMain -WindowStyle Hidden
& $mumu control --vmindex 0 launch
```

Do not repeatedly launch additional manager processes. Confirm the player state with `info --vmindex 0` and continue only when `is_android_started` and `is_process_started` are true.

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
& $mumu control --vmindex 0 shutdown
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
- `Game_Details/Resources/_snapshots/2026-10-01/analyze_update.py`: repeatable example that hashes resources, decodes changed non-map protobufs, compares rows, and diffs localization.
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

## Latest Local Findings

The 2026-10-01 local snapshot compares client `26.9.56700` (`versionCode` 326) with the 2026-09-16 snapshot of `26.9.56160`.

High-confidence Strategist-relevant findings:

- Commander trait affinities were added for Corlys, Criston, Daemon, young Alicent, and young Rhaenyra.
- Criston, Daemon, and young Alicent received complete named three-talent kits instead of placeholder dragon habits.
- Corlys and young Rhaenyra talent behavior changed materially, including trait gates, mitigation targets, status choice, and Tile Damage effects.
- Meleys gained explicit Relentless and Physical DPS labels.
- Reflect now distinguishes specified damage categories, includes a one-effect-per-target limit, and has a dedicated `ability_label_reflect_damage` label.
- Smoketail's Ember Snare text now names its ongoing Fire damage status as Burn.
- New targeter/condition rows distinguish left flank, right flank, Vanguard, Dominant/Stalwart composition, and several Control statuses.
- Four Alpha savage-dragon spawn rows were added.
- The snapshot added 221 `Westeros_*` logical resources but changed no existing logical map resource, consistent with cache completion rather than a map revision.

Consult the local snapshot report and machine-readable manifests for exact IDs and row-level changes. Before incorporating these findings into canonical data or the Strategist agent, decide whether each item is a durable mechanic, staged content, or a current live rule, and preserve uncertainty explicitly.

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

- Check `git status --short` before and after work. Preserve unrelated user changes and confirm that local snapshots remain ignored.
