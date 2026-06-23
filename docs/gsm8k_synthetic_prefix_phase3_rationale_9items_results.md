# GSM8K Synthetic Prefix Phase 3 Rationale-Contamination Analysis
Caution:
- exploratory diagnostic
- repeated stochastic prompt samples
- not benchmark-level evidence
- no causal proof
- no statistical-significance claim
- rationale wording is synthetic and may bias results
## Summary
- n: `1080`
- accuracy: `0.574074`
- oracle_at_k: `0.731481`
- answer_loss_rate: `0.215190`
- same_error_agreement_rate: `0.266667`
- diversity_drop: `0.000000`
- extraction_failure_rate: `0.000000`
- qualitative_labels: `numeric_anchor_consistent, correct_answer_anchor_consistent`
## By Condition
| condition                     | correct_rate | target_wrong_rate | raw_failure | effective_failure |
| ----------------------------- | ------------ | ----------------- | ----------- | ----------------- |
|            baseline_no_prefix |        0.589 |             0.406 |       0.000 |             0.000 |
|             wrong_answer_only |        0.117 |             0.883 |       0.000 |             0.000 |
|          wrong_rationale_only |        0.539 |             0.450 |       0.000 |             0.000 |
|   wrong_answer_plus_rationale |        0.278 |             0.722 |       0.000 |             0.000 |
|           correct_answer_only |        0.950 |             0.050 |       0.000 |             0.000 |
| correct_answer_plus_rationale |        0.972 |             0.028 |       0.000 |             0.000 |
## Condition Effects
| effect                                                     | value  |
| ---------------------------------------------------------- | ------ |
|                            wrong_answer_delta_target_wrong |  0.478 |
|                         wrong_rationale_delta_target_wrong |  0.044 |
|             wrong_answer_plus_rationale_delta_target_wrong |  0.317 |
|                               correct_answer_delta_correct |  0.361 |
|                correct_answer_plus_rationale_delta_correct |  0.383 |
|    wrong_answer_plus_minus_wrong_answer_delta_target_wrong | -0.161 |
| wrong_answer_plus_minus_wrong_rationale_delta_target_wrong |  0.272 |
|     correct_answer_plus_minus_correct_answer_delta_correct |  0.022 |
## Extraction and Recovery
- baseline effective failure rate: 0.000
## Interpretation Guide
- If wrong_answer_only shifts target_wrong more than the baseline, numeric anchoring is plausible.
- If wrong_rationale_only shifts target_wrong, rationale contamination is plausible.
- If the combined condition exceeds either alone, the answer and rationale may interact.
- If correct_rationale helps more than correct_answer_only, the explanation may provide corrective structure.
No raw model text is included.
