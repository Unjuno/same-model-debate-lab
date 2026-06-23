from __future__ import annotations

import json
from pathlib import Path

from tools.analyze_synthetic_prefix_phase3b import analyze_synthetic_prefix_phase3b, write_markdown
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
            "id": "gsm8k_test_000236__phase3_baseline_no_prefix_sample_000",
            "type": "gsm8k_synthetic_prefix_phase3",
            "question": "Problem:\nExample.\n\nNow solve the original problem independently.\nReturn only the final numeric answer.",
            "answer": "19",
            "metadata": {"base_item_id": "gsm8k_test_000236", "gold": "19", "target_wrong_answer": "14", "item_group": "numeric_anchor_dominant"},
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
                "weak_wrong_rationale": "A smaller count is implied.",
                "medium_wrong_rationale": "Only the smaller count is carried through, so the total stays low.",
                "strong_wrong_rationale": "The smaller count is kept and the extra step is skipped, leaving the total low.",
            },
            {
                "item_id": "gsm8k_test_000236",
                "gold": "19",
                "target_wrong": "14",
                "weak_wrong_rationale": "A smaller adjustment is implied.",
                "medium_wrong_rationale": "Only the smaller adjustment is carried forward, so the total stays low.",
                "strong_wrong_rationale": "The smaller adjustment is kept and the extra step is skipped, leaving the total low.",
            },
            {
                "item_id": "gsm8k_test_000089",
                "gold": "24",
                "target_wrong": "18",
                "weak_wrong_rationale": "A smaller bag count is implied.",
                "medium_wrong_rationale": "The missing portion is not fully restored, so the total stays low.",
                "strong_wrong_rationale": "The missing portion is treated as still absent, which keeps the total low.",
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


def test_analyzer_aggregates_group_and_strength(tmp_path: Path) -> None:
    data_rows = build_dataset(phase3_data=_phase3_rows(), rationales_path=_rationales(tmp_path), replicates=1)
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, data_rows)
    raw_rows = []
    for item_id, answers_by_condition in {
        "gsm8k_test_000012": {
            "baseline_no_prefix": "13",
            "wrong_answer_only": "12",
            "weak_wrong_rationale_only": "13",
            "medium_wrong_rationale_only": "12",
            "strong_wrong_rationale_only": "13",
            "weak_wrong_answer_plus_rationale": "12",
            "medium_wrong_answer_plus_rationale": "12",
            "strong_wrong_answer_plus_rationale": "12",
        },
        "gsm8k_test_000236": {
            "baseline_no_prefix": "19",
            "wrong_answer_only": "14",
            "weak_wrong_rationale_only": "19",
            "medium_wrong_rationale_only": "14",
            "strong_wrong_rationale_only": "19",
            "weak_wrong_answer_plus_rationale": "14",
            "medium_wrong_answer_plus_rationale": "14",
            "strong_wrong_answer_plus_rationale": "14",
        },
        "gsm8k_test_000089": {
            "baseline_no_prefix": "24",
            "wrong_answer_only": "18",
            "weak_wrong_rationale_only": "24",
            "medium_wrong_rationale_only": "24",
            "strong_wrong_rationale_only": "18",
            "weak_wrong_answer_plus_rationale": "18",
            "medium_wrong_answer_plus_rationale": "18",
            "strong_wrong_answer_plus_rationale": "18",
        },
    }.items():
        for condition, final_answer in answers_by_condition.items():
            raw_rows.append(
                _raw_row(
                    f"{item_id}__phase3b_{condition}_sample_000",
                    final_answer,
                    [final_answer, final_answer, final_answer],
                    extraction_failures=1 if item_id == "gsm8k_test_000089" and condition == "wrong_answer_only" else 0,
                )
            )
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)
    report = analyze_synthetic_prefix_phase3b(data_path=data_path, raw_path=raw_path)
    assert report["by_condition"]["wrong_answer_only"]["target_wrong_rate"] > report["by_condition"]["baseline_no_prefix"]["target_wrong_rate"]
    assert report["by_item_group_condition"]["numeric_anchor_dominant__baseline_no_prefix"]["n_outputs"] == 2
    assert report["by_strength_condition"]["weak__weak_wrong_rationale_only"]["n_outputs"] == 3
    assert report["by_item_group_condition"]["rationale_corrective_reversal__baseline_no_prefix"]["n_outputs"] == 1
    assert report["item_effects"]["gsm8k_test_000012"]["wrong_answer_delta_target_wrong"] > 0
    assert report["item_group_effects"]["numeric_anchor_dominant"]["wrong_answer_delta_target_wrong"] > 0
    assert "numeric_anchor_consistent" in report["summary"]["qualitative_labels"]
    assert "item_group_heterogeneity_consistent" in report["summary"]["qualitative_labels"]
    out_md = tmp_path / "nested" / "report.md"
    write_markdown(report, out_md)
    assert out_md.exists()
    assert "No raw model text is included." in out_md.read_text(encoding="utf-8")


def test_analyzer_handles_extraction_failure_and_missing_keys(tmp_path: Path) -> None:
    data_rows = build_dataset(phase3_data=_phase3_rows(), rationales_path=_rationales(tmp_path), replicates=1)
    data_path = tmp_path / "data.jsonl"
    write_jsonl(data_path, data_rows)
    raw_rows = [_raw_row("gsm8k_test_000012__phase3b_baseline_no_prefix_sample_000", "13", ["13"], extraction_failures=1)]
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)
    report = analyze_synthetic_prefix_phase3b(data_path=data_path, raw_path=raw_path)
    assert report["summary"]["n"] == 1
    assert report["by_condition"]["baseline_no_prefix"]["effective_extraction_failure_rate"] == 1.0
