# Phase 2b Extraction Failure Audit Plan

## 1. Purpose

Phase 2b extraction failures are a major confound for interpreting answer shifts.
This audit classifies parser-visible failures to separate likely empty or malformed outputs from cases where a numeric answer may exist but was not wrapped as expected.

This is a planning document only.

## 2. Audit Scope

The audit targets the existing Phase 2b raw output:

- `runs/qwen3_8b_gsm8k_synthetic_prefix_phase2b_9items_independent/raw.jsonl`

The audit reads local raw outputs and classifies failed responses using only parser-visible fields.
It does not rerun model inference.

## 3. Failure Categories

Use exactly these categories:

- `empty_output`
- `missing_answer_tag`
- `contains_numeric_but_unwrapped`
- `multiple_candidate_numbers`
- `non_numeric_answer`
- `tool_or_format_noise`
- `unknown`

## 4. Interpretation Guardrails

- exploratory diagnostic
- based on parser-visible raw response fields
- does not prove model intent
- does not prove causal mechanism
- not benchmark-level evidence
- repeated stochastic samples are not independent benchmark items

## 5. Expected Outputs

The audit may write local artifacts such as:

- `runs/qwen3_8b_gsm8k_synthetic_prefix_phase2b_9items_independent/extraction_failure_audit.json`
- `docs/gsm8k_synthetic_prefix_phase2b_failure_audit.md`

These remain local artifacts by default and should not be committed unless explicitly promoted.

## 6. Planned Command

```bash
python tools/audit_extraction_failures_phase2b.py \
  --data data/benchmarks/gsm8k_synthetic_prefix_phase2b_9items.jsonl \
  --raw runs/qwen3_8b_gsm8k_synthetic_prefix_phase2b_9items_independent/raw.jsonl \
  --out-json runs/qwen3_8b_gsm8k_synthetic_prefix_phase2b_9items_independent/extraction_failure_audit.json \
  --out-md docs/gsm8k_synthetic_prefix_phase2b_failure_audit.md
```

## 7. Artifact Policy

Raw model outputs, run directories, generated summaries, and generated result reports are local artifacts by default. Stable conclusions may later be promoted into curated documentation, but `runs/*`, raw JSONL, summary JSON, and generated result markdown should not be committed unless explicitly reviewed and intentionally promoted.
