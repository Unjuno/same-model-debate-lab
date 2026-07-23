# ruff: noqa: E402, I001

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_synthetic_prefix_phase3c_dataset import load_jsonl
from tools.select_partial_correct_items import normalize_answer

CONDITION_ORDER = [
    "independent",
    "full_context_debate",
    "answer_hidden_debate",
    "numeric_masked_debate",
    "commit_then_numeric_masked_debate",
    "answer_hidden_numeric_masked_debate",
]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _entropy(values: list[str]) -> float:
    if not values:
        return 0.0
    counts = Counter(values)
    total = len(values)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _majority(values: list[str]) -> str:
    counts = Counter(values)
    if not counts:
        return ""
    return counts.most_common(1)[0][0]


def _empty(condition: str) -> dict[str, Any]:
    return {
        "condition": condition,
        "n_outputs": 0,
        "non_failed_outputs": 0,
        "correct_count": 0,
        "target_wrong_count": 0,
        "other_count": 0,
        "raw_extraction_failure_count": 0,
        "effective_extraction_failure_count": 0,
        "correct_rate": 0.0,
        "target_wrong_rate": None,
        "other_rate": 0.0,
        "raw_extraction_failure_rate": 0.0,
        "effective_extraction_failure_rate": 0.0,
        "answer_entropy": 0.0,
        "unique_answer_count": 0,
        "answer_counts": {},
        "initial_any_correct_rate": 0.0,
        "final_majority_correct_rate": 0.0,
        "correct_to_wrong_collapse_rate": None,
        "correct_initial_lost_rate": None,
        "target_wrong_convergence_rate": None,
        "history_metrics_available": False,
    }


def _finalize(summary: dict[str, Any], answers: list[str]) -> dict[str, Any]:
    summary["answer_counts"] = dict(sorted(Counter(answers).items()))
    summary["correct_rate"] = summary["correct_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
    summary["other_rate"] = summary["other_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
    summary["raw_extraction_failure_rate"] = summary["raw_extraction_failure_count"] / summary["n_outputs"] if summary["n_outputs"] else 0.0
    summary["effective_extraction_failure_rate"] = summary["effective_extraction_failure_count"] / summary["n_outputs"] if summary["n_outputs"] else 0.0
    summary["unique_answer_count"] = len(summary["answer_counts"])
    summary["answer_entropy"] = _entropy(answers)
    return summary


def _load_raw_rows(raw_paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in raw_paths:
        rows.extend(load_jsonl(path))
    return rows


def analyze_live_mitigation(*, data_path: Path, raw_paths: list[Path]) -> dict[str, Any]:
    data_rows = load_jsonl(data_path)
    raw_rows = _load_raw_rows(raw_paths)
    data_by_id = {str(row["id"]): row for row in data_rows if "id" in row}
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"answers": [], "total": 0, "raw_failures": 0, "gold": "", "target_wrong": None, "history_rows": []})
    overall_answers: list[str] = []
    overall_correct = 0
    overall_total = 0
    overall_initial_any_correct = 0
    overall_final_majority_correct = 0
    overall_history_eligible = 0
    overall_collapse = 0
    overall_correct_lost = 0
    overall_target_wrong_conv = 0

    for raw_row in raw_rows:
        row_id = str(raw_row.get("id", ""))
        data_row = data_by_id.get(row_id)
        if data_row is None:
            continue
        condition = str(raw_row.get("condition", data_row.get("condition", "unknown")))
        gold = normalize_answer(data_row.get("answer", raw_row.get("gold", "")))
        target_wrong = data_row.get("metadata", {}).get("target_wrong") if isinstance(data_row.get("metadata", {}), dict) else None
        bucket = grouped[condition]
        bucket["gold"] = gold
        bucket["target_wrong"] = normalize_answer(target_wrong) if target_wrong else None
        bucket["total"] += 1
        final_answer = normalize_answer(raw_row.get("final_answer", ""))
        if final_answer:
            bucket["answers"].append(final_answer)
            overall_answers.append(final_answer)
            overall_correct += int(final_answer == gold)
            overall_total += 1
        if int(raw_row.get("extraction_failures", 0)) > 0:
            bucket["raw_failures"] += 1
        if isinstance(raw_row.get("transcript_raw"), list):
            bucket["history_rows"].append(raw_row)
            initial_answers = [normalize_answer(value) for value in raw_row.get("initial_answers", []) if normalize_answer(value)]
            if initial_answers:
                overall_history_eligible += 1
                initial_has_correct = gold in initial_answers
                overall_initial_any_correct += int(initial_has_correct)
                overall_final_majority_correct += int(_majority([normalize_answer(value) for value in raw_row.get("final_answers", []) if normalize_answer(value)]) == gold)
                if initial_has_correct and target_wrong and final_answer == normalize_answer(target_wrong):
                    overall_collapse += 1
                if initial_has_correct and final_answer != gold:
                    overall_correct_lost += 1
                if target_wrong and final_answer == normalize_answer(target_wrong):
                    overall_target_wrong_conv += 1

    by_condition = {condition: _empty(condition) for condition in CONDITION_ORDER}
    for condition, bucket in grouped.items():
        summary = _empty(condition)
        answers = bucket["answers"]
        summary["n_outputs"] = bucket["total"]
        summary["non_failed_outputs"] = len(answers)
        summary["correct_count"] = sum(1 for answer in answers if answer == bucket["gold"])
        target_wrong = bucket["target_wrong"]
        summary["target_wrong_count"] = sum(1 for answer in answers if target_wrong and answer == target_wrong)
        summary["other_count"] = summary["non_failed_outputs"] - summary["correct_count"] - summary["target_wrong_count"]
        summary["raw_extraction_failure_count"] = bucket["raw_failures"]
        summary["effective_extraction_failure_count"] = bucket["raw_failures"]
        history_rows = bucket["history_rows"]
        if history_rows:
            summary["history_metrics_available"] = True
            initial_any_correct = 0
            final_majority_correct = 0
            collapse = 0
            correct_lost = 0
            target_wrong_conv = 0
            eligible = 0
            for row in history_rows:
                final_answers = [normalize_answer(value) for value in row.get("final_answers", []) if normalize_answer(value)]
                initial_answers = [normalize_answer(value) for value in row.get("initial_answers", []) if normalize_answer(value)]
                final_answer = normalize_answer(row.get("final_answer", ""))
                if not initial_answers:
                    continue
                eligible += 1
                initial_has_correct = bucket["gold"] in initial_answers
                final_is_correct = final_answer == bucket["gold"]
                initial_any_correct += int(initial_has_correct)
                final_majority_correct += int(_majority(final_answers) == bucket["gold"])
                if initial_has_correct and final_answer == target_wrong:
                    collapse += 1
                if initial_has_correct and not final_is_correct:
                    correct_lost += 1
                if target_wrong and final_answer == target_wrong:
                    target_wrong_conv += 1
            summary["initial_any_correct_rate"] = initial_any_correct / eligible if eligible else 0.0
            summary["final_majority_correct_rate"] = final_majority_correct / eligible if eligible else 0.0
            summary["correct_to_wrong_collapse_rate"] = collapse / eligible if eligible else 0.0
            summary["correct_initial_lost_rate"] = correct_lost / eligible if eligible else 0.0
            summary["target_wrong_convergence_rate"] = target_wrong_conv / eligible if eligible else 0.0
        summary["target_wrong_rate"] = summary["target_wrong_count"] / summary["non_failed_outputs"] if target_wrong else None
        summary = _finalize(summary, answers)
        if not target_wrong:
            summary["target_wrong_rate"] = None
        by_condition[condition] = summary

    baseline = by_condition["independent"]
    full_context = by_condition["full_context_debate"]
    condition_effects = {
        "full_context_minus_independent_delta_correct_rate": full_context["correct_rate"] - baseline["correct_rate"],
        "answer_hidden_minus_full_context_delta_correct_rate": by_condition["answer_hidden_debate"]["correct_rate"] - full_context["correct_rate"],
        "numeric_masked_minus_full_context_delta_correct_rate": by_condition["numeric_masked_debate"]["correct_rate"] - full_context["correct_rate"],
        "commit_then_numeric_masked_minus_full_context_delta_correct_rate": by_condition["commit_then_numeric_masked_debate"]["correct_rate"] - full_context["correct_rate"],
    }

    summary = {
        "n": len(raw_rows),
        "final_accuracy": overall_correct / overall_total if overall_total else 0.0,
        "oracle_at_k": overall_initial_any_correct / overall_history_eligible if overall_history_eligible else 0.0,
        "answer_loss_rate": overall_correct_lost / overall_history_eligible if overall_history_eligible else 0.0,
        "same_error_agreement_rate": 0.0,
        "diversity_drop": 0.0,
        "extraction_failure_rate": sum(1 for row in raw_rows if int(row.get("extraction_failures", 0)) > 0) / len(raw_rows) if raw_rows else 0.0,
        "history_metrics_available": bool(overall_history_eligible),
        "initial_any_correct_rate": overall_initial_any_correct / overall_history_eligible if overall_history_eligible else 0.0,
        "final_majority_correct_rate": overall_final_majority_correct / overall_history_eligible if overall_history_eligible else 0.0,
        "correct_to_wrong_collapse_rate": overall_collapse / overall_history_eligible if overall_history_eligible else None,
        "correct_initial_lost_rate": overall_correct_lost / overall_history_eligible if overall_history_eligible else None,
        "target_wrong_convergence_rate": overall_target_wrong_conv / overall_history_eligible if overall_history_eligible else None,
    }
    return {
        "summary": summary,
        "by_condition": by_condition,
        "condition_effects": condition_effects,
        "raw_sources": [str(path) for path in raw_paths],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Live Debate Mitigation Smoke Report",
        "",
        "Caution: this is a smoke-oriented, diagnostic report, not a safety proof or benchmark claim.",
        "",
        "## Summary",
        "",
        f"- n: {report['summary']['n']}",
        f"- final_accuracy: {report['summary']['final_accuracy']}",
        f"- oracle_at_k: {report['summary']['oracle_at_k']}",
        f"- answer_loss_rate: {report['summary']['answer_loss_rate']}",
        f"- same_error_agreement_rate: {report['summary']['same_error_agreement_rate']}",
        f"- diversity_drop: {report['summary']['diversity_drop']}",
        f"- extraction_failure_rate: {report['summary']['extraction_failure_rate']}",
        "",
        "## By Condition",
        "",
        "| condition | correct_rate | target_wrong_rate | answer_entropy | initial_any_correct_rate | final_majority_correct_rate | correct_to_wrong_collapse_rate | correct_initial_lost_rate | target_wrong_convergence_rate | history_metrics_available |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for condition in CONDITION_ORDER:
        summary = report["by_condition"][condition]
        target_wrong_rate = summary["target_wrong_rate"]
        target_wrong_text = "N/A" if target_wrong_rate is None else f"{target_wrong_rate:.3f}"
        lines.append(
            f"| {condition} | {summary['correct_rate']:.3f} | {target_wrong_text} | {summary['answer_entropy']:.3f} | {summary['initial_any_correct_rate']:.3f} | {summary['final_majority_correct_rate']:.3f} | {summary['correct_to_wrong_collapse_rate']} | {summary['correct_initial_lost_rate']} | {summary['target_wrong_convergence_rate']} | {summary['history_metrics_available']} |"
        )
    lines.extend(
        [
            "",
            "## Condition Effects",
            "",
            "| effect | value |",
            "| --- | ---: |",
        ]
    )
    for name, value in report["condition_effects"].items():
        lines.append(f"| {name} | {value:.3f} |")
    lines.append("")
    lines.append("No raw model text is included.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a live debate mitigation run.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", nargs="+", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    report = analyze_live_mitigation(data_path=Path(args.data), raw_paths=[Path(path) for path in args.raw])
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
