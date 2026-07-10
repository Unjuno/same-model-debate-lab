from pathlib import Path

from tools.analyze_live_mitigation import analyze_live_mitigation, write_json
from tools.build_synthetic_prefix_phase3c_dataset import write_jsonl


def _data_rows() -> list[dict]:
    return [
        {
            "id": "item_a",
            "question": "Q1",
            "answer": "10",
            "metadata": {"target_wrong": "12"},
        },
        {
            "id": "item_b",
            "question": "Q2",
            "answer": "20",
            "metadata": {"target_wrong": "22"},
        },
    ]


def _raw_rows() -> list[dict]:
    return [
        {
            "id": "item_a",
            "condition": "independent",
            "gold": "10",
            "initial_answers": ["10", "12", "10"],
            "final_answers": ["10", "10", "10"],
            "final_answer": "10",
            "extraction_failures": 0,
            "transcript_raw": [{"round_index": 0, "answer": "10"}],
        },
        {
            "id": "item_b",
            "condition": "full_context_debate",
            "gold": "20",
            "initial_answers": ["20", "22", "22"],
            "final_answers": ["22", "22", "22"],
            "final_answer": "22",
            "extraction_failures": 0,
            "transcript_raw": [{"round_index": 0, "answer": "20"}, {"round_index": 1, "answer": "22"}],
        },
    ]


def test_analyze_live_mitigation_reports_history_metrics(tmp_path: Path) -> None:
    data_path = tmp_path / "data.jsonl"
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(data_path, _data_rows())
    write_jsonl(raw_path, _raw_rows())

    report = analyze_live_mitigation(data_path=data_path, raw_paths=[raw_path])

    assert report["summary"]["final_accuracy"] == 0.5
    assert report["summary"]["history_metrics_available"] is True
    assert report["raw_sources"] == [str(raw_path)]
    assert report["by_condition"]["independent"]["initial_any_correct_rate"] == 1.0
    assert report["by_condition"]["full_context_debate"]["target_wrong_rate"] == 1.0
    assert report["by_condition"]["full_context_debate"]["correct_to_wrong_collapse_rate"] == 1.0
    assert report["by_condition"]["full_context_debate"]["correct_initial_lost_rate"] == 1.0
    assert report["by_condition"]["full_context_debate"]["target_wrong_convergence_rate"] == 1.0
    assert report["condition_effects"]["full_context_minus_independent_delta_correct_rate"] < 0

    out_json = tmp_path / "report.json"
    write_json(out_json, report)
    assert out_json.exists()


def test_analyze_live_mitigation_accepts_multiple_raw_inputs(tmp_path: Path) -> None:
    data_path = tmp_path / "data.jsonl"
    raw_a = tmp_path / "raw_a.jsonl"
    raw_b = tmp_path / "raw_b.jsonl"
    write_jsonl(data_path, _data_rows())
    write_jsonl(raw_a, [_raw_rows()[0]])
    write_jsonl(raw_b, [_raw_rows()[1]])

    report = analyze_live_mitigation(data_path=data_path, raw_paths=[raw_a, raw_b])
    assert report["summary"]["n"] == 2
    assert report["raw_sources"] == [str(raw_a), str(raw_b)]
