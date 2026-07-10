from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.build_synthetic_prefix_phase3c_dataset import load_jsonl, write_jsonl


def build_dataset(*, data_rows: list[dict[str, Any]], limit: int | None = None) -> list[dict[str, Any]]:
    if limit is not None and limit <= 0:
        raise ValueError("limit must be positive")
    rows = [row for row in data_rows if isinstance(row, dict) and "id" in row and "question" in row and "answer" in row]
    if limit is not None:
        rows = rows[:limit]
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a small live-mitigation smoke dataset from an existing benchmark JSONL.")
    parser.add_argument("--data", required=True, help="Input JSONL benchmark file.")
    parser.add_argument("--out", required=True, help="Output JSONL dataset path.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of rows to keep.")
    args = parser.parse_args()

    rows = build_dataset(data_rows=load_jsonl(Path(args.data)), limit=args.limit)
    write_jsonl(Path(args.out), rows)
    print(json.dumps({"rows": len(rows), "limit": args.limit, "out": args.out}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
