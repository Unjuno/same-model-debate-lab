# GSM8K Partial9 R3 Aggregation Rule Analysis

This is a post-hoc aggregation analysis over the selected GSM8K partial-correct subset and the existing `raw.jsonl` traces.

## Summary Metrics
| rule | accuracy | answer_loss_rate | loss_denominator |
| --- | ---: | ---: | ---: |
| final_round_majority | 0.5555555555555556 | 0.5 | 8 |
| all_round_majority | 0.7777777777777778 | 0.125 | 8 |
| last_non_empty_majority | 0.5555555555555556 | 0.5 | 8 |
| timeout_carry_forward_majority | 0.5555555555555556 | 0.5 | 8 |
| initial_majority | 0.7777777777777778 | 0.125 | 8 |
| oracle_any_history_correct | 1.0 | 0.0 | 8 |

## Item-Level Selections
| item_id | gold | final_round_majority | all_round_majority | last_non_empty_majority | timeout_carry_forward_majority | initial_majority | oracle_any_history_correct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gsm8k_test_000012 | 13 | 13 | 12 | 13 | 13 | 12 | 13 |
| gsm8k_test_000089 | 24 | 18 | 24 | 18 | 18 | 24 | 24 |
| gsm8k_test_000093 | 36 | 36.36 | 36.36 | 36.36 | 36.36 | 36.36 | 36 |
| gsm8k_test_000147 | 75 | 15 | 75 | 15 | 15 | 75 | 75 |
| gsm8k_test_000187 | 106 | 106 | 106 | 106 | 106 | 106 | 106 |
| gsm8k_test_000234 | 21 | 14 | 21 | 14 | 14 | 21 | 21 |
| gsm8k_test_000236 | 31 | 31 | 31 | 31 | 31 | 31 | 31 |
| gsm8k_test_000241 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| gsm8k_test_000255 | 192 | 192 | 192 | 192 | 192 | 192 | 192 |

## Notes
- No raw text, prompts, or transcript dumps are included.
- `answer_loss_rate` is reported only for rules where the initial-answer recovery denominator is meaningful.
- `oracle_any_history_correct` is an oracle-style upper bound over the full debate history, not a deployable selection rule.
