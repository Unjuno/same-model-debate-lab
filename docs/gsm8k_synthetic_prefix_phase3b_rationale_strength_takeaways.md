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
Phase 3b reinforces that numeric answer anchoring remains the main aggregate driver in this diagnostic setting. Rationale-only effects are present, but they are not monotonic in rationale strength: stronger rationales do not uniformly produce stronger contamination. Instead, rationale text appears item-group dependent, sometimes acting as a contaminating cue and sometimes as a corrective cue. Adding rationale to a wrong answer can reduce the wrong-answer anchor, which is consistent with answer-rationale tension rather than simple amplification.

## Aggregate Results
| condition | correct_rate | target_wrong_rate | effective_failure |
| --- | ---: | ---: | ---: |
| baseline_no_prefix | 0.628 | 0.367 | 0.000 |
| wrong_answer_only | 0.100 | 0.900 | 0.000 |
| weak_wrong_rationale_only | 0.378 | 0.611 | 0.000 |
| medium_wrong_rationale_only | 0.633 | 0.367 | 0.000 |
| strong_wrong_rationale_only | 0.467 | 0.456 | 0.000 |
| weak_wrong_answer_plus_rationale | 0.117 | 0.883 | 0.000 |
| medium_wrong_answer_plus_rationale | 0.322 | 0.672 | 0.000 |
| strong_wrong_answer_plus_rationale | 0.228 | 0.772 | 0.000 |

## Condition Effects
| effect | value |
| --- | ---: |
| wrong_answer_delta_target_wrong | +0.533 |
| weak_wrong_rationale_delta_target_wrong | +0.244 |
| medium_wrong_rationale_delta_target_wrong | +0.000 |
| strong_wrong_rationale_delta_target_wrong | +0.089 |
| medium_minus_weak_wrong_rationale_delta_target_wrong | -0.244 |
| strong_minus_weak_wrong_rationale_delta_target_wrong | -0.156 |
| strong_minus_medium_wrong_rationale_delta_target_wrong | +0.089 |
| weak_answer_plus_minus_wrong_answer_delta_target_wrong | -0.017 |
| medium_answer_plus_minus_wrong_answer_delta_target_wrong | -0.228 |
| strong_answer_plus_minus_wrong_answer_delta_target_wrong | -0.128 |

## Item-Group Effects
| item_group | wrong_answer_delta_target_wrong | weak_wrong_rationale_delta_target_wrong | medium_wrong_rationale_delta_target_wrong | strong_wrong_rationale_delta_target_wrong | strong_answer_plus_minus_wrong_answer_delta_target_wrong | note |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| numeric_anchor_dominant | +0.550 | -0.017 | -0.117 | +0.000 | -0.083 | numeric anchor dominates, rationale effect is weak or mixed |
| rationale_contamination_positive | +0.750 | +0.650 | +0.583 | +0.533 | -0.033 | rationales tend to reinforce target-wrong outputs here |
| rationale_corrective_reversal | +0.300 | +0.100 | -0.467 | -0.267 | -0.267 | rationales can reverse the wrong-answer anchor here |

## Key Diagnostic Examples
- `numeric_anchor_dominant`: wrong-answer exposure remains strong, while rationale-only effects are weak or mixed.
- `rationale_contamination_positive`: both wrong-answer and rationale prefixes push toward the target-wrong output.
- `rationale_corrective_reversal`: rationale text reintroduces structure and can reduce the wrong-answer anchor.

## Interpretation
The result is consistent with numeric answer anchoring being the primary mechanism behind the Phase 2b/2c consensus-prefix effect in this diagnostic setting. Rationale-only contamination is not absent, but it is item-group dependent and not the dominant aggregate effect under the short synthetic rationale design used here. Adding rationale to a wrong answer can weaken the wrong-answer anchor when the explanation reintroduces the problem structure. Stronger rationale wording did not produce a clean monotonic increase in contamination.

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
