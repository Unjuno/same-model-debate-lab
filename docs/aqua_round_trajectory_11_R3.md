# AQuA-RAT Round Trajectory Follow-Up: 11-Item Debate R3

## Purpose

- This is a small within-subset exploratory follow-up to the earlier `debate_1r` AQuA screening result.
- It compares the completed `debate_3r_full_context` run against the previously documented `debate_1r` result on the same 11-item subset.
- It does not establish statistical significance.

## Runtime

- `n`: 11
- condition: `debate_3r_full_context`
- rounds: 3
- model: `qwen3:8b`
- backend: Ollama OpenAI-compatible API
- base URL: `http://localhost:11434/v1`
- agent count: 3
- dataset: `data/benchmarks/aqua_calibrated_partial_combined_11.jsonl`

## Observed Metrics

| condition | n | accuracy | oracle_at_k | answer_loss_rate | same_error_agreement_rate | diversity_drop | extraction_failure_rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| debate_3r_full_context | 11 | 0.6363636363636364 | 0.9090909090909091 | 0.3 | 0.2727272727272727 | 0.2727272727272727 | 0.015151515151515152 |

## Cautious Comparison To Debate_1r

Relative to the earlier `debate_1r` result on the same 11-item subset:

- accuracy did not improve
- answer_loss_rate did not improve
- same_error_agreement_rate increased
- diversity_drop increased
- extraction failures appeared but remained low

## Interpretation

The strong claim is not supported by this n=11 exploratory follow-up; the result points toward an aggregation/selection problem.

This does not mean longer debate generally worsens performance. It only shows that, for this small within-subset run, increasing rounds did not recover more correct final answers under the current aggregation scheme.

## What Remains Plausible

- Same-model multi-agent sampling can generate correct candidates.
- The current debate and aggregation process may fail to recover them reliably.
- A different aggregation or selection method may improve the final answer without changing the underlying prompts.

## Next Hypotheses

- Final-round majority is failing to recover correct candidates from same-model debate histories.
- All-round aggregation or judge-based selection may improve accuracy and reduce answer loss.
- Timeout handling should avoid turning a transient failure into avoidable empty-answer damage.

## Follow-Up Direction

- Compare final-round majority, all-round majority, timeout carry-forward, and judge-based selection on a larger sample.
- Keep `n=11` labeled as exploratory only.
- Use `n=50` to `n=100` for a more reliable conclusion.

