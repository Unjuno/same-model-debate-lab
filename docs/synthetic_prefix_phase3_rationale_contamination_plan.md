# Synthetic Prefix Phase 3 Rationale-Contamination Plan

## Purpose

Plan the next diagnostic experiment after Phase 2c.

## Research Question

When a prior answer shifts the model toward a target-wrong output, is the shift driven mainly by the numeric answer anchor, by the accompanying rationale, or by the combination of answer plus rationale?

## Why This Follows Phase 2c

Phase 2c showed that the consensus effect persisted across prompt formats. The next step is to separate the numeric anchor from the explanatory text that may travel with it.

## Conditions

Use a minimal, controlled design:

- `baseline_no_prefix`
- `wrong_answer_only`
- `wrong_rationale_only`
- `wrong_answer_plus_rationale`
- `correct_answer_only`
- `correct_answer_plus_rationale`

Optional later extension:

- `conflicting_wrong_answer_correct_rationale`
- `conflicting_correct_answer_wrong_rationale`

Keep the optional extensions out of the first run.

## Item Source

Use the same 9 diagnostic GSM8K items from Phase 2b/2c.

## Prompt Design

Use one output format only at first: `plain_final`.

Keep the final instruction simple:

```text
Return only the final numeric answer. Do not include explanation.
```

Reason:

- Phase 2c showed `plain_final` has low effective failure and avoids answer-tag/JSON extractor issues.
- This keeps Phase 3 focused on rationale contamination rather than output-format recovery.

Rationale source:

- Use an external rationale definition file for auditability.
- Keep the rationale file separate from the dataset builder so the gold and target-wrong fields can be validated against the Phase 2c source rows.

Rationale construction:

- Use synthetic rationales, not copied model traces.
- Each item should have a concise correct rationale leading to the gold answer.
- Each item should have a concise wrong rationale leading to the target wrong answer.
- Rationales should be short, arithmetic-style, and structurally plausible.
- Do not include long chain-of-thought-like text.
- Do not claim these are hidden model thoughts.
- Label them only as `previous agent explanation` or similar.

Important:

- For `wrong_rationale_only`, include the wrong explanation but omit the final numeric answer if possible.
- The rationale may contain intermediate numbers, but should avoid explicitly stating the target wrong answer as a final answer.
- This helps separate reasoning contamination from direct numeric answer anchoring.

- For `answer_only`, include only prior agent answer, no rationale.
- For `answer_plus_rationale`, include both prior answer and explanation.

## Dataset Size

Recommended first run:

- 9 items x 6 conditions x 20 replicates = 1080 rows
- 1080 rows x 3 agents = 3240 outputs

If runtime is a concern:

- 9 items x 6 conditions x 10 replicates = 540 rows
- 1620 outputs

## Metrics

- `correct_rate`
- `target_wrong_rate`
- `other_rate`
- `effective_extraction_failure_rate`
- `answer_entropy`
- `answer_only_vs_rationale_only` deltas
- `answer_plus_rationale` interaction effect
- item-level heterogeneity

## Interpretation

- If `wrong_answer_only` shifts `target_wrong` but `wrong_rationale_only` does not, numeric anchor dominates.
- If `wrong_rationale_only` shifts `target_wrong` without explicit final answer, rationale contamination is plausible.
- If `wrong_answer_plus_rationale` is stronger than either alone, answer and rationale may combine additively or interactively.
- If `correct_rationale` rescues correct outputs more than `correct_answer_only`, rationale may provide corrective structure beyond answer anchoring.

## Risks and Confounds

- rationale wording bias
- wrong rationale accidentally reveals target answer
- rationales vary in persuasiveness across items
- small item count
- target_wrong derivation issue
- same model/backend/config only

## Implementation Notes

Do not implement Phase 3 builder or analyzer yet unless explicitly asked later. This task is planning only.

## Artifact Policy

Do not commit future Phase 3 raw outputs or generated reports by default.
