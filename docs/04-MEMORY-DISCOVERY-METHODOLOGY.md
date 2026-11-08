# 04 — Memory discovery methodology

Discovery is a controlled, bounded experiment after M1 proves the read-only provider. Use `TrikePistol` only. Do not assume plaintext, contiguous records, a renderer-owned history, or persistence after a battle.

## Experiment ledger

Record one session per game build, instance, and acquisition generation. Annotate UTC and monotonic boundaries for: idle menu; combat initiation; active combat; individually visible actions; completion; report open; report close; second battle; app restart. Repeat each sequence at least three times with comparable idle/control windows. For each phase, record game-visible action labels from ordinary observation as independent reference evidence, along with uncertainty about timing. Do not treat OCR or client strings as server truth.

Start with only named, mapped, non-sensitive game regions. Capture small windows at a fixed interval and a predeclared byte budget. Record region identity, VA range, mapping generation, read status and latency. A changing VMM mapping invalidates the current series. A larger region comparison is a separately approved, bounded research run with explicit start/end and quota; no continuous full-memory dumps. Filter likely credential, account, payment, auth and unrelated app data before persistence; do not store incidental secrets.

## Candidate search and controls

For each selected range, compute hash, byte-change count, run-length and entropy summaries per phase; compare against equal-duration idle/control windows. Search for **known non-sensitive combat labels or displayed numeric values** with explicit encodings and false-positive controls. Cluster repeated structures by aligned offsets, lengths and change timing. Test whether candidate deltas precede, coincide with, or follow annotated actions. Use randomized/shuffled event times as a null control. Treat temporal association as correlation.

Classify candidates as numeric scalar, text, repeated record, variable-length sequence, ring buffer, object collection, event queue, serialized payload, or unknown binary. For each candidate keep: region and mapping generation; observed lifetime; update frequency; inferred type; structural evidence; relation to visible activity; controls; confidence; competing interpretations; and the next falsification test. Never equate an address or byte pattern with a semantic field solely because it changes during battle.

## Validation ladder

1. Reproduce within one battle and across at least three battles.
2. Show a comparable idle period does not produce the same signature at the same rate.
3. Reacquire after app restart and demonstrate a structural locator, rather than a fixed absolute VA.
4. Recheck after emulator restart; new instance and app version are separate validation dimensions.
5. For a proposed event record, correlate multiple independently visible events with distinct actor/action/outcome evidence, including negative cases and ordering.
6. Quantify false matches, missed intervals, duplicate updates, and time alignment uncertainty before event extraction.

If candidate data exists only for a shorter interval than safe polling can capture, or cannot be separated from normal activity, mark that candidate infeasible. Do not defeat protections or substitute invasive instrumentation. Current-client observations may inform local analysis but are not automatically canonical mechanics.
