# AQuA R3 Aggregation Rule Analysis

This is a post-hoc aggregation analysis over the existing `raw.jsonl` traces.

## Summary Metrics
| rule | accuracy | answer_loss_rate | loss_denominator |
| --- | ---: | ---: | ---: |
| final_round_majority | 1.0 | 0.0 | 2 |
| all_round_majority | 1.0 | 0.0 | 2 |
| last_non_empty_majority | 1.0 | 0.0 | 2 |
| timeout_carry_forward_majority | 1.0 | 0.0 | 2 |
| initial_majority | 1.0 | 0.0 | 2 |
| oracle_any_history_correct | 1.0 | 0.0 | 2 |

## Item-Level Selections
| item_id | gold | final_round_majority | all_round_majority | last_non_empty_majority | timeout_carry_forward_majority | initial_majority | oracle_any_history_correct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| aqua_test_1_000106 | d | d | d | d | d | d | d |
| aqua_test_1_000138 | c | c | c | c | c | c | c |

## Notes
- No raw text, prompts, or transcript dumps are included.
- `answer_loss_rate` is reported only for rules where the initial-answer recovery denominator is meaningful.
- `oracle_any_history_correct` is an oracle-style upper bound, not a deployable selection rule.
