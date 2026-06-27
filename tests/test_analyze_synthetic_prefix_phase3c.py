from __future__ import annotations

from pathlib import Path

from tools.analyze_synthetic_prefix_phase3c import analyze_synthetic_prefix_phase3c, write_markdown
from tools.build_synthetic_prefix_phase3_dataset import write_jsonl
from tools.build_synthetic_prefix_phase3c_dataset import build_dataset


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


def _raw_row(row_id: str, final_answer: str, answers: list[str], *, extraction_failures: int = 0) -> dict:
    return {
        "id": row_id,
        "final_answer": final_answer,
        "initial_answers": answers,
        "extraction_failures": extraction_failures,
        "final_raw": [{"answer": a, "extraction_failed": False} for a in answers],
    }


def test_analyzer_computes_by_condition_and_effects(tmp_path: Path) -> None:
    data_rows = build_dataset(phase3_data=_phase3_rows(), replicates=1)
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, data_rows)
    raw_rows = [
        _raw_row("gsm8k_test_000012__phase3c_baseline_no_prefix_sample_000", "13", ["13", "13", "12"]),
        _raw_row("gsm8k_test_000012__phase3c_wrong_answer_labeled_sample_000", "12", ["12", "12", "12"]),
        _raw_row("gsm8k_test_000012__phase3c_wrong_number_unlabeled_sample_000", "12", ["12", "12", "12"]),
        _raw_row("gsm8k_test_000012__phase3c_wrong_answer_with_uncertainty_sample_000", "13", ["13", "13", "13"]),
        _raw_row("gsm8k_test_000089__phase3c_baseline_no_prefix_sample_000", "24", ["24", "24", "18"]),
        _raw_row("gsm8k_test_000089__phase3c_wrong_answer_labeled_sample_000", "18", ["18", "18", "18"], extraction_failures=1),
        _raw_row("gsm8k_test_000089__phase3c_wrong_number_unlabeled_sample_000", "24", ["24", "24", "24"]),
        _raw_row("gsm8k_test_000089__phase3c_wrong_answer_with_uncertainty_sample_000", "18", ["18", "18", "18"]),
    ]
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)
    report = analyze_synthetic_prefix_phase3c(data_path=data_path, raw_path=raw_path)
    assert report["by_condition"]["wrong_answer_labeled"]["target_wrong_rate"] > report["by_condition"]["baseline_no_prefix"]["target_wrong_rate"]
    assert report["condition_effects"]["wrong_answer_labeled_delta_target_wrong"] > 0
    assert report["condition_effects"]["unlabeled_minus_labeled_delta_target_wrong"] <= 0
    assert report["item_effects"]["gsm8k_test_000012"]["wrong_answer_labeled_delta_target_wrong"] > 0
    assert report["item_group_effects"]["numeric_anchor_dominant"]["wrong_answer_labeled_delta_target_wrong"] > 0
    assert report["by_anchor_format_condition"]["answer_labeled__wrong_answer_labeled"]["n_outputs"] == 2
    assert "numeric_anchor_consistent" in report["summary"]["qualitative_labels"]
    out_md = tmp_path / "nested" / "report.md"
    write_markdown(report, out_md)
    assert out_md.exists()
    assert "No raw model text is included." in out_md.read_text(encoding="utf-8")


def test_analyzer_skips_unknown_and_handles_failure(tmp_path: Path) -> None:
    data_rows = build_dataset(phase3_data=_phase3_rows(), replicates=1)
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, data_rows)
    raw_rows = [
        _raw_row("unknown", "13", ["13"]),
        _raw_row("gsm8k_test_000012__phase3c_baseline_no_prefix_sample_000", "13", ["13"], extraction_failures=1),
    ]
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)
    report = analyze_synthetic_prefix_phase3c(data_path=data_path, raw_path=raw_path)
    assert report["summary"]["n"] == 2
    assert report["summary"]["skipped_raw_ids"] == ["unknown"]
    assert report["by_condition"]["baseline_no_prefix"]["effective_extraction_failure_rate"] == 1.0
