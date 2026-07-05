from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze_synthetic_prefix_phase2c import (  # noqa: E402
    analyze_synthetic_prefix_phase2c,
    write_json,
    write_markdown,
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def _shard_run_dir(run_root: Path, job_index: int) -> Path:
    return run_root / f"shard_{job_index}"


def _shard_is_complete(shard_run_dir: Path) -> bool:
    raw_path = shard_run_dir / "raw.jsonl"
    return raw_path.exists() and raw_path.stat().st_size > 0


def split_dataset(*, data_path: Path, out_dir: Path, shards: int) -> dict[str, Any]:
    if shards <= 0:
        raise ValueError("shards must be positive")
    rows = load_jsonl(data_path)
    shard_rows: list[list[dict[str, Any]]] = [[] for _ in range(shards)]
    for index, row in enumerate(rows):
        shard_rows[index % shards].append(row)
    out_dir.mkdir(parents=True, exist_ok=True)
    shard_counts: dict[str, int] = {}
    for shard_index, shard in enumerate(shard_rows):
        shard_path = out_dir / f"phase2c_shard_{shard_index}.jsonl"
        write_jsonl(shard_path, shard)
        shard_counts[shard_path.name] = len(shard)
    return {
        "mode": "split",
        "rows": len(rows),
        "shards": shards,
        "shard_counts": shard_counts,
    }


def plan_commands(*, shard_dir: Path, run_root: Path, condition: str, jobs: int) -> str:
    if jobs <= 0:
        raise ValueError("jobs must be positive")
    lines = ["mkdir -p " + str(run_root)]
    for job_index in range(jobs):
        shard_path = shard_dir / f"phase2c_shard_{job_index}.jsonl"
        shard_run_dir = run_root / f"shard_{job_index}"
        lines.extend(
            [
                "SMDEBATE_PROGRESS=1 \\",
                "SMDEBATE_REQUEST_TIMEOUT_SECONDS=600 \\",
                "SMDEBATE_MAX_TOKENS=64 \\",
                "SMDEBATE_CONTINUE_ON_ERROR=1 \\",
                f"smdebate --data {shard_path} --condition {condition} --out {shard_run_dir} &",
                f"PID{job_index}=$!",
            ]
        )
    for job_index in range(jobs):
        lines.append(f"wait $PID{job_index}")
    lines.append("")
    lines.append("Start with 2 jobs. Increase to 4 only if memory pressure remains green and throughput improves.")
    lines.append("On local Ollama/Apple Silicon, more parallel jobs can be slower if the backend serializes requests or triggers swap.")
    return "\n".join(lines)


def resume_commands(*, shard_dir: Path, run_root: Path, condition: str, jobs: int) -> str:
    if jobs <= 0:
        raise ValueError("jobs must be positive")
    lines = ["mkdir -p " + str(run_root)]
    active_jobs = 0
    for job_index in range(jobs):
        shard_path = shard_dir / f"phase2c_shard_{job_index}.jsonl"
        shard_run_dir = _shard_run_dir(run_root, job_index)
        if _shard_is_complete(shard_run_dir):
            lines.append(f"echo 'Skipping completed shard {job_index}: {shard_run_dir}/raw.jsonl'")
            continue
        lines.extend(
            [
                "SMDEBATE_PROGRESS=1 \\",
                "SMDEBATE_REQUEST_TIMEOUT_SECONDS=600 \\",
                "SMDEBATE_MAX_TOKENS=64 \\",
                "SMDEBATE_CONTINUE_ON_ERROR=1 \\",
                f"smdebate --data {shard_path} --condition {condition} --out {shard_run_dir} &",
                f"PID{job_index}=$!",
            ]
        )
        active_jobs += 1
    for job_index in range(jobs):
        shard_run_dir = _shard_run_dir(run_root, job_index)
        if not _shard_is_complete(shard_run_dir):
            lines.append(f"wait $PID{job_index}")
    if active_jobs == 0:
        lines.append("echo 'All requested shards are already complete.'")
    return "\n".join(lines)


def merge_raw_outputs(*, data_path: Path, shard_run_root: Path, out_run: Path, allow_missing: bool = False) -> dict[str, Any]:
    dataset_rows = load_jsonl(data_path)
    expected_ids = [str(row.get("id", "")) for row in dataset_rows if str(row.get("id", ""))]
    expected_set = set(expected_ids)
    raw_rows: list[dict[str, Any]] = []
    for shard_dir in sorted(shard_run_root.glob("shard_*")):
        raw_path = shard_dir / "raw.jsonl"
        if raw_path.exists():
            raw_rows.extend(load_jsonl(raw_path))
    raw_ids = [str(row.get("id", "")) for row in raw_rows if str(row.get("id", ""))]
    raw_set = set(raw_ids)
    missing_ids = sorted(expected_set - raw_set)
    duplicate_ids = sorted([row_id for row_id, count in Counter(raw_ids).items() if count > 1])
    out_run.mkdir(parents=True, exist_ok=True)
    out_raw = out_run / "raw.jsonl"
    write_jsonl(out_raw, raw_rows)
    if missing_ids and not allow_missing:
        raise ValueError(f"missing dataset ids: {missing_ids}")
    return {
        "mode": "merge",
        "dataset_rows": len(dataset_rows),
        "raw_rows": len(raw_rows),
        "missing_ids": missing_ids,
        "duplicate_ids": duplicate_ids,
        "out_raw": str(out_raw),
    }


def analyze_run(*, data_path: Path, run_dir: Path) -> dict[str, Any]:
    raw_path = run_dir / "raw.jsonl"
    out_json = run_dir / "synthetic_prefix_phase2c_summary.json"
    out_md = ROOT / "docs" / "gsm8k_synthetic_prefix_phase2c_prompt_formats_9items_results.md"
    report = analyze_synthetic_prefix_phase2c(data_path=data_path, raw_path=raw_path)
    write_json(out_json, report)
    write_markdown(report, out_md)
    return {
        "mode": "analyze",
        "out_json": str(out_json),
        "out_md": str(out_md),
        "summary": report["summary"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Shard-parallel Phase 2c execution helper.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    split_parser = subparsers.add_parser("split")
    split_parser.add_argument("--data", required=True)
    split_parser.add_argument("--out-dir", required=True)
    split_parser.add_argument("--shards", type=int, required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--shard-dir", required=True)
    plan_parser.add_argument("--run-root", required=True)
    plan_parser.add_argument("--condition", required=True)
    plan_parser.add_argument("--jobs", type=int, required=True)
    plan_parser.add_argument("--resume", action="store_true")

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--data", required=True)
    merge_parser.add_argument("--shard-run-root", required=True)
    merge_parser.add_argument("--out-run", required=True)
    merge_parser.add_argument("--allow-missing", action="store_true")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--data", required=True)
    analyze_parser.add_argument("--run-dir", required=True)

    args = parser.parse_args()

    if args.mode == "split":
        payload = split_dataset(data_path=Path(args.data), out_dir=Path(args.out_dir), shards=args.shards)
    elif args.mode == "plan":
        planner = resume_commands if args.resume else plan_commands
        payload = planner(
            shard_dir=Path(args.shard_dir),
            run_root=Path(args.run_root),
            condition=args.condition,
            jobs=args.jobs,
        )
        print(payload)
        return
    elif args.mode == "merge":
        payload = merge_raw_outputs(
            data_path=Path(args.data),
            shard_run_root=Path(args.shard_run_root),
            out_run=Path(args.out_run),
            allow_missing=args.allow_missing,
        )
    elif args.mode == "analyze":
        payload = analyze_run(data_path=Path(args.data), run_dir=Path(args.run_dir))
    else:
        raise ValueError(f"unknown mode: {args.mode}")

    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
