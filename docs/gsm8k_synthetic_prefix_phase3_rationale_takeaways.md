# GSM8K Synthetic Prefix Phase 3 Rationale-Contamination Takeaways

## Status

Exploratory diagnostic result; same model/backend/config family; repeated stochastic prompt samples; not benchmark-level evidence.

## Setup

- 9 diagnostic GSM8K items
- 6 conditions:
  - `baseline_no_prefix`
  - `wrong_answer_only`
  - `wrong_rationale_only`
  - `wrong_answer_plus_rationale`
  - `correct_answer_only`
  - `correct_answer_plus_rationale`
- 20 replicates
- 3 agents per row
- 1080 rows
- 3240 outputs
- `plain_final` output format
- 0 extraction failures

## Main Result

Phase 3 suggests that prior numeric answers are the dominant driver of answer-distribution shifts in this diagnostic setting. Wrong-rationale-only prefixes showed a weak aggregate effect, but item-level effects were heterogeneous. Some wrong rationales increased target-wrong outputs, while others appeared to reactivate the correct problem structure and reduce target-wrong outputs.

## Aggregate Results

| condition | correct_rate | target_wrong_rate | effective_failure |
| --- | ---: | ---: | ---: |
| baseline_no_prefix | 0.589 | 0.406 | 0.000 |
| wrong_answer_only | 0.117 | 0.883 | 0.000 |
| wrong_rationale_only | 0.539 | 0.450 | 0.000 |
| wrong_answer_plus_rationale | 0.278 | 0.722 | 0.000 |
| correct_answer_only | 0.950 | 0.050 | 0.000 |
| correct_answer_plus_rationale | 0.972 | 0.028 | 0.000 |

## Condition Effects

| effect | value |
| --- | ---: |
| wrong_answer_delta_target_wrong | +0.478 |
| wrong_rationale_delta_target_wrong | +0.044 |
| wrong_answer_plus_rationale_delta_target_wrong | +0.317 |
| wrong_answer_plus_minus_wrong_answer_delta_target_wrong | -0.161 |
| correct_answer_delta_correct | +0.361 |
| correct_answer_plus_rationale_delta_correct | +0.383 |
| correct_answer_plus_minus_correct_answer_delta_correct | +0.022 |

## Item-Level Heterogeneity

| item | wrong_answer_delta_target_wrong | wrong_rationale_delta_target_wrong | note |
| --- | ---: | ---: | --- |
| `gsm8k_test_000255` | +1.00 | +0.00 | numeric answer anchor saturated; wrong rationale alone did not target wrong |
| `gsm8k_test_000241` | +0.95 | +0.95 | wrong answer and wrong rationale both saturated target wrong |
| `gsm8k_test_000187` | +0.70 | +0.70 | both wrong answer and wrong rationale strongly increased target wrong |
| `gsm8k_test_000147` | +0.60 | +0.45 | both numeric anchor and rationale contamination visible |
| `gsm8k_test_000236` | +0.40 | +0.00 | numeric anchor moderate; rationale-only neutral |
| `gsm8k_test_000234` | +0.35 | -0.40 | wrong rationale reversed wrong-answer anchor |
| `gsm8k_test_000012` | +0.30 | -0.05 | numeric anchor moderate; rationale-only weak/negative |
| `gsm8k_test_000093` | +0.05 | -0.30 | baseline already wrong-heavy; rationale-only partially corrected |
| `gsm8k_test_000089` | -0.05 | -0.95 | wrong rationale recovered correct answer |

## Key Diagnostic Examples

### `gsm8k_test_000234`

- baseline: target_wrong `14` = 8/20, correct `21` = 12/20
- wrong_answer_only: target_wrong `14` = 15/20, correct `21` = 5/20
- wrong_rationale_only: target_wrong `14` = 0/20, correct `21` = 20/20
- wrong_answer_plus_rationale: target_wrong `14` = 1/20, correct `21` = 19/20

Interpretation: the wrong answer is a strong anchor, but the wrong rationale reintroduces the correct problem structure and weakens that anchor.

### `gsm8k_test_000089`

- baseline: target_wrong `18` = 19/20, correct `24` = 1/20
- wrong_answer_only: target_wrong `18` = 18/20, correct `24` = 2/20
- wrong_rationale_only: target_wrong `18` = 0/20, correct `24` = 20/20
- wrong_answer_plus_rationale: target_wrong `18` = 0/20, correct `24` = 20/20

Interpretation: the explanation acts as a corrective cue in this item, not a contaminating one.

### `gsm8k_test_000241`

- wrong_answer_delta_target_wrong = +0.95
- wrong_rationale_delta_target_wrong = +0.95

Interpretation: this is a contamination-positive case where both answer and rationale strongly push toward the wrong output.

## Interpretation

The result is consistent with numeric answer anchoring being the primary mechanism behind the Phase 2b/2c consensus-prefix effect in this diagnostic setting. Rationale-only contamination is not absent, but it is item-dependent and not the dominant aggregate effect under the short synthetic rationale design used here.

Adding rationale to a wrong answer can weaken the wrong-answer anchor when the explanation reintroduces the problem structure.

## Limitations

- small item count
- selected diagnostic items
- single model/backend/config family
- short synthetic rationales
- rationale wording may act as either a contaminating cue or corrective cue
- same stochastic samples are not independent benchmark items
- target_wrong derivation issue remains for values such as `106.12`
- natural debate transcripts may contain longer and more persuasive rationales

## Next Step

A natural next diagnostic is Phase 3b: rationale strength / wording variants. This would test whether rationale-only contamination becomes stronger with more explicit, more persuasive, or more misleading rationale wording, while still avoiding direct final-answer leakage.
