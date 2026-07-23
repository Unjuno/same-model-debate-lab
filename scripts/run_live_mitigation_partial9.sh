#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate

export SMDEBATE_BASE_URL=http://localhost:11434/v1
export SMDEBATE_API_KEY=ollama
export SMDEBATE_MODEL=qwen3:8b
export SMDEBATE_PROGRESS=1
export SMDEBATE_REQUEST_TIMEOUT_SECONDS=600
export SMDEBATE_MAX_TOKENS=64
export SMDEBATE_CONTINUE_ON_ERROR=1

for repeat in $(seq -w 0 19); do
  for condition in independent full_context_debate answer_hidden_debate numeric_masked_debate commit_then_numeric_masked_debate; do
    out="runs/live_mitigation_partial9_r${repeat}_${condition}"
    if [[ -e "$out" ]]; then
      echo "refusing to overwrite existing artifact: $out" >&2
      exit 1
    fi
    ./.venv/bin/smdebate \
      --data data/benchmarks/gsm8k_test_300_partial_correct.jsonl \
      --condition "$condition" \
      --rounds 3 \
      --out "$out"
  done
done
