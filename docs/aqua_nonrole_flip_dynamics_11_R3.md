# AQuA Non-Role Debate Flip Dynamics

## Purpose
Post-hoc flip analysis for the non-role same-model debate trajectories on the 11-item calibrated AQuA subset.

## Summary
| metric | value |
| --- | ---: |
| n | 11 |
| correct_to_wrong_majority_rate | 0.09090909090909091 |
| wrong_to_correct_majority_rate | 0.0 |
| correct_path_retention_rate | 0.875 |
| extraction_failure_count | 1 |
| item_count_with_any_extraction_failure | 1 |

## Majority Transition Counts
- preserved_correct: 7
- correct_to_wrong: 1
- wrong_to_correct: 0
- persistent_error: 3
- no_initial_majority: 0
- no_final_majority: 0

## Agent-Level Transition Counts
- correct_to_correct: 18
- correct_to_wrong: 4
- wrong_to_correct: 3
- wrong_to_wrong: 7
- missing_initial: 0
- missing_final: 1

## Role-Level Transition Counts
- solver: {'correct_to_correct': 5, 'correct_to_wrong': 1, 'wrong_to_correct': 1, 'wrong_to_wrong': 3, 'missing_initial': 0, 'missing_final': 1}
- skeptic/error-checker: {'correct_to_correct': 6, 'correct_to_wrong': 3, 'wrong_to_correct': 1, 'wrong_to_wrong': 1, 'missing_initial': 0, 'missing_final': 0}
- alternative-solver: {'correct_to_correct': 7, 'correct_to_wrong': 0, 'wrong_to_correct': 1, 'wrong_to_wrong': 3, 'missing_initial': 0, 'missing_final': 0}

## Item-Level Compact Table
| item_id | gold | initial_majority | final_majority | majority_transition_category |
| --- | --- | --- | --- | --- |
| aqua_test_0_000016 | A | A | A | preserved_correct |
| aqua_test_0_000184 | D | D | D | preserved_correct |
| aqua_test_1_000016 | A | A | A | preserved_correct |
| aqua_test_1_000059 | C | C | C | preserved_correct |
| aqua_test_1_000067 | B | B | C | correct_to_wrong |
| aqua_test_1_000069 | C | E | E | persistent_error |
| aqua_test_1_000117 | C | C | C | preserved_correct |
| aqua_test_1_000172 | E | E | E | preserved_correct |
| aqua_test_1_000188 | D | C | C | persistent_error |
| aqua_test_1_000210 | E | D | D | persistent_error |
| aqua_test_1_000237 | B | B | B | preserved_correct |

## Interpretation
On this 11-item exploratory subset, non-role debate also shows a correct-to-wrong majority flip with no wrong-to-correct majority flips.
That pattern supports, but does not prove, the idea that trajectory mixing failure is not limited to role prompting.
It still does not establish a general causal mechanism.

## Limitations
- n=11 only
- post-hoc analysis
- one model/backend
- no statistical significance
- role prompts are simple
