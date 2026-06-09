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

## Item-Level Trajectory

Compact round-level summary derived from the existing run artifacts. It excludes raw text, prompts, and full transcripts.

| item_id | gold | majority_answer_by_round | correctness_by_round | flip_count | category |
|---|---|---|---|---:|---|
| `aqua_test_0_000016` | `A` | `{"0":"A","1":"A","2":"A","3":"A"}` | `{"0":true,"1":true,"2":true,"3":true}` | 0 | `preserved_correct` |
| `aqua_test_0_000184` | `D` | `{"0":"D","1":"D","2":"D","3":"D"}` | `{"0":true,"1":true,"2":true,"3":true}` | 0 | `preserved_correct` |
| `aqua_test_1_000016` | `A` | `{"0":"A","1":"A","2":"A","3":"A"}` | `{"0":true,"1":true,"2":true,"3":true}` | 0 | `preserved_correct` |
| `aqua_test_1_000059` | `C` | `{"0":"C","1":"C","2":"C","3":"C"}` | `{"0":true,"1":true,"2":true,"3":true}` | 0 | `preserved_correct` |
| `aqua_test_1_000067` | `B` | `{"0":"B","1":"B","2":"B","3":"C"}` | `{"0":true,"1":true,"2":true,"3":false}` | 1 | `deterioration` |
| `aqua_test_1_000069` | `C` | `{"0":"E","1":"E","2":"E","3":"E"}` | `{"0":false,"1":false,"2":false,"3":false}` | 0 | `persistent_error` |
| `aqua_test_1_000117` | `C` | `{"0":"C","1":"C","2":"C","3":"C"}` | `{"0":true,"1":true,"2":true,"3":true}` | 0 | `preserved_correct` |
| `aqua_test_1_000172` | `E` | `{"0":"E","1":"E","2":"E","3":"E"}` | `{"0":true,"1":true,"2":true,"3":true}` | 0 | `preserved_correct` |
| `aqua_test_1_000188` | `D` | `{"0":"C","1":"C","2":"C","3":"C"}` | `{"0":false,"1":false,"2":false,"3":false}` | 0 | `persistent_error` |
| `aqua_test_1_000210` | `E` | `{"0":"D","1":"D","2":"D","3":"D"}` | `{"0":false,"1":false,"2":false,"3":false}` | 0 | `persistent_error` |
| `aqua_test_1_000237` | `B` | `{"0":"B","1":"B","2":"B","3":"B"}` | `{"0":true,"1":true,"2":true,"3":true}` | 0 | `preserved_correct` |

## Cautious Comparison To Debate_1r

Relative to the earlier `debate_1r` result on the same 11-item subset:

- accuracy did not improve
- answer_loss_rate did not improve
- same_error_agreement_rate increased
- diversity_drop increased
- extraction failures appeared but remained low

## Interpretation

The strong claim is not supported by this n=11 exploratory follow-up.

The result raises the possibility that the current final-round majority aggregation may not fully use correct candidates or useful information present in the debate history.

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
- Before scaling to a larger sample, compare aggregation rules on the existing 11-item subset.
