# AQuA Follow-Up 2-Item Sanity Check

## Purpose
Record the completed 2-item AQuA follow-up sanity check.

## Dataset
- `data/benchmarks/aqua_calibrated_partial_followup_15.jsonl`
- Item count: `2`
- Items:
  - `aqua_test_1_000106`
  - `aqua_test_1_000138`

## Run Summary
| metric | value |
| --- | ---: |
| n | 2 |
| accuracy | 1.0 |
| oracle_at_k | 1.0 |
| answer_loss_rate | 0.0 |
| same_error_agreement_rate | 0.0 |
| diversity_drop | 0.0 |
| extraction_failure_rate | 0.0 |

## Aggregation Summary
| rule | accuracy | answer_loss_rate | loss_denominator |
| --- | ---: | ---: | ---: |
| initial_majority | 1.0 | 0.0 | 2 |
| final_round_majority | 1.0 | 0.0 | 2 |
| all_round_majority | 1.0 | 0.0 | 2 |
| oracle_any_history_correct | 1.0 | 0.0 | 2 |

## Flip Dynamics Summary
| metric | value |
| --- | ---: |
| n | 2 |
| preserved_correct | 2 |
| correct_to_wrong | 0 |
| wrong_to_correct | 0 |
| persistent_error | 0 |
| correct_path_retention_rate | 1.0 |
| correct_to_wrong_majority_rate | 0.0 |
| wrong_to_correct_majority_rate | 0.0 |

## Item-Level Table
| item_id | gold | initial_majority | final_majority | majority_transition_category |
| --- | --- | --- | --- | --- |
| aqua_test_1_000106 | D | D | D | preserved_correct |
| aqua_test_1_000138 | C | C | C | preserved_correct |

## Interpretation
The two-item follow-up was solved unanimously from the initial round, so it provides no meaningful opportunity to observe correct-to-wrong or wrong-to-correct majority transitions.
This is only a sanity check and should not be framed as a replication of the trajectory-mixing pattern.

## Limitation
- `n=2` only
- not a replication
- not a calibrated partial-correct test in practice
