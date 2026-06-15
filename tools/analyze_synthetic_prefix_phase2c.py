from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_synthetic_prefix_phase2c_dataset import (  # noqa: E402
    CONDITION_ORDER,
    PROMPT_FORMAT_ORDER,
)
from tools.select_partial_correct_items import normalize_answer  # noqa: E402

JSON_ANSWER_RE = re.compile(r'^\s*\{\s*"answer"\s*:\s*"(.*?)"\s*\}\s*$', re.DOTALL)
NUMERIC_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


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
    for key in ("final_raw", "initial_raw", "transcript_raw"):
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


def _base_summary(prompt_format: str, condition: str) -> dict[str, Any]:
    return {
        "prompt_format": prompt_format,
        "condition": condition,
        "n_outputs": 0,
        "raw_extraction_failure_count": 0,
        "format_recovered_count": 0,
        "effective_extraction_failure_count": 0,
        "non_failed_outputs": 0,
        "correct_count": 0,
        "target_wrong_count": 0,
        "other_count": 0,
        "raw_extraction_failure_rate": 0.0,
        "format_recovered_rate": 0.0,
        "effective_extraction_failure_rate": 0.0,
        "correct_rate": 0.0,
        "target_wrong_rate": 0.0,
        "other_rate": 0.0,
        "unique_answer_count": 0,
        "answer_entropy": 0.0,
        "answer_counts": {},
    }


def _extract_candidate_text(entry: dict[str, Any]) -> str:
    for key in ("answer", "raw_text", "text", "content", "raw", "message", "response"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, dict):
            nested = _extract_candidate_text(value)
            if nested.strip():
                return nested
    return ""


def _extract_format_recovered_answer(prompt_format: str, raw_text: str) -> str:
    text = raw_text.strip()
    if not text:
        return ""
    if prompt_format == "answer_tag":
        return ""
    if prompt_format == "json":
        match = JSON_ANSWER_RE.match(text)
        if match:
            return normalize_answer(match.group(1))
        try:
            payload = json.loads(text)
        except Exception:
            return ""
        if isinstance(payload, dict):
            return normalize_answer(payload.get("answer", ""))
        return ""
    if prompt_format == "plain_final":
        numeric = NUMERIC_RE.findall(text)
        if len(numeric) == 1:
            return normalize_answer(numeric[0])
        return ""
    return ""


def _effective_answer(prompt_format: str, entry: dict[str, Any]) -> tuple[str, bool]:
    raw_answer = normalize_answer(entry.get("answer", ""))
    if not bool(entry.get("extraction_failed", False)) and raw_answer:
        return raw_answer, False
    raw_text = _extract_candidate_text(entry)
    recovered = _extract_format_recovered_answer(prompt_format, raw_text)
    if recovered:
        return recovered, True
    return "", False


def _update_summary(
    summary: dict[str, Any],
    *,
    answers: list[str],
    raw_failures: int,
    recovered_count: int,
    total: int,
    gold: str,
    target_wrong: str,
) -> dict[str, Any]:
    correct_count = sum(1 for answer in answers if answer == gold)
    target_wrong_count = sum(1 for answer in answers if answer == target_wrong)
    other_count = len(answers) - correct_count - target_wrong_count
    summary.update(
        {
            "n_outputs": total,
            "raw_extraction_failure_count": raw_failures,
            "format_recovered_count": recovered_count,
            "effective_extraction_failure_count": raw_failures - recovered_count,
            "non_failed_outputs": len(answers),
            "correct_count": correct_count,
            "target_wrong_count": target_wrong_count,
            "other_count": other_count,
            "raw_extraction_failure_rate": raw_failures / total if total else 0.0,
            "format_recovered_rate": recovered_count / total if total else 0.0,
            "effective_extraction_failure_rate": (raw_failures - recovered_count) / total if total else 0.0,
            "correct_rate": correct_count / len(answers) if answers else 0.0,
            "target_wrong_rate": target_wrong_count / len(answers) if answers else 0.0,
            "other_rate": other_count / len(answers) if answers else 0.0,
            "unique_answer_count": len(Counter(answers)),
            "answer_entropy": _entropy(answers),
            "answer_counts": dict(sorted(Counter(answers).items())),
        }
    )
    return summary


def _merge_summary(
    target: dict[str, Any],
    source: dict[str, Any],
    *,
    gold: str,
    target_wrong: str,
) -> dict[str, Any]:
    answers = []
    for answer, count in source["answer_counts"].items():
        answers.extend([answer] * count)
    return _update_summary(
        target,
        answers=answers,
        raw_failures=int(source["raw_extraction_failure_count"]),
        recovered_count=int(source["format_recovered_count"]),
        total=int(source["n_outputs"]),
        gold=gold,
        target_wrong=target_wrong,
    )


def analyze_synthetic_prefix_phase2c(*, data_path: Path, raw_path: Path) -> dict[str, Any]:
    data_rows = load_jsonl(data_path)
    raw_rows = load_jsonl(raw_path)
    data_by_id = {str(row["id"]): row for row in data_rows if "id" in row}

    skipped_raw_ids: list[str] = []
    by_item_format_condition: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    item_ids: list[str] = []

    for raw_row in raw_rows:
        row_id = str(raw_row.get("id", ""))
        data_row = data_by_id.get(row_id)
        if data_row is None:
            skipped_raw_ids.append(row_id)
            continue

        metadata = _metadata(data_row)
        item_id = str(metadata.get("base_item_id", ""))
        condition = str(metadata.get("condition", "unknown"))
        prompt_format = str(metadata.get("prompt_format", "unknown"))
        gold = normalize_answer(metadata.get("gold", data_row.get("answer", "")))
        target_wrong = normalize_answer(metadata.get("target_wrong_answer", ""))
        if item_id and item_id not in item_ids:
            item_ids.append(item_id)
        key = (item_id, prompt_format, condition)
        bucket = grouped.setdefault(
            key,
            {
                "answers": [],
                "raw_failures": 0,
                "recovered_count": 0,
                "total": 0,
                "gold": gold,
                "target_wrong": target_wrong,
            },
        )

        for entry in _response_entries(raw_row):
            bucket["total"] += 1
            effective_answer, recovered = _effective_answer(prompt_format, entry)
            if bool(entry.get("extraction_failed", False)):
                bucket["raw_failures"] += 1
            if recovered:
                bucket["recovered_count"] += 1
            if effective_answer:
                bucket["answers"].append(effective_answer)

    by_format_condition: dict[str, dict[str, dict[str, Any]]] = {
        prompt_format: {condition: _base_summary(prompt_format, condition) for condition in CONDITION_ORDER}
        for prompt_format in PROMPT_FORMAT_ORDER
    }
    aggregate_by_format: dict[str, dict[str, Any]] = {
        prompt_format: _base_summary(prompt_format, "all_conditions") for prompt_format in PROMPT_FORMAT_ORDER
    }
    aggregate_by_condition: dict[str, dict[str, Any]] = {
        condition: _base_summary("all_formats", condition) for condition in CONDITION_ORDER
    }

    item_summaries: dict[tuple[str, str, str], dict[str, Any]] = {}

    for (item_id, prompt_format, condition), bucket in grouped.items():
        summary = _base_summary(prompt_format, condition)
        summary = _update_summary(
            summary,
            answers=bucket["answers"],
            raw_failures=bucket["raw_failures"],
            recovered_count=bucket["recovered_count"],
            total=bucket["total"],
            gold=bucket["gold"],
            target_wrong=bucket["target_wrong"],
        )
        item_summaries[(item_id, prompt_format, condition)] = summary
        by_item_format_condition.setdefault(item_id, {}).setdefault(prompt_format, {})[condition] = summary

    for prompt_format in PROMPT_FORMAT_ORDER:
        for condition in CONDITION_ORDER:
            merged = _base_summary(prompt_format, condition)
            item_count = 0
            for item_id in item_ids:
                summary = item_summaries.get((item_id, prompt_format, condition))
                if summary is None:
                    continue
                item_count += 1
                merged["n_outputs"] += int(summary["n_outputs"])
                merged["raw_extraction_failure_count"] += int(summary["raw_extraction_failure_count"])
                merged["format_recovered_count"] += int(summary["format_recovered_count"])
                merged["effective_extraction_failure_count"] += int(summary["effective_extraction_failure_count"])
                merged["non_failed_outputs"] += int(summary["non_failed_outputs"])
                merged["correct_count"] += int(summary["correct_count"])
                merged["target_wrong_count"] += int(summary["target_wrong_count"])
                merged["other_count"] += int(summary["other_count"])
                merged["answer_counts"].update(summary["answer_counts"])
            merged["raw_extraction_failure_rate"] = (
                merged["raw_extraction_failure_count"] / merged["n_outputs"] if merged["n_outputs"] else 0.0
            )
            merged["format_recovered_rate"] = merged["format_recovered_count"] / merged["n_outputs"] if merged["n_outputs"] else 0.0
            merged["effective_extraction_failure_rate"] = (
                merged["effective_extraction_failure_count"] / merged["n_outputs"] if merged["n_outputs"] else 0.0
            )
            merged["correct_rate"] = merged["correct_count"] / merged["non_failed_outputs"] if merged["non_failed_outputs"] else 0.0
            merged["target_wrong_rate"] = merged["target_wrong_count"] / merged["non_failed_outputs"] if merged["non_failed_outputs"] else 0.0
            merged["other_rate"] = merged["other_count"] / merged["non_failed_outputs"] if merged["non_failed_outputs"] else 0.0
            merged["unique_answer_count"] = len(Counter(merged["answer_counts"]))
            merged["answer_entropy"] = _entropy(
                [answer for answer, count in merged["answer_counts"].items() for _ in range(count)]
            )
            merged["answer_counts"] = dict(sorted(merged["answer_counts"].items()))
            merged["item_count"] = item_count
            by_format_condition[prompt_format][condition] = merged

    for condition in CONDITION_ORDER:
        merged = _base_summary("all_formats", condition)
        item_count = 0
        for prompt_format in PROMPT_FORMAT_ORDER:
            summary = by_format_condition[prompt_format][condition]
            merged["n_outputs"] += int(summary["n_outputs"])
            merged["raw_extraction_failure_count"] += int(summary["raw_extraction_failure_count"])
            merged["format_recovered_count"] += int(summary["format_recovered_count"])
            merged["effective_extraction_failure_count"] += int(summary["effective_extraction_failure_count"])
            merged["non_failed_outputs"] += int(summary["non_failed_outputs"])
            merged["correct_count"] += int(summary["correct_count"])
            merged["target_wrong_count"] += int(summary["target_wrong_count"])
            merged["other_count"] += int(summary["other_count"])
            merged["answer_counts"].update(summary["answer_counts"])
        for item_id in item_ids:
            if condition in by_item_format_condition.get(item_id, {}).get(PROMPT_FORMAT_ORDER[0], {}):
                item_count += 1
        merged["raw_extraction_failure_rate"] = merged["raw_extraction_failure_count"] / merged["n_outputs"] if merged["n_outputs"] else 0.0
        merged["format_recovered_rate"] = merged["format_recovered_count"] / merged["n_outputs"] if merged["n_outputs"] else 0.0
        merged["effective_extraction_failure_rate"] = merged["effective_extraction_failure_count"] / merged["n_outputs"] if merged["n_outputs"] else 0.0
        merged["correct_rate"] = merged["correct_count"] / merged["non_failed_outputs"] if merged["non_failed_outputs"] else 0.0
        merged["target_wrong_rate"] = merged["target_wrong_count"] / merged["non_failed_outputs"] if merged["non_failed_outputs"] else 0.0
        merged["other_rate"] = merged["other_count"] / merged["non_failed_outputs"] if merged["non_failed_outputs"] else 0.0
        merged["unique_answer_count"] = len(Counter(merged["answer_counts"]))
        merged["answer_entropy"] = _entropy([answer for answer, count in merged["answer_counts"].items() for _ in range(count)])
        merged["answer_counts"] = dict(sorted(merged["answer_counts"].items()))
        merged["item_count"] = item_count
        aggregate_by_condition[condition] = merged

    for prompt_format in PROMPT_FORMAT_ORDER:
        merged = _base_summary(prompt_format, "all_conditions")
        condition_count = 0
        for condition in CONDITION_ORDER:
            summary = by_format_condition[prompt_format][condition]
            merged["n_outputs"] += int(summary["n_outputs"])
            merged["raw_extraction_failure_count"] += int(summary["raw_extraction_failure_count"])
            merged["format_recovered_count"] += int(summary["format_recovered_count"])
            merged["effective_extraction_failure_count"] += int(summary["effective_extraction_failure_count"])
            merged["non_failed_outputs"] += int(summary["non_failed_outputs"])
            merged["correct_count"] += int(summary["correct_count"])
            merged["target_wrong_count"] += int(summary["target_wrong_count"])
            merged["other_count"] += int(summary["other_count"])
            merged["answer_counts"].update(summary["answer_counts"])
            if summary["n_outputs"] > 0:
                condition_count += 1
        merged["raw_extraction_failure_rate"] = merged["raw_extraction_failure_count"] / merged["n_outputs"] if merged["n_outputs"] else 0.0
        merged["format_recovered_rate"] = merged["format_recovered_count"] / merged["n_outputs"] if merged["n_outputs"] else 0.0
        merged["effective_extraction_failure_rate"] = merged["effective_extraction_failure_count"] / merged["n_outputs"] if merged["n_outputs"] else 0.0
        merged["correct_rate"] = merged["correct_count"] / merged["non_failed_outputs"] if merged["non_failed_outputs"] else 0.0
        merged["target_wrong_rate"] = merged["target_wrong_count"] / merged["non_failed_outputs"] if merged["non_failed_outputs"] else 0.0
        merged["other_rate"] = merged["other_count"] / merged["non_failed_outputs"] if merged["non_failed_outputs"] else 0.0
        merged["unique_answer_count"] = len(Counter(merged["answer_counts"]))
        merged["answer_entropy"] = _entropy([answer for answer, count in merged["answer_counts"].items() for _ in range(count)])
        merged["answer_counts"] = dict(sorted(merged["answer_counts"].items()))
        merged["condition_count"] = condition_count
        aggregate_by_format[prompt_format] = merged

    answer_tag = aggregate_by_format["answer_tag"]
    format_effects: dict[str, dict[str, Any]] = {}
    for prompt_format in PROMPT_FORMAT_ORDER:
        summary = aggregate_by_format[prompt_format]
        format_effects[prompt_format] = {
            "delta_raw_extraction_failure": summary["raw_extraction_failure_rate"] - answer_tag["raw_extraction_failure_rate"],
            "delta_effective_extraction_failure": summary["effective_extraction_failure_rate"] - answer_tag["effective_extraction_failure_rate"],
            "delta_correct_rate": summary["correct_rate"] - answer_tag["correct_rate"],
            "delta_target_wrong_rate": summary["target_wrong_rate"] - answer_tag["target_wrong_rate"],
            "correct_consensus_delta_correct_vs_baseline": by_format_condition[prompt_format]["single_round_correct_consensus"]["correct_rate"]
            - by_format_condition[prompt_format]["baseline_no_prefix"]["correct_rate"],
            "wrong_consensus_delta_wrong_vs_baseline": by_format_condition[prompt_format]["single_round_wrong_consensus"]["target_wrong_rate"]
            - by_format_condition[prompt_format]["baseline_no_prefix"]["target_wrong_rate"],
            "wrong_consensus_delta_failure_vs_baseline": by_format_condition[prompt_format]["single_round_wrong_consensus"]["effective_extraction_failure_rate"]
            - by_format_condition[prompt_format]["baseline_no_prefix"]["effective_extraction_failure_rate"],
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

    qualitative_labels: list[str] = []
    if any(
        format_effects[prompt_format]["wrong_consensus_delta_wrong_vs_baseline"] > 0.10
        for prompt_format in PROMPT_FORMAT_ORDER
        if prompt_format != "answer_tag"
    ) and any(
        format_effects[prompt_format]["correct_consensus_delta_correct_vs_baseline"] > 0.10
        for prompt_format in PROMPT_FORMAT_ORDER
        if prompt_format != "answer_tag"
    ):
        qualitative_labels.append("consensus_effect_format_robust")
    if max(
        aggregate_by_format[prompt_format]["raw_extraction_failure_rate"] for prompt_format in PROMPT_FORMAT_ORDER
    ) - min(aggregate_by_format[prompt_format]["raw_extraction_failure_rate"] for prompt_format in PROMPT_FORMAT_ORDER) >= 0.10:
        qualitative_labels.append("format_failure_sensitive")
    if any(
        aggregate_by_format[prompt_format]["effective_extraction_failure_rate"]
        <= aggregate_by_format[prompt_format]["raw_extraction_failure_rate"] - 0.05
        for prompt_format in PROMPT_FORMAT_ORDER
        if prompt_format != "answer_tag"
    ):
        qualitative_labels.append("format_recovery_useful")
    if (
        aggregate_by_format["json"]["effective_extraction_failure_rate"]
        <= aggregate_by_format["answer_tag"]["raw_extraction_failure_rate"] - 0.05
    ):
        qualitative_labels.append("json_reduces_failure")
    if (
        aggregate_by_format["plain_final"]["effective_extraction_failure_rate"]
        <= aggregate_by_format["answer_tag"]["raw_extraction_failure_rate"] - 0.05
    ):
        qualitative_labels.append("plain_final_reduces_failure")
    if not qualitative_labels:
        qualitative_labels.append("inconclusive")

    return {
        "phase": "phase2c_prompt_format",
        "data": str(data_path),
        "raw": str(raw_path),
        "items": sorted(item_ids),
        "conditions": CONDITION_ORDER,
        "prompt_formats": PROMPT_FORMAT_ORDER,
        "by_format_condition": by_format_condition,
        "by_item_format_condition": by_item_format_condition,
        "aggregate_by_format": aggregate_by_format,
        "aggregate_by_condition": aggregate_by_condition,
        "format_effects": format_effects,
        "summary": {
            "n_items": len(item_ids),
            "n_conditions": len(CONDITION_ORDER),
            "n_prompt_formats": len(PROMPT_FORMAT_ORDER),
            "n_outputs": len(raw_rows) * 3,
            "skipped_raw_ids": skipped_raw_ids,
            "qualitative_labels": qualitative_labels,
        },
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# GSM8K Synthetic Prefix Phase 2c Prompt-Format Robustness Analysis")
    lines.append("")
    lines.append("Caution:")
    lines.append("- exploratory diagnostic")
    lines.append("- repeated stochastic prompt samples")
    lines.append("- prompt-format comparison")
    lines.append("- not benchmark-level evidence")
    lines.append("- no causal proof")
    lines.append("- no statistical-significance claim")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- qualitative_labels: `{', '.join(report['summary']['qualitative_labels'])}`")
    lines.append("")
    lines.append("## By Prompt Format and Condition")
    lines.append("")
    lines.append("| prompt_format | condition | n_outputs | raw_extraction_failure_rate | effective_extraction_failure_rate | correct_rate | target_wrong_rate | answer_entropy |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for prompt_format in report["prompt_formats"]:
        for condition in report["conditions"]:
            summary = report["by_format_condition"][prompt_format][condition]
            lines.append(
                f"| {prompt_format} | {condition} | {summary['n_outputs']} | {summary['raw_extraction_failure_rate']} | {summary['effective_extraction_failure_rate']} | {summary['correct_rate']} | {summary['target_wrong_rate']} | {summary['answer_entropy']} |"
            )
    lines.append("")
    lines.append("## Aggregate by Prompt Format")
    lines.append("")
    lines.append("| prompt_format | n_outputs | raw_extraction_failure_rate | effective_extraction_failure_rate | correct_rate | target_wrong_rate | answer_entropy |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for prompt_format in report["prompt_formats"]:
        summary = report["aggregate_by_format"][prompt_format]
        lines.append(
            f"| {prompt_format} | {summary['n_outputs']} | {summary['raw_extraction_failure_rate']} | {summary['effective_extraction_failure_rate']} | {summary['correct_rate']} | {summary['target_wrong_rate']} | {summary['answer_entropy']} |"
        )
    lines.append("")
    lines.append("## Aggregate by Condition")
    lines.append("")
    lines.append("| condition | n_outputs | raw_extraction_failure_rate | effective_extraction_failure_rate | correct_rate | target_wrong_rate | answer_entropy |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for condition in report["conditions"]:
        summary = report["aggregate_by_condition"][condition]
        lines.append(
            f"| {condition} | {summary['n_outputs']} | {summary['raw_extraction_failure_rate']} | {summary['effective_extraction_failure_rate']} | {summary['correct_rate']} | {summary['target_wrong_rate']} | {summary['answer_entropy']} |"
        )
    lines.append("")
    lines.append("## Format Effects")
    lines.append("")
    lines.append("| prompt_format | delta_raw_extraction_failure | delta_effective_extraction_failure | delta_correct_rate | delta_target_wrong_rate | correct_consensus_delta_correct_vs_baseline | wrong_consensus_delta_wrong_vs_baseline | wrong_consensus_delta_failure_vs_baseline |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for prompt_format in report["prompt_formats"]:
        effect = report["format_effects"][prompt_format]
        lines.append(
            f"| {prompt_format} | {effect['delta_raw_extraction_failure']} | {effect['delta_effective_extraction_failure']} | {effect['delta_correct_rate']} | {effect['delta_target_wrong_rate']} | {effect['correct_consensus_delta_correct_vs_baseline']} | {effect['wrong_consensus_delta_wrong_vs_baseline']} | {effect['wrong_consensus_delta_failure_vs_baseline']} |"
        )
    lines.append("")
    lines.append("## Interpretation Guide")
    lines.append("")
    lines.append("- If the consensus effects stay similar across formats, that is consistent with a format-robust consensus effect.")
    lines.append("- If raw and effective extraction failure differ, that suggests parser recovery can matter.")
    lines.append("- If JSON or plain-final reduces effective failure relative to answer-tag, that is consistent with format-sensitive extraction.")
    lines.append("- If formats are similar, the robustness signal may be weak or absent in this diagnostic.")
    lines.append("")
    lines.append("No raw model text is included.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a synthetic-prefix phase 2c run.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    report = analyze_synthetic_prefix_phase2c(data_path=Path(args.data), raw_path=Path(args.raw))
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
