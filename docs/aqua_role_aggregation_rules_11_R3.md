# AQuA Role-Separated Aggregation Rules: 11-Item R3 Follow-Up

This is a post-hoc aggregation analysis over the existing `raw.jsonl` traces for the role-separated 11-item follow-up.

## Summary Metrics

| rule | accuracy | answer_loss_rate | loss_denominator |
| --- | ---: | ---: | ---: |
| initial_majority | 0.7272727272727273 | 0.0 | 8 |
| all_round_majority | 0.6363636363636364 | 0.125 | 8 |
| final_round_majority | 0.5454545454545454 | 0.25 | 8 |
| oracle_any_history_correct | 0.9090909090909091 | 0.0 | 8 |
| last_non_empty_majority | 0.5454545454545454 | 0.25 | 8 |
| timeout_carry_forward_majority | 0.5454545454545454 | 0.25 | 8 |

## Notes

- No raw text, prompts, or transcript dumps are included.
- `answer_loss_rate` is reported only for rules where the initial-answer recovery denominator is meaningful.
- `oracle_any_history_correct` is an oracle-style upper bound, not a deployable selection rule.
