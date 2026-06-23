from __future__ import annotations

import json
from pathlib import Path

from tools.analyze_synthetic_prefix_phase3b import (
    analyze_synthetic_prefix_phase3b,
    write_markdown,
)
from tools.build_synthetic_prefix_phase3_dataset import write_jsonl
from tools.build_synthetic_prefix_phase3b_dataset import build_dataset


def _phase3_rows() -> list[dict]:
    return [
        {
            "id": "gsm8k_test_000012__phase3_baseline_no_prefix_sample_000",
            "type": "gsm8k_synthetic_prefix_phase3",
            "question": "Problem:\nExample.\n\nNow solve the original problem independently.\nReturn only the final numeric answer.",
            "answer": "13",
            "metadata": {"base_item_id": "gsm8k_test_000012", "gold": "13", "target_wrong_answer": "12", "item_group": "numeric_anchor_dominant"},
        },
        {
            "id": "gsm8k_test_000089__phase3_baseline_no_prefix_sample_000",
            "type": "gsm8k_synthetic_prefix_phase3",
            "question": "Problem:\nExample.\n\nNow solve the original problem independently.\nReturn only the final numeric answer.",
            "answer": "24",
            "metadata": {"base_item_id": "gsm8k_test_000089", "gold": "24", "target_wrong_answer": "18", "item_group": "rationale_corrective_reversal"},
        },
    ]


def _rationales(tmp_path: Path) -> Path:
    payload = {
        "items": [
            {
                "item_id": "gsm8k_test_000012",
                "gold": "13",
                "target_wrong": "12",
                "weak_wrong_rationale": "A lower estimate slips under the final count.",
                "medium_wrong_rationale": "The count stays below the correct value.",
                "strong_wrong_rationale": "The lower estimate keeps the count below the correct value.",
            },
            {
                "item_id": "gsm8k_test_000089",
                "gold": "24",
                "target_wrong": "18",
                "weak_wrong_rationale": "A smaller bag count is implied.",
                "medium_wrong_rationale": "The missing quarter is not fully included.",
                "strong_wrong_rationale": "The missing quarter is not fully restored.",
            },
        ]
    }
    path = tmp_path / "rationales.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _raw_row(row_id: str, final_answer: str, answers: list[str], *, extraction_failures: int = 0) -> dict:
    return {
        "id": row_id,
        "final_answer": final_answer,
        "initial_answers": answers,
        "extraction_failures": extraction_failures,
        "final_raw": [{"answer": a, "extraction_failed": False} for a in answers],
    }


def test_analyzer_computes_effects_and_writes_markdown(tmp_path: Path) -> None:
    data_rows = build_dataset(phase3_data=_phase3_rows(), rationales_path=_rationales(tmp_path), replicates=1)
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, data_rows)
    raw_rows = [
        _raw_row("gsm8k_test_000012__phase3b_baseline_no_prefix_sample_000", "13", ["13", "13", "12"]),
        _raw_row("gsm8k_test_000012__phase3b_wrong_answer_only_sample_000", "12", ["12", "12", "12"]),
        _raw_row("gsm8k_test_000012__phase3b_weak_wrong_rationale_only_sample_000", "13", ["13", "13", "13"]),
        _raw_row("gsm8k_test_000012__phase3b_medium_wrong_rationale_only_sample_000", "12", ["12", "12", "12"]),
        _raw_row("gsm8k_test_000012__phase3b_strong_wrong_rationale_only_sample_000", "12", ["12", "12", "12"]),
        _raw_row("gsm8k_test_000012__phase3b_weak_wrong_answer_plus_rationale_sample_000", "12", ["12", "12", "12"]),
        _raw_row("gsm8k_test_000012__phase3b_medium_wrong_answer_plus_rationale_sample_000", "12", ["12", "12", "12"]),
        _raw_row("gsm8k_test_000012__phase3b_strong_wrong_answer_plus_rationale_sample_000", "12", ["12", "12", "12"]),
        _raw_row("gsm8k_test_000089__phase3b_baseline_no_prefix_sample_000", "24", ["24", "18", "24"]),
        _raw_row("gsm8k_test_000089__phase3b_wrong_answer_only_sample_000", "18", ["18", "18", "18"], extraction_failures=1),
        _raw_row("gsm8k_test_000089__phase3b_weak_wrong_rationale_only_sample_000", "24", ["24", "24", "24"]),
        _raw_row("gsm8k_test_000089__phase3b_medium_wrong_rationale_only_sample_000", "24", ["24", "24", "24"]),
        _raw_row("gsm8k_test_000089__phase3b_strong_wrong_rationale_only_sample_000", "18", ["18", "18", "18"]),
        _raw_row("gsm8k_test_000089__phase3b_weak_wrong_answer_plus_rationale_sample_000", "18", ["18", "18", "18"]),
        _raw_row("gsm8k_test_000089__phase3b_medium_wrong_answer_plus_rationale_sample_000", "18", ["18", "18", "18"]),
        _raw_row("gsm8k_test_000089__phase3b_strong_wrong_answer_plus_rationale_sample_000", "18", ["18", "18", "18"]),
    ]
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)
    report = analyze_synthetic_prefix_phase3b(data_path=data_path, raw_path=raw_path)
    assert report["by_condition"]["wrong_answer_only"]["target_wrong_rate"] > report["by_condition"]["baseline_no_prefix"]["target_wrong_rate"]
    assert "numeric_anchor_consistent" in report["summary"]["qualitative_labels"]
    out_md = tmp_path / "nested" / "report.md"
    write_markdown(report, out_md)
    assert out_md.exists()
