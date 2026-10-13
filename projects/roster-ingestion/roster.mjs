#!/usr/bin/env node

import path from "node:path";
import { fileURLToPath } from "node:url";
import { ingestFormationForge, ingestScreenshotTranscription } from "./src/ingest.mjs";
import { loadKnowledge, readJson, writeJsonExclusive, writeTextExclusive } from "./src/core.mjs";
import {
  diffSnapshots,
  formationForgeExport,
  readSnapshot,
  renderDiffReport,
  renderReviewReport,
  writeIngestionBundle,
} from "./src/outputs.mjs";
import { validateSnapshot } from "./src/validate.mjs";

function parseArgs(argv) {
  const result = { _: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg.startsWith("--")) result._.push(arg);
    else if (arg === "--overwrite") result.overwrite = true;
    else {
      const key = arg.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
      if (index + 1 >= argv.length || argv[index + 1].startsWith("--")) throw new Error(`${arg} requires a value.`);
      result[key] = argv[++index];
    }
  }
  return result;
}

function required(options, name) {
  if (!options[name]) throw new Error(`--${name.replace(/[A-Z]/g, letter => `-${letter.toLowerCase()}`)} is required.`);
  return options[name];
}

function usage() {
  return `Usage:
  node projects/roster-ingestion/roster.mjs ingest-site --input export.json --profile-id NAME --observed-at YYYY-MM-DD --output-dir DIR [--active-means owned|include] [--dragons-army-skill III --dragons-army-level 2]
  node projects/roster-ingestion/roster.mjs ingest-screenshots --input transcription.json --output-dir DIR [--dragons-army-skill III --dragons-army-level 2]
  node projects/roster-ingestion/roster.mjs validate --input roster.json [--report report.md]
  node projects/roster-ingestion/roster.mjs diff --before old/roster.json --after new/roster.json --output-dir DIR
  node projects/roster-ingestion/roster.mjs export-forge --input roster.json --output export.json [--template original-export.json]

Options:
  --knowledge PATH       Override the canonical encyclopedia dataset.
  --dragons-army-skill   Highest unlocked Dragon's Army skill: I, II, III, or IV.
  --dragons-army-level   Current level from 0-5. If both options are absent, assume no bonus.
  --overwrite            Replace generated outputs. Historical snapshots are protected by default.`;
}

function dragonsArmyOptions(options) {
  const hasSkill = options.dragonsArmySkill != null;
  const hasLevel = options.dragonsArmyLevel != null;
  if (hasSkill !== hasLevel) throw new Error("--dragons-army-skill and --dragons-army-level must be provided together.");
  return hasSkill ? { skill: options.dragonsArmySkill, level: options.dragonsArmyLevel, basis: "user_declaration" } : null;
}

export function main(argv = process.argv.slice(2)) {
  try {
    const options = parseArgs(argv);
    const command = options._[0];
    if (!command || command === "help") {
      process.stdout.write(`${usage()}\n`);
      return 0;
    }
    const knowledge = loadKnowledge(options.knowledge);
    if (command === "ingest-site") {
      const inputPath = required(options, "input");
      const snapshot = ingestFormationForge({
        inputPath,
        profileId: required(options, "profileId"),
        observedAt: required(options, "observedAt"),
        knowledge,
        activeMeans: options.activeMeans || "owned",
        completeness: options.completeness || "complete",
        dragonsArmy: dragonsArmyOptions(options),
      });
      const result = writeIngestionBundle({ snapshot, knowledge, outputDir: required(options, "outputDir"), rawInputPath: inputPath, overwrite: Boolean(options.overwrite) });
      process.stdout.write(`${JSON.stringify({ status: snapshot.review.status, planner_profile_written: Boolean(result.planner), output_dir: result.output_dir }, null, 2)}\n`);
      return result.validation.valid && result.planner ? 0 : 2;
    }
    if (command === "ingest-screenshots") {
      const inputPath = required(options, "input");
      const snapshot = ingestScreenshotTranscription({ inputPath, knowledge, dragonsArmy: dragonsArmyOptions(options) });
      const result = writeIngestionBundle({ snapshot, knowledge, outputDir: required(options, "outputDir"), rawInputPath: inputPath, overwrite: Boolean(options.overwrite) });
      process.stdout.write(`${JSON.stringify({ status: snapshot.review.status, planner_profile_written: Boolean(result.planner), output_dir: result.output_dir }, null, 2)}\n`);
      return result.validation.valid && result.planner ? 0 : 2;
    }
    if (command === "validate") {
      const snapshot = readSnapshot(required(options, "input"));
      const validation = validateSnapshot(snapshot, knowledge);
      if (options.report) writeTextExclusive(options.report, renderReviewReport(snapshot, validation), { overwrite: Boolean(options.overwrite) });
      process.stdout.write(`${JSON.stringify(validation, null, 2)}\n`);
      return validation.valid ? 0 : 2;
    }
    if (command === "diff") {
      const before = readSnapshot(required(options, "before"));
      const after = readSnapshot(required(options, "after"));
      if (before.profile_id !== after.profile_id) throw new Error("Cannot diff snapshots with different profile_id values.");
      const outputDir = path.resolve(required(options, "outputDir"));
      const diff = diffSnapshots(before, after);
      writeJsonExclusive(path.join(outputDir, "roster-diff.json"), diff, { overwrite: Boolean(options.overwrite) });
      writeTextExclusive(path.join(outputDir, "roster-diff.md"), renderDiffReport(diff), { overwrite: Boolean(options.overwrite) });
      process.stdout.write(`${JSON.stringify({ changes: diff.changes.length, regressions: diff.regressions.length, output_dir: outputDir }, null, 2)}\n`);
      return 0;
    }
    if (command === "export-forge") {
      const snapshot = readSnapshot(required(options, "input"));
      const validation = validateSnapshot(snapshot, knowledge);
      if (!validation.valid) throw new Error(`Roster is invalid: ${validation.errors.map(item => item.message).join("; ")}`);
      const template = options.template ? readJson(options.template) : [];
      writeJsonExclusive(required(options, "output"), formationForgeExport(snapshot, knowledge, template), { overwrite: Boolean(options.overwrite) });
      return 0;
    }
    throw new Error(`Unknown command: ${command}`);
  } catch (error) {
    process.stderr.write(`roster-ingestion: ${error.message}\n\n${usage()}\n`);
    return 2;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exitCode = main();

