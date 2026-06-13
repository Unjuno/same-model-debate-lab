from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_synthetic_prefix_phase2b_dataset import CONDITION_ORDER  # noqa: E402
from tools.select_partial_correct_items import normalize_answer  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata", {})
    return metadata if isinstance(metadata, dict) else {}


def _response_entries(row: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("final_raw", "initial_raw"):
        value = row.get(key)
        if isinstance(value, list):
            return [entry for entry in value if isinstance(entry, dict)]
    return []


def _entropy(values: list[str]) -> float:
    if not values:
        return 0.0
    counts = Counter(values)
    total = len(values)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _base_condition_summary(condition: str) -> dict[str, Any]:
    return {
        "condition": condition,
        "n_outputs": 0,
        "non_failed_outputs": 0,
        "correct_count": 0,
        "target_wrong_count": 0,
        "other_count": 0,
        "extraction_failure_count": 0,
        "correct_rate": 0.0,
        "target_wrong_rate": 0.0,
        "other_rate": 0.0,
        "extraction_failure_rate": 0.0,
        "unique_answer_count": 0,
        "answer_entropy": 0.0,
        "answer_counts": {},
    }


def _summarize_answers(condition: str, answers: list[str], total: int, failures: int, gold: str, target_wrong: str) -> dict[str, Any]:
    correct_count = sum(1 for answer in answers if answer == gold)
    target_wrong_count = sum(1 for answer in answers if answer == target_wrong)
    other_count = len(answers) - correct_count - target_wrong_count
    answer_counts = dict(sorted(Counter(answers).items()))
    summary = _base_condition_summary(condition)
    summary.update(
        {
            "n_outputs": total,
            "non_failed_outputs": len(answers),
            "correct_count": correct_count,
            "target_wrong_count": target_wrong_count,
            "other_count": other_count,
            "extraction_failure_count": failures,
            "correct_rate": correct_count / len(answers) if answers else 0.0,
            "target_wrong_rate": target_wrong_count / len(answers) if answers else 0.0,
            "other_rate": other_count / len(answers) if answers else 0.0,
            "extraction_failure_rate": failures / total if total else 0.0,
            "unique_answer_count": len(answer_counts),
            "answer_entropy": _entropy(answers),
            "answer_counts": answer_counts,
        }
    )
    return summary


def _comparison(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "left": left["condition"],
        "right": right["condition"],
        "delta_correct_rate": left["correct_rate"] - right["correct_rate"],
        "delta_target_wrong_rate": left["target_wrong_rate"] - right["target_wrong_rate"],
        "delta_entropy": left["answer_entropy"] - right["answer_entropy"],
    }


def analyze_synthetic_prefix_phase2b(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
    data_rows = load_jsonl(data_path)
    raw_rows = load_jsonl(raw_path)
    data_by_id = {str(row["id"]): row for row in data_rows if "id" in row}

    skipped_raw_ids: list[str] = []
    by_item_condition: dict[str, dict[str, dict[str, Any]]] = {}
    aggregate_answers: dict[str, list[str]] = {condition: [] for condition in CONDITION_ORDER}
    aggregate_totals: dict[str, int] = {condition: 0 for condition in CONDITION_ORDER}
    aggregate_failures: dict[str, int] = {condition: 0 for condition in CONDITION_ORDER}
    aggregate_correct: dict[str, int] = {condition: 0 for condition in CONDITION_ORDER}
    aggregate_target_wrong_count: dict[str, int] = {condition: 0 for condition in CONDITION_ORDER}
    aggregate_other_count: dict[str, int] = {condition: 0 for condition in CONDITION_ORDER}
    items: list[str] = []

    for raw_row in raw_rows:
        row_id = str(raw_row.get("id", ""))
        data_row = data_by_id.get(row_id)
        if data_row is None:
            skipped_raw_ids.append(row_id)
            continue

        metadata = _metadata(data_row)
        item_id = str(metadata.get("base_item_id", ""))
        condition = str(metadata.get("condition", "unknown"))
        gold = normalize_answer(metadata.get("gold", data_row.get("answer", "")))
        target_wrong = normalize_answer(metadata.get("target_wrong_answer", ""))

        if item_id and item_id not in items:
            items.append(item_id)

        answers: list[str] = []
        total = 0
        failures = 0
        for entry in _response_entries(raw_row):
            total += 1
            if bool(entry.get("extraction_failed", False)):
                failures += 1
                continue
            answer = normalize_answer(entry.get("answer", ""))
            if answer == "":
                failures += 1
                continue
            answers.append(answer)
            aggregate_answers[condition].append(answer)
            if answer == gold:
                aggregate_correct[condition] += 1
            elif answer == target_wrong:
                aggregate_target_wrong_count[condition] += 1
            else:
                aggregate_other_count[condition] += 1
        aggregate_totals[condition] += total
        aggregate_failures[condition] += failures

        by_item_condition.setdefault(item_id, {})[condition] = _summarize_answers(
            condition,
            answers,
            total,
            failures,
            gold,
            target_wrong,
        )

    aggregate_by_condition: dict[str, dict[str, Any]] = {}
    for condition in CONDITION_ORDER:
        non_failed = len(aggregate_answers[condition])
        summary = _base_condition_summary(condition)
        summary.update(
            {
                "n_outputs": aggregate_totals[condition],
                "non_failed_outputs": non_failed,
                "correct_count": aggregate_correct[condition],
                "target_wrong_count": aggregate_target_wrong_count[condition],
                "other_count": aggregate_other_count[condition],
                "extraction_failure_count": aggregate_failures[condition],
                "correct_rate": aggregate_correct[condition] / non_failed if non_failed else 0.0,
                "target_wrong_rate": aggregate_target_wrong_count[condition] / non_failed if non_failed else 0.0,
                "other_rate": aggregate_other_count[condition] / non_failed if non_failed else 0.0,
                "extraction_failure_rate": aggregate_failures[condition] / aggregate_totals[condition]
                if aggregate_totals[condition]
                else 0.0,
                "unique_answer_count": len(Counter(aggregate_answers[condition])),
                "answer_entropy": _entropy(aggregate_answers[condition]),
                "answer_counts": dict(sorted(Counter(aggregate_answers[condition]).items())),
            }
        )
        aggregate_by_condition[condition] = summary
        aggregate_by_condition[condition]["item_count"] = len(
            [1 for item_map in by_item_condition.values() if condition in item_map]
        )

    items = sorted(items)

    for item_id in items:
        item_map = by_item_condition.setdefault(item_id, {})
        for condition in CONDITION_ORDER:
            item_map.setdefault(condition, _base_condition_summary(condition))

    item_effects: dict[str, dict[str, float | bool]] = {}
    for item_id in items:
        baseline = by_item_condition[item_id]["baseline_no_prefix"]
        correct_consensus = by_item_condition[item_id]["single_round_correct_consensus"]
        correct_majority = by_item_condition[item_id]["single_round_correct_majority"]
        wrong_majority = by_item_condition[item_id]["single_round_wrong_majority"]
        wrong_consensus = by_item_condition[item_id]["single_round_wrong_consensus"]
        item_effects[item_id] = {
            "correct_consensus_delta_correct": correct_consensus["correct_rate"] - baseline["correct_rate"],
            "correct_majority_delta_correct": correct_majority["correct_rate"] - baseline["correct_rate"],
            "wrong_majority_delta_wrong": wrong_majority["target_wrong_rate"] - baseline["target_wrong_rate"],
            "wrong_consensus_delta_wrong": wrong_consensus["target_wrong_rate"] - baseline["target_wrong_rate"],
            "wrong_consensus_minus_wrong_majority_delta_wrong": wrong_consensus["target_wrong_rate"] - wrong_majority["target_wrong_rate"],
            "correct_consensus_entropy_delta": correct_consensus["answer_entropy"] - baseline["answer_entropy"],
            "wrong_consensus_entropy_delta": wrong_consensus["answer_entropy"] - baseline["answer_entropy"],
            "correct_consensus_anchor_positive": correct_consensus["correct_rate"] - baseline["correct_rate"] >= 0.10,
            "correct_majority_anchor_positive": correct_majority["correct_rate"] - baseline["correct_rate"] >= 0.10,
            "wrong_majority_anchor_positive": wrong_majority["target_wrong_rate"] - baseline["target_wrong_rate"] >= 0.10,
            "wrong_consensus_anchor_positive": wrong_consensus["target_wrong_rate"] - baseline["target_wrong_rate"] >= 0.10,
            "wrong_consensus_stronger_than_wrong_majority": wrong_consensus["target_wrong_rate"] - wrong_majority["target_wrong_rate"] >= 0.10,
            "baseline_wrong_heavy": baseline["target_wrong_rate"] >= 0.50,
            "baseline_correct_heavy": baseline["correct_rate"] >= 0.70,
            "baseline_mixed": baseline["correct_rate"] >= 0.30 and baseline["target_wrong_rate"] >= 0.30,
        }

    def summarize_numeric(values: list[float]) -> dict[str, Any]:
        return {
            "mean": mean(values) if values else 0.0,
            "median": median(values) if values else 0.0,
            "min": min(values) if values else 0.0,
            "max": max(values) if values else 0.0,
            "positive_count": sum(1 for value in values if value > 0),
            "negative_count": sum(1 for value in values if value < 0),
            "zero_count": sum(1 for value in values if value == 0),
        }

    effect_summaries: dict[str, dict[str, Any]] = {}
    for metric in [
        "correct_consensus_delta_correct",
        "correct_majority_delta_correct",
        "wrong_majority_delta_wrong",
        "wrong_consensus_delta_wrong",
        "wrong_consensus_minus_wrong_majority_delta_wrong",
        "correct_consensus_entropy_delta",
        "wrong_consensus_entropy_delta",
    ]:
        values = [float(item_effects[item_id][metric]) for item_id in items]
        effect_summaries[metric] = summarize_numeric(values)

    indicator_counts: dict[str, int] = {}
    for metric in [
        "correct_consensus_anchor_positive",
        "correct_majority_anchor_positive",
        "wrong_majority_anchor_positive",
        "wrong_consensus_anchor_positive",
        "wrong_consensus_stronger_than_wrong_majority",
        "baseline_wrong_heavy",
        "baseline_correct_heavy",
        "baseline_mixed",
    ]:
        indicator_counts[metric] = sum(1 for item_id in items if item_effects[item_id][metric])

    labels: list[str] = []
    if indicator_counts["baseline_wrong_heavy"] >= max(1, math.ceil(0.25 * len(items))):
        labels.append("shared_prior_common")
    if indicator_counts["correct_consensus_anchor_positive"] >= math.ceil(0.5 * len(items)):
        labels.append("correct_consensus_anchor_common")
    if indicator_counts["wrong_consensus_anchor_positive"] >= math.ceil(0.5 * len(items)):
        labels.append("wrong_consensus_anchor_common")
    if indicator_counts["wrong_consensus_stronger_than_wrong_majority"] >= math.ceil(0.5 * len(items)):
        labels.append("wrong_consensus_stronger_than_wrong_majority_common")
    mean_wrong_consensus = effect_summaries["wrong_consensus_delta_wrong"]["mean"]
    mean_wrong_majority = effect_summaries["wrong_majority_delta_wrong"]["mean"]
    mean_correct_consensus = effect_summaries["correct_consensus_delta_correct"]["mean"]
    mean_correct_majority = effect_summaries["correct_majority_delta_correct"]["mean"]
    if mean_wrong_consensus > mean_wrong_majority and mean_correct_consensus > mean_correct_majority:
        labels.append("majority_effect_weaker_than_consensus")
    if not labels:
        labels.append("inconclusive")

    return {
        "phase": "phase2b_multi_item",
        "data": str(data_path),
        "raw": str(raw_path),
        "items": items,
        "conditions": CONDITION_ORDER,
        "by_item_condition": by_item_condition,
        "aggregate_by_condition": aggregate_by_condition,
        "item_effects": item_effects,
        "effect_summaries": effect_summaries,
        "indicator_counts": indicator_counts,
        "summary": {
            "n_items": len(items),
            "n_conditions": len(CONDITION_ORDER),
            "n_outputs": len(raw_rows) * 3,
            "skipped_raw_ids": skipped_raw_ids,
            "qualitative_labels": labels,
        },
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# GSM8K Synthetic Prefix Phase 2b Multi-Item Analysis")
    lines.append("")
    lines.append("Caution:")
    lines.append("- exploratory diagnostic")
    lines.append("- repeated stochastic prompt samples")
    lines.append("- not independent benchmark items")
    lines.append("- no causal proof")
    lines.append("- no statistical-significance claim")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- qualitative_labels: `{', '.join(report['summary']['qualitative_labels'])}`")
    lines.append("")
    lines.append("## Aggregate by Condition")
    lines.append("")
    lines.append(
        "| condition | n_outputs | non_failed_outputs | correct_count | target_wrong_count | other_count | extraction_failure_count | correct_rate | target_wrong_rate | other_rate | extraction_failure_rate | unique_answer_count | answer_entropy |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for condition in report["conditions"]:
        summary = report["aggregate_by_condition"][condition]
        lines.append(
            f"| {condition} | {summary['n_outputs']} | {summary['non_failed_outputs']} | {summary['correct_count']} | {summary['target_wrong_count']} | {summary['other_count']} | {summary['extraction_failure_count']} | {summary['correct_rate']} | {summary['target_wrong_rate']} | {summary['other_rate']} | {summary['extraction_failure_rate']} | {summary['unique_answer_count']} | {summary['answer_entropy']} |"
        )
    lines.append("")
    lines.append("## Effect Summaries")
    lines.append("")
    lines.append("| metric | mean | median | min | max | positive_count | negative_count | zero_count |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for metric, summary in report["effect_summaries"].items():
        lines.append(
            f"| {metric} | {summary['mean']} | {summary['median']} | {summary['min']} | {summary['max']} | {summary['positive_count']} | {summary['negative_count']} | {summary['zero_count']} |"
        )
    lines.append("")
    lines.append("## Indicator Counts")
    lines.append("")
    lines.append("| indicator | count |")
    lines.append("| --- | ---: |")
    for metric, count in report["indicator_counts"].items():
        lines.append(f"| {metric} | {count} |")
    lines.append("")
    lines.append("## Item-Level Effects")
    lines.append("")
    lines.append("| item_id | correct_consensus_delta_correct | correct_majority_delta_correct | wrong_majority_delta_wrong | wrong_consensus_delta_wrong | wrong_consensus_minus_wrong_majority_delta_wrong | correct_consensus_entropy_delta | wrong_consensus_entropy_delta |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for item_id in report["items"]:
        effects = report["item_effects"][item_id]
        lines.append(
            f"| {item_id} | {effects['correct_consensus_delta_correct']} | {effects['correct_majority_delta_correct']} | {effects['wrong_majority_delta_wrong']} | {effects['wrong_consensus_delta_wrong']} | {effects['wrong_consensus_minus_wrong_majority_delta_wrong']} | {effects['correct_consensus_entropy_delta']} | {effects['wrong_consensus_entropy_delta']} |"
        )
    lines.append("")
    lines.append("## Interpretation Guide")
    lines.append("")
    lines.append("- If wrong majority exceeds baseline, that is consistent with an anchor/majority effect.")
    lines.append("- If wrong consensus exceeds wrong majority, that is consistent with a unanimity increment.")
    lines.append("- If trajectory-like differences appear after pooling, that is consistent with an order/recency effect.")
    lines.append("- If forward and reversed are similar, frequency may dominate over order, or the order effect may be weak.")
    lines.append("- If baseline is already wrong-heavy, shared-prior possible.")
    lines.append("")
    lines.append("No raw model text is included.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a synthetic-prefix phase 2b run.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    report = analyze_synthetic_prefix_phase2b(data_path=Path(args.data), raw_path=Path(args.raw))
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
