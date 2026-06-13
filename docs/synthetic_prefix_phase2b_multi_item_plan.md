# Synthetic Prefix Phase 2b Multi-Item Plan

## 1. Purpose

Phase 2b extends the single-item synthetic-prefix test to multiple GSM8K diagnostic items.
The goal is descriptive replication across items, not causal proof or benchmark-level evidence.

This is a planning document only.

## 2. Why Phase 2b Exists

Phase 1 and Phase 2 on `gsm8k_test_000234` suggest that answer-only prefixes can move next-agent answer distributions.
However, those experiments were single-item diagnostics.
Phase 2b checks whether the same descriptive pattern appears across multiple GSM8K diagnostic items.

## 3. Guardrails

- exploratory
- diagnostic
- repeated stochastic samples
- not independent benchmark items
- no causal proof
- no statistical-significance claim
- no human-psychology claim

## 4. Conditions

Use exactly five conditions:

| condition | prefix |
| --- | --- |
| `baseline_no_prefix` | none |
| `single_round_correct_consensus` | `gold, gold, gold` |
| `single_round_correct_majority` | `gold, gold, target_wrong_answer` |
| `single_round_wrong_majority` | `target_wrong_answer, target_wrong_answer, gold` |
| `single_round_wrong_consensus` | `target_wrong_answer, target_wrong_answer, target_wrong_answer` |

Each item uses its own gold answer and its own derived target wrong answer.

## 5. Item Selection

Select 20 GSM8K diagnostic items deterministically from `data/benchmarks/gsm8k_test_300_partial_correct.jsonl`.
Prefer a target wrong answer when it can be derived from existing answer fields or existing run traces.
If no target wrong answer can be derived for an item, use a deterministic numeric fallback so the phase-2b dataset can still reach 20 items.

The fallback is a convenience for rapid replication, not a new benchmark claim.

## 6. Dataset And Prompt Rules

The builder should:

- strip any existing final-answer instruction from the source question
- add exactly one final-answer instruction
- omit previous-debate text for `baseline_no_prefix`
- include previous-debate text for non-baseline conditions
- keep condition order deterministic
- record the synthetic prefix only in metadata

Baseline prompt:

```text
Problem: {original_problem}

Now solve the original problem independently.
Return only the final answer inside <answer>...</answer>.
```

Non-baseline prompt:

```text
Problem: {original_problem}

Previous debate answers:
Round 0:
- Agent 1: ...
- Agent 2: ...
- Agent 3: ...

Now solve the original problem independently.
The previous answers may be right or wrong.
Return only the final answer inside <answer>...</answer>.
```

## 7. Metadata

Each row should record:

- `base_item_id`
- `condition`
- `replicate_index`
- `gold`
- `target_wrong_answer`
- `synthetic_prefix`
- `phase`
- `condition_family`
- `context_rounds_included`
- `context_answers_by_round`
- `prefix_answer_counts`
- `latest_round_answers`
- `latest_round_majority`
- `source_metadata`

## 8. Analysis Goals

The analyzer should aggregate:

- by item and condition
- across all selected items by condition

It should compute item-level deltas against each item’s baseline and summarize the distribution of those deltas across items.

## 9. Qualitative Labels

Use descriptive labels only:

- `shared_prior_common`
- `correct_consensus_anchor_common`
- `wrong_consensus_anchor_common`
- `wrong_consensus_stronger_than_wrong_majority_common`
- `majority_effect_weaker_than_consensus`
- `inconclusive`

These labels describe the data pattern only. They do not prove mechanism.

## 10. Planned Execution

After the tooling and tests are in place, generate the phase-2b dataset:

```bash
python tools/build_synthetic_prefix_phase2b_dataset.py \
  --data data/benchmarks/gsm8k_test_300_partial_correct.jsonl \
  --out data/benchmarks/gsm8k_synthetic_prefix_phase2b_20items.jsonl \
  --items 20 \
  --replicates 20
```

Then verify the row counts and prompt strings before any model run.

## 11. Out Of Scope

- No smdebate run in this task.
- No mitigation runner changes.
- No Phase 3 implementation.
- No benchmark-level claim.
