# GSM8K Screening Run Plan

## Purpose

Prepare a new GSM8K benchmark path for independent screening so we can collect more partial-correct items beyond AQuA.

## Dataset Preparation

Prepare the benchmark JSONL files with:

```bash
python tools/prepare_gsm8k_benchmark.py \
  --out-dir data/benchmarks \
  --limits 100 300
```

## Candidate Files

- `data/benchmarks/gsm8k_test_100.jsonl` - 100 items
- `data/benchmarks/gsm8k_test_300.jsonl` - 300 items

## Manual Independent Screening

Do not run this from Codex. Run it manually after the dataset is prepared.

```bash
export SMDEBATE_PROGRESS=1
export SMDEBATE_REQUEST_TIMEOUT_SECONDS=600
export SMDEBATE_MAX_TOKENS=128
export SMDEBATE_CONTINUE_ON_ERROR=1

# Do not delete an existing run. Choose a new output directory or resume it.
test ! -e runs/qwen3_8b_gsm8k_test_300_independent || {
  echo "Existing run preserved; choose a new directory or use --resume." >&2
  exit 1
}

smdebate \
  --data data/benchmarks/gsm8k_test_300.jsonl \
  --condition independent \
  --out runs/qwen3_8b_gsm8k_test_300_independent
```

## Partial-Correct Extraction Plan

Use the generalized selector to extract benchmark rows where:
- at least one agent is correct
- not all agents are correct
- no extraction failures if possible

```bash
python tools/select_partial_correct_items.py \
  --data data/benchmarks/gsm8k_test_300.jsonl \
  --raw runs/qwen3_8b_gsm8k_test_300_independent/raw.jsonl \
  --out data/benchmarks/gsm8k_calibrated_partial_300.jsonl \
  --limit 15
```

## Expected Output Paths

- `runs/qwen3_8b_gsm8k_test_300_independent/raw.jsonl`
- `runs/qwen3_8b_gsm8k_test_300_independent/summary.json`
- `data/benchmarks/gsm8k_calibrated_partial_300.jsonl`

## Do Not Commit

- `runs/*`
- raw outputs
- summary JSON
- reports/*
- generated run notes

## Interpretation Caveat

GSM8K is a new benchmark path. Compare its screening results to AQuA cautiously because the item distribution, answer format, and difficulty profile differ.

## Report Back After Manual Screening

- the final `summary.json`
- how many partial-correct items were selected
- the selected item IDs
- whether any extraction failures occurred
- whether the 15-item target was reached
