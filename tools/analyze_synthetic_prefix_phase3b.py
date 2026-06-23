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

from tools.build_synthetic_prefix_phase3b_dataset import CONDITION_ORDER  # noqa: E402
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
    if "id" not in row or "final_answer" not in row or "initial_answers" not in row:
        raise KeyError(f"raw row {row_id} missing required keys")


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


def analyze_synthetic_prefix_phase3b(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
    data_rows = load_jsonl(data_path)
    raw_rows = load_jsonl(raw_path)
    data_by_id = {str(row["id"]): row for row in data_rows if "id" in row}
    skipped_raw_ids: list[str] = []
    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"answers": [], "raw_failures": 0, "total": 0})
    by_item_condition: dict[str, dict[str, Any]] = {}
    by_item_group_condition: dict[str, dict[str, Any]] = {}
    by_strength_condition: dict[str, dict[str, Any]] = {}

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
        gold = normalize_answer(metadata.get("gold", data_row.get("answer", "")))
        target_wrong = normalize_answer(metadata.get("target_wrong", ""))
        bucket = grouped[(item_id, condition)]
        bucket.setdefault("gold", gold)
        bucket.setdefault("target_wrong", target_wrong)
        bucket["total"] += 1
        final_answer = normalize_answer(raw_row.get("final_answer", ""))
        if final_answer:
            bucket["answers"].append(final_answer)
        if int(raw_row.get("extraction_failures", 0)) > 0:
            bucket["raw_failures"] += 1

    by_condition = {condition: _empty(condition) for condition in CONDITION_ORDER}
    item_effects: dict[str, dict[str, float]] = {}
    item_group_effects: dict[str, dict[str, float]] = {}
    condition_answers: dict[str, list[str]] = defaultdict(list)
    condition_golds: dict[str, str] = {}
    condition_targets: dict[str, str] = {}

    for (item_id, condition), bucket in grouped.items():
        answers = bucket["answers"]
        summary = _empty(condition)
        summary.update(
            {
                "n_outputs": bucket["total"],
                "non_failed_outputs": len(answers),
                "correct_count": sum(1 for answer in answers if answer == bucket["gold"]),
                "target_wrong_count": sum(1 for answer in answers if answer == bucket["target_wrong"]),
                "raw_extraction_failure_count": bucket["raw_failures"],
                "effective_extraction_failure_count": bucket["raw_failures"],
                "answer_counts": dict(sorted(Counter(answers).items())),
            }
        )
        summary["other_count"] = summary["non_failed_outputs"] - summary["correct_count"] - summary["target_wrong_count"]
        summary["correct_rate"] = summary["correct_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
        summary["target_wrong_rate"] = summary["target_wrong_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
        summary["other_rate"] = summary["other_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
        summary["raw_extraction_failure_rate"] = summary["raw_extraction_failure_count"] / summary["n_outputs"] if summary["n_outputs"] else 0.0
        summary["effective_extraction_failure_rate"] = summary["effective_extraction_failure_count"] / summary["n_outputs"] if summary["n_outputs"] else 0.0
        summary["unique_answer_count"] = len(summary["answer_counts"])
        summary["answer_entropy"] = _entropy(answers)
        by_item_condition[f"{item_id}__{condition}"] = summary
        by_condition[condition]["n_outputs"] += summary["n_outputs"]
        by_condition[condition]["non_failed_outputs"] += summary["non_failed_outputs"]
        by_condition[condition]["correct_count"] += summary["correct_count"]
        by_condition[condition]["target_wrong_count"] += summary["target_wrong_count"]
        by_condition[condition]["other_count"] += summary["other_count"]
        by_condition[condition]["raw_extraction_failure_count"] += summary["raw_extraction_failure_count"]
        by_condition[condition]["effective_extraction_failure_count"] += summary["effective_extraction_failure_count"]
        condition_answers[condition].extend(answers)
        condition_golds.setdefault(condition, bucket["gold"])
        condition_targets.setdefault(condition, bucket["target_wrong"])
        item_group = _item_group(item_id)
        by_item_group_condition[f"{item_group}__{condition}"] = summary
        by_strength_condition[f"{metadata.get('rationale_strength', 'none')}__{condition}"] = summary

    for condition, summary in by_condition.items():
        answers = condition_answers[condition]
        summary["answer_counts"] = dict(sorted(Counter(answers).items()))
        summary["correct_rate"] = summary["correct_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
        summary["target_wrong_rate"] = summary["target_wrong_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
        summary["other_rate"] = summary["other_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
        summary["raw_extraction_failure_rate"] = summary["raw_extraction_failure_count"] / summary["n_outputs"] if summary["n_outputs"] else 0.0
        summary["effective_extraction_failure_rate"] = summary["effective_extraction_failure_count"] / summary["n_outputs"] if summary["n_outputs"] else 0.0
        summary["unique_answer_count"] = len(summary["answer_counts"])
        summary["answer_entropy"] = _entropy(answers)

    baseline = by_condition["baseline_no_prefix"]
    effects = {
        "wrong_answer_delta_target_wrong": by_condition["wrong_answer_only"]["target_wrong_rate"] - baseline["target_wrong_rate"],
        "weak_wrong_rationale_delta_target_wrong": by_condition["weak_wrong_rationale_only"]["target_wrong_rate"] - baseline["target_wrong_rate"],
        "medium_wrong_rationale_delta_target_wrong": by_condition["medium_wrong_rationale_only"]["target_wrong_rate"] - baseline["target_wrong_rate"],
        "strong_wrong_rationale_delta_target_wrong": by_condition["strong_wrong_rationale_only"]["target_wrong_rate"] - baseline["target_wrong_rate"],
        "medium_minus_weak_wrong_rationale_delta_target_wrong": by_condition["medium_wrong_rationale_only"]["target_wrong_rate"] - by_condition["weak_wrong_rationale_only"]["target_wrong_rate"],
        "strong_minus_weak_wrong_rationale_delta_target_wrong": by_condition["strong_wrong_rationale_only"]["target_wrong_rate"] - by_condition["weak_wrong_rationale_only"]["target_wrong_rate"],
        "strong_minus_medium_wrong_rationale_delta_target_wrong": by_condition["strong_wrong_rationale_only"]["target_wrong_rate"] - by_condition["medium_wrong_rationale_only"]["target_wrong_rate"],
        "weak_answer_plus_minus_wrong_answer_delta_target_wrong": by_condition["weak_wrong_answer_plus_rationale"]["target_wrong_rate"] - by_condition["wrong_answer_only"]["target_wrong_rate"],
        "medium_answer_plus_minus_wrong_answer_delta_target_wrong": by_condition["medium_wrong_answer_plus_rationale"]["target_wrong_rate"] - by_condition["wrong_answer_only"]["target_wrong_rate"],
        "strong_answer_plus_minus_wrong_answer_delta_target_wrong": by_condition["strong_wrong_answer_plus_rationale"]["target_wrong_rate"] - by_condition["wrong_answer_only"]["target_wrong_rate"],
    }
    labels: list[str] = []
    if effects["wrong_answer_delta_target_wrong"] > 0.10:
        labels.append("numeric_anchor_consistent")
    if effects["strong_minus_weak_wrong_rationale_delta_target_wrong"] > 0.10:
        labels.append("rationale_strength_sensitive")
    if effects["strong_wrong_rationale_delta_target_wrong"] > 0.10:
        labels.append("rationale_only_contamination_consistent")
    if effects["strong_answer_plus_minus_wrong_answer_delta_target_wrong"] > 0.05:
        labels.append("answer_rationale_amplification_consistent")
    if effects["strong_answer_plus_minus_wrong_answer_delta_target_wrong"] < -0.05:
        labels.append("answer_rationale_tension_consistent")
    if len({summary["target_wrong_rate"] for summary in by_condition.values()}) > 3:
        labels.append("item_group_heterogeneity_consistent")
    if not labels:
        labels = ["inconclusive"]
    return {
        "summary": {
            "n": len(raw_rows),
            "qualitative_labels": labels,
            "skipped_raw_ids": skipped_raw_ids,
        },
        "by_condition": by_condition,
        "by_item_condition": by_item_condition,
        "by_item_group_condition": by_item_group_condition,
        "by_strength_condition": by_strength_condition,
        "condition_effects": effects,
        "item_effects": item_effects,
        "item_group_effects": item_group_effects,
    }


def _format_table(rows: list[list[Any]]) -> str:
    if not rows:
        return ""
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    lines = []
    for idx, row in enumerate(rows):
        lines.append("| " + " | ".join(str(cell).rjust(widths[i]) if idx else str(cell).ljust(widths[i]) for i, cell in enumerate(row)) + " |")
        if idx == 0:
            lines.append("| " + " | ".join("-" * widths[i] for i in range(len(widths))) + " |")
    return "\n".join(lines)


def write_markdown(report: dict[str, Any], out_path: Path) -> None:
    lines = [
        "# GSM8K Synthetic Prefix Phase 3b Rationale-Strength Analysis",
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
        "No raw model text is included.",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a GSM8K synthetic-prefix phase 3b dataset.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()
    report = analyze_synthetic_prefix_phase3b(data_path=Path(args.data), raw_path=Path(args.raw))
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))


if __name__ == "__main__":
    main()
