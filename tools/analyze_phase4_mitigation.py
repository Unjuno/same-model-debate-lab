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

from tools.select_partial_correct_items import normalize_answer  # noqa: E402

CONDITION_ORDER = [
    "independent",
    "full_context_debate",
    "answer_hidden_debate",
    "numeric_masked_debate",
    "commit_then_numeric_masked_debate",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _entropy(values: list[str]) -> float:
    if not values:
        return 0.0
    counts = Counter(values)
    total = len(values)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


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
        "target_wrong_rate": 0.0,
        "other_rate": 0.0,
        "raw_extraction_failure_rate": 0.0,
        "effective_extraction_failure_rate": 0.0,
        "answer_entropy": 0.0,
        "unique_answer_count": 0,
        "answer_counts": {},
        "correct_to_wrong_collapse_rate": None,
        "correct_initial_lost_rate": None,
        "target_wrong_convergence_rate": None,
        "history_metrics_available": False,
    }


def _finalize(summary: dict[str, Any], answers: list[str]) -> dict[str, Any]:
    summary["answer_counts"] = dict(sorted(Counter(answers).items()))
    summary["correct_rate"] = summary["correct_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
    summary["target_wrong_rate"] = summary["target_wrong_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
    summary["other_rate"] = summary["other_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
    summary["raw_extraction_failure_rate"] = summary["raw_extraction_failure_count"] / summary["n_outputs"] if summary["n_outputs"] else 0.0
    summary["effective_extraction_failure_rate"] = summary["effective_extraction_failure_count"] / summary["n_outputs"] if summary["n_outputs"] else 0.0
    summary["unique_answer_count"] = len(summary["answer_counts"])
    summary["answer_entropy"] = _entropy(answers)
    return summary


def analyze_phase4_mitigation(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
    data_rows = load_jsonl(data_path)
    raw_rows = load_jsonl(raw_path)
    data_by_id = {str(row["id"]): row for row in data_rows if "id" in row}
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"answers": [], "total": 0, "raw_failures": 0, "target_wrong": "", "gold": "", "metadata": {}})
    skipped_raw_ids: list[str] = []
    history_available = False
    history_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for raw_row in raw_rows:
        row_id = str(raw_row.get("id", ""))
        data_row = data_by_id.get(row_id)
        if data_row is None:
            skipped_raw_ids.append(row_id)
            continue
        metadata = data_row.get("metadata", {})
        condition = str(metadata.get("mitigation_condition", metadata.get("condition", "unknown")))
        bucket = grouped[condition]
        bucket["metadata"] = metadata
        bucket["gold"] = normalize_answer(metadata.get("gold", data_row.get("answer", "")))
        bucket["target_wrong"] = normalize_answer(metadata.get("target_wrong", ""))
        bucket["total"] += 1
        final_answer = normalize_answer(raw_row.get("final_answer", ""))
        if final_answer:
            bucket["answers"].append(final_answer)
        if int(raw_row.get("extraction_failures", 0)) > 0:
            bucket["raw_failures"] += 1
        if isinstance(raw_row.get("initial_answers"), list) and isinstance(raw_row.get("final_answers"), list):
            if bool(metadata.get("history_metrics_applicable", False)):
                history_available = True
                history_buckets[condition].append(raw_row)

    by_condition = {condition: _empty(condition) for condition in CONDITION_ORDER}
    for condition, bucket in grouped.items():
        summary = _empty(condition)
        answers = bucket["answers"]
        summary["n_outputs"] = bucket["total"]
        summary["non_failed_outputs"] = len(answers)
        summary["correct_count"] = sum(1 for answer in answers if answer == bucket["gold"])
        summary["target_wrong_count"] = sum(1 for answer in answers if bucket["target_wrong"] and answer == bucket["target_wrong"])
        summary["other_count"] = summary["non_failed_outputs"] - summary["correct_count"] - summary["target_wrong_count"]
        summary["raw_extraction_failure_count"] = bucket["raw_failures"]
        summary["effective_extraction_failure_count"] = bucket["raw_failures"]
        summary["history_metrics_available"] = history_available and condition in history_buckets
        if summary["history_metrics_available"]:
            collapse = 0
            correct_lost = 0
            target_wrong_conv = 0
            eligible = 0
            for row in history_buckets[condition]:
                initial_answers = [normalize_answer(v) for v in row.get("initial_answers", []) if normalize_answer(v)]
                final_answer = normalize_answer(row.get("final_answer", ""))
                if not initial_answers:
                    continue
                eligible += 1
                initial_has_correct = bucket["gold"] in initial_answers
                final_is_correct = final_answer == bucket["gold"]
                final_is_target_wrong = bool(bucket["target_wrong"]) and final_answer == bucket["target_wrong"]
                if initial_has_correct and final_is_target_wrong:
                    collapse += 1
                if initial_has_correct and not final_is_correct:
                    correct_lost += 1
                if final_is_target_wrong:
                    target_wrong_conv += 1
            summary["correct_to_wrong_collapse_rate"] = collapse / eligible if eligible else 0.0
            summary["correct_initial_lost_rate"] = correct_lost / eligible if eligible else 0.0
            summary["target_wrong_convergence_rate"] = target_wrong_conv / eligible if eligible else 0.0
        summary = _finalize(summary, answers)
        by_condition[condition] = summary

    baseline = by_condition["independent"]
    full_context = by_condition["full_context_debate"]
    condition_effects = {
        "full_context_minus_independent_delta_target_wrong": full_context["target_wrong_rate"] - baseline["target_wrong_rate"],
        "answer_hidden_minus_full_context_delta_target_wrong": by_condition["answer_hidden_debate"]["target_wrong_rate"] - full_context["target_wrong_rate"],
        "numeric_masked_minus_full_context_delta_target_wrong": by_condition["numeric_masked_debate"]["target_wrong_rate"] - full_context["target_wrong_rate"],
        "commit_then_numeric_masked_minus_full_context_delta_target_wrong": by_condition["commit_then_numeric_masked_debate"]["target_wrong_rate"] - full_context["target_wrong_rate"],
    }

    summary = {
        "n": len(raw_rows),
        "accuracy": baseline["correct_rate"],
        "oracle_at_k": max(summary["correct_rate"] for summary in by_condition.values()) if by_condition else 0.0,
        "answer_loss_rate": 1.0 - baseline["correct_rate"],
        "same_error_agreement_rate": 0.0,
        "diversity_drop": 0.0,
        "extraction_failure_rate": baseline["effective_extraction_failure_rate"],
        "skipped_raw_ids": skipped_raw_ids,
    }
    if history_available:
        summary["same_error_agreement_rate"] = sum(1 for answers in history_buckets.values() if answers and len({normalize_answer(r.get("final_answer", "")) for r in answers}) == 1) / len(history_buckets) if history_buckets else 0.0
        summary["diversity_drop"] = 0.0

    return {
        "summary": summary,
        "by_condition": by_condition,
        "condition_effects": condition_effects,
    }


def write_markdown(report: dict[str, Any], out_path: Path) -> None:
    lines = [
        "# GSM8K Phase 4 Mitigation Diagnostic",
        "",
        "Caution: this is exploratory and diagnostic, not a safety proof or benchmark-level claim.",
        "",
        "## Summary",
        "",
        f"- n: {report['summary']['n']}",
        f"- accuracy: {report['summary']['accuracy']}",
        f"- oracle_at_k: {report['summary']['oracle_at_k']}",
        f"- answer_loss_rate: {report['summary']['answer_loss_rate']}",
        "",
        "## By Condition",
        "",
        "| condition | correct_rate | target_wrong_rate | extraction_failure_rate | history_metrics_available |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for condition in CONDITION_ORDER:
        summary = report["by_condition"][condition]
        lines.append(
            f"| {condition} | {summary['correct_rate']:.3f} | {summary['target_wrong_rate']:.3f} | {summary['effective_extraction_failure_rate']:.3f} | {summary['history_metrics_available']} |"
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
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a GSM8K Phase 4 mitigation diagnostic.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()
    report = analyze_phase4_mitigation(data_path=Path(args.data), raw_path=Path(args.raw))
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
