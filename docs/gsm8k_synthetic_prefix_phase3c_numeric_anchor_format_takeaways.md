# GSM8K Synthetic Prefix Phase 3c Takeaways

This is a curated, research-facing summary of the completed Phase 3c diagnostic.
It should be read as exploratory and descriptive, not as benchmark-level evidence or causal proof.

## Purpose

Phase 3c asks whether numeric anchoring depends only on explicit answer labeling, or whether numeric values in shared context can influence the next response even when they are unlabeled, embedded in explanations, or presented as intermediate values.

## Design

- Dataset: 9 GSM8K diagnostic items
- Conditions: baseline, labeled wrong answer, unlabeled wrong number, wrong number in explanation, wrong number as intermediate value, wrong answer with uncertainty, wrong answer marked possibly wrong
- Metric focus: correct rate, target-wrong rate, and deltas against baseline
- Scope: repeated stochastic prompt samples in one model/backend/config family

## Aggregate Results

- Baseline correct rate was `0.622`, with target-wrong rate `0.378`
- `wrong_answer_labeled` was the strongest condition: target-wrong rate `0.928`
- Bare numeric exposure remained strong:
  - `wrong_number_unlabeled` target-wrong rate `0.739`
  - `wrong_number_in_explanation` target-wrong rate `0.789`
  - `wrong_number_as_intermediate` target-wrong rate `0.772`
- Cautionary framing weakened the effect, but did not remove it:
  - `wrong_answer_with_uncertainty` target-wrong rate `0.794`
  - `wrong_answer_marked_possibly_wrong` target-wrong rate `0.667`

## Condition-Effect Interpretation

- Explicit `Answer: X` labeling is the strongest anchor format in this diagnostic.
- The effect is not limited to explicit answer labels.
- Bare numbers, explanation-internal numbers, and intermediate-value numbers all substantially increase target-wrong outputs over baseline.
- Uncertainty and explicit error warnings attenuate the effect, but they do not eliminate it.
- `possibly wrong` attenuates more than generic uncertainty, but target-wrong rate still remains above baseline.

## Item-Group Interpretation

The item groups are not interchangeable. The same presentation format does not affect all items equally.

- `numeric_anchor_dominant`
  - Numeric exposure is strong across formats.
  - The labeled-answer variant is strongest, but unlabeled and embedded-number variants are also robust.
- `rationale_contamination_positive`
  - Answer-labeled, explanation, and uncertainty formats remain strong.
  - This group is compatible with broader context sensitivity than answer labels alone.
- `rationale_corrective_reversal`
  - Unlabeled and intermediate numeric exposure is much weaker here.
  - Even so, answer labeling still increases target-wrong outputs.

This heterogeneity matters: the aggregate pattern is stable in this diagnostic, but it is not uniform across items.

## Relation to Phase 3 and Phase 3b

Phase 3 suggested that aggregate shifts were more consistent with prior numeric answer anchoring than with rationale persuasion alone. Phase 3b then showed that rationale effects are item-group dependent and non-monotonic with respect to rationale strength.

Phase 3c refines that picture by showing that the numeric anchor itself is not limited to explicit final-answer labels. Numeric values in shared context can matter even when they are unlabeled, embedded in explanations, or framed as intermediate values. In that sense, Phase 3c narrows the mechanism further: the anchor is partly a property of the numeric content itself, not only of the answer-form label.

## Protocol-Design Implications

- Hiding only final answers may be insufficient if surrounding context still exposes the relevant number.
- Reasoning text and intermediate calculations can also become anchor sources.
- Warning labels alone are not a complete mitigation strategy.
- If the goal is to reduce carryover from prior model outputs, the protocol likely needs to control both answer labels and numeric exposure in surrounding context.

## Cautions and Limitations

- This is a small, exploratory diagnostic on 9 selected items.
- The result is specific to one model/backend/config family.
- Repeated stochastic prompt samples are not independent benchmark items.
- The item groups were hand-selected for diagnostic contrast, so the heterogeneity is informative but not population-level.
- The results should not be generalized to human social influence or persuasion.

## Main Claim

In this diagnostic setting, target-wrong outputs increased most strongly when the wrong numeric value was explicitly labeled as an answer. However, the effect was not limited to answer-labeled contexts: unlabeled numbers, explanation-internal numbers, and intermediate-value numbers all substantially increased target-wrong outputs over baseline. Uncertainty and explicit error warnings attenuated, but did not eliminate, the numeric-anchor effect.
