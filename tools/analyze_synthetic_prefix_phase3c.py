from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_synthetic_prefix_phase3c_dataset import CONDITION_ORDER  # noqa: E402
from tools.select_partial_correct_items import normalize_answer  # noqa: E402

NUMERIC_RE = re.compile(r"^-?\d[\d,]*(?:\.\d+)?$")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata", {})
    return metadata if isinstance(metadata, dict) else {}


def _validate_raw_row(row: dict[str, Any], row_id: str) -> None:
    missing = [key for key in ("id", "final_answer", "initial_answers") if key not in row]
    if missing:
        raise KeyError(f"raw row {row_id} missing required keys: {', '.join(sorted(missing))}")


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
    }


def _item_group(item_id: str) -> str:
    if item_id in {"gsm8k_test_000241", "gsm8k_test_000187", "gsm8k_test_000147"}:
        return "rationale_contamination_positive"
    if item_id in {"gsm8k_test_000089", "gsm8k_test_000234", "gsm8k_test_000093"}:
        return "rationale_corrective_reversal"
    return "numeric_anchor_dominant"


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


def _aggregate_group(grouped: dict[tuple[str, str], list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    aggregated: dict[str, dict[str, Any]] = {}
    for (group_or_format, condition), summaries in grouped.items():
        summary = _empty(condition)
        answers: list[str] = []
        for item_summary in summaries:
            summary["n_outputs"] += item_summary["n_outputs"]
            summary["non_failed_outputs"] += item_summary["non_failed_outputs"]
            summary["correct_count"] += item_summary["correct_count"]
            summary["target_wrong_count"] += item_summary["target_wrong_count"]
            summary["other_count"] += item_summary["other_count"]
            summary["raw_extraction_failure_count"] += item_summary["raw_extraction_failure_count"]
            summary["effective_extraction_failure_count"] += item_summary["effective_extraction_failure_count"]
            answers.extend(item_summary.get("_answers", []))
        aggregated[f"{group_or_format}__{condition}"] = _finalize(summary, answers)
    return aggregated


def _summary_effects(by_condition: dict[str, dict[str, Any]]) -> dict[str, float]:
    def get(condition: str) -> dict[str, Any]:
        return by_condition.get(condition, _empty(condition))

    baseline = get("baseline_no_prefix")
    labeled = get("wrong_answer_labeled")
    unlabeled = get("wrong_number_unlabeled")
    explanation = get("wrong_number_in_explanation")
    intermediate = get("wrong_number_as_intermediate")
    uncertainty = get("wrong_answer_with_uncertainty")
    possibly_wrong = get("wrong_answer_marked_possibly_wrong")
    return {
        "wrong_answer_labeled_delta_target_wrong": labeled["target_wrong_rate"] - baseline["target_wrong_rate"],
        "wrong_number_unlabeled_delta_target_wrong": unlabeled["target_wrong_rate"] - baseline["target_wrong_rate"],
        "wrong_number_in_explanation_delta_target_wrong": explanation["target_wrong_rate"] - baseline["target_wrong_rate"],
        "wrong_number_as_intermediate_delta_target_wrong": intermediate["target_wrong_rate"] - baseline["target_wrong_rate"],
        "wrong_answer_with_uncertainty_delta_target_wrong": uncertainty["target_wrong_rate"] - baseline["target_wrong_rate"],
        "wrong_answer_marked_possibly_wrong_delta_target_wrong": possibly_wrong["target_wrong_rate"] - baseline["target_wrong_rate"],
        "unlabeled_minus_labeled_delta_target_wrong": unlabeled["target_wrong_rate"] - labeled["target_wrong_rate"],
        "explanation_minus_labeled_delta_target_wrong": explanation["target_wrong_rate"] - labeled["target_wrong_rate"],
        "intermediate_minus_labeled_delta_target_wrong": intermediate["target_wrong_rate"] - labeled["target_wrong_rate"],
        "uncertainty_minus_labeled_delta_target_wrong": uncertainty["target_wrong_rate"] - labeled["target_wrong_rate"],
        "possibly_wrong_minus_labeled_delta_target_wrong": possibly_wrong["target_wrong_rate"] - labeled["target_wrong_rate"],
    }


def _effects_by_scope(scoped: dict[str, dict[str, Any]]) -> dict[str, float]:
    return _summary_effects(scoped)


def analyze_synthetic_prefix_phase3c(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
    data_rows = load_jsonl(data_path)
    raw_rows = load_jsonl(raw_path)
    data_by_id = {str(row["id"]): row for row in data_rows if "id" in row}
    skipped_raw_ids: list[str] = []
    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"answers": [], "raw_failures": 0, "total": 0, "metadata": {}})
    for raw_row in raw_rows:
        row_id = str(raw_row.get("id", ""))
        data_row = data_by_id.get(row_id)
        if data_row is None:
            skipped_raw_ids.append(row_id)
            continue
        _validate_raw_row(raw_row, row_id)
        metadata = _metadata(data_row)
        condition = str(metadata.get("condition", "unknown"))
        item_id = str(metadata.get("base_item_id", ""))
        bucket = grouped[(item_id, condition)]
        bucket["metadata"] = metadata
        bucket["gold"] = normalize_answer(metadata.get("gold", data_row.get("answer", "")))
        bucket["target_wrong"] = normalize_answer(metadata.get("target_wrong", ""))
        bucket["total"] += 1
        final_answer = normalize_answer(raw_row.get("final_answer", ""))
        if final_answer:
            bucket["answers"].append(final_answer)
        if int(raw_row.get("extraction_failures", 0)) > 0:
            bucket["raw_failures"] += 1

    by_condition = {condition: _empty(condition) for condition in CONDITION_ORDER}
    by_item_condition: dict[str, dict[str, Any]] = {}
    by_item_group_condition_buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_anchor_format_condition_buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    item_condition_answers: dict[str, list[str]] = defaultdict(list)

    for (item_id, condition), bucket in grouped.items():
        answers = bucket["answers"]
        summary = _empty(condition)
        summary["n_outputs"] = bucket["total"]
        summary["non_failed_outputs"] = len(answers)
        summary["correct_count"] = sum(1 for answer in answers if answer == bucket["gold"])
        summary["target_wrong_count"] = sum(1 for answer in answers if answer == bucket["target_wrong"])
        summary["other_count"] = summary["non_failed_outputs"] - summary["correct_count"] - summary["target_wrong_count"]
        summary["raw_extraction_failure_count"] = bucket["raw_failures"]
        summary["effective_extraction_failure_count"] = bucket["raw_failures"]
        summary["_answers"] = answers
        by_item_condition[f"{item_id}__{condition}"] = _finalize(summary, answers)
        by_condition[condition]["n_outputs"] += summary["n_outputs"]
        by_condition[condition]["non_failed_outputs"] += summary["non_failed_outputs"]
        by_condition[condition]["correct_count"] += summary["correct_count"]
        by_condition[condition]["target_wrong_count"] += summary["target_wrong_count"]
        by_condition[condition]["other_count"] += summary["other_count"]
        by_condition[condition]["raw_extraction_failure_count"] += summary["raw_extraction_failure_count"]
        by_condition[condition]["effective_extraction_failure_count"] += summary["effective_extraction_failure_count"]
        by_condition[condition].setdefault("_answers", []).extend(answers)
        item_condition_answers[item_id].extend(answers)
        group = _item_group(item_id)
        by_item_group_condition_buckets[(group, condition)].append(summary)
        anchor_format = str(bucket["metadata"].get("anchor_format", "none"))
        by_anchor_format_condition_buckets[(anchor_format, condition)].append(summary)

    for condition, summary in list(by_condition.items()):
        answers = summary.pop("_answers", [])
        by_condition[condition] = _finalize(summary, answers)

    by_item_group_condition = _aggregate_group(by_item_group_condition_buckets)
    by_anchor_format_condition = _aggregate_group(by_anchor_format_condition_buckets)

    item_effects: dict[str, dict[str, float]] = {}
    item_ids = sorted({key.split("__", 1)[0] for key in by_item_condition})
    for item_id in item_ids:
        scoped = {key.split("__", 1)[1]: value for key, value in by_item_condition.items() if key.startswith(f"{item_id}__")}
        if "baseline_no_prefix" in scoped:
            item_effects[item_id] = _effects_by_scope(scoped)

    item_group_effects: dict[str, dict[str, float]] = {}
    groups = sorted({key.split("__", 1)[0] for key in by_item_group_condition})
    for group in groups:
        scoped = {key.split("__", 1)[1]: value for key, value in by_item_group_condition.items() if key.startswith(f"{group}__")}
        if "baseline_no_prefix" in scoped:
            item_group_effects[group] = _effects_by_scope(scoped)

    anchor_format_effects: dict[str, dict[str, float]] = {}
    formats = sorted({key.split("__", 1)[0] for key in by_anchor_format_condition})
    for anchor_format in formats:
        scoped = {key.split("__", 1)[1]: value for key, value in by_anchor_format_condition.items() if key.startswith(f"{anchor_format}__")}
        if "baseline_no_prefix" in scoped:
            anchor_format_effects[anchor_format] = _effects_by_scope(scoped)

    condition_effects = _summary_effects(by_condition)
    labels: list[str] = []
    if condition_effects["wrong_answer_labeled_delta_target_wrong"] > 0.10:
        labels.append("numeric_anchor_consistent")
    if condition_effects["unlabeled_minus_labeled_delta_target_wrong"] < -0.10:
        labels.append("answer_label_framing_consistent")
    if condition_effects["wrong_number_unlabeled_delta_target_wrong"] > 0.10:
        labels.append("bare_number_anchor_consistent")
    if condition_effects["wrong_number_in_explanation_delta_target_wrong"] > 0.10:
        labels.append("explanation_number_anchor_consistent")
    if condition_effects["intermediate_minus_labeled_delta_target_wrong"] < -0.10:
        labels.append("intermediate_number_weaker_consistent")
    if condition_effects["uncertainty_minus_labeled_delta_target_wrong"] < -0.10:
        labels.append("uncertainty_reduces_anchor_consistent")
    if condition_effects["wrong_answer_marked_possibly_wrong_delta_target_wrong"] > 0.10:
        labels.append("warning_insufficient_consistent")
    spreads = []
    if item_group_effects:
        spreads = [
            max(effect.get("wrong_answer_labeled_delta_target_wrong", 0.0) for effect in item_group_effects.values())
            - min(effect.get("wrong_answer_labeled_delta_target_wrong", 0.0) for effect in item_group_effects.values()),
            max(effect.get("wrong_number_unlabeled_delta_target_wrong", 0.0) for effect in item_group_effects.values())
            - min(effect.get("wrong_number_unlabeled_delta_target_wrong", 0.0) for effect in item_group_effects.values()),
        ]
    # If item-group spreads exceed 0.10, the presentation format effect is visibly heterogeneous at this scale.
    if any(spread > 0.10 for spread in spreads):
        labels.append("item_group_heterogeneity_consistent")
    if not labels:
        labels = ["inconclusive"]

    summary = {
        "n": len(raw_rows),
        "accuracy": by_condition["baseline_no_prefix"]["correct_rate"],
        "oracle_at_k": max(condition["correct_rate"] for condition in by_condition.values()) if by_condition else 0.0,
        "answer_loss_rate": 1.0 - by_condition["baseline_no_prefix"]["correct_rate"],
        "same_error_agreement_rate": 0.0,
        "diversity_drop": 0.0,
        "extraction_failure_rate": by_condition["baseline_no_prefix"]["effective_extraction_failure_rate"],
        "qualitative_labels": labels,
        "skipped_raw_ids": skipped_raw_ids,
    }
    if item_condition_answers:
        same_error = 0
        for item_id, answers in item_condition_answers.items():
            if len(set(answers)) == 1:
                row = next(row for row in data_rows if str(row.get("metadata", {}).get("base_item_id", "")) == item_id)
                gold = normalize_answer(row.get("metadata", {}).get("gold", row.get("answer", "")))
                if answers[0] != gold:
                    same_error += 1
        summary["same_error_agreement_rate"] = same_error / len(item_condition_answers)

    return {
        "summary": summary,
        "by_condition": by_condition,
        "by_item_condition": by_item_condition,
        "by_item_group_condition": by_item_group_condition,
        "by_anchor_format_condition": by_anchor_format_condition,
        "condition_effects": condition_effects,
        "item_effects": item_effects,
        "item_group_effects": item_group_effects,
        "anchor_format_effects": anchor_format_effects,
    }


def _format_table(rows: list[list[Any]]) -> str:
    if not rows:
        return ""
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    lines = []
    for idx, row in enumerate(rows):
        lines.append("| " + " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)) + " |")
        if idx == 0:
            lines.append("| " + " | ".join("-" * widths[i] for i in range(len(widths))) + " |")
    return "\n".join(lines)


def write_markdown(report: dict[str, Any], out_path: Path) -> None:
    lines = [
        "# GSM8K Synthetic Prefix Phase 3c Numeric-Anchor Format Analysis",
        "Caution:",
        "- exploratory diagnostic",
        "- repeated stochastic prompt samples",
        "- not benchmark-level evidence",
        "- no causal proof",
        "- no statistical-significance claim",
        "## Summary",
        f"- qualitative_labels: `{', '.join(report['summary']['qualitative_labels'])}`",
        "## By Condition",
        _format_table([["condition", "correct_rate", "target_wrong_rate", "effective_failure"]] + [[c, f"{report['by_condition'][c]['correct_rate']:.3f}", f"{report['by_condition'][c]['target_wrong_rate']:.3f}", f"{report['by_condition'][c]['effective_extraction_failure_rate']:.3f}"] for c in CONDITION_ORDER]),
        "## Condition Effects",
        _format_table([["effect", "value"]] + [[k, f"{v:.3f}"] for k, v in report["condition_effects"].items()]),
        "## Item Group Effects",
        _format_table([["item_group", "wrong_answer_labeled_delta_target_wrong", "wrong_number_unlabeled_delta_target_wrong", "wrong_number_in_explanation_delta_target_wrong", "wrong_number_as_intermediate_delta_target_wrong", "wrong_answer_with_uncertainty_delta_target_wrong", "wrong_answer_marked_possibly_wrong_delta_target_wrong"]] + [[g, f"{v.get('wrong_answer_labeled_delta_target_wrong', 0.0):.3f}", f"{v.get('wrong_number_unlabeled_delta_target_wrong', 0.0):.3f}", f"{v.get('wrong_number_in_explanation_delta_target_wrong', 0.0):.3f}", f"{v.get('wrong_number_as_intermediate_delta_target_wrong', 0.0):.3f}", f"{v.get('wrong_answer_with_uncertainty_delta_target_wrong', 0.0):.3f}", f"{v.get('wrong_answer_marked_possibly_wrong_delta_target_wrong', 0.0):.3f}"] for g, v in report["item_group_effects"].items()]),
        "No raw model text is included.",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a GSM8K synthetic-prefix phase 3c dataset.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()
    report = analyze_synthetic_prefix_phase3c(data_path=Path(args.data), raw_path=Path(args.raw))
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))


if __name__ == "__main__":
    main()
