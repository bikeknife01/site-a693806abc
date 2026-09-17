# Shared Data Foundation

The first implemented foundation slice normalizes the repository's canonical dragon,
ability, effect, and progression records into the compact dataset consumed by the
Game-Data Encyclopedia. It reads only tracked normalized JSON; ignored snapshots and
raw protobuf data are never runtime dependencies.

Ability interpretation is emitted as a first-class graph of schedules, conditions,
targeters, prioritizers, and status operations. Every graph record references a stable
ability ID and preserves the exact phrase used for its conservative normalization.

## Build and validate

```powershell
python projects/shared-data-foundation/src/normalize/build_encyclopedia_data.py
python projects/shared-data-foundation/src/normalize/build_encyclopedia_data.py --check
```

The output is deterministic for the same inputs. Its manifest records the SHA-256 of
every input, while entity facts retain evidence class, source, client version, and
uncertainty. Stable IDs come from installed-client logical keys. Effects without a
client key use a versioned, normalized effect registry ID.

The normalizer also compares current entity fingerprints with the checked-in compact
baseline and writes `changes.json`. It ignores JSON key ordering and formatting, but
reports added, removed, or changed stable records and the specific semantic fields
that differ. The baseline changes only with an explicit reviewed command:

```powershell
python projects/shared-data-foundation/src/normalize/build_encyclopedia_data.py --update-baseline
```

## Current boundary

This slice implements combat-reference entities and semantic history only. Map,
economy, raw snapshot selection, and full diagnostic output remain planned. Anonymous
decoded fields are not consumed.
