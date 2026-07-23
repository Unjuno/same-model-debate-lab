# Live Debate Mitigation Status

## Current State

The live mitigation runner support, repeated-run analyzer, and report are implemented. The partial9 live run is complete: 20 repeats across five conditions, with 100 raw run files and 900 item-level outputs.

## Smoke Outcome

The small smoke pass confirmed:

- the live runner can execute the mitigation conditions
- raw history is preserved in `initial_raw`, `final_raw`, and `transcript_raw`
- the analyzer can aggregate multiple condition outputs

The smoke also showed that the current live path is usable for diagnostic work, but it is not a final result.

## Repeated-Run Result

The report is available at [results/live_mitigation_partial9_repeated/report.md](../results/live_mitigation_partial9_repeated/report.md). It summarizes each repeat as one 9-item unit and includes 95% exploratory confidence intervals and paired accuracy differences versus `independent`.

Headline final accuracy means:

- `independent`: `0.678`
- `full_context_debate`: `0.672`
- `answer_hidden_debate`: `0.672`
- `numeric_masked_debate`: `0.650`
- `commit_then_numeric_masked_debate`: `0.633`

The paired accuracy differences versus independent all have confidence intervals crossing zero. These results are descriptive and do not establish a general mitigation effect.

## Conditions In Scope

- `independent`
- `full_context_debate`
- `answer_hidden_debate`
- `numeric_masked_debate`
- `commit_then_numeric_masked_debate`

`answer_hidden_numeric_masked_debate` remains optional for later.

## Artifact Policy

Keep `runs/*`, raw JSONL, logs, generated summaries, and smoke reports out of version control.
