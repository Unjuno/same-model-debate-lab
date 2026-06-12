# Synthetic Prefix Phase 2 Majority-Recency Plan

## 1. Purpose

Phase 1 suggested that synthetic prefixes can move the next answer toward the wrong attractor, but it did not separate majority, frequency, order, and unanimity effects.
This Phase 2 plan defines a compact diagnostic follow-up for `gsm8k_test_000234` that separates those factors using repeated stochastic prompt samples.

This is a planning document only. It does not report results and it does not claim causal proof or statistical significance.

## 2. Why Phase 2 Exists

Phase 1 conditions mixed several properties at once:

- latest visible round
- total prefix frequency
- chronological order
- unanimity versus non-unanimity

Phase 2 narrows the test to seven small conditions so we can compare:

- single-round consensus versus majority
- majority versus consensus
- trajectory order versus reversed order with the same prefix counts

## 3. Important Interpretation Guardrails

- This is a single-item diagnostic experiment.
- The 20 rows per condition are repeated stochastic samples from the same prompt template, not independent benchmark items.
- The 420 outputs from the planned independent run are repeated samples, not 420 independent benchmark items.
- Do not treat the output counts as benchmark-level evidence.
- Do not infer causality from a descriptive shift in answer rates.

## 4. Phase 2 Conditions

Use exactly these seven conditions:

| condition | prefix | family |
| --- | --- | --- |
| `baseline_no_prefix` | none | baseline |
| `single_round_correct_consensus` | round 0: `21`, `21`, `21` | single_round |
| `single_round_correct_majority` | round 0: `21`, `21`, `14` | single_round |
| `single_round_wrong_majority` | round 0: `14`, `14`, `21` | single_round |
| `single_round_wrong_consensus` | round 0: `14`, `14`, `14` | single_round |
| `trajectory_forward` | rounds 0-2 in forward order | trajectory |
| `trajectory_reversed` | rounds 0-2 in reversed order | trajectory |

The dataset should contain 20 replicates per condition.

## 5. Data And Prompt Rules

The builder should:

- load the target item from `data/benchmarks/gsm8k_test_300_partial_correct.jsonl`
- strip any existing final-answer instruction from the original question
- add exactly one final-answer instruction
- keep the condition order deterministic
- record the synthetic prefix only in metadata, not in the prompt

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

## 6. Phase 2 Metadata

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

For the trajectory conditions, the forward and reversed prefixes should have identical prefix counts but different order.

## 7. Analysis Goals

The Phase 2 analyzer should compute condition-level answer distributions and these planned comparisons:

- `single_round_correct_consensus_vs_baseline`
- `single_round_wrong_majority_vs_baseline`
- `single_round_wrong_consensus_vs_wrong_majority`
- `single_round_correct_majority_vs_wrong_majority`
- `trajectory_forward_vs_baseline`
- `trajectory_reversed_vs_baseline`
- `trajectory_forward_vs_reversed`

The goal is descriptive disentanglement, not proof.

## 8. Qualitative Labels

Use only descriptive labels:

- `shared_prior_possible`
- `correct_consensus_anchor_consistent`
- `wrong_majority_anchor_consistent`
- `wrong_consensus_stronger_than_wrong_majority`
- `recency_order_consistent`
- `frequency_without_recency_insufficient`
- `inconclusive`

These labels should be interpreted cautiously. They are consistent with a hypothesis, not evidence of mechanism by themselves.

## 9. Planned Execution

After the tooling and tests are in place, generate the Phase 2 dataset:

```bash
python tools/build_synthetic_prefix_phase2_dataset.py \
  --data data/benchmarks/gsm8k_test_300_partial_correct.jsonl \
  --out data/benchmarks/gsm8k_000234_synthetic_prefix_phase2.jsonl \
  --item-id gsm8k_test_000234 \
  --replicates 20
```

Then verify the prompt contents and row counts before any model run.

## 10. Out Of Scope

- No Phase 3 implementation.
- No rationale contamination conditions.
- No mitigation runner changes.
- No debate rerun in this task.
- No interpretation as benchmark-level evidence.
