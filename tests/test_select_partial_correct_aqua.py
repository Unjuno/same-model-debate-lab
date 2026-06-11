from pathlib import Path

from tools.select_partial_correct_aqua import select_partial_correct_aqua, write_jsonl


def _row(item_id: str, answer: str = "A") -> dict:
    return {"id": item_id, "type": "x", "question": "q", "answer": answer, "metadata": {}}


def test_select_partial_correct_applies_partial_rule_and_exclusions(tmp_path: Path) -> None:
    data_rows = [_row("keep"), _row("exclude")]
    raw_rows = [
        {
            "id": "keep",
            "gold": "A",
            "initial_raw": [
                {"answer": "A", "extraction_failed": False},
                {"answer": "B", "extraction_failed": False},
                {"answer": "C", "extraction_failed": False},
            ],
        },
        {
            "id": "exclude",
            "gold": "A",
            "initial_raw": [
                {"answer": "A", "extraction_failed": False},
                {"answer": "B", "extraction_failed": False},
                {"answer": "C", "extraction_failed": False},
            ],
        },
    ]

    selected = select_partial_correct_aqua(raw_rows=raw_rows, data_rows=data_rows, excluded_ids={"exclude"})

    assert [row["id"] for row in selected] == ["keep"]
    out = tmp_path / "out.jsonl"
    write_jsonl(out, selected)
    assert out.exists()


def test_select_partial_correct_rejects_all_correct_wrong_and_failures() -> None:
    data_rows = [_row("all_correct"), _row("all_wrong"), _row("failed")]
    raw_rows = [
        {
            "id": "all_correct",
            "gold": "A",
            "initial_answers": ["A", "A", "A"],
            "initial_extraction_failures": 0,
        },
        {
            "id": "all_wrong",
            "gold": "A",
            "initial_answers": ["B", "C", "D"],
            "initial_extraction_failures": 0,
        },
        {
            "id": "failed",
            "gold": "A",
            "initial_raw": [
                {"answer": "", "extraction_failed": True},
                {"answer": "A", "extraction_failed": False},
                {"answer": "B", "extraction_failed": False},
            ],
        },
    ]

    selected = select_partial_correct_aqua(raw_rows=raw_rows, data_rows=data_rows)

    assert selected == []
