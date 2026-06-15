import json
from pathlib import Path

from tools.audit_extraction_failures_phase2b import audit_extraction_failures, write_markdown


def _entry(*, text: str = "", answer: str = "", extraction_failed: bool = True) -> dict:
    payload = {"agent_id": 1, "round_index": 0, "answer": answer, "extraction_failed": extraction_failed}
    if text:
        payload["raw_text"] = text
    return payload


def _raw_row(row_id: str, entry: dict) -> dict:
    return {"id": row_id, "final_raw": [entry]}


def test_audit_classifies_primary_categories_and_caps_examples(tmp_path: Path) -> None:
    raw_rows = [
        _raw_row("empty", _entry(text="")),
        _raw_row("missing", _entry(text="I think maybe so.")),
        _raw_row("unwrapped", _entry(text="The answer is 13.")),
        _raw_row("multiple", _entry(text="Maybe 13 or 14.")),
        _raw_row("non_numeric", _entry(text="<answer>thirteen</answer>")),
        _raw_row("noise", _entry(text="```json\n{\"answer\":\"13\"}\n```")),
        _raw_row("unknown", _entry(text="<answer>13</answer> extra")),
        _raw_row("cap0", _entry(text="13")),
        _raw_row("cap1", _entry(text="14")),
        _raw_row("cap2", _entry(text="15")),
        _raw_row("cap3", _entry(text="16")),
        _raw_row("cap4", _entry(text="17")),
        _raw_row("cap5", _entry(text="18")),
    ]
    raw_path = tmp_path / "raw.jsonl"
    raw_path.write_text("\n".join(__import__("json").dumps(row, ensure_ascii=False) for row in raw_rows) + "\n", encoding="utf-8")

    report = audit_extraction_failures(raw_path=raw_path)
    assert report["summary"]["failure_total"] == len(raw_rows)
    assert report["summary"]["category_counts"]["empty_output"] == 1
    assert report["summary"]["category_counts"]["missing_answer_tag"] >= 1
    assert report["summary"]["category_counts"]["contains_numeric_but_unwrapped"] >= 1
    assert report["summary"]["category_counts"]["multiple_candidate_numbers"] >= 1
    assert report["summary"]["category_counts"]["non_numeric_answer"] >= 1
    assert report["summary"]["category_counts"]["tool_or_format_noise"] >= 1
    assert report["summary"]["category_counts"]["unknown"] >= 1
    assert all(len(values) <= 5 for values in report["examples"].values())

    out_md = tmp_path / "audit.md"
    write_markdown(report, out_md)
    text = out_md.read_text(encoding="utf-8")
    assert "# Phase 2b Extraction Failure Audit" in text
    assert "## Category Definitions" in text
    assert "## Summary Counts" in text
    assert "## By Condition" in text
    assert "## By Item" in text
    assert "## Top Item-Condition Failure Concentrations" in text
    assert "## Short Examples" in text
    assert "No raw model text is included." in text
    assert "The answer is 13." not in text


def test_audit_uses_metadata_and_truncates_examples(tmp_path: Path) -> None:
    raw_rows = [_raw_row("row-1", _entry(text="I think maybe so."))]
    raw_path = tmp_path / "raw.jsonl"
    raw_path.write_text("\n".join(__import__("json").dumps(row, ensure_ascii=False) for row in raw_rows) + "\n", encoding="utf-8")
    data_path = tmp_path / "data.jsonl"
    data_path.write_text(
        "\n".join(
            [
                __import__("json").dumps(
                    {
                        "id": "row-1",
                        "metadata": {
                            "base_item_id": "gsm8k_test_000012",
                            "condition": "baseline_no_prefix",
                            "gold": "13",
                        },
                    },
                    ensure_ascii=False,
                )
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit_extraction_failures(raw_path=raw_path, data_path=data_path)
    example = report["examples"]["missing_answer_tag"][0]
    assert example["base_item_id"] == "gsm8k_test_000012"
    assert example["condition"] == "baseline_no_prefix"


def test_audit_truncates_long_text_and_caps_examples(tmp_path: Path) -> None:
    long_text = "A" * 1000
    raw_rows = [_raw_row(f"row-{index}", _entry(text=long_text)) for index in range(7)]
    raw_path = tmp_path / "raw.jsonl"
    raw_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in raw_rows) + "\n", encoding="utf-8")
    report = audit_extraction_failures(raw_path=raw_path)
    assert len(report["examples"]["missing_answer_tag"]) <= 5
    assert report["examples"]["missing_answer_tag"][0]["text_excerpt"] == long_text[:300]
