# Phase 2c Sharded Execution

## Purpose

This document describes a safe local shard-parallel workflow for the Phase 2c prompt-format robustness run.
It does not change the experiment design or dataset contents.

## Why Sharding

The full Phase 2c dataset is large enough that a single local run may take a long time.
Sharding lets you run a few smaller jobs in parallel, then merge the raw outputs and analyze them with the existing Phase 2c analyzer.

## Memory Caution

Start with 2 parallel jobs. Increase to 4 only if memory pressure remains green and throughput improves. On local Ollama/Apple Silicon, more parallel jobs can be slower if the backend serializes requests or triggers swap.

## Step 1: Split

```bash
python tools/run_phase2c_sharded.py split \
  --data data/benchmarks/gsm8k_synthetic_prefix_phase2c_prompt_formats_9items.jsonl \
  --out-dir data/benchmarks/phase2c_shards \
  --shards 2
```

## Step 2: Run 2 Shards in Parallel

```bash
python tools/run_phase2c_sharded.py plan \
  --shard-dir data/benchmarks/phase2c_shards \
  --run-root runs/phase2c_shards \
  --condition independent \
  --jobs 2
```

If the run was interrupted, rerun the same command with `--resume` to skip shards that already wrote `raw.jsonl`:

```bash
python tools/run_phase2c_sharded.py plan \
  --shard-dir data/benchmarks/phase2c_shards \
  --run-root runs/phase2c_shards \
  --condition independent \
  --jobs 2 \
  --resume
```

For a 4-way restart, change `--jobs 4`. Only the missing shard directories will be relaunched.

## Step 3: Monitor Memory

Watch local memory pressure before increasing the shard count.
If the backend starts swapping or serializing requests heavily, fewer jobs can be faster.

## Step 4: Merge Raw Outputs

```bash
python tools/run_phase2c_sharded.py merge \
  --data data/benchmarks/gsm8k_synthetic_prefix_phase2c_prompt_formats_9items.jsonl \
  --shard-run-root runs/phase2c_shards \
  --out-run runs/qwen3_8b_gsm8k_synthetic_prefix_phase2c_prompt_formats_9items_independent
```

## Step 5: Analyze

```bash
python tools/run_phase2c_sharded.py analyze \
  --data data/benchmarks/gsm8k_synthetic_prefix_phase2c_prompt_formats_9items.jsonl \
  --run-dir runs/qwen3_8b_gsm8k_synthetic_prefix_phase2c_prompt_formats_9items_independent
```

## Artifact Policy

Shard datasets, shard run directories, merged raw outputs, summary JSON, and generated markdown reports are local artifacts by default. Do not commit `runs/*`, raw JSONL, summary JSON, generated reports, or shard files unless explicitly promoted.
