# AQuA-RAT Minimal Calibrated Debate Result

## Purpose

- `synthetic_minimal_90` validated the harness but was too easy.
- The next goal was to screen existing benchmark items for `partial_correct` cases.
- A `partial_correct` item is one where 3 same-model independent agents produce mixed correctness: `initial_correct_count` is 1 or 2.

## Runtime setup

- model: `qwen3:8b`
- backend: Ollama OpenAI-compatible API
- base URL: `http://localhost:11434/v1`
- agent_count: `3`
- benchmark: `deepmind/aqua_rat` test split
- conditions: independent screening, then `debate_1r`
- local hardware/runtime was a MacBook Pro; exact hardware details not fully recorded.
- local power state affected runtime; low battery appeared to slow inference.

## Screening results

| source | total | selected | all_correct | all_wrong | extraction_failed | partial_correct_rate | oracle_at_k |
|---|---:|---:|---:|---:|---:|---:|---:|
| aqua_candidates_100 | 100 | 2 | 85 | 11 | 2 | 0.0200 | 0.8900 |
| aqua_candidates_500_newonly | 254 | 9 | 221 | 22 | 2 | 0.0354 | 0.9134 |
| combined | 354 | 11 | 306 | 33 | 4 | 0.0311 | not directly computed |

## Debate result

| condition | n | accuracy | oracle_at_k | answer_loss_rate | same_error_agreement_rate | diversity_drop | extraction_failure_rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| debate_1r | 11 | 0.6364 | 0.9091 | 0.3000 | 0.1818 | 0.0909 | 0.0000 |

## Interpretation

- Operationally, the minimal calibrated experiment succeeded.
- AQuA-RAT produced 11 `partial_correct` items after screening 354 candidates.
- On these 11 items, `debate_1r` showed `answer_loss_rate = 0.3`.
- This is an initial signal that same-model debate can lose correct candidates on calibrated boundary items.
- The result is preliminary and exploratory.

## Caveats

- `n=11` is small.
- No statistical significance claim.
- Public benchmark contamination is possible.
- AQuA-RAT was mostly easy for `qwen3:8b`.
- The second candidate file name says 500, but actual generated rows were 254.
- Local runtime speed depended on power state.
- No `debate_3r` result is included.
- No multi-model comparison is included.

## Reproduction outline

```bash
python tools/prepare_aqua_hf_subset.py --out data/benchmarks/aqua_candidates_100.jsonl --split test --seed 0 --limit 100
smdebate --data data/benchmarks/aqua_candidates_100.jsonl --condition independent --out runs/qwen3_8b_aqua_candidates_100_independent_retry1
python tools/filter_by_independent_calibration.py --raw runs/qwen3_8b_aqua_candidates_100_independent_retry1/raw.jsonl --data data/benchmarks/aqua_candidates_100.jsonl --out data/benchmarks/aqua_calibrated_partial_100.jsonl --report runs/qwen3_8b_aqua_candidates_100_independent_retry1/calibration_report.json
smdebate --data data/benchmarks/aqua_calibrated_partial_100.jsonl --condition debate_1r --out runs/qwen3_8b_aqua_calibrated_11_debate_1r
```
