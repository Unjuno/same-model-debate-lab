# AQuA Follow-Up Run Plan

## Purpose
Prepare a second small calibrated AQuA follow-up subset to test whether the trajectory-mixing and flip-dynamics pattern reproduces outside the original 11-item subset.

## Dataset
- `data/benchmarks/aqua_calibrated_partial_followup_15.jsonl`
- Selected item count: `2`
- Reason: only 2 fresh partial-correct AQuA items were available from existing independent screening runs after excluding the original 11-item subset.

## Excluded Original 11 Item IDs
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

## Selected Follow-Up Items
- `aqua_test_1_000106`
- `aqua_test_1_000138`

## Manual Inference Command
Do not run this from Codex. Run it manually after the subset is ready.

```bash
export SMDEBATE_PROGRESS=1
export SMDEBATE_REQUEST_TIMEOUT_SECONDS=600
export SMDEBATE_MAX_TOKENS=64
export SMDEBATE_CONTINUE_ON_ERROR=1
rm -rf runs/qwen3_8b_aqua_calibrated_partial_followup_15_debate_R3
smdebate \
  --data data/benchmarks/aqua_calibrated_partial_followup_15.jsonl \
  --condition debate_3r_full_context \
  --rounds 3 \
  --out runs/qwen3_8b_aqua_calibrated_partial_followup_15_debate_R3
```

## Post-Hoc Commands
Run these only after the raw output exists.

```bash
python tools/analyze_aggregation_rules.py \
  --data data/benchmarks/aqua_calibrated_partial_followup_15.jsonl \
  --raw runs/qwen3_8b_aqua_calibrated_partial_followup_15_debate_R3/raw.jsonl \
  --out-json runs/qwen3_8b_aqua_calibrated_partial_followup_15_debate_R3/aggregation_summary.json \
  --out-md docs/aqua_followup15_aggregation_rules_R3.md
```

```bash
python tools/analyze_flip_dynamics.py \
  --data data/benchmarks/aqua_calibrated_partial_followup_15.jsonl \
  --raw runs/qwen3_8b_aqua_calibrated_partial_followup_15_debate_R3/raw.jsonl \
  --out-json runs/qwen3_8b_aqua_calibrated_partial_followup_15_debate_R3/flip_dynamics_summary.json \
  --out-md docs/aqua_followup15_flip_dynamics_R3.md
```

## Expected Output Paths
- `runs/qwen3_8b_aqua_calibrated_partial_followup_15_debate_R3/raw.jsonl`
- `runs/qwen3_8b_aqua_calibrated_partial_followup_15_debate_R3/summary.json`
- `runs/qwen3_8b_aqua_calibrated_partial_followup_15_debate_R3/aggregation_summary.json`
- `runs/qwen3_8b_aqua_calibrated_partial_followup_15_debate_R3/flip_dynamics_summary.json`
- `docs/aqua_followup15_aggregation_rules_R3.md`
- `docs/aqua_followup15_flip_dynamics_R3.md`

## Do Not Commit
- `runs/*`
- raw outputs
- generated JSON summaries
- temporary reports

## Report Back After the Manual Run
- `summary.json`
- `aggregation_summary.json`
- `flip_dynamics_summary.json`
- item-level examples of any `initial correct majority -> final wrong majority` flips
- item-level examples of any `wrong majority -> correct majority` recoveries

## Follow-Up Note
The resulting available subset contained only two items, and both were unanimously correct from the initial round.
A new screening pass is needed before this can serve as a meaningful follow-up for trajectory-mixing analysis.
