# AQuA Role-Separated Follow-Up: 11-Item Exploratory Subset

## Purpose

Test whether simple role-separated prompting changes answer diversity, answer loss, or final-majority behavior on the 11-item calibrated AQuA subset.

## Conditions

- `role_independent`
- `role_debate_3r_full_context` with `--rounds 3`

## Roles

- agent 1: solver
- agent 2: skeptic/error-checker
- agent 3: alternative-solver

## Summary Metrics

| condition | accuracy | oracle_at_k | answer_loss_rate | same_error_agreement_rate | diversity_drop | extraction_failure_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| role_independent | 0.5454545454545454 | 0.8181818181818182 | 0.3333333333333333 | 0.09090909090909091 | 0.0 | 0.0 |
| role_debate_R3 | 0.5454545454545454 | 0.7272727272727273 | 0.25 | 0.2727272727272727 | 0.0 | 0.015151515151515152 |
| non-role debate_R3 baseline | 0.6363636363636364 | 0.9090909090909091 | 0.3 | 0.2727272727272727 | 0.2727272727272727 | 0.015151515151515152 |

## Role-Debate Aggregation Summary

| rule | accuracy | answer_loss_rate |
| --- | ---: | ---: |
| initial_majority | 0.7272727272727273 | 0.0 |
| all_round_majority | 0.6363636363636364 | 0.125 |
| final_round_majority | 0.5454545454545454 | 0.25 |
| oracle_any_history_correct | 0.9090909090909091 | 0.0 |

## Interpretation

On this 11-item exploratory subset, simple role-separated prompting did not improve final-round majority accuracy. Role debate R3 matched role-independent accuracy and underperformed the non-role R3 run. In the role-debate aggregation analysis, initial majority outperformed final-round majority, while oracle-any-history remained high. This is consistent with a trajectory-mixing failure interpretation: debate may amplify contextually dominant reasoning paths rather than reliably selecting the correct path.

## Conceptual Note

Same-model debate may not aggregate independent reasoning paths. It may mix highly correlated reasoning trajectories. Because these trajectories share model-specific biases, later debate rounds can reinforce whichever path becomes contextually dominant. Correct and incorrect trajectories can both become attractors.

## Limitations

- `n=11` only.
- exploratory subset.
- no statistical significance.
- role prompts are simple and short.
- no general conclusion about role prompting.
- no claim that same-model debate is generally harmful.

## Next Analysis

Compute `correct_to_wrong_flip_rate`, `wrong_to_correct_flip_rate`, and `correct_path_retention_rate`.
Prefer post-hoc analysis before any larger run.
