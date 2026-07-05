from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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


def shard_paths(*, shard_dir: Path) -> list[Path]:
    return sorted(shard_dir.glob("*.jsonl"))


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
        shard_path = out_dir / f"phase3c_shard_{shard_index}.jsonl"
        write_jsonl(shard_path, shard)
        shard_counts[shard_path.name] = len(shard)
    return {"mode": "split", "rows": len(rows), "shards": shards, "shard_counts": shard_counts}


def plan_commands(*, shard_dir: Path, run_root: Path, condition: str, jobs: int, resume: bool) -> str:
    if jobs <= 0:
        raise ValueError("jobs must be positive")
    paths = shard_paths(shard_dir=shard_dir)
    if len(paths) < jobs:
        raise ValueError(f"expected at least {jobs} shard files in {shard_dir}")
    lines = ["mkdir -p " + str(run_root)]
    for job_index in range(jobs):
        shard_path = paths[job_index]
        shard_run_dir = run_root / f"shard_{job_index}"
        raw_path = shard_run_dir / "raw.jsonl"
        resume_flag = " --resume" if resume and raw_path.exists() else ""
        lines.extend(
            [
                "SMDEBATE_PROGRESS=1 \\",
                "SMDEBATE_REQUEST_TIMEOUT_SECONDS=600 \\",
                "SMDEBATE_MAX_TOKENS=64 \\",
                "SMDEBATE_CONTINUE_ON_ERROR=1 \\",
                f"smdebate --data {shard_path} --condition {condition} --out {shard_run_dir}{resume_flag} &",
                f"PID{job_index}=$!",
            ]
        )
    for job_index in range(jobs):
        lines.append(f"wait $PID{job_index}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Shard-parallel Phase 3c execution helper.")
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

    args = parser.parse_args()
    if args.mode == "split":
        payload = split_dataset(data_path=Path(args.data), out_dir=Path(args.out_dir), shards=args.shards)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return
    if args.mode == "plan":
        print(
            plan_commands(
                shard_dir=Path(args.shard_dir),
                run_root=Path(args.run_root),
                condition=args.condition,
                jobs=args.jobs,
                resume=args.resume,
            )
        )
        return
    raise ValueError(f"unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
