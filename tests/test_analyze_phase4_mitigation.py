from pathlib import Path

from tools.analyze_phase4_mitigation import analyze_phase4_mitigation, write_json
from tools.build_phase4_mitigation_dataset import build_dataset


def _phase3c_row(item_id: str, gold: str, wrong: str) -> dict:
    return {
        "id": f"{item_id}__phase3c_baseline_no_prefix_sample_000",
        "type": "gsm8k_synthetic_prefix_phase3c",
        "question": "Problem:\nExample.\n\nNow solve the original problem independently.\nReturn only the final numeric answer.",
        "answer": gold,
        "metadata": {
            "base_item_id": item_id,
            "gold": gold,
            "target_wrong": wrong,
            "item_group": "numeric_anchor_dominant",
            "history_metrics_applicable": False,
        },
    }


def _phase3c_data() -> list[dict]:
    return [_phase3c_row("gsm8k_test_000012", "13", "12")]


def _raw_row(row_id: str, final_answer: str, answers: list[str], *, extraction_failures: int = 0) -> dict:
    return {
        "id": row_id,
        "final_answer": final_answer,
        "initial_answers": answers,
        "final_answers": answers,
        "extraction_failures": extraction_failures,
        "final_raw": [{"answer": a, "extraction_failed": False} for a in answers],
    }


def test_analyzer_groups_by_condition_and_handles_missing_history(tmp_path: Path) -> None:
    data_rows = build_dataset(phase3c_data=_phase3c_data(), replicates=1)
    data_path = tmp_path / "data.jsonl"
    from tools.build_synthetic_prefix_phase3c_dataset import write_jsonl

    write_jsonl(data_path, data_rows)
    raw_rows = [
        _raw_row("gsm8k_test_000012__phase4_mitigation_independent_sample_000", "13", ["13"]),
        _raw_row("gsm8k_test_000012__phase4_mitigation_full_context_debate_sample_000", "12", ["13"]),
        _raw_row("gsm8k_test_000012__phase4_mitigation_answer_hidden_debate_sample_000", "13", ["13"]),
    ]
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw_rows)
    report = analyze_phase4_mitigation(data_path=data_path, raw_path=raw_path)
    assert report["by_condition"]["full_context_debate"]["target_wrong_rate"] == 1.0
    assert report["condition_effects"]["full_context_minus_independent_delta_target_wrong"] > 0
    assert report["by_condition"]["full_context_debate"]["history_metrics_available"] is False
    out_json = tmp_path / "report.json"
    write_json(out_json, report)
    assert out_json.exists()
