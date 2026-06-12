# GSM8K Partial9 Takeaways

## Overview

This is a post-hoc analysis of an exploratory GSM8K partial-correct subset selected from the 300-item independent screening run.
The subset is intentionally small and selected after screening, so the results are best read as a focused diagnostic rather than a general benchmark claim.

## Run Summary

| metric | value |
| --- | ---: |
| n | 9 |
| accuracy | 0.5555555555555556 |
| oracle_at_k | 0.8888888888888888 |
| answer_loss_rate | 0.5 |
| same_error_agreement_rate | 0.2222222222222222 |
| diversity_drop | 0.3333333333333333 |
| extraction_failure_rate | 0.0 |

## Aggregation View

The aggregation analyzer gives a useful post-hoc comparison of selection rules on the same selected subset.

| rule | accuracy | answer_loss_rate |
| --- | ---: | ---: |
| final_round_majority | 0.5556 | 0.5 |
| initial_majority | 0.7778 | 0.125 |
| all_round_majority | 0.7778 | 0.125 |
| oracle_any_history_correct | 1.0 | 0.0 |

The `oracle_at_k=8/9` value from the run summary and `oracle_any_history_correct=9/9` from the aggregation analyzer measure different things.
The latter is a full-history upper bound over the debate trace, not a deployable selector.

## Flip Dynamics

The flip analysis suggests that the selected subset includes both retained correct paths and post-hoc losses of initially correct majority answers.

| category | count |
| --- | ---: |
| preserved_correct | 4 |
| correct_to_wrong | 3 |
| wrong_to_correct | 1 |
| persistent_error | 1 |

Derived rates:

| metric | value |
| --- | ---: |
| correct_path_retention_rate | 0.5714285714285714 |
| correct_to_wrong_majority_rate | 0.3333333333333333 |
| wrong_to_correct_majority_rate | 0.1111111111111111 |
| extraction_failure_count | 0 |

## Transient Correctness

The transient correctness report is consistent with the aggregation view: some items started with a correct majority or unanimous correct consensus and later lost it.

| category | count |
| --- | ---: |
| preserved_correct | 4 |
| recovered_to_correct | 1 |
| transient_correct_majority_lost | 2 |
| transient_correct_consensus_lost | 1 |
| persistent_error | 1 |

## Item-Level Notes

- `gsm8k_test_000089`:
  - gold `24`
  - round 0 majority `24`
  - final majority `18`
  - classified as `transient_correct_majority_lost`
- `gsm8k_test_000147`:
  - gold `75`
  - rounds 0-2 majority `75`
  - final majority `15`
  - classified as `transient_correct_majority_lost`
- `gsm8k_test_000234`:
  - gold `21`
  - round 0 `21,21,21`
  - round 1 `21,21,14`
  - round 2 `14,14,21`
  - round 3 `14,14,14`
  - classified as `transient_correct_consensus_lost`
- `gsm8k_test_000093`:
  - gold `36`
  - round 0 `36,36.36,36.36`
  - later rounds and final `36.36,36.36,36.36`
  - classified as `persistent_error` by majority, while a correct minority answer existed initially

## Takeaway

On this exploratory subset, the full debate trace often contained the correct answer at some point, but the final majority still lost several initially correct cases.
That pattern is consistent with a post-hoc trajectory where the model can retain or recover correctness, yet the final aggregation may still collapse onto a wrong consensus.
This suggests a useful diagnostic for aggregation design, not a general conclusion about the benchmark or the model.
