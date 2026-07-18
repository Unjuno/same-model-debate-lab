# AQuA Role Debate Flip Dynamics

## Purpose
Post-hoc flip analysis for the role-separated same-model debate trajectories.

## Summary
| metric | value |
| --- | ---: |
| n | 3 |
| correct_to_wrong_majority_rate | 0.0 |
| wrong_to_correct_majority_rate | 0.0 |
| correct_path_retention_rate | 1.0 |
| extraction_failure_count | 0 |
| item_count_with_any_extraction_failure | 0 |

## Majority Transition Counts
- preserved_correct: 1
- correct_to_wrong: 0
- wrong_to_correct: 0
- persistent_error: 2
- no_initial_majority: 0
- no_final_majority: 0

## Agent-Level Transition Counts
- correct_to_correct: 2
- correct_to_wrong: 1
- wrong_to_correct: 2
- wrong_to_wrong: 4
- missing_initial: 0
- missing_final: 0

## Role-Level Transition Counts
- solver: {'correct_to_correct': 0, 'correct_to_wrong': 1, 'wrong_to_correct': 1, 'wrong_to_wrong': 1, 'missing_initial': 0, 'missing_final': 0}
- skeptic/error-checker: {'correct_to_correct': 1, 'correct_to_wrong': 0, 'wrong_to_correct': 1, 'wrong_to_wrong': 1, 'missing_initial': 0, 'missing_final': 0}
- alternative-solver: {'correct_to_correct': 1, 'correct_to_wrong': 0, 'wrong_to_correct': 0, 'wrong_to_wrong': 2, 'missing_initial': 0, 'missing_final': 0}

## Item-Level Compact Table
| item_id | gold | initial_majority | final_majority | majority_transition_category |
| --- | --- | --- | --- | --- |
| aqua_test_1_000032 | B | C | C | persistent_error |
| aqua_test_1_000086 | E | A | A | persistent_error |
| aqua_test_1_000176 | D | D | D | preserved_correct |

## Interpretation
On this 11-item exploratory subset, the majority path often held steady, but the final majority still lost some correct cases.
This is consistent with trajectory-mixing failure: same-model debate may reinforce contextually dominant reasoning paths rather than reliably selecting the correct path.
This does not establish a general causal mechanism.

## Limitations
- n=11 only
- post-hoc analysis
- one model/backend
- no statistical significance
- role prompts are simple
