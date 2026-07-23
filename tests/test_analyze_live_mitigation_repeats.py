import json

from tools.analyze_live_mitigation_repeats import metric_row


def test_metric_row_counts_initial_loss_and_extraction() -> None:
    rows = [
        {"id": "a", "initial_answers": ["1", "2"], "final_answer": "2", "extraction_failures": 0},
        {"id": "b", "initial_answers": ["3", "3"], "final_answer": "3", "extraction_failures": 1},
    ]
    metrics = metric_row(rows, {"a": "1", "b": "4"})
    assert metrics["final_accuracy"] == 0.0
    assert metrics["initial_any_correct_rate"] == 0.5
    assert metrics["answer_loss_rate"] == 1.0
    assert metrics["extraction_failure_rate"] == 0.5


def test_report_json_retains_repeat_metrics() -> None:
    report = json.loads(open("results/live_mitigation_partial9_repeated/report.json", encoding="utf-8").read())
    assert report["n_repeats"] == 20
    assert report["n_raw_paths"] == 100
    for condition in report["conditions"]:
        assert len(report["repeat_metrics"][condition]) == 20
