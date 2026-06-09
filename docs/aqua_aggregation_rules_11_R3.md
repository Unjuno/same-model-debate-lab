# AQuA R3 Aggregation Rule Analysis

This is a post-hoc aggregation analysis over the existing `raw.jsonl` traces.

## Summary Metrics
| rule | accuracy | answer_loss_rate | loss_denominator |
| --- | ---: | ---: | ---: |
| final_round_majority | 0.6363636363636364 | 0.3 | 10 |
| all_round_majority | 0.7272727272727273 | 0.2 | 10 |
| last_non_empty_majority | 0.6363636363636364 | 0.3 | 10 |
| timeout_carry_forward_majority | 0.6363636363636364 | 0.3 | 10 |
| initial_majority | 0.7272727272727273 | 0.2 | 10 |
| oracle_any_history_correct | 0.9090909090909091 | 0.0 | 10 |

## Item-Level Selections
| item_id | gold | final_round_majority | all_round_majority | last_non_empty_majority | timeout_carry_forward_majority | initial_majority | oracle_any_history_correct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| aqua_test_0_000016 | A | A | A | A | A | A | A |
| aqua_test_0_000184 | D | D | D | D | D | D | D |
| aqua_test_1_000016 | A | A | A | A | A | A | A |
| aqua_test_1_000059 | C | C | C | C | C | C | C |
| aqua_test_1_000067 | B | C | B | C | C | B | B |
| aqua_test_1_000069 | C | E | E | E | E | E | C |
| aqua_test_1_000117 | C | C | C | C | C | C | C |
| aqua_test_1_000172 | E | E | E | E | E | E | E |
| aqua_test_1_000188 | D | C | C | C | C | C | D |
| aqua_test_1_000210 | E | D | D | D | D | D | D |
| aqua_test_1_000237 | B | B | B | B | B | B | B |

## Notes
- No raw text, prompts, or transcript dumps are included.
- `answer_loss_rate` is reported only for rules where the initial-answer recovery denominator is meaningful.
- `oracle_any_history_correct` is an oracle-style upper bound, not a deployable selection rule.
