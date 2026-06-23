# Synthetic Prefix Phase 3b Rationale-Strength Plan

## Purpose

Test whether rationale-only contamination is sensitive to rationale strength and wording.

## Research Question

If numeric answer anchoring is the dominant aggregate mechanism, under what conditions can rationale text override, amplify, or reverse that anchor?

## Why This Follows Phase 3

Phase 3 found strong aggregate numeric answer anchoring, weak aggregate wrong-rationale-only effects, and substantial item-level heterogeneity. Phase 3b tests whether rationale-only contamination depends on rationale strength or wording.

## Item Groups

- Rationale-only contamination positive: `gsm8k_test_000241`, `gsm8k_test_000187`, `gsm8k_test_000147`
- Rationale corrective / reversal: `gsm8k_test_000089`, `gsm8k_test_000234`, `gsm8k_test_000093`
- Numeric-anchor dominant: `gsm8k_test_000255`, `gsm8k_test_000236`, `gsm8k_test_000012`

## Conditions

Initial Phase 3b conditions:

- `baseline_no_prefix`
- `wrong_answer_only`
- `weak_wrong_rationale_only`
- `medium_wrong_rationale_only`
- `strong_wrong_rationale_only`
- `weak_wrong_answer_plus_rationale`
- `medium_wrong_answer_plus_rationale`
- `strong_wrong_answer_plus_rationale`

Keep the first run focused on wrong-answer and wrong-rationale mechanisms.

## Rationale Variants

- `weak_wrong_rationale`: similar in strength and style to Phase 3, short and conservative
- `medium_wrong_rationale`: more structured and more explicit about the misleading reasoning path
- `strong_wrong_rationale`: more persuasive and explicit about the misleading reasoning path

Forbidden patterns inside wrong rationale text:

- `Answer: {target_wrong}`
- `the answer is {target_wrong}`
- `therefore the answer is {target_wrong}`
- `final answer is {target_wrong}`
- `<answer>{target_wrong}</answer>`
- `#### {target_wrong}`

Permitted style:

- points to the smaller count
- keeps the decimal amount instead of rounding
- counts only the direct weekly need
- does not add the second component
- uses only the first group
- treats the extra quantity as spread too thinly

## Dataset Size

Default:

- 9 items x 8 conditions x 20 replicates = 1440 rows
- 1440 rows x 3 agents = 4320 outputs

Fallback smaller run:

- 9 items x 8 conditions x 10 replicates = 720 rows
- 2160 outputs

## Metrics

- `correct_rate`
- `target_wrong_rate`
- `other_rate`
- `answer_entropy`
- `effective_extraction_failure_rate`
- `weak_vs_strong_rationale_delta_target_wrong`
- `wrong_answer_plus_weak_vs_wrong_answer_only`
- `wrong_answer_plus_strong_vs_wrong_answer_only`
- item-group effects

## Interpretation

- If `strong_wrong_rationale_only` increases `target_wrong` over `weak_wrong_rationale_only`, rationale contamination is wording-strength dependent.
- If `strong_wrong_answer_plus_rationale` exceeds `wrong_answer_only`, rationale can amplify numeric answer anchoring.
- If `strong_wrong_answer_plus_rationale` remains below `wrong_answer_only`, rationale may still reactivate problem structure or create tension with the numeric anchor.
- If positive, reversal, and numeric-anchor groups behave differently, rationale effects are item-structure dependent.

## Risks and Confounds

- strong rationale may accidentally reveal the final target answer
- wording strength is hard to calibrate
- item groups are post-hoc from Phase 3
- small item count
- single model/backend/config family
- natural debate rationales may differ from synthetic rationales

## Artifact Policy

Do not commit future Phase 3b raw outputs or generated reports by default.
