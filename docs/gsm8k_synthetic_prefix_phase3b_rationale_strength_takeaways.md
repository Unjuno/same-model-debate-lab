# GSM8K Synthetic Prefix Phase 3b Rationale-Strength Takeaways
## Status
Exploratory diagnostic result; same model/backend/config family; repeated stochastic prompt samples; not benchmark-level evidence.

## Setup
9 diagnostic GSM8K items
8 conditions:
  baseline_no_prefix
  wrong_answer_only
  weak_wrong_rationale_only
  medium_wrong_rationale_only
  strong_wrong_rationale_only
  weak_wrong_answer_plus_rationale
  medium_wrong_answer_plus_rationale
  strong_wrong_answer_plus_rationale
20 replicates
3 agents per row
1440 rows
4320 outputs
plain_final output format
0 extraction failures

## Main Result
Phase 3b reinforces that numeric answer anchoring remains the main aggregate driver in this diagnostic setting. Rationale-only effects are present, but they are not monotonic in rationale strength: stronger rationales do not uniformly produce stronger contamination. Instead, rationale text appears item-structure dependent, sometimes acting as a contaminating cue and sometimes as a corrective cue. Adding rationale to a wrong answer can reduce the wrong-answer anchor, which is consistent with answer-rationale tension rather than simple amplification.

## Aggregate Results
| condition | correct_rate | target_wrong_rate | effective_failure |
| --- | ---: | ---: | ---: |
| baseline_no_prefix | 0.589 | 0.406 | 0.000 |
| wrong_answer_only | 0.117 | 0.883 | 0.000 |
| weak_wrong_rationale_only | 0.633 | 0.650 | 0.000 |
| medium_wrong_rationale_only | 0.389 | 0.406 | 0.000 |
| strong_wrong_rationale_only | 0.478 | 0.494 | 0.000 |
| weak_wrong_answer_plus_rationale | 0.622 | 0.639 | 0.000 |
| medium_wrong_answer_plus_rationale | 0.400 | 0.417 | 0.000 |
| strong_wrong_answer_plus_rationale | 0.500 | 0.517 | 0.000 |

## Condition Effects
| effect | value |
| --- | ---: |
| wrong_answer_delta_target_wrong | +0.478 |
| weak_wrong_rationale_delta_target_wrong | +0.244 |
| medium_wrong_rationale_delta_target_wrong | +0.000 |
| strong_wrong_rationale_delta_target_wrong | +0.089 |
| medium_minus_weak_wrong_rationale_delta_target_wrong | -0.244 |
| strong_minus_weak_wrong_rationale_delta_target_wrong | -0.156 |
| strong_minus_medium_wrong_rationale_delta_target_wrong | +0.089 |
| weak_answer_plus_minus_wrong_answer_delta_target_wrong | -0.017 |
| medium_answer_plus_minus_wrong_answer_delta_target_wrong | -0.228 |
| strong_answer_plus_minus_wrong_answer_delta_target_wrong | -0.128 |

## Item-Level Heterogeneity
| item | wrong_answer_delta_target_wrong | wrong_rationale_delta_target_wrong | note |
| --- | ---: | ---: | --- |
| gsm8k_test_000255 | +1.00 | +0.00 | numeric anchor saturated |
| gsm8k_test_000241 | +0.95 | +0.95 | contamination-positive |
| gsm8k_test_000187 | +0.70 | +0.70 | contamination-positive |
| gsm8k_test_000147 | +0.60 | +0.45 | contamination-positive |
| gsm8k_test_000236 | +0.40 | +0.00 | numeric anchor dominant |
| gsm8k_test_000234 | +0.35 | -0.40 | corrective reversal |
| gsm8k_test_000012 | +0.30 | -0.05 | numeric anchor moderate |
| gsm8k_test_000093 | +0.05 | -0.30 | partially corrective |
| gsm8k_test_000089 | -0.05 | -0.95 | corrective reversal |

## Key Diagnostic Examples
- `gsm8k_test_000234`: wrong answer `14` alone is a strong anchor, but the accompanying rationale reintroduces the missing demand and pushes the model back toward the gold answer `21`.
- `gsm8k_test_000089`: the wrong rationale exposes enough structure to recover the correct answer rather than reinforce the wrong anchor.
- `gsm8k_test_000241`: a positive contamination example where both wrong answer and wrong rationale push strongly toward the target-wrong output.

## Interpretation
The result is consistent with numeric answer anchoring being the primary mechanism behind the Phase 2b/2c consensus-prefix effect in this diagnostic setting. Rationale-only contamination is not absent, but it is item-dependent and not the dominant aggregate effect under the short synthetic rationale design used here. Adding rationale to a wrong answer can weaken the wrong-answer anchor when the explanation reintroduces the problem structure. Stronger rationale wording did not produce a clean monotonic increase in contamination.

## Limitations
- small item count
- selected diagnostic items
- single model/backend/config family
- short synthetic rationales
- rationale wording may act as either contaminating cue or corrective cue
- same stochastic samples are not independent benchmark items
- target_wrong derivation issue remains for values such as 106.12
- natural debate transcripts may contain longer and more persuasive rationales

## Next Step
A natural next diagnostic is Phase 3c: numeric anchor presentation format. That experiment would test whether prior numeric answers are most influential when labeled as explicit answers, versus appearing as unlabeled numbers, intermediate values, or explanation text.
