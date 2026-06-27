# Research Framing

## Core Question

Does same-model multi-agent debate preserve the benefits of independent sampling, or can interaction and prior-answer exposure reduce effective independence and amplify shared errors?

## Structural Human Analogy

Human group-judgment studies often examine majority exposure, unanimity, repeated questioning, and misinformation-like prior statements. This repository uses those as structural templates, not as claims about LLM psychology.

The analogy is about input structure and output distribution shifts. It is not a claim that LLMs experience conformity pressure, social motives, belief change, memory distortion, or persuasion in the human sense.

## What This Project Tests

- answer loss
- same-error agreement
- diversity collapse
- consensus anchoring
- majority versus unanimity effects
- synthetic-prefix sensitivity
- extraction and format collapse under prefix conditions

## What This Project Does Not Claim

- LLMs have human social motives
- LLMs experience conformity pressure
- multi-agent debate is generally harmful
- current results are benchmark-level conclusions
- current results are statistically decisive

## Current Experimental Lines

1. Independent versus debate comparisons on AQuA and GSM8K
2. Partial-correct GSM8K item diagnostics
3. Synthetic-prefix continuation on `gsm8k_test_000234`
4. Phase 2 majority, unanimity, and recency disentanglement
5. Phase 2b multi-item diagnostic replication
6. Failure-aware stratified analysis
7. Phase 2c prompt-format robustness check and Phase 3 rationale-contamination planning
8. Phase 3 rationale-contamination diagnostics with an external rationale definition file
9. Phase 3 rationale-contamination takeaways and Phase 3b rationale-strength follow-up
10. Phase 3b rationale-strength / wording-variant diagnostics
11. Phase 3b takeaways now separate aggregate numeric anchoring from item-level rationale effects
12. Phase 3c numeric-anchor presentation-format diagnostics

## Current Evidence Status

The current results are exploratory and diagnostic. They are consistent with:

- consensus prefixes can strongly shift output distributions
- wrong consensus can increase target-wrong outputs
- correct consensus can recover correct outputs
- 2-to-1 majority prefixes appear weaker than unanimous prefixes in the current diagnostics
- extraction failures are nontrivial and item-concentrated, requiring stratified analysis

These results suggest structural sensitivity to prior-answer exposure, but they do not establish causality or generalize beyond the present model/backend/config family.

## Open Risks and Confounds

- small item count
- item selection bias
- shared prior errors
- prompt wording effects
- answer extraction failures
- model-specific behavior
- repeated stochastic samples are not independent benchmark items

## Next Validation Steps

- inspect raw text for failure-heavy items
- keep valid-baseline and failure-heavy strata separate
- replicate on another model family
- test prompt-format robustness
- test answer-only versus rationale-prefix conditions
- only later scale to larger benchmark-level claims

## Artifact Policy

Raw model outputs, run directories, generated summaries, and generated result reports are local artifacts by default. Stable conclusions may be promoted into curated documentation, but `runs/*`, raw JSONL, summary JSON, and generated result markdown should not be committed unless explicitly reviewed and intentionally promoted.
