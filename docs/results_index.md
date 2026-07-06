# Exploratory Results Index

This page indexes the current exploratory same-model debate experiments in one place.
It is intentionally post-hoc, limited to a single model/backend/config family, and should be read as a descriptive summary rather than a general claim.

See [docs/research_framing.md](research_framing.md) for the broader framing and artifact policy.

## Summary Table

| experiment | subset | condition | n | accuracy | oracle_at_k | answer_loss_rate | same_error_agreement_rate | diversity_drop | extraction_failure_rate | note |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| AQuA 100 independent | screened subset | independent | 100 | exploratory screening | 0.8900 | - | - | - | - | 2 partial-correct items selected from 100 screened |
| AQuA 254 newonly independent | screened subset | independent | 254 | exploratory screening | 0.9134 | - | - | - | - | 9 partial-correct items selected from 254 screened |
| AQuA 11 non-role R3 | post-hoc selected subset | debate_3r_full_context | 11 | 0.6364 | 0.9091 | 0.3 | - | - | 0.0 | same-model non-role R3 on the 11-item exploratory subset |
| AQuA 11 role-separated R3 | post-hoc selected subset | role-separated R3 | 11 | 0.5455 | 0.7273 | 0.25 | - | - | 0.0909 | role-separated variant appeared more fragile in this small subset |
| AQuA screened3 non-role R3 | post-hoc selected subset | debate_3r_full_context | 3 | 0.3333 | 0.6667 | - | - | - | - | key example: `aqua_test_1_000086`; transient correct consensus appeared and was lost before final aggregation; additional diagnostic example, not replication |
| GSM8K 300 independent | screened subset | independent | 300 | 0.9533 | 0.97 | - | - | - | - | independent GSM8K screening; selected partial-correct items = 9 |
| GSM8K partial9 debate R3 | post-hoc selected subset | debate_3r_full_context | 9 | 5/9 | 8/9 | 0.5 | 0.2222222222222222 | 0.3333333333333333 | 0.0 | final_round_majority 5/9; initial_majority 7/9; all_round_majority 7/9; oracle_any_history_correct 9/9 |
| GSM8K synthetic prefix phase2c | post-hoc selected subset | prompt-format robustness check | 9 | exploratory | exploratory | - | - | - | - | consensus effects persisted across answer_tag, JSON, and plain-final formats; JSON required format-aware recovery |
| GSM8K synthetic prefix phase3 | post-hoc selected subset | rationale-contamination diagnostic | 9 | exploratory | exploratory | - | - | - | - | aggregate results favored numeric answer anchoring over rationale-only contamination, with item-level heterogeneity |
| GSM8K synthetic prefix phase3b | completed diagnostic | rationale-strength / wording-variant check | 9 | exploratory | exploratory | - | - | - | - | rationale-strength follow-up; numeric answer anchoring remained dominant in aggregate, with item-level heterogeneity |
| GSM8K synthetic prefix phase3c | completed diagnostic | numeric-anchor presentation-format check | 9 | exploratory | exploratory | - | - | - | - | answer-label framing is strongest; unlabeled, explanation-internal, and intermediate numbers also increase target-wrong outputs, while warning phrasing attenuates but does not eliminate the effect |
| GSM8K synthetic prefix phase4 | planned mitigation diagnostic | protocol-level contamination attenuation check | - | planned | planned | - | - | - | - | planned Phase 4 will test whether hiding answers, masking numeric tokens, and committing before exposure attenuate contamination |

## GSM8K Partial9 Notes

- `transient_correct_majority_lost`: 2
- `transient_correct_consensus_lost`: 1
- key example: `gsm8k_test_000234`, where a correct unanimous consensus became a wrong unanimous consensus

## AQuA Screened3 Notes

- key example: `aqua_test_1_000086`
- transient correct consensus appeared and was lost before final aggregation
- this is an additional diagnostic example, not replication

## Cautions

- These are exploratory, post-hoc summaries.
- The selected subsets are not random samples of the benchmark distributions.
- `oracle_at_k` in the run summaries is not the same as `oracle_any_history_correct` from the aggregation analyzer; the latter is a full-history upper bound.
- The results come from one model/backend/config family, so they may not generalize.

## Phase 3c References

- Raw/generated result doc: [docs/gsm8k_synthetic_prefix_phase3c_numeric_anchor_format_9items_results.md](gsm8k_synthetic_prefix_phase3c_numeric_anchor_format_9items_results.md)
- Curated takeaway doc: [docs/gsm8k_synthetic_prefix_phase3c_numeric_anchor_format_takeaways.md](gsm8k_synthetic_prefix_phase3c_numeric_anchor_format_takeaways.md)
