# Live Debate Mitigation Runbook

## Purpose

This runbook covers the first live mitigation smoke cycle for same-model debate.
The goal is to verify prompt construction, raw-history preservation, and analysis plumbing before any larger run.

## Current Status

The smoke path is implemented and verified on a small sample.
The full partial9 live run is intentionally deferred until the backend and timing budget are ready for a longer pass.
Do not treat the current smoke as a benchmark result.

## Scope

Use the following five conditions first:

- `independent`
- `full_context_debate`
- `answer_hidden_debate`
- `numeric_masked_debate`
- `commit_then_numeric_masked_debate`

`answer_hidden_numeric_masked_debate` can be treated as an optional later control.

## Smoke Dataset

Use a small subset of clean original GSM8K problem text.

Do not use synthetic-prefix Phase 3c prompts for live mitigation evaluation. They already contain prior exposure structure and would confound the live-debate signal.

Suggested command:

```bash
./.venv/bin/python tools/build_live_mitigation_dataset.py \
  --data data/benchmarks/gsm8k_test_300_partial_correct.jsonl \
  --limit 2 \
  --out /tmp/live_mitigation_smoke.jsonl
```

This is only a convenience subset builder. It does not alter the live runner data model.

## Smoke Run

Suggested settings:

- 1 to 2 items
- 5 conditions
- 1 to 2 repeats
- 3 agents
- 2 or 3 rounds

Suggested shell pattern:

```bash
for condition in independent full_context_debate answer_hidden_debate numeric_masked_debate commit_then_numeric_masked_debate; do
  ./.venv/bin/smdebate \
    --data /tmp/live_mitigation_smoke.jsonl \
    --condition "$condition" \
    --rounds 2 \
    --out "runs/live_mitigation_smoke_${condition}" \
    > "runs/live_mitigation_smoke_${condition}.log" 2>&1
done
```

## What to Inspect

Do not start with accuracy. First inspect:

- full-context visibility in `full_context_debate`
- hidden final answers in `answer_hidden_debate`
- masked peer numbers in `numeric_masked_debate`
- unmodified original problem text
- unmodified raw history fields
- preserved round-0 initial answers

Example checks:

```bash
python - <<'PY'
import json
from pathlib import Path

row = json.loads(Path("runs/live_mitigation_smoke_numeric_masked_debate/raw.jsonl").read_text().splitlines()[0])
print(row["initial_raw"][0]["raw_text"])
print(row["transcript_raw"][0]["raw_text"])
PY
```

## Analyzer

Run the live mitigation analyzer after the smoke run:

```bash
cat runs/live_mitigation_smoke_*/raw.jsonl > runs/live_mitigation_smoke_all_raw.jsonl

./.venv/bin/python tools/analyze_live_mitigation.py \
  --data /tmp/live_mitigation_smoke.jsonl \
  --raw runs/live_mitigation_smoke_all_raw.jsonl \
  --out-json runs/live_mitigation_smoke_report.json \
  --out-md docs/live_mitigation_smoke_report.md
```

For smoke validation, inspect:

- `initial_any_correct_rate`
- `final_majority_correct_rate`
- `correct_to_wrong_collapse_rate`
- `correct_initial_lost_rate`
- `target_wrong_convergence_rate`

If `target_wrong` is unavailable in the live data, that metric should be treated as not applicable.

## Next Step After Smoke

If prompt/history behavior is correct, scale to the partial9 live run:

- 9 items
- 5 conditions
- 20 repeats
- 3 agents
- 3 rounds

Only after that should a cautious result summary be promoted into docs.

## Artifact Policy

Do not commit:

- `runs/*`
- raw JSONL
- logs
- generated summary JSON
- generated smoke reports

Only the tooling, runbook, and eventual curated documentation should be committed.
