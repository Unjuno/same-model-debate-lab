from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.select_partial_correct_items import normalize_answer  # noqa: E402

FAILURE_CATEGORIES = [
    "missing_answer_tag",
    "empty_output",
    "non_numeric_answer",
    "contains_numeric_but_unwrapped",
    "multiple_candidate_numbers",
    "tool_or_format_noise",
    "unknown",
]

ANSWER_TAG_RE = re.compile(r"<answer>(.*?)</answer>", re.IGNORECASE | re.DOTALL)
NUMERIC_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
NOISE_RE = re.compile(
    r"(```|```python|\\boxed|tool call|function call|json|analysis:|final answer:|answer:|scratchpad|python|calculator|work shown)",
    re.IGNORECASE,
)


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


def _extract_raw_text(entry: dict[str, Any]) -> str:
    value = entry.get("raw_text", entry.get("answer", ""))
    return str(value)


def _numeric_candidates(text: str) -> list[str]:
    return NUMERIC_RE.findall(text)


def _classify_failure(raw_text: str) -> str:
    text = raw_text.strip()
    if not text:
        return "empty_output"

    if NOISE_RE.search(text):
        return "tool_or_format_noise"

    tags = ANSWER_TAG_RE.findall(text)
    if tags:
        normalized_tags = [normalize_answer(tag) for tag in tags if str(tag).strip()]
        numeric_tags = [tag for tag in normalized_tags if NUMERIC_RE.fullmatch(tag.replace(",", ""))]
        if len(tags) > 1 and len(set(numeric_tags)) > 1:
            return "multiple_candidate_numbers"
        if len(tags) > 1 and len(set(normalized_tags)) > 1:
            return "tool_or_format_noise"
        if normalized_tags:
            first = normalized_tags[0]
            if NUMERIC_RE.fullmatch(first.replace(",", "")):
                return "unknown"
            return "non_numeric_answer"
        return "missing_answer_tag"

    candidates = _numeric_candidates(text)
    if len(candidates) > 1:
        return "multiple_candidate_numbers"
    if len(candidates) == 1:
        return "contains_numeric_but_unwrapped"

    if "<answer>" not in text.lower():
        return "missing_answer_tag"

    return "unknown"


def audit_extraction_failures(*, raw_path: Path, data_path: Path | None = None) -> dict[str, Any]:
    raw_rows = load_jsonl(raw_path)
    data_rows = load_jsonl(data_path) if data_path is not None else []
    data_by_id = {str(row["id"]): row for row in data_rows if "id" in row}

    failures: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    examples: dict[str, dict[str, Any]] = {}

    for raw_row in raw_rows:
        row_id = str(raw_row.get("id", ""))
        data_row = data_by_id.get(row_id, {})
        metadata = _metadata(data_row) if data_row else {}
        item_id = str(metadata.get("base_item_id", row_id))
        condition = str(metadata.get("condition", raw_row.get("condition", "")))
        gold = normalize_answer(metadata.get("gold", raw_row.get("gold", raw_row.get("answer", ""))))
        for entry in _response_entries(raw_row):
            if not bool(entry.get("extraction_failed", False)):
                continue
            raw_text = _extract_raw_text(entry)
            category = _classify_failure(raw_text)
            counts[category] += 1
            record = {
                "id": row_id,
                "base_item_id": item_id,
                "condition": condition,
                "agent_id": entry.get("agent_id"),
                "round_index": entry.get("round_index"),
                "raw_text": raw_text,
                "answer": normalize_answer(entry.get("answer", "")),
                "gold": gold,
                "category": category,
            }
            failures.append(record)
            examples.setdefault(category, record)

    for category in FAILURE_CATEGORIES:
        counts.setdefault(category, 0)

    summary = {
        "failure_total": len(failures),
        "category_counts": dict(sorted(counts.items())),
        "raw_rows": len(raw_rows),
        "items_seen": len({row["base_item_id"] for row in failures}),
        "condition_counts": dict(sorted(Counter(row["condition"] for row in failures).items())),
    }
    return {
        "raw": str(raw_path),
        "data": str(data_path) if data_path is not None else None,
        "failure_categories": FAILURE_CATEGORIES,
        "failures": failures,
        "examples": examples,
        "summary": summary,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Phase 2b Extraction Failure Audit")
    lines.append("")
    lines.append("Caution:")
    lines.append("- exploratory diagnostic")
    lines.append("- descriptive classification of existing raw outputs")
    lines.append("- not independent benchmark evidence")
    lines.append("- no causal proof")
    lines.append("- no statistical-significance claim")
    lines.append("")
    lines.append("## Category Definitions")
    lines.append("")
    lines.append("| category | description |")
    lines.append("| --- | --- |")
    lines.append("| missing_answer_tag | content exists but no `<answer>...</answer>` wrapper is present |")
    lines.append("| empty_output | output is empty or whitespace-only |")
    lines.append("| non_numeric_answer | answer is wrapped but not numeric for GSM8K-style items |")
    lines.append("| contains_numeric_but_unwrapped | a numeric candidate is present in the text but not wrapped |")
    lines.append("| multiple_candidate_numbers | multiple plausible numeric candidates are present |")
    lines.append("| tool_or_format_noise | tool chatter, malformed markup, or obvious format noise dominates |")
    lines.append("| unknown | catch-all when no other category fits |")
    lines.append("")
    lines.append("## Summary Counts")
    lines.append("")
    lines.append("| category | count |")
    lines.append("| --- | ---: |")
    for category, count in report["summary"]["category_counts"].items():
        lines.append(f"| {category} | {count} |")
    lines.append("")
    lines.append("## Examples")
    lines.append("")
    lines.append("| category | example_id | base_item_id | condition | agent_id | round_index |")
    lines.append("| --- | --- | --- | --- | ---: | ---: |")
    for category in report["failure_categories"]:
        example = report["examples"].get(category)
        if example is None:
            continue
        lines.append(
            f"| {category} | {example['id']} | {example['base_item_id']} | {example['condition']} | {example['agent_id']} | {example['round_index']} |"
        )
    lines.append("")
    lines.append("## Artifact Policy")
    lines.append("")
    lines.append("Raw model outputs, run directories, generated summaries, and generated result reports are local artifacts by default. Stable conclusions may be promoted into curated documentation, but `runs/*`, raw JSONL, summary JSON, and generated result markdown should not be committed unless explicitly reviewed and intentionally promoted.")
    lines.append("")
    lines.append("No raw model text is included.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit extraction failures for Phase 2b raw outputs.")
    parser.add_argument("--raw", required=True, help="Path to the raw.jsonl file to audit.")
    parser.add_argument("--data", default=None, help="Optional phase-2b data JSONL for metadata lookup.")
    parser.add_argument("--out-json", required=True, help="Output JSON audit path.")
    parser.add_argument("--out-md", required=True, help="Output Markdown audit path.")
    args = parser.parse_args()

    report = audit_extraction_failures(
        raw_path=Path(args.raw),
        data_path=Path(args.data) if args.data else None,
    )
    write_json(Path(args.out_json), report)
    write_markdown(report, Path(args.out_md))
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
