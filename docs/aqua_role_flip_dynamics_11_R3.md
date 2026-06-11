# AQuA Role Debate Flip Dynamics

## Purpose
Post-hoc flip analysis for the role-separated same-model debate trajectories.

## Summary
| metric | value |
| --- | ---: |
| n | 11 |
| correct_to_wrong_majority_rate | 0.18181818181818182 |
| wrong_to_correct_majority_rate | 0.0 |
| correct_path_retention_rate | 0.75 |
| extraction_failure_count | 1 |
| item_count_with_any_extraction_failure | 1 |

## Majority Transition Counts
- preserved_correct: 6
- correct_to_wrong: 2
- wrong_to_correct: 0
- persistent_error: 3
- no_initial_majority: 0
- no_final_majority: 0

## Agent-Level Transition Counts
- correct_to_correct: 16
- correct_to_wrong: 4
- wrong_to_correct: 1
- wrong_to_wrong: 12
- missing_initial: 0
- missing_final: 0

## Role-Level Transition Counts
- solver: {'correct_to_correct': 7, 'correct_to_wrong': 1, 'wrong_to_correct': 0, 'wrong_to_wrong': 3, 'missing_initial': 0, 'missing_final': 0}
- skeptic/error-checker: {'correct_to_correct': 6, 'correct_to_wrong': 1, 'wrong_to_correct': 0, 'wrong_to_wrong': 4, 'missing_initial': 0, 'missing_final': 0}
- alternative-solver: {'correct_to_correct': 3, 'correct_to_wrong': 2, 'wrong_to_correct': 1, 'wrong_to_wrong': 5, 'missing_initial': 0, 'missing_final': 0}

## Item-Level Compact Table
| item_id | gold | initial_majority | final_majority | majority_transition_category |
| --- | --- | --- | --- | --- |
| aqua_test_0_000016 | A | A | A | preserved_correct |
| aqua_test_0_000184 | D | D | D | preserved_correct |
| aqua_test_1_000016 | A | A | A | preserved_correct |
| aqua_test_1_000059 | C | C | A | correct_to_wrong |
| aqua_test_1_000067 | B | B | B | preserved_correct |
| aqua_test_1_000069 | C | C | E | correct_to_wrong |
| aqua_test_1_000117 | C | C | C | preserved_correct |
| aqua_test_1_000172 | E | D | D | persistent_error |
| aqua_test_1_000188 | D | C | C | persistent_error |
| aqua_test_1_000210 | E | D | D | persistent_error |
| aqua_test_1_000237 | B | B | B | preserved_correct |

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
