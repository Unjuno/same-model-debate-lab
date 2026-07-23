# AQuA Follow-Up Screen 200 Run Plan

## Purpose

Prepare a larger independent screening pass for AQuA so we can find a fresh set of partial-correct items for a meaningful follow-up subset.

## Candidate File

- `data/benchmarks/aqua_candidates_followup_screen_200.jsonl`
- Selected candidate count: `200`
- Source: AQuA test items from the local benchmark pool, excluding the original 11-item calibrated subset and the 2-item sanity-check subset.

## Excluded Existing Subset IDs

- `aqua_test_0_000016`
- `aqua_test_0_000184`
- `aqua_test_1_000016`
- `aqua_test_1_000059`
- `aqua_test_1_000067`
- `aqua_test_1_000069`
- `aqua_test_1_000117`
- `aqua_test_1_000172`
- `aqua_test_1_000188`
- `aqua_test_1_000210`
- `aqua_test_1_000237`
- `aqua_test_1_000106`
- `aqua_test_1_000138`

## Manual Independent Screening Command

Do not run this from Codex. Run it manually after the subset is ready.

```bash
export SMDEBATE_PROGRESS=1
export SMDEBATE_REQUEST_TIMEOUT_SECONDS=600
export SMDEBATE_MAX_TOKENS=64
export SMDEBATE_CONTINUE_ON_ERROR=1

# Do not delete an existing run. Choose a new output directory or resume it.
test ! -e runs/qwen3_8b_aqua_followup_screen_200_independent || {
  echo "Existing run preserved; choose a new directory or use --resume." >&2
  exit 1
}

smdebate \
  --data data/benchmarks/aqua_candidates_followup_screen_200.jsonl \
  --condition independent \
  --out runs/qwen3_8b_aqua_followup_screen_200_independent
```

## Partial-Correct Filtering Command

Use the local selector to extract benchmark rows where at least one agent is correct, not all agents are correct, and extraction failures are excluded if possible.

```bash
python tools/select_partial_correct_aqua.py \
  --data data/benchmarks/aqua_candidates_followup_screen_200.jsonl \
  --raw runs/qwen3_8b_aqua_followup_screen_200_independent/raw.jsonl \
  --exclude data/benchmarks/aqua_calibrated_partial_combined_11.jsonl \
  --exclude data/benchmarks/aqua_calibrated_partial_followup_15.jsonl \
  --out data/benchmarks/aqua_calibrated_partial_followup_screened_15.jsonl \
  --limit 15
```

## Expected Output Paths

- `runs/qwen3_8b_aqua_followup_screen_200_independent/raw.jsonl`
- `runs/qwen3_8b_aqua_followup_screen_200_independent/summary.json`
- `data/benchmarks/aqua_calibrated_partial_followup_screened_15.jsonl`

## Do Not Commit

- `runs/*`
- raw outputs
- generated summaries under `runs/`
- `reports/*`
- `.venv/*`
- `egg-info` generated changes
- result docs for runs that have not happened

## What To Report Back After Manual Screening

- final screening `summary.json`
- how many partial-correct items were selected
- the selected item IDs
- whether any extraction failures occurred
- whether the resulting screened subset reaches 15 items
