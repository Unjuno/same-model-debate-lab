# Next Experiment Plan

The current result does not support the strong claim that same-model 3-agent debate naturally improves final accuracy. However, high `oracle_at_k` suggests that correct candidates are often present, so future work should focus on aggregation and selection.

## Hypotheses

### H1

Final-round majority is failing to recover correct candidates from same-model debate histories.

### H2

All-round aggregation or judge-based selection will improve accuracy and reduce `answer_loss_rate`.

### H3

Timeout carry-forward will reduce avoidable extraction and empty-answer damage.

## Suggested Next Conditions

- A. baseline final-round aggregation
- B. timeout carry-forward
- C. all-round majority aggregation
- D. timeout carry-forward + all-round majority
- E. judge selector over all rationales and answer histories

## Target Metrics

- `accuracy`
- `oracle_at_k`
- `answer_loss_rate`
- `same_error_agreement_rate`
- `diversity_drop`
- `extraction_failure_rate`

## Pass / Fail Criteria for the Next 11-Item Exploratory Test

### PASS

- `accuracy > 0.6363636363636364`
- `answer_loss_rate < 0.3`

### FAIL

- `accuracy <= 0.6363636363636364`
- `answer_loss_rate >= 0.3`

### UNCERTAIN

- only one-question movement on `n=11`
- timeout or API instability contaminates comparison

## Sample Size Note

- `n=11` is exploratory.
- `n=50` to `n=100` is needed for a more reliable conclusion.

## Implementation Notes

- Prefer adding CLI options in a small, testable way rather than rewriting the full debate flow.
- Likely future options:
  - `--aggregation final_round_majority`
  - `--aggregation all_round_majority`
  - `--aggregation judge`
  - `--timeout-policy empty`
  - `--timeout-policy carry_forward`

