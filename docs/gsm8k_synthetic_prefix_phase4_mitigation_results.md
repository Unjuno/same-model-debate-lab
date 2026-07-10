# GSM8K Phase 4 Mitigation Diagnostic

Caution: this is exploratory and diagnostic, not a safety proof or benchmark-level claim.

## Summary

- n: 900
- accuracy: 0.09444444444444444
- oracle_at_k: 0.1111111111111111
- answer_loss_rate: 0.9055555555555556

## By Condition

| condition | correct_rate | target_wrong_rate | extraction_failure_rate | history_metrics_available |
| --- | ---: | ---: | ---: | --- |
| independent | 0.094 | 0.006 | 0.000 | False |
| full_context_debate | 0.039 | 0.072 | 0.000 | False |
| answer_hidden_debate | 0.111 | 0.000 | 0.000 | False |
| numeric_masked_debate | 0.106 | 0.000 | 0.000 | False |
| commit_then_numeric_masked_debate | 0.100 | 0.006 | 0.000 | False |

## Condition Effects

| effect | value |
| --- | ---: |
| full_context_minus_independent_delta_target_wrong | 0.067 |
| answer_hidden_minus_full_context_delta_target_wrong | -0.072 |
| numeric_masked_minus_full_context_delta_target_wrong | -0.072 |
| commit_then_numeric_masked_minus_full_context_delta_target_wrong | -0.067 |

No raw model text is included.
