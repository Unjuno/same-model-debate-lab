import json
from pathlib import Path

from tools.audit_extraction_failures_phase2b import (
    audit_extraction_failures,
    write_json,
    write_markdown,
)


def _raw_row(row_id: str, raw_text: str, *, answer: str = "", extraction_failed: bool = True) -> dict:
    return {
        "id": row_id,
        "condition": "independent",
        "gold": "13",
        "final_raw": [
            {
                "agent_id": 1,
                "round_index": 0,
                "raw_text": raw_text,
                "answer": answer,
                "extraction_failed": extraction_failed,
            }
        ],
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def test_audit_classifies_failure_categories_and_writes_reports(tmp_path: Path) -> None:
    raw_rows = [
        _raw_row("empty", "   "),
        _raw_row("missing_tag", "I think maybe so."),
        _raw_row("non_numeric", "<answer>thirteen</answer>"),
        _raw_row("unwrapped_numeric", "The answer is 13."),
        _raw_row("multiple_numbers", "Maybe 13 or 14."),
        _raw_row("noise", "```python\nprint(13)\n```"),
        _raw_row("unknown", "<answer>13</answer> extra"),
    ]
    raw_path = tmp_path / "raw.jsonl"
    _write_jsonl(raw_path, raw_rows)

    report = audit_extraction_failures(raw_path=raw_path)

    assert report["summary"]["failure_total"] == 7
    assert report["summary"]["category_counts"]["empty_output"] == 1
    assert report["summary"]["category_counts"]["missing_answer_tag"] == 1
    assert report["summary"]["category_counts"]["non_numeric_answer"] == 1
    assert report["summary"]["category_counts"]["contains_numeric_but_unwrapped"] == 1
    assert report["summary"]["category_counts"]["multiple_candidate_numbers"] == 1
    assert report["summary"]["category_counts"]["tool_or_format_noise"] == 1
    assert report["summary"]["category_counts"]["unknown"] == 1

    out_json = tmp_path / "audit.json"
    out_md = tmp_path / "audit.md"
    write_json(out_json, report)
    write_markdown(report, out_md)

    assert out_json.read_text(encoding="utf-8").strip()
    text = out_md.read_text(encoding="utf-8")
    assert "# Phase 2b Extraction Failure Audit" in text
    assert "## Category Definitions" in text
    assert "## Summary Counts" in text
    assert "## Examples" in text
    assert "## Artifact Policy" in text
    assert "No raw model text is included." in text
    assert "The answer is 13." not in text


def test_audit_uses_data_metadata_when_available(tmp_path: Path) -> None:
    raw_rows = [_raw_row("gsm8k_test_000012__slot_00_baseline_no_prefix_sample_000", "I think maybe so.")]
    raw_path = tmp_path / "raw.jsonl"
    _write_jsonl(raw_path, raw_rows)

    data_path = tmp_path / "data.jsonl"
    _write_jsonl(
        data_path,
        [
            {
                "id": "gsm8k_test_000012__slot_00_baseline_no_prefix_sample_000",
                "metadata": {"base_item_id": "gsm8k_test_000012", "condition": "baseline_no_prefix", "gold": "13"},
            }
        ],
    )

    report = audit_extraction_failures(raw_path=raw_path, data_path=data_path)
    example = report["examples"]["missing_answer_tag"]
    assert example["base_item_id"] == "gsm8k_test_000012"
    assert example["condition"] == "baseline_no_prefix"
