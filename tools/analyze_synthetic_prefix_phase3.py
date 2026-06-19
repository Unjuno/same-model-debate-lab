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


def _extract_answer(entry: dict[str, Any]) -> tuple[str, bool, bool]:
    parsed = normalize_answer(entry.get("answer", ""))
    if not bool(entry.get("extraction_failed", False)) and parsed:
        return parsed, False, False
    raw_text = ""
    for key in ("raw_text", "text", "content", "response"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            raw_text = value.strip()
            break
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


def _update_summary(summary: dict[str, Any], answers: list[str], raw_failures: int, recovered: int, total: int, gold: str, target_wrong: str) -> dict[str, Any]:
    correct_count = sum(1 for answer in answers if answer == gold)
    target_wrong_count = sum(1 for answer in answers if answer == target_wrong)
    other_count = len(answers) - correct_count - target_wrong_count
    summary.update(
        {
            "n_outputs": total,
            "non_failed_outputs": len(answers),
            "correct_count": correct_count,
            "target_wrong_count": target_wrong_count,
            "other_count": other_count,
            "raw_extraction_failure_count": raw_failures,
            "format_recovered_count": recovered,
            "effective_extraction_failure_count": raw_failures - recovered,
            "correct_rate": correct_count / len(answers) if answers else 0.0,
            "target_wrong_rate": target_wrong_count / len(answers) if answers else 0.0,
            "other_rate": other_count / len(answers) if answers else 0.0,
            "raw_extraction_failure_rate": raw_failures / total if total else 0.0,
            "effective_extraction_failure_rate": (raw_failures - recovered) / total if total else 0.0,
            "answer_entropy": _entropy(answers),
            "unique_answer_count": len(Counter(answers)),
            "answer_counts": dict(sorted(Counter(answers).items())),
        }
    )
    return summary


def _load_data(data_path: Path, raw_path: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    data_rows = load_jsonl(data_path)
    raw_rows = load_jsonl(raw_path)
    return {str(row["id"]): row for row in data_rows if "id" in row}, raw_rows


def analyze_synthetic_prefix_phase3(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
    data_by_id, raw_rows = _load_data(data_path, raw_path)
    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"answers": [], "raw": 0, "recovered": 0, "total": 0})
    skipped_raw_ids: list[str] = []

    for raw_row in raw_rows:
        row_id = str(raw_row.get("id", ""))
        data_row = data_by_id.get(row_id)
        if data_row is None:
            skipped_raw_ids.append(row_id)
            continue
        metadata = _metadata(data_row)
        condition = str(metadata.get("condition", "unknown"))
        base_item_id = str(metadata.get("base_item_id", ""))
        gold = normalize_answer(metadata.get("gold", data_row.get("answer", "")))
        target_wrong = normalize_answer(metadata.get("target_wrong_answer", ""))
        bucket = grouped[(base_item_id, condition)]
        bucket.setdefault("gold", gold)
        bucket.setdefault("target_wrong", target_wrong)
        for entry in _response_entries(raw_row):
            bucket["total"] += 1
            answer, raw_failed, recovered = _extract_answer(entry)
            if raw_failed:
                bucket["raw"] += 1
            if recovered:
                bucket["recovered"] += 1
            if answer:
                bucket["answers"].append(answer)

    by_condition: dict[str, dict[str, Any]] = {condition: _empty_condition(condition) for condition in CONDITION_ORDER}
    by_item_condition: dict[str, dict[str, Any]] = {}

    for (item_id, condition), bucket in grouped.items():
        summary = _update_summary(
            _empty_condition(condition),
            bucket["answers"],
            bucket["raw"],
            bucket["recovered"],
            bucket["total"],
            bucket.get("gold", ""),
            bucket.get("target_wrong", ""),
        )
        by_item_condition[f"{item_id}__{condition}"] = summary
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

    for _condition, summary in by_condition.items():
        summary["answer_counts"] = dict(sorted(Counter(summary.pop("answers", [])).items()))
        summary["correct_rate"] = summary["correct_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
        summary["target_wrong_rate"] = summary["target_wrong_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
        summary["other_rate"] = summary["other_count"] / summary["non_failed_outputs"] if summary["non_failed_outputs"] else 0.0
        summary["raw_extraction_failure_rate"] = summary["raw_extraction_failure_count"] / summary["n_outputs"] if summary["n_outputs"] else 0.0
        summary["effective_extraction_failure_rate"] = summary["effective_extraction_failure_count"] / summary["n_outputs"] if summary["n_outputs"] else 0.0
        summary["answer_entropy"] = _entropy([answer for answer, count in summary["answer_counts"].items() for _ in range(count)])
        summary["unique_answer_count"] = len(summary["answer_counts"])

    baseline = by_condition["baseline_no_prefix"]
    condition_effects = _condition_effects(by_condition)
    item_effects = _item_effects(by_item_condition)
    qualitative_labels = _qualitative_labels(condition_effects, by_condition)

    return {
        "summary": {
            "n_conditions": len(CONDITION_ORDER),
            "qualitative_labels": qualitative_labels,
            "skipped_raw_ids": skipped_raw_ids,
        },
        "by_condition": by_condition,
        "by_item_condition": by_item_condition,
        "condition_effects": condition_effects,
        "item_effects": item_effects,
        "baseline": baseline,
    }


def _condition_effects(by_condition: dict[str, dict[str, Any]]) -> dict[str, float]:
    baseline = by_condition["baseline_no_prefix"]
    return {
        "wrong_answer_delta_target_wrong": by_condition["wrong_answer_only"]["target_wrong_rate"] - baseline["target_wrong_rate"],
        "wrong_rationale_delta_target_wrong": by_condition["wrong_rationale_only"]["target_wrong_rate"] - baseline["target_wrong_rate"],
        "wrong_answer_plus_rationale_delta_target_wrong": by_condition["wrong_answer_plus_rationale"]["target_wrong_rate"] - baseline["target_wrong_rate"],
        "correct_answer_delta_correct": by_condition["correct_answer_only"]["correct_rate"] - baseline["correct_rate"],
        "correct_answer_plus_rationale_delta_correct": by_condition["correct_answer_plus_rationale"]["correct_rate"] - baseline["correct_rate"],
        "wrong_answer_plus_minus_wrong_answer_delta_target_wrong": by_condition["wrong_answer_plus_rationale"]["target_wrong_rate"] - by_condition["wrong_answer_only"]["target_wrong_rate"],
        "wrong_answer_plus_minus_wrong_rationale_delta_target_wrong": by_condition["wrong_answer_plus_rationale"]["target_wrong_rate"] - by_condition["wrong_rationale_only"]["target_wrong_rate"],
        "correct_answer_plus_minus_correct_answer_delta_correct": by_condition["correct_answer_plus_rationale"]["correct_rate"] - by_condition["correct_answer_only"]["correct_rate"],
    }


def _item_effects(by_item_condition: dict[str, dict[str, Any]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for key, summary in by_item_condition.items():
        item_id, condition = key.rsplit("__", 1)
        grouped[item_id][condition] = summary
    effects: dict[str, dict[str, float]] = {}
    for item_id, condition_map in grouped.items():
        baseline = condition_map["baseline_no_prefix"]
        effects[item_id] = {
            "wrong_answer_delta_target_wrong": condition_map["wrong_answer_only"]["target_wrong_rate"] - baseline["target_wrong_rate"],
            "wrong_rationale_delta_target_wrong": condition_map["wrong_rationale_only"]["target_wrong_rate"] - baseline["target_wrong_rate"],
            "wrong_answer_plus_rationale_delta_target_wrong": condition_map["wrong_answer_plus_rationale"]["target_wrong_rate"] - baseline["target_wrong_rate"],
            "correct_answer_delta_correct": condition_map["correct_answer_only"]["correct_rate"] - baseline["correct_rate"],
            "correct_answer_plus_rationale_delta_correct": condition_map["correct_answer_plus_rationale"]["correct_rate"] - baseline["correct_rate"],
        }
    return effects


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
        "## Item-Level Effects",
    ])
    item_rows = [["item_id", "wrong_answer_delta_target_wrong", "wrong_rationale_delta_target_wrong", "wrong_answer_plus_rationale_delta_target_wrong"]]
    for item_id in sorted(report["item_effects"]):
        effects = report["item_effects"][item_id]
        item_rows.append([item_id, f"{effects['wrong_answer_delta_target_wrong']:.3f}", f"{effects['wrong_rationale_delta_target_wrong']:.3f}", f"{effects['wrong_answer_plus_rationale_delta_target_wrong']:.3f}"])
    lines.append(_format_table(item_rows))
    lines.extend([
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
