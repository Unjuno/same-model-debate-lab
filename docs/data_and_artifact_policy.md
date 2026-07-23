# Data and Artifact Policy

## Preservation rule

Experimental data is irreplaceable research evidence and must not be deleted, truncated, or overwritten. This includes raw JSONL, run configurations, summaries, logs, generated benchmark subsets, and local metadata needed to reproduce an analysis.

The `runs/` and benchmark JSONL paths are intentionally ignored by Git because they can be large or machine-local. Ignored does not mean disposable: they must be backed up separately and retained alongside the repository revision used to create them.

## Analysis rule

Analysis scripts must read raw artifacts without modifying them. Derived reports, tables, and plots belong under `results/` and should record:

- source dataset and raw-run glob;
- model, backend, prompt/protocol, and repeat count;
- aggregation unit and metric definitions;
- uncertainty method and limitations;
- the code command used to regenerate the artifact.

## Cleanup rule

Repository cleanup may reorganize documentation, scripts, and derived artifacts. It must not remove experimental evidence. Before any potentially destructive operation, create a dated backup or archive and obtain explicit confirmation.

## Current retained experiment

The GSM8K partial9 repeated live mitigation experiment contains 100 raw run directories: 20 repeats for each of five conditions, covering 9 items per repeat. The derived report and SVG plots are in [results/live_mitigation_partial9_repeated](../results/live_mitigation_partial9_repeated/).
