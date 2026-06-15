# Extraction Failure Audit Plan

## Purpose

Phase 2b extraction failures are a major confound in the current failure-aware analysis. This audit classifies failed raw outputs so we can tell whether they are:

- truly empty or missing
- unwrapped numeric answers
- wrapped but non-numeric answers
- noisy tool or formatting spillover

The audit is exploratory and descriptive. It does not claim causality, benchmark-level conclusions, or human social psychology.

## Target Raw Output

The current audit target is the existing Phase 2b raw file:

`runs/qwen3_8b_gsm8k_synthetic_prefix_phase2b_9items_independent/raw.jsonl`

## Categories

- `missing_answer_tag`
- `empty_output`
- `non_numeric_answer`
- `contains_numeric_but_unwrapped`
- `multiple_candidate_numbers`
- `tool_or_format_noise`
- `unknown`

## Outputs

The audit script writes two local artifacts by default:

- `runs/qwen3_8b_gsm8k_synthetic_prefix_phase2b_9items_independent/extraction_failure_audit.json`
- `docs/gsm8k_synthetic_prefix_phase2b_failure_audit.md`

These are local artifacts unless they are explicitly reviewed and promoted.

## Artifact Policy

Raw model outputs, run directories, generated summaries, and generated result reports are local artifacts by default. Stable conclusions may be promoted into curated documentation, but `runs/*`, raw JSONL, summary JSON, and generated result markdown should not be committed unless explicitly reviewed and intentionally promoted.

## Next Use

Read the summary counts first, then inspect a few examples per category. If the audit shows many wrapped but non-numeric or unwrapped numeric outputs, the extraction-failure confound is partly format-related rather than pure non-response.
