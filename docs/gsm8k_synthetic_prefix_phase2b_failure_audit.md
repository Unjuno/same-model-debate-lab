# Phase 2b Extraction Failure Audit

Caution:
- exploratory diagnostic
- descriptive classification of existing raw outputs
- not independent benchmark evidence
- no causal proof
- no statistical-significance claim

## Category Definitions

| category | description |
| --- | --- |
| missing_answer_tag | content exists but no `<answer>...</answer>` wrapper is present |
| empty_output | output is empty or whitespace-only |
| non_numeric_answer | answer is wrapped but not numeric for GSM8K-style items |
| contains_numeric_but_unwrapped | a numeric candidate is present in the text but not wrapped |
| multiple_candidate_numbers | multiple plausible numeric candidates are present |
| tool_or_format_noise | tool chatter, malformed markup, or obvious format noise dominates |
| unknown | catch-all when no other category fits |

## Summary Counts

| category | count |
| --- | ---: |
| contains_numeric_but_unwrapped | 0 |
| empty_output | 1503 |
| missing_answer_tag | 0 |
| multiple_candidate_numbers | 0 |
| non_numeric_answer | 0 |
| tool_or_format_noise | 0 |
| unknown | 0 |

## By Condition

| condition | n_failed_entries | categories |
| --- | ---: | --- |
| baseline_no_prefix | 240 | {'empty_output': 240} |
| single_round_correct_consensus | 240 | {'empty_output': 240} |
| single_round_correct_majority | 303 | {'empty_output': 303} |
| single_round_wrong_consensus | 360 | {'empty_output': 360} |
| single_round_wrong_majority | 360 | {'empty_output': 360} |

## By Item

| item_id | n_failed_entries | categories |
| --- | ---: | --- |
| gsm8k_test_000236 | 303 | {'empty_output': 303} |
| gsm8k_test_000241 | 600 | {'empty_output': 600} |
| gsm8k_test_000255 | 600 | {'empty_output': 600} |

## Top Item-Condition Failure Concentrations

| item_id | condition | n_failed_entries | categories |
| --- | --- | ---: | --- |
| gsm8k_test_000236 | single_round_wrong_consensus | 120 | {'empty_output': 120} |
| gsm8k_test_000236 | single_round_wrong_majority | 120 | {'empty_output': 120} |
| gsm8k_test_000241 | baseline_no_prefix | 120 | {'empty_output': 120} |
| gsm8k_test_000241 | single_round_correct_consensus | 120 | {'empty_output': 120} |
| gsm8k_test_000241 | single_round_correct_majority | 120 | {'empty_output': 120} |
| gsm8k_test_000241 | single_round_wrong_consensus | 120 | {'empty_output': 120} |
| gsm8k_test_000241 | single_round_wrong_majority | 120 | {'empty_output': 120} |
| gsm8k_test_000255 | baseline_no_prefix | 120 | {'empty_output': 120} |
| gsm8k_test_000255 | single_round_correct_consensus | 120 | {'empty_output': 120} |
| gsm8k_test_000255 | single_round_correct_majority | 120 | {'empty_output': 120} |

## Short Examples

| category | example_id | base_item_id | condition | agent_id | round_index |
| --- | --- | --- | --- | ---: | ---: |
| empty_output | gsm8k_test_000236__slot_06_single_round_correct_majority_sample_019 | gsm8k_test_000236 | single_round_correct_majority | 1 | 0 |

## Artifact Policy

Raw model outputs, run directories, generated summaries, and generated result reports are local artifacts by default. Stable conclusions may be promoted into curated documentation, but `runs/*`, raw JSONL, summary JSON, and generated result markdown should not be committed unless explicitly reviewed and intentionally promoted.

No raw model text is included.
