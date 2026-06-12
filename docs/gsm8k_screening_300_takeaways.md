# GSM8K Screening 300 Takeaways

## Run Summary

Independent GSM8K screening completed on `data/benchmarks/gsm8k_test_300.jsonl` with `runs/qwen3_8b_gsm8k_test_300_independent/raw.jsonl`.

Observed metrics:

| n | accuracy | oracle_at_k | answer_loss_rate | same_error_agreement_rate | diversity_drop | extraction_failure_rate |
| --- | --- | --- | --- | --- | --- | --- |
| 300 | 0.9533333333333334 | 0.97 | 0.01718213058419244 | 0.02 | 0.0 | 0.0 |

## Selector Result

The generic partial-correct selector now works for both multiple-choice and numeric answers.

Command:

```bash
python tools/select_partial_correct_items.py \
  --data data/benchmarks/gsm8k_test_300.jsonl \
  --raw runs/qwen3_8b_gsm8k_test_300_independent/raw.jsonl \
  --out data/benchmarks/gsm8k_test_300_partial_correct.jsonl \
  --limit 20
```

Summary:

```json
{"candidates": 9, "excluded": 0, "input_items": 300, "raw_items_seen": 300, "selected": 9}
```

Selected ids:

- `gsm8k_test_000012`
- `gsm8k_test_000089`
- `gsm8k_test_000093`
- `gsm8k_test_000147`
- `gsm8k_test_000187`
- `gsm8k_test_000234`
- `gsm8k_test_000236`
- `gsm8k_test_000241`
- `gsm8k_test_000255`

## Notes

- Numeric normalization treats comma formatting and exact decimal equivalents as equal, so `29`, `29.00`, and `1,000` vs `1000` compare as the same answer.
- The selector preserves the original benchmark JSONL row when writing the output file.
- Extraction failures in `initial_raw` exclude the item from selection.
