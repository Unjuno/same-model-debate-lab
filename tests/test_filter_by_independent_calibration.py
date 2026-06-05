from pathlib import Path

from tools.filter_by_independent_calibration import filter_by_independent_calibration, write_jsonl


def _row(item_id: str, answer: str) -> dict:
    return {"id": item_id, "type": "x", "question": "q", "answer": answer, "metadata": {}}


def test_filter_selects_partial_correct_item(tmp_path: Path) -> None:
    data_rows = [_row("keep", "42")]
    raw_rows = [
        {
            "id": "keep",
            "gold": "42",
            "initial_raw": [
                {"answer": "42", "extraction_failed": False},
                {"answer": "7", "extraction_failed": False},
                {"answer": "9", "extraction_failed": False},
            ],
        }
    ]

    selected, report = filter_by_independent_calibration(raw_rows=raw_rows, data_rows=data_rows)

    assert [row["id"] for row in selected] == ["keep"]
    assert report["selected"] == 1
    assert report["partially_correct"] == 1
    assert report["selected_ids"] == ["keep"]

    out = tmp_path / "out.jsonl"
    write_jsonl(out, selected)
    assert out.exists()


def test_filter_rejects_all_correct_all_wrong_and_extraction_failed() -> None:
    data_rows = [_row("all_correct", "10"), _row("all_wrong", "7"), _row("failed", "5")]
    raw_rows = [
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

    assert selected == []
    assert report["selected"] == 0
    assert report["all_correct"] == 1
    assert report["all_wrong"] == 1
    assert report["extraction_failed"] == 1


def test_filter_normalizes_choice_labels_and_numbers() -> None:
    data_rows = [_row("choice", "A"), _row("tagged", "A"), _row("number", "1234"), _row("float", "42")]
    raw_rows = [
        {"id": "choice", "gold": "A", "initial_answers": ["a", "B", "C"], "initial_extraction_failures": 0},
        {"id": "tagged", "gold": "A", "initial_answers": ["<answer>A</answer>", "B", "C"], "initial_extraction_failures": 0},
        {"id": "number", "gold": "1234", "initial_answers": ["1,234", "0", "9"], "initial_extraction_failures": 0},
        {"id": "float", "gold": "42", "initial_answers": ["42.0", "0", "9"], "initial_extraction_failures": 0},
    ]

    selected, report = filter_by_independent_calibration(raw_rows=raw_rows, data_rows=data_rows)

    assert [row["id"] for row in selected] == ["choice", "tagged", "number", "float"]
    assert report["selected"] == 4
    assert report["oracle_at_k"] == 1.0
    assert "partial_correct_rate" in report
    assert "extraction_failure_rate" in report


def test_filter_does_not_require_network(monkeypatch) -> None:
    import socket

    def fail_connect(*args, **kwargs):  # pragma: no cover - defensive guard
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr(socket.socket, "connect", fail_connect, raising=True)
    data_rows = [_row("x", "1")]
    raw_rows = [{"id": "x", "gold": "1", "initial_answers": ["1", "2", "3"], "initial_extraction_failures": 0}]

    selected, _ = filter_by_independent_calibration(raw_rows=raw_rows, data_rows=data_rows)
    assert selected
