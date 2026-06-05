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


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def normalize_answer(value: Any) -> str:
    text = str(value).strip()
    match = ANSWER_RE.match(text)
    if match:
        text = match.group(1).strip()
    if LETTER_RE.match(text):
        return text.upper()
    if NUMBER_RE.match(text):
        return text.replace(",", "")
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


def filter_by_independent_calibration(
    *,
    raw_rows: list[dict[str, Any]],
    data_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data_by_id = {row["id"]: row for row in data_rows}
    selected: list[dict[str, Any]] = []
    selected_ids: list[str] = []
    all_correct = 0
    all_wrong = 0
    partially_correct = 0
    extraction_failed = 0
    oracle_hits = 0

    for row in raw_rows:
        initial = _initial_answers(row)
        agent_count = len(initial)
        if agent_count == 0:
            continue
        gold = _gold_answer(row)
        correct_count = sum(1 for answer in initial if answer == gold)
        failures = _initial_extraction_failures(row)
        has_correct = correct_count > 0
        oracle_hits += int(has_correct)

        if failures:
            extraction_failed += 1
        elif correct_count == agent_count:
            all_correct += 1
        elif correct_count == 0:
            all_wrong += 1
        else:
            partially_correct += 1

        if failures == 0 and 1 <= correct_count <= agent_count - 1:
            item = data_by_id.get(row["id"])
            if item is not None:
                selected.append(item)
                selected_ids.append(row["id"])

    total = len(raw_rows)
    report = {
        "total": total,
        "selected": len(selected),
        "all_correct": all_correct,
        "all_wrong": all_wrong,
        "partially_correct": partially_correct,
        "extraction_failed": extraction_failed,
        "partial_correct_rate": partially_correct / total if total else 0.0,
        "oracle_at_k": oracle_hits / total if total else 0.0,
        "selected_ids": selected_ids,
    }
    return selected, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter items using independent calibration results.")
    parser.add_argument("--raw", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    raw_rows = load_jsonl(Path(args.raw))
    data_rows = load_jsonl(Path(args.data))
    selected, report = filter_by_independent_calibration(raw_rows=raw_rows, data_rows=data_rows)
    write_jsonl(Path(args.out), selected)
    write_json(Path(args.report), report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
