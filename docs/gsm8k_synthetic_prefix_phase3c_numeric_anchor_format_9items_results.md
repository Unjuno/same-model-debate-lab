# GSM8K Synthetic Prefix Phase 3c Numeric-Anchor Format Analysis
Caution:
- exploratory diagnostic
- repeated stochastic prompt samples
- not benchmark-level evidence
- no causal proof
- no statistical-significance claim
## Summary
- qualitative_labels: `numeric_anchor_consistent, answer_label_framing_consistent, bare_number_anchor_consistent, explanation_number_anchor_consistent, intermediate_number_weaker_consistent, uncertainty_reduces_anchor_consistent, warning_insufficient_consistent, item_group_heterogeneity_consistent`
## By Condition
| condition                          | correct_rate | target_wrong_rate | effective_failure |
| ---------------------------------- | ------------ | ----------------- | ----------------- |
| baseline_no_prefix                 | 0.622        | 0.378             | 0.000             |
| wrong_answer_labeled               | 0.072        | 0.928             | 0.000             |
| wrong_number_unlabeled             | 0.261        | 0.739             | 0.000             |
| wrong_number_in_explanation        | 0.211        | 0.789             | 0.000             |
| wrong_number_as_intermediate       | 0.228        | 0.772             | 0.000             |
| wrong_answer_with_uncertainty      | 0.206        | 0.794             | 0.000             |
| wrong_answer_marked_possibly_wrong | 0.333        | 0.667             | 0.000             |
## Condition Effects
| effect                                                | value  |
| ----------------------------------------------------- | ------ |
| wrong_answer_labeled_delta_target_wrong               | 0.550  |
| wrong_number_unlabeled_delta_target_wrong             | 0.361  |
| wrong_number_in_explanation_delta_target_wrong        | 0.411  |
| wrong_number_as_intermediate_delta_target_wrong       | 0.394  |
| wrong_answer_with_uncertainty_delta_target_wrong      | 0.417  |
| wrong_answer_marked_possibly_wrong_delta_target_wrong | 0.289  |
| unlabeled_minus_labeled_delta_target_wrong            | -0.189 |
| explanation_minus_labeled_delta_target_wrong          | -0.139 |
| intermediate_minus_labeled_delta_target_wrong         | -0.156 |
| uncertainty_minus_labeled_delta_target_wrong          | -0.133 |
| possibly_wrong_minus_labeled_delta_target_wrong       | -0.261 |
## Item Group Effects
| item_group                       | wrong_answer_labeled_delta_target_wrong | wrong_number_unlabeled_delta_target_wrong | wrong_number_in_explanation_delta_target_wrong | wrong_number_as_intermediate_delta_target_wrong | wrong_answer_with_uncertainty_delta_target_wrong | wrong_answer_marked_possibly_wrong_delta_target_wrong |
| -------------------------------- | --------------------------------------- | ----------------------------------------- | ---------------------------------------------- | ----------------------------------------------- | ------------------------------------------------ | ----------------------------------------------------- |
| numeric_anchor_dominant          | 0.600                                   | 0.533                                     | 0.483                                          | 0.550                                           | 0.450                                            | 0.367                                                 |
| rationale_contamination_positive | 0.750                                   | 0.500                                     | 0.567                                          | 0.517                                           | 0.550                                            | 0.267                                                 |
| rationale_corrective_reversal    | 0.300                                   | 0.050                                     | 0.183                                          | 0.117                                           | 0.250                                            | 0.233                                                 |
No raw model text is included.
