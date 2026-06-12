from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_synthetic_prefix_phase2_dataset import CONDITION_ORDER  # noqa: E402
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


def _empty_condition_summary(condition: str) -> dict[str, Any]:
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
        "delta_correct_vs_baseline": None,
        "delta_target_wrong_vs_baseline": None,
        "delta_entropy_vs_baseline": None,
    }


def _comparison(left: str, right: str, by_condition: dict[str, dict[str, Any]]) -> dict[str, Any]:
    left_summary = by_condition.get(left, _empty_condition_summary(left))
    right_summary = by_condition.get(right, _empty_condition_summary(right))
    return {
        "left": left,
        "right": right,
        "delta_correct_rate": left_summary["correct_rate"] - right_summary["correct_rate"],
        "delta_target_wrong_rate": left_summary["target_wrong_rate"] - right_summary["target_wrong_rate"],
        "delta_entropy": left_summary["answer_entropy"] - right_summary["answer_entropy"],
    }


def analyze_synthetic_prefix_phase2(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
    data_rows = load_jsonl(data_path)
    raw_rows = load_jsonl(raw_path)
    data_by_id = {str(row["id"]): row for row in data_rows if "id" in row}

    grouped_answers: dict[str, list[str]] = {}
    grouped_totals: dict[str, int] = {}
    grouped_failures: dict[str, int] = {}
    grouped_gold: dict[str, str] = {}
    grouped_target_wrong: dict[str, str] = {}
    skipped_raw_ids: list[str] = []

    for raw_row in raw_rows:
        row_id = str(raw_row.get("id", ""))
        data_row = data_by_id.get(row_id)
        if data_row is None:
            skipped_raw_ids.append(row_id)
            continue

        metadata = _metadata(data_row)
        condition = str(metadata.get("condition", "unknown"))
        gold = normalize_answer(metadata.get("gold", data_row.get("answer", "")))
        target_wrong = normalize_answer(metadata.get("target_wrong_answer", ""))

        grouped_answers.setdefault(condition, [])
        grouped_totals.setdefault(condition, 0)
        grouped_failures.setdefault(condition, 0)
        grouped_gold[condition] = gold
        grouped_target_wrong[condition] = target_wrong

        for entry in _response_entries(raw_row):
            grouped_totals[condition] += 1
            if bool(entry.get("extraction_failed", False)):
                grouped_failures[condition] += 1
                continue
            answer = normalize_answer(entry.get("answer", ""))
            if answer == "":
                grouped_failures[condition] += 1
                continue
            grouped_answers[condition].append(answer)

    conditions = list(CONDITION_ORDER)
    by_condition: dict[str, dict[str, Any]] = {}
    for condition in conditions:
        answers = grouped_answers.get(condition, [])
        total = grouped_totals.get(condition, 0)
        failures = grouped_failures.get(condition, 0)
        non_failed = len(answers)
        gold = grouped_gold.get(condition, "")
        target_wrong = grouped_target_wrong.get(condition, "")
        correct_count = sum(1 for answer in answers if answer == gold)
        target_wrong_count = sum(1 for answer in answers if answer == target_wrong)
        other_count = non_failed - correct_count - target_wrong_count
        answer_counts = dict(sorted(Counter(answers).items()))

        summary = _empty_condition_summary(condition)
        summary.update(
            {
                "n_outputs": total,
                "non_failed_outputs": non_failed,
                "correct_count": correct_count,
                "target_wrong_count": target_wrong_count,
                "other_count": other_count,
                "extraction_failure_count": failures,
                "correct_rate": correct_count / non_failed if non_failed else 0.0,
                "target_wrong_rate": target_wrong_count / non_failed if non_failed else 0.0,
                "other_rate": other_count / non_failed if non_failed else 0.0,
                "extraction_failure_rate": failures / total if total else 0.0,
                "unique_answer_count": len(answer_counts),
                "answer_entropy": _entropy(answers),
                "answer_counts": answer_counts,
            }
        )
        by_condition[condition] = summary

    baseline = by_condition.get("baseline_no_prefix", _empty_condition_summary("baseline_no_prefix"))
    for summary in by_condition.values():
        if summary["n_outputs"] == 0 or baseline["n_outputs"] == 0:
            continue
        summary["delta_correct_vs_baseline"] = summary["correct_rate"] - baseline["correct_rate"]
        summary["delta_target_wrong_vs_baseline"] = summary["target_wrong_rate"] - baseline["target_wrong_rate"]
        summary["delta_entropy_vs_baseline"] = summary["answer_entropy"] - baseline["answer_entropy"]

    comparisons = {
        "single_round_correct_consensus_vs_baseline": _comparison(
            "single_round_correct_consensus",
            "baseline_no_prefix",
            by_condition,
        ),
        "single_round_wrong_majority_vs_baseline": _comparison(
            "single_round_wrong_majority",
            "baseline_no_prefix",
            by_condition,
        ),
        "single_round_wrong_consensus_vs_wrong_majority": _comparison(
            "single_round_wrong_consensus",
            "single_round_wrong_majority",
            by_condition,
        ),
        "single_round_correct_majority_vs_wrong_majority": _comparison(
            "single_round_correct_majority",
            "single_round_wrong_majority",
            by_condition,
        ),
        "trajectory_forward_vs_baseline": _comparison("trajectory_forward", "baseline_no_prefix", by_condition),
        "trajectory_reversed_vs_baseline": _comparison("trajectory_reversed", "baseline_no_prefix", by_condition),
        "trajectory_forward_vs_reversed": _comparison("trajectory_forward", "trajectory_reversed", by_condition),
    }

    labels = _qualitative_labels(by_condition)

    return {
        "data": str(data_path),
        "raw": str(raw_path),
        "conditions": conditions,
        "by_condition": by_condition,
        "planned_comparisons": comparisons,
        "summary": {
            "qualitative_labels": labels,
            "skipped_raw_ids": skipped_raw_ids,
        },
    }


def _qualitative_labels(by_condition: dict[str, dict[str, Any]]) -> list[str]:
    labels: list[str] = []
    baseline = by_condition.get("baseline_no_prefix", _empty_condition_summary("baseline_no_prefix"))
    single_round_correct_consensus = by_condition.get("single_round_correct_consensus")
    single_round_wrong_majority = by_condition.get("single_round_wrong_majority")
    single_round_wrong_consensus = by_condition.get("single_round_wrong_consensus")
    trajectory_forward = by_condition.get("trajectory_forward")
    trajectory_reversed = by_condition.get("trajectory_reversed")

    if baseline["target_wrong_rate"] >= 0.30:
        labels.append("shared_prior_possible")

    if single_round_correct_consensus and single_round_correct_consensus["correct_rate"] >= baseline["correct_rate"] + 0.10:
        labels.append("correct_consensus_anchor_consistent")

    if single_round_wrong_majority and single_round_wrong_majority["target_wrong_rate"] >= baseline["target_wrong_rate"] + 0.10:
        labels.append("wrong_majority_anchor_consistent")

    if (
        single_round_wrong_consensus
        and single_round_wrong_majority
        and single_round_wrong_consensus["target_wrong_rate"] >= single_round_wrong_majority["target_wrong_rate"] + 0.10
    ):
        labels.append("wrong_consensus_stronger_than_wrong_majority")

    if trajectory_forward and trajectory_reversed:
        if (
            trajectory_forward["target_wrong_rate"] >= trajectory_reversed["target_wrong_rate"] + 0.10
            or trajectory_reversed["correct_rate"] >= trajectory_forward["correct_rate"] + 0.10
        ):
            labels.append("recency_order_consistent")
        if (
            trajectory_forward["target_wrong_rate"] >= trajectory_reversed["target_wrong_rate"] + 0.10
            or trajectory_forward["correct_rate"] >= trajectory_reversed["correct_rate"] + 0.10
            or trajectory_reversed["target_wrong_rate"] >= trajectory_forward["target_wrong_rate"] + 0.10
            or trajectory_reversed["correct_rate"] >= trajectory_forward["correct_rate"] + 0.10
        ):
            labels.append("frequency_without_recency_insufficient")

    if not labels:
        labels.append("inconclusive")
    return labels


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# GSM8K 000234 Synthetic Prefix Phase 2 Analysis")
    lines.append("")
    lines.append("Caution: this is a single-item diagnostic with repeated stochastic prompt samples; it is not benchmark-level evidence and does not provide causal proof.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- qualitative_labels: `{', '.join(report['summary']['qualitative_labels'])}`")
    lines.append("")
    lines.append("## By Condition")
    lines.append("")
    lines.append(
        "| condition | n_outputs | correct_rate | target_wrong_rate | other_rate | extraction_failure_rate | unique_answer_count | answer_entropy |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for condition in report["conditions"]:
        summary = report["by_condition"][condition]
        lines.append(
            f"| {condition} | {summary['n_outputs']} | {summary['correct_rate']} | {summary['target_wrong_rate']} | {summary['other_rate']} | {summary['extraction_failure_rate']} | {summary['unique_answer_count']} | {summary['answer_entropy']} |"
        )
    lines.append("")
    lines.append("## Planned Comparisons")
    lines.append("")
    lines.append("| comparison | left | right | delta_correct_rate | delta_target_wrong_rate | delta_entropy |")
    lines.append("| --- | --- | --- | ---: | ---: | ---: |")
    for name, comparison in report["planned_comparisons"].items():
        lines.append(
            f"| {name} | {comparison['left']} | {comparison['right']} | {comparison['delta_correct_rate']} | {comparison['delta_target_wrong_rate']} | {comparison['delta_entropy']} |"
        )
    lines.append("")
    lines.append("## Interpretation Guide")
    lines.append("")
    lines.append("- If wrong majority > baseline, that is consistent with an anchor/majority effect.")
    lines.append("- If wrong consensus > wrong majority, that is consistent with an unanimity increment.")
    lines.append("- If trajectory forward > reversed for wrong answer, that is consistent with a recency/order effect.")
    lines.append("- If forward and reversed are similar, frequency may dominate over order, or the order effect may be weak.")
    lines.append("- If baseline is already wrong-heavy, shared-prior possible.")
    lines.append("")
    lines.append("No raw model text is included in this report.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a synthetic-prefix phase 2 run.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    report = analyze_synthetic_prefix_phase2(data_path=Path(args.data), raw_path=Path(args.raw))
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
