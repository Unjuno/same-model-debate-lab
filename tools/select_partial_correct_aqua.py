from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ANSWER_RE = re.compile(r"^\s*<answer>\s*(.*?)\s*</answer>\s*$", re.IGNORECASE | re.DOTALL)
LETTER_RE = re.compile(r"^[A-Ea-e]$")
NUMBER_RE = re.compile(r"^-?[\d,]+(?:\.\d+)?$")


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


def normalize_answer(value: Any) -> str:
    text = str(value).strip()
    match = ANSWER_RE.match(text)
    if match:
        text = match.group(1).strip()
    if LETTER_RE.match(text):
        return text.upper()
    if NUMBER_RE.match(text):
        normalized = text.replace(",", "")
        if "." in normalized:
            integer_part, fractional_part = normalized.split(".", 1)
            if set(fractional_part) <= {"0"} and integer_part not in {"", "-"}:
                return integer_part
        return normalized
    return text.strip()


def _initial_answers(row: dict[str, Any]) -> list[str]:
    if "initial_raw" in row:
        return [normalize_answer(entry.get("answer", "")) for entry in row["initial_raw"]]
    if "initial_answers" in row:
        return [normalize_answer(answer) for answer in row["initial_answers"]]
    return []


def _initial_extraction_failures(row: dict[str, Any]) -> int:
    if "initial_raw" in row:
        return sum(int(bool(entry.get("extraction_failed", False))) for entry in row["initial_raw"])
    return int(row.get("initial_extraction_failures", 0))


def _gold_answer(row: dict[str, Any]) -> str:
    return normalize_answer(row.get("gold", row.get("answer", "")))


def _load_excluded_ids(paths: list[Path]) -> set[str]:
    excluded: set[str] = set()
    for path in paths:
        for row in load_jsonl(path):
            row_id = row.get("id")
            if row_id is not None:
                excluded.add(str(row_id))
    return excluded


def select_partial_correct_aqua(
    *,
    raw_rows: list[dict[str, Any]],
    data_rows: list[dict[str, Any]],
    excluded_ids: set[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    excluded_ids = excluded_ids or set()
    data_by_id = {row["id"]: row for row in data_rows}
    selected: list[dict[str, Any]] = []

    for row in raw_rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in excluded_ids:
            continue
        initial = _initial_answers(row)
        agent_count = len(initial)
        if agent_count == 0:
            continue
        if _initial_extraction_failures(row):
            continue
        gold = _gold_answer(row)
        correct_count = sum(1 for answer in initial if answer == gold)
        if 1 <= correct_count <= agent_count - 1:
            item = data_by_id.get(row_id)
            if item is not None:
                selected.append(item)
                if limit is not None and len(selected) >= limit:
                    break

    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Select partial-correct AQuA benchmark rows from screening results.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--exclude", action="append", default=[], help="JSONL file of benchmark rows to exclude.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    data_rows = load_jsonl(Path(args.data))
    raw_rows = load_jsonl(Path(args.raw))
    excluded_ids = _load_excluded_ids([Path(path) for path in args.exclude])
    selected = select_partial_correct_aqua(
        raw_rows=raw_rows,
        data_rows=data_rows,
        excluded_ids=excluded_ids,
        limit=args.limit,
    )
    write_jsonl(Path(args.out), selected)
    print(json.dumps({"selected": len(selected), "excluded": len(excluded_ids)}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
