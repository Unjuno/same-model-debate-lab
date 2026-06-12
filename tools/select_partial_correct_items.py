from __future__ import annotations

import argparse
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ANSWER_RE = re.compile(r"^\s*<answer>\s*(.*?)\s*</answer>\s*$", re.IGNORECASE | re.DOTALL)
LETTER_RE = re.compile(r"^[A-Ea-e]$")
NUMERIC_RE = re.compile(r"^-?[\d,]+(?:\.\d+)?$")


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

    if NUMERIC_RE.match(text):
        normalized = text.replace(",", "")
        try:
            decimal_value = Decimal(normalized)
        except InvalidOperation:
            return normalized
        if decimal_value == decimal_value.to_integral():
            return str(decimal_value.to_integral())
        return format(decimal_value.normalize(), "f").rstrip("0").rstrip(".")

    return text


def _initial_entries(row: dict[str, Any]) -> list[dict[str, Any]]:
    initial_raw = row.get("initial_raw")
    if isinstance(initial_raw, list):
        return [entry for entry in initial_raw if isinstance(entry, dict)]
    return []


def _initial_answers(row: dict[str, Any]) -> list[str]:
    entries = _initial_entries(row)
    if entries:
        return [normalize_answer(entry.get("answer", "")) for entry in entries]
    initial_answers = row.get("initial_answers")
    if isinstance(initial_answers, list):
        return [normalize_answer(answer) for answer in initial_answers]
    return []


def _initial_extraction_failed(row: dict[str, Any]) -> bool:
    entries = _initial_entries(row)
    if entries:
        return any(bool(entry.get("extraction_failed", False)) for entry in entries)
    return bool(row.get("initial_extraction_failures", 0))


def _gold_answer(row: dict[str, Any]) -> str:
    value = row.get("gold", row.get("answer", ""))
    text = str(value).strip()
    if text.startswith("####"):
        text = text[4:].strip()
    return normalize_answer(text)


def _load_excluded_ids(paths: list[Path]) -> set[str]:
    excluded: set[str] = set()
    for path in paths:
        for row in load_jsonl(path):
            row_id = row.get("id")
            if row_id is not None:
                excluded.add(str(row_id))
    return excluded


def select_partial_correct_items(
    *,
    raw_rows: list[dict[str, Any]],
    data_rows: list[dict[str, Any]],
    limit: int | None = None,
    excluded_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    excluded_ids = excluded_ids or set()
    data_by_id = {str(row["id"]): row for row in data_rows if "id" in row}
    selected: list[dict[str, Any]] = []

    for row in raw_rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in excluded_ids:
            continue
        item = data_by_id.get(row_id)
        if item is None:
            continue

        initial = _initial_answers(row)
        if not initial or _initial_extraction_failed(row):
            continue

        gold = _gold_answer(item)
        correct_count = sum(1 for answer in initial if answer == gold)
        if 1 <= correct_count <= len(initial) - 1:
            selected.append(item)
            if limit is not None and len(selected) >= limit:
                break

    return selected


def _candidate_ids(
    *,
    raw_rows: list[dict[str, Any]],
    data_rows: list[dict[str, Any]],
    excluded_ids: set[str],
) -> list[str]:
    data_by_id = {str(row["id"]): row for row in data_rows if "id" in row}
    candidates: list[str] = []
    for row in raw_rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in excluded_ids:
            continue
        item = data_by_id.get(row_id)
        if item is None:
            continue
        initial = _initial_answers(row)
        if not initial or _initial_extraction_failed(row):
            continue
        gold = _gold_answer(item)
        correct_count = sum(1 for answer in initial if answer == gold)
        if 1 <= correct_count <= len(initial) - 1:
            candidates.append(row_id)
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Select partial-correct benchmark rows from screening results.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--exclude", action="append", default=[], help="JSONL file of benchmark rows to exclude.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    data_rows = load_jsonl(Path(args.data))
    raw_rows = load_jsonl(Path(args.raw))
    excluded_ids = _load_excluded_ids([Path(path) for path in args.exclude])
    selected = select_partial_correct_items(
        raw_rows=raw_rows,
        data_rows=data_rows,
        limit=args.limit,
        excluded_ids=excluded_ids,
    )
    write_jsonl(Path(args.out), selected)
    candidates = _candidate_ids(raw_rows=raw_rows, data_rows=data_rows, excluded_ids=excluded_ids)
    summary = {
        "candidates": len(candidates),
        "excluded": len(excluded_ids),
        "input_items": len(data_rows),
        "raw_items_seen": len(raw_rows),
        "selected": len(selected),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
