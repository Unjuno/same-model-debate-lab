# GSM8K Partial9 Transient Correctness Analysis

## Summary
| category | count |
| --- | ---: |
| recovered_to_correct | 1 |
| transient_correct_majority_lost | 2 |
| persistent_error | 1 |
| preserved_correct | 4 |
| transient_correct_consensus_lost | 1 |

## Item Table
| item_id | gold | initial_majority | final_majority | any_round_majority_correct | any_round_unanimous_correct | category |
| --- | --- | --- | --- | --- | --- | --- |
| gsm8k_test_000012 | 13 | 12 | 13 | True | True | recovered_to_correct |
| gsm8k_test_000089 | 24 | 24 | 18 | True | False | transient_correct_majority_lost |
| gsm8k_test_000093 | 36 | 36.36 | 36.36 | False | False | persistent_error |
| gsm8k_test_000147 | 75 | 75 | 15 | True | False | transient_correct_majority_lost |
| gsm8k_test_000187 | 106 | 106 | 106 | True | True | preserved_correct |
| gsm8k_test_000234 | 21 | 21 | 14 | True | True | transient_correct_consensus_lost |
| gsm8k_test_000236 | 31 | 31 | 31 | True | True | preserved_correct |
| gsm8k_test_000241 | 6 | 6 | 6 | True | True | preserved_correct |
| gsm8k_test_000255 | 192 | 192 | 192 | True | True | preserved_correct |

## Highlighted Items
| item_id | gold | category | initial_majority | final_majority |
| --- | --- | --- | --- | --- |
| gsm8k_test_000089 | 24 | transient_correct_majority_lost | 24 | 18 |
| gsm8k_test_000147 | 75 | transient_correct_majority_lost | 75 | 15 |
| gsm8k_test_000234 | 21 | transient_correct_consensus_lost | 21 | 14 |

No raw transcripts are included in this report.
