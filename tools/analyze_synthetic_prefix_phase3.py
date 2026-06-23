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

from tools.build_synthetic_prefix_phase3_dataset import CONDITION_ORDER  # noqa: E402
from tools.select_partial_correct_items import normalize_answer  # noqa: E402

NUMERIC_RE = re.compile(r"^-?\d[\d,]*(?:\.\d+)?$")
REQUIRED_RAW_KEYS = {
    "id",
    "final_raw",
    "final_answer",
    "initial_answers",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata", {})
    return metadata if isinstance(metadata, dict) else {}


def _response_entries(row: dict[str, Any]) -> list[dict[str, Any]]:
    value = row.get("final_raw")
    if isinstance(value, list):
        return [entry for entry in value if isinstance(entry, dict)]
    return []


def _extract_candidate_text(entry: dict[str, Any]) -> str:
    for key in ("raw_text", "text", "content", "response", "message"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _extract_answer(entry: dict[str, Any]) -> tuple[str, bool, bool]:
    parsed = normalize_answer(entry.get("answer", ""))
    if not bool(entry.get("extraction_failed", False)) and parsed:
        return parsed, False, False
    raw_text = _extract_candidate_text(entry)
    if NUMERIC_RE.match(raw_text):
        return normalize_answer(raw_text), True, True
    return "", bool(entry.get("extraction_failed", False)), False


def _entropy(values: list[str]) -> float:
    if not values:
        return 0.0
    total = len(values)
    counts = Counter(values)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _empty_condition(condition: str) -> dict[str, Any]:
    return {
        "condition": condition,
        "n_outputs": 0,
        "non_failed_outputs": 0,
        "correct_count": 0,
        "target_wrong_count": 0,
        "other_count": 0,
        "raw_extraction_failure_count": 0,
        "format_recovered_count": 0,
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


def _validate_raw_row(row: dict[str, Any], *, row_id: str) -> None:
    missing = REQUIRED_RAW_KEYS - set(row)
    if missing:
        raise KeyError(f"raw row {row_id} missing keys: {', '.join(sorted(missing))}")
    final_raw = row.get("final_raw")
    if not isinstance(final_raw, list):
        raise TypeError(f"raw row {row_id} final_raw must be a list")


def _load_data(data_path: Path, raw_path: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    data_rows = load_jsonl(data_path)
    raw_rows = load_jsonl(raw_path)
    return {str(row["id"]): row for row in data_rows if "id" in row}, raw_rows


def _aggregate_condition(bucket: dict[str, Any]) -> dict[str, Any]:
    summary = _empty_condition(bucket["condition"])
    answers = bucket["answers"]
    summary.update(
        {
            "n_outputs": bucket["total"],
            "non_failed_outputs": len(answers),
            "correct_count": sum(1 for answer in answers if answer == bucket["gold"]),
            "target_wrong_count": sum(1 for answer in answers if answer == bucket["target_wrong"]),
            "other_count": 0,
            "raw_extraction_failure_count": bucket["raw_failures"],
            "format_recovered_count": 0,
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
    return summary


def analyze_synthetic_prefix_phase3(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
    data_rows = load_jsonl(data_path)
    raw_rows = load_jsonl(raw_path)
    data_by_id = {str(row["id"]): row for row in data_rows if "id" in row}

    by_item_condition: dict[str, dict[str, Any]] = {}
    item_bucket: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"answers": [], "raw_failures": 0, "total": 0})
    skipped_raw_ids: list[str] = []

    for raw_row in raw_rows:
        row_id = str(raw_row.get("id", ""))
        data_row = data_by_id.get(row_id)
        if data_row is None:
            skipped_raw_ids.append(row_id)
            continue
        _validate_raw_row(raw_row, row_id=row_id)
        metadata = _metadata(data_row)
        condition = str(metadata.get("condition", "unknown"))
        item_id = str(metadata.get("base_item_id", ""))
        gold = normalize_answer(metadata.get("gold", data_row.get("answer", "")))
        target_wrong = normalize_answer(metadata.get("target_wrong_answer", ""))
        bucket = item_bucket[(item_id, condition)]
        bucket.setdefault("condition", condition)
        bucket.setdefault("gold", gold)
        bucket.setdefault("target_wrong", target_wrong)
        bucket["total"] += 1
        final_answer = normalize_answer(raw_row.get("final_answer", ""))
        if not final_answer:
            entries = _response_entries(raw_row)
            if entries:
                final_answer, _, _ = _extract_answer(entries[0])
        if final_answer:
            bucket["answers"].append(final_answer)
        if int(raw_row.get("extraction_failures", 0)) > 0:
            bucket["raw_failures"] += 1

    by_condition: dict[str, dict[str, Any]] = {condition: _empty_condition(condition) for condition in CONDITION_ORDER}
    item_effects: dict[str, dict[str, float]] = {}
    item_condition_summaries: dict[tuple[str, str], dict[str, Any]] = {}

    for (item_id, condition), bucket in item_bucket.items():
        summary = _aggregate_condition(bucket)
        item_condition_summaries[(item_id, condition)] = summary
        merged = by_condition[condition]
        merged["n_outputs"] += summary["n_outputs"]
        merged["non_failed_outputs"] += summary["non_failed_outputs"]
        merged["correct_count"] += summary["correct_count"]
        merged["target_wrong_count"] += summary["target_wrong_count"]
        merged["other_count"] += summary["other_count"]
        merged["raw_extraction_failure_count"] += summary["raw_extraction_failure_count"]
        merged["format_recovered_count"] += summary["format_recovered_count"]
        merged["effective_extraction_failure_count"] += summary["effective_extraction_failure_count"]
        merged.setdefault("answers", []).extend(bucket["answers"])
        merged.setdefault("gold", bucket["gold"])
        merged.setdefault("target_wrong", bucket["target_wrong"])
        by_item_condition[f"{item_id}__{condition}"] = summary

    for _condition, summary in by_condition.items():
        answers = summary.pop("answers", [])
        summary["answer_counts"] = dict(sorted(Counter(answers).items()))
        summary["correct_rate"] = summary["correct_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
        summary["target_wrong_rate"] = summary["target_wrong_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
        summary["other_rate"] = summary["other_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
        summary["raw_extraction_failure_rate"] = summary["raw_extraction_failure_count"] / summary["n_outputs"] if summary["n_outputs"] else 0.0
        summary["effective_extraction_failure_rate"] = summary["effective_extraction_failure_count"] / summary["n_outputs"] if summary["n_outputs"] else 0.0
        summary["unique_answer_count"] = len(summary["answer_counts"])
        summary["answer_entropy"] = _entropy(answers)

    baseline = by_condition["baseline_no_prefix"]
    condition_effects = {
        "wrong_answer_delta_target_wrong": by_condition["wrong_answer_only"]["target_wrong_rate"] - baseline["target_wrong_rate"],
        "wrong_rationale_delta_target_wrong": by_condition["wrong_rationale_only"]["target_wrong_rate"] - baseline["target_wrong_rate"],
        "wrong_answer_plus_rationale_delta_target_wrong": by_condition["wrong_answer_plus_rationale"]["target_wrong_rate"] - baseline["target_wrong_rate"],
        "correct_answer_delta_correct": by_condition["correct_answer_only"]["correct_rate"] - baseline["correct_rate"],
        "correct_answer_plus_rationale_delta_correct": by_condition["correct_answer_plus_rationale"]["correct_rate"] - baseline["correct_rate"],
        "wrong_answer_plus_minus_wrong_answer_delta_target_wrong": by_condition["wrong_answer_plus_rationale"]["target_wrong_rate"] - by_condition["wrong_answer_only"]["target_wrong_rate"],
        "wrong_answer_plus_minus_wrong_rationale_delta_target_wrong": by_condition["wrong_answer_plus_rationale"]["target_wrong_rate"] - by_condition["wrong_rationale_only"]["target_wrong_rate"],
        "correct_answer_plus_minus_correct_answer_delta_correct": by_condition["correct_answer_plus_rationale"]["correct_rate"] - by_condition["correct_answer_only"]["correct_rate"],
    }

    for item_id in {key[0] for key in item_bucket}:
        condition_map = {condition: item_condition_summaries[(item_id, condition)] for condition in CONDITION_ORDER if (item_id, condition) in item_condition_summaries}
        if len(condition_map) != len(CONDITION_ORDER):
            continue
        base = condition_map["baseline_no_prefix"]
        item_effects[item_id] = {
            "wrong_answer_delta_target_wrong": condition_map["wrong_answer_only"]["target_wrong_rate"] - base["target_wrong_rate"],
            "wrong_rationale_delta_target_wrong": condition_map["wrong_rationale_only"]["target_wrong_rate"] - base["target_wrong_rate"],
            "wrong_answer_plus_rationale_delta_target_wrong": condition_map["wrong_answer_plus_rationale"]["target_wrong_rate"] - base["target_wrong_rate"],
            "correct_answer_delta_correct": condition_map["correct_answer_only"]["correct_rate"] - base["correct_rate"],
            "correct_answer_plus_rationale_delta_correct": condition_map["correct_answer_plus_rationale"]["correct_rate"] - base["correct_rate"],
        }

    qualitative_labels = _qualitative_labels(condition_effects, by_condition)
    total_outputs = len(raw_rows)
    correct_total = sum(1 for raw_row in raw_rows if normalize_answer(raw_row.get("final_answer", "")) == normalize_answer(data_by_id.get(str(raw_row.get("id", "")), {}).get("metadata", {}).get("gold", "")))
    sibling_summary_path = raw_path.parent / "summary.json"
    sibling_summary: dict[str, Any] = {}
    if sibling_summary_path.exists():
        try:
            loaded = json.loads(sibling_summary_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                sibling_summary = loaded
        except Exception:
            sibling_summary = {}

    report = {
        "n": total_outputs,
        "accuracy": correct_total / total_outputs if total_outputs else 0.0,
        "oracle_at_k": float(sibling_summary.get("oracle_at_k", 0.0)),
        "answer_loss_rate": float(sibling_summary.get("answer_loss_rate", 0.0)),
        "same_error_agreement_rate": float(sibling_summary.get("same_error_agreement_rate", 0.0)),
        "diversity_drop": float(sibling_summary.get("diversity_drop", 0.0)),
        "extraction_failure_rate": float(sibling_summary.get("extraction_failure_rate", 0.0)),
        "by_condition": by_condition,
        "condition_effects": condition_effects,
        "summary": {
            "n": total_outputs,
            "accuracy": correct_total / total_outputs if total_outputs else 0.0,
            "oracle_at_k": float(sibling_summary.get("oracle_at_k", 0.0)),
            "answer_loss_rate": float(sibling_summary.get("answer_loss_rate", 0.0)),
            "same_error_agreement_rate": float(sibling_summary.get("same_error_agreement_rate", 0.0)),
            "diversity_drop": float(sibling_summary.get("diversity_drop", 0.0)),
            "extraction_failure_rate": float(sibling_summary.get("extraction_failure_rate", 0.0)),
            "qualitative_labels": qualitative_labels,
            "skipped_raw_ids": skipped_raw_ids,
        },
        "by_item_condition": by_item_condition,
        "item_effects": item_effects,
    }
    return report


def _qualitative_labels(condition_effects: dict[str, float], by_condition: dict[str, dict[str, Any]]) -> list[str]:
    labels: list[str] = []
    if condition_effects["wrong_answer_delta_target_wrong"] > 0.10:
        labels.append("numeric_anchor_consistent")
    if condition_effects["wrong_rationale_delta_target_wrong"] > 0.10:
        labels.append("rationale_contamination_consistent")
    if (
        condition_effects["wrong_answer_plus_rationale_delta_target_wrong"]
        > condition_effects["wrong_answer_delta_target_wrong"] + 0.05
        and condition_effects["wrong_answer_plus_rationale_delta_target_wrong"]
        > condition_effects["wrong_rationale_delta_target_wrong"] + 0.05
    ):
        labels.append("answer_rationale_combination_consistent")
    if condition_effects["correct_answer_delta_correct"] > 0.10:
        labels.append("correct_answer_anchor_consistent")
    if condition_effects["correct_answer_plus_rationale_delta_correct"] > condition_effects["correct_answer_delta_correct"] + 0.05:
        labels.append("correct_rationale_recovery_consistent")
    baseline_failure = by_condition["baseline_no_prefix"]["effective_extraction_failure_rate"]
    if max(summary["effective_extraction_failure_rate"] for summary in by_condition.values()) - baseline_failure > 0.05:
        labels.append("failure_sensitive")
    if not labels:
        labels.append("inconclusive")
    return labels


def _format_table(rows: list[list[Any]]) -> str:
    if not rows:
        return ""
    widths = [max(len(str(row[index])) for row in rows) for index in range(len(rows[0]))]
    lines = []
    for row_index, row in enumerate(rows):
        parts = [str(cell).ljust(widths[index]) if row_index == 0 else str(cell).rjust(widths[index]) for index, cell in enumerate(row)]
        lines.append("| " + " | ".join(parts) + " |")
        if row_index == 0:
            lines.append("| " + " | ".join("-" * widths[index] for index in range(len(widths))) + " |")
    return "\n".join(lines)


def write_markdown(report: dict[str, Any], out_path: Path) -> None:
    lines = [
        "# GSM8K Synthetic Prefix Phase 3 Rationale-Contamination Analysis",
        "Caution:",
        "- exploratory diagnostic",
        "- repeated stochastic prompt samples",
        "- not benchmark-level evidence",
        "- no causal proof",
        "- no statistical-significance claim",
        "- rationale wording is synthetic and may bias results",
        "## Summary",
        f"- n: `{report['n']}`",
        f"- accuracy: `{report['accuracy']:.6f}`",
        f"- oracle_at_k: `{report['oracle_at_k']:.6f}`",
        f"- answer_loss_rate: `{report['answer_loss_rate']:.6f}`",
        f"- same_error_agreement_rate: `{report['same_error_agreement_rate']:.6f}`",
        f"- diversity_drop: `{report['diversity_drop']:.6f}`",
        f"- extraction_failure_rate: `{report['extraction_failure_rate']:.6f}`",
        f"- qualitative_labels: `{', '.join(report['summary']['qualitative_labels'])}`",
        "## By Condition",
    ]
    table = [["condition", "correct_rate", "target_wrong_rate", "raw_failure", "effective_failure"]]
    for condition in CONDITION_ORDER:
        summary = report["by_condition"][condition]
        table.append([condition, f"{summary['correct_rate']:.3f}", f"{summary['target_wrong_rate']:.3f}", f"{summary['raw_extraction_failure_rate']:.3f}", f"{summary['effective_extraction_failure_rate']:.3f}"])
    lines.append(_format_table(table))
    lines.extend([
        "## Condition Effects",
        _format_table([["effect", "value"]] + [[name, f"{value:.3f}"] for name, value in report["condition_effects"].items()]),
        "## Extraction and Recovery",
        f"- baseline effective failure rate: {report['by_condition']['baseline_no_prefix']['effective_extraction_failure_rate']:.3f}",
        "## Interpretation Guide",
        "- If wrong_answer_only shifts target_wrong more than the baseline, numeric anchoring is plausible.",
        "- If wrong_rationale_only shifts target_wrong, rationale contamination is plausible.",
        "- If the combined condition exceeds either alone, the answer and rationale may interact.",
        "- If correct_rationale helps more than correct_answer_only, the explanation may provide corrective structure.",
        "No raw model text is included.",
    ])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a GSM8K synthetic-prefix phase 3 dataset.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    report = analyze_synthetic_prefix_phase3(data_path=Path(args.data), raw_path=Path(args.raw))
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))


if __name__ == "__main__":
    main()
