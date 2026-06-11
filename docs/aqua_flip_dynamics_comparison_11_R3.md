# AQuA Flip Dynamics Comparison

## Purpose
Compare non-role and role-separated R3 flip dynamics on the same 11-item calibrated AQuA subset.

## Summary Comparison

| metric | non-role R3 | role-separated R3 |
| --- | ---: | ---: |
| initial_majority accuracy | 0.7272727272727273 | 0.7272727272727273 |
| final_majority accuracy | 0.6363636363636364 | 0.5454545454545454 |
| oracle_any_history accuracy | 0.9090909090909091 | 0.9090909090909091 |
| preserved_correct | 7 | 6 |
| correct_to_wrong | 1 | 2 |
| wrong_to_correct | 0 | 0 |
| persistent_error | 3 | 3 |
| correct_to_wrong_majority_rate | 0.09090909090909091 | 0.18181818181818182 |
| wrong_to_correct_majority_rate | 0.0 | 0.0 |
| correct_path_retention_rate | 0.875 | 0.75 |

## Interpretation
Non-role and role-separated debate both show a correct-to-wrong majority flip with no wrong-to-correct majority flips in this 11-item exploratory subset.
That supports the idea that trajectory mixing failure is not only a role-prompt artifact.

The role-separated run shows a stronger majority degradation than the non-role run:
its final majority accuracy is lower, and its correct-to-wrong majority rate is higher.
That suggests role prompts may have changed the failure mode, but this remains post-hoc and non-causal.

No statistical significance can be claimed from n=11.
