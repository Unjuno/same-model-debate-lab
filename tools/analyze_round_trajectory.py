from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from smdebate.metrics import is_correct
from tools.filter_by_independent_calibration import load_jsonl, normalize_answer, write_json


def _majority(values: list[str]) -> str:
    counts = Counter(normalize_answer(value) for value in values)
    if not counts:
        return ""
    best = counts.most_common(1)[0][0]
    for value in values:
        if normalize_answer(value) == best:
            return normalize_answer(value)
    return best


def _category(correctness: list[bool]) -> str:
    if not correctness:
        return "persistent_error"
    if all(correctness):
        return "preserved_correct"
    if not any(correctness):
        return "persistent_error"
    flips = sum(int(a != b) for a, b in zip(correctness, correctness[1:], strict=False))
    if flips > 1:
        return "oscillation"
    if correctness[0] is False and correctness[-1] is True:
        return "recovery"
    if correctness[0] is True and correctness[-1] is False:
        return "deterioration"
    if any(correctness[i] is False and any(correctness[i + 1 :]) for i in range(len(correctness) - 1)):
        return "recovery"
    if any(correctness[i] is True and any(not x for x in correctness[i + 1 :]) for i in range(len(correctness) - 1)):
        return "deterioration"
    return "oscillation"


def analyze_round_trajectory(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
    data_rows = {row["id"]: row for row in load_jsonl(data_path)}
    raw_rows = load_jsonl(raw_path)
    trajectories: list[dict[str, Any]] = []
    category_counts = {
        "preserved_correct": 0,
        "persistent_error": 0,
        "recovery": 0,
        "deterioration": 0,
        "oscillation": 0,
    }

    for row in raw_rows:
        item_id = row["id"]
        data_row = data_rows.get(item_id, {})
        transcript = row.get("transcript_raw", [])
        by_round: dict[int, list[str]] = {}
        for entry in transcript:
            by_round.setdefault(int(entry["round_index"]), []).append(normalize_answer(entry.get("answer", "")))

        round_numbers = sorted(by_round)
        initial_answers = [normalize_answer(answer) for answer in row.get("initial_answers", [])]
        majority_answer_by_round = {str(round_index): _majority(by_round[round_index]) for round_index in round_numbers}
        correctness_by_round = {
            str(round_index): is_correct(majority_answer_by_round[str(round_index)], data_row.get("answer", ""))
            for round_index in round_numbers
        }
        correctness_list = [correctness_by_round[str(round_index)] for round_index in round_numbers]
        category = _category(correctness_list)
        category_counts[category] += 1

        flip_count = sum(int(a != b) for a, b in zip(correctness_list, correctness_list[1:], strict=False))
        trajectories.append(
            {
                "item_id": item_id,
                "gold": normalize_answer(data_row.get("answer", "")),
                "initial_answers": initial_answers,
                "answers_by_round": {str(round_index): by_round[round_index] for round_index in round_numbers},
                "majority_answer_by_round": majority_answer_by_round,
                "correctness_by_round": correctness_by_round,
                "flip_count": flip_count,
                "category": category,
            }
        )

    return {
        "data": str(data_path),
        "raw": str(raw_path),
        "n": len(trajectories),
        "trajectories": trajectories,
        "category_counts": category_counts,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = ["# AQuA Round Trajectory", "", "## Categories"]
    for category, count in report["category_counts"].items():
        lines.append(f"- {category}: {count}")
    lines.append("")
    lines.append("## Item Trajectories")
    lines.append(
        "| item_id | gold | initial_answers | answers_by_round | majority_answer_by_round | correctness_by_round | flip_count | category |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | ---: | --- |")
    for row in report["trajectories"]:
        lines.append(
            f"| {row['item_id']} | {row['gold']} | {row['initial_answers']} | {row['answers_by_round']} | {row['majority_answer_by_round']} | {row['correctness_by_round']} | {row['flip_count']} | {row['category']} |"
        )
    lines.append("")
    lines.append("No raw transcripts are included in this report.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze within-run debate trajectories from transcript_raw.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    report = analyze_round_trajectory(data_path=Path(args.data), raw_path=Path(args.raw))
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
