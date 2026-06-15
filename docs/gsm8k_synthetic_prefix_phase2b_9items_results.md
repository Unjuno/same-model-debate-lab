# GSM8K Synthetic Prefix Phase 2b Multi-Item Analysis

Caution:
- exploratory diagnostic
- repeated stochastic prompt samples
- not independent benchmark items
- no causal proof
- no statistical-significance claim

## Summary

- qualitative_labels: `shared_prior_common, correct_consensus_anchor_common, wrong_consensus_anchor_common, majority_effect_weaker_than_consensus`

## Aggregate by Condition

| condition | n_outputs | non_failed_outputs | correct_count | target_wrong_count | other_count | extraction_failure_count | correct_rate | target_wrong_rate | other_rate | extraction_failure_rate | unique_answer_count | answer_entropy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_no_prefix | 1080 | 840 | 499 | 341 | 0 | 240 | 0.594047619047619 | 0.40595238095238095 | 0.0 | 0.2222222222222222 | 13 | 3.5376391102054114 |
| single_round_correct_consensus | 1080 | 840 | 763 | 77 | 0 | 240 | 0.9083333333333333 | 0.09166666666666666 | 0.0 | 0.2222222222222222 | 12 | 3.1392065887174385 |
| single_round_correct_majority | 1080 | 777 | 307 | 470 | 0 | 303 | 0.39510939510939513 | 0.6048906048906049 | 0.0 | 0.28055555555555556 | 14 | 3.4974915975839047 |
| single_round_wrong_majority | 1080 | 720 | 248 | 472 | 0 | 360 | 0.34444444444444444 | 0.6555555555555556 | 0.0 | 0.3333333333333333 | 12 | 3.3247145230830584 |
| single_round_wrong_consensus | 1080 | 720 | 38 | 682 | 0 | 360 | 0.05277777777777778 | 0.9472222222222222 | 0.0 | 0.3333333333333333 | 11 | 2.820566402401524 |

## Effect Summaries

| metric | mean | median | min | max | positive_count | negative_count | zero_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| correct_consensus_delta_correct | 0.24444444444444446 | 0.1166666666666667 | 0.0 | 0.7583333333333334 | 6 | 0 | 3 |
| correct_majority_delta_correct | -0.1255847953216374 | -0.06666666666666665 | -0.875 | 0.26666666666666666 | 2 | 5 | 2 |
| correct_consensus_delta_failure | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 9 |
| correct_majority_delta_failure | 0.058333333333333334 | 0.0 | 0.0 | 0.525 | 1 | 0 | 8 |
| wrong_majority_delta_wrong | 0.12129629629629629 | 0.09999999999999998 | -0.1833333333333334 | 0.9333333333333333 | 5 | 2 | 2 |
| wrong_consensus_delta_wrong | 0.31574074074074077 | 0.2749999999999999 | -0.11666666666666667 | 1.0 | 6 | 1 | 2 |
| wrong_consensus_minus_wrong_majority_delta_wrong | 0.19444444444444445 | 0.06666666666666665 | 0.0 | 0.47500000000000003 | 6 | 0 | 3 |
| wrong_majority_delta_failure | 0.1111111111111111 | 0.0 | 0.0 | 1.0 | 1 | 0 | 8 |
| wrong_consensus_delta_failure | 0.1111111111111111 | 0.0 | 0.0 | 1.0 | 1 | 0 | 8 |
| wrong_consensus_minus_wrong_majority_delta_failure | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 9 |
| correct_consensus_entropy_delta | -0.3098919611573122 | -0.26571087752185707 | -0.7469093391484511 | 0.0 | 0 | 6 | 3 |
| wrong_consensus_entropy_delta | -0.4109295452169382 | -0.5197027865043055 | -0.9272619849868288 | 0.0 | 0 | 6 | 3 |

## Failure Effects

| metric | mean | median | min | max | positive_count | negative_count | zero_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| correct_consensus_delta_failure | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 9 |
| correct_majority_delta_failure | 0.058333333333333334 | 0.0 | 0.0 | 0.525 | 1 | 0 | 8 |
| wrong_majority_delta_failure | 0.1111111111111111 | 0.0 | 0.0 | 1.0 | 1 | 0 | 8 |
| wrong_consensus_delta_failure | 0.1111111111111111 | 0.0 | 0.0 | 1.0 | 1 | 0 | 8 |
| wrong_consensus_minus_wrong_majority_delta_failure | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | 9 |

## Indicator Counts

| indicator | count |
| --- | ---: |
| correct_consensus_anchor_positive | 5 |
| correct_majority_anchor_positive | 1 |
| wrong_majority_anchor_positive | 4 |
| wrong_consensus_anchor_positive | 6 |
| wrong_consensus_stronger_than_wrong_majority | 4 |
| wrong_prefix_failure_increase_common | 1 |
| baseline_wrong_heavy | 3 |
| baseline_correct_heavy | 2 |
| baseline_mixed | 4 |

## Item-Level Effects

| item_id | correct_consensus_delta_correct | correct_majority_delta_correct | wrong_majority_delta_wrong | wrong_consensus_delta_wrong | wrong_consensus_minus_wrong_majority_delta_wrong | correct_consensus_delta_failure | correct_majority_delta_failure | wrong_majority_delta_failure | wrong_consensus_delta_failure | wrong_consensus_minus_wrong_majority_delta_failure | correct_consensus_entropy_delta | wrong_consensus_entropy_delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gsm8k_test_000012 | 0.4666666666666666 | 0.26666666666666666 | -0.1833333333333334 | 0.2749999999999999 | 0.4583333333333333 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | -0.7128013971476835 | -0.2609134881201892 |
| gsm8k_test_000089 | 0.275 | -0.11666666666666659 | 0.1166666666666667 | 0.5916666666666668 | 0.47500000000000003 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | -0.5060696413661807 | -0.69819595076072 |
| gsm8k_test_000093 | 0.7583333333333334 | -0.125 | 0.125 | 0.15833333333333333 | 0.033333333333333326 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | -0.26571087752185707 | -0.5804927746535463 |
| gsm8k_test_000147 | 0.09166666666666667 | -0.22500000000000003 | 0.09999999999999998 | 0.475 | 0.375 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | -0.0378336087273321 | -0.7117989219268538 |
| gsm8k_test_000187 | 0.0 | -0.875 | 0.9333333333333333 | 1.0 | 0.06666666666666665 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| gsm8k_test_000234 | 0.4916666666666667 | -0.06666666666666665 | 0.1166666666666667 | 0.45833333333333337 | 0.3416666666666667 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | -0.7469093391484511 | -0.9272619849868288 |
| gsm8k_test_000236 | 0.1166666666666667 | 0.01140350877192986 | -0.11666666666666667 | -0.11666666666666667 | 0.0 | 0.0 | 0.525 | 1.0 | 1.0 | 0.0 | -0.5197027865043055 | -0.5197027865043055 |
| gsm8k_test_000241 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| gsm8k_test_000255 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

## Interpretation Guide

- If wrong majority exceeds baseline, that is consistent with an anchor/majority effect.
- If wrong consensus exceeds wrong majority, that is consistent with a unanimity increment.
- If trajectory-like differences appear after pooling, that is consistent with an order/recency effect.
- If forward and reversed are similar, frequency may dominate over order, or the order effect may be weak.
- If baseline is already wrong-heavy, shared-prior possible.

No raw model text is included.
