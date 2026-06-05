from pathlib import Path

from tools.filter_by_independent_calibration import filter_by_independent_calibration, write_jsonl


def test_filter_selects_partially_correct_and_rejects_other_cases(tmp_path: Path) -> None:
    data_rows = [
        {"id": "keep", "type": "x", "question": "q", "answer": "42", "metadata": {}},
        {"id": "all_correct", "type": "x", "question": "q", "answer": "10", "metadata": {}},
        {"id": "all_wrong", "type": "x", "question": "q", "answer": "7", "metadata": {}},
        {"id": "failed", "type": "x", "question": "q", "answer": "5", "metadata": {}},
    ]
    raw_rows = [
        {
            "id": "keep",
            "gold": "42",
            "initial_raw": [
                {"answer": "42", "extraction_failed": False},
                {"answer": "7", "extraction_failed": False},
                {"answer": "9", "extraction_failed": False},
            ],
        },
        {
            "id": "all_correct",
            "gold": "10",
            "initial_raw": [
                {"answer": "10", "extraction_failed": False},
                {"answer": "10", "extraction_failed": False},
                {"answer": "10", "extraction_failed": False},
            ],
        },
        {
            "id": "all_wrong",
            "gold": "7",
            "initial_raw": [
                {"answer": "1", "extraction_failed": False},
                {"answer": "2", "extraction_failed": False},
                {"answer": "3", "extraction_failed": False},
            ],
        },
        {
            "id": "failed",
            "gold": "5",
            "initial_raw": [
                {"answer": "", "extraction_failed": True},
                {"answer": "5", "extraction_failed": False},
                {"answer": "8", "extraction_failed": False},
            ],
        },
    ]

    selected, report = filter_by_independent_calibration(raw_rows=raw_rows, data_rows=data_rows)

    assert [row["id"] for row in selected] == ["keep"]
    assert report["total"] == 4
    assert report["selected"] == 1
    assert report["all_correct"] == 1
    assert report["all_wrong"] == 1
    assert report["partially_correct"] == 1
    assert report["extraction_failed"] == 1
    assert report["selected_ids"] == ["keep"]

    out = tmp_path / "out.jsonl"
    write_jsonl(out, selected)
    assert out.exists()


def test_filter_handles_fallback_row_shape() -> None:
    raw_rows = [
        {"id": "keep", "gold": "42", "initial_answers": ["42", "7", "8"], "initial_extraction_failures": 0},
    ]
    data_rows = [{"id": "keep", "type": "x", "question": "q", "answer": "42", "metadata": {}}]

    selected, report = filter_by_independent_calibration(raw_rows=raw_rows, data_rows=data_rows)

    assert len(selected) == 1
    assert report["selected"] == 1
