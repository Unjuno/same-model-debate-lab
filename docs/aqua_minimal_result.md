# AQuA-RAT Minimal Calibrated Debate Result

## Purpose

- `synthetic_minimal_90` validated the harness but was too easy.
- The next step was to screen existing benchmark items for `partial_correct` cases.
- A `partial_correct` item is one where 3 same-model independent agents produce mixed correctness: `initial_correct_count` is 1 or 2.
- The core question was whether same-model debate preserves or loses a correct candidate that exists among independent answers.

## Runtime

- model: `qwen3:8b`
- backend: Ollama OpenAI-compatible API
- base URL: `http://localhost:11434/v1`
- agent_count: `3`
- benchmark: `deepmind/aqua_rat` test split
- conditions: independent screening, then `debate_1r`

## Screening Results

| source | total | selected | all_correct | all_wrong | extraction_failed | partial_correct_rate | oracle_at_k |
|---|---:|---:|---:|---:|---:|---:|---:|
| aqua_candidates_100 | 100 | 2 | 85 | 11 | 2 | 0.0200 | 0.8900 |
| aqua_candidates_500_newonly | 254 | 9 | 221 | 22 | 2 | 0.0354 | 0.9134 |
| combined | 354 | 11 | 306 | 33 | 4 | 0.0311 | not directly computed |

## Debate_1r Result

| condition | n | accuracy | oracle_at_k | answer_loss_rate | same_error_agreement_rate | diversity_drop | extraction_failure_rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| debate_1r | 11 | 0.6364 | 0.9091 | 0.3000 | 0.1818 | 0.0909 | 0.0000 |

## Current Conclusion

- On this small calibrated subset, same-model debate can lose a correct answer that exists among the initial independent responses.
- The result is exploratory and limited to `n=11`.
- This is a within-item screening result, not a general proof.

## What This Does Not Show

- It does not establish statistical significance.
- It does not show behavior across arbitrary debate round counts.
- It does not show true within-run round trajectories from `transcript_raw`.
- It does not compare multiple model families.
- It does not rule out benchmark contamination.

## Future Work

- Run a true within-run transcript trajectory analysis on a completed higher-round debate run.
- If needed, compare separate round-count runs as a final-answer sweep, but keep that distinct from transcript-level trajectories.
- Expand beyond `n=11` only if the benchmark selection is intentionally widened.

## Reproduction Outline

```bash
python tools/prepare_aqua_hf_subset.py --out data/benchmarks/aqua_candidates_100.jsonl --split test --seed 0 --limit 100
smdebate --data data/benchmarks/aqua_candidates_100.jsonl --condition independent --out runs/qwen3_8b_aqua_candidates_100_independent_retry1
python tools/filter_by_independent_calibration.py --raw runs/qwen3_8b_aqua_candidates_100_independent_retry1/raw.jsonl --data data/benchmarks/aqua_candidates_100.jsonl --out data/benchmarks/aqua_calibrated_partial_100.jsonl --report runs/qwen3_8b_aqua_candidates_100_independent_retry1/calibration_report.json
smdebate --data data/benchmarks/aqua_calibrated_partial_combined_11.jsonl --condition debate_1r --out runs/qwen3_8b_aqua_calibrated_11_debate_1r
```
