# Current Aggregation Logic

This note documents the current code path used by `smdebate` for final answer selection in the local CLI.

## Final Answer Selection

- Final answer selection is based on the `final_answers` list from the last round that was run for the item.
- The CLI uses `majority_vote(final_answers)` in `src/smdebate/cli.py`.
- For `independent`, `final_answers` are the initial answers.
- For `debate_1r`, `final_answers` are the answers after one shared round.
- For `debate_3r_full_context`, `final_answers` are the answers after the configured number of rounds.

## Are All Rounds Considered?

- No. The final answer is not selected from all rounds.
- The code records `initial_raw`, `final_raw`, and `transcript_raw`, but aggregation only uses the last round's answers.

## Are Empty Answers Ignored?

- No explicit filtering removes empty answers before `majority_vote`.
- If a failure produces `answer=""`, that empty string can participate in the vote like any other string.
- This matters when a timeout or extraction failure leaves one agent blank and the other agents still answer normally.

## What Happens After `APITimeoutError`?

- The agent call is wrapped in `_invoke_agent`.
- `APITimeoutError` is caught when the dependency is available.
- The failed call returns an `AgentResponse` with:
  - `answer=""`
  - `extraction_failed=True`
  - compact `raw_text` error marker
- The run continues unless `SMDEBATE_CONTINUE_ON_ERROR=0` is set and the error is not a timeout.

## Does Timeout Produce Empty Answer?

- Yes.
- The current error path returns `answer=""` for timeout failures.

## Is Previous Answer Carried Forward?

- No.
- A failed agent call does not automatically reuse the previous round's answer.
- The blank answer only affects the current round's `final_answers` and the vote for that item.

## How Is `answer_loss_rate` Computed?

- `answer_loss_rate` is computed in `src/smdebate/metrics.py`.
- It only counts rows where the initial answers contained at least one correct answer.
- For those rows, it measures how often the final answer is incorrect.
- In other words, it is the fraction of initially recoverable items that were lost by the final selection.

## How Is `oracle_at_k` Computed?

- `oracle_at_k` is also computed in `src/smdebate/metrics.py`.
- It is the fraction of items where at least one initial answer was correct.
- It does not depend on the final selection.

## Notes

- The current aggregation logic is intentionally simple and transparent.
- It is sufficient for a baseline, but it does not test whether using all rounds or a judge-based selector would recover more correct candidates.
