from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from numbers import Real
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_synthetic_prefix_continuation_dataset import CONDITION_ORDER  # noqa: E402
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

    for key in ("final_answers", "initial_answers"):
        value = row.get(key)
        if isinstance(value, list):
            return [{"answer": answer, "extraction_failed": False} for answer in value]

    if "final_answer" in row:
        return [{"answer": row.get("final_answer", ""), "extraction_failed": False}]

    return []


def _entropy(values: list[str]) -> float:
    if not values:
        return 0.0
    counts = Counter(values)
    total = len(values)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _condition_sort_key(condition: str) -> tuple[int, str]:
    try:
        return (CONDITION_ORDER.index(condition), condition)
    except ValueError:
        return (len(CONDITION_ORDER), condition)


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


def analyze_synthetic_prefix_continuation(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
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

    conditions = sorted(set(CONDITION_ORDER) | set(grouped_totals), key=_condition_sort_key)
    by_condition: dict[str, dict[str, Any]] = {}

    for condition in conditions:
        answers = grouped_answers.get(condition, [])
        total = grouped_totals.get(condition, 0)
        failures = grouped_failures.get(condition, 0)
        non_failed = len(answers)
        gold = grouped_gold.get(condition, "")
        target_wrong = grouped_target_wrong.get(condition, "")

        correct_count = sum(1 for answer in answers if answer == gold)
        target_wrong_count = sum(1 for answer in answers if target_wrong and answer == target_wrong)
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
        summary["delta_target_wrong_vs_baseline"] = (
            summary["target_wrong_rate"] - baseline["target_wrong_rate"]
        )
        summary["delta_entropy_vs_baseline"] = summary["answer_entropy"] - baseline["answer_entropy"]

    labels = _qualitative_labels(by_condition)

    return {
        "data": str(data_path),
        "raw": str(raw_path),
        "conditions": conditions,
        "by_condition": by_condition,
        "summary": {
            "baseline_correct_rate": baseline["correct_rate"],
            "baseline_target_wrong_rate": baseline["target_wrong_rate"],
            "prefix_wrong_majority_r2_target_wrong_delta": by_condition.get(
                "prefix_wrong_majority_r2", _empty_condition_summary("prefix_wrong_majority_r2")
            )["delta_target_wrong_vs_baseline"],
            "prefix_wrong_consensus_r3_target_wrong_delta": by_condition.get(
                "prefix_wrong_consensus_r3", _empty_condition_summary("prefix_wrong_consensus_r3")
            )["delta_target_wrong_vs_baseline"],
            "prefix_wrong_consensus_r3_entropy_delta": by_condition.get(
                "prefix_wrong_consensus_r3", _empty_condition_summary("prefix_wrong_consensus_r3")
            )["delta_entropy_vs_baseline"],
            "qualitative_labels": labels,
            "skipped_raw_ids": skipped_raw_ids,
        },
    }


def _meaningfully_positive(value: Any, *, threshold: float = 0.05) -> bool:
    return isinstance(value, Real) and value > threshold


def _near_flat(values: list[float], *, threshold: float = 0.05) -> bool:
    return bool(values) and max(values) - min(values) <= threshold


def _qualitative_labels(by_condition: dict[str, dict[str, Any]]) -> list[str]:
    labels: list[str] = []
    baseline = by_condition.get("baseline_no_prefix")
    if not baseline or baseline["n_outputs"] == 0:
        return ["inconclusive"]

    wrong_majority = by_condition.get("prefix_wrong_majority_r2")
    wrong_consensus = by_condition.get("prefix_wrong_consensus_r3")
    correct_consensus = by_condition.get("prefix_correct_consensus_r0")

    # `prefix_wrong_majority_r2` is a last-round wrong-majority / recency-weighted
    # condition, not a generic global majority condition.
    wrong_majority_delta = wrong_majority.get("delta_target_wrong_vs_baseline") if wrong_majority else None
    wrong_consensus_delta = wrong_consensus.get("delta_target_wrong_vs_baseline") if wrong_consensus else None

    if _meaningfully_positive(wrong_majority_delta) or _meaningfully_positive(wrong_consensus_delta):
        labels.append("context_attractor_consistent")

    if correct_consensus and correct_consensus["n_outputs"] > 0:
        correct_delta = correct_consensus.get("delta_correct_vs_baseline")
        if isinstance(correct_delta, Real) and correct_delta >= -0.05:
            labels.append("correct_anchor_consistent")

    if wrong_consensus and wrong_majority:
        if wrong_consensus["target_wrong_rate"] > wrong_majority["target_wrong_rate"] + 0.05:
            labels.append("wrong_consensus_fixation_consistent")

    if wrong_consensus:
        entropy_delta = wrong_consensus.get("delta_entropy_vs_baseline")
        other_delta = wrong_consensus["other_rate"] - baseline["other_rate"]
        unique_delta = wrong_consensus["unique_answer_count"] - baseline["unique_answer_count"]
        if _meaningfully_positive(entropy_delta) or other_delta > 0.05 or unique_delta > 0:
            labels.append("dispersion_consistent")

    condition_rates = [
        summary["target_wrong_rate"]
        for summary in by_condition.values()
        if summary["n_outputs"] > 0
    ]
    if _near_flat(condition_rates):
        labels.append("flat_no_answer_only_context_effect")

    if baseline["target_wrong_rate"] >= 0.3:
        labels.append("shared_prior_possible")

    if not labels:
        labels.append("inconclusive")
    return labels


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Synthetic Prefix Continuation Analysis")
    lines.append("")
    lines.append("This is a descriptive analysis of a one-step synthetic-prefix continuation run.")
    lines.append("It should not be read as a causal proof or a benchmark-level result.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- data: `{report['data']}`")
    lines.append(f"- raw: `{report['raw']}`")
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
            f"| {condition} | {summary['n_outputs']} | {summary['correct_rate']} | "
            f"{summary['target_wrong_rate']} | {summary['other_rate']} | "
            f"{summary['extraction_failure_rate']} | {summary['unique_answer_count']} | "
            f"{summary['answer_entropy']} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Answer rates use non-failed outputs as denominator.")
    lines.append("- `answer_entropy` is Shannon entropy over normalized non-failed answers, using log base 2.")
    lines.append("- No raw model text is included in this report.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a synthetic-prefix continuation run.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    report = analyze_synthetic_prefix_continuation(data_path=Path(args.data), raw_path=Path(args.raw))
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
