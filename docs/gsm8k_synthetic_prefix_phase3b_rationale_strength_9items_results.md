# GSM8K Synthetic Prefix Phase 3b Rationale-Strength Analysis
Caution:
- exploratory diagnostic
- repeated stochastic prompt samples
- not benchmark-level evidence
- no causal proof
- no statistical-significance claim
## Summary
- qualitative_labels: `numeric_anchor_consistent, answer_rationale_tension_consistent, item_group_heterogeneity_consistent`
## By Condition
| condition                          | correct_rate | target_wrong_rate | effective_failure |
| ---------------------------------- | ------------ | ----------------- | ----------------- |
| baseline_no_prefix                 | 0.628        | 0.367             | 0.000             |
| wrong_answer_only                  | 0.100        | 0.900             | 0.000             |
| weak_wrong_rationale_only          | 0.378        | 0.611             | 0.000             |
| medium_wrong_rationale_only        | 0.633        | 0.367             | 0.000             |
| strong_wrong_rationale_only        | 0.467        | 0.456             | 0.000             |
| weak_wrong_answer_plus_rationale   | 0.117        | 0.883             | 0.000             |
| medium_wrong_answer_plus_rationale | 0.322        | 0.672             | 0.000             |
| strong_wrong_answer_plus_rationale | 0.228        | 0.772             | 0.000             |
## Condition Effects
| effect                                                   | value  |
| -------------------------------------------------------- | ------ |
| wrong_answer_delta_target_wrong                          | 0.533  |
| weak_wrong_rationale_delta_target_wrong                  | 0.244  |
| medium_wrong_rationale_delta_target_wrong                | 0.000  |
| strong_wrong_rationale_delta_target_wrong                | 0.089  |
| medium_minus_weak_wrong_rationale_delta_target_wrong     | -0.244 |
| strong_minus_weak_wrong_rationale_delta_target_wrong     | -0.156 |
| strong_minus_medium_wrong_rationale_delta_target_wrong   | 0.089  |
| weak_answer_plus_minus_wrong_answer_delta_target_wrong   | -0.017 |
| medium_answer_plus_minus_wrong_answer_delta_target_wrong | -0.228 |
| strong_answer_plus_minus_wrong_answer_delta_target_wrong | -0.128 |
| correct_answer_delta_correct                             | -0.628 |
| correct_answer_plus_rationale_delta_correct              | -0.628 |
| correct_answer_plus_minus_correct_answer_delta_correct   | 0.000  |
No raw model text is included.
