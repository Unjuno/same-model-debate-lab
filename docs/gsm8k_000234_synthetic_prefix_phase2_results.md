# GSM8K 000234 Synthetic Prefix Phase 2 Analysis

Caution: this is a single-item diagnostic with repeated stochastic prompt samples; it is not benchmark-level evidence and does not provide causal proof.

## Summary

- qualitative_labels: `shared_prior_possible, correct_consensus_anchor_consistent, wrong_majority_anchor_consistent, wrong_consensus_stronger_than_wrong_majority`

## By Condition

| condition | n_outputs | correct_rate | target_wrong_rate | other_rate | extraction_failure_rate | unique_answer_count | answer_entropy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_no_prefix | 60 | 0.4666666666666667 | 0.5333333333333333 | 0.0 | 0.0 | 2 | 0.9967916319816366 |
| single_round_correct_consensus | 60 | 0.9833333333333333 | 0.016666666666666666 | 0.0 | 0.0 | 2 | 0.1222915970693747 |
| single_round_correct_majority | 60 | 0.43333333333333335 | 0.5666666666666667 | 0.0 | 0.0 | 2 | 0.9871377743721863 |
| single_round_wrong_majority | 60 | 0.36666666666666664 | 0.6333333333333333 | 0.0 | 0.0 | 2 | 0.9480782435939055 |
| single_round_wrong_consensus | 60 | 0.03333333333333333 | 0.9666666666666667 | 0.0 | 0.0 | 2 | 0.21084230031853213 |
| trajectory_forward | 60 | 0.35 | 0.65 | 0.0 | 0.0 | 2 | 0.934068055375491 |
| trajectory_reversed | 60 | 0.36666666666666664 | 0.6333333333333333 | 0.0 | 0.0 | 2 | 0.9480782435939055 |

## Planned Comparisons

| comparison | left | right | delta_correct_rate | delta_target_wrong_rate | delta_entropy |
| --- | --- | --- | ---: | ---: | ---: |
| single_round_correct_consensus_vs_baseline | single_round_correct_consensus | baseline_no_prefix | 0.5166666666666666 | -0.5166666666666666 | -0.8745000349122618 |
| single_round_wrong_majority_vs_baseline | single_round_wrong_majority | baseline_no_prefix | -0.10000000000000003 | 0.09999999999999998 | -0.048713388387731094 |
| single_round_wrong_consensus_vs_wrong_majority | single_round_wrong_consensus | single_round_wrong_majority | -0.3333333333333333 | 0.33333333333333337 | -0.7372359432753733 |
| single_round_correct_majority_vs_wrong_majority | single_round_correct_majority | single_round_wrong_majority | 0.06666666666666671 | -0.06666666666666665 | 0.03905953077828084 |
| trajectory_forward_vs_baseline | trajectory_forward | baseline_no_prefix | -0.1166666666666667 | 0.1166666666666667 | -0.06272357660614558 |
| trajectory_reversed_vs_baseline | trajectory_reversed | baseline_no_prefix | -0.10000000000000003 | 0.09999999999999998 | -0.048713388387731094 |
| trajectory_forward_vs_reversed | trajectory_forward | trajectory_reversed | -0.016666666666666663 | 0.01666666666666672 | -0.014010188218414488 |

## Interpretation Guide

- If wrong majority > baseline, that is consistent with an anchor/majority effect.
- If wrong consensus > wrong majority, that is consistent with an unanimity increment.
- If trajectory forward > reversed for wrong answer, that is consistent with a recency/order effect.
- If forward and reversed are similar, frequency may dominate over order, or the order effect may be weak.
- If baseline is already wrong-heavy, shared-prior possible.

No raw model text is included in this report.
