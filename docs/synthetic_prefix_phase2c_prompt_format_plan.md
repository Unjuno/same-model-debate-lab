# Synthetic Prefix Phase 2c Prompt-Format Robustness Plan

## 1. Purpose

Phase 2c tests whether the Phase 2b consensus and extraction-failure patterns are robust to answer-output format.
This is a descriptive robustness check, not a benchmark claim or causal proof.

## 2. Why Phase 2c Exists

Phase 2b suggested that consensus prefixes can shift output distributions, but the observed extraction-failure pattern may depend on prompt formatting.
Phase 2c compares answer-tag, JSON-only, and plain-final formats on the same nine Phase 2b diagnostic items.

## 3. Guardrails

- exploratory
- diagnostic
- repeated stochastic samples
- not independent benchmark items
- prompt-format comparison
- no causal proof
- no statistical-significance claim
- no benchmark-level claim

## 4. Item Source

Phase 2c reuses the nine selected items already present in:

- `data/benchmarks/gsm8k_synthetic_prefix_phase2b_9items.jsonl`

Do not reselect items from the original partial-correct file.
Derive the item list, gold answer, target wrong answer, and source metadata from the Phase 2b dataset.

## 5. Conditions

Use exactly these conditions:

- `baseline_no_prefix`
- `single_round_correct_consensus`
- `single_round_wrong_consensus`

## 6. Prompt Formats

Use exactly these formats:

- `answer_tag`
- `json`
- `plain_final`

## 7. Dataset And Prompt Rules

The builder should strip any existing final-answer instruction from the source question and add exactly one output-format instruction.
The model must not be told that the prefix is synthetic.

Baseline prompt:

```text
Problem:
{original_problem}
Now solve the original problem independently.
{format_instruction}
```

Non-baseline prompt:

```text
Problem:
{original_problem}
Previous debate answers:
Round 0:
- Agent 1: ...
- Agent 2: ...
- Agent 3: ...
Now solve the original problem independently.
The previous answers may be right or wrong.
{format_instruction}
```

## 8. Planned Execution

After the tooling and tests are in place, generate the phase-2c dataset:

```bash
python tools/build_synthetic_prefix_phase2c_dataset.py \
  --phase2b-data data/benchmarks/gsm8k_synthetic_prefix_phase2b_9items.jsonl \
  --out data/benchmarks/gsm8k_synthetic_prefix_phase2c_prompt_formats_9items.jsonl \
  --replicates 20
```

For the current local diagnostic source file, this yields:

- 9 items x 3 conditions x 3 prompt formats x 20 replicates = 1620 rows
- 1620 rows x 3 agents = 4860 outputs

## 9. Out Of Scope

- No smdebate run in this task.
- No mitigation runner changes.
- No Phase 3 implementation.
- No benchmark-level claim.

## 10. Artifact Policy

Raw model outputs, run directories, generated summaries, and generated result reports are local artifacts by default. Stable conclusions may later be promoted into curated documentation, but `runs/*`, raw JSONL, summary JSON, and generated result markdown should not be committed unless explicitly reviewed and intentionally promoted.
