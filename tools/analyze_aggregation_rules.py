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


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize_answer(value: str) -> str:
    return str(value).strip().lower().replace(",", "")


def is_correct(predicted: str, gold: str) -> bool:
    return normalize_answer(predicted) == normalize_answer(gold)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _majority(values: list[str]) -> str:
    counts = Counter(normalize_answer(value) for value in values if normalize_answer(value) != "")
    if not counts:
        return ""
    best = counts.most_common(1)[0][0]
    for value in values:
        if normalize_answer(value) == best:
            return normalize_answer(value)
    return best


def _initial_answers(row: dict[str, Any]) -> list[str]:
    return [normalize_answer(entry.get("answer", "")) for entry in row.get("initial_raw", [])]


def _answers_by_round(row: dict[str, Any]) -> dict[int, list[str]]:
    by_round: dict[int, list[str]] = {}
    for entry in row.get("transcript_raw", []):
        by_round.setdefault(int(entry["round_index"]), []).append(normalize_answer(entry.get("answer", "")))
    return by_round


def _final_round_answers(row: dict[str, Any]) -> list[str]:
    return [normalize_answer(entry.get("answer", "")) for entry in row.get("final_raw", [])]


def _timeout_carry_forward_answers(row: dict[str, Any]) -> list[str]:
    history_by_agent: dict[int, list[tuple[int, str]]] = {}
    for entry in row.get("transcript_raw", []):
        history_by_agent.setdefault(int(entry["agent_id"]), []).append(
            (int(entry["round_index"]), normalize_answer(entry.get("answer", "")))
        )

    carried: list[str] = []
    for entry in row.get("final_raw", []):
        agent_id = int(entry["agent_id"])
        answer = normalize_answer(entry.get("answer", ""))
        if answer:
            carried.append(answer)
            continue
        previous = ""
        for round_index, candidate in sorted(history_by_agent.get(agent_id, []), key=lambda item: item[0], reverse=True):
            if round_index >= int(entry["round_index"]):
                continue
            if candidate:
                previous = candidate
                break
        carried.append(previous)
    return carried


def _all_round_answers(row: dict[str, Any]) -> list[str]:
    return [normalize_answer(entry.get("answer", "")) for entry in row.get("transcript_raw", [])]


def _majority_by_rule(row: dict[str, Any]) -> dict[str, str]:
    rule_answers = {
        "initial_majority": _initial_answers(row),
        "final_round_majority": _final_round_answers(row),
        "all_round_majority": _all_round_answers(row),
        "last_non_empty_majority": [answer for answer in _final_round_answers(row) if answer],
        "timeout_carry_forward_majority": _timeout_carry_forward_answers(row),
    }
    selected = {rule: _majority(answers) for rule, answers in rule_answers.items()}
    selected["oracle_any_history_correct"] = _oracle_any_history_correct(row)
    return selected


def _oracle_any_history_correct(row: dict[str, Any]) -> str:
    gold = normalize_answer(row.get("answer", ""))
    history_answers = _all_round_answers(row) + _initial_answers(row)
    if any(is_correct(answer, gold) for answer in history_answers):
        return gold
    return _majority(_final_round_answers(row)) or _majority(_initial_answers(row))


def _correctness_by_rule(row: dict[str, Any], selected_by_rule: dict[str, str]) -> dict[str, bool]:
    gold = row.get("gold", "")
    return {rule: is_correct(answer, gold) for rule, answer in selected_by_rule.items()}


def _initial_has_correct_answer(row: dict[str, Any]) -> bool:
    gold = row.get("gold", "")
    return any(is_correct(answer, gold) for answer in _initial_answers(row))


def analyze_aggregation_rules(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
    data_rows = {row["id"]: row for row in load_jsonl(data_path)}
    raw_rows = load_jsonl(raw_path)

    rules = [
        "final_round_majority",
        "all_round_majority",
        "last_non_empty_majority",
        "timeout_carry_forward_majority",
        "initial_majority",
        "oracle_any_history_correct",
    ]

    rows: list[dict[str, Any]] = []
    metrics = {
        rule: {
            "correct": 0,
            "loss_num": 0,
            "loss_den": 0,
        }
        for rule in rules
    }

    for row in raw_rows:
        item_id = row["id"]
        data_row = data_rows.get(item_id, {})
        merged = {**row, **data_row}
        selected_by_rule = _majority_by_rule(merged)
        correctness_by_rule = _correctness_by_rule(merged, selected_by_rule)
        initial_has_correct = _initial_has_correct_answer(merged)

        for rule in rules:
            metrics[rule]["correct"] += int(correctness_by_rule[rule])
            if initial_has_correct and rule != "oracle_any_history_correct":
                metrics[rule]["loss_den"] += 1
                metrics[rule]["loss_num"] += int(not correctness_by_rule[rule])
            elif initial_has_correct and rule == "oracle_any_history_correct":
                metrics[rule]["loss_den"] += 1
                metrics[rule]["loss_num"] += 0

        rows.append(
            {
                "item_id": item_id,
                "gold": normalize_answer(merged.get("answer", "")),
                "selected_by_rule": selected_by_rule,
                "correctness_by_rule": correctness_by_rule,
            }
        )

    summary = {
        rule: {
            "accuracy": metrics[rule]["correct"] / len(rows) if rows else 0.0,
            "answer_loss_rate": metrics[rule]["loss_num"] / metrics[rule]["loss_den"] if metrics[rule]["loss_den"] else None,
            "loss_denominator": metrics[rule]["loss_den"],
        }
        for rule in rules
    }

    return {
        "data": str(data_path),
        "raw": str(raw_path),
        "n": len(rows),
        "rules": rules,
        "summary": summary,
        "rows": rows,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# AQuA R3 Aggregation Rule Analysis")
    lines.append("")
    lines.append("This is a post-hoc aggregation analysis over the existing `raw.jsonl` traces.")
    lines.append("")
    lines.append("## Summary Metrics")
    lines.append("| rule | accuracy | answer_loss_rate | loss_denominator |")
    lines.append("| --- | ---: | ---: | ---: |")
    for rule in report["rules"]:
        summary = report["summary"][rule]
        loss_rate = "n/a" if summary["answer_loss_rate"] is None else f"{summary['answer_loss_rate']}"
        lines.append(f"| {rule} | {summary['accuracy']} | {loss_rate} | {summary['loss_denominator']} |")
    lines.append("")
    lines.append("## Item-Level Selections")
    lines.append(
        "| item_id | gold | final_round_majority | all_round_majority | last_non_empty_majority | timeout_carry_forward_majority | initial_majority | oracle_any_history_correct |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in report["rows"]:
        s = row["selected_by_rule"]
        lines.append(
            f"| {row['item_id']} | {row['gold']} | {s['final_round_majority']} | {s['all_round_majority']} | {s['last_non_empty_majority']} | {s['timeout_carry_forward_majority']} | {s['initial_majority']} | {s['oracle_any_history_correct']} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("- No raw text, prompts, or transcript dumps are included.")
    lines.append("- `answer_loss_rate` is reported only for rules where the initial-answer recovery denominator is meaningful.")
    lines.append("- `oracle_any_history_correct` is an oracle-style upper bound, not a deployable selection rule.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze post-hoc aggregation rules from a stored raw run.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    report = analyze_aggregation_rules(data_path=Path(args.data), raw_path=Path(args.raw))
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
