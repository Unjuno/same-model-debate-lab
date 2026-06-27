# Synthetic Prefix Phase 3c Numeric-Anchor Format Plan
## Purpose
Test whether numeric anchoring depends on the target-wrong value being explicitly framed as a previous answer, versus appearing as an unlabeled number, explanation-internal number, intermediate value, uncertain guess, or warned previous answer.

## Research Question
If prior numeric answer anchoring is the dominant aggregate mechanism, how much of that anchoring depends on the numeric value being explicitly framed as an answer?

## Why This Follows Phase 3b
Phase 3b reinforced that numeric answer anchoring remains the dominant aggregate driver, while rationale effects are item-group dependent and non-monotonic in rationale strength. Phase 3c isolates the presentation format of the numeric value itself.

## Item Groups
- numeric_anchor_dominant
- rationale_contamination_positive
- rationale_corrective_reversal

## Conditions
- baseline_no_prefix
- wrong_answer_labeled
- wrong_number_unlabeled
- wrong_number_in_explanation
- wrong_number_as_intermediate
- wrong_answer_with_uncertainty
- wrong_answer_marked_possibly_wrong

## Dataset Size
9 items x 7 conditions x 20 replicates = 1260 rows, or 3780 outputs with 3 agents per row.

## Metrics
- correct_rate
- target_wrong_rate
- other_rate
- raw_extraction_failure_rate
- effective_extraction_failure_rate
- answer_entropy
- item-level heterogeneity
- condition effects against baseline

## Interpretation
- If wrong_answer_labeled is much stronger than wrong_number_unlabeled, answer-label framing is an important component of the anchor.
- If wrong_number_unlabeled is still strong, the number itself functions as a contextual numeric anchor.
- If wrong_number_as_intermediate is weak, final-answer framing matters.
- If wrong_answer_with_uncertainty is weaker than wrong_answer_labeled, uncertainty reduces anchoring.
- If wrong_answer_marked_possibly_wrong remains strong, warning text is insufficient to neutralize the anchor.

## Risks and Confounds
- small item count
- selected diagnostic items
- single model/backend/config family
- same stochastic samples are not independent benchmark items
- prompt wording may change more than presentation format alone
- target_wrong derivation issues may still affect some items

## Artifact Policy
Do not commit future Phase 3c raw outputs or generated reports by default.
