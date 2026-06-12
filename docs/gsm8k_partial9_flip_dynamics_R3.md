# GSM8K Partial9 Debate Flip Dynamics

## Purpose
Post-hoc flip analysis for the role-separated same-model debate trajectories.

## Summary
| metric | value |
| --- | ---: |
| n | 9 |
| correct_to_wrong_majority_rate | 0.3333333333333333 |
| wrong_to_correct_majority_rate | 0.1111111111111111 |
| correct_path_retention_rate | 0.5714285714285714 |
| extraction_failure_count | 0 |
| item_count_with_any_extraction_failure | 0 |

## Majority Transition Counts
- preserved_correct: 4
- correct_to_wrong: 3
- wrong_to_correct: 1
- persistent_error: 1
- no_initial_majority: 0
- no_final_majority: 0

## Agent-Level Transition Counts
- correct_to_correct: 11
- correct_to_wrong: 7
- wrong_to_correct: 6
- wrong_to_wrong: 3
- missing_initial: 0
- missing_final: 0

## Role-Level Transition Counts
- solver: {'correct_to_correct': 4, 'correct_to_wrong': 3, 'wrong_to_correct': 2, 'wrong_to_wrong': 0, 'missing_initial': 0, 'missing_final': 0}
- skeptic/error-checker: {'correct_to_correct': 4, 'correct_to_wrong': 3, 'wrong_to_correct': 1, 'wrong_to_wrong': 1, 'missing_initial': 0, 'missing_final': 0}
- alternative-solver: {'correct_to_correct': 3, 'correct_to_wrong': 1, 'wrong_to_correct': 3, 'wrong_to_wrong': 2, 'missing_initial': 0, 'missing_final': 0}

## Item-Level Compact Table
| item_id | gold | initial_majority | final_majority | majority_transition_category |
| --- | --- | --- | --- | --- |
| gsm8k_test_000012 | 13 | 12 | 13 | wrong_to_correct |
| gsm8k_test_000089 | 24 | 24 | 18 | correct_to_wrong |
| gsm8k_test_000093 | 36 | 36.36 | 36.36 | persistent_error |
| gsm8k_test_000147 | 75 | 75 | 15 | correct_to_wrong |
| gsm8k_test_000187 | 106 | 106 | 106 | preserved_correct |
| gsm8k_test_000234 | 21 | 21 | 14 | correct_to_wrong |
| gsm8k_test_000236 | 31 | 31 | 31 | preserved_correct |
| gsm8k_test_000241 | 6 | 6 | 6 | preserved_correct |
| gsm8k_test_000255 | 192 | 192 | 192 | preserved_correct |

## Interpretation
On this 9-item exploratory subset, the majority path often held steady, but the final majority still lost some correct cases.
This is consistent with trajectory-mixing failure: same-model debate may reinforce contextually dominant reasoning paths rather than reliably selecting the correct path.
This does not establish a general causal mechanism.

## Limitations
- n=9 only
- post-hoc analysis
- one model/backend
- no statistical significance
- role prompts are simple
