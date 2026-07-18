# Synthetic Prefix Continuation Analysis

This is a descriptive analysis of a one-step synthetic-prefix continuation run.
It should not be read as a causal proof or a benchmark-level result.

## Summary

- data: `data/benchmarks/gsm8k_000234_synthetic_prefix_continuation.jsonl`
- raw: `runs/qwen3_8b_gsm8k_000234_synthetic_prefix_continuation_independent/raw.jsonl`
- qualitative_labels: `context_attractor_consistent, correct_anchor_consistent, shared_prior_possible`

## By Condition

| condition | n_outputs | correct_rate | target_wrong_rate | other_rate | extraction_failure_rate | unique_answer_count | answer_entropy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_no_prefix | 60 | 0.4166666666666667 | 0.5833333333333334 | 0.0 | 0.0 | 2 | 0.9798687566511528 |
| prefix_correct_consensus_r0 | 60 | 0.9666666666666667 | 0.03333333333333333 | 0.0 | 0.0 | 2 | 0.21084230031853213 |
| prefix_mixed_correct_majority_r1 | 60 | 0.43333333333333335 | 0.5666666666666667 | 0.0 | 0.0 | 2 | 0.9871377743721863 |
| prefix_wrong_majority_r2 | 60 | 0.26666666666666666 | 0.7333333333333333 | 0.0 | 0.0 | 2 | 0.8366407419411672 |
| prefix_wrong_consensus_r3 | 60 | 0.26666666666666666 | 0.7333333333333333 | 0.0 | 0.0 | 2 | 0.8366407419411672 |

## Notes

- Answer rates use non-failed outputs as denominator.
- `answer_entropy` is Shannon entropy over normalized non-failed answers, using log base 2.
- No raw model text is included in this report.
