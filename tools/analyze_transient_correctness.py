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

# ruff: noqa: E402

from tools.filter_by_independent_calibration import load_jsonl, normalize_answer


def _majority(values: list[str]) -> str:
    counts: dict[str, int] = {}
    order: list[str] = []
    for value in values:
        normalized = normalize_answer(value)
        if not normalized:
            continue
        if normalized not in counts:
            order.append(normalized)
            counts[normalized] = 0
        counts[normalized] += 1
    if not counts:
        return ""
    return max(counts, key=lambda value: (counts[value], -order.index(value)))


def _is_correct(answer: str, gold: str) -> bool:
    return normalize_answer(answer) == normalize_answer(gold)


def _answers_by_round(row: dict[str, Any]) -> dict[int, list[str]]:
    rounds: dict[int, list[str]] = {}
    for entry in row.get("transcript_raw", []):
        round_index = int(entry["round_index"])
        rounds.setdefault(round_index, []).append(normalize_answer(entry.get("answer", "")))
    return rounds


def _round_majorities(rounds: dict[int, list[str]]) -> dict[str, str]:
    return {str(round_index): _majority(rounds[round_index]) for round_index in sorted(rounds)}


def _round_correctness(round_majorities: dict[str, str], gold: str) -> dict[str, bool]:
    return {
        round_index: _is_correct(answer, gold)
        for round_index, answer in round_majorities.items()
    }


def _any_non_final_round_unanimous_correct(rounds: dict[int, list[str]], gold: str) -> bool:
    if not rounds:
        return False
    final_round = max(rounds)
    for round_index, answers in rounds.items():
        if round_index == final_round:
            continue
        filtered = [answer for answer in answers if answer]
        if filtered and len(set(filtered)) == 1 and _is_correct(filtered[0], gold):
            return True
    return False


def _any_non_final_round_correct_majority(round_majorities: dict[str, str], gold: str) -> bool:
    if not round_majorities:
        return False
    final_round = str(max(int(index) for index in round_majorities))
    for round_index, answer in round_majorities.items():
        if round_index == final_round:
            continue
        if _is_correct(answer, gold):
            return True
    return False


def _category(
    *,
    rounds: dict[int, list[str]],
    round_majorities: dict[str, str],
    gold: str,
) -> str:
    if not round_majorities:
        return "no_initial_majority"
    initial_round = str(min(int(index) for index in round_majorities))
    final_round = str(max(int(index) for index in round_majorities))
    initial_majority = round_majorities.get(initial_round, "")
    final_majority = round_majorities.get(final_round, "")
    initial_majority_correct = _is_correct(initial_majority, gold) if initial_majority else False
    final_majority_correct = _is_correct(final_majority, gold) if final_majority else False

    if not initial_majority:
        return "no_initial_majority"
    if not final_majority:
        return "no_final_majority"
    if _any_non_final_round_unanimous_correct(rounds, gold) and not final_majority_correct:
        return "transient_correct_consensus_lost"
    if _any_non_final_round_correct_majority(round_majorities, gold) and not final_majority_correct:
        return "transient_correct_majority_lost"
    if initial_majority_correct and final_majority_correct:
        return "preserved_correct"
    if not initial_majority_correct and final_majority_correct:
        return "recovered_to_correct"
    if initial_majority_correct and not final_majority_correct:
        return "correct_to_wrong"
    if not any(_is_correct(answer, gold) for answer in round_majorities.values()):
        return "persistent_error"
    return "persistent_error"


def analyze_transient_correctness(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
    data_rows = {row["id"]: row for row in load_jsonl(data_path)}
    raw_rows = load_jsonl(raw_path)

    items: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()

    for row in raw_rows:
        item_id = row["id"]
        data_row = data_rows.get(item_id, {})
        gold = normalize_answer(data_row.get("answer", row.get("gold", "")))
        rounds = _answers_by_round(row)
        round_majorities = _round_majorities(rounds)
        round_correctness = _round_correctness(round_majorities, gold)
        category = _category(rounds=rounds, round_majorities=round_majorities, gold=gold)
        category_counts[category] += 1
        initial_round = str(min(rounds)) if rounds else ""
        final_round = str(max(rounds)) if rounds else ""
        initial_majority = round_majorities.get(initial_round, "") if initial_round else ""
        final_majority = round_majorities.get(final_round, "") if final_round else ""
        any_round_majority_correct = any(round_correctness.values())
        any_round_unanimous_correct = _any_non_final_round_unanimous_correct(rounds, gold) or (
            bool(rounds)
            and _is_correct(_majority(rounds[int(final_round)]), gold)
            and len(set(answer for answer in rounds[int(final_round)] if answer)) == 1
        )

        items.append(
            {
                "item_id": item_id,
                "gold": gold,
                "answers_by_round": {str(round_index): rounds[round_index] for round_index in sorted(rounds)},
                "majority_by_round": round_majorities,
                "round_correctness_by_majority": round_correctness,
                "initial_majority": initial_majority,
                "final_majority": final_majority,
                "initial_majority_correct": _is_correct(initial_majority, gold) if initial_majority else False,
                "final_majority_correct": _is_correct(final_majority, gold) if final_majority else False,
                "any_round_majority_correct": any_round_majority_correct,
                "any_round_unanimous_correct": any_round_unanimous_correct,
                "category": category,
            }
        )

    summary = {
        "data": str(data_path),
        "raw": str(raw_path),
        "n": len(items),
        "category_counts": dict(category_counts),
        "items": items,
    }
    return summary


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = ["# Transient Correctness Analysis", "", "## Summary", "| category | count |", "| --- | ---: |"]
    for category, count in report["category_counts"].items():
        lines.append(f"| {category} | {count} |")
    lines.extend(
        [
            "",
            "## Item Table",
            "| item_id | gold | initial_majority | final_majority | any_round_majority_correct | any_round_unanimous_correct | category |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in report["items"]:
        lines.append(
            f"| {item['item_id']} | {item['gold']} | {item['initial_majority']} | {item['final_majority']} | "
            f"{item['any_round_majority_correct']} | {item['any_round_unanimous_correct']} | {item['category']} |"
        )
    highlighted = [
        item for item in report["items"]
        if item["category"] in {"transient_correct_consensus_lost", "transient_correct_majority_lost"}
    ]
    lines.extend(["", "## Highlighted Items"])
    if highlighted:
        lines.append("| item_id | gold | category | initial_majority | final_majority |")
        lines.append("| --- | --- | --- | --- | --- |")
        for item in highlighted:
            lines.append(
                f"| {item['item_id']} | {item['gold']} | {item['category']} | {item['initial_majority']} | {item['final_majority']} |"
            )
    else:
        lines.append("None")
    lines.append("")
    lines.append("No raw transcripts are included in this report.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze transient correct majority/consensus loss across debate rounds.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    report = analyze_transient_correctness(data_path=Path(args.data), raw_path=Path(args.raw))
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
