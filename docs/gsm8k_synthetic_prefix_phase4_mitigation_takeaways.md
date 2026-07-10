# GSM8K Synthetic Prefix Phase 4 Takeaways

This is a curated, research-facing summary of the completed Phase 4 mitigation diagnostic.
It should be read as exploratory and diagnostic, not as a safety proof or benchmark-level claim.

## Purpose

Phase 4 tests whether protocol-level controls can reduce same-model debate contamination driven by shared numeric anchors.
The core question is not whether contamination disappears, but how much different protocol designs attenuate it.

## Design

- Dataset: 9 GSM8K diagnostic items
- Conditions: `independent`, `full_context_debate`, `answer_hidden_debate`, `numeric_masked_debate`, `commit_then_numeric_masked_debate`
- Replicates: 20
- Scope: one model/backend/config family, repeated stochastic samples

## Aggregate Results

The run covered 900 total outputs.

- `independent`: correct_rate `0.094`, target_wrong_rate `0.006`
- `full_context_debate`: correct_rate `0.039`, target_wrong_rate `0.072`
- `answer_hidden_debate`: correct_rate `0.111`, target_wrong_rate `0.000`
- `numeric_masked_debate`: correct_rate `0.106`, target_wrong_rate `0.000`
- `commit_then_numeric_masked_debate`: correct_rate `0.100`, target_wrong_rate `0.006`

The full-context condition was the most contamination-prone in this diagnostic.
No target-wrong outputs were observed under `answer_hidden_debate` or `numeric_masked_debate` in this run.

## Condition-Effect Interpretation

- `full_context_debate` increased target-wrong rate relative to `independent`
- `answer_hidden_debate` reduced target-wrong rate relative to `full_context_debate`
- `numeric_masked_debate` showed a similar reduction relative to `full_context_debate`
- `commit_then_numeric_masked_debate` also reduced target-wrong rate relative to `full_context_debate`, but less cleanly than pure masking in this run

The main readout here is attenuation, not elimination.
The protocol controls did not make the task easy, but they were associated with lower observed target-wrong convergence than full-context debate in this diagnostic.

## Relation to Phase 3 and Phase 3b

Phase 3 and Phase 3c established that shared numeric content can act as an anchor, and that answer labels are not the only exposure form that matters.
Phase 4 turns that mechanism result into a protocol question: if contamination is partly driven by numeric-anchor exposure, does hiding answers or masking numbers reduce collapse?

This diagnostic is consistent with the answer being yes in this setting, but only as an exploratory result for this model/backend/config family.

## Protocol-Design Implications

- Hiding final answers alone is not the whole story, but it is a useful control.
- Numeric masking is also useful, consistent with Phase 3c's view that numeric content itself can act as an anchor.
- A commit-then-mask structure may preserve some interaction while reducing collapse, but it is not obviously superior to simple masking in this diagnostic.
- If the goal is to preserve multi-agent structure while reducing contamination, the protocol should control what numeric content is visible, not just whether an answer label is visible.

## Cautions and Limitations

- This is a small, exploratory diagnostic on a single model/backend/config family.
- The selected items are diagnostic items, not a random benchmark sample.
- Repeated stochastic samples are not independent benchmark items.
- History-dependent collapse metrics are not applicable here because this is a synthetic-prefix mitigation diagnostic rather than a live debate history run.
- The results should not be generalized to human social influence or persuasion.

## Main Claim

In this diagnostic setting, full shared context produced the most contamination, while hiding explicit answers or masking numeric tokens was associated with lower observed target-wrong convergence relative to full-context debate. The result is consistent with the Phase 3c interpretation that numeric exposure is a meaningful anchor source, and it suggests that protocol design can reduce, though not eliminate, same-model contamination.
