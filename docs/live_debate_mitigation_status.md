# Live Debate Mitigation Status

## Current State

The live mitigation runner support, smoke dataset builder, and analyzer are implemented.

## Smoke Outcome

The small smoke pass confirmed:

- the live runner can execute the mitigation conditions
- raw history is preserved in `initial_raw`, `final_raw`, and `transcript_raw`
- the analyzer can aggregate multiple condition outputs

The smoke also showed that the current live path is usable for diagnostic work, but it is not a final result.

## Deferred Work

The partial9 live mitigation run is postponed until a longer backend window is available.

## Conditions In Scope

- `independent`
- `full_context_debate`
- `answer_hidden_debate`
- `numeric_masked_debate`
- `commit_then_numeric_masked_debate`

`answer_hidden_numeric_masked_debate` remains optional for later.

## Artifact Policy

Keep `runs/*`, raw JSONL, logs, generated summaries, and smoke reports out of version control.
